---
issue: 2982
role: adversarial-review-fc5c800d
author: adversarial-review-fc5c800d
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: b0efb53aaa9e594c5002d894b8e74d2f5749caa3 (consult.py, tests/test_skill_candidates_floor.py)
type: verification
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: PR #3011 (issue-2982/silent-failure-audit-68344f70), head b0efb53aaa9e594c5002d894b8e74d2f5749caa3
    sha: b0efb53aaa9e594c5002d894b8e74d2f5749caa3
  - path: docs/issue-2982/reports/silent-failure-audit-68344f70.md
    sha: b0efb53aaa9e594c5002d894b8e74d2f5749caa3
---

# issue-2982 — adversarial-review-fc5c800d record

## What was done

Independent re-verification of PR #3011 (`issue-2982/silent-failure-audit-68344f70`,
head `b0efb53a`), the recalibration round that followed PRs #3007 and #3009's
independent verifications of PR #3003. Both earlier reviews found PR #3003's
shipped floor (16.0) fit to 7 self-authored positive examples and silently
suppressed genuine top-1 matches. PR #3011 claims a re-derivation from real
repository history (issue titles replayed as queries, kept only where the
`skills:` frontmatter shows the applied skill was the genuine BM25 top-1) and
ships `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`.

checked: `git fetch origin pull/3011/head:pr-3011-verify` then
`git worktree add /tmp/verify-3011 pr-3011-verify` — isolated worktree at
`b0efb53a`, original checkout on `issue-2982/adversarial-review-fc5c800d`
untouched throughout.

**Acceptance checks — re-run live in the isolated worktree:**

acceptance: `python3 -m pytest tests/ -k skill_candidates_floor -q` — result:
```
11 passed in 1.43s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_floor_calibrated -q` — result:
```
2 passed in 0.82s
```
acceptance: `python3 -m pytest tests/ -k skill_candidates_regression_cases -q` — result:
```
5 passed in 0.88s
```
Matches PR #3011's claimed 11/2/5 exactly.

**All five previously-suppressed cases from PR #3007 (3) and PR #3009 (2)
re-run live against the recalibrated floor, not read from the PR's own
report:**

derived:
```
$ python3 -c '...rank_skills(q) for each of the 5 queries...'
floor = 4.0
customer-support-sla-tier-priority            top1=customer-support-sla-tier-priority score=14.529 outcome=bm25-only suppressed=False
risk-management-aggregation-consolidation     top1=risk-management-aggregation-consolidation score=11.186 outcome=bm25-only suppressed=False
conformance-review-sampling-derivation        top1=conformance-review-sampling-derivation score=10.531 outcome=bm25-only suppressed=False
test-depth-audit                              top1=test-depth-audit score=11.459 outcome=bm25-only suppressed=False
knowledge-management-taxonomy-tagging         top1=knowledge-management-taxonomy-tagging score=13.870 outcome=bm25-only suppressed=False
```
(query text for the last two — `test-depth-audit` and
`knowledge-management-taxonomy-tagging` — taken verbatim from PR #3009's own
record. canonical: `git fetch origin issue-2982/adversarial-review-4a0acec2`
then `git show FETCH_HEAD:docs/issue-2982/reports/adversarial-review-4a0acec2.md`,
read directly, since PR #3009's PR body only gives scores, not the query
strings.) All five now score well above 4.0 and none collapse to
`no-candidates` — the over-suppression defect PRs #3007/#3009 both flagged
is fixed.

**Overlap claim — independently re-derived from scratch, not trusted from
the record.** Wrote a fresh extraction script (not copied from the record's
`/tmp/extract_pairs.py`/`/tmp/derive_floor.py`, which no longer exist on
disk) that reads `skills:`/`issue:` frontmatter across `docs/issue-*/reports/**/*.md`,
fetches each distinct issue's title live via `gh issue view`, replays it as a
BM25 query, and keeps it as a positive example only where the applied skill
is the genuine top-1:

