---
status: proposed
files:
  - spawn.py
  - gates/
  - tests/
  - test/
  - docs/issue-2040/reports/implementation.md
---

## Request

#2040 asks for judgment-based cross-family skill selection: today's
`_cross_family_skill_matches` (spawn.py:7988) ranks purely by raw
lexical-overlap count against candidate skills' "Use when" trigger
sentences, with no weighting for how common a token is across the
candidate pool — producing noise picks (e.g. kimball/finance-ltv-cac for
a REST pagination task) whose trigger condition does not actually match
the task. The issue body originally scoped a haiku-tier consult-judge
stage on top of lexical prefiltering. An operator direction-amendment
comment on the issue changed the phase order: implement a pure-python
BM25 ranker FIRST (IDF weighting should suppress generic-vocabulary
noise without a consult call), replay it over the same >=10-issue
corpus used before, and only add the consult-judge stage if that BM25
replay still shows condition-mismatch picks. Acceptance's replay/trace/
fallback requirements are otherwise unchanged from the issue body.

## Constraints

- No new dependency — BM25 must be pure-python, scored against the
  existing `_skill_trigger_line()` corpus and `_tokenize()` (or a
  drop-in variant of it).
- The determinism guard from issue #2001 (`_cross_family_task_text`
  pinned before later prompt-building appends skill-list text) must
  survive unchanged — BM25 replaces the *scoring function* only, not the
  call-site or its input text.
- Replay corpus: >= 10 real issues from the cycle-1/cycle-2 session
  corpus — reuse `docs/issue-2001/reports/implementation/replay-table.md`'s
  16-pair corpus rather than assembling a new one (same repo, same
  fetch method, already has a documented before/after baseline this
  issue is meant to close).
- Consult-judge stage (if triggered by the replay) must fail open to
  today's lexical top-2 on consult error, log picked+rejected+reasons to
  the consult trace, and add no more than one consult call per spawn.
- Acceptance's per-spawn latency measurement requirement carries into
  whichever stage(s) actually ship.

## Rationale

The survey (docs/issue-2040/reports/implementation/survey.md) ran both a
BM25 spike and a re-run of today's raw-overlap scorer against the
identical 16-pair corpus. BM25 clears `conformance-review-severity-classification`
from 16-of-16 rows down to 7-of-16 — real signal, IDF is doing its job —
but does not clear `model-routing` at all (5-of-16 under both scorers),
because `model-routing`'s trigger sentence is deliberately maximal
("Use this skill on EVERY non-trivial task..."); no token-frequency
statistic, however weighted, can distinguish a genuine match from a
by-design-broad trigger. That is a condition-match judgment, not a
lexical-scoring problem.

Two alternatives were considered and rejected:

- **Ship BM25 alone and stop** (the operator's own preferred outcome if
  the replay had come back clean): rejected because the replay does not
  come back clean — 7/16 and 5/16 residual mismatches on the same corpus
  the issue's own Acceptance criterion targets. Shipping BM25-only here
  would leave the exact noise-pick failure mode the issue exists to
  close, just at a lower rate, with no trace-visible reason attached to
  the remaining mismatches.
- **Tune the BM25 threshold/weighting further instead of adding the
  consult stage** (e.g. penalize skills whose trigger sentence is above
  some length/genericity heuristic, or raise the score-floor past
  "score > 0"): rejected because `model-routing`'s trigger is
  legitimately about breadth-of-applicability, not vocabulary noise — no
  statistical retuning of the same signal (document frequency, term
  weight, length normalization) changes what the sentence means. Only a
  judgment pass that reads the trigger's *condition* against the task's
  actual content can tell these apart, which is exactly the mechanism
  the issue's own body already specified before the amendment.

So this proposal keeps the operator's phase order but reports the
branch it actually resolves to: BM25 replaces the raw-overlap prefilter
(shipped, real precision gain, zero added latency), and the consult-judge
stage is added on top per the issue's original scope, gated on trace
visibility and fail-open behavior, because the same replay corpus the
BM25-alone path was supposed to clear did not clear.

## What will be done

