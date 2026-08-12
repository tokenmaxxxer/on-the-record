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

## Axis evaluation procedure — alignment

READ: the conformance-review record's own `subject`/`test`/`result`
  entries (`docs/issue-<n>/reports/conformance-review.md`) and the
  conformance criterion each `test` field resolves to (a spec section,
  requirement, or lint rule).

EXECUTE:
1. For each cited entry, resolve `test` to the actual conformance
   criterion text — a `test` value that names a criterion but does not
   quote or link its checkable condition fails this step (EARL 1.0
   Schema, https://www.w3.org/TR/EARL10-Schema/, requires `test` to
   reference a real `TestCriterion`, not a paraphrase).
2. Recompute the record's overall verdict as the worst-case `result`
   across all cited entries in the fixed EARL severity order (`failed`
   > `cantTell` > `inapplicable` > `untested` > `passed`) and compare it
   against any standalone summary verdict the record asserts.
3. Check that `assertedBy` names the actual conformance-review session
   or tool run, not a generic placeholder — EARL requires every
   assertion to be attributable to its asserter.

CRITERIA FOR supports: every cited `test` resolves to a real criterion,
  the recomputed worst-case verdict in step 2 matches any asserted
  summary verdict, and every entry carries a real `assertedBy`.
CRITERIA FOR contradicts: the recomputed worst-case verdict in step 2
  disagrees with an asserted summary verdict, or a cited `test` does
  not resolve to a real criterion — produce a `finding.target_path`
  inside conformance-review's own `write_scope` and a `required_fix`
  naming the specific entry whose recomputation or reference fails.
CRITERIA FOR no-opinion: no conformance-review record exists yet for
  the artifact under review (this role's own `use_when.board_condition`
  does not fire).

CITATION: the conformance-review record's own
  `docs/issue-<n>/reports/conformance-review.md` entry plus the EARL 1.0
  Schema (W3C, https://www.w3.org/TR/EARL10-Schema/) for the
  worst-case-recomputation method above.

## Axis evaluation procedure — external_burden

READ: the capacity-planning record's own `resource`/`demand_forecast`/
  `capacity_threshold`/`verdict` entries
  (`docs/issue-<n>/reports/capacity-planning.md`) for the resource the
  reviewed artifact adds load to.

EXECUTE:
1. Resolve `resource` to an actual monitored resource (a named service,
   queue, database, or external quota) — an unresolvable reference fails
   this step (ITIL Capacity Management practice requires every capacity
   record to name a real monitored resource, not an abstract concern).
2. Recompute `verdict` from the record's own `demand_forecast` against
   its own `capacity_threshold` (`within-capacity` iff forecast <=
   threshold) rather than accepting an asserted `verdict` at face value.
3. Check whether the artifact under review is itself a source of new
   demand on the resource (a new caller, a new write path, a new
   scheduled job) — if so, confirm the record's `demand_forecast`
   actually accounts for that artifact, not just pre-existing load.

CRITERIA FOR supports: `resource` resolves, the recomputed verdict in
  step 2 matches the record's asserted `verdict`, and step 3's new-demand
  check (when applicable) is accounted for in the forecast.
CRITERIA FOR contradicts: the recomputed verdict in step 2 disagrees
  with the record's asserted `verdict`, or the artifact under review adds
  demand the forecast does not account for — produce a
  `finding.target_path` inside capacity-planning's own `write_scope` and
  a `required_fix` naming the unaccounted demand source or the
  recomputation mismatch.
CRITERIA FOR no-opinion: no capacity-planning record exists yet for the
  resource the reviewed artifact touches (this role's own
  `use_when.board_condition` does not fire).

CITATION: the capacity-planning record's own
  `docs/issue-<n>/reports/capacity-planning.md` entry plus the ITIL
  Capacity Management practice (https://www.itlibrary.org/) for the
  demand-forecast-vs-threshold recomputation method above.

## Axis evaluation procedure — performance

READ: the performance-engineering record's own `sli`/`slo_target`/
  `error_budget_remaining`/`verdict` entries
  (`docs/issue-<n>/reports/performance-engineering.md`) for the SLI the
  reviewed artifact is latency- or throughput-sensitive against.

EXECUTE:
1. Resolve `sli` to an actual monitored metric — an unresolvable
   reference fails this step (Google SRE Workbook,
   https://sre.google/workbook/implementing-slos/, requires every SLO
   record to be anchored to a real, queryable SLI).
2. Recompute `error_budget_remaining` from the current `sli` measurement
   against `slo_target` (per the error-budget-policy formula,
   https://sre.google/workbook/error-budget-policy/) rather than
   accepting an asserted remaining-budget figure at face value.
3. Recompute `verdict` from the recomputed `error_budget_remaining`
   (`within-budget` iff remaining budget > 0) and compare it against the
   record's own asserted `verdict`.

CRITERIA FOR supports: `sli` resolves, the recomputed
  `error_budget_remaining` in step 2 matches the record's asserted
  figure within the policy's stated tolerance, and the recomputed
  `verdict` in step 3 matches the asserted `verdict`.
CRITERIA FOR contradicts: the recomputed budget or verdict disagrees
  with the record's asserted figures — produce a `finding.target_path`
  inside performance-engineering's own `write_scope` and a
  `required_fix` naming the recomputation mismatch.
CRITERIA FOR no-opinion: no performance-engineering record exists yet
  for the SLI the reviewed artifact touches (this role's own
  `use_when.board_condition` does not fire).

CITATION: the performance-engineering record's own
  `docs/issue-<n>/reports/performance-engineering.md` entry plus the
  Google SRE Workbook's SLO-implementation
  (https://sre.google/workbook/implementing-slos/) and error-budget-policy
  (https://sre.google/workbook/error-budget-policy/) chapters for the
  recomputation method above.
