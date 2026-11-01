"""Validate an atomic grid sample from an already parsed DSMR telegram."""

from datetime import datetime, timezone
import math
from uuid import uuid4


class SampleTracker:
    def __init__(self):
        self.session = uuid4().hex
        self.sequence = 0
        self.last_meter_time = None
        self.attributes = {}
        self.error = "waiting_for_telegram"

    def reject(self, reason):
        self.error = reason
        self.attributes = {"schema_version": 1, "session": self.session, "reason": reason}

    def accept(self, telegram, now):
        try:
            stamp = telegram.P1_MESSAGE_TIMESTAMP.value
            imported = telegram.CURRENT_ELECTRICITY_USAGE
            exported = telegram.CURRENT_ELECTRICITY_DELIVERY
            pairs = [(point.value, point.unit) for point in (imported, exported)]
        except AttributeError:
            self.reject("missing_required_fields")
            return
        if not isinstance(stamp, datetime) or stamp.utcoffset() is None:
            self.reject("invalid_meter_timestamp")
            return
        stamp = stamp.astimezone(timezone.utc)
        age = (now - stamp).total_seconds()
        if age >= 30 or age < -5:
            self.reject("meter_timestamp_out_of_range")
            return
        if self.last_meter_time is not None and stamp <= self.last_meter_time:
            self.reject("nonadvancing_meter_timestamp")
            return
        powers = []
        for raw, unit in pairs:
            if isinstance(raw, bool):
                self.reject("invalid_power")
                return
            try:
                value = float(raw)
            except (TypeError, ValueError):
                self.reject("invalid_power")
                return
            if unit not in ("W", "kW"):
                self.reject("unsupported_power_unit")
                return
            value *= 1000 if unit == "kW" else 1
            if not math.isfinite(value) or value < 0:
                self.reject("invalid_power")
                return
            powers.append(value)
        self.sequence += 1
        self.last_meter_time = stamp
        self.error = None
        self.attributes = {
            "schema_version": 1,
            "session": self.session,
            "sample_sequence": self.sequence,
            "meter_timestamp": stamp.isoformat(),
            "received_at": now.isoformat(),
            "import_w": powers[0],
            "export_w": powers[1],
        }
