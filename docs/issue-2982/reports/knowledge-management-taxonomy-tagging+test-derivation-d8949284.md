---
issue: 2982
role: knowledge-management-taxonomy-tagging+test-derivation-d8949284
author: knowledge-management-taxonomy-tagging+test-derivation-d8949284
skills: knowledge-management-taxonomy-tagging (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit (consult.py, spawn.py, test/test_skill_candidates_ranking.py, tests/test_skill_candidates_floor.py)
type: fix
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: consult.py (rank_skills(), issue #2678/#2040)
    sha: 98ae38ae649f19c5b61515c109b1450985729859
  - path: docs/issue-2040/reports/implementation/survey.md
    sha: same-commit
  - path: docs/issue-2001/reports/implementation/replay-table.md
    sha: same-commit
---

# issue-2982 — knowledge-management-taxonomy-tagging+test-derivation-d8949284 record

## What was done

canonical: `98ae38ae:consult.py:92` (`_SKILL_CANDIDATES_RELEVANCE_FLOOR = 16.0`)
and `98ae38ae:consult.py:875-885` (the `if not use_judge:` branch of
`rank_skills()`), read directly.

`rank_skills()` (the function behind `spawn.py --skill-candidates`) now
carries a calibrated relevance floor. When `use_judge=False` (the
command's default preview mode) and the top BM25 score is under the
floor, the function returns the same `{"ranked": [], "outcome":
"no-candidates", "picked": []}` shape it already returns when BM25 finds
nothing — a confident-looking list of unrelated skills collapses into the
same honest empty state instead of printing a ranked top-N that looks
decided but is not. The check sits inside the existing `if not use_judge`
branch, after the pre-existing `if not scored` empty-state branch.

Two things the floor deliberately does not touch, both load-bearing per
the issue's must-not clauses:

- **The judge path** (`use_judge=True`) is unaffected — the floor check
  is scoped to the `use_judge=False` branch only.
  acceptance: `python3 -m pytest tests/test_skill_candidates_floor.py::SkillCandidatesFloorTest::test_skill_candidates_floor_judge_path_is_unaffected -q` — result:
  ```
  1 passed
  ```
- **Spawn's own internal cross-family mount**
  (`_cross_family_skill_matches_with_consult()` /
  `_cross_family_skill_matches()`, `98ae38ae:directive_assembly.py:790-800`)
  calls `_bm25_cross_family_scores()` directly and never passes through
  `rank_skills()`, so nothing about what spawn silently mounts on a real
  spawn changes.

Tests added, mapped to the issue's three named checks:

acceptance: `python3 -m pytest tests/ -k skill_candidates_floor -q` — result:
```
7 passed
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_floor_calibrated -q` — result:
```
2 passed
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
```
2 passed
```

- `SkillCandidatesFloorTest` (`tests/test_skill_candidates_floor.py`) —
  all-below-floor collapses to `no-candidates`; a strong match still
  ranks exactly as before; the judge path is unaffected.
- `SkillCandidatesFloorCalibratedTest` (`tests/test_skill_candidates_floor.py`)
  — the shipped floor constant is checked against the measured
  positive/negative score sets this record derives it from (see `## Why`),
  and each measured pair is individually replayed through `rank_skills()`
  to confirm it classifies the way its label says.
- `SkillCandidatesRegressionCasesTest` (`tests/test_skill_candidates_floor.py`)
  — the issue's own two measured tasks, replayed with the exact scores
  the issue body reports, both collapse to `no-candidates`.

`test/test_skill_candidates_ranking.py` (the pre-existing suite for this
function) needed two repairs, not new coverage: `TaskShapeRankingTest` and
`SameScoringTest` build a synthetic 2-skill corpus and assert on ranking
*order*, not the floor. With the floor live, their tiny corpus's scores
tripped it and broke unrelated assertions (BM25's IDF denominator uses
corpus document count, so a 2-document corpus cannot reach the ~270-skill
corpus's score scale). Both now neutralize the floor
(`mock.patch.object(spawn, "_SKILL_CANDIDATES_RELEVANCE_FLOOR", 0.0)`) for
the duration of their own, unrelated check.
acceptance: `python3 -m pytest test/test_skill_candidates_ranking.py -q` — result:
```
13 passed
```

## Why

The issue's explicit must-not is picking the floor freehand, so the
number has to come from measurement, and that measurement has to survive
independently of this session.

**Data source: this repo's own recorded task/selection pairs.** Past
sessions leave `skill-verdict: <skill> — applied: invoked` lines in
`docs/issue-*/reports/*.md` — each one a real (issue, skill actually
used) pair.

derived:
```
$ python3 -c '
import re, glob
pat = re.compile(r"skill-verdict:\s*([a-zA-Z0-9_-]+)\s*.\s*applied: invoked")
n = 0
for f in glob.glob("docs/issue-*/reports/**/*.md", recursive=True):
    try:
        text = open(f, encoding="utf-8").read()
    except Exception:
        continue
    n += len(pat.findall(text))
print(n)
'
895
```

One issue per distinct skill (excluding `_STATIC_POLICY_SKILLS` —
`work-in-english`, `prose-modes` — which are statically mounted and never
enter the BM25 candidate pool) gave 40 (issue, skill) pairs to replay
(script: `/tmp/scan_skill_verdicts2.py`, not committed — throwaway scan,
per this repo's convention of citing `derived:` output rather than
shipping one-off scripts).

**First replay attempt did not separate cleanly, and the reason is itself
the finding.** Replayed with each issue's full title+body as the query
(matching how `_bm25_cross_family_scores()` is invoked by spawn's own
internal mount at a real spawn), the 40 pairs' own-skill scores ranged
from 0.94 to 55.4 — the derivation and every individual value are in the
shell history of this session, not re-quoted here since this attempt was
abandoned (see `## What did not work`) and none of these numbers feed the
shipped constant.

Replayed with the issue title alone instead (shorter, closer in shape to
a `--skill-candidates "<task>"` argument), the top-1 score across all 27
distinct issues in the sample was never below 5.56 — including issues
whose top-1 pick was a skill unrelated to the issue.

derived:
```
$ python3 -c '
import sys; sys.path.insert(0, ".")
import spawn
repo_root = spawn._skill_repo_root()
print(spawn.rank_skills(
    "Invoke-before-apply: applicable mounted skills must be actually "
    "loaded (Skill call) and the verdict must cite it",
    "candidates", repo_root)["ranked"][0])
'
{'name': 'technical-feasibility-license-scan', 'score': 10.313807721841842, 'source': 'skill-repo', 'trigger': None}
```

That title (issue #2062, whose actually-applied skills were
`conformance-review-*`) top-1-matches an unrelated licensing skill at
score 10.31 — a title-shaped query's top score is not a reliable
relevance signal, because BM25 sums per-matching-query-token regardless
of whether the match is topically real.

**What separated cleanly: task text written the way `--skill-candidates`
is meant to be used** — a specific, technical sentence describing the
work (the shape of this issue's own two reported examples), scored
against the live skill-repository corpus.

derived:
```
$ python3 -c '
import sys; sys.path.insert(0, ".")
import spawn
repo_root = spawn._skill_repo_root()
positive_tasks = [
    ("sync 호출을 이벤트로 바꿀지 orchestration vs choreography 로 boundary contract 를 설계해야 한다", "architecture-interface-contract-shape"),
    ("verify the failing test suite, integration merge CI run and classify each test by what it actually verifies", "test-depth-audit"),
    ("derive test cases from these written acceptance criteria and build a traceability matrix linking each requirement to a black-box test technique", "test-derivation"),
    ("audit this code path for a failure that gets silently swallowed instead of surfacing as an error", "silent-failure-audit"),
    ("review this PR diff adversarially and find everything wrong with its claim that the change is safe", "adversarial-review"),
    ("merge two synonym tags in the controlled vocabulary and decide which one becomes the canonical SKOS broader term", "knowledge-management-taxonomy-tagging"),
    ("review this endpoint for missing input validation and injection defense before it goes live", "secure-coding-input-validation-injection-defense"),
]
scores = []
for t, expect in positive_tasks:
    r = spawn.rank_skills(t, "candidates", repo_root)
    top1 = r["ranked"][0]
    assert top1["name"] == expect
    scores.append(top1["score"])
print("min positive top-1 score:", min(scores))
print(sorted(scores))
'
min positive top-1 score: 16.963157077618174
[16.963157077618174, 19.39626174860225, 19.71452027269867, 22.873312031309496, 23.89840150795929, 44.82385367480575, 51.663619541370785]
```

derived:
```
$ python3 -c '
import sys; sys.path.insert(0, ".")
import spawn
repo_root = spawn._skill_repo_root()
negative_tasks = [
    "rewrite the workspace preservation predicate in lifecycle.py from git-status-based to what-would-be-lost — unpushed commits, stash, merge/rebase state, untracked classification via git check-ignore",
    "remove the 200-turn session cap, replace with wall-clock/token backstops and an observe-only runaway signal reusing trajectory_analyzer",
    "fix a git rebase conflict-resolution edge case inside mechanical_rebase_cli when the checked-out branch has a stale index lock left by a crashed prior process",
    "add a new CLI flag to spawn.py that lists active roster leases filtered by checkout path and prints their PID and heartbeat age",
    "the watchdog freshness check compares startup_head against the wrong ref after a force-push rewrites main, so it reports stale code when the code is actually current",
    "batch three separate grep calls into one Bash invocation instead of three round trips when scanning for a symbol across the gates directory",
]
scores = []
for t in negative_tasks:
    scored = spawn._bm25_cross_family_scores(t, "candidates", repo_root, None, None)
    scores.append(scored[0][0])
print("max negative top-1 score:", max(scores))
print(sorted(scores))
'
max negative top-1 score: 15.134316351480955
[7.911048066340095, 10.69661598388458, 11.61075563596152, 12.050935130438033, 13.696502243775724, 15.134316351480955]
```

The first two negative tasks above are this issue's own two reported
regressions, replayed live against today's corpus (which has grown since
the issue was filed — the issue's own reported scores, 0.4325/1.3324, are
from that smaller historical snapshot and are not comparable in scale to
today's corpus; they are preserved as a deterministic fixture in
`SkillCandidatesRegressionCasesTest` for exactly that reason, rather than
re-derived live each run).

`min(positive) = 16.963157077618174`, `max(negative) = 15.134316351480955`
— `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 16.0`
(`98ae38ae:consult.py:92`) sits in that gap: `16.963157077618174 - 16.0 =
0.963157077618174` below the weakest positive, `16.0 -
15.134316351480955 = 0.865683648519045` above the strongest negative.

**Boundary condition, named rather than hedged:** this floor is
corpus-size- and query-length-sensitive by construction — BM25's raw
score is an un-normalized sum over matching query tokens, not a bounded
similarity measure — so it is a snapshot against today's skill-repository
corpus, not a universal constant. A future recalibration should rerun the
two `derived:` scripts above against the corpus at that time;
`SkillCandidatesFloorCalibratedTest` fails loud if a constant change
breaks the measured separation.

**Rejected alternative: query-length-normalized score** (raw BM25 sum
divided by the theoretical per-query maximum, i.e. sum of `idf(t) *
(k1+1)` over matching query tokens). This would correct the query-length
confound directly and might generalize better across corpus sizes.
Rejected for this issue: it requires exposing per-token IDF data
`_bm25_cross_family_scores()` does not currently return — a
scoring-function change — and the issue's explicit non-goal is leaving
spawn's internal scoring untouched ("do not change what spawn's own
internal cross-family mount adds"). A future issue can revisit this if
corpus growth erodes the absolute-floor gap measured here.

## What did not work

- Calibrating against full issue-title+body text (matching spawn's
  internal call shape) produced own-skill scores with no usable
  separation from this issue's reported negative examples — abandoned in
  favor of task-shaped text (see `## Why`).
- Calibrating against issue-title-only text produced a positive set that
  was mostly noise itself: replayed live just now, 22 of the 27 sampled
  issues' top-1 pick was not one of that issue's own applied skills at
  all.
  derived:
  ```
  $ python3 -c '
  import json, subprocess, sys
  sys.path.insert(0, ".")
  import spawn
  pairs = [json.loads(l) for l in open("/tmp/skill_pairs.jsonl") if l.strip() and not l.startswith("TOTAL")]
  repo_root = spawn._skill_repo_root()
  issues = {}
  for row in pairs:
      issues.setdefault(row["issue"], []).append(row["skill"])
  miss = hit = 0
  for issue, skills in issues.items():
      out = subprocess.run(["gh", "issue", "view", str(issue), "--json", "title"],
                            capture_output=True, text=True, timeout=30)
      if out.returncode != 0:
          continue
      title = json.loads(out.stdout).get("title") or ""
      ranked = spawn.rank_skills(title, "candidates", repo_root)["ranked"]
      top1 = ranked[0]["name"] if ranked else None
      if top1 in skills:
          hit += 1
      else:
          miss += 1
  print("hit", hit, "miss", miss, "total", hit + miss)
  '
  hit 5 miss 22 total 27
  ```
  Replaced with hand-written task-shaped text where the genuinely-relevant
  skill was confirmed (via `assert top1["name"] == expect`, see the
  positive-set `derived:` block in `## Why`) to be the actual top-1 pick
  before its score was used as a positive data point.

## Upstream basis

- `consult.py` (`rank_skills()`), issue #2678 (introduced the function)
  and #2040 (introduced BM25 scoring) — this session's edit builds
  directly on the existing function, `98ae38ae:consult.py:760-895`.
- `docs/issue-2040/reports/implementation/survey.md` — established that
  BM25's IDF weighting reduces but does not eliminate generic-vocabulary
  false positives, the same failure class this issue's floor addresses at
  the ranking-output level.
- `docs/issue-2001/reports/implementation/replay-table.md` — the 16-pair
  real-session replay methodology (`gh issue view <n> --json title,body`)
  this record's initial, abandoned title+body calibration attempt reused
  before switching to hand-written task-shaped text.

## Open findings

None. The one open question this session weighed — normalizing score by
query length instead of an absolute floor — is recorded in `## Why` as a
rejected alternative with a stated reopen condition (corpus growth
eroding the measured gap), not left as a loose end.

## Next steps

None — `loop_state: landed`. A future recalibration should rerun the two
`## Why` derivation scripts against the corpus at that time and update
`_SKILL_CANDIDATES_RELEVANCE_FLOOR` and
`SkillCandidatesFloorCalibratedTest`'s embedded score lists together.

## Test derivation (test-derivation skill)

Routed the issue's three acceptance checks:

| Requirement | Risk class | Route | Depth |
|---|---|---|---|
| R1 — all-below-floor -> no-candidates; strong match still ranks (`skill_candidates_floor`) | Medium — user-facing behavior change, single-threshold comparison, not safety-critical | EP/BVA — one ordered partition (BM25 top score), one boundary (the floor) | 2-value boundary: floor-0.001 / floor+0.001 |
| R2 — floor derived from measurement, derivation in the record (`skill_candidates_floor_calibrated`) | Medium — process requirement, not a runtime behavior | EP/BVA on the measured-gap boundary: is the shipped constant inside the measured positive/negative interval? | Boundary check against the measured extremes, plus one replay per measured pair |
| R3 — issue's two measured tasks do not return their recorded unrelated skills as top candidates (`skill_candidates_regression_cases`) | High — this is the concrete defect the issue reports; a regression here reintroduces it | GWT scenario per case (2 named tasks) | Full: exact reported scores replayed, exact outcome-shape asserted |

GWT scenarios:

- R1 — Given a BM25 ranking whose top score is 0.001 under the floor,
  When `rank_skills(use_judge=False)` is called, Then it returns
  `{"ranked": [], "outcome": "no-candidates", "picked": []}`.
  canonical: `98ae38ae:tests/test_skill_candidates_floor.py:41-48`
  (`test_skill_candidates_floor_suppresses_all_low_score_candidates`).
- R1 — Given a BM25 ranking whose top score is 0.001 over the floor, When
  `rank_skills(use_judge=False)` is called, Then `outcome` is
  `"bm25-only"` and the candidate still ranks.
  canonical: `98ae38ae:tests/test_skill_candidates_floor.py:50-57`
  (`test_skill_candidates_floor_strong_match_still_ranks_as_today`).
- R3a — Given the scores this issue reports for the workspace-
  preservation task, When `rank_skills(use_judge=False)` is called, Then
  `outcome` is `"no-candidates"`.
  canonical: `98ae38ae:tests/test_skill_candidates_floor.py:150-161`
  (`test_skill_candidates_regression_cases_workspace_preservation_task`).
- R3b — Given the scores this issue reports for the 200-turn-cap task,
  When `rank_skills(use_judge=False)` is called, Then `outcome` is
  `"no-candidates"`.
  canonical: `98ae38ae:tests/test_skill_candidates_floor.py:163-174`
  (`test_skill_candidates_regression_cases_turn_cap_task`).

acceptance: `python3 -m pytest tests/test_skill_candidates_floor.py -v -q` — result:
```
7 passed
```

Coverage: EP/BVA — 1 ordered partition (BM25 top score), boundary items
exercised = 2/2 (100% — floor-0.001 and floor+0.001, see the two GWT
rows above). Decision table / state transition / pairwise / MC/DC: not
routed — no combined conditions, no state machine, no multi-parameter
combination space, no safety-critical Boolean decision in this change.
Traceability: R1 -> `SkillCandidatesFloorTest`; R2 ->
`SkillCandidatesFloorCalibratedTest`; R3 ->
`SkillCandidatesRegressionCasesTest`
(canonical: `98ae38ae:tests/test_skill_candidates_floor.py`, read directly
— every method in the file maps to exactly one of R1/R2/R3 above and
every row above cites a method that exists in it, so there is no orphan
test case and no empty requirement row).

Residual: these techniques establish that the floor's threshold logic and
the two named regressions behave as specified against known inputs. They
do **not** establish that 16.0 remains correctly calibrated as the corpus
changes (a measurement-currency concern, addressed by the boundary note
in `## Why`, not by more test cases), and they do not establish anything
about BM25 recall (the issue's own stated non-goal).

## Skill verdicts

skill-verdict: test-derivation — applied: invoked; used to route each of
the issue's three acceptance checks by problem shape (EP/BVA for the
threshold boundary and the measured-gap boundary, GWT scenarios for the
two regression cases), classify each by risk/depth, and build the
traceability table above.

skill-verdict: knowledge-management-taxonomy-tagging — not-applicable:
this issue is about BM25 relevance-ranking calibration for the
`--skill-candidates` preview command, not about adding, merging, or
scoping a controlled-vocabulary term or an ambiguous/synonym-prone tag —
no taxonomy edit occurs in this change.

skill-verdict: work-in-english — applied: invoked; all repository-bound
output this session (code, comments, commit, tests, this record) is
English; the final message to the user is Korean per the policy's
routing rule.

skill-verdict: prose-modes — applied: invoked; this record is written in
decision-record mode for an expert reader (this repo's own contributors)
— comparison presented via measured extremes rather than a styled table,
the boundary condition named explicitly rather than hedged (R3), and the
rejected-alternative paragraph states the specific cost of the
query-length-normalized-score alternative rather than a vague "considered
and rejected" (R4/R8).
