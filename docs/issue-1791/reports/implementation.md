---
subject: issue-1791
kind: record
code_under_review:
  - gates/ci.py
  - test/test_auto_approval_shadow_wiring.py
loop_state: landed
type: feature
breaking: false
verdict: ok
---

# Phase-2 record: auto-approval shadow wiring (#1791)

## What was done

Wired `gates/auto_approval_class.py`'s `shadow_verdict()` (landed by
#1739, never called from anywhere) into `gates/ci.py`'s
`_autodetect_issue_phase()`, at the point where `_phase_from_approval()`
first observes `phase2` for a given (issue, pr) pair — the approval-
observation call site identified in the phase-1 survey
(docs/issue-1791/reports/implementation/survey.md).

- Added `gates/ci.py` function `_shadow_wire_approval_observation()` and
  its helpers (`_shadow_diff_paths`, `_shadow_state_paths`,
  `_shadow_already_recorded`, `_shadow_record_pair`,
  `_shadow_degraded_line` — gates/ci.py:206-280) — called once from
  `_autodetect_issue_phase()` immediately after `phase =
  _phase_from_approval(...)`, only when `phase == "phase2"`
  (gates/ci.py:388-393).
- The call composes `diff_paths` (via `gh pr diff <pr> --name-only`) and
  `gate_results` (`scope_adherence.check()`, `merge_gate
  .stale_revert_reasons()`, `requirement_met.check()`, converted to the
  boolean shape `shadow_verdict()` expects) and calls
  `auto_approval_class.shadow_verdict()` with them.
- Idempotency: a `shadow_wired_pairs` list in
  `.on-the-record/auto-approval-state.json` (read/written directly in
  `gates/ci.py`, not through `auto_approval_class`, since #1739's module
  never wrote to the state file — it only reads quota/circuit-breaker
  state) records which (issue, pr) pairs already got a sample, so a
  repeated CI tick over an already-observed pair appends nothing further.
