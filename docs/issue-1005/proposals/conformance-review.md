---
status: proposed
files:
  - docs/issue-1005/reports/conformance-review.md
---

# Conformance-review proposal — issue-1005 secure-coding routing-gap fix (phase 1)

## Upstream / basis

canonical: `gh pr view 1086` run this session — output showed
`mergeCommit.oid: fae380c75087e446b8cd8eb1347cc9da2b6161fa`.

Issue #1005. Approved phase-1 proposal:
`docs/issue-1005/proposals/secure-coding-routing-fix.md` (PR #1079).
Delivered implementation: PR #1086, `docs/issue-1005/reports/implementation.md`,
`roles/specs/secure-coding.spec.json`, `gates/test_secure_coding_routing.py`.
Survey: `docs/issue-1005/reports/conformance-review/survey.md`.

## Requirement list (extracted, verdict deferred to phase 2)

1. **R1 — Seeded security-relevant diff surfaces secure-coding as due.**
   Source: issue #1005 Acceptance bullet 1 ("A seeded security-relevant
   change makes secure-coding reachable/suggested by the board
   machinery"). Check: `gates/test_secure_coding_routing.py`'s
   `seeded security-relevant diff -> secure-coding is due` case, run live
   against `roles/specs/secure-coding.spec.json`'s `use_when.trigger`,
   actually asserts and passes.

2. **R2 — Unrelated diff does not surface secure-coding (empty state).**
   Source: issue #1005 Acceptance bullet 3 ("empty state: non-security
   changes do not surface the role"). Check: the same test file's
   `seeded unrelated diff -> secure-coding is not due` case actually
   asserts and passes.

3. **R3 — The named test proves both seed cases, per the acceptance
   check line.** Source: issue #1005 Acceptance bullet 2 verbatim
   ("check: `gates/test_role_utilization_report.py` (or the routing
   gate's own test) proves the seeded case fires and an unrelated change
   does not"). Check: whether `gates/test_secure_coding_routing.py`
   qualifies as "the routing gate's own test" under the acceptance's "or"
   clause, and whether it is wired into a suite an orchestrator actually
   runs (vs. a standalone script nothing invokes).

4. **R4 — Fix is a spec-data change only, no gate-code special-casing.**
   Source: approved phase-1 proposal's Constraints ("the evaluator
   already generalizes over any spec carrying a `use_when.trigger`
   block ... no gate/hook code change is required, only the spec's own
   missing key"). Check: `gates/roles_due.py` was not itself modified to
   special-case `secure-coding`, and its `load_triggered_specs`/
   `_trigger_matches` logic reads `use_when.trigger` generically for any
   role spec.

5. **R5 — Test loads the real on-disk spec, not a synthetic fixture.**
   Source: approved phase-1 proposal's "What will be done" item 2 ("loads
   the real `roles/specs/secure-coding.spec.json` from this working tree
   (not a synthetic spec)"). Check: `gates/test_secure_coding_routing.py`
   reads `roles/specs/secure-coding.spec.json` from disk into its scratch
   repo, rather than constructing an inline trigger dict.

6. **R6 — No regression to the existing `roles_due.py` test suite.**
   Source: approved phase-1 proposal's "What will be done" item 3 ("Run
   the new test and the existing `gates/test_roles_due.py` once"). Check:
   `gates/test_roles_due.py` still passes against the modified
   `secure-coding.spec.json` in the real tree (not just the scratch repo).

7. **R7 — Provenance: routing-gap basis traces to #993 phase-1.** Source:
   issue #1005 Acceptance's provenance line ("read — #993 phase-1
   proposal (merged #1004)"). Check: `docs/issue-1005/reports/implementation.md`'s
   `Why` section cites `docs/issue-993/proposals/product-discovery.md`
   (merged #1004) as the originating audit, not an unsourced claim.

## Out of scope (phase 2 will not re-litigate)

- Release-engineering's routing gap — issue #1005's own scope excludes it
  (approved phase-1 proposal's Out of scope section); not a conformance
  gap for this issue.
- `gates/roles_due.py`'s output being surfaced-only (not wired into an
  enforcement gate) — explicitly out of scope per the approved proposal,
  not a defect to flag here.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `roles/specs/secure-coding.spec.json`,
`gates/test_secure_coding_routing.py`, `gates/roles_due.py`, and issue
#1005's own text — `docs/issue-1005/reports/implementation.md`'s prose
(`Why`, `What did not work`) is read only to locate provenance sources, not
as evidence for a verdict. Both named tests are re-run live in phase 2
rather than trusting the builder's pasted output.

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

None at phase 1.

## Next steps

Await approval (`APPROVE issue-1005/conformance-review` per contract v3
s19, single-account mode). On approval: render the phase-2 per-requirement
verdicts (R1-R7 above) in `docs/issue-1005/reports/conformance-review.md`,
using `review-traceability:finding-record` to write one verdict row per
requirement.

## Resolution path

Phase 2 resolves R3 and R4 by direct code read of `gates/roles_due.py`
(confirming generic `use_when.trigger` handling and whether
`test_secure_coding_routing.py` is wired into any invoked suite) before
assigning verdicts.
