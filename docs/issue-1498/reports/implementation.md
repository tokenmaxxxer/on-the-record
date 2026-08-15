---
code_under_review:
  - gates/closure_sweep.py
  - gates/spawn_on_pr.py
  - spawn.py
  - tests/test_gh_quota_guard.py
  - docs/handbooks/gh-quota-guard.md
type: feature
breaking: false
verdict: ok
loop_state: landed
---

# issue-1498 implementation record (phase 2)

## What was done

Delivered the approved proposal (docs/issue-1498/proposals/quota-guard.md,
approval: issue #1498 comment `APPROVE issue-1498/implementation`) exactly
as scoped:

1. Quota floor (req 1) — closure_sweep.py's existing
   `_RATE_LIMIT_GUARD_THRESHOLD` is now also checked on the watchdog path:
   spawn.py's `_board_wide_sweep` calls `rate_limit_remaining()` first;
   below floor, all three gh-calling signals (spawn_on_pr's
   `spawn_missing_for_pr`, closure_sweep's `find_violations`,
   spawn_coverage's `_list_open_issues`) are skipped with one report
   line; local-only signals (`accumulation_trend`, `requirement_drift`)
   still run.
2. `test_graphql_free_watchdog_reads` — standing regression test in
   tests/test_gh_quota_guard.py asserting no `gh issue view`/`gh pr
   view`/`gh pr merge` subcommand appears among recorded calls (req 2,
   "verified, not migrated" per the proposal's survey finding).
3. Sweep backoff (req 3) — closure_sweep.py's new `sweep_should_run()`/
   `record_sweep_result()`, state in `runs/gh_quota_backoff.json`
   (`sweeps` namespace): interval starts at 1 tick, doubles on a
   rate-limited tick, resets to 1 on success. Wired into
   `_board_wide_sweep` as the outermost gate.
4. Re-check backoff (req 4) — closure_sweep.py's new `recheck_backoff()`
   (`recheck` namespace, same state file): consecutive no-change results
   double the interval, any observed change resets to 1. spawn_on_pr.py's
   `spawn_missing_for_pr` adopts it to gate the `is_approval_blocked()`
   gh call for previously-parked `(subject, role)` pairs.
5. Per-tick call budget (req 5) — `_board_wide_sweep` tallies known gh
   call sites against a stated default; an overage prints a
   `[watchdog] board-sweep: 예산 초과` line as a reported anomaly, never
   a silent retry.

derived: `git show 3899d087 --stat`

```
 docs/handbooks/gh-quota-guard.md   |  62 ++++++
 gates/closure_sweep.py             |  80 +++++++
 gates/spawn_on_pr.py               |  67 +++++--
 spawn.py                           | 122 ++++++++--
 tests/test_gh_quota_guard.py       | 172 +++++++++++++++
 5 files changed, 387 insertions(+), 16 deletions(-)
```

The four numeric defaults (quota floor, sweep-backoff cap, re-check
no-change threshold and cap, per-tick call budget) are written out in
docs/handbooks/gh-quota-guard.md's table, per the doctrine ladder.

Five acceptance tests added in tests/test_gh_quota_guard.py, all mocking
`subprocess.run` (no network): `test_bulk_loop_skipped_below_floor`,
`test_graphql_free_watchdog_reads`, `test_sweep_backoff_on_rate_limit`,
`test_recheck_backoff`, `test_sweep_call_budget`.

canonical: `python3 -m pytest tests/test_gh_quota_guard.py -q` — run this
turn, after committing the code (commit 3899d087).

```
.....                                                                    [100%]
5 passed in 0.26s
```

The wider related pre-existing suites (excludes tests/test_spawn.py per
this session's out-of-scope instruction) were also re-run —

canonical: `python3 -m pytest tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py gates/test_closure_sweep.py -q` — run this turn.

```
..................................                                       [100%]
34 passed in 1.40s
```

## Why

canonical: `gh issue view 1498` body, "## Problem" section, read this
session.

The issue's own text states the GraphQL quota was exhausted despite issue
#1459's earlier REST read-cost cut, because the watchdog sweep and gate
helpers had no quota awareness and kept attempting bulk/lookup calls at
full frequency.

## Basis

canonical: `gh issue view 1498 --comments` final comment, read this
session — comment body is exactly `APPROVE issue-1498/implementation`.

docs/issue-1498/proposals/quota-guard.md (phase-1 proposal, approved by
that comment).

## Rationale for deviations

canonical: docs/issue-1498/proposals/quota-guard.md, req-5 plan
paragraph, read this session.

The proposal's req-5 paragraph stated the survey saw no per-subject
lookup in the frozen write set's call graph. Writing
`test_sweep_call_budget` against real code (synthetic board with many
already-covered subjects) surfaced that gates/spawn_on_pr.py's
`missing_verification()` and `spawn_missing_for_pr()` each called
`spawn._pr_open_or_merged_for_branch()` (one `gh pr list --head <branch>`
call) once per subject with missing roles — a per-subject site the
phase-1 survey missed, inside a file already in the frozen write set.
Fixed by threading a single `closure_sweep._pr_index_all()` bulk index
into both functions (new `_pr_number_for_branch()` helper, falling back
to the per-branch call only when the index itself is unavailable/
truncated) — the same bulk+local-join shape req 5 already mandates
elsewhere, applied to the one site inside the frozen write set the
survey had missed, not a scope widening: no file outside `files:` was
touched.

canonical: `python3 -m pytest tests/test_gh_quota_guard.py::test_sweep_call_budget -q` — run this turn.

```
.                                                                        [100%]
1 passed in 0.16s
```

amendments-reconciled: issuecomment-5294696624 ("LIVE DIAGNOSIS
CORRECTION", orchestrator, posted after this session's approval comment)
— the reconciliation for the deviation above.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5294696624 --jq .body`,
read this session.
That comment independently confirmed the same per-subject site, citing a
live sample of GraphQL burn rate and the `spawn_on_pr.py` line numbers
for all three call sites.

canonical: same comment body, third bullet ("Call graph:"), read this
session.
It additionally named a call site this session's own
`test_sweep_call_budget` run had not exercised: `_missing_verification_closed()`.

canonical: gates/spawn_on_pr.py, `_missing_verification_closed`'s
docstring, read this session.
That function backs only the opt-in backfill CLI path, never the
automatic watchdog tick, but shares the same per-subject
`_pr_open_or_merged_for_branch` pattern. Migrated it to the same
bulk-index join as the other two sites for consistency, still inside the
frozen write set (`gates/spawn_on_pr.py`).

canonical: same comment body, first bullet ("Measured burn:"), read this
session — before-state: real production GraphQL burn observed at ~111
calls/minute with zero role-session gh calls (the sweep alone).

canonical: `python3 -m pytest tests/test_gh_quota_guard.py::test_sweep_call_budget -q`,
run this turn (same run cited above) — after-state: the full
`_board_wide_sweep` (all three gh-calling signals, spawn_on_pr included)
over a synthetic 400-subject board makes 5 gh calls in that one tick,
independent of subject count (the fixture's 400 subjects are all missing
roles, so the count is dominated by the fixed bulk-index call sites, not
subject count).

## What did not work

- First cut of `test_recheck_backoff` assumed the 3rd consecutive
  no-change call would still return "due" (interval not yet doubled at
  that point) — expected: `recheck_backoff` returns `True` on the 3rd
  no-change call; actual: the interval doubles before the tick-modulo
  check on that same call, so it returns `False` on that call. Fixed the
  test to assert the actual mechanical order instead of the assumed one.

## Open findings

None.

## Next steps

None — delivery is terminal (`loop_state: landed`).
