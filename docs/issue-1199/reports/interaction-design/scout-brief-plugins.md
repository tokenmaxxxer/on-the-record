kind: report
subject: issue-1199
doc-type: reference

# interaction-design — Claude Code plugin/skill scout brief (2026-08-14 amendment)

canonical: WebSearch results this turn (queries: "best Claude Code
plugin marketplace skills 2026 design wireframe UX Figma"; "\"claude
code\" plugin skill accessibility usability testing wireframe github
stars"), plus WebFetch on the two highest-signal hits — full pages
listed under Sources below.

## Skip record

Not skipped — scouting ran (2 sweep angles: general "design/wireframe/
Figma Claude Code plugins" and "accessibility/usability-testing Claude
Code plugin github stars"), followed by 1 deepening round (WebFetch on
Owl-Listener/designer-skills and gotalab/uxaudit). 3 stages total,
within the 5-stage/3min budget.

## Category must-bes (from sweep)

canonical: WebSearch results, github.com/Owl-Listener/designer-skills
and github.com/gotalab/uxaudit pages (see Sources)

- A broad, high-adoption design-focused Claude Code skill collection
  exists (Owl-Listener/designer-skills, 2.1k stars) covering the whole
  design cycle — research, interaction, prototyping-testing,
  visual-critique, handoff — not a single-purpose tool.
- A narrower, officially-marketplace-listed automated UX-testing plugin
  exists (gotalab/uxaudit) that runs live journey simulations rather
  than static review.
- Figma's own first-party Claude Code skills (surfaced via
  claude-plugins-official and Figma's own blog/resource pages) are the
  vendor-published bridge between this role's spec artifacts and the
  actual design tool practitioners hand off to.

## Performance axes (dimensions the field competes on)

canonical: WebFetch results, Owl-Listener/designer-skills and
gotalab/uxaudit pages (see Sources)

1. Static judgment (heuristic evaluation, visual critique as a review)
   vs. live simulated execution (uxaudit's Playwright journey walks
   that actually attempt signup/task-finish/error recovery on a
   running app).
2. Breadth of one collection (designer-skills' 8 plugins spanning the
   whole design cycle) vs. depth on one narrow check (uxaudit's ~40
   checks across 5 categories, each tied to a published design
   standard).
3. canonical: gotalab/uxaudit page (see Sources) — evidence format:
   uxaudit returns a prioritized fix plan with screenshot evidence,
   consumable directly by a coding agent, vs. designer-skills' handoff
   workflow which emits specs/measurements/assets/states/QA-checklist
   for a human developer.

## Adopt / skip

- Adopt as a pattern: uxaudit's explicit split of automated-checkable
  categories (accessibility compliance, usability patterns) from
  categories needing a simulated task walk-through (core experience
  finish, whether a user can reach signup and recover from an error) —
  this sharpens the existing manual-vs-automated accessibility split
  already folded in from the prior (domain-tool) round into a broader
  state-machine-shaped judgment: which flow states need a walked
  simulation, not just a presence check.
- Adopt as a pattern: designer-skills' `/interaction-design:map-states`
  and `/interaction-design:error-flow` commands treat state-mapping and
  error-flow as first-class, separately-named artifacts, not a
  sub-bullet under a general flow section — reinforces (does not
  duplicate) this role's existing `id-state-completeness` plugin
  requirement.
- Skip: adopting uxaudit's live-Playwright-execution mechanism itself —
  this role specs screens/flows and never runs a live app or writes
  test automation; the judgment (separate the automated-checkable list
  from the simulated-walkthrough list) is adopted, not the tool's
  execution layer, per the scout-directive's "never clone the exemplar"
  rule.
- Skip: Figma's own skill surface (variable/auto-layout/token
  mechanics) — that is the downstream design-tool operator's concern,
  not this role's spec-writing concern; noted as secondary context only
  (issue amendment's own carve-out for domain tools as secondary
  context).

## Gap line

canonical: docs/issue-1199/proposals/2026-08-13-interaction-design-tool-landscape.md
and docs/issue-1199/reports/interaction-design.md (this repo, read this
turn) — the prior round surveyed Figma, Maze, UserTesting, Tokens
Studio for Figma, and axe-core: general interaction-design-domain
practitioner tools, none of them a Claude Code plugin or skill. The
already-landed manual-vs-automated accessibility split (from axe-core)
and the fidelity-scope/test-sizing/token-default rules stand unchanged;
this round's gap is narrower and additive: none of those four rules
distinguish "checked by static review" from "checked by a walked
simulation" at the level of an individual flow state, which is exactly
what uxaudit's category split and designer-skills' map-states/error-flow
commands both independently converge on.

## Sources

- https://github.com/Owl-Listener/designer-skills
- https://github.com/gotalab/uxaudit
- https://uxplanet.org/figma-skills-for-claude-code-bb05a21984fd
- https://www.figma.com/resource-library/claude-skills-for-design/
- https://www.figma.com/blog/introducing-claude-code-to-figma/
- https://mcpmarket.com/tools/skills/wireframing-1

## kind / loop_state

kind: report
loop_state: phase-1-scouted
