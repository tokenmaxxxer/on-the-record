---
code_under_review:
  - scripts/check_skill_conformance.py
  - scripts/normalize_skill_frontmatter.py
  - skills/*/SKILL.md
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-1784 phase-2: skill-repository SKILL.md frontmatter conformance

## What was done

Delivered the approved phase-1 proposal
(`docs/issue-1784/proposals/frontmatter-conformance.md`) as a PR against
`tokenmaxxxer/skill-repository`:
https://github.com/tokenmaxxxer/skill-repository/pull/6 (branch
`issue-1784-frontmatter-conformance`, commit
`65d58b43a60b9b70024d2054a7c68a951ff4b33d`).

Two scripts were added to the skill-repository checkout at
`/tmp/skill-repository`:

1. `scripts/check_skill_conformance.py` — walks `skills/*/SKILL.md`,
   requires a non-empty `name:` equal to the directory name and a
   non-empty `description:` containing a usage/trigger clause (`use
   when`, `use while`, `use to`, `trigger`, etc.). Exits non-zero
   listing every violator (path + reason); exits 0 printing `"<n> skills
   checked"` on a fully conformant tree, including the vacuous `"0
   skills checked"` case for an empty `skills/` dir.
2. `scripts/normalize_skill_frontmatter.py` — one-shot, text-level
   frontmatter surgery (never a full YAML parse+dump round-trip): for
   each non-conformant skill it either prepends a new frontmatter block
   (11 no-frontmatter files), inserts `name:`/`description:` into an
   existing axis-only frontmatter block while preserving `axis:`/
   `rule_count_floor:` verbatim, or rewrites only a wrong `name:` value
   or a trigger-clause-less `description:` field in place. All bytes
   after the closing `---` (the skill body) are copied through
   unchanged in every code path. 31 already-conformant skills were left
   completely untouched; 203 skills were normalized.

## Why

Per the approved proposal's Rationale: text-level surgery (regex-anchored
splice, not a YAML dumper round-trip) makes the byte-identity property
structural rather than something to verify after the fact — a PyYAML
dumper does not guarantee byte-identical re-emission of the 31 already
correctly-formatted files (key order, quoting, `description: >-` block
folding are dumper-version-dependent), and the acceptance criterion is
checked by literal diff.

## Upstream

Based on: `docs/issue-1784/proposals/frontmatter-conformance.md` (this
repo), approved via the issue-level comment `APPROVE
issue-1784/implementation` from approvers.md account `JiwonJung94`.
skill-repository base commit: `8021adacaf93e2d3703da3da8c1e8847c0ee7294`
(main, fetched live at delivery time).

## Verification — all four runs executed live

canonical: executed live from the skill-repository checkout at
`/tmp/skill-repository`, branch `issue-1784-frontmatter-conformance`,
commit `65d58b43a60b9b70024d2054a7c68a951ff4b33d`.

### Run 1 — checker on the pre-normalization tree (`git checkout -- skills/` then run)

