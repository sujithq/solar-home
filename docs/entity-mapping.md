# Shared Home Assistant sensor contract

Status: Pending live validation. Owner task:
[solar-home#3](https://github.com/sujithq/solar-home/issues/3).
No real entity IDs or live readings have been supplied.

Both applications use this contract in their own configuration; this document
does not automatically configure either application.

| Measurement | Actual HA entity ID | Normalized unit | Semantics/status |
| --- | --- | --- | --- |
| Grid import | TBD | W | Nonnegative delivered grid power; required for initial slice |
| Grid export | TBD | W | Nonnegative returned grid power; required for initial slice |
| PV production | TBD | W | Optional; distinguish DC production from AC output |
| Inverter AC output | TBD | W | Optional; verify sign and status |
| Household use | TBD/derived | W | Fresh/coherent AC + import - export; verify nighttime behavior |
| Current quarter-hour demand | TBD | W | Meter-specific; not instantaneous import power |
| Monthly peak | TBD | W | Meter-specific; validate month and occurrence timestamp |
| Meter timestamp/calendar | TBD | Unix ms/local fields | Validate Europe/Brussels and DST semantics |
| Import tariff 1/2 cumulative counters | TBD | Wh | Validate separate nondecreasing meter registers |
| Export tariff 1/2 cumulative counters | TBD | Wh | Validate separate nondecreasing meter registers |

For each mapping, record:

- Source integration, tested version/device firmware and actual entity ID.
- Meaning, source unit, normalized unit, sign, device_class and state_class.
- Update/report interval and observed worst-case delay.
- Meter measurement time, HA report/update time and client receive time semantics.
- Unchanged-value reporting evidence; last_changed alone is insufficient.
- Availability, supported range, reset behavior and independent stale threshold.
- Sanitized fixtures and verification date.

Do not assume illustrative electricity_currently_delivered/returned or
sungrow_total_active_power names exist. Do not label AC output as PV/DC production
without evidence. No unavailable state may be coerced to zero.

Separate entity updates are not an atomic meter telegram. Require coherent
required inputs; a PV/demand event must not refresh grid measurement time or GO.
Optional clock/peak/counter values have their own ages and semantics.

The inspected Systray meter freshness default is 30 seconds, inverter expiry
90 seconds. These are existing app defaults, not validated HA configuration.
Measure actual cadence before deciding suitable settings for either client.
