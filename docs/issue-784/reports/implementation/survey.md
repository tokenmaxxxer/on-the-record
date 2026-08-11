# Survey — issue-784: concurrent-merge strand of a live phase-1→phase-2 session

## Scope surveyed

- `spawn.py`: session liveness/roster (`roster_ps`, `ROSTER = ROOT/"runs"/"active.json"`,
  `_alive()` via `os.kill(pid, 0)`), absorbed-branch re-cut
  (`checkout_issue_branch()`, spawn.py:4171-4260), spawn-claim files
  (`_acquire_spawn_claim`/`_release_spawn_claim`, spawn.py:4352-4437).
- `on-the-record/hooks/contract-guard.sh`: the one broker that executes
  every `gh pr merge` (PreToolUse/Bash deny-before-effect gate, issue #441,
  broker-attach revision issue #653). It already resolves `(issue, pr)` and
  reads `docs/specs/approvers.md` and `git rev-parse --abbrev-ref HEAD` in
  the target checkout before deciding phase1/phase2 and attaching `Closes`.
- `docs/issue-732/proposals/absorbed-branch-untracked-recut.md`: the prior
  absorbed-branch fix. Its guard runs inside `checkout_issue_branch()`,
  which fires **only once, at spawn** (call site: spawn.py:4487, inside
  the spawn command path). No other call site re-invokes it.
- `tests/test_spawn.py`: existing absorbed-branch coverage —
  `test_checkout_recuts_when_truly_fully_absorbed_local_and_remote`,
  `test_checkout_recuts_absorbed_branch_and_preserves_untracked_files`,
  `test_checkout_tracks_origin_instead_of_recut_when_locally_stale_only`
  (tests/test_spawn.py:1428-1557) — all exercise the spawn-time path only.

## What #732 already covers, and the gap #784 needs

`checkout_issue_branch()` correctly detects "0-ahead vs base" (fully
absorbed) and re-cuts a fresh branch **when a NEW spawn/respawn checks out
`issue-<n>/<role>`**. It cannot help a session that is already running: that
session already has the branch checked out in its own workspace and never
calls `checkout_issue_branch()` again during its lifetime. If an orchestrator
merges+deletes that branch mid-run, the running session's *next* `git
commit`/`gh pr create` is the first place absorption would be visible, and
today nothing checks for it there — it just silently produces "No commits
between main and issue-<n>/<role>" at PR-create time (spawn.py:4187 comment
already documents this failure shape for the spawn-time case; the same
symptom recurs mid-run with no matching guard).

## Merge-side surface: `contract-guard.sh`

`contract-guard.sh` is the single code path that intercepts every
`gh pr merge` regardless of who runs it (human or orchestrator agent), and
it already does per-merge `gh` lookups (PR body/commits/files, issue
comments) plus a local-checkout `git rev-parse HEAD` read when a checkout is
resolvable (`target_cwd`). It has no notion of session liveness today — it
never reads `spawn.py`'s roster (`ROOT/runs/active.json`, where `ROOT` is
`spawn.py`'s own parent, i.e. the **on-the-record orchestrator repo**, not
the consumer repo `contract-guard.sh` ships into). This is the key
asymmetry for direction (a): `contract-guard.sh` is deliberately
"zero-install" — it ships into arbitrary consumer repos and assumes only
`gh` + `python3` on PATH (header comment, lines 4-10). Reading spawn.py's
roster file assumes co-location with the on-the-record checkout and a
specific filesystem layout that a zero-install consumer-repo hook cannot
assume in general. Piercing that boundary would tie a generic contract hook
to one orchestration tool's private state file — a coupling `contract-guard.sh`
does not have anywhere else in its current design (it only ever reads
`docs/specs/approvers.md` and the target repo's own `.git`, both of which
are properties of the *repo being merged into*, not of the orchestrator
process).

## Directive-only precedent

The role-handoff contract already carries directive-only rules the local
hooks mechanically check afterward (e.g. `scout-directive`/`survey-order-gate.sh`,
`record-shape-directive`/`record-shape-gate.sh` — pattern seen throughout
this session's own system reminders): a directive states the norm, a gate
enforces the mechanical, checkable slice of it. A directive stating
"a multi-phase session finishes before its phase-1 PR is mergeable" has no
existing mechanical gate at all (no hook today reads roster state), so it
would land as pure convention with zero enforcement — the issue explicitly
asks this NOT be "left to orchestrator vigilance."

## Alternatives and their fragility, per the issue's own framing

- (a) refuse/warn merge when `(issue,role)` session is RUNNING: needs
  `contract-guard.sh` (repo-agnostic, zero-install) to reach spawn.py's
  roster file, which lives in a different repo/process than the one being
  merged into. Only works when merge happens on the same host as the
  spawning `spawn.py`, and only if that host's roster file path is
  discoverable from an arbitrary consumer-repo hook — an assumption
  `contract-guard.sh` does not make anywhere else today. Silently fails
  open (like every other lookup failure in this hook) whenever roster
  access isn't possible, i.e. exactly when it's needed.
- (b) extend #732's guard so a same-session-still-running absorbed branch
  re-cuts: reuses `checkout_issue_branch()`'s already-tested absorption
  detection (0-ahead-vs-base) as pure git state on the session's own
  workspace — no cross-process/cross-host roster lookup needed. The gap is
  only that today nothing calls the check again after spawn; adding a call
  right before the phase-2 commit/PR-open step (the `git commit`/`gh pr
  create` prefixes already tracked at `_PROGRESS_BASH_PREFIXES`,
  spawn.py:2251) closes it with the same mechanism #732 already validated.
- (c) directive that a multi-phase session finishes before its phase-1 PR
  is mergeable: as shown above, no mechanical gate exists to enforce this
  today, and it constrains the *orchestrator's* action (when to merge) —
  exactly the "left to orchestrator vigilance" shape the issue says isn't
  acceptable.

`derived: grep -n "checkout_issue_branch(" spawn.py` confirms the single
call site referenced above:
```
$ grep -n "checkout_issue_branch(" spawn.py
4171:def checkout_issue_branch(cwd: str, issue: int, role: str) -> str:
4487:            br = checkout_issue_branch(cwd, issue, role)
```
