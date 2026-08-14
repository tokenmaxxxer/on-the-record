---
status: proposed
files:
  - docs/issue-745/reports/execution-observation.md
---

# Proposal — execution-observation of PR #1517 (issue #745, Item 3)

## Intent

Judge whether `implementation`'s PR #1517 (Item 3, three-axis
`execution-observation` skip-eligibility classifier) was executed
soundly, and write the phase-2 record if approved.

## Constraints

- Never re-run the observed role's task, never edit its `src/`/`test/`/
  record paths (per this role's directive, session start).
- Verdicts require citation; every verdict-bearing sentence names its
  commit SHA / file:line / PR comment URL, adjacent to the verdict.
- Phase-2 record is the sole artifact that counts; it may not be written
  before a human Approve lands on this branch's PR (contract v3 s19).

## What will be checked, and against what evidence

Three verdict levels, per the role directive:

- **outcome** — recomputed as the worst case among this record's own
  step-level findings (not a standalone summary), evidence: the merged
  diff (`gh pr diff 1517`) and a live re-run of the PR's claimed test
  command on this branch (`python3 -m pytest gates/test_skip_eligibility.py
  tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py -q`).
- **trajectory** — three named pass/fail/not-applicable checks:
  scouted-when-required, surveyed-before-proposing (both against the
  approved phase-1 proposal file, `git show 22e162ed:docs/issue-745/
  proposals/item3-execution-observation-conditioning.md`, and PR #1517's
  own commit order), and approved-by-human (against the issue #745
  comment thread's `APPROVE issue-745/implementation` string match and
  `docs/specs/approvers.md`'s roster).
- **step** — per-artifact findings over `gates/skip_eligibility.py`'s
  three axis functions (checked against the approved proposal's rule
  text), the claimed test suite (checked by live re-run), and
  `docs/specs/enforcement-boundary.md`'s new registration row (checked
  by direct read).

## Out of scope

- Re-litigating Item 3's design (RICE scoring, threshold choice) — that
  was decided in the already-approved phase-1 proposal, not this PR.
- The pre-registered 20-PR measurement window's outcome — not yet due.
- Items 1 (thinking budget, operator-held) and 2 (already reverted).

## How this will be known to have worked

The phase-2 record (`docs/issue-745/reports/execution-observation.md`)
is committed on this branch, states all three verdict levels (or "not
applicable, because X" for any that don't apply) with adjacent
citations, and its `loop_state` reaches a terminal state for kind
`observation` per contract §2.
