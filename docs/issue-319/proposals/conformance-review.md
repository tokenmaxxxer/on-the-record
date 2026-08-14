# Conformance-review proposal — issue-319 risk-classified approval report (phase 1)

## Upstream / basis

canonical: `docs/issue-319/proposals/2026-08-07-risk-classified-approval-report.md`,
read this session — approved proposal for issue #319. Delivered by PR
#345 (`issue-319/implementation`, merged `05f266c0`),
`docs/issue-319/reports/implementation.md`. Later touched by issue
#511's PR #513 (`gates/risk_report.py`, `gates/test_risk_report.py`
relocated and extended). Survey:
`docs/issue-319/reports/conformance-review/survey.md`.

## Requirement list (extracted, verdict deferred to phase 2)

Requirements below are the review's fixed unit — phase 2 renders one
Present/Surface/Absent/Incorrect/Unverifiable verdict per row, from the
artifact and spec only. Full sourcing and supporting evidence for each
row is in the survey above; reproduced here in summary form.

1. **R1 — protected-path classification always high, regardless of
   size.**
2. **R2 — fail-closed classification on a missing/unparseable
   write-set.**
3. **R3 — blank-line-inside-`files:`-block regression guard.**
4. **R4 — `report()` batches, orders `high` before `low`, drops no
   input proposal.**
5. **R5 — the acceptance section's named test command still resolves
   and its behavior is present.**
6. **R6 — `gates.py` is imported, never written to, by
   `risk_report.py`.**
7. **R7 — the report stays advisory-only, wired into no blocking gate,
   workflow, or hook.**
8. **R8 — the handbook states the advisory-only disclaimer in its own
   text.**

## Out of scope (phase 2 will not re-litigate)

- Issue #511's own four-axis additions to the same module — reviewed
  under issue #511's own acceptance, not issue #319's; referenced only
  as supporting evidence for R7.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only, never a holistic
  quality read.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `gates/risk_report.py`,
`gates/test_risk_report.py`, `docs/handbooks/risk-classified-approvals.md`,
and the two spec documents (the approved 2026-08-07 proposal, issue
#319's own body) — the implementation record's own prose is consulted
only to locate what to check, never substituted for reading the
artifact directly, consistent with this role's artifact-only rulebook.

## What did not work

None yet — phase 1, no verdicts attempted.

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

None at phase 1. The phase-1 survey already found R5's evidence
suggestive of a non-Present-shaped verdict (the named command path no
longer resolves, though its behavior does under a new path) — left for
phase 2 to render, not pre-decided here.

## Next steps

Await approval (`APPROVE issue-319/conformance-review` per contract v3
s19, single-account mode). On approval: render the phase-2
per-requirement verdicts (R1-R8 above) in this role's own phase-2
record under this issue's reports directory, using
`review-traceability:finding-record` to write one verdict row per
requirement, and `review-severity:severity-classification` only if a
finding's risk needs explicit weighting.

## Resolution path

Phase 2 resolves each requirement by direct artifact read and the
derived commands the survey already reproduced, re-run rather than
reused, before assigning verdicts.
