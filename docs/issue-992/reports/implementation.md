---
code_under_review:
  - docs/handbooks/architecture-methodology.md
  - roles/specs/conformance-review.spec.json
  - roles/specs/capacity-planning.spec.json
  - roles/specs/performance-engineering.spec.json
  - roles/specs/requirements-engineering.spec.json
  - roles/specs/risk-management.spec.json
  - docs/issue-992/reports/implementation/fixtures/conformance-review.md
  - docs/issue-992/reports/implementation/fixtures/capacity-planning.md
  - docs/issue-992/reports/implementation/fixtures/performance-engineering.md
  - docs/issue-992/reports/implementation/fixtures/requirements-engineering.md
  - docs/issue-992/reports/implementation/fixtures/risk-management.md
type: docs
breaking: false
verdict: landed
loop_state: landed
---

# issue-992 implementation record (phase 2)

## Summary of work

Executed `docs/issue-992/proposals/2026-08-12-implementation-phase-a-deepening.md`
Phase A's "What will be built" steps 1-4:
1. Added 3 `## Axis evaluation procedure` sections
   (`alignment`, `external_burden`, `performance`) to
   `docs/handbooks/architecture-methodology.md`, following the
   existing template's READ/EXECUTE/CRITERIA/CITATION shape, each
   citing the owning role's own `source_standard` (EARL 1.0 for
   conformance-review; ITIL Capacity Management for capacity-planning;
   Google SRE SLO/error-budget for performance-engineering) — no new
   citation invented beyond those already present in the spec.json
   files.
2. Added `finding_method`/`anti_pattern` array fields to
   `roles/specs/requirements-engineering.spec.json` and
   `roles/specs/risk-management.spec.json`, grounded in EARS/29148 and
   NIST SP 800-161r1/IR 8286 respectively.

```
derived: python3 -c "
import json
for f in ['roles/specs/requirements-engineering.spec.json','roles/specs/risk-management.spec.json']:
    d=json.load(open(f))
    print(f, 'finding_method:', len(d['finding_method']), 'anti_pattern:', len(d['anti_pattern']))
"
roles/specs/requirements-engineering.spec.json finding_method: 4 anti_pattern: 4
roles/specs/risk-management.spec.json finding_method: 4 anti_pattern: 4
```

3. Wrote live-fire seed-task fixtures per Phase-A role under
   `docs/issue-992/reports/implementation/fixtures/`, each constructed
   with a stated generic-reasoning verdict and a methodology-correct
   verdict that diverges.

```
derived: ls docs/issue-992/reports/implementation/fixtures/ | wc -l
5
```
(5 fixture files, 2 scenarios each per the proposal's own count.)

4. Re-ran the guardrail-metric check.

canonical: `python3 gates/role_spec_shape.py --roles-dir roles` (run
this session)
```
derived: python3 gates/role_spec_shape.py --roles-dir roles; echo exit=$?
exit=0
```
Matches survey.md's stated pre-edit baseline (also exit 0) — additive
fields did not regress the gate.

## Why

Basis: `docs/issue-992/proposals/2026-08-12-implementation-phase-a-deepening.md`,
scoping Phase A of the deepening plan approved in #996.
canonical: `gh issue view 992 --comments` (run this session) shows the
exact-string comment `APPROVE issue-992/implementation` as the
authorizing comment for this role's own phase 2, and the exact-string
comment `APPROVE issue-992/product-discovery` authorizing #996
upstream.

## Upstream / basis

docs/issue-992/proposals/2026-08-12-implementation-phase-a-deepening.md

## What did not work

None.

## Live-fire seed-task result (per #996 §5)

canonical: docs/issue-992/reports/implementation/fixtures/conformance-review.md,
docs/issue-992/reports/implementation/fixtures/capacity-planning.md,
docs/issue-992/reports/implementation/fixtures/performance-engineering.md,
docs/issue-992/reports/implementation/fixtures/requirements-engineering.md,
docs/issue-992/reports/implementation/fixtures/risk-management.md (all
written this session) — every fixture states a generic-reasoning
verdict and a methodology-correct verdict per the newly-added
axis-evaluation EXECUTE steps / finding_method items, and in each
fixture the two verdicts are not the same (e.g. conformance-review
fixture 1: majority-vote reads "supports", EARL worst-case
recomputation reads "contradicts" on the identical input).

```
derived: grep -c '^Divergence:' docs/issue-992/reports/implementation/fixtures/*.md
docs/issue-992/reports/implementation/fixtures/capacity-planning.md:2
docs/issue-992/reports/implementation/fixtures/conformance-review.md:2
docs/issue-992/reports/implementation/fixtures/performance-engineering.md:2
docs/issue-992/reports/implementation/fixtures/requirements-engineering.md:2
docs/issue-992/reports/implementation/fixtures/risk-management.md:2
```

This clears #996 §5's threshold with margin, though the divergence is
reasoned from the written methodology text, not from an independent
agent actually re-grading each fixture blind — that grading-agent
mechanism is explicitly out of scope per this proposal's own "Out of
scope" section.

## Open findings

canonical: docs/issue-992/reports/implementation/2026-08-12-hunt-implementation-phase-a-deepening.md
(hunt record written this session, both after-proposal and
before-landing sections) — before-landing stance 0 (bypass-hunt) found
that `gates/role_spec_shape.py` never validates the new
`finding_method`/`anti_pattern` array fields: a spec carrying a
wrong-typed or garbage value in either field still exits 0. This does
not break this proposal's own constraint (fields are additive and the
gate's exit code does not regress, matching the pre-edit baseline
exactly) — it is a pre-existing gap in the gate's own coverage that
this diff's new fields fall into, same as any other field the gate does
not walk.

## Next steps

None required to close this Phase-A delivery.
canonical: docs/issue-992/reports/implementation/2026-08-12-hunt-implementation-phase-a-deepening.md
(read this session) — the gate-coverage gap that record names is a
follow-up for whichever role next touches `gates/role_spec_shape.py`;
extending that gate is outside this proposal's own frozen write set.

## Resolution path

File as a follow-up issue (or fold into the next `gates/role_spec_shape.py`
touch) to extend its `check()` function to walk `finding_method`/
`anti_pattern` when present (type: array of strings, non-empty). Not
blocking this record's `landed` state — the finding is about the
gate's own coverage, not about this diff's correctness.
