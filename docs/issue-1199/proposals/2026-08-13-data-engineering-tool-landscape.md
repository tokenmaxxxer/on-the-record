---
subject: issue-1199
role: data-engineering
loop_state: scope-proposed
status: proposed
files:
  - playbook/pipeline-design.md
  - playbook/failure-handling.md
  - playbook/data-quality.md
  - docs/issue-1199/reports/data-engineering.md
---

# Proposal: fold data-engineering's surveyed tool landscape into the rulebook (issue-1199)

All rulebook-repo file paths below live in the separate repo
("tokenmaxxxer/data-engineering-rulebook", mounted at
/home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook — see
docs/issue-1199/reports/data-engineering/survey.md), not in this
working tree; phase 2 branches and commits there directly.

## Phase-1 sub-fields (per methodology.md)

Pipeline design: N/A, this proposal is a documentation-only fold-in of
surveyed design moves into playbook rule text — no new pipeline
source/transform/sink is being built.

Data-quality check list: N/A, this proposal adds decision-rule text
(not a `model_name`/`column_name`/`data_type`/`constraint` schema) to
playbook/data-quality.md; no dataset schema is being defined here.

Failure-handling plan: N/A, this proposal is a documentation-only
fold-in; no new pipeline failure mode is being introduced that needs
its own recovery plan.

## Request
Per issue-1199 (northpole req#1/req#5) and the binding requirement
amendments posted on this issue (2026-08-13, "apply-not-reference" and
"native application, no tool-attribution catalogs"): survey the actual
data-engineering tool landscape across categories the rulebook's
existing GX-heavy data-quality.md program (issue #1174) does not
already cover, then fold the resulting design moves into the rulebook
as native rules the role would state as its own judgment — not as a
tool catalog, and not merely referencing an upgrade target without
editing it.

## Constraints
- Adoption evidence via the tech-feasibility method (GitHub stars,
  vendor case-study evidence, multi-source mentions), every claim
  citing a URL actually fetched this session — see scout-brief's
  Sources list.
- The rulebook repo gets no "Tool learnings" section, no tool names,
  and no "source: <tool repo>" catalog framing in its operating
  content — per the 2026-08-13 amendment. The research/evidence trail
  (which tools, what evidence, which insight) stays only in this
  report's scout-brief/survey; the rulebook absorbs the *insight*,
  phrased natively, matching the existing playbook convention of
  citing an evidentiary source for a design-move rationale (as
  pipeline-design.md and failure-handling.md already do for Fivetran/
  Airbyte/DAMA-DMBOK/Nature) — not as "tool X has feature Y so we
  adopt Y."
- Every named upgrade target is edited in this same delivery — no
  upgrade is only pointed at.
- Never delete existing rulebook content; do not restructure the
  numbered `condition → choice → source` rule format; do not touch
  `rule_count_floor` unless a counted rule is genuinely added (then
  increment correctly — not required here, since each file's existing
  count already exceeds its floor).
- Do not redo or restructure data-quality.md's GX-anchored program
  (issue #1174, separate); the one data-quality.md addition here is a
  genuinely new detection-philosophy angle (anomaly monitoring vs.
  authored thresholds), not a GX rework.
- Do not adopt, install, or depend on any of the five surveyed tools —
  design-move borrowing only, per this role's own methodology.md
  prohibition on new tooling dependencies.

## What will be done
Five tools, five distinct problem categories, each becoming one native
rule in a playbook file (not a catalog entry):

1. **Orchestration** (apache/airflow; 46.5k GitHub stars, read this
   session at github.com/apache/airflow; State of Airflow 2026 survey
   — astronomer.io/blog/state-of-airflow-2026/). Problem: a pipeline
   with real step-to-step dependencies encoded as a flat script or cron
   sequence cannot retry or backfill one failed step without rerunning
   everything upstream. How: express dependencies as an explicit task
   graph with per-task retry/backfill. Upgrades: playbook/
   pipeline-design.md — adds a new rule distinct from the existing
   idempotency rules (items 4-7), naming task-graph orchestration as
   its own design axis.

2. **Transformation** (dbt-labs/dbt-core; 13.6k GitHub stars, read
   this session at github.com/dbt-labs/dbt-core). Problem: chained SQL
   transforms with hard-coded table references and no attached tests
   make the transform DAG's shape and correctness verifiable only by
   tribal knowledge of execution order. How: named model references
   plus a machine-checkable test attached to each model's output.
   Upgrades: playbook/pipeline-design.md — adds a rule companion to the
   existing ELT choice (item 1), naming model-reference/test discipline
   for warehouse-side SQL transforms.

3. **Data contracts/catalog** (datahub-project/datahub; 12.5k GitHub
   stars and 3,000+ organizations listed as production users, read
   this session at github.com/datahub-project/datahub, including
   named adopters Netflix, Visa, Etsy, Block). Problem: dataset
   ownership and lineage known only inside a pipeline's code or a
   single person's head cannot be looked up by an unfamiliar team.
   How: publish owner/schema/lineage to a queryable central location.
   Upgrades: playbook/pipeline-design.md — adds a rule companion to the
   existing owner/steward-naming rule (item 8), naming centralized
   lookup as distinct from naming an owner once.

4. **CDC/ingestion** (debezium/debezium; 13.0k GitHub stars, read this
   session at github.com/debezium/debezium). Problem: repeated
   full-table polling for change detection degrades the source
   system's own read capacity — a failure precursor the pipeline's own
   retry/DLQ logic cannot fix because the damage happens upstream.
   How: capture changes via the source's transaction/commit log
   instead of polling. Upgrades: playbook/failure-handling.md — adds a
   rule naming source read-load as its own failure-mode design axis,
   distinct from the existing transient/permanent retry classification
   (items 1-3).

5. **Data observability** (Monte Carlo; named case-study evidence read
   this session at montecarlo.ai/blog-data-observability-use-cases/ —
   SeatGeek: incidents 10/month to 0 in one quarter; Choozle: 88%
   reduction in data downtime; Contentsquare: 17% faster incident
   detection). Problem: authored threshold checks only catch failure
   modes someone anticipated when writing them; a schema/volume/
   freshness shift nobody wrote a rule for passes silently. How: run
   an unsupervised anomaly monitor alongside authored checks, not
   instead of them. Upgrades: playbook/data-quality.md — adds one rule
   naming anomaly-detection as a second, distinct detection mode next
   to the existing per-check verdict rule (item 9); not a GX rework.

docs/issue-1199/reports/data-engineering.md is phase-2 output, written
only after approval opens phase 2, per contract v3 s19.

## Out of scope
- Any restructuring of data-quality.md's GX-anchored rule set
  (issue #1174 program).
- Mechanical gate changes (any `*-gate.py`/`*-gate.sh`) or
  `tests/` — issue-1199's acceptance criterion 1 names a possible
  cross-cutting gate; out of scope for a single role's fold-in,
  tracked at the issue level.
- Installing or depending on Airflow, dbt, DataHub, Debezium, or
  Monte Carlo — the fold-in borrows the design move only.
- A separate "Tool learnings" section in methodology.md — superseded
  by the 2026-08-13 native-application amendment; the evidence trail
  lives only in this report's companion scout-brief/survey.

## How you'll know it worked
Phase 2 diff, reviewed against this proposal, adds exactly five native
rules (one per tool above) split across pipeline-design.md (three),
failure-handling.md (one), and data-quality.md (one), each phrased in
the role's own voice with a real evidentiary source citation matching
the existing rule format, with no deletion of existing rulebook text,
no tool-catalog section, and no restructuring of the numbered-rule
format.
