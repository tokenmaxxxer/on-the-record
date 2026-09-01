---
issue: 3019
role: test-derivation+silent-failure-audit-20ea9371
author: test-derivation+silent-failure-audit-20ea9371
skills: test-derivation (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: tests/test_skill_candidates_floor.py
    sha: same-commit
type: test
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: docs/issue-2982/reports/adversarial-review-e63d3cd4.md
    sha: b0efb53aaa9e594c5002d894b8e74d2f5749caa3
---

# issue-3019 — test-derivation+silent-failure-audit-20ea9371 record

## What was done

Two changes to `tests/test_skill_candidates_floor.py` (only file touched
this session), build-now bypass (`CORE_BUILD_NOW=1`; delivered directly,
no phase-1 proposal round):

1. **`SkillCandidatesRegressionCasesTest`'s docstring** now states, in an
   explicit "PINNED, NOT LIVE" block, that every score in the class is a
   frozen snapshot captured `2026-09-01T03:40:29Z`
   (canonical: `gh issue view 2982 --json createdAt` — this session —
   `{"createdAt":"2026-09-01T03:40:29Z"}`), and that a green result there
   is a claim about that snapshot, not about live behaviour today. No
   score, no assertion, and no test case in the class changed — only the
   docstring, per the issue's own must-not (do not delete the pinned
   cases, do not convert them to live-corpus assertions, do not touch
   the floor value) — derived: `git diff tests/test_skill_candidates_floor.py`
   (this session) shows only docstring lines added inside
   `SkillCandidatesRegressionCasesTest`; every `REAL_POSITIVE_TOP1_SCORES`
   / `DOCUMENTED_DEGENERATE_NEGATIVE_SCORES` / regression-case score and
   every `assertEqual` in that class and in
   `SkillCandidatesFloorCalibratedTest` is byte-unchanged.

2. **New `SkillCandidatesPinnedFixtureDivergenceTest`** class, one test
   method (`test_pinned_fixture_divergence_from_live_scoring_is_reported`),
   replaying the same two pinned task descriptions
   (`SkillCandidatesRegressionCasesTest`'s workspace-preservation and
   turn-cap queries) through the real, unmocked
   `spawn._bm25_cross_family_scores` — via `spawn.rank_skills(...,
   skill="candidates", repo_root=spawn._skill_repo_root(), home=Path.home(),
   target_repo_root=Path(cwd))`, the same argument shape
   `spawn.py --skill-candidates` itself passes (derived:
   `grep -n "skill=\"candidates\"" spawn.py` — this session —
   `spawn.py:2514`, immediately followed by
   `repo_root=_skill_repo_root(), issue=a.issue, cwd=a.cwd,
   home=Path.home(), target_repo_root=Path(a.cwd)` at `spawn.py:2515-2517`),
   so the live scoring reproduced is what an operator running that
   command would see today, not a reduced-corpus approximation. For each
   case whose live `outcome` no longer matches the pinned
   `"no-candidates"` expectation, the test calls `warnings.warn(...)`
   with the task text, pinned outcome, live outcome, and live top-1
   candidate — visible in pytest's warning summary even under `-q`
   (unlike `print`, which `-q` suppresses for a passing test; canonical:
   pytest docs section cited under "Why" below). No divergence: the loop
   finds nothing to warn about and the test passes with no extra output.
   Either way the test itself always passes — the check reports drift,
   it does not gate on it (issue #3018 owns whether the floor value is
   right; this issue owns only whether drift is visible).

## Why

The issue's own concrete case is that both pinned "must-suppress"
queries now score above the 4.0 floor and rank `bm25-only` on today's
corpus. canonical:
`docs/issue-2982/reports/adversarial-review-e63d3cd4.md:146-171`
(`b0efb53a`, read this session) — quotes both derived CLI reproductions
(`agent-coordination` score 15.134316351480953, and
`secure-coding-session-authentication` score 7.911048066340095, both
`outcome: bm25-only`) and states plainly "Both score above the 4.0 floor
and both remain `bm25-only`". This session independently reproduced the
same divergence live against the current checkout — derived:
`python3 -m pytest tests/ -k pinned_fixture_divergence -q` (this
session, this checkout) — see the full transcript under "Next steps"
below, which shows both queries still warning as diverged today. The
issue is explicit that the mocking itself is not the defect (determinism
against a growing corpus is why the fixture is pinned, and #3018 needs
the fixture intact to detect the opposite-direction regression) — the
defect is that nothing states the pin or its capture time, and nothing
detects when live behaviour has moved away from it.

That maps directly to the two acceptance checks via test-derivation's
Step 3a classification:

| Requirement | A: failure impact | B: complexity | Level | Route (Step 3) |
|---|---|---|---|---|
| State the pin + capture time | no (docstring only, no logic) | no (single statement) | Low | GWT, no technique derivation |
| Detect + surface live drift, don't gate on it | yes — silent loss of a correctness signal is the failure-reports-itself-as-success shape the issue names as this repo's first question | yes (2 conditions: match/diverge, x 2 actions: warn/no-op) | High | decision table |

Low item: one GWT scenario — given the pinned regression class, when a
reader opens its docstring, then it names "pinned" and states the
`2026-09-01T03:40:29Z` capture timestamp (delivered as item 1 above).

