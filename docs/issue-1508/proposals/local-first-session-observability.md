---
status: proposed
files:
  - spawn.py
  - tests/test_watchdog_local_signals.py
  - docs/issue-1508/reports/implementation.md
---

## Request

Reduce gh-quota demand from the watchdog by confirming (per survey.md)
which liveness/progress/stall signals are already local-only, narrowing
the one remaining per-session gh call (dead-session PR-state check) to
ride the #1498 bulk PR index instead of its own per-branch `gh pr list`,
and adding a signal-coverage regression test plus a gh-calls-per-tick
measurement.

## Constraints

- Zero gh calls on `watchdog_check_one`'s anomaly-signal path (already
  true per survey.md; must stay true).
- Observe-only contract: no watchdog signal type may become
  non-derivable — the coverage test enumerates today's signal types and
  asserts each still fires.
- gh usage narrows to PR-state confirmation only, riding #1498's existing
  bulk query/budget/floor — no new gh call shape.
- Fixture-based, deterministic tests only (no live gh calls in tests).

## Rationale

Considered rewriting `diagnose_health`'s dead-branch check to call
`closure_sweep._pr_index_all` directly every time instead of accepting an
optional pre-fetched index. Rejected: that would make every standalone/unit
call to `diagnose_health` (existing test_spawn.py callers, spawn.py:5753)
issue its own bulk `gh pr list --state all` — trading one narrow call for
a wider, unconditional one, and breaking today's isolated-call tests that
pass no live repo. Threading an *optional* `pr_index` parameter preserves
the narrow per-branch fallback for isolated callers while letting the
roster-tick loop (which already iterates every entry) fetch the bulk index
once and share it — matching the pattern `_board_wide_sweep` already uses
for its own gh calls (spawn.py:2897-2898 backoff, budget 8).

## Accumulation

This adds one shared-helper indirection (`_pr_state_from_index`) rather
than an inline `gh`/subprocess call at a new call site — it does not add a
new per-caller inline gh call that would accumulate with N more callers;
each future caller reuses the same helper and shares one bulk index
instead of adding its own `subprocess.run(["gh", ...])`.

## What will be done

1. Add `_pr_state_from_index(pr_index, branch)` helper and an optional
   `pr_index: dict | None` parameter to `diagnose_health` (spawn.py:2560):
   when supplied, look up `branch` in the pre-fetched bulk index
   (OPEN/MERGED → PR number, else `None`) instead of calling
   `_pr_open_or_merged_for_branch`; when `None` (default), keep today's
   per-branch gh call unchanged.
2. Add `tests/test_watchdog_local_signals.py` with the three acceptance
   tests: `test_liveness_verdicts_no_gh` (fixture workspaces: fresh log /
   stale log / dead watcher pid / zero-commit aged session, each via
   `watchdog_check_one`/`diagnose_health` with a gh-call recorder
   asserting zero calls; empty-workspace-set case asserted separately),
   `test_signal_coverage_no_regression` (each of the six signal types
   above still derivable), `test_gh_only_for_pr_state` (`diagnose_health`
   with `pr_index` supplied makes zero gh calls on a dead entry; without
   `pr_index`, exactly one `gh pr list` call).
3. Record before/after gh-calls-per-tick measurement (roster-tick with N
   dead entries: before = N calls, after = 1 bulk call when the caller
   passes `pr_index`) in `docs/issue-1508/reports/implementation.md`.

## Out of scope

Per-session gh budget extension (issue's own exclusion, separate issue).
Rewiring `_board_wide_sweep`'s three gh signals — already covered by
#1498, unaffected here. Threading `pr_index` into the actual roster-tick
call site that iterates all entries is left for a follow-up if this
proposal's caller-facing test coverage surfaces it as needed — the
`diagnose_health` signature change alone satisfies requirement 2's
"narrows to riding the #1498 bulk query" for any caller that adopts it.

## How you'll know it worked

`pytest tests/test_watchdog_local_signals.py -v` passes all three tests
with the gh-call recorder showing zero calls on the local-only path and
exactly the expected count on the PR-state path; the measurement section
in the delivery record shows the before/after call count.
