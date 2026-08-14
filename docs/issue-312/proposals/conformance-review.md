# Conformance-review proposal — issue-312 closes-gate phase/refusal fix (phase 1)

Subject: issue-312

## Upstream / basis

canonical: `gh issue view 312` (issue body, Scope/Acceptance sections).
Issue #312, closed via PR #314. Proposal:
`docs/issue-312/proposals/2026-08-07-closes-gate-issue-level-phase-and-evidence-bearing-refusal.md`.
Decision: `docs/issue-312/decisions/phase-is-an-issue-property.md`. Delivered
implementation: PR #314, commit `3e3038690098a9efb686c47b6fb9cfb37de2ccb8`,
`gates/ci.py`, `gates/test_closes_gate_ci.py`.

## Requirement list (extracted, verdict deferred to phase 2)

canonical: issue #312 body, `## Scope` and `## Acceptance` sections
(`gh issue view 312`).

1. **R1 — Phase is encoded as a property of the issue, not of the
   (issue, role) pair; cross-role handoff is representable.** Source:
   Scope item 1. Check: `gates/ci.py::_phase_from_approval` derives phase
   from `_approved_roles_on_issue` (any `APPROVE issue-<n>/<role>` on the
   issue, any role) rather than requiring the delivering PR's own branch
   role to match.

2. **R2 — Every closes-gate refusal reports the evidence it judged on
   (role searched for, approvals actually present), not only the
   inferred verdict.** Source: Scope item 2. Check: the phase-1-mismatch
   refusal path in `gates/ci.py::check()` appends a line naming the
   searched role and the issue's actual approved-role set, not just the
   "closing keyword present" conclusion.

3. **R3 — A test reproduces the exact #304 configuration (issue with
   `APPROVE issue-<n>/<roleA>`, phase-2 PR on branch `issue-<n>/<roleB>`
   carrying `Closes #<n>`) and asserts the gate does not report a
   phase-1 closing-keyword violation.** Source: Acceptance bullet 1.
   Check: a test in `gates/test_closes_gate_ci.py` stubs this exact
   shape and asserts no phase-1-mismatch finding.

4. **R4 — A test asserts the refusal text for a missing approval names
   the role searched for and the approvals actually present on the
   issue.** Source: Acceptance bullet 2. Check: a test in
   `gates/test_closes_gate_ci.py` stubs an unapproved-role case and
   asserts the refusal string contains both the searched role and the
   issue's actual approval set (or "없음" if none).

5. **R5 — Re-running `closes-gate` on PR #307 unchanged shows it passing
   (or failing with an accurate, non-phase-misdiagnosis message).**
   Source: Acceptance bullet 3. Check: live invocation of
   `python3 gates/ci.py . --pr 307 --issue 304 --autodetect --closes-only`
   against real GitHub state.

## Out of scope (phase 2 will not re-litigate)

- The #313/#317 pure-bugfix-skip phase-determination gap — canonical:
  issue #312's second comment (`gh issue view 312 --comments`), which
  states this was raised as a follow-on and is explicitly not folded
  into PR #314's approved write set.
- Code-quality judgment (naming, structure, efficiency) — this role
  renders per-requirement fidelity verdicts only, never a holistic
  quality read.

## Method (phase 2, once approved)

Artifact-only review: phase 2 works from `gates/ci.py`,
`gates/test_closes_gate_ci.py`, and issue #312's body/decision record
only. R5 requires a live `gh`/`python3 gates/ci.py` invocation as
evidence, not a code read alone.

## What did not work

None.

## loop_state

kind: proposal
loop_state: scope-proposed

## Open findings

None at phase 1.

## Next steps

Await approval (`APPROVE issue-312/conformance-review` per contract v3
s19). On approval: render phase-2 per-requirement verdicts in
`docs/issue-312/reports/conformance-review.md`.

## Resolution path

N/A — phase 1, no verdicts rendered yet.
