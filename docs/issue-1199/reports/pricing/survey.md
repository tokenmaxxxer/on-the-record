---
kind: record
subject: issue-1199
loop_state: n/a
---

# issue-1199 (pricing): Claude Code plugin/skill survey

Method: tech-feasibility adoption-evidence (stars/downloads/multi-source
mentions), per issue #1199's 2026-08-14 amendment restricting the survey
target to the Claude Code plugin/skill ecosystem.

## Search trail

- `WebSearch "Claude Code plugin marketplace pricing \"willingness to pay\" OR \"pricing strategy\" skill 2026"`
- `WebSearch "\"claude code\" plugin marketplace github stars \"pricing\" skill agent"`
- `WebFetch https://awesomeskill.ai/skill/coreyhaines31-marketingskills-pricing-strategy`
- `WebFetch https://claudemarketplaces.com/skills/refoundai/lenny-skills/pricing-strategy`
- `gh api repos/coreyhaines31/marketingskills` (verify star count directly, marketplace pages drift)
- `gh api repos/coreyhaines31/marketingskills/contents/skills/pricing/SKILL.md` (read the actual skill body)
- `gh api repos/refoundai/lenny-skills` (verify star count directly)
- `WebSearch "OpenView \"value metric\" pricing definition scales with value delivered"` (corroborating non-plugin source for the value-metric test named inside skill 1, per the depth-of-analysis requirement)

## Tool 1: `pricing` skill, coreyhaines31/marketingskills

Adoption evidence:
canonical: `gh api repos/coreyhaines31/marketingskills` output, this session — `"stargazers_count":44320,"forks_count":6959,"open_issues_count":93`, MIT-licensed, pushed 2026-07-29 (actively maintained), distributed through multiple independent marketplace mirrors
(awesomeskill.ai, claudemarketplace.net, claudemarketplaces.com — cross-marketplace
listing itself is corroborating evidence of adoption beyond a single index).

Problem it solves: practitioners asking "what should I charge / how should I
package this" get generic advice with no structured elicitation and no
distinction between the three separable pricing decisions (what's included,
what's metered, what's charged).

How (design moves), read directly from the fetched SKILL.md
(`gh api repos/coreyhaines31/marketingskills/contents/skills/pricing/SKILL.md`):
- Gathers business/value/competitive/goal context BEFORE offering any
  recommendation, and checks for a project-level context file first so it
  does not re-ask what's already stated.
- Splits "pricing" into three independent axes — packaging, pricing metric,
  price point — instead of treating "set a number" as one decision.
- Value-metric test: "as a customer uses more of [metric], do they get more
  value? If yes → good metric, if no → price doesn't align with value" —
  a binary, checkable test rather than a vague "align with value" precept.
- Good-Better-Best tier framework with explicit anchor/decoy roles: Good =
  entry, Better = the anchor/recommended tier priced to look chosen, Best =
  2-3x Better to make Better look reasonable by contrast.
- A separate "pricing page teardown" mode scoring an existing page on two
  axes: human-buyer clarity AND machine/agent-readability (can an LLM
  shortlisting tools actually parse and quote the price) — a criterion this
  rulebook's chain has no analog for.
- A "when to raise prices" signal checklist (market/business/product
  signals) plus four concrete raise strategies (grandfather, delayed
  announce, tied-to-value, restructure) — treats a price increase as a
  distinct, well-defined follow-on decision, not an ad hoc renegotiation.

Learning target: this rulebook's four-file chain (scope-gate,
method-family, design-rigor, verdict-report) covers ONLY which
willingness-to-pay research method to run and how to label its output.
Issue #1199's own PRODUCES line for this role names "pricing verdict,
tier structure, rationale" — but no file in the chain has a single rule
about tier/packaging structure. The value-metric test and GBB
anchor/decoy structuring are the clearest gap: a verdict can be correctly
labeled (per verdict-report.md's existing rules) and still assemble into
a tier structure with no value-metric check and no anchor logic.

## Tool 2: `pricing-strategy` skill, RefoundAI/lenny-skills

Adoption evidence:
canonical: `gh api repos/refoundai/lenny-skills` output, this session —
`"stargazers_count":1247,"forks_count":158,"description":"86 product
management skills from Lenny's Podcast for Claude Code and AI agents."`,
MIT-licensed, pushed 2026-07-16, also cross-listed on crossaitools.com/
claudemarketplaces.com (redirect-verified same listing).

Problem it solves: pricing set once at launch and never revisited, and
premature hard-paywalling of every premium feature before there is
evidence customers won't pay at all.

How (design moves), per the fetched marketplace description of the
skill's interactive-questionnaire structure: prompts direct diagnostic
questions ("What would customers pay today?", "When did you last change
your pricing?", "What's actually preventing you from charging more?"),
frames pricing as a decision with a stated REVISIT CADENCE (6-12 months)
rather than a set-and-forget artifact, and pushes a willingness-to-pay
conversation before shipping rather than after.

Learning target: this rulebook's scope-gate.md rule 2 already has the
right shape (reuse a prior study "within the decision's shelf life") but
leaves "shelf life" undefined — an operator has no way to tell whether a
6-month-old PSM result is still current. This skill's explicit cadence
concept is the missing operational definition for that existing rule.

## Corroborating non-plugin source (value-metric test)

OpenView Partners, "How to Capture the Right Value Metrics to Accurately
Price Your Product" (https://openviewpartners.com/blog/how-to-price-your-product/)
— states the same three-part test (legible without a spreadsheet, aligns
with how the customer receives value, scales with usage/success so
accounts expand without renegotiation) independently of the surveyed
skill, corroborating that the skill's value-metric test reflects
converged practitioner consensus rather than one author's idiosyncratic
rule.
