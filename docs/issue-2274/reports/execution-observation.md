---
issue: 2274
role: execution-observation
kind: verify-record
loop_state: cleared
upstream:
  - path: consult.py (PR #2304, open, head 2dcbc085688c3434aaf928c5a08f813d1815f82d)
    sha: 2dcbc085688c3434aaf928c5a08f813d1815f82d
subject: PR #2304 (issue-2274: bound cross_family judge phase at evidence-based p90 timeout, fail-open to BM25 top-k), head commit 2dcbc085688c3434aaf928c5a08f813d1815f82d, code_under_review — consult.py / spawn.py / test/test_spawn_skill_judge_haiku_timeout_overlap.py
test: >
  from-scratch full-file scan + manual linear-interpolation percentile of
  $ON_THE_RECORD/runs/ledger.jsonl (not calling any PR code) cross-checked
  against the PR's own _skill_judge_perf_samples()/_skill_judge_p90_cutoff()
  run against the same real shared ledger; independent live-timeout
  reproduction (own script, own td, own timeout value, unmocked
  subprocess.run, real `sleep 5`) of the deliberately-slowed fail-open
  case; python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v;
  python3 -m unittest tests.test_retrieval_eval.RetrievalEvalTest.test_bm25_recall_at_8_and_final_pick_metrics -v
result: passed
assertedBy: independent re-execution, issue-2274/execution-observation session, 2026-08-25
---

# issue-2274 — execution-observation record

## What was done

Independent execution-observation of PR #2304 (`issue-2274: bound
cross_family judge phase at evidence-based p90 timeout, fail-open to
BM25 top-k`, open, head commit `2dcbc085`, targets issue #2274 —
`Closes #2274`). Per this session's mounted skill
(`defect-verification-independence-from-upstream-verdicts`), the two
load-bearing empirical claims in PR #2304's own record
(`docs/issue-2274/reports/performance-engineering.md` — untracked on
this branch, PR #2304 is still open and not yet merged to `main`; read
via `gh pr diff 2304`) — the measured ledger distribution/cutoff, and
the live fail-open demonstration — were re-derived from scratch in this
session rather than cited from that record.

The PR's changed files (`consult.py`, `spawn.py`,
`test/test_spawn_skill_judge_haiku_timeout_overlap.py`) were checked out
into an isolated `git worktree` at `/tmp/pr2304-review` (branch
`pr-2304-review`, fetched from `refs/pull/2304/head`), separate from this
branch's own working tree, and pointed at the real shared ledger via
`$ON_THE_RECORD/runs/ledger.jsonl` — the same file the PR's own record
reads and the same file every concurrent role session on this machine can
append to.

Check 1 — re-derive the cutoff from the real ledger, two independent
ways.

canonical: this session's own commands, executed live this turn from
`/tmp/pr2304-review` against `$ON_THE_RECORD/runs/ledger.jsonl`.

```
$ wc -l "$ON_THE_RECORD/runs/ledger.jsonl"
4654 .../runs/ledger.jsonl
```

(a) Own from-scratch scan — full file, no tail bound, hand-written
`json.loads` per line, hand-written genuineness filter
(`event == "skill_judge_perf" AND duration_ms is not None AND wall_s >=
1.0`), hand-written linear-interpolation percentile function (not
imported from the PR):

acceptance: python3 -c "<own from-scratch full-file scan + manual percentile script, no PR imports>" — result:
```
raw skill_judge_perf events (full-file, no tail bound): 928
genuine (duration_ms present AND wall_s>=1.0), full-file: 24
genuine samples: [16.29, 17.365, 21.861, 24.531, 25.426, 27.216, 27.395,
  29.192, 33.05, 33.411, 34.408, 35.812, 37.047, 40.317, 41.834, 42.013,
  51.109, 53.187, 53.852, 57.123, 62.262, 72.074, 75.048, 86.791]
manual p50: 36.4295
manual p90: 69.1304
min/max: (16.29, 86.791)
threshold (50) met: False
```

(b) PR's own `_skill_judge_perf_samples()` / `_skill_judge_p90_cutoff()`,
called directly against the same real ledger from the worktree checkout:

acceptance: python3 -c "import spawn; ... spawn._skill_judge_perf_samples(p); spawn._skill_judge_p90_cutoff(p)" (from /tmp/pr2304-review) — result:
```
ledger size bytes: 893091
PR-code n= 23
PR-code samples= [16.29, 17.365, 21.861, 24.531, 25.426, 27.216, 27.395,
  29.192, 33.411, 34.408, 35.812, 37.047, 40.317, 41.834, 42.013, 51.109,
  53.187, 53.852, 57.123, 62.262, 72.074, 75.048, 86.791]
PR-code p90_cutoff= None
```

derived: comparing (a) against (b) directly above — the two runs agree
on every sample except one: `33.05` appears in the own-scan full-file
result (a) but not in the PR-code bounded-tail-read result (b), because
the ledger has grown to 893KB — past the PR's own
`_LEDGER_TAIL_READ_BYTES = 512*1024` window — since the PR's record was
authored (which measured a 505KB ledger and 19 samples; both counts have
since grown, other sessions kept appending to the shared file between
then and this check). This is not a new defect: the PR's own "Open
findings" section already discloses this exact trade-off ("the >=50 gate
only ever sees genuine samples that fall within the ledger's last
~512KiB... could take longer to activate than a lifetime-total count
would suggest") — check 1 confirms that disclosed trade-off is already
live and observable in the real shared ledger right now, one sample
early, not merely theoretical.

Both derivations agree on the conclusion that matters for correctness
today: genuine-sample count is below the `_SKILL_JUDGE_PERF_MIN_EVENTS =
50` gate (23 or 24, either way <50), so the p90 bound stays dormant and
`_skill_judge_timeout()` must fall through to the unchanged fixed 90s
default.

