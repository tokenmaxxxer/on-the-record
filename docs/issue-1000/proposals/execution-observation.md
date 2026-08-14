---
kind: proposal
loop_state: proposed
---

# Proposal — issue #1000 (execution-observation)

## Verdict levels to be checked, and against what evidence

This is a phase-1 proposal; no verdict is rendered here. Phase 2 will
render all three of the role's mandated verdict levels:

- **outcome** — whether PR #1075 (subject issue-1000, merge commit
  `3269ae63b9e403df07503edca0f2f0692dbcc8f4`) satisfies issue #1000's
  acceptance criteria, recomputed as the worst case across cited
  step-level results, per `roles/specs/execution-observation.spec.json`'s
  recomputation rule (line 21). Primary evidence: a live re-run of
  `python3 gates/role_spec_shape.py roles/specs/capacity-planning.spec.json`
  against current `main` (already confirmed `exit=0` in the phase-1
  survey), cross-checked against the diff hunk in commit
  `3269ae63b9e403df07503edca0f2f0692dbcc8f4`.
- **trajectory** — whether the phase-1 (PR #1073) → phase-2 (PR #1075)
  path followed contract v3 s19: scouted where required (the phase-1
  proposal itself states no open design decision — a stated skip
  condition, not a silent omission), surveyed before proposing (PR
  #1073's own commit history and body), and obtained real human
  approval (the `APPROVE issue-1000/implementation` issue comment,
  checked for exact-string match, listed-account membership, and
  single- vs. two-account mode).
- **step** — which specific artifact, if any, is deficient among
  `roles/specs/capacity-planning.spec.json`'s new
  `axis_evaluation`/`reference_resolution`/`gate_c_axis_evaluation`
  fields and `docs/issue-1000/reports/implementation.md`'s acceptance
  claims — checked by re-executing the cited gate command directly
  (not re-reading the observed role's pasted output as proof) and, for
  the "verbatim-mirrored" claim, a direct diff against the four sibling
  spec files it claims to mirror.

## Skip record (scout-directive)

Scouting is skipped. Reason: this is not product-shaped work with a
competitive field to survey — the check is prescribed mechanically by
the spec's own recomputation rule and by the issue's acceptance
criteria, leaving no open design decision for an external sweep to
inform.

## What will be done (phase 2, on approval)

1. Re-run `python3 gates/role_spec_shape.py
   roles/specs/capacity-planning.spec.json` and `python3
   gates/role_spec_shape.py --roles-dir roles` live against current
   `main`, pasting fenced output (mode: command), to independently
   confirm rather than trust the observed role's own pasted `exit=0`
   claims.
2. Diff `roles/specs/capacity-planning.spec.json`'s new
   `reference_resolution.rule` clause against the equivalent clause in
   `roles/specs/architecture.spec.json`,
   `roles/specs/security-threat-model.spec.json`,
   `roles/specs/conformance-review.spec.json`, and
   `roles/specs/performance-engineering.spec.json`, to check the
   observed role's "verbatim-mirrored" claim directly rather than
   accept it as asserted.
3. Re-check the disclosed open finding (the `_VERIFICATION_FAMILY_ROLES`
   allowlist gap in
   `on-the-record/hooks/role-spec-reference-guard.sh`) by reading that
   file directly, to confirm the claim rather than carry it forward as
   asserted-only.
4. Render outcome, trajectory, and step-level verdicts in
   `docs/issue-1000/reports/execution-observation.md`, with the
   independence statement preceding any verdict language, each
   verdict-bearing sentence citing its source, and each step-level
   claim's evidence mode (read/command/asserted) stated inline.
5. If the allowlist re-check or the mirror-clause diff surfaces a real
   deficiency beyond what the observed role already disclosed, record
   it as a step-level finding (impact/timeline/root cause/action item)
   in this role's own record — never edited into
   `roles/specs/capacity-planning.spec.json` or the observed role's
   record, and never filed as a new GitHub issue.

## Out of scope

- Re-implementing or editing any part of
  `roles/specs/capacity-planning.spec.json` or
  `docs/issue-1000/reports/implementation.md`.
- Re-running the observed role's own test suite as this role's
  evidence (its own pasted output is cited, but independently
  re-executed, not treated as this role's verification by itself).
- Any change to `roles/specs/`, `gates/`, or `on-the-record/hooks/`.
- Filing a new GitHub issue — any deficiency found returns as a finding
  in this role's own record; the human files an issue if they judge it
  warranted.
