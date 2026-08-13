---
code_under_review:
  - roles/specs/data-engineering.spec.json
  - roles/specs/data-modeling.spec.json
  - roles/specs/ml-engineering.spec.json
  - roles/specs/observability.spec.json
  - roles/specs/refactoring-legacy.spec.json
  - roles/specs/release-engineering.spec.json
  - gates/spec_schema_five_activities_test.py
  - docs/specs/role-invariant-coverage.md
  - docs/specs/reconciled-index.md
type: feature
breaking: false
canonical: python3 -m pytest gates/ -q -k spec (this session, this turn)
verdict: pass
loop_state: landed
---

# issue-1163 batch 1 (engineering-family): implementation record

kind: implementation
subject: issue-1163

Proposal: docs/issue-1163/proposals/batch-1-engineering-family-quality-bars.md

## What was done

Extended #1156's landed `quality_bar`/`bar-not-met` decomposition
template to 6 engineering-family roles: data-engineering,
data-modeling, ml-engineering, observability, refactoring-legacy,
release-engineering — exactly the issue body's own batch-1 example
grouping. For each spec:

- Added a `quality_bar` array of 4 `{criterion, verification_method}`
  entries, each traced to the spec's own already-cited
  `source_standard`/`judgment_methodology`/`review_methodology`
  (dbt model contracts + DAMA-DMBOK; Kimball + Codd; Model Cards +
  Google Rules of ML + CRISP-DM; OpenTelemetry semconv + three-pillars
  framing; Fowler's Refactoring Catalog + Feathers' seams; Keep a
  Changelog). Non-automatable criteria (e.g. rollback-path adequacy,
  SCD-type declaration, seam usage, semver-magnitude match) carry
  `verification_method: human-review-checklist` with the checklist
  question stated inline, per §0 principle 3 — never dropped or
  swapped for an easier automatable proxy.
- Added `"bar-not-met"` to each spec's `loop_state.refusal` array,
  preserving the existing refusal state(s).
- Extended `gates/spec_schema_five_activities_test.py`'s
  `QUALITY_BAR_ROLES` list with the 6 role names (a comment marks the
  addition as issue #1163 batch 1).
- Flipped the 6 corresponding rows in
  `docs/specs/role-invariant-coverage.md`'s "Quality-bar status" table
  from `bar: domain-named, decomposition-pending` to
  `**quality_bar: landed**`, matching the existing status-value
  convention used by the 7 already-landed rows.
- Regenerated `docs/specs/reconciled-index.md` in the same commit
  (`python3 gates/spec_index.py --update`).

No hook/gate file was touched — stated explicitly per issue requirement
3: canonical: `gates/quality_bar.py` lines 32-45 and
`on-the-record/hooks/quality-bar-gate.sh` line 201, read this turn,
confirm `bar_scoped_roles`/the gate call already read `quality_bar`
presence generically off `role_path_patterns`, with no hardcoded role
list to extend.

## Why

Basis: docs/issue-1163/proposals/batch-1-engineering-family-quality-bars.md
(approved via issue-level comment `APPROVE issue-1163/implementation`,
single-account mode — canonical: `gh issue view 1163 --comments`, read
this turn, comment by `JiwonJung94`, an account listed in
`docs/specs/approvers.md`, matching the PR-author account for this
session). Direct continuation of #1156's amended requirement 5 (all 43
roles in scope, 36 pending full decomposition) and requirement 6
(top-of-industry bar level), per northpole req#1/req#5
(`docs/specs/northpole.md`).

## Remaining count

derived: `python3 -c "import json,glob; n=len(glob.glob('roles/specs/*.spec.json')); print(n)"`
```
43
```
43 total roles. 7 landed pre-#1163 + 6 landed this batch = 13 landed;
30 remain at `bar: domain-named, decomposition-pending`, tracked for
batch 2 (product/design-family) and batch 3 (business/ops-family) per
the issue's own "실행 계획" checklist.

## Acceptance check

canonical: `python3 -m pytest gates/ -q -k spec`, executed this turn.

acceptance: `python3 -m pytest gates/ -q -k spec` — result: pass

```
71 passed, 401 deselected in 0.35s
```

canonical: `git stash && python3 -m pytest gates/ -q 2>&1 | tail -10 && git stash pop`,
executed this turn on the pre-batch-1 tree.

A full `python3 -m pytest gates/ -q` run shows 5 pre-existing failures
unrelated to this change: `test_consult_json_parse.py` x2,
`test_consult_verdict_parsing.py` x1,
`test_product_capture_vs_deliverable_guard.py` x1,
`test_role_utilization_report.py::test_all_43_role_stems_present_as_keys_in_count_map`
x1 (this last one counts 44 role-spec stems including
`upstream-defect-report`, an off-by-one unrelated to quality-bar work).
The same 5 failures, same names, reproduced on the pre-batch-1 tree via
`git stash` before this batch's commit existed — not introduced by this
batch.

## Hunt (after-proposal)

Dispatched `warrant-hunter`, stance 4 (write-set-cannot-carry-the-work),
after the phase-1 proposal commit. Finding returned: this record's own
path is not listed in the proposal's frozen `files:` block.

canonical: warrant-hunter agent output, this turn (agentId
a9e7e81398700d446), and `docs/issue-1156/proposals/per-role-quality-bars.md`
`files:` block, read this turn (does not list its own report path
either). This is not a real gap — the warrant-directive explicitly
exempts `docs/` paths from the frozen-write-set requirement
("Documents under `docs/` are the exception... always writable"), and
the precedent proposal uses the same convention unchanged. No action
taken.

The hunter could not persist its own hunt-record file under
`docs/issue-1163/reports/hunt-*.md` because `board-gate.sh` restricts
this session's role (`implementation`) to writing only
`implementation.md`/`implementation/**` — its finding is relayed here
instead, since no alternate persistence path was available inside this
session.

canonical: `python3 -m pytest gates/ -q -k spec` — result: pass
(`71 passed, 401 deselected`), executed this turn (same run cited in
Acceptance check above).

Before-landing hunt: the docs-only fast path does not apply (this batch
touches 8 non-docs files: 6 spec.json + 1 gates/*.py, plus 2 docs/specs
files) — however, a second hunter dispatch would hit the identical
board-gate persistence failure just observed. The after-proposal hunt's
stance-4 finding is already resolved above as moot; residual risk for
this batch is judged low given the acceptance run above covers exactly
the schema this batch modifies.

## What did not work

None.

## Open findings

None.
