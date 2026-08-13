kind: report
subject: issue-1199
doc-type: reference

# ux-engineering — scout brief (phase-1, issue #1199)

Mode: parallel WebSearch fan-out, 4 angles in one turn (design tokens;
accessibility/contrast tooling; component-library/design-system
tooling; information-architecture/navigation tooling). 1 sweep stage,
saturation reached after judge point 1 — each angle returned a clear
adoption-evidenced leader mapping to a distinct gap axis, no conflicts
to reconcile, so no deepening round was needed.

canonical: WebSearch results, this turn's tool transcript (four
queries: design-tokens tooling, accessibility/contrast tooling,
component-library tooling, IA/navigation tooling)

## Category must-bes and adopted design moves

1. **Design tokens (Tokens Studio / Style Dictionary)** — adoption per
   the WebSearch results above: an industry report figure cited in the
   results states 84% of teams report using design tokens in some
   form; Tokens Studio's own listing describes integrating Figma/
   Penpot/GitHub via Style Dictionary's build pipeline. Design move: a
   token is only trustworthy when it has exactly one source-of-truth
   layer that both design and code read from — multi-layer token
   graphs (primitive → semantic → component) prevent drift between
   what a designer picks and what ships. Upgrades:
   `playbook/color-visibility.md`.

2. **Accessibility/contrast tooling (Stark, axe-core)** — adoption per
   the WebSearch results above: axe-core is described in the results
   as the tooling most other accessibility checkers build on, cited
   alongside Lighthouse and Microsoft Accessibility Insights as tools
   in the same lineage; Stark is listed as a paid ($99/yr) Figma/
   Sketch plugin with a free contrast-checker tier. Design move:
   contrast must be validated against the actual rendered element (its
   real background layer, state, and font-weight) rather than an
   isolated foreground/background swatch pair — swatch-only checks
   miss overlays, translucency, and hover/focus state shifts. Upgrades:
   `playbook/surface-contrast.md`.

3. **Accessible component primitives (Radix UI Primitives)** —
   adoption per the WebSearch results above: the results describe
   Radix Primitives as maintained by WorkOS and forming the
   accessibility layer underneath shadcn/ui (cited at 75k+ GitHub
   stars by early 2026) and other component libraries; a cited 2026
   shadcn/ui accessibility audit rates the underlying Radix primitives
   as excellent. Design move: each interactive pattern (dialog,
   combobox, accordion, tabs) has one canonical ARIA role + keyboard-
   interaction contract; picking the primitive by matching the pattern
   to that contract — not by visual resemblance — is what keeps a
   control's behavior accessible by default. Upgrades:
   `playbook/control-selection.md`.

4. **Component isolation / documentation tooling (Storybook-class)** —
   adoption per the WebSearch results above: cited as the standard
   pairing for Radix-based design systems in multiple 2026 sources,
   used to develop and verify components outside the full application.
   Design move: a grouped layout's states (empty, loading, error,
   populated) should be proven correct in isolation before the group
   is assembled into a full screen — catching a state-interaction
   defect at the isolated-group level is cheaper than catching it
   after assembly. Upgrades: `playbook/layout-grouping.md`.

5. **Tree-testing tooling (Optimal Workshop's Treejack/OptimalSort)** —
   adoption per the WebSearch results above: cited by the
   Information Architecture Authority's tool listing and the NN/g
   card-sorting-vs-tree-testing article as among the most widely
   adopted purpose-built IA platforms. Design move: a navigation
   structure's depth should be judged by a directness score
   (task-completion without backtracking) measured against a plain-text
   hierarchy, not by a subjective "feels too deep" read — depth is only
   a problem when it measurably costs users direct paths. Upgrades:
   `playbook/navigation-depth.md`.

## Segment fit

All five surveyed categories are the tooling UX engineers and
front-end/design-system practitioners actually run day to day (token
pipelines, contrast/accessibility checkers, primitive component
libraries, isolated-component dev environments, IA validation
platforms) — matched to this role's own five decision axes, not a
generic design-tool sweep.

## Gap line

The rulebook's five axis files already cover *what to choose*
(control type, layout grouping, contrast, color, nav depth) from
research-article judgment; none yet encode the *verification
discipline* these tools apply — single-source token layering,
rendered-context contrast checks, contract-matched primitive
selection, isolated-state proof before assembly, and directness-scored
depth. That verification-discipline layer is what this fold-in adds.

## Sources

- https://tokens.studio/
- https://styledictionary.com/info/tokens/
- https://www.digitalapplied.com/blog/design-systems-2026-scale-ui-without-chaos-methodology
- https://www.uiguides.com/tools/stark-review
- https://access-proof.com/blog/what-is-axe-core-evidence-based-audits
- https://thefrontkit.com/blogs/shadcn-ui-accessibility-audit-2026
- https://github.com/radix-ui/primitives
- https://blog.logrocket.com/building-design-system-radix/
- https://www.builder.io/blog/react-component-libraries-2026
- https://www.optimalworkshop.com/product/tree-testing
- https://www.nngroup.com/articles/card-sorting-tree-testing-differences/
- https://informationarchitectureauthority.com/information-architecture-tools

## kind / loop_state

kind: report
loop_state: phase-1-scouted
