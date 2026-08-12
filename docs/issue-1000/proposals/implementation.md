---
status: proposed
files:
  - roles/specs/capacity-planning.spec.json
  - docs/issue-1000/reports/implementation.md
---

## Request

Wire capacity-planning's spec with the `external_burden` axis-evaluation
procedure per docs/issue-586/proposals/product-discovery.md (merged #995,
batch 3). The handbook prose for this axis already exists
(docs/handbooks/architecture-methodology.md, "Axis evaluation procedure —
external_burden"); the remaining gap is
`roles/specs/capacity-planning.spec.json` wiring, mirroring the pattern
already landed for architecture, security-threat-model, conformance-review
(issue #998), and performance-engineering (issue #999).

## Constraints

- No design decision is open: field shape, resolution-clause phrasing, and
  the `gate_c_axis_evaluation` format are fixed by four prior identical
  merges plus the handbook section already on disk (see survey, skip
  condition).
- Edit scoped to one role's spec file only — "roles without the axis are
  untouched" is an explicit acceptance criterion.
- `gates/role_spec_shape.py` shape checks (`check_axis_evaluation_entry`,
  `check_role_judgment_axes`, `check_axis_ownership`) must keep passing
  against the edited file.

## Rationale

Considered writing a brand-new `gate_c_axis_evaluation` prose sentence from
first principles for the `external_burden` axis, independent of the four
already-landed sentences (architecture/maintenance_complexity,
security-threat-model/attack_potential, conformance-review/alignment,
performance-engineering/performance). Rejected: those four sentences all
follow one fixed shape — name the source standard, restate in one clause
what EXECUTE actually recomputes — and the handbook's own "Axis evaluation
procedure — external_burden" section already states exactly what EXECUTE
recomputes (resolve `resource`, recompute `verdict` from `demand_forecast`
against `capacity_threshold`, then check whether the reviewed artifact
itself adds unaccounted new demand). Deriving a fresh sentence
independently risks drifting from the handbook section it must point at;
restating the handbook's own EXECUTE steps keeps the pointer sentence and
the section it cites in sync, matching how the four landed precedents were
built.

Also considered a push-back (reassigning `external_burden` away from
capacity-planning), since the issue explicitly allows one. Rejected: the
survey found capacity-planning is architecture's nearest-fit assignment and
the handbook section already describes a coherent
READ/EXECUTE/CRITERIA/CITATION procedure scoped to this role's own
`resource`/`demand_forecast`/`capacity_threshold`/`verdict` fields — there
is no fit problem to push back on.

## What will be done

- Add one `required_fields` entry to
  `roles/specs/capacity-planning.spec.json`:
  `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`.
- Extend `reference_resolution.rule` with a clause describing what each
  `axis_evaluation` ref must resolve to (axis in `judgment_axes`, verdict in
  the fixed supports/contradicts/no-opinion set, non-empty citation, and —
  iff verdict is `contradicts` — an object carrying `target_path` and
  `required_fix`), mirroring conformance-review's and
  performance-engineering's landed clauses.
- Add a `gate_c_axis_evaluation` top-level key pointing at
  `docs/handbooks/architecture-methodology.md`, section 'Axis evaluation
  procedure — external_burden', restating in one sentence that EXECUTE
  resolves `resource`, recomputes `verdict` from the record's own
  `demand_forecast` against `capacity_threshold`, and checks whether the
  reviewed artifact adds unaccounted new demand, per the ITIL Capacity
  Management practice (https://www.itlibrary.org/).
- Run `python3 gates/role_spec_shape.py roles/specs/capacity-planning.spec.json`
  and `python3 gates/role_spec_shape.py --roles-dir roles` to confirm the
  edited file and the axis-ownership matrix still pass.
- Write the phase-2 record at `docs/issue-1000/reports/implementation.md`.

## Out of scope

- Any other role's spec file — untouched per acceptance.
- The rulebook's actual external repo content
  (`$TOKENMAXXXER_RULEBOOKS/capacity-planning-rulebook`) — this repo only
  carries the spec/handbook side of the contract; the external rulebook
  repo is out of this session's reach.
- Any change to the handbook's existing "Axis evaluation procedure —
  external_burden" prose — it already exists and is not part of this
  issue's gap.

## How you'll know it worked

`python3 gates/role_spec_shape.py roles/specs/capacity-planning.spec.json`
exits 0, and `python3 gates/role_spec_shape.py --roles-dir roles` exits 0
with no axis-ownership regressions; `git diff --stat` against the
proposal's approval point shows only the two listed files touched.
