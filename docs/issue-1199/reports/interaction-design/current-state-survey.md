kind: report
subject: issue-1199
doc-type: reference

# interaction-design — issue #1199 current-state survey

## Governing basis

Issue #1199 (northpole req#1/req#5): survey the plugins/tools
practitioners in this role's domain most use, extract the design moves
each embodies, and fold distilled learnings into the rulebook as this
role's own native rules — no per-tool attribution in public rulebook
content, provenance kept only in this on-the-record trail.

## Rulebook write surface

canonical: git -C /tmp/idr log -1 --format=%H (this turn's tool transcript, clone of tokenmaxxxer/interaction-design-rulebook)
`tokenmaxxxer/interaction-design-rulebook` carries eleven machine-
enforced plugins (`id-proposal-shape`, `id-citation-format`,
`id-persona-goal`, `id-task-flow`, `id-state-completeness`,
`id-wireframe-staging`, `id-nielsen-heuristics`, `id-accessibility-floor`,
`id-usability-test-plan`, `id-traceability`, `id-stage-order`) plus one
substantive playbook file: `interaction-design/playbook/
01-form-control-and-layout.md` (issue-1174 batch 1, 7 condition→choice→
source rule blocks: control-type-by-option-count x2, field grouping,
navigation depth, text contrast floor, non-text contrast floor, and one
REMOVAL rule for mid-task modals).

## Design-system document — named as missing

canonical: find /tmp/idr -iname '*design-system*' (this turn's tool transcript)
Only a prior hunt report (docs/reports/2026-07-30-hunt-design-system-
contract.md) and an issue-12 proposal about a design-system contract
exist in the rulebook repo — no live token/type/color spec file at the
path a design-system document would occupy. Per this role's own
directive, that absence is a survey finding in itself: any proposal
touching token usage must name the gap, not silently assume such a
document exists.

## Methodology already named

The rulebook's phase-1/phase-2 gates already require Nielsen's ten
usability heuristics (`id-nielsen-heuristics`) and a named persona/goal
model (`id-persona-goal`) — this fold-in's proposal extends the
methodology already governing rather than introducing a new one.

## Gap this fold-in targets

Playbook file 01 covers forms/layout/navigation/contrast at a general
UI level. It carries no rules on: (a) prototyping fidelity staging —
what should differ in scope between a lo-fi wireframe and a hi-fi one,
beyond the `id-wireframe-staging` plugin's bare ordering check; (b) how
a usability-test plan should size its task scenario and participant
count — the `id-usability-test-plan` plugin checks presence, not
quality; (c) what an accessibility floor should concretely verify
beyond the WCAG contrast numbers already in rule R5/R6, before a spec
is judged ready; (d) how token references in a spec should be scoped
(semantic vs. primitive) given the missing design-system document.
These four gaps are the scout's targets.
