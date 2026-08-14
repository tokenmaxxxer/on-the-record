# Current-state survey — issue-1124 conformance-review (phase 1)

## Target artifact and spec

canonical: `git show --stat b62e57dc` (read this session)
Commit b62e57dc touches `spawn.py` and
`gates/test_clean_reconcile_safety.py`.

canonical: `git log --all --oneline | grep 1124` (read this session)
That commit merged to main via PR #1146.

canonical: `docs/issue-1124/reports/implementation.md` (read this session)
Implementation record confirms the same commit and write set.

- Target: `spawn.py` (`LANDED_OUTCOMES`, `_ledger_log_outcomes`,
  `roster_clean`, the `_roster_reconcile_unreported` existence check),
  `gates/test_clean_reconcile_safety.py`'s `CleanReconcileSafetyTest`
  class.
- Spec: issue #1124's own body — Requirements + Acceptance sections
  (canonical: `gh issue view 1124`, read this session) — and the
  approved proposal `docs/issue-1124/proposals/clean-reconcile-safety.md`
  (canonical: that file, read this session).

## Note on the invoking framing vs. the issue's own text

canonical: `gh issue view 1124` (read this session)
The task that opened this session states "이 이슈가 인용하는 요구:
R001." Issue #1124's body itself ends with the line
`infrastructure/no-direct-requirement — session lifecycle tooling; R001
is not this issue's target.` (verbatim last line of the body).

The issue's own text overrides the invocation framing for scope
purposes: this review checks the issue's stated Requirements/
Acceptance sections, not an R001 traceability line the issue explicitly
disclaims. Carried forward as an open finding, not resolved silently.

## What exists to check against

canonical: `gh issue view 1124` (read this session)
Issue #1124 states three Requirements bullets and one Acceptance block
with three `check:` items.

canonical: `git show b62e57dc -- spawn.py` (read this session)
Code regions matching those Requirements/Acceptance items:

| Issue requirement | Code region |
|---|---|
| reconcile tolerates missing workspace, skip-not-crash | `_roster_reconcile_unreported`, `spawn.py` (existence check added right after reading `work`) |
| clean must not delete a non-landed session's log; archive/preserve it | `LANDED_OUTCOMES`, `_ledger_log_outcomes`, `roster_clean` sibling-file loop, `spawn.py` |
| workspace deletion may stay as-is | `roster_clean`'s workspace `shutil.rmtree` path — unchanged from prior `clean` behavior per the diff |
| regression test covers both | `gates/test_clean_reconcile_safety.py`, class `CleanReconcileSafetyTest` |
| acceptance items (a)-(d) | four test methods in the same class (see test file) |

## Thin/unknown/contested surfaces (what this review must check directly)

canonical: `git show b62e57dc -- spawn.py` (read this session)
`LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}` is the
added constant. The proposal states this is the outcome set where
`fail_closed_downgrade` confirms a commit reached origin.

canonical: same read as above
Phase 2 must directly read `classify()`'s full outcome vocabulary
(`spawn.py`, function `classify`) to verify the set's completeness,
rather than trusting the proposal's citation unverified.

canonical: `git show b62e57dc -- spawn.py` (read this session)
`roster_clean`'s sibling loop keys on `log_outcomes.get(str(sibling))`
— the ledger's `entry.get("log")` string must equal the glob-produced
sibling path string exactly for the match to fire.

canonical: same read as above
Phase 2 must directly confirm this path-equality holds for
ledger-written paths vs. glob-produced sibling paths, not assume it
from the proposal text.

canonical: `docs/issue-1124/proposals/clean-reconcile-safety.md` (read this session)
The proposal's "Out of scope" section states: no retroactive archiving
of logs deleted before this fix; siblings absent from the ledger keep
the prior unconditional-delete behavior.

canonical: same read as above
Phase 2 verifies the delivered code against this stated scope line
directly.

canonical: `gh issue view 1124` (read this session)
Requirements bullet 1 requires reconcile to keep reporting every other
reachable entry past a skipped missing-workspace one.

canonical: `git show b62e57dc -- spawn.py` (read this session)
Phase 2 must directly read the loop structure around the new
`continue` in `_roster_reconcile_unreported`, not just the added lines
in isolation, to verify the loop reaches subsequent entries.

## Sampling derivation

canonical: `gh issue view 1124` (read this session)
Full-population check, not a sample: three issue-body Requirements
bullets plus four issue-body Acceptance check items form the checkable
requirement-row set, small enough to check exhaustively against the
diff and test file rather than sample.

## Scout: skipped

canonical: `git log --all --oneline | grep 1124` (read this session)
The PR #1146 merge commit precedes this review session.

canonical: same read as above
Skip condition: issue #1124's spec (Requirements + Acceptance) leaves
no design decision open for this review to make — conformance-review
checks an artifact that is already built and already merged, against
an already-fixed spec. Per scout-directive's two skip conditions, this
is the second (spec leaves no open design decision); this role's
review method (Present/Surface/Absent/Incorrect/Unverifiable per
requirement) is fixed by the role's own directive, not a choice this
session makes.
