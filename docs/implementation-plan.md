# Implementation plan

Recorded: 2026-11-01. [Tracking issue](https://github.com/sujithq/solar-home/issues/1)
and [Project](https://github.com/users/sujithq/projects/5).
See [analysis](analysis.md) for evidence and [decision 0001](decisions/0001-local-ha-and-independent-websocket-clients.md)
for accepted scope.

## Work packages and actual prerequisites

| Work | Issue | Depends on | Exit gate |
| --- | --- | --- | --- |
| Preserve coordination records | [solar-home#2](https://github.com/sujithq/solar-home/issues/2) | User approval, received | Committed docs, linked issues and verified Project |
| Local HA deployment | [solar-home#4](https://github.com/sujithq/solar-home/issues/4) | Chosen Linux host and explicit deployment approval | Reachable HA, persistent data, documented recovery |
| Integrations and sensor contract | [solar-home#3](https://github.com/sujithq/solar-home/issues/3) | Local deployment; authorized hardware access | Verified IDs, units, signs, timestamps/cadence and limitations |
| Solar Agent HA source | [madebyq/solar-agent#99](https://github.com/madebyq/solar-agent/issues/99) | Accepted sensor contract | Independent client, preserved decisions/device support, reviewed change |
| Solar Systray HA source | [solar-systray-rust#2](https://github.com/sujithq/solar-systray-rust/issues/2) | Accepted sensor contract | Independent client, authoritative HA mode, reviewed change |
| End-to-end acceptance | [solar-home#5](https://github.com/sujithq/solar-home/issues/5) | Both clients and validated integrations | Outage/freshness checks, isolated restore and approved cutover |

The two application packages can proceed independently once the contract is
accepted. Current readiness lives in Project Status, not this static table.
Hardware deployment is not blocked on administrative documentation completion.

## Phase 1: minimal local HA

Development checkpoint (2026-11-01): the user chose existing Windows Docker
Desktop with ordinary bridge networking for the first trial. VM/External-switch
work is paused. [Development instructions](development-home-assistant.md) cover
`compose.dev.yaml`, localhost-only access and named-volume `/config` persistence.
No HA startup or hardware cutover has been performed. This does not satisfy the
Linux/LAN, persistence or recovery exit gates above.

Choose the existing Linux host, storage and LAN access controls. Add validated
Compose, pinned HA image, runtime ignore rules and installation documentation.
For that later Linux deployment, keep HA runtime in ignored data/homeassistant
mounted at /config; the Desktop development trial uses a named volume instead.
No tracked HA YAML,
dashboard or automation is required initially. .env.example is conditional on
actual environment-variable use.

Document upgrades, rollback and protected backups. Verify persistence through
container recreation. No public hosting, router forwarding or credentials in Git.

## Phase 2: hardware and measurement validation

Stop competing readers, configure Belgian DSMR 5B through the verified
SlimmeLezer TCP path, and install/configure the exact tested Sungrow integration.
Capture sanitized import/export/night/failure samples. Populate the
[sensor contract](entity-mapping.md); do not use illustrative names as defaults.

Verify unchanged-value reports and per-entity age. Distinguish PV production
from inverter AC output. Inventory meter clock, demand/peak and tariff counters.
Decide credential storage and network transport before switching clients.

## Phase 3: independent application clients

Implement bounded authenticated WebSocket lifecycle and normalization separately
in each repo. Preserve local GO/surplus thresholds and stability, cancellation,
explicit simulation and non-HA compatibility. In HA mode no REST/local-API/direct
hardware fallback is allowed.

Solar Systray must bypass its Agent chooser at all lifecycle points, not merely
start another provider. Solar Agent must inspect and settle service/device source
delivery without unauthorized device-setting changes or competing hardware reads.

First slice: validated live grid import/export and local GO, optionally PV/AC.
Declare daily/quarter-hour outputs unavailable until their full inputs are proven.

## Required application regressions

- Authentication rejection, bounded messages/deadlines and clean cancellation.
- Bootstrap/subscription ordering, duplicate and out-of-order events.
- W/kW and Wh/kWh conversions, sign conventions, real zero versus unavailable.
- Negative/nonfinite/unsupported values, missing entities and future timestamps.
- Exact stale thresholds, distinct optional-field ages and unchanged-value reports.
- Cached readings, display refreshes, heartbeats and unrelated entity events
  cannot advance grid stability.
- Import/dips/outages reset GO; reconnect/resubscription earns a fresh stable window.
- HA selection produces no competing hardware/Agent-API connections.
- Config round trips, backward compatibility, reload and credential redaction.
- Daily/peak semantics, timezone/DST and counter reset tests when those features
  are implemented.

For Solar Systray run:

```text
cargo clippy --workspace --all-targets -- -D warnings -A clippy::approx_constant
cargo test --workspace
```

Add focused home_assistant.rs integration/fake-server coverage and preserve shared
fixtures. Opt-in Windows tray_smoke verifies actual source selection and no direct
connections. For Solar Agent, choose targeted commands from AGENTS.md after tracing
affected daemon/desktop/solar/firmware surfaces. Record command AND result.

## Phase 4: acceptance and recovery

Observe both independent clients against live HA with approved access. Exercise
HA restart/network loss/auth rejection and entity unavailability. Verify local
decisions, supported feature scope and no fallback device connections. Restore a
protected runtime backup in isolation without connecting duplicate hardware readers.

Record actual versions, observations, limitations and owner-approved cutover.
Only then close the tracking issue.

## Deferred phase: Raspberry Pi 5 and NVMe

Not yet scheduled or implemented. Decide Linux+Compose versus Home Assistant OS.
The latter is a backup/restore migration, not a Compose redeployment. Plan storage,
backup handling, access changes and rollback only after the local rollout is accepted.
