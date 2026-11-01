# Shared Home Assistant sensor contract

Status: First implementation slice approved on 2026-11-01; physical measurement
correctness is a working assumption, not verified acceptance. Owner task:
[solar-home#3](https://github.com/sujithq/solar-home/issues/3).

Both applications use this contract in their own configuration; this document
does not automatically configure either application. The IDs below were found
in the existing HA entity registry. They are deployment-specific defaults, not
hardcoded requirements: both clients must allow each mapping to be configured.
No device identifiers, private endpoints, credentials or raw readings belong here.

## First-slice mappings

HA Container 2026.10.4 uses built-in DSMR and HACS Sungrow 6.7.0 with
`sungrow-isolarcloud==0.20.0`. DSMR working and Sungrow local setup are
user-confirmed. Source units below are screenshot-confirmed; this does not
validate physical cadence, daytime readings or meter sign behavior.

| Role | Actual HA entity ID | Source -> normalized | First-slice use |
| --- | --- | --- | --- |
| Grid import | `sensor.electricity_meter_power_consumption` | kW -> W, multiply by 1000 | Required, nonnegative power taken from grid |
| Grid export | `sensor.electricity_meter_power_production` | kW -> W, multiply by 1000 | Required, nonnegative power sent to grid |
| Inverter AC output | `sensor.sg5_0rs_local_total_active_power` | W -> W | Optional, AC output; daytime/sign validation pending |
| PV/DC power | `sensor.sg5_0rs_local_total_dc_power` | W -> W | Optional display only; not interchangeable with AC |
| Daily solar energy | `sensor.sg5_0rs_local_daily_yield` | kWh -> Wh, multiply by 1000 | Optional partial-day display; not full daily feature parity |
| Lifetime solar energy | `sensor.sg5_0rs_local_total_yield` | kWh -> Wh, multiply by 1000 | Optional cumulative display; resets/cadence unverified |
| Inverter availability | `binary_sensor.sg5_0rs_local_connectivity` | on/off | Availability gate only, never a measurement timestamp |
| Modbus diagnostics | `sensor.sg5_0rs_local_modbus_status` | text/attributes | Exists but disabled; do not enable automatically |
| Operating/running state | Not found | Not established | Unsupported until discovered and validated |

Grid net import is `import_W - export_W`; net export/surplus uses the opposite
sign. Do not swap these independent nonnegative readings or use absolute values
to conceal invalid signs. Household use can be derived as
`AC_W + import_W - export_W` only with fresh, coherent inputs and a validated
topology/sign contract. Do not substitute DC or missing AC with zero; household
derivation remains unavailable without those prerequisites.

The SG-RS integration derives daily yield from lifetime energy minus a persisted
day baseline. First-time setup cannot reconstruct generation earlier that day;
first-evening zero is not proof of either no generation or a read failure.
Power zeros at night are plausible, but all-zero voltage/frequency/temperature
and daytime data remain unresolved.

## Transport, freshness and failure behavior

Both clients independently use authenticated HA `/api/websocket`, including
diagnostics. Explicit HA mode has no REST, Agent-API or direct-hardware fallback.
Credentials are independently configurable and stored using each application's
existing protected storage, never source-controlled defaults. Connection/auth
errors must be visible and clear HA-derived recommendations.

Track availability and measurement evidence independently for every mapped
entity. Grid import/export use their own freshness limit; optional AC/DC use
their own inverter limit. Energy counters, connectivity and diagnostic events
must not refresh grid ages. Existing Systray defaults of 30 seconds for meter
and 90 seconds for inverter are provisional configuration defaults, not measured
HA cadence; retain configurable thresholds and measure before live acceptance.
Sungrow is configured to poll every 30 seconds, but configured polling is not
proof that reads succeed.

Retain source measurement time where validated, HA `last_changed`, `last_updated`
and `last_reported` separately from monotonic client receive time:

- `last_changed` advances on value changes, not necessarily every measurement.
- `last_updated` reflects HA state/attribute updates, not necessarily a new
  physical sample.
- `last_reported` or an incoming event can reflect reporting of unchanged or
  retained data; neither alone proves a fresh meter telegram/register read.
- A heartbeat, reconnect, initial snapshot or repeated cached state must not
  reset physical freshness or independently enable a recommendation.

Accept measurement freshness only from a source signal whose relationship to
successful acquisition is established, or conservatively from a demonstrably
new source state update under the explicitly provisional acquisition assumption.
Label the latter as HA-update evidence, not verified physical measurement time.
If unchanged reports lack validated acquisition evidence, allow the entity to
expire rather than invent freshness. The last UI observation lost its connection
and yielded no multi-telegram timestamp validation. Sungrow may retain last-good
data during transient failures, including an apparently successful status.

Separate entity events are not an atomic telegram. Require both grid inputs
valid and independently fresh, with configurable bounded sample skew, before
computing surplus/recommendations. Optional inverter failure must not refresh or
invalidate otherwise independent grid inputs, but must disable AC-dependent
derivations. No PV/demand event can renew grid eligibility.

Missing mappings, `unknown`, `unavailable`, invalid/nonfinite numeric values,
wrong units, negative grid import/export, stale data or incoherent required
inputs yield explicit unavailable state, not zero or a retained recommendation.
A real numeric zero is allowed only when its own validity/freshness conditions
hold. Disconnect/auth failure clears recommendations immediately; reconnect
must reacquire eligible inputs, not restore cached decisions.

## Deferred mappings and acceptance

### Unchanged DSMR readings: acquisition evidence investigation

Read-only inspection of installed HA 2026.10.4 on 2026-11-01 found
`sensor.electricity_meter_timestamp` in the DSMR registry, currently disabled.
Its source is `P1_MESSAGE_TIMESTAMP` (meter OBIS `1.0.0`), not client arrival
time. The parser accepts a complete parsed telegram before invoking the HA
callback; invalid checksum/parse failures do not invoke that callback.
The local DSMR 5B entry has update throttling set to zero.

In `homeassistant/components/dsmr/sensor.py`, the callback distributes the same
parsed telegram to its entities. The timestamp entity precedes the power
entities in the descriptor list. Each entity publishes separately, and a
missing object can skip that entity's update. Import/export do not have
`force_update=True`. HA WebSocket `subscribe_entities` listens to
`state_changed`, not every unchanged state report. Therefore unchanged power
may produce no event while an enabled meter timestamp advances.

**The built-in timestamp is a useful diagnostic but not yet an atomic sample
contract.** It is the meter's message clock, not a proven timestamp for each
physical electrical measurement. It needs observed advancement, clock offset,
DST/timezone, replay/backward-jump and no-telegram checks. A timestamp event
must not refresh cached grid powers: it can arrive before same-telegram power
events, and it does not prove both fields existed in that telegram. Debouncing
or arbitrarily delaying events cannot supply the missing association.

Next approval gate: enable only the existing timestamp diagnostic entity,
then observe it and the existing power entities without another reader.
Enabling has not been performed. This observation can establish telegram-clock
behavior, but clients must retain the conservative expiry rules until coherent
power pairing is proven.

If the built-in surfaces cannot establish pairing, the required interface is an
explicitly approved HA-side atomic sample publisher attached to the existing
DSMR acquisition callback, not a second reader:

| Sample field | Required semantics |
| --- | --- |
| `sample_sequence` | Advances once per accepted complete telegram containing both grid powers |
| `meter_timestamp` | Parsed timezone-aware message clock; never synthesized from heartbeat |
| `received_at` | HA arrival time for that callback; distinct from meter clock |
| `import_w`, `export_w` | Validated finite nonnegative powers from that same telegram, normalized to W |
| `available` | False on transport loss or missing/invalid required fields; no substituted zeros |

Publish all fields together in one WebSocket-delivered entity state/attribute
update, including when both powers are unchanged. Clients must reject
replayed/nonadvancing samples, stale/invalid timestamps and mismatched fields,
and track arrival silence using monotonic time. A reconnect snapshot alone must
not renew eligibility; acquire a new eligible sample. An arrival timestamp alone
does not exclude upstream replay, so advancing meter time must also be validated.
This interface is proposed, not installed or supported by the current built-in
integration. A custom component/core change requires separate explicit approval,
compatibility review and tests; do not patch the runtime as a shortcut.

Do not weaken the existing 30-second stale cutoff or 300-second sustained-GO
requirement to compensate for absent unchanged-sample evidence. Monitoring-only
acceptance still requires user-configured protected HA credentials, and
daytime inverter validation remains a separate gate.

| Measurement | Actual HA entity ID | Normalized unit | Semantics/status |
| --- | --- | --- | --- |
| Current quarter-hour demand | TBD | W | Meter-specific; not instantaneous import power |
| Monthly peak | TBD | W | Meter-specific; validate month and occurrence timestamp |
| Meter timestamp/calendar | TBD | Unix ms/local fields | Validate Europe/Brussels and DST semantics |
| Import tariff 1/2 cumulative counters | TBD | Wh | Validate separate nondecreasing meter registers |
| Export tariff 1/2 cumulative counters | TBD | Wh | Validate separate nondecreasing meter registers |

Full daily/quarter-hour recommendations, demand/peak forecasts and tariff parity
remain unavailable until clock, counters, demand/peak and calendar/timezone
semantics are validated. Do not approximate them from instantaneous power,
Sungrow daily yield or incomplete counters.

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

The user approved beginning independent first-slice implementations in
[madebyq/solar-agent#99](https://github.com/madebyq/solar-agent/issues/99) and
[sujithq/solar-systray-rust#2](https://github.com/sujithq/solar-systray-rust/issues/2)
before full contract validation. This supersedes waiting to start implementation,
not the fail-safe rules or live acceptance gates. Test import/export, zero,
unchanged-report expiry, malformed units, missing/optional inputs, skew,
unavailability, disconnect/auth failure and reconnect with synthetic fixtures.
Actual physical cadence, daytime inverter checks and end-to-end behavior remain
pending; implementation approval is not permission to deploy either client.
