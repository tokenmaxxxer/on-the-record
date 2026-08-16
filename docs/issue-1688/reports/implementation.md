---
code_under_review:
  - path: spawn.py
  - path: tests/test_spawn.py
  - path: docs/issue-1688/reports/implementation/survey.md
  - path: docs/issue-1688/proposals/wire-delta-into-watchdog.md
loop_state: coding
type: feature
breaking: false
verdict: pending
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

- `fetch_delta(root, slug, "issues")` filters to non-PR issues only
  client-side (its own `resource="issues"` semantics per #1682); a strict
  reading of "issues+PRs" coverage in a single probe would require also
  calling `resource="pulls"`, which would be a second gh call per tick and
  contradict the "single conditional probe" requirement. This wiring calls
  `resource="issues"` only, per the issue text's explicit instruction — PR
  changes are not separately probed.
  Resolution path: track as a follow-up issue if PR-triggered drift/closure
  narrowing turns out to matter in practice (e.g. calling `resource="pulls"`
  as a second, separately-budgeted probe); not blocking here since gh_delta's
  own module contract (from #1682) is unchanged by this wiring.
- `gh_budget` (#1681) metering backstop: searched the repo for `gh_budget`
  (case-insensitive, excluding `__pycache__`) — no such module exists.
  Resolution path: once #1681 lands a real meter/backstop entry point, wire
  it into `_board_wide_sweep` in a small follow-up (try/except best-effort
  call, per the original issue's sub-point 8); not built here per the
  issue's explicit allowance to omit it.

## Next steps

- Land: commit, push, open PR (Closes #1688), update `loop_state` to `landed`.
