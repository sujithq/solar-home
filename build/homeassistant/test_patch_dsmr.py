"""Test the reviewed DSMR checksum configuration and patch guard."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from patch_dsmr import (
    EXPECTED_SOURCE_SHA256,
    load_expected_source_sha256,
    patched_source,
)


class ChecksumConfigurationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.config_path = Path(directory.name) / "versions.json"

    def write_config(self, value):
        self.config_path.write_text(json.dumps(value), encoding="utf-8")

    def test_reads_reviewed_checksum(self):
        checksum = "a" * 64
        self.write_config({"dsmr_sensor_sha256": checksum})
        self.assertEqual(load_expected_source_sha256(self.config_path), checksum)

    def test_real_config_is_used(self):
        config_path = Path(__file__).with_name("versions.json")
        self.assertEqual(
            EXPECTED_SOURCE_SHA256, load_expected_source_sha256(config_path)
        )

    def test_rejects_missing_or_invalid_checksum(self):
        for value in (None, "", "a" * 63, "a" * 64 + "\n", "A" * 64, "g" * 64, 42):
            with self.subTest(value=value):
                self.write_config({"dsmr_sensor_sha256": value})
                with self.assertRaisesRegex(ValueError, "dsmr_sensor_sha256"):
                    load_expected_source_sha256(self.config_path)
        self.write_config({})
        with self.assertRaisesRegex(ValueError, "dsmr_sensor_sha256"):
            load_expected_source_sha256(self.config_path)

    def test_rejects_non_object_and_malformed_config(self):
        self.write_config([])
        with self.assertRaisesRegex(ValueError, "JSON object"):
            load_expected_source_sha256(self.config_path)
        self.config_path.write_text("{", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            load_expected_source_sha256(self.config_path)

    def test_rejects_missing_config(self):
        with self.assertRaises(FileNotFoundError):
            load_expected_source_sha256(self.config_path)

    def test_patch_uses_config_and_rejects_modified_source(self):
        source = (
            b"def callback(entities, hass, telegram, entry, dsmr_version):\n"
            b"        entities.extend(create_mbus_entities(hass, telegram, entry, dsmr_version))\n"
        )
        checksum = hashlib.sha256(source).hexdigest()
        self.write_config({"dsmr_sensor_sha256": checksum})
        patch_path = self.config_path.with_name("patch_dsmr.py")
        shutil.copyfile(Path(__file__).with_name("patch_dsmr.py"), patch_path)
        spec = importlib.util.spec_from_file_location("isolated_patch_dsmr", patch_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load isolated patch module {patch_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertEqual(module.EXPECTED_SOURCE_SHA256, checksum)
        self.assertIn(
            "entities.append(AtomicGridSensor(entry, telegram))",
            module.patched_source(source),
        )
        with self.assertRaisesRegex(RuntimeError, "Unreviewed DSMR source"):
            module.patched_source(source + b"\n")

    def test_patch_rejects_a_missing_hook(self):
        source = b"pass\n"
        with patch(
            "patch_dsmr.EXPECTED_SOURCE_SHA256", hashlib.sha256(source).hexdigest()
        ):
            with self.assertRaisesRegex(
                RuntimeError, "DSMR acquisition hook no longer matches"
            ):
                patched_source(source)


if __name__ == "__main__":
    unittest.main()