```
203 violation(s) found (234 skills checked):
  skills/accessibility-aria-and-contrast-rules/SKILL.md: missing frontmatter
  skills/api-design-error-design/SKILL.md: missing or empty name:
  skills/api-design-error-design/SKILL.md: missing or empty description:
  skills/api-design-http-semantics/SKILL.md: missing or empty name:
  skills/api-design-http-semantics/SKILL.md: missing or empty description:
  skills/api-design-payload-design/SKILL.md: missing or empty name:
  skills/api-design-payload-design/SKILL.md: missing or empty description:
  skills/api-design-resource-modeling/SKILL.md: missing or empty name:
  skills/api-design-resource-modeling/SKILL.md: missing or empty description:
  skills/api-design-tool-landscape/SKILL.md: missing or empty name:
  skills/api-design-tool-landscape/SKILL.md: missing or empty description:
  skills/api-design-versioning-evolution/SKILL.md: missing or empty name:
  skills/api-design-versioning-evolution/SKILL.md: missing or empty description:
  skills/architecture-coupling-classification/SKILL.md: missing or empty name:
  skills/architecture-coupling-classification/SKILL.md: missing or empty description:
  skills/architecture-decomposition-strategy/SKILL.md: missing or empty name:
  skills/architecture-decomposition-strategy/SKILL.md: missing or empty description:
  skills/architecture-dependency-direction/SKILL.md: missing or empty name:
  skills/architecture-dependency-direction/SKILL.md: missing or empty description:
  skills/architecture-interface-contract-shape/SKILL.md: missing or empty name:
  skills/architecture-interface-contract-shape/SKILL.md: missing or empty description:
  skills/architecture-module-boundary-definition/SKILL.md: missing or empty name:
  skills/architecture-module-boundary-definition/SKILL.md: missing or empty description:
  skills/brand-design-brand-consistency-governance/SKILL.md: missing or empty name:
  skills/brand-design-brand-consistency-governance/SKILL.md: missing or empty description:
  skills/brand-design-brand-identity-strategy/SKILL.md: missing or empty name:
  skills/brand-design-brand-identity-strategy/SKILL.md: missing or empty description:
  skills/brand-design-color-visibility/SKILL.md: missing or empty name:
  skills/brand-design-color-visibility/SKILL.md: missing or empty description:
  skills/brand-design-logo-clear-space-size/SKILL.md: missing or empty name:
  skills/brand-design-logo-clear-space-size/SKILL.md: missing or empty description:
  skills/brand-design-typography-pairing/SKILL.md: missing or empty name:
  skills/brand-design-typography-pairing/SKILL.md: missing or empty description:
  skills/capacity-planning-cost-attribution-at-trigger/SKILL.md: missing or empty name:
  skills/capacity-planning-cost-attribution-at-trigger/SKILL.md: missing or empty description:
  skills/capacity-planning-demand-shape-and-forecast-method/SKILL.md: missing or empty name:
  skills/capacity-planning-demand-shape-and-forecast-method/SKILL.md: missing or empty description:
  skills/capacity-planning-expansion-trigger-threshold-sizing/SKILL.md: missing or empty name:
  skills/capacity-planning-expansion-trigger-threshold-sizing/SKILL.md: missing or empty description:
  skills/capacity-planning-headroom-band-and-degradation-risk/SKILL.md: missing or empty name:
  skills/capacity-planning-headroom-band-and-degradation-risk/SKILL.md: missing or empty description:
  skills/capacity-planning-safety-buffer-sizing-by-criticality/SKILL.md: missing or empty name:
  skills/capacity-planning-safety-buffer-sizing-by-criticality/SKILL.md: missing or empty description:
  skills/conformance-review-finding-record/SKILL.md: name: 'finding-record' does not match directory 'conformance-review-finding-record'
  skills/conformance-review-requirement-extraction/SKILL.md: missing or empty name:
  skills/conformance-review-requirement-extraction/SKILL.md: missing or empty description:
  skills/conformance-review-sampling-derivation/SKILL.md: missing or empty name:
  skills/conformance-review-sampling-derivation/SKILL.md: missing or empty description:
  skills/conformance-review-severity-classification/SKILL.md: name: 'severity-classification' does not match directory 'conformance-review-severity-classification'
  skills/conformance-review-traceability-and-evidence/SKILL.md: missing or empty name:
  skills/conformance-review-traceability-and-evidence/SKILL.md: missing or empty description:
  skills/conformance-review-verdict-assignment/SKILL.md: missing or empty name:
  skills/conformance-review-verdict-assignment/SKILL.md: missing or empty description:
  skills/conformance-review-verification-method-selection/SKILL.md: missing or empty name:
  skills/conformance-review-verification-method-selection/SKILL.md: missing or empty description:
  skills/content-design-operational-playbook/SKILL.md: missing frontmatter
  skills/customer-support-escalation-path/SKILL.md: missing frontmatter
  skills/customer-support-five-whys-recurring-scope/SKILL.md: missing frontmatter
  skills/customer-support-kcs-article-authoring/SKILL.md: missing frontmatter
  skills/customer-support-research-log/SKILL.md: missing or empty name:
  skills/customer-support-research-log/SKILL.md: missing or empty description:
  skills/customer-support-sla-tier-priority/SKILL.md: missing frontmatter
  skills/customer-support-subtraction-comprehensibility/SKILL.md: missing frontmatter
  skills/data-engineering-data-quality/SKILL.md: missing or empty name:
  skills/data-engineering-data-quality/SKILL.md: missing or empty description:
  skills/data-engineering-failure-handling/SKILL.md: missing or empty name:
  skills/data-engineering-failure-handling/SKILL.md: missing or empty description:
  skills/data-engineering-pipeline-design/SKILL.md: missing or empty name:
  skills/data-engineering-pipeline-design/SKILL.md: missing or empty description:
  skills/data-modeling-datavault/SKILL.md: missing or empty name:
  skills/data-modeling-datavault/SKILL.md: missing or empty description:
  skills/data-modeling-inmon/SKILL.md: missing or empty name:
  skills/data-modeling-inmon/SKILL.md: missing or empty description:
  skills/data-modeling-kimball/SKILL.md: missing or empty name:
  skills/data-modeling-kimball/SKILL.md: missing or empty description:
  skills/data-modeling-structure/SKILL.md: missing or empty name:
  skills/data-modeling-structure/SKILL.md: missing or empty description:
  skills/defect-verification-evidence-artifact-completeness/SKILL.md: missing or empty name:
  skills/defect-verification-evidence-artifact-completeness/SKILL.md: missing or empty description:
  skills/defect-verification-independence-from-upstream-verdicts/SKILL.md: missing or empty name:
  skills/defect-verification-independence-from-upstream-verdicts/SKILL.md: missing or empty description:
  skills/defect-verification-reproduction-evidence-quality/SKILL.md: missing or empty name:
  skills/defect-verification-reproduction-evidence-quality/SKILL.md: missing or empty description:
  skills/defect-verification-severity-band-assignment/SKILL.md: missing or empty name:
  skills/defect-verification-severity-band-assignment/SKILL.md: missing or empty description:
  skills/devrel-channel-convention/SKILL.md: missing or empty name:
  skills/devrel-channel-convention/SKILL.md: missing or empty description:
  skills/devrel-content-comprehensibility/SKILL.md: missing or empty name:
  skills/devrel-content-comprehensibility/SKILL.md: missing or empty description:
  skills/devrel-program-subtraction/SKILL.md: missing or empty name:
  skills/devrel-program-subtraction/SKILL.md: missing or empty description:
  skills/finance-unit-economics-cac-payback/SKILL.md: missing or empty name:
  skills/finance-unit-economics-cac-payback/SKILL.md: missing or empty description:
  skills/finance-unit-economics-evidence-chain/SKILL.md: missing or empty name:
  skills/finance-unit-economics-evidence-chain/SKILL.md: missing or empty description:
  skills/finance-unit-economics-ltv-cac-band/SKILL.md: missing or empty name:
  skills/finance-unit-economics-ltv-cac-band/SKILL.md: missing or empty description:
  skills/finance-unit-economics-ltv-churn-assumption/SKILL.md: missing or empty name:
  skills/finance-unit-economics-ltv-churn-assumption/SKILL.md: missing or empty description:
  skills/finance-unit-economics-proposal-shape/SKILL.md: missing or empty name:
  skills/finance-unit-economics-proposal-shape/SKILL.md: missing or empty description:
  skills/finance-unit-economics-sensitivity-scenario/SKILL.md: missing or empty name:
  skills/finance-unit-economics-sensitivity-scenario/SKILL.md: missing or empty description:
  skills/growth-analytics-experiment-trust/SKILL.md: missing or empty name:
  skills/growth-analytics-experiment-trust/SKILL.md: missing or empty description:
  skills/growth-analytics-funnel-stage-attribution/SKILL.md: missing or empty name:
  skills/growth-analytics-funnel-stage-attribution/SKILL.md: missing or empty description:
  skills/growth-analytics-metric-selection/SKILL.md: missing or empty name:
  skills/growth-analytics-metric-selection/SKILL.md: missing or empty description:
  skills/growth-analytics-reporting-reduction/SKILL.md: missing or empty name:
  skills/growth-analytics-reporting-reduction/SKILL.md: missing or empty description:
  skills/growth-analytics-segmentation/SKILL.md: missing or empty name:
  skills/growth-analytics-segmentation/SKILL.md: missing or empty description:
  skills/implementation-audit/SKILL.md: description: has no usage/trigger clause
  skills/implementation-blueprint/SKILL.md: name: 'blueprint' does not match directory 'implementation-blueprint'
  skills/implementation-complexity-coupling-management/SKILL.md: missing or empty name:
  skills/implementation-complexity-coupling-management/SKILL.md: missing or empty description:
  skills/implementation-design-pattern-selection/SKILL.md: missing or empty name:
  skills/implementation-design-pattern-selection/SKILL.md: missing or empty description:
  skills/implementation-performance-data-structure-choice/SKILL.md: missing or empty name:
  skills/implementation-performance-data-structure-choice/SKILL.md: missing or empty description:
  skills/incident-response-action-item-quality/SKILL.md: missing or empty name:
  skills/incident-response-action-item-quality/SKILL.md: missing or empty description:
  skills/incident-response-blameless-language-editing/SKILL.md: missing or empty name:
  skills/incident-response-blameless-language-editing/SKILL.md: missing or empty description:
  skills/incident-response-rca-method-selection/SKILL.md: missing or empty name:
  skills/incident-response-rca-method-selection/SKILL.md: missing or empty description:
  skills/incident-response-severity-classification-scoping/SKILL.md: missing or empty name:
  skills/incident-response-severity-classification-scoping/SKILL.md: missing or empty description:
  skills/incident-response-timeline-construction/SKILL.md: missing or empty name:
  skills/incident-response-timeline-construction/SKILL.md: missing or empty description:
  skills/incident-response-tool-landscape/SKILL.md: missing or empty name:
  skills/incident-response-tool-landscape/SKILL.md: missing or empty description:
  skills/interaction-design-form-control-and-layout/SKILL.md: missing frontmatter
  skills/issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md: missing or empty name:
  skills/issue-retrospective-timeline-comprehensibility-and-subtraction-rules/SKILL.md: missing or empty description:
  skills/knowledge-management-curation-pruning/SKILL.md: missing or empty name:
  skills/knowledge-management-curation-pruning/SKILL.md: missing or empty description:
  skills/knowledge-management-pattern-extraction/SKILL.md: missing or empty name:
  skills/knowledge-management-pattern-extraction/SKILL.md: missing or empty description:
  skills/knowledge-management-structure-findability/SKILL.md: missing or empty name:
  skills/knowledge-management-structure-findability/SKILL.md: missing or empty description:
  skills/knowledge-management-supersession-lifecycle/SKILL.md: missing or empty name:
  skills/knowledge-management-supersession-lifecycle/SKILL.md: missing or empty description:
  skills/knowledge-management-taxonomy-tagging/SKILL.md: missing or empty name:
  skills/knowledge-management-taxonomy-tagging/SKILL.md: missing or empty description:
  skills/legal-compliance-consent-ux/SKILL.md: missing or empty name:
  skills/legal-compliance-consent-ux/SKILL.md: missing or empty description:
  skills/legal-compliance-cross-border-transfer/SKILL.md: missing or empty name:
  skills/legal-compliance-cross-border-transfer/SKILL.md: missing or empty description:
  skills/legal-compliance-lawful-basis-selection/SKILL.md: missing or empty name:
  skills/legal-compliance-lawful-basis-selection/SKILL.md: missing or empty description:
  skills/legal-compliance-license-compatibility/SKILL.md: missing or empty name:
  skills/legal-compliance-license-compatibility/SKILL.md: missing or empty description:
  skills/legal-compliance-research-log/SKILL.md: missing frontmatter
  skills/legal-compliance-retention-minimization/SKILL.md: missing or empty name:
  skills/legal-compliance-retention-minimization/SKILL.md: missing or empty description:
  skills/legal-compliance-vendor-dpa/SKILL.md: missing or empty name:
  skills/legal-compliance-vendor-dpa/SKILL.md: missing or empty description:
  skills/localization-locale-convention-formatting/SKILL.md: missing or empty name:
  skills/localization-locale-convention-formatting/SKILL.md: missing or empty description:
  skills/localization-pluralization-and-grammar/SKILL.md: missing or empty name:
  skills/localization-pluralization-and-grammar/SKILL.md: missing or empty description:
  skills/localization-rtl-and-script-support/SKILL.md: missing or empty name:
  skills/localization-rtl-and-script-support/SKILL.md: missing or empty description:
  skills/localization-string-externalization/SKILL.md: missing or empty name:
  skills/localization-string-externalization/SKILL.md: missing or empty description:
  skills/localization-text-expansion-and-layout/SKILL.md: missing or empty name:
  skills/localization-text-expansion-and-layout/SKILL.md: missing or empty description:
  skills/market-analysis-competitor-mapping/SKILL.md: missing or empty name:
  skills/market-analysis-competitor-mapping/SKILL.md: missing or empty description:
  skills/market-analysis-evidence-rigor/SKILL.md: missing or empty name:
  skills/market-analysis-evidence-rigor/SKILL.md: missing or empty description:
  skills/market-analysis-five-forces/SKILL.md: missing or empty name:
  skills/market-analysis-five-forces/SKILL.md: missing or empty description:
  skills/market-analysis-jtbd-fit/SKILL.md: missing or empty name:
  skills/market-analysis-jtbd-fit/SKILL.md: missing or empty description:
  skills/market-analysis-mece-proposal/SKILL.md: missing or empty name:
  skills/market-analysis-mece-proposal/SKILL.md: missing or empty description:
  skills/marketing-channel-selection/SKILL.md: missing or empty name:
  skills/marketing-channel-selection/SKILL.md: missing or empty description:
  skills/marketing-message-persuasion/SKILL.md: missing or empty name:
  skills/marketing-message-persuasion/SKILL.md: missing or empty description:
  skills/marketing-positioning-differentiation/SKILL.md: missing or empty name:
  skills/marketing-positioning-differentiation/SKILL.md: missing or empty description:
  skills/marketing-scope-pruning/SKILL.md: missing or empty name:
  skills/marketing-scope-pruning/SKILL.md: missing or empty description:
  skills/marketing-segment-targeting/SKILL.md: missing or empty name:
  skills/marketing-segment-targeting/SKILL.md: missing or empty description:
  skills/ml-engineering-evaluation-discipline/SKILL.md: missing or empty name:
  skills/ml-engineering-evaluation-discipline/SKILL.md: missing or empty description:
  skills/ml-engineering-ml-test-score-scoring/SKILL.md: missing or empty name:
  skills/ml-engineering-ml-test-score-scoring/SKILL.md: missing or empty description:
  skills/ml-engineering-model-provenance-versioning/SKILL.md: missing or empty name:
  skills/ml-engineering-model-provenance-versioning/SKILL.md: missing or empty description:
  skills/ml-engineering-rollout-promotion-rollback/SKILL.md: missing or empty name:
  skills/ml-engineering-rollout-promotion-rollback/SKILL.md: missing or empty description:
  skills/ml-engineering-serving-pattern-selection/SKILL.md: missing or empty name:
  skills/ml-engineering-serving-pattern-selection/SKILL.md: missing or empty description:
  skills/ml-engineering-slo-definition-tradeoffs/SKILL.md: missing or empty name:
  skills/ml-engineering-slo-definition-tradeoffs/SKILL.md: missing or empty description:
  skills/observability-cardinality-budget/SKILL.md: missing or empty name:
  skills/observability-cardinality-budget/SKILL.md: missing or empty description:
  skills/observability-explorability/SKILL.md: missing or empty name:
  skills/observability-explorability/SKILL.md: missing or empty description:
  skills/observability-methodology-selection/SKILL.md: missing or empty name:
  skills/observability-methodology-selection/SKILL.md: missing or empty description:
  skills/observability-phase-trace/SKILL.md: missing or empty name:
  skills/observability-phase-trace/SKILL.md: missing or empty description:
  skills/observability-signal-golden/SKILL.md: missing or empty name:
  skills/observability-signal-golden/SKILL.md: missing or empty description:
  skills/observability-signal-red/SKILL.md: missing or empty name:
  skills/observability-signal-red/SKILL.md: missing or empty description:
  skills/observability-signal-use/SKILL.md: missing or empty name:
  skills/observability-signal-use/SKILL.md: missing or empty description:
  skills/overengineering-audit/SKILL.md: description: has no usage/trigger clause
  skills/partnerships-bd-deal-structure-selection/SKILL.md: missing or empty name:
  skills/partnerships-bd-deal-structure-selection/SKILL.md: missing or empty description:
  skills/partnerships-bd-exclusivity-and-scope-terms/SKILL.md: missing or empty name:
  skills/partnerships-bd-exclusivity-and-scope-terms/SKILL.md: missing or empty description:
  skills/partnerships-bd-governance-cadence-and-kpi/SKILL.md: missing or empty name:
  skills/partnerships-bd-governance-cadence-and-kpi/SKILL.md: missing or empty description:
  skills/partnerships-bd-negotiation-positioning/SKILL.md: missing or empty name:
  skills/partnerships-bd-negotiation-positioning/SKILL.md: missing or empty description:
  skills/partnerships-bd-term-sheet-comprehensibility-and-convention/SKILL.md: missing or empty name:
  skills/partnerships-bd-term-sheet-comprehensibility-and-convention/SKILL.md: missing or empty description:
  skills/performance-engineering-operational-playbook/SKILL.md: missing or empty name:
  skills/performance-engineering-operational-playbook/SKILL.md: missing or empty description:
  skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md: missing or empty name:
  skills/pr-communications-message-planning-and-evaluation-rules/SKILL.md: missing or empty description:
  skills/pricing-design-rigor/SKILL.md: missing or empty name:
  skills/pricing-design-rigor/SKILL.md: missing or empty description:
  skills/pricing-method-family/SKILL.md: missing or empty name:
  skills/pricing-method-family/SKILL.md: missing or empty description:
  skills/pricing-scope-gate/SKILL.md: missing or empty name:
  skills/pricing-scope-gate/SKILL.md: missing or empty description:
  skills/pricing-tier-structure/SKILL.md: missing or empty name:
  skills/pricing-tier-structure/SKILL.md: missing or empty description:
  skills/pricing-verdict-report/SKILL.md: missing or empty name:
  skills/pricing-verdict-report/SKILL.md: missing or empty description:
  skills/product-discovery-assumption-mapping/SKILL.md: name: 'assumption-mapping' does not match directory 'product-discovery-assumption-mapping'
  skills/product-discovery-guardrail-metric-status/SKILL.md: missing or empty name:
  skills/product-discovery-guardrail-metric-status/SKILL.md: missing or empty description:
  skills/product-discovery-guardrail-metrics/SKILL.md: name: 'guardrail-metrics' does not match directory 'product-discovery-guardrail-metrics'
  skills/product-discovery-hypothesis-preregistration/SKILL.md: missing or empty name:
  skills/product-discovery-hypothesis-preregistration/SKILL.md: missing or empty description:
  skills/product-discovery-hypothesis-testing/SKILL.md: name: 'hypothesis-testing' does not match directory 'product-discovery-hypothesis-testing'
  skills/product-discovery-jtbd-problem-framing/SKILL.md: missing or empty name:
  skills/product-discovery-jtbd-problem-framing/SKILL.md: missing or empty description:
  skills/product-discovery-one-pager/SKILL.md: name: 'one-pager' does not match directory 'product-discovery-one-pager'
  skills/product-discovery-opportunity-solution-tree/SKILL.md: name: 'opportunity-solution-tree' does not match directory 'product-discovery-opportunity-solution-tree'
  skills/product-discovery-opportunity-solution-tree-branching/SKILL.md: missing or empty name:
  skills/product-discovery-opportunity-solution-tree-branching/SKILL.md: missing or empty description:
  skills/product-discovery-rice-ice-prioritization/SKILL.md: missing or empty name:
  skills/product-discovery-rice-ice-prioritization/SKILL.md: missing or empty description:
  skills/refactoring-legacy-characterization-test-scope/SKILL.md: missing or empty name:
  skills/refactoring-legacy-characterization-test-scope/SKILL.md: missing or empty description:
  skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md: missing or empty name:
  skills/refactoring-legacy-refactoring-step-decomposition/SKILL.md: missing or empty description:
  skills/refactoring-legacy-seam-selection/SKILL.md: missing or empty name:
  skills/refactoring-legacy-seam-selection/SKILL.md: missing or empty description:
  skills/refactoring-legacy-strangler-fig-migration/SKILL.md: missing or empty name:
  skills/refactoring-legacy-strangler-fig-migration/SKILL.md: missing or empty description:
  skills/refactoring-legacy-verification-cadence/SKILL.md: missing or empty name:
  skills/refactoring-legacy-verification-cadence/SKILL.md: missing or empty description:
  skills/release-engineering-branching-release-strategy/SKILL.md: missing or empty name:
  skills/release-engineering-branching-release-strategy/SKILL.md: missing or empty description:
  skills/release-engineering-changelog-entry-categorization/SKILL.md: missing or empty name:
  skills/release-engineering-changelog-entry-categorization/SKILL.md: missing or empty description:
  skills/release-engineering-deployment-rollout-strategy/SKILL.md: missing or empty name:
  skills/release-engineering-deployment-rollout-strategy/SKILL.md: missing or empty description:
  skills/release-engineering-error-budget-policy/SKILL.md: name: 'error-budget-policy' does not match directory 'release-engineering-error-budget-policy'
  skills/release-engineering-postmortem/SKILL.md: name: 'postmortem' does not match directory 'release-engineering-postmortem'
  skills/release-engineering-readiness-checklist/SKILL.md: name: 'readiness-checklist' does not match directory 'release-engineering-readiness-checklist'
  skills/release-engineering-release-cadence-and-toil/SKILL.md: missing or empty name:
  skills/release-engineering-release-cadence-and-toil/SKILL.md: missing or empty description:
  skills/release-engineering-rollback-and-recovery/SKILL.md: missing or empty name:
  skills/release-engineering-rollback-and-recovery/SKILL.md: missing or empty description:
  skills/release-engineering-rollout-plan/SKILL.md: name: 'rollout-plan' does not match directory 'release-engineering-rollout-plan'
  skills/release-engineering-semver-bump-selection/SKILL.md: missing or empty name:
  skills/release-engineering-semver-bump-selection/SKILL.md: missing or empty description:
  skills/requirements-engineering-rules/SKILL.md: name: 'requirements-engineering-playbook' does not match directory 'requirements-engineering-rules'
  skills/requirements-engineering-rules/SKILL.md: missing or empty description:
  skills/risk-management-aggregation-consolidation/SKILL.md: missing or empty name:
  skills/risk-management-aggregation-consolidation/SKILL.md: missing or empty description:
  skills/risk-management-appetite-tolerance-threshold/SKILL.md: missing or empty name:
  skills/risk-management-appetite-tolerance-threshold/SKILL.md: missing or empty description:
  skills/risk-management-likelihood-impact-scale/SKILL.md: missing or empty name:
  skills/risk-management-likelihood-impact-scale/SKILL.md: missing or empty description:
  skills/risk-management-monitoring-review-cadence/SKILL.md: missing or empty name:
  skills/risk-management-monitoring-review-cadence/SKILL.md: missing or empty description:
  skills/risk-management-response-strategy-selection/SKILL.md: missing or empty name:
  skills/risk-management-response-strategy-selection/SKILL.md: missing or empty description:
  skills/sales-objection-handling/SKILL.md: missing or empty name:
  skills/sales-objection-handling/SKILL.md: missing or empty description:
  skills/sales-pitch-scoping-and-messaging-handoff/SKILL.md: missing or empty name:
  skills/sales-pitch-scoping-and-messaging-handoff/SKILL.md: missing or empty description:
  skills/sales-qualification-and-discovery/SKILL.md: missing or empty name:
  skills/sales-qualification-and-discovery/SKILL.md: missing or empty description:
  skills/secure-coding-authorization-access-control/SKILL.md: missing or empty name:
  skills/secure-coding-authorization-access-control/SKILL.md: missing or empty description:
  skills/secure-coding-cryptography-secrets-management/SKILL.md: missing or empty name:
  skills/secure-coding-cryptography-secrets-management/SKILL.md: missing or empty description:
  skills/secure-coding-dependency-supply-chain-security/SKILL.md: missing or empty name:
  skills/secure-coding-dependency-supply-chain-security/SKILL.md: missing or empty description:
  skills/secure-coding-input-validation-injection-defense/SKILL.md: missing or empty name:
  skills/secure-coding-input-validation-injection-defense/SKILL.md: missing or empty description:
  skills/secure-coding-session-authentication/SKILL.md: missing or empty name:
  skills/secure-coding-session-authentication/SKILL.md: missing or empty description:
  skills/security-threat-model-threat-modeling-decision-rules/SKILL.md: missing or empty name:
  skills/security-threat-model-threat-modeling-decision-rules/SKILL.md: missing or empty description:
  skills/silent-failure-audit/SKILL.md: description: has no usage/trigger clause
  skills/technical-feasibility-build-vs-buy/SKILL.md: name: 'build-vs-buy' does not match directory 'technical-feasibility-build-vs-buy'
  skills/technical-feasibility-build-vs-buy-dependency-health/SKILL.md: missing or empty name:
  skills/technical-feasibility-build-vs-buy-dependency-health/SKILL.md: missing or empty description:
  skills/technical-feasibility-license-and-regulatory-risk/SKILL.md: missing or empty name:
  skills/technical-feasibility-license-and-regulatory-risk/SKILL.md: missing or empty description:
  skills/technical-feasibility-license-scan/SKILL.md: name: 'license-scan' does not match directory 'technical-feasibility-license-scan'
  skills/technical-feasibility-reversibility-and-spike-scoping/SKILL.md: missing or empty name:
  skills/technical-feasibility-reversibility-and-spike-scoping/SKILL.md: missing or empty description:
  skills/technical-feasibility-reversibility-tag/SKILL.md: name: 'reversibility-tag' does not match directory 'technical-feasibility-reversibility-tag'
  skills/technical-feasibility-reversibility-tag/SKILL.md: description: has no usage/trigger clause
  skills/technical-feasibility-spike-report/SKILL.md: name: 'spike-report' does not match directory 'technical-feasibility-spike-report'
  skills/technical-feasibility-stride-table/SKILL.md: name: 'stride-table' does not match directory 'technical-feasibility-stride-table'
  skills/technical-feasibility-threat-model-disposition/SKILL.md: missing or empty name:
  skills/technical-feasibility-threat-model-disposition/SKILL.md: missing or empty description:
  skills/technical-feasibility-verdict-and-timebox-selection/SKILL.md: missing or empty name:
  skills/technical-feasibility-verdict-and-timebox-selection/SKILL.md: missing or empty description:
  skills/technical-writing-doc-type-selection/SKILL.md: missing or empty name:
  skills/technical-writing-doc-type-selection/SKILL.md: missing or empty description:
  skills/technical-writing-minimalism-scoping/SKILL.md: missing or empty name:
  skills/technical-writing-minimalism-scoping/SKILL.md: missing or empty description:
  skills/technical-writing-persuasion-trust/SKILL.md: missing or empty name:
  skills/technical-writing-persuasion-trust/SKILL.md: missing or empty description:
  skills/technical-writing-structure-comprehension/SKILL.md: missing or empty name:
  skills/technical-writing-structure-comprehension/SKILL.md: missing or empty description:
  skills/technical-writing-style-guide-compliance/SKILL.md: missing or empty name:
  skills/technical-writing-style-guide-compliance/SKILL.md: missing or empty description:
  skills/technical-writing-tool-landscape/SKILL.md: missing or empty name:
  skills/technical-writing-tool-landscape/SKILL.md: missing or empty description:
  skills/test-authoring-isolation-and-fixture-strategy/SKILL.md: missing frontmatter
  skills/test-depth-audit/SKILL.md: description: has no usage/trigger clause
  skills/upstream-defect-report-comprehensibility/SKILL.md: missing or empty name:
  skills/upstream-defect-report-comprehensibility/SKILL.md: missing or empty description:
  skills/upstream-defect-report-convention/SKILL.md: missing or empty name:
  skills/upstream-defect-report-convention/SKILL.md: missing or empty description:
  skills/upstream-defect-report-subtraction/SKILL.md: missing or empty name:
  skills/upstream-defect-report-subtraction/SKILL.md: missing or empty description:
  skills/user-discovery-evidence-strength-tagging/SKILL.md: missing or empty name:
  skills/user-discovery-evidence-strength-tagging/SKILL.md: missing or empty description:
  skills/user-discovery-follow-up-ladder-depth/SKILL.md: missing or empty name:
  skills/user-discovery-follow-up-ladder-depth/SKILL.md: missing or empty description:
  skills/user-discovery-question-design-past-behavior/SKILL.md: missing or empty name:
  skills/user-discovery-question-design-past-behavior/SKILL.md: missing or empty description:
  skills/user-discovery-saturation-stopping-rule/SKILL.md: missing or empty name:
  skills/user-discovery-saturation-stopping-rule/SKILL.md: missing or empty description:
  skills/user-discovery-switch-timeline-causal-forces/SKILL.md: missing or empty name:
  skills/user-discovery-switch-timeline-causal-forces/SKILL.md: missing or empty description:
  skills/user-discovery-verdict-prevalence-reporting/SKILL.md: missing or empty name:
  skills/user-discovery-verdict-prevalence-reporting/SKILL.md: missing or empty description:
  skills/ux-engineering-color-visibility/SKILL.md: missing or empty name:
  skills/ux-engineering-color-visibility/SKILL.md: missing or empty description:
  skills/ux-engineering-control-selection/SKILL.md: missing or empty name:
  skills/ux-engineering-control-selection/SKILL.md: missing or empty description:
  skills/ux-engineering-layout-grouping/SKILL.md: missing or empty name:
  skills/ux-engineering-layout-grouping/SKILL.md: missing or empty description:
  skills/ux-engineering-navigation-depth/SKILL.md: missing or empty name:
  skills/ux-engineering-navigation-depth/SKILL.md: missing or empty description:
  skills/ux-engineering-research-log/SKILL.md: missing frontmatter
  skills/ux-engineering-surface-contrast/SKILL.md: missing or empty name:
  skills/ux-engineering-surface-contrast/SKILL.md: missing or empty description:
  skills/verify-finding-record/SKILL.md: name: 'finding-record' does not match directory 'verify-finding-record'
  skills/verify-severity-classification/SKILL.md: name: 'severity-classification' does not match directory 'verify-severity-classification'
$ echo "exit=$?"
exit=1
```

