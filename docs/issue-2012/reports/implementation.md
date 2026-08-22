---
code_under_review:
  - gates/design_bearing_classifier.py
  - test/test_design_bearing_classifier.py
  - gates/test_design_bearing_classifier.py
  - docs/issue-2012/reports/implementation/corpus.md
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-2012 phase-2 implementation record

## What was done

canonical: 251baa4d (this branch's phase-2 commit).

Delivered the phase-2 build approved via `APPROVE issue-2012/implementation`
(basis: `docs/issue-2012/proposals/design-bearing-issue-classifier.md`,
proposal PR #2017), plus the operator's amendment comment on issue
#2012: include at least one real consumer-repo design-bearing exemplar
in the corpus and its own test row.
canonical: `gh pr view 2017` and `gh issue view 2012 --comments` (both run this session) — PR #2017 state MERGED, and the amendment/APPROVE comment text on issue #2012.

- `gates/design_bearing_classifier.py`: `_tokenize`/`_TOKEN_RE`/
  `_STOPWORDS` copied verbatim from spawn.py:7952-7961, a fixed
  `_DESIGN_SIGNAL_KEYWORDS` vocabulary drawn from the parent issue's own
  artifact list, `_design_bearing_score(body) -> (overlap, evidence)`,
  a closed-vocabulary `design-bearing-override: yes|no` short-circuit,
  `check_issue_body(issue, body)` (no network), `check(repo, issue)`
  (fetches via `gates/gh_rest.py fetch_issue_body`), and a `main()` CLI
  (`python3 gates/design_bearing_classifier.py <issue-number> [--repo
  <path>]`) that always exits 0 — this is a classifier in this phase,
  not an enforcement gate; wiring a core gate to consume the verdict is
  #2013's scope, explicitly out of scope here.
- `docs/issue-2012/reports/implementation/corpus.md`: four real
  mechanical rows (#1975, #1635, #1596, #1742, this repo's own landed
  issues, bodies fetched live via `gh issue view <n> --json body`),
  three constructed design-bearing fixtures (landing-page build,
  brand/SVG identity asset, k8s platform topology design), and one
  real design-bearing exemplar fetched live from a consumer repo
  (`gh issue view 1 -R tokenmaxxxer/tm-webfolio --json body`,
  2026-08-22) per the operator's amendment. Documents per-row expected
  keyword matches and the threshold-calibration rationale
  (`_DESIGN_BEARING_MIN_OVERLAP = 3`: mechanical set tops out at
  overlap 2 — #1596 and #1742 — design-bearing set bottoms out at
  overlap 3, the real exemplar's own score).
- `test/test_design_bearing_classifier.py`: `TokenizeTest` and
  `DesignBearingScoreTest` unit tests for the scoring primitives; one
  test per mechanical corpus row asserting `design_bearing is False`
  with the exact expected evidence set; one test per design-bearing row
  (3 constructed fixtures + the real tm-webfolio#1 exemplar) asserting
  `design_bearing is True` with non-empty evidence, the real-exemplar
  row asserting the exact evidence set `{html, landing, page}`; two
  override-path tests (force-yes on a mechanical-shaped body, force-no
  on a design-bearing-shaped body), each asserting the evidence names
  the override tag, not scored keywords.
- `gates/test_design_bearing_classifier.py`: added mid-commit after
  `on-the-record/hooks/live-fire-test-guard.sh` refused the first
  commit attempt for lacking a live-fire test at this exact path
  calling the module from >= 2 top-level `test_*` functions — a
  mechanical requirement the proposal did not anticipate, satisfied
  in-set (no scope change; see Rationale for deviations).
- `docs/specs/enforcement-boundary.md`: added the classifier's
  registration row (repo-local, no `spawn.py`/core-gate wiring yet —
  matches `design_research_consult.py`'s existing row shape), required
  by `gate-registration-guard.sh` before the commit would accept a new
  `gates/*.py` module.

canonical: acceptance: python3 -m pytest -q -m "not slow" test/test_design_bearing_classifier.py — result: PASS (14 passed in 0.79s)

canonical: acceptance: python3 -m pytest -q gates/test_design_bearing_classifier.py -o addopts='' — result: PASS (2 passed in 0.03s)

canonical: acceptance: python3 gates/design_bearing_classifier.py 1975 — result: PASS (design_bearing=False override=False evidence=[])

## Why

Per the proposal's Rationale (unchanged in phase 2): reuse `_tokenize`
verbatim rather than importing `_cross_family_skill_matches` (that
function's signature is keyed to skill-repo directory scans, not a
fixed keyword list); a new `gates/` module rather than living inside
`spawn.py`, matching this repo's own convention for issue-body
classifiers (`design_research_consult.py`, `requirement_intake_consult.py`)
and keeping `gates/` as leaf modules relative to `spawn.py`. Constructed
fixtures for the design-bearing side of the corpus because this repo
(a process/orchestration tool) has no literal design-bearing issue of
its own; the operator's amendment additionally required at least one
real consumer-repo exemplar since the classifier's actual future
consumers are consumer-repo issues, not this repo's own tracker.

## Rationale for deviations

The build matches the approved proposal's What-will-be-done section and
the operator's own amendment. One in-set addition surfaced mid-commit,
not anticipated by the proposal: `live-fire-test-guard.sh` (issue #914)
requires a `gates/test_<stem>.py` live-fire test calling the new
module's checking function from >= 2 top-level `test_*` functions,
staged in the same commit as the gate module. This is a mechanical
commit-time gate requirement, not a design/architecture judgment call,
stays inside the already-frozen write set (a `gates/` test file sibling
to the module), and does not change what the deliverable claims to
do — logged inline per the deviation loop, not filed as a separate
issue.

## What did not work

None.

## Open findings

None.
