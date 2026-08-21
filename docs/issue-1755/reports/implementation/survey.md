# Survey — issue #1755 (watchdog code-freshness alert dedup)

Skip condition: issue #1755 body carries `design-research-skip: mechanical`
and `assumptions-skip: mechanical` — this is a mechanical bugfix (add
per-HEAD dedup state to an existing check), no product-facing design
decision. Scouting/design-research is skipped per the scout directive's
mandatory skip-record requirement.

## Current state

- `spawn.py:3417` `watchdog_freshness_check(startup_head, cwd=ROOT,
  fetched_this_tick=False)` compares the checkout's current HEAD against
  `startup_head` every tick and returns `(fresh, msg)`. It has no memory
  across calls — every tick with a changed HEAD returns the same
  non-empty `msg`.
- `spawn.py:6971-6976` (CLI `watchdog` role) calls
  `watchdog_freshness_check(startup_head)` once per tick after
  `roster_watchdog(...)`, `print(msg)` when not fresh, and returns
  `WATCHDOG_STALE_CODE_SENTINEL` (95). Nothing currently caches state
  across the process's repeated tick invocations — hence the reported
  repeat-until-restart noise.
- `spawn.py:3361` `watchdog_lock_acquire(lock_path=WATCHDOG_LOCK_PATH, ...)`
  is the existing precedent for a JSON state file under
  `STATE_ROOT` (`spawn.py:3342`, `WATCHDOG_LOCK_PATH = STATE_ROOT /
  "watchdog.lock"`) used for cross-tick state — same pattern this issue's
  dedup state should follow (JSON file, `json.loads`/`json.dumps`,
  `state_path.parent.mkdir(parents=True, exist_ok=True)`).
- Tests: `tests/test_watchdog_freshness.py` already covers
  `watchdog_freshness_check`'s mismatch/match cases
  (`test_head_mismatch_tick_exits_nonzero_with_restart_line`,
  `test_matching_head_ticks_proceed_normally`) with no state-file
  argument — the new dedup param must default to no-op (`state_path=None`)
  so these stay unaffected.

## Write set (frozen)

- `spawn.py` — add a `state_path: Path | None = None` parameter to
  `watchdog_freshness_check`; on a stale-HEAD result, read/write a JSON
  state file keyed by `last_alerted_head` to suppress the `msg` on repeat
  ticks for the same HEAD. Wire the CLI `watchdog` role callsite
  (`spawn.py:6971`) to supply a state path (a sibling of
  `WATCHDOG_LOCK_PATH`, e.g. `STATE_ROOT / "watchdog-freshness.json"`) and
  to only `print(msg)` when `msg` is non-empty.
- `tests/test_watchdog_freshness.py` — add the three-tick unit test
  (changed, unchanged, changed-again → two alerts) plus the empty-state
  case (no state file → first observation alerts and seeds state).

No new dependency, no env var, no schema/migration, no config surface.
