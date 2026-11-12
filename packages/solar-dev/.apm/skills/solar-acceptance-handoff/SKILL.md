---
name: solar-acceptance-handoff
description: Prepare Solar feature handoffs, user test steps, evidence levels, unverified gates, caveats, and issue updates.
---

Use at implementation milestones, local/device rollout, acceptance review, and
release handoff. Report only completed, scoped evidence; unknown is not passed.
Use this compact template:

```markdown
## What changed
Behavior and scope, with the related issue and commit/PR when they exist.

## How to see or test it
Prerequisites, approved environment, exact user-visible steps, expected result,
and any remaining approval boundary. Distinguish mock from live data.

## Evidence
| Level | Result and scope | Artifact or attributable observation |
| --- | --- | --- |
| Implemented | Verified / not verified / not applicable | Diff |
| Committed | ... | Commit |
| Tests passed | ... | Completed command/check and result |
| Built | ... | Build result and artifact |
| Installed locally | ... | Installation and version confirmation |
| Installed on device | ... | Device installation verification |
| Visually verified | ... | Saved screenshot/video, or explicitly observation only |
| Accepted by owner | ... | Explicit scoped owner decision |
| PR opened | ... | PR |
| Merged | ... | Forge merge record |
| Released | ... | Published release and artifact |

## Not verified and caveats
Remaining acceptance gates, unavailable evidence, limitations, and next action.
```

No saved screenshot file means no saved screenshot evidence. A build does not
prove installation; device presence does not prove measurements; a PR does not
prove merge/release. Preserve issue/sub-issue and blocked-by relationships.
Update related issue and parent summaries on material changes when authorized.
Set Start date on first In progress only if empty, never overwrite; set End date
when Done (it may change for a later completion). Do not close the parent while
end-to-end acceptance is incomplete.

Repository artifacts and GitHub comments must exclude personal data, usernames,
profile paths, hostnames, LAN addresses, tokens, device identifiers/ports, and
private implementation details. Use sanitized evidence, never raw captures.
Nothing in this template authorizes installation, flashing, merge, or release.
