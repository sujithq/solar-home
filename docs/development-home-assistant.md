# Home Assistant development on Docker Desktop

Checkpoint: 2026-11-01. [Deployment issue #4](https://github.com/sujithq/solar-home/issues/4).
Configuration prepared; no image pulled, container started, account created or
hardware connected by this slice. Full deployment acceptance remains pending.
That describes the original preparation slice, not the later running instance.
The dependency-source checkpoint below records the subsequent observed state.

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

The blocks below are templates, not a request to run commands now. Follow the
[manual command checkpoint rule](../README.md#privacy-and-manual-command-checkpoints):
when the specific step is ready, receive its explanation and copy/paste command
in chat. Keep resolved local paths and personal values out of repository files
and comments. Use PowerShell from the checkout containing this file; the neutral
`<solar-home-checkout>` placeholder is resolved only at that manual chat step.

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

### Microsoft-only Python dependencies: pending recreation

Read-only observation on 2026-11-01 confirms running HA Container 2026.10.4,
configured HACS 2.0.5 and the downloaded Sungrow 6.7.0 manifest in `/config`.
Downloading the integration is not proof that its Python requirements installed
or that its local Modbus setup works. The declared requirements are
`sungrow-isolarcloud==0.20.0` and `pymodbus>=3.6.0`.

The running image's HA dependency installer uses `uv pip install`, inherits its
environment, and can retry without failing extra indexes. The image supplied a
public HA wheel extra index for both pip and uv. `compose.dev.yaml` now explicitly
sets the Microsoft PyPI proxy as both pip's index and uv's default/legacy index:
`https://packagefeedproxy.microsoft.io/pypi/simple`. Empty extra-index,
additional-index and find-links settings override inherited sources.
`PIP_CONFIG_FILE=/dev/null` disables pip configuration files; `UV_NO_CONFIG=true`
disables uv configuration discovery. Do not add a public fallback if the proxy
fails or lacks a compatible distribution. Report the sanitized error and pause.

This constrains index-based dependency installation; it is not a network
firewall and does not rewrite explicit URL requirements. The downloaded Sungrow
manifest uses package specifiers, not direct URL requirements. Recheck future
integration requirements and installer behavior before upgrading.

These Compose settings do not change an already-created container.
An HA UI restart or `docker compose restart` retains its old environment.
After the user approves the recreation checkpoint, use PowerShell from the
checkout containing the updated file. This command is a template; provide its
copy/paste form in chat only when that specific manual step is ready:

```powershell
docker --context desktop-linux compose -f .\compose.dev.yaml up -d --no-deps --pull never --force-recreate homeassistant
```

Recreation retains `solar-home-ha-dev_homeassistant-config` at `/config`,
including HACS and downloaded integration files. Keep the project name and never
use `down -v`. `--pull never` uses the existing image; if it is absent, stop rather
than changing the image/version implicitly. HA and any active DSMR reader inside
HA are briefly unavailable during shutdown/startup. Do not start a competing
meter reader or connect/configure the inverter in this checkpoint.

After recreation, verify only the dependency-source environment values, HA
startup and whether dependencies load without source errors. Existing image or
cached packages may already satisfy requirements; do not claim a successful proxy
download without evidence. Compose validation and an intercepted installer call
verify configuration/argument propagation only, not proxy package availability,
actual installation, runtime compatibility or inverter communication.

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

## Manual GitHub Actions image build

The user chose to retain Sungrow 6.7.0, not downgrade to 6.6.0. Its exact
`sungrow-isolarcloud==0.20.0` requirement was absent from the observed Microsoft
feed. The authorized official PyPI attempt from Docker Desktop failed at the
artifact CDN TLS handshake. A GitHub-hosted build is a separate download path;
success there is not yet verified.

`.github/workflows/home-assistant-build.yml` is **manual and build-only**. It has
no push, pull-request or scheduled trigger, registry login, Azure resources,
image publication, deployment or runtime configuration access. Its Linux amd64
runner builds `build/homeassistant/Dockerfile` from the same HA 2026.10.4 tag as
Compose. That tag is not immutable; record the resolved base digest after a
successful build before preparing publication.

The build uses HA's own dependency installer with official PyPI as the sole
index for this approved installation and its required transitive dependencies.
Extra indexes, find-links and configuration discovery are disabled. Constraints
pin every existing base package: a dependency conflict fails the build rather
than upgrading HA's packages. Version and package-import checks must pass.
The source exception is process-scoped; it does not change Compose's durable
Microsoft-only defaults. No TLS bypass, alternate mirror or fallback is used.

The image contains the Python dependency, **not the Sungrow integration**.
HACS's existing 6.7.0 component stays in the separate persistent `/config`
volume. The narrowly allowlisted build context excludes configuration, backups
and credentials. Do not expand it to the checkout or export `/config` into an
image. Imports do not configure HA or establish inverter connectivity.

**Next manual checkpoint:** review these files, then explicitly approve running
the workflow. GitHub requires the workflow to exist on the default branch before
manual dispatch is available; a feature-branch push alone does not enable the
Actions Run workflow control. Merging/promoting the workflow is a separate
repository checkpoint, not permission to deploy. At that ready step, chat will
provide the exact UI guidance or PowerShell command, selected ref, effects and
expected result. Do not run Docker builds on the development PC for this check.

A successful run leaves the test image only on its temporary runner; no
downloadable image is retained. Review sanitized success/failure evidence before
adding Azure Container Registry publication with separately approved Azure
scope and OIDC permissions. ACR storage, runner costs where applicable, image
architecture, digest selection and rebuilds for future HA/dependency upgrades
need review. Pulling an image and recreating HA remain separate approval gates,
preserving the named volume and allowing for a brief interruption to HA/DSMR.
No workflow preparation or image-build success resolves issue #4's hardware,
persistence, backup or production acceptance checks.

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
