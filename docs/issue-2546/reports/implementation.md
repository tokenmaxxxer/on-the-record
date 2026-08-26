---
issue: 2546
role: implementation
author: implementation
loop_state: done
upstream:
  - path: gates/closure_sweep.py
    sha: same-commit
code_under_review:
  - gates/closure_sweep.py
type: fix
breaking: "none — advisory-only output format changes (line now carries a `[<repo>]` prefix and legacy unkeyed state files are migrated on first read), no gate behavior or exit codes change"
verdict: pass
---

# issue-2546 — implementation record

## What was done

`gates/closure_sweep.py`'s `accumulation_trend()`/`format_accumulation_trend()`
pair was rewritten to make the advisory state repo-keyed instead of a single
shared counter file:

- Added `_accumulation_repo_key(root)` — delegates to `spawn._repo_identity(root)`
  (= `events._repo_identity`, `events.py:331-344`) as the stable,
  human-readable repo identifier. `_repo_identity` is local-only (one
  `git remote get-url origin` subprocess call, no `gh` API call) and parses
  the GitHub org/repo out of the origin URL, falling back to checkout
  directory basename only when there is no GitHub origin remote. **This
  replaces an earlier version of this function that returned
  `root.resolve().name` (bare checkout directory basename) directly — see
  "What did not work" below for why that was changed.**
- `accumulation_trend()` now reads `runs/accumulation_trend.json` as a
  `{repo_key: {shape1_sites, shape1_ok}}` mapping. A legacy (pre-#2546)
  unkeyed file has non-dict top-level values, so it fails the
  `all(isinstance(v, dict) for v in loaded.values())` check and the whole
  thing is discarded (treated as "no usable prior") rather than raising or
  being misread as another repo's data.
- The prior used for delta computation is looked up as `all_state.get(repo_key)`
  — only that same repo's own previous entry, never another repo's.
- On write, only `all_state[repo_key]` is updated and the full (now-keyed)
  mapping is written back, migrating the file to the new shape on that same
  write.
- `format_accumulation_trend()` prints `trend["repo"]` in a `[<repo>]` prefix
  on all three branches (error / first-run / delta), e.g.
  `[on-the-record] accumulation-trend: shape1_sites=365 (+0)`.

derived: `git diff HEAD -- gates/closure_sweep.py` — result: diff touches only
`_accumulation_repo_key` (new), `accumulation_trend`, and
`format_accumulation_trend`; no other functions in the file changed.

## Why

Root cause (issue text, verified by reading the file at `HEAD` before editing
— see Open findings for the line-number correction):

```
   474	def accumulation_trend(root: Path) -> dict:
   ...
   485	    state_path = state_paths.orchestrator_state_path(_ACCUMULATION_TREND_STATE)
   486	    prior = None
   487	    if state_path.is_file():
   488	        try:
   489	            prior = json.loads(state_path.read_text(encoding="utf-8"))
   490	        except (OSError, ValueError):
   491	            prior = None
   492	
   493	    current = _current_accumulation_counts(root)
   494	    result = {"current": current, "has_prior": prior is not None}
   495	    if prior is not None and current["shape1_ok"]:
   496	        result["prior"] = prior
   497	        result["delta"] = {"shape1_sites": current["shape1_sites"] - prior.get("shape1_sites", 0)}
```
derived: `git show cdf80483a583faf29ee343db8ca17a112c61c158:gates/closure_sweep.py | nl -ba | sed -n '474,497p'` — result: quoted above verbatim.

`state_paths.orchestrator_state_path()` resolves to one fixed file
(`gates/state_paths.py:34-41`, `return STATE_ROOT / filename`, no repo
argument in the signature at all) regardless of which repo `root` the
watchdog is currently sweeping. `prior` above is therefore whatever the
previous *process* happened to write, independent of which repo that
process was sweeping — so `delta` at line 497 can subtract repo B's count
from repo A's count and both get reported as if they were the same repo's
growth/shrinkage over time. Fix: give the state file per-repo keys and scope
both the prior lookup and the write to `repo_key`, per the issue's required
fix shape (numbered items 1-5 in the issue). `_repo_slug()`
(`spawn.py`/`plumbing.py`, gh-API-backed) was considered and rejected as the
repo-identity source: `watchdog.py`'s `_run_local_only_signals` docstring
(read at `watchdog.py:915-921`) documents `accumulation_trend` as one of the
signals that "runs regardless of gh quota/backoff gating" specifically
because it makes no gh calls; adding one here would silently break that
invariant. `root.resolve().name` (checkout directory basename) matches the
issue's own suggested option and needs no network call. **Deviation, applied
after initial landing: basename keying was replaced with
`spawn._repo_identity(root)` — see "What did not work" for why. This does
not reopen the gh-quota concern above: `_repo_identity` makes exactly one
`git remote get-url origin` subprocess call, never a `gh` API call, so the
`_run_local_only_signals` invariant still holds.**

derived: `grep -n "repo_name\|repo_root\|REPO_NAME\|_repo_slug\|repo_slug" gates/*.py` —
result: found `spawn._repo_slug` (defined via `plumbing._repo_slug` in
`plumbing.py`, gh-API-backed) and `flows._cwd_repo_name` (a
workspace-dir-naming-convention parser not applicable to a plain checkout
root); neither was reused as-is, see Open findings.

## What did not work

The first implementation of `_accumulation_repo_key()` returned
`root.resolve().name` (bare checkout directory basename), reasoning that it
matched the issue's own suggested option and needed no network call (see Why
above for the full rejection-of-`_repo_slug()` reasoning, which still holds).
This was verified live against two real repos before landing (Verification
b/c below, unchanged) — but those two repos (this checkout, basename
`on-the-record-issue-2546-implementation`, and `$CLAUDE_PLUGIN_ROOT_CORE`,
basename `core`) happened to have different directory basenames, so the
verification exercised the "two different repos → two different keys" path
without ever exercising the "two different repos → same basename" path. The
flaw was basename keying's actual failure mode: any two distinct repos
(different git origin) checked out under the same directory name — e.g. two
worktrees both named `checkout/`, which is exactly the pattern the
multi-repo sweep loop in `watchdog._board_wide_sweep_all` can produce when
juggling several repos' worktrees — collide on the same state key, silently
reintroducing the exact cross-repo-delta-reported-as-growth bug issue #2546
was filed to fix, just triggered by same-tick-set basename collision instead
of sequential-tick alternation of a single shared unkeyed file.

