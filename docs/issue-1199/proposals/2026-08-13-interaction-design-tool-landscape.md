---
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-13-interaction-design-tool-landscape.md
---

# issue-1199 (interaction-design): tool-landscape fold-in

kind: proposal
subject: issue-1199

Proposal: docs/issue-1199/proposals/2026-08-13-interaction-design-tool-landscape.md

## Problem / goal framing

Issue #1199 (northpole req#1/req#5) requires each role to survey the
tool ecosystem practitioners in its domain actually use, extract the
design moves those tools embody, and fold them into the rulebook as
this role's own native judgment (no per-tool attribution in the public
rulebook — provenance stays only in this on-the-record trail, per the
2026-08-13 native-application amendment). This role's write surface,
per `docs/issue-1199/reports/interaction-design/current-state-survey.md`,
has one playbook file covering forms/layout/navigation/contrast but no
rules on prototyping-fidelity staging, usability-test-plan sizing,
token-reference scoping, or manual-vs-automated accessibility coverage
— the four gaps this proposal closes.

## Comparison set / exemplars

Four category-leading tools surveyed with adoption evidence
(`docs/issue-1199/reports/interaction-design/scout-brief.md`): Figma
(prototyping/handoff, ~41% market share / 13M MAU), Maze and
UserTesting (usability-testing platforms, opposite ends of the self-
serve/enterprise-panel spectrum), Tokens Studio for Figma (dominant
design-token plugin), and axe-core (category-leading automated
accessibility engine, ~57% WCAG-issue detection ceiling stated by its
own maintainers).

## Methodology cited

This role's existing governing methodology — Nielsen's ten usability
heuristics and WCAG 2.1 AA — is not replaced. The four new rules extend
that same methodology into gaps it does not currently cover (fidelity
staging, test sizing, token scoping, manual-check coverage), rather
than introducing a competing framework.

## What will be delivered

Four native rule additions to `interaction-design/playbook/`, applied
directly into the named target locations (per the apply-not-reference
amendment), each phrased as this role's own judgment with no tool-repo
name or `source:` framing in the rulebook body:

1. **Fidelity-scope rule** — when staging a lo-fi wireframe before a
   hi-fi one, the lo-fi pass may omit color/type/imagery but must still
   resolve every navigation path and state; the hi-fi pass is where
   token-referenced values and pixel-accurate spacing enter. Upgrades:
   the `id-wireframe-staging` plugin's bare lo-fi-before-hi-fi ordering
   check, by giving it content criteria instead of ordering alone —
   applied into the wireframe-staging guidance file/section that plugin
   reads.
2. **Test-plan sizing rule** — a usability-test plan names not only a
   task scenario but a participant count/recruitment criterion sized to
   its moderated-vs-unmoderated choice (unmoderated: wider, cheaper
   recruitment; moderated: smaller, criteria-matched panel). Upgrades:
   the `id-usability-test-plan` plugin's presence-only check, by adding
   a sizing judgment — applied into the usability-test-plan guidance
   file/section that plugin reads.
3. **Semantic-token-reference-by-default rule** — every spec element
   carrying a value names a semantic token, never a raw value, even
   before a design-system document exists; when no token document
   exists yet (per the current-state survey's missing-design-system
   finding), the spec instead names the semantic role it expects a
   future token to fill, flagged as provisional. Upgrades: playbook
   file 01's contrast rules (R5/R6), which already reference numeric
   floors but not token scoping — extended with a token-reference
   clause in the same file.
4. **Manual-accessibility-coverage rule** — an accessibility-floor
   section names, alongside automated-checkable items (contrast,
   alt-text presence), which categories automated tooling cannot verify
   (keyboard-only task completion, screen-reader label sense, focus
   order) as separately, explicitly checked — never satisfied by
   automated coverage alone. Upgrades: the `id-accessibility-floor`
   plugin's WCAG-AA-named-but-uncategorized check, by adding the
   manual/automated split — applied into the accessibility-floor
   guidance file/section that plugin reads.

Delivery target: `tokenmaxxxer/interaction-design-rulebook`, branch
`issue-1199/tool-landscape`, editing `interaction-design/playbook/
01-form-control-and-layout.md` (rule 3) and the plugin-referenced
guidance content backing `id-wireframe-staging`, `id-usability-test-
plan`, and `id-accessibility-floor` (rules 1, 2, 4) — the exact files
those three plugins' directive.sh/README point at, confirmed at
phase-2 build time.

## Adopt / skip rationale

Adopt: the four judgments above, because each closes a gap the current-
state survey already named as missing and each traces to one scout-
brief finding (issue requirement 4's per-tool traceability bar).
Skip: cloning any surveyed tool's actual UI, file format, or rule-
engine internals (Figma's component mechanics, Tokens Studio's JSON
sync schema, axe-core's rule-engine implementation) — this role specs
screens/flows and never operates design tooling; the surveyed
judgment is adopted, not the tool's surface, per the scout-directive's
"never clone the exemplar" rule and the native-application amendment's
ban on tool-catalog framing in rulebook content.

## How it will be judged

Judged done when: (a) all four rules land as edits to the named target
files in `tokenmaxxxer/interaction-design-rulebook` in the same
delivery (apply-not-reference amendment), with no tool-repo name or
`source:` link in the rulebook body (native-application amendment); (b)
this repo's phase-2 record (`docs/issue-1199/reports/interaction-
design.md`) documents the rulebook PR/branch and cites the scout-brief
evidence trail for each rule, without duplicating tool names/URLs into
the rulebook; (c) the interaction-design row in issue #1199's 43-item
tracker is checked.

## Plan for phase 2

1. On `tokenmaxxxer/interaction-design-rulebook`, branch
   `issue-1199/tool-landscape`: add rule 3 to
   `interaction-design/playbook/01-form-control-and-layout.md`, and
   locate + edit the guidance content the `id-wireframe-staging`,
   `id-usability-test-plan`, and `id-accessibility-floor` plugins each
   reference, applying rules 1, 2, 4 natively.
2. Open a PR against `tokenmaxxxer/interaction-design-rulebook` (or, if
   the cross-repo PR-create guard blocks it as it did for the
   technical-writing unit, push the branch and log a filed deviation
   for external relay to open the PR).
3. Write this repo's phase-2 record `docs/issue-1199/reports/
   interaction-design.md` documenting the branch/PR and the evidence
   trail.
4. Check off the interaction-design row in issue #1199's 43-item
   tracker.

## Out of scope

- Tool-landscape fold-ins for any other role — each fan-out unit is
  separate per issue requirement 6.
- Building or modifying the shape-check gate
  (`gates/playbook_depth_gate.py`) — issue's step-1 infra unit.
- Creating `docs/specs/design-system.md` for the rulebook repo — named
  as a gap in the current-state survey, but establishing a full token
  document is a separate, larger proposal than this bounded fold-in.
- Touching any tracker row but interaction-design's own.

## Approval

Awaiting a PR review Approve (two-account mode) or an issue-level
`APPROVE issue-1199/interaction-design` comment (single-account mode)
from a `docs/specs/approvers.md` account before phase 2 (the rulebook
edits and this repo's phase-2 record) begins, per contract v3 s19. No
such approval exists on issue #1199 as of this session
(canonical: gh issue view 1199 --comments, this turn's tool transcript
— only `APPROVE issue-1199/implementation`, `APPROVE issue-1199/
technical-writing`, and `APPROVE issue-1199/brand-design` are present).
This session accordingly stops after phase 1.
