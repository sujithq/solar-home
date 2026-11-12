# Solar development primitives

Shared, public-safe Copilot agents and skills for HA configuration, desktop
clients, device firmware, and tray applications. Repo-specific implementation
procedures belong in each consuming repository.

| Primitive | Purpose |
| --- | --- |
| `ha-contract-reviewer` | Read-only HA contract, freshness, and consumer regression review |
| `solar-acceptance-reviewer` | Read-only evidence, rollout status, and acceptance review |
| `solar-ha-contract` | Add or change an HA-sourced value end-to-end |
| `solar-feature-spec` | Specify decision rules and obtain approval before implementation |
| `solar-acceptance-handoff` | Report evidence without overstating delivery or acceptance |
| `solar-environment-preflight` | Read-only checkout, toolchain, HA, and device readiness checks |

## Consume with APM

Requires an APM CLI supporting subdirectory packages (validated with 0.29.0).
From an isolated consumer checkout, install:

```sh
apm install sujithq/solar-home/packages/solar-dev --target copilot
```

Or declare this in the consumer's `apm.yml`, preserving its other dependencies:

```yaml
name: solar-consumer
version: 0.1.0
targets: [copilot]
dependencies:
  apm:
    - sujithq/solar-home/packages/solar-dev#<reviewed-commit-or-tag>
```

Replace the placeholder with a real reviewed ref, then run `apm install`.
The exact unpinned dependency is `sujithq/solar-home/packages/solar-dev`.
The manifest version does not create a Git tag: pin a Git ref and retain the
consumer lockfile for reproducibility. Remote installation works only after this
directory exists on the default branch or the chosen published ref.

APM deploys agents into `.github/agents/` and skills into `.agents/skills/`. Inspect
the installation diff; do not use `--force` to replace hand-written content.
No root manifest or generated files are added to this repository. For local
validation, copy this package into a scratch directory, install with
`--target copilot`, run `apm audit --ci --no-policy`, and pack there with
`apm pack --format claude-plugin --archive --offline`. Despite its format name,
this bundle can be installed into Copilot with `--target copilot`; it preserves
both agents and skills. APM 0.29.0's portable `agent-plugin` format does not
support agents, and its legacy `apm` format produces an empty bundle for these
own-project primitives. Local-path dependencies can exercise the consumer loop
without publishing, but cannot themselves be packed; pack the package directory.
No package license has been declared; APM reports `NOASSERTION` in the SBOM.

The skills bundle their own references. The canonical deployment mapping remains
[the Solar Home sensor contract](https://github.com/sujithq/solar-home/blob/main/docs/entity-mapping.md);
review it at the same pinned ref when validating a historical package.
These primitives grant no deployment, hardware, account, merge, or release
authorization. They contain no runtime endpoints, credentials, or device values.
