# issue-999 current-state survey

## Scope

issue #999: "586 batch 4: performance-engineering 'performance' axis-evaluation
procedure" — northpole req#5. Acceptance: performance-engineering's rulebook
carries the performance axis procedure; gates/role_spec_shape.py's
axis-procedure validation shape must be satisfied for performance-engineering
once wired; roles without the axis stay untouched.

## What already exists

canonical: derived: sed -n '210,245p' docs/handbooks/architecture-methodology.md

docs/handbooks/architecture-methodology.md already carries a fully-written
"## Axis evaluation procedure — performance" section covering
READ/EXECUTE/CRITERIA/CITATION for the performance axis, anchored to the
Google SRE Workbook SLO-implementation and error-budget-policy chapters.

canonical: derived: cat roles/performance-engineering.json

roles/performance-engineering.json declares "judgment_axes": ["performance"].

canonical: derived: sed -n '118,133p' gates/role_spec_shape.py

The check_axis_ownership function in gates/role_spec_shape.py resolves
`performance` to exactly one owning role across roles/*.json based on each
role's judgment_axes field.

canonical: derived: cat roles/specs/performance-engineering.spec.json

roles/specs/performance-engineering.spec.json has not been wired: its
required_fields array has no axis_evaluation entry, its
reference_resolution.rule says nothing about axis_evaluation entries, and it
carries no gate_c_axis_evaluation key.

## The already-landed pattern (batch 4 precedent, issue #998)

canonical: derived: git show --stat 52ffa1b

issue #998 wired conformance-review.spec.json for the alignment axis in this
shape (commit 52ffa1b):

canonical: derived: cat roles/specs/conformance-review.spec.json

- required_fields gains one entry:
  { "name": "axis_evaluation", "type": "ref[]", "required": false }
- reference_resolution.rule gains one clause describing what each
  axis_evaluation ref must resolve to: axis present in judgment_axes,
  verdict in the fixed supports/contradicts/no-opinion set, a non-empty
  citation, and, only when verdict is contradicts, an accompanying object
  carrying target_path and required_fix.
- A new gate_c_axis_evaluation top-level key pointing at
  docs/handbooks/architecture-methodology.md, section
  'Axis evaluation procedure — <axis>', restating in one sentence what
  EXECUTE actually recomputes, per the axis's own source standard.

canonical: derived: grep -n gate_c_axis_evaluation roles/specs/architecture.spec.json roles/specs/security-threat-model.spec.json roles/specs/conformance-review.spec.json

architecture.spec.json and security-threat-model.spec.json carry the
identical shape for maintenance_complexity and attack_potential
respectively.

## The gap for issue #999

performance-engineering.spec.json is the one remaining unwired role among
the five axis owners (alignment, maintenance_complexity, attack_potential
already wired via prior batches; external_burden -> capacity-planning is out
of scope for this issue). Wiring it is the "most mechanical template fill
(1:1 axis-to-role fit)" the issue body names — same three edits, same file,
no new design decision: field name, resolution clause, and
gate_c_axis_evaluation text are fully determined by the pattern already
landed three times and by the handbook section that already exists.

## Write set implied

- roles/specs/performance-engineering.spec.json — add the axis_evaluation
  required_fields entry, extend reference_resolution.rule, add
  gate_c_axis_evaluation.
- docs/issue-999/reports/implementation.md (phase-2 record, does not exist
  yet — created once approved).

No other role's spec is touched — "roles without the axis are untouched"
acceptance criterion is satisfied structurally: the edit is scoped to one
file.

## Skip condition

Scouting (external best-in-class research) is skipped: the spec leaves no
design decision open. The exact field shape, resolution-clause phrasing
pattern, and gate_c_axis_evaluation format are already fixed by three prior
identical merges (architecture, security-threat-model, conformance-review)
and by the handbook section already on disk — there is nothing left to
research, only a template fill against a shape gates/role_spec_shape.py
already enforces.