High item: routed to a 2-condition decision table — {live outcome
matches pinned | live outcome diverges} x {no-op | warn} — both feasible
rows exercised: today's corpus hits the "diverges -> warn" row for both
pinned queries (derived: `python3 -m pytest tests/ -k
pinned_fixture_divergence -q`, transcript under "Next steps", 2
`UserWarning`s emitted); the "matches -> no-op" row is exercised
structurally by the test's own `if live["outcome"] == pinned_outcome:
continue` branch and documented as the acceptance's own "empty state: no
divergence reports nothing; passes" bullet — not separately covered by a
forced-non-divergent case, since forcing one would require mocking the
live scorer, which collapses back into the pinned-fixture pattern this
test exists to check *against*.

`warnings.warn` was chosen over a hard assertion failure specifically
because the acceptance check itself (`pytest tests/ -k
pinned_fixture_divergence -q`) must pass today per the issue's own
Acceptance list, and today the two queries have diverged (derived above)
— an assertion would fail the very check meant to prove the surfacing
works. `warnings.warn` was chosen over a bare `print` because pytest's
`-q` suppresses captured stdout for a passing test but always renders
the warnings summary regardless of `-q` — canonical:
https://docs.pytest.org/en/stable/how-to/capture-warnings.html (pytest's
own capture-warnings doc, the alternative considered and rejected in
favor of warnings) — confirmed live this session: derived: `python3 -m
pytest tests/ -k pinned_fixture_divergence -q` (transcript under "Next
steps") shows the `warnings summary` section with both messages despite
`-q`. `pytest.ini` carries no `filterwarnings` key at all (derived: `cat
pytest.ini` — this session — only `[pytest]`, `python_functions`,
`norecursedirs`, `addopts`, `markers`), so the warning cannot flip a
pass into a failure by itself.

## What did not work

None.

## Upstream basis

- `docs/issue-2982/reports/adversarial-review-e63d3cd4.md` (`b0efb53a`,
  lines 146-221) — PR #3015's independent finding that the two headline
  queries no longer reproduce their pinned suppression live; the concrete
  case this issue names and this record's divergence test reproduces.
  canonical: file read directly this session at that path/sha.
- `gh issue view 2982` (this session) — `createdAt:
  2026-09-01T03:40:29Z`, the pin timestamp now stated in
  `SkillCandidatesRegressionCasesTest`'s docstring.
- `gh pr view 3015 --repo tokenmaxxxer/on-the-record` (this session) —
  body states verdict "fail" (on substance, not on the three named
  checks) and quotes the same finding text cited above.
- `tests/test_skill_candidates_floor.py` (pre-existing, this session's
  only edited file) — `SkillCandidatesFloorKnownLimitationTest.MID_BAND_PLAUSIBLE_BUT_WRONG_SCORES`
  already hardcodes `7.911048066340095` and `15.134316351480955`
  (canonical: `tests/test_skill_candidates_floor.py:165-167`, this
  checkout, byte-unchanged by this session) — this session's live
  divergence run (derived: `python3 -m pytest tests/ -k
  pinned_fixture_divergence -q`, transcript under "Next steps") confirms
  those are the identical live scores the new test now reproduces for
  the same two queries.

## Open findings

None.

## Next steps

None — `loop_state: landed`. Both acceptance checks executed live this
session, this checkout, HEAD `5f83399d` before this session's own commit:

acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
```
.....                                                                    [100%]
5 passed in 0.99s
```

acceptance: `python3 -m pytest tests/ -k pinned_fixture_divergence -q` — result:
```
.                                                                        [100%]
=============================== warnings summary ===============================
tests/test_skill_candidates_floor.py::SkillCandidatesPinnedFixtureDivergenceTest::test_pinned_fixture_divergence_from_live_scoring_is_reported
  UserWarning: pinned-fixture-divergence (issue #3019): task='rewrite the
  workspace preservation predicate in lifecycle.py from git-status-based
  to what-would-be-lost ...' pinned_outcome='no-candidates'
  live_outcome='bm25-only' live_top={'name': 'agent-coordination',
  'score': 15.134316351480953, ...} -- SkillCandidatesRegressionCasesTest's
  pinned score for this task (captured 2026-09-01T03:40:29Z) no longer
  matches live _bm25_cross_family_scores() behaviour against today's
  corpus.
tests/test_skill_candidates_floor.py::SkillCandidatesPinnedFixtureDivergenceTest::test_pinned_fixture_divergence_from_live_scoring_is_reported
  UserWarning: pinned-fixture-divergence (issue #3019): task='remove the
  200-turn session cap, replace with wall-clock/token backstops and an
  observe-only runaway signal reusing trajectory_analyzer'
  pinned_outcome='no-candidates' live_outcome='bm25-only'
  live_top={'name': 'secure-coding-session-authentication', 'score':
  7.911048066340095, ...} -- ... no longer matches live
  _bm25_cross_family_scores() behaviour against today's corpus.
1 passed, 2 warnings in 1.03s
```

Both pinned queries currently diverge live, confirming the concrete case
the issue names is still present on today's corpus and that the new
test surfaces it (visible warnings, exit code 0). Full file also
reproduced green — derived: `python3 -m pytest
tests/test_skill_candidates_floor.py -q` (this session) — result:
`12 passed, 2 warnings in 0.91s`.

skill-verdict: test-derivation — applied: invoked; used Step 3a's
High/Medium/Low classification to size each of the issue's two
acceptance criteria (Low for the docstring statement, High for the
divergence detector) and Step 3's routing (GWT for the Low item, a
2-row decision table for the High item), per the classification table
and routing paragraphs under "Why" above.
other mounted skills: silent-failure-audit not triggered — this issue's
"silent failure" is a test-fixture staleness problem (a pinned score no
longer describing live behaviour), not error-handling code with
try/catch, Promise rejection, or result-type paths to classify
Handled/Silently-Absorbed/Unreachable; no such code was added or
touched by this change (derived: `git diff --stat` this session shows
only `tests/test_skill_candidates_floor.py`, no error-handling call
sites). work-in-english was not invoked via the Skill tool this session;
its guidance (English in commits/code/docs) was followed by default
throughout without a formal invocation.
