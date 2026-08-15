---
subject: issue-1199
role: ux-engineering
loop_state: scope-proposed
status: proposed
files:
  - <ux-engineering-rulebook repo, playbook/*.md file(s) touched by the 2026-08-13 fold-in, confirmed at phase-2 build time>
  - docs/issue-1199/reports/ux-engineering.md
---

# Proposal: fold Claude Code plugin/skill landscape into ux-engineering rulebook (issue-1199, 2026-08-14 amendment rework)

kind: proposal
subject: issue-1199

## Request

The 2026-08-14 amendment to issue-1199 supersedes the prior survey
target: the required survey basis is now the Claude Code plugin/skill
ecosystem (marketplace/community plugins relevant to ux-engineering),
not general ux-engineering-domain practitioner tools. This proposal
requests an additive, three-entry tool-learnings block folded into the
ux-engineering-rulebook's existing `playbook/*.md` files, on top of
(not replacing) the five domain-tool entries the 2026-08-13 fold-in
already landed.

## Survey summary

canonical: docs/issue-1199/reports/ux-engineering.md and
docs/issue-1199/proposals/2026-08-13-ux-engineering-tool-landscape.md
(this repo, read this turn) — the landed 2026-08-13 fold-in surveyed
Tokens Studio, Stark, Radix UI, Storybook, and Optimal Workshop into
`tokenmaxxxer/ux-engineering-rulebook`: general design-tooling and
research-tooling platforms, none of them a Claude Code plugin or
skill, folded in natively with no per-tool attribution surfaced in the
public rulebook text. The 2026-08-14 amendment states explicitly that
a fold-in whose surveyed sources are domain tools alone does not
satisfy the amended acceptance check, so the ux-engineering tracker
line needs this additive rework before it can count toward the
issue-level 43/43.

## Scout summary

canonical: `docs/issue-1199/reports/ux-engineering/scout-brief-plugins.md`
(this repo, written this turn) — full scouting record, adoption
evidence, and source list. Three Claude Code plugins/skills surveyed
with adoption evidence:

1. **storybookjs/mcp** (`@storybook/claude-code-plugin`, official,
   Storybook-org-published) — manages the component-library workflow
   (init, story writing/review, live dev-server preview, version
   upgrades) from inside a Claude Code session, backed by an MCP
   server that lets Claude query existing stories/docs/build
   instructions before generating new UI.
2. **wilwaldon/Claude-Code-Frontend-Design-Toolkit** (636 GitHub
   stars, 79 forks per the scout brief's WebFetch) — a curated
   collection layering design-token (OKLCH color space, single
   derived-hue variable), theming, and accessibility-tree-based
   Playwright-MCP testing tools on top of Anthropic's own first-party
   `frontend-design` skill.
3. **anthropics/claude-plugins-official — `frontend-design` skill**
   (repository: 30.4k GitHub stars per the scout brief's WebSearch;
   Anthropic first-party, auto-invoked by Claude for frontend work) —
   names accessibility as one of its built-in technical-requirement
   constraints alongside framework and performance.

A fourth candidate, darasoba/design-engineer-plugin, was scouted but
not carried forward: the scout brief's Skip record cites 1 GitHub star
at time of scouting, below the adoption-evidence bar the two sibling
reworks (devrel, interaction-design) applied to their own entries.

## Adopted norms

Three native rule upgrades, applied directly into the
ux-engineering-rulebook's existing `playbook/*.md` target files,
phrased as this role's own judgment with no tool-repo name or
`source:` framing in the rulebook body:

1. **Live-source-of-truth-before-authoring rule** — before specifying
   a new component, the spec states whether an existing component/
   story already covers the need, checked against the live component
   library rather than assumed from memory. Upgrades: the existing
   component-reuse guidance folded in from the prior Storybook entry,
   from a general "prefer existing components" statement into a
   concrete check-the-source-first clause.
2. **Token color-space default rule** — the token-default guidance
   names OKLCH (or an equivalent wide-gamut, perceptually-uniform
   space) as the default token color space, with a single
   derived-hue variable as the preferred mechanism for deriving a full
   palette. Upgrades: the existing token-default rule folded in from
   the prior Tokens Studio entry, replacing a bare "define tokens"
   instruction with a concrete color-space recommendation.
3. **Accessibility-as-co-equal-constraint rule** — accessibility is
   listed alongside framework and performance as a named technical
   constraint at spec time, not deferred to a separate later pass.
   Upgrades: the existing accessibility-parity rule folded in from the
   prior Stark entry, with a first-party-confirmed placement.

## Rationale

Adopt: the three judgments above, because each closes a gap the scout
brief's gap line names (no existing rule names a live-component-
lookup-before-authoring check or a concrete token color-space default)
and each traces to one scout-brief finding (issue requirement 4's
per-tool traceability bar). None of the prior five landed rules are
retracted — the amendment adds a survey-target correction, it does not
instruct deleting prior work, and domain tools remain valid secondary
context per requirement 1's own wording.

Skip: adopting storybookjs/mcp's live dev-server/MCP execution
mechanism, the toolkit's Playwright-MCP accessibility-testing layer as
a run mechanism, or darasoba/design-engineer-plugin's motion/
interaction-state catalog wholesale — this role specs components and
tokens and never runs a live dev server or writes test automation; the
judgment is adopted, not the tool's execution surface, per the
scout-directive's "never clone the exemplar" rule.

A new standalone file for the plugin-sourced entries was considered
and rejected, for the same reason the 2026-08-13 proposal's own
alternatives section gave: the existing `playbook/*.md` files are
where an author already reads guidance.

## Plugin reflection plan

1. On `tokenmaxxxer/ux-engineering-rulebook`, branch
   `issue-1199/plugin-tool-landscape`: locate and edit the
   `playbook/*.md` sections backing component-reuse, token-default,
   and accessibility-parity guidance, applying the three rules
   natively, placed after the existing 2026-08-13 tool-learnings
   section (kept, not removed).
2. Open a PR against `tokenmaxxxer/ux-engineering-rulebook` (or, if the
   cross-repo PR-create guard blocks it, push the branch and log a
   filed deviation for external relay, matching the prior round's
   observed pattern).
3. Update this repo's phase-2 record
   `docs/issue-1199/reports/ux-engineering.md` documenting the
   branch/PR and the evidence trail, and set `loop_state: landed` once
   the edit is pushed. This record update is phase-2 output and is not
   performed by this proposal.

## Constraints

- Tool-landscape rework for any other role is out of scope — each
  fan-out unit is separate per issue requirement 6.
- Re-opening or re-landing the five already-landed 2026-08-13 rules
  (component-reuse, token-default, accessibility-parity, and the other
  two folded-in rules) is out of scope — this rework is additive to
  them, not a replacement.
- Building or modifying any shape-check gate infrastructure is out of
  scope — issue's step-1 infra unit.
- Adopting storybookjs/mcp's live execution mechanism, the toolkit's
  Playwright-MCP testing layer, or darasoba/design-engineer-plugin's
  catalog beyond the three named judgments is out of scope.
- Phase 2 (the rulebook edits and this repo's phase-2 record update)
  does not begin until a PR review Approve (two-account mode) or an
  issue-level `APPROVE issue-1199/ux-engineering` comment
  (single-account mode) from a `docs/specs/approvers.md` account is
  posted after this proposal exists, per contract v3 s19. Any prior
  `APPROVE issue-1199/ux-engineering` comment predates the 2026-08-14
  amendment and this proposal, and does not authorize this rework's
  phase-2 work. This session accordingly stops after phase 1.
