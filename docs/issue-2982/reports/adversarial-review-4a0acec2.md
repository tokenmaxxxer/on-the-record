---
issue: 2982
role: adversarial-review-4a0acec2
author: adversarial-review-4a0acec2
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: PR #3003 (issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284)
    sha: 084dbe8c4b7da8d885cad36165247e3bfbb9a42d
  - path: docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md
    sha: 084dbe8c4b7da8d885cad36165247e3bfbb9a42d
  - path: consult.py (rank_skills(), _SKILL_CANDIDATES_RELEVANCE_FLOOR)
    sha: 084dbe8c4b7da8d885cad36165247e3bfbb9a42d
---

# issue-2982 — adversarial-review-4a0acec2 record

## What was done

Independently verified PR #3003 (`issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284`,
head `084dbe8c4b7da8d885cad36165247e3bfbb9a42d`) against issue #2982's acceptance
checks and must-not list, from an isolated git worktree
(`git worktree add /tmp/pr3003-verify 084dbe8c4b7da8d885cad36165247e3bfbb9a42d`),
original checkout on `issue-2982/adversarial-review-4a0acec2` confirmed
untouched throughout via `git status`.

canonical: this turn's own delegated evidence-gathering transcript (Agent
tool call, subagent_type freelunch:freelunch-worker, foreground/consumed
this turn) — full command outputs pasted verbatim below.

**Acceptance checks — reproduced live in the worktree:**
- checked: `python3 -m pytest tests/ -k skill_candidates_floor -q` — result:
  ```
  .......                                                                  [100%]
  7 passed in 0.98s
  ```
- checked: `python3 -m pytest tests/ -k skill_candidates_floor_calibrated -q` — result:
  ```
  ..                                                                       [100%]
  2 passed in 0.85s
  ```
- checked: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
  ```
  ..                                                                       [100%]
  2 passed in 0.85s
  ```
- checked: `python3 -m pytest test/test_skill_candidates_ranking.py -q`
  (pre-existing suite, touched by the PR to neutralize the new floor via
  `mock.patch.object(spawn, "_SKILL_CANDIDATES_RELEVANCE_FLOOR", 0.0)` for
  its tiny synthetic 2-skill corpus, see
  `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:test/test_skill_candidates_ranking.py`
  lines 53-65 and 124-129) — result: all passed, no failures observed in
  the transcript.

