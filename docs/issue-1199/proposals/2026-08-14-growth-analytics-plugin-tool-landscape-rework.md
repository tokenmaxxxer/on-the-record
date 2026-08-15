---
subject: issue-1199
role: growth-analytics
loop_state: scope-proposed
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-14-growth-analytics-plugin-tool-landscape-rework.md
---

# Proposal: fold Claude Code plugin/skill landscape into growth-analytics-rulebook (issue-1199, 2026-08-14 amendment rework)

kind: proposal
subject: issue-1199

## Pre-registration fields (not applicable — meta-proposal, no new experiment)

This proposal edits the growth-analytics rulebook's pre-registration/
trust-gate METHODOLOGY text itself; it does not register a new
experiment, so the ga-prereg fields below are stated as not-applicable
rather than left absent:

- primary metric: not applicable — no new experiment is being run by this
  proposal.
- hypothesis: not applicable — no expected effect direction/magnitude is
  claimed; this is a rulebook-content edit, not a test.
- sample size: not applicable; duration: not applicable; power basis: not
  applicable — no data collection is proposed here.
- guardrail: not applicable, breach bound: not applicable — no guardrail
  metric is being monitored by this proposal.
- decision rule: not applicable — no threshold on a primary metric is
  being committed to; the "decision-cadence commitment rule" described
  below is a rulebook METHODOLOGY addition (a rule other future
  experiments must follow), not this proposal's own pre-registration.

## Problem / goal framing

canonical: docs/issue-1199/reports/growth-analytics.md and
docs/issue-1199/proposals/2026-08-13-growth-analytics-tool-landscape.md
(this repo, read this turn) — the landed 2026-08-13 fold-in surveyed
GrowthBook, PostHog, Eppo, and Amplitude/Mixpanel as general growth-
analytics-domain practitioner tools, judged by adoption evidence but not
scoped to the Claude Code plugin/skill ecosystem specifically. The
issue's 2026-08-14 amendment redefines the survey target as the CLAUDE
CODE PLUGIN/SKILL ecosystem itself, so growth-analytics' tracker line
needs this additive rework before it counts toward the amended
acceptance check. Read basis:
`docs/issue-1199/reports/growth-analytics/scout-brief-plugins.md`
(written this turn).

## Comparison set / exemplars

Two Claude Code plugins/skills surveyed with adoption evidence
(`docs/issue-1199/reports/growth-analytics/scout-brief-plugins.md`):

