# Current-state survey — issue #998

## Write set surveyed
- `roles/specs/conformance-review.spec.json`

## What already exists

- derived: `grep -n "^## Axis evaluation procedure — alignment" -A2 docs/handbooks/architecture-methodology.md`
  ```
  132:## Axis evaluation procedure — alignment
  133-
  134-READ: the conformance-review record's own `subject`/`test`/`result`
  ```
  acceptance: grep on docs/handbooks/architecture-methodology.md — result: the
  `## Axis evaluation procedure — alignment` section (READ / EXECUTE /
  CRITERIA FOR supports / contradicts / no-opinion / CITATION) is
  present in the file. The prose issue #998 asks for
  ("conformance-review's rulebook carries the alignment procedure") is
  already present in this file — this repo's rulebook home for
  axis-evaluation procedures is this handbook file, not
  conformance-review's cross-repo rulebook
  (`docs/issue-586/proposals/product-discovery.md` states plainly it
  "cannot write rulebook prose itself (cross-repo …)" — the same
  constraint applies here).
- canonical: roles/conformance-review.json (full file read) — already
  declares `"judgment_axes": ["alignment"]`.
- derived: `grep -rl axis_evaluation roles/specs/*.spec.json`
  ```
  roles/specs/architecture.spec.json
  roles/specs/security-threat-model.spec.json
  ```
  Only these two carry an `axis_evaluation` required_fields entry, a
  matching `reference_resolution.rule` clause, and a
  `gate_c_axis_evaluation` field pointing at the handbook section.
  `roles/specs/conformance-review.spec.json` has none of the three —
  this is the actual gap issue #998's "gate C check points at it"
  acceptance line names.

## The gap

canonical: roles/specs/conformance-review.spec.json (full file read) —
it has 4 `required_fields` (`subject`, `test`, `result`, `assertedBy`),
a `reference_resolution.rule` that covers only `test`/`subject`
resolution, and no `gate_c_axis_evaluation` field at all — unlike
architecture and security-threat-model's specs (canonical:
roles/specs/architecture.spec.json and
roles/specs/security-threat-model.spec.json, both full file reads),
which both carry:
1. an `axis_evaluation` entry in `required_fields` (`type: "ref[]"`,
   `required: false`),
2. a `reference_resolution.rule` clause (verbatim-identical wording
   across both existing specs) describing what a valid `axis_evaluation`
   ref must carry (`axis`, `verdict`, `citation`, and the conditional
   `finding` object),
3. a `gate_c_axis_evaluation` field citing
   `docs/handbooks/architecture-methodology.md`'s matching section by
   name.

## Alternative considered and rejected

Writing new prose in the handbook for the alignment procedure was
considered and rejected — per the grep result above, the section
already exists; re-writing it would duplicate present content with no
acceptance-criterion gap to close. The only remaining gap is the
spec.json wiring (axis_evaluation field + reference_resolution clause +
gate_c_axis_evaluation pointer) that the other two axis-owning roles'
specs already carry.

## Skip-condition note (scout-directive)

Scouting (external field sweep) is skipped: the spec leaves no design
decision open. The target shape (`axis_evaluation` field,
`reference_resolution.rule` clause, `gate_c_axis_evaluation` field) is
fixed byte-for-byte by the template documented in
`docs/handbooks/architecture-methodology.md`'s own "Axis evaluation
procedure template" section and mirrored identically in the two
existing instances (canonical: roles/specs/architecture.spec.json,
roles/specs/security-threat-model.spec.json) — this is mechanical
propagation of an established pattern to a third role, not a new design
choice.

## Check command available for this change

acceptance: `python3 gates/role_spec_shape.py roles/specs/conformance-review.spec.json` — result: exit 0, no stderr output.
Must stay exit 0 after the edit, since the new fields are additive to a
shape the checker already accepts.
