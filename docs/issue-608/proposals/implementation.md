---
status: proposed
files:
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/test_approval_gate.py
  - on-the-record/hooks/hooks.json
  - docs/specs/enforcement-boundary.md
  - docs/issue-608/reports/implementation.md
---

## Request

#608 step 2: close the coverage hole step 1 confirmed
(`docs/issue-608/reports/execution-observation/fixture-measurement.md`,
Findings 1-2) — no deployed `PreToolUse` hook checks phase-2 approval for
a role session's own writes (record file, `src/`, `test/`), and the one
hook that does check `approvers.md` presence (`deliverable-guard.sh`)
fails open with a silent allow when that file is absent, instead of
refusing and instructing. Add the missing enforcement, zero-install, and
fix the fail-open branch, with a red/green fixture matrix over the full
2x2 (approvers present/absent x approved/unapproved) plus the
absent-approvers boundary case, and the required
`docs/specs/enforcement-boundary.md` row in the same unit.

## Constraints

- Zero-install hooks only (plugin `on-the-record/hooks/`) — no GitHub
  Actions, no dependency on this repo's own `gates/` checkout existing in
  a consumer repo (per issue body: "Any fix ships zero-install (hooks
  surface), no Actions").
- Must not block phase-1-legal writes: proposals, survey files under
  `reports/<role>/`, decisions, handbooks — only the role's own record
  file (`docs/issue-<n>/reports/<role>.md`) and `src/`/`test/` paths for
  the acting issue are phase-2-shaped (survey, "phase-2 shaped write"
  section).
- Absent-`approvers.md` case denies with a refuse-and-instruct
  (bootstrap-offer) message, never a silent allow — the issue's explicit
  acceptance line, and the fix for step 1's Finding 1.
- `docs/specs/enforcement-boundary.md` row required in the same unit —
  confirmed live: `gates/test_boundary.py` fails the build on an
  unrecorded `on-the-record/hooks/*.sh` file (survey, boundary-spec
  section).
- No edits to the seven existing hooks or their tests — none of them
  currently do `Write`/`Edit`/`MultiEdit` approval checking (step 1,
  Finding 2), so the fix is additive, not corrective, to that set.

## Rationale

**Considered: extend `deliverable-guard.sh` in place instead of adding a
new hook script — rejected.** `deliverable-guard.sh` is orchestrator-
scoped by design: it explicitly no-ops for any role session
(`[ -z "${CLAUDE_ROLE:-}" ] || exit 0`) and its own spec row describes
its job as "blocks orchestrator-authored deliverables." The missing
enforcement is the opposite case — checking a *role* session's approval
state. Folding both concerns into one script would invert its documented
contract and make every future reader hold two unrelated jobs
(orchestrator-authorship blocking vs. role-approval blocking) in one
file. A second, narrowly-scoped hook (`approval-gate.sh`) keeps each
script's blast radius matching its one stated job, matching the
established pattern: `pr-preflight.sh` was added as a sibling to
`contract-guard.sh` for a related-but-distinct `gh pr` sub-check rather
than folded into it.

