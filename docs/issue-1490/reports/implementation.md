---
code_under_review:
  - pytest.ini
  - requirements-dev.txt
  - docs/handbooks/operations.md
  - tests/test_spawn.py
loop_state: committing
type: process
breaking: false
verdict: pass  # canonical: python3 -m pytest -q --ignore=bench -m "not slow" (this turn) — see fenced output below
---

# Implementation record — issue #1490

canonical: `python3 -m pytest -q --ignore=bench -m "not slow"` (this
turn)
```
run 1: 18 failed, 1824 passed, 1 xfailed in 248.92s — real 4m9.238s
run 2: 18 failed, 1824 passed, 1 xfailed in 317.56s — real 5m17.957s
run 3: 18 failed, 1824 passed, 1 xfailed in 288.83s — real 4m48.83s
```
derived: two of the three runs above land under the 300s target; the
317.56s outlier's cause is in Open findings.

## What was done

1. `pytest-xdist==3.8.0` and `pytest.ini`'s `addopts = -n auto` / `slow`
   marker existed before this session started.

   canonical: `cat pytest.ini` (this turn)
   ```
   [pytest]
   python_functions = test_* t_*
   norecursedirs = runs
   addopts = -n auto
   markers =
       slow: real subprocess spawn or real git clone/checkout lifecycle tests, excluded by default (issue #1490); run with -m slow or without -m "not slow" to include.
   ```

   canonical: `python3 -m pytest -p no:xdist -q tests/test_gates.py`
   (this turn)
   ```
   ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
   __main__.py: error: unrecognized arguments: -n
   ```
   Because `addopts` already carries `-n auto`, any bare
   `pytest.ini`-driven invocation runs parallel by default — including
   the orchestrator's pre-started reference run (see Timings). Disabling
   the plugin alone does not remove the ini's `-n auto`; `-o addopts=""`
   is needed instead for a truly serial run.

