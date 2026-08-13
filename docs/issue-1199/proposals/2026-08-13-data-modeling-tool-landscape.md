---
status: proposed
files:
  - docs/issue-1199/reports/data-modeling/scout-brief.md
  - docs/issue-1199/reports/data-modeling/survey.md
  - docs/issue-1199/reports/data-modeling.md
---

# Proposal: data-modeling tool-landscape fold-in (issue-1199)

## Intent
For the `data-modeling` role, survey the tool ecosystem data modelers
actually use, analyze what each tool solves and how, and fold the
distilled design moves into the role's own rulebook methodology — not
as a tool catalog, but as native upgrades to the existing methodology
table, deliverable checklist, and Data-Vault deviation row. See
`docs/issue-1199/reports/data-modeling/survey.md` for the current-state
survey this proposal is built on.

## Layers
Per the survey's Layers section: the rulebook's methodology already
requires conceptual/logical/physical layering per deliverable. This
proposal upgrades that same layering requirement's constraint-
expression rule (adding the assertion requirement below), not the
layering requirement itself.

## Methodology fit
Per the survey's Methodology-fit section: this is a cross-cutting
fold-in touching the methodology table across all three rows
(Inmon/3NF, Kimball dimensional, Data Vault) plus the Data Vault row's
deviation column specifically — no single row applies alone.

## Grain
n/a — this proposal is not a fact-table deliverable. Grain is: one row
per methodology-table upgrade in the rulebook's own README.md (three
upgrade rows added, matching the three items under "What will be
done").

## Normalization target
n/a — this proposal touches methodology text (README.md), not a schema
deliverable, so no 1NF/2NF/3NF/BCNF target applies; the Inmon/3NF row
of the methodology table is one of the three rows this fold-in edits,
but the edit itself is prose, not a normalized schema.

## Hub/satellite/link
The Data Vault upgrade below names a naming-convention floor for
satellite hash-diff columns and hub/link hash-key columns specifically
— it does not add or remove any hub, link, or satellite table, only
constrains how their key/audit columns are named.

## Rationale
Per the survey's gap #3: hash-key/hash-diff/load-metadata columns
currently have no naming floor, so satellite/link artifacts drift
across deliverables and lose the auditability and schema-drift
resilience that Data Vault's audit-trail design is meant to guarantee.
Standardizing the naming floor once at the methodology level restores
that audit-trail guarantee across deliverables.

## Constraints
- Adoption evidence only (stars/downloads/multi-source), no pretrained-
  recall tool lists — see `docs/issue-1199/reports/data-modeling/scout-brief.md`.
- Bounded fold-in: distilled design moves and checklist items, not a
  tool catalog, and no "learned from tool X" attribution inside the
  public rulebook.
- No verbatim copying from any surveyed tool's docs.
- Every named upgrade target file must actually be edited.
- Work happens in the separate `tokenmaxxxer/data-modeling-rulebook`
  repo; this repo (on-the-record) carries only the phase-2 record.

## What will be done
Edit `tokenmaxxxer/data-modeling-rulebook`'s `README.md` Methodology
section (the rulebook's own methodology home — this repo has no
separate `docs/handbooks/*/methodology.md` file) to add:
1. A requirement that every phase-2 deliverable state its grain/
   constraints as at least one machine-checkable assertion (not only
   normalization-rationale prose).
2. A requirement that any ERD/diagram artifact be either generated from
   the DDL/migration it accompanies or committed in a diffable text
   format alongside it.
3. A naming-convention floor for the Data Vault deviation row's
   hash-key/hash-diff/load-metadata columns.

Then commit, push, and open a PR in that repo on branch
`issue-1199/data-modeling`, and write this repo's phase-2 record at
`docs/issue-1199/reports/data-modeling.md` citing that PR/commit.

## Alternatives considered
See the survey's Alternatives-considered section: a separate
`tool-learnings/` doc was considered and rejected in favor of folding
directly into README.md, this rulebook's single methodology source.

## Open questions
See the survey's Open-questions section: the issue's shape-gate
extension (Acceptance section) is left to the issue's step-1
implementation unit, not this per-role unit.

## Out of scope
dbt's DAG/lineage tooling, Great Expectations' report generation, and
any pipeline/orchestration concern — outside this role's `write_scope`
(migrations only).

## How you will know it worked
The rulebook PR's diff shows the three README.md edits landed verbatim
in the methodology table/checklist; this repo's phase-2 record cites
the rulebook-repo commit sha and PR URL as canonical sources.
