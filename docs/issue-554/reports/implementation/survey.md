---
subject: issue-554
kind: survey
---

## Scope

Pure bugfix / UX-dead-end fix on already-existing `spawn.py` watch
machinery. No new design decision opens beyond which of two roster
sources (`workspace index` vs `roster`/`active.json`) supplies liveness —
resolved directly by reading the existing code (see below), so scouting
is skipped per the scout-directive's second skip condition: the spec
leaves no product-facing design decision open, only a mechanical fix.

## Current state

- `spawn.py:2658` `_lookup_roster_entry(idx, issue, role, repo=None)` —
  looks up watch targets in the workspace index (`WORKSPACE_INDEX`,
  keys `"{repo}/issue-{n}/{role}"`). When `role` is `None` and more than
  one key matches issue `n`, it currently calls `sys.exit()` with a
  message listing candidate role names but never mentioning `--role` as
  the fix (three near-duplicate branches: repo-scoped ambiguous at
  spawn.py:2669-2672, role-given-multi-repo at spawn.py:2678-2680,
  no-repo ambiguous at spawn.py:2685-2687).
- Liveness lives in a separate store: `ROSTER` (`runs/active.json`),
  written by `roster_register()` at spawn.py:4003 with key
  `f"issue-{issue}/{role}"` (no repo scoping) and fields including
  `"pid"`. `_alive(pid)` (spawn.py:1720) does a bare `os.kill(pid, 0)`
  liveness probe; this is the same primitive already used elsewhere
  (e.g. spawn.py:2838, spawn.py:3294) for "is this session live" checks,
  so reusing it here is consistent with existing conventions rather than
  introducing a new liveness definition.
- `main()` (spawn.py:3195) parses two positionals, `role` and `task`
  (nargs="?" each), and dispatches subcommands by string-matching
  `a.role` (e.g. `a.role == "watch"`, `a.role == "kill"`). The `watch`
  branch (spawn.py:3277-3286) reads `--issue` and `--role`
  (`a.watch_role`) but never looks at the second positional (`a.task`)
  — unlike `kill` (spawn.py:3273-3276), which already accepts
  `<role> --issue N` via `a.task`. So the positional-role grammar issue
  #554 asks for is not new invention — it is applying `kill`'s existing
  pattern to `watch`.
- `test_spawn.py` already has a `WatchRegistrationRace`-style class
  (~line 6455) using `_workspace_index_put`/`_lookup_roster_entry`
  directly, and `WatchFollow` (~line 5378) driving `spawn.main()` via
  `sys.argv` — both are the established patterns for testing this area,
  reused for the new tests rather than inventing a third style.

## Write set

- `spawn.py` — `_lookup_roster_entry` (auto-select on single live match,
  actionable ambiguous-error message), `main()`'s `watch` dispatch
  (accept positional role).
- `test_spawn.py` — new tests covering the three acceptance checks,
  extending the existing `WatchRegistrationRace`/`WatchFollow` classes.
- This survey file and the phase-1 proposal that follows it.

No `.env.example`, dependency-manifest, or migration surface is touched
— this is in-process Python logic and argparse wiring only.
