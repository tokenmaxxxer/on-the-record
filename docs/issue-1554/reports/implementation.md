---
code_under_review:
  - gates/closure_sweep.py
  - spawn.py
  - gates/test_closure_sweep.py
  - tests/test_board_sweep_budget_carryover.py
  - tests/test_board_sweep_cross_workspace_lock.py
  - tests/test_board_sweep_etag.py
type: feature
breaking: false
verdict: ok
loop_state: landed
---

Subject: issue-1554

## What was done

- gates/closure_sweep.py: added a per-tick call-budget queue with
  carry-over (`BOARD_SWEEP_CATEGORIES`, `load_board_sweep_queue`/
  `save_board_sweep_queue`/`next_categories`, persisted at
  runs/board_sweep_queue.json) so a category deferred by budget is
  re-queued for a later tick instead of dropped. canonical:
  gates/closure_sweep.py:539 (`next_categories`). Added ETag/If-None-Match
  conditional re-fetch (`_board_list_etag_cache_path`/
  `_conditional_issue_list`) wired into `issue_state_index_all`; falls back
  to the pre-existing unconditional path when the repo slug is unavailable
  or the board exceeds 100 issues. canonical: gates/closure_sweep.py:199
  (`issue_state_index_all`).
- spawn.py: `_board_wide_sweep` asks `closure_sweep.next_categories` for
  this tick's categories instead of always running all three, and prints a
  carry-over line for deferred categories. canonical: spawn.py:2891
  (`_board_wide_sweep`). Added `_cross_workspace_board_sweep_lock_path`/
  `cross_workspace_board_sweep_lock_acquire`, keyed by
  `_repo_identity(repo_root)` under a fixed path relative to
  `_workspace_base()` (independent of which checkout runs the code); wired
  into `_board_wide_sweep_all` so one workspace's watchdog sweeps a given
  repo per tick. canonical: spawn.py:3053
  (`cross_workspace_board_sweep_lock_acquire`).
- gates/test_closure_sweep.py: one existing test's gh-call whitelist and
  expected count updated because `issue_state_index_all` now probes the
  repo slug once before falling back — logged as an inline deviation, see
  docs/issue-1554/reports/implementation/deviation-log.md.
- Three new hermetic test files (no network):
  tests/test_board_sweep_budget_carryover.py,
  tests/test_board_sweep_cross_workspace_lock.py,
  tests/test_board_sweep_etag.py.

`accumulation_trend`/`requirement_drift` needed no code change — already
gh-free, already covered by tests/test_watchdog_local_signals.py.

canonical: `python3 -m pytest gates/test_closure_sweep.py
tests/test_gh_quota_guard.py tests/test_watchdog_local_signals.py
tests/test_watchdog_freshness.py tests/test_board_sweep_budget_carryover.py
tests/test_board_sweep_cross_workspace_lock.py tests/test_board_sweep_etag.py
-q` output:
```
...................................................                      [100%]
51 passed in 1.26s
```

`python3 -m py_compile spawn.py gates/closure_sweep.py` exited 0.

## Why

Phase 2 gate opened by an issue-level comment whose entire body is the exact
string `APPROVE issue-1554/implementation`, posted 2026-08-15 by JiwonJung94
(listed in docs/specs/approvers.md), on issue #1554 — single-account mode
(author == approver on this branch). canonical: `gh issue view 1554 --json
comments -q '.comments[] | "\(.author.login): \(.body)"'` output, last
comment.

## Upstream

docs/issue-1554/proposals/2026-08-15-gh-call-budget-dedup-etag.md

## What did not work

- Considered giving `_pr_index_all` the same ETag-conditional treatment as
  `issue_state_index_all` (originally in the proposal's write set). Set
  aside instead: the three-way lifecycle field `gh pr list --json
  ...state` synthesizes has no single equivalent on the raw REST list
  endpoint a conditional request would have to use (that endpoint gives
  only a two-way state field plus a separate nullable timestamp field —
  see canonical), and reconstructing the third value correctly without an
  extra per-PR call was out of this session's time budget. canonical:
  gates/closure_sweep.py:91-131 (`_pr_index_all`) versus GitHub REST `GET
  /repos/{owner}/{repo}/pulls`'s documented response shape.
  `find_violations` still calls the pre-existing, unconditional
  `_pr_index_all`; the conditional path covers only the issue-list call.

## Rationale for deviations

- gates/test_closure_sweep.py was not in the frozen write set but needed a
  mechanical one-line-shape update (gh-call whitelist + expected count) to
  stay green after `issue_state_index_all` gained its slug-probe call — see
  docs/issue-1554/reports/implementation/deviation-log.md.
- `_pr_index_all` conditional-caching, named in the proposal, was set aside
  during implementation for the reason in "What did not work" above — a
  scope narrowing, not an added surface. The req-5 acceptance check ("0
  REST quota on an unchanged board") is exercised for the issue-list call
  in tests/test_board_sweep_etag.py.

## Open findings

None.

## Next steps

None for this record's own scope. A follow-up issue could extend
conditional-request coverage to `_pr_index_all` per "What did not work".

## Resolution path

N/A
