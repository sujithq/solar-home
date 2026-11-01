# Local Home Assistant rollout analysis

Recorded: 2026-11-01. Tracking: [solar-home rollout](https://github.com/sujithq/solar-home/issues/1).

## User intent and evidence boundary

The user requested a local Home Assistant setup and BOTH Solar Agent and Solar
Systray using WebSockets, followed by durable storage of the analysis, plan,
progress and decisions in GitHub issues, a Project and repository documents.

This record synthesizes the discussion and a read-only inspection of Solar
Systray. Solar Agent's current AGENTS.md was read to verify its high-level
architecture and conventions; its complete provider/runtime/firmware paths have
not been independently traced here. HA documentation was consulted. No builds,
tests, deployments, hardware access or application implementation occurred.

At inspection, solar-home contained only a minimal README. The proposed Compose
and configuration layout was not an existing deployment.

## Recommendation

Use solar-home as the infrastructure and coordination repository. Begin with
Docker Engine and Compose on the existing Linux host, then consider Raspberry Pi
5 plus NVMe. HA owns hardware reads and history; both applications independently
subscribe to HA and retain their own decision logic.

The supplied discussion assumes existing integrations for SlimmeLezer TCP
Belgian DSMR and local Sungrow SG5.0RS Modbus. Built-in DSMR documentation supports
Belgian 5B and network proxies. The exact Sungrow integration, firmware and model
compatibility remain unverified. No custom HA integration is requested.

## Inspected Solar Systray facts

Paths below are relative to sujithq/solar-systray-rust.

| Surface | Existing implementation | Consequence |
| --- | --- | --- |
| Workspace | Rust 2024, minimum Rust 1.88; solar-core, Windows solar-tray and xtask | Put portable HA consumption in solar-core |
| Core dependencies | Chrono, IndexMap, Serde, serde_json | No WebSocket/TLS dependency in the inspected core manifest |
| Networking | Blocking TcpStream workers, Arc/Mutex runtime, atomic stop flag | A bounded blocking WebSocket worker fits existing architecture |
| Sources | SourceKind and Meter support only Mock and SlimmeLezer | No generic provider trait exists; a focused HA variant is sufficient initially |
| Runtime | DecisionEngine, PeakForecaster, DailyEnergy, NightBaseline and SungrowState | Normalize HA readings; do not import an HA GO recommendation |
| Tray feed | Direct SolarService or AgentResult | Explicit HA selection must bypass automatic Agent source choice |

Relevant core modules are `crates/solar-core/src/config.rs`, `reading.rs`,
`runtime.rs`, `service.rs`, `decision.rs`, `slimmelezer.rs`, `sungrow.rs`,
`daily_energy.rs`, `peak_forecast.rs` and `agent.rs`. Tray wiring is in
`crates/solar-tray/src/app.rs` and `settings.rs`.

### Reading contract

Reading stores validated nonnegative grid import/export in watts, a timestamp
documented as local receive Unix milliseconds, optional demand/monthly peak,
meter calendar fields and four cumulative tariff counters in Wh.

- Valid grid powers are finite and between zero and 1,000,000 W.
- Freshness rejects future samples and ages beyond decision.staleAfterSeconds,
  default 30 seconds.
- GO stability advances with reading timestamps, not the one-second menu timer.
- Missing/invalid data, source changes, backward timestamps and excessive sample
  gaps reset stability.
- Sungrow currently polls every 30 seconds and expires readings after 90 seconds.
- Daytime household use requires fresh grid data and AC output; nighttime uses
  grid import.
- DailyEnergy requires meter day/minute/offset/time and four tariff counters.
  It reports usage since its first accepted sample that day, not a persisted HA
  midnight total. It validates Belgian offsets of 60 or 120 minutes.
- Quarter-hour forecasting uses meter time, demand, peak and month information.

HA entities update separately. A PV event must not refresh grid age; a
demand/peak event must not advance grid stability. Optional field ages must not
be inherited automatically from a newer grid event.

### Configuration and source selection

Settings live in `%LOCALAPPDATA%\Solar Systray\config.json` with solar and tray
sections. Unknown configuration keys are rejected. Defaults, parsing and full
serialization are explicit. Initial solar settings can be copied from Solar
Agent companion.json; tray preference saves preserve solar edits.

app.rs always starts AgentLink/SourceChooser in the inspected implementation.
It prefers Agent data while Agent runs in solar mode and otherwise starts its
own meter/inverter workers. This preference avoids competing SlimmeLezer
connections, but conflicts with the newly requested independent HA clients.

HA mode must bypass that chooser at startup, reload and every tick. The tray
must retain local appliance control in HA mode. Existing non-HA configurations
and explicit mock behavior should remain compatible.

Agent authentication is not HA authentication: agent.rs uses a loopback-only
local token from a bounded settings-info file, redacts Endpoint Debug output,
and bounds headers, bodies and deadlines. It must not be reused as a LAN HA
client or HA credential mechanism.

### First implementation slice

Add explicit HA mode for live import/export, local surplus/GO and presentation.
Optionally add verified PV/AC mappings. Keep daily energy and quarter-hour
outputs visibly unavailable until meter semantics are mapped; do not synthesize
counter values, zero unavailable sensors or substitute an arbitrary clock.

Likely changes:

- New bounded HA protocol/cache/normalization module and declaration in lib.rs.
- config.rs: source selection, validation, defaults, credential references and
  serialization.
- runtime.rs: HA latest-reading state, invalidation and honest source diagnostics.
  Do not masquerade HA as SlimmeLezer to reuse push_reading.
- service.rs: cancellable WebSocket worker and no meter/inverter workers in HA mode.
- app.rs: authoritative HA feed, chooser bypass, local controls and source labels.
- settings.rs: HA preservation and compatible companion seeding.
- Presentation/alerts: unavailable mappings, freshness errors and recovery.
- README, Unreleased changelog, security-skill guidance and committed Cargo.lock.

Existing tests include energy.rs, service.rs, agent.rs, present.rs,
peak_forecast.rs and inverter_and_baseline.rs plus tray module unit tests and
opt-in native tray_smoke coverage. Shared JSON fixtures pin Solar Agent parity.

## Verified Solar Agent architecture and remaining inspection

AGENTS.md describes:

- daemon/: TypeScript service on Node.js 24.11+, shared solar runtime,
  USB/Wi-Fi transport and settings.
- desktop/: Tauri desktop and WebAssembly engine; bundles the daemon.
- solar/: standalone Node/browser prototype re-exporting daemon/src/solar modules.
- firmware/: Arduino firmware for supported ESP32-S3 displays.
- Existing service and standalone device paths can read SlimmeLezer independently.

Before coding, trace shared provider/runtime/configuration modules, desktop
settings, local status API and standalone firmware source selection. Determine
how configured devices receive HA-backed readings while preserving ESP32
functionality and avoiding competing direct readers. No firmware WebSocket or
daemon-relay design is accepted yet.

Respect explicit revision-aware Apply to device, opt-in startup, and the existing
standalone transition tracked in madebyq/solar-agent#3. Do not enable hosting,
flash hardware or release implicitly. Use the configured Microsoft npm/PyPI/
NuGet proxies if dependencies are required.

Documented targeted checks include daemon npm test, desktop npm test and Tauri
cargo test, solar Node tests and relevant firmware/native checks. Select exact
commands after the implementation scope is inspected.

## Shared WebSocket requirements

Authenticate at /api/websocket; correlate increasing command IDs; establish
subscriptions and a coherent initial state; reject older bootstrap/event data.
HA currently documents subscribe_entities with entity_ids, delivering initial
states and compact changes. Evaluate this against supported HA versions instead
of assuming raw state_changed events are the only subscription option.

Use a bounded mapped-entity cache, message limits, deadlines and responsive
cancellation. Reconnect with capped backoff and jitter, authenticate/resubscribe,
and rebuild coherent state. Grid failures invalidate decisions and recovery
earns stability again. Surface auth, unit, mapping and freshness errors separately.

Transport liveness, HA state/report freshness and meter measurement freshness
are different. Ping/pong only confirms connection health. last_changed alone
cannot establish unchanged measurement updates. Neither repeated cached states
nor unrelated events may manufacture advancing samples.

Separate revocable credentials per application are recommended. Decide the
protected credential mechanism jointly; never place tokens in shareable config,
logs or snapshots. Validate TLS certificates for wss. Plain ws, if used, needs
an explicit trusted-LAN decision; no automatic TLS downgrade. Do not assume
entity-scoped token permissions.

## Infrastructure proposal assessment

Start small: Compose, README, ignore rules, integrations and sensor contract.
Include .env.example only when Compose consumes its variables.

- Pin a tested image version/digest rather than relying on mutable stable.
- Run Docker Engine on Linux, not Docker Desktop.
- Host networking requires host/LAN access controls; no internet port forwarding.
- Initially HA owns ignored data/homeassistant mounted at /config.
  A separate tracked homeassistant directory is not loaded by that mount.
- Introduce tracked YAML only with explicit mount/copy ownership, preserving
  generated files and .storage. Do not edit .storage directly.
- Container has no Supervisor-managed add-ons/apps. Community integrations can
  still be installed; document the exact method/version and compatibility.
- Protect runtime backups containing credentials and history. Use supported HA
  backup or stop the container for a consistent full-directory copy; test restore.

Do not introduce MQTT, InfluxDB, dashboards or automations without a need.
HA may derive measurement templates, but GO logic stays in the apps. Never use
zero-valued template fallbacks for unavailable inputs.

## Unknowns and acceptance evidence

Actual Linux host, storage budget, network addresses, device firmware, selected
Sungrow integration, entity IDs and measured update intervals are not supplied.
Credential storage, ws/wss setup, missing Belgian fields and ESP32 source delivery
remain unresolved. Pi migration needs a later Linux+Compose versus HA OS decision.

Validate sensor units/sign/cadence/timestamps before switching either app.
Unchanged-value freshness must be demonstrated. Full parity requires demand,
peak/month, meter clock/timezone/DST and tariff counter evidence.

## Sources

- [Solar Systray source](https://github.com/sujithq/solar-systray-rust)
- [Solar Agent conventions](https://github.com/madebyq/solar-agent/blob/main/AGENTS.md)
- [Home Assistant Linux/Container installation](https://www.home-assistant.io/installation/linux/)
- [DSMR configuration and update options](https://www.home-assistant.io/integrations/dsmr/)
- [HA WebSocket API](https://developers.home-assistant.io/docs/api/websocket/)

These observations are dated; verify live code/docs again before implementation.
