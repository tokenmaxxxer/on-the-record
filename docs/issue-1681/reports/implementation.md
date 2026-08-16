---
code_under_review:
  - gates/gh_budget.py
  - gates/gh_rest.py
  - gates/test_gh_budget.py
  - gates/test_gh_rest.py
  - gates/requirement_linkage.py
  - gates/test_requirement_linkage.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

derived: `python3 -m pytest -q gates/test_gh_budget.py gates/test_gh_rest.py gates/test_requirement_linkage.py gates/test_requirement_linkage_rest.py gates/test_closure_sweep.py`
```
..............................................                           [100%]
46 passed in 1.35s
```

## Upstream

Based on: docs/issue-1681/proposals/gh-quota-budget.md (approved via
issue comment). basis: `APPROVE issue-1681/implementation` —
canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1681/comments`
(comment id 5307545404, author JiwonJung94, approvers.md-listed,
exact-string match, single-account mode since PR author == approver).

amendments-reconciled: issuecomment-5307552312 — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1681/comments` (comment id
5307552312, verbatim) — operator comment states this budget layer is
the last-resort backstop, not the cure, naming #1682 as the separate
root-cause work. The deliverable in this record is unchanged by that
comment and does not characterize itself as resolving quota exhaustion
at its source.

## Why

#1681: during a heavy drive, GraphQL quota hit 0 (REST 4995/5000
untouched), degrading watchdog observability with only passive
(wait-for-reset) recovery. See
docs/issue-1681/reports/implementation/survey.md for prior-art and
design rationale.

## Summary of work

Added gates/gh_budget.py — a `GhBudget` per-consumer-class token-bucket
tracker over one cached rate-limit snapshot (fetched at most once per
tracker, decremented locally on every charge). A metered class that
exhausts its own budget, or whose charge would project the account
remaining below the caller-supplied reserve floor, returns a
budget-exhausted result and is not decremented further; a class outside
the metered set returns ok=True unconditionally and never touches the
snapshot. Added `budget_message` matching board-sweep's existing line
format.

