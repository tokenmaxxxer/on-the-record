---
status: proposed
files:
  - docs/issue-745/reports/product-discovery/current-state.md
  - docs/issue-745/reports/product-discovery/scout-brief.md
  - docs/issue-745/proposals/product-discovery.md
---

# Proposal — issue #745: session cost-structure valuation

Phase 1 only, per this role's own contract obligation and the issue's own step-1 assignment ("product-discovery") and explicit "결정 유보" section. This proposal values three cost centers (thinking, records, `execution-observation`) against `docs/issue-745/reports/product-discovery/current-state.md`'s re-derivation of the issue's cited 2026-08-11 analysis, scores reduction candidates per item, and pre-registers a metric/threshold/guardrail/revert-condition package for the strongest candidate per item. It does not pick which candidate to actually build — that stays the operator's call, per the issue's own instruction not to pre-commit an execution choice in this phase.

## Item 1 — Thinking budget

**Current spend** (current-state.md): thinking is 49.26% of output tokens summed across the measured sessions, 44.98% median per session, inside the issue's cited 40-51%. No per-role or per-session thinking-effort configuration exists anywhere in this repo today.

**Candidates scored (RICE)** — reach/impact scored qualitatively against "sessions this repo runs per week across active issue×role branches" (no direct cadence log exists, same limit `docs/issue-707/proposals/product-discovery.md` noted for its own RICE table):

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Note |
|---|---|---|---|---|---|---|---|
| 1 | Judgment-tier effort conditioning: extend the same contract-pinned-vs-judgment-needing reasoning-effort split freelunch already applies to its own dispatched workers to primary role sessions — mechanical/gate-checking turns at reduced effort, judgment-bearing turns (product-discovery, architecture, review) at full effort | 4 | 3 | 0.4 | 3 | 1.6 | Uses an effort-level parameter, not a raw token cap — sidesteps the budget-cap viability risk below |
| 2 | Raw per-role `budget_tokens` cap via env var (the issue's own suggested direction) | 5 | 4 | 0.2 | 2 | 2.0 | Higher raw RICE, but confidence is capped low for a real reason, not arithmetic caution: `scout-brief.md` found newer Claude models reportedly reject a manually-set `budget_tokens` outright (400 error), and this repo has no existing wiring (`derived: grep -rn "budget_tokens\|thinking_budget\|effort" roles/*.json spawn.py` — no hits) to confirm which model version, or whether the parameter is even accepted, before betting effort on it |
| 3 | No change (status quo) | 5 | 1 | 0.9 | 0 | — | Baseline candidate; kept only as the fallback every other candidate must beat |

Candidate 2 scores higher on raw arithmetic but is not preferred over candidate 1 for the same reason `docs/issue-707/proposals/product-discovery.md` and its own cited `docs/issue-573/proposals/product-discovery.md` precedent both reject a higher-RICE candidate that skips a load-bearing must-be: candidate 2's must-be (the model actually accepts the parameter) is unconfirmed, and RICE screens, it does not verdict.

**Pre-registered hypothesis package — candidate 1 (judgment-tier effort conditioning).**

Guardrail metric: `rework_outcome_rate`, named and non-empty at this same registration moment, distinct from the primary metric below — using the ledger's existing `outcome` field, the non-clean values already tracked (`refused`, `silent-failure`, `failed-no-commit`, `errored`, `progressed-dirty-tree`, `uncommitted-work`, all confirmed present as ledger `outcome` values by `docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md`'s own outcome-distribution table) — a token-output win on the primary metric while this guardrail rises is a reduced-trust result, not a win, because a rework loop is the cheapest available signal that reduced thinking degraded judgment.

