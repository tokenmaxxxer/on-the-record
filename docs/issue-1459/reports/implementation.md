---
code_under_review:
  - spawn.py
  - gates/ci.py
  - tests/test_gh_read_cost.py
  - tests/test_spawn.py
type: enhancement
breaking: false
verdict: pending
loop_state: committing
---

## What was done

Implemented the three gh-cost-reduction mechanisms scoped in #1459, touching
only `spawn.py` read helpers and `gates/ci.py`'s paginated commit-list read
(no `gates/spawn_on_pr.py` trigger logic, no reduction in what sessions
observe):

1. **`per_page=100` everywhere**: `spawn.py` `_issue_comments` (both the
   ETag-probe request and the `_issue_comments_uncached`/
   `_issue_comments_more_pages` fallback paths) and `gates/ci.py`
   `_pr_commit_messages` now carry `-f per_page=100` on every
   `gh api ... --paginate --slurp` call.
   derived: `grep -n "per_page=100" spawn.py gates/ci.py`
   ```
   spawn.py:1295:                        "-f", "per_page=100", "--paginate", "--slurp"],
   spawn.py:1312:                        "-f", "per_page=100", "-f", "page=2",
   spawn.py:1364:           "-f", "per_page=100", "-i"]
   gates/ci.py:107:                        "-f", "per_page=100", "--paginate", "--slurp"],
   ```
2. **Bulk comment reads via REST**: `spawn.py` `_issue_comments` was already
   `gh api repos/<r>/issues/<n>/comments` (REST) before this issue, not the
   GraphQL `gh issue view --json comments`.
   derived: `grep -rn "issue view.*--json comments\|gh api.*issues/.*comments" spawn.py gates/*.py`
   ```
   (no "issue view --json comments" hits in spawn.py/gates/)
   spawn.py:1294:    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{number}/comments",
   ```
   `_issue_comments`'s returned shape (`login`, `body`) is unchanged, matching
   what every call site consumes.
   derived: `grep -n '\.get("id"\|\.get("created_at"\|createdAt' spawn.py gates/*.py`
   ```
   (no call site of _issue_comments reads id/created_at/createdAt)
   ```
3. **ETag conditional re-reads**: `spawn.py` `_issue_comments` sends page 1
   (`per_page=100`) with `-i` always, adding `If-None-Match: <cached-etag>`
   when a cache entry exists at `.git/gh-read-cache/issue-<n>-comments.json`.
   A `304` short-circuits to the cached full thread (0 counted calls). A
   `200` re-reads remaining pages unconditionally when `Link` indicates
   `rel="next"`, and refreshes the cache. Any transport failure, unparsable
   response, or corrupt/malformed cache falls back to the pre-existing
   unconditional full fetch (`_issue_comments_uncached`) — fail-open.

## Why

Operator directive in the issue: role sessions and gates were re-reading
entire comment threads at GraphQL cost on every canonical-citation/amendment
check, exhausting the shared 5,000/h GraphQL pool during concurrent
verification sessions (observed 2026-08-14, 1,400+/h per the issue body).
The fix must not change read semantics or reduce watch-coverage.

## Upstream

Basis: issue #1459 body (validity-consult 2026-08-14T07:30:30, commit
2da02eb6). No prior phase-1 proposal existed on this branch; approval was
already posted as an issue comment (`APPROVE issue-1459/implementation` by
JiwonJung94, a listed approvers.md account, single-account mode) before this
session started, so phase 2 proceeded directly.
canonical: `gh issue view 1459 --json comments`

## What did not work

None.

## Acceptance verification

canonical: `python3 -m pytest tests/test_gh_read_cost.py -v`
acceptance: `python3 -m pytest tests/test_gh_read_cost.py -v` — result: green (see fence below)
```
tests/test_gh_read_cost.py::TestReadEquivalence::test_read_equivalence PASSED
tests/test_gh_read_cost.py::TestCountedCallsBounded::test_counted_calls_bounded PASSED
tests/test_gh_read_cost.py::TestCacheFailureFallback::test_cache_failure_fallback PASSED
tests/test_gh_read_cost.py::TestNoObservationLoss::test_no_observation_loss PASSED

4 passed in 0.05s
```

canonical: `python3 -m pytest tests/test_gh_read_cost.py -v` (output above)
checked: tests/test_gh_read_cost.py::test_read_equivalence — result: green

canonical: `python3 -m pytest tests/test_gh_read_cost.py -v` (output above)
checked: tests/test_gh_read_cost.py::test_counted_calls_bounded — result: green

canonical: `python3 -m pytest tests/test_gh_read_cost.py -v` (output above)
checked: tests/test_gh_read_cost.py::test_cache_failure_fallback — result: green

canonical: `python3 -m pytest tests/test_gh_read_cost.py -v` (output above)
checked: tests/test_gh_read_cost.py::test_no_observation_loss — result: green

canonical: `gh api rate_limit --jq '{graphql: .resources.graphql, rest: .resources.core}'`
acceptance: `gh api rate_limit` before this session's work — result:
```
{"graphql":{"limit":5000,"remaining":2221,"reset":1786694551,"used":2779},"rest":{"limit":5000,"remaining":4969,"reset":1786694571,"used":31}}
```

canonical: session's own tool-call transcript (no long-lived comment-heavy
issue and no concurrent-session harness available inside this turn)
unverifiable: a full "one role-session bootstrap + record run on a long
issue" before/after A/B against the 2026-08-14 1,400+/h baseline — reason:
this single turn has no live long-lived comment-heavy issue and no
concurrent-session load to reproduce the operator's original measurement
against. The mechanism's call-count reduction is instead asserted directly
by `test_counted_calls_bounded` (unit-provenance), matching the issue's own
provenance split ("executed-unit for the four tests; executed-live for the
rate_limit check line").

## Open findings

None.

Resolution path: none — no open findings to resolve.

## Next steps

Push this branch and open the phase-2 delivery PR carrying `Closes #1459`.