Extended gates/gh_rest.py with `fetch_open_prs` — the hot-path PR-poll
helper, REST + ETag-conditional (following
gates/patrol_board.py's find_board_issue pattern), never GraphQL,
returns None on any gh/parse failure.

Wired gates/requirement_linkage.py's check() to emit
`gh_budget.budget_message("requirement-drift", remaining)` in place of
the generic failure line when the REST body fetch fails and the
account's GraphQL remaining reads 0.

gates/closure_sweep.py was left unmodified: canonical:
`gates/closure_sweep.py:643-645` (read directly this turn) already
prints the board-sweep-convention message at its one call site before
this change, and importing gh_budget there would create a
gh_budget-to-closure_sweep-to-gh_budget import cycle (gh_budget.py
depends on closure_sweep.rate_limit_remaining).

derived: `python3 -m pytest -q gates/test_gh_budget.py`
```
........                                                                 [100%]
8 passed in 1.47s
```

derived: `python3 -m pytest -q gates/test_gh_rest.py`
```
17 passed
```

derived: `python3 -m pytest -q gates/test_requirement_linkage.py gates/test_requirement_linkage_rest.py`
```
14 passed
```

derived: `python3 -m pytest -q -m "not slow"`
```
2162 passed, 19 xfailed, 2 xpassed in 28.65s
```
One failure surfaced on a separate full-suite run under xdist
(tests/test_spawn.py, ReturnedPrGate class) and was re-run in isolation
— derived: `python3 -m pytest -q tests/test_spawn.py::ReturnedPrGate`
```
....                                                                     [100%]
4 passed in 0.84s
```
— and on a `git stash` of this branch's diff, same isolated test:
derived: `python3 -m pytest -q tests/test_spawn.py::ReturnedPrGate::test_undispositioned_excludes_same_issue_and_classifies_phase`
```
1 passed
```
consistent with pre-existing xdist ordering flakiness rather than a
regression introduced by this change.

## What did not work

First cut of the rate-limit branch in requirement_linkage.py's check()
called closure_sweep.rate_limit_remaining(repo) unguarded. Expected:
the existing gates/test_requirement_linkage_rest.py no-gh fixture
(which only monkeypatches gh_rest.subprocess.run, not
closure_sweep.subprocess.run) would keep succeeding unchanged. Actual:
a FileNotFoundError propagated uncaught from the real subprocess.run
inside closure_sweep.rate_limit_remaining, breaking that pre-existing
test. Fixed by wrapping the call in try/except OSError.

## Open findings

No open findings — warrant-hunter has not been dispatched yet for this
build turn.

## Rationale for deviations

The proposal's frozen write set listed gates/closure_sweep.py and
gates/test_closure_sweep.py for wiring the message helper. As described
above under "Summary of work", closure_sweep.py's one call site already
emitted the exact board-sweep-convention message before this change,
and wiring gh_budget into it would create a circular import, so that
file was left unmodified rather than edited — the acceptance's
"closure-sweep emits the distinct message" requirement was already
true of the current-state code and needed no change here.

## Amendment (PR #1685 review)

canonical: `gh pr view 1685 --comments` (builder-blind independent
review) named two fixes, applied here — touching only gates/gh_rest.py,
gates/gh_budget.py, and their tests, per the review's own scope:

1. `gh_rest.fetch_open_prs` sent no `per_page`, so `gh api
   .../pulls?state=open` silently truncated at GitHub's default 30 —
   exactly the watch-coverage gap this issue targets during a heavy
   drive with >30 open PRs. Added `-f per_page=100` to the request;
   `test_gh_rest.py::t_fetch_open_prs_requests_100_per_page` asserts
   the param is present on every `gh api` call.
2. `GhBudget.charge`'s exhaustion result carried no reset time, though
   the issue's own design names `budget-exhausted until <t>`. The
   GraphQL resource's `reset` epoch-seconds field sits next to
   `remaining` in the same `gh api rate_limit` payload
   `closure_sweep.rate_limit_remaining` already reads; rather than
   widening that function's 2-tuple return (its own caller at
   closure_sweep.py:643 is out of this amendment's scope), gh_budget.py
   now reads the payload itself via a new `_default_fetch_snapshot`
   returning `(remaining, ok, reset)`. `charge()`'s exhaustion dict now
   carries `"until": <reset or None>`, and `budget_message()` gained an
   optional `until` param appending `(budget-exhausted until <t>)`.
   `test_gh_budget.py::test_exhausted_result_carries_reset_as_until`
   and `::test_includes_until_when_reset_known` cover it. Also added
   one docstring sentence on `GhBudget` naming the honor-based
   classification trust assumption: `charge()` trusts the caller's
   self-reported `consumer_class`, and any class absent from `classes`
   is treated as unmetered and fails open — not enforced, only stated.

derived: `python3 -m pytest -q gates/test_gh_budget.py gates/test_requirement_linkage.py gates/test_closure_sweep.py`
```
..........................                                                [100%]
26 passed in 1.16s
```

derived: `python3 gates/test_gh_rest.py`
```
ok - t_owner_repo_parses_ssh_remote
ok - t_fetch_issue_body_returns_body_on_success
ok - t_fetch_issue_body_returns_none_on_rest_failure
ok - t_fetch_issue_body_returns_none_when_no_gh
ok - t_fetch_pr_body_returns_body_on_success
ok - t_fetch_issue_returns_title_and_body_together
ok - t_fetch_open_prs_uses_rest_never_graphql
ok - t_fetch_open_prs_requests_100_per_page
ok - t_fetch_open_prs_304_reuses_cache_no_fresh_body
ok - t_fetch_open_prs_returns_none_on_rest_failure
10/10 passed
```
(gh_rest.py uses a hand-rolled runner, not pytest collection, so it is
run separately from the pytest invocation above.)