- **Metric**: `output_token_reduction_pct` = (a conditioned role's mean output tokens per session over its next 20 sessions after conditioning ships) versus (that same role's mean output tokens per session over its most recent 20 sessions before conditioning ships).
- **Threshold**: `output_token_reduction_pct` at least 15% for the conditioned role population, measured against the pre-conditioning baseline computed at test-start (not assumed from today's aggregate figures, which mix conditioned and unconditioned roles).
- **Guardrail status at measurement**: `rework_outcome_rate` for the conditioned role's post-conditioning window must not exceed its own pre-conditioning baseline (same before/after windows as the primary metric) by more than 3 percentage points, stated explicitly next to the primary metric's value, never implied.
- **Decision rule**: `output_token_reduction_pct` at or above threshold AND `rework_outcome_rate` within the guardrail tolerance → **persist**, and consider widening which roles/turns are classified as mechanical. If the primary metric falls short → **pivot**: the mechanical/judgment classification boundary was likely drawn wrong (too little of a role's own turns counted as mechanical); redraw it before retrying, don't abandon the shape. If the guardrail breaches regardless of the primary metric → **kill immediately** and revert conditioned roles to full effort — no pivot on the guardrail, because judgment degradation is the exact harm the issue's own "thinking buys judgment quality" framing warns against.
- **Revert condition**: a guardrail breach at any single measurement, or the primary metric still under threshold after one redraw of the mechanical/judgment boundary.

## Item 2 — Record output ("기록물")

**Current spend** (current-state.md): markdown-targeted Write/Edit calls are roughly half of all such calls in sampled implementation sessions, and markdown content is 22.2% of non-thinking output tokens — inside the issue's cited 17-24%. Separately, and new to this analysis: a large share of the repo's record/proposal population is never cited again by any later session, and the specific boilerplate `## What did not work` section — present across the large majority of role records — is quoted or referenced by zero other files repo-wide.

**Candidates scored (RICE):**

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Note |
|---|---|---|---|---|---|---|---|
| 1 | Citation-informed section tiering: keep the sections that measurably get cross-issue-cited (named verdicts, RICE tables, root-cause findings) at full fidelity; default named-boilerplate sections with a zero-citation track record (e.g. `## What did not work` when nothing did not work) to a one-line terse form unless the author has real content for them | 5 | 3 | 0.7 | 2 | 5.25 | Grounded directly in current-state.md's own citation measurement, not a guess at what's padding |
| 2 | Blanket record-length cap (e.g. hard word limit per section) | 5 | 2 | 0.3 | 1 | 3.0 | Rejected as a candidate to pre-register: a length cap can't distinguish a terse-but-load-bearing RICE table from terse boilerplate — it would cut both alike, the same undifferentiated-cut failure every scouted source (`scout-brief.md`) warns against |
| 3 | No change (status quo) | 5 | 1 | 0.9 | 0 | — | Baseline candidate |

**Pre-registered hypothesis package — candidate 1 (citation-informed section tiering).**

Guardrail metric: `cross_issue_citation_rate`, named and non-empty at this same registration moment, distinct from the primary metric below — a reduction in output tokens while this guardrail falls is not a reduced-trust result, it directly undoes the thing this candidate exists to protect (the institutional-memory sections current-state.md found already earn their keep).

- **Metric**: `boilerplate_output_token_share` = (output tokens spent on the named low-citation section set — `## What did not work` when empty, current-state/scout-brief-equivalent scratch content once a phase's next step has consumed it) divided by (a record's total output tokens), measured over the next 20 records written under the tiered format.
- **Threshold**: `boilerplate_output_token_share` falls by at least 30% relative to the pre-tiering baseline (the same measurement, same section set, over the most recent 20 records before the format change ships).
- **Guardrail status at measurement**: `cross_issue_citation_rate` for the named high-citation categories (`proposals/*.md`, `reports/<role>.md`, repo-wide `docs/reports/*.md`) must not fall below the category's own current baseline established in current-state.md by more than 5 percentage points, stated explicitly next to the primary metric's value.
- **Decision rule**: the primary metric at or beyond its 30% threshold AND `cross_issue_citation_rate` within the 5-point guardrail tolerance for every named category → **persist**. If the token reduction falls short → **pivot**: the low-citation section set was drawn too narrowly; widen it using the next citation-rate measurement round rather than loosening the guardrail. If any named category's `cross_issue_citation_rate` breaches its tolerance → **kill immediately** for that category's tiering (revert to full verbose sections for it), because a citation-rate drop means real institutional memory was cut, not padding.
- **Revert condition**: any named category's guardrail breach at any single 20-record measurement window, checked per category independently — a breach in one category kills tiering for that category only, not the others.

## Item 3 — `execution-observation`

**Current spend** (current-state.md): a large minority of the 219-session snapshot and roughly a third of its total cost belong to `execution-observation` (both figures land within a point of the issue's own cited 35%/33%), with the large majority of its Write/Edit calls targeting `.md` — no committed code output. Already sparse in practice, not universal: `implementation.md` reports far outnumber `execution-observation*` records across issue directories — meaning most implemented issues never spawn it at all, contrary to a literal "every issue" reading of the issue's own "이슈당 구현 2세션 + 관찰 2세션" framing.

**Candidates scored (RICE):**

| # | Candidate | Reach | Impact | Confidence | Effort | RICE | Note |
|---|---|---|---|---|---|---|---|
| 1 | Mechanically enforce the `board_condition` `roles/execution-observation.json` already states in prose ("an executable artifact landed AND no execution-observation record exists yet for this commit sha") — a docs-only PR's own preflight gate refuses/skips an `execution-observation` spawn attempt, mirroring warrant-directive's own already-normalized docs-only fast path for the before-landing hunter dispatch | 3 | 4 | 0.8 | 2 | 4.8 | Enforces a rule that already exists in writing; does not invent a new condition |
| 2 | Sampling-based reduction (spawn `execution-observation` on a random fraction of otherwise-qualifying PRs) | 3 | 3 | 0.3 | 2 | 1.35 | Rejected as a candidate to pre-register: sampling is exactly the shape `docs/issue-476/decisions/2026-08-08-h1-h2-mechanism-adr.md` rejected for the underlying trust-ban mechanism itself ("still self-report shaped" reasoning generalizes: an unsampled PR's fabricated claim ships un-caught by construction, not by bad luck) |
| 3 | No change (status quo) | 5 | 1 | 0.9 | 0 | — | Baseline candidate |

**Pre-registered hypothesis package — candidate 1 (enforce the existing board_condition).**

Guardrail metric: `fabrication_survival_rate` — already a named metric in `docs/issue-476/reports/execution-observation.md` — named and non-empty at this same registration moment, distinct from the primary metric below. This item's guardrail carries a stricter bar than the other two items' guardrails, mirroring `docs/issue-707/proposals/product-discovery.md`'s own precedent for a zero-tolerance invariant guardrail: a self-report shipping unverified because an exemption misfired is not a reduced-trust result, it is the exact contract violation `#476` exists to prevent, so no nonzero rate is acceptable here.

- **Metric**: `execution_observation_sessions_per_landed_pr`, computed separately for two populations — (a) PRs whose entire diff is under `docs/` (no executable artifact), and (b) all other landed PRs — over the next 20 landed PRs after the gate ships.
- **Threshold**: population (a) falls to zero `execution_observation_sessions_per_landed_pr` (the board_condition already says this population should never qualify); population (b) stays within measurement noise of its own pre-change baseline (no more than a 10% relative change either direction — a rise would mean the gate is over-triggering, which is also a defect worth catching, not just a cost regression).
- **Guardrail status at measurement**: `fabrication_survival_rate` over the same measurement window must be exactly zero for population (b) — not a percentage tolerance, per the zero-tolerance framing above — stated explicitly next to the primary metric's value, never implied.
- **Decision rule**: population (a) at zero AND population (b) within its tolerance band AND the guardrail at zero → **persist**. If population (a) does not reach zero → **pivot**: the docs-only diff check itself has a gap (e.g. a PR mixing one code file with mostly docs is being misclassified); tighten the check's diff-classification logic before retrying. If the guardrail is ever nonzero, regardless of the cost metrics → **kill immediately**: the gate is refused and every PR reverts to the unconditioned always-eligible path until redesigned — no pivot is acceptable on this guardrail, mirroring `#476`'s own decision-record precedent for invariant violations.
- **Revert condition**: any nonzero guardrail reading, or population (a) failing to reach zero across two consecutive measurement windows after one classification-logic fix.

## ITWWS (if this works we should ...), per item

- **Item 1**: if candidate 1 persists at threshold, re-run `scout-brief.md`'s open question (does the harness's actual model accept a manual `budget_tokens`) as a targeted follow-up check, since a confirmed-viable raw budget cap (candidate 2) could then be layered on top of effort-tier conditioning rather than substituted for it.
- **Item 2**: if candidate 1 persists, extend the same citation-rate measurement to a second round after the tiered format has been in use long enough to accumulate its own citation history, since the current baseline (`derived: see current-state.md's repo-wide citation inventory`) predates any tiering and cannot yet show whether the tiered sections keep earning citations at the same rate as their untiered predecessors.
- **Item 3**: if candidate 1 persists, consider whether the same enforced-board_condition pattern generalizes to other roles in this repo that also carry an unenforced `use_when`/`board_condition` clause — named here as a follow-up scope, not actioned in this proposal.

Deferred to whichever role and issue the operator assigns each ITWWS to next — none of the three is actioned in this phase.

## 결정 유보 (decision deferred)

This proposal stops here, per the issue's own instruction. Three cost centers are now valued with real numbers traceable to the live ledger (`current-state.md`), each carries at least one RICE-screened, fully pre-registered candidate with a named metric, numeric threshold, guardrail, and revert condition, and none of the three has been picked for execution. Whichever candidate(s) the operator chooses to actually run move to a step-2 role the operator assigns next; this PR carries no code changes and no execution-role assignment.
