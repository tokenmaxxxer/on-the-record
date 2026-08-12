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
   `## Axis evaluation procedure — external_burden` section, restating the
   resource/demand_forecast/capacity_threshold recomputation that section
   specifies.

## Why
Closes issue #1000 (northpole req#5, `586 batch 3`): capacity-planning's
gate C check must point at the already-written external_burden procedure so
`gates/role_spec_shape.py` validates it the same way it already validates
the other four axis-owning roles.

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

## Doc-placement ladder
- No env var, config key, new dependency, migration, or setup step
  introduced — nothing to add to a handbook.
- No library/format choice over a named alternative and no changed public
  signature/wire format beyond the spec-file field addition itself, which
  the approved proposal already covers — no new docs/issue-1000/decisions/
  entry required.
- No benchmark/investigation numbers produced — nothing for
  docs/issue-1000/reports/ beyond this record.

## Open findings
None open at write time. Hunt record:
docs/issue-1000/reports/implementation/hunt-external-burden-axis-wiring.md
(after-proposal, phase 1); a before-landing dispatch is appended to that
same file prior to commit, per the warrant directive.
