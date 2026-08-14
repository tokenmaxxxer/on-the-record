---
status: proposed
files:
  - docs/issue-1510/reports/execution-observation.md
---

## Request

Issue #1510 asks this session to write the execution-observation record
for the commits landed on branch `issue-1510/implementation` (PR #1513) —
per docs/issue-1510/reports/execution-observation/survey.md, no observation
record exists yet for that PR.

## Constraints

- This role never edits the observed artifact: no changes to
  `on-the-record/`, `spawn.py`, `tests/`, or `docs/issue-1510/reports/implementation*`,
  `docs/issue-1510/proposals/heartbeat-cadence-widen.md` — findings return
  only through this role's own record file.
- Phase 2 (writing docs/issue-1510/reports/execution-observation.md) opens
  only on an Approve for `issue-1510/execution-observation` specifically —
  the existing `APPROVE issue-1510/implementation` comment authorizes the
  observed role's own phase 2, not this one.

## What will be done (once phase 2 opens)

Three verdict levels will be rendered in docs/issue-1510/reports/execution-observation.md,
each against evidence already located in the phase-1 survey:

- **outcome** — recomputed as the worst case among this record's own
  step-level results (never a standalone summary), checked against
  `gh pr diff 1513` and the issue's three Acceptance line items.
- **trajectory** — three named pass/fail/not-applicable checks: scouted-
  when-required (per the observed role's own
  docs/issue-1510/reports/implementation/survey.md skip record),
  surveyed-before-proposing (ordering of the observed role's own survey vs.
  proposal file), approved-by-human (the `APPROVE issue-1510/implementation`
  comment timing and account, per the survey's Approval-path note).
- **step** — at minimum the candidate finding already logged in the
  survey's Off-diff observation section: `on-the-record/hooks/stop-poll-rearm.sh:48`
  still reads `MONITOR_LIVENESS_STALE_SECONDS:-180`, unscaled, despite
  `on-the-record/hooks/directive.sh`'s own comment stating the convention
  is duplicated verbatim there — subject/test/result/assertedBy in the
  spec's per-claim vocabulary, evidence mode `read` (this session read the
  file directly, not the observed role's own claim about it).

## Out of scope

- Re-running the observed PR's tests or any of its code — evidence is
  limited to the diff, commits, and the observed role's own record, per
  this role's standing prohibition.
- Filing an issue for the stop-poll-rearm.sh gap — any confirmed
  deficiency goes into this role's own record only; the human decides
  whether to file it.

## How you'll know it worked

docs/issue-1510/reports/execution-observation.md exists, committed on this
branch, with the independence statement preceding all verdict language,
all three verdict levels addressed (including "not applicable, because X"
where a level does not apply), every verdict sentence carrying an adjacent
citation, and loop_state set per the record-fields terminal-state table.
