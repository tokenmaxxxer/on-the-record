---
proposal: issue-2274/performance-engineering build-now delivery
---

# Hunt record — cross-family-judge-p90-timeout

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the "≥50 genuine samples" filter keys only on `duration_ms is not None`, which is a field a mocked/fabricated `subprocess.run` stdout can set freely regardless of real elapsed time; 50+ such near-instant "genuine" ledger entries collapse the p90 cutoff to ~0s and permanently defeat the whole timeout for every real judge call afterward (instant TimeoutExpired -> fail-open every time).
Kind: silent-failure
Seed: consult.py `_skill_judge_perf_samples()` / `_skill_judge_p90_cutoff()` / `_skill_judge_timeout()`, spawn.py re-exports, test/test_spawn_skill_judge_haiku_timeout_overlap.py (uncommitted working-tree diff, ~187 lines across 3 files)
cap_seconds: 120
tier: size:21-200
diff_stat_lines: 178 (+169/-9 across consult.py, spawn.py, test/test_spawn_skill_judge_haiku_timeout_overlap.py)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:20:00Z

### Reproduce
canonical: python3 -c "<script below>" — run this turn against the uncommitted working tree at /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2274-performance-engineering; stdout captured verbatim in the Observed block below.

Ran from repo root (`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2274-performance-engineering`):

```
python3 -c "
import sys, json, tempfile, subprocess as real_subprocess
from pathlib import Path
from unittest import mock

sys.path.insert(0, '.')
import spawn

tmp = Path(tempfile.mkdtemp())
spawn.ROOT = tmp
spawn.consult._sp.ROOT = tmp

candidates = [('some-skill', tmp / 'some-skill', 'skill-repo')]
(tmp / 'some-skill').mkdir()
(tmp / 'roles').mkdir()
(tmp / 'roles' / 'implementation.json').write_text(json.dumps({'model':'sonnet'}))

# a plausible, non-malicious test-style mock: subprocess.run replaced so it
# returns instantly, but the fabricated stdout JSON happens to carry a
# 'duration_ms' key (the exact shape the real claude CLI's --output-format
# json also uses) -- nothing else about it is attacker-controlled or unusual.
session_json = json.dumps({
    'result': json.dumps({'picked': [], 'rejected': [], 'reasons': {}}),
    'duration_ms': 42,
})

with mock.patch.object(spawn, '_consult_cmd_and_env',
                        lambda role, spec, cwd, model, **kw: (['true'], {}, None)), \
     mock.patch.object(spawn.subprocess, 'run',
                        lambda *a, **k: real_subprocess.CompletedProcess(a, 0, stdout=session_json, stderr='')):
    for i in range(60):
        spawn._skill_judge_consult('task text', 'implementation', candidates, 9999, str(tmp))

samples = spawn._skill_judge_perf_samples()
print('n_samples', len(samples), 'min', min(samples), 'max', max(samples))
print('p90 cutoff seconds:', spawn._skill_judge_p90_cutoff())
print('_skill_judge_timeout():', spawn._skill_judge_timeout())
"
```

### Observed
Verbatim stdout from the command above, this turn:
```
n_samples 60 min 0.0 max 0.0
p90 cutoff seconds: 0.0
_skill_judge_timeout(): 0.0
```

`_SKILL_JUDGE_PERF_MIN_EVENTS = 50` was intended to require 50 *genuine, real
model-call* samples before the p90 bound activates. But `_skill_judge_perf_samples()`'s
only genuineness test is `obj.get("duration_ms") is not None` — and `duration_ms`
is whatever key the (mocked or real) subprocess's stdout JSON happens to contain;
it is completely decoupled from the `call_wall_s` the code measures with
`time.monotonic()`. A mocked `subprocess.run()` that returns near-instantly but
whose fabricated stdout includes a `duration_ms` field (the same field name the
real `claude --output-format json` CLI emits, so an ordinary test double
naturally has it) produces `wall_s ≈ 0.0` samples that clear the "genuine"
filter. Once ≥50 of these accumulate in the shared, integrity-unchecked
`runs/ledger.jsonl` (gitignored, appended-to by every process/test on the
machine, per `plumbing.ledger_write()`), `_skill_judge_p90_cutoff()` computes to
~0.0 as shown above, and `_skill_judge_timeout()` — with `SKILL_JUDGE_TIMEOUT`
left unset — returns that same ~0.0, feeding straight into
`subprocess.run(..., timeout=judge_timeout)` for every subsequent *real*
skill_judge call. Every such real call then times out effectively instantly and
falls to BM25 fail-open, defeating the whole cross_family judge step without
any visible error (it looks identical to the pre-existing, expected occasional
timeout/fail-open path).

### Expected
The ≥50-genuine-samples gate should be robust to any caller (test or otherwise)
that can append to `runs/ledger.jsonl` with a non-null `duration_ms`; either the
sample should be validated against the independently-measured `wall_s` (e.g.
reject if `wall_s` is implausibly small, or require both fields to agree it was
a real subprocess execution), or the ledger write path used by real skill_judge
calls should be distinguished from anything a mock can produce (e.g. a
same-process nonce/pid+monotonic marker the reader can verify), so that a
same-shaped-but-fabricated JSON payload cannot silently collapse the timeout
bound to zero for every future real call.
