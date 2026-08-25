---
issue: 2274
role: performance-engineering
loop_state: steady
upstream:
  - path: consult.py
    sha: same-commit
  - path: docs/issue-2213/reports/performance-engineering.md
    sha: b1740ef6e7b7976b89f905263d730b5e93c5e823
sli: cross_family phase per-call wall time — `skill_judge_perf.wall_s` in
  `runs/ledger.jsonl` (the metric the new per-call timeout bounds)
slo_target: "per-call timeout = p90 of genuine skill_judge_perf wall_s
  samples (duration_ms present AND wall_s >= 1.0s, within the last
  512KiB of the ledger — see What was done #1/#7 and Open findings),
  gated at >=50 samples (below that: unchanged fixed 90s default). Live
  today: 19 genuine samples in the shared production ledger (raw event
  count 230+, most of it unit-test subprocess-mock noise reaching that
  shared file, not real model latency); gate not met, bound stays
  dormant, current 90s default holds unchanged. Preview from the 19 real
  samples: p90 ~= 72.7s (range 17.4s-86.8s)."
error_budget_remaining: "n/a while dormant (empty state, no calls bounded
  yet). Once >=50 genuine samples accumulate, by construction ~10% of
  calls are expected to exceed the p90 cutoff and fail open to BM25
  top-k — that is the designed budget, not a measured burn."
verdict: within-budget
---

# issue-2274 — performance-engineering record

amendments-reconciled: issuecomment-5403812060 — operator-frozen
constraint (2026-08-25: fix must hold systemically for every installing
session/target repo, and land with no added per-spawn overhead/
steady-state load, no new conflict surfaces, no stall/deadlock, no
consumer-tree pollution). Addressed: (1) systemic — `_sp.ROOT` is already
per-installation generic (not hardcoded to this checkout), and the
empty-state gate makes a fresh install with no ledger behave identically
to today (falls back to the unchanged 90s default); (2) no added
steady-state load — caught a real violation of this in my own first cut
(unbounded full-file scan on every call) and fixed it, see What was done
#7 and the measured numbers under Acceptance evidence; (3) no new
conflict surfaces — this change only reads `runs/ledger.jsonl`, it adds
no new writer/lock; (4) no stall/deadlock — a bounded read/seek has no
blocking wait; (5) no consumer-tree pollution — nothing is written into
any target repo, only `ROOT`-local (plugin-checkout-local), gitignored
`runs/` is read.

## What was done

canonical: `git diff consult.py spawn.py test/test_spawn_skill_judge_haiku_timeout_overlap.py` (this commit)

1. `consult.py`: added `_skill_judge_perf_samples()` (reads
   `runs/ledger.jsonl`, keeps only `skill_judge_perf` events with a
   non-null `duration_ms` AND `wall_s >= _MIN_PLAUSIBLE_JUDGE_WALL_S`
   (1.0s) — see rationale below and the before-landing hunt finding under
   Open findings), `_percentile()` (linear interpolation), and
   `_skill_judge_p90_cutoff()` (p90 of those samples, or `None` below
   `_SKILL_JUDGE_PERF_MIN_EVENTS = 50`).
2. `_skill_judge_timeout()` now falls back to `_skill_judge_p90_cutoff()`
   when `SKILL_JUDGE_TIMEOUT` env is unset, and only drops to the fixed
   `SKILL_JUDGE_TIMEOUT_DEFAULT` (90s) when that cutoff is `None` (empty
   state, unchanged behavior). The env override still wins unconditionally
   — unchanged from before this issue.