acceptance: python3 -c "import spawn, os; os.environ.pop('SKILL_JUDGE_TIMEOUT', None); print(spawn._skill_judge_timeout())" (from /tmp/pr2304-review, against the real shared ledger) — result:
```
this checkout _skill_judge_timeout() against real shared ledger: 90
```

matching PR #2304's own claim of "empty-state gate correctly holds
today."

Check 2 — independent live reproduction of the deliberately-slowed
fail-open case. Own script (not the PR's test file), own temp dir, a
different timeout value (0.4s vs. the PR's 0.3s) and a real unmocked
`sleep 5` subprocess.run call.

acceptance: python3 -c "<own script: mock.patch.object(spawn, '_consult_cmd_and_env', ... (['sleep','5'], ...)); SKILL_JUDGE_TIMEOUT=0.4; time.monotonic() around spawn._cross_family_skill_matches_with_consult(...)>" — result:
```
consult-trace 커밋 실패 — ... (pre-existing, unrelated to the timeout path)
[implementation] skill_judge 자문 실패 — BM25 top-2 로 fail-open: Command
  '['sleep', '5']' timed out after 0.4 seconds
elapsed_s= 0.404
matches= [PosixPath('/tmp/does-not-need-to-exist-independent-check')]
outcome= fail-open
PASS: real unmocked sleep(5) subprocess genuinely timed out within the
  bound and fell open to BM25 top-k
```

`elapsed_s = 0.404` (bounded near the 0.4s timeout, not the full 5s
sleep) and `outcome == 'fail-open'` with the BM25-scored candidate
returned unchanged — reproduces the PR's claimed "live spawn where a
deliberately-slowed judge call fails open within the bound" acceptance
line end to end, independently, this turn.

Check 3 — full shipped test suite and the issue's stated acceptance gate,
run from the same isolated worktree.

acceptance: python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py -v (from /tmp/pr2304-review) — result:
```
============================== 18 passed in 1.17s ==============================
```

acceptance: cd tests && python3 -m unittest test_retrieval_eval.RetrievalEvalTest.test_bm25_recall_at_8_and_final_pick_metrics -v (from /tmp/pr2304-review/tests) — result:
```
test_bm25_recall_at_8_and_final_pick_metrics ... ok
Ran 1 test in 0.577s
OK
macro (non-empty n=4): Recall@8=1.000 MRR=1.000 | precision@mount (all n=12)=1.000
```

Both runs above, executed live this turn, show all 18 unit tests passing
and the acceptance gate's 12 gold cases all holding (recall@8/precision/
recall = 1.0), matching the PR's own reported numbers exactly.

## Why

Per `defect-verification-independence-from-upstream-verdicts`: this
issue's acceptance criterion is specifically evidentiary ("report the
chosen cutoff and its expected fail-open rate from the measured
distribution... provenance: executed-live"), so accepting the PR
record's own pasted numbers at face value would defeat the point of an
independent execution-observation. Re-scanning the real ledger from
scratch, with a hand-written filter and percentile function rather than
importing the PR's own `_skill_judge_perf_samples`/`_percentile`, and
separately also calling the PR's own functions against the same file,
lets any divergence between "what the code computes" and "what the raw
data actually contains" surface as a disagreement between (a) and (b) in
Check 1. The live fail-open re-run in Check 2 was written independently
(own script, own timeout value, own temp target) rather than re-running
the PR's own test file, to avoid trusting a test double the PR authored
to prove its own point.

derived: Check 1/(a) vs (b) above — no divergence found beyond the
disclosed, already-open tail-window trade-off (one sample, `33.05`, now
falls outside the PR's bounded-read window as the ledger has grown past
authoring time; the gate's dormant/active conclusion is unaffected
either way since both counts are <50).

## Upstream basis

- PR #2304, head commit `2dcbc085688c3434aaf928c5a08f813d1815f82d`
  (`issue-2274/performance-engineering` branch on
  `tokenmaxxxer/on-the-record`), fetched this turn via
  `git fetch origin pull/2304/head:pr-2304-review` and checked out into
  `git worktree add /tmp/pr2304-review pr-2304-review`.
- `$ON_THE_RECORD/runs/ledger.jsonl` (the real, shared production
  ledger; not a fixture) — 4654 lines, 893091 bytes at check time this
  turn.
- Issue #2274 itself (`gh issue view 2274`, read this turn) for the
  acceptance criteria being checked against.

## Open findings

canonical: this record's own Check 1 above (own from-scratch full-file
scan (a) vs. PR-code bounded-tail-read (b), executed live this turn
against `$ON_THE_RECORD/runs/ledger.jsonl`).

None new. One existing open finding from PR #2304's own record
(`_LEDGER_TAIL_READ_BYTES` bounded-read trade-off: genuine samples older
than the last ~512KiB window drop out of the p90 computation) is
independently confirmed by that same Check 1 comparison to already be
live in the shared production ledger (one genuine sample, `33.05`, now
falls outside the window) — no new resolution path needed beyond what
that record already states, since the gate stays correctly dormant (<50
genuine samples either way, 23 vs. 24) regardless of which of the two
counts is used.

## Next steps

loop_state is `cleared` (terminal for `verify-record`) — nothing pending
from this record.

derived: Check 1's tail-window finding above — once genuine
`skill_judge_perf` volume crosses 50 in the shared ledger, a follow-up
session should re-run the same from-scratch scan against the ledger at
that time to confirm the active cutoff and observed fail-open rate,
since the tail-window trade-off noted above means the first activation's
cutoff will be computed from whatever genuine samples happen to still be
within the last 512KiB at that moment, not from full history.
