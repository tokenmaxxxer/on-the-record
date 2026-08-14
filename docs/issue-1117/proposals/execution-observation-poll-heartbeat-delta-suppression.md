---
status: proposed
files:
  - docs/issue-1117/reports/execution-observation.md
---

# execution-observation of PR #1122 (issue #1117 delivery) — proposal

## Request

Issue #1117 assigns this role to observe whether PR #1122's
phase-1→phase-2 execution of issue #1117 was sound, by reading its actual
artifacts (diff, commits, its own record) — never by re-executing the
observed task.

## Constraints

- Never edit anything under the observed role's `src/`, `test/`, or
  `docs/issue-1117/` paths outside this role's own report path
  (`docs/issue-1117/reports/execution-observation.md`).
- Never re-run the observed role's code as a way of producing evidence —
  live re-execution of the *cited test suites* (already part of the
  observed record's own acceptance surface) is admissible; re-implementing
  or re-authoring the observed feature is not.
- Every verdict-bearing sentence must name its source (commit SHA,
  file:line, or PR comment URL) directly adjacent to the verdict.
- The independence statement (this role did not author or edit the
  observed artifact) must precede any verdict language in the record.

## What will be checked, and against what evidence

This is a proposal — no verdict is rendered here or anywhere before phase 2
opens. Phase 2's record will check all three named verdict levels:

- **outcome** — did PR #1122 land what issue #1117 asked for. Checked
  against: the observed record's own `## Verification run` section
  (`docs/issue-1117/reports/implementation.md`, commit `ff8bdf3a`), cross-
  checked by re-running the same two commands it cites
  (`gates/test_poll_heartbeat_delta.py`,
  `on-the-record/monitors/test_poll_heartbeat.py`) live against the current
  tree this session, per the recomputation rule (worst case among the cited
  step-level results, scoped to what #1122 itself delivered and was
  checked against at its own merge time — not later, unrelated regressions
  as shown in the current-state survey).
- **trajectory** — was the phase-1→phase-2 path sound. Checked as three
  named pass/fail/not-applicable lines: scouted-when-required (against
  `docs/issue-1117/reports/implementation/survey.md` and
  `hunt-poll-heartbeat-delta-suppression.md` existing and predating the
  phase-2 commits, per the current-state survey's commit-order check),
  surveyed-before-proposing (against
  `docs/issue-1117/proposals/poll-heartbeat-delta-suppression.md`'s own
  commit position relative to `d3db195c`), approved-by-human (against the
  exact-string `APPROVE issue-1117/implementation` issue comment from
  `JiwonJung94`, cross-checked against `docs/specs/approvers.md` and PR
  #1122's author, both read this session).
- **step** — which specific artifact, if any, is deficient. Checked
  against: the diff-scope-admissible hunk in
  `on-the-record/monitors/poll-heartbeat.sh` (the due-tick branch only),
  the live re-run of both cited test suites (current-state survey above),
  and the current-tree grep confirming the shipped hash-file mechanism has
  since been superseded — each finding will carry subject/test/result/
  assertedBy per the spec's per-claim vocabulary, with an explicit
  evidence mode (read/command/asserted) on each.

## Out of scope

- Judging issue #1245's later, unrelated work (the 3 currently-failing
  tests in `on-the-record/monitors/test_poll_heartbeat.py` trace to that
  issue's commits, not #1122's) — noted for visibility only, not scored
  against #1117's own outcome.
- Re-authoring or re-implementing any part of the delta-suppression
  mechanism.
- Filing any issue for findings — a confirmed deficiency, if any, goes
  into this role's own record only; the human judges and files it.

## How you'll know it worked

- `docs/issue-1117/reports/execution-observation.md` exists, phase-2-gated,
  with an independence statement preceding all verdict language, all three
  verdict levels addressed (each pass/fail/not-applicable named with
  cause), and every verdict-bearing sentence carrying an adjacent citation.

Proposal: docs/issue-1117/proposals/execution-observation-poll-heartbeat-delta-suppression.md
