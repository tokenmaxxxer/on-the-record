---
status: proposed
files:
  - docs/issue-638/reports/implementation.md
---

## Request

#623's drive flagged as its finding 2: `docs/issue-600`'s implementation
record references `proposal-shape-gate.sh` and `survey-order-gate.sh` as
things it hit while building, but neither file exists under the packaged
`on-the-record/hooks/` tree. #638 asks for a small audit — are these
repo-root tooling, a rename, or a stale reference — and to fix whichever
it is, keeping the boundary test green.

## Constraints

- No code changes unless the audit finds an actual packaging gap (a hook
  meant to ship but missing from `on-the-record/hooks/hooks.json`).
- `gates/test_boundary.py` (the boundary completeness check) must stay
  green — no fabricated row for a file that doesn't exist in the repo.
- `board-gate.sh` (external harness hook, contract v3 s10) refuses any
  write under `docs/issue-600/` or `docs/issue-623/` from this branch
  (`issue-638/implementation`) — confirmed by direct test (Edit attempt
  on `docs/issue-600/reports/implementation.md` was refused: "writing
  docs/issue-600/ requires branch issue-600/implementation"). Editing
  another issue's tree is structurally not this session's to do; the
  write set is narrowed to this issue's own tree accordingly.
- Fix scoped to this issue's own record; other occurrences of the same
  two names elsewhere in `docs/` are the standing directive boilerplate
  quoted verbatim in unrelated surveys, not claims about file location,
  and are out of scope (survey.md documents this after checking each
  one).

## Rationale

Considered adding a boundary-spec row for the two names (treating them
as hooks that were "meant to ship" per the issue's alternative branch)
and writing stub scripts under `on-the-record/hooks/` to match. Rejected
this: the survey found no git history for either filename anywhere in
the repo (`git log --all` over both paths is empty), and
`on-the-record/hooks/directive.sh` — the plugin's only `UserPromptSubmit`
injector — provably never fires into a role session at all (it exits
immediately when `CLAUDE_ROLE` is set) and contains no reference to
either name. There is nothing in this repo to rename, restore, or stub;
fabricating a hook and a boundary row for it would assert a mechanism
this repo does not own and cannot enforce, which is worse than the
stale reference it would replace. The two gate behaviors #600's session
actually hit are real, but they come from an external layer (the
harness that spawns role sessions and injects directives, observed
firing in this very session under the same two names) — correcting the
prose to say so is the accurate fix, not a packaging change.

## What will be done

1. `docs/issue-638/reports/implementation.md` (the phase-2 record) will
   state the audit's resolved answer plainly — the two names are
   external-harness tooling, never packaged under
   `on-the-record/hooks/`, confirmed by `git log --all` (empty
   history), `hooks.json` (never listed), and a full read of
   `directive.sh` (structurally cannot fire into a role session) — so
   this record itself is the corrected reference this issue produces.
2. The record will name the two stale-claim sites verbatim
   (`docs/issue-600/reports/implementation.md` lines 73/83,
   `docs/issue-623/reports/execution-observation.md` lines 39/61/130/156)
   and state that correcting them requires a session on each of those
   issues' own branches (`issue-600/implementation`,
   `issue-623/implementation`) per `board-gate.sh` — out of #638's reach
   from this branch, and hand this off explicitly rather than silently
   leaving the source docs uncorrected.
3. Confirm `python3 -m pytest gates/test_boundary.py` runs (fenced
   output in the record) to show the pre-existing, unrelated
   `remediation_spawn.py` failure is not something this issue's change
   introduces or needs to fix.

## Out of scope

- Editing `docs/issue-600/**` or `docs/issue-623/**` directly — blocked
  by `board-gate.sh` from this branch; each issue's own role session
  must apply its own correction.
- Any change to `on-the-record/hooks/hooks.json`, `directive.sh`, or
  `docs/specs/enforcement-boundary.md` — the audit found no real file
  for either name, so there is nothing to register or list.
- The unrelated boilerplate occurrences of the two names in other
  issues' survey/proposal files (#319, #245, #547, #517, #363, #373,
  #419) — verified in the survey to be the standing directive text, not
  stale claims.
- Fixing the pre-existing `remediation_spawn.py` boundary-table gap —
  unrelated to this issue's two names, not introduced by this change.

## How you'll know it worked

- `docs/issue-638/reports/implementation.md` states the resolved answer
  (external harness tooling, not a packaging gap) with the evidence
  trail, and names the exact lines in `docs/issue-600`/`docs/issue-623`
  that still need each issue's own session to correct.
- `python3 -m pytest gates/test_boundary.py` output is fenced in the
  record, showing the same pre-existing failure count before and after
  this issue's change (i.e., this change adds zero new boundary-test
  failures).