derived:
```
$ python3 /tmp/verify_derive.py
distinct issues: 81
total pairs: 219
genuine top-1 matches: 7
7.617285 issue=2906 skill=silent-failure-audit
7.926376 issue=2874 skill=adversarial-review
8.354879 issue=2924 skill=silent-failure-audit
8.364782 issue=2511 skill=silent-failure-audit
9.713774 issue=2626 skill=silent-failure-audit
9.839628 issue=2892 skill=adversarial-review
13.785566 issue=2894 skill=silent-failure-audit
min positive: 7.617284997267742
```
The 7 scores match the record's `REAL_POSITIVE_TOP1_SCORES` to 6 decimal
places exactly (81 vs the record's 80 distinct issues, 219 vs 215 pairs — a
small drift plausibly from commits landed on this branch after the record
was written; it does not change which 7 pairs qualify or their scores). This
confirms the derivation is real measurement, not a fabricated or
selectively-rounded number.

Also independently re-ran the first derivation's own 6 "negative" probe
tasks (verbatim query text from
`8057d4b1:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`,
read directly) against today's live corpus:

derived:
```
$ python3 /tmp/verify_negatives.py
floor = 4.0
score=15.134316 top1=agent-coordination             suppressed=False
score=7.911048  top1=secure-coding-session-authentication suppressed=False
score=12.050935 top1=agent-coordination             suppressed=False
score=11.610756 top1=design-artifact-user-flow      suppressed=False
score=10.696616 top1=test-depth-audit               suppressed=False
score=13.696502 top1=user-discovery-saturation-stopping-rule suppressed=False
```
Reproduces the record's cited 7.911048066340095 / 15.134316351480955 exactly.
The overlap claim (real positives as low as 7.617, off-topic negatives
occupying 7.911-15.134, the bands overlap) is confirmed independently, not
just cited.

**New finding beyond what the record discloses: how much the floor actually
filters in practice.** The record frames the unresolved gap as bounded to a
"7.617-15.134" score band from two specific probe tasks. I tested that
framing against 35 queries not drawn from any PR's record (10 generic
off-topic prompts, 10 plausible coding-task sentences, 15 short vague
operator-style prompts like "fix this bug" / "add a new feature" — the
shape the issue itself uses as its running example):

derived:
```
$ python3 /tmp/verify_noop_check.py    # 10 generic off-topic prompts
suppressed 2/10   (scores of the other 8: 4.84-8.0)
$ python3 /tmp/verify_noop_check2.py   # 10 plausible coding-task sentences
suppressed 0/10   (scores: 5.38-22.05)
$ python3 /tmp/verify_noop_check3.py   # 15 short vague operator prompts
suppressed 2/15   (scores of the other 13: 4.18-8.38)
```
derived: `2 + 0 + 2 = 4` suppressed of `10 + 10 + 15 = 35` total, `4/35 =
0.114` — full transcripts of all three runs are reproduced in this session.
The other 31 returned a confident-looking, wrong top-1 skill — e.g.
`"fix this bug"` → `upstream-defect-report-subtraction` (4.73), `"add a new
feature"` → `legal-compliance-retention-minimization` (6.43), `"clean this
up"` → `market-analysis-evidence-rigor` (8.38). This is not a narrow band
around 7.6-15.1; unrelated queries score anywhere from ~4 up past 20,
because BM25's raw per-token sum grows with query length and this
270+-skill corpus shares some vocabulary with almost any English sentence.
The floor mechanically only removes near-zero-overlap cases (scores under
~4), which the issue's own two originally-filed examples (0.4325, 1.3324)
happened to be, but that is a narrow slice of the actual "confident-looking
unrelated skill" failure mode the issue names in its title.

I also ran the test suite the environment's own lint-test-on-edit hook
flagged as failing in the worktree:

derived:
```
$ python3 -m pytest test/test_spawn_cross_family_skill_selection.py -q
6 failed, 17 passed in 1.06s
FAILED ...test_family_skill_never_returned_as_cross_family_candidate
...
fatal: 'origin' does not appear to be a git repository
```
The failure is `SystemExit: 브랜치 체크아웃: fetch 실패 — fatal: 'origin' does not
appear to be a git repository` — the fetched worktree lacks a real `origin`
remote wired up, a property of how I isolated the worktree, not a
regression in PR #3011's diff (`git diff main...HEAD -- spawn.py` shows only
a one-line re-export addition, quoted under "Upstream basis" below). Out of
scope for this issue and not counted against the verdict.

## Why

The task asked me to re-derive the overlap claim myself rather than trust
the record's numbers, and to judge plainly whether the floor does anything
useful — treating a no-op dressed as a fix as its own failure mode. I chose
to (1) reproduce every number the record cites from a script I wrote from
scratch, not a copy of the session's own derivation script, so agreement is
evidence of correctness rather than of copying, and (2) go beyond the
record's own probe set with independently authored queries closer to how an
operator would actually type a task, since the record's disclosed
"known limitation" only quantifies two specific probe scores and does not
report a hit rate against realistic usage.

## What did not work

My first extraction script under-counted positive pairs — derived:
```
$ python3 /tmp/verify_derive.py   # before the fix below
genuine top-1 matches: 6   # expected 7, per the record's REAL_POSITIVE_TOP1_SCORES
```
Root cause: its regex assumed every skill name in a `skills:` frontmatter
line has its own trailing `(skill-repository(...))` parenthetical, but
`docs/issue-2626/reports/adversarial-review+silent-failure-audit-9ea418cf.md`
(checked: `grep -H "^skills:"` on that path, read directly) groups two
comma-separated names under one shared trailing parenthetical —
`skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))`
happened to work by accident, but a `split(..., 1)` on the first
`(skill-repository` silently dropped every name after the first occurrence
on lines shaped that way. Fixed by stripping all `(skill-repository(...))`
groups with a regex before splitting on commas, which recovered the missing
`issue=2626, skill=silent-failure-audit` pair — derived:
```
$ python3 /tmp/verify_derive.py   # after the fix
2626 pairs: [(2626, 'adversarial-review'), (2626, 'implementation-audit'), (2626, 'silent-failure-audit')]
genuine top-1 matches: 7
```
and reproduced all 7 of the record's scores exactly (quoted under "What was
done" above).

## Upstream basis

checked: `gh pr view 3011 --json headRefOid` — result:
`{"headRefOid":"b0efb53aaa9e594c5002d894b8e74d2f5749caa3"}`, then verified
via isolated `git worktree add /tmp/verify-3011 pr-3011-verify` (not the PR
description).

