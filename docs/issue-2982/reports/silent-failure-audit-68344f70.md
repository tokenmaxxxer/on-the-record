---
issue: 2982
role: silent-failure-audit-68344f70
author: silent-failure-audit-68344f70
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit (consult.py, tests/test_skill_candidates_floor.py)
type: fix
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: consult.py (`_SKILL_CANDIDATES_RELEVANCE_FLOOR`, PR #3003)
    sha: 98ae38ae649f19c5b61515c109b1450985729859
  - path: docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md (first derivation)
    sha: 8057d4b10159f45f53b9575cb5589d27898a20e1
  - path: docs/issue-2982/reports/adversarial-review-bcc60aba.md (PR #3007 independent verification, verdict fail)
    sha: 0de957736e9efd941da3393c6b1725f66775ed13
---

# issue-2982 — silent-failure-audit-68344f70 record

## What was done

This is a follow-up to PR #3003's calibrated relevance floor for
`spawn.py --skill-candidates` (`rank_skills()` in consult.py).

canonical: `0de957736e9efd941da3393c6b1725f66775ed13:docs/issue-2982/reports/adversarial-review-bcc60aba.md`,
read directly (verdict: fail).

PR #3007's independent verification found the shipped floor (16.0) was
fit to 7 positive examples the same session hand-wrote before choosing
the threshold, and reproduced 3 realistic queries with genuine,
unambiguous BM25 top-1 matches that it silently suppressed to
`no-candidates`:
```
raw top1: customer-support-sla-tier-priority, score=14.53 (rank 1, correct)
raw top1: risk-management-aggregation-consolidation, score=11.19 (rank 1, correct)
raw top1: conformance-review-sampling-derivation, score=10.53 (rank 1, correct)
```
(quoted verbatim from the canonical record above) — the exact failure
direction issue #2982's own must-not named: "an uncalibrated floor
filters out correct candidates."

canonical: `git rev-parse HEAD` output at the time of this fix:
```
e465079d8a45eafb0cc3c181b7a5888a834506dd
```
Current branch (`issue-2982/silent-failure-audit-68344f70`) was merged
with `origin/issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284`
at that commit (merge commit `e465079d`, this session) so the fix builds
directly on PR #3003's code rather than re-deriving spawn.py/consult.py
from scratch on an unrelated branch — the sidecar role/branch gate
(`.on-the-record/role.json`) ties this session to
`issue-2982/silent-failure-audit-68344f70`, so the merge (not a branch
switch) is how PR #3003's commits entered this session's tree.

**Re-derivation source: this repo's own recorded operator selections,
not text this session wrote.** `skills:` frontmatter across
`docs/issue-*/reports/*.md` records what `--skills` an operator actually
chose for a real spawn.

derived:
```
$ python3 /tmp/extract_pairs.py
distinct issues with skills frontmatter: 80
total (issue, skill) pairs: 234
```
(regex-extracted `issue:`/`skills:` frontmatter pairs across
`docs/issue-*/reports/**/*.md`, excluding the static-mounted
`work-in-english` policy skill, which never enters the BM25 candidate
pool per `spawn._STATIC_POLICY_SKILLS`)

Each distinct issue's title was fetched live via `gh issue view <n>
--json title` for all 80 issue numbers:

derived:
```
$ wc -l /tmp/issue_titles.jsonl
80 /tmp/issue_titles.jsonl
$ wc -w /tmp/issue_nums.txt
80 /tmp/issue_nums.txt
```
(line count of fetched titles equals the word count of the requested
issue-number list — every lookup resolved, no fetch errors logged to
`/tmp/gh_errors.log`, which is empty)

Each title was then replayed as a `spawn._bm25_cross_family_scores()`
query against the live skill-repository corpus, and kept as a positive
example only where the operator's actually-applied skill was the genuine
BM25 top-1 pick — the same "genuine top-1" filter the first derivation
used, but applied to real historical selections instead of hand-written
sentences:

derived:
```
$ python3 /tmp/derive_floor.py
total non-static (issue,skill) pairs considered: 215
genuine top-1 matches (applied skill == BM25 top-1): 7
  7.617284997267742  issue=2906  skill=silent-failure-audit
  7.926375755789291  issue=2874  skill=adversarial-review
  8.354878908889502  issue=2924  skill=silent-failure-audit
  8.36478203459652   issue=2511  skill=silent-failure-audit
  9.713773500211078  issue=2626  skill=silent-failure-audit
  9.839628389484924  issue=2892  skill=adversarial-review
  13.78556616833873  issue=2894  skill=silent-failure-audit
```

`min(real genuine top-1) = 7.617284997267742` — well below the first
derivation's self-authored positive floor (16.963) and below even PR
#3007's three reproduction cases quoted above. This is independent
confirmation of PR #3007's finding: a floor anywhere near 16.0 suppresses
real operator-chosen matches, not just probed edge cases.

**The honest limit this re-derivation surfaces:**

canonical: `98ae38ae:consult.py` lines 92 and `8057d4b1:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`,
read directly — the first derivation's own `NEGATIVE_TOP1_SCORES` /
`negative_tasks` (task descriptions it judged off-topic, scored live
against today's corpus) top out at 15.134316351480955 — inside the same
7.617-15.134 band the real genuine matches above also occupy. No hard
BM25-score floor separates "genuinely on-topic" from "plausible but
wrong" across that overlap; recalibrating cannot fix that, because the
overlap is a property of BM25 scores on this corpus, not of which
examples happened to calibrate it. This is recorded as a known, accepted
limitation (`SkillCandidatesFloorKnownLimitationTest` in
`tests/test_skill_candidates_floor.py`, same-commit), not hidden.

What the evidence does support: a floor placed above the two near-zero
degenerate matches issue #2982 itself originally reported (0.4325,
1.3324 — real observed defects, not chosen to fit a number) and below
every documented genuine top-1 match (7.617284997267742 lowest). The
floor was set at the midpoint of that gap:

derived:
```
$ python3 -c "print((1.3324 + 7.617284997267742) / 2)"
4.474842498633871
```

Shipped as `consult._SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`
(same-commit, `consult.py`) — inside the gap, not the exact midpoint, to
keep clean margin on both sides (2.6676 above the degenerate negatives,
3.6173 below the weakest real genuine match: `4.0 - 1.3324 = 2.6676`,
`7.617284997267742 - 4.0 = 3.617284997267742`) without implying false
precision from an n=7/n=2 sample.

**Tests updated** (`tests/test_skill_candidates_floor.py`, same-commit):
- `SkillCandidatesFloorCalibratedTest` now pins the floor against the
  real operator-history positive set and the two documented degenerate
  negatives, instead of the first derivation's self-authored examples.
- `SkillCandidatesFloorKnownLimitationTest` (new) documents, as a passing
  test rather than a silent gap, that the first derivation's own
  mid-band probe scores (7.911048066340095, 15.134316351480955) are NOT
  suppressed by the recalibrated floor — an accepted scope limit.
- `SkillCandidatesRegressionCasesTest` keeps the original two
  "must-suppress" fixtures and adds three new "must-survive" fixtures for
  PR #3007's exact reproduction cases (SLA-tier, risk-aggregation,
  conformance-sampling queries), each re-measured live against today's
  corpus rather than copied from PR #3007's record:

derived:
```
$ python3 -c "
import sys; sys.path.insert(0,'.')
import spawn
repo_root = spawn._skill_repo_root()
cases = [
    ('define SLA tiers and escalation priority for support tickets', 'customer-support-sla-tier-priority'),
    ('consolidate and aggregate risk exposure across business units', 'risk-management-aggregation-consolidation'),
    ('derive the sampling method for this conformance review', 'conformance-review-sampling-derivation'),
]
for q, expect in cases:
    scored = spawn._bm25_cross_family_scores(q, 'candidates', repo_root, None, None)
    top1 = scored[0]
    print(expect, top1[1], top1[0], top1[1]==expect)
"
customer-support-sla-tier-priority customer-support-sla-tier-priority 14.528541509218531 True
risk-management-aggregation-consolidation risk-management-aggregation-consolidation 11.185550391505078 True
conformance-review-sampling-derivation conformance-review-sampling-derivation 10.530965217698867 True
```
Matches PR #3007's reported values to 2 decimal places (14.53/11.19/10.53
quoted above) — the defect reproduces identically today, and with the
recalibrated floor, none of the three collapses to `no-candidates`.

Issue #2982's acceptance checks, re-run after the fix:

acceptance: `python3 -m pytest tests/ -k skill_candidates_floor -q` — result:
```
11 passed in 0.85s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_floor_calibrated -q` — result:
```
2 passed in 0.86s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
```
5 passed in 0.83s
```
acceptance: `python3 -m pytest test/test_skill_candidates_ranking.py -q` — result:
```
6 passed in 1.08s
```
(the pre-existing ranking suite, unaffected by this change, re-run to
confirm no regression)

## Why

The task was explicit that the fix must not repeat PR #3003's mistake:
the positive set has to come from evidence this session did not author,
and the result must be reported honestly even if it lands far below 16.0
or supports no useful floor at all.

canonical: `8057d4b1:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`,
read directly — the first derivation's own `## Why` section states its
positive set was 7 sentences this same calibrating session wrote itself
("`positive_tasks = [...]`" embedded directly in its `derived:` block),
which is the self-authored-example bias PR #3007's finding is about.

`skills:` report frontmatter is the one source in this repo that records
what an operator actually chose, independent of and predating this
issue — using issue titles (not hand-written task sentences) as the
query text keeps the replay close to how `--skill-candidates` is
actually invoked, without reintroducing that bias.

The honest result is a partial fix, not a full one: real operator-chosen
matches score as low as 7.617284997267742, which overlaps the
7.911-15.134 band the first derivation's own negative probes occupy (see
`## What was done`), so no single BM25-score floor can separate
"genuinely correct" from "plausible but wrong" across that whole range.
Rather than pick a number that either still risks eating real matches
(anything near or above 7.617) or claims a separation the evidence
doesn't support, the floor is set only where the evidence is unambiguous
— above the two documented near-zero degenerate scores and below every
documented genuine match — and the remaining gap is recorded as a known
limitation with its own passing test, per the task's instruction that an
honest partial fix beats a filter that silently drops correct answers.

## What did not work

None — the re-derivation scripts (`/tmp/extract_pairs.py`,
`/tmp/derive_floor.py`, not committed, throwaway scans per this repo's
convention of citing `derived:` output rather than shipping one-off
scripts) worked on the first pass; no attempted approach was abandoned
mid-session.

## Upstream basis

canonical: `git log --oneline -1` at commit `e465079d` (this session, HEAD
at time of writing):
```
e465079d issue-2982: merge PR #3003 (calibrated relevance floor) to build the recalibration fix on top
```

- PR #3003 (`98ae38ae`, `8057d4b1`, `084dbe8c`,
  `issue-2982/knowledge-management-taxonomy-tagging+test-derivation-d8949284`),
  merged into this branch at `e465079d` (see the `git log` output
  above).
