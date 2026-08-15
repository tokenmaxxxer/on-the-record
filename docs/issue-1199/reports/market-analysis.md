---
subject: issue-1199
role: market-analysis
kind: record
loop_state: landed
---

# Record: market-analysis tool-landscape fold-in (issue-1199)

## Status note (2026-08-15)

The section below, starting at the next `##` heading through "Open
findings," is the 2026-08-13 round's record, surveying the general
competitive-intelligence domain-tool market (Klue, Crayon, SimilarWeb,
G2, AlphaSense).

canonical: `gh pr view 1541 --comments`, read this session.
PR #1541 carrying that round is closed unmerged — orchestrator refusal
comment, 2026-08-15: "this branch executed a pre-existing 2026-08-13
phase-1 proposal surveying general practitioner tools — the 2026-08-14
operator amendment on issue #1199 supersedes that reading."

canonical: `gh issue view 1199 --comments`, read this session.
The 2026-08-14 operator amendment comment ("Requirement amendment
(operator, 2026-08-14)") retargets the survey to the Claude Code
plugin/skill ecosystem, not domain tools. That section stays below as
superseded-historical, not deleted. The binding work for this branch
is the "## 2026-08-14 plugin-ecosystem rework (phase 2 executed)"
section further down.

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

amendments-reconciled: issuecomment-5299675518 ("Judgment opened: PR
#? — candidate decision on branch `issue-1199/customer-support` (4
path(s) changed) entered delegated-judgment evaluation.", canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5299675518`,
read this session) names branch issue-1199/customer-support, not this
market-analysis unit or its rulebook-repo counterpart branch — no
content amendment warranted.

amendments-reconciled: issuecomment-5299803250 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)", canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5299803250`, read
this session) is a delegated-judgment verdict for a different,
unnumbered candidate PR — the comment body names no PR number and no
reference to this market-analysis unit or its rulebook-repo
counterpart branch (tokenmaxxxer/market-analysis-rulebook,
issue-1199/market-analysis) — so no content amendment to this record
is warranted.

## 2026-08-14 plugin-ecosystem rework (phase 2 executed)

This section is a redo of the tool-landscape fold-in above, under the
issue's 2026-08-14 operator amendment (supersedes the broad reading
the section above was authored under).

canonical: `gh issue view 1199 --comments`, read this session, the
"Requirement amendment (operator, 2026-08-14)" comment.
The amendment retargets the survey to the Claude Code plugin/skill
ecosystem, not domain tools — the five entries surveyed in the section
above are general competitive-intelligence/market-research domain
tools; none names a Claude Code plugin/skill repo, so per the
amendment that round alone does not satisfy issue-1199's Acceptance
criterion 1.

Surveyed the Claude Code plugin/skill ecosystem for tools relevant to
this role's domain (competitive/market research), adoption evidence
via the tech-feasibility method (stars/forks/multi-source mentions),
this session:

- **VoltAgent/awesome-claude-code-subagents** — a curated collection
  of 100+ Claude Code subagents.
  canonical: `curl -s https://api.github.com/repos/VoltAgent/awesome-claude-code-subagents`,
  run this session → `"stargazers_count": 24309, "forks_count": 2825`.
  Contains a `market-researcher.md` subagent (direct domain match).
  canonical: WebFetch of
  `https://raw.githubusercontent.com/VoltAgent/awesome-claude-code-subagents/main/categories/10-research-analysis/market-researcher.md`,
  run this session, quoting its stated completion checklist verbatim:
  "Market data accurate verified", "Sources authoritative maintained",
  "Analysis comprehensive achieved", "Insights actionable delivered" —
  plus a structured JSON progress object counting
  `markets_analyzed`, `consumers_surveyed`, `competitors_assessed`,
  `opportunities_identified`. Problem: a market-research deliverable
  can read as internally consistent narrative while silently skipping
  a required analytical domain, with no explicit signal that each
  domain was actually covered. How (same canonical WebFetch): coverage
  is gated on a named, checkable verification list plus explicit
  per-domain counters, instead of being an implicit property of the
  prose. Learning → upgrades the rulebook's (b).1 five-forces
  requirement: a `five-forces-summary` verdict must carry an explicit
  "checked" marker distinct from its narrative, so a reviewer can tell
  evaluated-and-low apart from not-evaluated.

