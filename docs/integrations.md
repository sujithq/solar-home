# Integration setup requirements

Status: Planning only; no integration has been installed or tested.
Deployment: [solar-home#4](https://github.com/sujithq/solar-home/issues/4).
Integration validation: [solar-home#3](https://github.com/sujithq/solar-home/issues/3).

## Belgian DSMR / SlimmeLezer

Use HA's built-in DSMR Smart Meter integration with Belgian 5B and the verified
serial-to-network transport. Confirm actual SlimmeLezer firmware, host/port and
owner-authorized access rather than assuming ESPHome/native API or telnet.

Stop Solar Agent/device/Systray competing direct readers before HA takes over.
HA documentation exposes a time-between-updates option; zero requests entity
updates whenever meter data arrives but increases event load. Measure actual
cadence and unchanged-value freshness rather than blindly choosing a value.

See [DSMR documentation](https://www.home-assistant.io/integrations/dsmr/).

## Sungrow SG5.0RS

Select and document the exact existing community integration only after checking
model/firmware compatibility, local Modbus behavior, installation procedure and
tested version. Community integrations may require custom_components installation
and/or YAML; do not claim all Sungrow integrations are UI-configured.

Do not add a second inverter poller while HA owns reads. Verify PV/DC versus
AC output meanings, units, status and sampling intervals.

## Configuration, access and backup

Initially HA manages /config: a named Docker volume for
[Desktop development](development-home-assistant.md), or a Git-ignored runtime
directory for the later Linux deployment. UI-created integration
entries live in .storage, not automatically in tracked YAML. Never edit .storage
directly or commit it. A tracked homeassistant directory is ineffective unless
an explicit copy/mount procedure makes it available in /config.

Home Assistant Container on Linux does not have Supervisor-managed add-ons/apps.
Install only needed integrations and track their versions and recovery procedure.

Restrict HA LAN access, do not expose it through router forwarding, and settle
credential storage/TLS before client configuration. Use separately revocable
credentials; never include token values in issue comments or fixtures.

Back up configuration, .storage, history and community integration versions.
Use supported HA backups or stop the container before copying all /config data;
protect backups and verify restoration without duplicate live hardware reads.

Complete [entity-mapping.md](entity-mapping.md) before either client switches.
