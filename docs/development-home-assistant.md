# Home Assistant development on Docker Desktop

Checkpoint: 2026-11-01. [Deployment issue #4](https://github.com/sujithq/solar-home/issues/4).
Configuration prepared; no image pulled, container started, account created or
hardware connected by this slice. Full deployment acceptance remains pending.

## Scope and configuration

Use the user's existing Windows Docker Desktop Linux daemon (`desktop-linux`).
No Linux VM, Hyper-V External switch or Docker/WSL network changes are needed for
this development trial. VM and External-switch preparation are paused.

`compose.dev.yaml` defines one Home Assistant service on Compose's default bridge
network. It publishes only `127.0.0.1:8123:8123`, sets `TZ=Europe/Brussels`, allows
60 seconds for clean shutdown, and has no privileged mode, device mounts,
D-Bus mount, host networking or extra services. `restart: "no"` deliberately
avoids restarting this trial automatically with Docker Desktop; start it manually
when needed. It still uses the host's CPU, RAM and Docker disk while running.

The Compose project name `solar-home-ha-dev` keeps the named volume
`solar-home-ha-dev_homeassistant-config` stable when the checkout folder changes.
Do not override the project name with `-p` or `COMPOSE_PROJECT_NAME`: that selects
a different volume and can appear to lose configuration. Separate checkouts with
this project name manage the same development instance; do not run them in parallel.
There is no fixed `container_name`.

HA owns all of `/config` inside that named Docker volume, including generated
YAML, `.storage`, credentials, databases and future community integrations.
Nothing in a tracked directory is automatically loaded into HA. No `.env` or
`.env.example` is consumed or needed. `.gitignore` protects common local runtime
exports and future bind-mounted data, but is not permission to put secrets in Git.

The image is pinned to `ghcr.io/home-assistant/home-assistant:2026.10.4`, the
[latest stable Core release observed on 2026-11-01](https://github.com/home-assistant/core/releases/tag/2026.10.4).
It is a selected release, not yet a tested deployment. A version tag prevents
automatic drift to the next release but is not an immutable digest.

## Next checkpoint: start only after user approval

Use PowerShell from the checkout containing this file. Replace
`<solar-home-checkout>` with that checkout's local folder before running:

```powershell
Set-Location '<solar-home-checkout>'
docker --context desktop-linux compose -f .\compose.dev.yaml config --quiet
```

Configuration validation does not pull an image, create a volume or start HA.
After the user approves the startup checkpoint, run:

```powershell
docker --context desktop-linux compose -f .\compose.dev.yaml up -d homeassistant
docker --context desktop-linux compose -f .\compose.dev.yaml ps
```

`up` downloads the pinned image if absent and creates the project network,
container and persistent named volume. If it fails because port 8123 is occupied,
stop and report the error; do not stop another container or change its port.
Open <http://localhost:8123> on Windows and allow time for first startup.
Report whether the onboarding page appears before proceeding to account creation.
If it does not appear, inspect locally:

```powershell
docker --context desktop-linux compose -f .\compose.dev.yaml logs --tail 80 homeassistant
```

Do not paste unsanitized logs, tokens, private addresses or account details into
issues. Do not connect SlimmeLezer/Sungrow, change devices or stop existing readers
until a separate user-approved hardware checkpoint.

## Later checkpoints: persistence, backup and upgrades

For a routine pause after startup:

```powershell
docker --context desktop-linux compose -f .\compose.dev.yaml stop homeassistant
```

To resume, use the same `up -d homeassistant` command and project name.
`stop` and ordinary `down` retain the named volume. **Never use `down -v`,
delete this volume or prune volumes**: doing so can destroy HA configuration,
credentials and history. A Docker Desktop reset/uninstall can also lose local
volumes. Git is not a runtime backup.

After approved onboarding, record a harmless setting, recreate this service with
`up -d --force-recreate homeassistant` using the same file, and confirm the setting
survives. Also inspect the volume attachment and deployed image digest locally.
These persistence and version checks have not run yet.

Before any upgrade or migration, create a supported HA backup from its UI,
download it to protected storage outside Git and outside Docker's disk, and
retain its recovery/encryption information securely. Include configuration,
history and installed integration versions; confirm the backup's actual contents.
Alternatively, stop HA cleanly before a complete `/config` volume copy; never
copy a live database as if it were consistent. Copy/export tooling and an
isolated restore procedure require their own approved checkpoint.

Choose an explicit newer stable version, read its release notes and compatibility
requirements, record the currently deployed version/digest and protected backup,
then review the Compose image change. Only with approval pull that version and
recreate this service using the same volume. Record observed results in issue #4;
do not use `stable`/`latest` or unattended upgrades.

Rollback may require the pre-upgrade backup as well as the previous image:
database/config migrations can make an image-only downgrade unsafe. Verify
restoration in isolation without duplicate hardware readers before claiming
recovery works. Backup export, restore and upgrade/rollback are not yet verified.

## Development limitations and later Linux/Pi deployment

The [official Container installation guide](https://www.home-assistant.io/installation/linux/)
requires Docker Engine on Linux, not Docker Desktop. This Desktop bridge-network
configuration is a bounded development trial, not that officially documented
deployment or proof of issue #4's full production acceptance.

Local UI and future WebSocket client development are in scope. Manually configured
outbound LAN connections may work through Desktop NAT but remain untested.
Multicast discovery, USB/Bluetooth access, VPN/firewall behavior and access from
other LAN machines are not guaranteed. The loopback publication intentionally
does not offer a LAN endpoint. No router forwarding or public hosting is allowed.
Container installations have no Supervisor-managed add-ons/apps; community
integrations require their own compatibility and installation checks.

Both future application clients, including diagnostics, use HA WebSockets only
at `/api/websocket`; there is no REST, Agent-API or direct-hardware fallback in
HA mode. This slice implements no clients, credentials or sensor mappings.
All actual entity IDs remain pending in [the sensor contract](entity-mapping.md).

For the always-on Linux/Pi path, choose the host/OS, storage and LAN controls
separately. Linux Docker Engine + Compose needs a reviewed deployment file and
appropriate host-network/device/access decisions; do not reuse this loopback-only
Desktop file as a production recipe. Linux may use ignored `data/homeassistant`
at `/config` as originally planned, with an explicit backup/restore transfer from
the development volume. Raspberry Pi Home Assistant OS is instead a supported
backup/restore migration, not a Compose redeployment. Choose between those paths
later and verify reachability, persistence and isolated recovery before Done.
