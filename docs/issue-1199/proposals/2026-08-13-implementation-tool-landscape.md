---
status: approved
files:
  - implementation-rulebook: playbook/complexity-coupling-management.md
---

## Request
Survey the plugins/tools implementation (coding) practitioners most use
by adoption evidence, analyze {problem, how, learning} per tool, and
fold the learnings into implementation-rulebook's own operating content
as native rules — no per-tool attribution, no tool catalog in the
public rulebook. Full evidence trail lives only in on-the-record.

## Constraints
- Adoption evidence method: stars/downloads/multi-source, web-fetched,
  no pretrained recall (issue #1199 requirement 1).
- Bounded fold-in: distilled design moves, not a tool catalog (issue
  #1199 requirement 3).
- Applied natively as the role's own judgment, no "learned from repo X"
  attribution (issue #1199 body).
- Named upgrade target file must actually be edited (issue #1199 body,
  brand-design exemplar).

## Rationale
Considered folding learnings into a NEW standalone
`tool-learnings.md` file in the rulebook, mirroring the on-the-record
issue text's suggestion of a bounded `tool-learnings/` section as one
option. Rejected: this role's existing playbook convention already
carries numbered, sourced decision rules per topic file
(complexity-coupling-management.md, design-pattern-selection.md,
performance-data-structure-choice.md); adding a fourth file duplicates
that structure for content that fits the coupling-management file's
existing scope, and the issue's fold-in requirement is satisfied by
extending an existing rules list, not by adding a parallel catalog
surface that risks becoming exactly the "tool-catalog section" the
issue prohibits.

## What will be done
- Survey coding-implementation tooling by adoption evidence (stars,
  downloads, dependent-repo counts) across lint/format, architecture
  enforcement, and pre-merge-hook orchestration categories.
- Extract one design move per surveyed category and add each as a
  native numbered rule to `playbook/complexity-coupling-management.md`
  in the implementation-rulebook repo, each ending in a `source:` line
  to a general concept reference (never the tool's name).
- Write the full evidence trail (tools, adoption evidence, insight
  mapping) into docs/issue-1199/reports/implementation.md only.

## Out of scope
- Editing `design-pattern-selection.md` or
  `performance-data-structure-choice.md` — no surveyed tool's design
  move maps onto pattern selection or data-structure choice.
- The issue #1199 step-1 shared gate/tracker infrastructure — already
  landed, a separate deliverable.

## How you'll know it worked
- `playbook/complexity-coupling-management.md` in implementation-rulebook
  gains 3 new numbered rules with no tool names/attribution.
- docs/issue-1199/reports/implementation.md carries the full
  {tool, adoption evidence, problem, how, learning->rule} trail for all
  4 surveyed tools.
- A PR is open against implementation-rulebook's main and a PR is open
  against on-the-record's main, both referencing #1199 without a
  Closes trailer.
