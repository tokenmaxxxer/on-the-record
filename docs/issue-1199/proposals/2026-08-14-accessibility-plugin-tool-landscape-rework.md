---
subject: issue-1199
role: accessibility
loop_state: scope-proposed
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-14-accessibility-plugin-tool-landscape-rework.md
---

# Proposal: fold Claude Code plugin/skill landscape into accessibility-rulebook (issue-1199, 2026-08-14 amendment rework)

kind: proposal
subject: issue-1199

## Problem / goal framing

canonical: docs/issue-1199/reports/accessibility.md and
docs/issue-1199/proposals/2026-08-13-accessibility-tool-landscape.md
(this repo, read this turn) — the landed 2026-08-13 fold-in surveyed
axe-core, Lighthouse, Pa11y, Stark, and Microsoft Accessibility
Insights for Web: general accessibility-domain practitioner tools,
none of them a Claude Code plugin or skill. The issue's 2026-08-14
amendment states a fold-in whose surveyed sources are domain tools
alone does not satisfy the amended acceptance check, so accessibility's
tracker line needs this additive rework before it counts toward it.
Read basis: `docs/issue-1199/reports/accessibility/scout-brief-
plugins.md` (written this turn).

## Comparison set / exemplars

Two Claude Code plugins/skills surveyed with adoption evidence, plus
three lower-adoption plugins as secondary confirmation
(`docs/issue-1199/reports/accessibility/scout-brief-plugins.md`):

1. **Community-Access/accessibility-agents** (390 GitHub stars) — the
   highest-adoption accessibility plugin found; eleven named
   interaction-pattern specialists (aria, modal/focus-trap, contrast,
   keyboard, live-region, forms, alt-text/headings, tables, links,
   plus a coordinating lead and guided-audit wizard) enforcing WCAG
   2.2 AA, with a stated stance that automated tooling never replaces
   real AT testing.
2. **Owl-Listener/inclusive-design-skills** (93 stars) — an inclusive-
   design skill collection built by the same author as designer-
   skills (already an interaction-design-rework exemplar), organized
   into six plugins: cognitive accessibility, inclusive interaction
   (multi-modal input), accessible content, inclusive personas,
   adaptive interfaces, and accessibility decisions (ADR-style
   rationale capture for accessibility tradeoffs).
3. gotalab/uxaudit (51 stars), masuP9/a11y-specialist-skills (55
   stars), airowe/claude-a11y-skill (14 stars) — noted as secondary
   confirmation only; their scan-fix-verify catalogs restate the
   automated-scan-ceiling must-be this role's prior round already
   adopted.

## Methodology cited

This role's existing governing methodology (WCAG-EM, WCAG 2.1/2.2 AA)
is not replaced. This round extends the already-landed evidence-field
rules (5.1 AT tool+version naming, 5.2 machine-suggestion draft-only,
5.3 automated-scan ceiling) and the standing manual-check pair with two
additive, plugin-ecosystem-sourced judgments the prior domain-tool
round did not cover.

## What will be delivered

Two native rule additions, applied directly into the named target
files, phrased as this role's own judgment with no tool-repo name or
`source:` framing in the rulebook body (matching the interaction-
design rework's native-application convention — provenance stays only
in this on-the-record trail):

1. **Named-pattern manual-check rule** — for interaction-heavy
   patterns, the standing manual-check minimum (currently keyboard
   tab-stop walk + focus-visible walk) gains two named additions when
   the pattern includes a modal/dialog (focus-trap-and-return check)
   or dynamic content that updates without a page reload (live-region-
   announcement check), instead of relying on the generic SC 2.4.3/
   4.1.3 checklist bullets alone to surface these two specific,
   evidence-confirmed failure-prone patterns. Upgrades:
   `wcag-em-checklist/checklists/wcag-em.md`'s standing-minimum bullet
   from a two-item default pair to a conditional four-item set.
