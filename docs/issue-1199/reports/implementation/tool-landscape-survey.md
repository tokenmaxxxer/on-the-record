# issue-1199 implementation survey (step 2: self tool-landscape fold-in)

## Write surfaces
- `implementation-rulebook` repo, `playbook/complexity-coupling-management.md`
  (canonical: /home/jwjung/implementation-rulebook/playbook/complexity-coupling-management.md,
  read this session) — the operational playbook file this role already
  uses for coupling/cohesion decision rules (6 rules present before this
  unit, per `git show 217810f^:playbook/complexity-coupling-management.md`
  read this session). This is the natural fold-in home: the 3 new design
  moves (boundary-at-write-time, consolidation, cheapest-first ordering)
  are all complexity/coupling-management judgments.
- `playbook/design-pattern-selection.md` and
  `playbook/performance-data-structure-choice.md` (both read this
  session) — surveyed but not edited: none of the four tools' design
  moves (lint consolidation, architecture-fitness testing, hook
  ordering) bear on pattern selection or data-structure choice, so
  folding into those files would be attribution-shaped padding, not a
  genuine upgrade.

## Unknowns the survey resolved
- Whether this role has an existing "tool-learnings"-shaped section
  convention to extend:
  canonical: this session's own live command, output below.

```
$ grep -rn "tool-learnings\|tool_learnings" /home/jwjung/implementation-rulebook/playbook /home/jwjung/implementation-rulebook/*.md
```
  (no output — no prior fold-in existed for this role's own rulebook
  content; step 1, this issue's shared gate/tracker infra, is a
  different, already-landed deliverable.)
- Bounded fold-in without a catalog: issue #1199 requirement 3 forbids a
  tool-catalog section. Chosen approach: apply each design move as a
  native numbered rule in the existing rules list (rules 7-9), each
  ending in a `source:` line pointing to a general concept reference
  (fitness functions / static analysis / fail-fast), never the surveyed
  tool's name — matching the issue's own "no 'learned from repo X'"
  instruction. canonical: docs/issue-1199/reports/brand-design.md
  (commit 2f7f902, read this session) describes brand-design's own
  fold-in the same way — a bounded section with no per-tool
  attribution in the public rulebook.
