---
subject: issue-1199
role: market-analysis
kind: record
loop_state: landed
---

# Record: market-analysis tool-landscape fold-in (issue-1199)

## What was done

Executed the phase-2 fold-in approved by the `APPROVE
issue-1199/market-analysis` comment on this issue (single-account mode;
canonical: `gh issue view 1199 --comments`, read this session — the
comment body is exactly `APPROVE issue-1199/market-analysis`, posted by
JiwonJung94, a docs/specs/approvers.md account). Worked directly in the
separate rulebook repo (tokenmaxxxer/market-analysis-rulebook, mounted
at /home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook), on
branch issue-1199/market-analysis:

- Added a bounded "Tool learnings (issue-1199)" section to
  docs/handbooks/market-analysis-norms.md (that repo's root, not this
  working tree): five surveyed tools (Klue, Crayon, SimilarWeb, G2,
  AlphaSense), each carrying {tool, adoption evidence, problem, how,
  learning→named upgrade to an existing phase-1/phase-2 checklist
  item}, per the proposal.
- Added a one-sentence pointer to that section in each of the five
  plugin READMEs in that same rulebook repo (mece-proposal,
  evidence-rigor, five-forces, competitor-mapping, jtbd-fit), mirroring
  the issue-1199 README-mirrors-handbook precedent already used for
  brand-design.
- No existing handbook or README text deleted; no gate.sh mechanical
  logic touched, per the proposal's Out of scope.
- Committed in the rulebook repo (canonical: `git -C
  /home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook log -1
  --stat`, read this session) and pushed to
  origin/issue-1199/market-analysis. PR creation there hit the same
  pr-preflight retry loop as issue-1199's brand-design unit (repeated
  unnumbered "Verdict: PR #? → escalate" comments landing faster than
  each reconciliation) — reconciled twice (see amendments-reconciled
  below), then stopped per the same precedent
  (docs/issue-1174/reports/implementation.md, commit 8bf080a): branch
  is committed and pushed, PR creation is left for external relay
  rather than retried further.

