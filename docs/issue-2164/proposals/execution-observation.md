status: proposed
files:
  - docs/issue-2164/reports/execution-observation/survey.md
  - docs/issue-2164/reports/execution-observation.md

## Request

Independently verify issue #2164's two acceptance criteria against commit 3ea0ec88 (PR #2168's
own merge to main, referenced plainly here per the phase-1/phase-2 trailer split — no
Closes/Fixes in this proposal) and write this role's EARL-shaped record with the resulting
pass/fail evidence.

## Constraints

- Never edit `consult.py`, `pipeline.py`, or implementation's own record
  (`docs/issue-2164/reports/implementation.md`) — independence per this role's directive; a
  confirmed deficiency goes into this role's own record as a finding, never a fix applied here.
- Verification runs against commit 3ea0ec88 (a disposable worktree or equivalent), never
  against implementation's self-report, and never against this branch's own tree (which sits on
  the pre-merge d9a1e826 and cannot substitute for the actual landed artifact).
- No re-litigation of the terminology-naming choice itself (already decided by implementation);
  this role only checks whether the shipped code meets the criteria the issue already states.

## Rationale

Rejected alternative: restate implementation's own claimed acceptance evidence
(`docs/issue-2164/reports/implementation.md`'s "194 passed, 0 failed, 4 xfailed" and grep
result) as this role's verdict without re-running anything. Rejected because this role's
directive is explicit independent execution — never accept a prior role's claim about what
shipped code does — and the role's own spec calls a record with no independently-run command
behind its verdict a "hollow instance" that asserts nothing about the artifact
(`roles/specs/execution-observation.spec.json`, `gate_b_contrast`). The whole reason this role
exists is to catch drift between a claim and the actual landed artifact; restating without
re-running would defeat that purpose even though it is far cheaper.

## What will be done

Phase 2 (after `APPROVE issue-2164/execution-observation`) writes
`docs/issue-2164/reports/execution-observation.md` citing the evidence already gathered and
recorded in this phase's survey (`docs/issue-2164/reports/execution-observation/survey.md`):
the two independent `grep -n '룰북'` runs against commit 3ea0ec88 (0 hits in `consult.py`; 3
hits in `pipeline.py`, each read in context and matched to the issue's own core-plugin-bundle
exclusion clause) and the independent `pytest` run of the consult/judge/panel/pipeline test
files the issue's acceptance names (167 passed, 4 xfailed, 0 failed). Both criteria pass; the
record sets `subject`/`test` to the concrete commit/command refs, `result` to the EARL enum's
affirmative value, `assertedBy` to this role, `loop_state` to `handed-off` (terminal), and `open
findings` to none.

## Out of scope

- Fixing anything (none found) — this role never fixes regardless of outcome.
- Re-running or re-judging implementation's own full test suite figure; this role's own subset
  run stands as independent evidence without needing to match that count.
- Touching `docs/issue-2164/reports/implementation.md` or any other role's write area.

## How you'll know it worked

This phase-1 PR opens referencing #2164 as a plain issue number (no Closes/Fixes trailer,
per the phase split). Phase 2, once `APPROVE issue-2164/execution-observation` is posted by a
`docs/specs/approvers.md`-listed account, commits the terminal record satisfying contract §20's
required fields (what was done, why, upstream basis, loop_state, open findings) and this repo's
`roles/specs/execution-observation.spec.json` required fields (subject, test, result,
assertedBy), on the same branch and PR.
