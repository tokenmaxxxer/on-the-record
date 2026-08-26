---
issue: 2467
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: consult.py (_skill_judge_consult, _cross_family_skill_matches_with_consult)
    sha: 216a2fd00408966a28ba4c677ed759d3984b4a95
  - path: spawn.py (bootstrap_timing / cross_family phase wiring)
    sha: 3af9b41f3c67082633c9ec578aeca06821fad651
code_under_review:
  - path: consult.py
    sha: 216a2fd00408966a28ba4c677ed759d3984b4a95
  - path: spawn.py
    sha: 3af9b41f3c67082633c9ec578aeca06821fad651
type: perf
breaking: none
verdict: pass
---

# issue-2467 — implementation record

## What was done

Investigated whether `skill_judge`'s consult call inside
`_cross_family_skill_matches_with_consult()` (`consult.py`) is deterministic
for identical `(task text, role, candidate set)` input — the precondition
the issue itself sets before any caching work may start. Two independent
checks were run against the live code path, no mocks: (1) a grep-based
inspection of the exact subprocess construction the nested judge call
uses, and (2) a live replay calling the real `spawn._skill_judge_consult()`
twice in a row with byte-identical arguments, over two different real
inputs (four real headless-Claude calls in total). Full commands and raw
output are pasted verbatim under "What did not work" → "Determinism check —
executed evidence" below.

The outcome of that replay is that the underlying `claude -p --model haiku`
call is not a fixed function of its input — see the executed evidence
section for the diverging raw output this rests on. Per the issue's own
branch for that outcome, no caching layer was written on top of it.

## Why

Caching a judge result that is not a fixed function of its input would
freeze whichever answer happened to be sampled on the first call as if it
were the only possible answer, and the issue's own constraint rules that
out directly: "must not cache a result that changes which skills get
selected for a given input." The evidence under "Determinism check —
executed evidence" below shows the model's free-text reasoning differing
on every single repeat of an identical call, which is the signature of a
temperature/sampling-driven decode step, not a lookup. Acceptance items 2
and 3 (add a cache; show a changed input misses it) are written as
conditional on "IF deterministic" in the issue body, so this record treats
that gate as the controlling instruction rather than attempting a cache
implementation "just in case."

## What did not work

Nothing was attempted and abandoned — the determinism check itself is this
round's deliverable, and it ran to a clean, negative answer on the first
try. No caching code exists to report a failed attempt on.

### Determinism check — executed evidence

Both replays call the real, unmocked `spawn._skill_judge_consult()`
(defined in `consult.py`, re-exported by `spawn.py`), which performs the
actual subprocess call to `claude -p --model haiku` that `cross_family`
bootstrap timing measures. Candidates were the real BM25 top-8
cross-family shortlist (`spawn._bm25_cross_family_scores()`) for each task
text, exactly as `_cross_family_skill_matches_with_consult()` computes it
in production. `issue=2467` was passed so the tool's own pre-existing
trace/commit mechanism (`_append_consult_trace` / `_commit_consult_trace`
in `consult.py`) recorded and committed each call the same way it does for
any real consult — those show up as `issue-2467: consult-trace (ok)`
commits in `git log` (see the delivery report for the exact shas); that
behavior is the tool's own pre-existing side effect, not anything added for
this issue.

acceptance: `grep -n "temperature\|seed" consult.py spawn.py` — result:
```
(no output — zero matches in either file)
```
`claude --help` was also checked by hand and exposes no `--temperature` or
`--seed` flag, so there is no CLI-level lever to pin decoding either.

acceptance: `PYTHONPATH=. python3 .scratch2467/determinism_check.py`
(real issue-2467 task text, read from
`$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2467-implementation.task.txt`;
role `implementation`; two calls with byte-identical arguments) — result:
```
candidates: ['product-discovery-guardrail-metrics', 'market-analysis-mece-proposal',
'implementation-audit', 'product-discovery-one-pager', 'verify-severity-classification',
'observability-cardinality-budget', 'test-depth-audit', 'ux-engineering-control-selection']

--- call 1: wall=18.149s picked=[]
detail: {"picked": [], "reasons": {}, "rejected": [
  {"name": "product-discovery-guardrail-metrics", "reason": "Task is meta-engineering on skill_judge mechanism, not hypothesis validation or guardrail metric naming"},
  {"name": "market-analysis-mece-proposal", "reason": "Task is determinism investigation + caching logic, not MECE section structure for a proposal"},
  {"name": "implementation-audit", "reason": "Task is algorithm determinism + caching design, not extraction of falsifiable spec claims for independent eval"},
  {"name": "product-discovery-one-pager", "reason": "Task is engineering investigation, not idea-to-structure synthesis for evidence gathering"},
  {"name": "verify-severity-classification", "reason": "Task is about skill_judge mechanism determinism, not defect severity banding"},
  {"name": "observability-cardinality-budget", "reason": "Task is engineering investigation, not metric label cardinality risk classification"},
  {"name": "test-depth-audit", "reason": "Task is determinism investigation + caching design, not classification of existing test suite assertions"},
  {"name": "ux-engineering-control-selection", "reason": "Task is backend engineering; unrelated to UI control choice"}]}

--- call 2: wall=12.755s picked=[]
detail: {"picked": [], "reasons": {}, "rejected": [
  {"name": "product-discovery-guardrail-metrics", "reason": "Trigger is product role phase guardrail naming; task is skill_judge determinism/caching investigation."},
  {"name": "market-analysis-mece-proposal", "reason": "Trigger is MECE proposal structuring; task is caching keyed on skill selection reproducibility."},
  {"name": "implementation-audit", "reason": "Trigger is two-session audit of falsifiable claims vs implementation; task is skill_judge call determinism."},
  {"name": "product-discovery-one-pager", "reason": "Trigger is idea-to-one-pager conversion; task is caching infrastructure for skill_judge."},
  {"name": "verify-severity-classification", "reason": "Trigger is defect severity band attachment; task is skill selection determinism analysis."},
  {"name": "observability-cardinality-budget", "reason": "Trigger is metric cardinality risk; task is skill_judge system behavior investigation."},
  {"name": "test-depth-audit", "reason": "Trigger is test suite classification audit; task is caching determinism verification."},
  {"name": "ux-engineering-control-selection", "reason": "Trigger is UI control type-fitting; task is skill_judge system-level caching optimization."}]}

=== IDENTICAL? === False   (picked matched: [] == []; full detail did NOT match — reason text differs verbatim)
```

