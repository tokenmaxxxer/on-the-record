---
status: proposed
files:
  - docs/issue-2211/reports/execution-observation/survey.md
  - docs/issue-2211/proposals/2026-08-25-execution-observation-issue-2211.md
  - docs/issue-2211/reports/execution-observation.md
---

## Request

Fill in the pre-written skeleton at
`docs/issue-2211/reports/execution-observation.md` with an
execution-observation record for issue #2211: whether the
`issue-2211/implementation` branch (PR #2228, currently open, not yet
merged) delivered the two `check:` acceptance bullets the issue states —
env vars readable inside a live spawn, and zero `find /`/`find /home`
calls for a re-measured engineering-class task — using independently
re-executed evidence, not a restatement of the implementation role's own
claims.

## Constraints

No code path may be touched by this role — only the record files listed
above. The record's frontmatter must carry the fields its own skeleton
already declares (`issue`, `role`, `loop_state`, `upstream`, `subject`,
`test`, `result`, `assertedBy`) and set `result:` from this session's own
independently re-executed evidence (the survey's "Independent
re-verification" section), not from trusting PR #2228's own reported
numbers.

Blocking precondition, confirmed this session and detailed in the
survey's "Issue #2211's own approval state" section: this is the first
session for `issue-2211/execution-observation` — no PR yet exists for
this branch, and no issue comment reads the exact string `APPROVE
issue-2211/execution-observation`. This workspace's own approval-gate
PreToolUse hook denies a `Write`/`Edit`/`MultiEdit` at the record path
unconditionally until that signal exists (verified this session — see the
survey's "Write surface" section). Only that comment from a
`docs/specs/approvers.md`-listed account (or a `CORE_BUILD_NOW=1` stamp on
a future spawn of this role, set by the spawner, never by this session)
can open phase 2.

## Rationale

Considered writing `docs/issue-2211/reports/execution-observation.md`
directly in this same session, on the theory that an observation-only role
with no design decision open should not owe the two-phase proposal/approval
gate at all. Rejected: the role-handoff contract states a record file is
phase-2 output "like code" with no carve-out for observation-only roles,
and the approval-gate hook's own comment (read this session, at
`~/.claude/plugins/marketplaces/tokenmaxxxer/on-the-record/hooks/approval-gate.sh`)
confirms it treats this role's record exactly like any other phase-2
write, regardless of whether the underlying task involves a design choice.
Bypassing that gate would defeat the review checkpoint this role exists to
provide, not route around an accident of scope.

Considered asking this session to set `CORE_BUILD_NOW=1` itself, since the
spawning prompt's own text ("PR 생성 시 자동 스폰됨 (spawn_on_pr.py)")
suggests this role may often run as a single build-now delivery. Rejected
outright, not merely deprioritized: the role-handoff contract's own text is
explicit that "a session cannot grant itself this bypass by setting the
variable on its own" — the absence of that stamp in this session's own
environment (checked this session: `env | grep -Ei "CORE_|CLAUDE_"` shows
no `CORE_BUILD_NOW` line) is a spawn-configuration question for whoever
owns `spawn.py`'s env wiring for this role, not something this session may
correct unilaterally.

Also considered skipping the scout/survey round entirely, since this task
investigates already-written code rather than proposing a design. Accepted
in part: scout-protocol's own "no design decision open" skip condition
applies (recorded in the survey's own skip line) and no scouting sweep
ran, but the current-state survey itself was still written with real
content — the diff, the implementation record's own frontmatter and
pasted test run, and two independently reproduced live `claude -p` spawns
run this session against a disposable worktree of the real code path
(not a restatement of the implementation role's own transcripts) —
rather than a placeholder, satisfying survey-order-directive's "must be
real, not decorative" criterion.

Considered waiting for PR #2228 to merge to `main` before doing any
independent re-verification at all, on the theory that "the board is what
is merged to main" (contract v3). Rejected: the role's own spec
(`roles/specs/execution-observation.spec.json`, read this session) keys
`use_when.board_condition` on an artifact landing on "the branch", not
`main`, and this role was auto-spawned specifically on PR-create — waiting
for a merge that this role has no way to trigger or predict would leave
this round of work stalled on an event outside this proposal's control.
The survey instead notes, under "Open items for phase 2", that the
record's `subject:`/`upstream:` fields need a re-check for the real `main`
commit sha only if the merge lands before this role's own phase 2 runs.

## What will be done

On phase-2 approval (an `APPROVE issue-2211/execution-observation` comment
from a `docs/specs/approvers.md`-listed account, or a `CORE_BUILD_NOW=1`
stamp from a future spawn of this role), fill in
`docs/issue-2211/reports/execution-observation.md`'s five body sections
using the survey's findings: both acceptance `check:` bullets — env-var
readback and the zero-`find /` re-measurement — independently reproduced
this session via two live nested `claude -p` spawns run from a disposable
worktree, matching the implementation record's own pasted transcripts with
no discrepancy; the targeted pytest suite independently re-run with the
same pass total. `loop_state` is set to `handed-off` (this role's own
terminal state per `roles/execution-observation.json`) once that content
is written.

## Out of scope

No change to `pipeline.py`, `spawn.py`, `tests/test_spawn_pipeline.py`,
`tests/test_directive_diet_2135.py`, or any other code path. No edits to
PR #2228 or the `issue-2211/implementation` branch. No attempt by this
session to set `CORE_BUILD_NOW=1` itself, post an approval-shaped comment
on its own subject's issue, or merge PR #2228 — all are human/spawner acts
this role does not perform on its own behalf.

## How you'll know it worked

`docs/issue-2211/reports/execution-observation.md` is filled in, its
`result:` field reflects this session's own re-executed evidence, every
state/outcome/count claim in it carries the `canonical:`/`derived:`
grounding `on-the-record/hooks/record-claim-guard.sh` already enforces at
write time, and the commit landing it is pushed with a phase-2 delivery
PR (carrying `Closes #2211` per the role protocol's phase trailer split,
once a live approval path actually exists) opened against `main`.
