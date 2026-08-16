---
code_under_review:
  - path: spawn.py
  - path: tests/test_spawn.py
  - path: gates/gh_delta.py
  - path: gates/gh_budget.py
  - path: docs/issue-1688/reports/implementation/survey.md
  - path: docs/issue-1688/proposals/wire-delta-into-watchdog.md
loop_state: landed
type: feature
breaking: false
canonical: pytest -q tests/test_spawn.py -k board_wide_sweep executed live this session
verdict: pass
---

## What was done

Wired `gates/gh_delta.py` (`fetch_delta`) and `gates/gh_cache.py`
(`cached_get`) (landed module-only in #1682) into `spawn.py`'s watchdog tick
path:

- `_board_wide_sweep` now calls `fetch_delta(root, slug, "issues")`
  once per tick, right after the existing backoff/rate-limit guards, as the
  tick's single conditional probe.
- classification `"no-change"`: closure-sweep/spawn-on-pr/spawn-coverage
  detail fetches and requirement-drift's full rescan are skipped; an explicit
  `no-change (delta empty)` line is printed; `accumulation_trend()` still runs
  unconditionally (zero gh calls, pre-existing contract).
- classification `"delta"`: `find_violations` is called with a `subjects`
  dict narrowed to the delta's issue/PR numbers (cross-referenced against
  `board(root)`); `requirement_drift(root, changed_numbers=...)` re-fetches
  only those numbers via `cached_get` and reuses a small on-disk verdict
  cache (`runs/requirement_drift_cache.json`, atomic temp+rename write) for
  everything else.
- classification `"full-rescan"`: falls through unchanged to today's
  full-board logic; an explicit `full-rescan` line is printed (gh_delta does
  not expose a reason string, so the line states that plainly rather than
  fabricating one).
- classification `"error"`: falls back to today's full logic (conservative),
  logs that gh_delta itself failed.
- `slug is None` (non-GitHub repo): falls back to today's full logic
  silently — pre-existing behavior, untouched.

