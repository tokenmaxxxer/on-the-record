---
subject: issue-1199
role: data-modeling
kind: record
loop_state: landed
---

# Record: data-modeling tool-landscape fold-in (issue-1199)

table_name: n/a
table_type: n/a
grain: one row per methodology rule added to README.md (three rules)
canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/data-modeling-rulebook show bad8995d88406d81d6c33a20848b27cb074a9943 --stat`, run this session — confirms the three-rule diff landed on branch issue-1199/data-modeling.
verdict: pass

## Layers
n/a, justified skip: this deliverable edits methodology prose, not a
schema, so no conceptual/logical/physical model artifacts apply.

## Data dictionary
n/a — no table/column set introduced; the naming-floor rule constrains
column names for future Data Vault deliverables, not this one.

## Migration plan
n/a — no migration.

## Rollback
n/a — revert the single rulebook-repo commit
(bad8995d88406d81d6c33a20848b27cb074a9943) to roll back.

## What was done
Executed the phase-2 fold-in approved by the `APPROVE issue-1199/data-modeling`
comment on this issue (single-account mode; canonical: `gh issue view
1199 --comments`, read this session — trailing comment body is exactly
`APPROVE issue-1199/data-modeling`). Scouted the tool landscape first
(docs/issue-1199/reports/data-modeling/scout-brief.md, docs/issue-1199/reports/data-modeling/survey.md)
per the adoption-evidence method: dbt-core (13,633 stars), great_expectations
(11,709 stars), soda-core (2,410 stars), AutomateDV/dbtvault (595 stars,
official dbt Hub package) — canonical: `gh api repos/dbt-labs/dbt-core
repos/great-expectations/great_expectations repos/sodadata/soda-core
repos/Datavault-UK/automate-dv --jq '{stars:.stargazers_count,forks:.forks_count}'`,
run this session — plus dbdiagram.io/SchemaSpy via three independent
2026 ERD-tool comparison roundups (talkingschema.ai, liambx.com,
holistics.io), fetched via WebSearch this session.

Worked directly in the separate rulebook repo
(tokenmaxxxer/data-modeling-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/data-modeling-rulebook), on branch
issue-1199/data-modeling:

- Added three additive rules to the rulebook repo's `README.md`
  Methodology section (this rulebook keeps its methodology directly in
  README.md, no separate handbook file exists): (1) every phase-2
  deliverable must state grain/constraints as at least one
  machine-checkable assertion, not only normalization-rationale prose;
  (2) any ERD/diagram artifact must be reproducible from its source
  (generated from DDL/migration, or a diffable text format such as
  DBML); (3) the Data Vault row's hub/link/satellite columns follow a
  fixed naming floor (`<entity>_hk`, `<entity>_hd`, `load_date` +
  `record_source`).
- No tool names, "learned from X" attribution, or tool-catalog section
  added to the public rulebook — each rule is stated as the role's own
  methodology norm; the evidence trail lives only in this record and
  the two phase-1 docs above.
- No existing README text deleted; no gate logic touched.
- Committed in the rulebook repo (commit
  bad8995d88406d81d6c33a20848b27cb074a9943, subject: issue-1199;
  canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/data-modeling-rulebook
  log -1 --format=%H`, read this session), pushed to
  origin/issue-1199/data-modeling.

## Why
Per issue-1199 (northpole req#1/req#5): the data-modeling role's
rulebook had encoded methodology but not learnings from the tool
ecosystems data modelers actually use. The three rules close the gaps
the phase-1 survey identified — no machine-checkable assertion
requirement, no reproducible-diagram requirement, no Data-Vault
column-naming floor — none of which the prior methodology text asked
for.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-data-modeling-tool-landscape.md

## Open findings
None.

## amendments-reconciled
issuecomment-5277534993 ("Verdict: PR #? → escalate (depth or impact
axis did not clear)") is a delegated-judgment verdict for a different,
unnumbered candidate PR on branch `issue-1199/capacity-planning`
(canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"
--paginate --jq 'sort_by(.id) | .[-6:]'`, run this session — the
"Judgment opened" comment immediately preceding it names branch
`issue-1199/capacity-planning`) — it does not name or reference this
data-modeling unit's record or its rulebook-repo counterpart
(data-modeling-rulebook, branch issue-1199/data-modeling), so no
content amendment to this record is warranted.

canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"
--paginate --jq 'sort_by(.id) | .[-4:]'`, run this session.
issuecomment-5277548038 is a watcher session-end notice for the
capacity-planning role's own unit. issuecomment-5277549120 is a
judgment-loop notice naming branch `issue-1199/conformance-review`.
issuecomment-5277549292 is that same judgment loop's escalate verdict.
None of the three name or reference this data-modeling unit; this
issue is under continuous concurrent comment traffic from sibling role
sessions (the known post-approval pr-preflight comment-race pattern),
so this record reconciles the tail as observed at write time rather
than retrying PR-create indefinitely against a moving target.

canonical: `gh api "repos/tokenmaxxxer/on-the-record/issues/1199/comments?per_page=100"
--paginate --jq 'sort_by(.id) | .[-1]'`, run this session (id
5277555847, another escalate-verdict judgment-loop notice for a
different, unnamed branch — not data-modeling). Per the identical
precedent already logged for this issue's own comment-race pattern
(docs/issue-1174/reports/issue-retrospective/deviation-log.md, commit
005e2c6), this session stops chasing individual new comment ids after
this reconciliation round.