canonical: `docs/issue-2546/reports/implementation/2026-08-26-hunt-accumulation-trend-repo-key.md`
— a warrant-hunter probe run against commit `cab3255b` caught this via a
constructed two-repo, same-basename reproduction (`repo-alpha`/`repo-beta`,
both checked out under a directory literally named `checkout`), quoted in
full in that report's Observed section: both roots resolved to
`_accumulation_repo_key() == "checkout"`, so repo-beta's first-ever tick was
misreported as a `-1` delta against repo-alpha's prior count. The same
report also pointed out that `watchdog._board_wide_sweep_all` already calls
`_sp._repo_identity(repo)` at this exact call site (`watchdog.py` ~836 for
the per-repo print label, ~1218 for the cross-workspace lock filename) and
that function is proven collision-resistant there. Resolution: replaced
`_accumulation_repo_key()`'s body with `spawn._repo_identity(root)` (this
commit), re-ran the original three checks plus a fresh two-real-repo
same-basename collision repro against the corrected code — see Verification
below, "post warrant-hunter fix" section.

## Upstream basis

No prior docs/issue-2546/ artifacts existed in this worktree before this
record (issue went straight from filing to build-now implementation in this
session, `CORE_BUILD_NOW=1`, no separate phase-1 proposal commit). Basis is
the issue body itself (root-cause citations) plus direct reads of
`gates/closure_sweep.py`, `gates/state_paths.py`, `watchdog.py`, `spawn.py`,
`plumbing.py`, and `gates/flows.py` performed in this session.

derived: `ls docs/issue-2546/` (run at task start, before this record was
written) — result: only the `reports/` skeleton directory existed, no other
phase artifacts.

## Open findings

1. The issue text cited root-cause line numbers as `closure_sweep.py:472`
   (state_path resolution), `:476` (prior read), and `:484-486` (delta
   computation). Reading the actual file at the commit this branch was built
   from (`cdf80483`) shows the real lines are 485 (state_path), 486 (prior
   init), and 494-497 (delta computation) — the code and behavior described
   are exactly right, only the issue's line numbers were off by roughly
   9-13 lines (likely measured against a slightly different revision than
   `cdf80483`). Resolution path: verified directly against `HEAD` before
   editing (quoted in Why above) and cited the corrected line numbers in
   this record; no code change needed, not a blocker.
   derived: `git show cdf80483a583faf29ee343db8ca17a112c61c158:gates/closure_sweep.py | nl -ba | sed -n '470,500p'`
