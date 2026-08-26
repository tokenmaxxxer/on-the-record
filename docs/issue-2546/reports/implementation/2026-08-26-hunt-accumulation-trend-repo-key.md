---
proposal: docs/issue-2546/reports/implementation.md
---

# Hunt record — accumulation-trend-repo-key

## after-proposal — stance 1: does the accumulation-trend repo-keying fix (commit cab3255b, gates/closure_sweep.py) genuinely satisfy issue #2546's acceptance criteria, or is there a silent-failure / composition-regression / design-error at this handoff point?

Verdict: FINDING — `_accumulation_repo_key()` keys on directory basename, which collides for two genuinely distinct repos swept in the same tick set by the pre-existing multi-repo sweep loop (`watchdog._board_wide_sweep_all`), silently reintroducing the exact cross-repo-delta-reported-as-growth bug issue #2546 was filed to fix.
Kind: composition
Seed: git show cab3255b -- gates/closure_sweep.py (the issue-2546 fix commit); also examined watchdog.py `_board_wide_sweep_all`/`_roster_target_repos`/`_repo_identity` (events.py) as the multi-repo call site this fix must compose with.
cap_seconds: n/a (not provided by dispatcher)
tier: default
diff_stat_lines: 1 file changed, 40 insertions(+), 11 deletions(-) (gates/closure_sweep.py only)
started_at: 2026-08-26T00:00:00Z
ended_at: 2026-08-26T00:45:00Z

### Reproduce
```
cd /tmp && rm -rf wrap1 wrap2 && mkdir -p wrap1/checkout wrap2/checkout
cd wrap1/checkout && git init -q && git remote add origin https://github.com/orgA/repo-alpha.git \
  && printf 'import subprocess\nsubprocess.run(["echo","a"])\nsubprocess.run(["echo","b"])\n' > a.py \
  && git add a.py && git -c user.email=a@a -c user.name=a commit -q -m init
cd /tmp/wrap2/checkout && git init -q && git remote add origin https://github.com/orgB/repo-beta.git \
  && printf 'import subprocess\nsubprocess.run(["echo","c"])\n' > b.py \
  && git add b.py && git -c user.email=a@a -c user.name=a commit -q -m init

rm -rf /tmp/state_root && mkdir -p /tmp/state_root
MUSTER_STATE_ROOT=/tmp/state_root python3 -c "
import sys
sys.path.insert(0, '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation/gates')
import closure_sweep
from pathlib import Path
rootA = Path('/tmp/wrap1/checkout')   # git origin orgA/repo-alpha
rootB = Path('/tmp/wrap2/checkout')   # git origin orgB/repo-beta -- a DIFFERENT repo
t1 = closure_sweep.accumulation_trend(rootA)
print('tick1 (repo-alpha):', closure_sweep.format_accumulation_trend(t1))
t2 = closure_sweep.accumulation_trend(rootB)
print('tick2 (repo-beta):', closure_sweep.format_accumulation_trend(t2))
"
cat /tmp/state_root/accumulation_trend.json
```

For comparison, the identity function the same call site (`watchdog._board_wide_sweep_all`,
which already computes `label = _sp._repo_identity(repo)` for this exact `repo` Path to
label output and to key the cross-workspace board-sweep lock filename, `watchdog.py:836`
and `:1218`) correctly distinguishes the two:
```
python3 -c "
import sys
sys.path.insert(0, '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation')
import events
from pathlib import Path
print('repo_identity A:', events._repo_identity(Path('/tmp/wrap1/checkout')))
print('repo_identity B:', events._repo_identity(Path('/tmp/wrap2/checkout')))
"
```

### Observed
```
tick1 (repo-alpha): [checkout] accumulation-trend: no prior tick data (first run) — shape1_sites=2
tick2 (repo-beta): [checkout] accumulation-trend: shape1_sites=1 (-1)
{"checkout": {"shape1_sites": 1, "shape1_ok": true}}
```
Both roots resolve to `_accumulation_repo_key() == "checkout"` (the shared basename), so
repo-beta's first-ever tick is misreported as a `-1` delta against repo-alpha's prior count
— cross-repo arithmetic printed as growth/shrinkage, silently, with no error and no signal
that the two repos were ever conflated. This is the identical failure shape issue #2546
describes, just triggered by same-tick-set basename collision (via the pre-existing
`_board_wide_sweep_all` roster-of-distinct-target-repos loop, which is not gh-gated and
runs `accumulation_trend()` for every `repo` in `targets`) rather than by
sequential-tick alternation of a single shared unkeyed file.

`events._repo_identity()` (already used by the very same sweep loop, at `watchdog.py:836`
for the per-repo print label and `:1218` for the cross-workspace lock filename) correctly
distinguishes the two as `repo-alpha` and `repo-beta` — it is local-only (reads
`git remote get-url origin`, no network/gh-API call) and only falls back to directory
basename when there's no origin remote. It was available, already imported transitively via
`_sp`, and already proven collision-resistant at this exact call site, but
`_accumulation_repo_key()` reimplements basename-only keying instead of reusing it.

### Expected
`_accumulation_repo_key()` should use the same collision-resistant identity the sweep loop
already established for this purpose (`_repo_identity`, or equivalent), or the fix should at
minimum note that repo-keying by basename is only safe under an invariant ("checkout
basenames are unique across everything one orchestrator install ever sweeps in the same
process") that nothing in the codebase enforces or documents, and that the adjacent
multi-repo call site does not rely on.
