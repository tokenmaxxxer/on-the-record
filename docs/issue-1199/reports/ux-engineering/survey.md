kind: report
subject: issue-1199
doc-type: reference

# ux-engineering — current-state survey (phase-1, issue #1199)

## What was checked

canonical: git -C /tmp/uxr1199 log -1 --format=%H (clone of
tokenmaxxxer/ux-engineering-rulebook, this turn's tool transcript)
Cloned `tokenmaxxxer/ux-engineering-rulebook` and read its `playbook/`
tree: five decision-axis files exist —
`playbook/color-visibility.md`, `playbook/surface-contrast.md`,
`playbook/control-selection.md`, `playbook/layout-grouping.md`,
`playbook/navigation-depth.md` — plus `playbook/research-log.md` as
the evidence trail for existing rules. Each axis file carries a
`rule_count_floor` front-matter field and numbered rules with
`source:` + `counter-example:` blocks (verified against
`playbook/control-selection.md`'s shape).

## Gaps this fold-in targets

Every existing rule in the five axis files traces to *research articles*
(NN/g and platform guidance) about UX judgment, not to *practitioner
tooling* — no rule currently reflects how a design-token pipeline
enforces single-source-of-truth token values, how a contrast checker
validates against rendered UI rather than isolated swatches, how an
accessible-primitives library encodes interaction-pattern-to-ARIA-role
mapping, how a component-isolation tool (Storybook-class) validates a
grouped layout before assembly, or how a tree-testing tool scores
navigation structures by a directness metric before shipping. This is
the gap issue #1199 asks this unit to close: fold tool-encoded design
moves into these same five axis files as native rules.

## kind / loop_state

kind: report
loop_state: phase-1-scouted
