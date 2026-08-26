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

The script below was re-run after a warrant-hunter review (below) found the
first pass's cited `.scratch2467/determinism_check.py` had been cleaned up
and was no longer reproducible from the record alone — the block is now the
script source (`cat`) immediately followed by its real, live execution
(`python3`), matching this repo's `.scratch*`-citing precedent
(`docs/issue-1730/reports/implementation.md`).

acceptance: `cat .scratch2467v2/determinism_check3.py && PYTHONPATH=. python3 .scratch2467v2/determinism_check3.py`
(real issue-2467 task text, matching `$MUSTER_WORKSPACE_ROOT/on-the-record-issue-2467-implementation.task.txt`;
role `implementation`; `repo_root=spawn._skill_repo_root()`,
`home=Path.home()`, `target_repo_root=Path(cwd)` — the exact arguments
`_spawn_one()` passes at `spawn.py:2606-2611`; two calls with
byte-identical arguments) — result:
```
$ cat .scratch2467v2/determinism_check3.py
import sys
from pathlib import Path
sys.path.insert(0, ".")
import spawn as _sp

task_text = ("Fix issue #2467: investigate whether skill_judge's consult call in "
             "_cross_family_skill_matches_with_consult is deterministic for "
             "identical input; if so, add caching keyed on (task text, role, "
             "candidate set), verified narrowly against 5-10 real existing "
             "session logs (before/after wall-clock, identical skill selection "
             "required). Explicitly out of scope: corpus-scale claims, "
             "production cache eviction policy.")
role = "implementation"
issue = 2467
cwd = str(Path(".").resolve())

repo_root = _sp._skill_repo_root()
scored = _sp._bm25_cross_family_scores(task_text, role, repo_root,
                                        home=Path.home(),
                                        target_repo_root=Path(cwd))
candidates = [(name, d, source) for _, name, d, source
              in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]]
print("candidates:", [name for name, _d, _s in candidates])

for i in (1, 2):
    picked, detail = _sp._skill_judge_consult(task_text, role, candidates, issue, cwd)
    print(f"\n--- call {i}: picked={[p.name for p in picked]}")
    print("reasons:", detail.get("reasons"))
    print("rejected reasons:", [r.get("reason") for r in detail.get("rejected", [])])

$ PYTHONPATH=. python3 .scratch2467v2/determinism_check3.py
candidates: ['implementation-audit', 'model-routing', 'marketing-channel-selection', 'product-discovery-guardrail-metrics', 'product-discovery-one-pager', 'market-analysis-mece-proposal', 'design-artifact-user-scenario', 'technical-writing-persuasion-trust']

--- call 1: picked=[]
reasons: {}
rejected reasons: ['Task is implementing caching, not applying a two-session audit protocol with adversarial review against extracted falsifiable claims', 'Standing instruction for all non-trivial tasks, but this task specifies direct implementation work, not a routing decision', 'Task is technical implementation, not channel budget allocation', 'Task is technical development, not product hypothesis measurement setup', 'Task is implementation with verification, not idea structuring', 'Task is technical, not phase-1 proposal content verification', 'Task is technical caching implementation, not narrative user journey', 'Task is implementation and verification, not adoption-facing documentation']

--- call 2: picked=[]
reasons: {}
rejected reasons: ['Audit protocol applies to evaluating implementation against a spec; this task is implementing a feature (caching), not auditing an existing implementation.', 'Triggers on routing decisions (what-to-delegate); this task requests direct implementation of a fix, not routing advice.', 'Domain mismatch: task is technical caching implementation, not marketing budget allocation.', 'Domain mismatch: task is engineering, not product discovery or metric naming.', 'Domain mismatch: task is engineering, not product idea structuring.', 'Domain mismatch: task is engineering, not market or proposal analysis.', 'Domain mismatch: task is engineering, not user scenario authoring.', 'Domain mismatch: task is engineering implementation, not adoption-facing documentation.']

real	0m57.291s
```

=== IDENTICAL? === False — `picked` matched ([] == []) but the `rejected`
reason text differs verbatim, word-for-word, on every one of the 8
candidates between the two calls to the same real 8-name candidate set —
the same sampled-decode signature as the original (now-unreproducible) pass,
confirmed independently on a third real headless-Claude replay with real,
committed evidence this time.

acceptance: `cat .scratch2467v2/determinism_check4.py && PYTHONPATH=. python3 .scratch2467v2/determinism_check4.py`
(synthetic-but-real caching/coupling task text, role `implementation`, same
real `_spawn_one()` argument shape as the block above, a different real
BM25 candidate set chosen to make a non-empty pick likely) — result:
```
$ cat .scratch2467v2/determinism_check4.py
import sys
from pathlib import Path
sys.path.insert(0, ".")
import spawn as _sp

task_text = ("Implement a cache module for the skill_judge consult result. "
             "This requires a design review of the coupling between the cache "
             "module and its callers, and a decision on the cache module's "
             "data structure and eviction strategy.")
role = "implementation"
issue = 2467
cwd = str(Path(".").resolve())

repo_root = _sp._skill_repo_root()
scored = _sp._bm25_cross_family_scores(task_text, role, repo_root,
                                        home=Path.home(),
                                        target_repo_root=Path(cwd))
candidates = [(name, d, source) for _, name, d, source
              in scored[:_sp._CROSS_FAMILY_CONSULT_TOPN]]
print("candidates:", [name for name, _d, _s in candidates])

for i in (1, 2):
    picked, detail = _sp._skill_judge_consult(task_text, role, candidates, issue, cwd)
    print(f"\n--- call {i}: picked={[p.name for p in picked]}")
    print("reasons:", detail.get("reasons"))
    print("rejected reasons:", [r.get("reason") for r in detail.get("rejected", [])])

$ PYTHONPATH=. python3 .scratch2467v2/determinism_check4.py
candidates: ['architecture-coupling-classification', 'code-architecture', 'content-strategy-content-governance-ownership', 'risk-management-response-strategy-selection', 'brand-design-brand-identity-strategy', 'org-design-hiring-rubric-structured-interview', 'experiment-trust', 'product-discovery-guardrail-metrics']

--- call 1: picked=['architecture-coupling-classification', 'code-architecture']
reasons: {'architecture-coupling-classification': 'Task explicitly requires design review of coupling between cache module and callers, and deciding on coupling model', 'code-architecture': 'Task requires designing a new cache module spanning potential multiple files with structural decisions (data structure, eviction strategy) that outlive initial implementation'}

--- call 2: picked=['architecture-coupling-classification', 'code-architecture']
reasons: {'architecture-coupling-classification': 'Task explicitly requires design review of coupling between cache module and callers; skill directly addresses classifying and deciding on component coupling', 'code-architecture': 'Building a new cache module with structural decisions (data structure, eviction strategy) that will outlive the initial implementation; skill covers proactive structure decisions for new modules'}

real	0m24.406s
```

=== PICKED IDENTICAL? === True (`['architecture-coupling-classification', 'code-architecture']` both times)
=== FULL DETAIL IDENTICAL? === False — reason text differs verbatim between the two calls, same as above

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
skill-verdict: implementation-performance-data-structure-choice — not-applicable: invoked to check before treating this as a cache-design task, but the outcome turned on call determinism/correctness (no cache was built), not on any of the skill's six data-structure/algorithm/removal rules — none of them govern whether a non-deterministic call may be cached at all

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