**Considered: gate `Bash` (`git commit`) in addition to
`Write`/`Edit`/`MultiEdit` — rejected for this unit, left as an explicit
gap.** Step 1's Finding 2 recommendation mentions gating `git commit`
too. But the actual unapproved act the issue's live evidence names is
the write itself (the role's record file, or `src`/`test` content) —
blocking the write is sufficient to stop the phase-2 act before it
happens, and `git commit` on an unwritten/unstaged phase-2 file is not
independently reachable (nothing to commit). Adding a second command-
parsing surface for `git commit` roughly doubles this unit's scope
(command-line commit parsing, staged-file introspection) for a case the
write-time gate already forecloses. Recorded here rather than silently
dropped: a role could still stage and commit a phase-2 file written in a
*previous*, already-approved session state that later reverted to
unapproved (an edge case, not the fixture-measured gap), which this unit
does not close.

## What will be done

1. `on-the-record/hooks/approval-gate.sh` — new `PreToolUse` hook,
   matcher `Write|Edit|MultiEdit`. No-ops immediately unless
   `CLAUDE_ROLE` is set (role sessions only — orchestrator-authored
   writes are `deliverable-guard.sh`'s job). Parses `issue-<n>/<role>`
   off the current branch name (same regex as `pr-preflight.sh`). Skips
   (exit 0) any write outside the two phase-2-shaped targets: the acting
   role's own record file (`docs/issue-<n>/reports/<role>.md`) or a
   `src/`/`test/`/`tests/` path. For a phase-2-shaped write: if
   `docs/specs/approvers.md` is absent, deny (exit 2) with a
   refuse-and-instruct message offering to bootstrap the file (name the
   path, one-line format example) — never a silent allow. If present,
   check `approvers.md` membership plus an exact `APPROVE
   issue-<n>/<role>` issue comment from a listed account (ported inline,
   same shape as `pr-preflight.sh:90-120`); deny with a clear message
   naming what's missing if no match, allow if matched. A `gh` lookup
   failure fails open (consistent with `pr-preflight.sh`'s own documented
   fail-open policy on infrastructure failures, not approval-state
   failures) with a stderr note that the check could not run.
2. `on-the-record/hooks/test_approval_gate.py` — pytest, invoking the
   real shell script via subprocess against fixture stdin payloads (same
   style as the existing `test_*.sh`-adjacent hook tests). Matrix: {role
   session, orchestrator session} x {approvers present, absent} x
   {approved, unapproved} for each of the two phase-2-shaped targets
   (record file, src/test path), plus a phase-1-legal-path control row
   (proposal/survey write always allowed regardless of approval state) —
   the boundary-spec row the issue asks for, expressed as a fixture case
   in the same unit. Red before `approval-gate.sh` exists (or before its
   logic is correct), green after.
3. `on-the-record/hooks/hooks.json` — add `approval-gate.sh` to the
   `PreToolUse` array under the existing `Write|Edit|MultiEdit` matcher
   group (alongside `record-claim-guard.sh` et al.).
4. `docs/specs/enforcement-boundary.md` — add a row for
   `approval-gate.sh` under `on-the-record/hooks/*.sh (plugin-shipped)`,
   verdict `contract` (new, issue #608: closes the role-session
   Write/Edit approval-gate coverage hole step 1's fixture measurement
   confirmed).
5. Run the full hook test suite (`python3 -m pytest on-the-record/hooks/
   -q` or equivalent) plus the new fixture matrix, fenced output in this
   role's record (`docs/issue-608/reports/implementation.md`).

## Hunt note (after-proposal, stance 0)

`docs/reports/2026-08-10-hunt-implementation.md` flags that the
branch-name parse (`^issue-(\d+)/([\w-]+)$`, `pr-preflight.sh`'s own
pattern) fails open — a detached-HEAD checkout or any non-matching
branch name skips the gate entirely (`sys.exit(0)`), letting an
unapproved phase-2-shaped write through unblocked on such a checkout.
This is real but not new scope: `pr-preflight.sh` and `contract-guard.sh`
already fail open on the identical branch-parse-mismatch case, so
`approval-gate.sh` inherits an already-accepted repo-wide policy rather
than introducing a fresh one — the alternative (deny outright on any
unparseable branch) would also deny legitimate non-issue branches
(scratch work, `main` itself) with no phase-2 act in play. Recorded here
as an accepted, pattern-consistent limitation, not silently dropped: a
detached-HEAD or oddly-named checkout is a known residual gap this unit
does not close.

## Accumulation

`approval-gate.sh` adds one more inline `subprocess`/`gh` call site to the
`on-the-record/hooks/*.sh` family (alongside `pr-preflight.sh`,
`contract-guard.sh`, `record-claim-guard.sh`); its test file adds one more
fake-`gh`-shim pytest module. Neither is expected to repeat: this closes
the one remaining `Write`/`Edit`/`MultiEdit` approval-check gap step 1
found — there is no next hook in this family queued behind it. If a
future issue adds another `Write`/`Edit`-scoped `gh`-consulting hook, the
existing `gh_json`-shaped helper in `pr-preflight.sh`/`approval-gate.sh`
should be factored into a shared inline snippet at that point, not before
(YAGNI: two instances of the same 15-line helper is not yet a maintenance
cost worth a shared-import indirection in a zero-install bash+heredoc
hook family).

## Out of scope

- Gating `Bash`/`git commit` directly (Rationale, second alternative) —
  recorded as a known remaining gap, not silently dropped.
- Any change to `contract-guard.sh` or `pr-preflight.sh` — their `gh pr`
  scope is already correctly enforced (step 1 did not flag them).
- Chasing candidate cause (b), plugin-version skew in the tailor repo —
  step 1 recorded this as not needed to explain the gap (Finding 3).

## How you'll know it worked

`on-the-record/hooks/test_approval_gate.py` passes, with the full matrix
(approvers present/absent x approved/unapproved, both target shapes,
plus the phase-1-legal control row) shown as fenced pytest output in
`docs/issue-608/reports/implementation.md`. The full existing
`on-the-record/hooks/` suite still passes (no regression). Re-running
step 1's own fixture script (`run_fixture.sh`'s approach, adapted to
target `approval-gate.sh`) against the unmodified new script reproduces
rc=2 with a refuse-and-instruct message for
`approvers=absent, role=execution-observation` — the exact cell step 1's
Finding 1 showed silently allowing before this fix.