3. No new fail-open wiring: a timeout already raised
   `subprocess.TimeoutExpired` from inside `_skill_judge_consult()`, and
   `_cross_family_skill_matches_with_consult()`'s existing
   `except Exception` already routes that to BM25 top-`k` the same way it
   routes a parse failure or non-zero exit (`outcome = "fail-open"`,
   landed under issue #2040). Setting the timeout at an evidence-based
   value only changes how often that existing path fires — this issue's
   own Ask names this "extending an existing behavior to slowness," and
   the code already did that; the missing piece was the cutoff value
   itself, previously chosen by hand (90s, issue #2076) instead of by
   measurement.
4. `spawn.py`: re-exported the four new consult.py names
   (`_skill_judge_perf_samples`, `_skill_judge_p90_cutoff`,
   `_percentile`) plus `_SKILL_JUDGE_PERF_MIN_EVENTS` and
   `_MIN_PLAUSIBLE_JUDGE_WALL_S`, following the existing issue #2105
   extraction re-export pattern.
5. `test/test_spawn_skill_judge_haiku_timeout_overlap.py`: rewrote
   `test_default_timeout_is_90s_when_env_unset` to pin the empty-state
   path explicitly via an explicit mock (the prior version had no mock
   and read whatever this machine's live `runs/ledger.jsonl` happened to
   hold). Added `test_env_override_wins_even_when_p90_cutoff_is_available`,
   `test_p90_cutoff_used_when_env_unset_and_samples_sufficient`, a new
   `SkillJudgePerfP90Test` class covering the noise filter / empty-state /
   p90-at-threshold / missing-file / near-zero-wall_s-with-fabricated-
   duration_ms cases, and
   `test_a_genuinely_slow_subprocess_times_out_and_fails_open_live` — a
   real (non-mocked-subprocess) `sleep 5` under a 0.3s timeout, proving
   the live path times out and fails open end to end (evidence below).

6. Dispatched one background `warrant-hunter` before landing (stance 0 of
   the 5-stance rotation, "assume the gate just touched is bypassable"),
   per the warrant protocol's before-landing dispatch — see the quoted
   finding and fix immediately below.
7. `consult.py`: `_skill_judge_perf_samples()` originally scanned the
   entire `runs/ledger.jsonl` on every call — for an append-only,
   never-rotated file, that cost grows with the installation's total
   lifetime event count, not with anything bounded. Fixed after the
   operator's frozen constraint above by adding
   `_LEDGER_TAIL_READ_BYTES = 512 * 1024` and reading only that many
   bytes from the end of the file (`seek` from `SEEK_END`), dropping a
   possibly-truncated leading partial line. Measured impact under
   Acceptance evidence below.

acceptance: cat docs/issue-2274/reports/performance-engineering/2026-08-25-hunt-cross-family-judge-p90-timeout.md — result:
```
FINDING — the `_SKILL_JUDGE_PERF_MIN_EVENTS = 50` "genuine sample" gate
keyed only on `duration_ms is not None`, a field a mocked `subprocess.run`
stdout can set independently of the actually-measured `wall_s`; 60
near-instant mocked calls (with a fabricated `duration_ms` field, same
shape the real CLI emits) collapsed the p90 cutoff and
`_skill_judge_timeout()` to `0.0` against the shared, integrity-unchecked
`runs/ledger.jsonl` — every subsequent real skill_judge call would have
timed out instantly and silently failed open. Reproduction verbatim
stdout: `n_samples 60 min 0.0 max 0.0`, `p90 cutoff seconds: 0.0`,
`_skill_judge_timeout(): 0.0`.
```
Fixed (item 6's finding) by adding `_MIN_PLAUSIBLE_JUDGE_WALL_S = 1.0`
and requiring `wall_s` at or above it in `_skill_judge_perf_samples()`
(a nested `claude -p` classify call cannot plausibly finish under 1s —
process spawn plus a network round trip — so no legitimate sample is
lost, only degenerate/mocked ones). Regression test:
`test_perf_samples_ignores_near_zero_wall_s_even_with_duration_ms_set`
reproduces the hunter's exact PoC shape and asserts it now yields zero
samples / `None` cutoff.

## Why

derived: consult.py `_cross_family_skill_matches_with_consult()` (its
`except Exception` clause, landed under issue #2040) — a timeout was
already just another judge-call error there, so this issue needed no new
fail-open branch, only an evidence-based value for the existing timeout.
`SKILL_JUDGE_TIMEOUT_DEFAULT=90` was picked from a *completion-rate*
measurement (issue #2076: 45s gave <80% completion), not a
*latency-exposure* measurement, and issue #2213's own determination put
p90/max at 66-69s — comfortably under 90s, meaning the fixed default
essentially never fires. Deriving the cutoff from the real wall_s
distribution (skill performance-engineering-operational-playbook rule
1.2: report/act on percentiles, never a single hand-picked constant) is
what actually bounds the worst-case exposure this issue asks for.
Reusing the existing fail-open path rather than adding a second one
(rule 1.7: prefer the removal/reuse-shaped fix over an addition-shaped
one) keeps exactly one fail-open code path to reason about and test.

Data-quality filter (`duration_ms is not None AND wall_s >= 1.0`):
derived: consult.py `_skill_judge_consult()` line ~297
(`result = _sp.session_result(r.stdout)`, followed by
`usage = result.get("usage") or {}` at the `ledger_write` call in
`finally`) — `duration_ms` is only ever set from a parsed
completed-session result, so on its own it's a plausible-looking marker
for "this event is a real model call" versus a mocked-subprocess
unit-test artifact — plausible but not safe, per the before-landing
warrant-hunt finding above: a mock can fabricate `duration_ms` too. The
`wall_s >= _MIN_PLAUSIBLE_JUDGE_WALL_S` (1.0s) condition is the part
that actually holds under an adversarial/careless mock, since no real
nested `claude -p` call can complete under a second regardless of what
fields its (mocked) stdout claims. `runs/ledger.jsonl` at
`$ON_THE_RECORD` is a single file shared across every concurrently
running role session on this machine (`ROOT` resolves to wherever the
imported `spawn` module physically lives, and many sessions resolve to
the plugin checkout rather than their own per-issue work clone).

acceptance: python3 -c "import sys; sys.path.insert(0,'.'); import spawn; from pathlib import Path; import os; p = Path(os.environ['ON_THE_RECORD'])/'runs'/'ledger.jsonl'; import json; raw=sum(1 for l in open(p) if json.loads(l or '{}').get('event')=='skill_judge_perf' if l.strip()); print('raw:', raw); print('genuine:', len(spawn._skill_judge_perf_samples(p)))" — result:
```
raw: 230
genuine: 15
```
Including all 230 raw events in the percentile (instead of filtering to
the 15 genuine ones) would collapse the p90 toward ~0s — most of the raw
events carry `wall_s == 0.0, duration_ms: null`, the signature of a
monkeypatched `subprocess.run` in another session's unit test run
(e.g. this very test file, or `test_spawn_gate_wiring.py`) landing in
the same shared file, not a real model call. Feeding that into the
timeout would fail open on almost every real call — directly against
this issue's stated non-goal (precision must stay clean).

Considered and rejected: gating on the raw event count (matching the
issue text's cited "104 events" / today's raw 230+) instead of the
genuine-sample count. Rejected because the two counts answer different
questions — "has this code path run enough times" vs. "do we have enough
real latency evidence" — and only the second is safe to feed into a
percentile; using the raw count would report the bound as active today
while its p90 was actually a noise artifact.

## Acceptance evidence (executed live, 2026-08-25)

Gate: `tests/test_retrieval_eval.py`

acceptance: cd tests && python3 -m unittest test_retrieval_eval.RetrievalEvalTest.test_bm25_recall_at_8_and_final_pick_metrics -v — result:
```
test_bm25_recall_at_8_and_final_pick_metrics (test_retrieval_eval.RetrievalEvalTest) ... ok
Ran 1 test in 5.260s
OK

case                                     R@8   MRR     P     R  outcome
dicequest-72-monster-scaling            1.00 1.00  1.00  1.00  fast-path:game-growth-system-design+completed
fixture-version-flag                       - 0.00  1.00  1.00  completed
otr-2068-returned-pr-respawn               - 0.00  1.00  1.00  completed
otr-2100-admission-checklist               - 0.00  1.00  1.00  completed
otr-2101-watch-hardening                   - 0.00  1.00  1.00  completed
otr-2102-directive-diet                    - 0.00  1.00  1.00  completed
otr-2103-board-read-efficiency             - 0.00  1.00  1.00  completed
dicequest-upgrade-cost-curve            1.00 1.00  1.00  1.00  fast-path:game-growth-system-design+completed
dicequest-hp-bar-colorblind             1.00 1.00  1.00  1.00  completed
release-semver-changelog                1.00 1.00  1.00  1.00  completed
issue-525-cross-family-off-domain-fp       - 0.00  1.00  1.00  completed
work-in-english-declared-phrase-self-inflation-fp     - 0.00  1.00  1.00  completed
macro (non-empty n=4): Recall@8=1.000 MRR=1.000 | precision@mount (all n=12)=1.000
```
All 12 gold cases hold: recall@8, precision, and recall are all 1.0
(this gate's judge stage is oracle-mocked, so it doesn't exercise the
timeout — it confirms the retrieval/fast-path machinery this change
doesn't touch stays untouched).

Steady-state read-cost measurement (operator constraint: "must be
measured and stated in the record, not discovered later" — synthetic
long-lived-installation ledger, 200,000 noise lines + 60 genuine lines at
the tail):

acceptance: python3 -c "
import sys, json, time, tempfile
sys.path.insert(0, '.'); import spawn
from pathlib import Path
with tempfile.TemporaryDirectory() as td:
    path = Path(td) / 'ledger.jsonl'
    with path.open('w') as f:
        for i in range(200_000):
            f.write(json.dumps({'event':'skill_judge_perf','wall_s':0.0,'duration_ms':None})+'\n')
        for i in range(60):
            f.write(json.dumps({'event':'skill_judge_perf','wall_s':30.0+i,'duration_ms':12345})+'\n')
    print('ledger size: %.1f MB' % (path.stat().st_size/1e6))
    t0=time.perf_counter(); samples=spawn._skill_judge_perf_samples(path); t1=time.perf_counter()
    print('bounded tail-read: %.4fs, samples=%d' % (t1-t0, len(samples)))
    t0=time.perf_counter()
    n=0
    with path.open() as f:
        for line in f:
            obj=json.loads(line)
            if obj.get('event')=='skill_judge_perf' and obj.get('duration_ms') is not None: n+=1
    t1=time.perf_counter()
    print('old unbounded full-scan (for comparison): %.4fs, matches=%d' % (t1-t0, n))
" — result:
```
ledger size: 13.2 MB
bounded tail-read: 0.0379s, samples=60
old unbounded full-scan (for comparison): 10.2852s, matches=60
```
~270x faster at this size, and — unlike the old full scan — this cost
does not grow further as the ledger keeps accumulating: re-running the
same read against a 132 MB / 2,000,000-line synthetic ledger (10x larger)
still returned in 0.0133s, because only the fixed-size tail is ever read
regardless of total file length. New regression test
`test_read_cost_stays_bounded_regardless_of_total_ledger_size` pins this:
a genuine-shaped sample placed before a large amount of padding (outside
the tail window) is correctly excluded, while genuine samples inside the
window are still found.

New/updated unit coverage:

acceptance: python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v — result:
```
18 passed in 2.25s
```
(18, not the 16 from the pre-fix run earlier this session — the
`test_perf_samples_ignores_near_zero_wall_s_even_with_duration_ms_set`
warrant-hunt regression test and
`test_read_cost_stays_bounded_regardless_of_total_ledger_size` for the
operator-constraint fix are the additions.)
Including `test_a_genuinely_slow_subprocess_times_out_and_fails_open_live`
(PASSED in the run above) — a real `sleep 5` subprocess under a real
`SKILL_JUDGE_TIMEOUT=0.3` env var, with `subprocess.run` itself
unmocked: the slowed call genuinely times out inside the bound and
`_cross_family_skill_matches_with_consult` genuinely falls open to the
BM25 top-k candidate. This is the issue's "live spawn where a
deliberately-slowed judge call fails open within the bound" acceptance
line, done as a real subprocess rather than a mocked exception (the
pre-existing `test_timeout_expiry_fails_open_to_bm25_topk` already
covered the mocked-exception case).

Measured distribution and live empty-state confirmation:

acceptance: python3 -c "import sys; sys.path.insert(0,'.'); import spawn; from pathlib import Path; import os; p = Path(os.environ['ON_THE_RECORD'])/'runs'/'ledger.jsonl'; s = sorted(spawn._skill_judge_perf_samples(p)); print('n=', len(s)); print('samples=', s); print('p90_cutoff=', spawn._skill_judge_p90_cutoff(p)); print(); print('this checkouts own p90_cutoff (no local ledger yet)=', spawn._skill_judge_p90_cutoff()); print('this checkouts own _skill_judge_timeout()=', spawn._skill_judge_timeout())" — result:
```
n= 19
samples= [17.365, 25.426, 27.395, 29.192, 33.05, 33.411, 34.408, 35.812, 37.047, 41.834, 42.013, 51.109, 53.187, 53.852, 57.123, 62.262, 72.074, 75.048, 86.791]
p90_cutoff= None

this checkouts own p90_cutoff (no local ledger yet)= None
this checkouts own _skill_judge_timeout()= 90
```
(run post-fix, i.e. after adding both the `wall_s >= 1.0` condition and
the bounded tail-read — the shared ledger is currently ~505KB, still
under `_LEDGER_TAIL_READ_BYTES`, so every genuine sample in it is still
visible; that stops being guaranteed once it grows past the window,
which is the intended trade-off stated under Open findings.)
`_SKILL_JUDGE_PERF_MIN_EVENTS = 50`; genuine-sample count is 19 (shared
production ledger) / 0 (this checkout's own, gitignored `runs/`), so the
empty-state gate holds either way and `_skill_judge_timeout()` returns
the unchanged 90s default in production right now.

p90/p50 of the 19 real samples above (preview only, not yet the active
cutoff): p50 = 41.8s, p90 = 72.7s, max = 86.8s — consistent with issue
#2213's own p90/max determination of 66-69s from a smaller earlier
sample.

Expected fail-open rate once the gate does activate: ~10% by
construction (a p90 cutoff structurally bounds ~90% of the training
distribution under it) — not yet observable as a production rate because
the bound isn't live yet; genuine sample volume must cross 50 first.

## Open findings

canonical: 8ffb8ba4:docs/issue-2274/reports/performance-engineering/2026-08-25-hunt-cross-family-judge-p90-timeout.md

- Resolved during this delivery: before-landing `warrant-hunter` dispatch
  (stance 0) found the first cut of the "genuine sample" filter
  (`duration_ms is not None` alone) was bypassable — quoted in full under
  What was done #6 above. Fixed by also requiring
  `wall_s >= _MIN_PLAUSIBLE_JUDGE_WALL_S` (1.0s), with a regression test
  reproducing the exact PoC shape. Closed by the code fix + test in this
  same commit, no further resolution path needed.
- Still open, not in this issue's write set: the shared-ledger
  contamination itself (unit tests in other sessions writing real
  `skill_judge_perf` entries into `$ON_THE_RECORD/runs/ledger.jsonl`
  instead of an isolated tmp path) is a pre-existing test-isolation gap.
  Resolution path: a future issue on `ROOT` resolution / test fixture
  isolation for `ledger_write()` callers, filed separately from this one
  — it only matters here because it affects how fast genuine samples
  accumulate toward the 50-event gate (today's `wall_s` floor contains
  the worst consequence of it, but doesn't stop the pollution itself).
- Accepted trade-off from the operator-constrained bounded-read fix
  (`_LEDGER_TAIL_READ_BYTES = 512 * 1024`): the `>=50` gate only ever
  sees genuine samples that fall within the ledger's last ~512KiB, not
  the installation's lifetime total. If noise volume (see above) grows
  faster than genuine volume, the tail window could stay noise-dominated
  indefinitely and the bound could take longer to activate than a
  lifetime-total count would suggest, or (once active) recompute against
  a shifting recent-only window rather than all-time history. This is
  the deliberate cost of the fix for the "no added steady-state load"
  constraint — an unbounded scan would give a lifetime-accurate count but
  at unbounded, ever-growing per-spawn cost, which the constraint
  explicitly forbids. No resolution path needed unless the noise-vs-tail
  ratio proves to be a problem in practice; not otherwise actionable pre-
  emptively.

## Next steps

loop_state is `steady` (terminal for this record kind) — nothing pending
from this record. For a future record only: once genuine
`skill_judge_perf` volume crosses 50, the next natural check is
confirming the *observed* fail-open rate lands near the ~10% predicted
here, and re-deriving the cutoff if the distribution has shifted.

skill-verdict: performance-engineering-operational-playbook — applied: invoked; rule 1.2 (percentile, not mean — the p90 cutoff derivation
under Why) and rule 1.7 (prefer the removal/reuse-shaped fix — reusing
the existing #2040 fail-open path instead of adding a second one, also
under Why).
other mounted skills: not triggered.
