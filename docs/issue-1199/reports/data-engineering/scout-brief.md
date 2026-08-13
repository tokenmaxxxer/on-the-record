---
subject: issue-1199
role: data-engineering
kind: scout-brief
loop_state: scouted
---

# Scout brief: data-engineering tool landscape (issue-1199)

Mode: parallel WebSearch/WebFetch, one sweep round across five distinct
problem categories (orchestration, transformation, catalog/contracts,
CDC/ingestion, observability), each verified against the tool's own
GitHub repo or a vendor case-study page fetched directly.

## Category must-bes (what any tool in this category has to do)
- **Orchestration**: express task dependencies as a graph (not a flat
  cron list), retry/backfill individual nodes without re-running the
  whole pipeline.
- **Transformation**: version-controlled, testable SQL/model layer with
  an explicit dependency graph between models (not ad hoc scripts).
- **Catalog/contracts**: a queryable inventory of what datasets exist,
  who owns them, and lineage between them — not tribal knowledge.
- **CDC/ingestion**: capture row-level source changes without adding
  read load to the source system via repeated full-table polling.
- **Observability**: detect anomalies (freshness, volume, schema,
  distribution) the team did not think to write an explicit check for.

## Chosen performance axes
1. Dependency-graph fidelity vs. flat/implicit ordering (Airflow, dbt).
2. Source-of-truth centralization vs. duplicated/tribal metadata
   (DataHub).
3. Read-load impact on the source system (Debezium's log-based CDC vs.
   polling).
4. Detection coverage for *unknown* failure modes vs. only pre-authored
   checks (Monte Carlo).

## Adopt / skip patterns
canonical: playbook/pipeline-design.md, playbook/data-quality.md,
playbook/failure-handling.md, docs/handbooks/data-engineering/
methodology.md (all in the separate rulebook repo, read this session).
- Adopt: the *design move* each tool encodes — dependency-graph task
  orchestration; a testable, ref()-based transform DAG; centralized
  owner/lineage metadata instead of implicit tribal knowledge;
  log-based CDC over source-polling for read-load reasons; anomaly
  monitors as a distinct failure-detection mode alongside authored
  threshold checks (the existing data-quality.md is entirely
  authored-threshold rules — no rule currently names "check for
  the failure mode nobody wrote a rule for").
- Skip: adopting any of the five tools themselves as a dependency —
  per this role's methodology.md prohibition ("do not adopt new
  tooling ... as a dependency — cite as source of shape only") and per
  this task's constraint against installing surveyed tools.

## Gap line
pipeline-design.md and failure-handling.md already cite Fivetran/
Airbyte/DAMA-DMBOK design moves (ELT vs ETL, idempotency, ownership).
data-quality.md is GX-heavy (issue #1174 program, out of scope here).
No existing rule in any of the three playbook files addresses:
task-dependency-graph orchestration as distinct from idempotency;
model-level transform testing/lineage; centralized dataset
ownership/lineage lookup as distinct from the ownership-naming rule
already present; or anomaly-detection-class monitoring as distinct
from authored-threshold checks. Those four are this fold-in's targets.

## Sources
- https://github.com/apache/airflow
- https://www.astronomer.io/blog/state-of-airflow-2026/
- https://github.com/dbt-labs/dbt-core
- https://github.com/datahub-project/datahub
- https://github.com/debezium/debezium
- https://montecarlo.ai/blog-data-observability-use-cases/
