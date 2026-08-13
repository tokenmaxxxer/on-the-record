---
subject: issue-1199
role: data-engineering
kind: record
loop_state: landed
---

# Record: data-engineering tool-landscape fold-in (issue-1199)

Pipeline design: N/A, this record documents a documentation-only
fold-in of surveyed design moves into playbook rule text; no new
pipeline source/transform/sink was built.

Data-quality check list: N/A, this record documents adding
decision-rule text (not a `model_name`/`column_name`/`data_type`/
`constraint` schema) to playbook/data-quality.md; no dataset schema
was defined in this unit's own work.

Failure-handling plan: N/A, this record documents a documentation-only
fold-in; no new pipeline failure mode requiring its own recovery plan
was introduced.

## What was done
Executed the phase-2 fold-in approved by the `APPROVE
issue-1199/data-engineering` comment on this issue (single-account
mode; canonical: `gh issue view 1199 --comments`, read this session —
the comment body is exactly `APPROVE issue-1199/data-engineering`).
Worked directly in the separate rulebook repo
(tokenmaxxxer/data-engineering-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook), on a
fresh branch `issue-1199/data-engineering` cut from `origin/main`
(canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook
log --oneline main..issue-1199/data-engineering`, read this session —
one commit, `48cf6e2`).

- Surveyed five tools across five distinct data-engineering problem
  categories not already covered by the rulebook's GX-heavy
  data-quality.md program (issue #1174, separate): orchestration
  (Apache Airflow), transformation (dbt-core), data contracts/catalog
  (DataHub), CDC/ingestion (Debezium), data observability (Monte
  Carlo). Adoption evidence collected via real WebSearch/WebFetch this
  session (star counts fetched directly from each project's GitHub
  page, Monte Carlo's named-company case-study data fetched directly
  from its own blog); full trail in
  `docs/issue-1199/reports/data-engineering/scout-brief.md`.
- Per this issue's binding 2026-08-13 requirement amendments
  ("apply-not-reference" and "native application, no tool-attribution
  catalogs"): added no "Tool learnings" section and no tool names to
  the rulebook's operating content. Instead added five native decision
  rules directly into the three playbook files the proposal named as
  upgrade targets, each rule phrased as the role's own judgment with
  an evidentiary source citation, matching the existing
  `condition → choice → source` rule format those files already use
  for citing Fivetran/Airbyte/DAMA-DMBOK/*Nature* as rationale
  sources:
  - `playbook/pipeline-design.md`: rule 12 (task-graph orchestration,
    distinct from the existing idempotency rules), rule 13
    (model-reference/test discipline for chained SQL transforms), rule
    14 (centralized dataset ownership/lineage lookup, distinct from
    naming an owner once).
  - `playbook/failure-handling.md`: rule 13 (source read-load as its
    own failure-mode design axis, via log-based capture instead of
    polling).
  - `playbook/data-quality.md`: rule 12 (anomaly-detection monitoring
    as a second detection mode alongside authored threshold checks —
    a genuinely new detection-philosophy angle, not a rework of the
    existing GX-anchored rules).
- Canonical diff (`git -C /home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook
  diff main...issue-1199/data-engineering --stat`, run this session):
  ```
   playbook/data-quality.md     | 11 +++++++++++
   playbook/failure-handling.md | 12 ++++++++++++
   playbook/pipeline-design.md  | 33 +++++++++++++++++++++++++++++++++
   3 files changed, 56 insertions(+)
  ```
  All three files show insertions only (canonical:
  `git -C /home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook
  diff main...issue-1199/data-engineering | grep -E '^-[^-]'`, run this
  session — empty output, no deletions).
- No gate `.py`/`.sh` file or `tests/` directory touched (canonical:
  the `--stat` output above lists exactly the three playbook files).
  No `rule_count_floor` changed in any touched file's frontmatter —
  each file's existing rule count already exceeded its floor of 10
  before this addition.
- Committed in the rulebook repo (commit `48cf6e239fde28b602bd9cbb8c1f04f1b5e69f11`,
  subject: issue-1199; canonical: `git -C
  /home/jwjung/tokenmaxxxer/rulebooks/data-engineering-rulebook log -1
  --stat`, run this session), pushed to
  `origin/issue-1199/data-engineering`.

## Why
Per issue-1199 (northpole req#1/req#5): the data-engineering role's
rulebook encoded pipeline-design, data-quality, and failure-handling
judgment but had not folded in learnings from the wider tool ecosystem
data engineers actually use beyond the Great Expectations program
issue #1174 already landed. The five rules close gaps the phase-1
scout brief identified: no rule distinguished task-graph orchestration
from idempotency; no rule named model-reference/test discipline for
chained transforms; no rule named centralized lineage lookup as
distinct from naming an owner once; no rule named source-side
read-load as a failure-mode design axis; and no rule named
anomaly-detection monitoring as a detection mode distinct from
authored thresholds.

## Upstream basis
docs/issue-1199/proposals/2026-08-13-data-engineering-tool-landscape.md

## What did not work
None.

## Open findings
None.

amendments-reconciled: issuecomment-5277549292 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for a different, unnumbered candidate PR (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277549292`, read
this session — the body names no branch, and the surrounding thread's
adjacent verdicts in this session's read of `gh issue view 1199
--comments` are for branch `issue-1199/technical-writing`); it does
not name or reference this data-engineering unit's work, so no content
amendment to this record is warranted — same reconciliation class
already logged for the brand-design unit's `docs/issue-1199/reports/
brand-design.md` (issuecomment-5276738377).

amendments-reconciled: issuecomment-5277572136 ("Judgment opened: PR
#? — candidate decision on branch `issue-1199/data-engineering` (4
path(s) changed) entered delegated-judgment evaluation.") is an
automated watcher notification that this unit's own push was picked up
for delegated-judgment evaluation (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277572136`, read
this session); it states a process transition, not a content objection
or amendment, so no content change to this record is warranted beyond
this acknowledgment.

amendments-reconciled: issuecomment-5277582498 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for a different, unnumbered candidate PR (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277582498`, read
this session — the body names no branch); it does not name or
reference this data-engineering unit's work, so no content amendment
to this record is warranted — same reconciliation class already logged
above for issuecomment-5277549292.

amendments-reconciled: issuecomment-5277590212 ("Verdict: PR #? →
escalate (depth or impact axis did not clear)") is a delegated-judgment
verdict for a different, unnumbered candidate PR (canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277590212`, read
this session — the body names no branch); it does not name or
reference this data-engineering unit's work, so no content amendment
to this record is warranted — same reconciliation class already logged
above. This is the pr-preflight comment-race pattern (issue #1174
retrospective, commit 005e2c6): a reconciliation commit here can itself
trigger a fresh watcher comment while `gh pr create` is still pending.
