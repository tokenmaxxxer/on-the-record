---
subject: issue-1199
role: data-modeling
kind: scout-brief
---

# Scout brief: data-modeling tool landscape (issue-1199)

Mode: parallel WebSearch fan-out (4 angles), 1 sweep stage + 1 star-count
verification stage via `gh api repos/<org>/<repo>` (adoption-evidence
method per tech-feasibility).
canonical: `gh api repos/dbt-labs/dbt-core repos/great-expectations/great_expectations repos/sodadata/soda-core repos/Datavault-UK/automate-dv --jq stargazers_count/forks_count`, run this session (see counts below). Saturation: the
verification stage's star counts matched the sweep's ranking with no
disagreement, so a third round was not run.

## Surveyed tools (adoption evidence, live-fetched)

- **dbt-core** (dbt-labs/dbt-core): 13,633 stars / 2,502 forks
  (canonical: `gh api repos/dbt-labs/dbt-core --jq '{stars:.stargazers_count,forks:.forks_count}'`,
  run this session). Problem: analytics transformation SQL sprawls with
  no test/doc/lineage discipline. How: models are version-controlled
  SELECT statements; a `schema.yml` sits beside each model declaring
  column-level tests (`not_null`, `unique`, `relationships`) and
  descriptions, and `dbt docs generate` derives a lineage graph from
  `ref()` calls instead of a hand-drawn diagram. Learning: co-locate the
  *test/assertion* with the *model definition*, not in a separate QA
  doc — a model without its own tests is structurally incomplete.
- **great_expectations** (great-expectations/great_expectations): 11,709
  stars / 1,797 forks (canonical: `gh api repos/great-expectations/great_expectations --jq '{stars:.stargazers_count,forks:.forks_count}'`,
  run this session). Problem: "does this data match the model" is
  usually checked ad hoc, post-hoc, or never. How: expectations are
  declared per-column/per-table as machine-checkable assertions
  (`expect_column_values_to_be_between`, `expect_table_row_count_to_equal`)
  that run as a gate, and violations produce a structured "data docs"
  report instead of a bare yes/no line. Learning: a data model's
  grain and constraints should be expressed as machine-checkable
  assertions, not only prose in a data dictionary.
- **soda-core** (sodadata/soda-core): 2,410 stars / 283 forks (canonical:
  `gh api repos/sodadata/soda-core --jq '{stars:.stargazers_count,forks:.forks_count}'`,
  run this session). Problem: same space as Great Expectations but
  optimized for lightweight, YAML-declared checks close to the
  warehouse rather than a Python framework. How: a single `checks.yml`
  per dataset, human-writable, checked into the same repo as the model.
  Learning: checks-as-code belongs in the same PR/commit as the schema
  change it constrains, not a downstream ops task.
- **AutomateDV / dbtvault** (Datavault-UK/automate-dv): 595 stars / 157
  forks (canonical: `gh api repos/Datavault-UK/automate-dv --jq '{stars:.stargazers_count,forks:.forks_count}'`,
  run this session), official dbt Hub package, dbt Labs maintains an
  official demo project against it (dbt-labs/dbt_datavault_demo, per
  https://github.com/dbt-labs/dbt_datavault_demo, fetched this session).
  Problem: Data Vault hub/link/satellite hand-loading is repetitive and
  error-prone — every hub load needs the identical hash-key/hash-diff/
  audit-column boilerplate. How: macros take a YAML-declared
  source-to-target mapping (business keys, descriptive attributes,
  source) and generate the load SQL; hash-key and hash-diff column
  naming is a fixed, non-negotiable convention baked into the macro, not
  left to author discretion. Learning: for the Data-Vault deviation row
  specifically, standardize the hash-key/hash-diff/load-metadata column
  naming convention once at the methodology level so every satellite/
  link in a deliverable is structurally comparable, instead of
  re-deriving naming per artifact.
- **dbdiagram.io** (SaaS, no public star count; ranked among the top
  ERD tools in 3 independent 2026 comparison roundups — per
  https://talkingschema.ai/blog/best-erd-database-design-tools-2026,
  https://liambx.com/blog/er-diagram-tool-trends-2025,
  https://www.holistics.io/blog/top-5-free-database-diagram-design-tools/,
  fetched this session) vs. **SchemaSpy** (metadata-driven, live-DB
  introspection, per the same sources). Problem: ERDs drift from the
  schema they document because they're drawn by hand in a GUI tool
  disconnected from source control. How: dbdiagram.io's DBML is
  diagram-as-code — the ERD is a text file reviewable in a diff,
  versioned beside the migration that changes it; SchemaSpy instead
  regenerates the diagram from live metadata so it can never drift.
  Learning: an ERD artifact should be either (a) generated from the
  DDL/migration it accompanies, or (b) committed as a diffable text
  format alongside it — never a standalone image with no reproducible
  source.

## Gap line (rulebook's current state vs. the surveyed field)

canonical: `README.md` (this rulebook repo), Methodology section, read
this session.

The rulebook's README already requires conceptual/logical/physical
layering per deliverable and a `verdict` field on each record, matching
the surveyed tools' shared stance that checks are structural, not
optional, at the deliverable-shape level.

It does not yet require: (1) that a deliverable's constraints be stated
as machine-checkable assertions — the methodology table only asks for
"normalization rationale" prose; (2) that an ERD/diagram artifact be
reproducible from its source — a deliverable could ship a static image
with no diffable source; (3) a naming-convention floor for the Data
Vault row's hash-key/hash-diff/load-metadata columns.

## Adopt / skip

Adopt: (1) assertions-with-the-model requirement, (2) diagram-must-be-
reproducible-from-source requirement, (3) Data-Vault column-naming
floor. Skip: dbt's full DAG/lineage-graph tooling and Great
Expectations' "data docs" report generation — those are execution-time
tooling outside this role's `write_scope` (migrations only, no
pipeline/orchestration per README.md's role summary, read this
session); adopting the underlying discipline (assertions belong with
the model) captures the design move without pulling in out-of-scope
tooling.

Sources:
- https://github.com/dbt-labs/dbt-core
- https://github.com/great-expectations/great_expectations
- https://github.com/sodadata/soda-core
- https://github.com/Datavault-UK/automate-dv
- https://github.com/dbt-labs/dbt_datavault_demo
- https://hub.getdbt.com/Datavault-UK/automate_dv/latest/
- https://talkingschema.ai/blog/best-erd-database-design-tools-2026
- https://liambx.com/blog/er-diagram-tool-trends-2025
- https://www.holistics.io/blog/top-5-free-database-diagram-design-tools/
