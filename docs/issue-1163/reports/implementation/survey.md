# issue-1163 batch 1 (engineering-family) — current-state survey

kind: survey
subject: issue-1163

## What exists today

canonical: `docs/specs/role-invariant-coverage.md` "Quality-bar status"
table, read this turn. All 43 roles are listed; 7 carry
`quality_bar: landed` (issue #1156), the other 36 carry
`bar: domain-named, decomposition-pending` with a named domain and
source standard. Among the 36, the engineering-family cluster is:
data-engineering (row 14), data-modeling (row 15), ml-engineering
(row 29), observability (row 30), refactoring-legacy (row 35),
release-engineering (row 36) — the exact 6 roles issue #1163's body
names as its batch-1 example.

derived: `grep -c '"quality_bar"' roles/specs/{data-engineering,data-modeling,ml-engineering,observability,refactoring-legacy,release-engineering}.spec.json`
```
roles/specs/data-engineering.spec.json:0
roles/specs/data-modeling.spec.json:0
roles/specs/ml-engineering.spec.json:0
roles/specs/observability.spec.json:0
roles/specs/refactoring-legacy.spec.json:0
roles/specs/release-engineering.spec.json:0
```
None of the 6 batch-1 specs carry a `quality_bar` key yet. Each already
carries `source_standard`; data-engineering, data-modeling,
ml-engineering, observability, refactoring-legacy also carry
`judgment_methodology`/`review_methodology` (five-activity depth from
#1130) — release-engineering carries `source_standard` only (canonical:
read of all 6 `roles/specs/*.spec.json` files this turn).

canonical: `docs/issue-1156/proposals/per-role-quality-bars.md` §0/§1,
and `roles/specs/secure-coding.spec.json`, read this turn. The landed
7-role template shape: `quality_bar` is an array of
`{criterion, verification_method}` objects (4 entries in the landed
examples), sourced from the spec's own already-cited
`source_standard`/`judgment_methodology`/`review_methodology`;
`loop_state.refusal` gains `"bar-not-met"` alongside whatever refusal
states already existed (e.g. secure-coding keeps
`target-level-undeclared` and adds `bar-not-met`).

canonical: `gates/spec_schema_five_activities_test.py`, read this turn,
lines 95-141. Defines `QUALITY_BAR_ROLES` (currently the 7 landed
roles) and three tests: every listed role has a nonempty `quality_bar`
array with non-empty `criterion`/`verification_method` strings; every
listed role's `loop_state.refusal` contains `bar-not-met`; and
`test_no_other_spec_carries_a_quality_bar_yet` asserts every spec NOT
in `QUALITY_BAR_ROLES` does not carry a `quality_bar` key — this last
test fails as soon as any of the 6 batch-1 specs gains a `quality_bar`
unless the 6 are added to `QUALITY_BAR_ROLES` in the same commit.

canonical: `gates/quality_bar.py` lines 32-45, read this turn.
`bar_scoped_roles` reads role scoping generically from
`role_path_patterns` (each role's `use_when.trigger.path_patterns`)
and only enters a role into scope if it matches a changed path — no
role list is hardcoded.

canonical: `on-the-record/hooks/quality-bar-gate.sh` line 201, read
this turn: `quality_bar.bar_scoped_roles(pr_files, role_patterns)` is
called the same generic way. This confirms the issue's own requirement
3 claim: no hook/gate file change is needed for the 6 new roles.

canonical: `git log --oneline -5` and `git status`, read this turn.
Branch `issue-1163/implementation` sits on top of `main` post-merge of
PR #1164 (fast-forward, clean tree). PR #1164 touched
`roles/specs/brand-design.spec.json`,
`roles/specs/content-design.spec.json`,
`roles/specs/market-analysis.spec.json` (issue-1160 mission fields) —
none of those 3 files overlap this batch's 6-role write set, so no
rebase conflict or regression risk on the just-landed mission fields.

## Write set this batch will touch

- `roles/specs/data-engineering.spec.json`
- `roles/specs/data-modeling.spec.json`
- `roles/specs/ml-engineering.spec.json`
- `roles/specs/observability.spec.json`
- `roles/specs/refactoring-legacy.spec.json`
- `roles/specs/release-engineering.spec.json`
- `gates/spec_schema_five_activities_test.py` (extend `QUALITY_BAR_ROLES`
  with the 6 new roles)
- `docs/specs/role-invariant-coverage.md` (flip the 6 rows' status to
  landed, matching the table's own status-value convention)
- `docs/specs/reconciled-index.md` (regenerate — required whenever a
  `docs/specs/*` file changes, per the standing spec-index-preflight
  rule)

canonical: `gates/quality_bar.py` lines 32-45 and
`on-the-record/hooks/quality-bar-gate.sh` line 201, both read this
turn. No hook/gate file changes are in this write set — confirmed
above that `quality-bar-gate.sh`/`quality_bar.py` read `quality_bar`
presence generically.

## Alternatives considered

- Batch by the issue's literal "product/design-family" or "business/
  ops-family" split instead of engineering-family first: rejected —
  the issue body names engineering-family as batch 1's example grouping
  and the issue's own "실행 계획" checklist lists it as step 1
  (canonical: `gh issue view 1163`, read this turn).
- Include architecture (row 8) or execution-observation (row 18) in
  this batch as adjacent "engineering" domains: rejected — the coverage
  matrix families these under decision-record-quality and
  execution-conformance respectively (canonical:
  `docs/specs/role-invariant-coverage.md`, read this turn), not the
  pipeline/data/ML/observability/release engineering cluster the issue
  names by example, and 6 already sits inside the stated 6-8 band
  without stretching the family definition.
