---
status: proposed
files:
  - docs/issue-2180/reports/execution-observation/survey.md
  - docs/issue-2180/proposals/2026-08-24-execution-observation-issue-2180.md
  - docs/issue-2180/reports/execution-observation.md
---

## Request

Fill in the pre-written skeleton at
`docs/issue-2180/reports/execution-observation.md` with an
execution-observation record for issue #2180: whether the
`issue-2180/implementation` branch (PR #2181, already merged to `main` as
`abdb5ac0`) delivered what the issue asked for, and independently
re-executed acceptance evidence — not a re-statement of the
implementation role's own claims.

## Constraints

No code path may be touched by this role — only the record files listed
above. The record's frontmatter must carry the fields its own skeleton
already declares (`issue`, `role`, `loop_state`, `upstream`, `subject`,
`test`, `result`, `assertedBy`) and set `result:` from this session's own
independently re-executed evidence (survey's "Independent re-verification"
section), not from trusting PR #2181's own reported numbers.

Blocking precondition, found this session and detailed in the survey's
"Issue #2180's own state" section: issue #2180 is closed
(`stateReason: COMPLETED`), auto-closed by GitHub the moment PR #2181's
own `Closes #2180` trailer merged to `main`. The outer orchestration
harness's `approval-gate.sh` denies any execution-surface write for this
subject unconditionally while the issue stays in that state — this
denial fires before either approval-signal path (a PR review Approve, or
an issue comment exactly `APPROVE issue-2180/execution-observation`) is
even evaluated, and only a `CORE_BUILD_NOW=1` environment stamp (set by
the spawner, never by this session itself) or a human reopening the issue
can restore a live path to the write this proposal's own "What will be
done" section describes.

## Rationale

Considered writing `docs/issue-2180/reports/execution-observation.md`
directly in this same session, on the theory that an observation-only
role with no design decision open should not owe the two-phase
proposal/approval gate at all. Rejected: the role-handoff contract states
a record file is phase-2 output "like code" with no carve-out for
observation-only roles, and this session's own direct `Write` attempt at
that path (denied — see the survey's "Write surface" section) confirms
the mechanical gate treats this role's record exactly like any other
phase-2 write, regardless of whether the underlying task involves a
design choice. Bypassing that gate would defeat the review checkpoint
this role exists to provide, not route around an accident of scope.

Considered asking this session to set `CORE_BUILD_NOW=1` itself, since
the empirical precedent for this exact role (issue #2166's and
issue #2164's execution-observation records, both merged as a single
direct commit with no separate phase-1 PR) strongly suggests the role is
normally spawned in build-now mode. Rejected outright, not merely
deprioritized: the role-handoff contract's own text is explicit that "a
session cannot grant itself this bypass by setting the variable on its
own" — the absence of that stamp in this session's environment is most
likely a spawn-configuration gap (worth flagging to whoever owns
`spawn.py`'s env wiring for this role), not something this session may
correct unilaterally.

Also considered skipping the scout/survey round entirely, since this
task investigates already-written code rather than proposing a design.
Accepted in part: scout-protocol's own "no design decision open" skip
condition applies (recorded in the survey's own skip line) and no
scouting sweep ran, but the current-state survey itself was still
written with real content — the diff, the implementation record's own
frontmatter and pasted test run, and this session's own independently
re-executed test runs against a read-only worktree — rather than a
placeholder, satisfying survey-order-directive's "must be real, not
decorative" criterion.

## What will be done

On phase-2 approval (a `CORE_BUILD_NOW=1` stamp from a future spawn of
this role, or the issue being reopened followed by an
`APPROVE issue-2180/execution-observation` comment from a
`docs/specs/approvers.md`-listed account), fill in
`docs/issue-2180/reports/execution-observation.md`'s five body sections
using the survey's findings: the distinct `[new-returned-pr]` marker and
the collapsed `[returned-pr-pending]` line both match the issue's two
acceptance bullets, the empty-state clause is covered by the
first-ever-tick test named in the survey, and this session's own
independently re-executed test runs (in a read-only worktree, not the
implementation role's self-reported numbers) match the implementation
record's own claimed results with no discrepancy. `loop_state` is set to
`handed-off` (this role's own terminal state per
`roles/execution-observation.json`) once that content is written.

## Out of scope

No change to `on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/monitors/test_poll_heartbeat.py`, or any other code path.
No edits to PR #2181 (already merged) or the `issue-2180/implementation`
branch. No attempt by this session to set `CORE_BUILD_NOW=1` itself, post
an approval-shaped comment on its own subject's issue, or reopen issue
#2180 — all three are human/spawner acts this role does not perform on
its own behalf.

## How you'll know it worked

`docs/issue-2180/reports/execution-observation.md` is filled in, its
`result:` field reflects this session's own re-executed evidence, every
state/outcome/count claim in it carries the `canonical:`/`derived:`
grounding `on-the-record/hooks/record-claim-guard.sh` already enforces at
write time, and the commit landing it is pushed with a phase-2 delivery
PR (carrying `Closes #2180` per the role protocol's phase trailer split,
once a live approval path actually exists) opened against `main`.
