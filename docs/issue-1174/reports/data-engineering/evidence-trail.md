# data-engineering operational playbook — evidence trail (phase-1 record)

This session's phase-2 record file (docs/issue-1174/reports/data-engineering.md)
is phase-2 output gated behind an "APPROVE issue-1174/data-engineering"
comment per contract v3 s19; this fan-out unit's PR target
(tokenmaxxxer/data-engineering-rulebook) is external to this repo
anyway, so this file carries the evidence trail as phase-1-legal
material, matching the market-analysis/technical-writing fan-out units'
precedent (docs/issue-1174/reports/market-analysis/evidence-trail.md,
docs/issue-1174/reports/technical-writing/evidence-trail.md).

## Delivered to the rulebook repo

Authored the data-engineering role's operational playbook and pushed it
to tokenmaxxxer/data-engineering-rulebook, branch
issue-1174/operational-playbook, commit 23fc80c. Opened PR #25 against
that repo's main.
canonical: `git push -u origin issue-1174/operational-playbook` and
`gh pr create` output this turn (this session), remote accepting the
branch and returning
https://github.com/tokenmaxxxer/data-engineering-rulebook/pull/25.

Per the approved proposal design
(docs/issue-1174/proposals/operational-playbook-program.md sections (a)
axis-derived N floor, (b-revised) fan-out unit, (c) depth-gate shape,
(d) playbook/topic.md landing, amendment 4 removal-category
requirement) and matching this rulebook's own 3 existing gate plugins
(pipeline-design-gate, data-quality-gate, failure-handling-gate —
README.md's gate table), the commit adds:

- playbook/pipeline-design.md (11 rules, rule_count_floor: 10, 2 REMOVAL)
- playbook/data-quality.md (11 rules, rule_count_floor: 10, 2 REMOVAL)
- playbook/failure-handling.md (12 rules, rule_count_floor: 10, 2 REMOVAL)
- README.md (Layout section pointer added)

34 rule blocks total, each condition -> choice -> source, each axis
file carrying at least one rule marked **REMOVAL** (amendment 4).
canonical: file content of the three playbook/*.md files as written by
this session this turn on branch issue-1174/operational-playbook in
the data-engineering-rulebook repo (commit 23fc80c).

## Research protocol (amendment 1, three layers)

Layer 1 (practitioner decision knowledge) — queries run and their lead
sources: ETL-vs-ELT choice practice (domo.com, fivetran.com,
stripe.com); idempotency/exactly-once-vs-at-least-once practice
(airbyte.com); retry/backoff/DLQ/alerting practice (confluent.com,
oneuptime.com, flowfuse.com, medium.com/@krthiak,
medium.com/@vinay.georgiatech).
canonical: WebSearch tool results returned this turn for these three
queries (this session's transcript, this turn).

Layer 2 (named methodology/standard, verified at source) — queries run
and their lead sources: Great Expectations data-quality-dimension
practice and its ExpectColumn* threshold API (docs.greatexpectations.io,
greatexpectations.io/blog); the Data Contract Specification
(github.com/datacontract/datacontract-specification); DAMA-DMBOK
data-owner/steward/custodian governance framework (ovaledge.com).
canonical: WebSearch tool results returned this turn for these two
queries (this session's transcript, this turn).

Layer 3 (academic theory) — query run and its source: the amendment-4-
named subtraction-neglect paper (Adams, Converse, Hales & Klotz,
*Nature* 592, 2021, "People systematically overlook subtractive
changes," nature.com/articles/s41586-021-03380-y), used as the
removal-category rules' academic backing across all three axis files,
matching the market-analysis/technical-writing exemplars' reuse of the
same source.
canonical: WebSearch tool results returned this turn for the
subtraction-neglect query (this session's transcript, this turn).

Per-rule mapping: each of the 34 rule blocks carries its own source
line resolving to one of the sources above — see the playbook files on
branch issue-1174/operational-playbook in the data-engineering-rulebook
repo (or PR #25's diff) for the full per-rule citations (not
reproduced here to avoid duplicating primary content across two repos).

## Open findings

- The parent repo's playbook-depth-gate script (proposal section (c))
  does not exist yet, so PR #25 could not paste its output as
  acceptance evidence.
  canonical: `find gates -iname '*playbook*depth*'` in this working
  tree this turn, no match.
- The role's spec file has not gained a playbook-pointer field yet
  (also out of scope for this unit, per the proposal's "Out of scope"
  section).
  canonical: `ls roles/specs/data-engineering.spec.json` in this
  working tree this turn — file not present at that path (no
  `roles/specs/` directory in this checkout).
- Layer-2 source pages were read via WebSearch result summaries, not
  individually WebFetched. A later session should fetch each cited
  page directly to check for summarization drift against the live
  text. no canonical citation for this item — it is a stated risk, not
  a claim about current state.

## Next steps

- On receiving "APPROVE issue-1174/data-engineering", promote this
  file's content into the phase-2 record
  (docs/issue-1174/reports/data-engineering.md) with the full
  required-field set.
- PR #25 (tokenmaxxxer/data-engineering-rulebook) awaits review/merge —
  not an action this session can take.
- Parent-repo units this work depends on for full Acceptance: the
  playbook-depth-gate script and the spec's playbook-pointer field —
  both out of scope for this fan-out unit.

## basis

- docs/issue-1174/proposals/operational-playbook-program.md
- tokenmaxxxer/data-engineering-rulebook branch issue-1174/operational-playbook (commit 23fc80c), PR #25 (https://github.com/tokenmaxxxer/data-engineering-rulebook/pull/25)

## kind

report

## loop_state

awaiting_approval

## why

Records this session's research-and-delivery work for issue #1174's
operational-playbook program (data-engineering fan-out unit) while the
phase-2 record file stays gated pending human approval.