- PR #3007's independent verification finding
  (`0de95773:docs/issue-2982/reports/adversarial-review-bcc60aba.md`),
  read directly — its reproduction cases (quoted verbatim under `## What
  was done`) are now regression fixtures in
  `tests/test_skill_candidates_floor.py`.
- `docs/issue-*/reports/*.md` `skills:` frontmatter — the positive-set
  source this record derives the new floor from (extraction counts
  quoted with `derived:` under `## What was done`).

## Open findings

- The floor does not, and cannot with a single BM25-score cutoff,
  separate genuine top-1 matches from plausible-but-wrong ones in the
  7.617-15.134 score band (documented and tested in
  `SkillCandidatesFloorKnownLimitationTest`, same-commit). Resolution
  path: if this needs closing later, it requires a design change (e.g. a
  relative margin between top-1 and top-2, or a signal other than the
  raw BM25 score), not a different constant — flagged for a future issue
  rather than attempted here, since issue #2982's own must-not forbids
  making the judge the default fix and no other signal was in scope.

## Next steps

None — `loop_state: landed`, verdict `pass`. Acceptance checks re-run
and passing above.

skill-verdict: silent-failure-audit — applied: invoked; used the
skill's classification/trace-forward lens on the new floor-check branch
in `rank_skills()` (consult.py) — confirmed the `no-candidates` collapse
on a low top-1 score is a deliberate, symmetrical reuse of the
pre-existing empty-`scored` branch's return shape (not a new absorbed
error), that it changes nothing about the judge path or spawn's own
internal cross-family mount (both traced and confirmed unaffected, per
the docstring and
`SkillCandidatesFloorTest::test_skill_candidates_floor_judge_path_is_unaffected`,
which passed — see `## What was done` acceptance output), and that the
suppression itself remains visible to the caller as an explicit
`outcome` field rather than a silently swallowed distinction — this is
the property the audit's lens exists to check for.
skill-verdict: work-in-english — applied: invoked; all commits, this
record, and the PR are written in English despite the spawning prompt
and directives being in Korean.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-ran PR #3007's three reproduction queries live myself (see `derived:` block under `## What was done`) rather than citing its reported scores at face value, and re-derived the floor from primary evidence (report frontmatter + live BM25 scores) rather than treating PR #3007's "fail" verdict as license to skip independent measurement.
other mounted skills: verify-finding-record not-applicable — this session builds and lands a fix, not a fresh `docs/issue-<n>/reports/defect-verification.md` reproduction-attempt record; PR #3007's own record already covers that outcome.
