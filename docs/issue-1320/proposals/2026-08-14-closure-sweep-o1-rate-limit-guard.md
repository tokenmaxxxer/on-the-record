---
status: proposed
files:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
---

Skip condition (scout-directive): spec leaves no design decision open —
issue #1320 fixes exact thresholds, an exact output line, and exact call
sites to remove. Scouting skipped (see
docs/issue-1320/reports/implementation/survey.md).

## Request

Watchdog board sweep exhausts the GitHub GraphQL rate limit on a 1300+
item board. `find_violations()` in `gates/closure_sweep.py` falls back to
per-issue `gh issue view` / per-PR `gh pr view` calls when its bulk-list
indices are missing or truncated — that fallback is the O(board-size)
call path. Make the sweep path O(1) gh calls (bulk list only, no
per-item fallback), and add a pre-sweep GraphQL rate-limit guard that
skips the sweep with a single line when remaining budget is low.
Sweep-invocation dedup and the `spawn.py` tick call site are explicitly
out of scope here (ordering note: lands after #1313, which has not
merged — `gh pr view 1313` 404s).

## Constraints

- Per-item `gh issue view`/`gh pr view` calls are prohibited in the sweep
  path (`find_violations`) — not just discouraged/reduced.
- `POLL_INTERVAL_SEC` (60s) is untouched; this proposal doesn't touch
  `spawn.py`.
- Existing skip/violation reporting contract (`(violations, skips)`,
  issue #287 S1: "checked, clean" must not be confused with "couldn't
  check") must be preserved — truncation/failure still surfaces as a
  skip, just never as a per-item retry.
- Rate-limit guard threshold is exactly < 500 remaining GraphQL points;
  output line is exactly `[watchdog] board-sweep: 미집계 (rate-limit,
  remaining=<n>)`.

## Rationale

Two ways to reach "no per-item gh calls in the sweep path":

1. **Delete the fallback branches** (chosen): when a bulk index is
   `None` (truncated or failed), every subject/role it would have
   covered becomes a `skip` with a reason — no retry.
2. **Keep the fallback but cap it** (rejected): e.g. only allow the
   per-item fallback for the first K items, or make it opt-in via a
   flag. Rejected because the issue requires the sweep path to *never*
   grow with board size, not merely stay bounded — a capped fallback
   still issues gh calls proportional to min(K, board size), which is
   the exact shape the issue's acceptance test (b) is designed to catch
   ("any code path invoking gh issue view/gh pr view from the sweep
   raises/fails the test"). Deleting the fallback is also strictly
   simpler: no new flag, no new failure mode to reason about.

For the rate-limit guard, checked `gh api rate_limit` (REST) against
GraphQL: `gh api graphql` has no rate-limit-only query cheaper than a
real query, so REST `rate_limit` (which reports the GraphQL resource's
remaining budget without spending a GraphQL point) is the only way to
read remaining budget without spending it.

## What will be done

- Remove the per-item fallback in `find_violations`: when
  `issue_state_index_all` returns `(None, ok)`, every subject is skipped
  with reason `gh-issue-list-failed` (ok=False) or
  `gh-issue-list-truncated` (ok=True, len>=limit) — no `_issue_view`
  call. When `_pr_index_all` returns `(None, ok)`, every role under a
  checked subject is skipped with reason `gh-pr-list-failed` or
  `gh-pr-list-truncated` — no `_pr_for_branch`/`_pr_view_state_body`
  call.
- `find_violations` computes its own `issue_state_index_all` internally
  when `issue_states` is not passed in, instead of falling back to
  per-subject `_issue_view` — so the function is O(1) gh calls
  regardless of caller.
- `_issue_view`/`_pr_view_state_body` stay as standalone functions (still
  directly unit-tested) but are no longer called from `find_violations`.
- Add `rate_limit_remaining(root) -> tuple[int | None, bool]`: runs `gh
  api rate_limit`, parses `resources.graphql.remaining`. `(None, False)`
  on gh/JSON failure.
- Add a pre-sweep guard in `main()`: call `rate_limit_remaining`; if it
  succeeds and remaining < 500, print exactly `[watchdog] board-sweep:
  미집계 (rate-limit, remaining=<n>)` and return without calling
  `find_violations` (exit code 2, consistent with the existing "couldn't
  check" exit code). If the guard call itself fails, proceed with the
  sweep as today (fail open — a guard-read failure is not itself
  evidence of exhaustion).
- Extend `gates/test_closure_sweep.py`: (a) constant-gh-call-count test
  for N ∈ {5, 50} via a subprocess-call-counting stub; (b) a test
  asserting no `gh issue view`/`gh pr view` argv appears anywhere during
  a sweep even when indices are truncated; (c) rate-limit guard
  short-circuit test with a stubbed remaining < 500; (d) update the two
  existing tests that assumed the per-item fallback
  (`test_pr_view_failure_is_a_skip`,
  `test_issue_view_failure_is_a_skip_not_a_silent_pass`) to assert the
  new truncation-is-a-skip behavior instead.

## Out of scope

- `spawn.py` dedup/wiring (acceptance check (d), "one tick triggers
  exactly one board-wide sweep") and the tick call site — ordering note
  defers this to after #1313 merges.
- `bash tests/run-orchestrate-tests.sh` full regression pass is expected
  to still pass since `spawn.py` is untouched; not re-verified beyond
  the pytest run for this proposal's write set.
- `ci._phase2_record_evidence` (a separate, already-bounded conditional
  gh api call inside `classify`'s MERGED/OPEN branch) — not named in the
  issue's root-cause line citations, left as-is.

## Accumulation

This change adds one new inline `gh api rate_limit` subprocess call
(`rate_limit_remaining`) and removes two existing per-item inline gh
calls (`_issue_view`, `_pr_view_state_body`) from the sweep's call graph
— net inline-subprocess-call-site count in this file goes down by one,
not up. If this pattern (a bounded, once-per-sweep-tick `gh api` guard
call) recurs N more times across gates, each instance is still O(1) per
call site regardless of board size, so it does not compound into the
O(board-size) shape `accumulation.py` shape-1 tracks — no new shared
helper is warranted for a single guard call.

## How you'll know it worked

`python3 -m pytest gates/test_closure_sweep.py -v` passes, including the
new constant-call-count, no-per-item-view, and rate-limit-guard tests.
