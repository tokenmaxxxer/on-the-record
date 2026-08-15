---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

`spawn.py watch` reported "기록 없음" (no record) for a role session
that `spawn.py ps` simultaneously showed RUNNING. Skip condition: pure
bugfix, per docs/issue-1585/reports/implementation/survey.md — `watch`
and `ps` read two different registries (workspace index vs ROSTER) for
the same existence question, and no design choice is open in aligning
them.

## Constraints

- No blocking behavior added to any `watch` code path (issue's own
  acceptance wording).
- `ps`'s existing behavior/output must not change.
- Regression test must assert: a registered, running session makes
  `watch` attach, never "기록 없음".

## Rationale

Considered rewriting `watch` to read ROSTER exclusively (dropping the
workspace-index lookup). Rejected: the workspace index carries `log`/
`watcher_pid`/`watcher_armed_at` fields ROSTER doesn't, and multi-repo
scoping (`-C`) is keyed off the workspace index's repo-qualified key
(spawn.py:4226) — switching the primary source would be a much larger,
riskier change touching every `watch`/`ps`/rearm call site for no
benefit over a narrow fallback.

Chosen instead: keep the workspace index as the primary source (no
behavior change for the common case), and add a fallback that consults
ROSTER only when the workspace-index lookup misses — reusing the
`_alive()` liveness check `ps` and `_live_roster_matches()` already use,
so both commands agree on what counts as "running" from one function.

## What will be done

- Add `_roster_fallback_entry()` in spawn.py: given issue/role/repo,
  look up a live ROSTER entry (`_alive(pid)` true, `work`/`log` present)
  and reconstruct a workspace-index-shaped `(key, entry)` pair from it.
- `_lookup_roster_entry()` calls the existing workspace-index lookup
  first (renamed `_lookup_workspace_entry()`), and falls back to
  `_roster_fallback_entry()` only when that lookup returns no entry.
- Add regression tests in `tests/test_spawn.py` that register a live
  ROSTER entry with no matching workspace-index entry and assert
  `_lookup_roster_entry()` returns a usable entry and `_watch()`
  attaches (rc 0, calls `_await_bounded` with the right log path)
  instead of returning the no-record error.

## Accumulation

This adds one fallback function called from the single existing lookup
site (`_lookup_roster_entry()`), not a per-call-site inline pattern —
future `watch`/`ps`/rearm consistency fixes extend this same helper
rather than repeating an inline ROSTER lookup at each call site. No
repeated per-role file (`roles/*.json`-style) is touched, and no
subprocess/`gh` calls are added.

## Out of scope

- Making the two registries a single store (survey names this as a
  bigger, unrelated change).
- Any change to `ps`'s own output or to the workspace-index write
  ordering in `_spawn_one()`.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k WatchRosterWorkspaceIndexRace`
passes, plus the existing `RepoScopedWorkspaceIndex` and
`WatchMultiRoleAmbiguity` suites stay green (no regression in
repo-scoping or multi-role ambiguity handling).
