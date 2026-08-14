---
kind: current-state-survey
subject: issue-1000
code_under_review:
- roles/specs/capacity-planning.spec.json
- docs/issue-1000/reports/implementation.md
- docs/handbooks/architecture-methodology.md
---

# Current-state survey — conformance review of issue #1000

## Background

canonical: docs/issue-1000/reports/implementation.md, read this session — the merged phase-2 delivery (commit 3269ae63b9e403df07503edca0f2f0692dbcc8f4, PR #1075) claims all four of issue #1000's acceptance items met. No conformance-review record for this sha exists yet on origin/main.

## Method

Re-ran each `derived:`/`acceptance:` command the implementation record cites against current origin/main state, and independently re-checked the two acceptance items the record does not cite a command for (empty-state, provenance).

## Findings

canonical: roles/specs/capacity-planning.spec.json, read this session:
```
$ grep -n axis_evaluation roles/specs/capacity-planning.spec.json
30:      "name": "axis_evaluation",
36:    "rule": "resource must resolve to an actual monitored resource ... Each axis_evaluation ref must resolve to a real entry ...",
39:  "gate_c_axis_evaluation": "see docs/handbooks/architecture-methodology.md, section 'Axis evaluation procedure — external_burden' ..."
```
### Acceptance #1 — "capacity-planning's rulebook carries the external_burden procedure" — reproduces

canonical: docs/handbooks/architecture-methodology.md, read this session — section `## Axis evaluation procedure — external_burden` exists at line 170, and line 50 maps `external_burden` -> capacity-planning in the axis-to-role table. The `gate_c_axis_evaluation` field's cited section actually exists and actually specifies a READ/EXECUTE/CRITERIA/CITATION method.

derived: `python3 gates/role_spec_shape.py roles/specs/capacity-planning.spec.json; echo exit=$?`, run this session:
```
exit=0
```
derived: `python3 gates/role_spec_shape.py --roles-dir roles; echo exit=$?`, run this session:
```
exit=0
```
### Acceptance #2 — "gates/role_spec_shape.py axis-procedure validation passes for capacity-planning" — reproduces

derived: `git diff dfa1230e^ 3269ae63 --stat -- roles/`, run this session:
```
 roles/specs/capacity-planning.spec.json | 8 +++++++-
 1 file changed, 7 insertions(+), 1 deletion(-)
```
### Acceptance #3 — "empty state: roles without the axis are untouched" — reproduces

Only capacity-planning.spec.json under roles/ changed across the phase-1+phase-2 commit range; the other 42 files in roles/specs/ are untouched.

canonical: docs/issue-1000/proposals/implementation.md, read this session — states basis `docs/issue-586/proposals/product-discovery.md (merged #995)`, matching the issue body's stated provenance ("Follow-up per docs/issue-586/proposals/product-discovery.md (merged #995), RICE 18").

### Acceptance #4 — "provenance: read — merged proposal batch 3" — reproduces

## Open findings

canonical: docs/issue-1000/reports/implementation.md, "Open findings" section, read this session — the implementation record itself flags that `on-the-record/hooks/role-spec-reference-guard.sh`'s `_VERIFICATION_FAMILY_ROLES` allowlist does not include capacity-planning, so the `axis_evaluation` reference-shape rule this diff adds is not yet enforced by that hook for capacity-planning records. This is a pre-existing gap (also recorded for performance-engineering in issue #999), not introduced by this commit, and is out of this record's write set.

No other discrepancy located between the four acceptance items and current repo state; the phase-2 delivery's own verification transcript reproduces on independent re-run.
