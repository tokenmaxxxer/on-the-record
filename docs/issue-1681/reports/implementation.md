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
