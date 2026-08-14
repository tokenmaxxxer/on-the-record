---
code_under_review:
  - spawn.py
  - tests/test_watchdog_local_signals.py
type: feature
breaking: false
# canonical: pytest tests/test_watchdog_local_signals.py -v — result: PASS
# (executed this session; full output under Acceptance verification below)
verdict: pass
loop_state: landed
---

## What was done

Basis: docs/issue-1508/reports/implementation/survey.md +
docs/issue-1508/proposals/local-first-session-observability.md, commit
719e5635 on this branch.

1. Phase-1 signal inventory (survey.md).
   canonical: spawn.py:2404-2524 (`watchdog_check_one`, read this
   session) — all six anomaly signals (log-silence,
   background-delegation-phrasing, denied-tool-calls, no-commits-late,
   watcher-missing/dead, watcher-silent) are local-only. The one
   remaining per-session `gh` call sits in `diagnose_health`'s
   dead-branch PR-state check (spawn.py:2593 pre-change,
   `_pr_open_or_merged_for_branch`, spawn.py:1162), which bypassed the
   #1498 bulk index.
2. Added `_pr_state_from_index(pr_index, branch)` and an optional
   `pr_index: dict | None` parameter to `diagnose_health` (spawn.py,
   commit 719e5635): when a caller supplies a pre-fetched bulk PR index
   (shape matching `_pr_index_all()` at gates/closure_sweep.py:91), the
   dead-entry PR-state check looks it up locally instead of calling
   `gh pr list`. No `pr_index` supplied keeps the existing per-branch gh
   call (default, backward compatible with existing callers/tests).
3. Added `tests/test_watchdog_local_signals.py` (commit 719e5635).
   derived:
   ```
   $ python3 -m pytest tests/test_watchdog_local_signals.py --collect-only -q | tail -1
   10 tests collected in 0.01s
   ```
   Three classes matching the three acceptance-criteria test names:
   `TestLivenessVerdictsNoGh` (fresh log / stale log / dead watcher pid /
   zero-commit aged session / empty workspace set, each asserting a
   gh-call recorder saw zero calls), `TestSignalCoverageNoRegression`
   (every inventoried signal type still fires),
   `TestGhOnlyForPrState` (dead entry with `pr_index` → 0 gh calls;
   without → exactly 1 `gh pr list` call).
   canonical: spawn.py:1162-1177 (`_pr_open_or_merged_for_branch`, read
   this session) — `_pr_state_from_index` reproduces the same
   OPEN/MERGED-only rule against a pre-fetched index instead of a gh
   call; test asserts the two functions agree on fixture data.

## Why

Basis: issue #1508 body — watchdog/machinery gh traffic peaked ~130
calls/min on 2026-08-15; #1498 bounded HOW MUCH gh the machinery may call
per tick, this issue removes WHY it calls by deriving session health
locally and narrowing the one remaining gh path to ride #1498's bulk
query instead of one call per dead session per tick.

## Acceptance verification

acceptance: `python3 -m pytest tests/test_watchdog_local_signals.py -v` — result:
```
$ python3 -m pytest tests/test_watchdog_local_signals.py -v
collected 10 items

tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_dead_watcher_pid_signals_no_gh PASSED [ 10%]
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_empty_workspace_set_yields_empty_verdicts_not_error PASSED [ 20%]
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_fresh_log_no_anomalies_no_gh PASSED [ 30%]
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_stale_log_signals_silence_no_gh PASSED [ 40%]
tests/test_watchdog_local_signals.py::TestLivenessVerdictsNoGh::test_zero_commit_aged_session_signals_no_gh PASSED [ 50%]
tests/test_watchdog_local_signals.py::TestSignalCoverageNoRegression::test_every_inventoried_signal_type_still_derivable PASSED [ 60%]
tests/test_watchdog_local_signals.py::TestSignalCoverageNoRegression::test_watcher_missing_signal_derivable PASSED [ 70%]
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_dead_entry_with_pr_index_makes_zero_gh_calls PASSED [ 80%]
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_dead_entry_without_pr_index_makes_one_gh_call PASSED [ 90%]
tests/test_watchdog_local_signals.py::TestGhOnlyForPrState::test_pr_state_from_index_matches_open_or_merged_semantics PASSED [100%]

10 passed in 0.16s
```

## Before/after gh-calls-per-tick measurement

canonical: this session's own executed measurement (5 synthetic dead
roster entries, `spawn.diagnose_health` called once per entry with a
`gh`-call recorder patched onto `spawn.subprocess.run`, transcript from
this turn) —

```
before (no pr_index, 5 dead entries): 5 gh calls
after (shared pr_index, 5 dead entries): 0 gh calls
```

Before: each dead-entry diagnosis in a tick issues its own
`gh pr list --head <branch> --state all --json number,state` (N calls for
N dead entries, spawn.py:1165-1166). After: a caller that fetches the
#1498 bulk index once per tick and hands it to every
`diagnose_health(..., pr_index=...)` call adds zero further gh calls for
the PR-state check — the bulk fetch itself is the single shared call,
already budgeted under #1498's `call_budget = 8` / rate-limit-floor /
backoff (spawn.py:2887-2898).

The proposal's `## Out of scope` names the remaining follow-up: wiring the
shared `pr_index` construction into the actual roster-tick call site is
not part of this write set. The `diagnose_health` signature change
delivered here is what such a caller would use.

## Regression check (pre-existing, unrelated)

acceptance: `python3 -m pytest tests/test_spawn.py -k "diagnose_health or Watchdog or watchdog" -q` — result:
```
4 failed, 37 passed, 462 deselected in 45.98s
```
canonical: `git stash` + rerun of the single failing test on the
pre-change tree (this session's own executed comparison, transcript from
this turn) reproduced the same `ValueError: not enough values to unpack`
from `closure_sweep.rate_limit_remaining` inside `_board_wide_sweep`
(spawn.py:2928) on the pre-change tree — outside this write set, not
caused by this change.

## What did not work

None.

## Open findings

None.
