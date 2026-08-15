---
subject: issue-1199
role: market-analysis
kind: scout-brief
loop_state: scouted
---

# Scout brief: market-analysis tool landscape (issue-1199)

Mode: parallel WebSearch, one sweep round across four angles
(competitive-intelligence platforms, traffic/market-share estimation,
company/competitor databases, review-based comparison grids), followed
by one targeted deepening round on the thinnest adoption-evidence hit
(AlphaSense).

## Category patterns observed in the surveyed tools

- A structured per-competitor field set (pricing, positioning, win/loss
  reason), not freeform prose with a trailing link (Klue's battlecard
  model).
- A citation that is a dated snapshot, not a static reference, because
  the underlying page changes (Crayon's change-tracking model).
- A quantified proxy metric backing a qualitative verdict (SimilarWeb's
  traffic/market-share estimate behind "strong"/"weak" rivalry framing).
- A dual-axis score (satisfaction + presence) rather than one blended
  verdict, and a minimum evidence-volume bar before a verdict counts
  (G2's Score = (Satisfaction + Presence) / 2, gated on >= 50 reviews and
  a shared category).
- An explicit primary-vs-secondary source split, with primary interviews
  tracked as their own evidence class (AlphaSense's Channel Checks vs.
  its document/transcript library).

## Performance axes the surveyed tools compete on

1. Structured-fact capture vs. narrative summary (Klue/Crayon vs. a
   plain notes doc).
2. Evidence freshness/traceability over time (Crayon's tracked-change
   history vs. a one-time snapshot).
3. Verdict-behind-a-number vs. verdict-as-impression (SimilarWeb, G2).
4. Primary-source reach (expert interviews, filings) vs.
   secondary-only aggregation (AlphaSense vs. most competitor-tracking
   tools, which are secondary-only).

## Adopt / skip against this role's checklists

canonical: docs/handbooks/market-analysis-norms.md and the five
market-analysis/plugins/*/README.md files (rulebook repo, read this
session).

- Adopt into existing checklist wording: a fixed per-competitor field
  set for competitor-list entries (mirrors Klue); an as-of date on every
  evidence citation (mirrors Crayon); a quantified proxy metric
  requirement on the two most rivalry-sensitive forces (mirrors
  SimilarWeb); a two-independent-evidence-point minimum plus a
  satisfaction/reach split for the jtbd verdict (mirrors G2); a named
  primary-vs-secondary source split in the phase-1 evidence plan
  (mirrors AlphaSense).
- Skip: any live platform integration, paid-tier feature, or dashboard
  UI — outside this role's write scope (docs/issue-<n>/proposals/*.md,
  docs/issue-<n>/reports/market-analysis.md); the fold-in borrows the
  design move, not the tool. Also skip Owler (community-verified
  company graph): weaker adoption signal than the other five in this
  sweep (0.20% Market Research segment share vs. Crunchbase's 7.42% per
  the same source, and its core "direct-vs-indirect" idea is already
  covered by Klue's structured-field pattern) — redundant, not a
  distinct design move worth a sixth entry.

## Segment fit

This role's phase-2 record is a text report (five-forces-summary,
competitor-list, jtbd-landscape-verdict, evidence appendix), not a live
dashboard or API integration, so the fold-in targets checklist wording
in the handbook and the five existing plugin READMEs rather than new
tooling or gate logic.

## Field-vs-current-checklist gap

canonical: docs/issue-1199/reports/market-analysis/survey.md, "What the
current checklist wording does NOT yet ask for" section (this session,
same PR). Five named gaps there, one per plugin, each closed by exactly
one of the five entries below.

## Sources

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
