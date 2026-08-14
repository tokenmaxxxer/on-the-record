---
status: proposed
files:
  - docs/issue-1017/reports/execution-observation.md
---

## Intent

Phase 2 of this role will render a three-level verdict (outcome / trajectory / step) on the
`implementation` role's phase-1→phase-2 execution for issue #1017, once phase-2 approval
(`APPROVE issue-1017/execution-observation`) is posted by a `docs/specs/approvers.md`-listed
account.

## Constraints

- Never re-run the observed role's `spawn.py`/`requirement_linkage.py` behavior as a
  correctness check — only the artifacts read this session (PR diffs, commits, the
  implementer's own record) are admissible evidence, except where independently re-running a
  test *the implementer's own record already cites* to check its claim is itself in scope
  (already done in phase 1's survey — see `docs/issue-1017/reports/execution-observation/survey.md`).
- Never edit `docs/issue-1017/reports/implementation.md`, `spawn.py`, `gates/*`, or any other
  path outside this role's own `docs/issue-1017/reports/execution-observation.md`.
- Every verdict-bearing sentence must name its source (commit SHA, file:line, or PR comment
  URL) directly adjacent to the verdict.

## What will be checked, against what evidence

**Outcome** — recomputed as the worst case among the step-level results the phase-2 record
(`docs/issue-1017/reports/implementation.md`) cites against issue #1017's four Acceptance
bullets, cross-checked against the diff (`gh pr diff 1026`) and an independent re-run of the two
test commands the record cites (already captured in the phase-1 survey:
`python3 gates/test_requirement_digest.py`, `python3 gates/test_requirement_linkage.py`, both on
`main` HEAD).

**Trajectory** — three named pass/fail/not-applicable checks: scouted-when-required (was
`docs/issue-1017/reports/implementation/survey.md` written and read before the proposal, per the
same commit's file order already established in the phase-1 survey); surveyed-before-proposing
(did that survey's content precede any proposal-shaped language in the same commit); and
approved-by-human (the `APPROVE issue-1017/implementation` comment on issue #1017, judged under
single-account mode since PR #1020/#1026's author and the approving login are the same account
per the phase-1 survey's findings).

**Step** — any deficiency found in the diff or the phase-2 record, each finding stating subject
(artifact judged), test (what was checked), result (the spec's five-value enum), and assertedBy
(this role). One candidate already surfaced in phase-1 survey (not yet classified): the phase-2
record's `## Acceptance verification` section does not include a verbatim watchdog-tick output
quote, though issue #1017's fourth Acceptance sub-bullet asks for one.

## Out of scope

Re-implementing or extending `gates/requirement_linkage.py` or `spawn.py`; filing an issue for
any deficiency found (contract v3: issues are user-authored only; a confirmed deficiency goes
into this role's own record for the human to act on).

## How it will be known to have worked

Phase 2's `docs/issue-1017/reports/execution-observation.md` states all three verdict levels
(each addressed even if "not applicable, because X"), every verdict sentence carries an adjacent
citation, the independence statement precedes any verdict language, and the file is committed on
`issue-1017/execution-observation` with `loop_state: handed-off` (or the appropriate non-terminal
state if phase 2 cannot complete this session).
