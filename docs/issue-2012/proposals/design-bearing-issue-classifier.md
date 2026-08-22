---
status: proposed
files:
  - gates/design_bearing_classifier.py
  - test/test_design_bearing_classifier.py
  - docs/issue-2012/reports/implementation/corpus.md
---

## Request

Artifact-gate phase 1 (#2012): a function/CLI classifying an issue body
as design-bearing or not, returning a verdict plus cited evidence
(which signals fired), precision-first (zero false positives on a
mechanical exemplar corpus), with an override path, reusing the
existing cross-family keyword-overlap machinery from #2001 rather than
inventing a new detector. Unit tests cover both classes and the
override path. This issue does not wire the verdict into any core gate
or spawn path — that consumption is #2013 (already filed, artifact-gate
phase 2).

## Constraints

- Confined to `spawn.py`, `gates/`, `test/`/`tests/`, `docs/` per the
  issue's stated scope.
- Must reuse #2001's cross-family signal machinery
  (`_tokenize`/overlap-scoring shape at spawn.py:7952-7986), not invent
  an unrelated detector — per the issue's explicit framing.
- Precision-first: zero false positives on the mechanical exemplar set
  is a hard bar (survey, "Precision-first framing" section) — no stated
  false-negative bound on the design-bearing set.
- Verdict + cited evidence (which signals fired) must both be exposed
  — a bare boolean does not satisfy the acceptance line.
- Must expose an override path the orchestrator can set per issue.
- No network calls beyond the existing `gh_rest.fetch_issue_body`
  fetch pattern already used by sibling `gates/*_consult.py` modules
  (survey, "Existing gate module conventions" section) — no new
  dependency.

## Rationale

Two placements were considered for the scoring function itself:

1. **Import and directly reuse `_cross_family_skill_matches` from
   `spawn.py`**, treating "design-bearing signal keywords" as if they
   were a family of skill trigger sentences. Rejected: that function's
   signature and body are keyed to skill directories and
   `_skill_trigger_line()` extraction (spawn.py:7964-7986) — bending it
   to score against a fixed keyword list instead of skill-repo
   directories would mean either mocking a fake skill-repo layout for
   every classification call (indirection with no payoff) or forking
   its internals until nothing is shared but the name. The proposal
   instead reuses `_tokenize` (spawn.py:7957-7961) verbatim — the part
   that is actually keyword-scoring-shaped and vocabulary-agnostic —
   and writes a small dedicated overlap function shaped like
   `_cross_family_skill_matches`'s body (tokenize, count distinct
   shared tokens, threshold, sort deterministically) but scoped to a
   fixed design-signal keyword list instead of a directory scan. This
   is "reuse the signal," per the issue's own wording, not "reuse the
   call site."
2. **Live inside `spawn.py` itself**, next to `_cross_family_skill_matches`,
   since that is where the reused signal lives. Rejected in favor of a
   new `gates/design_bearing_classifier.py` module: every existing
   issue-body classifier in this repo (`design_research_consult.py`,
   `requirement_intake_consult.py`, `acceptance_gate.py` — survey,
   "Existing gate module conventions" section) lives under `gates/` as
   a standalone `check_issue_body`/`check`/`main` module, independently
   unit-testable with no `spawn.py` import surface. #2012's acceptance
   line asks for "a function/CLI (`spawn.py` or `gates/`)" — `gates/`
   matches this repo's own convention for exactly this shape of
   classifier, and keeps the classifier importable by #2013's future
   core gate without pulling in all of `spawn.py`. `_tokenize` is
   copied (not imported) from `spawn.py` into the new module: importing
   `spawn.py` from a `gates/` module would invert this repo's existing
   dependency direction (`gates/` modules are leaves; `spawn.py` is a
   heavier top-level CLI that itself may import `gates/` code) for the
   sake of four lines of regex/set-comprehension.

For the design-bearing exemplar set, the survey found no literal
design-bearing issue in this repo's own tracker (a process/orchestration
tool, not a product-UI repo) to replay against the way #2001 replayed
against 12+ real spawned sessions. Two options were considered:

1. **Skip the design-bearing side of the corpus and validate only
   against the mechanical exemplars this repo does have.** Rejected:
   the acceptance line requires the corpus to mark "known design-bearing
   exemplars ... as design-bearing" — a corpus with zero design-bearing
   rows cannot demonstrate that half of the acceptance criterion at
   all, regardless of how clean the mechanical-side precision looks.
2. **Construct representative fixture issue bodies for the
   design-bearing side** (a landing-page build, a brand/SVG asset
   request, a k8s platform topology design — the parent issue's own
   named categories), paired with the mechanical side pulled verbatim
   from this repo's real closed issues (#1975, #1635, #1596, #1742 —
   survey, "No existing design-bearing corpus" section). Chosen: this
   keeps the higher-stakes precision-first (false-positive) side of the
   corpus check grounded in real, already-landed mechanical work while
   still exercising the design-bearing recall side against text shaped
   like genuine design requests.

## What will be done

