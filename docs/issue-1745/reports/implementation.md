---
code_under_review:
  - tests/test_gh_quota_guard.py
  - tests/test_spawn.py
loop_state: scope-undeclared
type: fix
breaking: false
verdict: fail
---

# Implementation record: issue-1745

## What was done

Executed the approved proposal
(docs/issue-1745/proposals/fast-tier-red-baseline-repair.md, approved via
`APPROVE issue-1745/implementation` on the issue by JiwonJung94):

1. In `tests/test_gh_quota_guard.py`'s `_fake_run_factory`, added a `gh
   repo view` stub (returns a fake `owner/repo` slug) and a `gh api
   .../pulls` stub (returns `"[]"`), so `_repo_slug()` resolves and
   `_pr_index_all()` reaches its bulk REST path instead of
   short-circuiting to `(None, False)`.
2. In `tests/test_spawn.py`'s `PollHeartbeatMarkerRelocationTest` class,
   method `test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`,
   applied the same two additions to its local `fake_run` closure. The
   class had not been relocated by issue #1959's split as of this
   session — canonical: `grep -n PollHeartbeatMarkerRelocationTest tests/test_spawn.py`
   (this session, live run) still shows it at line 4569 — so no path
   deviation applied.
3. (Beyond the proposal's literal step list — see Rationale for
   deviations below) added a third stub branch in both files for `gh
   api repos/{slug}/issues ... -i` (the REST issues-index endpoint used
   by `closure_sweep.issue_state_index_all()` and by the issue #1688
   delta probe), returning a synthetic 200-response with a JSON issue
   list. Without it, `issue_state_index_all()` still failed (`ok=False`)
   even after fix 1-2, which was masked in the original proposal's
   count because the repo-slug gap made `_pr_index_all()` fail first
   and short-circuit before this second bulk call was ever reached.

canonical: `python3 -m pytest -q tests/test_spawn.py -k PollHeartbeatMarkerRelocationTest` (this session, live run)
Result: 6 passed, 1 xfailed, 1 xpassed.

canonical: `python3 -m pytest -q -m "not slow"` (this session, live run)
Result: 2429 passed, 1 failed (test_sweep_call_budget in
tests/test_gh_quota_guard.py), 18 xfailed, 3 xpassed. The issue's stated
acceptance check (`python3 -m pytest -q -m "not slow"` exits 0) is not
yet met.

## Why

Issue #1745 asks for a green fast tier; the approved proposal traced
both original failures to the same test-fixture gap (stubs answering
`gh repo view` with an empty catch-all, so `_repo_slug()` cached `None`
and both call sites fell back to their O(N) per-subject paths instead
of exercising the bulk index). Fixing the fixtures to resolve a slug
and answer the bulk REST endpoints was scoped as a pure test-only fix,
with production-code batching explicitly rejected as an alternative
(see the proposal's Rationale — the bulk path already exists,
issue #1702).

## Upstream basis

docs/issue-1745/proposals/fast-tier-red-baseline-repair.md (this
branch, commit a7223b1057cdc782343ada8335714f62c21a93a3).

## What did not work

Fixing the repo-slug + pulls-index stub gap alone did not fully repair
the PollHeartbeatMarkerRelocationTest call-count-constant test: once
`_pr_index_all()` started resolving, the sweep's issue-index call
(`closure_sweep.issue_state_index_all()`) still failed for the same
underlying reason (its own bulk REST shape, `gh api .../issues -i`, was
unstubbed), which the original proposal's two-branch plan did not
anticipate because the repo-slug failure alone was already enough to
explain the pre-fix symptom. A third stub branch (see item 3 above)
turned out to be necessary.

canonical: `python3 -m pytest -q tests/test_spawn.py -k PollHeartbeatMarkerRelocationTest` (this session, live run)
Result after adding the third branch: 6 passed, 1 xfailed, 1 xpassed.

Separately, test_sweep_call_budget in tests/test_gh_quota_guard.py
remains red even with all three stub branches correctly wired: a
correctly-stubbed cold-start sweep now issues 10 gh calls (`gh api
rate_limit` x2, `gh repo view` x1, the issue #1688 delta-probe's issues
call x1, `closure_sweep.issue_state_index_all()`'s own issues call x1,
`closure_sweep._pr_index_all()` x2, `git ls-files` x2 from
spawn-coverage, `gh issue list` x1) against the test's asserted ceiling
of 8.

canonical: `python3 -m pytest -q tests/test_gh_quota_guard.py::test_sweep_call_budget -s` (this session, live run; full 10-entry call list shown in the assertion failure output)
Result: 1 failed, assertion `10 <= 8` is false.

This is logged as a filed deviation
(docs/issue-1745/reports/implementation/deviation-log.md) rather than
resolved in this session: resolving it requires a production-behavior
judgment (whether 10 calls is the correct new ceiling for the sweep's
three gh-calling signals plus the #1688 delta probe, or whether the
duplicate rate_limit/pulls-index calls are themselves a fixable
inefficiency) that is outside this issue's frozen write set and outside
the approved proposal's scope, which explicitly ruled out
production-code changes.

## Rationale for deviations

The approved proposal's build-steps section specified exactly two stub
additions per file (`gh repo view`, `gh api .../pulls`). This session
added a third (`gh api .../issues -i`) in both files, and discovered
test_sweep_call_budget fails even with all three, for a reason the
proposal's Rationale did not name as a possibility (a second
independent call-multiplicity issue, not a fixture-stub gap).

canonical: `python3 -m pytest -q tests/test_spawn.py -k PollHeartbeatMarkerRelocationTest` (this session, live run)
The PollHeartbeatMarkerRelocationTest fix (6 passed, 1 xfailed, 1
xpassed) was completed by extending the same INLINE-FIX pattern the
proposal already committed to (same file, same kind of stub branch, no
design judgment). The test_sweep_call_budget gap was not — see Open
findings.

## Open findings

- test_sweep_call_budget in tests/test_gh_quota_guard.py fails: 10 gh
  calls for a correctly-stubbed cold-start 400-subject sweep vs. an
  asserted ceiling of 8. Filed as a deviation rather than resolved in
  this session (docs/issue-1745/reports/implementation/deviation-log.md).

## Next steps

A follow-up decision is needed on test_sweep_call_budget: either the
ceiling should be raised to reflect the sweep's current (still bulk,
still O(1)-in-subject-count) three-signal-plus-delta-probe call cost, or
the duplicate rate_limit/pulls-index calls should be treated as a
production inefficiency and addressed separately. Either path needs a
new phase-1 proposal (production-code changes are out of this issue's
approved scope) before it can land.

## Resolution path

File a new issue (or amend this one) scoped to test_sweep_call_budget's
call-budget mismatch, with a phase-1 survey covering
`_board_wide_sweep`'s three gh-calling signals and the issue #1688
delta probe's call cost, before any fix (test-ceiling or production)
lands.
