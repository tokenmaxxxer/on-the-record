---
subject: issue-1199
role: data-modeling
kind: survey
---

# Current-state survey: data-modeling rulebook (issue-1199)

canonical: `README.md` (tokenmaxxxer/data-modeling-rulebook repo root,
mounted at /home/jwjung/tokenmaxxxer/rulebooks/data-modeling-rulebook),
Methodology section, read this session.

## Layers
The rulebook's methodology already routes every phase-2 deliverable
through explicit conceptual/logical/physical layering (README.md,
"Every phase-2 deliverable must produce conceptual, logical, and
physical model artifacts...") and a required `verdict` field. This is
the write surface the tool-landscape fold-in upgrades, not replaces.

## Methodology fit
This is a cross-cutting survey, not a single schema deliverable, so no
single row of the methodology table (Inmon/3NF, Kimball dimensional,
Data Vault) applies alone — the fold-in touches the methodology table
itself plus the Data Vault row's deviation-column convention
specifically. Explicit no-single-fit statement: this survey spans all
three rows at the methodology-table level.

canonical: `README.md` (tokenmaxxxer/data-modeling-rulebook repo root),
Methodology section and Data Vault deviation row, read this session —
the items below are the absence of the following text in that section.
## Gaps found (feeding the scout sweep)

1. No requirement that a deliverable's grain/constraints be expressed
   as a machine-checkable assertion — only "normalization rationale"
   prose is required.
2. No requirement that an ERD/diagram artifact be reproducible from its
   source (DDL/migration or diffable text) rather than a static image.
3. No naming-convention floor for the Data Vault row's hash-key/
   hash-diff/load-metadata columns, so satellite/link artifacts from
   different deliverables aren't structurally comparable.

## Alternatives considered
Considered leaving the fold-in as a separate `tool-learnings/` doc
cross-referenced from the methodology table, mirroring some sibling
roles' handbook-file convention. Rejected: this rulebook keeps its
methodology directly in README.md with no separate handbook file, so a
satellite doc would fork the source of truth the gate above already
enforces; folding the three upgrades directly into the existing table/
row keeps one methodology source.

## Open questions
Whether the shape-gate extension named in issue-1199's Acceptance
section (extending `gates/playbook_depth_gate.py` or a sibling gate to
check tool-learnings entry completeness) belongs to this per-role unit
or to the issue's separate step-1 implementation unit. Resolved for
this unit's scope as: the issue's own "실행 계획" step 1 is a distinct
implementation unit; this survey and its proposal cover only the
data-modeling role's per-role fan-out unit (step 2+), so the gate
extension is left to step 1.
