---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

`spawn.py watch` was reading its session-existence signal from the
workspace index (`WORKSPACE_INDEX`, `_workspace_index_load()`) while
`spawn.py ps` reads from ROSTER (`_roster_load()`) — two independently
written files, so a session already RUNNING per ROSTER could still hit
`watch`'s "기록 없음" no-record branch if the workspace-index write
hadn't landed yet. Fixed by adding `_roster_fallback_entry()`
(spawn.py, above `_lookup_roster_entry()`) that reconstructs a
workspace-index-shaped `(key, entry)` pair from a live ROSTER entry
(`_alive(pid)` true, `work`/`log` present), and wiring it as a fallback
in `_lookup_roster_entry()` (renamed the pre-existing lookup body to
`_lookup_workspace_entry()`) — the fallback runs only when the
workspace-index lookup returns no entry, so the common/fast path is
unchanged.

Added regression tests in `tests/test_spawn.py`
(`WatchRosterWorkspaceIndexRace`): a live ROSTER entry with an
*empty* workspace index asserts (1) `_lookup_roster_entry()` returns a
usable entry, (2) `_watch()` attaches (rc 0, calls `_await_bounded`)
by role, and (3) the same by auto-selecting role (no `--role` given).

## Why

canonical: docs/issue-1585/reports/implementation/survey.md
Per the survey, this is a pure bugfix — no design choice is open in
making `watch` and `ps` agree on the same source of truth for session
existence, matching issue #1585's acceptance wording.

## Upstream / basis

docs/issue-1585/proposals/watch-roster-fallback.md

## What did not work

None — no dead end was hit during this build; the fallback approach
in the proposal was implemented directly.

## Open findings

None.

## Test run

canonical: `python3 -m pytest tests/test_spawn.py -k "WatchRosterWorkspaceIndexRace or RepoScopedWorkspaceIndex or WatchMultiRoleAmbiguity or WatchFollow"` — result: pass
acceptance: `python3 -m pytest tests/test_spawn.py -k "WatchRosterWorkspaceIndexRace or RepoScopedWorkspaceIndex or WatchMultiRoleAmbiguity or WatchFollow"` — result: pass

```
36 passed in 1.81s
```

Full `tests/test_spawn.py` (no `-k` filter) was also launched this turn
to check for wider regression — no `.on-the-record/test-tiers.json`
exists in this repo, so the test-tier directive's observe-only
full-suite path applies (wall-clock being measured directly rather than
tiered). That run's own result, once observed within this same turn,
is reported in this session's final reply rather than backfilled here.
