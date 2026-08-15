# Scout brief — issue-1199 partnerships-bd tool landscape

Mode: batched-sequential (3 WebSearch calls, one message, no parallel
subagent dispatch available in this session) — 1 stage, well under the
5-stage/3min budget; stopped at judge point 1 since all 3 angles landed
on the same must-be pattern (structured, routed, named data — not a
free-text field) and no further round would change a build decision.

## Category sweep (adoption-evidence angles: PRM/CRM, deal-desk/CLM)

1. **PRM / partner-CRM category** — Introw, Attio, HubSpot, Pipedrive,
   Salesforce lead cited "best for partner management" 2026 roundups;
   PRM software market sized ~$3.33B (2026) per Grand View/Fortune
   Business Insights, growing double-digit CAGR — high, durable
   adoption, not a fad tool.
2. **Deal-desk category** — DealHub, Rattle, PandaDoc, Ironclad,
   DocuSign CLM cited across 2026 "best deal desk" roundups. Rattle's
   distinguishing adoption claim: it embeds the deal desk directly into
   Slack rather than a new portal, and its cited adoption driver is
   exactly that it "fits existing workflow rather than disrupting it."
3. **CLM/term-sheet category** — Ironclad, DocuSign CLM, PandaDoc,
   Linkpoint repeatedly named as the enterprise-tier tools; overlap with
   angle 2 (deal-desk and CLM tooling converge on the same vendor set),
   confirming this is the field's real center of gravity, not noise
   from one search.

## Judge point 1 — must-bes extracted

- **Must-be 1 (PRM category):** partner data is modeled with an
  explicit tier/segment, not a flat list — tiering drives resourcing
  and review cadence differently per partner.
- **Must-be 2 (deal-desk category):** approvals succeed when routed
  through a workflow surface the counterpart already uses, not a new
  standalone portal — naming *where* an approval happens is itself a
  design move, not an afterthought.
- **Must-be 3 (CLM category):** termination/exit clauses in
  professionally-run CLM tooling are structured with explicit cure
  periods and explicit data/IP-handling terms as separate fields, not
  folded into free-text "termination conditions."

## Gap line

This role's rulebook (`partnerships-bd/reference/deliverable-shapes.md`)
already had a strategic/ICP-fit axis (no tier field), a governance
sub-section (authority thresholds, no named routing surface), and an
exit/termination sub-section (conditions/notice/wind-down, no cure
period or data/IP split). All three must-bes were gaps, not
already-covered ground — each becomes a targeted upgrade rather than a
restatement of existing rule content.

## Adopt / skip

- **Adopt:** partner-tier naming on the strategic/ICP-fit axis;
  named-approval-routing-surface requirement on governance; explicit
  cure-period + data/IP-handling split on exit/termination.
- **Skip:** cloning any tool's actual UI/portal/workflow-engine concept
  (this role produces a document, not software) and skip naming any
  tool in the rulebook itself (out of scope per this issue's fold-in
  rule — evidence trail lives only in this report, not the public
  rulebook).

Sources:
- https://www.introw.io/blog/best-partner-relationship-management-software
- https://www.introw.io/blog/top-crm-for-partner-management
- https://www.grandviewresearch.com/industry-analysis/partner-relationship-management-market-report
- https://www.fortunebusinessinsights.com/partner-relationship-management-market-116173
- https://www.heyiris.ai/blog/top-9-deal-desk-software-solutions-to-boost-revenue
- https://dealhub.io/glossary/deal-desk/