**Must-not audit (issue #2982's explicit list), each checked against the
diff (`git diff origin/main...084dbe8c4b7da8d885cad36165247e3bfbb9a42d`),
not the PR description's claim:**

1. **Haiku judge NOT made the default fix.** `rank_skills()`'s
   `use_judge: bool = False` default is pre-existing and unchanged by this
   diff — checked: the diff hunk touching `consult.py` shows only new
   lines added inside/around the existing function, no change to the
   `def rank_skills(..., use_judge: bool = False, ...)` signature line.
   The floor check is nested inside `if not use_judge:` — canonical:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:consult.py:880-887`:
   ```python
       if not use_judge:
           if scored[0][0] < _sp._SKILL_CANDIDATES_RELEVANCE_FLOOR:
               return {"ranked": [], "outcome": "no-candidates", "picked": []}
           return {"ranked": ranked, "outcome": "bm25-only", "picked": []}
       picked_dirs, outcome = _sp._cross_family_skill_matches_with_consult(
   ```
   checked: the calibration test suite includes a dedicated
   judge-path-unaffected case — result: passed (part of the 7-passed run
   above); canonical:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:tests/test_skill_candidates_floor.py`
   (`SkillCandidatesFloorTest`, third method) mocks a below-floor score
   with `use_judge=True` and asserts `result["outcome"] != "no-candidates"`.

2. **Floor NOT freehand — derivation present, but scope-limited.** A
   derivation exists at
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`
   (canonical: full 411-line file read this turn). It reports 7 positive
   task/skill pairs and 6 negative pairs; derived:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:tests/test_skill_candidates_floor.py`
   `SkillCandidatesFloorCalibratedTest.POSITIVE_TOP1_SCORES` /
   `NEGATIVE_TOP1_SCORES` module constants, which embed the same 7 and 6
   scores as the derivation doc and are exercised by the calibration test
   asserting `min(POSITIVE_TOP1_SCORES) > floor > max(NEGATIVE_TOP1_SCORES)`
   (part of the 2-passed `skill_candidates_floor_calibrated` run above).
   Two earlier attempts (real issue-title/body text as query) are
   disclosed in the doc as abandoned for not separating cleanly. This
   satisfies the must-not's letter (16.0 is inside a measured gap, not
   picked freehand). **Whether it satisfies the must-not's purpose is a
   separate question — see "Open findings" below, where this review
   independently probed for and reproduced the floor-too-high failure
   mode the issue asked to be checked for.**

3. **`--skill-candidates` must not select skills on the operator's
   behalf.** checked: the CLI handler — canonical:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:spawn.py:2462-2483`:
   ```python
       if a.skill_candidates:
           ...
           result = rank_skills(task_text, skill="candidates", ...)
           print(json.dumps({"task": task_text, "issue": a.issue, **result},
                            indent=2, ensure_ascii=False))
           return 0
   ```
   only calls `rank_skills(...)` then prints and returns — no downstream
   mount/spawn call in that branch. This behavior (print-only) is
   unchanged by this PR's diff, which touches only the one-line constant
   re-export in `spawn.py` (see diff `--stat` in "Upstream basis" below).

4. **spawn's own internal cross-family mount must be unchanged.**
   checked: `grep -n "rank_skills(" **/*.py` in the worktree (run by the
   delegated worker) found no call site outside the `--skill-candidates`
   CLI branch and its own module-level re-export line. The real-spawn
   mount path,
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:consult.py:637`
   (`_cross_family_skill_matches_with_consult`, called from
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:spawn.py:3874`), and
   `directive_assembly.py`'s `_cross_family_skill_matches()` both call
   `_bm25_cross_family_scores()` directly, bypassing `rank_skills()` and
   therefore the new floor entirely.

**Regression cases — checked two ways:**
- Locked-in unit fixtures: checked: the two regression-case test methods
  in `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:tests/test_skill_candidates_floor.py`
  (`SkillCandidatesRegressionCasesTest`, workspace-preservation-task and
  turn-cap-task methods) — result: both passed (part of the 2-passed
  `skill_candidates_regression_cases` run above). Those tests mock
  `_bm25_cross_family_scores` to return the issue's originally-reported
  scores verbatim:
  ```python
  scored = [(0.4325, "market-analysis-competitor-mapping", d, "skill-repo"),
            (0.4325, "growth-analytics-north-star", d, "skill-repo"),
            (0.4202, "conformance-review-traceability-and-evidence", d, "skill-repo")]
  ```
  and
  ```python
  scored = [(1.3324, "tech-feasibility", d, "skill-repo"),
            (1.3324, "usability-eval", d, "skill-repo"),
            (1.3066, "compliance-scan", d, "skill-repo")]
  ```
  (the same numbers quoted in the issue body itself, reproduced unchanged
  in the test source) and assert `outcome == "no-candidates"`,
  `ranked == []`.
- Live, un-mocked reproduction against the real corpus — checked:
  `python3 spawn.py --skill-candidates "<task text copied verbatim from
  the issue body>"` for both tasks — result:
  ```
  {"ranked": [], "outcome": "no-candidates", "picked": []}
  ```
  for both, independent of the mocked test.

**Floor-too-high probe (issue explicitly asked this review to check this
direction).** checked: 12 plain-English task prompts run against the live
corpus via the delegated worker's direct calls to
`_bm25_cross_family_scores()` (raw top-1) compared against `rank_skills()`'s
outcome for the same prompt — full transcript is this turn's Agent-tool
result (canonical, quoted verbatim below). Two are load-bearing
counterexamples:

- `"check whether this test suite actually covers the requirements or
  just looks like it does"` — checked: raw top-1
  `(11.458521808745413, 'test-depth-audit')` — derived: worker's
  corpus-scan command, result quoted verbatim from the transcript:
  ```
  expected skill present in corpus scan: True | score if present:
  [(11.458521808745413, 'test-depth-audit')] | rank of expected
  (1-indexed) among scored: 1 of 271
  ```
  i.e. the single best match in the whole corpus, not a near-tie.
  `11.458... < 16.0`, so `rank_skills()` returns `no-candidates`,
  discarding the correct match.
- `"tag and file this note into the knowledge base taxonomy"` — checked:
  raw top-1 `(13.869986173094503, 'knowledge-management-taxonomy-tagging')`
  — derived: same corpus-membership scan command, result quoted verbatim:
  ```
  rank of expected (1-indexed) among scored: 1 of 192
  ```
  `13.869... < 16.0`, same suppression.

Two other probed prompts ("do a security review of the pending changes on
this branch", "code review this diff for correctness bugs and
simplification opportunities") also fell below the floor, but derived:
the worker's corpus scan reported `expected skill present in corpus scan:
False` for both (no skill literally named `security-review` or
`code-review` exists in this repo's skill corpus) — pre-existing recall
gaps unrelated to the floor, not counted as findings here.

## Why

The issue explicitly asked this review to scrutinize whether the claimed
derivation actually supports the number, and to probe specifically for
the floor-too-high failure direction, because an uncalibrated-in-practice
floor "silently filters out correct candidates" — the same failure the
PR's own derivation doc and issue #2961's backstop-threshold discipline
both warn against. Taking the derivation doc's numbers at face value
without an independent probe would have missed exactly this: the doc's
positive set is constructed from sentences the author wrote and kept only
after confirming they scored above threshold (`assert
top1["name"] == expect` gates each one into the positive set before its
score is banked — canonical:
`084dbe8c4b7da8d885cad36165247e3bfbb9a42d:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`,
"What worked" subsection), which measures how high deliberately dense,
pre-vetted sentences score rather than how high the correct-topic
sentences an operator would actually type score. The two abandoned
attempts logged in that same doc (real issue text, and issue-title-only)
are the author's own evidence that real operator phrasing does not
separate cleanly at any single threshold; the pivot to hand-written
positives sidesteps that finding rather than resolving it. The two
counterexamples found here (see "What was done" above, both cited with
`canonical`/`derived` tags and corpus rank-1 confirmation) are not edge
cases: both are short, plain, single-clause task descriptions naming the
exact action a real skill covers, and both rank #1 in the whole corpus
for their query yet are discarded. That is the concrete, reproduced
manifestation of "a floor set too high silently filters out correct
candidates."

## What did not work

None — no path taken during this review was abandoned or reversed. The
delegated evidence-gathering worker's first false-negative probe attempt
used `security-review`/`code-review` as example "known repo skill
triggers," which turned out not to exist in this corpus. checked: worker
ran a corpus-membership scan (`expected skill present in corpus scan`
command, see "What was done" above) before counting either probe as a
finding — derived: result quoted verbatim there
(`expected skill present in corpus scan: False` for both) — so this is
reported as a non-finding rather than a defect, corrected within the same
pass rather than left standing.

## Upstream basis

- PR #3003, head commit `084dbe8c4b7da8d885cad36165247e3bfbb9a42d` on
  `issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284`
  — checked: `gh pr view 3003 --repo tokenmaxxxer/on-the-record --json
  headRefName,headRefOid` — result:
  `{"headRefName":"issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284","headRefOid":"084dbe8c4b7da8d885cad36165247e3bfbb9a42d"}`,
  then verified via isolated `git worktree add /tmp/pr3003-verify
  084dbe8c4b7da8d885cad36165247e3bfbb9a42d`, not the PR description.
- `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`
  (411 lines, read in full this turn) — the derivation record this review
  audits.
- `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284/hunt-skill-candidates-floor.md`
  (24 lines, read in full this turn) — a prior before-landing warrant-hunt
  on the same PR, verdict "no finding," stance "assume the gate/check is
  bypassable." Consistent with this review: neither found a bypass of the
  floor mechanism itself — this review's finding is about calibration
  coverage (correct candidates suppressed), not a logic bypass of the
  floor check.
- `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:consult.py` (diff:
  `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 16.0` and the
  `if not use_judge: if scored[0][0] < ...` branch in `rank_skills()`),
  `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:spawn.py` (diff: one-line
  re-export of the constant),
  `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:test/test_skill_candidates_ranking.py`
  (diff: floor neutralized to 0.0 for its synthetic corpus),
  `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:tests/test_skill_candidates_floor.py`
  (new, 181 lines, read in full this turn) — derived: `git diff
  origin/main...084dbe8c4b7da8d885cad36165247e3bfbb9a42d --stat` — result:
  ```
  consult.py                                         |  44 +++
  ...nt-taxonomy-tagging+test-derivation-d8949284.md | 411 +++++++++++++++++++++
  .../hunt-skill-candidates-floor.md                 |  24 ++
  spawn.py                                           |   1 +
  test/test_skill_candidates_ranking.py              |  22 +-
  tests/test_skill_candidates_floor.py               | 181 +++++++++
  6 files changed, 682 insertions(+), 1 deletion(-)
  ```

## Open findings

1. **Floor calibration does not generalize to realistic short/plain-English
   queries — confirmed, reproducible** (see "What was done" §
   floor-too-high probe, and "Why" above for the mechanism). derived:
   `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 16.0` (canonical:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:consult.py:96`) suppresses at
   least two genuinely correct, rank-1-in-corpus candidates
   (`test-depth-audit` at 11.458 vs floor 16.0, `knowledge-management-taxonomy-tagging`
   at 13.870 vs floor 16.0 — both quoted with corpus-rank evidence above)
   for short, plain, on-topic task descriptions. The derivation's positive
   set (min score 16.963, canonical:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:tests/test_skill_candidates_floor.py`
   `POSITIVE_TOP1_SCORES`) was built exclusively from hand-written, dense,
   task-shaped sentences vetted to score above threshold, so it does not
   bound the score of shorter or more colloquial correct queries — the
   exact failure mode issue #2982 asked this review to probe for. This
   does not violate the letter of the must-not (a real derivation with
   real numbers exists, it was not picked freehand), but it does not
   satisfy the must-not's underlying purpose: the floor as calibrated
   still discards correct candidates for a plausible, non-adversarial
   class of real invocations. Resolution path: either (a) recalibrate
   using a broader/representative sample of task phrasings, including
   short/plain ones, or (b) if the floor is intentionally scoped to only
   the "task-shaped technical sentence" register, state that scope
   explicitly (e.g. in `--skill-candidates`'s `--help` text) so an
   operator typing a short query knows a `no-candidates` result may be a
   floor artifact rather than genuine absence — left to a follow-up
   session to choose and land.
2. Cosmetic, pre-existing, not new to this PR: `consult.py` and `spawn.py`
   each hold their own module-level copy of
   `_SKILL_CANDIDATES_RELEVANCE_FLOOR`; only `spawn`'s copy is read at
   runtime via `_sp.` inside `rank_skills()` (canonical:
   `084dbe8c4b7da8d885cad36165247e3bfbb9a42d:consult.py:884`, `if
   scored[0][0] < _sp._SKILL_CANDIDATES_RELEVANCE_FLOOR:`), so patching
   `consult`'s copy directly is a no-op. checked: the PR's own hunt record
   (`.../hunt-skill-candidates-floor.md`, cited above) already surfaced
   this and traced it to a pre-existing convention shared by three sibling
   constants in the same file, not something this PR introduced. No
   action needed from this review; noted for completeness only.

## Next steps

None for this record — `loop_state: landed`. Finding 1 in "Open findings"
above is handed off to a follow-up session; the evidence and resolution
path for it are recorded there, not here.

skill-verdict: adversarial-review — applied: invoked; this entire record
is the output of applying the adversarial-review protocol — independent
worktree, no trust in the PR's self-reported results, evidence re-derived
from scratch, and an explicit probe for the failure direction the subject
PR would be least likely to have tested against itself.
other mounted skills: not triggered
