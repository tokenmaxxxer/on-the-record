---
status: proposed
files:
  - roles/specs/performance-engineering.spec.json
  - docs/issue-999/reports/implementation.md
---

## Request

Wire performance-engineering's spec with the `performance` axis-evaluation
procedure per docs/issue-586/proposals/product-discovery.md (merged #995,
batch 4). The handbook prose for this axis already exists
(docs/handbooks/architecture-methodology.md, "Axis evaluation procedure —
performance"); the remaining gap is `roles/specs/performance-engineering.spec.json`
wiring, mirroring the pattern already landed for architecture,
security-threat-model, and conformance-review (issue #998).

## Constraints

- No design decision is open: field shape, resolution-clause phrasing, and
  the `gate_c_axis_evaluation` format are fixed by three prior identical
  merges plus the handbook section already on disk (see survey, skip
  condition).
- Edit scoped to one role's spec file only — "roles without the axis are
  untouched" is an explicit acceptance criterion.
- `gates/role_spec_shape.py` shape checks (`check_axis_evaluation_entry`,
  `check_role_judgment_axes`, `check_axis_ownership`) must keep passing
  against the edited file.

## Rationale

Considered writing a brand-new `gate_c_axis_evaluation` prose sentence from
first principles for the `performance` axis, independent of the three
already-landed sentences (architecture/maintenance_complexity,
security-threat-model/attack_potential, conformance-review/alignment).
Rejected: those three sentences all follow one fixed shape — name the
source standard, restate in one clause what EXECUTE actually recomputes —
and the handbook's own "Axis evaluation procedure — performance" section
already states exactly what EXECUTE recomputes (error_budget_remaining from
sli against slo_target, then verdict from that recomputed budget). Deriving
a fresh sentence independently risks drifting from the handbook section it
must point at; restating the handbook's own EXECUTE steps keeps the pointer
sentence and the section it cites in sync, matching how the three landed
precedents were built.

## What will be done

- Add one `required_fields` entry to
  `roles/specs/performance-engineering.spec.json`:
  `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`.
- Extend `reference_resolution.rule` with a clause describing what each
  `axis_evaluation` ref must resolve to (axis in `judgment_axes`, verdict in
  the fixed supports/contradicts/no-opinion set, non-empty citation, and —
  iff verdict is `contradicts` — an object carrying `target_path` and
  `required_fix`), mirroring conformance-review's landed clause.
- Add a `gate_c_axis_evaluation` top-level key pointing at
  `docs/handbooks/architecture-methodology.md`, section 'Axis evaluation
  procedure — performance', restating in one sentence that EXECUTE
  recomputes `error_budget_remaining` from the current `sli` measurement
  against `slo_target` and recomputes `verdict` from that recomputed
  budget, per the Google SRE Workbook (implementing-slos /
  error-budget-policy chapters).
- Run `python3 gates/role_spec_shape.py roles/specs/performance-engineering.spec.json`
  and `python3 gates/role_spec_shape.py --roles-dir roles` to confirm the
  edited file and the axis-ownership matrix still pass.
- Write the phase-2 record at `docs/issue-999/reports/implementation.md`.

## Out of scope

- Any other role's spec file (capacity-planning/`external_burden`
  included) — untouched per acceptance.
- The rulebook's actual external repo content
  (`$TOKENMAXXXER_RULEBOOKS/performance-engineering-rulebook`) — this repo
  only carries the spec/handbook side of the contract; the external
  rulebook repo is out of this session's reach.
- Any change to the handbook's existing "Axis evaluation procedure —
  performance" prose — it already exists and is not part of this issue's
  gap.

## How you'll know it worked

`python3 gates/role_spec_shape.py roles/specs/performance-engineering.spec.json`
exits 0, and `python3 gates/role_spec_shape.py --roles-dir roles` exits 0
with no axis-ownership regressions; `git diff --stat` against the proposal's
approval point shows only the two listed files touched.
