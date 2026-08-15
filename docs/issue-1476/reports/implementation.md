---
code_under_review:
  - gates/spawn_on_pr.py
  - spawn.py
  - tests/test_spawn_on_pr_park.py
type: fix
breaking: false
verdict: pass  # canonical: python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q — 18 passed, 0 failed (this turn)
loop_state: landed
---

canonical: `python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q` — 18 passed, 0 failed (fenced output below, this turn's run)

## What was done

Implemented the park/re-arm mechanism from
`docs/issue-1476/proposals/park-approval-blocked-respawn.md`:

canonical: gates/spawn_on_pr.py (this turn's edit, see `code_under_review`)
- `spawn_missing_for_pr()` now, per candidate `(subject, role)` pair,
  checks a persisted park state (`runs/spawn_on_pr_parked.json`, per
  `root`). A pair only gets checked for park when a prior-tick entry
  exists AND the current PR number (already computed via
  `spawn._pr_open_or_merged_for_branch`, no new gh call for that part)
  matches the prior one — i.e. no new commit landed. Only then does it
  call `is_approval_blocked()` (new function, wraps a call structurally
  equivalent to `gates/ci.py`'s `_approved_roles_on_issue` — the
  codebase's existing exact-string `APPROVE issue-<n>/<role>` comment
  scanner, structured, never prose matching). `should_park()` is a pure
  function combining these into the park/no-park verdict. A first-time
  candidate (no prior park entry) always spawns, unchanged from before —
  no new gh calls on that path, so existing tests needed no mocking
  changes.
- Added `parked_report(root)` (lists currently-parked `(subject, role)`
  pairs) and `unpark(root, subject, role)` (explicit re-arm, requirement
  2's third trigger) plus a `spawn_on_pr.py unpark --subject --role` CLI
  subcommand.
- `spawn.py`: the watchdog board-sweep print site (next to the existing
  `[watchdog] spawn-on-pr: N건 스폰` line) now also prints
  `[watchdog] spawn-on-pr: waiting-for-human N건: [...]` when
  `parked_report()` is non-empty — parked pairs stay visible instead of
  silently dropping out of watchdog output (requirement 3).
- `tests/test_spawn_on_pr_park.py`: the four Acceptance tests plus three
  supporting tests (pure `should_park()` truth table, explicit `unpark()`,
  and an empty-state case confirming a never-before-seen pair spawns
  without any gh approval lookup).

## Why

canonical: docs/issue-1476/reports/implementation/survey.md (written this
turn) — the survey found no existing structured per-role blocker field
usable before a role has ever written a board record (the exact state a
human-approve-blocked role is stuck in), so the park signal is built from
two already-existing structured primitives instead: the exact-match
APPROVE-comment scanner already present in the codebase, and the
PR-number lookup `spawn_missing_for_pr()` already performs every tick.

## Upstream

Based on: docs/issue-1476/proposals/park-approval-blocked-respawn.md

## Test run

canonical: python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q — this turn's run, fenced below
```
$ python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q
..................                                                       [100%]
18 passed in 0.34s
```

canonical: python3 -m pytest tests/test_spawn_on_pr_park.py tests/test_spawn_on_pr.py -q — same run as above
The four Acceptance tests (`test_approval_blocked_respawn_parked`,
`test_no_18th_spawn_on_replay`, `test_unpark_on_approve_comment`,
`test_parked_entry_still_reported`) are inside that pytest run.

## PR #1485 review response

Reviewer flagged test_cli_watchdog_all_flag_threads_all_scope
(tests/test_spawn.py, class RosterOwnershipScoping) as newly failing on
this branch.

canonical: spawn.py:2999-3013 (watchdog_canonical_guard, read this turn)
The guard rejects any checkout path under `_workspace_base()` unless
`SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1` is set, and this worktree's own
checkout path is under `_workspace_base()`.

canonical: this turn's run — `git checkout main -- spawn.py && python3 -m pytest tests/test_spawn.py::RosterOwnershipScoping::test_cli_watchdog_all_flag_threads_all_scope -x` (then `git checkout HEAD -- spawn.py` to restore)
Swapping in main's spawn.py verbatim into this worktree and re-running
the same test failed identically (same watchdog_canonical_guard
rejection message), so the failure is environmental to this sandbox
worktree, not caused by this branch's diff.

canonical: `git diff main..HEAD -- spawn.py` (this turn's run)
The diff's spawn.py hunks touch only `_board_wide_sweep`'s print site
and add the new gc-monitor-alive functions; they never touch `main()`'s
`a.role == "watchdog"` branch or the --all/all_scope argument threading.

A second, independent cause stacked on top: a stale runs/watchdog.lock
(gitignored, left over from a prior run in this worktree) made
watchdog_lock_acquire() also reject.

canonical: this turn's run — `cat runs/watchdog.lock` then `ps -p <pid>`
The recorded pid was no longer running; removed the stale lock file
this turn (untracked, gitignored path, not part of `code_under_review`).

canonical: `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 -m pytest tests/test_spawn.py::RosterOwnershipScoping::test_cli_watchdog_all_flag_threads_all_scope tests/test_spawn_on_pr_park.py -v` — this turn's run, fenced below
```
tests/test_spawn.py::RosterOwnershipScoping::test_cli_watchdog_all_flag_threads_all_scope PASSED [ 12%]
tests/test_spawn_on_pr_park.py::test_approval_blocked_respawn_parked PASSED [ 25%]
tests/test_spawn_on_pr_park.py::test_no_18th_spawn_on_replay PASSED      [ 37%]
tests/test_spawn_on_pr_park.py::test_unpark_on_approve_comment PASSED    [ 50%]
tests/test_spawn_on_pr_park.py::test_parked_entry_still_reported PASSED  [ 62%]
tests/test_spawn_on_pr_park.py::test_empty_state_spawns_normally PASSED  [ 75%]
tests/test_spawn_on_pr_park.py::test_should_park_pure PASSED             [ 87%]
tests/test_spawn_on_pr_park.py::test_unpark_explicit PASSED              [100%]
8 passed in 0.68s
```
No --all/all_scope threading code was changed — the park gate does not
touch that path (issue req 4 does not license a test update here; none
was made).

## What did not work

None.

## Open findings

None.
