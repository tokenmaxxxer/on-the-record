---
code_under_review:
  - roles/specs/conformance-review.spec.json
type: feature
breaking: false
verdict: supports
loop_state: landed
---

# Implementation record — issue #998

## What was done
Wired conformance-review's `alignment` axis-evaluation procedure into
`roles/specs/conformance-review.spec.json`, per the approved proposal
`docs/issue-998/proposals/implementation.md`:
1. Added `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`
   to `required_fields`.
2. Extended `reference_resolution.rule` with the axis_evaluation clause
   (axis/verdict/citation/finding shape) verbatim-mirrored from
   `roles/specs/architecture.spec.json` and
   `roles/specs/security-threat-model.spec.json`.
3. Added a `gate_c_axis_evaluation` field pointing at
   `docs/handbooks/architecture-methodology.md`'s
   `## Axis evaluation procedure — alignment` section, naming the EARL
   worst-case-recomputation method that section actually specifies.

## Why
Closes issue #998 (northpole req#5, `586 batch 2`): conformance-review's
gate C check must point at the already-written alignment procedure so
`gates/role_spec_shape.py` validates it the same way it already validates
the other two axis-owning roles.

## Upstream
Based on: docs/issue-998/proposals/implementation.md

## Acceptance verification
acceptance: `python3 gates/role_spec_shape.py roles/specs/conformance-review.spec.json`
canonical: command executed live this session against the edited file.

```
$ python3 gates/role_spec_shape.py roles/specs/conformance-review.spec.json; echo "exit=$?"
exit=0
```

derived: `grep -c axis_evaluation roles/specs/conformance-review.spec.json`

```
$ grep -c axis_evaluation roles/specs/conformance-review.spec.json
3
```

`>=1`, matching architecture.spec.json and security-threat-model.spec.json.

## What did not work
None.

## Open findings
None.
