---
issue: 2834
role: adversarial-review-b63f1fd1
author: adversarial-review-b63f1fd1
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: watchdog.py:diagnose_health, watchdog.py:roster_watchdog, spawn.py:_build_expected, spawn.py:_build_observed
type: review-record
breaking: false
verdict: fix-confirmed-with-one-inaccurate-claim
loop_state: landed
upstream:
  - path: PR #2838 (issue #2834), diff against main
    sha: da731155c9e5d81cbdaf3b7f8c5c86d1cee9b64d
  - path: da731155c9e5d81cbdaf3b7f8c5c86d1cee9b64d:docs/issue-2834/reports/silent-failure-audit-f7c99b40.md
    sha: da731155c9e5d81cbdaf3b7f8c5c86d1cee9b64d
---

# issue-2834 — adversarial-review-b63f1fd1 record

## What was done

Independently re-derived PR #2838's fix (not restated from its record):
re-ran the sweep with my own search terms across both repos, wrote a fresh
repro/negative-control/overhead harness from scratch (not the delivery's
`/tmp/issue2834_repro.py`), read every one of the four call sites in their
surrounding caller context (not just the diff hunks), and benchmarked a
healthy tick before/after using two `git worktree` checkouts (`main` and
`pr-2838`).

canonical: `gh pr view 2838` — state OPEN, `additions: 433, deletions: 4`,
touches `spawn.py` and `watchdog.py` (remainder of the 433/4 total is the
delivery's own record file).

## Why

skill-verdict: adversarial-review — applied: invoked; I am the
structurally-independent evaluator session in this role's own two-party
contract (separate session from the PR's author, no shared context) —
re-executed the delivery's checks with my own fixtures/search terms
instead of re-running or trusting its scripts, per the skill's core
mechanism (self-review is architecturally biased; independent
re-derivation is not).
skill-verdict: work-in-english — applied: invoked; this record, all
intermediate commands, and code comments (none added) are in English.
other mounted/configured skills: verify-finding-record — not-applicable:
its target path is docs/issue-<n>/reports/defect-verification.md, not
this adversarial-review record path.

### 1. Sweep completeness — confirmed complete, no sixth site found

My own search terms (deliberately different from the delivery's
`Path(work)\.name|Path(cwd)\.name` grep): `.stem`, `.parts[-1]`,
`os.path.basename`, `os.path.split(`, and independently, every bare
`branch\s*=` assignment repo-wide (including tests, which the delivery
excluded).

derived: `grep -rnE "\.stem\b|\.parts\[-1\]|os\.path\.basename|os\.path\.split\(" --include=*.py .` (on-the-record repo) — result: hits in `deviation_log.py:73`, `lifecycle.py:762`, `events.py:132`, `board.py:802`, `gates/frozen_decisions.py:149`, `test/test_subject_deliverable_record_name_free.py:79`, `spawn.py:3988`, `scripts/measure_skill_invocation.py:12,77`, `scripts/skill_outcome_contrast.py:51` — every one derives a filename stem, hook name, or artifact basename, none feeds a branch/PR-lookup variable (checked each by reading its containing function).

derived: `grep -rnE "\bbranch\s*=" --include=*.py .` (on-the-record repo, tests included, run on the `main`-based working tree, i.e. pre-fix state) — result: exactly the four known-bad assignments appear as `Path(work).name` (two in `watchdog.py`, two in `spawn.py`). All other `branch =` assignments in the same grep (`lifecycle.py:147,287,1119`, `checkpoint.py:38`, `board.py:73`, `gates/*.py`, `harness/driver.py:223`, `spawn.py:801,806,873,906,914,3215,4601`, `test/test_approval_gate_carriers.py`) derive from `git rev-parse`/`git symbolic-ref`, a `gh pr list --json headRefName` field, a synthesized `issue-<n>/<skill>` string, or a test fixture parameter — none from a directory/workspace basename.

derived: `git show pr-2838:watchdog.py | grep -n "Path(work).name"` and `git show pr-2838:spawn.py | grep -n "Path(work).name"` — result: zero matches on `pr-2838` (both empty) — confirms all four sites the delivery names are actually gone in the PR's diff, not just claimed gone.

Second repo (`tokenmaxxxer-core`, confirmed via `git -C "$CLAUDE_PLUGIN_ROOT_CORE" remote -v` → `origin https://github.com/tokenmaxxxer/tokenmaxxxer-core.git`, distinct from this repo's `origin https://github.com/tokenmaxxxer/on-the-record.git`):

derived: `grep -rnE "\.stem\b|\.parts\[-1\]|os\.path\.basename|os\.path\.split\(" --include=*.py --include=*.sh "$CLAUDE_PLUGIN_ROOT_CORE"` — result: 2 hits, both in `hooks/tests/gate-prose-coverage-check.py` comparing `os.path.basename(dirpath)` to the literal `"hooks"` for test discovery — not a branch derivation.

derived: `grep -rnE "\bbranch\s*=" --include=*.py --include=*.sh "$CLAUDE_PLUGIN_ROOT_CORE"` — result: every `branch = ...` assignment in `approval-gate.sh`, `pretooluse_dispatcher.py`, `board-gate.sh` reads `git symbolic-ref --short HEAD` or `git rev-parse --abbrev-ref HEAD` via `subprocess.run(...).stdout`. Confirmed by reading each site directly:
```
$ sed -n '230,240p' "$CLAUDE_PLUGIN_ROOT_CORE/hooks/approval-gate.sh"
    out = subprocess.run(["git", "-C", root, "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True)
    branch = out.stdout.strip() if out.returncode == 0 else ""
$ sed -n '315,330p' "$CLAUDE_PLUGIN_ROOT_CORE/hooks/pretooluse_dispatcher.py"
    out = subprocess.run(["git", "-C", cpd, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, timeout=10)
    branch = out.stdout.strip()
$ sed -n '895,905p' "$CLAUDE_PLUGIN_ROOT_CORE/hooks/board-gate.sh"
    out = subprocess.run(["git", "-C", root, "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True)
    branch = out.stdout.strip() if out.returncode == 0 else ""
```
Real git calls, not path-derived strings. The rest of the `branch=` hits are shell-test fixture literals (`run-approval-gate-tests.sh`, `run-board-gate-tests.sh`).

**Result: no sixth site. My sweep, run with independent terms and including test files, agrees with the delivery's: four sites fixed in `on-the-record`, zero instances in `tokenmaxxxer-core`.**

I separately re-checked the delivery's one reviewed-and-left-alone
non-instance, `gates/flows.py:236` `_cwd_repo_name()`:
derived: `grep -n "_cwd_repo_name" -r . --include=*.py` — result: defined
at `gates/flows.py:236`, called once at `gates/flows.py:250`:
`entry.get("repo") or _cwd_repo_name(entry.get("cwd"))` — feeds a `repo`
attribution field, never a branch/PR-lookup variable. Agrees with the
delivery: not an instance of this bug class.

### 2. Negative control and healthy-output comparison — confirmed, not quieter

Wrote an independent fixture (`/tmp/adv2834_bench.py`, mode `repro`) —
different issue number (8123 vs. the delivery's 9999), different skill
name, and patches `spawn._pr_open_or_merged_for_branch` directly rather
than any board-index layer, keeping the real `diagnose_health()` and real
`_current_branch()` on the live code path. Ran it against two `git
worktree` checkouts, `/tmp/otr-main-bench` (main, pre-fix) and
`/tmp/otr-pr2838-bench` (pr-2838, post-fix).

acceptance: `python3 /tmp/adv2834_bench.py repro /tmp/otr-main-bench`
(pre-fix, fake PR registered under the real branch
`issue-8123/adv-fixture-check`) — result:
```
    [adv fake gh] queried branch='on-the-record-issue-8123-adv-fixture-check'
diagnose_health() -> {'state': 'DEAD-ERRORED', 'next_action': 'respawn', 'detail': "adv:8123:adv-fixture-check: pid 138707 부재, PR 없음, 커밋 없음, session_verdict='crashed'", ...}
```
Misdiagnosis reproduced live, independently, through the real pre-fix
`diagnose_health()` — the query used the dash-form dirname, never matched
the real branch, so a genuinely-open PR was invisible.

acceptance: `python3 /tmp/adv2834_bench.py repro /tmp/otr-pr2838-bench`
(post-fix, same fixture) — result:
```
    [adv fake gh] queried branch='issue-8123/adv-fixture-check'
diagnose_health() -> {'state': None, 'next_action': 'none', 'detail': 'completion, not a health diagnosis', ...}
negative-control diagnose_health() -> {'state': 'DEAD-ERRORED', 'next_action': 'respawn', 'detail': "adv:8123:adv-fixture-check: pid 138727 부재, PR 없음, 커밋 없음, session_verdict='crashed'", ...}
```
Fix confirmed (real branch now queried, completion correctly returned),
and — same post-fix binary, same fixture, PR registered under an
unrelated branch (`issue-9999/never-checked-out`) that this fixture never
checks out — the genuinely-dead, PR-less session still returns
`DEAD-ERRORED`. Not quieter.

**Full healthy-tick output, before vs. after**: ran `diagnose_health()`
directly on 5 genuinely-alive entries (`pid` = this process's own pid) in
real git workspaces, on both checkouts, and printed the exact
`[poll-report] {key}: {state} — {detail}` line `roster_watchdog()` prints
for each.

acceptance: `python3 /tmp/adv2834_bench.py healthtick-output /tmp/otr-main-bench` and the same against `/tmp/otr-pr2838-bench` — result: five lines each, **byte-identical** between the two runs:
```
[poll-report] adv:7100:adv-out: HEALTHY — adv:7100:adv-out: 최근 로그 성장, RUNNING
[poll-report] adv:7101:adv-out: HEALTHY — adv:7101:adv-out: 최근 로그 성장, RUNNING
[poll-report] adv:7102:adv-out: HEALTHY — adv:7102:adv-out: 최근 로그 성장, RUNNING
[poll-report] adv:7103:adv-out: HEALTHY — adv:7103:adv-out: 최근 로그 성장, RUNNING
[poll-report] adv:7104:adv-out: HEALTHY — adv:7104:adv-out: 최근 로그 성장, RUNNING
```
Nothing stopped being printed on the healthy path; nothing changed value.
This is expected once finding 3 below is understood: for a truly alive
entry, `diagnose_health()` still computes `branch` (now via a `git` call
instead of a string op) but never uses it, because the `if not alive:`
block that reads `branch` is skipped.

### 3. Overhead — the delivery's placement claim is wrong for 3 of 4 sites; the healthy tick does slow down, modestly

The record states: "confirmed by the diff itself... all four edits are
inside `if not alive:` / dead-entry branches" and "the living/HEALTHY
tick path... is untouched by this diff." I read each site in its
surrounding caller context (not just the diff hunks) and this claim does
not hold for three of the four:

canonical: `watchdog.py:263-268` (`diagnose_health()`, read directly on
the `pr-2838` checkout) —
```python
    now = time.time() if now is None else now
    pid = entry.get("pid", 0)
    work = entry.get("work")
    branch = _sp._current_branch(Path(work)) if work else None
```
This line is **above** `alive = _sp._alive(pid)` (`watchdog.py:274`),
inside `diagnose_health()`'s own top-level body — not inside its `if not
alive:` block. It runs on every call to `diagnose_health()`, alive or
dead.

canonical: `watchdog.py:1724-1727` (`roster_watchdog()`'s per-entry
loop, reached only when the entry passed the earlier `if not
_sp._alive(...): ... continue` at `watchdog.py:1617` / the `continue` at
`watchdog.py:1685` — i.e., only for genuinely-alive entries) —
```python
        health = _sp.diagnose_health(key, e, state=state, anomalies=anomalies, root=root)
        print(f"[poll-report] {key}: {health['state']} — {health['detail']}")
```
`diagnose_health()` is called here for **live** entries too. Combined
with the previous citation: every alive/healthy roster entry, every poll
tick, now runs one `git symbolic-ref` subprocess (`_current_branch()`,
`board.py:53-58`) that did not exist pre-fix — the result is computed and
then discarded, since the `if not alive:` block that would use `branch`
never executes for a live entry.

canonical: `watchdog.py:1604-1607` (`roster_watchdog()`'s per-entry loop,
**above** the `if not _sp._alive(...)` check at line 1617 — runs for
every entry unconditionally, alive or dead) —
```python
        divergences = _sp.reconcile(_sp._build_expected(e), _sp._build_observed(root, e),
                                 recovery_state_dir=root / ".on-the-record" / "recovery-state")
```
`_build_expected()` and `_build_observed()` (the two `spawn.py` sites)
are called here, unconditionally, before the alive/dead branch. Both now
call `_current_branch()` — two more `git` subprocesses per entry, per
tick, for every roster entry regardless of alive/dead status.

Only the fourth site — `watchdog.py`'s `roster_watchdog()` resume-for-
ready-PR check (`watchdog.py:1680`, inside `if dead_health["state"] is
None:` inside the dead-entry block) — is actually confined to the
dead-entry branch as claimed.

**Condition under which the call lands on the hot path**: any roster
entry that is alive (the normal, majority case on a healthy board) —
via `reconcile(_build_expected(e), _build_observed(root, e))` at
`watchdog.py:1606` (unconditional) and via `diagnose_health()`'s own
`branch` line at `watchdog.py:268` (called for alive entries too, from
`watchdog.py:1727`).

Measured the actual cost, not just the placement. Isolated one
`_current_branch()`-equivalent call:

derived: `python3 -c "import subprocess,time; t0=time.perf_counter()
[subprocess.run(['git','-C','.','symbolic-ref','--short','HEAD'], capture_output=True, text=True) for _ in range(20)]
print((time.perf_counter()-t0)/20*1000)"` — result: `1.63 ms per git symbolic-ref call` (this machine).

acceptance: `python3 /tmp/adv2834_bench.py healthtick /tmp/otr-main-bench` (main, pre-fix; N=20 real, genuinely-alive entries, own pid) — result:
```
reconcile(_build_expected,_build_observed) total: 1.1762s (58.81ms/entry)
diagnose_health() total: 0.3556s (17.78ms/entry)
```

acceptance: `python3 /tmp/adv2834_bench.py healthtick /tmp/otr-pr2838-bench` (pr-2838, post-fix; same fixture) — result:
```
reconcile(_build_expected,_build_observed) total: 1.3380s (66.90ms/entry)
diagnose_health() total: 0.4353s (21.77ms/entry)
```
Re-ran once for stability — result: `59.21ms → 66.61ms` and `18.58ms →
20.77ms`, consistent. Per-entry increase: ~+7-8ms (+12-13%) for the
reconcile/build_expected/build_observed path, ~+2-4ms (+13-22%) for
diagnose_health() — in the same ballpark as one-to-two extra isolated
`git symbolic-ref` calls (1.63ms each), plausible given process/OS
scheduling noise on top of the already-heavy pre-existing `git`/`gh`
calls in these functions (the pre-fix baseline already costs 58-59ms/entry
from `_git_head`, `_is_new_commit`, `checkpoint.checkpoint_health`, and
the `board()` read).

This is a measured overhead increase on the healthy/alive tick path,
contradicting "No overhead increase" and the hot-path-exclusion argument
as stated. It is not a correctness regression — the healthy tick's
printed output is unchanged (finding 2, byte-identical) — and at roughly
20-40 total added ms across a poll tick with 20 concurrent alive entries
against a 60-second poll interval (`POLL_INTERVAL_SEC`, referenced in a
comment at `watchdog.py:1699`), it is unlikely to be operationally
significant. The defect is in the delivery's argument, not in the fix's
behavior: the record's central premise for "no overhead" ("confirmed by
the diff itself... all four edits are inside if not alive / dead-entry
branches") is falsifiable by reading the twenty lines of surrounding
context the record did not quote, and is false for three of the four
sites.

### No fallback / fuzzy matching — confirmed

canonical: `board.py:53-58` (`_current_branch()`, unmodified by this PR,
read on the `pr-2838` checkout) —
```python
def _current_branch(root: Path) -> str:
    r = subprocess.run(["git", "-C", str(root), "symbolic-ref", "--short", "HEAD"],
                       capture_output=True, text=True)
    name = r.stdout.strip() if r.returncode == 0 else ""
    return name or "HEAD"
```
The only non-exact-match behavior is the literal string `"HEAD"` on
detached HEAD / git failure — not a fuzzy guess against existing
branches, never a partial/substring match.

derived: `git diff main -- watchdog.py spawn.py | grep -inE 'fuzzy|similar|difflib|startswith|endswith|\.replace\(|SequenceMatcher|closest'` (`pr-2838` checkout) — result: zero matches, exit code 1. No fallback/fuzzy matching was added anywhere in this diff.

## What did not work

None.

## Standing invariants

1. **No return of the retired role axis in any reshaped form.**
   derived: `git diff main -- watchdog.py spawn.py | grep -inE 'role_axis|judgment_ax|"role"|role-axis|\brole\b'` (run against `pr-2838` checkout) — result: zero matches, exit code 1.

2. **No new bug — failing-test set vs. `origin/main`, compared as SETS OF NAMES.**
   acceptance: `python3 -m pytest -q -m "not slow"` on `pr-2838` worktree — result: `16 failed, 570 passed, 3 xfailed in 32.83s`.
   acceptance: `python3 -m pytest -q -m "not slow"` on `main` worktree (sha `0b852068ed256abb704eaed1f1e6af005bab083b`) — result: `16 failed, 570 passed, 3 xfailed in 33.96s`.
   derived: `diff <(grep "^FAILED" before.txt | sort) <(grep "^FAILED" after.txt | sort)` — result: empty diff. Every one of the 16 `FAILED` lines in the `pr-2838` run appears verbatim in the `main` run and vice versa.

3. **No overhead increase.** See finding 3 above: not confirmed as
   stated — measured, via `python3 /tmp/adv2834_bench.py healthtick
   <checkout>` on both worktrees, a per-entry increase (~+7-8ms /
   +12-13% for the reconcile path, ~+2-4ms / +13-22% for
   `diagnose_health()`) on the healthy/alive tick path, contradicting the
   delivery's "no overhead increase, hot path untouched" framing, though
   not large enough in absolute terms (tens of ms per 60-second tick) to
   read as an operationally significant regression.

4. **Monitor and watch machinery unbroken, and NOT QUIETER.**
   acceptance: `python3 -m pytest -q test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py` (`pr-2838` checkout) — result: `10 passed`.
   Negative control (finding 2): genuinely-dead, PR-less session still reports `DEAD-ERRORED` post-fix. Healthy-tick output (finding 2): byte-identical `[poll-report]` lines before/after for 5 alive entries — nothing stopped being printed, nothing changed value.

## Upstream basis

PR #2838 (issue #2834), head commit `da731155c9e5d81cbdaf3b7f8c5c86d1cee9b64d`,
diff against `main` at `0b852068ed256abb704eaed1f1e6af005bab083b`
(`git diff main...pr-2838 -- spawn.py watchdog.py`).
Its own record at `da731155c9e5d81cbdaf3b7f8c5c86d1cee9b64d:docs/issue-2834/reports/silent-failure-audit-f7c99b40.md`
(read via `git show <that sha>:<that path>` for orientation only; it is
not present in this working tree, which is based on `main`, since
`pr-2838` is unmerged). Every claim from it that I use above was
independently re-derived with different fixtures/search terms, not
re-run from its scratch scripts, which no longer exist on disk.

## Open findings

- **Overhead-placement claim is inaccurate**: the delivery's "no overhead
  increase" argument rests on "all four edits are inside if not alive /
  dead-entry branches," which is false for `watchdog.py:268`
  (`diagnose_health()`'s own `branch` computation, called for alive
  entries too via `watchdog.py:1727`) and for both `spawn.py` sites
  (`_build_expected`/`_build_observed`, called unconditionally per entry
  at `watchdog.py:1606`, before the alive/dead branch). Measured impact
  is small (~single-digit ms per entry, see finding 3) and does not
  change any output — no code change is required on correctness grounds,
  but the record's overhead argument should not be relied on as written.
  Resolution path: none needed for this PR to land; a future
  overhead-sensitive change to the same functions should re-derive
  placement from caller context, not from the diff hunk alone.
- No other open findings — sweep, negative control, no-fallback
  confirmation, and the four standing invariants all independently
  reproduced the delivery's outcome.

## Next steps

None outstanding beyond the one open finding logged above (informational,
no code change required). `loop_state: landed` — every acceptance check
in this record (repro, negative control, sweep, both pytest runs, both
watchdog test files, both overhead benchmarks) was executed live in this
session, cited with its command and output above.
