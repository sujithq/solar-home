from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as Object
import unittest

from atomic_sample import SampleTracker


def telegram(stamp, imported=0, exported=0, unit="kW", **optional):
    fields = dict(
        P1_MESSAGE_TIMESTAMP=Object(value=stamp),
        CURRENT_ELECTRICITY_USAGE=Object(value=imported, unit=unit),
        CURRENT_ELECTRICITY_DELIVERY=Object(value=exported, unit=unit),
    )
    if "demand" in optional:
        fields["BELGIUM_CURRENT_AVERAGE_DEMAND"] = optional["demand"]
    if "peak" in optional:
        fields["BELGIUM_MAXIMUM_DEMAND_MONTH"] = optional["peak"]
    for parser_name, argument_name in (
        ("ELECTRICITY_USED_TARIFF_1", "import_tariff_1"),
        ("ELECTRICITY_USED_TARIFF_2", "import_tariff_2"),
        ("ELECTRICITY_DELIVERED_TARIFF_1", "export_tariff_1"),
        ("ELECTRICITY_DELIVERED_TARIFF_2", "export_tariff_2"),
    ):
        if argument_name in optional:
            fields[parser_name] = optional[argument_name]
    return Object(**fields)


class SampleTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        self.tracker = SampleTracker()

    def test_unchanged_zero_is_new_sample(self):
        for seconds in (0, 1):
            now = self.now + timedelta(seconds=seconds)
            self.tracker.accept(telegram(now), now)
        self.assertEqual(self.tracker.sequence, 2)
        self.assertEqual(self.tracker.attributes["import_w"], 0)

    def test_units_and_timezone(self):
        local = self.now.astimezone(timezone(timedelta(hours=1)))
        self.tracker.accept(telegram(local, 1.2, 0.3), self.now)
        self.assertEqual(self.tracker.attributes["import_w"], 1200)
        self.assertEqual(self.tracker.attributes["export_w"], 300)
        self.assertEqual(self.tracker.attributes["meter_timestamp"], self.now.isoformat())

    def test_optional_fields_are_atomic_and_normalized(self):
        peak_at = datetime(2025, 12, 31, 23, 30, tzinfo=timezone.utc)
        current = self.now.replace(month=1, day=1, hour=1).astimezone(
            timezone(timedelta(hours=1))
        )
        sample = telegram(
            current,
            demand=Object(value=1.25, unit="kW"),
            peak=Object(datetime=peak_at, value=2.5, unit="kW"),
            import_tariff_1=Object(value=100.25, unit="kWh"),
            import_tariff_2=Object(value=200, unit="Wh"),
            export_tariff_1=Object(value=3, unit="kWh"),
            export_tariff_2=Object(value=4.5, unit="kWh"),
        )
        self.tracker.accept(sample, current.astimezone(timezone.utc))
        attrs = self.tracker.attributes
        self.assertIsNone(self.tracker.error)
        self.assertEqual(attrs["schema_version"], 1)
        self.assertEqual(attrs["demand_w"], 1250)
        self.assertEqual(attrs["monthly_peak_w"], 2500)
        self.assertEqual(attrs["monthly_peak_at"], peak_at.isoformat())
        self.assertEqual(attrs["monthly_peak_month"], "2026-01")
        self.assertEqual(attrs["import_tariff_1_wh"], 100250)
        self.assertEqual(attrs["import_tariff_2_wh"], 200)
        self.assertEqual(attrs["export_tariff_1_wh"], 3000)
        self.assertEqual(attrs["export_tariff_2_wh"], 4500)
        self.assertTrue(
            all(
                isinstance(attrs[name], int)
                for name in (
                    "demand_w",
                    "monthly_peak_w",
                    "import_tariff_1_wh",
                    "import_tariff_2_wh",
                    "export_tariff_1_wh",
                    "export_tariff_2_wh",
                )
            )
        )
        self.assertTrue(all(value == "available" for value in attrs["optional_status"].values()))

    def test_missing_optional_values_are_null_and_not_carried_forward(self):
        peak_at = self.now - timedelta(seconds=1)
        first = telegram(
            self.now,
            demand=Object(value=1, unit="kW"),
            peak=Object(datetime=peak_at, value=2, unit="kW"),
            import_tariff_1=Object(value=10, unit="kWh"),
        )
        self.tracker.accept(first, self.now)
        later = self.now + timedelta(seconds=1)
        self.tracker.accept(telegram(later), later)
        attrs = self.tracker.attributes
        self.assertEqual(attrs["demand_w"], None)
        self.assertEqual(attrs["monthly_peak_w"], None)
        self.assertEqual(attrs["monthly_peak_at"], None)
        self.assertEqual(attrs["monthly_peak_month"], None)
        self.assertEqual(attrs["import_tariff_1_wh"], None)
        self.assertEqual(attrs["optional_status"]["demand"], "missing")
        self.assertEqual(attrs["optional_status"]["monthly_peak"], "missing")
        self.assertEqual(attrs["optional_status"]["import_tariff_1"], "missing")
        self.assertEqual(attrs["optional_status"]["import_tariff_2"], "missing")
        self.assertEqual(
            set(attrs["optional_status"]),
            {
                "demand",
                "monthly_peak",
                "import_tariff_1",
                "import_tariff_2",
                "export_tariff_1",
                "export_tariff_2",
            },
        )

    def test_partial_monthly_peak_is_unavailable_as_a_group(self):
        sample = telegram(
            self.now,
            peak=Object(
                datetime=self.now - timedelta(seconds=1), value=None, unit="kW"
            ),
        )
        self.tracker.accept(sample, self.now)
        attrs = self.tracker.attributes
        self.assertIsNone(self.tracker.error)
        self.assertEqual(attrs["monthly_peak_w"], None)
        self.assertEqual(attrs["monthly_peak_at"], None)
        self.assertEqual(attrs["monthly_peak_month"], None)
        self.assertEqual(attrs["optional_status"]["monthly_peak"], "missing")

    def test_invalid_optional_value_does_not_invalidate_grid_sample(self):
        sample = telegram(
            self.now,
            demand=Object(value=float("nan"), unit="kW"),
            peak=Object(
                datetime=self.now + timedelta(seconds=1), value=5, unit="kW"
            ),
            import_tariff_1=Object(value=-1, unit="kWh"),
            import_tariff_2=Object(value=10, unit="MWh"),
        )
        self.tracker.accept(sample, self.now)
        attrs = self.tracker.attributes
        self.assertTrue(self.tracker.error is None)
        self.assertEqual(attrs["sample_sequence"], 1)
        self.assertEqual(attrs["import_w"], 0)
        self.assertEqual(attrs["demand_w"], None)
        self.assertEqual(attrs["monthly_peak_w"], None)
        self.assertEqual(attrs["monthly_peak_at"], None)
        self.assertEqual(attrs["import_tariff_1_wh"], None)
        self.assertEqual(attrs["import_tariff_2_wh"], None)
        self.assertEqual(attrs["optional_status"]["demand"], "invalid")
        self.assertEqual(attrs["optional_status"]["monthly_peak"], "invalid")
        self.assertEqual(attrs["optional_status"]["import_tariff_1"], "invalid")
        self.assertEqual(attrs["optional_status"]["import_tariff_2"], "invalid")

    def test_optional_range_and_fractional_wh_are_invalid_only_for_that_field(self):
        sample = telegram(
            self.now,
            demand=Object(value=1000.001, unit="kW"),
            peak=Object(
                datetime=self.now - timedelta(seconds=1),
                value=1000.001,
                unit="kW",
            ),
            import_tariff_1=Object(value=1_000_000, unit="kWh"),
            import_tariff_2=Object(value=0.0005, unit="kWh"),
        )
        self.tracker.accept(sample, self.now)
        attrs = self.tracker.attributes
        self.assertIsNone(self.tracker.error)
        self.assertEqual(attrs["sample_sequence"], 1)
        self.assertEqual(attrs["demand_w"], None)
        self.assertEqual(attrs["monthly_peak_w"], None)
        self.assertEqual(attrs["import_tariff_1_wh"], None)
        self.assertEqual(attrs["import_tariff_2_wh"], None)
        self.assertEqual(attrs["optional_status"]["demand"], "invalid")
        self.assertEqual(attrs["optional_status"]["monthly_peak"], "invalid")
        self.assertEqual(attrs["optional_status"]["import_tariff_1"], "invalid")
        self.assertEqual(attrs["optional_status"]["import_tariff_2"], "invalid")

    def test_optional_numeric_overflow_is_field_local(self):
        sample = telegram(
            self.now,
            demand=Object(value=10**10000, unit="W"),
            import_tariff_1=Object(value=1, unit=["unexpected"]),
        )
        self.tracker.accept(sample, self.now)
        self.assertIsNone(self.tracker.error)
        self.assertEqual(self.tracker.attributes["demand_w"], None)
        self.assertEqual(self.tracker.attributes["optional_status"]["demand"], "invalid")
        self.assertEqual(self.tracker.attributes["import_tariff_1_wh"], None)
        self.assertEqual(
            self.tracker.attributes["optional_status"]["import_tariff_1"], "invalid"
        )

    def test_cumulative_counter_reset_does_not_block_new_grid_sample(self):
        previous = telegram(
            self.now, import_tariff_1=Object(value=900, unit="kWh")
        )
        self.tracker.accept(previous, self.now)
        later = self.now + timedelta(seconds=1)
        reset = telegram(
            later, import_tariff_1=Object(value=1, unit="kWh")
        )
        self.tracker.accept(reset, later)
        self.assertIsNone(self.tracker.error)
        self.assertEqual(self.tracker.attributes["sample_sequence"], 2)
        self.assertEqual(self.tracker.attributes["import_tariff_1_wh"], 1000)

    def test_partial_does_not_keep_powers(self):
        self.tracker.accept(telegram(self.now, 1), self.now)
        self.tracker.accept(Object(), self.now)
        self.assertEqual(self.tracker.sequence, 1)
        self.assertNotIn("import_w", self.tracker.attributes)
        self.assertIsNotNone(self.tracker.error)

    def test_invalid_and_stale(self):
        for value, unit in [(float("nan"), "W"), (float("inf"), "W"), (-1, "W"),
                            (True, "W"), ("invalid", "W"), (1, "MW")]:
            self.tracker.accept(telegram(self.now, value, unit=unit), self.now)
            self.assertIsNotNone(self.tracker.error)
        for stamp in [self.now - timedelta(seconds=30),
                      self.now + timedelta(seconds=6), self.now.replace(tzinfo=None)]:
            self.tracker.accept(telegram(stamp), self.now)
            self.assertIsNotNone(self.tracker.error)
        self.assertEqual(self.tracker.sequence, 0)

    def test_replay_reconnect_and_restart(self):
        self.tracker.accept(telegram(self.now), self.now)
        self.tracker.reject("transport_unavailable")
        self.tracker.accept(telegram(self.now), self.now)
        self.assertEqual(self.tracker.error, "nonadvancing_meter_timestamp")
        new_time = self.now + timedelta(seconds=1)
        self.tracker.accept(telegram(new_time), new_time)
        self.assertEqual(self.tracker.sequence, 2)
        restarted = SampleTracker()
        self.assertNotEqual(restarted.session, self.tracker.session)
        self.assertEqual(restarted.sequence, 0)
        restarted.accept(telegram(self.now), self.now + timedelta(seconds=31))
        self.assertIsNotNone(restarted.error)

    def test_silence_does_not_advance_sequence(self):
        self.tracker.accept(telegram(self.now), self.now)
        self.assertEqual(self.tracker.sequence, 1)
        self.assertEqual(self.tracker.attributes["received_at"], self.now.isoformat())


if __name__ == "__main__":
    unittest.main()