2. The issue's quoted current on-disk file content
   (`{"shape1_sites": 365, "shape5_files": 0}`) does not exist verbatim
   anywhere reachable in this environment. The actual current unkeyed state
   files found on disk (at `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/accumulation_trend.json`
   and a sibling worktree's `runs/accumulation_trend.json`) both contain
   `{"shape1_sites": 365, "shape1_ok": true}` — the post-#2543 shape (which
   dropped `shape5_files` and added `shape1_ok`), still unkeyed by repo.
   Resolution path: this is still the exact migration case requirement 5
   describes (an unkeyed file with no repo identity); the fix's
   discard-and-first-run behavior applies identically regardless of which
   unkeyed shape is on disk, since detection is "not all top-level values
   are dicts" rather than a match on specific legacy keys — verified live
   in Verification (a) below using the real file copied from disk, not a
   hand-edited stand-in.
   derived: `find /home/jwjung/.tokenmaxxxer -maxdepth 6 -name accumulation_trend.json; find /home/jwjung/.claude -maxdepth 8 -name accumulation_trend.json`

## Next steps

None.

## Verification

a) Real existing unkeyed on-disk state file, read without raising:

The literal file quoted in the issue wasn't present anywhere reachable (see
Open findings #2); the actual current on-disk unkeyed shape
(`{"shape1_sites": 365, "shape1_ok": true}`, copied from
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/accumulation_trend.json`,
also present verbatim at the sibling worktree
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2543-implementation/runs/accumulation_trend.json`)
was placed at this worktree's `runs/accumulation_trend.json` (gitignored
path, not committed) and read via:

derived: `python3 -c "import sys; sys.path.insert(0,'gates'); import closure_sweep; from pathlib import Path; root=Path('.').resolve(); trend=closure_sweep.accumulation_trend(root); print(closure_sweep.format_accumulation_trend(trend)); print('RAISED: no')"`

output:
```
[on-the-record-issue-2546-implementation] accumulation-trend: no prior tick data (first run) — shape1_sites=365
RAISED: no
```
Exit code was 0 (no exception). The file was then rewritten in the new
keyed shape (`{"on-the-record-issue-2546-implementation": {"shape1_sites": 365, "shape1_ok": true}}`),
confirmed by `cat runs/accumulation_trend.json` afterward.

b) / c) Three-tick alternation across two real repos, state file reset first
(`rm -f runs/accumulation_trend.json`). Repo A = this checkout
(`on-the-record`, worktree root, resolves to repo key
`on-the-record-issue-2546-implementation`). Repo B = `$CLAUDE_PLUGIN_ROOT_CORE`
(`printenv CLAUDE_PLUGIN_ROOT_CORE` →
`/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core`,
confirmed a distinct git repo via `git -C "$CLAUDE_PLUGIN_ROOT_CORE" rev-parse --show-toplevel`
and `git -C "$CLAUDE_PLUGIN_ROOT_CORE" remote -v` → `origin  https://github.com/tokenmaxxxer/tokenmaxxxer-core.git`;
resolves to repo key `core`, the directory basename).

derived (tick 1, repo A):
`python3 -c "import sys; sys.path.insert(0,'gates'); import closure_sweep; from pathlib import Path; root=Path('.').resolve(); trend=closure_sweep.accumulation_trend(root); print(closure_sweep.format_accumulation_trend(trend))"`
```
[on-the-record-issue-2546-implementation] accumulation-trend: no prior tick data (first run) — shape1_sites=365
```

derived (tick 2, repo B):
`python3 -c "import sys, os; sys.path.insert(0,'gates'); import closure_sweep; from pathlib import Path; root=Path(os.environ['CLAUDE_PLUGIN_ROOT_CORE']).resolve(); trend=closure_sweep.accumulation_trend(root); print(closure_sweep.format_accumulation_trend(trend))"`
```
[core] accumulation-trend: no prior tick data (first run) — shape1_sites=6
```
(first-run line, not a delta against repo A's 365 — this is the check (c)
evidence: a never-seen-before repo key prints the first-run form.)

