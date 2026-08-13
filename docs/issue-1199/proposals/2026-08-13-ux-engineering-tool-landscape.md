---
status: proposed
files:
  - docs/issue-1199/reports/ux-engineering.md
---

# issue-1199 (ux-engineering): tool-landscape fold-in

kind: proposal
subject: issue-1199

## Request

Issue #1199 (northpole req#1) asks every role to survey the tools its
domain's practitioners actually use, distill each tool's design move
with adoption evidence, and fold that judgment natively into the
rulebook. Two binding amendments: (a) apply-not-reference — the same
delivery must edit the named upgrade target files, not only point at
them; (b) native application — absorbed rules read as this role's own
judgment, no tool/repo names or `source: <url>` framing inside the
public rulebook; the survey/adoption-evidence trail stays only in this
on-the-record record. This proposal covers the ux-engineering unit.

## Survey summary

canonical: docs/issue-1199/reports/ux-engineering/survey.md
`tokenmaxxxer/ux-engineering-rulebook` carries five `playbook/*.md`
decision-axis files (color-visibility, surface-contrast,
control-selection, layout-grouping, navigation-depth), each sourced
from research-article judgment only — none reflects practitioner
tooling. That is the gap this fold-in targets.

## Scout summary

canonical: docs/issue-1199/reports/ux-engineering/scout-brief.md
Four parallel WebSearch angles (design tokens, accessibility/contrast
tooling, component-library tooling, IA/navigation tooling), one sweep
stage, saturation at judge point 1. Findings: design-token
single-source-of-truth layering (Tokens Studio/Style Dictionary,
cited 84%-adoption figure); rendered-context contrast checking
(Stark/axe-core); contract-matched primitive selection (Radix UI
Primitives, underlying shadcn/ui's cited 75k+-star adoption);
isolated-state proof before assembly (Storybook-class tooling);
directness-scored navigation depth (Optimal Workshop's Treejack/
OptimalSort).

## Adopted norms

One new native rule appended to each of the five existing axis files
(no new sixth file — a standalone tool-landscape file is ruled out by
the native-application amendment), matching each file's existing rule
shape (numbered rule + rationale + counter-example), phrased with no
tool/repo attribution:

1. `playbook/color-visibility.md` — a color value is only safe to
   reuse once it resolves through one source-of-truth layer read by
   both the design surface and the shipped code; flag any color
   decision that hard-codes a value bypassing that layer.
2. `playbook/surface-contrast.md` — check contrast against the
   element's actual rendered layer (real background, current
   interaction state, real font-weight), not an isolated foreground/
   background swatch pair.
3. `playbook/control-selection.md` — for an interactive pattern with
   an established role-and-keyboard-interaction contract (dialog,
   combobox, accordion, tabs), pick the control matching that
   contract over one that only looks similar.
4. `playbook/layout-grouping.md` — prove a grouped layout's states
   (empty, loading, error, populated) correct in isolation before
   assembling the group into a full screen.
5. `playbook/navigation-depth.md` — judge navigation depth by a
   measured directness score (task completion without backtracking),
   not a subjective "feels too deep" read.

## Rationale

- Apply-not-reference (issue amendment, 2026-08-13): all five named
  upgrade targets are edited in the same phase-2 delivery, not merely
  referenced by a catalog section.
- Native application, no attribution (issue amendment, 2026-08-13): no
  rule text names a tool or carries a `source:` URL; each rule is
  phrased as this role's own design judgment, evidenced in the Scout
  summary above.
- Bounded fold-in (issue requirement 3): five one-rule additions, not
  a tool catalog — each traces to one scout-brief finding and one
  named upgrade target (issue requirement 4).
- Adoption evidence routed through the scout's WebSearch trail (issue
  requirement 1), not pretrained-recall.

## Plugin reflection plan

1. Clone `tokenmaxxxer/ux-engineering-rulebook`, branch
   `issue-1199/tool-landscape`, add the five rules above (one per
   file) to the existing `playbook/*.md` files.
2. No README change needed — the fold-in extends existing files, adds
   no new file to list.
3. Open a PR against `tokenmaxxxer/ux-engineering-rulebook`; land the
   PR URL and diff summary in
   `docs/issue-1199/reports/ux-engineering.md` (this repo's phase-2
   record, gated behind the `APPROVE issue-1199/ux-engineering`
   comment per contract v3 s19).
4. Check off the ux-engineering row in issue #1199's 43-item tracker
   once the rulebook PR is opened.

## Constraints

- No sixth `playbook/tool-landscape.md` file — ruled out by the
  native-application amendment (technical-writing's own such file was
  retrofit-removed for the same reason).
- No tool catalog for any role other than ux-engineering — each
  role's fan-out unit is separate per issue requirement 6.
- No shape-check gate work (`gates/playbook_depth_gate.py`) — that is
  the issue's step-1 infra unit, not a per-role fan-out unit.
- No touching the 43-item tracker for any row but ux-engineering's
  own.
- Awaiting a PR review Approve (two-account mode) or an issue-level
  `APPROVE issue-1199/ux-engineering` comment (single-account mode)
  from a `docs/specs/approvers.md` account before phase 2 begins, per
  contract v3 s19.

Sources:
- https://tokens.studio/
- https://styledictionary.com/info/tokens/
- https://www.uiguides.com/tools/stark-review
- https://access-proof.com/blog/what-is-axe-core-evidence-based-audits
- https://thefrontkit.com/blogs/shadcn-ui-accessibility-audit-2026
- https://github.com/radix-ui/primitives
- https://www.optimalworkshop.com/product/tree-testing
- https://www.nngroup.com/articles/card-sorting-tree-testing-differences/
- https://informationarchitectureauthority.com/information-architecture-tools
