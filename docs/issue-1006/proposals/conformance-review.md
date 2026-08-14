---
status: proposed
files:
  - docs/issue-1006/reports/conformance-review.md
---

Subject: issue-1006

## Intent

Render a per-requirement conformance verdict (Present|Surface|Absent|
Incorrect|Unverifiable) for the operator-experience layer landed by PR
#1018 (commit fafa01f4, issue-1006/implementation phase-2), against the
requirement list extracted in
docs/issue-1006/reports/conformance-review/survey.md.

## Constraints

- Never a holistic code-quality judgment — per-requirement verdicts only.
- Verdicts rendered from the artifact and the merged spec alone, without
  the building agent's stated intent (implementation.md's own narrative).
- Findings addressed_to the owning role (implementation), never fixed by
  this role editing the target artifact.
- Two-phase flow (role-handoff contract v3 s19): this PR stops after the
  survey + this proposal; the verdict record
  (docs/issue-1006/reports/conformance-review.md) is phase-2 output and
  waits for a human Approve.

## What will be done (phase 2, pending approval)

Write docs/issue-1006/reports/conformance-review.md with one verdict row
per item in the survey's nine-item requirement list, each row's evidence
citing a file:line location or a live re-run of
harness/fixture-operator-experience/test_flow.py and
harness/fixture-operator-experience/scenario.py. Any item found Absent or
Incorrect becomes an open finding addressed_to implementation
(issue-1006/implementation).

## Out of scope

- Fixing any gap found (e.g. building a missing handbook page) — that is
  implementation's work, not this role's.
- Re-litigating the merged design (docs/issue-1006/proposals/operator-experience-layer.md)
  itself.

## How this will be known to work

- Every one of the survey's nine requirement-list items has exactly one
  verdict row in the phase-2 record, each with cited evidence.
- Any Absent/Incorrect verdict carries an open finding entry with a
  resolution path.

## What did not work

None.
