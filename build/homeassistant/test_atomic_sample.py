from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as Object
import unittest

from atomic_sample import SampleTracker


def telegram(stamp, imported=0, exported=0, unit="kW"):
    return Object(
        P1_MESSAGE_TIMESTAMP=Object(value=stamp),
        CURRENT_ELECTRICITY_USAGE=Object(value=imported, unit=unit),
        CURRENT_ELECTRICITY_DELIVERY=Object(value=exported, unit=unit),
    )


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