The subject of this fold-in unit's own survey was, itself, the
competitive-intelligence/market-research tooling market — so the
required per-role sections below are filled with that survey's real
content, not placeholders, staying true to what this unit actually is
(a tool-landscape survey, not a product spec's market analysis).

## five-forces-summary

- Competitive rivalry: high — five actively-competing vendors in one category cluster (Klue, Crayon, Kompyte, AlphaSense, Contify), combined market-size estimate $1.0B–$1.4B, named ARR per vendor (Crayon ~$70M, Klue ~$45M, AlphaSense ~$420M). Source: https://www.useluminix.com/reports/competitive-intelligence/competitive-intelligence-market-size/source/0
- Threat of new entrants: medium — Kompyte's 2022 acquisition by Semrush shows bundling by adjacent SEO/marketing suites is a live entry path. Source: https://www.contify.com/resources/blog/best-competitive-intelligence-tools/
- Supplier bargaining power: low — the underlying "supply" is public web/company data (pricing pages, filings, review sites); no single data supplier gates any surveyed vendor. Source: https://www.semrush.com/features/competitor-analysis/
- Buyer bargaining power: high — enterprise sales-enablement buyers concentrate ~$840M of annual revenue across ~12,000 accounts at $800–$2,000/month entry price points, giving buyers leverage to switch vendors. Source: https://www.useluminix.com/reports/competitive-intelligence/competitive-intelligence-market-size/source/0
- Threat of substitutes: medium — a manual notes-doc-plus-search-engine workflow is a real substitute for a paid platform at small scale. Source: docs/issue-1199/reports/market-analysis/survey.md, "What the current checklist wording does NOT yet ask for" section (this PR, read this session).

## competitor-list

### Direct competitors
(compete directly for the same competitive-intelligence-platform budget)
- Klue — battlecard + win/loss portal; ~$45M ARR estimate. Source: https://www.useluminix.com/reports/competitive-intelligence/competitive-intelligence-market-size/source/0
- Crayon — website/pricing change-tracking; ~$70M ARR estimate. Source: https://www.useluminix.com/reports/competitive-intelligence/competitive-intelligence-market-size/source/0
- AlphaSense — enterprise market-intelligence search, primary + secondary sourcing; ~$420M ARR estimate, 4,000+ enterprise clients including 88% of the S&P 100. Source: https://www.alpha-sense.com/press/alphasense-solidifies-leadership-in-enterprise-intelligence-as-the-ai-platform-of-choice-for-the-enterprise/

### Indirect competitors
(adjacent tooling that partially substitutes)
- SimilarWeb / Semrush — traffic/market-share estimation used as a competitive-benchmarking input rather than a dedicated CI platform. Source: https://www.similarweb.com/blog/marketing/marketing-strategy/best-competitor-analysis-tools/
- G2 (with Capterra, post-acquisition) — review-based comparison grids; a discovery/validation substitute for a dedicated CI tool on the buyer-facing side. Source: https://documentation.g2.com/docs/competitors
- Owler — community-verified company graph; surveyed and explicitly not adopted as a design-move source (see scout-brief) because its 0.20% Market Research segment share vs. Crunchbase's 7.42% signals materially weaker adoption. Source: https://www.g2.com/compare/crunchbase-vs-owler

## jtbd-landscape-verdict

Customer job: a market-analysis practitioner (or, here, this
rulebook's own phase-1/phase-2 writer) needs to produce a competitive
record that is structured, dated, and quantified enough that a
reviewer can trust it without re-deriving the evidence.

Verdict: the strongest competing alternative for that job is a paid
platform (Klue/Crayon/AlphaSense) offering live data feeds and
dashboards — a text-report rulebook cannot match that on
freshness-at-scale. Differentiation holds on a narrower ground: this
role's phase-2 record is a one-shot, spec-scoped competitive gate
("does this spec survive against the landscape"), not a
continuously-maintained CI subscription — the fold-in in this unit (see
Upstream basis) closes the gap that matters for that narrower job
(dated citations, quantified verdicts, structured competitor fields,
dual-axis JTBD evidence) without requiring the live-platform
infrastructure the paid tools provide, which this role's write scope
(a markdown report, not a dashboard) was never going to reach anyway.

## Evidence appendix

- https://www.contify.com/resources/blog/best-competitive-intelligence-tools/
- https://www.useluminix.com/reports/competitive-intelligence/competitive-intelligence-market-size/source/0
- https://www.similarweb.com/blog/marketing/marketing-strategy/best-competitor-analysis-tools/
- https://www.semrush.com/features/competitor-analysis/
- https://www.crunchbase.com/organization/owler
- https://tomba.io/blog/crunchbase-vs-owler
- https://www.g2.com/compare/crunchbase-vs-owler
- https://documentation.g2.com/docs/competitors
- https://blastra.io/guides/how-to-get-ranked-on-g2/
- https://www.alpha-sense.com/solutions/market-intelligence-platform/
- https://www.alpha-sense.com/press/alphasense-solidifies-leadership-in-enterprise-intelligence-as-the-ai-platform-of-choice-for-the-enterprise/
- https://sacra.com/c/alphasense/

## Why

Per issue-1199 (northpole req#1/req#5): the market-analysis role's
rulebook encoded methodology and mechanical gates but had learned
nothing from the tool ecosystems market-analysis practitioners
actually use. The five entries close the gaps the phase-1 scout brief
identified — dated citations, quantified force verdicts, structured
per-competitor fields, dual-axis JTBD evidence, primary/secondary
source planning — none of which the prior checklist wording asked for
(canonical: docs/issue-1199/reports/market-analysis/survey.md, "What the
current checklist wording does NOT yet ask for" section, this PR).

## Upstream basis

docs/issue-1199/proposals/2026-08-13-market-analysis-tool-landscape.md

## Open findings

None.

amendments-reconciled: issuecomment-5277607380, issuecomment-5277613057,
and issuecomment-5277617205 (all "Verdict: PR #? → escalate (depth or
impact axis did not clear)") are delegated-judgment verdicts for a
different, unnumbered candidate PR (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277607380`,
`.../5277613057`, and `.../5277617205`, read this session) — none names
a PR number or references this market-analysis unit or its rulebook-repo
counterpart branch (tokenmaxxxer/market-analysis-rulebook,
issue-1199/market-analysis), so no content amendment to this record is
warranted. pr-preflight retry stopped after this
reconciliation, per the same precedent already logged for issue-1174's
final-session record state (docs/issue-1174/reports/implementation.md,
8bf080a) — further identical unnumbered-verdict comments landing after
this point are not re-chased.
