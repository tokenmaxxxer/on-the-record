---
proposal: docs/issue-2250/reports/ml-engineering.md
---

# Hunt record — ml-engineering

## after-proposal — stance 1: assume the classification / "no code fix needed" conclusion is wrong in a way that would embarrass the author (checked: numeric claims vs raw log, live-BM25-rerun plausibility, correct-abstain defensibility, lint conventions)

Verdict: FINDING — the record's "live BM25 re-run" evidence block (the sole
support for ruling out retrieval-miss on task pattern C/E, 13 of the 19
classified lines) does not reproduce: re-running
`spawn._bm25_cross_family_scores()` against the actual task-C/E text (issue
#2208's real body, fetched with `gh issue view 2208`) and the actual skill
corpus produces a top-12 that shares only 2 of 12 names with the record's
quoted top-12, at roughly 3x the score magnitude, and 8 of the record's 12
claimed top-12 skills actually rank between #14 and #187.
Kind: silent-failure
Seed: docs/issue-2250/reports/ml-engineering.md (new, uncommitted) vs
  docs/issue-2208/reports/consult-log.md (raw source it classifies)
cap_seconds: n/a (not given by dispatcher)
tier: default
diff_stat_lines: n/a (new untracked file, ~170 lines)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:45:00Z

### Reproduce

```
$ gh issue view 2208 --json body -q .body > /tmp/issue2208_body.txt
$ python3 -c "
import spawn, os
from pathlib import Path
body = open('/tmp/issue2208_body.txt', encoding='utf-8').read()
task_text = ('Issue #2208: Skill selection follow-ups from #2205: judge '
             'abstention rate, negative-clause indexing, pinning policy '
             'skills\n\n') + body
repo_root = Path(os.environ['MUSTER_SKILL_REGISTRY_ROOT'])
scored = spawn._bm25_cross_family_scores(task_text, 'execution-observation', repo_root)
print('total scored', len(scored))
for s, name, d, src in scored[:12]:
    print(f'{s:.3f} {name}')
"
```

(`MUSTER_SKILL_REGISTRY_ROOT` points at the same skill-repository checkout
the record itself invokes — 273 skill dirs on disk, 272 scored once the
execution-observation family is excluded, matching the record's own stated
corpus size, so the corpus is not the mismatch.)

### Observed

```
total scored 272
64.441 test-depth-audit
55.159 adversarial-review
51.719 growth-analytics-metric-selection
50.388 implementation-audit
50.333 reference-forecast
47.372 model-routing
45.479 technical-feasibility-verdict-and-timebox-selection
44.901 conformance-review-finding-record
43.968 verify-finding-record
43.919 product-discovery-opportunity-solution-tree
43.136 pricing-research
43.094 finance-unit-economics-sensitivity-scenario
```

The record's "Ruled out as retrieval-miss" section quotes, for the same
role/task:

```
TOP12 for role=execution-observation:
20.728 adversarial-review          20.310 technical-feasibility-verdict-and-timebox-selection
20.161 blameless-postmortem        18.944 model-routing
18.437 release-engineering-error-budget-policy   18.428 decision-records
17.034 observability-phase-trace   17.023 hypothesis-testing
16.087 partnerships-bd-exclusivity-and-scope-terms
15.909 incident-response-action-item-quality
14.958 flow-metrics                14.902 verify-severity-classification
```

Checking where the record's claimed top-12 names actually land in the real
re-run: `blameless-postmortem` rank 143 (score 22.2), `release-engineering-
error-budget-policy` rank 107 (score 25.6), `partnerships-bd-exclusivity-
and-scope-terms` rank 187 (score 18.0), `incident-response-action-item-
quality` rank 100 (score 26.5), `verify-severity-classification` rank 82
(score 28.7), `decision-records` rank 26, `observability-phase-trace` rank
38, `hypothesis-testing` rank 33, `flow-metrics` rank 14 — none is actually
in the top-12. Only `adversarial-review` (real rank 2, not 1) and
`technical-feasibility-verdict-and-timebox-selection` (real rank 7, not 2)
overlap with the record's list at all, and even those have the wrong rank
and roughly a third of the claimed score. The skill the real run puts at
rank 1 (`test-depth-audit`, score 64.4) does not appear anywhere in the
record's quoted list. The record's two rank figures for the ml-engineering
skills also don't match: it claims `ml-engineering-evaluation-discipline`
rank 101 and `ml-engineering-ml-test-score-scoring` rank 150; the real
re-run gives rank 105 and rank 77 respectively — the second is off by
roughly 2x.

### Expected

A record whose acceptance line says "re-run live" should reproduce when the
same call is made again against the same corpus and the same task text. The
sole empirical evidence used to rule out retrieval-miss for 13 of the 19
classified abstain lines (task patterns C and E, the largest single group)
is a set of numbers that do not match what the cited function actually
returns, which means that specific ruling was not verified the way the
record claims it was — the "no code fix needed" conclusion for that block
rests on unreproduced evidence, independent of whether the eventual
correct-abstain verdict happens to still be right for other reasons (the
real top-12 also does not contain an obvious retrieval-tuning skill, so the
verdict may still hold — but the record's stated proof of that does not).
