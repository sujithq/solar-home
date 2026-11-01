# ADR 0001: local HA and independent WebSocket clients

- Date: 2026-11-01
- Status: Accepted
- Tracking: https://github.com/sujithq/solar-home/issues/1

## Context

The user wants to start with local Home Assistant and BOTH Solar Agent and Solar
Systray using WebSockets. Existing direct SlimmeLezer readers can compete;
Solar Systray currently prefers Solar Agent's local status API to avoid that.
The user also approved preserving all analysis, plans, progress and decisions
in solar-home and a shared GitHub Project spanning the three repositories.

## Decision

1. Use the existing solar-home repository, not an additional coordination repo.
2. Start HA with Docker Engine/Compose on an existing Linux host.
3. HA owns physical meter/inverter reads and history using verified existing
   integrations; no custom HA integration is requested.
4. Solar Agent and Solar Systray each consume authenticated HA WebSockets
   independently. Solar Agent's local API may remain for other existing functions.
5. Retain application-side decisions, real-time surplus behavior and supported
   device functionality.
6. Explicit HA mode never silently downgrades to REST, Solar Agent's API or
   direct hardware. Stale/invalid input clears recommendations.
7. Validate actual sensor mappings, units, signs, timestamps, freshness and
   upstream report intervals before switching either application.
8. Store canonical docs in solar-home, repository-owned task issues and live
   progress in the private cross-repository Solar Home rollout Project.
9. Keep first deployment minimal. Dashboards, automations and extra services
   are deferred unless a real requirement appears.

## Consequences

HA becomes a shared dependency; outages must be visible and safe. Both apps
retain their own decision state and need independent lifecycle/freshness tests.
WebSockets remove the need for competing hardware clients but do not increase
upstream sampling cadence. Daily energy and quarter-hour parity cannot be
claimed until complete meter semantics are mapped.

Git is not a backup of HA runtime configuration/history. Protected, consistent
runtime backups and tested restore are required separately.

## Open decisions, not accepted assumptions

- Exact Linux host, HA version/digest and storage/access controls.
- Exact Sungrow integration, installation/version and SG5.0RS compatibility.
- Credential storage and trusted ws versus certificate-validated wss setup.
- Actual entity IDs and reliable unchanged-value freshness reporting.
- Availability/semantics of Belgian demand/peak/time/tariff counter fields.
- Solar Agent ESP32 source-delivery implementation in HA mode.
- Later Raspberry Pi Linux+Compose versus Home Assistant OS migration.

## Authorization boundary

This decision and coordination setup do not authorize actual deployment,
credential creation, hardware access, firmware flashing, releases or merges.
Record implementation approval and evidence in the corresponding task.