derived (tick 3, repo A again):
`python3 -c "import sys; sys.path.insert(0,'gates'); import closure_sweep; from pathlib import Path; root=Path('.').resolve(); trend=closure_sweep.accumulation_trend(root); print(closure_sweep.format_accumulation_trend(trend)); print('trend:', trend)"`
```
[on-the-record-issue-2546-implementation] accumulation-trend: shape1_sites=365 (+0)
trend: {'repo': 'on-the-record-issue-2546-implementation', 'current': {'shape1_sites': 365, 'shape1_ok': True}, 'has_prior': True, 'prior': {'shape1_sites': 365, 'shape1_ok': True}, 'delta': {'shape1_sites': 0}}
```
This is a delta against repo A's own tick-1 value (365 → 365, `+0`), not
against repo B's tick-2 value (6) — had the old cross-repo bug still been
present, this line would have read `(+359)` (365 - 6) instead of `(+0)`.
The `trend` dict's own `prior` field (`{'shape1_sites': 365, 'shape1_ok': True}`)
matches repo A's own tick-1 `current`, not repo B's `{'shape1_sites': 6, ...}`.
The real accumulation counts for repo A did not naturally differ between
tick 1 and tick 3 (no tracked-file changes to this checkout's `*.py` files
occurred between the two calls), so the delta is 0; per the verification
brief this is acceptable since the check is which prior the delta is
computed against, not whether the count itself moved.

State file after all three ticks:
```
{"on-the-record-issue-2546-implementation": {"shape1_sites": 365, "shape1_ok": true}, "core": {"shape1_sites": 6, "shape1_ok": true}}
```

acceptance: `python3 -m py_compile gates/closure_sweep.py` — result: exit 0, no syntax errors.

## Verification — post warrant-hunter fix (`_repo_identity`-based keying)

All three checks below were re-run against the corrected code
(`_accumulation_repo_key()` now `return spawn._repo_identity(root)`), fresh,
in this worktree, plus a fourth check demonstrating the collision case the
warrant-hunter probe found is actually fixed.

d) On-disk legacy unkeyed file, read without raising (fresh state root, not
this worktree's real `runs/` dir):

derived:
```
rm -rf /tmp/verify_state && mkdir -p /tmp/verify_state
printf '{"shape1_sites": 365, "shape5_files": 0}' > /tmp/verify_state/accumulation_trend.json
MUSTER_STATE_ROOT=/tmp/verify_state python3 -c "
import sys
sys.path.insert(0, 'gates'); sys.path.insert(0, '.')
import closure_sweep
from pathlib import Path
t = closure_sweep.accumulation_trend(Path('.'))
print('unkeyed-file tick:', closure_sweep.format_accumulation_trend(t))
"
cat /tmp/verify_state/accumulation_trend.json
```
output:
```
unkeyed-file tick: [on-the-record] accumulation-trend: no prior tick data (first run) — shape1_sites=365
{"on-the-record": {"shape1_sites": 365, "shape1_ok": true}}
```
No exception. Note the repo key is now `on-the-record` (parsed from this
checkout's real `origin` remote), not the directory basename
(`on-the-record-issue-2546-implementation`) — confirms the key now comes
from `_repo_identity`, not `root.resolve().name`.

e) Three-tick alternation, this checkout + `$CLAUDE_PLUGIN_ROOT_CORE`, fresh
state root:

derived:
```
rm -rf /tmp/verify_state2 && mkdir -p /tmp/verify_state2
MUSTER_STATE_ROOT=/tmp/verify_state2 python3 -c "
import sys
sys.path.insert(0, '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation/gates')
sys.path.insert(0, '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation')
import closure_sweep
from pathlib import Path
rootA = Path('/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation')
rootB = Path('\$CLAUDE_PLUGIN_ROOT_CORE')
t1 = closure_sweep.accumulation_trend(rootA)
print('tick1 (on-the-record):', closure_sweep.format_accumulation_trend(t1))
t2 = closure_sweep.accumulation_trend(rootB)
print('tick2 (core):', closure_sweep.format_accumulation_trend(t2))
t3 = closure_sweep.accumulation_trend(rootA)
print('tick3 (on-the-record again):', closure_sweep.format_accumulation_trend(t3))
"
cat /tmp/verify_state2/accumulation_trend.json
```
output:
```
tick1 (on-the-record): [on-the-record] accumulation-trend: no prior tick data (first run) — shape1_sites=365
tick2 (core): [tokenmaxxxer-core] accumulation-trend: no prior tick data (first run) — shape1_sites=6
tick3 (on-the-record again): [on-the-record] accumulation-trend: shape1_sites=365 (+0)
{"on-the-record": {"shape1_sites": 365, "shape1_ok": true}, "tokenmaxxxer-core": {"shape1_sites": 6, "shape1_ok": true}}
```
Repo B's key is now `tokenmaxxxer-core` (parsed from its real origin
`https://github.com/tokenmaxxxer/tokenmaxxxer-core.git`), not `core` (the
directory basename) as in the original (pre-fix) verification run above —
demonstrates the key source changed from basename to origin-derived
identity. Tick 3's delta against repo A's own tick-1 prior is still
correctly `(+0)`, not contaminated by repo B's `6`.

