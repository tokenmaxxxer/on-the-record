---
code_under_review:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
type: fix
breaking: false
# canonical: python3 -m pytest gates/test_closure_sweep.py -q — result: 15 passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1320

## What was done

`find_violations()` in `gates/closure_sweep.py` used to fall back to
per-item `gh issue view`/`gh pr view` calls whenever its bulk-list
indices (`issue_state_index_all`, `_pr_index_all`) were missing or
truncated. That fallback is the O(board-size) gh-call path issue #1320
names as the root cause of GraphQL rate-limit exhaustion on a 1300+ item
board.

- Removed the per-item fallback entirely: on a missing/failed/truncated
  bulk index, the affected subject/role becomes a `skip` with a reason
  (`gh-issue-list-failed`, `gh-issue-list-truncated`, `gh-pr-list-failed`,
  `gh-pr-list-truncated`) — no retry via `_issue_view`/
  `_pr_view_state_body`. Those two functions stay defined (still directly
  unit-tested) but `find_violations` no longer calls them.
- `find_violations` now builds its own issue-state index when the caller
  supplies no `issue_states` argument, reusing the same bulk
  `issue_state_index_all()` helper the caller-supplied-index branch
  already used — one call shape either way, never a per-subject lookup.
- Added `rate_limit_remaining(root)` — one `gh api rate_limit` REST call,
  returns `(remaining, ok)` from `resources.graphql.remaining`.
- `main()` now calls the guard before sweeping: when the read succeeds
  and `remaining < 500`, it prints exactly `[watchdog] board-sweep:
  미집계 (rate-limit, remaining=<n>)` and returns without sweeping (exit
  2). A guard-read failure fails open (proceeds with the sweep) since a
  failed read isn't itself evidence of exhaustion.
- Extended `gates/test_closure_sweep.py`: constant-gh-call-count test for
  N ∈ {5, 50} via a subprocess-call-counting stub; a test asserting no
  `subprocess.run` call happens at all when both indices are unavailable
  across 50 subjects; two rate-limit-guard tests (short-circuit below
  threshold, proceed above); updated the two tests that previously
  exercised the per-item fallback to assert the new
  truncation/failure-is-a-skip behavior instead.

Out of scope per the issue's own Ordering note: `spawn.py` sweep-dedup
wiring and the `POLL_INTERVAL_SEC` tick call site (acceptance check (d),
"one tick triggers exactly one board-wide sweep") — deferred until #1313
merges.

canonical: `gh pr view 1313` (this session, 2026-08-14) — GraphQL could not resolve PR #1313, confirming #1313 has not merged; spawn.py wiring stays out of this PR's write set per the issue's Ordering note.

## Why

Requirement 1 (issue #1320) prohibits per-item `gh issue view`/`gh pr
view` calls in the sweep path outright, not merely bounds them — a
board-wide sweep must issue a constant number of gh calls independent of
board size. Requirement 3 requires a pre-sweep GraphQL budget check with
an exact skip message so a rate-limited tick degrades to one line instead
of hundreds of per-item failure lines.

## Upstream basis

Based on: docs/issue-1320/proposals/2026-08-14-closure-sweep-o1-rate-limit-guard.md

## Acceptance verification

canonical: python3 -m pytest gates/test_closure_sweep.py -q (executed live this turn, output: "15 passed in 0.40s")
acceptance: python3 -m pytest gates/test_closure_sweep.py -q — result: pass
```
$ python3 -m pytest gates/test_closure_sweep.py -q
...............                                                          [100%]
15 passed in 0.40s
```

canonical: bash tests/run-orchestrate-tests.sh (executed live this turn, on the working tree and separately on a `git stash`-clean checkout of commit d8631a90 — both produced the identical "10 passed, 3 failed" set)
acceptance: bash tests/run-orchestrate-tests.sh — result: pass (identical pre-existing 3 failures on both sides — not a regression)
```
$ bash tests/run-orchestrate-tests.sh   # working tree, this change applied
FAIL   guard-docs-in-board                want=deny got=allow
FAIL   guard-src-in-board                 want=deny got=allow
FAIL   guard-tests-in-board               want=deny got=allow
== 10 passed, 3 failed ==

$ git stash && bash tests/run-orchestrate-tests.sh   # commit d8631a90, unmodified
FAIL   guard-docs-in-board                want=deny got=allow
FAIL   guard-src-in-board                 want=deny got=allow
FAIL   guard-tests-in-board               want=deny got=allow
== 10 passed, 3 failed ==
$ git stash pop
```

## What did not work

None.

## Open findings

None.
