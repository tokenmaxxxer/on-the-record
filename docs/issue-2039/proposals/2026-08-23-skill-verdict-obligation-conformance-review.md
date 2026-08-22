---
status: proposed
files:
  - docs/issue-2039/reports/conformance-review.md
---

## Request

Issue #2039's spawn context (spawn_on_pr.py auto-spawn on PR merge)
asks for a conformance review of the landed per-mounted-skill verdict
obligation feature (PR #2042 phase-1, PR #2049 phase-2): decompose its
Acceptance block into checked requirements (R1-R6, see
docs/issue-2039/reports/conformance-review/survey.md), assign each a
verdict with evidence, and record the result.

## Constraints

- Write set frozen to `docs/issue-2039/reports/conformance-review.md`
  only — this review does not touch the implementation's own code or
  tests (that write set belongs to the implementation role, already
  landed and merged).
- Verdicts must cite live, re-derived evidence (test runs, file:line
  reads performed this session), not a restatement of the
  implementation record's own self-reported pass claims.
- Shape-only enforcement boundary (the feature's own design constraint,
  confirmed in the survey) stays out of scope to re-litigate — this
  review checks whether that boundary was actually built as specified,
  not whether the boundary itself was the right call.

## Rationale

Two candidate approaches for this review's depth were considered:

1. **Chosen: requirement-by-requirement verdict record** — decompose
   the Acceptance block into R1-R6 (done in the survey), assign each a
   Present/Surface/Absent/Incorrect/Unverifiable verdict with its own
   re-derived evidence citation, using inspection (code read) and
   demonstration (live pytest run) as verification methods.
2. **Rejected: trust the implementation record's self-reported PASS
   claims and only spot-check the hook registration/spec rows** — this
   would be faster, but a conformance review whose evidence is "the
   implementation record says so" adds no independent signal over the
   implementation record itself; the role's whole purpose (issue #1955)
   is to be a second, independent pass. Rejected because it collapses
   the review into a rubber stamp.

Full enumeration (not sampling) was chosen over a sampling-derivation
approach because the write set is small — the survey's "Sampling scope"
note found `code_under_review:` in
docs/issue-2039/reports/implementation.md lists few enough files that
checking all of them costs no more than deriving and justifying a
sample would.

## What will be done

1. For each of R1-R6, assign a verdict (Present/Surface/Absent/
   Incorrect/Unverifiable) with its evidence citation, re-running the
   relevant test(s) live where a demonstration method applies (already
   partially done in the survey; the review record restates it as
   verdicts, not narrative).
2. Check the supporting infrastructure items already surveyed (hook
   registration, spec rows, spec-index consistency, handbook, tracked
   mirror parity) and fold each into either its nearest requirement or
   a short infrastructure-conformance note.
3. Record any Surface/Absent/Incorrect/Unverifiable finding as an open
   finding with severity, per this role's severity-classification and
   finding-record skills.
4. Write docs/issue-2039/reports/conformance-review.md with the
   required frontmatter (subject, loop_state, kind, etc. per contract
   v3 s20) and skill-verdict lines for this session's mounted skills.

## Out of scope

- Modifying or re-implementing any part of the landed skill-verdict
  feature itself (spawn.py, gates/record_lint.py,
  on-the-record/hooks/skill-verdict-guard.sh, tests) — those are
  implementation-role write surfaces, already merged.
- Re-opening whether the shape-only enforcement boundary was the
  correct design choice — that was PR #2042's phase-1 decision, out of
  this review's mandate.
- Reviewing any other issue's landed work — this review's scope is
  exactly issue #2039.

## How you'll know it worked

docs/issue-2039/reports/conformance-review.md exists, carries a verdict
line for each of R1-R6 with a re-derived evidence citation (not a copy
of the implementation record's own claims), states any open findings
with severity, and passes record-claim-guard.sh and
record-shape-gate.sh at commit time.
