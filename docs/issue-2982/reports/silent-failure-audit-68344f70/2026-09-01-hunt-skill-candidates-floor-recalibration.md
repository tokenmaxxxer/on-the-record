---
proposal: docs/issue-2982/reports/silent-failure-audit-68344f70.md
---

# Hunt record — skill-candidates-floor-recalibration

## after-proposal — stance: probe commit 8d991aa9 (floor 16.0 -> 4.0 re-derivation) for a defect invisible in a normal read

Verdict: FINDING — `SkillCandidatesFloorCalibratedTest.REAL_POSITIVE_TOP1_SCORES`' own inline "applied skill=" comments contradict the `skills:` frontmatter of the report files they cite as the evidence source, for 5 of the 7 rows
Kind: design-error
Seed: git show 8d991aa9 (consult.py floor 16.0->4.0, tests/test_skill_candidates_floor.py rewrite); git diff e465079d 8d991aa9 -- consult.py tests/test_skill_candidates_floor.py
cap_seconds: n/a (no dispatcher cap given in this invocation)
tier: default
diff_stat_lines: consult.py +26/-16, tests/test_skill_candidates_floor.py 187 lines (rewritten), 468 insertions/63 deletions total per `git show --stat`
started_at: 2026-09-01T00:00:00Z
ended_at: 2026-09-01T01:10:00Z

The new calibration test class documents its positive set as "real
(issue, applied-skill) pairs read from this repo's own `skills:` report
frontmatter ... kept where the applied skill was the genuine BM25 top-1
pick" and labels each of the 7 `REAL_POSITIVE_TOP1_SCORES` entries with a
`# issue #NNNN, applied skill=<skill>` comment naming which report
supplied that score. Cross-checking those comments against the actual
`skills:` frontmatter line of the cited report file for each issue shows
5 of the 7 labels are wrong -- the comment names a skill the report never
applied, while the skill the report actually recorded is a different one
also present elsewhere in the same list (silent-failure-audit /
adversarial-review get swapped repeatedly). This is not a cosmetic typo:
the whole justification for lowering the floor from 16.0 to 4.0 rests on
these 7 numbers being verified real-selection top-1 scores tied to a
specific (issue-title, applied-skill) pair; if the bookkeeping that
attached a skill label to a score was already wrong for most of the
positive set when writing the comment, there is no remaining evidence in
the test file itself that the *scores* (not just the labels) were
correctly paired to the right (issue, skill) query in the first place --
exactly the kind of unverified-provenance mistake PR #3007 caught the
first floor derivation making.

### Reproduce
```
cd <repo>
grep -n "applied skill=" tests/test_skill_candidates_floor.py
grep -H "^skills:" \
  docs/issue-2874/reports/silent-failure-audit-e7b244cd.md \
  docs/issue-2924/reports/adversarial-review-83c8f7f0.md \
  docs/issue-2626/reports/adversarial-review+implementation-audit-ee26fbd8.md \
  docs/issue-2892/reports/silent-failure-audit-f753aa68.md \
  docs/issue-2894/reports/adversarial-review-3fb40e3e.md
```

### Observed
`tests/test_skill_candidates_floor.py` lines 116-122:
```
        7.617284997267742,   # issue #2906, applied skill=silent-failure-audit
        7.926375755789291,   # issue #2874, applied skill=adversarial-review
        8.354878908889502,   # issue #2924, applied skill=silent-failure-audit
        8.36478203459652,    # issue #2511, applied skill=silent-failure-audit
        9.713773500211078,   # issue #2626, applied skill=silent-failure-audit
        9.839628389484924,   # issue #2892, applied skill=adversarial-review
        13.78556616833873,   # issue #2894, applied skill=silent-failure-audit
```
The actual `skills:` frontmatter of the cited reports:
```
docs/issue-2874/.../e7b244cd.md:  skills: silent-failure-audit   (comment says adversarial-review)
docs/issue-2924/.../83c8f7f0.md:  skills: adversarial-review     (comment says silent-failure-audit)
docs/issue-2626/.../ee26fbd8.md:  skills: adversarial-review, implementation-audit  (comment says silent-failure-audit -- neither actual skill)
docs/issue-2892/.../f753aa68.md:  skills: silent-failure-audit   (comment says adversarial-review)
docs/issue-2894/.../3fb40e3e.md:  skills: adversarial-review     (comment says silent-failure-audit)
```
5 of 7 rows are mislabeled relative to the primary source the test's own
class docstring cites as its evidence.

### Expected
Every `# issue #NNNN, applied skill=<X>` comment in
`REAL_POSITIVE_TOP1_SCORES` should name the skill actually recorded in
that issue's own `skills:` report frontmatter, since the class docstring
stakes the recalibration's credibility on these being real, checkable
(issue, applied-skill, top-1-score) triples rather than another set of
numbers whose correspondence to real evidence cannot actually be
verified by re-reading the cited source.
