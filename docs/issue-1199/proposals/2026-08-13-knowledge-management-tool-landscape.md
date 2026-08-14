---
subject: issue-1199
role: knowledge-management
loop_state: scope-proposed
status: proposed
files:
  - docs/handbooks/knowledge-management.md
  - docs/issue-1199/reports/knowledge-management.md
---

# Proposal: fold knowledge-management's surveyed tool landscape into the rulebook (issue-1199)

All handbook paths below live in the separate rulebook repo
(`tokenmaxxxer/knowledge-management-rulebook`, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/knowledge-management-rulebook` — see
docs/issue-1199/reports/knowledge-management/current-state-survey.md and
scout-brief.md), not in this working tree; phase 2 branches and commits
there directly, mirroring the brand-design/interaction-design precedent
(docs/issue-1199/proposals/2026-08-13-brand-design-tool-landscape.md).

## Request

Per issue-1199 (northpole req#1/req#5, consult-log 2026-08-13T06:10:35
entry), add a bounded "Tool learnings" subsection to
`docs/handbooks/knowledge-management.md`: five surveyed KM-adjacent tools,
each with adoption evidence, problem/how/learning, and a named upgrade to
an existing template/field in the SAME handbook — never a tool catalog,
never a "learned from X" attribution inside the handbook body itself.

## Constraints

- Adoption evidence via the tech-feasibility method (stars/downloads/
  multi-source mentions), not an ad hoc popularity claim — per issue
  requirement 1.
- Size-capped, distilled design moves, not a tool catalog — per issue
  requirement 3.
- Each entry states which deliverable/rule/judgment it upgrades — per
  issue requirement 4.
- Every named upgrade target is actually edited in the same phase-2
  change (no reference-only fold-in).
- Never delete existing methodology language.

## What will be done

Edit `docs/handbooks/knowledge-management.md` directly (phase 2):

1. Pattern-entry front matter gains a `reused_by` field (list of issue
   numbers that later consulted/applied this entry) — closes the
   no-backlink gap; upgrades the pattern-library-entry template.
2. Phase-2 self-check gains a line: a landed entry's five body sections
   are never edited in place after `loop_state: landed` — only superseded
   — upgrades the phase-2 record self-check.
3. Pattern-entry front matter gains an `applies_to_roles` field (list of
   other role names this pattern is relevant to) — upgrades the
   pattern-library-entry template and the cross-issue index row shape.
4. The pattern-entry template's `<slug>` convention gains a required
   `<domain>.<slug>` prefix drawn from a short fixed domain list —
   upgrades the pattern-library-entry template's naming rule.
5. `docs/patterns/index.md`'s template gains a second required grouping
   (by `keywords`, alongside the existing by-source_issues table) —
   upgrades the cross-issue index template.

Each of the five items maps 1:1 to a scouted tool's design move (see
scout-brief.md's Gap line) and is applied as a rule/field change to the
rulebook's own template language — not as prose describing the tool.

## Out of scope

- Adopting any surveyed tool's UI, storage format, or plugin surface.
- Retrofitting existing landed pattern entries to the new fields (applies
  to future entries only, per rulebook convention for additive field
  changes).

## How you'll know it worked

- `docs/handbooks/knowledge-management.md` diff shows all five items
  landed as rule/template text, not a "learned from Obsidian" attribution
  line.
- docs/issue-1199/reports/knowledge-management.md (this role's phase-2
  record) states what was done, why, and cites the scout-brief/survey as
  upstream basis.
