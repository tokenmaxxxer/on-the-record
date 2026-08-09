## Current-state survey — issue #559

Scope: `spawn.py` roster/watch/workspace-index machinery. No new dependency,
no schema migration, no product-facing surface — internal CLI observability
for the orchestrator. Scouting skipped: this is an internal ops-tooling
change with no external product category to benchmark against; the
acceptance checks and the file's own existing conventions (roster vs.
workspace-index split, `_watcher_looks_real`, `_workspace_index_put`)
fully determine the design space.

### Two separate registries already exist

- `ROSTER` (`runs/active.json`, via `_roster_load`/`_roster_save`,
  spawn.py:1686-1740): one entry per running role session — `pid`
  (wrapper_pid of the `claude` subprocess... actually the roster's `pid`
  field, `ts`, `role`, `issue`, `log`, `work`. Read by `roster_ps()`
  (spawn.py:1742-1762), which prints RUNNING/DEAD per entry and prunes dead
  ones. It currently prints nothing about watchers at all.
- `WORKSPACE_INDEX` (via `_workspace_index_load`/`_workspace_index_put`,
  spawn.py:2550-2595): keyed `f"{_repo_identity(work)}/issue-{issue}/{role}"`.
  Holds `work`, `log`, and optionally `watcher_pid` — set only when a spawn
  auto-arms a watcher (spawn.py:4021-4022, inside `_spawn_one`'s
  parent-return branch, spawn.py:3997-4026). No timestamp field for when
  the watcher was armed, and no `follow` flag stored (the auto-armed
  watcher always runs `watch --follow`, spawn.py:4010-4016, so `follow` is
  always true for it — but there is no field recording that fact for `ps`
  to print).

### Watcher liveness check already exists

`_watcher_looks_real(pid, issue)` (spawn.py:1698-1717) is the existing dead
-watcher check used by `watchdog_check_one` signal 5 (spawn.py:1853-1866):
`_alive(pid)` plus, on Linux, a `/proc/<pid>/cmdline` check that the pid is
actually a `watch` call for this issue (guards against pid-reuse). This is
exactly the check `ps` needs to decide RUNNING vs. dead-watcher — no new
liveness primitive is needed, just reuse.

### `ROSTER` key vs. `WORKSPACE_INDEX` key mismatch

`ROSTER` keys are bare `issue-<n>/<role>` (spawn.py:2868-2870 confirms
`roster_kill` builds the same bare form). `WORKSPACE_INDEX` keys carry a
repo-identity prefix (`_repo_identity(work)/issue-<n>/<role>`). `_watch`
already does this exact bare->prefixed lookup at spawn.py:2806-2811 when it
needs to cross-reference the two registries — that lookup pattern
(`_repo_identity` + string match) is the one to reuse in `ps` rather than
inventing a new join.

### `watch --all --follow` never terminates

`_watch_all` (spawn.py:2830-2865) loops `while True`, polling
`_workspace_index_load()` every 0.2s, and returns only on
`KeyboardInterrupt`. Even after every session in the index has emitted
`session-end` (tracked in the local `seen_end` set), the loop keeps polling
forever — confirmed by reading the loop body: there is no check of
`len(seen_end) == len(idx)` anywhere, and no exit path besides SIGINT. This
matches the issue's "Additional finding" exactly. `_watch`'s (singular)
`--follow` loop, by contrast, already exits at the first `session-end`
event (spawn.py:2782-2788) or after a `stall_timeout_min` of no progress
(spawn.py:2822-2827) — that per-session exit-on-no-progress precedent is
the model to extend to `_watch_all`.

### CLI wiring

`main()` (spawn.py:3233 onward) parses the `watch` subcommand; the test
`test_all_flag_rejects_issue_combo_in_cli` (test_spawn.py:6693-6697) shows
`--all` already exists as a flag and is validated against `--issue`. Adding
`--until-idle` is an additive argparse flag on the same subcommand.

### Existing test conventions

`test_spawn.py` has `WatcherAutoArm` (line 6358), `WatchAll` (line 6620),
and `Watchdog` (line 3181) test classes already covering the exact pieces
this issue touches, each with its own `setUp` that swaps `spawn.ROSTER` /
`spawn.WORKSPACE_INDEX` to a tempdir path and registers via
`_workspace_index_put`/`roster_register`. New tests belong alongside these,
following the same fixture-swap pattern (no new test infrastructure
needed).

### Write set implied

- `spawn.py`: `roster_ps()` (join roster+workspace-index, print
  watcher/UNWATCHED line), `_workspace_index_put` (add `watcher_armed_at`
  field), the auto-arm call site (pass armed-at timestamp), `_watch_all`
  (add `until_idle` param + exit condition), `main()` (add `--until-idle`
  flag, thread through to `_watch_all`).
- `test_spawn.py`: new tests under/near `WatcherAutoArm` and `WatchAll`.
