---
name: role-invariant-coverage
description: >
  All 43 role domains (roles/specs/*.spec.json) classified against
  on-the-record's standing hook enforcement (on-the-record/hooks/hooks.json)
  — gate-now / directive-only / spawn-only, per issue #960. Landed from
  docs/issue-960/proposals/role-invariant-coverage.md (approved phase-1).
---

# Role-invariant coverage matrix (issue #960)

Audit of all 43 role domains against standing hook enforcement, so role
expertise is not invocation-only: for work that flows through the
pipeline, related domains carry STANDING duties (hook/gate invariants,
default-on) wherever a gate can decide the case; spawns are reserved for
the judgment residue a gate cannot.

Legend — **gate-now**: mechanically checkable today, a hook could enforce
it; **directive-only**: worth stating as a standing role directive but
not mechanically checkable without unacceptable false positives;
**spawn-only**: genuinely requires situational judgment a gate cannot
approximate (rationale given).

## Coverage matrix (43 roles)

| # | Role | Existing standing invariant | Classification | Invariant (proposed if none exists) |
|---|------|------------------------------|-----------------|--------------------------------------|
| 1 | accessibility | `accessibility-guard.sh` (issue #1130 phase 2) | **gate-now (landed)** | user-visible surface diff must carry an accessibility check reference (alt text / contrast / keyboard-nav note) before landing |
| 2 | api-design | `api-version-guard.sh` (issue #1130 phase 2) | **gate-now (landed)** | removing/renaming a public field or endpoint without a version bump is refused |
| 3 | architecture | `spec-index-preflight.sh`, `role-axis-completeness-guard.sh` (structural completeness, not duplication) | directive-only | no new top-level mechanism when an existing one composes — requires judging "composes" case by case, not mechanically decidable from a diff alone |
| 4 | brand-design | none | spawn-only — visual/tone judgment has no mechanical proxy; false positives on any keyword-based check would be near-total |
| 5 | capacity-planning | none | spawn-only — a numeric capacity projection needs live load context a gate cannot fetch |
| 6 | conformance-review | none | directive-only | conformance-affecting change states which standard/spec clause it conforms to |
| 7 | content-design | none | directive-only | user-facing copy change states the design rationale in the commit/PR body |
| 8 | customer-support | none | spawn-only — support-impact judgment depends on live ticket context outside the repo |
| 9 | data-engineering | none | directive-only | schema/pipeline migration change states its rollback path |
| 10 | data-modeling | none | directive-only | new/changed data model states its normalization/invariant rationale |
| 11 | defect-verification | `acceptance-command-real-run-guard.sh`, `accumulation-claim-guard.sh` | gate-now (already landed) | — |
| 12 | devrel | none | spawn-only — external-developer messaging judgment, no repo-local signal |
| 13 | execution-observation | `record-claim-guard.sh`, `live-fire-test-guard.sh`, `live-fire-claim-real-run-guard.sh` | gate-now (already landed) | — |
| 14 | finance-unit-economics | none | spawn-only — unit-economics judgment needs external financial data |
| 15 | growth-analytics | none | directive-only | a metric-moving change states which metric and expected direction |
| 16 | implementation | `deliverable-guard.sh`, `call-shape-guard.sh`, `retry-loop-bound.sh`, others | gate-now (already landed) | — |
| 17 | incident-response | none | spawn-only — response judgment depends on live incident state, not diffable |
| 18 | interaction-design | `design-rationale-guard.sh` (issue #960 phase 2) | **gate-now (landed)** | user-facing text/UX change carries a design rationale — enforced on `on-the-record/commands/*.md` frontmatter's `design-rationale:` field |
| 19 | issue-retrospective | `deviation-log-guard.sh` | gate-now (already landed) | — |
| 20 | knowledge-management | `deviation-log-guard.sh` (shared) | directive-only | a closed issue's durable learning is filed under `docs/decisions/` or `docs/handbooks/`, not left only in the PR thread |
| 21 | legal-compliance | none | spawn-only — regulatory applicability judgment needs jurisdiction/context a gate cannot infer |
| 22 | localization | none | directive-only | user-facing string change flags whether translated surfaces need updating |
| 23 | market-analysis | none | spawn-only — external market judgment, no repo-local signal |
| 24 | marketing | none | spawn-only — messaging/positioning judgment, no repo-local signal |
| 25 | ml-engineering | none | directive-only | training-affecting change states an eval/model-card note |
| 26 | observability | none | directive-only | hot-path or prod-facing change states which metric/log covers it |
| 27 | partnerships-bd | none | spawn-only — external negotiation judgment, no repo-local signal |
| 28 | performance-engineering | `perf-measurement-guard.sh` (issue #1130 phase 2) | **gate-now (landed)** | hot-path change carries a measurement |
| 29 | pr-communications | none | directive-only | a PR description states the audience-facing summary distinct from the technical diff |
| 30 | pricing | none | spawn-only — pricing judgment needs market/financial context |
| 31 | product-discovery | `product-capture-stopgate.sh`, `requirement-digest-preflight.sh` | gate-now (already landed) | — |
| 32 | refactoring-legacy | none | directive-only | a refactor PR states behavior-preservation evidence (tests unchanged in assertions) |
| 33 | release-engineering | `pr-preflight.sh`, `merge-allow-gate.sh`, `spawn-allow-gate.sh` | gate-now (already landed) | — |
| 34 | requirements-engineering | `requirement-digest-preflight.sh` | gate-now (already landed) | — |
| 35 | risk-management | none | spawn-only — risk-tolerance judgment is a human call, not a repo-diffable fact |
| 36 | sales | none | spawn-only — external sales judgment, no repo-local signal |
| 37 | secure-coding | `credential-network-guard.sh`, `credential-record-guard.sh` | gate-now (already landed) | — |
| 38 | security-threat-model | `credential-network-guard.sh`, `credential-record-guard.sh` (shared) | directive-only | a new external-facing surface states its threat-model note beyond the shared credential checks |
| 39 | technical-feasibility | none | directive-only | a feasibility claim about a candidate technology cites a source, mirroring product-discovery's evidence-citation rule |
| 40 | technical-writing | none | directive-only | a doc change targeting a specific reader level states that level (mirrors `prose-modes` skill) |
| 41 | test-authoring | `test-authoring-invariant-guard.sh`, `role-test-claim-guard.sh` | gate-now (already landed) | — |
| 42 | user-discovery | none | directive-only | cited user evidence is observation, not stated preference (Mom Test rule, shared with product-discovery) |
| 43 | ux-engineering | `design-rationale-guard.sh` (shares row 18's gate) | **gate-now (landed)** | user-visible surface diff carries an accessibility+design check reference — shares row 18's `design-rationale:` frontmatter gate |

## Landing status

- Rows 18/43 (design/UX cluster) landed phase 2, issue #960: `design-rationale-guard.sh`
  (`on-the-record/hooks/design-rationale-guard.sh`), tested by
  `on-the-record/hooks/test_design_rationale_guard.py`.
- Rows 1/2/28 (accessibility, api-design, performance-engineering) landed
  phase 2, issue #1130: `accessibility-guard.sh`, `api-version-guard.sh`,
  `perf-measurement-guard.sh` (all under `on-the-record/hooks/`), tested by
  `on-the-record/hooks/test_accessibility_guard.py`,
  `on-the-record/hooks/test_api_version_guard.py`,
  `on-the-record/hooks/test_perf_measurement_guard.py` respectively.
  Every gate-now row now carries a `(landed)` marker.
- Rows judged spawn-only carry a written rationale in the table above,
  not an empty cell, per the issue's "empty state" acceptance line.

## Quality-bar status (issue #1156)

Per-role `quality_bar` decomposition status, amended requirement 5 (all 43 roles in scope, the 7 below landing-order-first). Source: `docs/issue-1156/proposals/per-role-quality-bars.md` §1/§7 (approved phase-1).

| # | Role | Bar status | Domain / source standard |
|---|------|------------|---------------------------|
| 1 | ux-engineering | **quality_bar: landed** (4 criteria, `roles/specs/ux-engineering.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 2 | interaction-design | **quality_bar: landed** (4 criteria, `roles/specs/interaction-design.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 3 | accessibility | **quality_bar: landed** (4 criteria, `roles/specs/accessibility.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 4 | api-design | **quality_bar: landed** (4 criteria, `roles/specs/api-design.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 5 | performance-engineering | **quality_bar: landed** (4 criteria, `roles/specs/performance-engineering.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 6 | secure-coding | **quality_bar: landed** (4 criteria, `roles/specs/secure-coding.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 7 | test-authoring | **quality_bar: landed** (4 criteria, `roles/specs/test-authoring.spec.json`, `bar-not-met` in `loop_state.refusal`) | see spec's own `quality_bar` array |
| 8 | architecture | bar: domain-named, decomposition-pending | decision-record quality and traceability. Source: MADR (Markdown Any Decision Records), `adr.github.io/madr` |
| 9 | brand-design | bar: domain-named, decomposition-pending | design-token consistency and cross-surface visual coherence. Source: DTCG Design Tokens Format, `designtokens.org/tr/2025.10/format` |
| 10 | capacity-planning | bar: domain-named, decomposition-pending | forecast accuracy and headroom discipline. Source: ITIL Capacity Management practice |
| 11 | conformance-review | bar: domain-named, decomposition-pending | machine-checkable conformance evidence completeness. Source: EARL 1.0 Schema (W3C) |
| 12 | content-design | bar: domain-named, decomposition-pending | microcopy clarity and usability. Source: GOV.UK Content Design / GDS style guide; judgment lens NN/g 10 Usability Heuristics |
| 13 | customer-support | bar: domain-named, decomposition-pending | support-center service quality. Source: HDI Support Center Standard + CSAT |
| 14 | data-engineering | bar: domain-named, decomposition-pending | pipeline data-quality and contract stability. Source: dbt model contracts; judgment lens DAMA-DMBOK data-quality dimensions |
| 15 | data-modeling | bar: domain-named, decomposition-pending | schema correctness and grain discipline. Source: Kimball dimensional-modeling conventions; judgment lens Codd's normalization rules (1NF-3NF/BCNF) |
| 16 | defect-verification | bar: domain-named, decomposition-pending | reproducible incident-report completeness. Source: ISO/IEC/IEEE 29119-3 Incident Report (clause 7.12, Annex A.2.15) + Bugmon reproduction precedent |
| 17 | devrel | bar: domain-named, decomposition-pending | developer-relations impact measurement. Source: Keystone DevRel metrics + DevRel-Qualified-Lead concept (convergent practice, no single ratified standard — stated as assumption per the spec's own scout-brief gap) |
| 18 | execution-observation | bar: domain-named, decomposition-pending | machine-checkable execution-conformance evidence. Source: EARL 1.0 Schema (W3C) |
| 19 | finance-unit-economics | bar: domain-named, decomposition-pending | unit-economics metric correctness. Source: SaaS unit-economics metric set (CAC, LTV, LTV:CAC, CAC payback, Rule of 40) — de facto convention, no single ratified standards body (stated as assumption per the spec's own scout-brief gap) |
| 20 | growth-analytics | bar: domain-named, decomposition-pending | funnel-metric attribution soundness. Source: AARRR Pirate Metrics + North Star Metric (original source not independently fetched — stated as assumption per the spec's own scout-brief gap) |
| 21 | implementation | bar: domain-named, decomposition-pending | commit-message and change traceability. Source: Conventional Commits v1.0.0 |
| 22 | incident-response | bar: domain-named, decomposition-pending | postmortem completeness and blamelessness. Source: SRE Postmortem Template (Google SRE book) |
| 23 | issue-retrospective | bar: domain-named, decomposition-pending | retrospective format completeness and blamelessness. Source: Blameless retrospective format (SRE lineage) |
| 24 | knowledge-management | bar: domain-named, decomposition-pending | tacit-knowledge capture completeness. Source: KCS (Knowledge-Centered Service) Solve loop; judgment lens SECI model |
| 25 | legal-compliance | bar: domain-named, decomposition-pending | privacy-impact assessment completeness. Source: GDPR Article 35(7) DPIA |
| 26 | localization | bar: domain-named, decomposition-pending | translation quality and locale-data correctness. Source: Unicode CLDR / UTS #35 (LDML); judgment lens MQM error typology |
| 27 | market-analysis | bar: domain-named, decomposition-pending | competitive-analysis rigor. Source: Porter's Five Forces (HBR) |
| 28 | marketing | bar: domain-named, decomposition-pending | positioning clarity and differentiation. Source: April Dunford's positioning framework |
| 29 | ml-engineering | bar: domain-named, decomposition-pending | model documentation and build/no-build judgment soundness. Source: Model Cards (Mitchell et al. 2019); judgment lens Google's Rules of ML |
| 30 | observability | bar: domain-named, decomposition-pending | instrumentation completeness across the three pillars. Source: OpenTelemetry semantic conventions; judgment lens three-pillars framing (logs/metrics/traces) |
| 31 | partnerships-bd | bar: domain-named, decomposition-pending | collaborative-relationship management discipline. Source: ISO 44001:2017 |
| 32 | pr-communications | bar: domain-named, decomposition-pending | PR-description and evaluation rigor. Source: AMEC Integrated Evaluation Framework (Barcelona Principles); judgment lens Google eng-practices reviewer standard |
| 33 | pricing | bar: domain-named, decomposition-pending | price-sensitivity research validity. Source: Van Westendorp Price Sensitivity Meter |
| 34 | product-discovery | bar: domain-named, decomposition-pending | opportunity-assessment rigor and pre-registered decision rules. Source: Cagan/SVPG Opportunity Assessment + lean-startup pre-registered decision rules |
| 35 | refactoring-legacy | bar: domain-named, decomposition-pending | refactor justification against a named code smell, not stylistic preference. Source: Fowler's Refactoring Catalog; judgment lens Fowler's code-smell catalog |
| 36 | release-engineering | bar: domain-named, decomposition-pending | changelog completeness and format. Source: Keep a Changelog |
| 37 | risk-management | bar: domain-named, decomposition-pending | supply-chain risk assessment completeness. Source: NIST SP 800-161r1 (C-SCRM) (NIST IR 8286 lineage cited by secondary sources only — stated as assumption per the spec's own scout-brief gap) |
| 38 | sales | bar: domain-named, decomposition-pending | qualification-criteria completeness. Source: MEDDPICC |
| 39 | security-threat-model | bar: domain-named, decomposition-pending | threat-model schema completeness. Source: STRIDE / OWASP Threat Dragon model schema |
| 40 | technical-feasibility | bar: domain-named, decomposition-pending | spike-record completeness and decision traceability. Source: ADR-style spike record |
| 41 | technical-writing | bar: domain-named, decomposition-pending | documentation-type correctness (tutorial/how-to/reference/explanation). Source: Diataxis |
| 42 | user-discovery | bar: domain-named, decomposition-pending | interview-saturation and signal-vs-noise discipline. Source: Teresa Torres interview snapshots + Guest/Bunce/Johnson 2006 and Hennink/Kaiser/Weber 2020 saturation run-length; judgment lens The Mom Test's three failure-mode filter |
| 43 | requirements-engineering | bar: domain-named, decomposition-pending | requirement verifiability and bidirectional traceability (this role's own domain, subject to the same bar it enforces on others). Source: EARS (Mavin et al., IEEE RE'09) + ISO/IEC/IEEE 29148 bidirectional traceability |

Status values: **quality_bar: landed** — full `{criterion, verification_method}` decomposition landed and enforced by `gates/quality_bar.py`/`on-the-record/hooks/quality-bar-gate.sh`. **bar: domain-named, decomposition-pending** — domain and source standard named per amended requirement 5; full per-criterion decomposition to the landed 7's depth is phase-wise, tracked per role in a later issue/PR reusing §0's decomposition principles (top-of-industry level; non-automatable criteria become named human-review checklists, never a lowered bar) — not silently dropped and not marked out-of-scope.
