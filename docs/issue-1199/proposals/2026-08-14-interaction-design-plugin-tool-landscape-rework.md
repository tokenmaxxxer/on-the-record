---
subject: issue-1199
role: interaction-design
loop_state: scope-proposed
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-14-interaction-design-plugin-tool-landscape-rework.md
---

# Proposal: fold Claude Code plugin/skill landscape into interaction-design rulebook (issue-1199, 2026-08-14 amendment rework)

kind: proposal
subject: issue-1199

## Problem / goal framing

canonical: docs/issue-1199/reports/interaction-design.md and
docs/issue-1199/proposals/2026-08-13-interaction-design-tool-landscape.md
(this repo, read this turn) — the landed 2026-08-13 fold-in surveyed
Figma, Maze, UserTesting, Tokens Studio for Figma, and axe-core:
general interaction-design-domain practitioner tools, none of them a
Claude Code plugin or skill. The issue's 2026-08-14 amendment states a
fold-in whose surveyed sources are domain tools alone does not satisfy
the amended acceptance check, so interaction-design's tracker line
needs this additive rework before it counts toward it. Read basis:
`docs/issue-1199/reports/interaction-design/scout-brief-plugins.md`
(written this turn).

## Comparison set / exemplars

Two Claude Code plugins/skills surveyed with adoption evidence, plus
one vendor-published skill surface as secondary context
(`docs/issue-1199/reports/interaction-design/scout-brief-plugins.md`):

1. **Owl-Listener/designer-skills** (2.1k GitHub stars) — the broadest
   design-cycle skill collection, including an interaction-design
   plugin (22 skills) with `/interaction-design:map-states` and
   `/interaction-design:error-flow` as first-class, separately-named
   commands, and a prototyping-testing plugin (heuristic evaluation, A/B
   experiments).
2. **gotalab/uxaudit** (official Claude Code marketplace listing) —
   automated UX regression testing that walks live user journeys via
   Playwright, running ~40 checks split across five categories
   (AI-slop, accessibility, usability patterns, core-experience finish,
   visual/copy quality), each tied to a published design standard.
3. Figma's first-party Claude Code skills (via `claude-plugins-official`
   and Figma's own blog/resource pages) — noted as secondary context
   only, per the amendment's own carve-out; this role specs screens and
   never operates the design tool itself.

## Methodology cited

This role's existing governing methodology — Nielsen's ten usability
heuristics and WCAG 2.1 AA — is not replaced. This round extends the
already-landed manual-vs-automated accessibility split (from the prior,
domain-tool-basis round) with a sharper, plugin-ecosystem-confirmed
distinction: which flow states need a walked simulation versus a
presence check, per the scout-brief's performance-axis finding.

## What will be delivered

Two native rule additions, applied directly (apply-not-reference
amendment) into the named target files, phrased as this role's own
judgment with no tool-repo name or `source:` framing in the rulebook
body (native-application amendment — provenance stays only in this
on-the-record trail):

1. **State-simulation-vs-presence-check rule** — for each named flow
   state (`id-state-completeness`'s default/empty/error/loading set),
   the spec states explicitly whether that state's correctness can be
   judged by a static presence check (the state is named, its content
   is non-blank) or requires a walked simulation to judge (e.g. an
   error-recovery state whose correctness depends on whether the
   recovery path actually returns the user to a completable task, not
   only on whether an error message is present). Upgrades: the
   `id-state-completeness` plugin's default/empty/error/loading check,
   by adding a checked-by clause per state — applied into the
   state-completeness guidance file/section that plugin reads.
2. **Named-state-artifact rule** — state-mapping and error-flow are
   each named as their own distinct sub-artifact within the task/
   interaction-flow section (not folded as an unlabeled sub-bullet
   under a general flow narrative), mirroring the field's convergence
   on treating them as first-class commands. Upgrades: the
   `id-task-flow` plugin's distinct-heading check, by adding a
   named-sub-artifact clause — applied into the task-flow guidance
   file/section that plugin reads.

Delivery target: `tokenmaxxxer/interaction-design-rulebook`, branch
`issue-1199/plugin-tool-landscape`, editing the plugin-referenced
guidance content backing `id-state-completeness` and `id-task-flow` —
the exact files those two plugins' directive.sh/README point at,
confirmed at phase-2 build time.

## Adopt / skip rationale

Adopt: the two judgments above, because each closes a gap the scout
brief's gap line names (no existing rule distinguishes checked-by-
simulation from checked-by-presence at the individual-state level; no
existing rule names state-mapping/error-flow as first-class artifacts)
and each traces to one scout-brief finding (issue requirement 4's
per-tool traceability bar).

