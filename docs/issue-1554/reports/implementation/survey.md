Subject: issue-1554

# Current-state survey

## What exists already

- `spawn.py::_board_wide_sweep(root)` (spawn.py:2921) runs closure-sweep +
  spawn-coverage + spawn-on-pr once per tick, gated by `closure_sweep.sweep_should_run`
  backoff (issue #1498) and a `rate_limit_remaining` guard. It tracks
  `calls_made` and only *reports* an overage (`예산 초과`) after already making
  all the calls — there is no actual per-tick cap, and no carry-over queue:
  every category always runs every tick when not backed off.
- `spawn.py::_board_wide_sweep_all(root, d_all)` (spawn.py:2856) fans the sweep
  out per distinct roster target repo (issue #1276) — each workspace's watchdog
  independently walks its own roster and calls `_board_wide_sweep` once per
  target repo, per tick. Nothing dedups this across *workspaces* sweeping the
  same repo.
- `spawn.py::watchdog_lock_acquire` (spawn.py:3003) is a single-instance lock,
  but its path is `WATCHDOG_LOCK_PATH = STATE_ROOT / "watchdog.lock"`, and
  `STATE_ROOT` (spawn.py:76) defaults to `ROOT / "runs"` where `ROOT =
  Path(__file__).resolve().parent` — the *installed checkout* spawn.py is
  running from. Each role-session workspace has its own plugin checkout, so
  each gets its own `STATE_ROOT`/lock file. This is exactly the #1510
  enforcement gap named in the issue: single-instance is enforced per
  checkout, not per target repo across checkouts. `_repo_identity(cwd)`
  (spawn.py:4094) already gives a pure-local (no gh call) repo key used
  elsewhere for multi-board output labels — reusable as a lock key.
- `closure_sweep.py::issue_state_index_all` / `_pr_index_all` /
  `find_violations` (gates/closure_sweep.py:91-249) are the board-wide gh
  calls billed each tick; none of them use conditional requests. Contrast
  with `spawn.py::_issue_comments` (spawn.py:1323), which already does
  ETag/If-None-Match conditional re-fetch per-issue (issue #1459) — that
  pattern is the one to extend to the board-wide list calls.
- `closure_sweep.py::load_backoff_state`/`save_backoff_state`/
  `sweep_should_run`/`record_sweep_result` (gates/closure_sweep.py:381-450,
  issue #1498) already give a per-repo local JSON state file
  (`runs/gh_quota_backoff.json`) for tick-interval backoff. No carry-over
  queue exists yet — backoff skips a whole tick's sweep, it does not defer
  a partial tick's remaining categories.
- `closure_sweep.accumulation_trend` / `requirement_drift` (both local-only,
  gh-free) already run unconditionally every tick regardless of backoff/budget
  — requirement 4 (local-first) is already satisfied for these two signals;
  `tests/test_watchdog_local_signals.py` already asserts this.
- `tests/test_gh_quota_guard.py` covers the existing rate-limit guard/backoff;
  no existing test asserts carry-over completeness across ticks, cross-workspace
  dedup, or conditional-request billing for the board-wide list calls.

## Write set (frozen)

- `gates/closure_sweep.py` — per-tick call-budget queue with carry-over
  (req 1), ETag/conditional board-list requests (req 5).
- `spawn.py` — cross-workspace board-sweep lock keyed by repo identity
  (req 2), wiring the budget queue into `_board_wide_sweep`.
- new test file tests/test_board_sweep_budget_carryover.py — req 1 + req 3.
- new test file tests/test_board_sweep_cross_workspace_lock.py — req 2.
- new test file tests/test_board_sweep_etag.py — req 5.

## Skip condition

Not applicable — scouting is skipped for this task because it is
infrastructure-shaped (gh-call budgeting/locking/caching inside an existing
watchdog), not a product-facing surface with external exemplars to compare
against; the design space is fully determined by the issue's binding
constraint (carry-over, never drop) and the existing local primitives
surveyed above.
