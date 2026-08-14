---
subject: issue-1199
role: architecture
loop_state: scope-proposed
status: proposed
files:
  - playbook/dependency-direction.md
  - playbook/coupling-classification.md
  - playbook/module-boundary-definition.md
  - docs/handbooks/architecture-methodology.md
  - docs/issue-1199/reports/architecture.md
---

# Proposal: fold architecture's surveyed tool landscape into the rulebook (issue-1199)

All file paths above except the last live in the separate rulebook repo
(`tokenmaxxxer/architecture-rulebook`, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/architecture-rulebook`; see
`docs/issue-1199/reports/architecture/survey.md` and `scout-brief.md`),
not in this working tree; phase 2 branches and commits there directly,
mirroring the brand-design/ux-engineering precedent for this issue.

## Request

Per issue-1199 (northpole req#1/req#5), and per the operator's explicit
instruction for this role (verbatim intent, no attribution/catalog
section): fold the surveyed tool landscape's design moves directly into
this rulebook's own operating content — new condition/choice/why/source
rules in the existing playbook files, plus two methodology-handbook
requirements — with **no** "Tool learnings" section, no per-tool
attribution language, and no verbatim copying. The full evidence trail
(tools, adoption evidence, insight mapping) lives only in
`docs/issue-1199/reports/architecture.md` in this on-the-record repo,
never in the public rulebook.

## Constraints

- Adoption-evidence method (stars/downloads/multi-source mentions), not
  an ad hoc popularity claim — per issue requirement 1.
- No tool-catalog section and no "learned from repo X" attribution in
  the public rulebook — explicit operator instruction for this role,
  narrower than the brand-design/ux-engineering precedent's "Tool
  learnings" subsection pattern.
- No verbatim copying of any surveyed tool's own text.
- Each new rule/requirement states which existing deliverable/rule/
  judgment it upgrades — per issue requirement 4.
- Never delete existing playbook or methodology-handbook language.
- New playbook rules follow the exact existing rule shape
  (condition/choice/why/source) so they read as native rulebook content,
  not an inserted foreign block.

## What will be done

Four gaps identified in `survey.md`, one native rule/requirement each
(full design-move mapping in `scout-brief.md`):

1. `playbook/dependency-direction.md` — new rule 15: pair a declared
   dependency-direction decision with a generated (not asserted) import
   graph as its verification method. Upgrades: dependency-direction
   rules 1-14's decisions gain a required verification step instead of
   review-by-memory.
2. `playbook/coupling-classification.md` — new rule 15: combine
   structural coupling severity with observed change-frequency
   (co-change in version-control history) to order remediation.
   Upgrades: rule 14's "don't gate on the metric alone" warning gains a
   concrete second signal to pair the metric with.
3. `playbook/module-boundary-definition.md` — new rule 15: require a C4
   boundary diagram be generated from one versioned text model, not a
   pasted image. Upgrades: rule 13's container/component-level
   separation gains a diagram-provenance requirement so the two levels
   stay derived from one source instead of independently hand-drawn.
4. `docs/handbooks/architecture-methodology.md` — Phase 2 facet gains
   two requirements: (a) the C4 diagram accompanying a phase-2 record
   must be the text-model source from rule 15 above, not an image; (b) a
   record whose decision supersedes an earlier ADR for the same boundary
   must carry a `supersedes:`/`superseded_by:` frontmatter pointer.
   Upgrades: the existing "four ADR sections plus a C4-level diagram"
   requirement and the spec-alignment `outcome: superseded` value (which
   currently has no pointer field to the record it supersedes).

`docs/issue-1199/reports/architecture.md` (this repo) carries the full
evidence trail: the five surveyed tools, each with adoption evidence,
{problem, how, learning}, and which upgrade above it maps to.

## Out of scope

- Adopting any surveyed tool's own DSL, config format, or CLI as an
  actual dependency of this rulebook (native rules only).
- Gate-script changes (`arch-*-gate/hooks/*.sh`) — the new rules and
  requirements are documented/checklist-level for now; a follow-up issue
  may propose mechanizing them.
- Log4brains's hosted static-site publishing and CodeScene's org-wide
  dashboarding — no equivalent surface exists in this per-issue record
  practice.

## How success will be judged

- Each of the three playbook files gains exactly one new rule (15),
  in the same condition/choice/why/source shape as its existing rules,
  with no existing rule text altered or removed.
- `architecture-methodology.md`'s Phase 2 facet gains the two
  requirements above, worded without naming any surveyed tool by way of
  "learned from" attribution.
- `docs/issue-1199/reports/architecture.md` in this repo carries the
  full tool/evidence/mapping trail; the public rulebook files carry none
  of it.