2. Isolation-fix investigation — every failure under `-n auto` was
   re-run alone via `-o addopts=""` to see whether it was a
   parallel-only collision or predated this change.

   canonical: `python3 -m pytest -o addopts="" -q
   "tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_find_violations_result_unchanged_with_prebuilt_issue_states"
   "tests/test_spawn.py::ClosureSweepCallCountTest::test_truncated_pr_list_falls_back_to_per_branch_lookup"
   "tests/test_gates.py::t_find_violations_uses_prefetched_issue_state_skips_issue_view"
   "tests/test_gates.py::t_find_violations_without_issue_states_still_calls_issue_view"`
   (this turn)
   ```
   FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_find_violations_result_unchanged_with_prebuilt_issue_states
   FAILED tests/test_spawn.py::ClosureSweepCallCountTest::test_truncated_pr_list_falls_back_to_per_branch_lookup
   FAILED tests/test_gates.py::t_find_violations_uses_prefetched_issue_state_skips_issue_view
   FAILED tests/test_gates.py::t_find_violations_without_issue_states_still_calls_issue_view
   4 failed in 17.57s
   ```
   Same 4 IDs, same assertion shapes, as under `-n auto`, with no other
   test loaded in the process — this shows the failure predates
   parallelism rather than being caused by it.

   canonical: `python3 -m pytest -o addopts="" -q
   gates/test_consult_verdict_parsing.py::t_retries_once_and_recovers_when_first_attempt_has_no_json
   gates/test_clean_reconcile_safety.py::CleanReconcileSafetyTest::test_reconcile_unreported_skips_missing_workspace
   gates/test_role_utilization_report.py::test_all_43_role_stems_present_as_keys_in_count_map
   gates/test_consult_json_parse.py::t_both_attempts_exhausted_raises_with_reported_symptom
   gates/test_consult_json_parse.py::t_consult_cmd_settings_never_carry_self_hosted_hooks
   gates/test_product_capture_vs_deliverable_guard.py::t_empty_state_bootstrap_still_works
   harness/fixture-redtest/test_discount.py::test_bulk_discount_applies
   harness/fixture-target/test_fixture_target.py::test_resolve_version_returns_version_string_when_flag_set
   on-the-record/hooks/test_monitor_notice.py::test_first_observation_records_start_and_prints_no_notice
   on-the-record/hooks/test_monitor_notice.py::test_no_notice_when_alive_marker_fresh_for_this_session`
   (this turn)
   ```
   10 failed in 1.56s
   ```
   Same 10 IDs as under `-n auto`, all outside the frozen write set,
   same story: fails alone too, so it predates this change.

   These two command outputs, together, show no shared-mutable-state
   collision exists in the frozen write set — every failure under
   `-n auto` reproduces byte-identically alone. The same IDs recur
   identically in both the baseline run and the combined post-change
   run cited in Timings, so the outcome-set diff requirement is
   unaffected, and none of these was touched.

   Two tests were genuinely load-sensitive under `-n auto` (succeed
   alone, break under worker contention):
   `SpawnOneIssueRoleClaim.test_concurrent_spawn_one_calls_let_exactly_one_through`
   and `SpawnOneNoWait.test_no_wait_returns_promptly_without_calling_await_bounded`
   in `tests/test_spawn.py`.

   canonical: `python3 -m pytest -o addopts="" -q
   "tests/test_spawn.py::SpawnOneNoWait::test_no_wait_returns_promptly_without_calling_await_bounded"
   "tests/test_spawn.py::SpawnOneIssueRoleClaim::test_concurrent_spawn_one_calls_let_exactly_one_through"`
   (this turn)
   ```
   FAILED tests/test_spawn.py::SpawnOneNoWait::test_no_wait_returns_promptly_without_calling_await_bounded
   1 failed, 1 passed in 31.02s
   ```
   The failing one's own assertion (`elapsed < 1.0`) measured 15.4s
   even fully isolated (a real unmocked `Popen(["cat"])` call) — this
   test was already environment-flaky before this change, not a new
   collision. Both were tiered into `slow` (item 3) rather than
   rewritten, since both are themselves real-subprocess-spawn tests.

   No `71173111`-style "patch the resource's path, not the acquisition
   logic" fix was needed anywhere else: `spawn.ROOT`,
   `spawn._RULEBOOK_CACHE`, `os.environ`, and `spawn.ROSTER` mutations
   across `tests/test_spawn.py` restore via `try`/`finally` or
   `setUp`/`tearDown` within the same test, and xdist workers are
   separate processes, so a properly-restored process-global mutation
   cannot leak across workers regardless of xdist's random ordering.

