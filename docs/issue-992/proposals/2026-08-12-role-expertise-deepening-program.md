---
status: proposed
files:
  - docs/issue-992/reports/product-discovery/current-state.md
  - docs/issue-992/proposals/2026-08-12-role-expertise-deepening-program.md
---

## Request

Issue #992 (product-discovery, phase 1): define the expertise template a
rulebook must carry, survey the remaining 37 `roles/specs/*.spec.json`
files against it (the 6 files piloted by #807/#926/#935 are out of this
issue's scope per its own text), reuse #807's Gate A/B/C
prioritization to rank the 37 for deepening, and propose a phased plan
with a live-fire verification design. No spec or handbook edits land in
this PR — this is the survey + proposal round; a build-now or approved
follow-up does the per-cluster rewrite.

## Constraints

- Reuse #807's Gate A (valid judgment) / Gate B (valid deliverable) /
  Gate C (lens-based finding) rubric verbatim as the judgment/deliverable
  layer of #992's 5-part template; do not redefine it.
- Every methodology/framework/citation named below must be a real,
  checkable source with an identifiable author or issuing body — no
  fabricated citations (issue's own constraint).
- Compose with `judgment_axes` (#586) and the `axis_evaluation` shared
  mechanism (`docs/handbooks/architecture-methodology.md`) rather than
  inventing a second decision-framework template for the 5 axis-owning
  roles.
- Rulebook repos are not readable this session (current-state.md); this
  proposal grades against `roles/specs/*.spec.json` as #807 did, and
  states that substitution rather than asserting rulebook-repo content
  it did not read.

## 1. The expertise template (5 parts, composing with #807's 3 gates)

| Template part | Composes with | Pass condition |
|---|---|---|
| (a) core methodologies + when-to-use routing | Gate A | `source_standard` names a real, citable method AND the spec text states which method applies under which circumstance (routing), not one method asserted as universal |
| (b) decision frameworks composing with `judgment_axes` | Gate A + `axis_evaluation` | for axis-owning roles: the role's `axis_evaluation` READ/EXECUTE/CRITERIA/CITATION section is filled (not just declared); for non-axis roles: `recomputation.rule` ties the decision to the named method, not a generic aggregation |
| (c) failure/anti-pattern catalog | Gate B (hollow-instance) | spec/rulebook names specific, domain-real failure modes (not "be careful") — the hollow-instance text #807 already requires for Gate B is the minimum bar; a catalog goes further by naming *multiple* named anti-patterns, not one hollow-instance example |
| (d) senior-practitioner checklist | Gate C (finding method) | the finding method resolves to an enumerable checklist a practitioner would actually run (STRIDE's six-category walk is the existing worked example) |
| (e) canonical sources, no fabricated citations | cross-cutting | every citation resolves to a real, findable source; step 2's per-role work must confirm resolution, not just presence (same discipline `market-analysis`'s evidence-citation rulebook already applies) |

(c) and (d) are net-new relative to #807 — confirmed in
current-state.md's evidence read (0/43 specs, including the 6 already
piloted, carry an `anti_pattern`/`failure_catalog` field).

## 2. Survey of the 37 non-piloted roles against the template

canonical: ad-hoc `python3` read of `roles/specs/*.spec.json` this
session (current-state.md "Evidence read this session").

```
derived: python3 -c "
import json, glob
axis = []
for f in sorted(glob.glob('roles/specs/*.spec.json')):
    d = json.load(open(f))
    if 'axis_evaluation' in json.dumps(d):
        axis.append(f)
print(len(axis))
for a in axis: print(a)
"
2
roles/specs/architecture.spec.json
roles/specs/security-threat-model.spec.json
```

All 37 non-piloted roles pass part (a)'s citation half (43/43 carry
`source_standard`, current-state.md) but fail the routing half — no
spec text states when the named method applies vs. does not (checked by
absence of "when"/"route"/circumstance language tied to
`source_standard` in every non-piloted file read this session). All 37
fail (b) (only `architecture` and `security-threat-model` — both
piloted — carry `axis_evaluation`, and neither's section is filled per
#807 step-2 §1). All 37 fail (c) and (d) (current-state.md: 0 carry
`hollow`/`finding_method`/`anti_pattern`/`failure_catalog` outside the
6-role pilot). All 37 are ungraded on (e)'s resolution check (no
citation-resolution pass has run against any of the 37 this session or
in #807).

No role in the 37 met the full template; none is claimed N/A without
running #807 step-1 §4's mechanical N/A test first (deferred to step 2
per role, same as #807 itself deferred it).

## 3. Prioritization (reusing #807 step-1 §2, extended)

#807 step-1 §2 already ranked the 6 piloted roles priority-1/1/1/1/2/3
against northpole reqs #1/#3/#5 and named "remaining 35" as priority-3,
deferred to "step 2's normal per-cluster sweep." #992 IS that per-cluster
sweep. Reusing #807's reasoning (failure-propagation through the
harness's own measurement chain, and axis-owner status) rather than
re-deriving a fresh ranking from scratch:

RICE scoring (Reach = roles whose thin rulebook could corrupt another
role's measurement or gate a shared mechanism; Impact = 1-3 vs
northpole req severity; Confidence = 1.0 where #807's failure-mode
reasoning directly transfers, 0.7 where inferred by analogy; Effort =
roughly template-parts-missing × spec complexity, 1-3):

| Cluster | Roles | Reach | Impact | Confidence | Effort | RICE | Reasoning |
|---|---|---|---|---|---|---|---|
| A — axis owners (unfinished #807 debt) | conformance-review, capacity-planning, performance-engineering | 3 | 3 | 1.0 | 2 | 4.5 | `axis_evaluation` is a shared mechanism (`docs/handbooks/architecture-methodology.md`) already 2/5 filled (architecture, security-threat-model, both piloted); leaving 3/5 axis owners unfilled means the shared mechanism itself is inconsistently exercised, propagating to every future axis-owning role add |
| B — requirements/risk fan-out | requirements-engineering, risk-management | 2 | 3 | 1.0 | 2 | 3.0 | #807 step-1 §2 named both priority-1/2 directly ("every other role's 'is this done' call is downstream," "findings feed multiple downstream roles") but left them unaudited pending this sweep |
| C — standards-body roles (formal external standard, high Gate-A confidence, cheap to route+checklist) | accessibility, secure-coding, legal-compliance, localization, api-design | 2 | 2 | 1.0 | 2 | 2.0 | formal standards (WCAG-EM, OWASP ASVS, GDPR Art.35, CLDR/UTS#35, OpenAPI/Spectral) make part (a) routing and (d) checklists directly extractable from the standard's own structure — lowest-effort-per-template-part cluster |
| D — named-practitioner-framework roles | market-analysis, marketing, sales, pricing, growth-analytics, user-discovery | 2 | 2 | 0.7 | 2 | 1.4 | frameworks exist (Porter, Dunford, MEDDPICC, Van Westendorp, AARRR, Torres) but confidence is lower — these depend more on judgment application than mechanical standard-following, so template fit is less certain until step 2 actually drafts one |
| E — engineering-discipline roles (remaining) | data-modeling, data-engineering, observability, ml-engineering, refactoring-legacy, technical-feasibility, release-engineering, implementation | 3 | 2 | 0.8 | 3 | 1.6 | canonical texts exist (Kimball, dbt, OpenTelemetry, Model Cards, Fowler) but this cluster is largest and most heterogeneous — split into per-role sub-tasks in step 2 rather than one PR |
| F — remaining (customer-facing, process, comms) | customer-support, content-design, technical-writing, devrel, pr-communications, interaction-design, ux-engineering, brand-design, knowledge-management, issue-retrospective, incident-response, partnerships-bd, finance-unit-economics | 1 | 1 | 0.7 | 3 | 0.23 | lowest northpole-req fan-out per #807's own reasoning (no direct load-bearing link named); deepen last |

Reach/Impact/Confidence/Effort are this session's estimates, not a
measured RICE input (no interview/observation count exists for an
internal-tooling prioritization call) — flagged per this role's own
evidence-admissibility rule rather than presented as measured data.

## 4. Phased deepening plan

- **Phase A** (cluster A + B, 5 roles): fill the 3 remaining
  `axis_evaluation` sections + requirements-engineering/risk-management's
  full 5-part template. Smallest role count, highest RICE, directly
  closes #807's own left-open debt.
- **Phase B** (cluster C, 5 roles): standards-body roles, template
  extraction is mechanical from the standard's own structure.
- **Phase C** (cluster D + E, 14 roles): split per role or small
  sub-groups in step 2 given lower confidence / larger heterogeneity.
- **Phase D** (cluster F, 13 roles): remaining roles, lowest measured
  fan-out.

Each phase is its own PR (or small PR set), gated the same way #807
step-2→step-3 was: phase N does not start until phase N-1's live-fire
verification (§5) is recorded.

## 5. Live-fire verification design

Per issue's Acceptance: "a seeded domain task where the strengthened
rulebook demonstrably changes the role's judgment/output vs before."

**Hypothesis package (pre-registered, per this role's own
hypothesis-testing methodology, fixed before any run)**:
- **Metric**: verdict divergence — does the role's stated verdict on a
  seeded task differ between the pre-deepening spec and the
  post-deepening spec, on a task constructed so a real practitioner
  applying the named methodology would reach a DIFFERENT verdict than a
  generic-reasoning pass would?
- **Threshold**: at least 1 of N seeded tasks per role (N=2 minimum,
  one per Gate-B hollow-instance case and one per Gate-C
  finding-method case) shows divergence, AND the post-deepening verdict
  matches the methodology-correct answer (graded by an independent
  same-domain agent per #807 step-1 §3's signal-#8 mechanism —
  independent-verdict-first, not primed by the producing role's
  reasoning trail).
- **Decision rule**: divergence + methodology-correct on the
  post-deepening side → the deepening is load-bearing, promote the
  cluster's edits; no divergence → the spec change was decorative for
  that role, and the finding routes back to step 2 as a per-role defect
  (the template fill did not touch the actual decision path), not a
  pass.
- **Guardrail metric** (must not move adversarially): pre-deepening
  spec's existing passing checks (`gates/role_spec_shape.py`,
  `record_lint.py`) stay green post-deepening — a template fill that
  breaks the machine-checked shape contract is a regression regardless
  of verdict-divergence outcome.
- **ITWWS follow-up** (pre-committed): if Phase A's live-fire confirms
  divergence, Phase B-D proceed on the same design without re-registering
  per phase; if Phase A shows no divergence on any of its 5 roles, stop
  and escalate the template itself (§1) as the defect, not individual
  role content, before spending effort on Phase B-D.

**Concrete seed-task shape** (worked example, requirements-engineering,
cluster B): construct a repo state with a requirement whose acceptance
criteria are internally ambiguous (two readings, only one closeable by
EARS's own disambiguation pattern per #807-cited IEEE RE'09 source).
Pre-deepening spec: role likely picks either reading generically.
Post-deepening spec (EARS routing filled): role's `recomputation.rule`
should force the EARS-pattern reading. Divergence + correctness against
the EARS-pattern reading is the pass signal.

## Out of scope

- Editing any `roles/*.json`, `roles/specs/*.spec.json`, or rulebook-repo
  content (this is phase 1; a build-now or approved phase 2 does the
  edits per phase).
- Re-grading the 6 already-piloted roles (#807/#926/#935's own scope).
- Building signal #8's actual grading-agent code (named in #807 step-1
  §3, still unbuilt; this proposal reuses its design for live-fire, does
  not implement it).
- Auditing rulebook-repo prose directly (inaccessible this session,
  current-state.md).

## Acceptance

- §1 states a 5-part template composing with #807's Gate A/B/C rather
  than replacing it.
- §2 grades all 37 non-piloted roles against the template with cited
  evidence (derived: command output), not assertion.
- §3 reuses #807's own priority reasoning and extends it with an RICE
  table covering all 37, each row's Reach/Impact/Confidence/Effort
  justified in prose.
- §4 phases the 37 into ordered clusters with a stated gate between
  phases.
- §5 gives a live-fire design that is a genuine pre-registered
  hypothesis (named metric, threshold, decision rule, guardrail metric,
  ITWWS follow-up) per this role's own methodology, not a restated goal.

## Accumulation

This proposal adds no code. It commits a follow-up (build-now or
approved phase 2) to editing, per phase: 3 `axis_evaluation` sections in
`docs/handbooks/architecture-methodology.md`-linked spec files (Phase A),
and 34 more `roles/specs/*.spec.json` files (+ their paired rulebook
repos, out-of-tree) across Phases A-D, plus the live-fire seed-task
fixtures and independent-grading-agent scaffolding §5 requires for at
least the Phase A pilot (5 roles × 2 seed tasks = 10 fixtures minimum).
No standing maintenance burden is created by this proposal itself; the
per-phase edits do create a standing maintenance surface (every future
new role must fill the same 5-part template), which is inherent to the
issue's own ask, not an avoidable side effect of this scoping step.

## What did not work

None.
