---
code_under_review:
  - roles/specs/capacity-planning.spec.json
type: feature
breaking: false
verdict: supports
loop_state: landed
---

# Implementation record — issue #1000

## What was done
Wired capacity-planning's `external_burden` axis-evaluation procedure into
`roles/specs/capacity-planning.spec.json`, per the approved proposal
`docs/issue-1000/proposals/implementation.md`:
1. Added `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`
   to `required_fields`.
2. Extended `reference_resolution.rule` with the axis_evaluation clause
   (axis/verdict/citation/finding shape) verbatim-mirrored from
   `roles/specs/architecture.spec.json`,
   `roles/specs/security-threat-model.spec.json`,
   `roles/specs/conformance-review.spec.json`, and
   `roles/specs/performance-engineering.spec.json`.
3. Added a `gate_c_axis_evaluation` field pointing at
   `docs/handbooks/architecture-methodology.md`'s
   `## Axis evaluation procedure — external_burden` section, naming the
   resource/demand recomputation method that section actually specifies.

## Why
Closes issue #1000 (northpole req#5, `586 batch 3`): capacity-planning's
gate C check must point at the already-written external_burden procedure
so `gates/role_spec_shape.py` validates it the same way it already
validates architecture, security-threat-model, conformance-review, and
performance-engineering.

## Upstream
Based on: docs/issue-1000/proposals/implementation.md

## Acceptance verification
acceptance: `python3 gates/role_spec_shape.py roles/specs/capacity-planning.spec.json`
canonical: command executed live this session against the edited file.

```
$ python3 gates/role_spec_shape.py roles/specs/capacity-planning.spec.json; echo "exit=$?"
exit=0
```

acceptance: `python3 gates/role_spec_shape.py --roles-dir roles`
canonical: command executed live this session against the whole roles tree.

```
$ python3 gates/role_spec_shape.py --roles-dir roles; echo "exit=$?"
exit=0
```

derived: `grep -c axis_evaluation roles/specs/capacity-planning.spec.json`

```
$ grep -c axis_evaluation roles/specs/capacity-planning.spec.json
3
```

`>=1`, matching architecture.spec.json, security-threat-model.spec.json,
conformance-review.spec.json, and performance-engineering.spec.json.

derived: `git diff --stat`

```
$ git diff --stat
 roles/specs/capacity-planning.spec.json | 8 +++++++-
 1 file changed, 7 insertions(+), 1 deletion(-)
```

Only the one listed spec file touched, matching the proposal's frozen
write set.

## What did not work
None.

## Open findings
canonical: on-the-record/hooks/role-spec-reference-guard.sh, `_VERIFICATION_FAMILY_ROLES` definition (lines 40-55), read this session.

Same pre-existing gap already recorded for performance-engineering in
issue #999: the hardcoded `_VERIFICATION_FAMILY_ROLES` allowlist there
does not include capacity-planning (nor architecture/
performance-engineering, which carry the identical mirrored rule text
already landed). The `reference_resolution.rule` text this diff adds is
enforced for in-family roles (conformance-review, security-threat-model,
etc.) but not yet for capacity-planning — orphaned `axis_evaluation`
references in capacity-planning records go unchecked by that hook today.
This is outside this record's write set (roles/specs/capacity-planning.spec.json)
— a follow-up issue on the hook file is the right next step, not a
change to this delivery.
