---
status: proposed
files:
  - roles/specs/data-engineering.spec.json
  - roles/specs/data-modeling.spec.json
  - roles/specs/ml-engineering.spec.json
  - roles/specs/observability.spec.json
  - roles/specs/refactoring-legacy.spec.json
  - roles/specs/release-engineering.spec.json
  - gates/spec_schema_five_activities_test.py
  - docs/specs/role-invariant-coverage.md
  - docs/specs/reconciled-index.md
---

# issue-1163 batch 1 (engineering-family): quality-bar decomposition

kind: proposal
subject: issue-1163

Proposal: docs/issue-1163/proposals/batch-1-engineering-family-quality-bars.md

## Request

Extend #1156's landed `quality_bar`/`bar-not-met` template (§0
decomposition principles: top-of-industry, decompose-the-adjective,
non-automatable → named human-review checklist, no self-grading,
bounded rejection) to 6 engineering-family roles among the 36 still at
`bar: domain-named, decomposition-pending`: data-engineering,
data-modeling, ml-engineering, observability, refactoring-legacy,
release-engineering — the exact set the issue body names as batch 1's
example grouping. Each gets a `quality_bar` array of
`{criterion, verification_method}` entries sourced from the spec's own
already-cited `source_standard`/`judgment_methodology`/
`review_methodology`, plus `bar-not-met` added to `loop_state.refusal`.
Extend `gates/spec_schema_five_activities_test.py`'s `QUALITY_BAR_ROLES`
coverage list with the 6, and flip the 6 rows' status in
`docs/specs/role-invariant-coverage.md`.

## Constraints

- Bar level is top-of-industry, not passing-grade — each criterion sits
  at the refuse-below line, per §0 principle 1
  (`docs/issue-1156/proposals/per-role-quality-bars.md`).
- No new, uncited standard: every criterion traces to the role's
  already-cited `source_standard`/`judgment_methodology`/
  `review_methodology` (§0 principle 2).
- Where a criterion cannot be automated, it becomes a named human-review
  checklist item with `verification_method: human-review-checklist`
  (or equivalent), never dropped or downgraded to an easier automatable
  proxy (§0 principle 3).
- `gates/quality-bar-gate.sh`/`gates/quality_bar.py` read `quality_bar`
  presence generically off `role_path_patterns` (survey: canonical
  `gates/quality_bar.py` lines 32-45) — no hook/gate file is in this
  write set; stated explicitly per the issue's requirement 3.
- Do not touch `roles/specs/brand-design.spec.json`,
  `content-design.spec.json`, `market-analysis.spec.json` — #1160's
  just-landed mission fields must not regress (survey: PR #1164 touched
  only those 3 files, no overlap with this batch's write set).

## Rationale

Considered decomposing by literal issue-order across all 36 roles in
one PR instead of a 6-role engineering-family batch: rejected —
requirement 2 explicitly asks for phase-wise batching ("6-8 roles per
PR") so review stays real, and a 36-role single PR would be exactly the
oversized review surface requirement 2 exists to prevent.

Considered widening this batch to 8 by pulling in architecture and
execution-observation as adjacent "engineering" domains: rejected — the
coverage matrix families those under decision-record-quality and
execution-conformance respectively (survey: `docs/specs/role-invariant-coverage.md`
rows 8/18), a different family than the
pipeline/data/ML/observability/release cluster this batch targets; 6
already sits inside the issue's stated 6-8 band without stretching the
family definition, and mixing families would make review harder to
scope, not easier.

## What will be done

1. For each of the 6 specs, add a `quality_bar` array (4 criteria each,
   matching the landed 7's depth) decomposed from the spec's own cited
   standard(s):
   - data-engineering: dbt model contracts + DAMA-DMBOK data-quality
     dimensions.
   - data-modeling: Kimball dimensional-modeling conventions + Codd's
     normalization rules.
   - ml-engineering: Model Cards (Mitchell et al. 2019) + Google's Rules
     of ML + CRISP-DM evaluation-phase sign-off.
   - observability: OpenTelemetry semantic conventions + three-pillars
     framing (Sridharan).
   - refactoring-legacy: Fowler's Refactoring Catalog/code-smell
     catalog + Feathers' seam-identification.
   - release-engineering: Keep a Changelog.
2. Add `"bar-not-met"` to each of the 6 specs' `loop_state.refusal`
   array, preserving existing refusal states.
3. Extend `gates/spec_schema_five_activities_test.py`'s
   `QUALITY_BAR_ROLES` list with the 6 role names.
4. Flip the 6 corresponding rows in
   `docs/specs/role-invariant-coverage.md`'s "Quality-bar status" table
   from `bar: domain-named, decomposition-pending` to
   `quality_bar: landed`, matching the table's existing status-value
   convention and citing each spec's own `quality_bar` array.
5. Regenerate `docs/specs/reconciled-index.md` in the same commit
   (`python3 gates/spec_index.py --update`), required whenever
   `docs/specs/*` changes.
6. Record: `docs/issue-1163/reports/implementation.md`, stating the
   remaining count (43 total − 7 landed − 6 this batch = 30 roles still
   pending) per the issue's acceptance "empty state" line.

## Out of scope

- The other 30 pending roles (product/design-family, business/ops-
  family) — later batches per the issue's own step 2/step 3 plan.
- Any hook/gate change — none needed (see Constraints).
- Any change to the already-landed 7 roles or to the 3 roles #1160 just
  touched.

## How you'll know it worked

`python3 -m pytest gates/spec_schema_five_activities_test.py -q` exits
0 with `QUALITY_BAR_ROLES` covering 13 roles (7 landed + 6 this batch)
and `test_no_other_spec_carries_a_quality_bar_yet` passing for the
remaining 30.
