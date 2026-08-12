---
status: proposed
files:
  - roles/specs/conformance-review.spec.json
  - docs/issue-998/reports/implementation/survey.md
  - docs/issue-998/proposals/implementation.md
---

# Proposal — issue #998, conformance-review 'alignment' axis-evaluation wiring

## Request
Per issue #998 (northpole req#5, `586 batch 2`): conformance-review's
gate C check must point at the already-written 'alignment'
axis-evaluation procedure, and `gates/role_spec_shape.py`'s
axis-procedure validation must pass for conformance-review.

## Constraints
- The alignment procedure's prose already exists in
  `docs/handbooks/architecture-methodology.md` (survey's grep result)
  and is not reopened or rewritten here.
- The 5-axis vocabulary and ownership matrix are settled
  (`roles/conformance-review.json` already declares
  `"judgment_axes": ["alignment"]`) and are not reopened here.
- Write set is `roles/specs/conformance-review.spec.json` plus this
  proposal's own docs — no rulebook-repo prose (cross-repo, out of this
  role's write scope) and no gate-script code change (the two existing
  instances already exercise `check_axis_evaluation_entry` correctly;
  this proposal only wires a third role into the pattern that code
  already checks).

## Rationale
Two ways to close the "gate C check points at it" acceptance line were
considered:

1. **Add a new field/property to `gates/role_spec_shape.py`'s `check()`
   that explicitly requires `gate_c_axis_evaluation` on every
   axis-owning role's spec.** Rejected: `architecture.spec.json` and
   `security-threat-model.spec.json` both already carry the
   `axis_evaluation` field / `reference_resolution` clause /
   `gate_c_axis_evaluation` pointer without any such mechanical
   requirement forcing them — the pattern was established by hand,
   matching the handbook's own stated shape contract ("each owning
   role's rulebook session fills the four blanks … using its own domain
   knowledge"). Adding a new mechanical requirement to the shared gate
   script is a design change to shared validation logic that this
   issue's acceptance criteria do not ask for (the acceptance line only
   asks that the check *pass*, not that a new check be added), and it
   would touch a second role's shape (gate script) beyond the frozen
   write set.
2. **Mirror the exact fields the two existing axis-owning roles already
   carry into `conformance-review.spec.json`** (chosen). This closes the
   literal gap the survey found — conformance-review is the only one of
   the three currently-implemented axis owners missing the wiring — using
   a shape `gates/role_spec_shape.py::check()` already accepts (the two
   existing instances prove this), so no gate-script change is needed at
   all.

## What will be done
Edit `roles/specs/conformance-review.spec.json`:
1. Add `{ "name": "axis_evaluation", "type": "ref[]", "required": false }`
   to `required_fields`, after the existing 4 fields.
2. Extend `reference_resolution.rule` with the same axis_evaluation
   clause `architecture.spec.json` and `security-threat-model.spec.json`
   both already carry verbatim (axis/verdict/citation/finding shape).
3. Add a `gate_c_axis_evaluation` field pointing at
   `docs/handbooks/architecture-methodology.md`'s
   `## Axis evaluation procedure — alignment` section, worded to name
   the EARL worst-case-recomputation method the section actually
   specifies (mirroring how the other two roles' `gate_c_axis_evaluation`
   fields name their own section's actual method, not just the section
   title).

## Out of scope
- Rewriting or relocating the alignment procedure prose itself.
- Reopening the axis vocabulary or ownership assignments.
- Any change to `gates/role_spec_shape.py` or to any other role's spec.
- Batches 3/4/5 from `docs/issue-586/proposals/product-discovery.md`
  (capacity-planning, performance-engineering, panel fixture) — each is
  its own filed issue, not this one.

## How you'll know it worked
acceptance: `python3 gates/role_spec_shape.py roles/specs/conformance-review.spec.json` — result: exit 0, no stderr, after the edit (same command already exits 0 today per the survey; the edit only adds optional/additive fields to a shape the checker already accepts).
derived: `grep -c axis_evaluation roles/specs/conformance-review.spec.json` after the edit should be >=1, matching the >=1 count already present in `roles/specs/architecture.spec.json` and `roles/specs/security-threat-model.spec.json`.
