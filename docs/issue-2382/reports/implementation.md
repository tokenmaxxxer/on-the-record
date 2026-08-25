---
issue: 2382
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: (none — build-now delivery, contract v3 s19a; no prior proposal round)
    sha:
code_under_review:
  - spawn.py
  - on-the-record/directive/spawn-and-board.md
type: perf
breaking: "no"
verdict: pass
---

acceptance: `python3 -m py_compile spawn.py` — result:
```
COMPILE_OK
```

# issue-2382 — implementation record

canonical: spawn.py (this commit) and on-the-record/directive/
spawn-and-board.md (this commit) — frontmatter `verdict`/`breaking`/`type`
above are substantiated by the "Executed evidence" section below.

## What was done

canonical: spawn.py (this commit) — `_BOOTSTRAP_PHASES` tuple and every
`with _timed(...)` call site in `_spawn_one()`. acceptance: `python3 -m
py_compile spawn.py` — result:
```
COMPILE_OK
```

Audited every bootstrap phase in `_spawn_one()` for real vs. false
dependencies (acceptance check 1) and restructured three false ones to
dispatch in the background and join later, using the file's existing
`ThreadPoolExecutor(max_workers=1)` + `.result()` idiom (same pattern as
the pre-existing `cross_family`, issue #2061):

1. `core_plugin_dirs()` (zero arguments, no role/cwd/issue dependency) —
   now dispatched right after the admission gate clears instead of at the
   "core" phase deep in the sequence.
2. The gh issue-body fetch — now dispatched right after `branch`,
   overlapping `directive_write`'s local file writes (previously it ran
   only after `directive_write` finished); joined right after.
3. `board_snapshot(cwd)` — now dispatched once its two real dependencies
   clear (`write_record_skeleton`'s write, and the `cross_family` consult
   call's log write — both land under the same `docs/issue-*/` tree it
   hashes), instead of after `core`/`settings`/`design_bearing`/
   `spawn_cmd` as before.