2. **Tradeoff-rationale scope-note rule** — when a `not-applicable`
   verdict reflects a deliberate design tradeoff (not merely "this SC
   cannot apply to this artifact type"), the scope note must also
   state the rationale the tradeoff was weighed against, mirroring
   ADR discipline. Upgrades: `playbook/aria-and-contrast-rules.md`'s
   scope-note guidance (currently only requires stating the exclusion
   boundary) to distinguish a boundary-exclusion note from a
   tradeoff-rationale note.

Delivery target: `tokenmaxxxer/accessibility-rulebook`, branch
`issue-1199/plugin-tool-landscape`, editing
`wcag-em-checklist/checklists/wcag-em.md` and
`playbook/aria-and-contrast-rules.md` — the same two files the prior
round edited.

## Adopt / skip rationale

Adopt: the two judgments above, because each closes a gap the scout
brief's gap line names (no existing rule names focus-trap-and-return
or live-region-announcement as distinct check items; no existing rule
distinguishes a tradeoff-rationale scope note from a boundary-
exclusion scope note) and each traces to one scout-brief finding
(issue requirement 4's per-tool traceability bar).

Skip: adopting accessibility-agents' eleven-specialist multi-agent
architecture or inclusive-design-skills' full 40-skill catalog
wholesale — this role produces one evaluation record per scope, not a
multi-agent audit pipeline; the judgment is adopted, not the tool's
surface, per the scout-directive's "never clone the exemplar" rule and
the native-application convention's ban on tool-catalog framing in
rulebook content.

## How it will be judged

Judged done when: (a) both rules land as edits to the named target
files in `tokenmaxxxer/accessibility-rulebook` in the same delivery;
(b) this repo's phase-2 record (`docs/issue-1199/reports/
accessibility.md`) documents the rulebook PR/branch and cites the
scout-brief-plugins.md evidence trail for each rule, without
duplicating tool names/URLs into the rulebook, and sets
`loop_state: landed` only once the named upgrade files are actually
edited and pushed; (c) the accessibility row in issue #1199's 43-item
tracker stays checked (already checked from the prior round; this is
an additive rework, not a first landing).

## Plan for phase 2

1. On `tokenmaxxxer/accessibility-rulebook`, branch
   `issue-1199/plugin-tool-landscape`: add the named-pattern manual-
   check rule to `wcag-em-checklist/checklists/wcag-em.md` and the
   tradeoff-rationale scope-note rule to
   `playbook/aria-and-contrast-rules.md`.
2. Open a PR against `tokenmaxxxer/accessibility-rulebook` (or, if the
   cross-repo PR-create guard blocks it, push the branch and log a
   filed deviation for external relay, matching the prior round's
   observed pattern in
   `docs/issue-1199/reports/accessibility/deviation-log.md`).
3. Update this repo's phase-2 record
   `docs/issue-1199/reports/accessibility.md` documenting the branch/
   PR and the evidence trail, and set `loop_state: landed` once the
   edit is pushed.

## Out of scope

- Tool-landscape rework for any other role — each fan-out unit is
  separate per issue requirement 6.
- Re-opening or re-landing the three already-landed 2026-08-13 rules
  (5.1 AT evidence specificity, 5.2 machine-suggestion draft-only, 5.3
  automated-scan ceiling) or the existing standing manual-check pair —
  this rework is additive to them, not a replacement.
- Building or modifying the shape-check gate
  (`gates/playbook_depth_gate.py`) — issue's step-1 infra unit.
- Adopting accessibility-agents' multi-agent architecture or
  inclusive-design-skills' full skill catalog beyond the two named
  judgments.

## Approval

Awaiting a PR review Approve (two-account mode) or an issue-level
`APPROVE issue-1199/accessibility` comment (single-account mode) from
a `docs/specs/approvers.md` account, posted after this proposal
exists, before phase 2 (the rulebook edits and this repo's phase-2
record update) begins, per contract v3 s19. The existing
`APPROVE issue-1199/accessibility` comment
(canonical: `docs/issue-1199/reports/accessibility.md`, "What was
done" section, read this session) predates the 2026-08-14 amendment
and this proposal, and does not authorize this rework's phase-2 work.
This session accordingly stops after phase 1, mirroring the
interaction-design rework's own stop point
(`git show 70ca1890:docs/issue-1199/proposals/2026-08-14-interaction-
design-plugin-tool-landscape-rework.md`'s "Approval" section, read
this session).
