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

- Added `_accumulation_repo_key(root)` — returns `root.resolve().name` (the
  checkout directory basename) as the stable, human-readable repo identifier.
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
issue's own suggested option and needs no network call.

derived: `grep -n "repo_name\|repo_root\|REPO_NAME\|_repo_slug\|repo_slug" gates/*.py` —
result: found `spawn._repo_slug` (defined via `plumbing._repo_slug` in
`plumbing.py`, gh-API-backed) and `flows._cwd_repo_name` (a
workspace-dir-naming-convention parser not applicable to a plain checkout
root); neither was reused as-is, see Open findings.

## What did not work

N/A.

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
