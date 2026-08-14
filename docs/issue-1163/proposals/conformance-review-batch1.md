---
status: proposed
files:
  - docs/issue-1163/proposals/conformance-review-batch1.md
  - docs/issue-1163/reports/conformance-review.md
---

# issue-1163 conformance-review (batch 1, engineering-family): requirement list

kind: proposal
subject: issue-1163

Proposal: docs/issue-1163/proposals/conformance-review-batch1.md

## Intent

PR #1167 (`issue-1163/implementation`, merged commit
`461d142436a9e25f1b6d05d505d0c08a7f0dd682`) landed batch 1 of the
36-role quality-bar decomposition (issue #1163): 6 engineering-family
role specs. No conformance-review record exists yet for this commit —
per the marketplace conformance-review role spec's board condition
(issue-521), that is this pass's trigger. This proposal is phase 1: it
extracts the requirement list to check against the merged artifact;
phase 2 (docs/issue-1163/reports/conformance-review.md) renders a
per-requirement verdict, working from the artifact and the spec/
proposal text only, deliberately without re-reading the implementation
role's stated intent beyond what is needed to locate the proposal's
own commitments.

requirement: northpole req#1 (`docs/specs/northpole.md`).

## Constraints

- Verdicts are Present/Surface/Absent/Incorrect/Unverifiable per
  requirement, never a holistic code-quality judgment, never a fix.
- Findings are handed off to the owning role (`implementation`), never
  fixed by editing the target artifact from this session.

## What will be done

Phase 2 checks the merged commit against 8 requirements derived from
the batch-1 proposal
(docs/issue-1163/proposals/batch-1-engineering-family-quality-bars.md)
and the implementation record's operator-amended revision
(docs/issue-1163/reports/implementation.md, "Revision" section):

1. `quality_bar` array of `{criterion, verification_method}` on each
   of the 6 named specs, traced to each spec's own cited source
   standard.
2. Non-automatable criteria carry `human-review-checklist`.
3. `bar-not-met` added to each spec's `loop_state.refusal`.
4. `gates/spec_schema_five_activities_test.py`'s `QUALITY_BAR_ROLES`
   extended with the 6 role names.
5. The 6 rows in `docs/specs/role-invariant-coverage.md` flipped to
   `quality_bar: landed`.
6. No hook/gate file (`gates/quality-bar-gate.sh`,
   `gates/quality_bar.py`, `on-the-record/hooks/quality-bar-gate.sh`)
   touched.
7. Operator revision: `evidence_grade` + `verified_source` on all 24
   criteria, web-verified, graded `validated`/`practitioner-consensus`.
8. Acceptance: `python3 -m pytest gates/ -q -k spec` exits 0.

## Out of scope

Batches 2 and 3 (product/design-family, business/ops-family) — no
implementation commit for either has landed yet as of this review.
Fixing any finding — hand-off only.

## How it will be known to have worked

docs/issue-1163/reports/conformance-review.md carries one verdict per
requirement above, each backed by a `canonical:`-cited command/read
executed this turn against the merged commit or the current tree.

## What did not work

None.
