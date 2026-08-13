---
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-13-tool-landscape-fold-in.md
---

# issue-1199 (technical-writing): tool-landscape fold-in

kind: proposal
subject: issue-1199

Proposal: docs/issue-1199/proposals/2026-08-13-tool-landscape-fold-in.md

## Background

Issue #1199 (northpole req#1/req#5) asks every role to survey the
plugins/tools practitioners in its domain actually use, with adoption
evidence, and fold distilled learnings into a bounded rulebook section
naming which deliverable/rule/judgment each learning upgrades. It is a
separate program from #1174's playbook build. Read basis: `docs/issue-
1199/reports/technical-writing/current-state-survey.md` and `docs/
issue-1199/reports/technical-writing/scout-brief.md` (both written this
turn). The rulebook already carries #1174's five `playbook/*.md` axis
files (doc-type-selection, minimalism-scoping, style-guide-compliance,
structure-comprehension, persuasion-trust) — canonical: `ls
/tmp/twr-1199/playbook` output this turn (tool transcript) — but none
of them names a tool or tool-derived design move; this proposal is the
missing fold-in.

## Target reader

A phase-2 implementing session (this role) that will add a new
`playbook/tool-landscape.md` file to tokenmaxxxer/technical-writing-rulebook
following the existing axis-file shape (front matter + condition→choice→
source rule blocks), with no further scouting needed — the scout brief
already carries the sourced findings.

## Proposed structure

New file `playbook/tool-landscape.md`, `rule_count_floor: 6` (below the
existing axis files' 10, since this is a fold-in bounded by issue
requirement 3's "not a tool catalog," not a full decision axis).
Content, per finding in `docs/issue-1199/reports/technical-writing/
scout-brief.md`:

1. **diagram_cost_tradeoff** — when: a deliverable would benefit from a
   diagram. choice: name explicitly whether the diagram optimizes for
   visual polish (editorial, hand-placed, infrequently updated) or for
   update-cheapness (as-code, regenerated on every change) — never
   silently default to one. source: `cathrynlavery/diagram-design`
   (editorial exemplar) vs Mermaid (as-code exemplar), scout brief
   §Diagramming. Upgrades: doc-type-selection.md's diagram judgment,
   currently absent.
2. **visual_noise_discipline** — when: producing an editorial-style
   diagram. choice: cap to one accent color and 1-2 focal elements per
   diagram; avoid decorative shadow/gradient noise. source: diagram-
   design's constraint set (accent-color cap, focal-element cap,
   grid-snap), scout brief §Diagramming. Upgrades: minimalism-
   scoping.md's diagram judgment, currently absent.
3. **style_rule_executability** — when: a style-guide-compliance note
   would otherwise stay advisory prose only. choice: prefer citing or
   pointing to an executable check (a Vale-style rule file, a lint
   config) over a prose-only compliance claim, where the repo has one;
   name the gap explicitly when it doesn't. source: Vale's "compile the
   style guide into CI-checkable rules" move, scout brief §Prose/style
   linting. Upgrades: style-guide-compliance.md's accuracy-review-
   evidence judgment.
4. **diataxis_confirmed_by_field** — when: choosing a Diátaxis quadrant
   (doc-type-selection.md's existing rule). choice: no rule change —
   record that both major docs-site generators (Docusaurus, MkDocs
   Material) structurally assume the same quadrant discipline, so this
   axis needs no fold-in beyond a confirming citation. source: scout
   brief §Docs-site generation gap line. Upgrades: nothing new;
   documents that the existing rule already matches practitioner
   tooling (issue requirement 4's "visibly upgrade" bar is met by
   confirmation here, not by adding a redundant rule).

Each entry keeps the axis files' shape: condition → choice → source,
each tagged with which existing playbook file's judgment it upgrades
(issue requirement 4). Adoption-evidence citations (stars/downloads/
multi-source mentions) live in the scout brief, referenced by name here
rather than restated, to keep this file bounded per issue requirement 3.

## Rationale

- Bounded fold-in (issue requirement 3, consult finding): four entries,
  not a tool catalog — each traces to one scout-brief finding and one
  named upgrade target, per requirement 4's "each learning traces to
  the surveyed tool" bar.
- Adoption evidence routed through the scout's WebSearch/WebFetch trail
  (issue requirement 1), not pretrained-recall — `docs/issue-1199/
  reports/technical-writing/scout-brief.md`'s Sources list carries every
  citation.
- `diataxis_confirmed_by_field` is included even though it adds no new
  rule, because issue requirement 4 asks each role to state what it
  learned per category surveyed — a category that confirms rather than
  changes an existing rule is still a real finding, and silently
  dropping it would understate the survey's actual coverage.
- `rule_count_floor: 6` (not 10) mirrors #1174's own per-axis floor
  convention while staying under it, since this file's scope (four
  distilled learnings) is intentionally narrower than a full decision
  axis — sized to what the scout brief actually supports, not padded
  to match the existing floor.

## Plan for phase 2

1. Add `playbook/tool-landscape.md` to tokenmaxxxer/technical-writing-rulebook,
   branch `issue-1199/tool-landscape`, with the four entries above in
   the existing playbook/*.md rule-block shape.
2. Add a README Layout line pointing to the new file, mirroring the
   existing playbook/*.md bullet.
3. Open a PR against tokenmaxxxer/technical-writing-rulebook; land the
   PR URL and diff summary in `docs/issue-1199/reports/technical-
   writing.md` (this repo's phase-2 record, gated behind the
   `APPROVE issue-1199/technical-writing` comment per contract v3 s19).
4. Check off the technical-writing row in issue #1199's 43-item tracker
   once the rulebook PR is opened.

## Out of scope

- Adding tool-landscape sections for any role other than
  technical-writing — each role's fan-out unit is separate per issue
  requirement 6 (distinct branches, never shared).
- Building the shape-check gate extending `gates/playbook_depth_gate.py`
  for entry-completeness (issue Acceptance check 1) — that is the
  issue's step-1 infra unit, not a per-role fan-out unit.
- Cloning diagram-design's full 27-type catalog or Vale's rule syntax
  into the rulebook — scout brief's explicit adopt/skip call, per
  scout-directive's "never clone the exemplar" rule.
- Touching the 43-item tracker for any row but technical-writing's own.

## Approval

Awaiting a PR review Approve (two-account mode) or an issue-level
`APPROVE issue-1199/technical-writing` comment (single-account mode)
from a `docs/specs/approvers.md` account before phase 2 (the rulebook
PR and this repo's phase-2 record) begins, per contract v3 s19.