canonical: `b0efb53a:docs/issue-2982/reports/silent-failure-audit-68344f70.md`
(read in full this turn via the isolated worktree; this path is untracked in
this session's own checkout since PR #3011 has not merged) — the derivation
this review re-derives independently rather than cites.

canonical: `0de95773:docs/issue-2982/reports/adversarial-review-bcc60aba.md`
(PR #3007's record, fetched via `git fetch origin issue-2982/adversarial-review-bcc60aba`,
read in full) and `git fetch origin issue-2982/adversarial-review-4a0acec2`
then `FETCH_HEAD:docs/issue-2982/reports/adversarial-review-4a0acec2.md`
(PR #3009's record, read in full) — source of the exact query text for the
five PR #3007/#3009 cases re-run live above.

canonical: `8057d4b1:docs/issue-2982/reports/knowledge-management-taxonomy-tagging+test-derivation-d8949284.md`
(first derivation's record) — source of the six "negative" probe queries
re-run independently above.

derived: `git diff main...HEAD -- spawn.py` at `b0efb53a`, result:
```
+_SKILL_CANDIDATES_RELEVANCE_FLOOR = consult._SKILL_CANDIDATES_RELEVANCE_FLOOR
```
one-line re-export addition only — confirms the must-not constraints (no
change to the judge path, `--skill-candidates` selection behavior, or
spawn's internal cross-family mount) hold at the code level.

## Open findings

canonical: acceptance-check results, five-case re-run, and overlap
re-derivation all quoted verbatim under "What was done" above (this turn's
own transcript, not a citation of PR #3011's claims).

- The floor genuinely fixes the two originally-reported degenerate cases and
  the five PR #3007/#3009 over-suppression cases, and is honestly derived
  from real history rather than self-authored examples — this satisfies all
  three of issue #2982's acceptance checks and every must-not, confirmed
  independently above. No resolution needed.
- The floor does very little against the issue's own title complaint
  ("Skill candidate ranking returns unrelated skills") — derived: `31/35 =
  0.886` of independently authored realistic/unrelated queries in my sample
  (see "What was done", the three `verify_noop_check*.py` runs) still
  return a confident-looking wrong top-1 skill unsuppressed, because BM25
  raw scores for unrelated-but-English-language queries routinely land well
  above 4.0 on this corpus. The record already discloses, honestly, that no
  single BM25-score floor can separate the classes cleanly and defers a
  general fix to a future issue requiring a different signal (e.g. a
  relative top-1/top-2 margin) — my finding does not contradict that
  disclosure, but shows the practical gap is wider than the record's own
  framing (a narrow "7.617-15.134" overlap band from two probe tasks)
  suggests: it is not a narrow edge case, it is most of the everyday
  false-positive surface — derived: `4/35 = 0.114` (the three
  `verify_noop_check*.py` runs quoted under "What was done" above).
  Resolution path: same one the record already names — a follow-up issue
  for a non-raw-score signal (relative margin, judge-assisted rerank scoped
  only to a `--with-judge`-style opt-in, or something else) rather than a
  different BM25 constant, since no constant on this corpus separates the
  classes (confirmed independently under "What was done" — real positives
  as low as 7.617 overlap negative probes up to 15.134). Recommend the
  follow-up issue also carry, up front, a measured hit-rate number like this
  session's 4/35 (11%), so a future reader doesn't have to independently
  discover how narrow the current floor's effect is.

## Next steps

None from this record. acceptance: all three of issue #2982's specified
checks re-run live this turn — result: see "What was done" above (11
passed / 2 passed / 5 passed, matching PR #3011's claim exactly) —
`loop_state: landed`, `verdict: pass` on issue #2982's own acceptance
criteria and must-nots. The open finding above names a follow-up issue as
its own resolution path, not a blocker on PR #3011 itself.

skill-verdict: adversarial-review — applied: invoked; ran this entire
verification as a structurally independent evaluator with no access to the
building sessions' reasoning beyond their committed records, incentivized to
find everything wrong with PR #3011 rather than confirm it (canonical: the
"New finding beyond what the record discloses" subsection under "What was
done" above is that adversarial pass) — wrote fresh extraction/derivation
scripts instead of reusing or citing the session's own throwaway scripts
(which no longer exist on disk), and went past the record's own probe set
with independently authored queries to test whether its "partial fix"
framing understated the practical gap (it did, per the 4/35 result above).
skill-verdict: work-in-english — applied: invoked; this record and all
commands run are in English despite the spawning prompt and directives
being in Korean.
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; did not treat PR #3007/#3009's "fail" verdicts, or PR
#3011's own "pass"-shaped record, as license to skip independent
measurement — re-derived the positive-set extraction from scratch (catching
and fixing my own script bug in the process, see "What did not work"),
re-ran the negative-probe queries live, and additionally probed 35 queries
none of the three prior sessions had used, rather than re-running only what
the upstream records already claimed to have checked.
skill-verdict: verify-finding-record — not-applicable: this session's
deliverable is this adversarial-review record itself, not a separate
`docs/issue-<n>/reports/defect-verification.md` reproduction-attempt record.