Amendment (PR #1691 review, both blockers addressed on this branch):

- **PR-only delta drops (blocker 1)**: `gates/gh_delta.py` (`fetch_delta`,
  around gates/gh_delta.py:102) gained an additive `include_prs: bool = False`
  param (default preserves every existing caller's behavior unchanged — no
  extra `gh` call, same response already fetched by the single probe).
  spawn.py's `_board_wide_sweep` (around spawn.py:3138) now calls
  `fetch_delta(root, slug, "issues", include_prs=True)`. Changed PR items are
  split from changed issue items by the `pull_request` key; each PR number is
  mapped to its subject issue via `closure_sweep._pr_index_all(root)`
  (a `gh pr list` call, already used elsewhere in this file for the same
  branch->PR index) and its `headRefName` matched against `^issue-(\d+)/` —
  the matched subject number is unioned into `changed_numbers`. This extra
  `gh pr list` call only fires when the delta actually contains changed PR
  items (never on a no-change or issue-only tick). A failed PR-index lookup
  or an unparseable head-ref logs an explicit line and drops that PR from
  narrowing rather than silently ignoring it.
- **`gates/gh_budget.py` false-nonexistence claim + unwired metering
  (blocker 2)**: canonical: `git log --oneline -3` on this branch, read live
  this session, shows `10b23780` (this issue's prior commit) sits on top of
  `ca66636a` ("Merge pull request #1685 from
  tokenmaxxxer/issue-1681/implementation") — `gates/gh_budget.py` was landed
  by that merge and exists on this branch's own base; it was read directly
  (its `GhBudget`/`charge`/`budget_message` are used below). The "no such
  module exists" open finding below was wrong. spawn.py's
  `_board_wide_sweep` (around spawn.py:3195) now instantiates
  `gh_budget.GhBudget(root, classes={"watchdog": 200},
  reserve=closure_sweep._RATE_LIMIT_GUARD_THRESHOLD)` once per tick and
  charges the `"watchdog"` class before both gh-calling points: once before
  the `gh_delta` probe itself, and once (cost = number of sweep categories
  selected this tick) before the `issue_state_index_all`/`find_violations`/
  `spawn_coverage` block. A `budget-exhausted` charge result prints
  `gh_budget.budget_message(...)` and skips that step (falls through to
  `_run_local_only_signals`), exactly like the existing rate-limit-guard
  skip path.
- Non-blocking notes from the same review applied: `requirement_drift`'s
  delta-mode per-number fetch failures now print an explicit
  `조회 실패 [...] — 이전 캐시 판정 유지` line instead of silently vanishing
  (spawn.py, `_fetch_issue_or_pr_via_cache` call site around spawn.py:2921).
  The closed-item filter note (delta mode matching full mode's `--state
  open`) was not applied — see Open findings.

## Why

`gates/gh_delta.py` and `gates/gh_cache.py` existed but nothing called them
(issue #1688's own framing) — the watchdog's board-sweep and
requirement-drift kept doing full per-tick gh rescans, burning GraphQL/REST
quota every tick regardless of whether anything changed on the board.

## Upstream

Based on #1682's landed modules `gates/gh_delta.py` and `gates/gh_cache.py`
(see `docs/issue-1682/proposals/` and PR #1687 for their own design/contract).
This issue only wires them into a consumer; their internals are unchanged.

## What did not work

None.

## Open findings

- (Superseded, kept for history) The two bullets that used to sit here
  claimed PR changes were intentionally left unprobed and that `gh_budget`
  did not exist; both claims were wrong per PR #1691's review. canonical:
  the "Amendment" paragraphs in this file's opening section, above under
  the work-summary heading, name the `include_prs`/PR-index-mapping change
  and the `gh_budget.GhBudget` wiring made this session, with file:line
  locations.
- Non-blocking, not applied: canonical: spawn.py:2889-2894 (full-mode
  `_list()`, calls `gh issue/pr list --state open`) and spawn.py:2921-2922
  (delta-mode's per-number `_fetch_issue_or_pr_via_cache` call, no state
  filter), both read live this session — a delta-mode recheck of a
  since-closed issue/PR could differ from what a full-mode rescan of the
  same tick would produce.
  Resolution path: track as a follow-up if this drift-cache mismatch is
  observed live; low blast radius since requirement-drift is advisory-only
  and never gates anything (spawn.py:2859-2860's own documented contract).

## Test evidence

acceptance: python3 -m pytest -q -m "not slow" tests/test_spawn.py
canonical: pytest -q -m "not slow" tests/test_spawn.py, executed live this session — result: 418 passed, 3 xfailed, 1 xpassed (1 failure on first `-n auto` parallel run, MustMcpAllowEnv::test_unset_env_leaves_allow_list_unchanged; isolated re-run passed — cross-test env pollution, unrelated to this change and pre-existing)

acceptance: python3 -m pytest -q -m slow tests/test_spawn.py
canonical: pytest -q -m slow tests/test_spawn.py, executed live this session — result: 100 passed, 2 xfailed

acceptance: python3 -m pytest -q tests/test_spawn.py -k "board_wide_sweep or requirement_drift_delta" gates/test_gh_delta.py gates/test_gh_budget.py
canonical: pytest -q tests/test_spawn.py -k "board_wide_sweep or requirement_drift_delta" gates/test_gh_delta.py gates/test_gh_budget.py, executed live this session (PR #1691 amendment: PR-only-delta subject mapping + GhBudget wiring) — result: 18 passed

acceptance: python3 -m pytest -q -m "not slow" tests/test_spawn.py
canonical: pytest -q -m "not slow" tests/test_spawn.py, executed live this session after the PR #1691 amendment — result: 421 passed, 3 xfailed, 1 xpassed

## Next steps

None — landed.