f) Collision repro: two real local git repos, distinct GitHub origins, same
checkout directory basename (`checkout`) — the exact case the
warrant-hunter probe constructed against the pre-fix code:

derived:
```
cd /tmp && rm -rf wrap1 wrap2 && mkdir -p wrap1/checkout wrap2/checkout
cd /tmp/wrap1/checkout && git init -q && git remote add origin https://github.com/orgA/repo-alpha.git \
  && printf 'import subprocess\nsubprocess.run(["echo","a"])\nsubprocess.run(["echo","b"])\n' > a.py \
  && git add a.py && git -c user.email=a@a -c user.name=a commit -q -m init
cd /tmp/wrap2/checkout && git init -q && git remote add origin https://github.com/orgB/repo-beta.git \
  && printf 'import subprocess\nsubprocess.run(["echo","c"])\n' > b.py \
  && git add b.py && git -c user.email=a@a -c user.name=a commit -q -m init

rm -rf /tmp/state_root && mkdir -p /tmp/state_root
MUSTER_STATE_ROOT=/tmp/state_root python3 -c "
import sys
sys.path.insert(0, '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation/gates')
sys.path.insert(0, '/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2546-implementation')
import closure_sweep
from pathlib import Path
rootA = Path('/tmp/wrap1/checkout')   # git origin orgA/repo-alpha
rootB = Path('/tmp/wrap2/checkout')   # git origin orgB/repo-beta -- a DIFFERENT repo, SAME dirname
t1 = closure_sweep.accumulation_trend(rootA)
print('tick1 (repo-alpha):', closure_sweep.format_accumulation_trend(t1))
t2 = closure_sweep.accumulation_trend(rootB)
print('tick2 (repo-beta):', closure_sweep.format_accumulation_trend(t2))
t3 = closure_sweep.accumulation_trend(rootA)
print('tick3 (repo-alpha again):', closure_sweep.format_accumulation_trend(t3))
"
cat /tmp/state_root/accumulation_trend.json
```
output:
```
tick1 (repo-alpha): [repo-alpha] accumulation-trend: no prior tick data (first run) — shape1_sites=2
tick2 (repo-beta): [repo-beta] accumulation-trend: no prior tick data (first run) — shape1_sites=1
tick3 (repo-alpha again): [repo-alpha] accumulation-trend: shape1_sites=2 (+0)
{"repo-alpha": {"shape1_sites": 2, "shape1_ok": true}, "repo-beta": {"shape1_sites": 1, "shape1_ok": true}}
```
Both roots have the identical directory basename `checkout`, yet the fixed
code assigns distinct keys `repo-alpha`/`repo-beta` (parsed from each repo's
own origin URL) and tracks independent deltas correctly: repo-beta's
first-ever tick correctly prints the first-run form (not a delta against
repo-alpha's `2`), and repo-alpha's own tick-3 delta against its own tick-1
prior is correctly `(+0)`.

Under the old (basename) keying this collides: `_accumulation_repo_key()`
would have returned `root.resolve().name == "checkout"` for both roots, so
`all_state.get(repo_key)` at tick 2 would look up repo-alpha's tick-1 entry
(`{"shape1_sites": 2, ...}`) as if it were repo-beta's own prior — this is
exactly what the warrant-hunter probe demonstrated against the unfixed code
(quoted verbatim in
`docs/issue-2546/reports/implementation/2026-08-26-hunt-accumulation-trend-repo-key.md`,
Observed section): `tick2 (repo-beta): [checkout] accumulation-trend:
shape1_sites=1 (-1)` — repo-beta's first-ever observation misreported as a
`-1` shrink against a repo it had never touched.

acceptance: `python3 -m py_compile gates/closure_sweep.py` — result: exit 0, no syntax errors (re-run against the corrected function body).
