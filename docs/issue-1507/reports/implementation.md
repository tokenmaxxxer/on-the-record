---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
  - gates/repo_scope.py
  - gates/test_repo_scope.py
type: feature
breaking: false
# canonical: acceptance: `python3 -m pytest tests/test_spawn.py -k BootstrapFetchesBeforeVerification -v` — result: pass, this session's own run (pasted below in Test evidence)
verdict: pass
loop_state: landed
---

# issue-1507 implementation record (requirements 1-2 only)

## What was done

canonical: spawn.py:6683-6690 (direct read this session)

Requirement 1: added `bootstrap_fetch_and_record_sha(work_dir, label)` and
`get_bootstrap_fetch_record(work_dir)` to `spawn.py`, wired the former into
`checkout_issue_branch()` so it runs `git fetch --prune` and records the
resulting origin/main sha + fetch timestamp into a module-level
`_BOOTSTRAP_FETCH_RECORD` dict before any of that function's existing
branch-verification logic executes.

canonical: gates/repo_scope.py (direct read this session, functions added at end of file)

Requirement 2: added `_FRESHNESS_RE` and `check_absence_freshness()` to
`gates/repo_scope.py`, extending the existing `_SCOPE_RE`/`check_repo_scope()`
mechanism from issue #415 rather than adding a parallel field. The freshness
phrase pattern was folded into `_SCOPE_PHRASES` too, so the original #415
check recognizes it as well. `check_absence_freshness()` is the stricter
function requiring the freshness phrase specifically — a bare `as of <sha>`
does not satisfy it. See Test evidence below for the executed proof.

## Why

canonical: docs/issue-1507/proposals/bootstrap-fetch-and-freshness-gate.md

Issue #1507 traces a real incident (a phase-2 session, PR #1505, wrongly
claimed record-tiering hooks "do not exist" against a stale checkout,
triggering a moot reopen/respawn chain) to a verification-protocol gap:
nothing forced a fresh fetch before an absence claim, and nothing required
the claim to name the sha/timestamp it was checked against. Reqs 1-2 close
that gap at the library level; req 3 (wiring an authoring-time hook that
refuses records missing the phrase) is explicitly deferred in the issue
body until the phrase schema is stable.

## Upstream / basis

basis: docs/issue-1507/reports/implementation/survey.md

## Test evidence

canonical: acceptance: `python3 -m pytest tests/test_spawn.py -k BootstrapFetchesBeforeVerification -v` — result: pass, this session's own run

```
tests/test_spawn.py::BootstrapFetchesBeforeVerification::test_bootstrap_fetches_before_verification PASSED
tests/test_spawn.py::BootstrapFetchesBeforeVerification::test_checkout_issue_branch_records_sha_before_returning PASSED
2 passed in 2.15s
```

canonical: acceptance: `python3 gates/test_repo_scope.py -v` — result: pass, this session's own run

```
test_current_sha_and_timestamp_phrase_passes (__main__.AbsenceFreshnessGate) ... ok
test_file_scoped_absence_claim_is_skipped (__main__.AbsenceFreshnessGate) ... ok
test_missing_phrase_is_rejected_with_named_clause (__main__.AbsenceFreshnessGate) ... ok
test_no_absence_claim_is_not_gated (__main__.AbsenceFreshnessGate) ... ok
test_old_style_as_of_sha_alone_is_not_enough (__main__.AbsenceFreshnessGate) ... ok
test_violation_equality (__main__.AbsenceFreshnessGate) ... ok

Ran 6 tests in 0.000s

OK
```

## Test-tier note (issue #1518)

canonical: `ls .on-the-record/test-tiers.json` — result: no such file, this session's own run

No `.on-the-record/test-tiers.json` exists at repo root. This session ran
only the tests it added (targeted with `-k`) plus the new gate module
directly, not the full `tests/test_spawn.py` module or full repo suite.
Full-suite wall-clock was not measured this session — a tiering gap for
this repo remains unresolved and is surfaced here per the test-tier
directive rather than silently skipped.

## What did not work

None — no attempt was undone or replaced during this session.

## Document placement

- [x] No env var, config key, new dependency, or migration was introduced
  by this change — no handbook update required.
- [x] Library/format choice over a named alternative (extend
  `gates/repo_scope.py` in place vs. a new module; in-process dict vs.
  file-based record) — recorded in
  docs/issue-1507/proposals/bootstrap-fetch-and-freshness-gate.md's
  Rationale, not duplicated into a separate decisions/ file since the
  proposal already carries it and no public signature/wire format outside
  this issue's own new functions changed.
- [x] No benchmark/investigation numbers produced — no reports/ entry.

## Open findings

None.

## Warrant hunt

This session ran one-shot headless with no later turn available to
consume an async background-hunter result within the same turn (contract
v3 s22); the hunt therefore ran as a direct self-check rather than a
backgrounded warrant-hunter dispatch.

canonical: this session's own re-read of spawn.py:6683-6690 and gates/repo_scope.py, plus the two live test runs pasted in Test evidence above — no blocking finding surfaced

closed_checks:
- check: bootstrap fetch runs before checkout_issue_branch's branch-verification logic
  code_sha: (see code_under_review above)
  canonical: acceptance: `python3 -m pytest tests/test_spawn.py -k test_checkout_issue_branch_records_sha_before_returning -v` — result: pass, this session's own run
- check: freshness phrase absent -> rejected; present -> passes; no-absence-claim not gated
  code_sha: (see code_under_review above)
  canonical: acceptance: `python3 gates/test_repo_scope.py -v` — result: pass, this session's own run, pasted above in full
