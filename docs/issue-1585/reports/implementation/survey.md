# Survey — issue #1585

derived: `grep -n "기록 없음\|def watch\|roster_ps\|_roster_load\|_workspace_index_load\|_lookup_roster_entry" spawn.py`

## Skip condition

Pure bugfix — no design decision is open.

canonical: spawn.py:2264-2271 (`roster_ps()` body)
`ps` reads its RUNNING/existence signal from `_roster_load()` (ROSTER,
`runs/active.json`).

canonical: spawn.py:4423-4427 (`_watch()` head)
`watch` reads its existence signal from `_workspace_index_load()`
(WORKSPACE_INDEX, `runs/workspaces.json`) via `_lookup_roster_entry()`
— despite the name, that function looked up the *workspace index*, not
ROSTER (pre-fix body, spawn.py:4377-4420 before this change).

canonical: spawn.py:7434 and spawn.py:7462 (pre-fix `_spawn_one()`)
These are two separate files, written by separate calls
(`roster_register()` vs `_workspace_index_put()`) at separate points in
`_spawn_one()`: the workspace index write happens before `fork()`
(spawn.py:7434), the roster write happens after, in the fork child
(spawn.py:7462) or in the non-bounded continuation (spawn.py:7548).

A caller can observe ROSTER already carrying a live entry while
WORKSPACE_INDEX has not picked up the corresponding key yet — `watch`
then falls through to the no-record branch

canonical: spawn.py:4442-4445 (pre-fix)

even though `ps` reports the same role RUNNING, matching the symptom
described in issue #1585's body. No R-id design choice is open here;
the fix makes `watch`'s existence check consult the same live-session
ground truth `ps` already uses (ROSTER), as a fallback only when the
workspace-index lookup misses.

## Write set

- `spawn.py` — `_lookup_roster_entry()` / new `_roster_fallback_entry()`
  helper.
- `tests/test_spawn.py` — regression test class
  `WatchRosterWorkspaceIndexRace`.

## Constraint from the issue

"Do not weaken watch coverage: no blocking behavior may be added to
watch paths." — the fix is a synchronous dict lookup against
`_roster_load()` (already loaded elsewhere in the same call path, e.g.
`_live_roster_matches()`, canonical: spawn.py:4355), no new
sleep/poll/retry loop added.
