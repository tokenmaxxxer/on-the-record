# Architecture methodology

## Axis evaluation procedure template

Every methodology-axis-owning role's rulebook must add one section shaped
exactly like this template, one section per axis it owns
(`docs/issue-586/proposals/architecture.md` section 2). The shape mirrors
the `axis_evaluation` record shape `gates/role_spec_shape.py::check_axis_evaluation_entry`
already validates: `axis` must be one the role's `judgment_axes` names,
`verdict` one of `supports`/`contradicts`/`no-opinion`, `citation`
non-empty, and — iff `verdict == "contradicts"` — a `finding` object
carrying `target_path` (must resolve against some role's `write_scope`
glob) and `required_fix`.

```markdown
## Axis evaluation procedure — <axis-name>

READ: <the specific record/spec paths this role reads to judge this
  axis — e.g. conformance-review reads the spec cited by the
  implementation record's `Upstream / basis` line>

EXECUTE:
1. <mechanical step producing evidence — e.g. "diff the landed artifact
   against the cited spec section", not "consider whether it feels
   aligned">
2. <mechanical step>
3. ...

CRITERIA FOR supports: <closed, checkable condition>
CRITERIA FOR contradicts: <closed, checkable condition — must be able to
  produce a `finding.target_path` that resolves against some role's
  `write_scope` and a `finding.required_fix`, per the existing shape
  check>
CRITERIA FOR no-opinion: <when the axis is out of scope for the artifact
  under review — e.g. no trust boundary present for attack_potential>

CITATION: <what `axis_evaluation.citation` must point to — a record path
  or commit sha, never a paraphrase>
```

This is a shape contract, not prose per role — each owning role's
rulebook session fills the four blanks (READ/EXECUTE/CRITERIA/CITATION)
for its own axis using its own domain knowledge. `EXECUTE` steps must be
mechanical (read a file, run a diff, check a field) so the verdict is
"expertise exercised," not a self-report; a step that reduces to
"consider whether X" with no checkable output does not satisfy this
template.

The 5-axis matrix (`alignment` -> conformance-review, `maintenance_complexity`
-> architecture, `external_burden` -> capacity-planning, `attack_potential`
-> security-threat-model, `performance` -> performance-engineering) is
fixed and machine-checked by `gates/role_spec_shape.py::check_axis_ownership`
(run via `python3 gates/role_spec_shape.py --roles-dir roles`) — see
`docs/decisions/2026-08-10-judgment-axis-matrix.md`.
