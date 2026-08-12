---
status: proposed
files:
  - docs/specs/role-invariant-coverage.md
---

# issue-960: role-invariant coverage matrix (proposal)

kind: proposal
subject: issue-960

Proposal: docs/issue-960/proposals/role-invariant-coverage.md

## Intent

Audit all 43 role domains (`roles/specs/*.spec.json`) against
on-the-record's standing hook enforcement
(`on-the-record/hooks/hooks.json`) and classify, per domain, whether its
invariant is enforceable as a gate now, advisory/directive-only, or
genuinely spawn-only judgment — then propose a landing order for the
enforceable tier. Read evidence for the current gap is in
docs/issue-960/reports/product-discovery/current-state-survey.md.

## Constraints stated so far

- Acceptance requires a coverage matrix doc at
  `docs/specs/role-invariant-coverage.md` with every one of the 43 roles
  covered — a role judged spawn-only must carry a written rationale, not
  an empty cell.
- Actually landing the first domain-cluster gate (a `on-the-record/hooks/test_*`
  file) is acceptance item 3, phase-2 execution work — it requires a
  human approver's Approve per contract v3 s19 before this session may do
  it. This phase-1 PR delivers the matrix and the landing plan only.
- Per contract v3 s19, phase-1 output stays inside
  `docs/issue-960/reports/product-discovery/` and `docs/issue-960/proposals/`;
  the final `docs/specs/role-invariant-coverage.md` file is itself a
  phase-2 write (it lives in the standing `docs/specs/` bucket, not a
  per-issue bucket) — so this proposal carries the matrix's full content
  now, and phase 2 is copying it to its final path plus landing the first
  gate.

## What will be done (this PR, phase 1)

1. Full 43-role classification matrix (below), each row: existing
   standing invariant (if any, cited by hook file), classification
   (gate-now / directive-only / spawn-only), and either the gate-now
   invariant proposed or the spawn-only rationale.
2. RICE-scored prioritization across the gate-now candidates to pick
   which domain cluster lands first in phase 2.
3. A pre-registered hypothesis for the first gate that lands (metric,
   threshold, decision rule) per product-hypothesis-testing's
   pre-registration requirement, since "does a new gate stay default-on
   without false-positive override" is an empirical question the
   coverage matrix itself cannot answer.

## Out of scope (this PR)

- Writing or landing any new hook/gate script — that is phase 2, gated
  on human Approve.
- Copying the matrix to its final `docs/specs/role-invariant-coverage.md`
  path — also phase 2 (docs/specs/ is a standing bucket outside this
  phase's write set; committing there now would also require the
  spec-index regeneration step, which is a phase-2-scale change).

## How this will be known to have worked

- The matrix has exactly 43 rows, one per `roles/specs/*.spec.json`
  file, and every spawn-only row has a non-empty, specific rationale
  (mechanical check, per the issue's "empty state" acceptance line).
- The PR is reviewable as phase-1 (proposal + survey only, no code
  changes, no `Closes #960` trailer per the phase-1/phase-2 trailer
  split) and unblocks a phase-2 PR that lands the first gate named in
  the prioritization section.

## Coverage matrix (43 roles)

Legend — **gate-now**: mechanically checkable today, a hook could enforce
it; **directive-only**: worth stating as a standing role directive but
not mechanically checkable without unacceptable false positives;
**spawn-only**: genuinely requires situational judgment a gate cannot
approximate (rationale given).

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
| 18 | interaction-design | none | gate-now | user-facing text/UX change carries a design rationale (issue #960's own example) |
| 19 | issue-retrospective | `deviation-log-guard.sh` | gate-now (already landed) | — |
| 20 | knowledge-management | `deviation-log-guard.sh` (shared) | directive-only | a closed issue's durable learning is filed under `docs/decisions/` or `docs/handbooks/`, not left only in the PR thread |
| 21 | legal-compliance | none | spawn-only — regulatory applicability judgment needs jurisdiction/context a gate cannot infer |
| 22 | localization | none | directive-only | user-facing string change flags whether translated surfaces need updating |
| 23 | market-analysis | none | spawn-only — external market judgment, no repo-local signal |
| 24 | marketing | none | spawn-only — messaging/positioning judgment, no repo-local signal |
| 25 | ml-engineering | none | directive-only | training-affecting change states an eval/model-card note |
| 26 | observability | none | directive-only | hot-path or prod-facing change states which metric/log covers it |
| 27 | partnerships-bd | none | spawn-only — external negotiation judgment, no repo-local signal |
| 28 | performance-engineering | none | gate-now | hot-path change carries a measurement (issue #960's own example) |
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
| 43 | ux-engineering | none | gate-now | user-visible surface diff carries an accessibility+design check reference (shares row 1's gate) |

## Accumulation

This proposal is not accumulation-cost-shaped: it adds one draft document
and no runtime code; there is no per-call or per-session cost to
project.

## Prioritization (RICE) across gate-now candidates

Evidence for reach/impact below is internal repo structure (file counts),
not user research — this is an internal-tooling prioritization, not a
market one, so it is scored but not claimed as Mom-Test-grade evidence.

| Cluster (rows) | Reach (role-sessions/month, est.) | Impact (1-3) | Confidence (0-1) | Effort (dev-days) | RICE |
|---|---|---|---|---|---|
| design/UX (18, 43, and 7/1 as directive) | 10 | 2 | 0.6 | 3 | 4.0 |
| performance (28) | 4 | 3 | 0.5 | 2 | 3.0 |
| api-design (2) | 5 | 2 | 0.5 | 2 | 2.5 |
| architecture directive (3) | 6 | 2 | 0.4 | 4 | 1.2 |

Reach/effort are estimates (no historical per-role session log exists to
derive them from — flagged as an assumption, not a finding, per the
scout directive's source-citation rule). Highest RICE: **design/UX
cluster (rows 18, 43)** — proposed as the first gate to land in phase 2.

## Pre-registered hypothesis (first gate: design/UX rationale check)

- **Metric**: false-positive rate — role-session turns where the gate
  blocks a Write/Edit to a user-facing surface that did NOT need a
  design rationale.
- **Threshold**: false-positive rate < 10% measured over the first 20
  triggered instances after landing.
- **Decision rule**: if false-positive rate stays < 10% after 20
  instances, keep the gate default-on (go); if it exceeds 10%, downgrade
  it to directive-only (pivot) and re-evaluate after refining the
  trigger heuristic; if triggered fewer than 20 times in the first 30
  days, the test is inconclusive and the gate stays on with the count
  re-measured at 60 days.
- **Guardrail metric**: total Write/Edit turns blocked by ANY gate must
  not increase by more than 5% session-wide (this new gate must not
  become a second choke point stacked on existing ones) — status is
  unmeasured until the gate ships; this is a placeholder registration
  for whoever executes phase 2.
- **ITWWS follow-up**: if the design/UX gate validates, apply the same
  rationale-citation pattern to accessibility (row 1) and observability
  (row 26) next, since they share the "surface diff needs a citation"
  shape.

## What did not work

None.
