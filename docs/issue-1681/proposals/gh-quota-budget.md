---
status: proposed
files:
  - gates/gh_budget.py
  - gates/gh_rest.py
  - gates/test_gh_budget.py
  - gates/test_gh_rest.py
  - gates/requirement_linkage.py
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
  - gates/test_requirement_linkage.py
---

## Request

#1681: during a heavy drive, GraphQL quota hit 0 while REST sat almost
untouched (measured live: REST 4995/5000). Recovery was passive (wait
for reset). Build a structural, client-side quota budget: a shared
module every recurring `gh` caller goes through, enforcing per-consumer-
class token-bucket budgets (watchdog/sweep metered, orchestration draws
the reserved remainder) over one cached rate-limit snapshot with local
decrement (no `rate_limit` query per call). A metered class that
exhausts its own budget gets an explicit budget-exhausted result and
skips; the account-level reserve floor is never crossed by metered
classes; unmetered one-off calls fail open. Also shift the hot-path
PR-poll helper to REST/conditional, and give requirement-drift/
closure-sweep the same distinct rate-limit message board-sweep already
emits. spawn.py's watchdog wiring is an explicitly out-of-scope,
sequenced follow-up (avoids a collision with #1678, in flight on
spawn.py concurrently).

## Constraints

- No network in unit tests; the account-level live check (acceptance's
  3rd check) is not executed by this PR — it needs an actual heavy
  drive, not a fixture.
- Do not touch spawn.py.
- gh_budget must not query `gh api rate_limit` more than once per
  tracker lifetime — callers get one cached snapshot, decremented
  locally on every charge.
- The reserve floor is an account-level invariant checked against the
  *projected* remaining after a metered charge, never crossed by any
  metered class regardless of which class is charging.
- Message format must match the existing board-sweep convention exactly
  (`gates/closure_sweep.py:645`): `[watchdog] <source>: 미집계
  (rate-limit, remaining=<n>)`.

## Rationale

Considered folding this into `closure_sweep.py`'s existing interval-
doubling backoff (`sweep_should_run`/`record_sweep_result`) instead of a
new module. Rejected: that backoff is *reactive* — it only widens the
polling interval after a sweep has already hit a rate-limit error, and
it is one shared state file across all sweeps, with no notion of
per-class budget or an account-level reserve floor that orchestration
calls can rely on. #1681 explicitly wants a *proactive* budget that
stops a metered class before the account is driven to 0, which is a
different mechanism (charge-before-call vs. back-off-after-failure), so
it is additive, not a parameter change to what already exists.

Considered tracking budgets as a live percentage of the fetched hourly
total, recomputed on each charge. Rejected for this module: it
reintroduces a "do we need the live total right now" branch on every
call, works against the "no rate_limit query per call" requirement, and
is harder to unit-test deterministically without network. Point budgets
(caller-supplied, optionally derived from a percentage once at snapshot
time) keep the module deterministic and fixture-friendly.

## What will be done

1. `gates/gh_budget.py` — a `GhBudget` tracker: constructed with a
   `root: Path`, a `classes: dict[str, int]` per-class point budget
   (e.g. `{"watchdog": N, "sweep": M}`), a `reserve: int` account-level
   floor, and an injectable `fetch_snapshot` callable defaulting to
   `closure_sweep.rate_limit_remaining` (so it reuses the existing
   REST-only, 0-GraphQL-cost snapshot read). `.charge(consumer_class,
   cost=1)`:
   - fetches the snapshot exactly once (cached thereafter, decremented
     locally on every charge — no repeat `rate_limit` queries);
   - unmetered classes (not in `classes`) fail open: always `ok=True`
     (orchestration draws the reserved remainder by simply never being
     capped);
   - metered classes: exhausting their own per-class budget, or a
     charge that would project the account remaining below `reserve`,
     returns `{"ok": False, "reason": "budget-exhausted", "class":
     ..., "remaining": ...}` (skip) without decrementing further;
     otherwise decrements both the per-class counter and the cached
     snapshot and returns `{"ok": True, ...}`.
   - `budget_message(source: str, remaining: int) -> str` — the shared
     message helper, format matching board-sweep's convention exactly,
     for reuse by requirement-drift/closure-sweep/future watchdog
     wiring.
2. `gates/gh_rest.py` — add a REST/conditional PR-poll helper
   (`fetch_open_prs`, ETag-cached under `.git/gh-read-cache/`, following
   `patrol_board.find_board_issue`'s `gh api -i` + `If-None-Match` + 304
   pattern) for the hot-path PR list used by pollers, so that path never
   touches GraphQL.
3. Wire `budget_message` into `gates/requirement_linkage.py` and any
   `gates/closure_sweep.py` sweep call site that currently detects a
   rate-limit condition without the board-sweep-style message, so both
   emit the same distinct string at `remaining=0`. No new `gh` calls are
   added to either file for this.
4. Tests: `gates/test_gh_budget.py` (fixture-only, no network) covering
   — watchdog-class exhaustion vs. orchestration-class pass-through;
   reserve floor never crossed by a metered class; snapshot fetched
   once per tracker regardless of call count. `gates/test_gh_rest.py`
   extended for the PR-poll helper (fixture asserts the command it
   shells out to is REST, never `gh pr list --json`/GraphQL). Message-
   format tests for requirement-drift/closure-sweep at `remaining=0`.

## Accumulation

This adds one more `gh`-calling module (`gh_budget.py`) alongside the
existing ones (`gh_rest.py`, `closure_sweep.py`, `patrol_board.py`), and
wires two more call sites (requirement-drift, closure-sweep) through the
shared `budget_message` helper instead of inlining another ad-hoc
rate-limit string. If N more sweep/watchdog call sites appear later,
each one calls `GhBudget.charge(class, ...)` and `budget_message(...)`
rather than adding its own inline `subprocess`/message-formatting copy
— the accumulation point is centralized in gh_budget.py itself (one
charge path, one message format), so N more callers means N more
one-line `charge()`/`budget_message()` call sites, not N more copies of
the token-bucket or message logic. No repeated-file (roles/*.json-style)
edits are involved.

## Out of scope

- spawn.py / the actual watchdog loop wiring gh_budget in for real
  ticks (sequenced follow-up, avoids collision with #1678 in flight).
- Executing the acceptance's live check (heavy-drive GraphQL-never-0)
  — needs a real drive, not this PR.
- Percentage-based budget derivation tooling (callers pass point
  budgets directly for now).

## How you'll know it worked

- `python3 -m pytest -q gates/test_gh_budget.py gates/test_gh_rest.py
  gates/test_closure_sweep.py gates/test_requirement_linkage.py` passes,
  covering: a watchdog-class consumer exhausting its budget gets
  budget-exhausted while an orchestration-class call still passes; the
  reserve floor is never crossed by a metered class; the snapshot fetch
  is called at most once per tracker across many charges (no network,
  fixture-injected fetch); the PR-poll helper's fixture shows no
  GraphQL invocation; requirement-drift/closure-sweep emit the distinct
  message at `remaining=0`.
