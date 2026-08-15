---
status: proposed
files:
  - roles/specs/content-design.spec.json
  - roles/specs/brand-design.spec.json
  - roles/specs/technical-writing.spec.json
  - roles/specs/pr-communications.spec.json
  - roles/specs/devrel.spec.json
  - roles/specs/localization.spec.json
  - roles/specs/knowledge-management.spec.json
  - roles/specs/user-discovery.spec.json
  - gates/spec_schema_five_activities_test.py
---

## Request

Issue #1638 asks for "batch 2" of the phase-wise `quality_bar`
decomposition started in #1156 and continued in #1163: pick the next
coherent family of 6-8 roles from the 30 still domain-named-only, write
each a per-criterion `quality_bar` decomposed from its spec's own
`source_standard` (per the §0 principles in
docs/issue-1156/proposals/per-role-quality-bars.md), add `bar-not-met`
to each role's refusal states, add the roles to
`QUALITY_BAR_ROLES` in gates/spec_schema_five_activities_test.py, and
keep `test_no_other_spec_carries_a_quality_bar_yet` green for the
remaining roles.

## Constraints

- No re-litigation of §0 principles: top-of-industry bar, decomposed
  adjectives, non-automatable criteria become named
  human-review-checklist items (never a lowered bar), no self-grading,
  bounded rejection via the existing `bar-not-met` mechanism.
- Each criterion's source must trace to the role's own already-cited
  `source_standard` (or a `verified_source` citation that corrects/
  strengthens it, matching batch-1 precedent).
- The remaining 22 non-batch roles must stay byte-identical (asserted
  by the existing boundary test).
- No new gate/hook logic — `quality-bar-gate.sh` and
  `gates/quality_bar.py` already exist from #1156/#1163; this batch only
  adds spec content and extends the test list.

## Rationale

Two groupings were viable for "next coherent family": (a) the
quality/review family (defect-verification, conformance-review,
execution-observation, incident-response, issue-retrospective,
security-threat-model, technical-feasibility) — these share a
QA/verification-record shape; (b) the content/design/communication
family (content-design, brand-design, technical-writing,
pr-communications, devrel, localization, knowledge-management,
user-discovery) — these share a "produce/measure human-facing
communication artifacts" shape and a heavier reliance on
human-review-checklist criteria (content voice, positioning,
translation nuance) rather than machine-checkable schema criteria.

Chose (b), the content/design/communication family, over (a), the
quality/review family: (a)'s roles skew toward roles the on-the-record
verification pipeline itself already exercises heavily
(conformance-review, execution-observation both cite EARL 1.0, and
incident-response/issue-retrospective share the SRE-postmortem lineage)
— decomposing them well requires cross-referencing how
`gates/quality_bar.py`'s existing anti-circularity design interacts
with roles that themselves produce verification records, which is a
larger design surface than a phase-wise batch should absorb without a
dedicated proposal. (b) has no such entanglement: each of its 8 roles'
`source_standard` is a self-contained external standard (GOV.UK content
design, DTCG tokens, Diataxis, AMEC/Barcelona Principles, Keystone
DevRel metrics, Unicode CLDR, KCS Solve loop, Torres/Guest-Bunce-Johnson
interview saturation) that can be decomposed independently per role,
matching how batch 1 (the engineering family) was scoped.

## What will be done

For each of the 8 roles, add a `quality_bar` array of 4-5 criteria
decomposed from that role's `source_standard`, each with `criterion`,
`verification_method`, `evidence_grade`, and a URL-cited
`verified_source`; automatable criteria get an `automated check that
...` verification_method, non-automatable ones get a
`human-review-checklist: ...` verification_method with the checklist
question stated. Every role's array ends with the same
`human_comprehensibility_verdict` entry already shared by all 13 landed
roles. Each role's `loop_state.refusal` gains `"bar-not-met"` appended
to its existing list. `QUALITY_BAR_ROLES` in
gates/spec_schema_five_activities_test.py gets the 8 role names
appended (alphabetized within a new "issue #1638 batch 2
(content/design/communication family)" comment block, matching the
existing batch-1 comment pattern).

## Out of scope

- The quality/review family (defect-verification, conformance-review,
  execution-observation, incident-response, issue-retrospective,
  security-threat-model, technical-feasibility) and the remaining
  roles named in §7 — deferred to a later phase-wise batch.
- Any change to `gates/quality_bar.py`, `quality-bar-gate.sh`, or the
  anti-circularity/escalation mechanism — those already exist and are
  reused as-is.
- Re-scoring or revising the 13 already-landed roles' `quality_bar`
  arrays.

## How you'll know it worked

- `python3 -m pytest gates/spec_schema_five_activities_test.py -q`
  exits 0: the 8 new roles pass
  `test_every_quality_bar_role_has_nonempty_quality_bar_array` and
  `test_every_quality_bar_role_has_bar_not_met_refusal_state`, and
  `test_no_other_spec_carries_a_quality_bar_yet` still passes for all
  35 non-batch roles (43 total minus the now-21 `QUALITY_BAR_ROLES`).
- `git diff --stat` confirms only the 9 listed files changed.
