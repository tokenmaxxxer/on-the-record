# issue-1688 survey

Read before drafting the proposal:

- `gates/gh_delta.py` — `fetch_delta(root, slug, resource, ...)` returns
  `(items, new_cursor_since, classification)` with classification in
  `{"delta", "no-change", "full-rescan", "error"}`. Cold/corrupt cursor and
  page overflow both drive `full-rescan`. `resource="pulls"` reuses the
  `/issues` endpoint (no `since` support on `/pulls`) and filters
  client-side on the `pull_request` key; `resource="issues"` filters the
  opposite way (keeps only non-PR issues).
- `gates/gh_cache.py` — `cached_get(url, root=None, run=None, cache_root=None)`
  returns `(data, ok, billed_calls)`, ETag-conditional, shared cache under
  `~/.tokenmaxxxer/gh-cache/`, atomic temp+rename writes.
- `spawn.py:_board_wide_sweep(root)` (~line 2967) — per-tick entry point.
  After backoff/rate-limit guards, it picks `this_tick` categories via
  `closure_sweep.next_categories`, then runs spawn-on-pr / closure-sweep /
  spawn-coverage against the full board every tick, and always calls
  `_run_local_only_signals()` (accumulation_trend + requirement_drift, both
  currently unconditional).
- `spawn.py:requirement_drift(root)` (~line 2808) — lists ALL open
  issues+PRs via `gh issue list` / `gh pr list` every call, matches
  `R\d+` mentions against `docs/specs/requirement-digest.md`.
- `gates/closure_sweep.py:find_violations(root, subjects=None, issue_states=None)`
  — already accepts an optional `subjects` dict shaped like `spawn.board(root)`;
  when given, it only evaluates those subjects. No core-logic change needed
  here — the existing optional parameter is exactly the hook #1688 needs.

Conclusion: the wiring point is `_board_wide_sweep`, calling `gh_delta.fetch_delta`
once per tick (resource="issues") right after the existing backoff/rate-limit
guards, and using its classification to pick between (a) skipping detail work
entirely (no-change), (b) narrowing `find_violations`'s `subjects` and
`requirement_drift`'s recheck set to the delta's issue/PR numbers (delta), or
(c) falling through unchanged to today's full-board logic (full-rescan/error/no-slug).
`gh_budget` (#1681) was searched for (`grep -rn gh_budget` repo-wide, case
insensitive, excluding `__pycache__`) — no such module exists yet, so the
backstop-metering sub-point (#8) is a no-op per the issue's own allowance.
