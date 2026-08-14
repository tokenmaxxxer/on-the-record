---
subject: issue-1199
role: knowledge-management
loop_state: scope-proposed
status: proposed
files:
  - docs/handbooks/knowledge-management.md
  - docs/issue-1199/reports/knowledge-management.md
---

# Proposal: fold Claude Code plugin/skill landscape into knowledge-management rulebook (issue-1199, 2026-08-14 amendment rework)

All file paths below except this repo's own record/proposal live in the
separate rulebook repo (`tokenmaxxxer/knowledge-management-rulebook`,
mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook`) —
see docs/issue-1199/reports/knowledge-management/scout-brief-plugins.md.

## Request

The 2026-08-14 amendment to issue-1199 supersedes the prior survey
target: the CLAUDE CODE PLUGIN/SKILL ecosystem relevant to
knowledge-management, not general KM/PKM practitioner tools. Add a
second, additive tool-learnings section to
`docs/handbooks/knowledge-management.md`: three surveyed Claude Code
plugins/skills, each with adoption evidence, problem/how, and a named
upgrade to an existing rulebook field/self-check.

## Problem/Motivation

canonical: docs/issue-1199/reports/knowledge-management.md (this repo,
read this turn), commit 0beb2fe in
tokenmaxxxer/knowledge-management-rulebook — the 2026-08-13 fold-in
surveyed Obsidian, an ADR-example GitHub repo, Backstage TechDocs,
Dendron, and Notion: general PKM/IDP/docs products, none of them a
Claude Code plugin or skill. The amendment states a fold-in whose
surveyed sources are domain tools alone does not satisfy the acceptance
check, so this role's tracker line needs this additive rework.

## Proposed surface decision

Add one "Claude Code plugin/skill tool learnings (issue-1199, 2026-08-14
amendment)" section to `docs/handbooks/knowledge-management.md`, placed
after the existing enforcement-plugin-composition table (kept, not
removed — the amendment adds a plugin/skill-sourced set, it does not
retract the prior domain-tool one). Three entries, each naming which
existing field/self-check it upgrades:

1. **coleam00/claude-memory-compiler**. Session-boundary hooks feed a
   compilation step that extracts decisions into cross-referenced
   articles, ahead of manual authoring. Upgrades: the phase-2 self-check
   gains a line prompting `reused_by` citation at the point a later
   record names an entry as upstream basis, instead of leaving that
   citation to happen only if remembered.
2. **Korni22/claude-adr** (`ruflo-adr`, 65.4K-star listing on
   claudeskills.info). Bundles create+index+supersede+link into one
   action. Upgrades: the phase-2 self-check's supersession item becomes
   one paired line — both `superseded_by`/`supersedes` edits checked
   together, not as two independently satisfiable items.
3. **terrylica/cc-skills**. Groups skills by lifecycle phase
   (bootstrap vs. ongoing). Upgrades: the enforcement plugin composition
   table gains an explicit phase label already implicit in its
   phase-1/phase-2 row split, making the label machine-checkable
   phrasing rather than only a table structure.

docs/issue-1199/reports/knowledge-management.md is phase-2 output,
updated only after this rework lands, per contract v3 s19.

## Constraints

- Adoption evidence via the tech-feasibility method (stars/listing
  counts/multi-source mentions) — per issue requirement 1.
- Size-capped, distilled design moves, not a plugin catalog — per issue
  requirement 3.
- Each entry states which existing field/self-check it upgrades — per
  issue requirement 4.
- Every named upgrade target is actually edited in the same phase-2
  change.
- No tool-attribution framing inside the handbook body (per the
  2026-08-13 "native application, no tool-attribution catalogs"
  amendment already reconciled in the prior fold-in) — insight absorbed
  natively; provenance stays in this repo's records only.
- Never delete existing methodology language.

## Out of scope

- Adopting any surveyed plugin's actual runtime (hooks, compilation
  step, marketplace tagging UI).
- Retrofitting existing landed pattern entries to the upgraded
  self-check wording (applies to future phase-2 rounds only).

## How you'll know it worked

- `docs/handbooks/knowledge-management.md` diff shows all three items
  landed as rule/self-check text, not a "learned from claude-adr"
  attribution line.
- docs/issue-1199/reports/knowledge-management.md (this role's phase-2
  record) states what was done, why, and cites the scout brief as
  upstream basis.

## Upstream basis / continuation

This rework amends the already-landed knowledge-management unit on this
issue (`APPROVE issue-1199/knowledge-management`, issue #1199 comment,
single-account mode) under the 2026-08-14 amendment, rather than opening
a new approval cycle for an already-approved role line — same reasoning
the devrel rework
(docs/issue-1199/proposals/2026-08-14-devrel-plugin-tool-landscape-rework.md)
used.
