---
name: solar-feature-spec
description: Specify user-visible Solar features, thresholds, indicator states, precedence, stale-input neutrality, and approval before implementation.
---

Before implementing a user-visible or decision-affecting feature:

1. Define scope, outputs, and non-goals. List every symbol, unit, source entity
   or setting key, default policy, range, and freshness requirement. Resolve
   unknown settings explicitly; never invent live values.
2. Produce an ordered threshold/rule table and Mermaid state diagram. Specify
   precedence, equality at every boundary, validation, and neutral behavior for
   missing/stale/invalid inputs. Cover disconnect and reconnect eligibility.
3. Identify double-counting, clock/coherence assumptions, and whether values are
   measured or derived. State what must NOT change: physical GO, scheduling,
   control, transport, reader ownership, and existing staleness windows unless
   separately approved.
4. Give boundary and transition acceptance cases, including conflicting rules.
   Label instantaneous calculations as such, not verified tariff demand.
5. Present the specification and request explicit user approval. Stop before
   implementation until approval is recorded; a skill invocation, generated
   spec, reviewer opinion, or prior unrelated approval is not approval.
   If requirements change materially, return for approval.

Use [the worked example](references/indicator-example.md) as a structural guide,
not an approved feature or a replacement for the consuming repository's rules.
Save a requested specification/diagram as a reviewable artifact; preserve
privacy and link it from the related issue when authorized.
