# Survey — issue #1681 (GraphQL quota budget)

## Write set (projected, new paths not yet on disk — listed unquoted)
- gates/gh_budget.py (new) — per-consumer-class token-bucket budget over
  a cached rate-limit snapshot, reserve floor, budget-exhausted result,
  distinct message helper.
- `gates/gh_rest.py` (extend) — REST/conditional PR-poll helper (hot path)
  alongside the existing issue/PR title+body REST fetchers.
- gates/test_gh_budget.py (new)
- `gates/test_gh_rest.py` (extend, for the PR-poll helper) — canonical: `ls gates/test_gh_rest.py` confirms the file already exists in the tree.
- `gates/requirement_linkage.py`, `gates/closure_sweep.py` — only if
  wiring the distinct message is in scope for THIS issue's acceptance
  check 2; issue body says spawn.py watchdog wiring is a sequenced
  follow-up, but requirement-drift/closure-sweep message emission is
  explicitly named in check 2, so these two get the message-helper call
  wired at their existing rate-limit-detection sites (no new gh calls
  added to them).

## Prior art in-repo
- canonical: `gates/closure_sweep.py:489-503` (read directly) — `rate_limit_remaining(root)`
  reads `gh api rate_limit` (REST, 0 GraphQL cost), returns
  `(remaining, ok)`.
- canonical: `gates/closure_sweep.py:643-645` (read directly) — the sole existing
  call site (board-sweep) prints
  `f"[watchdog] board-sweep: 미집계 (rate-limit, remaining={remaining})"`
  — this is the message convention issue #1681 wants generalized and
  reused by requirement-drift.
- canonical: `gates/closure_sweep.py:497-560` (read directly) — an existing
  *tick-interval* backoff (`sweep_should_run`/`record_sweep_result`,
  doubling interval on rate-limit, stored in `runs/gh_quota_backoff.json`).
  This is a different mechanism from what #1681 asks for: it is a
  **shared** reactive backoff after a rate-limit is already hit, not a
  **per-class proactive token-bucket budget** that stops a class before
  the account floor is reached. #1681's gh_budget.py is additive, not a
  replacement.
- canonical: `gates/gh_rest.py` (read directly, full file) — REST helpers for
  issue/PR title+body reads (`fetch_issue`, `fetch_issue_body`,
  `fetch_pr_body`, `fetch_pr_title`), all fail-closed (return `None` on
  any `gh`/parse failure), no conditional/ETag caching in this file yet.
- canonical: `gates/patrol_board.py:204-262` (read directly) — the repo's
  existing ETag-conditional `gh api -i` pattern: cache
  `{etag, raw}` under `.git/gh-read-cache/<name>.json`, send
  `If-None-Match`, treat HTTP 304 (gh exits non-zero on 304, so the
  status must be parsed before the returncode check) as a cache hit
  billing 0 calls. `spawn._split_gh_api_i_output` (spawn.py:1401) parses
  `gh api -i` output into `(status, headers, body)`; `spawn._repo_slug`
  (spawn.py:1109) resolves `owner/repo`.

## Consumer classes named in the issue
- **watchdog** — the recurring tick-based observer (issue's own example:
  120s-interval sweeps over all open issues/PRs). Metered, capped.
- **sweep** — requirement-drift / closure-sweep style periodic scans.
  Metered, capped (issue says "sweeps ≤M%").
- **orchestration** — interactive role-session / orchestrator calls
  (`gh pr list`, `gh issue create`, etc.). Gets "the reserved
  remainder" — i.e. draws from what metered classes are forbidden to
  touch (the reserve floor), and is itself unmetered/fail-open per the
  issue text ("fail-open for one-off calls; only recurring pollers are
  metered").

## Open questions resolved for the proposal
- Budget units: the issue says "≤N%/hr" but also wants "no rate_limit
  query per call" — i.e. one snapshot fetch per budget-tracker lifetime
  (per process), decremented locally. Concrete point-caps (not live
  percentages) are simplest to make deterministic and testable without
  network; percentage caps can be computed by the caller from a fetched
  total if desired, but the module's own contract is point budgets +
  a reserve floor, both configurable by the caller.
- Fixture-testability requires an injectable snapshot-fetch function
  (mirrors `closure_sweep.rate_limit_remaining`'s signature) so unit
  tests can stub `(remaining, ok)` without `subprocess`.
- Live check (acceptance's 3rd check, "during a heavy drive, account
  GraphQL remaining never reaches 0") is out of scope for this PR to
  execute — it requires an actual live heavy-drive session, not a unit
  fixture; this proposal delivers the module + tests that make that
  outcome *possible*, wiring into the actual watchdog loop (spawn.py)
  is the named follow-up per the issue body itself.

## Alternatives considered (feeds proposal Rationale)
- Extend `gates/closure_sweep.py`'s existing interval-doubling backoff to
  be "per class" instead of adding a new module — rejected: that backoff
  is reactive (after a rate-limit error) and shared across all sweeps
  under one state file; the issue explicitly wants a *proactive* budget
  that stops a class before it drives the account to 0, and a
  reserved floor for orchestration — different mechanism, not a
  parameter change to the existing one.
- Percentage-of-hourly-quota budgets tracked as a live ratio (recompute
  cap from fetched total every check) — rejected for this module: it
  reintroduces a "does this need the live total" branch on every call,
  works against the "no rate_limit query per call" requirement, and is
  harder to unit-test deterministically; point budgets set by the
  caller (who can derive them from a percentage once, at snapshot time)
  keep the module's own logic simple and fixture-friendly.
