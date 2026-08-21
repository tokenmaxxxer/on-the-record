---
name: skill-invocation-baseline-measurement
subject: issue-1960
---

# Baseline measurement: relevance-gated Skill-invocation rate (issue-1960, phase A)

Subject: issue-1960
kind: report
loop_state: reported

## Method

canonical: docs/issue-1960/reports/execution-observation/survey.md (join point + relevance heuristic)

Per-session join: `plugins[].path` containing `/skill-registry/skills/`
gives mounted skills; any `"type":"tool_use","name":"Skill"` line gives
invocation count. Relevance gate: session counted in the denominator iff
`mounted_count > 0` (role mapping actively mounted >=1 skill-repository
skill). Measured via `/tmp/measure_skill_invocation.py` against a sample:
the 40 most-recent distinct sessions by log mtime, plus additional
sessions hand-picked to cover role diversity not present in the 40
most-recent window (conformance-review, observability, market-analysis,
architecture, product-discovery, technical-feasibility, and one zero-byte
log to exercise the unmeasurable path).

```
canonical: /tmp/measure_skill_invocation.py (script run 2026-08-22, this session)
$ python3 /tmp/measure_skill_invocation.py   # (see script body in appendix)
```

## Results table

`derived: python3 /tmp/format_table.py` (reproduces the table below from
`/tmp/measurement_output.jsonl`, itself produced by the script above).

| session | status | mounted_count | mounted skills | Skill invocations | relevance-gated |
|---|---|---|---|---|---|
| on-the-record-issue-1960-execution-observation | measured | 0 | (none) | 0 | no |
| on-the-record-issue-1958-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1959-test-authoring | measured | 1 | test-authoring-isolation-and-fixture-strategy | 0 | yes |
| on-the-record-issue-1955-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1950-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1943-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1945-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1942-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1937-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1934-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1932-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1927-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1928-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1921-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1920-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1917-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1912-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1911-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1907-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1906-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1901-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1900-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1896-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1892-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1891-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1884-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1882-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1883-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1874-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1873-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1875-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1867-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1866-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1862-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1861-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1854-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1853-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1847-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1843-conformance-review | measured | 0 | (none) | 0 | no |
| on-the-record-issue-1844-implementation | measured | 4 | implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint | 0 | yes |
| on-the-record-issue-1199-observability | measured | 0 | (none) | 0 | no |
| on-the-record-issue-1199-market-analysis | measured | 0 | (none) | 0 | no |
| tokenmaxxxer-core-issue-189-architecture | measured | 0 | (none) | 0 | no |
| my-travel-issue-11-product-discovery | measured | 0 | (none) | 0 | no |
| on-the-record-issue-1199-technical-feasibility | measured | 0 | (none) | 0 | no |
| on-the-record-issue-473-conformance-review | **unmeasurable** (no-init-plugins-line, 0-byte log) | - | - | - | - |

Every row in this table was independently measured by the script, not
extrapolated; the repeated `implementation`-role pattern is the finding
itself.

## Derived: relevance-gated invocation rate

```
canonical: /tmp/measurement_output.jsonl (this session's script output)
derived: python3 -c "import json; rows=[json.loads(l) for l in open('/tmp/measurement_output.jsonl')]; m=[r for r in rows if r['status']=='measured']; u=[r for r in rows if r['status']!='measured']; rel=[r for r in m if r['mounted_count']>0]; inv=[r for r in rel if r['skill_calls']>0]; print('total sampled', len(rows)); print('measured', len(m), 'unmeasurable', len(u)); print('relevance-gated denominator', len(rel)); print('invoked>=1', len(inv)); print('rate', len(inv)/len(rel))"
total sampled: 47
measured: 46, unmeasurable: 1
relevance-gated denominator (mounted_count > 0): 38
sessions with >=1 Skill tool invocation: 0
relevance-gated invocation rate: 0 / 38 = 0.0%
```

## Interpretation

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md#derived-relevance-gated-invocation-rate (the fenced block directly above, this same file)

Every relevance-gated session in the table above — every `implementation`
and `test-authoring` role row, the only roles in the sample currently
skill-repository-mapped with a non-zero `mounted_count` — shows `0` in the
"Skill invocations" column despite a non-zero `mounted_count`. This
reproduces, at a larger sample size, the single-session gap noted in the
issue's own Request text (canonical: `gh issue view 1960` — the issue-1955
phase-2 session: mounted skill names appeared 21 times in context, zero
Skill invocations). The fenced derivation above shows the gap is not
sample noise: the "invoked>=1" count over the relevance-gated denominator
is exactly zero, not merely a low rate.

Rows with `mounted_count: 0` (execution-observation, conformance-review,
observability, market-analysis, architecture, product-discovery,
technical-feasibility in the table above) belong to roles not yet migrated
to skill-repository mapping (issue-1955/#1758 covers only `implementation`
and `test-authoring` in this sample), so per the relevance heuristic in
survey.md they are correctly excluded from the denominator rather than
counted as a 0-rate false positive.

## Baseline established — phase B is needed

canonical: docs/issue-1960/reports/execution-observation/baseline-measurement.md#derived-relevance-gated-invocation-rate (fenced derivation above, this same file)
The fenced derivation above shows a real gap, not a healthy rate, so per
the issue's acceptance empty-state clause: phase B (single-change
improvement) proceeds, not closed as not-needed. The specific single change
is proposed separately:
docs/issue-1960/proposals/phase-b-skill-invocation-nudge.md.

## What did not work

None.

## What was done

Ran the join+count script against the sampled sessions (40 most-recent +
role-diversity picks), derived the relevance-gated denominator and rate,
and recorded the empty-state (unmeasurable) case per the acceptance
criterion.

## Why

Directly answers issue-1960 acceptance check 1: "a measurement artifact
lists, per sampled recent role session, the mounted skills and the count
of Skill invocations, with the relevance-gated rate derived in the
artifact."

## Upstream

canonical: docs/issue-1960/reports/execution-observation/survey.md
basis: gh issue view 1960

## Open findings

- Sample is drawn overwhelmingly from `implementation`-role sessions
  because that role currently dominates recent session-log volume.
  ```
  canonical: this session, live command
  derived: ls ~/.tokenmaxxxer/work/*.session*.log | sed -E 's/\.session.*$//' | sed -E 's/^on-the-record-issue-[0-9]+-//' | sort | uniq -c | sort -rn | head -3
  323 implementation
  46 execution-observation
  33 conformance-review
  ```
  The relevance-gated rate is real for the roles it covers but should not
  be read as representative of roles not yet skill-repository-mapped.
- This baseline does not distinguish "skill not invoked because irrelevant
  to this specific task" from "skill not invoked despite being relevant" —
  the coarse role-mapping relevance gate (see survey.md) cannot make that
  finer distinction. A rate this low at this granularity is a strong
  enough signal to proceed to phase B regardless.

kind: report
loop_state: reported
