---
status: proposed
files:
  - docs/handbooks/architecture-methodology.md
  - roles/specs/conformance-review.spec.json
  - roles/specs/capacity-planning.spec.json
  - roles/specs/performance-engineering.spec.json
  - roles/specs/requirements-engineering.spec.json
  - roles/specs/risk-management.spec.json
  - docs/issue-992/reports/implementation/fixtures/*.md
  - docs/issue-992/reports/implementation.md
---

## Request

#992 (implementation, phase 1): build proposal for Phase A of the
approved deepening plan (`docs/issue-992/proposals/2026-08-12-role-expertise-deepening-program.md`,
merged #996, approved via `APPROVE issue-992/product-discovery`). Phase
A covers cluster A (the 3 unfilled axis owners — `conformance-review`,
`capacity-planning`, `performance-engineering`) and cluster B
(`requirements-engineering`, `risk-management`), per #996 §4. This PR
carries only the survey and this proposal; the edits themselves land
under `implementation`'s own two-phase gate once
`APPROVE issue-992/implementation` is posted (contract v3 s19 — no
`CORE_BUILD_NOW` env var was set for this session, so the default
two-phase flow applies to this role's own PR the same way it applied to
product-discovery's).

## Constraints

- Rulebook prose repos remain unreadable this session (survey.md); the
  only in-repo write surfaces for Phase A are the handbook's
  `axis_evaluation` sections and additive `roles/specs/*.spec.json`
  fields — no rulebook-repo edit is proposed.
- `axis_evaluation` sections must follow
  `docs/handbooks/architecture-methodology.md`'s own template exactly
  (READ/EXECUTE/CRITERIA/CITATION, machine-checked shape via
  `gates/role_spec_shape.py::check_axis_evaluation_entry`) — reuse the
  template, do not invent a new shape.
- New `roles/specs/*.spec.json` fields (`finding_method`, `anti_pattern`)
  must not break `gates/role_spec_shape.py` (guardrail metric per #996
  §5) — additive only, verified by re-running the gate post-edit.
- Every methodology/citation named must be a real, checkable source
  (issue's own constraint, restated in #996 §1).

## Rationale

Considered doing the Phase A edits directly in this same session/PR
(treating the merged #996 approval as sufficient authorization for the
downstream implementation role too), since #996 §4 already names Phase A
concretely and this session's invocation asked for direct execution.
Rejected: the interaction protocol's approval gate is per-role
(`APPROVE issue-<n>/<role>`), not transitive across roles on the same
issue — `product-discovery`'s approval authorized *its own* PR (#996,
the proposal), not a different role's phase-2 build. Skipping straight
to edits here would mean this role's PR lands code with no
role-scoped human approval recorded for it, which is exactly the
failure mode the two-phase gate exists to prevent. The safer, protocol-
compliant path is: this PR carries phase 1 (survey + this proposal,
scoped tightly to #996's already-approved Phase A so the human's next
approval is a short confirmation, not a fresh design review), and
`implementation`'s phase 2 opens on its own `APPROVE issue-992/implementation`.

## What will be done (on approval)

1. Add 3 `axis_evaluation` sections to `docs/handbooks/architecture-methodology.md`
   (`alignment`, `external_burden`, `performance`), each filled with a
   real READ/EXECUTE/CRITERIA/CITATION per the existing template, citing
   each role's own `source_standard` (EARL 1.0 for conformance-review;
   ITIL Capacity Management for capacity-planning; Google SRE SLO/
   error-budget for performance-engineering — all already present in the
   respective spec.json files, no new citation is fabricated).
2. Add `finding_method` (senior-practitioner checklist) and
   `anti_pattern` (named failure catalog, >=3 entries) fields to
   `roles/specs/requirements-engineering.spec.json` and
   `roles/specs/risk-management.spec.json`, grounded in EARS/29148 and
   NIST SP 800-161r1 respectively.
3. Write >=2 live-fire seed-task fixtures per Phase-A role (10 total,
   per #996 §5) under `docs/issue-992/reports/implementation/fixtures/`,
   each constructed so a practitioner applying the named methodology
   reaches a different verdict than generic reasoning.
4. Run `python3 gates/role_spec_shape.py --roles-dir roles` post-edit as
   the guardrail-metric check (must stay exit 0, matching survey.md's
   pre-edit baseline).
5. Record `docs/issue-992/reports/implementation.md` per contract v3
   s19/s20, including the live-fire divergence results per #996 §5's
   decision rule.

## Out of scope

- Cluster C/D/E/F roles (Phases B-D per #996 §4) — separate future PRs,
  gated behind Phase A's live-fire result per #996 §5's ITWWS follow-up.
- Building signal #8's independent-grading-agent code (#996 explicitly
  scopes this out; live-fire grading for this phase uses the lighter
  mechanism this proposal's `## What will be done` step 3 constructs
  inline, not a standing agent).
- Any rulebook-repo edit (inaccessible this session).

## How you'll know it worked

- `python3 gates/role_spec_shape.py --roles-dir roles` exits 0 after the
  edits (guardrail).
- All 5 Phase-A `roles/specs/*.spec.json`/handbook entries carry real,
  resolvable citations (no fabricated source).
- At least 1 of the 10 seed-task fixtures shows verdict divergence
  matching the methodology-correct answer, per #996 §5's threshold.
- `docs/issue-992/reports/implementation.md` records the outcome with
  `loop_state: landed` (or an honest non-terminal state with next steps,
  if the live-fire threshold is not met).

## What did not work

None.