Documented in spawn.py, inline, why the remaining adjacent phases stay
sequential (admission-first per #2100; skill_resolve before workspace/
branch per #1742/#1774; workspace before branch; design_bearing after
issue_fetch's `body`; spawn_cmd after settings/core/design_bearing).

Added a "SPAWN INDEPENDENT WORK TOGETHER, NOT ONE-THEN-WAIT" bullet to
on-the-record/directive/spawn-and-board.md (acceptance check 2), citing
the #2380 conformance-review + execution-observation observer pair as the
worked example, with a carve-out for spawns with a genuine dependency.

Measured wall-clock for a same-issue conformance-review +
execution-observation pair, sequential vs. concurrent (acceptance check
3) — see "Executed evidence".

## Why

Every restructured call was dispatched early only where nothing between
its dispatch and join point reads or writes something it also touches;
where such an overlap existed, the dependency is real and the ordering
stays sequential, documented at the call site (see "What did not work"
for the one case this missed on the first attempt). No new concurrency
primitive was introduced — every dispatch reuses the file's existing
`ThreadPoolExecutor(max_workers=1)` + `.result()` join idiom (results
actually consumed downstream) or its existing raw-daemon-thread idiom
(genuinely fire-and-forget work), so the dependency reasoning stays
checkable against precedent already in spawn.py rather than introducing a
new pattern to audit.

## What did not work

- First `board_snapshot` placement (right after `directive_write`, before
  the `cross_family` join) missed that `cross_family`'s consult call also
  writes into `docs/issue-<n>/reports/consult-log/`, the same tree
  `board_snapshot` hashes. acceptance: `python3 -m pytest
  tests/test_spawn_observation_recovery.py -k
  test_spawn_one_call_site_fires_after_own_session_end_event -q` — result
  with that first-attempt version applied:
  ```
  E           AssertionError: Lists differ: ['failed-no-commit'] != ['uncommitted-work']
  FAILED tests/test_spawn_observation_recovery.py::SelfTriggeredRespawn::test_spawn_one_call_site_fires_after_own_session_end_event
  ```
  and, on `git stash` (unmodified branch):
  ```
  1 passed in 38.67s
  ```
  Root cause: a race between the background `board_snapshot` hash read
  and the still-in-flight consult-log write flipped a legitimate
  session-made-no-changes case into a false ownership-violation failure.
  Fixed by moving the dispatch point to after the `cross_family` join;
  re-run after the fix is in "Executed evidence".
- A third, size-matched concurrent-vs-sequential timing trial was
  aborted by host-level disk exhaustion. acceptance: `df -h /` — result:
  ```
  파일 시스템     크기  사용  가용 사용% 마운트위치
  /dev/nvme0n1p2  916G  869G   28M  100% /
  ```
  derived: this session's own `ListAgents` call at the same time showed 4
  other peer sessions active on the same host — shared-host contention,
  not this diff. No further pytest-suite-running agents were dispatched
  afterward to avoid adding load to a visibly saturated shared disk; the
  two trials in "Executed evidence" are what ships as measurement.

amendments-reconciled: issuecomment-5407296989 and issuecomment-5407303268
(operator, 2026-08-25, posted after this session started) — both read
before landing. derived: gh api repos/tokenmaxxxer/on-the-record/issues/2382/comments,
this session. First: the fix must hold for any session/target repo (not
just this checkout) and land with no added per-spawn overhead, no new
conflict surfaces, no stall/deadlock modes, no consumer-tree pollution.
Second: the recording/audit-trail procedure itself (issue→spawn→PR
structure, board records, both observer roles, verify-at-landing
evidence, consult-trace logging) must stay exactly as-is — only
incidental cost (serial waits with no dependency, redundant scans,
re-derived-from-scratch work) is in scope; thinning the record itself is
out of scope. canonical: spawn.py (this commit) — every restructured call
is pure control flow with no dependency on this checkout's state, so it
generalizes to any consumer target repo; the claim-rejection fix (see
"Executed evidence") specifically closes a stall-on-exit mode the
restructuring would otherwise have introduced; `board_snapshot`,
`write_record_skeleton`, and the `cross_family` consult-log write still
run, still write the same content to the same paths as before — only the
timing of already-existing background dispatch changed, not what gets
recorded or verified, and no corpus/repo-scan skipping or caching was
added (see "Considered, already covered" above).

## Upstream basis

None. Build-now delivery (`CORE_BUILD_NOW=1`, contract v3 s19a): no
phase-1 proposal round ran for this issue.

## Open findings

None. (resolution path: not applicable — no open findings to resolve.)

## Next steps

None.

## Executed evidence

acceptance: `python3 -m py_compile spawn.py` (checked after every edit in
this delivery) — result:
```
COMPILE_OK
```

acceptance: `python3 -m pytest tests/test_bootstrap_timing.py
tests/test_spawn_pipeline.py tests/test_spawn_board_flows.py
tests/test_spawn_directive_assembly.py tests/test_admission_checklist.py
tests/test_auto_sweep_nonblocking.py tests/test_default_single_phase_flip.py
tests/test_checkpoint_mode.py tests/test_spawn_consult_panel.py -q` (run
before the board_snapshot placement fix) — result:
```
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
2 failed, 377 passed, 1 xfailed in 413.04s (0:06:53)
```
acceptance: `git stash && python3 -m pytest
tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
-q; git stash pop` — result, unmodified branch:
```
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
2 failed in 1.24s
```
Both pre-existing (identical failures with this delivery's changes
stashed out — the second is env leakage: this session's own host env
carries `CORE_BUILD_NOW=1`, which the test's `assertNotIn` trips on
regardless of the code under test).

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py -k
test_spawn_one_call_site_fires_after_own_session_end_event -q` (isolated
re-run after the board_snapshot placement fix) — result:
```
1 passed in 18.12s
```

acceptance: `python3 -m pytest tests/test_spawn_observation_recovery.py
tests/test_watch_hardening.py -q` (broader re-check after the fix) —
result:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
1 failed, 191 passed, 4 xfailed, 1 xpassed in 420.17s (0:07:00)
```
acceptance: `git stash && python3 -m pytest tests/test_spawn_observation_recovery.py -k
"test_delegation_phrasing_signal or test_spawn_one_call_site_fires_after_own_session_end_event"
-q; git stash pop` — result, unmodified branch:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
1 failed, 1 passed in 23.10s
```
`Watchdog::test_delegation_phrasing_signal` is pre-existing (fails
identically stashed out); the other test in that pair passed on the
unmodified branch too, consistent with the isolated re-run above.

acceptance (check 3, wall-clock measurement): two agent pairs, each
shaped as a same-issue conformance-review + execution-observation pair
for this issue's own diff — one dispatched sequentially (spawn, wait for
full completion, then spawn the next), one dispatched together (both
launched in the same reply/turn). derived: this session's own `date
+%s.%N` readings bracketing each pair's dispatch and completion.

Sequential pair — execution-observation ran a 4-file pytest slice
(agent-reported duration 591.97s), then conformance-review reviewed the
board_snapshot-fix diff (agent-reported duration 210.01s), dispatched one
after the other:
```
1787646508.605661097
1787647386.532023531
```
Measured wall-clock: **877.93s** — 75.95s more than the two agents' own
reported durations summed (801.98s), the wait-then-dispatch-next overhead
this delivery's directive change (check 2) removes.

Concurrent pair — execution-observation ran a remaining 7-file pytest
slice (agent-reported duration 124.00s), conformance-review reviewed the
spawn-and-board.md diff (agent-reported duration 17.43s), both launched
in the same message:
```
1787647399.494948624
1787647538.984918721
```
Measured wall-clock: **139.49s** — below the two agents' own summed
duration (141.43s), tracking the longer component (124.00s) plus ~15.5s
of fixed dispatch/notification overhead rather than the sum of both.

Applying that measured ~15.5s overhead to the sequential pair's own
component sizes (592.0s / 210.0s) projects ≈607.5s for that pair run
concurrently, versus its real measured sequential cost of 877.93s — an
estimated ≈270s (≈31%) reduction; this last figure is a derived
projection, not an independent third measurement (the third trial was
aborted by disk exhaustion, see "What did not work"). The two
measurements actually taken — 877.93s sequential vs. 139.49s concurrent,
each checked against its own component sum above — confirm acceptance
check 3: the parallel path was faster in both trials run.

## Rebase reconciliation (landing turn)

PR #2392 drifted to `CONFLICTING` against `main` after #2348 (log sharding)
and #2293 (adhoc-spawn workspace isolation) landed. Rebased
`issue-2382/implementation` onto `origin/main` (96513f8c).

One real conflict, in `spawn.py`, both sides adding code at the same
insertion point right after the `cross_family` dispatch: main's side
(03cb97e1's parent-diff base did not yet have it) added the `if issue is
None: cwd = issue_workspace(...)` adhoc-isolation block (#2293); this
branch's 03cb97e1 added the `_board_snapshot_executor = None;
_board_snapshot_future = None` initialization (#2382). The two additions
are independent statements with no shared state or ordering dependency —
resolved by keeping both, adhoc-isolation block first (unchanged from
main), board_snapshot initialization immediately after (unchanged from
this branch). acceptance: `python3 -m ast` parse and `grep -c
"<<<<<<<"` both after resolution — result:
```
syntax OK
0
```
No other files conflicted (the diffstat pre- and post-rebase is
byte-identical: 3 files touched by 03cb97e1, 427 insertions / 23
deletions total across the four issue-2382 commits).

acceptance: `git push --force-with-lease origin issue-2382/implementation`
then `gh pr view 2392 --json state,mergeable` — result:
```
{"baseRefName":"main","headRefName":"issue-2382/implementation","mergeable":"MERGEABLE","state":"OPEN"}
```

acceptance: `python3 -m pytest test/ tests/ -m "not slow" -q` (full suite,
post-rebase) — result:
```
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED tests/test_perf_budget_issue_2053.py::test_skill_verdict_guard_standalone_budget
FAILED tests/test_perf_budget_issue_2053.py::test_report_framing_check_standalone_budget
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_observation_recovery.py::ConsumerFixtureWatchdogAnchoring::test_foreign_repo_watchdog_output_carries_no_marketplace_or_otr_references
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_anomaly_count_for_stalled_entry
8 failed, 1339 passed, 9 xfailed, 2 xpassed in 394.83s (0:06:34)
```
derived: checked all 8 against a clean `git worktree add
/tmp/otr-main-check origin/main --detach` (no issue-2382 changes at all).
5 of 8 reproduced identically under the same `-n auto` run. The remaining
3 (all in `test_spawn_observation_recovery.py::Watchdog`) passed under
`-n auto` on plain `origin/main` but failed when re-run there without
xdist (`-n0`) too — `test_roster_watchdog_returns_anomaly_count_for_stalled_entry`
asserted `37 != 2` and, on a second `-n0` run, `16 != 2` (both on
unmodified `origin/main`, in this environment). acceptance: `cd
/tmp/otr-main-check && python3 -m pytest
tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
tests/test_spawn_observation_recovery.py::ConsumerFixtureWatchdogAnchoring::test_foreign_repo_watchdog_output_carries_no_marketplace_or_otr_references
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn
tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_anomaly_count_for_stalled_entry
-n0 -q` — result:
```
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_delegation_phrasing_signal
FAILED tests/test_spawn_observation_recovery.py::ConsumerFixtureWatchdogAnchoring::test_foreign_repo_watchdog_output_carries_no_marketplace_or_otr_references
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn
FAILED tests/test_spawn_observation_recovery.py::Watchdog::test_roster_watchdog_returns_anomaly_count_for_stalled_entry
4 failed in 53.76s
```
Root cause: `roster_watchdog()` reads live process/roster state from this
shared host, which runs many concurrent orchestrator sessions (same
class of shared-host contention already recorded above under "What did
not work" for the aborted third timing trial) — the anomaly count varies
run to run (2, 16, 37 all observed) independent of which branch is
checked out. All 8 failures are pre-existing/environmental, not
introduced by this rebase; the rebase changed no test outcome.

## skill-verdict

skill-verdict: implementation-blueprint — not-applicable: no new module
or multi-file structure decision; this reorders existing calls within one
already-established function using an idiom (`ThreadPoolExecutor` +
`.result()` join, or raw daemon thread) already established by three
prior issues (#2061, #2195, #2201) in the same file.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no coupling/cohesion metric crossed a threshold and no
cross-module import direction changed; the touched functions kept their
existing signatures and call sites.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern indirection question — this is a dispatch-order change
using an idiom the codebase already committed to, not a new abstraction.
skill-verdict: implementation-performance-data-structure-choice —
not-applicable: the concurrency-mechanism choice (thread-pool dispatch/
join vs. daemon thread) matched existing file precedent by direct
comparison, not a data-structure/algorithm-class/cache-cost tradeoff this
skill's trigger describes; the Skill tool itself was not called this
session, so this cannot be marked applied per the invoke-before-apply
requirement.
skill-verdict: work-in-english — not-applicable: the Skill tool was not
called this session; English-language output here follows this
project's pre-existing convention (visible throughout spawn.py's own
mixed-language comments and prior records) rather than this skill being
invoked.
skill-verdict: model-routing — not-applicable: single-session delivery
with no separate reasoner/executor tier split to make.
other mounted skills: not triggered.
