---
issue: 3019
role: adversarial-review-9069221f
author: adversarial-review-9069221f
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3035, the subject deliverable for issue #3019
code_under_review:
  - path: tests/test_skill_candidates_floor.py
    sha: 463d963479336dafe865ae125f9811c5110594df
type: test
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: PR #3035 (issue-3019/test-derivation+silent-failure-audit-20ea9371)
    sha: 463d963479336dafe865ae125f9811c5110594df
---

# issue-3019 — adversarial-review-9069221f record

## What was done

Independent verification of PR #3035 against issue #3019's acceptance
checks and must-not list. canonical: `gh pr view 3035 --json
headRefOid,mergeable,commits` (this session) —
`headRefOid:463d963479336dafe865ae125f9811c5110594df`,
`mergeable:MERGEABLE`, single commit. Fetched the PR head into an
isolated worktree — derived: `git fetch origin
pull/3035/head:pr-3035-verify && git worktree add /tmp/verify-pr-3035
pr-3035-verify` (this session) — and re-ran both acceptance checks
myself, audited the diff against the issue's three must-nots, and
specifically re-tested the divergence detector against the real live
divergence issue #2982's own two headline queries currently exhibit on
today's corpus — not merely trusting the PR's claimed test-plan output.

acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` (this session, isolated worktree, PR head `463d9634`) — result:
```
.....                                                                    [100%]
5 passed in 0.97s
```

acceptance: `python3 -m pytest tests/ -k pinned_fixture_divergence -q` (this session, isolated worktree, PR head `463d9634`) — result:
```
.                                                                        [100%]
=============================== warnings summary ===============================
tests/test_skill_candidates_floor.py::SkillCandidatesPinnedFixtureDivergenceTest::test_pinned_fixture_divergence_from_live_scoring_is_reported
  UserWarning: pinned-fixture-divergence (issue #3019): task='rewrite the
  workspace preservation predicate in lifecycle.py from git-status-based
  to what-would-be-lost ...' pinned_outcome='no-candidates'
  live_outcome='bm25-only' live_top={'name': 'agent-coordination',
  'score': 15.134316351480953, ...}
tests/test_skill_candidates_floor.py::SkillCandidatesPinnedFixtureDivergenceTest::test_pinned_fixture_divergence_from_live_scoring_is_reported
  UserWarning: pinned-fixture-divergence (issue #3019): task='remove the
  200-turn session cap, ...' pinned_outcome='no-candidates'
  live_outcome='bm25-only' live_top={'name':
  'secure-coding-session-authentication', 'score': 7.911048066340095, ...}
1 passed, 2 warnings in 0.99s
```

Both queries diverge live today (score above the 4.0 floor, outcome
`bm25-only` not `no-candidates`), reproducing issue #2982's own headline
case, and the divergence is visibly printed in the warnings summary even
under `-q` — not silent, not gated. derived: this session's own two
`acceptance:` runs immediately above are the evidence — the mechanism
surfaced the real divergence sitting in the repo right now, not merely a
test asserting it would.

Also ran the full file — acceptance: `python3 -m pytest
tests/test_skill_candidates_floor.py -q` (this session, same worktree) —
result:
```
............                                                            [100%]
12 passed, 2 warnings in 0.92s
```

Must-not audit, against the merge-base — derived: `git diff
5f83399d..HEAD --stat` (this session, same worktree) — result:
```
 docs/issue-3019/reports/test-derivation+silent-failure-audit-20ea9371.md | 221 +++++++++++++++++++++
 tests/test_skill_candidates_floor.py                                    |  89 ++++++++-
 2 files changed, 305 insertions(+), 5 deletions(-)
```
confirms PR #3035's own commit touches exactly two files: the test file
under review and its own record file (untracked on this
issue-3019/adversarial-review-9069221f branch — derived: `git cat-file
-e HEAD:docs/issue-3019/reports/test-derivation+silent-failure-audit-20ea9371.md`
this session, on this branch, exit 128 "Not a valid object name"; read
directly instead via `git show
463d9634:docs/issue-3019/reports/test-derivation+silent-failure-audit-20ea9371.md`
in the isolated worktree this session). Separately, derived: `git diff
main..HEAD --stat` (this session, same worktree) showed two additional
files touched (`docs/issue-2978/reports/merge-gates-a0186a52.md` — which
does exist on this branch, canonical: `git cat-file -e
HEAD:docs/issue-2978/reports/merge-gates-a0186a52.md` this session, exit
0 — and a deleted deviation-log file under that same report's
directory), but derived: `git log --oneline main..HEAD` (this session,
same worktree) showed zero commits while `git log --oneline HEAD..main`
showed one commit (`a6b5ecdb`, an unrelated issue-2978 change) —
confirming PR #3035's branch is one commit behind current `main` and
those two extra files are a stale-base diff artifact, not something PR
#3035's own commit introduces. `gh pr view 3035 --json mergeable`
(canonical, cited above) reports `MERGEABLE`, so this resolves cleanly
on merge.

- **Pinned regression cases not deleted**: derived: `git diff
  main..HEAD -- tests/test_skill_candidates_floor.py` (this session,
  same worktree), filtered for `assertEqual|mock\.patch|REAL_POSITIVE|DEGENERATE`,
  shows only `+` (addition) lines, no `-` (removal) lines — all 5
  pre-existing test methods across `SkillCandidatesFloorTest` /
  `SkillCandidatesFloorCalibratedTest` /
  `SkillCandidatesFloorKnownLimitationTest` /
  `SkillCandidatesRegressionCasesTest` are byte-unchanged; the diff adds
  only a docstring block to `SkillCandidatesRegressionCasesTest` and a
  new class `SkillCandidatesPinnedFixtureDivergenceTest` appended after
  it. Satisfied.
- **Not converted to live-corpus assertions**: canonical:
  `tests/test_skill_candidates_floor.py:282-347` (read directly in the
  worktree this session) — `SkillCandidatesPinnedFixtureDivergenceTest`
  contains zero `self.assertX` calls against the live result; it
  compares `live["outcome"]` to the pinned value in plain Python and
  calls `warnings.warn(...)` on mismatch only, never
  `self.fail`/`assertEqual`. Confirmed empirically by this session's own
  `pinned_fixture_divergence` run above: the test passes (exit 0) even
  though both cases diverge live today. It cannot break as the corpus
  grows because nothing about corpus drift can fail it. Satisfied.
- **Floor value not changed**: derived: `grep -n
  "_SKILL_CANDIDATES_RELEVANCE_FLOOR" consult.py spawn.py` (this
  session, same worktree) — the floor is still defined in `consult.py`
  and re-exported in `spawn.py`, and the merge-base diff above lists
  only the two files noted (neither `consult.py` nor `spawn.py`).
  Satisfied.

## Why

The task asked me not to trust the PR's claimed results and to test the
divergence detector for real against a genuine live divergence — issue
#2982's own two headline queries, which score above the shipped 4.0
floor and are no longer suppressed on today's corpus (per issue #3019's
body, itself citing PR #3015's finding). canonical:
`docs/issue-2982/reports/adversarial-review-e63d3cd4.md:146-171` (read
directly in the worktree this session, at the sha `b0efb53a` cited by
PR #3035's own record) — quotes the derived CLI reproductions
`{"name": "agent-coordination", "score": 15.134316351480953, ...}
"outcome": "bm25-only"` and `{"name":
"secure-coding-session-authentication", "score": 7.911048066340095,
...} "outcome": "bm25-only"`, and states "Both score above the 4.0
floor and both remain `bm25-only`". I reproduced that live divergence
independently by running the pytest check in a freshly fetched worktree
rather than reading the PR's Test Plan section (acceptance run under
"What was done" above), and the two `UserWarning`s that fired there
match those scores, and also match the pre-existing
`SkillCandidatesFloorKnownLimitationTest.MID_BAND_PLAUSIBLE_BUT_WRONG_SCORES`
fixture — canonical: `tests/test_skill_candidates_floor.py:165-167`
(read directly in the worktree this session):
```
    MID_BAND_PLAUSIBLE_BUT_WRONG_SCORES = [
        7.911048066340095,    # top1=secure-coding-session-authentication (off-topic probe)
        15.134316351480955,   # top1=agent-coordination (off-topic probe)
    ]
```
— cross-corroborating that this is the same known, real divergence, not
a fabricated or cherry-picked warning.

I also applied test-depth-audit to the one new test method. canonical:
`tests/test_skill_candidates_floor.py:327-347` (read directly in the
worktree this session) — by the audit's strict taxonomy it is
**Execution-Only**: it contains no `self.assertX` call, and derived:
`cat pytest.ini` (this session, same worktree) confirms no
`filterwarnings` key exists, so it can never fail on divergence by
design, only ever on an exception from `spawn.rank_skills` itself.
Ordinarily EO classification is a defect (a test that can't catch a
logic error is decorative). Here it is not misclassified as a
correctness test — the issue's own acceptance criteria explicitly wants
a non-gating surfacing mechanism (the issue's second acceptance bullet's
own "empty state: no divergence reports nothing; passes" line states
the pass-either-way contract), so EO-by-taxonomy is the intended shape,
not an accidental one. What matters is whether the non-assertion path
(the `warnings.warn` call) is reachable and visible under real
divergence, which this session verified directly (acceptance run under
"What was done" above) rather than trusting the PR's Test Plan claim of
"1 passed, 2 warnings": the warnings summary printed in full under `-q`
in this session's own run, so a CI log or terminal reader sees the
divergence even though the exit code stays 0. A residual, non-blocking
risk: any consumer that checks only the pytest exit code (rather than
reading output) would still miss it — the issue's acceptance bar is
"detectable," which this session's own reproduction satisfies, not
"gates the merge," which the issue explicitly excludes as #3018's
territory.

One accuracy nit, not a functional defect: the new class's own comment
and the PR's record overstate the replay's fidelity. canonical:
`tests/test_skill_candidates_floor.py:314-315` (read directly in the
worktree this session) — "Same two task descriptions, and the same
pinned `outcome`, as `SkillCandidatesRegressionCasesTest` above" — but
the `PINNED_CASES` task strings at
`tests/test_skill_candidates_floor.py:317-323` are not byte-identical to
`SkillCandidatesRegressionCasesTest`'s own mocked-call task strings at
`tests/test_skill_candidates_floor.py:222-223,237-238`; the divergence
test's strings are longer, carrying extra clauses ("— unpushed commits,
stash, merge/rebase state, untracked classification via git
check-ignore" and "reusing trajectory_analyzer"). Checked against
canonical: `docs/issue-2982/reports/adversarial-review-e63d3cd4.md:146-160`
(same file/sha as above) — the longer strings are verbatim the actual
CLI queries PR #3015 ran (`$ python3 spawn.py --skill-candidates "..."`),
i.e. the real issue #2982 headline queries; the shorter strings in
`SkillCandidatesRegressionCasesTest` were already an abbreviated
paraphrase before this PR (pre-existing, untouched by this diff, per the
must-not audit above). So the new test in fact replays the more
faithful, real-world query text — the "same as above" wording is
imprecise, not the underlying mechanism. Not worth blocking on: the live
scores it produced (`15.134316351480953`, `7.911048066340095`, from
this session's own acceptance run above) match the upstream finding and
the pre-existing known-limitation fixture to the last meaningful digit,
so whichever string is used, the reproduction is faithful to the real
system.

## Upstream basis

- PR #3035 (`463d963479336dafe865ae125f9811c5110594df`, fetched into an
  isolated worktree this session via `git fetch origin
  pull/3035/head:pr-3035-verify && git worktree add
  /tmp/verify-pr-3035 pr-3035-verify`) — the deliverable under
  verification.
- `docs/issue-2982/reports/adversarial-review-e63d3cd4.md:146-171`
  (read this session, at sha `b0efb53a` — the sha cited by PR #3035's
  own record, which is untracked on this
  issue-3019/adversarial-review-9069221f branch and was read via `git
  show 463d9634:docs/issue-3019/reports/test-derivation+silent-failure-audit-20ea9371.md`
  in the isolated worktree this session) — PR #3015's finding that both
  headline queries diverge live; cross-checked against this session's
  own independently-run pytest output above.
- canonical: `gh issue view 2982 --json createdAt` (this session) —
  `{"createdAt":"2026-09-01T03:40:29Z"}`, confirms the capture timestamp
  the PR's new docstring states, independently of the PR's own claim.
- canonical: `gh pr view 3035 --json headRefOid,mergeable,commits` (this
  session) — head sha, single commit, `mergeable: MERGEABLE`.

## Open findings

None blocking. One non-blocking accuracy nit (see "Why" above,
canonical: `tests/test_skill_candidates_floor.py:314-323` this session):
the new test's docstring/comment claims byte-identical task-text replay
of `SkillCandidatesRegressionCasesTest`'s pinned queries; the strings
actually differ (the new test uses the longer, more faithful original
issue #2982 CLI query text, per
`docs/issue-2982/reports/adversarial-review-e63d3cd4.md:146-160` cited
above). No resolution path needed — the mechanism itself works
correctly and the live scores corroborate against two independent
upstream sources (this session's own acceptance runs above), so this is
a wording correction, not a re-open.

## Next steps

None — `loop_state: landed`. acceptance: `python3 -m pytest tests/ -k
skill_candidates_regression_cases -q` (this session, isolated worktree,
PR head `463d9634`) — result: `5 passed in 0.97s` (full transcript under
"What was done" above). acceptance: `python3 -m pytest tests/ -k
pinned_fixture_divergence -q` (this session, same worktree) — result:
`1 passed, 2 warnings in 0.99s`, with both `UserWarning`s printed in the
warnings summary (full transcript under "What was done" above) — both
acceptance checks pass independently in a freshly fetched worktree; the
must-not list (no deletion of pinned cases, no live-corpus assertions,
no floor-value change — all three audited under "What was done" above,
each with its own `derived:`/`canonical:` citation) is satisfied by
direct diff audit; and the divergence detector was confirmed, by this
session's own direct execution captured in the two `acceptance:`
transcripts above, to actually surface — not silently pass over — the
real, current divergence in issue #2982's own two headline queries.

skill-verdict: adversarial-review — applied: invoked; used the skill's
blindness-to-self-report principle to structure this verification as an
independent re-derivation (fresh worktree, own pytest runs, own diff
audit) rather than reading and trusting PR #3035's Test Plan section or
its linked record, per this session's assigned task.
skill-verdict: test-depth-audit — applied: invoked; classified the new
`test_pinned_fixture_divergence_from_live_scoring_is_reported` method
per Step 2's taxonomy (Execution-Only, since it has no `self.assertX`
call) and reasoned in "Why" above about why that classification is the
intended shape here rather than a defect, given the issue's own
acceptance contract explicitly wants a non-gating surfacing mechanism.
other mounted skills: verify-finding-record not-applicable — this
verification lands in an adversarial-review record, not
docs/issue-<n>/reports/defect-verification/, which is that skill's
specific file-location trigger. defect-verification-independence-from-upstream-verdicts
not-applicable — that skill's trigger is re-verifying a review's
"Present"/closed_checks verdict on a requirement; this session verifies
a PR deliverable directly against the issue's own acceptance checks, not
a prior review's verdict on a requirement. pricing-verdict-report
not-applicable — no pricing method or numbers involved. work-in-english
was followed by default (all work and this record are in English)
without a formal Skill-tool invocation.
