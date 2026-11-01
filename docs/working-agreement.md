# Working agreement

Effective: 2026-11-01. Applies to this rollout across solar-home, solar-agent and
solar-systray-rust. It does not replace each application's existing repository rules.

## One home for each kind of information

| Information | Canonical home |
| --- | --- |
| Architecture facts, investigation and uncertainty | docs/analysis.md or a focused analysis document linked from the issue |
| Phase plan, acceptance gates and prerequisites | docs/implementation-plan.md |
| Lasting decision and rationale | Numbered docs/decisions/ record |
| Overall rollout links and milestone outcome | solar-home tracking issue |
| Implementation task and acceptance criteria | Issue in the repository where code/deployment changes occur |
| Live progress | Shared GitHub Project Status |
| Implementation/review/test evidence | Linked PR and concise issue comments |
| Actual sensors, setup and recovery | Version-controlled solar-home documentation |

Do not duplicate the complete plan in multiple issue bodies. Link canonical docs.
Never treat chat history alone as the permanent record.

## Status meanings

| Status | Meaning |
| --- | --- |
| Backlog | Planned, prerequisites incomplete or not selected for execution |
| Ready | Required decisions/access/prerequisites are satisfied and work can start |
| In progress | Actively executing a bounded task |
| Blocked | Started or scheduled work cannot proceed; issue comment names blocker and next decision |
| Done | Acceptance criteria met with linked evidence; close completed implementation issue |

The tracking issue stays open until overall acceptance; it is not the daily task.
Use native sub-issues for rollout membership and native blocked-by relationships
for actual prerequisites when available. Retain human-readable dependency links.

## Starting, updating and completing work

1. Read the task, canonical plan, decisions, sensor contract and local AGENTS.md.
2. Confirm prerequisites/access; set the issue's Project Status accurately.
   On first setting In progress, set Start date only if empty; never overwrite an
   existing start. Set End date only when Done, not at an intermediate checkpoint.
3. Record a concise issue comment when scope changes, a blocker appears or a
   milestone is achieved. Include evidence and next action, not raw chat logs.
4. Update canonical documents when findings or accepted decisions change.
5. Link implementation PRs to their issues. Preserve repository review/release rules.
6. Before Done, record exact relevant checks/results, remaining limitations and
   acceptance evidence; close the task and update its Project item.

Do not mark code complete on the strength of a plan, a running build or a green
check unrelated to the exact acceptance criteria. Do not close the tracking issue
while either application or end-to-end acceptance remains incomplete.

## Decision records

Use the next numbered filename and include date, status, context, decision,
consequences and related issues. Statuses: Proposed, Accepted or Superseded.
Accepted records capture user-approved goals; they do not authorize future
deployments, credential creation, device writes, flashing, release or merge.

Keep accepted historical rationale. Supersede it with a new record rather than
silently rewriting the previous decision. Record unknowns explicitly and ask the
owner before choices with material behavioral or deployment consequences.

## Privacy and permissions

The Project is private. Do not change repository visibility or enable hosting.
Never attach access tokens, private .storage files, full runtime backups or
unsanitized device data. Credential references are not credentials.

Human review, hardware/deployment approvals and application repository release
rules remain in force. No automated agents/schedules or deployment services are
installed by adopting this agreement.