1. **PostHog/ai-plugin** (65 GitHub stars; official, listed on
   Anthropic's own plugin directory at claude.com/plugins/posthog) —
   ships 30+ task-specific skills and a `/posthog:experiments` command
   surface that queries the live experimentation platform's actual
   running state (flags, exposure counts, results) rather than reasoning
   from a static description of an experiment.
2. **contains-studio/agents** (12.4k GitHub stars) — its
   `project-management/experiment-tracker.md` subagent names A/B
   testing, feature flagging, cohort analysis, and rapid iteration as
   one bundled concern, with an explicit fast ship-measure-decide
   cadence discipline as its own stated value, distinct from the
   underlying statistics.

## Methodology cited

This role's existing governing methodology — Kohavi's trustworthy-
experiments literature (ga-trust), pre-registration discipline
(ga-prereg), and the AARRR funnel framework (ga-funnel) — is not
replaced. This round extends the already-landed 2026-08-13 rules
(exposure-integrity SRM check, baseline-variance power accounting,
corroborated bottleneck hypothesis, named reusable segment axis) with
two additive, plugin-ecosystem-sourced judgments the prior domain-tool
round did not cover: live-platform-state grounding and decision-cadence
commitment.

## What will be delivered

Two native rule additions, applied directly into the named target
files, phrased as this role's own judgment with no tool-repo name or
`source:` framing in the rulebook body (matching the interaction-design
and accessibility reworks' native-application convention — provenance
stays only in this on-the-record trail):

1. **Live-platform-state grounding rule** — before an experiment-trust
   walkthrough proceeds past the exposure-integrity check (the
   2026-08-13 SRM+contamination hard-stop), the walkthrough must state
   whether the reported effect and guardrail deltas were confirmed
   against a queryable live source (the experimentation platform's own
   current state) or only against a static write-up, and treat
   "unconfirmed against live state" as a confidence cap on the verdict,
   the same way an unvalidated A/A status already caps confidence.
   Upgrades: `ga-trust/agents/trust-gate-walker.md`, inserted between the
   existing step 1 (SRM + exposure integrity) and step 2 (A/A
   validation status).
2. **Decision-cadence commitment rule** — the pre-registration decision
   rule (existing step 5: a threshold on the primary metric, committed
   before data) must also name how soon after the threshold clears the
   call will actually be acted on (e.g. "next release cycle," "within 5
   business days"), so the pre-registered commitment covers not just
   the statistical trigger but the operational follow-through. Upgrades:
   `ga-prereg/hooks/directive.sh`, step 5 (decision rule).

Delivery target: `tokenmaxxxer/growth-analytics-rulebook`, branch
`issue-1199/plugin-tool-landscape`, editing
`ga-trust/agents/trust-gate-walker.md` and
`ga-prereg/hooks/directive.sh` — the same rulebook repo the prior round
edited, on files the prior round either edited directly
(trust-gate-walker.md) or edited a sibling step of (directive.sh).

## Adopt / skip rationale

Adopt: the two judgments above, because each closes a gap the scout
brief's gap line names (no existing rule requires confirming a reported
effect against queryable live platform state before a trust verdict
proceeds; no existing rule requires a decision-cadence commitment
alongside the decision-rule threshold) and each traces to one scout-brief
finding (issue requirement 4's per-tool traceability bar).

Skip: adopting PostHog's actual MCP/API integration mechanism or
contains-studio's full 40-plus-agent collection — this role produces one
walkthrough/pre-registration judgment per scope, not a live-integration
harness or a multi-agent studio; the judgment is adopted, not the tool's
surface, per the scout-directive's "never clone the exemplar" rule and
the native-application amendment's ban on tool-catalog framing in
rulebook content.

## How it will be judged

Judged done when: (a) both rules land as edits to the named target files
in `tokenmaxxxer/growth-analytics-rulebook` in the same delivery; (b)
this repo's phase-2 record (`docs/issue-1199/reports/
growth-analytics.md`) documents the rulebook PR/branch and cites the
scout-brief-plugins.md evidence trail for each rule, without duplicating
tool names/URLs into the rulebook, and sets `loop_state: landed` only
once the named upgrade files are actually edited and pushed; (c) the
growth-analytics row in issue #1199's tracker stays checked (already
checked from the prior round; this is an additive rework, not a first
landing).

## Plan for phase 2

1. On `tokenmaxxxer/growth-analytics-rulebook`, branch
   `issue-1199/plugin-tool-landscape`: add the live-platform-state
   grounding rule to `ga-trust/agents/trust-gate-walker.md` and the
   decision-cadence commitment rule to `ga-prereg/hooks/directive.sh`.
2. Open a PR against `tokenmaxxxer/growth-analytics-rulebook` (or, if
   the cross-repo PR-create guard blocks it, push the branch and log a
   filed deviation for external relay, matching the prior round's
   observed pattern in this record's existing "Open findings" section).
3. Update this repo's phase-2 record `docs/issue-1199/reports/
   growth-analytics.md` documenting the branch/PR and the evidence
   trail, and set `loop_state: landed` once the edit is pushed.

## Out of scope

- Tool-landscape rework for any other role — each fan-out unit is
  separate per issue requirement 6.
- Re-opening or re-landing the four already-landed 2026-08-13 rules
  (exposure-integrity SRM check, named reusable segment axis,
  corroborated bottleneck hypothesis, baseline-variance power
  accounting) — this rework is additive to them, not a replacement.
- Building or modifying the mechanical gate scripts
  (`ga-prereg-gate.sh` / `ga-funnel-gate.sh` / `ga-trust-gate.sh`) —
  the prior round already established that these edits stay to prose
  walkthrough/directive content only.
- Adopting PostHog's live MCP/API integration or contains-studio's full
  agent collection beyond the two named judgments.

## Approval

Awaiting a PR review Approve (two-account mode) or an issue-level
`APPROVE issue-1199/growth-analytics` comment (single-account mode) from
a `docs/specs/approvers.md` account, posted after this proposal exists,
before phase 2 (the rulebook edits and this repo's phase-2 record
update) begins, per contract v3 s19. The existing
`APPROVE issue-1199/growth-analytics` comment
(canonical: `gh issue view 1199 --comments`, this turn) predates the
2026-08-14 amendment and this proposal, and does not authorize this
rework's phase-2 work. This session accordingly stops after phase 1,
mirroring the interaction-design and accessibility units' own rework
proposals (`docs/issue-1199/proposals/2026-08-14-interaction-design-
plugin-tool-landscape-rework.md` and `docs/issue-1199/proposals/
2026-08-14-accessibility-plugin-tool-landscape-rework.md`'s "Approval"
sections, same pattern).
