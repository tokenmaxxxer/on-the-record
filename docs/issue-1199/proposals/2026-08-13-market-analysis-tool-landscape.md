---
subject: issue-1199
role: market-analysis
loop_state: scope-proposed
status: proposed
files:
  - docs/handbooks/market-analysis-norms.md
  - market-analysis/plugins/mece-proposal/README.md
  - market-analysis/plugins/evidence-rigor/README.md
  - market-analysis/plugins/five-forces/README.md
  - market-analysis/plugins/competitor-mapping/README.md
  - market-analysis/plugins/jtbd-fit/README.md
  - docs/issue-1199/reports/market-analysis.md
---

# Proposal: fold market-analysis's surveyed tool landscape into the rulebook (issue-1199)

All file paths above (except the last) live in the separate rulebook
repo (tokenmaxxxer/market-analysis-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook — see
docs/issue-1199/reports/market-analysis/survey.md), not in this working
tree; phase 2 branches and commits there directly, mirroring the
issue-1199 brand-design/interaction-design/ux-engineering precedent.

## Decision framed

Whether the market-analysis role's rulebook (handbook + five plugin
checklists) should absorb design moves from the tool ecosystem its
practitioners actually use, so this role's phase-1 proposals and
phase-2 records reach the completeness those tools' users expect —
without turning the rulebook into a tool catalog. Downstream hand-off
target: the same five plugin checklists every future market-analysis
issue's phase-1/phase-2 writes are gated against.

## Frameworks selected + why each answers a distinct question

Not new analytical frameworks (industry attractiveness / competitive
positioning / customer-need fit are already the role's three, per
docs/handbooks/market-analysis-norms.md section (a).2) — this proposal
maps tool design moves onto the existing three-framework structure:

- Klue, Crayon → competitive positioning (competitor-mapping,
  evidence-rigor): how a competitor-list entry is structured and dated.
- SimilarWeb → industry attractiveness (five-forces): how a Porter's
  force verdict is quantified.
- G2 → customer-need fit (jtbd-fit): how a differentiation verdict is
  evidenced.
- AlphaSense → cross-cutting evidence planning (mece-proposal): how a
  phase-1 evidence plan classifies primary vs. secondary sourcing.

No framework is included "because it's standard" — each is included
because a checklist gap named in the current-state survey maps to it
one-for-one (see survey.md).

## Evidence plan

Primary sourcing: none required for this proposal itself (it modifies
methodology text, not a market claim). Secondary sourcing: each of the
five tools' adoption-evidence and design-move claims is backed by at
least one web-fetched source (vendor page, third-party market survey,
or review-platform documentation), logged in scout-brief.md's Sources
list — minimum one independent source per tool, two where adoption
figures came from a market-size estimate (Klue, Crayon).

## Adoption rationale

This role's decision boundary is a competitive gate ("does this spec
survive against the competitive/customer landscape"), not a
market-sizing task (per handbook section (b)'s scope note). The five
selected tools were chosen because each one's design move closes a gap
in exactly one of the role's five existing gated sections (five-forces,
competitor-list, jtbd-landscape-verdict, evidence appendix, phase-1
evidence plan) — not because they are generically popular tools; a
tool with no mapped gap (e.g. Owler) was surveyed and explicitly
skipped for that reason.

## Plugin-reflection plan

`directive.sh`: no change in any of the five plugins — the directive
stubs only source core canon's role-directive dispatch and carry no
role-specific checklist text. Record fields: no new required section or
spec field — all five upgrades add a line inside an already-required
section (five-forces-summary, competitor-list, jtbd-landscape-verdict,
evidence appendix, phase-1 evidence plan), never a new top-level
heading. Gates (`gate.sh`): no mechanical change in this fan-out unit —
the five gate.sh scripts keep checking presence only (section marker +
citation marker), same as today; whether a future gate should
mechanically check for a date-stamped citation or a fixed
per-competitor field set is named as future work, out of this unit's
scope (see Out of scope below).

## What will be done

Add one "Tool learnings (issue-1199)" subsection to the methodology
handbook, five entries, each capped to a short paragraph:

