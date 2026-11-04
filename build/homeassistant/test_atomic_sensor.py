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
from dsmr_parser.objects import Telegram
from dsmr_parser.telegram_specifications import BELGIUM_FLUVIUS
from patch_dsmr import EXPECTED_SOURCE_SHA256, patched_source

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

    def test_belgian_5b_fields_are_extracted_from_same_parsed_telegram(self):
        lines = {
            "P1_MESSAGE_TIMESTAMP": "1-0:1.0.0(261025030000W)\r\n",
            "CURRENT_ELECTRICITY_USAGE": "1-0:1.7.0(000.500*kW)\r\n",
            "CURRENT_ELECTRICITY_DELIVERY": "1-0:2.7.0(000.100*kW)\r\n",
            "BELGIUM_CURRENT_AVERAGE_DEMAND": "1-0:1.4.0(001.234*kW)\r\n",
            "BELGIUM_MAXIMUM_DEMAND_MONTH": (
                "1-0:1.6.0(261025023000W)(001.250*kW)\r\n"
            ),
            "ELECTRICITY_USED_TARIFF_1": "1-0:1.8.1(00123.456*kWh)\r\n",
            "ELECTRICITY_USED_TARIFF_2": "1-0:1.8.2(00002.001*kWh)\r\n",
            "ELECTRICITY_DELIVERED_TARIFF_1": "1-0:2.8.1(00003.000*kWh)\r\n",
            "ELECTRICITY_DELIVERED_TARIFF_2": "1-0:2.8.2(00004.000*kWh)\r\n",
        }
        telegram = Telegram()
        spec = {obj["value_name"]: obj for obj in BELGIUM_FLUVIUS["objects"]}
        for name, line in lines.items():
            obj = spec[name]
            telegram.add(
                obj["obis_reference"], obj["value_parser"].parse(line), name
            )

        stamp = telegram.P1_MESSAGE_TIMESTAMP.value
        tracker = sys.modules[f"{PREFIX}.atomic_sample"].SampleTracker()
        tracker.accept(telegram, stamp)
        attrs = tracker.attributes
        self.assertIsNone(tracker.error)
        self.assertEqual(attrs["import_w"], 500)
        self.assertEqual(attrs["export_w"], 100)
        self.assertEqual(attrs["demand_w"], 1234)
        self.assertEqual(attrs["monthly_peak_w"], 1250)
        self.assertEqual(attrs["monthly_peak_at"], "2026-10-25T01:30:00+00:00")
        self.assertEqual(attrs["monthly_peak_month"], "2026-10")
        self.assertEqual(attrs["import_tariff_1_wh"], 123456)
        self.assertEqual(attrs["import_tariff_2_wh"], 2001)
        self.assertEqual(attrs["export_tariff_1_wh"], 3000)
        self.assertEqual(attrs["export_tariff_2_wh"], 4000)
        self.assertTrue(
            all(value == "available" for value in attrs["optional_status"].values())
        )

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
            EXPECTED_SOURCE_SHA256,
        )
        compiled = patched_source(source)
        self.assertIn("entities.append(AtomicGridSensor(entry, telegram))", compiled)
        with self.assertRaisesRegex(RuntimeError, "Unreviewed DSMR source"):
            patched_source(source + b"\n")


if __name__ == "__main__":
    unittest.main()
