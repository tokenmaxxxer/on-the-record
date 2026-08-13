# technical-writing — tool-landscape scout brief (issue #1199, phase 1)

Subject: issue-1199. Mode: parallel WebSearch fan-out (one round) + one
deepening WebFetch round on the operator-named exemplar, within the
5-stage / 3min scout budget.
canonical: this session's tool transcript this turn — one message with
four parallel WebSearch calls, followed by one message with a single
WebFetch call.

## Sweep angles run

1. Operator-named exemplar: `cathrynlavery/diagram-design`
2. Prose/style linting category: Vale
3. Docs-site generation category: Docusaurus vs MkDocs Material
4. Diagram-as-code category: Mermaid

## Category must-bes and exemplars

**Diagramming (editorial vs as-code split — this is the field's real
performance axis, not a single winner):**
- `cathrynlavery/diagram-design` — author reports 550+ stars, and the
  repo is independently tracked as GitHub-trending by trendshift.io.
  Positions itself explicitly AGAINST Mermaid: "No shadows, no
  Mermaid-slop." Ships 27 diagram types plus 3 primitives, all
  self-contained HTML+SVG, no build step. Design moves: (a) hard
  visual-discipline constraints — one accent color, 1-2 focal elements
  per diagram, coordinates snapped to a 4px grid, 3 fixed typefaces —
  that exist specifically to suppress "AI-generated" visual noise; (b)
  import/redraw from Mermaid/draw.io sources into its own constrained
  vocabulary, i.e. it treats diagram GENERATION and diagram STYLE as
  separable steps.
- Mermaid (`mermaid-js/mermaid`) — GitHub repo and npm package page
  report large-scale adoption (weekly npm downloads in the millions,
  GitHub stars in the tens of thousands as of the June 2026 snapshot
  those pages showed). Design move: diagrams as versionable plain text
  embedded in markdown, optimized for "cheap to keep current," not
  visual polish — the opposite tradeoff from diagram-design.
- Gap line: this role's rulebook currently has no rule on when a
  diagram belongs in a doc at all, nor on visual-noise discipline —
  both categories' must-be (diagrams must stay cheap to update OR
  visually disciplined, practitioners pick one deliberately) is
  entirely missing from playbook/*.md today.

**Prose/style linting:**
- Vale (`vale-cli/vale`, formerly errata-ai/vale) — used in production
  by AWS, NVIDIA, Microsoft, GitLab, Red Hat per vale.sh and
  engineering.contentsquare.com's writeup; an actively maintained
  multi-contributor project per those same pages. Design move: style
  guides compiled into machine-checkable YAML rules (existence/
  substitution/readability checks) run in CI like a code linter — the
  "docs as code" pattern applied to prose review specifically, not
  just to storage format.
- Gap line: playbook/style-guide-compliance.md already encodes Google
  Developer Documentation Style Guide judgment calls (per issue
  #1174's evidence trail) but has no rule on making compliance
  CI-checkable — Vale's must-be (style rules should be executable, not
  just advisory) is the missing piece.

**Docs-site generation:**
- Docusaurus and Material for MkDocs both report large GitHub star
  counts and name-brand adopters per stackshare.io/docsio.co
  comparison pages (Docusaurus: React Native, Redux Toolkit, Supabase,
  Prettier; MkDocs: 90,000+ dependent GitHub projects per those pages).
  Material for MkDocs entered maintenance mode in November 2025 per
  the same sources, with Zensical named as its successor. Design move
  (shared across both): Diátaxis-compatible information architecture
  is a first-class navigation primitive (sidebar categories map to
  tutorial/how-to/reference/explanation), not an afterthought bolted
  onto a generic site.
- Gap line: playbook/doc-type-selection.md already picks one Diátaxis
  quadrant per deliverable (per the role directive); the tool
  landscape's must-be here is confirmatory, not a gap — both
  Docusaurus and MkDocs Material structurally assume the same
  quadrant discipline this role already enforces. No new rule needed
  from this category; it validates an existing one.

## Adopt / skip

- Adopt: diagram-design's visual-noise-discipline constraints (accent-
  color cap, focal-element cap, grid-snap) as a checklist item when a
  deliverable includes a diagram — upgrades doc-type-selection.md /
  minimalism-scoping.md's diagram judgment.
- Adopt: Vale's "compile the style guide into an executable check"
  move as a rule in style-guide-compliance.md — upgrades the accuracy/
  compliance judgment from advisory prose to a checkable artifact
  reference.
- Adopt: the diagram-cost tradeoff (editorial-polish-diagram vs
  cheap-to-update-diagram-as-code) as an explicit decision rule —
  currently entirely absent, upgrades doc-type-selection.md.
- Skip: cloning diagram-design's exact type catalog or Vale's exact
  rule syntax into the rulebook — the bar is the design MOVE
  (discipline constraints, executable checks), not the tool's own
  surface, per scout-directive's "never clone the exemplar" rule.

Sources:
- https://github.com/cathrynlavery/diagram-design
- https://x.com/cathrynlavery/status/2045869046222958872
- https://trendshift.io/repositories/26141
- https://github.com/mermaid-js/mermaid
- https://www.npmjs.com/package/mermaid
- https://vale.sh/
- https://vale.sh/docs
- https://github.com/vale-cli/vale
- https://engineering.contentsquare.com/2023/using-vale-to-help-engineers-become-better-writers/
- https://stackshare.io/stackups/docusaurus-vs-mkdocs
- https://blog.damavis.com/en/mkdocs-vs-docusaurus-for-technical-documentation/
