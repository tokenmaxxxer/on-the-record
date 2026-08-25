---
issue: 2250
role: execution-observation
kind: verify-record
loop_state: cleared
upstream:
  - path: docs/issue-2250/reports/ml-engineering.md
    sha: 33ef4af23cd5692574addf6501585d8fc6e63712
subject: docs/issue-2250/reports/ml-engineering.md at commit 33ef4af2 (PR #2292, open, targets issue #2250) — its correct-abstain classification of tonight's skill-judge abstentions
test: >
  wc -l docs/issue-2208/reports/consult-log.md and manual re-count of
  picked=[] vs picked=[...] lines;
  independent re-run of spawn._bm25_cross_family_scores() against the real,
  live gh issue view 2208 body for both roles seen in the log
  (execution-observation, conformance-review);
  direct read of 4 candidates' own SKILL.md trigger clauses
  (test-depth-audit, adversarial-review, implementation-audit,
  reference-forecast);
  python3 -m pytest tests/test_retrieval_eval.py -v -o addopts=;
  skill-registry directory count under $MUSTER_SKILL_REGISTRY_ROOT
result: passed
assertedBy: independent re-execution, issue-2250/execution-observation session, 2026-08-25
---

# issue-2250 — execution-observation record

## What was done

Independent execution-observation of PR #2292 (`issue-2250: classify
tonight's skill-judge abstentions — correct-abstain, file missing-skill
gap`, open, head commit `33ef4af2`, targets issue #2250, ships
`docs/issue-2250/reports/ml-engineering.md` — untracked on this branch
since PR #2292 is still open, not yet merged to `main`; read via `gh pr
diff 2292` — with `code_under_review: none`). PR #2292's own
correct-abstain count claim is re-derived independently below (canonical:
check 1 below, this session's own `wc -l` + manual recount), not taken on
its word. This session wrote no retrieval/judge code and did not re-read
PR #2292's own record as evidence — it re-derived the two load-bearing
empirical claims from scratch: the abstain/pick count from the raw consult
log, and the live BM25 re-run PR #2292's classification of task pattern
C/E depends on.

Check 1 — raw abstain/pick count, `docs/issue-2208/reports/consult-log.md`:

```
$ wc -l docs/issue-2208/reports/consult-log.md
21 docs/issue-2208/reports/consult-log.md
```
canonical: `docs/issue-2208/reports/consult-log.md`, this session's own
read of all 21 lines — result: `picked=[]` on 19 of them (lines 1, 4-21
minus 2-3), `picked=[work-in-english=...]` on exactly lines 2 and 3;
derived: 21 total − 2 picks = 19 abstains, matching PR #2292's stated
19-abstain/2-pick split exactly, 0 divergence.

Check 2 — live BM25 re-run against the real issue #2208 body, both roles.
Fetched the body live (own `gh issue view` call, own temp file, not PR
#2292's record transcript) and called the same scoring function directly:

```
$ gh issue view 2208 --json body -q .body > /tmp/issue2208_body_indep.txt
$ python3 -c "
import spawn, os
from pathlib import Path
body = open('/tmp/issue2208_body_indep.txt', encoding='utf-8').read()
task_text = ('Issue #2208: Skill selection follow-ups from #2205: judge '
             'abstention rate, negative-clause indexing, pinning policy '
             'skills\n\n') + body
repo_root = Path(os.environ['MUSTER_SKILL_REGISTRY_ROOT'])
for role in ['execution-observation', 'conformance-review']:
    scored = spawn._bm25_cross_family_scores(task_text, role, repo_root)
    print('role', role, 'total scored', len(scored))
    for s, name, d, src in scored[:12]:
        print(f'  {s:.3f} {name}')
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
```
canonical: this session's own `gh issue view 2208` fetch + own
`spawn._bm25_cross_family_scores()` call — result: PASS, exact match
(scores and rank order both) to the corrected evidence block in PR #2292's
own record. This is significant because PR #2292's own record documents a
"What did not work": a before-landing warrant-hunter caught that record's
*first draft* citing fabricated/paraphrased numbers for this exact call
(wrong top-12 names, inflated scores, missing rank-1 `test-depth-audit`
entirely) — this session's from-scratch re-run reproduces the *corrected*
numbers the record landed with, not the discarded fabricated ones,
confirming the fix that followed the warrant-hunter finding actually holds
and is reproducible by an independent session, not just internally
self-consistent.

Check 3 — spot-check 4 candidates' own `SKILL.md` trigger clauses, read
directly under `$MUSTER_SKILL_REGISTRY_ROOT` (not taken from PR #2292's
paraphrase of them) — canonical: check 2's re-run above for each
candidate's rank:

- `test-depth-audit/SKILL.md` (rank 1 for both roles, per check 2):
  triggers on auditing an *existing test suite*, classifying each test
  Genuine/Execution-Only/Mock-Dominated/Happy-Path-Only/Dead. Task C/E is
  a log-query measurement plus a frozen-gate regression re-run, not test
  suite auditing — correct-abstain confirmed.
- `adversarial-review/SKILL.md` (rank 2 for both roles, per check 2):
  triggers on setting up a *structurally independent* evaluator session
  with no shared context with the builder, to critique an AI-made
  artifact the builder can't self-grade. Task C/E is the builder's own
  first-pass investigative work, not a handoff to a separate blind
  evaluator — correct-abstain confirmed.
- `implementation-audit/SKILL.md` (rank 4 for execution-observation, rank
  5 for conformance-review, per check 2): triggers on a two-session
  protocol where a structurally independent evaluator grades a
  *completed* implementation against extracted spec claims. Same
  reasoning as adversarial-review — no completed deliverable being handed
  to a separate grading session here — correct-abstain confirmed.
- `reference-forecast/SKILL.md` (rank 5 for execution-observation, rank 4
  for conformance-review, per check 2): triggers on building or auditing
  a duration/cost/effort estimate against comparable past cases. Task C/E
  builds no such estimate — correct-abstain confirmed.

canonical: direct `SKILL.md` reads under `$MUSTER_SKILL_REGISTRY_ROOT`, this
session — result: PASS, all 4 rejections independently confirmed correct
against each skill's own trigger text, no divergence from PR #2292's
per-candidate reasoning.

Check 4 — regression gate re-run:

```
$ python3 -m pytest tests/test_retrieval_eval.py -v -o addopts=
9 passed in 4.16s
```
canonical: this session's own re-run — result: PASS, 9 passed = 0 failed +
0 skipped, matches PR #2292's stated 9-passed with no code changed.

Check 5 — corpus size sanity check underlying the "272 skills" claim:

```
$ find $MUSTER_SKILL_REGISTRY_ROOT -maxdepth 1 -mindepth 1 -type d | wc -l
273
```
canonical: this session's own listing — derived: 273 skill directories on
disk, 272 scored once the `execution-observation` family is excluded from
its own cross-family candidate pool (`total scored 272` in check 2's own
output line) — matches PR #2292's stated corpus size, 0 divergence.

## Why

Per this role's governing skill
(`defect-verification-independence-from-upstream-verdicts`), a coding/
classification record's own pasted evidence is a claim pending independent
re-derivation, not evidence in its own right — doubly so here, since PR
#2292's own record documents that its first-draft evidence for this exact
BM25 call did not reproduce and had to be corrected mid-session by a
before-landing warrant-hunter finding. That history is precisely the
failure mode this role exists to catch independently rather than take on
the builder's word that the fix stuck. This session's task explicitly named
two things to re-derive rather than re-read: the live BM25 re-run against
the real (not paraphrased) issue #2208 body, and a spot-check of 4
candidates' `SKILL.md` triggers.

canonical: this session's own `gh issue view 2208` fetch and
`spawn._bm25_cross_family_scores()` call (check 2 above) plus this
session's own direct `SKILL.md` reads under `$MUSTER_SKILL_REGISTRY_ROOT`
(check 3 above) — result: both re-derivations match PR #2292's landed
(corrected) claims exactly, no divergence.

## Upstream basis

- `docs/issue-2250/reports/ml-engineering.md` at commit `33ef4af2` (PR
  #2292, still open — untracked on this branch, read via `gh pr diff
  2292`) — the classification and evidence this record independently
  re-derives rather than re-cites.
- `docs/issue-2208/reports/consult-log.md` at sha
  `bd497d02d512dc62140b32e27f76a58e2c7053d1` — the raw 21-line source this
  session re-counted in check 1.
- `spawn.py`'s `_bm25_cross_family_scores()` and the skill repository under
  `$MUSTER_SKILL_REGISTRY_ROOT` (273 skill directories, check 5 above) —
  the function and corpus re-invoked directly in check 2.
- Issue #2208's own live body — canonical: `gh issue view 2208 --json body
  -q .body`, fetched fresh this session (own file, not PR #2292's).
- `tests/test_retrieval_eval.py` — the regression gate re-run in check 4.

## Open findings

none — canonical: checks 1-5 above, this session's own re-derivations
(`gh issue view 2208`, `spawn._bm25_cross_family_scores()`, direct
`SKILL.md` reads, `pytest tests/test_retrieval_eval.py`, and the
`$MUSTER_SKILL_REGISTRY_ROOT` directory listing); all 5 reproduce PR
#2292's landed claims with no divergence. This session's assigned scope
(per the spawning task) was the abstain count plus a live BM25 re-run and
a 4-candidate `SKILL.md` spot-check for task pattern C/E — the group PR
#2292's own record flags (in its "What did not work" section) as having
previously failed to reproduce, and therefore the correct group to
prioritize verifying. This session did not separately re-verify task
patterns A/D's two remaining `SKILL.md` triggers
(`observability-phase-trace`, `market-analysis-mece-proposal` /
`verify-severity-classification`) beyond confirming via check 1's own log
read that those consult-log lines are genuinely `picked=[]`; that is a
scope note against the assigned task, not a defect found in PR #2292.

## Next steps

None — loop_state is terminal (`cleared`, kind `verify-record`). PR #2292
is still open (not yet merged) — canonical: `gh pr view 2292 --json
state -q .state`, this session's own query, result `OPEN`; this record's
independent re-derivation matches its classification and evidence
exactly, with no divergence to hand back.