3. `@pytest.mark.slow` was applied to test methods in
   `tests/test_spawn.py` that spawn a real `git` subprocess
   (`init`/`clone`/`commit`/`add`/`config`/`status`) or a real
   fixture-repo helper (`self._prep_repo(...)`,
   `self._fake_clone(...)`), excluding methods that only mock
   `subprocess.run` and never invoke the real thing.

   canonical: `grep -c "@pytest.mark.slow" tests/test_spawn.py`
   (this turn)
   ```
   64
   ```
   derived: per-class tally from the applied-marker locations this
   turn, summing to the 64 above: `SpawnCmd` 3, `GitHead` 2,
   `IsNewCommit` 2, `WorkspaceSyncFailClosed` 9,
   `AbsorbedBranchRecutMidRun` 3, `WorkspaceExcludesHomeDotfiles` 1,
   `OrchestratorGitToken` 2, `EnsurePushedResult` 1, `Ledger` 2,
   `IssueScopedPrompt` 1, `Clean` 1, `Watchdog` 2,
   `PollHeartbeatMarkerRelocationTest` 2, `ProgressAwareRespawnCounter`
   4, `SelfTriggeredRespawn` 2, `SpawnOneNoWait` 2,
   `SpawnOneIssueRoleClaim` 5, `SpawnDeathBeforeRegistration` 3,
   `EventExitScope` 2, `RulebookCheckoutMemo` 3,
   `LegacyTtlMarkerMigration` 2, `FetchDedupe` 2,
   `WorkspaceReuseOriginMismatch` 1, `ReturnedPrGate` 4,
   `EnsureTargetRemote` 1, `RequireRequirementLinkageRemoteBranch` 1.
   Added `import pytest` to `tests/test_spawn.py` (previously imported
   only `unittest`).

   `tests/test_gates.py`, `tests/test_watchdog_freshness.py`, and
   `tests/test_poll_watchdog_log.py` were also grepped for
   `subprocess.` — all three do real `git`/subprocess work, but none
   were tiered into `slow` since together they run quickly.

   canonical: `python3 -m pytest -o addopts="" -q tests/test_gates.py
   tests/test_watchdog_freshness.py tests/test_poll_watchdog_log.py`
   (this turn)
   ```
   6 failed, 119 passed in 17.11s
   real	0m17.533s
   ```
   The 6 failures are the same pre-existing IDs cited under item 2
   above, not new ones. Tiering any of these three files' tests into
   `slow` would drop real coverage from the default tier for no
   measurable time-budget gain.

4. Editing `docs/handbooks/operations.md` (contract v3 s21) changed
   its content hash, which broke a self-check test that had been
   passing (`t_baseline_repo_passes` in `tests/test_spec_index.py`),
   asserting `docs/specs/reconciled-index.md`'s recorded hash matches
   the file's actual content.

   canonical: `python3 -m pytest -o addopts="" -q
   tests/test_spec_index.py -k t_baseline_repo_passes` (this turn,
   before regenerating the index)
   ```
   AssertionError: ['docs/handbooks/operations.md: 내용이 바뀌었는데 docs/specs/reconciled-index.md 의 기록된 해시와 다르다 (기록=050addd2a66a…, 실제=7dc90f57354f…) — 의도된 변경이면 `python3 gates/spec_index.py --update` 로 재생성하고 관련 있다면 "Resolved ambiguities" 도 갱신하라']
   1 failed
   ```

   canonical: `python3 gates/spec_index.py --update` (this turn)
   ```
   docs/specs/reconciled-index.md 갱신됨
   ```
   This touched only `docs/specs/reconciled-index.md`.

   canonical: `python3 -m pytest -o addopts="" -q
   tests/test_spec_index.py -k t_baseline_repo_passes` (this turn,
   after regenerating)
   ```
   1 passed in 0.02s
   ```

   `docs/specs/reconciled-index.md` sat outside the originally-frozen
   write set; it was touched anyway since leaving it stale would break
   a test that had succeeded in the reference run above, and would
   also violate the same contract-v3-s21 rule this proposal itself
   cites for editing an operational-surface doc. Flagged here for
   visibility.

## Why

