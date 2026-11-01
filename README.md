# Solar Home

Infrastructure and coordination home for the local Home Assistant energy rollout.
This repository does not contain Home Assistant source code or either application's
source code. No deployment has been performed yet.

## Start here

- [Rollout tracking issue](https://github.com/sujithq/solar-home/issues/1)
- [Cross-repository Project](https://github.com/users/sujithq/projects/5)
- [Analysis and evidence](docs/analysis.md)
- [Implementation plan and acceptance gates](docs/implementation-plan.md)
- [Docker Desktop development checkpoint](docs/development-home-assistant.md)
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

The always-on deployment targets Docker Engine on Linux. The user selected
existing Windows Docker Desktop for the first development trial; VM and External
switch setup are paused. See the development checkpoint before starting anything.
HA is the sole hardware
reader. Both clients consume HA directly; explicit HA mode has no automatic
fallback to direct hardware, REST or Solar Agent's local API.

## Current scope

Planning records, work tracking and `compose.dev.yaml` are implemented.
The development file publishes localhost port 8123 and persists `/config` in a
named Docker volume outside the checkout. HA 2026.10.4 is selected, not yet tested
in a running deployment. Startup requires the next user checkpoint. No actual
sensor IDs, device addresses or credentials have been supplied.
Do not treat example entities as working configuration.

Never commit tokens, `.env` secrets, HA `.storage`, databases, runtime backups or
private device captures. Existing applications retain their own repository rules.

## Privacy and manual command checkpoints

Do not persist personal names, OS usernames, user-profile paths, personal email
addresses, hostnames, machine identifiers or credentials in tracked files,
examples, commit messages/metadata, issues, comments, reviews or release notes.
Use neutral placeholders and synthetic test identities instead. Canonical GitHub
owner/repository links and necessary public account attribution are distinct from
incidental personal data. Use a GitHub noreply address and neutral contributor
name for commits; never copy a local Git identity into repository history.

Repository command blocks are templates, not permission to execute. Keep local
paths as `<solar-home-checkout>` and sensitive inputs as neutral placeholders.
When a manual step is ready, guidance in chat must explain its purpose, required
folder, effects, approval boundary and expected result. Only then provide the
copy/paste command for that specific step in chat, resolving local values there
if needed; never save those resolved values back into a file or GitHub comment.
Do not include credentials in command literals, even in chat.

Proceed one checkpoint at a time: configuration review, approved startup, UI
observation, approved onboarding, then separately approved hardware access and
recovery checks. Record sanitized results in the issue, not personal command
values or raw logs. Preparing a file does not authorize running it.