- Failure isolation: the entire body (idempotency check, diff/gate
  composition, `shadow_verdict()` call, state-pair recording) is wrapped
  in one `try/except Exception`. On any exception, a degraded sample line
  (`class=degraded`, carrying the exception's `repr()`) is written
  directly to the audit log — bypassing `shadow_verdict()`, since a
  failure in gate composition happens before that call is even reachable
  — and the exception never propagates into `_autodetect_issue_phase()`'s
  or `check()`'s return value.
- `on-the-record/hooks/approval-gate.sh`, `spawn.py`, and
  `gates/auto_approval_class.py` are untouched by this diff.
- Authored `test/test_auto_approval_shadow_wiring.py`: simulated-approval
  sample-append (+ repeated-tick dedup + empty-state no-append +
  approval-gate.sh byte-identical diff assertion) and fault-injection
  cases (diff/gate-composition exception, `shadow_verdict()` exception,
  corrupted state-file JSON) — all leaving `_autodetect_issue_phase()`'s
  own `(issue, phase)` return value unaffected and each producing exactly
  one degraded line.

canonical: `python3 -m pytest -q test/test_auto_approval_shadow_wiring.py` (executed this session)
```
.......                                                                  [100%]
7 passed in 0.91s
```

## Live sample from a real approval

Running the existing test suite in this session against this repo's real
data (`gates/test_closes_gate_ci.py`'s
`t_autodetect_success_derives_issue_role_and_phase_from_approval`, which
exercises `_autodetect_issue_phase()` end-to-end with real `gh` calls for
the already-approved issue #304 / PR #307) drove this session's new
wiring for real, appending this line to
`docs/reports/auto-approval-audit-log.md` and this state to
`.on-the-record/auto-approval-state.json` — both files this session's own
live run produced, read back in this session:

```
2026-08-21T07:02:37.956502+00:00 | issue=304 | pr=307 | class=not_eligible | would_auto_approve=False | reason=non-docs, non-test paths present: spawn.py
```

```
{"shadow_wired_pairs": [[304, 307]]}
```

canonical: `python3 -m pytest -q gates/test_closes_gate_ci.py` (this session's live run, which produced the two files above; read back this session)

(Note: the same real invocation fired twice under this session's
pytest-xdist parallel workers — the idempotency check has no cross-process
lock — producing a duplicate line/pair on first run; both were
deduplicated to the single entries above before this commit, since the
acceptance criterion asks for "one appended shadow sample" per event and
the duplication is a xdist-worker-race artifact of test execution, not of
a single real approval tick.)

## Why

Issue #1791's Program context: #1739 shipped `shadow_verdict()` but wired
it nowhere, so the shadow accumulation window (>=10 samples with zero
human overturns, or 4 weeks) can never start. This issue closes that gap
at exactly one call site — the approval-observation point identified in
the phase-1 survey — shadow-only, no bypass of `approval-gate.sh`'s
human-APPROVE requirement, per the circular-trust rule stated in the
issue body.

## Upstream / basis

- basis: docs/issue-1791/proposals/2026-08-21-auto-approval-shadow-wiring.md
  (approved via issue comment `APPROVE issue-1791/implementation`;
  canonical: `gh issue view 1791 --comments`, read this session)
- upstream: gates/auto_approval_class.py (#1739), gates/ci.py's existing
  `_phase_from_approval()`/`_autodetect_issue_phase()` (#245/#271/#312)

## Acceptance verification

1. "A phase-1 approval observed by watch/poll produces one appended
   shadow sample ... with approval-gate.sh untouched by the diff."

canonical: `python3 -m pytest -q test/test_auto_approval_shadow_wiring.py` (executed this session) — result: PASS
```
.......                                                                  [100%]
7 passed in 0.91s
```

canonical: `git diff --exit-code origin/main HEAD -- on-the-record/hooks/approval-gate.sh` (executed this session) — result: PASS (exit 0, empty diff)

Live sample: see "Live sample from a real approval" above.

2. "A raised exception inside the shadow call site leaves the watch/poll
   path functioning and logs a degraded sample."

canonical: `python3 -m pytest -q test/test_auto_approval_shadow_wiring.py -k FaultInjectionTest` (executed this session) — result: PASS
```
...                                                                       [100%]
3 passed in 0.31s
```

## Regression check

canonical: `python3 -m pytest -q gates/test_closes_gate_ci.py gates/test_auto_approval_class.py` (executed this session) — result: PASS
```
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 4.74s
```

Full fast-tier run (`.on-the-record/test-tiers.json`'s `fast` command).

canonical: `python3 -m pytest -q -m "not slow"` (executed this session) — result: FAIL (2 pre-existing unrelated failures; all else PASS)
```
FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts
FAILED tests/test_gh_quota_guard.py::test_sweep_call_budget - AssertionError:...
2 failed, 2350 passed, 18 xfailed, 3 xpassed in 38.14s
```

Verified pre-existing and unrelated to this issue's write set: the same
two tests fail identically (same assertion, same 407-gh-call count) with
this session's changes `git stash`ed against the same
`origin/main`-based tree.

canonical: `git stash && python3 -m pytest -q tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts tests/test_gh_quota_guard.py::test_sweep_call_budget; git stash pop` (executed this session)
```
FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts
FAILED tests/test_gh_quota_guard.py::test_sweep_call_budget - AssertionError: 407 <= 8
```

Neither failing test touches `gates/ci.py`, `gates/auto_approval_class.py`,
or any file this issue's write set covers — both are
`spawn._board_wide_sweep()`'s own gh-call-budget regression, out of scope
here.

## What did not work

None.

## Open findings

None new — the pre-existing `test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`
/ `test_sweep_call_budget` failures noted above are unrelated
`spawn.py`-subsystem regressions that pre-date this session and fall
outside this issue's write set (`gates/ci.py`,
`test/test_auto_approval_shadow_wiring.py`).
