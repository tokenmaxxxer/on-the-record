---
subject: issue-2012/implementation (HEAD f310a254, origin/issue-2012/implementation)
issue: 2012
reviewer: conformance-review (issue-2012/conformance-review)
reviewed: 2026-08-22
overall_verdict: pass (8/8 requirements Present; 1 documentation-only Incorrect finding, does not affect classifier behavior)
---

# Conformance review — issue #2012 (design-bearing issue classifier)

Spec basis: `gh issue view 2012` Acceptance section (canonical, read this
session). Subject: `origin/issue-2012/implementation` @ f310a254, diffed
against `origin/main` (merge-base e282b4cc).

## Requirement list (extracted per conformance-review-requirement-extraction)

- R1 (functional): a function/CLI (`spawn.py` or `gates/`) classifies an issue body as design-bearing or not.
- R2 (functional): the classifier returns verdict + cited evidence (which signals fired).
- R3 (scope-boundary): the classifier is replayed against the existing corpus of landed issues.
- R4 (functional): known design-bearing exemplars (webfolio landing page, brand SVG, k8s platform design) are marked design-bearing.
- R5 (functional): known mechanical exemplars (changelog fix, flag wiring) are marked not design-bearing.
- R6 (edge-case, precision-first per issue's stated hazard): zero false positives on the mechanical set.
- R7 (error-handling/test-coverage): unit tests cover both classes (design-bearing and mechanical).
- R8 (edge-case/test-coverage): unit tests cover the override path.

---
requirement: R1 — a function/CLI classifies an issue body as design-bearing or not
spec_ref: issue #2012, Acceptance, clause 1 ("a function/CLI (`spawn.py` or `gates/`) classifies an issue body as design-bearing or not")
verdict: Present
evidence: gates/design_bearing_classifier.py:79-91 (`check_issue_body`), gates/design_bearing_classifier.py:94-99 (`check`), gates/design_bearing_classifier.py:102-114 (`main`, CLI entry point)
rationale: method=inspection+demonstration. `check_issue_body` is a pure function taking issue body text and returning a `Verdict` TypedDict; `main()` wires it to a CLI (`python3 gates/design_bearing_classifier.py <issue-number>`). Live-ran `python3 gates/design_bearing_classifier.py 1975` in a worktree checkout of the branch — output `design_bearing=False override=False evidence=[]`, matching the implementation record's own cited acceptance line.
---

---
requirement: R2 — classifier returns verdict + cited evidence (which signals fired)
spec_ref: issue #2012, Acceptance, clause 1 ("returning verdict + cited evidence (which signals fired)")
verdict: Present
evidence: gates/design_bearing_classifier.py:70-77 (`_design_bearing_score` returns `(overlap, matched)` where `matched` is the sorted list of design-signal keywords found), gates/design_bearing_classifier.py:88-91 (`evidence: matched` in the returned `Verdict`)
rationale: method=inspection+test. Every code path returns a non-empty, specific evidence list (matched keywords, or the override tag string) rather than a bare boolean; test/test_design_bearing_classifier.py asserts exact evidence sets per corpus row (e.g. `{"architecture", "demo"}` for #1596).
---

---
requirement: R3 — replayed against the existing corpus of landed issues
spec_ref: issue #2012, Acceptance, clause 2 ("replayed against the existing corpus of landed issues")
verdict: Present
evidence: docs/issue-2012/reports/implementation/corpus.md (mechanical rows: real issues #1975, #1635, #1596, #1742), test/test_design_bearing_classifier.py `MechanicalCorpusTest` (4 test methods, one per real issue, bodies fetched live per the corpus doc)
rationale: method=inspection+test. The mechanical side of the corpus uses this repo's own real, already-landed issues rather than constructed fixtures, satisfying "existing corpus of landed issues" for the mechanical class; the design-bearing side additionally includes one real consumer-repo issue (tokenmaxxxer/tm-webfolio#1) per the operator's phase-2 amendment recorded in docs/issue-2012/reports/implementation.md.
---

---
requirement: R4 — known design-bearing exemplars marked design-bearing
spec_ref: issue #2012, Acceptance, clause 2 ("known design-bearing exemplars (e.g. webfolio landing page, brand SVG, k8s platform design) as design-bearing")
verdict: Present
evidence: test/test_design_bearing_classifier.py `DesignBearingCorpusTest` (fixture_a landing-page, fixture_b brand/SVG identity, fixture_c k8s platform topology, plus the real tm-webfolio#1 exemplar) — all 4 assert `design_bearing is True` and non-empty evidence
rationale: method=test (live-ran). Re-ran the full suite in a clean worktree checkout of `origin/issue-2012/implementation`: `python3 -m pytest -q test/test_design_bearing_classifier.py gates/test_design_bearing_classifier_live_fire.py` — 16 passed, including all four design-bearing-corpus rows and the live-fire landing-page scenario.
---

---
requirement: R5 — known mechanical exemplars marked not design-bearing
spec_ref: issue #2012, Acceptance, clause 2 ("known mechanical exemplars (e.g. changelog fix, flag wiring) as not")
verdict: Present
evidence: test/test_design_bearing_classifier.py `MechanicalCorpusTest` (issue #1975 watcher rearm, #1635 record_enums bucketed-enum FP, #1596 record-lint-violation, #1742 skills-mount phase 1) — all 4 assert `design_bearing is False`
rationale: method=test (live-ran, same run cited under R4). All four real mechanical rows classify False as required.
---

---
requirement: R6 — zero false positives on the mechanical set (precision-first)
spec_ref: issue #2012, Acceptance, clause 2 ("with zero false positives on the mechanical set") + issue body's own stated hazard ("a mechanical issue wrongly tagged design-bearing would re-inflate the session cost we just cut")
verdict: Present
evidence: gates/design_bearing_classifier.py:64 (`_DESIGN_BEARING_MIN_OVERLAP = 3`); test/test_design_bearing_classifier.py `MechanicalCorpusTest` — all 4 real mechanical rows assert `design_bearing is False`; live worktree run confirms 0 failures
rationale: method=test+analysis. Independently recomputed `_design_bearing_score` for the two highest-scoring mechanical rows (#1596, #1742) in a live Python session against the module as shipped: both score overlap=2, which is `< _DESIGN_BEARING_MIN_OVERLAP = 3`, so both correctly classify False. Zero false positives confirmed on this corpus by direct re-derivation, not just by trusting the test's own assertions.
---

---
requirement: R7 — unit tests cover both classes
spec_ref: issue #2012, Acceptance, clause 3 ("unit tests cover both classes and the override path")
verdict: Present
evidence: test/test_design_bearing_classifier.py `MechanicalCorpusTest` (4 tests, mechanical class) and `DesignBearingCorpusTest` (4 tests, design-bearing class), plus `TokenizeTest`/`DesignBearingScoreTest` for the scoring primitives
rationale: method=test. Both classes have dedicated test classes with real/constructed exemplars each; live run confirms all pass.
---

---
requirement: R8 — unit tests cover the override path
spec_ref: issue #2012, Acceptance, clause 3 ("unit tests cover ... the override path")
verdict: Present
evidence: test/test_design_bearing_classifier.py `OverridePathTest` (`test_override_yes_forces_design_bearing_on_mechanical_shaped_body`, `test_override_no_forces_not_design_bearing_on_design_shaped_body`); gates/design_bearing_classifier.py:53-58 (`_OVERRIDE_YES`/`_OVERRIDE_NO` regexes), :83-87 (override short-circuit in `check_issue_body`)
rationale: method=test. Both override directions are tested, each on a body shaped like the opposite class (override=yes on a mechanical-shaped body, override=no on a design-bearing-shaped body), confirming the override actually overrides rather than just agreeing with the score.
---

---
requirement: additional finding — corpus.md "Threshold calibration" section evidence accuracy
spec_ref: docs/issue-2012/reports/implementation/corpus.md, "Threshold calibration" section (last section of the file)
verdict: Incorrect
evidence: docs/issue-2012/reports/implementation/corpus.md, "Threshold calibration" section states "the mechanical set tops out at overlap 1 (#1596)"; the same file's own earlier per-row sections state #1596 and #1742 each score overlap 2 (`architecture`+`demo`, `identity`+`layout`). Independently re-derived live via `dbc._design_bearing_score(...)` against gates/design_bearing_classifier.py in a worktree checkout of the branch: both #1596 and #1742 return `(2, [...])`, confirming the earlier per-row sections (overlap 2) are correct and the calibration-section sentence (overlap 1) is wrong.
spec_vs_built: the corpus document is supposed to state the actual measured overlap for its own calibration rationale ("the mechanical set tops out at overlap 1"); the true, re-derived value (and the value stated two sections earlier in the same document) is 2.
rationale: this is a documentation-accuracy defect in the supporting corpus report, not a classifier-behavior defect — the shipped threshold (`_DESIGN_BEARING_MIN_OVERLAP = 3`) is still correct and still clears the mechanical set at zero false positives regardless of whether the true ceiling is 1 or 2, so R6 is unaffected. Flagged because the calibration section is the evidentiary basis a future threshold-tuning change would rely on, and a wrong ceiling figure there could mislead that future change (e.g. someone lowering the threshold to 2 believing the mechanical ceiling is 1, which would actually introduce false positives at #1596/#1742).
---

## Merge-readiness note (not a requirement verdict)

`origin/issue-2012/implementation` branched from `e282b4cc`, before
`issue-2016 phase 1` (`25fefd45`) and `issue-2012 phase 1` (`76647a38`)
landed on `origin/main`. A direct diff (`git diff origin/main..
origin/issue-2012/implementation`) therefore shows two files deleted —
`docs/issue-2016/proposals/2026-08-22-single-session-profiling.md` and
`docs/issue-2016/reports/performance-engineering/survey.md` — that are
real, already-landed issue-2016 artifacts on `main`, untouched by any
commit on this branch. This is branch staleness, not an intentional
deletion by the issue-2012 work: `git log --oneline --all -- docs/
issue-2016/*` shows those paths were never touched by any commit on
`issue-2012/implementation`. Flagged so the landing step rebases/merges
issue-2012/implementation onto current `main` (not a raw diff-and-apply)
before this PR merges, so those two files are not lost.
