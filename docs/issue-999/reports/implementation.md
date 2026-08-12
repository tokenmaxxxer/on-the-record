---
code_under_review:
  - roles/specs/performance-engineering.spec.json
type: feature
breaking: false
verdict: supports
loop_state: landed
---

# Implementation record — issue #999

## What was done
Wired performance-engineering's `performance` axis-evaluation procedure
into `roles/specs/performance-engineering.spec.json`, per the approved
proposal `docs/issue-999/proposals/implementation.md`:
1. Added `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`
   to `required_fields`.
2. Extended `reference_resolution.rule` with the axis_evaluation clause
   (axis/verdict/citation/finding shape) verbatim-mirrored from
   `roles/specs/architecture.spec.json`,
   `roles/specs/security-threat-model.spec.json`, and
   `roles/specs/conformance-review.spec.json`.
3. Added a `gate_c_axis_evaluation` field pointing at
   `docs/handbooks/architecture-methodology.md`'s
   `## Axis evaluation procedure — performance` section, naming the
   error-budget recomputation method that section actually specifies.

## Why
Closes issue #999 (northpole req#5, `586 batch 4`): performance-engineering's
gate C check must point at the already-written performance procedure so
`gates/role_spec_shape.py` validates it the same way it already validates
the other three axis-owning roles.

## Upstream
Based on: docs/issue-999/proposals/implementation.md

## Acceptance verification
acceptance: `python3 gates/role_spec_shape.py roles/specs/performance-engineering.spec.json`
canonical: command executed live this session against the edited file.

```
$ python3 gates/role_spec_shape.py roles/specs/performance-engineering.spec.json; echo "exit=$?"
exit=0
```

acceptance: `python3 gates/role_spec_shape.py --roles-dir roles`
canonical: command executed live this session against the whole roles tree.

```
$ python3 gates/role_spec_shape.py --roles-dir roles; echo "exit=$?"
exit=0
```

derived: `grep -c axis_evaluation roles/specs/performance-engineering.spec.json`

```
$ grep -c axis_evaluation roles/specs/performance-engineering.spec.json
3
```

`>=1`, matching architecture.spec.json, security-threat-model.spec.json,
and conformance-review.spec.json.

derived: `git diff --stat`

```
$ git diff --stat
 roles/specs/performance-engineering.spec.json | 8 +++++++-
 1 file changed, 7 insertions(+), 1 deletion(-)
```

Only the one listed spec file touched, matching the proposal's frozen
write set.

## What did not work
None.

## Open findings
canonical: docs/issue-999/reports/implementation/hunt-performance-axis-wiring.md, section "before-landing — stance 1", read this session.

Before-landing warrant hunt (stance 1, composition) found that
`on-the-record/hooks/role-spec-reference-guard.sh`'s hardcoded
`_VERIFICATION_FAMILY_ROLES` allowlist does not include
performance-engineering (nor architecture, which carries the identical
mirrored rule text already landed). The `reference_resolution.rule` text
this diff adds is enforced for in-family roles (conformance-review,
security-threat-model, etc.) but not yet for performance-engineering —
orphaned `axis_evaluation` references in performance-engineering records
go unchecked by that hook today.

canonical: roles/specs/architecture.spec.json read this session, `reference_resolution.rule` field, compared against the same hook's `_VERIFICATION_FAMILY_ROLES` allowlist.

This affects the already-merged architecture.spec.json equally and is
outside this record's write set (roles/specs/performance-engineering.spec.json)
— a follow-up issue on the hook file is the right next step, not a change
to this delivery.
