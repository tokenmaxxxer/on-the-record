---
subject: issue-1199
role: risk-management
loop_state: scope-proposed
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-15-risk-management-plugin-tool-landscape.md
---

# Proposal: fold Claude Code plugin/skill landscape into risk-management-rulebook (issue-1199, 2026-08-14 amendment)

kind: proposal
subject: issue-1199

## Governance/context
risk-id: RM-1199-01
risk-description: the five new playbook rules folded in from surveyed
  Claude Code plugins/skills (severity-gated action-queue ordering,
  control-source-first hierarchy, residual-re-score-on-completion
  trigger, framework-clause threshold anchoring, dual qualitative/ALE
  scoring) go unused by future risk-management sessions because they
  are buried as rule 5/6 additions rather than being surfaced at the
  point a session actually applies the axis file.
risk-category: operational

### Objective linkage
This entry's objective is issue-1199's own acceptance criterion 4 (the
fold-in must visibly upgrade the role's output quality) — an unused new
rule fails that objective as surely as a rule never written.

## Assessment
likelihood: possible
impact: moderate
risk-score-inherent: 3x3=9 (moderate)
risk-score-residual: 2x2=4 (low)

## Risk treatment
existing-controls: each new rule is a numbered decision rule inside the
  same axis file every risk-management session already reads for that
  axis (no new file, no separate index to miss), each carries an
  explicit "when X, do Y" trigger condition matching the existing
  rules' format, and each carries a `source:` citation consistent with
  the file's existing convention.
risk-appetite-threshold: low — this rulebook's appetite statement
  (playbook/appetite-tolerance-threshold.md) treats an unused or
  untraceable decision rule as equivalent to a stale threshold, which
  the rulebook's own removal-heavy convention treats as low-tolerance.
mitigation-owner: risk-management role
mitigation-plan: no dedicated follow-up action; the existing
  removal-heavy rule-review convention already in each axis file
  (see e.g. aggregation-consolidation.md rule 4) will surface an unused
  rule the same way it surfaces a stale register entry, at the next
  axis-file review.

## Monitoring and review
review-date: 2027-02-15

## Request

Fold learnings from the most-adopted Claude Code plugins/skills in the
risk-management domain into `tokenmaxxxer/risk-management-rulebook`'s
existing `playbook/` axis files, as bounded, native (non-attributed)
decision-rule additions. Full current-state survey and sweep evidence:
`docs/issue-1199/reports/risk-management/scout-brief.md` (this repo).

## Constraints

- Only Claude Code plugins/skills count as primary evidence (2026-08-14
  operator amendment); adoption graded via
  stars/forks/multi-source-mentions.
- No tool name or `source:`-as-prose framing inside the rulebook body
  itself (2026-08-13T06:36:54Z native-application amendment) — every
  new rule reads as this role's own judgment; provenance stays in this
  repo's phase-2 record only.
- Additions must be bounded: one rule per existing axis file, no new
  axis files, no tool-catalog section.
- Phase 1 proposal: this document is phase-1 only. APPROVE is out of scope of this write; execution begins only once the approval condition below is satisfied.

## Rationale

Considered and rejected: adding a sixth standalone
`tool-landscape.md` axis file cataloging the surveyed tools directly —
rejected because the 2026-08-13T06:36:54Z amendment forbids a
tool-catalog section in the rulebook, and a prior role's attempt at
exactly this shape (incident-response, per the merged
conformance-review record's cross-role note) was flagged Incorrect for
it. Instead, each learning is folded as a native rule inside an
existing axis file, matching the accepted conformance-review PR #1525
shape (docs/issue-1199/reports/conformance-review.md, this repo).

Considered and rejected: adopting the full FMEA/FTA/HAZOP
identification-method-selection machinery from borghei's skill —
rejected as out of scope, since this rulebook has no
identification-method-selection axis to extend; adopting it would
require a new axis file, which the native-application/bounded-fold-in
constraint above disallows for this round.

## What will be done

Read basis: `docs/issue-1199/reports/risk-management/scout-brief.md`
(this repo, written this session) — current-state survey of the five
axis files plus a parallel-fan-out sweep of Claude Code risk/GRC
skills.

Four Claude Code plugins/skills surveyed with adoption evidence
(GitHub stars/forks, this session; full detail in the scout brief):

1. **Sushegaad/Claude-Skills-Governance-Risk-and-Compliance** (829
   stars, 170 forks) — GRC skills anchoring per-risk register entries
   to specific regulatory-framework clause citations (e.g. NIST AI RMF
   category codes) rather than a generic bucket.
2. **borghei/Claude-Skills** `risk-management-specialist` skill (479
   stars, 109 forks) — ISO 14971-style five-stage lifecycle: control
   selection follows an inherent-safety > protective-measures >
   information hierarchy, and residual-risk re-evaluation is its own
   distinct post-control lifecycle stage.
3. **Masriyan/Claude-Code-CyberSecurity-Skill** (335 stars, 60 forks)
   — risk register scoring combining a qualitative band with a
   quantitative annualized-loss-expectancy (ALE) figure.
4. **ddunnock/claude-plugins** `fmea-analysis` skill (10 stars) —
   secondary, direct-domain-match confirmation only (per the
   adoption-evidence method's allowance for a named secondary entry,
   the same allowance the merged conformance-review precedent used for
   codacy-specs): AIAG-VDA Action Priority prioritizes severity first,
   ahead of occurrence/detection, unlike a multiplied RPN score that
   can bury a rare-but-catastrophic risk.

Five native rule additions (no tool/plugin name or `source:`-as-prose
framing in the rulebook body; each new rule's `source:` line points to
the surveyed skill's repo, matching every existing rule's own
convention):

1. `playbook/aggregation-consolidation.md` rule 5 — order a
   consolidated action queue by severity band first, likelihood/
   velocity only breaks ties within a band, never a multiplied
   combined score.
2. `playbook/appetite-tolerance-threshold.md` rule 5 — when a
   threshold is bound by an external regulatory/contractual limit,
   cite the exact clause/control ID on the entry, not only the
   entity-level appetite band.
3. `playbook/likelihood-impact-scale.md` rule 5 — when a risk carries a
   plausible dollar-denominated loss estimate, record the ALE figure
   alongside the qualitative band, not in place of it.
4. `playbook/monitoring-review-cadence.md` rule 5 — when a mitigation
   control completes, trigger an immediate residual-risk re-score and
   re-derive cadence from that fresh score.
5. `playbook/response-strategy-selection.md` rule 6 — when selecting a
   Mitigate control, rank candidates source-removal > protective/add-on
   > information-only, pick the highest-ranked feasible one.

Delivery target: `tokenmaxxxer/risk-management-rulebook`, branch
`issue-1199/risk-management`, editing the five files above, one commit,
PR opened; then this repo's phase-2 record
(`docs/issue-1199/reports/risk-management.md`) updated citing the
branch/PR and the scout-brief evidence trail, `loop_state: landed`.

## Out of scope

- Tool-landscape rework for any other role.
- Building or modifying the shape-check gate
  (`gates/playbook_depth_gate.py`) — issue's step-1 infra unit.
- Adopting any surveyed repo's identification-method-selection
  machinery or full skill catalog beyond the five named rule additions.
- A standalone tool-catalog axis file (rejected above).

## How you'll know it worked

All five rules land as edits to the named target files in
`tokenmaxxxer/risk-management-rulebook` in one delivery; this repo's
phase-2 record documents the rulebook PR/branch and cites the
scout-brief evidence trail for each rule without duplicating tool
names/URLs into the rulebook body; `loop_state: landed` is set only
once the named files are actually edited, committed, and pushed; the
risk-management row in issue #1199's 43-item tracker stays/becomes
checked.

## Approval

The `APPROVE issue-1199/risk-management` comment posted by JiwonJung94
(a `docs/specs/approvers.md` account) at 2026-08-15T02:38:33Z
(canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate`, read this session) postdates both the 2026-08-13T06:36:54Z
native-application amendment and the 2026-08-14 plugin-ecosystem
amendment this proposal is scoped to, so it authorizes this proposal's
phase 2 (single-account mode) without requiring a further comment.
Phase 2 proceeds in the same session, same branch, as this proposal.