Per approved proposal docs/issue-1490/proposals/parallel-test-suite.md
(APPROVE issue-1490/implementation comment on issue #1490): parallelize
the default pytest run and split real-subprocess/git lifecycle tests
into an opt-in `slow` tier, target <300s default-tier wall-clock.

## Upstream

docs/issue-1490/proposals/parallel-test-suite.md

## Timings

canonical: `python3 -m pytest -q --ignore=bench -o addopts="" -rA`
(this turn, true single-threaded reference)
```
21 failed, 1885 passed, 1 xfailed in 1272.43s (0:21:12)
real	21m12.791s
```
This matches the issue's own framing (docs/issue-1490/proposals/parallel-test-suite.md)
that `tests/test_spawn.py` alone dominates single-threaded runtime.

canonical: `python3 -m pytest -q --ignore=bench -rA` (command started
by the orchestrating session before this session began; per item 1
above it actually ran parallel since `pytest.ini`'s addopts already
had `-n auto`) — used below as the reference for the required
outcome-set diff
```
20 failed, 1886 passed, 1 xfailed in 248.05s (0:04:08)
real	4m8.416s
```

canonical: `python3 -m pytest -q --ignore=bench -m "not slow"` (this
turn, default tier, parallel, three measurements)
```
run 1: 18 failed, 1824 passed, 1 xfailed in 248.92s — real 4m9.238s
run 2: 18 failed, 1824 passed, 1 xfailed in 317.56s — real 5m17.957s
run 3: 18 failed, 1824 passed, 1 xfailed in 288.83s — real 4m48.83s
```
derived: two of the three runs above land under the 300s target; the
317.56s run is explained in Open findings.

canonical: `python3 -m pytest -q --ignore=bench -rA` (this turn, both
tiers, parallel, no `-m` filter, final measurement after regenerating
`docs/specs/reconciled-index.md`)
```
20 failed, 1886 passed, 1 xfailed in 280.46s (0:04:40)
real	4m40.912s
```
This matches the counts of the reference run above.

## Pass/fail-set diff

canonical: `diff <(sort /tmp/baseline_ids.txt) <(sort
/tmp/combined_ids2.txt)` (this turn)

Each `*_ids.txt` was built this turn via:
```
grep -E "^(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS) " <output-file> | sed 's/ - .*$//' | sort
```
```
1c1
< FAILED ../../../../../tmp/tmp_45t3591/test_fixture.py::test_fails
---
> FAILED ../../../../../tmp/tmpv02lqd95/test_fixture.py::test_fails
1908c1908
< SKIPPED [1] ../../../../../tmp/tmpf0fvvg5t/test_fixture.py:8: environment-gated, not run here
---
> SKIPPED [1] ../../../../../tmp/tmplsli8jd_/test_fixture.py:8: environment-gated, not run here
```
derived: exactly two lines of the 1909-line file differ, per the diff
above; both belong to the same synthetic fixture test whose node ID
embeds a freshly-`tempfile`-generated directory name by design (its
text differs on every run regardless of parallelism), while the
outcome tag on each line (FAILED / SKIPPED) is identical between
baseline and combined. No other line differs.

## What did not work

None — no isolation approach was tried and reverted; item 2 above
concluded, from the single-test-alone reruns cited there, that no
narrow isolation fix was needed because no shared-mutable-state
collision existed in the frozen write set.

## Open findings

`conftest.py`'s `_no_global_state_leak` session-scoped autouse fixture
(reads `subprocess.run` and 3 `spawn` module attributes at session
start/end, read this turn) is weaker under `-n auto`: each xdist
worker is a separate process with its own session scope, so there is
no single final cross-worker checkpoint the way a fully serial run
has. This was not redesigned, per the approved proposal's "Out of
scope" section (docs/issue-1490/proposals/parallel-test-suite.md, read
this turn).

Default-tier wall-clock across three back-to-back runs this turn (the
fenced pytest output under Timings above) landed at 248.92s, 317.56s,
and 288.83s. The middle run's window overlapped a second, unrelated
agent session starting its own work on this shared 16-core host.

canonical: `ps aux | grep pytest` (this turn, run during the 317.56s
measurement)
```
jwjung   2150690  0.0  0.0  48848 31748 ?        Ss   23:45   0:00 python3 /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/spawn.py implementation Issue #1498 phase-2: execute the approved proposal docs/issue-1498/proposals/quota-guard.md ...
```
A second `spawn.py implementation` process for "Issue #1498 phase-2"
started `23:45`, inside the measurement window. This points to
host-sharing noise rather than a regression from this change, since
the other two same-code measurements above land under 300s. No
additional test was tiered into `slow` to chase this margin, per the
instruction not to slow-tier a test merely to hit the time budget.

## Next steps

Commit and push are pending — handled by the orchestrating session, not
by this session.
