---
issue: 2250
role: ml-engineering
loop_state: landed
code_under_review: none
type: docs
breaking: none
upstream:
  - path: docs/issue-2208/reports/implementation.md
    sha: 0fc13f242c55bcadca9a99647ba71264d86af9e8
  - path: docs/issue-2208/reports/consult-log.md
    sha: bd497d02d512dc62140b32e27f76a58e2c7053d1
  - path: docs/issue-2211/reports/consult-log.md
    sha: 20555359f9d51cd3cd7bb6cd3b1dac581e8302fa
  - path: tests/test_retrieval_eval.py
    sha: 049731f953b9c1bfdac206651e64622792132e3d
model_id: n/a — this record classifies skill_judge retrieval decisions, no model was trained or retrained
intended_use: n/a
training_data: n/a
eval_data: docs/issue-2208/reports/consult-log.md (tonight's 19 real abstentions, lines 1-21 minus 2 picks)
verdict: pass
---

# issue-2250 — ml-engineering record

## What was done

canonical: docs/issue-2208/reports/consult-log.md (sha bd497d02, lines 1-21)

Classified tonight's 19 real skill-judge abstentions (2026-08-25, from
`docs/issue-2208/reports/consult-log.md`) into correct-abstain /
retrieval-miss / judge-miss, per issue #2250's Ask. Result: 19/19
correct-abstain, derived: classification table below, one row per
consult-log line, verdict column. No retrieval-miss, no judge-miss.
Precision stays clean over this sample (0 wrongful picks observed among the
19 rows below). Because correct-abstain dominates, the remedy is the one
the issue's own Ask #3 prescribes for that outcome: file the specific
missing-skill gap rather than tune the judge or BM25 index — logged in Open
findings below with a resolution path, not filed as a new issue (this role
does not file issues, contract v3 s5).

### Locating "tonight's 19"

canonical: docs/issue-2208/reports/consult-log.md (sha bd497d02); commit
0fc13f24's own `Date:` trailer confirms the repo commits in `+0900` (KST).

`docs/issue-2208/reports/consult-log.md` is the entire #2208 build session's
own consult trace, timestamped 2026-08-24T15:14–15:59 UTC = 2026-08-25T00:14–
00:59 KST — "tonight 2026-08-25" (KST) starts at UTC 15:00 the day before.
The file has exactly 21 `verb=skill_judge` lines, derived: `wc -l
docs/issue-2208/reports/consult-log.md` = 21 (re-run below), of which 2 are
picks (`work-in-english`, lines 2 and 3) and 19 are abstains (lines 1, 4-21
minus 2-3) — an exact match to issue #2250's stated count.

acceptance: wc -l docs/issue-2208/reports/consult-log.md — result:
```
21 docs/issue-2208/reports/consult-log.md
```

I did not additionally pull `docs/issue-2211/reports/consult-log.md`'s 1
abstain (same KST night, immediately adjacent) into the frozen 19-row table
below, to keep the row count matching issue #2250's own frozen number
exactly; it is the same underlying pattern (see Open findings).

acceptance: re-run of #2208's own abstention query (`docs/issue-2208/reports/
implementation.md` @ 0fc13f24, "Upstream basis" footnote), independently
re-run by this session against the current corpus state — result:
```
$ python3 -c "
import re, glob
total = 0; abstain = 0; errors = 0; ok_lines = 0
for path in sorted(glob.glob('docs/*/reports/consult-log.md')):
    for line in open(path, encoding='utf-8'):
        if 'verb=skill_judge' not in line: continue
        m = re.search(r'outcome=\'(.*)\'', line) or re.search(r'outcome=\"(.*)\"', line)
        outcome = m.group(1) if m else None
        total += 1
        if outcome is None: continue
        if outcome.startswith('error'): errors += 1; continue
        ok_lines += 1
        pm = re.search(r'picked=\[([^\]]*)\]', outcome)
        picked = pm.group(1).strip() if pm else None
        if picked == '': abstain += 1