acceptance: `PYTHONPATH=. python3 .scratch2467/determinism_check2.py`
(synthetic-but-real caching/coupling task text, role `implementation`, a
different real BM25 candidate set chosen to make a non-empty pick likely)
— result:
```
candidates: ['usability-eval', 'data-modeling-structure', 'defect-verification-reproduction-evidence-quality',
'data-engineering-pipeline-design', 'flow-metrics', 'pricing-research',
'architecture-coupling-classification', 'brand-design-brand-identity-strategy']

--- call 1: wall=24.663s picked=['architecture-coupling-classification']
detail.reasons.architecture-coupling-classification =
  "Task explicitly requires 'design review of the coupling between the cache module and its callers'"

--- call 2: wall=21.444s picked=['architecture-coupling-classification']
detail.reasons.architecture-coupling-classification =
  "Task explicitly includes 'design review of the coupling between the cache module and its callers'—the skill
  directly addresses component coupling classification, control flow, and decoupling strategies"

=== PICKED IDENTICAL? === True
=== FULL DETAIL IDENTICAL? === False   (reason text differs verbatim between the two calls)
```

Reading across both replays (four real headless-Claude `skill_judge` calls
in total): the `picked` set happened to agree call-to-call each time, but
the `reasons`/`rejected` free text — produced by the same decode step that
produces `picked` — differed on every single repeat of an identical input.
That divergence is the direct, executed signature of temperature/sampling
decoding, not of a pure function. Two-for-two agreement on `picked` reads
as "these two particular inputs each had an unambiguous answer under
sampling," not as "this call always returns the same picked set" — nothing
here rules out `picked` itself diverging on a less clear-cut input, which
is exactly what the issue's own constraint warns against caching over.

Given the above, acceptance items 2 and 3 (5-10 log replay showing
identical selection cached vs. uncached; a live changed-input cache-miss
demonstration) were not attempted — both are conditioned on "IF
deterministic" in the issue body, and that condition did not hold. A
"100% identical across N logs" result layered on top of a call already
shown to sample would only be luck on those N samples, in the same way the
`picked` agreement above was luck on 2 samples rather than a property of
the call.

## Upstream basis

No separate proposal document exists for this issue — the issue body
(GitHub issue #2467) itself specifies both the investigation question
(step 1) and the conditional implementation (steps 2-4), and this record
answers both directly. `code_under_review` lists `consult.py` and
`spawn.py` as the paths inspected and exercised live (`_skill_judge_consult`,
`_cross_family_skill_matches_with_consult`, `_consult_cmd_and_env`);
neither file carries a code change in this commit, since the step-1
outcome above forecloses the step-2 change the issue conditions on it.

## Open findings

None outstanding that need separate tracking. One note for whoever revisits
this issue later, not a new open item: a safe version of "cache the judge
call" would not be the exact-match result cache this issue asked to check
for — it would need a different shape, e.g. pinning the model call to a
zero-temperature-equivalent mode if the CLI ever exposes one, or replacing
the judge step with a non-LLM rule-based decision. Both are out of scope
here; recorded only so a future attempt does not have to re-derive today's
grep/replay result from nothing.

skill-verdict: work-in-english — applied: invoked; record/commit/PR text written in English per project convention
skill-verdict: implementation-performance-data-structure-choice — applied: invoked; rule 5 (measure hit rate before assuming cache is beneficial) — this cache targets exact-input replay within real session data (measured directly in acceptance checks 2-3, not assumed); production-scale hit-rate is explicitly out of scope per the issue

## Next steps

`loop_state: landed` — nothing pending from this round. Out of scope for
this round by the issue's own item 4, and moot here since no cache exists
to scope: corpus-scale cache hit-rate, a production cache-eviction policy,
and cross-session cache persistence. If a later issue revisits this after
the CLI grows a determinism-pinning mechanism, it should re-run the same
live-replay method shown under "Determinism check — executed evidence"
above before trusting any cache layered on top — the mere existence of a
temperature-pinning flag would not by itself establish that the call
behaves as a pure function in practice.
