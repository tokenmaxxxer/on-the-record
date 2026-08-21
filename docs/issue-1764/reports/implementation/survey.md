# Current-state survey: issue #1764 (phase-4a family classification)

## Skip condition

design-research-skip: mechanical / assumptions-skip: mechanical, per the
issue's own labels (canonical: `gh issue view 1764`, read live). This
issue's requirements 1-4 and Acceptance section specify the family
grouping criterion, disposition vocabulary (fold/demote), and the output
doc's required sections verbatim, leaving no open design decision.
Scouting is skipped under the scout-directive's own "spec leaves no
design decision open" condition.

## Write set

- `docs/reports/keep-role-family-classification.md` (already committed
  at f7fd9026) — the sole scope named by the issue's own
  `scope: docs/reports/keep-role-family-classification.md` line.

canonical: `gh issue view 1764` body, read live — states "This issue is
the CLASSIFICATION deliverable only — no hook is moved, edited, or
deleted." No repo other than this one receives a commit from this issue;
the 43 rulebook repos referenced in the deliverable's Methodology
section were cloned read-only, to fetch full script bodies as
classification evidence.

## Current state

canonical: `docs/reports/rulebook-hook-audit.md` and
`docs/reports/ordering-norm-sweep.md`, read live from the working tree.

- `rulebook-hook-audit.md`'s Summary table: promote 7 / keep-role 307 /
  retire 0 / total 314, across 44 rulebooks. Its own Methodology section
  states classification was by header-comment reading, not full-script
  reading.
- `ordering-norm-sweep.md` (#1753) screened those 307 keep-role rows,
  read 14 candidates' full script bodies, and reclassified 7 rows to
  `promote` — its "Updated class counts" section states 300 keep-role
  rows remain, this issue's frozen input.
- `docs/reports/` carries no prior family classification of the 300
  keep-role rows before this issue.

## Method (mechanical, no design decision)

1. Extract the audit table's 307 keep-role rows; remove the 7
   #1753-promoted rows (matched by rulebook+plugin+filename) -> 300.
2. Clone all 43 rulebook repos carrying at least one keep-role row.
3. Locate each row's script file on disk; read its full body.
4. Classify each hook into one of 6 families via a deterministic,
   filename/plugin-name-anchored signature match, in priority order
   (event type first for SessionStart/UserPromptSubmit/PostToolUse,
   then filename-pattern signatures for PreToolUse gates).
5. Assign each family exactly one disposition (fold naming a core-gate
   target + config shape, or demote with a stated rationale).
6. Build the per-rulebook migration-blocking map.
7. Run the two Acceptance shape checks and record their output in the
   deliverable doc's own Acceptance checks section.

## Alternatives considered (for the proposal's Rationale)

- **Full-body keyword matching as the primary family-boundary
  signature** (rather than filename/plugin-name-anchored matching):
  considered and rejected mid-classification — header comments
  cross-reference sibling plugins by name (e.g. a citation-gate.sh
  header naming a sibling "stage-order" plugin), which produced
  false-positive family matches when the classifier matched against
  full body text instead of filename/plugin-name; the deliverable's own
  "What did not work" section documents 3 such corrections.
- **One family per unique hook filename** (137 distinct filenames in the
  300-row set, per the audit table's `hook file` column): rejected —
  does not group by "what they mechanically check" per requirement 1;
  e.g. `methodology-gate.sh` alone spans 25 rows across a dozen
  rulebooks and is mechanically almost all a record-section-shape check,
  so splitting by filename would leave no shared core-gate target per
  family, defeating requirement 2's per-family parameterization intent.