print('total', total, 'errors', errors, 'ok_lines', ok_lines, 'abstain', abstain)
print(f'rate_over_ok={abstain}/{ok_lines}={abstain/ok_lines*100:.1f}%')
"
total 77 errors 5 ok_lines 72 abstain 38
rate_over_ok=38/72=52.8%
```
The corpus has grown since #2208's own snapshot (36 total/18 abstain at
build time, per `docs/issue-2208/reports/implementation.md` @ 0fc13f24, ->
77 total/38 abstain now, per the fenced re-run above) — the cumulative rate
is not the "tonight" figure issue #2250 quotes, which is why classification
below is scoped to the frozen `docs/issue-2208/reports/consult-log.md` file
rather than a re-run of the cumulative query.

### Classification table (19/19 correct-abstain)

canonical: docs/issue-2208/reports/consult-log.md (sha bd497d02, lines cited
per row) and skill-repo SKILL.md files under `$MUSTER_SKILL_REGISTRY_ROOT`
(triggers quoted verbatim below).

Four distinct decisions repeat across the 19 lines (the #2208 session
re-invoked `skill_judge` on the same task text multiple times while building
its own abstention measurement) — grouped below, one row per line as the
acceptance criterion requires.

| line(s) | role | task (id) | candidates seen (from outcome) | class | why |
|---|---|---|---|---|---|
| 1, 11, 18 | execution-observation | **A**: "APPROVE ... phase-2로 계속한다" (issue-2208/execution-observation boilerplate continuation) | rejected: observability-phase-trace, market-analysis-mece-proposal, partnerships-bd-term-sheet-... | correct-abstain | `observability-phase-trace/SKILL.md`'s trigger is "phase-2 signals vs phase-1 *methodology for that surface*" — #2208's own body is BM25/judge-abstention-measurement work, not an observability-signal surface. Contrast `docs/issue-2180/reports/consult-log.md` line 2 (2026-08-24T11:14:47), where the identical boilerplate template correctly picked this skill because issue-2180 is genuinely about RED/USE signals — the judge is discriminating on domain, not failing. |
| 4, 6, 8, 10, 12 | execution-observation | **C**: "Issue #2208: Skill selection follow-ups..." (raw issue body fed as task text) | rejected: work-in-english, adversarial-review, implementation-audit, test-depth-audit, ... (real BM25 top candidates, confirmed below) | correct-abstain | See "Ruled out as retrieval-miss" section below (live BM25 re-run against the real issue #2208 body) — the true top-8 candidates (test-depth-audit, adversarial-review, growth-analytics-metric-selection, implementation-audit, reference-forecast, model-routing, technical-feasibility-verdict-and-timebox-selection, conformance-review-finding-record/verify-finding-record) were all correctly rejectable by their own SKILL.md triggers. |
| 5, 13, 17 | conformance-review | **D**: "APPROVE ... phase-2로 계속한다" (issue-2208/conformance-review boilerplate continuation) | rejected: observability-phase-trace, market-analysis-mece-proposal, verify-severity-classification, ... | correct-abstain | Same reasoning as A. `verify-severity-classification/SKILL.md`'s trigger is "a reproduced defect's finding" in `docs/issue-<n>/reports/defect-verification.md`, not applicable to a conformance-review record for retrieval-tuning work. |
| 7, 9, 14, 15, 16, 19, 20, 21 | conformance-review | **E**: "Issue #2208: Skill selection follow-ups..." (raw issue body, same text as C, different role) | rejected: work-in-english, reference-forecast, test-depth-audit, adversarial-review, ... (real BM25 top candidates, confirmed below) | correct-abstain | Same coverage gap as C — no mounted skill (of 272, per the corrected BM25 re-run below) covers this project's own retrieval/judge-tuning work regardless of which role label is attached to the call. |

Per-class counts, derived: 3+5+3+8=19 (row groups above) — correct-abstain
19, retrieval-miss 0, judge-miss 0.

### Ruled out as retrieval-miss: live BM25 re-run against tasks C/E

acceptance: `spawn._bm25_cross_family_scores()` re-run live against task C/E's
ACTUAL text — `gh issue view 2208 --json body -q .body`, the real #2208 body,
prefixed with the same header the log shows — for both roles seen in the
log — result:
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
for role in ['execution-observation', 'conformance-review']:
    scored = spawn._bm25_cross_family_scores(task_text, role, repo_root)
    print('role', role, 'total scored', len(scored))
    for s, name, d, src in scored[:12]:
        print(f'  {s:.3f} {name}')
    names = [n for s,n,d,src in scored]
    for target in ['ml-engineering-evaluation-discipline','ml-engineering-ml-test-score-scoring']:
        print('  rank', target, names.index(target)+1 if target in names else 'MISSING')
"

role execution-observation total scored 272
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
  rank ml-engineering-evaluation-discipline 105
  rank ml-engineering-ml-test-score-scoring 77

role conformance-review total scored 265
  64.338 test-depth-audit
  55.138 adversarial-review
  51.846 growth-analytics-metric-selection
  50.234 reference-forecast
  50.194 implementation-audit
  47.319 model-routing
  45.617 technical-feasibility-verdict-and-timebox-selection
  45.050 verify-finding-record
  44.023 product-discovery-opportunity-solution-tree
  43.188 pricing-research
  42.915 finance-unit-economics-sensitivity-scenario
  42.813 market-recon
  rank ml-engineering-evaluation-discipline 100
  rank ml-engineering-ml-test-score-scoring 71
```
This corrected re-run reproduces the real candidate names visible (truncated)
in the actual log outcomes cited in the table (`test-depth-audit`,
`adversarial-review`, `implementation-audit`, `reference-forecast`,
`work-in-english` — the last is the static-pinned policy skill, outside the
family-exclusion filter for `execution-observation`/`conformance-review` so
it still competes for those two roles). Checking each real top-8 name
against its own `SKILL.md` trigger (`$MUSTER_SKILL_REGISTRY_ROOT/<name>/
SKILL.md`, read directly): `test-depth-audit` triggers on classifying an
*existing test suite's* assertion depth (Genuine/Execution-Only/Mock-
Dominated/etc.) — task C/E is measuring a judge's abstention rate via a log
query and running a frozen gold-set regression test, not auditing test
assertion quality, so the rejection is correct; `implementation-audit` and
`adversarial-review` both require a *second, structurally independent*
session grading a *completed* deliverable against a spec — task C/E is the
builder's own first-pass investigative work, not a post-hoc audit, so both
rejections are correct; `reference-forecast` triggers on building/auditing a
duration/cost/effort estimate, which task C/E does not do; `growth-analytics-
metric-selection` (North Star metric choice), `conformance-review-finding-
record`/`verify-finding-record` (recording an already-reproduced finding for
different roles' record files), and the product/pricing/finance skills are
all off-domain on inspection. `model-routing` (a blanket "use on every
non-trivial task" policy skill, rank 6) is the one candidate this record
could not independently confirm rejected-vs-picked from the truncated log
text — even if it were picked, it does not supply a retrieval/relevance-
tuning domain skill, so it would not change the correct-abstain verdict for
the underlying gap. Ranks and names above rule out retrieval-miss (BM25 does
surface the true top-8, including `test-depth-audit` at rank 1) and confirm
no judge-miss (every real candidate's own trigger genuinely excludes it).
`grep -li` across all 272 `SKILL.md` files under `$MUSTER_SKILL_REGISTRY_ROOT`
for retrieval/search-relevance/BM25/information-retrieval language (a
separate, independently-run sweep, not part of the BM25 scoring above) turned
up only document-findability skills (`knowledge-management-structure-
findability`, `knowledge-management-taxonomy-tagging`, etc. — Diátaxis
doc-placement, not a code-level relevance pipeline) and `market-recon`/
`api-design-http-semantics` (false-positive string hits, unrelated domains
on SKILL.md inspection) — no skill anywhere in the 272-skill corpus targets
this project's own retrieval-pipeline-tuning domain.

acceptance: `pytest tests/test_retrieval_eval.py -v -o addopts=` (re-run,
confirming no regression from this investigation — no code was touched) —
result:
```
9 passed in 13.32s
```
No gold cases were added (issue #2250's Ask #3 branch for correct-abstain-
dominant is "file the missing-skill list instead" of fixing indexing/judge),
so there is no before/after retrieval-eval delta to show.

## Why

canonical: issue #2250 body, "## Ask" item 3.

The issue's own decision rule (Ask #3) is unambiguous once the class counts
are in: retrieval-miss or judge-miss dominant -> fix that layer;
correct-abstain dominant -> the gap is skill-repository coverage, file the
missing-skill list instead of tuning toward "pick more" (explicitly a
non-goal in the issue). With 19/19 correct-abstain (derived: classification
table above) there is no code-layer defect to fix — BM25 and the judge are
both behaving correctly on this sample: they correctly discriminate
`observability-phase-trace` by whether the underlying issue is really about
signals (the A vs issue-2180 contrast, cited above), and they correctly
abstain when no skill in the 272-skill corpus covers this project's own
retrieval-tuning domain (the live BM25 re-run above). Tuning anything here
would either be a no-op (nothing to change) or actively harmful (loosening
the judge to "pick more" against issue #2250's own precision-must-stay-clean
constraint).

## What did not work

The first draft of the "Ruled out as retrieval-miss" evidence block called
`spawn._bm25_cross_family_scores()` against a hand-paraphrased approximation
of task C/E's text instead of the real issue #2208 body, producing a top-12
that did not reproduce (e.g. it omitted `test-depth-audit`, the real rank-1
candidate, entirely, and mis-stated both ml-engineering skill ranks). Caught
by a before-landing `warrant-hunter` dispatch (stance: assume the
"live-re-run" evidence is fabricated or wrong) — recorded at
`docs/issue-2250/reports/ml-engineering/2026-08-25-hunt-ml-engineering.md`
@ `59f9eef8b87ed977b00d3de947975d0cde69e539`. Fixed in this same checkpoint:
re-ran the query against the real body (`gh issue view 2208 --json body -q
.body`), replaced the evidence block, and re-derived the C/E row reasoning
from the corrected candidate list — the correct-abstain verdict for all 19
lines is unchanged (each real top-8 candidate's own `SKILL.md` trigger
independently excludes it), but the original supporting evidence for that
verdict was not what it claimed to be.

## Upstream basis

- `docs/issue-2208/reports/implementation.md` @ `0fc13f242c55bcadca9a99647ba71264d86af9e8` (canonical: this file, "### 1. Judge abstention rate" section) — landed the abstention-query methodology this record reuses verbatim, the negative-clause BM25 stripping, and the `work-in-english` static pin; its own measurement (18/31, 58.1%, quoted directly from its fenced result block) is issue #2250's "prior" figure.
- `docs/issue-2208/reports/consult-log.md` @ `bd497d02d512dc62140b32e27f76a58e2c7053d1` (canonical: this file, lines 1-21) — the 19-abstain, 2-pick source data classified above.
- `docs/issue-2211/reports/consult-log.md` @ `20555359f9d51cd3cd7bb6cd3b1dac581e8302fa` (canonical: this file, lines 1-2) — the adjacent same-night abstain/pick pair referenced in Open findings.
- `tests/test_retrieval_eval.py` @ `049731f953b9c1bfdac206651e64622792132e3d` — the frozen gate re-run above.
- `docs/issue-2250/reports/ml-engineering/2026-08-25-hunt-ml-engineering.md` @ `59f9eef8b87ed977b00d3de947975d0cde69e539` — before-landing warrant-hunt finding and fix, described in "What did not work" above.

## Open findings

- **Missing-skill gap** (the dominant-class remedy this record's Why section
  points to), canonical: live BM25 re-run above + `grep -li` sweep of
  `$MUSTER_SKILL_REGISTRY_ROOT`: the skill-repository (272 skills, derived:
  `len(scored)` in the BM25 re-run above, across ~43 role families) has no
  skill covering retrieval/relevance-tuning for this project's own
  skill-judge recommender — BM25 indexing hygiene (negative-clause
  stripping), judge-abstention-rate measurement methodology, and
  policy-skill static-pinning decisions. This is not a one-off: issues
  #2205, #2206, and #2208 (canonical: `docs/issue-2208/reports/
  implementation.md` "Upstream basis" section, naming #2205/#2206 as prior
  rounds of the same class of work) all did this exact class of work under
  `role=implementation`, and this session's live BM25 re-run found no
  candidate within reach of any role's top-8 for it. Resolution path: a
  follow-up issue asking a skill-repository-authoring session to add a
  skill (most naturally scoped under `implementation`, matching where this
  work has landed three times) for retrieval/relevance-pipeline tuning and
  judge-abstention measurement — this role does not file issues itself
  (contract v3 s5), so it is logged here rather than filed.
- `docs/issue-2211/reports/consult-log.md` (canonical: this file, line 1)'s
  1 abstain — role=conformance-review, same "issue-<n>/implementation
  branch landed, no record yet" boilerplate trigger as task pattern A/D
  above, same KST night — was not folded into the 19-row table, to keep the
  row count matching issue #2250's frozen number exactly, but it is the
  same class (correct-abstain, same reasoning as A/D — its rejected list
  cites `verify-severity-classification`/`verify-finding-record`/`defect-
  verification-severity-band-assignment`, all defect-verification-role
  skills, none fitting a conformance-review record for landed BM25/pinning
  work). Resolution path: none needed — it strengthens rather than changes
  the correct-abstain verdict.
- This session did not independently re-locate citable consult-log lines
  for the issue's stated "5 appropriate picks" (defect-verification-
  independence, observability-phase-trace, mece-proposal) — acceptance only
  requires classifying the 19 abstentions, and the picks were already
  asserted precision-clean by the issue itself. Two of the three named
  skills were independently confirmed as real historical picks during this
  investigation, canonical: `docs/issue-2180/reports/consult-log.md` line 2
  and `docs/issue-2062/reports/consult-log.md` line 5 (both pick
  `observability-phase-trace`), and `docs/issue-2070/reports/consult-log.md`
  line 1 (picks `market-analysis-mece-proposal`) — but all three are outside
  tonight's UTC window (2026-08-22/23/24 daytime, not the 2026-08-25 KST
  night this record scopes to), so they are not re-cited as tonight's
  evidence. Resolution path: none needed unless a future session disputes
  the precision-clean claim.

## Next steps

None — `loop_state: landed` is terminal; the missing-skill gap above has its
own resolution path (a follow-up issue, not owned by this record) and does
not block landing this classification.

---

skill-verdict: ml-engineering-evaluation-discipline — not-applicable: this task classifies skill_judge retrieval decisions, not an online/offline launch-metric trustworthiness question (no A/B arm split, no SRM check, no launch decision in play).
skill-verdict: ml-engineering-ml-test-score-scoring — not-applicable: no model's production readiness is being scored against the ML Test Score rubric here.
skill-verdict: ml-engineering-model-provenance-versioning — not-applicable: no model card or dataset/model version lineage question is open; frontmatter's model_id/training_data/eval_data fields are marked n/a for the same reason.
skill-verdict: ml-engineering-rollout-promotion-rollback — not-applicable: no rollout staging or rollback-trigger decision is open; nothing shipped to production traffic.
skill-verdict: ml-engineering-serving-pattern-selection — not-applicable: no batch/online/streaming serving-pattern choice is open.
skill-verdict: ml-engineering-slo-definition-tradeoffs — not-applicable: no serving SLO or error-budget policy is being set or audited.
other mounted skills: not triggered
