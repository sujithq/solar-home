---
name: solar-ha-contract
description: Add or change HA-sourced Solar values, entity mappings, units, signs, freshness, provenance, and cross-consumer behavior.
---

Use before adding or changing any HA-derived value or its eligibility rules.
Read [the bundled contract](references/contract.md) and the
[canonical entity mapping](https://github.com/sujithq/solar-home/blob/main/docs/entity-mapping.md).
Treat deployment examples as configurable mappings, not universal live facts.

1. Define the role, configurable entity ID, source unit, normalized unit,
   conversion, sign, valid range, and provenance. Record unknowns explicitly.
2. Define acquisition evidence, measurement timestamp, session/sequence where
   applicable, independent receive age, staleness window, coherence/skew limits,
   replay handling, and unavailable/stale/reconnect behavior. Connection health
   and repeated cached states cannot renew freshness.
3. List impacts on HA configuration, desktop, device firmware, and tray clients:
   mapping/configuration, authenticated WebSocket subscriptions, parsing,
   decisions, UI labels, diagnostics, tests, and compatibility. Mark each
   consumer affected, unaffected with rationale, or not yet inspected.
4. Update the canonical mapping in Solar Home as part of the change, or arrange
   a linked Solar Home change if working in a consumer checkout. Do not claim
   this step complete until that change exists. Keep private implementation
   detail in its own repository; public docs contain sanitized contracts only.
5. Test valid values and zero, wrong units/signs, missing/unavailable/nonfinite
   input, stale/repeated/replayed measurements, incoherent grid pairs,
   auth failure, disconnect/reconnect, and optional-data failure. Keep pure
   contract tests separate from approved live acquisition evidence.
6. If user-visible or decision-affecting, use `solar-feature-spec` and obtain
   approval before implementation. Handoff with `solar-acceptance-handoff`.

Do not change existing freshness thresholds without evidence and approval.
No step authorizes live HA changes, new hardware readers, or device writes.