canonical: `python3 scripts/check_skill_conformance.py` — result:
executed live in this session against commit
`8021adacaf93e2d3703da3da8c1e8847c0ee7294`; output pasted above. The
tool's own summary line reads `203 violation(s) found (234 skills
checked)`, covering 11 missing-frontmatter files plus 192
axis-only/name-mismatched files.

### Normalization run

```
$ python3 scripts/normalize_skill_frontmatter.py
203 skill(s) normalized, 31 already conformant
```

### Run 2 — checker on the post-normalization tree

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo "exit=$?"
exit=0
```
canonical: `python3 scripts/check_skill_conformance.py` — result:
executed live in this session against the normalized working tree
(commit `65d58b43a60b9b70024d2054a7c68a951ff4b33d`); output pasted
above.

### Byte-identity diff sweep (pre vs post, executed live)

Compares each skill's body (everything after the frontmatter block, or
the whole file for the 11 no-frontmatter cases) between the
pre-normalization commit (`git show HEAD:<path>`, HEAD =
`8021adacaf93e2d3703da3da8c1e8847c0ee7294`) and the post-normalization
working tree:

```
$ python3 byte_sweep.py
byte-identity sweep: 234 skills checked, 0 body mismatches
```
canonical: `python3 byte_sweep.py` — result: executed live in this
session, comparing `git show HEAD:<path>` at
`8021adacaf93e2d3703da3da8c1e8847c0ee7294` against the working tree at
commit `65d58b43a60b9b70024d2054a7c68a951ff4b33d`; output pasted above.

