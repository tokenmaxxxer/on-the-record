kind: report
subject: issue-1199
doc-type: record
loop_state: landed

# customer-support — issue #1199 tool-landscape record

ticket_id: n/a (methodology fold-in, not a support ticket)
csat_score: n/a (methodology fold-in, not a support ticket)
resolution_summary: Folded four distilled tool-landscape learnings
  natively into `tokenmaxxxer/customer-support-rulebook`'s
  `customer-support/handbook.md` (an L0 self-serve escalation tier, a
  reuse-before-drafting + ticket-action-bundling playbook step,
  close-time CSAT attribution, and scenario-naming in
  `resolution_summary`); no code, only the rulebook methodology and
  this evidence record.

amendments-reconciled: issuecomment-5277512631 (posted 2026-08-13T07:44:11Z
by JiwonJung94: "Verdict: PR #? → escalate (depth or impact axis did not
clear)"). Reconciled: no PR existed for this role's branch at the time
of that comment — canonical: `gh pr list --repo tokenmaxxxer/customer-
support-rulebook --head issue-1199/customer-support` (this turn's tool
transcript) returned empty immediately before this comment surfaced.
The verdict's `PR #?` placeholder is unresolved, and no PR-preflight
gate on this branch had run yet to produce a depth/impact verdict at
that timestamp — this comment is not evaluating this role's work
product and needs no content change here; it is recorded, not acted
on, so the thread is not silently dropped.

