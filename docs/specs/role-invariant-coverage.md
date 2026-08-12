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
| 1 | accessibility | none | gate-now | user-visible surface diff must carry an accessibility check reference (alt text / contrast / keyboard-nav note) before landing |
| 2 | api-design | none | gate-now | removing/renaming a public field or endpoint without a version bump is refused |
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
| 28 | performance-engineering | none | gate-now | hot-path change carries a measurement |
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
- Remaining gate-now rows without a `(landed)` marker (1, 2, 28) are the
  next candidates per the phase-1 proposal's RICE ordering
  (docs/issue-960/proposals/role-invariant-coverage.md), left for a
  follow-up issue — landing every remaining gate-now cluster in one PR
  was out of this phase's scope (one domain-cluster gate per the issue's
  acceptance criterion).
- Rows judged spawn-only carry a written rationale in the table above,
  not an empty cell, per the issue's "empty state" acceptance line.
