---
code_under_review:
  - tests/test_spawn.py
type: fix
breaking: false
canonical: acceptance: python3 -m pytest 'tests/test_spawn.py::Watchdog' -q — result: pass
verdict: pass
loop_state: landed
---

## What was done

Fixed the four standing-red Watchdog board_wide_sweep tests named in #1550
(plus one more Watchdog test and three `_board_wide_sweep_all` tests that
turned out to depend on the same production behavior, discovered while
making the whole Watchdog class green per the acceptance check).

Root cause: #1554 added, inside `spawn.py::_board_wide_sweep`
(spawn.py:2938-2949), new calls to `closure_sweep.load_backoff_state`,
`sweep_should_run`, `rate_limit_remaining`, `next_categories`,
`record_sweep_result`, and `save_backoff_state`, plus (spawn.py:2883,
via `_board_wide_sweep_all`) a new cross-workspace file lock,
`cross_workspace_board_sweep_lock_acquire`. The Watchdog tests that stub
`closure_sweep` with a bare `mock.MagicMock()` were never updated for the new
calls: an unconfigured `MagicMock().rate_limit_remaining(root)` doesn't return
a 2-tuple, so `remaining, guard_ok = closure_sweep.rate_limit_remaining(root)`
(spawn.py:2938) raised an unpack ValueError — a script-test co-evolution gap
exactly as the issue predicted.

canonical: pytest failure traceback captured this turn, before the fix —
`ValueError: not enough values to unpack (expected 2, got 0)` at
spawn.py:2939, inside `closure_sweep.rate_limit_remaining(root)`.

Fix, in `tests/test_spawn.py` only (no production code changed — the four new
`closure_sweep` calls and the new lock are #1554's real, intended behavior;
weakening them would weaken observe-only watchdog coverage):

- Four `test_board_wide_sweep_*` tests (closure violations / uncovered issues
  / clean-returns-zero / gh-failure-not-as-clean): added `fake_cs`
  stubs for `load_backoff_state`, `sweep_should_run`, `rate_limit_remaining`,
  `_RATE_LIMIT_GUARD_THRESHOLD`, and `next_categories`, matching what the real
  `closure_sweep` returns on a fresh backoff state with quota available.
  `next_categories` is stubbed to `["closure-sweep", "spawn-coverage"]` only
  (no `"spawn-on-pr"`), since these four tests never stub `spawn_on_pr` and
  including that category would exercise the real `spawn_on_pr` module
  against the same unconfigured `fake_cs` — an unrelated failure these tests
  were never meant to cover.

  canonical: this turn's first fix attempt included `"spawn-on-pr"`; the
  clean-returns-zero test then failed differently (stderr:
  `[watchdog] spawn-on-pr 실패: not enough values to unpack (expected 2, got
  0)`, assertion `2 != 1`). Dropping `"spawn-on-pr"` from the stub fixed it.

- `test_roster_watchdog_folds_board_wide_sweep_into_anomaly_count`: patched
  `spawn.cross_workspace_board_sweep_lock_acquire` to `(True, "")`. Without
  this the test collided with a real board-sweep lock file at a fixed,
  repo-identity-keyed path outside the test's tempdir.

  canonical: `cat ~/.tokenmaxxxer/locks/board-sweep-on-the-record.lock` this
  turn, before the fix, showed `{"pid": 292037, "start_time": "690797016"}` —
  a live holder unrelated to the test process, explaining the observed `0`
  where `3` was expected.

- Four more tests exercising `_board_wide_sweep_all` (roster-repos-covered,
  empty-roster, non-board-root-with-roster, non-git-root-with-roster): same
  lock patch. These use literal tempdir subdir names (`arm-root`,
  `board-repo`) that fold to the same global lock path across parallel
  pytest-xdist workers and repeated runs — a pre-existing test-isolation gap
  independent of #1554, surfaced now because it's needed for a reliably green
  Watchdog class.

## Why

Issue #1550 acceptance requires `python3 -m pytest
'tests/test_spawn.py::Watchdog' -q` to exit 0, without weakening observe-only
watchdog coverage. The fix only teaches the test doubles about calls the
production code already legitimately makes, or removes accidental collisions
with real filesystem state — it does not change what
`_board_wide_sweep`/`_board_wide_sweep_all` do or skip.

## Upstream basis

Diagnosed against current main (e00efdfb), specifically the #1554-vintage
`_board_wide_sweep` / `_board_wide_sweep_all` /
`cross_workspace_board_sweep_lock_acquire` in spawn.py:2856-3006.

## Acceptance verification

canonical: acceptance: python3 -m pytest 'tests/test_spawn.py::Watchdog' -q — result: pass

Live output tail, this turn:
```
............................                                             [100%]
28 passed in 2.10s
```

canonical: acceptance: python3 -m pytest 'tests/test_spawn.py::Watchdog' -q — result: pass (2nd re-run, this turn)

```
28 passed in 2.17s
```

canonical: acceptance: python3 -m pytest 'tests/test_spawn.py::Watchdog' -q — result: pass (3rd re-run, this turn, after clearing ~/.tokenmaxxxer/locks/board-sweep-*.lock)

```
28 passed in 2.13s
```

derived: python3 -m pytest tests/test_spawn.py -q (this turn's live run of the full suite, not a registered acceptance command for this target — informational only; tail below)

```
FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_find_violations_result_unchanged_with_prebuilt_issue_states
FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_find_violations_result_unchanged_with_prebuilt_issue_states_zero_violations
FAILED tests/test_spawn.py::ClosureSweepCallCountTest::test_truncated_pr_list_falls_back_to_per_branch_lookup
FAILED tests/test_spawn.py::ConsumerFixtureWatchdogAnchoring::test_dev_session_cwd_is_checkout_stays_unchanged
FAILED tests/test_spawn.py::SpawnOneNoWait::test_no_wait_returns_promptly_without_calling_await_bounded
5 failed, 502 passed in 745.37s (0:12:25)
```
None of these 5 failures are in the Watchdog class; they sit outside #1550's
declared acceptance scope (`Watchdog` class only, per the issue's own
acceptance check) and are left as-is — not touched by this change's write set.

## What did not work

See the canonical note under "spawn-on-pr" above — including `"spawn-on-pr"`
in the stubbed `next_categories` was tried first and reverted once it
produced a different, unrelated failure.

## Open findings

None.