amendments-reconciled: issuecomment-5277618420 (posted 2026-08-13T07:56:03Z
by JiwonJung94: "Judgment opened: PR #? — candidate decision on branch
`issue-1199/finance-unit-economics` (4 path(s) changed) entered
delegated-judgment evaluation."). Reconciled: this comment names branch
`issue-1199/finance-unit-economics`, a different role's branch entirely
— not `issue-1199/customer-support` — so it evaluates finance-unit-
economics's work product, not this role's; no content change needed
here, recorded so the thread is not silently dropped.

## SLA table (unchanged by this fold-in, restated for reference)

canonical: `git -C /tmp/csr-1199 show a1663e1 -- customer-support/handbook.md`
(this turn's tool transcript) — §1 is not part of this commit's diff;
table below is copied unchanged from `handbook.md` §1.

| Priority tier | Impact rating | Urgency rating | First response time target | Resolution time target | Escalation trigger time |
|---|---|---|---|---|---|
| P1 | High | High | 15 min | 4 h | 1 h unresolved |
| P2 | High | Medium | 30 min | 8 h | 2 h unresolved |
| P3 | Medium | Medium | 4 h | 24 h | 8 h unresolved |
| P4 | Low | Low/Medium | 24 h | 72 h | 24 h unresolved |

## Escalation path (as landed by this fold-in's commit)

canonical: `git -C /tmp/csr-1199 show a1663e1 -- customer-support/handbook.md`
(this turn's tool transcript) — full diff adding the L0 row below to
`handbook.md` §2.

| Tier | Trigger condition | Owner | Timeout |
|---|---|---|---|
| L0 | New inbound message arrives, before any human triage begins | Support Team Lead (owns self-serve macro/article accuracy) | Attempt an automated macro/article match immediately on intake; must hand off to L1 within the same session if no confident match exists, the customer explicitly asks for a human, or the match fails to resolve on first send |
| L1 | L0 finds no confident match, or ticket is not yet triaged after L0 | Support Agent | Must classify against SLA table and respond within tier's first-response target |
| L2 | L1 cannot resolve within tier's escalation trigger time, or ticket is P1/P2 at intake | Support Lead | Must resolve or reassign within remaining resolution-time budget for the tier, else escalate to L3 |
| L3 | L2 identifies a product defect, outage, or cannot resolve within remaining SLA budget | Engineering On-call | Must acknowledge within 15 min of L2 hand-off and drive to resolution or mitigation |

## 5-whys check (unchanged by this fold-in, restated for reference)

canonical: `git -C /tmp/csr-1199 show a1663e1 -- customer-support/handbook.md`
(this turn's tool transcript) — §5 is not part of this commit's diff;
the five questions below are copied unchanged from `handbook.md` §5,
which the recurring-pattern scenario D still governs:

1. Why are customers hitting this?
2. Why doesn't the current product flow or documentation prevent the confusion or error?
3. Why hasn't this been fixed already?
4. Why would a support-side workaround not be sufficient going forward?
5. Why would fixing this require product/engineering change rather than a support process change?

## KCS content fields (this record, treated as one article entry)

Issue: Rulebook methodology lacked pre-human deflection tiering,
reproducible ticket-action bundling, reuse-before-create discipline,
and close-time CSAT attribution — a fold-in gap, not a customer
ticket.
Environment: `tokenmaxxxer/customer-support-rulebook` main, file
`customer-support/handbook.md`, sections §2/§3/§4/§6; conditional on
that repo's handbook-based (no separate playbook/*.md) convention as
it exists on `main` at commit `a1663e1`'s parent.
Cause: These four gaps had no prior rule (per `docs/issue-1199/
reports/customer-support/survey.md`'s "Gaps this fold-in targets"),
not a regression — the field's leading tools each embody a design move
the handbook never adopted.
Resolution: Four handbook edits landed on branch
`issue-1199/customer-support` (external commit `a1663e1`), scoped to
`handbook.md` only; applies wherever that repo's handbook governs, not
conditionally per environment beyond the file/section scope above.
Metadata: lifecycle state = landed (external PR opened this turn,
awaiting human review per this record's `loop_state`); reuse: any
future customer-support tool-landscape fold-in should re-check this
record's four learnings before re-deriving the same ones.

## Playbook-scenario shape (this record's own subject, not a new handbook scenario)

Trigger: This fold-in itself is triggered by issue #1199's per-role
tool-survey requirement, applied against the four gaps in `docs/issue-
1199/reports/customer-support/survey.md`.

Decision criteria: Each of the four surveyed tools/methodologies was
adopted only where it mapped onto a real, named gap in the existing
handbook (survey.md's "Gaps this fold-in targets" list); nothing was
adopted speculatively.

Response: N/A for this record's own subject — the resulting scripts/
response templates are the four handbook.md scenarios A-D. canonical:
`git -C /tmp/csr-1199 show a1663e1 --stat` (this turn's tool
transcript) shows the single-file diff carrying the per-scenario
Ticket-actions line; full per-scenario text is under "What was done"
learning 1 below.

Escalation condition: N/A for this record's own subject (no ticket to
escalate). canonical: `git -C /tmp/csr-1199 show a1663e1 --stat` (this
turn's tool transcript, same citation) shows the same commit carrying
the new L0 escalation-path row described under "What was done"
learning 2 below.

## What was done

Surveyed four category-leading tools/methodologies for the
customer-support domain (adoption-evidence method, web-fetched, no
pretrained-recall listing): Zendesk (ticketing/help-desk), Intercom's
Fin (live-chat automated deflection), the KCS methodology / Consortium
for Service Innovation (knowledge reuse), and Nicereply vs. Delighted
(CSAT/NPS survey tooling). Full survey and scout-brief trail:
canonical: `git log -1 --format=%H -- docs/issue-1199/reports/customer-support/survey.md docs/issue-1199/reports/customer-support/scout-brief.md docs/issue-1199/proposals/customer-support.md`
(this turn's tool transcript) → commit `3d67d80` on this branch,
`docs/issue-1199/reports/customer-support/survey.md`, `docs/issue-1199/
reports/customer-support/scout-brief.md`, and `docs/issue-1199/
proposals/customer-support.md` (this repo).

Applied four learnings natively into
`tokenmaxxxer/customer-support-rulebook`'s `customer-support/
handbook.md` (no tool name or attribution in that repo — the mapping
below is the only place tool identity is recorded):

code_under_review:
- customer-support/handbook.md

1. **Zendesk** (help-desk/ticketing platform). Adoption evidence:
   ~28% help-desk-software category share, 100,000+ companies, per
   https://expandedramblings.com/index.php/zendesk-facts-and-statistics/
   and https://sqmagazine.co.uk/zendesk-statistics/. Problem: a
   response written as prose alone is not reproducible — a second
   agent hitting the same trigger has to reconstruct the same ticket
   actions from memory. How: a "macro" bundles response text with
   structured ticket actions (tag, priority, macro id) as one atomic,
   reusable unit. Learning → upgrades: `handbook.md` §3, each of
   scenarios A-D gained a Ticket-actions line (e.g. Scenario A: tag
   `account-lockout`, priority P2, macro `reset-link-sent`) alongside
   its existing script.
2. **Intercom** (Fin, live-chat automated agent). Adoption evidence:
   Fin resolves ~66% of customer questions before human hand-off, per
   https://research.com/software/reviews/intercom and
   https://greetnow.com/blog/live-chat-statistics. Problem: a support
   flow that starts triage at the first human tier spends L1's
   first-response SLA budget on tickets a self-serve step could have
   completed. How (canonical: `git -C /tmp/csr-1199 show a1663e1 --
   customer-support/handbook.md` this turn's tool transcript, applied
   diff): an explicit pre-human deflection step with its own named
   owner, timeout, and hand-off condition, tracked apart from
   human-tier resolution. Learning → upgrades: `handbook.md` §2, a new
   L0 escalation-path row (trigger: new inbound before human triage;
   owner: Support Team Lead; timeout: immediate attempt, hand off to
   L1 on no confident match / explicit human request / failed first
   send).
3. **KCS / Consortium for Service Innovation** (knowledge-reuse
   methodology). Adoption evidence: sole certifying body for KCS;
   cited adopters (Autodesk, Dell, HP Enterprise, Salesforce, others)
   report up to 50% improved first-resolution time in 3-9 months, per
   https://invgate.com/itsm/knowledge-management/kcs and
   https://library.serviceinnovation.org/KCS/KCS_v6/KCS_v6_Adoption_Guide/000_Introduction/020_KCS_Benefits.
   Problem: the same resolution gets free-composed from scratch every
   time its trigger recurs, instead of being reused. How: the "Evolve
   Loop" — search/reuse an existing article before drafting, flag for
   update only on no match. Learning → upgrades: `handbook.md` §3, a
   new "Reuse before drafting" step ahead of the scenario list.
4. **Nicereply vs. Delighted** (CSAT/NPS survey tooling). Adoption
   evidence: comparative adoption coverage across small-business/
   support-workflow feedback tooling, per
   https://www.zigpoll.com/content/nicereply-vs-delighted-features-pricing-verdict
   and https://www.nicereply.com/more/delighted-vs-nicereply. Problem:
   a CSAT score collected in a later, disconnected batch send cannot
   be traced back to the script/escalation path that earned it. How:
   Nicereply's category-distinguishing move — a one-click survey
   embedded into the workflow at ticket close, tied to that specific
   ticket. Learning → upgrades: `handbook.md` §4 (a sentence tying
   `csat_score`'s survey trigger to ticket-close time and scenario
   attribution) and §6 (`resolution_summary` now names the resolving
   scenario A/B/C/D/other and reused macro/article id, so a later
   `csat_score` is attributable to a specific scenario).

## Why

Issue #1199 (northpole req#1/req#5): a role's rulebook should reach the
completeness real practitioners' field-leading tools already embody,
not just its own internally-derived rules. This role's prior handbook
(landed under issue-19) already covered SLA derivation, a three-tier
escalation path, four scenarios, an evidence-metric tie-in, and a
5-whys check — but had no pre-human deflection tier, no reproducible
ticket-action bundling, no reuse-before-create discipline, and no
close-time CSAT attribution, each of which is a must-be in its
surveyed field's leading tools (`docs/issue-1199/reports/customer-
support/scout-brief.md`, Sweep angles 1-4).

## Evidence metric

This fold-in is expected to move **FCR** and **CSAT**: the L0 tier
(learning 2) increases the share of tickets resolved before ever
reaching a human agent, which is itself a form of first-contact
resolution; ticket-action bundling (learning 1) and reuse-before-
drafting (learning 3) reduce the chance an agent's manual
reconstruction of a known resolution drifts from what actually worked,
protecting FCR on repeat triggers; and close-time CSAT attribution
(learning 4) makes the existing FCR→CSAT causal link (`handbook.md`
§4, pre-existing) actually traceable back to which scenario/tier
produced a given score, rather than a score nobody can act on.

## Upstream basis

- `docs/issue-1199/reports/customer-support/survey.md` (this repo,
  commit `3d67d80`)
- `docs/issue-1199/reports/customer-support/scout-brief.md` (this
  repo, commit `3d67d80`)
- `docs/issue-1199/proposals/customer-support.md` (this repo, commit
  `3d67d80`)
- External commit: canonical: `git -C /tmp/csr-1199 log -1 --format=%H`
  (this turn's tool transcript) → `a1663e122275a88c2e6c6f23d224041c784e82ce`
  on `tokenmaxxxer/customer-support-rulebook` branch
  `issue-1199/customer-support`, pushed to origin this turn.
- Issue-level APPROVE: `APPROVE issue-1199/customer-support`, posted by
  approvers.md account `JiwonJung94` (canonical: `gh issue view 1199
  --repo tokenmaxxxer/on-the-record --comments` this turn's tool
  transcript, exact-string match at the comment preceding "author:
  JiwonJung94 / association: member").

## Open findings

None — the four gaps named in `docs/issue-1199/reports/customer-
support/survey.md` are each addressed by one learning above; no
unresolved question remains for this fold-in's scope.

## What did not work

None.