- Add `gates/design_bearing_classifier.py`, following the
  `check_issue_body(issue, body)` / `check(repo, issue)` / `main()`
  shape shared by `design_research_consult.py` and
  `requirement_intake_consult.py` (survey, "Existing gate module
  conventions" section):
  - Copy `_TOKEN_RE`/`_STOPWORDS`/`_tokenize` verbatim from
    spawn.py:7952-7961 into the new module (no `spawn.py` import, per
    Rationale above).
  - A fixed `_DESIGN_SIGNAL_KEYWORDS` vocabulary (storyboard,
    information architecture, flow diagram, user scenario(s), html
    demo, wireframe, landing page, mockup, visual design, brand
    identity, ui, ux, layout, and similar design-decision terms drawn
    from the parent issue's own artifact list: storyboard, IA, flow
    diagram, user scenarios, HTML demo).
  - `_design_bearing_score(issue_body) -> tuple[int, list[str]]`:
    tokenize the body, intersect against the keyword vocabulary,
    return the overlap count and the sorted list of matched keywords
    (the "cited evidence" the acceptance line requires).
  - `check_issue_body(issue, body)`: closed-vocabulary override check
    first — an explicit `design-bearing-override: yes` or
    `design-bearing-override: no` tag line in the body (same shape as
    #1653's `design-research-skip: mechanical`, survey "Override path"
    section) short-circuits the scorer entirely and is cited as the
    evidence. Absent an override, run the scorer, pick a conservative
    minimum-overlap threshold (calibrated against the corpus below —
    the precision-first bar means the threshold is picked to clear the
    mechanical set at zero false positives first, then checked for
    still catching the design-bearing set, not the reverse), and return
    a verdict object: `{"design_bearing": bool, "evidence":
    [matched keywords], "override": bool}`.
  - `main()`: CLI entry, `gates/design_bearing_classifier.py <issue-number>
    [--repo <path>]`, fetches via `gates/gh_rest.py`'s
    `fetch_issue_body` (survey, "conventions" section), prints the
    verdict and evidence, exits 0 always (this is a classifier, not a
    pass/fail gate in this phase — #2013 decides what a core gate does
    with the verdict).
- Add `docs/issue-2012/reports/implementation/corpus.md`: the exemplar
  corpus itself — the mechanical rows sourced verbatim from #1975,
  #1635, #1596, #1742 (title + a representative body excerpt each,
  fetched live via `gh issue view`), and the design-bearing rows as
  three constructed fixture bodies (landing-page build,
  brand/SVG-identity asset, k8s platform topology design) modeled on
  the parent issue's own named categories, each with a one-line note
  on which keywords are expected to fire.
- Add `test/test_design_bearing_classifier.py`:
  - Unit tests for `_tokenize` (reused behavior, mirroring #2001's own
    `TokenizeTest` shape) and `_design_bearing_score` (matching case,
    sub-threshold/no-match case).
  - One test per mechanical corpus row (#1975, #1635, #1596, #1742):
    asserts `design_bearing is False` — the precision-first
    zero-false-positive bar, enforced per-row so a future keyword
    addition that breaks any one of them fails loudly and individually
    rather than as one aggregate count.
  - One test per design-bearing fixture row: asserts `design_bearing is
    True` with non-empty evidence.
  - Override-path tests: a mechanical-shaped body carrying
    `design-bearing-override: yes` is classified design-bearing despite
    scoring below threshold; a design-bearing-shaped body carrying
    `design-bearing-override: no` is classified not-design-bearing
    despite scoring above threshold; both assert the evidence names the
    override, not scored keywords.

## Out of scope

- Wiring the classifier's verdict into any core gate, `spawn.py`
  directive assembly, or CI check — that consumption is #2013
  (artifact-gate phase 2), a separate issue per the parent issue's own
  "later (separate issue)" framing.
- Retiring or modifying `gates/design_research_consult.py`'s
  self-declared-tag mechanism (#1653) — it continues to operate
  independently; whether/how the two gates should be reconciled is a
  question for whichever issue wires #2012's verdict into a consumer.
- Tuning the keyword vocabulary or threshold beyond what the corpus in
  this proposal supports — if a broader corpus later reveals
  miscalibration, that is follow-up work, not decided speculatively
  here (mirrors #2001's own explicit Out-of-scope precedent on
  threshold tuning).
- A generalized/pluggable classification framework, multiple detector
  strategies, or ML-based scoring — one deterministic keyword-overlap
  classifier, per the issue's explicit direction to reuse #2001's
  signal shape rather than invent a new detector.

## How you'll know it worked

- `pytest test/test_design_bearing_classifier.py -o addopts=''` passes,
  asserting: zero false positives across all four real mechanical
  corpus rows individually, correct design-bearing classification with
  non-empty evidence across all three constructed design-bearing
  fixture rows, and both override-path cases (force-yes on a
  mechanical-shaped body, force-no on a design-bearing-shaped body).
- `docs/issue-2012/reports/implementation/corpus.md` exists, cites real
  issue numbers for the mechanical rows and states the design-bearing
  rows are constructed fixtures (not claimed as real issues), per the
  survey's finding that no literal design-bearing issue exists in this
  repo's own tracker.
- `python3 gates/design_bearing_classifier.py <issue-number>` run
  against a real issue number prints a verdict and its cited evidence
  (matched keywords or override tag), never a bare boolean.
