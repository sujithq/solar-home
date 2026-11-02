"""Validate an atomic grid sample from an already parsed DSMR telegram."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math
from zoneinfo import ZoneInfo
from uuid import uuid4

LOCAL_TIMEZONE = ZoneInfo("Europe/Brussels")


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
            value, error = _measurement(raw, unit, {"W": 1, "kW": 1000})
            if error:
                self.reject("invalid_power")
                return
            powers.append(value)
        optional = _optional_fields(telegram, stamp)
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
            **optional,
        }


def _measurement(raw, unit, units, *, maximum=None, whole_number=False):
    if isinstance(raw, bool) or raw is None:
        return None, "invalid"
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, OverflowError, TypeError, ValueError):
        return None, "invalid"
    if not isinstance(unit, str) or unit not in units or not value.is_finite():
        return None, "invalid"
    value *= units[unit]
    if (
        value < 0
        or (maximum is not None and value > Decimal(maximum))
        or (whole_number and value != value.to_integral_value())
    ):
        return None, "invalid"
    if whole_number:
        return int(value), None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None, "invalid"
    return numeric, None


def _read_optional_measurement(
    telegram, name, units, *, maximum=None, whole_number=False
):
    try:
        point = getattr(telegram, name)
    except AttributeError:
        return None, "missing"
    try:
        raw, unit = point.value, point.unit
    except AttributeError:
        return None, "invalid"
    if raw is None:
        return None, "missing"
    value, error = _measurement(
        raw, unit, units, maximum=maximum, whole_number=whole_number
    )
    return value, "invalid" if error else "available"


def _optional_fields(telegram, meter_stamp):
    demand, demand_status = _read_optional_measurement(
        telegram,
        "BELGIUM_CURRENT_AVERAGE_DEMAND",
        {"W": 1, "kW": 1000},
        maximum=1_000_000,
        whole_number=True,
    )
    fields = {
        "demand_w": demand,
        "monthly_peak_w": None,
        "monthly_peak_at": None,
        "monthly_peak_month": None,
        "import_tariff_1_wh": None,
        "import_tariff_2_wh": None,
        "export_tariff_1_wh": None,
        "export_tariff_2_wh": None,
    }
    status = {
        "demand": demand_status,
        "monthly_peak": "missing",
        "import_tariff_1": "missing",
        "import_tariff_2": "missing",
        "export_tariff_1": "missing",
        "export_tariff_2": "missing",
    }

    try:
        peak = telegram.BELGIUM_MAXIMUM_DEMAND_MONTH
    except AttributeError:
        peak = None
    if peak is not None:
        try:
            peak_at, raw, unit = peak.datetime, peak.value, peak.unit
        except AttributeError:
            status["monthly_peak"] = "invalid"
        else:
            if peak_at is None or raw is None:
                status["monthly_peak"] = "missing"
            elif not isinstance(peak_at, datetime) or peak_at.utcoffset() is None:
                status["monthly_peak"] = "invalid"
            else:
                peak_at = peak_at.astimezone(timezone.utc)
                peak_w, error = _measurement(
                    raw,
                    unit,
                    {"W": 1, "kW": 1000},
                    maximum=1_000_000,
                    whole_number=True,
                )
                if error or peak_at > meter_stamp:
                    status["monthly_peak"] = "invalid"
                else:
                    fields.update(
                        monthly_peak_w=peak_w,
                        monthly_peak_at=peak_at.isoformat(),
                        monthly_peak_month=peak_at.astimezone(LOCAL_TIMEZONE).strftime(
                            "%Y-%m"
                        ),
                    )
                    status["monthly_peak"] = "available"

    tariffs = (
        ("ELECTRICITY_USED_TARIFF_1", "import_tariff_1_wh"),
        ("ELECTRICITY_USED_TARIFF_2", "import_tariff_2_wh"),
        ("ELECTRICITY_DELIVERED_TARIFF_1", "export_tariff_1_wh"),
        ("ELECTRICITY_DELIVERED_TARIFF_2", "export_tariff_2_wh"),
    )
    for parser_name, output_name in tariffs:
        value, field_status = _read_optional_measurement(
            telegram,
            parser_name,
            {"Wh": 1, "kWh": 1000},
            maximum=999_999_999,
            whole_number=True,
        )
        fields[output_name] = value
        status[output_name.removesuffix("_wh")] = field_status

    fields["optional_status"] = status
    return fields
