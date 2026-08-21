---
status: proposed
files:
  - docs/reports/keep-role-family-classification.md
---

# phase-4a: family-classify the 300 keep-role hooks (#1764)

## Request

Group the 300 `keep-role` hook rows (post-#1753) into families by what
they mechanically check, give each family exactly one disposition
(fold-to-core-gate with a named target/config shape, or demote-to-
guidance with a rationale), and build a per-rulebook migration-blocking
map — classification only, no hook moved/edited/deleted.

## Constraints

- Scope is exactly `docs/reports/keep-role-family-classification.md`;
  no hook file in any of the 43 rulebook repos is touched.
- Every hook must be classified from its full script body (the #1750
  lesson the issue names directly), not from the audit's header-comment
  excerpt.
- Family definitions must be stated up front by mechanical check
  content, not by filename alone.
- Every family carries exactly one disposition; a family may be split
  only with per-hook justification rows.
- Counts must sum to 300, verified by a shape check in the record.

## Rationale

Considered classifying purely by full-body keyword matching (grep the
entire script body for family-defining terms like "citation" or
"facet") instead of anchoring the signature to filename/plugin-name.
Rejected mid-classification: header comments in these gate scripts
routinely cross-reference sibling plugins by name for context (e.g. a
citation-gate.sh's header mentioning "see also id-stage-order's gate"),
and a full-body keyword scan matched those cross-references as if they
were the hook's own check content, misclassifying at least 3 hooks
before the signature was narrowed to filename+plugin-name (full-body
reading was retained for verification of every match, and to resolve
the 3 collisions found this way — the deliverable's own "What did not
work" section records each).

Also considered one family per unique hook filename (137 distinct
filenames across the 300 rows). Rejected: this fails requirement 1's
"group by what they mechanically check" — many distinct filenames (e.g.
25 separate `methodology-gate.sh` instances across different rulebooks)
share the identical record-section-shape mechanism and would produce a
fold target with no shared core-gate config, defeating requirement 2's
parameterization purpose.

## What will be done

1. Build the 300-row input set (307 keep-role rows minus the 7 rows the
   #1753 sweep reclassified to `promote`).
2. Clone all 43 rulebook repos carrying a keep-role row; locate and read
   each row's full script body.
3. Classify every row into one of 6 families (role-directive,
   record-section-shape, ordering-methodology, citation-sourcing,
   facet-keyword, field-format-numeric) via the filename/plugin-name
   signature described in the survey's Method section.
4. Assign each family one disposition: fold (naming a `core/hooks/*.sh`
   target and a config shape) or demote (with a stated rationale).
5. Build the per-rulebook migration-blocking map (which fold families
   each rulebook's hooks depend on before it can map to phase-3 skill
   migration).
6. Run and record the two Acceptance shape checks (count=300/no
   family-less hook; no disposition-less family/every fold family names
   a target) directly in the deliverable doc.

## Out of scope

- Moving, editing, or deleting any hook file in any rulebook repo.
- Creating or wiring the named core gates (`record-shape-gate.sh`,
  `ordering-norm-gate.sh`, `citation-gate.sh`, `facet-keyword-gate.sh`)
  — that is a follow-up core issue fed by this classification, same as
  the #1753 sweep's promote-list handoff pattern.
- Migrating any rulebook's skills to skill-repository — blocked on the
  fold families landing in core first, per requirement 4.

## How you'll know it worked

`docs/reports/keep-role-family-classification.md` exists with: a
Families table (name, definition, count, disposition, core target or
demotion rationale) covering exactly 6 families that sum to 300; a
per-rulebook migration-blocking map for all 43 rulebooks; a 300-row
per-hook table (rulebook, hook file, family); and both Acceptance
checks recorded with their live-verified results.
