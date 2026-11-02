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

## Optional inverter display: acquisition limitations

Read-only inspection on 2026-11-02 confirmed both mapped AC/DC entities are
enabled, with unit `W`, device class `power`, state class `measurement` and
`source: modbus`. Installed Sungrow 6.7.0's SG-RS map defines AC
`total_active_power` as signed 32-bit register 5030, scale 1 W, and DC
`total_dc_power` as unsigned 32-bit register 5016, scale 1 W. These are source
definitions, not independent register reads or validation of inverter sign,
topology, calibration or daytime operation. Do not apply absolute value to hide
an unexpected AC sign, substitute DC for AC, or infer household consumption.

Neither entity exposes a successful-acquisition timestamp/sequence. The
coordinator's `_last_successful_update` is an internal monotonic value, not an
entity attribute available to WebSocket clients. Its Modbus-only path returns
last-good `self.data` after a read error/timeout while within
`AVAILABILITY_GRACE_SECONDS = 900` (15 minutes). Consequently, availability,
connectivity, a coordinator refresh or Modbus Status alone cannot certify that
the displayed power came from a newly successful register read.

A bounded 70-second observation of the existing HA recorder found no new AC/DC
states; the latest records were about 396 seconds old and zero-valued. This does
not prove stopped polling: unchanged readings need not generate state changes.
It also does not validate fresh physical zeros. Low-light/sleep, unchanged valid
values and retained data are not distinguished by that evidence. No raw powers,
device identifiers or runtime sample timestamps are preserved here.

First-slice clients may display a valid last-known HA value with an explicit
HA-update-age/provisional freshness label, but initial/reconnect snapshots,
heartbeats, unchanged cached reports and unrelated entities must not renew its
age. Without validated unchanged-acquisition evidence, allow optional AC/DC to
expire using their own configured bounds and show unavailable/stale rather than
zero. This conservative expiry can hide genuinely unchanged production until a
new qualifying update; it is preferable to claiming physical freshness.
Optional inverter failure/expiry must not disable independent atomic-grid
monitoring or grid-only decisions. Household derivation and full inverter
acceptance remain unavailable until their separate prerequisites are met.

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
`sensor.electricity_meter_timestamp` in the DSMR registry, initially disabled.
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

The user subsequently enabled that existing diagnostic manually; a filtered
registry check confirmed it is enabled. Bounded UI observation including a
35-second wait showed only the same relative timestamp label, without an
absolute timestamp or separately observed power events. Opening its details
did not expose a usable detail panel. This does not prove advancing telegrams,
stopped acquisition or coherent power pairing. No additional toggle or restart
was performed. Clients must retain conservative expiry until usable
telegram-clock and same-sample evidence is established.

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
### Approved build-time atomic entity implementation

The user approved implementing the acquisition-side change. It is packaged in
`build/homeassistant` and was deployed with explicit approval on 2026-11-01.
The Dockerfile adds an entity
to the pinned built-in DSMR integration's existing accepted-telegram callback.
`patch_dsmr.py` refuses any source not matching the reviewed SHA-256 of HA
2026.10.4's DSMR sensor module. This is a maintained downstream core patch,
**not an upstream-supported hook**: every HA/source change requires review,
new tests and an explicitly updated checksum; never bypass the guard.

The observed enabled entity ID is `sensor.dsmr_atomic_grid_sample`. HA's registry may
choose a suffixed ID, especially with multiple meters; discover and configure
the actual entity per client. Its numeric state is `sample_sequence`.
Attributes in the same state update are `schema_version: 1`, `session`,
`sample_sequence`, `meter_timestamp`, `received_at`, `import_w` and `export_w`.
Both times are UTC ISO-8601 with offsets. `received_at` is the time the accepted
telegram is processed by the existing callback, not sensor measurement time.
The random `session` token identifies entity lifecycle, not a device/person.
Sequence increases only for accepted complete samples and resets with a new
session after entity reload/restart; each meter has a separate entity.

Both power objects and an aware meter datetime must be present in the same
telegram. Only finite nonnegative W/kW values are accepted, with kW multiplied
by 1000. Source clock age must be below 30 seconds and no more than 5 seconds
ahead of HA. Repeated/backward meter timestamps fail closed; recovery requires
a newer acceptable meter time rather than silently resetting replay history.
Multiple messages with the same second-resolution timestamp are therefore
conservatively rejected. Meter resets/clock correction need diagnosis, not a
relaxed stale rule.

On invalid/partial/transport-loss input, the entity becomes `unavailable` and
attributes contain only schema/session/reason, never cached powers. On silence,
a timer expires at the earlier of 30 seconds after callback receipt or source
age reaching 30 seconds. Timer cancellation follows entity unload/replacement;
it opens no connection. The adapter uses `force_update`, and sequence changes
also make valid unchanged-power samples visible to `state_changed` subscribers.
Expiry and rejection are logged by reason without telemetry or identifiers.

Clients must validate numeric state equals the attribute sequence, schema,
finite powers and timestamp bounds; track increasing sequence and meter time
within a session. Session change/disconnect/invalid data resets sustained GO.
Initial/reconnect snapshots may be shown with their original ages for monitoring,
but cannot count as newly received acquisition evidence or resume GO. Wait for
a newer live eligible event after subscribing. Client monotonic silence tracking
is still mandatory even when HA stops before publishing `unavailable`.
The existing separate power/timestamp entities remain usable for display, not
as a substitute for this atomic eligibility payload.

Synthetic executable tests cover unchanged zero, unit/timezone normalization,
partial/invalid/stale/replay data, session/reconnect behavior, adapter expiry
and recovery, and parser checksum-error suppression. Build-time tests check
the exact source before applying the patch. No hardware fixture or raw telemetry
is used. The image still contains the scoped Sungrow dependency exception and
runtime Compose Microsoft-only defaults.

The approved main build and rollout are recorded in
[run 41339763651](https://github.com/sujithq/solar-home/actions/runs/41339763651);
the [development guide](development-home-assistant.md) gives image/digest and
rollback references. Build tests and checksum guard passed, then only HA was
recreated with the original named `/config` volume. No live source patch,
configuration edit, new credential or second meter reader was used.

A bounded 40-second read-only observation of the existing HA recorder found
36 complete valid atomic states spanning 35 seconds, with one session and
strictly advancing sequence and meter timestamps. Three adjacent pairs retained
both power values unchanged while publishing new samples; all 35 adjacent pairs
retained unchanged export. Source clock age at callback receipt was about
13.2 seconds, within the cutoff, not proof of meter clock synchronization or the
physical age of each electrical measurement. Only aggregate evidence is recorded
here; no runtime session token, raw powers or sample timestamps are persisted.

This establishes actual emitted HA states, not just source/registry presence.
The browser state page remained blank, so frontend/client WebSocket reception
was not verified. Live transport interruption, silence expiry and restart/session
recovery remain untested; synthetic tests do not complete these acceptance gates.
No application branch was merged or deployed.

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
