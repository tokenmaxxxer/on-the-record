---
status: proposed
files:
  - docs/issue-586/reports/product-discovery/current-state.md
  - docs/issue-586/proposals/product-discovery.md
---

# Proposal — issue #586, product-discovery pass

## Intent
Per `docs/issue-586/reports/product-discovery/current-state.md`: the
axis-ownership matrix and its gate are reached in this repo (batch 1,
merged). The remaining work — per-role rulebook procedures for the 3
newly-assigned axis owners (batches 2-4) and the 3+-role panel fixture
(batch 5) — has no filed GitHub issue tracking it. This proposal's only
ask is that gap: file the follow-up issues, in the priority order below,
so the work is trackable instead of living only as a paragraph inside a
merged PR's proposal body.

## Constraints found
- product-discovery cannot write rulebook prose itself (cross-repo,
  per the architecture proposal's own division of labor) or the
  conformance-review test fixture (another role's own step 3) — this
  proposal's write set is docs only, matching the two files above.
- The axis vocabulary and the 5 assignments are not reopened here; both
  are treated as settled per the current-state survey's citations.

## Hypothesis (pre-registration)
We believe filing the 4 tracking issues below (batches 2, 3, 4, 5) will
make issue #586's remaining scope actually trackable instead of living
only inside a merged PR's proposal prose.

Metric: count of new open GitHub issues cross-referencing #586 for
batches 2/3/4/5, beyond the existing 586/650/609/623/628/573/597 set
(`gh issue list --search "586"`).
Threshold: 4.

Decision rule:
- go: metric reaches 4 within this proposal's own execution — file all 4
  issues in the RICE order below.
- kill: not applicable — filing a tracking issue is reversible (closable
  if later judged unnecessary) and costs one `gh issue create` call per
  batch, so there is no scenario where filing should be abandoned rather
  than completed.
- pivot: if a candidate axis-owning role (conformance-review,
  capacity-planning, performance-engineering) states in this proposal's
  review that its own axis assignment should be revisited before a
  procedure is written against it, pivot by deferring only that one
  batch's filing until that role's own judgment lands — the other
  batches still go.

Guardrail metric: none of the 5 already-owned axes or the closed
5-vocabulary is reopened by any filed issue's body — a filed issue whose
text proposes a 6th axis or reassigns an existing owner is a guardrail
breach (not this proposal's authority; see Out of scope). Guardrail
status: not breached — no such issue is filed by this proposal's own
recommendation.

ITWWS (if this works we should): once all 4 issues are filed and closed,
re-run this same current-state survey's read set to confirm the
`axis_evaluation` rule count rises from 2/5 to 5/5 and a 3+-role panel
fixture exists — pre-committed as a follow-up survey pass, not done in
this proposal.

## Prioritization (RICE)
Reach and Impact are scored against "how much of the #573 panel's actual
trust surface each unit unblocks," not user count (no end-user
population exists for this internal gate).

| Candidate | Reach (1-5) | Impact (1-5) | Confidence (1-5) | Effort (person-days) | RICE = R×I×C/E |
|---|---|---|---|---|---|
| File batch 5 (3+-role panel fixture issue, conformance-review) | 5 — every future panel render depends on this fixture existing to prove the shape works at all | 5 — without it, "the gate renders a full panel" (issue #586 acceptance criterion 3) is unverified for any decision, not just these 3 roles | 4 — scope is a single test file extension, well-specified by the existing 2-role seed fixture | 1 | 100 |
| File batch 2 (conformance-review `alignment` procedure) | 3 — `alignment` axis gates conformance-review verdicts specifically | 4 — conformance-review's own domain is comparing artifact-vs-spec; an unwritten procedure here means its own gate C check has nothing to point at | 3 — template exists (READ/EXECUTE/CRITERIA/CITATION), but conformance-review must fill it from its own domain knowledge | 1 | 36 |
| File batch 3 (capacity-planning `external_burden` procedure) | 2 — narrower axis, architecture proposal itself flagged this assignment as "nearest fit, not literal match" | 3 | 3 | 1 | 18 |
| File batch 4 (performance-engineering `performance` procedure) | 3 — direct 1:1 axis-to-role fit per the architecture proposal | 3 | 4 — least ambiguous of the three, template fill-in is closest to mechanical here | 1 | 36 |

Recommended filing order: batch 5 first (blocks verifying the whole
panel mechanism), then batch 2 and batch 4 (tied, either order), then
batch 3.

## Evidence
- 0 interviews/observations, 2026-08-12: no end-user population exists
  for this internal-tooling gate; evidence substituted is repo-state
  reads (not stated preference), cited as `derived:` lines in
  `docs/issue-586/reports/product-discovery/current-state.md` —
  paraphrase: "3 of 5 axis-owning roles have no axis_evaluation rule in
  spec.json; no follow-up issue for that gap, or for the 3+-role panel
  fixture, appears in gh issue list --search 586".

## Accumulation
Filing 4 issues is a one-time act, not a repeating pattern — the axis
vocabulary is closed at 5 (survey citation:
`gates/role_spec_shape.py::_JUDGMENT_AXES`), so at most these 4 follow-ups
plus batch 5 will ever be needed for the current matrix; no unbounded
accumulation risk.

## Out of scope
- Reopening the 5-axis vocabulary or the existing 5 assignments.
- Writing the rulebook procedure prose itself (cross-repo) or the panel
  fixture test code (conformance-review's own step) — this proposal only
  recommends filing the tracking issues and their priority order.

## How I'll know it worked
- 4 new GitHub issues exist (batches 2, 3, 4, 5), each referencing this
  issue (#586) and citing the current-state survey's read evidence for
  what's missing.
- `gh issue list --search "586"` subsequently lists them.

## What did not work
None.
