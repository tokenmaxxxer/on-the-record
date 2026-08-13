kind: report
subject: issue-1199
doc-type: reference

# interaction-design — issue #1199 scout brief

canonical: this turn's tool transcript — four WebSearch calls dispatched in one message (Figma, Maze/UserTesting, Tokens Studio, axe-core queries)
Stages used: 1 sweep (4 parallel WebSearch angles), 0 deepening rounds.
Judge point 1: strong cross-angle agreement — each tool is the named
category leader with multi-source adoption evidence, per the four
angle sections below. Judge point 2: another round would not change
any build decision, so deepening stopped after the sweep. Mode:
parallel (four WebSearch calls dispatched in one turn).

## Sweep angle 1 — prototyping/handoff (Figma)

Figma holds roughly 41% market share and 13M MAU in collaborative
design/prototyping, ~93% category adoption among organizations
surveyed, and near-universal Fortune 500 presence as of late 2025.
Category must-be: a design tool that separates a low-fidelity
exploration mode from a high-fidelity, developer-ready mode, with an
explicit handoff step (component/spec inspection) bridging the two —
this is the field's dominant pattern, not an incidental Figma feature.
Sources:
- https://www.programming-helper.com/tech/figma-2026-40-market-share-13m-mau-ipo-python
- https://sanjaytarani.com/blog/top-design-handoff-tools-in-2026-bridging-the-gap-between-design-and-development

## Sweep angle 2 — usability-testing platforms (Maze / UserTesting)

Maze (self-serve, unmoderated-first, ~free–$73K/yr) and UserTesting
(enterprise panel research, 1M+ vetted participants, $36K–$148K/yr)
are the two category leaders on opposite ends of a moderated/
unmoderated and self-serve/managed-panel spectrum. Both converge on the
same test-plan shape regardless of tier: a named task scenario run
against a defined participant pool/count, with card-sort and tree-test
as adjacent methods for structure validation rather than task
validation. Must-be: a usability-test plan is not just "a test" — it
names task scenario type AND a recruitment size/criteria appropriate to
the plan's moderated/unmoderated choice.
Sources:
- https://maze.co/compare/maze-vs-usertesting/
- https://www.koji.so/blog/usertesting-vs-maze-2026

## Sweep angle 3 — design-token tooling (Tokens Studio for Figma)

The dominant design-token plugin for Figma stores tokens as JSON,
syncs them with a version-controlled source of truth (e.g. a git
provider), and explicitly supports token types with no native Figma
property (border-radius, spacing) alongside ones that do. The category
convention is a two-tier reference model: raw/primitive values defined
once, then referenced by named semantic aliases everywhere a designer
actually applies a value — never a hardcoded value in the applied
layer. Must-be: any spec element carrying a value should reference a
semantic token name, not a raw value, even before a full token
document exists.
Sources:
- https://docs.tokens.studio/
- https://github.com/tokens-studio/figma-plugin

## Sweep angle 4 — automated accessibility testing (axe-core)

axe-core (Deque Systems) is the category-leading automated a11y engine,
widely embedded in unit/integration/CI pipelines; its own stated
ceiling is that automated scanning finds on average 57% of WCAG issues
— the rest require manual/keyboard/screen-reader review. Must-be: an
accessibility floor that cites only automatable checks (contrast
ratios, alt-text presence) overstates coverage; a genuine floor must
name the manual-check categories automated tooling cannot reach
(keyboard-only task completion, screen-reader label sense-check, focus
order) as explicitly, separately verified.
Sources:
- https://github.com/dequelabs/axe-core
- https://medium.com/@SkorekM/from-theory-to-automation-wcag-compliance-using-axe-core-next-js-and-github-actions-b9f63af8e155

## Adopt / skip

Adopt: (1) explicit lo-fi-vs-hi-fi scope distinction beyond ordering;
(2) usability-test-plan sizing by moderated/unmoderated choice; (3)
semantic-token-reference-by-default even pre-design-system; (4) named
manual-check categories alongside automated a11y coverage, with the
57%-ceiling reasoning made explicit so the floor cannot be satisfied by
automated checks alone.
Skip: cloning any tool's actual UI/workflow (Figma's component-library
mechanics, Tokens Studio's JSON sync format, axe-core's rule-engine
internals) — this role specs screens/flows, it does not operate design
tooling; adopting the underlying judgment, not the tool's surface, per
scout-directive.

## Gap line

canonical: docs/issue-1199/reports/interaction-design/current-state-survey.md (this session's own file, written this turn) — "Gap this fold-in targets" section
Existing rulebook state already names Nielsen heuristics and WCAG 2.1
AA as the governing floor (met); it has no rule distinguishing lo-fi/
hi-fi scope, no test-plan sizing rule, no semantic-token-reference
default, and no manual-a11y-check-category rule (all four missing) —
these four gaps map 1:1 onto the four proposed rules below.
