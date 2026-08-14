---
subject: issue-1199
role: data-engineering
kind: survey
loop_state: surveyed
---

# Current-state survey: data-engineering rulebook (issue-1199)

canonical: /home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook
(read this session — README.md, docs/handbooks/data-engineering/
methodology.md, playbook/pipeline-design.md, playbook/data-quality.md,
playbook/failure-handling.md), all outside this working tree in the
separate rulebook repo "tokenmaxxxer/data-engineering-rulebook".

## Where the rulebook lives
Mounted locally at /home/jwjung/tokenmaxxxer/rulebooks/
data-engineering-rulebook. Prior issue-1174 landed an
operational-playbook program there on branch
issue-1174/operational-playbook (GX-heavy data-quality.md content);
issue-19/issue-22/issue-13 landed the methodology handbook shape,
loop_state vocabulary, and gate-house standard. This fold-in follows
the same per-issue docs/issue-<n>/{proposals,reports} layout and
"Subject: issue-<n>" commit-trailer convention.

## Existing structure
Three independent top-level gate plugins, one per PRODUCES sub-field
(`pipeline-design-gate`, `data-quality-gate`, `failure-handling-gate`),
each with its own mechanical `PreToolUse` hook; the methodology
handbook is the judgment layer above the gates. Three playbook files
under `playbook/` (`pipeline-design.md`, `data-quality.md`,
`failure-handling.md`) carry numbered decision rules in a
`condition → choice → source` format, each tagged `addition` or
`**REMOVAL**`, with a per-file `rule_count_floor` in frontmatter.

## Existing rule coverage (read this session)
- **pipeline-design.md** (11 rules, floor 10): ETL-vs-ELT choice,
  idempotency patterns (overwrite-partition, upsert), exactly-once
  effective semantics, DAMA-DMBOK owner/steward naming and
  change-control routing, two REMOVAL rules on unused hops and
  duplicated pre-load validation. No rule addresses task-dependency-
  graph orchestration (retry/backfill a single node without rerunning
  the whole pipeline) as distinct from idempotency, nor centralized
  lineage/ownership lookup as distinct from naming an owner once.
- **data-quality.md** (11 rules, floor 10): Great Expectations-anchored
  dimension checks (uniqueness, completeness, accuracy, freshness,
  volume), data-contract formalization at team boundaries,
  multi-column business-rule checks, fixed-vs-dynamic threshold
  sequencing, per-check verdict recording, two REMOVAL rules on stale
  and redundant checks — this is issue #1174's program; not touched by
  this fold-in per the task's scope boundary. Every rule here is an
  *authored* threshold check; none names anomaly-detection-class
  monitoring (flagging a deviation nobody wrote an explicit rule for)
  as a distinct failure-detection mode.
- **failure-handling.md** (12 rules, floor 10): transient/permanent
  failure classification, retry-with-backoff vs. DLQ routing, DLQ
  volume/age alerting, replay-success-rate diagnosis, impact-scaled
  RTOs, rollback-via-idempotent-rerun, DLQ overflow partitioning, two
  REMOVAL rules on dead runbook steps and redundant retry tiers. No
  rule addresses source-side read-load impact of the ingestion
  mechanism itself (polling vs. log-based capture) as a failure-mode
  design axis.

## Where the fold-in fits
canonical: docs/handbooks/data-engineering/methodology.md's
"Prohibitions: do not adopt new tooling ... as a dependency — cite as
source of shape only" line, and its "Mechanical enforcement" section
naming the three gate plugins as independent of each other's internals
(read this session). The tool-learnings fold-in therefore: (1) lives in
methodology.md as a bounded, evidence-citing section for the
research trail, and (2) applies its named upgrades as native rules
directly in pipeline-design.md and failure-handling.md (task-graph
orchestration; centralized lineage lookup; source read-load as a
design axis) plus one native rule in data-quality.md limited to the
anomaly-detection-vs-authored-check distinction — a genuinely new
angle the existing GX-anchored rule set does not cover, not a
restructuring of it.

## No prior tool-landscape section
No "Tool learnings" heading and no adoption-evidence citation to
Airflow, dbt, DataHub, Debezium, or Monte Carlo anywhere in the
methodology handbook or the three playbook files (read this session) —
this fan-out unit adds the section and the native rules; it does not
revise an existing one.