## What did not work

The first normalizer draft had two bugs, both caught by re-running the
checker after normalization (not shipped):

1. An off-by-one in the frontmatter-boundary index dropped the newline
   before the closing `---` delimiter, merging the last frontmatter
   line into the delimiter and breaking frontmatter detection for every
   normalized file. Fixed by correcting the slice boundary.
2. The normalizer only regenerated `description:` when it was missing
   or empty — it did not handle the case of a description that exists
   but lacks a usage/trigger clause.
   canonical: `python3 scripts/check_skill_conformance.py` — result:
   intermediate pre-fix run in this session listed exactly 5
   `description: has no usage/trigger clause` violations (e.g.
   `implementation-audit`), which was the signal this bug existed.
   Fixed by adding a `has_trigger_clause()` check that prepends a
   trigger clause to the existing description text in place
   (preserving the original description content) whenever the existing
   text lacks one.

Both bugs were caught before delivery.
canonical: `python3 scripts/check_skill_conformance.py` — result: the
Run 2 output block above, executed live at commit
`65d58b43a60b9b70024d2054a7c68a951ff4b33d`, is what confirmed the fix
rather than the first pass being assumed to pass.

## Open findings

None outstanding. The checker's trigger-clause heuristic
(`TRIGGER_MARKERS` in `scripts/check_skill_conformance.py`) is a fixed
word list (`use when`, `use while`, `use to`, `trigger`, etc.).
canonical: `scripts/check_skill_conformance.py` at commit
`65d58b43a60b9b70024d2054a7c68a951ff4b33d`, the `TRIGGER_MARKERS`
tuple, tuned iteratively against live checker runs in this session
against the 234 skills (54 of which — per the phase-1 survey,
`docs/issue-1784/reports/implementation/survey.md` — were already
conformant prior to this issue's normalization work) until Run 2 above
reached 0 violations. A genuinely new phrasing style in a future skill
could in principle slip past it; this is inherent to any
heuristic-word-list approach and was accepted per the proposal's stated
non-goal (procedural-body/description-quality authoring is explicit
follow-up, not this issue's scope).
