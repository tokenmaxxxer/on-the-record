---
kind: report
subject: issue-1199
doc-type: reference

# ux-engineering — Claude Code plugin/skill scout brief (2026-08-14 amendment)

canonical: WebSearch results this turn (queries: "Claude Code plugin
marketplace design system tokens skill github stars 2026"; "\"claude
code\" skill plugin accessibility component storybook design
engineering github"; "storybookjs/storybook claude code plugin mcp
official announcement"; "anthropics/claude-plugins-official
frontend-design skill github stars accessibility"), plus WebFetch on
the three highest-signal hits — full pages listed under Sources below.

## Skip record

Not skipped — scouting ran (2 sweep angles: general "design-system/
tokens Claude Code plugins" and "accessibility/component/storybook
Claude Code plugin github"), followed by 2 deepening rounds (WebFetch
on wilwaldon/Claude-Code-Frontend-Design-Toolkit and
darasoba/design-engineer-plugin, plus a targeted follow-up search that
surfaced the official storybookjs/mcp plugin and
anthropics/claude-plugins-official's frontend-design skill).
canonical: WebFetch result on github.com/darasoba/design-engineer-plugin
this turn — "The plugin currently has 1 star and 1 watcher on GitHub,
indicating early-stage adoption," which is why that candidate was
dropped in favor of the two higher-adoption follow-up hits. 4 stages
total, within the 5-stage/3min budget.

## Category must-bes (from sweep)

canonical: WebSearch results, storybook.js.org/docs/ai/mcp/overview,
github.com/wilwaldon/Claude-Code-Frontend-Design-Toolkit, and
github.com/anthropics/claude-plugins-official pages (see Sources)

- An official, first-party design-tooling plugin exists
  (`@storybook/claude-code-plugin`, published by the Storybook org
  itself) that manages the component-library workflow — init, story
  writing/review, live dev-server preview, version upgrades — from
  inside a Claude Code session, backed by an MCP server exposing the
  same manifests.
- A high-adoption curated collection exists
  (wilwaldon/Claude-Code-Frontend-Design-Toolkit). canonical: WebFetch
  result on that repo this turn — "This repository has 636 stars and
  79 forks" — that layers design-token, theming, and
  accessibility-tree-based testing tools on top of Anthropic's own
  first-party skill.
- Anthropic's own marketplace (anthropics/claude-plugins-official).
  canonical: WebSearch result this turn — "The claude-plugins-official
  repository has 30.4k stars" — ships a `frontend-design` skill,
  authored by Anthropic staff, that Claude auto-invokes for frontend
  work and that names accessibility as one of its built-in
  technical-requirement constraints.
- A narrow single-purpose interaction-craft plugin
  (darasoba/design-engineer-plugin) was found. canonical: WebFetch
  result on that repo this turn — "The plugin currently has 1 star and
  1 watcher on GitHub, indicating early-stage adoption" — noted as a
  weak-adoption candidate, not promoted to a proposal entry, per the
  requirement that adoption evidence be multi-source or otherwise
  substantiated.

## Performance axes (dimensions the field competes on)

canonical: WebFetch results, storybook.js.org/docs/ai and
wilwaldon/Claude-Code-Frontend-Design-Toolkit pages (see Sources)

1. Live component-source-of-truth access (storybookjs/mcp reads actual
   stories/docs from a running dev server before generating new UI) vs.
   static style-guidance-only skills (frontend-design and the
   toolkit's curated skills operate on written principles, not a live
   component registry).
2. Breadth of a single curated bundle (the toolkit composes a
   foundational aesthetic-direction skill + token/theming layer +
   accessibility-tree testing layer as one pipeline: "Baseline UI →
   Accessibility → Motion/Performance") vs. one narrowly-scoped
   first-party skill (frontend-design covers aesthetic direction and
   framework/performance/accessibility constraints, not testing or
   live component lookup).
3. canonical: storybook.js.org/docs/ai/mcp/overview and
   wilwaldon/Claude-Code-Frontend-Design-Toolkit pages (see Sources) —
   evidence format: storybookjs/mcp returns manifest-shaped tool
   results an agent can act on directly (build instructions, existing
   component docs); the toolkit's Playwright-MCP layer returns
   accessibility-tree snapshots (2-5KB) instead of full screenshots,
   optimized for agent context budgets rather than human review.

## Adopt / skip

- Adopt as a pattern: storybookjs/mcp's "look up the existing component
  library before generating a new one" workflow — this sharpens this
  role's existing component-reuse guidance (from the prior,
  domain-tool-sourced Storybook entry) into a concrete tool-shaped
  check: query the live source of truth for an existing story/doc
  before specifying a new component from scratch.
- Adopt as a pattern: the toolkit's explicit token-space judgment
  (OKLCH wide-gamut color space plus a single derived-hue variable
  driving a full palette) as an upgrade to this role's existing
  token-default rule — a concrete color-space recommendation, not just
  "define tokens."
- Adopt as a pattern: frontend-design's placement of accessibility
  alongside framework and performance. canonical: WebSearch result on
  anthropics/claude-plugins-official's frontend-design skill this
  turn — "The skill includes constraints for technical requirements
  including framework, performance, and accessibility" — a
  first-party precedent for treating accessibility as a co-equal
  constraint.
- Skip: promoting darasoba/design-engineer-plugin to a proposal entry
  — 1 star is not adoption evidence by this scout's bar (see Skip
  record above); its interaction-state/motion judgment is
  directionally similar to content already covered by the existing
  rulebook and not worth the single-source risk.
- Skip: storybookjs/mcp's live dev-server/MCP execution mechanism
  itself — this role specs components and tokens, it does not run a
  live dev server; the judgment (check the source of truth first) is
  adopted, not the tool's execution layer, per the scout-directive's
  "never clone the exemplar" rule.

## Gap line

canonical: docs/issue-1199/proposals/2026-08-13-ux-engineering-tool-landscape.md
and docs/issue-1199/reports/ux-engineering.md (this repo, read this
turn) — the prior round surveyed Tokens Studio, Stark, Radix UI,
Storybook, Optimal Workshop: general domain UX-engineering practitioner
tools, none of them a Claude Code plugin or skill (folded in natively,
with no per-tool attribution, per that proposal's own account). The
2026-08-14 amendment states a fold-in whose surveyed sources are
domain tools alone does not satisfy the acceptance check. This round's
gap is narrower and additive: none of the prior rules name a
live-component-lookup-before-authoring check or a concrete color-space
default, which is exactly what storybookjs/mcp and the toolkit's
token layer independently converge on.

## Sources

- https://github.com/storybookjs/mcp
- https://storybook.js.org/docs/ai/mcp/overview
- https://www.claudepluginhub.com/plugins/storybookjs-storybook-packages-claude-plugin
- https://github.com/wilwaldon/Claude-Code-Frontend-Design-Toolkit
- https://github.com/anthropics/claude-plugins-official
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/frontend-design
- https://github.com/darasoba/design-engineer-plugin

## kind / loop_state

kind: report
loop_state: phase-1-scouted
