# Solar Home

Infrastructure and coordination home for the local Home Assistant energy rollout.
This repository does not contain Home Assistant source code or either application's
source code. No deployment has been performed yet.

## Start here

- [Rollout tracking issue](https://github.com/sujithq/solar-home/issues/1)
- [Cross-repository Project](https://github.com/users/sujithq/projects/5)
- [Analysis and evidence](docs/analysis.md)
- [Implementation plan and acceptance gates](docs/implementation-plan.md)
- [Working agreement: issues, progress and decisions](docs/working-agreement.md)
- [Accepted architecture decision](docs/decisions/0001-local-ha-and-independent-websocket-clients.md)
- [Shared sensor contract](docs/entity-mapping.md)
- [Integration setup requirements](docs/integrations.md)

The Project is private; its links require access. Issue status and linked pull
requests track work; version-controlled documents preserve analysis and decisions.

## Repository responsibilities

| Repository | Responsibility |
| --- | --- |
| `sujithq/solar-home` | HA deployment, hardware integrations, history, sensor contract, recovery and rollout coordination |
| `madebyq/solar-agent` | Independent HA WebSocket client, application decisions, local API and supported ESP32 functionality |
| `sujithq/solar-systray-rust` | Independent HA WebSocket client, local decisions, Windows tray presentation and notifications |

Initially target Docker Engine on an existing Linux host. HA is the sole hardware
reader. Both clients consume HA directly; explicit HA mode has no automatic
fallback to direct hardware, REST or Solar Agent's local API.

## Current scope

Only planning records and work tracking are implemented. Planned infrastructure
is a small Compose deployment with persistent, Git-ignored runtime data. No actual
sensor IDs, device addresses, credentials or tested deployment version have been
supplied. Do not treat example entities as working configuration.

Never commit tokens, `.env` secrets, HA `.storage`, databases, runtime backups or
private device captures. Existing applications retain their own repository rules.
