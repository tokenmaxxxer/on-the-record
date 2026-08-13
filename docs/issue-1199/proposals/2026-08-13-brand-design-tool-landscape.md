---
subject: issue-1199
role: brand-design
loop_state: scope-proposed
status: proposed
files:
  - docs/handbooks/brand-design/methodology.md
  - brand-design-guide-and-spec/README.md
  - brand-design-wcag-consistency/README.md
  - brand-design-system-handoff/README.md
  - docs/issue-1199/reports/brand-design.md
---

# Proposal: fold brand-design's surveyed tool landscape into the rulebook (issue-1199)

All file paths below live in the separate rulebook repo
("tokenmaxxxer/brand-design-rulebook", mounted at
/home/jwjung/tokenmaxxxer/rulebooks/brand-design-rulebook — see
docs/issue-1199/reports/brand-design/survey.md), not in this working
tree; phase 2 will branch and commit there directly, mirroring
issue-20's pattern.

## Request
Per issue-1199 (northpole req#1/req#5, consult-log 2026-08-13T06:10:35
entry), add a bounded "Tool learnings" subsection to the methodology
handbook: five surveyed brand-design-adjacent tools, each with
adoption evidence, problem/how/learning, and a named upgrade to an
existing checklist line — never a tool catalog.

## Constraints
- Adoption evidence via the tech-feasibility method (stars/downloads/
  multi-source mentions), not an ad hoc popularity claim — per issue
  requirement 1.
- Size-capped, distilled design moves, not a tool catalog — per issue
  requirement 3.
- Each entry states which deliverable/rule/judgment it upgrades — per
  issue requirement 4.
- Never delete existing methodology language (issue-20 precedent,
  still binding).

## What will be done
Add one "Tool learnings (issue-1199)" subsection to the methodology
handbook, five entries, each capped to a short paragraph:

1. **diagram-design** (cathrynlavery/diagram-design; GitHub-trending,
   multi-thousand-star repo per trendshift.io/repositories/26141 and
   the repo's own star count — see scout-brief Sources). Problem: ad
   hoc diagram tooling (e.g. Mermaid) produces visually inconsistent,
   templated output for stakeholder-facing handoffs. How: a bounded,
   named list of diagram types, each rendered as self-contained
   HTML+SVG with a fixed visual style — no free-form category field.
   Upgrades: brand-design-system-handoff's literal-path requirement
   gains a companion line — name the diagram/asset TYPE from a fixed
   list, not a free-form description, alongside the path.

2. **Style Dictionary** (style-dictionary/style-dictionary, an Amazon-
   originated build system; GitHub-topic presence and multiple
   dependent packages — see scout-brief Sources). Problem: a token
   value hand-copied into each platform drifts from its source. How: a
   single source-of-truth token file transformed into every consuming
   format by one pipeline, never edited per-platform. Upgrades:
   brand-design-guide-and-spec's asset-spec item gains a distinct
   line — name the token source-of-truth file path, separate from the
   applied value already required.

3. **Tokens Studio for Figma** (tokens-studio/figma-plugin; cited
   production use at TomTom and Babbel design systems per
   docs.tokens.studio — see scout-brief Sources). Problem: multi-brand
   or multi-theme token sets re-diverge when each theme is maintained
   by hand. How: a graph-structured token model with explicit theme
   composition, synced to git as JSON. Upgrades: brand-design-guide-
   and-spec's brand-guide-entry item gains a line — when more than one
   brand/theme variant is touched, name which variant(s) explicitly,
   never left implicit.

4. **Stark** (getstark.co; over 40,000 users across over 28,000
   companies as vendor-stated adoption, and separately over 230,000
   users on the Figma plugin page — see scout-brief Sources). Problem:
   aggregate "looks fine" contrast review misses individual failing
   pairings inside a mostly-passing set. How: automated per-element
   contrast ratio and pass/fail badge, computed per pairing rather than
   once for the whole surface. Upgrades: brand-design-wcag-
   consistency's per-item pass/fail line is reworded to require one
   explicit line per distinct text/background pairing, not one
   consolidated verdict covering several pairings.

5. **zeroheight** (zeroheight.com; multiple published customer case
   studies and its own annual Design Systems Report — see scout-brief
   Sources). Problem: a design-system handoff artifact can exist and
   still go unread — "driving adoption" is reported as design systems'
   top recurring challenge in zeroheight's own report data. How: track
   documentation engagement and downstream component usage as a
   distinct signal from artifact existence. Upgrades: brand-design-
   system-handoff's literal-path item gains a line — name which
   downstream role/path is expected to actually consume the handoff,
   not only where it lives.

Companion README edits (brand-design-guide-and-spec, -wcag-
consistency, -system-handoff): one sentence each pointing to the new
handbook subsection, mirroring issue-20's README-mirrors-handbook
pattern — no gate-logic change.

docs/issue-1199/reports/brand-design.md is phase-2 output, written only
after approval opens phase 2, per contract v3 s19.

## Out of scope
- Any change to brand-design-kapferer-scope-guard (no surveyed tool
  maps to the Kapferer-facet scope-boundary concern).
- Mechanical shape-gate changes (gates/playbook_depth_gate.py or a
  sibling gate) — issue-1199's acceptance criterion 1 names this as a
  possible cross-cutting gate; out of scope for a single role's
  fold-in PR, tracked at the issue level instead.
- Installing or depending on any of the five surveyed tools — the
  fold-in borrows the design move only (see scout-brief's adopt/skip
  split).

## How you'll know it worked
Phase 2 diff, reviewed against this proposal, adds exactly the five
entries above (each carrying tool name, adoption-evidence citation,
problem, how, and the checklist line it upgrades) plus the three
one-line README pointers, with no deletion of existing handbook or
README text.
