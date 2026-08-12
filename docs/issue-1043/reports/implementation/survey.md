# Survey — issue #1043 (watcher-dead false warnings)

## Scope skip condition

None claimed — this is a pure bugfix per the scout-directive's own skip
condition: the issue names an exact defect (stale-auto-armed-pid check
fires while a live `watch --follow` covers the session) and the direction
section already fixes the design ("count ANY live watcher... clear stale
pids on replacement"). No product-facing or exemplar-comparable decision is
open. Scouting is skipped on this ground.

## Current state (`spawn.py`, single-file root module — no `src/` layout
in this repo)

- `watchdog_check_one()` (spawn.py:2245-2277, "signal 5", issue #488): reads
  `ws_entry = _workspace_index_load().get(ws_key)`, then:
  - `watcher_pid is None` -> `watcher-missing`.
  - `not _watcher_looks_real(watcher_pid, issue, role)` -> `watcher-dead`.
  - else (real & alive) -> signal 6 `watcher-silent` staleness check.
- `_workspace_index_put(issue, role, work, log, watcher_pid=None,
  watcher_armed_at=None)` (spawn.py:3497-3529): writes the workspace-index
  entry. Each call **replaces the entry wholesale** — `entry = {"work":
  work, "log": log}`, then `watcher_pid`/`watcher_armed_at` are added only
  when the caller supplies a non-`None` value that same call. A prior
  `watcher_pid` set by an earlier call is dropped whenever a later call
  omits it. This is already the "clear stale pids on replacement"
  primitive the issue asks for — it just isn't invoked anywhere for a
  `watch --follow` session today.
- `watcher_pid` is populated in exactly one place today: auto-arm at spawn
  time (spawn.py:5649-5651, `_workspace_index_put(..., watcher_pid=
  wproc.pid, watcher_armed_at=time.time())`), when `_spawn_one()` launches
  a detached `spawn.py watch --issue <n> --follow --self-heal` child.
- `_watch()` (spawn.py:3713-3871), the function backing `spawn.py watch
  --follow` (whether auto-armed or invoked directly by an orchestrator),
  never writes to the workspace index. It only reads the roster/workspace
  index to resolve `key`/`entry`/`work`/`log_path`, then loops calling
  `_await_bounded()`.
- Consequence matching the issue: when the auto-armed watcher process
  dies (or was never armed) but an orchestrator separately runs `spawn.py
  watch --issue <n> --follow` and is actively covering the session, that
  follow process registers nowhere. `watchdog_check_one()` still reads the
  stale/absent `watcher_pid` from the auto-arm write and flags
  `watcher-dead`/`watcher-missing` every tick, even though watch coverage
  is real.
- `_watcher_looks_real(pid, issue, role)` (spawn.py:1939-1967): liveness +
  `/proc/<pid>/cmdline` identity check (must contain `"watch"`, the issue
  number, and — if given — the role string). Already generic enough to
  validate a follow process's own pid without change.

## Related prior ownership pattern (issue mentions #1013/#1035)

- docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md is
  a different subsystem (decision_queue session ownership), not watcher
  registration — no reusable code path there. The "attribute liveness
  like #1013/#1035" instruction in #1043 is read as a citation of the
  *ownership-attribution pattern* (don't judge liveness from one stale
  signal when another live owner exists), not a shared function to call.

## Test scaffolding already in place

- `tests/test_spawn.py` `WatcherAutoArm` (line ~8170) covers
  `watchdog_check_one()` directly against a synthetic `WORKSPACE_INDEX`.
- `tests/test_spawn.py` `WatchFollow` (line ~6812) covers `_watch(...,
  follow=True)` end-to-end against a synthetic workspace index + roster +
  events log, with `_await_bounded` mocked to drive offset progress. This
  is the natural home for the two regression cases (`-k watcher_dead`
  acceptance filter): a stale auto-armed pid + a live follow watcher (no
  flag), and no watcher at all (flag fires) — both already partially
  covered by `WatcherAutoArm`, but the acceptance's `-k watcher_dead`
  filter requires new test names containing the literal substring
  `watcher_dead`.

## Write set (frozen for the proposal)

- `spawn.py` — `_watch()`: on entering follow mode, register the
  follow process's own pid into the workspace index via the existing
  `_workspace_index_put()` primitive, before the follow loop starts.
- `tests/test_spawn.py` — two new regression cases under `-k
  watcher_dead`.

No new dependency, no new env var, no schema/migration.
