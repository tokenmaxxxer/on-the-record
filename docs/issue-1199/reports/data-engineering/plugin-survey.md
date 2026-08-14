---
subject: issue-1199
role: data-engineering
kind: survey
loop_state: surveyed
---

# Claude Code plugin/skill ecosystem survey: data-engineering (issue-1199, 2026-08-14 rework)

canonical: this file's own Sources list — every claim below traces to a
URL fetched (WebSearch/WebFetch) this session, per the 2026-08-14
amendment superseding the prior domain-tool-basis survey at
docs/issue-1199/reports/data-engineering/survey.md (that file surveyed
Airflow/dbt-core/DataHub/Debezium/Monte Carlo as general OSS/vendor
tools, not as Claude Code plugins — it does not satisfy the amended
acceptance and is left in place unmodified as the prior round's record,
superseded by this file for the plugin-ecosystem requirement).

## Sweep

Two WebSearch rounds this session: (1) "Claude Code plugin marketplace
data engineering dbt skill 2026" and "claude code plugin marketplace
list data pipeline skill github stars"; (2) a follow-up narrowing on
"schema migration"/"data parity"/"PII audit" skills, to check for a
second independently-evidenced candidate beyond dbt-focused skills.

Multiple marketplace directories surfaced (jeremylongshore/
claude-code-plugins-plus-skills, rohitg00/awesome-claude-code-toolkit,
alirezarezvani/claude-skills, claudemarketplaces.com) but none of their
individual skill entries yielded a verifiable, fetched star count or
independent corroborating source for a second data-engineering-scoped
skill (a "migration-auditor" skill surfaced by name only, with no
locatable star count this session — dropped rather than asserted
without evidence). One candidate cleared the adoption-evidence bar on
both counts (a real number and a second independent source).

## Selected: AltimateAI/data-engineering-skills

canonical: https://github.com/AltimateAI/data-engineering-skills (fetched
this session)

- **Adoption evidence**: star count fetched directly from the repo page
  this session:
  ```
  derived: WebFetch https://github.com/AltimateAI/data-engineering-skills
  -> "The repository has 118 stars on GitHub."
  ```
  Multi-source: also covered by Altimate's own blog post, and
  independently evaluated (a build-vs-baseline eval, not a vendor claim)
  by rmoff dot net (see Sources).
- **Problem it solves**: baseline Claude Code "knows dbt syntax
  perfectly well" but lacks project-specific context and workflow
  discipline — it writes a model without checking the project's own
  naming/layering convention first, and it confuses a successful
  compile with actual correctness (canonical: fetched this session,
  altimate.ai blog post in Sources).
- **How**: 10 skills (7 dbt-focused: creating/debugging/testing/
  documenting/migrating/refactoring/incremental models; 2 Snowflake:
  expensive-query finding, query optimization; 1 delegation) each
  encode a trigger condition plus a step-by-step workflow, not just
  facts — e.g. the model-creation skill: discover conventions (read
  existing sibling models) then write, then build, then verify actual
  output (a real build/show step, not compile-only) (canonical: fetched
  this session, github.com/AltimateAI/data-engineering-skills README in
  Sources).
- **Measured evidence**: ADE-bench (a 43-task suite of real-world dbt
  tasks) model-creation accuracy improved with skills applied versus
  baseline; overall task accuracy likewise improved with skills applied
  versus baseline (canonical: fetched this session, blog.altimate.ai
  post in Sources — exact percentage figures are the vendor's own
  reported eval numbers, not independently re-run in this session, so
  they are attributed as vendor-reported rather than restated as a
  session-verified count). Independently, a from-scratch eval by rmoff
  dot net (dual deterministic-check plus LLM-judge validation, across
  several scenarios and models) corroborates that dbt-agent skills give
  a measurable but marginal benefit over baseline, and — a load-bearing
  caveat this fold-in keeps — that no trial reached production-quality
  output unassisted; Claude remains "a companion tool" requiring
  engineer review (canonical: fetched this session, rmoff.net post in
  Sources).

## Learning → rulebook upgrade

Two design moves, each a genuinely new angle the existing playbook
rules (prior round's survey.md) did not name:

1. **Convention-discovery-before-write.** Existing pipeline-design.md
   rules 1-14 cover ELT/ETL choice, idempotency, ownership, task-graph
   orchestration, and model-reference/test discipline (rule 13, prior
   round) — none states that authoring/changing a model should start by
   reading existing sibling models for project-specific convention, as
   distinct from the general model-reference/test discipline rule 13
   already covers. Upgrades: playbook/pipeline-design.md, new rule 15.
2. **Verify actual output, not just compile/build success.** Existing
   data-quality.md rules 1-12 (GX-anchored authored checks, issue #1174;
   anomaly monitoring, prior round's rule 12) all describe *what* to
   check; none states the verification-methodology point that a
   pipeline step's own execution success (compiles, runs, no error) is
   not evidence of correctness — a distinct claim from any existing
   threshold-check rule. Upgrades: playbook/data-quality.md, new rule
   13.

Both applied directly to the rulebook this session (not merely pointed
at) — see the record file for the canonical commit/push evidence.

## Sources
- github.com/AltimateAI/data-engineering-skills
- blog.altimate.ai/teaching-claude-code-the-art-of-data-engineering-introducing-altimate-skills
- altimate.ai/blog/we-created-data-engineering-skills-for-claude-code
- rmoff.net (2026-03-13 post) "Evaluating Claude's dbt Skills: Building an Eval from Scratch"