Skip: adopting uxaudit's live-Playwright-execution mechanism or
designer-skills' full 22-skill interaction-design plugin wholesale —
this role specs screens/flows and never runs a live app, writes test
automation, or operates a design tool; the judgment is adopted, not the
tool's surface, per the scout-directive's "never clone the exemplar"
rule and the native-application amendment's ban on tool-catalog framing
in rulebook content. Figma's own skill surface is out of scope for the
same reason, kept as secondary context only.

## How it will be judged

Judged done when: (a) both rules land as edits to the named target
files in `tokenmaxxxer/interaction-design-rulebook` in the same
delivery (apply-not-reference amendment), with no tool-repo name or
`source:` link in the rulebook body (native-application amendment); (b)
this repo's phase-2 record (`docs/issue-1199/reports/interaction-
design.md`) documents the rulebook PR/branch and cites the scout-brief
evidence trail for each rule, without duplicating tool names/URLs into
the rulebook, and sets `loop_state: landed` only once the named upgrade
files are actually edited and pushed; (c) the interaction-design row in
issue #1199's 43-item tracker stays checked (already checked from the
prior round; this is an additive rework, not a first landing).

## Plan for phase 2

1. On `tokenmaxxxer/interaction-design-rulebook`, branch
   `issue-1199/plugin-tool-landscape`: locate and edit the guidance
   content the `id-state-completeness` and `id-task-flow` plugins each
   reference, applying the two rules natively.
2. Open a PR against `tokenmaxxxer/interaction-design-rulebook` (or, if
   the cross-repo PR-create guard blocks it, push the branch and log a
   filed deviation for external relay, matching the prior round's
   observed pattern).
3. Update this repo's phase-2 record `docs/issue-1199/reports/
   interaction-design.md` documenting the branch/PR and the evidence
   trail, and set `loop_state: landed` once the edit is pushed.

## Out of scope

- Tool-landscape rework for any other role — each fan-out unit is
  separate per issue requirement 6.
- Re-opening or re-landing the four already-landed 2026-08-13 rules
  (fidelity-scope, test-sizing, provisional-token, manual/automated
  a11y split) — this rework is additive to them, not a replacement.
- Building or modifying the shape-check gate
  (`gates/playbook_depth_gate.py`) — issue's step-1 infra unit.
- Adopting Figma's own skill mechanics, uxaudit's Playwright execution,
  or designer-skills' full skill catalog beyond the two named judgments.

## Approval

Awaiting a PR review Approve (two-account mode) or an issue-level
`APPROVE issue-1199/interaction-design` comment (single-account mode)
from a `docs/specs/approvers.md` account, posted after this proposal
exists, before phase 2 (the rulebook edits and this repo's phase-2
record update) begins, per contract v3 s19. The existing
`APPROVE issue-1199/interaction-design` comment
(canonical: `gh issue view 1199 --comments`, this turn — timestamp
2026-08-13T07:02:23Z) predates the 2026-08-14 amendment and this
proposal, and does not authorize this rework's phase-2 work. This
session accordingly stops after phase 1, mirroring the devrel unit's
own rework proposal
(`docs/issue-1199/reports/devrel/scout-brief-plugins.md`'s companion
proposal, same pattern).
