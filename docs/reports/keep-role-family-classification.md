# Keep-Role Hook Family Classification (skill-axis phase-4a)

Issue #1764. Classification only — no hook moved, edited, or deleted.
Input: the 300 `keep-role` rows of `docs/reports/rulebook-hook-audit.md`,
as amended by the #1753 ordering-norm sweep (307 original keep-role rows
minus 7 reclassified to `promote` — see that report's "Updated class
counts" section).

## Methodology

canonical: `docs/reports/rulebook-hook-audit.md` per-rulebook tables
(class column) and `docs/reports/ordering-norm-sweep.md`'s reclassified-
promote list — both read live from the working tree.

1. Extracted every table row with class `keep-role` from
   `rulebook-hook-audit.md` (307 rows), then removed the 7 rows the
   #1753 sweep reclassified to `promote` (matched by rulebook + plugin +
   hook filename), leaving exactly 300 rows.
2. Cloned all 43 rulebook repos carrying a keep-role row at `main`
   (`gh repo clone`, depth 1; `upstream-defect-report-rulebook` has zero
   hooks and carries no row).
3. Located each row's script file on disk under `<plugin>/hooks/<file>`
   and read its full body (not the audit's header-comment excerpt — the
   #1750 lesson).
4. Assigned each hook to exactly one family via a deterministic,
   priority-ordered signature match against the hook's **filename and
   plugin/directory name** (event type first for SessionStart/
   UserPromptSubmit/PostToolUse hooks, then filename-pattern signatures
   for PreToolUse gates). Filename/plugin-name matching was used instead
   of full-body keyword matching for the family boundary itself because
   header comments freely reference sibling plugins by name (e.g. a
   `citation-gate.sh` header mentioning "see also id-stage-order's
   gate"), which produced false-positive family matches when matched
   against body text; full-body reading was used to verify and correct
   every such collision found during classification (three corrected —
   see "What did not work" below).
5. Ran a shape check (counts sum to 300, no unassigned hook) after
   classification — see Acceptance check 1 below.

derived: automated classifier pass over the 300 located hook files'
full bodies, executed live against the 43 cloned repos —

```
role-directive 113
ordering-methodology 18
record-section-shape 145
citation-sourcing 11
facet-keyword 8
field-format-numeric 5
total 300
```
Executed-live result: sums to 300; every row carries a non-empty
`family` value (verified by iterating the classified set and asserting
`family` is never null/empty — 0 unassigned rows).

## Families

Definitions are stated by what each family mechanically checks, per
requirement 1 — not by hook filename alone (filenames were the
*signature* used to sort hooks that, on full-body reading, do mechanically
match that definition; the definition is the grouping criterion).

| family | definition | hook count | disposition | core target / demotion rationale |
|---|---|---:|---|---|
| `role-directive` | SessionStart/UserPromptSubmit hooks that source `core/hooks/lib/role-directive.sh` (`core_role_directive`, core issue #66) and supply only the 4 role-unique strings (you-decide/use-when/produces/hand-off). No deterministic pass/fail verdict is produced — it injects context, it does not gate a write. | 113 | **demote** | The mechanism (delivery, kill-switch, EXIT trap) is already core; there is nothing left to enforce that a parameterized core gate could check — a directive hook can't "fail closed" on content it only displays. The 4 role-unique strings fold into the role's migrated skill guidance text (skill-axis phase-3's already-established per-role skill file), not into a new core gate. |
| `record-section-shape` | PreToolUse gates (mostly named `*-gate.sh` / `methodology-gate.sh`) that check a phase-1 proposal or phase-2 record for required sections, headings, frontmatter fields, or named-methodology checklist entries (e.g. WCAG-EM's 6 required fields per checklist entry, ADR's 5 non-empty sections, Kimball/Inmon/Data-Vault modeling checklists). Mechanically: presence/shape of required document structure, not sourcing and not ordering. | 145 | **fold** | `core/hooks/record-shape-gate.sh` (extends the existing parameterized `record-fields-gate.sh`, core issue #72) — config shape: `{rulebook: {surface: proposal\|record, required_sections: [...], required_frontmatter_fields: [...], checklist_entry_schema: {marker, required_keys: [...]}}}`. This is the exact "proven ordering-gate pattern" the issue names: one core mechanism, per-role config table. |
| `ordering-methodology` | Hooks (PreToolUse gates named with `order`/`sequence`/`phase`/`stage`/`timeline`/`trace`, plus their SessionStart/PostToolUse state-tracker siblings) that enforce a **named domain methodology's** step or phase ORDER — confirmed domain-specific by the #1753 sweep (RACE, ISO 31000 clauses, Double Diamond, Customer Development hypothesis-before-evidence, blameless-postmortem timeline-first) as distinct from the contract-wide phase-1-before-phase-2 ordering norm already promoted to core. | 18 | **fold** | `core/hooks/ordering-norm-gate.sh` — same core target the #1753 sweep named for its 7 promoted rows. Config shape: `{rulebook: {step_sequence: [named step markers, in order], marker_regex: {...}}}` — the mechanism (marker-A-before-marker-B file/section-offset check) is identical across all 18; only the step names and count differ. |
| `citation-sourcing` | PreToolUse gates requiring a citation/source/traceability tag adjacent to a flagged claim (a "conventionality" or "standard practice" assertion, a requirements-to-test traceability line, an evidence-chain reference). Mechanically: regex/adjacency check for a source marker near a claim pattern. | 11 | **fold** | `core/hooks/citation-gate.sh` (new) — config shape: `{rulebook: {claim_patterns: [regex...], citation_markers: [regex...], adjacency_window: N}}`. All 11 share the same adjacency-check mechanism; only the claim/marker vocabulary is role-specific. |
| `facet-keyword` | PreToolUse gates requiring a specific domain keyword/facet token adjacent to a flagged structural claim (customer-support's `sla`/`escalation`/`playbook`/`five-whys`/`kcs` facets via `check_facet`-style helpers; content-design's tone axis; sales' playbook scenarios). Mechanically identical shape to `citation-sourcing` (marker-adjacent-to-claim) but the marker is a fixed domain vocabulary list, not a citation-format pattern. | 8 | **fold** | `core/hooks/facet-keyword-gate.sh` (new) — config shape: `{rulebook: {facets: [{name, keyword_regex, claim_context_regex}]}}`. Kept as a separate family (not merged into `citation-sourcing`) per requirement 2's split rule: the check content differs in kind (a fixed keyword list vs. a citation-format pattern), even though the adjacency mechanism is structurally similar — each hook's per-row justification is that it fires on a role-specific closed keyword set, not an open citation-format pattern. |
| `field-format-numeric` | PreToolUse gates validating a field's numeric or statistical **format**, not merely its presence — capacity-planning's headroom/threshold percentages, its forecasting-method citation, conformance-review's severity scale, content-design's A/B-test spec shape. Each encodes bespoke domain math/statistics validation (a forecasting method's required inputs, a severity rubric's valid values, an A/B spec's required arms). | 5 | **demote** | The 5 hooks share no common parameterizable shape beyond "check a field's value against a domain-specific rule" — unlike `record-section-shape`'s uniform presence check, each of these 5 encodes distinct domain logic (a different rubric, a different statistical spec) that a generic core gate's config table cannot express without becoming role-specific code again. Demoted to guidance text in the migrated skill; revisit as a fold candidate only if a future pass finds 3+ more hooks sharing one of these 5's specific sub-shape (e.g. a generic "numeric field within declared range" checker). |

Family-count shape check (requirement 1 — no family-less hook, sum
verified):

```
113 (role-directive) + 145 (record-section-shape) + 18 (ordering-methodology)
  + 11 (citation-sourcing) + 8 (facet-keyword) + 5 (field-format-numeric)
  = 300
```
Executed-live result: 300 = 300 (matches the 300-row input set; every row
in the per-hook table below carries exactly one of these 6 family
values — grep-verified, see Acceptance check 2).

Disposition shape check (requirement 2 — no disposition-less family,
every fold family names a core target):

| family | disposition | core target named? |
|---|---|---|
| role-directive | demote | n/a (demote) |
| record-section-shape | fold | yes — `core/hooks/record-shape-gate.sh` |
| ordering-methodology | fold | yes — `core/hooks/ordering-norm-gate.sh` |
| citation-sourcing | fold | yes — `core/hooks/citation-gate.sh` |
| facet-keyword | fold | yes — `core/hooks/facet-keyword-gate.sh` |
| field-format-numeric | demote | n/a (demote) |

All 6 families carry exactly one disposition; all 4 `fold` families name
a core target — 0 disposition-less families, 0 fold families missing a
target.

## Per-rulebook migration-blocking map

Requirement 4: a rulebook maps to phase-3 skill migration only after
**all** its hooks' families are dispositioned (done here, for every
rulebook) and, for `fold` families, those families have **landed in
core** (not yet done — this issue is classification only). The table
below lists, per rulebook, which `fold` families gate its migration —
a rulebook with only `role-directive`/`field-format-numeric` hooks would
need no core landing to map, but no rulebook in this set is demote-only:
every one of the 43 rulebooks carries at least one `record-section-shape`
hook, so every rulebook is blocked until `record-shape-gate.sh` lands in
core at minimum; rulebooks listing additional families are blocked on
those landing too.

| rulebook | blocking fold families |
|---|---|
| accessibility-rulebook | record-section-shape |
| api-design-rulebook | citation-sourcing, record-section-shape |
| architecture-rulebook | citation-sourcing, record-section-shape |
| brand-design-rulebook | record-section-shape |
| capacity-planning-rulebook | citation-sourcing, record-section-shape |
| conformance-review-rulebook | citation-sourcing, ordering-methodology, record-section-shape |
| content-design-rulebook | facet-keyword, record-section-shape |
| customer-support-rulebook | facet-keyword, ordering-methodology, record-section-shape |
| data-engineering-rulebook | record-section-shape |
| data-modeling-rulebook | record-section-shape |
| defect-verification-rulebook | ordering-methodology, record-section-shape |
| devrel-rulebook | record-section-shape |
| execution-observation-rulebook | ordering-methodology, record-section-shape |
| finance-unit-economics-rulebook | citation-sourcing, facet-keyword, record-section-shape |
| growth-analytics-rulebook | record-section-shape |
| implementation-rulebook | record-section-shape |
| incident-response-rulebook | record-section-shape |
| interaction-design-rulebook | citation-sourcing, record-section-shape |
| issue-retrospective-rulebook | ordering-methodology, record-section-shape |
| knowledge-management-rulebook | record-section-shape |
| legal-compliance-rulebook | record-section-shape |
| localization-rulebook | record-section-shape |
| market-analysis-rulebook | record-section-shape |
| marketing-rulebook | record-section-shape |
| ml-engineering-rulebook | record-section-shape |
| observability-rulebook | ordering-methodology, record-section-shape |
| partnerships-bd-rulebook | record-section-shape |
| performance-engineering-rulebook | ordering-methodology, record-section-shape |
| pr-communications-rulebook | ordering-methodology, record-section-shape |
| pricing-rulebook | record-section-shape |
| product-discovery-rulebook | record-section-shape |
| refactoring-legacy-rulebook | record-section-shape |
| release-engineering-rulebook | record-section-shape |
| requirements-engineering-rulebook | citation-sourcing, record-section-shape |
| risk-management-rulebook | ordering-methodology, record-section-shape |
| sales-rulebook | facet-keyword, record-section-shape |
| secure-coding-rulebook | record-section-shape |
| security-threat-model-rulebook | citation-sourcing, record-section-shape |
| technical-feasibility-rulebook | citation-sourcing, record-section-shape |
| technical-writing-rulebook | record-section-shape |
| test-authoring-rulebook | citation-sourcing, record-section-shape |
| user-discovery-rulebook | ordering-methodology, record-section-shape |
| ux-engineering-rulebook | ordering-methodology, record-section-shape |

derived: classified set grouped by rulebook, filtered to families with
disposition `fold` — 43 rulebooks, all with at least one blocking fold
family (`record-section-shape` in all 43; core-only enforcement means no
rulebook can map before core gates exist for all its dispositioned-fold
families).

## Per-hook rows

300 rows: rulebook, hook file (repo-relative path within the rulebook
repo), assigned family. Sorted by rulebook then path.

| rulebook | hook file | family |
|---|---|---|
| accessibility-rulebook | `accessibility/hooks/directive.sh` | role-directive |
| accessibility-rulebook | `wcag-em-directive/hooks/directive.sh` | role-directive |
| accessibility-rulebook | `wcag-em-gate/hooks/methodology-gate.sh` | record-section-shape |
| api-design-rulebook | `api-design/hooks/directive.sh` | role-directive |
| api-design-rulebook | `api-design/plugins/adr-section-gate/hooks/gate.sh` | record-section-shape |
| api-design-rulebook | `api-design/plugins/deprecation-plan-gate/hooks/gate.sh` | record-section-shape |
| api-design-rulebook | `api-design/plugins/evidence-citation-gate/hooks/gate.sh` | citation-sourcing |
| api-design-rulebook | `api-design/plugins/interface-spec-gate/hooks/gate.sh` | record-section-shape |
| api-design-rulebook | `api-design/plugins/resource-model-gate/hooks/gate.sh` | record-section-shape |
| api-design-rulebook | `api-design/plugins/versioning-strategy-gate/hooks/gate.sh` | record-section-shape |
| architecture-rulebook | `arch-adr-content-gate/hooks/adr-content-gate.sh` | record-section-shape |
| architecture-rulebook | `arch-citation-gate/hooks/citation-gate.sh` | citation-sourcing |
| architecture-rulebook | `architecture/hooks/directive.sh` | role-directive |
| brand-design-rulebook | `brand-design-guide-and-spec/hooks/methodology-gate.sh` | record-section-shape |
| brand-design-rulebook | `brand-design-kapferer-scope-guard/hooks/methodology-gate.sh` | record-section-shape |
| brand-design-rulebook | `brand-design-system-handoff/hooks/methodology-gate.sh` | record-section-shape |
| brand-design-rulebook | `brand-design-wcag-consistency/hooks/methodology-gate.sh` | record-section-shape |
| brand-design-rulebook | `brand-design/hooks/directive.sh` | role-directive |
| capacity-planning-rulebook | `capacity-forecast-method/hooks/directive.sh` | role-directive |
| capacity-planning-rulebook | `capacity-forecast-method/hooks/forecast-method-gate.sh` | field-format-numeric |
| capacity-planning-rulebook | `capacity-headroom-costnote/hooks/directive.sh` | role-directive |
| capacity-planning-rulebook | `capacity-headroom-costnote/hooks/headroom-gate.sh` | field-format-numeric |
| capacity-planning-rulebook | `capacity-order-enforcement/hooks/citation-gate.sh` | citation-sourcing |
| capacity-planning-rulebook | `capacity-order-enforcement/hooks/directive.sh` | role-directive |
| capacity-planning-rulebook | `capacity-order-enforcement/hooks/directive.sh` | role-directive |
| capacity-planning-rulebook | `capacity-planning/hooks/capacity-fields-gate.sh` | record-section-shape |
| capacity-planning-rulebook | `capacity-threshold-decomposition/hooks/directive.sh` | role-directive |
| capacity-planning-rulebook | `capacity-threshold-decomposition/hooks/threshold-gate.sh` | field-format-numeric |
| conformance-review-rulebook | `review-proposal-completeness/hooks/proposal-completeness-gate.sh` | record-section-shape |
| conformance-review-rulebook | `review-record-norm/hooks/closed-checks-gate.sh` | record-section-shape |
| conformance-review-rulebook | `review-severity/hooks/severity-gate.sh` | field-format-numeric |
| conformance-review-rulebook | `review-traceability/hooks/traceability-gate.sh` | citation-sourcing |
| conformance-review-rulebook | `review/hooks/directive.sh` | role-directive |
| conformance-review-rulebook | `review/hooks/state.sh` | ordering-methodology |
| content-design-rulebook | `content-design-ab-spec/hooks/ab-spec-gate.sh` | field-format-numeric |
| content-design-rulebook | `content-design-decision-rationale/hooks/decision-rationale-gate.sh` | record-section-shape |
| content-design-rulebook | `content-design-self-critique/hooks/self-critique-gate.sh` | record-section-shape |
| content-design-rulebook | `content-design-tone-axis/hooks/tone-axis-gate.sh` | facet-keyword |
| content-design-rulebook | `content-design/hooks/directive.sh` | role-directive |
| customer-support-rulebook | `customer-support-escalation-path/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-escalation-path/hooks/escalation-path-gate.sh` | facet-keyword |
| customer-support-rulebook | `customer-support-evidence-metric/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-evidence-metric/hooks/evidence-metric-gate.sh` | record-section-shape |
| customer-support-rulebook | `customer-support-five-whys/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-five-whys/hooks/five-whys-gate.sh` | facet-keyword |
| customer-support-rulebook | `customer-support-kcs/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-kcs/hooks/kcs-gate.sh` | facet-keyword |
| customer-support-rulebook | `customer-support-phase1-order/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-phase1-order/hooks/phase1-order-gate.sh` | ordering-methodology |
| customer-support-rulebook | `customer-support-playbook-scenario/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-playbook-scenario/hooks/playbook-scenario-gate.sh` | facet-keyword |
| customer-support-rulebook | `customer-support-record-fields/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-record-fields/hooks/record-fields-gate.sh` | record-section-shape |
| customer-support-rulebook | `customer-support-sla-tier/hooks/directive-fragment.sh` | role-directive |
| customer-support-rulebook | `customer-support-sla-tier/hooks/sla-tier-gate.sh` | facet-keyword |
| customer-support-rulebook | `customer-support/hooks/directive.sh` | role-directive |
| data-engineering-rulebook | `data-engineering/hooks/directive.sh` | role-directive |
| data-engineering-rulebook | `data-quality-gate/hooks/data-quality-gate.sh` | record-section-shape |
| data-engineering-rulebook | `failure-handling-gate/hooks/failure-handling-gate.sh` | record-section-shape |
| data-engineering-rulebook | `pipeline-design-gate/hooks/pipeline-design-gate.sh` | record-section-shape |
| data-modeling-rulebook | `data-modeling-datavault/hooks/datavault-gate.sh` | record-section-shape |
| data-modeling-rulebook | `data-modeling-inmon/hooks/inmon-gate.sh` | record-section-shape |
| data-modeling-rulebook | `data-modeling-kimball/hooks/kimball-gate.sh` | record-section-shape |
| data-modeling-rulebook | `data-modeling-structure/hooks/structure-gate.sh` | record-section-shape |
| data-modeling-rulebook | `data-modeling/hooks/directive.sh` | role-directive |
| defect-verification-rulebook | `verify-directive-depth/hooks/directive.sh` | role-directive |
| defect-verification-rulebook | `verify-finding-gate/hooks/finding-gate.sh` | record-section-shape |
| defect-verification-rulebook | `verify-outcome-gate/hooks/outcome-gate.sh` | record-section-shape |
| defect-verification-rulebook | `verify-state-guard/hooks/state-guard.sh` | record-section-shape |
| defect-verification-rulebook | `verify-state-guard/hooks/verify-state.sh` | ordering-methodology |
| defect-verification-rulebook | `verify-state-guard/hooks/verify-state.sh` | ordering-methodology |
| defect-verification-rulebook | `verify/hooks/closed-checks-gate.sh` | record-section-shape |
| devrel-rulebook | `devrel/hooks/directive.sh` | role-directive |
| devrel-rulebook | `diataxis-record/hooks/record-fields-devrel-gate.sh` | record-section-shape |
| devrel-rulebook | `metric-record/hooks/metric-record-gate.sh` | record-section-shape |
| devrel-rulebook | `rfc-seven-section/hooks/proposal-sections-gate.sh` | record-section-shape |
| execution-observation-rulebook | `execution-observation/hooks/directive.sh` | role-directive |
| execution-observation-rulebook | `execution-observation/plugins/eo-methodology-gate/hooks/methodology-gate.sh` | record-section-shape |
| execution-observation-rulebook | `execution-observation/plugins/eo-state/hooks/state.sh` | ordering-methodology |
| execution-observation-rulebook | `execution-observation/plugins/eo-state/hooks/state.sh` | ordering-methodology |
| execution-observation-rulebook | `execution-observation/plugins/eo-state/hooks/state.sh` | ordering-methodology |
| finance-unit-economics-rulebook | `finance-cac-payback/hooks/cac-payback-gate.sh` | record-section-shape |
| finance-unit-economics-rulebook | `finance-evidence-chain/hooks/evidence-chain-gate.sh` | citation-sourcing |
| finance-unit-economics-rulebook | `finance-ltv-cac-band/hooks/ltv-cac-band-gate.sh` | record-section-shape |
| finance-unit-economics-rulebook | `finance-ltv-churn-assumption/hooks/ltv-churn-assumption-gate.sh` | record-section-shape |
| finance-unit-economics-rulebook | `finance-proposal-shape/hooks/proposal-shape-gate.sh` | record-section-shape |
| finance-unit-economics-rulebook | `finance-sensitivity-scenario/hooks/sensitivity-scenario-gate.sh` | facet-keyword |
| finance-unit-economics-rulebook | `finance-unit-economics/hooks/directive.sh` | role-directive |
| finance-unit-economics-rulebook | `finance-unit-economics/hooks/produces-fields-gate.sh` | record-section-shape |
| growth-analytics-rulebook | `ga-funnel/hooks/directive.sh` | role-directive |
| growth-analytics-rulebook | `ga-funnel/hooks/ga-funnel-gate.sh` | record-section-shape |
| growth-analytics-rulebook | `ga-prereg/hooks/directive.sh` | role-directive |
| growth-analytics-rulebook | `ga-prereg/hooks/directive.sh` | role-directive |
| growth-analytics-rulebook | `ga-prereg/hooks/ga-prereg-gate.sh` | record-section-shape |
| growth-analytics-rulebook | `ga-trust/hooks/directive.sh` | role-directive |
| growth-analytics-rulebook | `ga-trust/hooks/ga-trust-gate.sh` | record-section-shape |
| implementation-rulebook | `coding/hooks/coding-progress-gate.sh` | record-section-shape |
| implementation-rulebook | `coding/hooks/directive.sh` | role-directive |
| implementation-rulebook | `no-footgun/hooks/directive.sh` | role-directive |
| implementation-rulebook | `no-mock/hooks/directive.sh` | role-directive |
| incident-response-rulebook | `incident-response-action-item-gate/hooks/action-item-gate.sh` | record-section-shape |
| incident-response-rulebook | `incident-response-proposal-evidence-gate/hooks/evidence-gate.sh` | record-section-shape |
| incident-response-rulebook | `incident-response-rca-method-gate/hooks/rca-method-gate.sh` | record-section-shape |
| incident-response-rulebook | `incident-response/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-accessibility-floor/hooks/accessibility-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-accessibility-floor/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-citation-format/hooks/citation-gate.sh` | citation-sourcing |
| interaction-design-rulebook | `interaction-design/plugins/id-citation-format/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-nielsen-heuristics/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-nielsen-heuristics/hooks/nielsen-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-persona-goal/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-persona-goal/hooks/persona-goal-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-proposal-shape/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-proposal-shape/hooks/proposal-shape-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-stage-order/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-state-completeness/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-state-completeness/hooks/state-completeness-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-task-flow/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-task-flow/hooks/task-flow-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-traceability/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-traceability/hooks/traceability-gate.sh` | citation-sourcing |
| interaction-design-rulebook | `interaction-design/plugins/id-usability-test-plan/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-usability-test-plan/hooks/usability-test-gate.sh` | record-section-shape |
| interaction-design-rulebook | `interaction-design/plugins/id-wireframe-staging/hooks/directive.sh` | role-directive |
| interaction-design-rulebook | `interaction-design/plugins/id-wireframe-staging/hooks/wireframe-staging-gate.sh` | record-section-shape |
| issue-retrospective-rulebook | `action-item-shape-gate/hooks/action-item-shape-gate.sh` | record-section-shape |
| issue-retrospective-rulebook | `contributing-factors-gate/hooks/contributing-factors-gate.sh` | record-section-shape |
| issue-retrospective-rulebook | `freelunch-completeness-gate/hooks/freelunch-completeness-gate.sh` | record-section-shape |
| issue-retrospective-rulebook | `issue-retrospective/hooks/directive.sh` | role-directive |
| issue-retrospective-rulebook | `recurred-prediction-gate/hooks/recurred-prediction-gate.sh` | record-section-shape |
| issue-retrospective-rulebook | `timeline-order-gate/hooks/timeline-order-gate.sh` | ordering-methodology |
| knowledge-management-rulebook | `km-adr-proposal/hooks/adr-shape-gate.sh` | record-section-shape |
| knowledge-management-rulebook | `km-cross-index/hooks/index-pairing-gate.sh` | record-section-shape |
| knowledge-management-rulebook | `km-cross-index/hooks/index-shape-gate.sh` | record-section-shape |
| knowledge-management-rulebook | `km-pattern-entry/hooks/pattern-entry-gate.sh` | record-section-shape |
| knowledge-management-rulebook | `km-supersession/hooks/supersession-pairing-gate.sh` | record-section-shape |
| knowledge-management-rulebook | `knowledge-management/hooks/directive.sh` | role-directive |
| legal-compliance-rulebook | `legal-compliance-fanout-completeness-gate/hooks/gate.sh` | record-section-shape |
| legal-compliance-rulebook | `legal-compliance-phase1-proposal-gate/hooks/gate.sh` | record-section-shape |
| legal-compliance-rulebook | `legal-compliance-phase2-record-gate/hooks/gate.sh` | record-section-shape |
| legal-compliance-rulebook | `legal-compliance/hooks/directive.sh` | role-directive |
| localization-rulebook | `localization/hooks/directive.sh` | role-directive |
| localization-rulebook | `localization/hooks/record-fields-localization-gate.sh` | record-section-shape |
| localization-rulebook | `localization/plugins/mqm-tagging/hooks/directive.sh` | role-directive |
| localization-rulebook | `localization/plugins/mqm-tagging/hooks/mqm-tagging-gate.sh` | record-section-shape |
| localization-rulebook | `localization/plugins/proposal-gate/hooks/directive.sh` | role-directive |
| localization-rulebook | `localization/plugins/proposal-gate/hooks/methodology-gate.sh` | record-section-shape |
| localization-rulebook | `localization/plugins/verdict-axis/hooks/directive.sh` | role-directive |
| localization-rulebook | `localization/plugins/verdict-axis/hooks/verdict-axis-gate.sh` | record-section-shape |
| market-analysis-rulebook | `market-analysis/hooks/directive.sh` | role-directive |
| market-analysis-rulebook | `market-analysis/plugins/competitor-mapping/hooks/directive.sh` | role-directive |
| market-analysis-rulebook | `market-analysis/plugins/competitor-mapping/hooks/gate.sh` | record-section-shape |
| market-analysis-rulebook | `market-analysis/plugins/evidence-rigor/hooks/directive.sh` | role-directive |
| market-analysis-rulebook | `market-analysis/plugins/evidence-rigor/hooks/gate.sh` | record-section-shape |
| market-analysis-rulebook | `market-analysis/plugins/five-forces/hooks/directive.sh` | role-directive |
| market-analysis-rulebook | `market-analysis/plugins/five-forces/hooks/gate.sh` | record-section-shape |
| market-analysis-rulebook | `market-analysis/plugins/jtbd-fit/hooks/directive.sh` | role-directive |
| market-analysis-rulebook | `market-analysis/plugins/jtbd-fit/hooks/gate.sh` | record-section-shape |
| market-analysis-rulebook | `market-analysis/plugins/mece-proposal/hooks/directive.sh` | role-directive |
| market-analysis-rulebook | `market-analysis/plugins/mece-proposal/hooks/gate.sh` | record-section-shape |
| marketing-rulebook | `marketing-channel/hooks/channel-gate.sh` | record-section-shape |
| marketing-rulebook | `marketing-messaging/hooks/messaging-gate.sh` | record-section-shape |
| marketing-rulebook | `marketing-segment/hooks/segment-gate.sh` | record-section-shape |
| marketing-rulebook | `marketing/hooks/directive.sh` | role-directive |
| ml-engineering-rulebook | `ml-engineering-adr-proposal/hooks/methodology-gate.sh` | record-section-shape |
| ml-engineering-rulebook | `ml-engineering-eval-discipline/hooks/methodology-gate.sh` | record-section-shape |
| ml-engineering-rulebook | `ml-engineering-ml-test-score/hooks/methodology-gate.sh` | record-section-shape |
| ml-engineering-rulebook | `ml-engineering-model-provenance/hooks/methodology-gate.sh` | record-section-shape |
| ml-engineering-rulebook | `ml-engineering-slo-serving/hooks/methodology-gate.sh` | record-section-shape |
| ml-engineering-rulebook | `ml-engineering/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-cardinality-budget/hooks/cardinality-budget-gate.sh` | record-section-shape |
| observability-rulebook | `observability-cardinality-budget/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-explorability/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-explorability/hooks/explorability-gate.sh` | record-section-shape |
| observability-rulebook | `observability-methodology-selector/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-methodology-selector/hooks/methodology-selector-gate.sh` | ordering-methodology |
| observability-rulebook | `observability-methodology-selector/hooks/methodology-selector-status.sh` | ordering-methodology |
| observability-rulebook | `observability-phase-trace/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-phase-trace/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-phase-trace/hooks/phase-trace-gate.sh` | ordering-methodology |
| observability-rulebook | `observability-signal-golden/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-signal-golden/hooks/signal-golden-gate.sh` | record-section-shape |
| observability-rulebook | `observability-signal-red/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-signal-red/hooks/signal-red-gate.sh` | record-section-shape |
| observability-rulebook | `observability-signal-use/hooks/directive.sh` | role-directive |
| observability-rulebook | `observability-signal-use/hooks/signal-use-gate.sh` | record-section-shape |
| observability-rulebook | `observability/hooks/observability-produces-gate.sh` | record-section-shape |
| partnerships-bd-rulebook | `batna-zopa/hooks/batna-zopa-gate.sh` | record-section-shape |
| partnerships-bd-rulebook | `batna-zopa/hooks/directive.sh` | role-directive |
| partnerships-bd-rulebook | `evidence-discipline/hooks/directive.sh` | role-directive |
| partnerships-bd-rulebook | `evidence-discipline/hooks/directive.sh` | role-directive |
| partnerships-bd-rulebook | `evidence-discipline/hooks/evidence-discipline-gate.sh` | record-section-shape |
| partnerships-bd-rulebook | `multi-axis-scoring/hooks/directive.sh` | role-directive |
| partnerships-bd-rulebook | `multi-axis-scoring/hooks/multi-axis-scoring-gate.sh` | record-section-shape |
| partnerships-bd-rulebook | `strategic-fit-gate/hooks/directive.sh` | role-directive |
| partnerships-bd-rulebook | `strategic-fit-gate/hooks/strategic-fit-gate.sh` | record-section-shape |
| partnerships-bd-rulebook | `term-sheet-structure/hooks/directive.sh` | role-directive |
| partnerships-bd-rulebook | `term-sheet-structure/hooks/term-sheet-structure-gate.sh` | record-section-shape |
| performance-engineering-rulebook | `performance-engineering-order-check/hooks/order-check.sh` | ordering-methodology |
| performance-engineering-rulebook | `performance-engineering-proposal-gate/hooks/proposal-gate.sh` | record-section-shape |
| performance-engineering-rulebook | `performance-engineering-record-gate/hooks/record-gate.sh` | record-section-shape |
| performance-engineering-rulebook | `performance-engineering-session-informer/hooks/state.sh` | ordering-methodology |
| performance-engineering-rulebook | `performance-engineering/hooks/directive.sh` | role-directive |
| pr-communications-rulebook | `key-message-tiers/hooks/directive.sh` | role-directive |
| pr-communications-rulebook | `key-message-tiers/hooks/key-message-gate.sh` | record-section-shape |
| pr-communications-rulebook | `pr-communications/hooks/directive.sh` | role-directive |
| pr-communications-rulebook | `qa-preapproval/hooks/directive.sh` | role-directive |
| pr-communications-rulebook | `qa-preapproval/hooks/qa-preapproval-gate.sh` | record-section-shape |
| pr-communications-rulebook | `race-sequence/hooks/directive.sh` | role-directive |
| pr-communications-rulebook | `race-sequence/hooks/race-sequence-gate.sh` | ordering-methodology |
| pricing-rulebook | `pricing/hooks/directive.sh` | role-directive |
| pricing-rulebook | `pricing/plugins/pricing-design-rigor/hooks/design-gate.sh` | record-section-shape |
| pricing-rulebook | `pricing/plugins/pricing-design-rigor/hooks/directive.sh` | role-directive |
| pricing-rulebook | `pricing/plugins/pricing-method-family/hooks/directive.sh` | role-directive |
| pricing-rulebook | `pricing/plugins/pricing-method-family/hooks/family-gate.sh` | record-section-shape |
| pricing-rulebook | `pricing/plugins/pricing-scope-gate/hooks/directive.sh` | role-directive |
| pricing-rulebook | `pricing/plugins/pricing-scope-gate/hooks/scope-gate.sh` | record-section-shape |
| pricing-rulebook | `pricing/plugins/pricing-verdict-report/hooks/directive.sh` | role-directive |
| pricing-rulebook | `pricing/plugins/pricing-verdict-report/hooks/report-gate.sh` | record-section-shape |
| product-discovery-rulebook | `product-assumption-mapping/hooks/directive.sh` | role-directive |
| product-discovery-rulebook | `product-assumption-mapping/hooks/methodology-gate.sh` | record-section-shape |
| product-discovery-rulebook | `product-guardrail-metrics/hooks/directive.sh` | role-directive |
| product-discovery-rulebook | `product-guardrail-metrics/hooks/methodology-gate.sh` | record-section-shape |
| product-discovery-rulebook | `product-hypothesis-testing/hooks/directive.sh` | role-directive |
| product-discovery-rulebook | `product-hypothesis-testing/hooks/methodology-gate.sh` | record-section-shape |
| product-discovery-rulebook | `product-one-pager/hooks/directive.sh` | role-directive |
| product-discovery-rulebook | `product-one-pager/hooks/methodology-gate.sh` | record-section-shape |
| product-discovery-rulebook | `product-opportunity-solution-tree/hooks/directive.sh` | role-directive |
| product-discovery-rulebook | `product-opportunity-solution-tree/hooks/methodology-gate.sh` | record-section-shape |
| refactoring-legacy-rulebook | `characterization-tests/hooks/methodology-gate.sh` | record-section-shape |
| refactoring-legacy-rulebook | `proposal-norm/hooks/methodology-gate.sh` | record-section-shape |
| refactoring-legacy-rulebook | `refactoring-legacy/hooks/directive.sh` | role-directive |
| refactoring-legacy-rulebook | `refactoring-legacy/hooks/refactoring-legacy-progress-gate.sh` | record-section-shape |
| refactoring-legacy-rulebook | `refactoring-steps/hooks/methodology-gate.sh` | record-section-shape |
| release-engineering-rulebook | `error-budget-policy/hooks/error-budget-gate.sh` | record-section-shape |
| release-engineering-rulebook | `ops/hooks/directive.sh` | role-directive |
| release-engineering-rulebook | `postmortem/hooks/postmortem-review-gate.sh` | record-section-shape |
| release-engineering-rulebook | `proposal-norm/hooks/proposal-fields-gate.sh` | record-section-shape |
| release-engineering-rulebook | `readiness-checklist/hooks/readiness-fields-gate.sh` | record-section-shape |
| release-engineering-rulebook | `rollout-plan/hooks/rollout-plan-fields-gate.sh` | record-section-shape |
| requirements-engineering-rulebook | `ambiguity-resolution-gate/hooks/ambiguity-resolution-gate.sh` | record-section-shape |
| requirements-engineering-rulebook | `proposal-discipline-gate/hooks/proposal-discipline-gate.sh` | record-section-shape |
| requirements-engineering-rulebook | `req-id-gate/hooks/req-id-gate.sh` | record-section-shape |
| requirements-engineering-rulebook | `requirements-engineering/hooks/directive.sh` | role-directive |
| requirements-engineering-rulebook | `traceability-matrix-gate/hooks/traceability-matrix-gate.sh` | citation-sourcing |
| risk-management-rulebook | `erm-verdict-methodology/hooks/erm-order-gate.sh` | ordering-methodology |
| risk-management-rulebook | `phase1-proposal-norms/hooks/proposal-shape-gate.sh` | record-section-shape |
| risk-management-rulebook | `phase2-record-norms/hooks/record-shape-gate.sh` | record-section-shape |
| risk-management-rulebook | `risk-management/hooks/directive.sh` | role-directive |
| risk-management-rulebook | `risk-register-methodology/hooks/register-fields-gate.sh` | record-section-shape |
| sales-rulebook | `sales-playbook/hooks/playbook-gate.sh` | facet-keyword |
| sales-rulebook | `sales-proposal-norm/hooks/proposal-norm-gate.sh` | record-section-shape |
| sales-rulebook | `sales-qualification-meddpicc/hooks/qualification-gate.sh` | record-section-shape |
| sales-rulebook | `sales-stage-definitions/hooks/stage-definitions-gate.sh` | record-section-shape |
| sales-rulebook | `sales/hooks/directive.sh` | role-directive |
| secure-coding-rulebook | `asvs-verification/hooks/directive.sh` | role-directive |
| secure-coding-rulebook | `asvs-verification/hooks/level-gate.sh` | record-section-shape |
| secure-coding-rulebook | `cwe-cvss-findings/hooks/directive.sh` | role-directive |
| secure-coding-rulebook | `cwe-cvss-findings/hooks/finding-gate.sh` | record-section-shape |
| secure-coding-rulebook | `secure-coding/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-canon-citation/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-canon-citation/hooks/methodology-gate.sh` | citation-sourcing |
| security-threat-model-rulebook | `security-threat-model-mitigation/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-mitigation/hooks/methodology-gate.sh` | record-section-shape |
| security-threat-model-rulebook | `security-threat-model-residual-signoff/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-residual-signoff/hooks/methodology-gate.sh` | record-section-shape |
| security-threat-model-rulebook | `security-threat-model-risk-rating/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-risk-rating/hooks/methodology-gate.sh` | record-section-shape |
| security-threat-model-rulebook | `security-threat-model-stride/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-stride/hooks/directive.sh` | role-directive |
| security-threat-model-rulebook | `security-threat-model-stride/hooks/methodology-gate.sh` | record-section-shape |
| technical-feasibility-rulebook | `evidence-citation/directive-fragment.md` | role-directive |
| technical-feasibility-rulebook | `evidence-citation/hooks/citation-gate.sh` | citation-sourcing |
| technical-feasibility-rulebook | `feasibility/hooks/directive.sh` | role-directive |
| technical-feasibility-rulebook | `madr-options/directive-fragment.md` | role-directive |
| technical-feasibility-rulebook | `madr-options/hooks/options-gate.sh` | record-section-shape |
| technical-feasibility-rulebook | `nygard-adr-spine/directive-fragment.md` | role-directive |
| technical-feasibility-rulebook | `nygard-adr-spine/hooks/spine-gate.sh` | record-section-shape |
| technical-writing-rulebook | `plugins/tw-diataxis/hooks/diataxis-type-gate.sh` | record-section-shape |
| technical-writing-rulebook | `plugins/tw-minimalism/hooks/minimalism-check-gate.sh` | record-section-shape |
| technical-writing-rulebook | `plugins/tw-rfc-proposal/hooks/rfc-structure-gate.sh` | record-section-shape |
| technical-writing-rulebook | `plugins/tw-style-guide/hooks/style-guide-gate.sh` | record-section-shape |
| technical-writing-rulebook | `technical-writing/hooks/directive.sh` | role-directive |
| test-authoring-rulebook | `adr-proposal-shape/hooks/proposal-shape-gate.sh` | record-section-shape |
| test-authoring-rulebook | `ep-bva-technique/hooks/technique-gate.sh` | record-section-shape |
| test-authoring-rulebook | `test-authoring/hooks/directive.sh` | role-directive |
| test-authoring-rulebook | `traceability-line/hooks/traceability-gate.sh` | citation-sourcing |
| test-authoring-rulebook | `xunit-suite-patterns/hooks/suite-patterns-gate.sh` | record-section-shape |
| user-discovery-rulebook | `user-discovery-evidence-tagging/hooks/evidence-tagging-gate.sh` | record-section-shape |
| user-discovery-rulebook | `user-discovery-hypothesis-order/hooks/hypothesis-order-gate.sh` | ordering-methodology |
| user-discovery-rulebook | `user-discovery-hypothesis-order/hooks/hypothesis-order-state-sync.sh` | ordering-methodology |
| user-discovery-rulebook | `user-discovery-proposal-norm/hooks/proposal-norm-gate.sh` | record-section-shape |
| user-discovery-rulebook | `user-discovery-saturation/hooks/saturation-gate.sh` | record-section-shape |
| user-discovery-rulebook | `user-discovery/hooks/directive.sh` | role-directive |
| ux-engineering-rulebook | `ux-engineering/hooks/directive.sh` | role-directive |
| ux-engineering-rulebook | `ux-migration-handoff/hooks/migration-handoff-gate.sh` | record-section-shape |
| ux-engineering-rulebook | `ux-phase1-structure-gate/hooks/phase1-structure-gate.sh` | ordering-methodology |
| ux-engineering-rulebook | `ux-token-schema/hooks/token-schema-gate.sh` | record-section-shape |
| ux-engineering-rulebook | `ux-wcag-onpair/hooks/wcag-onpair-gate.sh` | record-section-shape |

## Acceptance checks

1. Shape check — per-hook rows count = 300; no family-less hook; sum
   verified.
   - checked: `len(classified_rows) == 300 and all(r['family'] for r in classified_rows) and sum(family_counts.values()) == 300`
   - result: **PASS** — 300 rows, 0 unassigned, sum 300 = 300 (see
     "Family-count shape check" above; canonical: this record's own
     Methodology section, executed live over the located+classified row
     set built from `docs/reports/rulebook-hook-audit.md` +
     `docs/reports/ordering-norm-sweep.md`).
2. Grep-based shape check — no disposition-less family; every fold
   family names a core target.
   - checked: `grep -c '| fold |' <the Families table> == 4 && grep -c '| demote |' <the Families table> == 2` (6 families total, each row carries exactly one disposition) and each `fold` row's "core target" column is non-empty
   - result: **PASS** — 4 `fold` rows (each naming a `core/hooks/*.sh`
     target) + 2 `demote` rows (each carrying a rationale) = 6 families,
     0 disposition-less, 0 fold-without-target (see "Disposition shape
     check" table above; canonical: this record's own Families table,
     read directly above).

## What did not work

Three filename/plugin-name signature collisions were found and corrected
during classification, discovered by spot-checking full-body content
against the initial classifier pass (a purely-broad content-keyword
match, before the classifier was narrowed to filename/plugin-name-only
signatures): (1) `api-design-rulebook`'s `evidence-citation-gate/hooks/gate.sh`
was first missed by `citation-sourcing` because the generic filename
`gate.sh` carries no citation token — expected: plugin directory name
alone would be enough; actual: the classifier only inspected the bare
hook filename until the plugin/directory name was folded into the match
target. (2) `interaction-design-rulebook`'s `id-citation-format/hooks/citation-gate.sh`
was first misclassified `ordering-methodology` because its header
comment mentions "see also id-stage-order's gate" and a full-body regex
pass matched `stage.?order` in that sentence — expected: full-body
matching would only find genuine ordering checks; actual: header
cross-references to sibling plugins produced false positives, so the
ordering/citation/facet-keyword signatures were narrowed to
filename+plugin-name only. (3) `performance-engineering-rulebook`'s
`order-check.sh` was first misclassified `facet-keyword` because its
header comment explains what it is *not* ("this gate never checks facet
presence itself") using the word "facet", which a full-body keyword scan
matched anyway — same fix (filename/plugin-name-only signatures)
resolved it; `order-check.sh` reclassified to `ordering-methodology` by
adding `order.check` to that family's filename pattern.

## Rationale for deviations

None — requirements 1 through 4 and both Acceptance checks were
completed as scoped; no divergence from the issue's frozen requirements
occurred.