- **phuryn/pm-skills** — a marketplace of 100+ agentic
  product-management skills, commands, and plugins.
  canonical: `curl -s https://api.github.com/repos/phuryn/pm-skills`,
  run this session → `"stargazers_count": 25260, "forks_count": 2712`.
  Its `pm-market-research` plugin bundles a `market-sizing` skill and
  a `competitor-analysis` skill (direct domain match).
  canonical: WebSearch results this session quoting the plugin's own
  skill listing verbatim: `market-sizing` — "Estimate market size
  using TAM, SAM, and SOM with top-down and bottom-up approaches";
  `competitor-analysis` — "Analyze competitors with strengths,
  weaknesses, and differentiation opportunities". Problem: a single
  cited market-size figure inherits whichever bias its one
  source/method carries, and a competitor's "differentiation
  opportunity" gets described in passing rather than stated as its own
  checkable fact. How (same canonical WebSearch results): two
  independent derivation paths for any sizing number used as evidence,
  and a named, separate differentiation-opportunity field per
  competitor. Learning → upgrades (b).1: a market-size or revenue
  figure cited to back a rivalry/buyer-power verdict must be
  corroborated by a second independent source or derivation before
  being cited as established (this stays an evidence-rigor rule on
  numbers already in scope; it does not reopen (b)'s existing
  TAM/SAM/SOM-out-of-scope line, since no sizing task is added) — and
  (b).2: every `competitor-list` direct-competitor entry states a
  named "differentiation opportunity" field, not only descriptive
  facts.

canonical: `curl -s https://api.github.com/repos/alirezarezvani/claude-skills`,
run this session → `"stargazers_count": 24435, "forks_count": 3433`.
Skipped this round: `alirezarezvani/claude-skills` — its
`research-ops/market-research` skill's stated scope, per this
session's WebSearch results, overlaps `pm-skills`'s two adopted skills
above.

canonical: `curl -s https://api.github.com/repos/daymade/claude-code-skills`,
run this session → `"stargazers_count": 1336, "forks_count": 214`.
Also skipped: `daymade/claude-code-skills` — star count an order of
magnitude below the two adopted entries above.

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook
show HEAD --stat`, run this session → 3 files changed:
docs/handbooks/market-analysis-norms.md,
market-analysis/plugins/five-forces/README.md,
market-analysis/plugins/competitor-mapping/README.md (all three paths
are in the separate market-analysis-rulebook repo, not this working
tree).
Applied (not referenced) both learnings directly into those three
target files in the separate rulebook repo
(tokenmaxxxer/market-analysis-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook), on
branch issue-1199/market-analysis. Per the operator's
native-application amendment (2026-08-13T06:36:54Z comment on this
issue, same precedent applied to the 2026-08-13 round above): no
`source: <tool repo>` framing and no tool-catalog section in the
rulebook rule text itself — the two new rules read as this role's own
judgment; the tool names, adoption evidence, and per-insight mapping
live only in the handbook's dedicated "Tool learnings" section and in
this record. No verbatim text copied from either surveyed repo beyond
the short quoted phrases attributed above.

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/market-analysis-rulebook
log -1 --stat`, run this session → commit
`ee202226dca39f5477cd58cdabca11136693a872`, subject line "2026-08-14
plugin-ecosystem tool-landscape rework (issue #1199)".
canonical: this session's `git push origin issue-1199/market-analysis`
output → `04f7528..ee20222  issue-1199/market-analysis ->
issue-1199/market-analysis`, pushed to
origin/issue-1199/market-analysis on
tokenmaxxxer/market-analysis-rulebook.

### code_under_review
- market-analysis-rulebook repo — docs/handbooks/market-analysis-norms.md
- market-analysis-rulebook repo — market-analysis/plugins/five-forces/README.md
- market-analysis-rulebook repo — market-analysis/plugins/competitor-mapping/README.md
- docs/issue-1199/reports/market-analysis.md

### Why

canonical: `gh pr view 1541 --comments`, read this session.
Per issue-1199's 2026-08-14 amendment (northpole req#1) and the
2026-08-15 orchestrator refusal on PR #1541: the prior 2026-08-13
round surveyed general market-analysis-domain tools, not the Claude
Code plugin/skill ecosystem the amendment specifically retargets. This
round closes that gap directly against this role's own two thinnest
phase-2 fields — force-verdict coverage certainty ((b).1) and
competitor-entry differentiation ((b).2) — leaving the 2026-08-13
round's five rules untouched and superseded-as-history, not replaced.

### Upstream basis

This issue's 2026-08-14 operator amendment comment; PR #1541's
2026-08-15 refusal comment; the "Status note (2026-08-15)" section at
the top of this file.

### Open findings

None.

amendments-reconciled: issuecomment-5299825502 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)", canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5299825502`, read
this session) is a delegated-judgment verdict for a different,
unnumbered candidate PR — the comment body names no PR number and no
reference to this market-analysis unit or its rulebook-repo
counterpart branch — no content amendment warranted. Per the
issue-1174 precedent (docs/issue-1174/reports/implementation.md,
commit 8bf080a) for this same identical-unnumbered-verdict retry
pattern, further such comments landing after this point are not
re-chased.

