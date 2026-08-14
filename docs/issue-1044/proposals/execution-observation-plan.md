---
status: proposed
files:
  - docs/issue-1044/reports/execution-observation.md
---

## Request

Issue #1044 asked implementation to wire `spawn.py panel <role_a>
<role_b> "<question>" [--issue n]` into `main()`'s CLI dispatch,
mirroring `consult`, and to add a CLI-dispatch test — per R001
(orphan-capability standard). That work landed as PR #1048 (phase-1)
and PR #1056 (phase-2, merged), per
docs/issue-1044/reports/execution-observation/survey.md (this session's
current-state survey). No execution-observation record exists yet for
this branch's commits, per the same survey. This proposal is phase-1
only: it commits to which of the three verdict levels will be checked
once phase-2 approval opens, and against what evidence, without
rendering any verdict itself.

## Constraints

- This role never edits the observed artifact — no change to spawn.py,
  on-the-record/hooks/directive.sh, tests/test_spawn.py, or
  docs/issue-1044/reports/implementation.md.
- The record must land at
  docs/issue-1044/reports/execution-observation.md, the sole phase-2
  artifact for this role.
- Phase-2 record writing requires a matching approval on THIS role
  (`APPROVE issue-1044/execution-observation`), separate from the
  `APPROVE issue-1044/implementation` comment that authorized the
  implementation role's own work — confirmed this session by
  approval-gate.sh's block on this session's phase-2 write attempt.

## What will be done (once phase-2 opens)

All three verdict levels will be checked, against the evidence already
gathered in this session's survey and re-confirmed live at phase-2 time:

- **outcome**: recomputed as the worst case across the step-level
  results below, against `python3 -m pytest tests/test_spawn.py -k
  panel_cli -v` run live at phase-2 time against the then-current
  working tree (this session already ran it once, in the survey, with
  result 3 passed; phase-2 will re-run it fresh rather than reuse that
  output, since the record must cite a phase-2-session-executed
  command per the outcome-claim citation rule).
- **trajectory**: three named checks — scouted-when-required (judged
  against docs/issue-1044/reports/implementation/survey.md's stated
  skip condition, embedded in PR #1048's diff), surveyed-before-
  proposing (judged against PR #1048's diff showing the survey and
  proposal landing together, survey preceding and grounding the
  proposal text), approved-by-human (judged against the exact-match
  `APPROVE issue-1044/implementation` comment from JiwonJung94, an
  account listed in docs/specs/approvers.md, found in
  `gh issue view 1044 --comments --json comments`).
- **step**: at minimum, two step-level subjects — (1) the
  `spawn.py` `if a.role == "panel":` dispatch branch (spawn.py, inside
  PR #1056's diff hunk), tested against the issue's own acceptance
  command; (2) the `on-the-record/hooks/directive.sh` panel mention,
  tested by grep against the working tree. Each will carry subject /
  test / result (spec's five-value enum) / assertedBy / mode, per
  roles/specs/execution-observation.spec.json.

## Out of scope

- Re-executing or second-guessing `panel_cmd()`'s own internal
  behavior beyond the CLI-dispatch surface the issue scoped.
- Any judgment on the before-landing warrant-hunt's finding (missing
  role_a != role_b guard) beyond confirming, at phase-2 time, that the
  delivered fix is present and its test passes — that finding was
  already caught and inline-fixed by the observed role itself, per its
  own hunt record and deviation log (both embedded in PR #1056's diff).

## How you'll know it worked

Once `APPROVE issue-1044/execution-observation` is posted by an
approvers.md account, this role writes
docs/issue-1044/reports/execution-observation.md carrying the
independence statement, all three verdict levels (each with adjacent
citations), and a loop_state of `handed-off` (or an appropriate
progress/refusal/error state if phase-2 evidence gathering surfaces a
reason to stop short).
