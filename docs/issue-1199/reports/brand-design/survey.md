---
subject: issue-1199
role: brand-design
kind: survey
loop_state: surveyed
---

# Current-state survey: brand-design rulebook (issue-1199)

canonical: /home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook
(read this session — README.md, docs/handbooks/brand-design/
methodology.md, and the four brand-design-*/README.md files, all
outside this working tree in the separate rulebook repo).

## Where the rulebook lives
Separate repo "tokenmaxxxer/brand-design-rulebook" (roles/brand-design
.json's repo field in this working tree, read this session), mounted
locally at /home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook.
Prior issue-20 landed there with branch issue-20/implementation, docs
under a per-issue proposals/reports layout, and commit trailer
"Subject: issue-20" — same layout this fan-out unit follows for
issue-1199.

## Existing structure (four plugins, one per methodology facet)
- brand-design-guide-and-spec — brand guide entry + asset spec
  presence/cross-reference gate.
- brand-design-kapferer-scope-guard — Physique-facet scope boundary
  (phase-1 and phase-2 modes).
- brand-design-wcag-consistency — consistency check + WCAG contrast
  ratio gate.
- brand-design-system-handoff — literal repo paths for the
  ux-engineering handoff.

Each plugin's gate is mechanical (a PreToolUse hook denying a write
that lacks required content); the methodology handbook is the judgment
layer the gates cannot check — checklists worded as questions the
writer answers.

## Where a bounded tool-learnings section fits
The methodology handbook already carries a "Design-token vocabulary
(spec-aligned)" subsection from issue-20 mapping the role spec's fields
onto the phase-2 checklist. The same pattern — a bounded subsection
layering new vocabulary onto existing checklist items, never replacing
them — is the right home for issue-1199's tool-learnings fold-in.

## No existing tool-landscape section
No tool-learnings heading, no adoption-evidence citations, and no
plugin README references an external tool's design move anywhere in
the four plugin READMEs or the methodology handbook (read this
session) — this fan-out unit adds the section, it does not revise one.
