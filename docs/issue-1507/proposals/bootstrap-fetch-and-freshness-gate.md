---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
  - gates/repo_scope.py
  - gates/test_repo_scope.py
---

## Request

#1507 requirements 1-2 only (req 3, the authoring-time deploy-hook gate, is
explicitly sequenced later in the issue body and out of scope here). Req 1:
session bootstrap must `git fetch --prune` and record the fetched
origin/main sha before any verification/absence-claim step, with
`tests/test_spawn.py::test_bootstrap_fetches_before_verification`. Req 2:
extend `gates/repo_scope.py`'s existing `as of <sha>` mechanism with a
freshness component so absence claims require "verified against
origin/main at <sha>, fetched <timestamp>", with a `gates/test_repo_scope.py`
extension.

## Constraints

- Reuse the existing `as of <sha>` scope mechanism in `gates/repo_scope.py`
  (#415) — no parallel field/module for freshness.
- Req 3 (authoring-time gate wiring into hooks) is explicitly out of scope;
  building it now would break on schema changes before req 2's phrase
  schema is stable (issue body's own ordering rationale).
- Acceptance requires retroactivity (#362): only records authored after the
  (later, req-3) gate lands are checked — not applicable to req 1-2's
  library-level additions, which carry no existing-record retroactivity
  concern.

## Rationale

Considered wiring the bootstrap fetch directly at the top of `main()`
instead of inside `checkout_issue_branch()`. Rejected: `checkout_issue_branch()`
is the function that already performs the fetch-then-verify sequence
(`_fetch_or_halt()` followed by branch-existence checks) that a session's
first verification step depends on — putting the record-then-fetch call
anywhere else would require re-deriving that ordering guarantee instead of
attaching to the call site that already provides it.

Considered making `check_absence_freshness()` replace `check_repo_scope()`
outright (tightening the existing #415 check in place) instead of adding a
new function. Rejected: #415's `check_repo_scope()` is reused elsewhere
(unrelated call sites) with its permissive scope-phrase acceptance as
designed behavior; tightening it in place would silently change behavior
for those other callers. A dedicated `check_absence_freshness()` — reusing
the same sentence-split/absence/file-anchor primitives — extends the
mechanism (per the issue's mandate) without altering #415's existing
contract for its other callers.

## What will be done

- `spawn.py`: add `bootstrap_fetch_and_record_sha(work_dir, label)` —
  `git fetch --prune -q origin`, fail-closed on error (same house style as
  `_fetch_or_halt`), then records `{sha, fetched_at}` for `_base(work_dir)`
  into a module-level `_BOOTSTRAP_FETCH_RECORD` dict keyed by resolved
  work_dir. Add `get_bootstrap_fetch_record(work_dir)` accessor. Call the
  former from `checkout_issue_branch()` before its existing
  `_fetch_or_halt()`/branch-verification logic.
- `tests/test_spawn.py`: add `test_bootstrap_fetches_before_verification`
  (deliberately-behind-origin clone fixture, asserts no record before the
  call and a correct sha/timestamp after) plus a `checkout_issue_branch`
  integration test, following the existing real-git-fixture pattern in
  `WorkspaceSyncFailClosed`.
- `gates/repo_scope.py`: add `_FRESHNESS_RE` and `check_absence_freshness()`.
- `gates/test_repo_scope.py`: new file — missing-phrase rejection (named
  clause), correct-phrase pass, old-style `as of <sha>`-alone still
  rejected, no-absence-claim not gated, file-scoped-claim skip.

## Accumulation

`bootstrap_fetch_and_record_sha()` adds one more `subprocess.run`-shaped
network call alongside `_fetch_or_halt()` inside `checkout_issue_branch()`,
following that function's existing house style (fail-closed, same
`_run_net`/`subprocess.run` call shape already used one function above it).
If a third or fourth bootstrap-time git call were added later (e.g. a
future requirement needing another ref check before verification), the
right move is to fold them into one shared bootstrap-fetch helper rather
than keep stacking sibling `subprocess.run` calls in
`checkout_issue_branch()` — not attempted here since only one call is being
added and `_fetch_or_halt()` already owns the adjacent one.

## Out of scope

- Req 3 (deploy-hook authoring-time enforcement of the freshness phrase).
- Wiring `check_absence_freshness()` into any live hook/gate pipeline —
  this proposal only adds the checked function and its tests.
- Changing `check_repo_scope()`'s existing behavior for its current callers.

## How you'll know it worked

`python3 -m pytest tests/test_spawn.py -k BootstrapFetchesBeforeVerification -v`
and `python3 gates/test_repo_scope.py -v` both pass.
