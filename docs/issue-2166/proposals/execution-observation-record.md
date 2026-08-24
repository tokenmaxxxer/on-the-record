---
status: proposed
files:
  - docs/issue-2166/reports/execution-observation/survey.md
  - docs/issue-2166/proposals/execution-observation-record.md
  - docs/issue-2166/reports/execution-observation/2026-08-24-hunt-execution-observation-record.md
  - docs/issue-2166/reports/execution-observation.md
---

## Request

Fill in the pre-written skeleton at
`docs/issue-2166/reports/execution-observation.md` with an
execution-observation record for issue #2166: what the
`issue-2166/implementation` branch (PR #2171) delivered, whether it
satisfies the issue's own acceptance criterion, and independently
re-executed acceptance evidence — not a re-statement of the
implementation role's own claims.

## Constraints

No code path may be touched by this role — only the record files listed
above. The record's frontmatter must carry the fields its own skeleton
already declares (`issue`, `role`, `loop_state`, `upstream`, `subject`,
`test`, `result`, `assertedBy`) and set `result:` from this session's own
independently re-executed evidence, not from trusting PR #2171's own
reported numbers. `approval-gate.sh` (confirmed this session by a direct
`Edit` denial, logged in the survey) mechanically requires a posted
`APPROVE issue-2166/execution-observation` comment, or
`CORE_BUILD_NOW=1`, before the phase-2 write to
`docs/issue-2166/reports/execution-observation.md` is allowed — neither
is present.

## Rationale

Considered writing `docs/issue-2166/reports/execution-observation.md`
directly in this same session, on the theory that an observation-only
role carries no design decision and so the two-phase proposal/approval
gate should not apply to it. Rejected: the role-handoff contract states a
record file is phase-2 output "like code" with no carve-out for
observation-only roles, and `approval-gate.sh`'s own deny path (exercised
directly this session — see the survey's "Write surface" section) treats
this role's record path exactly like any other phase-2 write, regardless
of whether the underlying task involves a design choice. Bypassing that
gate — e.g. by writing through a tool path the gate does not intercept —
would defeat the review checkpoint this role exists to provide, not
route around an accident of scope. Going through phase 1 first is the
only compliant path.

Also considered skipping the scout/survey round entirely, since this
task investigates already-written code rather than proposing a design.
Accepted in part: scout-protocol's own "no design decision open" skip
condition applies (recorded in the survey's own skip line) and no
scouting sweep ran, but the current-state survey itself was still
written — it names real content (the diff, the implementation record,
independently re-run tests) rather than a placeholder, satisfying
survey-order-directive's "must be real, not decorative" criterion.

## What will be done

On phase-2 approval (an `APPROVE issue-2166/execution-observation`
issue comment from a `docs/specs/approvers.md`-listed account, or a live
delegation citation), fill in
`docs/issue-2166/reports/execution-observation.md`'s five body sections
using the survey's findings and this session's own re-executed evidence:
`market-analysis-mece-proposal` needed no fix (BM25 rank outside the
judge's top-8 window for issue-525's real task text) and
`work-in-english`'s exposure through the unbounded fast-path phrase scan
is closed by the one-line topN bound in `consult.py`; independently
re-run `python3 -m py_compile` and the new regression test in
`tests/test_retrieval_eval.py` both pass. Any part of the PR's own test
plan this session cannot independently re-execute (the approval-gate
Bash-hook denial recorded in the survey) is named as an open finding
with its resolution path (re-run once the hook infrastructure issue is
fixed by whichever role owns `on-the-record/hooks/`), not silently
assumed passing. `loop_state` is set to a terminal value once the
record's own findings are resolved or explicitly deferred with a
resolution path.

## Out of scope

No change to `consult.py`, `pipeline.py`, or any code path. No edits to
PR #2171 or the `issue-2166/implementation` branch. No fix to the
`approval-gate` Bash-hook flake encountered this session — that is
`on-the-record/hooks/` infrastructure, outside this record's write area;
it is reported as an open finding, not repaired here.

## How you'll know it worked

`docs/issue-2166/reports/execution-observation.md` is filled in, its
`result:` field reflects this session's own re-executed evidence (not a
copy of PR #2171's self-reported numbers), every state/outcome/count
claim in it carries the `canonical:`/`derived:` grounding
`on-the-record/hooks/record-claim-guard.sh` already enforces at write
time, and the commit landing it is pushed with a phase-2 delivery PR
(carrying `Closes #2166` per the role protocol's phase trailer split)
opened against `main`.
