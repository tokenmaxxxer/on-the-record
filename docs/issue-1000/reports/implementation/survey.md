# issue-1000 current-state survey

## Scope

issue #1000: "586 batch 3: capacity-planning 'external_burden'
axis-evaluation procedure" — northpole req#5. Acceptance (as stated in the
issue body): capacity-planning's rulebook carries the external_burden axis
procedure (or a recorded push-back reassigning the axis); the check named
is `gates/role_spec_shape.py` axis-procedure validation for
capacity-planning; roles without the axis stay untouched.

## What already exists

canonical: derived: sed -n '170,207p' docs/handbooks/architecture-methodology.md

docs/handbooks/architecture-methodology.md already carries a fully-written
"## Axis evaluation procedure — external_burden" section covering
READ/EXECUTE/CRITERIA/CITATION for the external_burden axis, anchored to
the ITIL Capacity Management practice (https://www.itlibrary.org/).

canonical: derived: cat roles/capacity-planning.json

roles/capacity-planning.json declares `"judgment_axes": ["external_burden"]`.

canonical: derived: sed -n '118,133p' gates/role_spec_shape.py

`check_axis_ownership` in gates/role_spec_shape.py resolves `external_burden`
to exactly one owning role across `roles/*.json`, based on each role's
`judgment_axes` field.

canonical: derived: cat roles/specs/capacity-planning.spec.json

roles/specs/capacity-planning.spec.json has no `axis_evaluation` entry in
its `required_fields` array, its `reference_resolution.rule` says nothing
about `axis_evaluation` entries, and it carries no `gate_c_axis_evaluation`
key.

## The already-landed pattern (batch precedent, issues #997/#998/#999)

canonical: derived: git show --stat 52ffa1b

issue #998 wired conformance-review.spec.json for the alignment axis in
this shape (commit 52ffa1b):

canonical: derived: cat roles/specs/conformance-review.spec.json

- `required_fields` gains one entry:
  `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`.
- `reference_resolution.rule` gains one clause describing what each
  `axis_evaluation` ref must resolve to: axis present in `judgment_axes`,
  verdict in the fixed supports/contradicts/no-opinion set, a non-empty
  citation, and — only when verdict is `contradicts` — an accompanying
  object carrying `target_path` and `required_fix`.
- A new `gate_c_axis_evaluation` top-level key pointing at
  `docs/handbooks/architecture-methodology.md`, section
  'Axis evaluation procedure — <axis>', restating in one sentence what
  EXECUTE actually recomputes, per the axis's own source standard.

canonical: derived: grep -n gate_c_axis_evaluation roles/specs/architecture.spec.json roles/specs/security-threat-model.spec.json roles/specs/conformance-review.spec.json roles/specs/performance-engineering.spec.json

architecture.spec.json, security-threat-model.spec.json,
conformance-review.spec.json, and performance-engineering.spec.json (issue
#999) carry the identical shape for maintenance_complexity,
attack_potential, alignment, and performance respectively.

## The gap for issue #1000

capacity-planning.spec.json is the last remaining unwired role among the
five axis owners (alignment, maintenance_complexity, attack_potential, and
performance are already wired via prior batches). Wiring it is the same
mechanical template fill the prior four batches used: same three edits,
same file, no new design decision — field name, resolution clause, and
`gate_c_axis_evaluation` text are fully determined by the pattern already
landed four times and by the handbook section that already exists on disk.
No push-back is warranted: capacity-planning is architecture's nearest-fit
assignment for `external_burden` and the handbook section already
describes a coherent READ/EXECUTE/CRITERIA/CITATION procedure scoped to
this role's own `resource`/`demand_forecast`/`capacity_threshold`/`verdict`
fields.

## Write set implied

- roles/specs/capacity-planning.spec.json — add the `axis_evaluation`
  `required_fields` entry, extend `reference_resolution.rule`, add
  `gate_c_axis_evaluation`.
- docs/issue-1000/reports/implementation.md (phase-2 record, does not
  exist yet — created once approved).

No other role's spec is touched — "roles without the axis are untouched"
acceptance criterion is satisfied structurally: the edit is scoped to one
file.

## Skip condition

Scouting (external best-in-class research) is skipped: the spec leaves no
design decision open. The exact field shape, resolution-clause phrasing
pattern, and `gate_c_axis_evaluation` format are already fixed by four
prior identical merges (architecture, security-threat-model,
conformance-review, performance-engineering) and by the handbook section
already on disk — there is nothing left to research, only a template fill
against a shape `gates/role_spec_shape.py` already enforces.
