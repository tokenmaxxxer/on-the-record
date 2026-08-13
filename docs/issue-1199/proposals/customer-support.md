---
status: proposed
files:
  - customer-support/handbook.md
---

# issue-1199 (customer-support): tool-landscape fold-in

kind: proposal
subject: issue-1199

Proposal: docs/issue-1199/proposals/customer-support.md

## Background

Issue #1199 (northpole req#1/req#5) asks every role to survey the
plugins/tools practitioners in its domain actually use, with adoption
evidence, and fold distilled learnings into the rulebook as this
role's own native rules — no per-tool attribution and no tool-catalog
section in the public rulebook; the full evidence trail stays in this
on-the-record repo. Separate program from #1174. Read basis:
`docs/issue-1199/reports/customer-support/survey.md` and `docs/issue-
1199/reports/customer-support/scout-brief.md` (both written this
turn).

## Target reader

A phase-2 implementing session (this role) editing
`tokenmaxxxer/customer-support-rulebook`'s `customer-support/
handbook.md` directly — no new file, since main carries no separate
`playbook/*.md` axis files (`docs/issue-1199/reports/customer-support/
survey.md`, "Rulebook write surface" section). No further scouting
needed; the scout brief already carries the sourced findings.

## Proposed structure

Four edits to `handbook.md`, each traced to a scout-brief finding:

1. **§2 Escalation path** (SLA/escalation claim) gains an **L0** row
   (self-serve/deflection, ahead of L1), with a named owner (Support
   Team Lead) and a timeout (immediate attempt, hand off to L1 on no
   confident match / explicit human request / failed first send).
   Source: `docs/issue-1199/reports/customer-support/scout-brief.md`
   §Sweep angle 2 (Intercom's Fin-agent deflection-before-human
   pattern, ~66% auto-resolution). Upgrades: the escalation-path
   plugin's tier requirement — L0 is a genuine tier with
   trigger/owner/timeout, not a vague pre-step.
2. **§3 Support playbook** (playbook claim) gains a "Reuse before
   drafting" step ahead of the scenario list, and each of scenarios
   A-D gains a **Ticket actions** line (tag/priority/macro id)
   alongside its existing script. Source: `docs/issue-1199/reports/
   customer-support/scout-brief.md` §Sweep angle 1 (Zendesk's macro =
   response text + actions as one atomic unit, ~28% category share)
   and §Sweep angle 3 (KCS Evolve Loop's reuse-before-create,
   Consortium-cited adopters). Upgrades: the playbook-scenario
   plugin's script field — a resolution becomes reproducible by any
   agent, not reconstructed from memory each time.
3. **§4 Evidence metric** (evidence-metric claim) gains a sentence
   tying `csat_score`'s survey trigger to ticket-close time and
   scenario attribution. Source: `docs/issue-1199/reports/customer-
   support/scout-brief.md` §Sweep angle 4 (Nicereply's close-time,
   ticket-attached survey vs. Delighted's generic batch send).
   Upgrades: the evidence-metric plugin's CSAT citation from a
   named-but-unconnected metric to one with a stated collection-timing
   mechanism.
4. **§6 Record fields**, `resolution_summary` bullet gains a
   requirement to name the resolving scenario (A/B/C/D/other) and
   reused macro/article id. Source: `docs/issue-1199/reports/customer-
   support/scout-brief.md` §Adopt/skip item 4. Upgrades: the
   record-fields plugin's `resolution_summary` — a `csat_score` can
   now be attributed back to a specific scenario instead of only to
   the ticket in isolation.

No new required record field is introduced (record-fields plugin's
three-field contract stays `ticket_id`/`csat_score`/`resolution_summary`
unchanged); the scenario/macro-id naming is additive detail inside the
existing `resolution_summary` string, not a fourth field.

## Out of scope

- No tool name, vendor name, or "learned from X" attribution anywhere
  in `tokenmaxxxer/customer-support-rulebook` — the four edits above
  read as this role's own rules.
- No new plugin, no new gate, no change to SLA-tier derivation logic
  (§1, SLA claim) or the 5-whys question set (§5, five-whys claim) —
  both already meet the field's must-bes per `docs/issue-1199/reports/
  customer-support/scout-brief.md`'s "Gap line" paragraph (§1's
  Impact×Urgency derivation and §5's five-question shape already match
  the category norm, so neither the SLA table nor the 5-whys set gets
  an edit here).
- No verbatim copying of any surveyed tool's UI text or documentation.

## How this will be verified

- The four edits land as a single commit on
  `tokenmaxxxer/customer-support-rulebook`'s `issue-1199/customer-
  support` branch, reviewable as a diff against `main`.
- Phase-2 record (`docs/issue-1199/reports/customer-support.md`, this
  repo) cites the external commit sha and PR, and states the evidence
  trail (tool, adoption evidence, problem, how, upgraded target) for
  each of the four learnings.
