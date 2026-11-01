"""Exercise the adapter against installed HA without starting HA or a reader."""

from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from dsmr_parser.clients.protocol import DSMRProtocol
from dsmr_parser.exceptions import InvalidChecksumError
from patch_dsmr import patched_source

ROOT = Path(__file__).parent
PREFIX = "homeassistant.components.dsmr"
for name in ("atomic_sample", "atomic_sensor"):
    spec = importlib.util.spec_from_file_location(f"{PREFIX}.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
adapter = sys.modules[f"{PREFIX}.atomic_sensor"]


class AdapterTests(unittest.TestCase):
    def test_parser_only_forwards_checksum_accepted_telegram(self):
        parser = Mock()
        callback = Mock()
        protocol = DSMRProtocol(Mock(), parser, callback)
        parser.parse.side_effect = InvalidChecksumError("synthetic checksum rejection")
        protocol.handle_telegram("synthetic")
        callback.assert_not_called()
        parsed = object()
        parser.parse.side_effect = None
        parser.parse.return_value = parsed
        protocol.handle_telegram("synthetic")
        callback.assert_called_once_with(parsed)

    def test_expiry_and_recovery(self):
        now = datetime.now(timezone.utc)
        telegram = SimpleNamespace(
            P1_MESSAGE_TIMESTAMP=SimpleNamespace(value=now),
            CURRENT_ELECTRICITY_USAGE=SimpleNamespace(value=0, unit="kW"),
            CURRENT_ELECTRICITY_DELIVERY=SimpleNamespace(value=0, unit="kW"),
        )
        sensor = adapter.AtomicGridSensor(SimpleNamespace(entry_id="synthetic"), telegram)
        sensor.hass = Mock()
        sensor.async_write_ha_state = Mock()
        with patch.object(adapter, "async_call_later", return_value=Mock()) as schedule:
            sensor._schedule_expiry()
            self.assertEqual(schedule.call_count, 1)
            sensor._expire(None)
            self.assertFalse(sensor.available)
            self.assertNotIn("import_w", sensor.extra_state_attributes)
            sensor.update_data(None)
            self.assertFalse(sensor.available)
            telegram.P1_MESSAGE_TIMESTAMP.value += timedelta(seconds=1)
            sensor.update_data(telegram)
            self.assertTrue(sensor.available)
            self.assertEqual(sensor.native_value, 2)
            self.assertTrue(sensor.force_update)

    def test_reviewed_source_contains_accepted_telegram_hook(self):
        source = Path(
            "/usr/src/homeassistant/homeassistant/components/dsmr/sensor.py"
        ).read_bytes()
        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            "b9a0c9c9ff0d82de52f9574bf41ef3b12501d387de3a37c4211e84a08e0c4b60",
        )
        compiled = patched_source(source)
        self.assertIn("entities.append(AtomicGridSensor(entry, telegram))", compiled)
        with self.assertRaisesRegex(RuntimeError, "Unreviewed DSMR source"):
            patched_source(source + b"\n")


if __name__ == "__main__":
    unittest.main()
