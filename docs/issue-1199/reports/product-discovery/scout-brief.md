---
subject: issue-1199
role: product-discovery
kind: scout-brief
---

# Scout brief: product-discovery Claude Code plugin-ecosystem sweep (issue-1199)

Mode: batched-sequential fallback in this session — three WebSearch calls
issued in one turn (parallel tool-call dispatch, not serialized one at a
time), one judge-point round, no further deepening needed (saturation:
the same handful of repos — phuryn/pm-skills, deanpeters/Product-Manager-Skills
— surfaced across all three angles). 1 sweep stage, 0 deepening stages
(saturated at judge point 1).

Angles: (1) JTBD/product-discovery plugin marketplaces, (2) RICE/ICE and
opportunity-solution-tree skill plugins, (3) most-installed PM-skill
marketplaces generally.

## Exemplars (adoption evidence)
- **phuryn/pm-skills** — 25,262 stars, 2,713 forks (`curl -s
  https://api.github.com/repos/phuryn/pm-skills`, run this session).
  "PM Skills Marketplace: 100+ agentic skills, commands, and plugins —
  from discovery to strategy, execution, launch, and growth."
- **deanpeters/Product-Manager-Skills** — 6,463 stars, 780 forks (`curl
  -s https://api.github.com/repos/deanpeters/Product-Manager-Skills`,
  run this session). "Product Management skills framework built on
  battle-tested methods for Claude Code, Cowork, Codex, and AI agents."
- Secondary (broader PM-skill collections, not discovery-specific):
  alirezarezvani/claude-skills (24,435 stars),
  pmprompt/claude-plugin-product-management (44 stars, low — noted, not
  used as a primary exemplar).

## Must-bes (Kano) observed across exemplars
- A discovery flow decomposes into named, separate skills per stage
  (ideate → identify-assumptions → prioritize-assumptions →
  opportunity-solution-tree → brainstorm-experiments), never one
  monolithic "discovery" skill.
- Assumption-prioritization is its own explicit step, distinct from
  feature-prioritization (pm-skills: `identify-assumptions-*` +
  `prioritize-assumptions` are separate skills from `prioritize-features`).
- Opportunity-solution-tree tooling explicitly ranks which
  experiment/proof-of-concept to run first, not just which opportunity
  is biggest (deanpeters: "recommends the best proof-of-concept to test
  first").

## Performance axes exemplars compete on
1. Depth of the risk/assumption taxonomy (pm-skills' 8 risk categories
   for new products vs. 4 for existing) — richer taxonomy vs. simpler,
   faster taxonomy.
2. Whether next-experiment selection is impact-only or
   impact-times-cost/learning-value (deanpeters' PoC recommendation
   move is the sharper of the two).

## Adopt / skip
- Adopt: risk-ranked assumption ordering with a named next-experiment
  attached at registration time (pm-skills `prioritize-assumptions` —
  "Impact × Risk matrix with experiment suggestions").
- Adopt: ranking sibling solution branches under one opportunity by
  which next test teaches the most per unit cost, not by apparent
  solution size (deanpeters `opportunity-solution-tree`).
- Skip: full 8-category risk taxonomy reproduction — this role's
  existing `hypothesis-preregistration.md` already carries a
  metric/guardrail structure; duplicating a parallel risk-category list
  would bloat rather than sharpen it.

## Gap line
Existing rulebook (`hypothesis-preregistration.md`,
`opportunity-solution-tree-branching.md`) already covers: registering a
numeric threshold+decision rule before data, naming guardrails,
prioritizing opportunities-not-solutions, generating many solutions
before selecting, pruning stale/invalidated branches. Missing before
this fold-in: (a) no rule for *which* assumption to register first when
several compete for the next test slot; (b) no rule for *which* sibling
solution's assumption test to run next once an opportunity already has
multiple candidate solutions. Both gaps map directly to the two adopted
patterns above.

Sources:
- https://github.com/phuryn/pm-skills
- https://github.com/deanpeters/Product-Manager-Skills
- https://github.com/alirezarezvani/claude-skills
- https://github.com/pmprompt/claude-plugin-product-management
