---
proposal: commit c81af5af (issue-2173: flag phase-1 Acceptance format early, auto-spawn phase-2 on approval)
---

# Hunt record — spawn-on-approve

## before-landing — stance 1: spawn-on-approve budget/pr_index wiring in watchdog._board_wide_sweep

Verdict: FINDING — gates/spawn_on_approve.py's PR lookup fan-out is O(candidate branches) real `gh` calls when `pr_index` is None, unlike its two sibling categories which fall back to a single bulk fetch, and none of those per-branch calls are counted by watchdog's `_charge_watchdog_budget` per-tick accounting.
Kind: composition
Seed: git show --stat c81af5af; git diff b9cd89af..c81af5af -- gates/spawn_on_approve.py watchdog.py gates/closure_sweep.py
cap_seconds: not specified by dispatcher (standalone invocation)
tier: default
diff_stat_lines: 821 insertions, per `git show --stat c81af5af`
started_at: 2026-08-24T17:05:00+09:00
ended_at: 2026-08-24T17:40:00+09:00

### Reproduce
Ran `gates/spawn_on_approve.ready_for_phase2(root, issue_states=..., pr_index=None)` directly (the same call the module makes internally whenever `shared_pr_index` is `None`) against a repo with 5 local `issue-N/implementation` branches, all approved, no phase-2 board record, with `subprocess.run` instrumented to count `gh` invocations:

```
$ python3 /tmp/repro/count_calls.py   # calls spawn_on_approve.ready_for_phase2(repo, issue_states=..., pr_index=None)
result: {}
gh calls made: 5
```

Contrast with the sibling module `gates/spawn_on_pr.py`, whose equivalent callers (`park_check`, `spawn_prs`, `missing_verification`) all do `if pr_index is None: pr_index, _ = closure_sweep._pr_index_all(root)` — exactly ONE bulk `gh pr list` call regardless of candidate count — before doing any per-branch lookup. `spawn_on_approve.py`'s `_pr_number_for_branch()` has no such bulk-fetch fallback; it falls straight through to `spawn._pr_open_or_merged_for_branch(root, branch)` (one `gh pr list --head <branch>` subprocess call) for every candidate that survives the earlier local-only filters, and `ready_for_phase2()` evaluates ALL candidates (not capped by `SPAWN_CAP`) before `spawn_phase2()` applies the cap.

`watchdog.py::_board_wide_sweep` only builds `shared_pr_index` (and therefore avoids this path) when `_pr_index_consumers >= 2`, i.e. when at least one other PR-index-consuming category (`spawn-on-pr`/`closure-sweep`) also runs in the same tick. With today's constants (`call_budget = 8`, 4 total `BOARD_SWEEP_CATEGORIES`), `closure_sweep.next_categories()` always returns all 4 categories together every tick, so in the currently-wired watchdog flow this path is masked — `shared_pr_index` happens to always be populated whenever `spawn-on-approve` runs. But the function is public, is exactly the code path exercised by `tests/test_spawn_on_approve.py` (always with a single-branch fixture, so N=1 never reveals the fan-out), and the masking is an incidental consequence of `call_budget(8) > category_count(4)` that nothing enforces — e.g. a future 5th `BOARD_SWEEP_CATEGORIES` entry, or any direct/future caller passing `pr_index=None` with many local branches, silently reintroduces one uncounted `gh` call per candidate branch, defeating the entire point of the `_charge_watchdog_budget`/`gh_budget` per-tick call accounting this feature is supposed to be gated by (issue #1498/#1554/#1681's "요구 5: 틱당 호출 예산" requirement).

### Expected
`_pr_number_for_branch()` in `gates/spawn_on_approve.py` should fall back to a single bulk `closure_sweep._pr_index_all(root)` fetch (like `spawn_on_pr.py` does) when `pr_index` is `None`, so a `spawn-on-approve` tick makes at most O(1) additional real `gh` calls — matching the invariant the rest of `_board_wide_sweep`'s budget accounting (`cost=len(this_tick)`, one token per category) already relies on for its sibling categories.