1. **Klue** (klue.com; ~$45M ARR per Crunchbase-sourced estimate, cited
   in a multi-source competitive-intelligence market survey — see
   scout-brief Sources). Problem: a competitor-list entry written as
   free prose omits the fields a decision actually needs (price point,
   positioning claim, why deals are won/lost against them). How: a
   battlecard format with named, fixed fields per competitor rather
   than a paragraph. Upgrades: competitor-mapping's per-entry citation
   requirement gains a companion line — each entry states pricing,
   positioning, and win/loss-reason as distinct labeled fields, not
   folded into one sentence.

2. **Crayon** (crayon.co; ~$70M ARR per the same multi-source survey —
   see scout-brief Sources). Problem: a competitor pricing-page or
   product-page citation goes stale silently; the same URL can support
   a true claim today and a false one next quarter with no way to tell
   which. How: continuous change-tracking on the source page, so every
   captured fact carries the date it was observed. Upgrades:
   evidence-rigor's evidence-block requirement gains a line — every
   citation states the date the source was read, not only the URL.

3. **SimilarWeb** (similarweb.com; industry-standard competitive
   benchmarking tool per its own and third-party competitor-analysis
   guides — see scout-brief Sources). Problem: a Porter's-forces
   verdict of "high"/"low" rivalry or new-entrant threat can rest on
   impression alone, with no way to check it later. How: a quantified
   proxy metric (traffic share, market-share estimate) behind every
   competitive-strength claim, not a bare adjective. Upgrades:
   five-forces's per-force citation requirement gains a line —
   competitive-rivalry and threat-of-new-entrants verdicts must cite a
   quantified proxy metric (traffic, revenue estimate, funding count),
   not only a qualitative source.

4. **G2** (g2.com; Score = (Market Satisfaction + Market Presence) / 2,
   gated on a minimum review count and a shared category before a
   product appears in a comparison grid — see scout-brief Sources).
   Problem: a JTBD differentiation verdict can rest on a single
   favorable data point, and conflates "customers prefer it" with
   "customers can find/reach it." How: a dual-axis score plus a
   minimum-evidence-volume floor before a verdict is allowed to stand.
   Upgrades: jtbd-fit's verdict-clause requirement gains a line — the
   differentiation verdict must cite at least two independent evidence
   points, and separately address preference (why chosen) and reach
   (how discovered/accessed).

5. **AlphaSense** (alpha-sense.com; over 4,000 enterprise clients
   including 88% of the S&P 100, per the vendor's own published
   adoption figures — see scout-brief Sources). Problem: an "evidence
   plan" that just says "we'll gather sources" doesn't tell a reviewer
   whether a claim rests on a primary interview/filing or a secondary
   aggregator repeating someone else's number. How: an explicit
   primary-vs-secondary source split, with primary sourcing (expert
   interviews, filings, transcripts) tracked as its own evidence class.
   Upgrades: mece-proposal's "Evidence plan" element gains a line — the
   plan names, per claim category, whether primary or secondary
   sourcing is expected, and the minimum independent-source count for
   each.

Companion README edits (all five plugins): one sentence each pointing
to the new handbook subsection, mirroring the issue-1199
README-mirrors-handbook pattern already used for brand-design.

docs/issue-1199/reports/market-analysis.md is phase-2 output, written
only after approval opens phase 2, per contract v3 s19.

## Out of scope

- Any change to the five plugins' gate.sh mechanical logic — the
  fold-in changes handbook wording and README pointers only; whether a
  future gate should mechanically check for dated citations or
  per-competitor fields is a separate, larger change tracked at the
  issue level, not this fan-out unit.
- Owler — surveyed and explicitly skipped (see scout-brief: weaker
  adoption signal than the other five, and its design move is already
  covered by Klue's structured-field pattern).
- Installing or depending on any of the five surveyed tools — the
  fold-in borrows the design move only.

## How you'll know it worked

Phase 2 diff, reviewed against this proposal, adds exactly the five
entries above (each carrying tool name, adoption-evidence citation,
problem, how, and the checklist line it upgrades) plus the five
one-line README pointers, with no deletion of existing handbook or
README text.

## Sources

See docs/issue-1199/reports/market-analysis/scout-brief.md's Sources
list (same PR) for the full set of URLs consulted for adoption
evidence and design-move claims.
