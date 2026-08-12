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

## Axis evaluation procedure — maintenance_complexity

READ: the ADR referenced by `decision_id`, its `considered_options` and
  `decision_drivers` fields, and the module(s) the decision's `outcome`
  actually touches (per the ADR's own file references).

EXECUTE:
1. List every entry in `considered_options`; an ADR with exactly one
   listed option fails step 2 automatically (MADR, adr.github.io/madr,
   requires >=2 real alternatives for a decision to be a decision, not a
   foregone conclusion documented after the fact).
2. For each considered option, check that `decision_drivers` states at
   least one concrete driver (a constraint, quality attribute, or cost)
   that differentiates it from the chosen option — a driver present only
   as a restated goal ("should be maintainable") does not count.
3. Diff the module(s) touched by the accepted option against the
   rejected options' described scope: does the chosen option's
   `outcome` actually reduce coupling/duplication relative to at least
   one rejected option, checkable against the referenced files, or does
   it only claim to?

CRITERIA FOR supports: >=2 considered_options, each with a stated
  driver, and the diff in step 3 shows the accepted option measurably
  reduces coupling/duplication versus a rejected alternative.
CRITERIA FOR contradicts: the ADR's own considered_options/drivers are
  present, but the diff in step 3 shows the accepted option does not
  reduce (or worsens) maintenance burden versus a rejected alternative —
  produce a `finding.target_path` inside the ADR's own write_scope and a
  `required_fix` naming the specific missing trade-off analysis.
CRITERIA FOR no-opinion: the reviewed artifact carries no ADR
  (decision_id unresolved) or the change is additive with no considered
  alternative in scope (e.g. a net-new module with no prior design to
  weigh against).

CITATION: the ADR's own `docs/decisions/*.md` path plus MADR's template
  (https://adr.github.io/madr/), which is the source for the
  >=2-options/stated-drivers requirement above.

## Axis evaluation procedure — attack_potential

READ: the spec or design doc that introduced the trust boundary,
  authentication surface, or sensitive-data flow, and this role's own
  `element`-listed data-flow-diagram entries for that artifact.

EXECUTE:
1. Enumerate every element named in the record's `element` field(s) —
   each process, data store, data flow, and external entity that
   crosses or touches the trust boundary under review.
2. For each element, test it against all six STRIDE categories
   explicitly (Spoofing, Tampering, Repudiation, Information Disclosure,
   Denial of Service, Elevation of Privilege) — per Adam Shostack,
   *Threat Modeling: Designing for Security* (Wiley, 2014), ch. 3-4,
   which defines STRIDE's method as this per-element-per-category walk,
   not a free-form threat brainstorm.
3. Count categories with at least one recorded `type` entry for that
   element versus categories with none — an element crossing an
   authentication boundary with zero Spoofing or Elevation of Privilege
   entries is an incomplete walk, not a clean bill.

CRITERIA FOR supports: every element identified in step 1 has at least
  one threat entry, or an explicit "not applicable to this element"
  note, for all six STRIDE categories.
CRITERIA FOR contradicts: an element that crosses an authentication
  surface or sensitive-data flow has zero entries for Spoofing,
  Tampering, Information Disclosure, or Elevation of Privilege with no
  stated reason — produce a `finding.target_path` inside the
  security-threat-model write_scope and a `required_fix` naming the
  missing category/element pair.
CRITERIA FOR no-opinion: the reviewed artifact introduces no new trust
  boundary, authentication surface, or sensitive-data flow (this role's
  own `use_when.board_condition` does not fire).

CITATION: the security-threat-model record's own
  `docs/issue-<n>/reports/security-threat-model.md` entry plus Shostack
  (2014) ch. 3-4 for the per-element STRIDE-coverage method above.
