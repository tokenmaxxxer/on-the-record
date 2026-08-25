---
status: proposed
files:
  - docs/issue-2204/reports/execution-observation/survey.md
  - docs/issue-2204/proposals/execution-observation-record.md
  - docs/issue-2204/reports/execution-observation/deviation-log.md
  - docs/issue-2204/reports/execution-observation.md
---

## Request

Fill in the pre-written skeleton at
`docs/issue-2204/reports/execution-observation.md` with an
execution-observation record for issue #2204: what
`issue-2204/implementation` (PR #2212, merged to `main` as `443f6136`)
delivered, whether it satisfies the issue's own acceptance line, and
independently re-executed evidence — not a re-statement of the
implementation role's own reported numbers.

## Constraints

No code path may be touched by this role — only the record files listed
above. The record's frontmatter must carry the fields its own skeleton
already declares (`issue`, `role`, `loop_state`, `upstream`, `subject`,
`test`, `result`, `assertedBy`) and set `result:` from this session's
own independently re-executed evidence. `approval-gate.sh` (confirmed
this session by a direct `Bash git show` denial on a `docs/issue-2204/`
path, logged in the survey) mechanically requires a posted `APPROVE
issue-2204/execution-observation` comment, or `CORE_BUILD_NOW=1`,
before the phase-2 write to
`docs/issue-2204/reports/execution-observation.md` is allowed — neither
is present. Issue #2204 is already CLOSED (auto-closed by PR #2212's
own `Closes #2204` trailer on merge), so this role's write also depends
on the OBSERVER_ROLES exemption in `tokenmaxxxer-core`'s
`approval-gate.sh` (issue-295 there) to clear the closed-issue
precondition — confirmed applicable this session (survey, "PR #2212 and
issue #2204's own state").

## Rationale

Considered writing `docs/issue-2204/reports/execution-observation.md`
directly in this same session, on the theory that the issue's already
being closed via a merged PR on its own implementation branch removes
any reason to gate this role's own record behind a second, separate
human approval. Rejected: the role-handoff contract treats a role's
record as phase-2 output requiring human approval regardless of the
underlying issue's own lifecycle state, and the OBSERVER_ROLES exemption
this session verified in `approval-gate.sh` is scoped narrowly to the
closed-issue precondition only — its own comment block states the
approval requirement itself is unaffected ("Non-observer roles are
unaffected... the precondition below still denies them unconditionally
on any closed state, exactly as before issue-295"; nothing in that same
patch touches the separate APPROVE-comment/PR-review check further
down). Bypassing that separate check — e.g. by writing through a tool
path the gate does not intercept — would defeat the review checkpoint
this role exists to provide. Going through phase 1 first is the only
compliant path.

Also considered treating this session's own SessionStart-hook pointer to
`session-protocol.md`, and its own first-turn "디렉티브 인덱스" pointer
block, as themselves sufficient live-spawn evidence that the fix does
not work end-to-end. Rejected: this session was spawned when PR #2212
was opened, before its own merge timestamp (survey, "This session's own
spawn predates the fix") — the orchestrator that spawned it necessarily
ran the pre-merge `spawn.py`/`pipeline.py`. Treating a pre-fix spawn's
behavior as a post-fix regression would be exactly the kind of
unfounded state claim `record-claim-guard.sh` (encountered directly
this session while drafting the survey) already refuses to let a record
assert without a grounded citation — the correct framing, and the one
the survey uses, is that this session corroborates the issue's original
pre-fix problem description, not that it disproves the fix.

Also considered skipping the scout/survey round entirely, since this
task investigates already-landed code rather than proposing a design.
Accepted in part: scout-protocol's own "no design decision open" skip
condition applies (recorded in the survey's own skip line) and no
scouting sweep ran, but the current-state survey itself was still
written with real content — the diff, the implementation record, and
this session's own independently re-executed grep/Read/pytest
evidence — satisfying survey-order-directive's "must be real, not
decorative" criterion.

## What will be done

On phase-2 approval (an `APPROVE issue-2204/execution-observation`
issue comment from a `docs/specs/approvers.md`-listed account), fill in
`docs/issue-2204/reports/execution-observation.md`'s five body sections
using the survey's findings: the on-the-record-controlled half of
Defect 1 (inline Read-pointer removal) and Defect 2 (cross-cwd cache
miss) are both present in the merged diff and independently re-verified
this session at the code level (grep/Read against a read-only worktree)
and at the test level (a clean re-run of the six cited test files, `315
passed, 1 skipped, 3 xfailed, 2 xpassed`, corroborating rather than
contradicting the implementation record's own one-FAILED-line
explanation). The remaining half of Defect 1 —
`tokenmaxxxer-core`'s own `directive.sh` SessionStart hook still
pointing every spawned session at `session-protocol.md` — stays an open
finding, named as such rather than silently assumed fixed, with its
resolution path (a companion issue against `tokenmaxxxer-core`) carried
forward from the implementation record. This session's own inability to
launch a real post-fix `spawn.py`-issued role spawn (it was itself
spawned pre-merge) is named as a second open finding, with its
resolution path (a live spawn from `main`@`443f6136` or later, launched
by a future session) rather than silently treated as equivalent to the
implementation record's own directly-invoked `claude -p` measurements.
`loop_state` is set to `handed-off` once the record's own findings are
resolved or explicitly deferred with a resolution path, per
`roles/specs/execution-observation.spec.json`'s terminal-state list.

## Out of scope

No change to `pipeline.py`, `spawn.py`, or any code path. No edits to PR
#2212 (already merged) or the `issue-2204/implementation` branch. No fix
to `tokenmaxxxer-core`'s `directive.sh` Read-pointer or the missing
live-spawn confirmation named above — both are open findings for a
resolution path outside this record's write area, not repaired here.

## How you'll know it worked

`docs/issue-2204/reports/execution-observation.md` is filled in, its
`result:` field reflects this session's own re-executed evidence (not a
copy of PR #2212's self-reported numbers), every state/outcome/count
claim in it carries the `canonical:`/`derived:` grounding
`on-the-record/hooks/record-claim-guard.sh` already enforces at write
time (exercised directly this session while drafting the survey above),
and the commit landing it is pushed with a phase-2 delivery PR opened
against `main`.