1. Add a pure-python BM25 scorer (`_bm25_topk` or similar name,
   spawn.py, near `_cross_family_skill_matches`) using
   `_skill_trigger_line()` per-candidate documents and the same
   task-text query input as today, replacing `_cross_family_skill_matches`'s
   raw-overlap scoring internals — call-site and signature stay the
   same so spawn.py:8160 does not need to change shape.
2. Re-derive the top-K score floor for BM25 output (today's fixed
   `_CROSS_FAMILY_MIN_OVERLAP=2` doesn't transfer to BM25's score scale);
   document the chosen floor and why in the phase-2 implementation
   record, with the replay numbers behind it.
3. Add a consult-judge stage on top of the BM25-narrowed top-K
   candidates: single cheap consult call (haiku-tier, existing consult
   machinery) receiving the issue body plus the BM25-survived candidates'
   trigger sentences, returning the accepted subset (0-2) with a
   one-line condition-match reason each; reject with reason logged too.
4. Log BM25 scores and consult picked/rejected+reasons to the consult
   trace (`_append_consult_trace`/`_commit_consult_trace` machinery,
   spawn.py:5663-5712) for later precision measurement, per Acceptance.
5. Fail-open path: on consult error, fall back to BM25's own top-2 (not
   today's raw-overlap top-2 — BM25 is now the shipped baseline
   prefilter); add a test asserting this fallback.
6. Replay the full pipeline (BM25 + consult) over the same 16-pair
   corpus and confirm the known noise picks
   (`conformance-review-severity-classification`, `model-routing`) are
   now rejected with stated reasons in the trace, per Acceptance.
7. Measure and record per-spawn added latency (BM25 is O(candidates),
   negligible; the added consult call is the dominant cost — record its
   measured wall-clock delta).
8. Add/update tests under `test/` covering: BM25 ranking determinism,
   the score-floor behavior, the consult-fallback path, and trace
   logging shape.

## Out of scope

- Retuning BM25's k1/b hyperparameters beyond the standard defaults used
  in the spike (1.5/0.75) — no evidence in the replay that non-default
  values would matter; a follow-up can revisit if the phase-2 replay
  surfaces a reason to.
- Building a second/independent replay corpus — the existing 16-pair
  cycle-1/cycle-2 corpus already satisfies Acceptance's >=10-issue floor
  and carries the prior baseline this work compares against.
- Any change to `_skill_trigger_line()`'s trigger-sentence extraction
  format, or to how skills declare their triggers — this issue changes
  the *scorer*, not the corpus format.
- Any change to the role→family skill mapping (`_ROLE_SKILLS`) or to
  same-family skill selection — only cross-family candidate selection is
  in scope.

## Accumulation

The replay script (spike + phase-2 verification) calls `gh issue view`
once per corpus row inline, the same pattern
`docs/issue-2001/reports/implementation/replay-table.md` already used.
If the corpus grows past its current 16 rows across future replays, the
inline-subprocess-per-row shape stays fine at that scale (a one-off
survey/verification script, not a hot path); it should only move into a
shared helper if a future issue turns replay into a routinely-re-run
CI-style check rather than a per-issue phase-1/phase-2 survey step. No
`roles/*.json`-style repeated-file edit is introduced by this change —
the scorer and the consult call are each touched in one place (spawn.py),
not per-role, so there is no per-role file to accumulate edits across.

## How you'll know it worked

- The phase-2 replay over the same 16-pair corpus shows
  `conformance-review-severity-classification` and `model-routing`
  rejected (not present in the final picked set) on the rows the
  existing replay table already marked "No", each with a stated
  condition-match reason visible in the consult trace.
- A consult-error path test confirms fallback to BM25 top-2 with no
  crash and a trace entry marking the fallback.
- Measured per-spawn added latency is recorded in the phase-2 record and
  is dominated by (at most) one consult call, per Acceptance's "<one
  consult call" ceiling.
- `test/test_spawn_cross_family_skill_selection.py` (and any new tests)
  pass, covering BM25 scoring, score-floor behavior, consult
  accept/reject shape, and the fail-open path.
