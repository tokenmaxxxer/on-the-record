---
issue: 2834
role: silent-failure-audit-f7c99b40
author: silent-failure-audit-f7c99b40
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: watchdog.py:diagnose_health, watchdog.py:roster_watchdog, spawn.py:_build_expected, spawn.py:_build_observed
type: coding-record
breaking: false
verdict: fixed
loop_state: landed
upstream:
  - path: board.py:53-58 (`_current_branch()`)
    sha: 2c00749365fd1a967525127e1c847538f697e794
  - path: PR #2824 (issue-2795) commit that first reused `_current_branch()` at board.py's `_unrecovered_commit_count()` call sites
    sha: 31ceac1e8b3d7312204283aa4c422c3c13bebc99
---

# issue-2834 — silent-failure-audit-f7c99b40 record

## What was done

Fixed the `Path(work).name`-as-branch bug named in issue #2834, at its
named site and at three sibling sites the sweep found, by switching all
four to `_sp._current_branch(Path(work))` (or `_current_branch(Path(work))`
directly inside spawn.py, since spawn.py *is* the `_sp` module for its own
internal calls) — the same primitive PR #2824/issue #2795 already reused
for the same reason at board.py's two `_unrecovered_commit_count()` call
sites.

derived: `git diff -- watchdog.py spawn.py` (this commit's actual diff) — result: four hunks, one per site listed below, each replacing `branch = Path(work).name if work else None` with a `_current_branch(...)` call. Full hunks:
```diff
--- a/watchdog.py
+++ b/watchdog.py
@@ diagnose_health() @@
-    branch = Path(work).name if work else None
+    branch = _sp._current_branch(Path(work)) if work else None
@@ roster_watchdog() resume-for-ready-PR check @@
-                    branch = Path(work).name if work else None
+                    branch = _sp._current_branch(Path(work)) if work else None
--- a/spawn.py
+++ b/spawn.py
@@ _build_expected() @@
-    branch = Path(work).name if work else None
+    branch = _current_branch(Path(work)) if work else None
@@ _build_observed() @@
-    branch = Path(work).name if work else None
+    branch = _current_branch(Path(work)) if work else None
```

Root-cause chain, from the pre-fix code (canonical: `git show b5a0926bfc92b1806bb2c354f6073c725a18334a:watchdog.py | sed -n '265,269p'`, the parent commit before this fix):

```python
    now = time.time() if now is None else now
    pid = entry.get("pid", 0)
    work = entry.get("work")
    branch = Path(work).name if work else None
```

`work` is the workspace directory path, named `<repo>-issue-<n>-<skill>`
(dashes — filesystem-safe). `Path(work).name` returns that dash-form
basename. The real checked-out git branch is `issue-<n>/<skill>` (a
slash). Two lines later this wrong string becomes the lookup key
(canonical: same pre-fix `watchdog.py`, lines 295-303):

```python
        else:
            pr_number = _sp._pr_open_or_merged_for_branch(root, branch)
        if verdict == "normal" or pr_number is not None:
            return _diagnosis({"state": None, "next_action": "none",
                    "detail": "completion, not a health diagnosis"})
```

Since the dash-form string never equals any real branch, the lookup
always misses, `pr_number` is always `None` for this path, and a session
that actually finished and opened its PR falls through to
`DEAD-ERRORED` instead of the completion branch. Confirmed live in the
"Live reproduction" section below (real code path, not a synthetic
reimplementation).

Four sites fixed, all the same one-line substitution (see diff above):
- `watchdog.py:277` — `diagnose_health()`, the site named in the issue.
- `watchdog.py:1693` — `roster_watchdog()`'s `--resume`-for-ready-PR check.
- `spawn.py:933` — `_build_expected()` (feeds `reconcile()`'s
  expected-vs-observed comparison).
- `spawn.py:951` — `_build_observed()` (feeds the same `reconcile()`
  call's PR lookup).

derived: `grep -n "_current_branch(Path(work))\|def _current_branch" watchdog.py spawn.py board.py` — result:
```
board.py:53:def _current_branch(root: Path) -> str:
watchdog.py:277:    branch = _sp._current_branch(Path(work)) if work else None
watchdog.py:1693:                    branch = _sp._current_branch(Path(work)) if work else None
spawn.py:933:    branch = _current_branch(Path(work)) if work else None
spawn.py:951:    branch = _current_branch(Path(work)) if work else None
```

`_current_branch()` itself (board.py:53-58) was not modified — it already
existed with the right semantics (`git symbolic-ref --short HEAD`, falling
back to the literal string `"HEAD"` only for detached-HEAD, never a fuzzy
guess). It was not yet exported to spawn.py's `_sp` surface on this branch
(canonical: `python3 -c "import spawn; print(hasattr(spawn, '_current_branch'))"` printed `False`
before this change) — PR #2824, which is unmerged, is the only place that
export previously existed. Added
`_current_branch = _board_mod._current_branch` to spawn.py's re-export
block so watchdog.py can reach it via `_sp._current_branch()` per this
codebase's cross-module call convention (board.py's own module docstring,
lines 7-13, describing the `_sp` patching-compat mechanism).

## Why

skill-verdict: work-in-english — applied: invoked; all commit messages, PR title/body, code comments and this record are written in English per the skill
skill-verdict: silent-failure-audit — applied: invoked; traced the failure chain site→return-value→caller-behavior→downstream-consequence for the wrong branch-key lookup (watchdog.py:272-ish): wrong key → PR-completion lookup misses → absence is silently interpreted as "not complete" → DEAD-ERRORED, even though the session succeeded. Used this trace to justify the must-not-fallback requirement (a wrong key must fail loudly, not guess).
other mounted skills: not triggered — verify-finding-record targets docs/issue-<n>/reports/defect-verification.md, not this record path

derived: this trace is executed live in "Live reproduction" below — `python3 /tmp/issue2834_repro.py before` reproduces exactly this chain (wrong key queried, fake PR lookup misses, `DEAD-ERRORED` returned) through the real `diagnose_health()`.

Reusing `_current_branch()` rather than inventing a second derivation
keeps exactly one source of truth for "what branch is this workspace on"
in the codebase, and PR #2824 already established that exact primitive as
the fix for this exact class of bug (issue #2795) at two sibling call
sites in board.py (see Upstream basis). Diverging with a second helper
would have created two things a future reader has to keep in sync. No
fallback/fuzzy-matching was added at any of the four sites:
`_current_branch()` either resolves the real branch or (detached HEAD)
returns the honest literal `"HEAD"`; a `gh`/lookup failure downstream
still surfaces as "no PR found" (i.e. `DEAD-ERRORED`, per the negative
control below) rather than being silently guessed into a match.

## What did not work

None.

## Deviations

- **Overhead check**: the task asked to search `docs/specs` and
  `CLAUDE.md` for "overhead" to find a benchmark to run before/after.
  derived: `find . -iname CLAUDE.md` — result: no file found anywhere in
  this repo. derived: `grep -rn "overhead" docs/specs/*.md README.md bench/*.py scripts/*.py` —
  result: zero matches. No dedicated overhead-measurement artifact exists
  to run. Substituted a direct hot-path argument instead (see Invariants
  below) rather than skip the invariant silently.
- **`_cwd_repo_name` (defined in `gates/flows.py`)**: the sweep's grep
  turned this up (`Path(cwd).name` near a function used by ledger
  reporting). Reading it directly (canonical: `sed -n '225,247p' gates/flows.py`,
  reproduced below) showed it derives a **repo short name** for ledger
  attribution, not a git branch, and its return value is never used as a
  branch/PR-lookup key:
  ```python
  _CWD_REPO_RE = re.compile(r"^(.+)-issue-[0-9]+-[a-z0-9-]+$")


  def _cwd_repo_name(cwd: str | None) -> str | None:
      """`<repo>-issue-<n>-<role>` 작업 디렉터리 명명 관례(강제되지 않는
      호출자 쪽 관례, issue #216 survey)에서 레포 짧은 이름을 되짚는
      소급 폴백. 관례에 안 맞으면 basename 그대로 돌려준다."""
      if not cwd:
          return None
      name = Path(cwd).name
      m = _CWD_REPO_RE.match(name)
      return m.group(1) if m else name
  ```
  Out of scope for this issue: left unchanged, not counted as an instance
  of the branch-derivation bug.

## Upstream basis

`_current_branch(root: Path) -> str` (board.py:53-58) is the primitive PR
#2824 reused, per that PR's own commit.

canonical: `git show 31ceac1e8b3d7312204283aa4c422c3c13bebc99 -- spawn.py` output —
```diff
-_session_commit_count = _board_mod._session_commit_count
+_current_branch = _board_mod._current_branch
+_unrecovered_commit_count = _board_mod._unrecovered_commit_count
+UNPUSHED_STATUS_UNKNOWN = _board_mod.UNPUSHED_STATUS_UNKNOWN
```
and, at board.py's own call site added by that same commit:
```diff
-                commit_count = _sp._session_commit_count(
-                    work, e.get("before_head"), _sp._git_head(work))
+                commit_count = _sp._unrecovered_commit_count(
+                    work, e.get("before_head"), _sp._git_head(work),
+                    _sp._current_branch(Path(work)))
```

canonical: `gh pr view 2824 --json state,url` — result: `{"state":"OPEN","url":"https://github.com/tokenmaxxxer/on-the-record/pull/2824"}`.
PR #2824 is **not merged** as of this record — its own commit sha
(`31ceac1e8b3d7312204283aa4c422c3c13bebc99`) is cited above instead of a
merge-commit sha because no merge commit exists yet; this is a real
40-char hex identifying a real, distinct, already-existing commit, not a
placeholder. Only the single-line primitive (`_current_branch`, already
present in `board.py` before PR #2824 and unrelated to that PR's actual
`_unrecovered_commit_count()` payload) was reused here; PR #2824's own
remote-aware `DEAD-UNRECOVERED-COMMITS` rework is untouched by this
change and remains unmerged, out of this record's scope.

## Sweep

derived: `grep -rn "Path(work)\.name\|Path(cwd)\.name" --include=*.py .` (run from this repo's root) —
result: one hit outside the four fixed sites, `gates/flows.py:242: name = Path(cwd).name`,
reviewed above under Deviations and confirmed to be repo-name derivation,
not branch-derivation (not fixed, not an instance of this bug).

derived: `grep -rn "dirname\|basename\|\.name\b" --include=*.py --include=*.sh .` (this repo's product code) followed by
`grep -n "branch" <each matched file>` (production files only, tests excluded) —
result: hits only in `harness/driver.py:219` (`gh api repos/.../branches --jq .[].name`,
a GitHub API branch-listing call, not a directory-derived string) and the
four sites fixed in this change; all other `.name`/`dirname`/`basename`
occurrences (in `board.py`, `roster.py`, `lifecycle.py`, `skills.py`,
`plumbing.py`, `events.py`, `consult.py`, `pipeline.py`, `gates/*.py`) have
no `branch` co-occurrence at all — clean.

Second repo (`tokenmaxxxer-core`, mounted at `$CLAUDE_PLUGIN_ROOT_CORE`):

canonical: `printenv | grep -E "ON_THE_RECORD|CLAUDE_PLUGIN_ROOT_CORE|MUSTER_WORKSPACE_ROOT"` — result:
```
ON_THE_RECORD=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer
MUSTER_WORKSPACE_ROOT=/home/jwjung/.tokenmaxxxer/work
CLAUDE_PLUGIN_ROOT_CORE=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core
```
canonical: `git -C "$CLAUDE_PLUGIN_ROOT_CORE" remote -v` — result: `origin https://github.com/tokenmaxxxer/tokenmaxxxer-core.git` — confirming this is the sibling repo, distinct from this one (`origin https://github.com/tokenmaxxxer/on-the-record.git`).

derived: `grep -rnE "branch\s*=.*\.name\b|branch\s*=.*basename|branch\s*=.*dirname" --include=*.py --include=*.sh "$CLAUDE_PLUGIN_ROOT_CORE"` —
result: zero matches.
derived: `grep -rn "dirname\|basename\|\.name\b" --include=*.py --include=*.sh "$CLAUDE_PLUGIN_ROOT_CORE"` —
result: every hit is either a bash `$(dirname "${BASH_SOURCE[0]}")` self-locating
idiom used to source `gate-lib.sh`/find sibling hook files, or unrelated
path plumbing (`hooks/lib/gate-lib.sh`, `hooks/*.sh`,
`hooks/pretooluse_dispatcher.py`) — none derive or feed a git branch name.
tokenmaxxxer-core came back clean: no instance of this bug class found
there.

Fixed (this repo only, `tokenmaxxxer-core` had nothing to fix):
`watchdog.py:277` (`diagnose_health`, the issue's named site),
`watchdog.py:1693` (`roster_watchdog`'s resume-for-ready-PR branch),
`spawn.py:933` (`_build_expected`), `spawn.py:951` (`_build_observed`) —
all four via the same `_current_branch()` primitive, no new derivation
invented (see the diff under "What was done").
Left unfixed, with reason: `_cwd_repo_name` in `gates/flows.py` — not
an instance of this bug (repo name, not branch; never used as a
PR-lookup key), see Deviations.

## Invariants

**No role-axis reintroduction.** `grep -in "role axis" docs/specs/*.md`
located the retired-concept docs (`docs/specs/consult-guidance-source.md:16`,
`docs/specs/enforcement-boundary.md:168`, `docs/specs/generated-paths.md:65`,
`docs/specs/role-invariant-coverage.md:30`) — this issue's fix does not
touch any `roles/*.json`/`judgment_axes` machinery, so the applicable
check is a direct grep of the diff itself:
derived: `git diff -- watchdog.py spawn.py | grep -inE '"role"|role_axis|role-axis|judgment_axes|\brole\b'` —
result: zero matches, exit code 1 (no lines found).

**No new failing test.** Ran the full non-slow suite on this branch and on
an `origin/main` worktree, diffed the sorted `FAILED ...` name sets (not
counts).

acceptance: `python3 -m pytest -q -m "not slow"` (this branch, post-fix) — result:
```
16 failed, 570 passed, 3 xfailed in 33.47s
```

acceptance: `python3 -m pytest -q -m "not slow"` (in `git worktree add /tmp/otr-main-worktree origin/main`, sha `0b852068ed256abb704eaed1f1e6af005bab083b`) — result:
```
16 failed, 570 passed, 3 xfailed in 33.24s
```

derived: `diff <(grep "^FAILED" main-run.txt | sort) <(grep "^FAILED" after-run.txt | sort)` — result:
```
(empty diff)
```
The two 16-name sets are byte-identical; no new failure name appears on
this branch. All 16 are pre-existing network/fetch-dependent failures
(e.g. `pipeline.py`'s `bootstrap_fetch_and_record_sha` hitting
`"'origin' does not appear to be a git repository"` in a fixture with no
real remote) — unrelated to this change, present on `origin/main` too.

**No overhead increase.** No dedicated overhead-measurement script exists
in this repo — see Deviations for the grep proving this. Direct argument
instead: `_current_branch()` adds one `git symbolic-ref --short HEAD`
subprocess call per site, only inside the already-not-alive
(`if not alive:`) branch of `diagnose_health()` and `roster_watchdog()`'s
completion check — a branch that, immediately afterward on the very same
code path, already shells out to `session_end_verdict()` (reads an events
file) and `_sp._pr_open_or_merged_for_branch()` (a `gh pr list` call,
unless `pr_index`/`tick_index` is already warm) per dead entry. One more
cheap local `git` call added to an already `git`/`gh`-heavy, per-dead-entry
(not per-tick, not per-healthy-entry) path is not a hot-path change. The
living/HEALTHY tick path (the poll loop's steady-state cost) is untouched
by this diff — confirmed by the diff itself (see "What was done"): all
four edits are inside `if not alive:` / dead-entry branches.

**Monitor/watch machinery unbroken, not quieter.** Ran watchdog's own test
files directly.

acceptance: `python3 -m pytest -q test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py` — result:
```
10 passed
```

The negative control in "Live reproduction" below is the direct answer to
the "not quieter" requirement: a genuinely dead session with no PR
anywhere still reports `DEAD-ERRORED` after this fix — the change only
corrects a false `DEAD-ERRORED` on a session that in fact completed; it
introduces no new way to suppress or downgrade a real dead-session alarm.

## Live reproduction (before / after / negative control)

All three runs call the real `watchdog.diagnose_health()` through a real
temporary git workspace whose directory is named
`on-the-record-issue-9999-silent-failure-fixture` (dash form) while its
checked-out branch is `issue-9999/silent-failure-fixture` (slash form) —
the exact on-disk mismatch `issue_workspace()` produces for every real
spawn. Only `spawn._pr_open_or_merged_for_branch` (the `gh`-backed network
call) is stubbed, to stand in for "a PR is genuinely open under branch X";
branch derivation itself runs unmodified, real code
(`watchdog.diagnose_health` imported and called directly, not
reimplemented).

The fixture also writes a synthetic `session-start` event (pid = a
genuinely-dead pid obtained via `subprocess.Popen(["true"]).wait()`) with
no matching `session-end`, so that `session_end_verdict()` returns
`"crashed"` rather than its no-events-file default of `"normal"` — a
`"normal"` verdict alone short-circuits `diagnose_health()` to completion
regardless of the PR lookup (`if verdict == "normal" or pr_number is not
None`), which would have hidden the branch-key bug entirely.

**Before** (pre-fix code, obtained via `git stash push -- watchdog.py spawn.py`):

derived: `python3 /tmp/issue2834_repro.py before` — result:
```
    [fake gh pr lookup] queried branch='on-the-record-issue-9999-silent-failure-fixture'
[before] dirname='on-the-record-issue-9999-silent-failure-fixture' real_branch='issue-9999/silent-failure-fixture'
[before] diagnose_health() -> {'state': 'DEAD-ERRORED', 'next_action': 'respawn', 'detail': "issue-9999/silent-failure-fixture: pid 83044 부재, PR 없음, 커밋 없음, session_verdict='crashed'", 'dirty_files': 0, 'minutes_since_checkpoint': None}
REPRO CONFIRMED: misdiagnosed as DEAD-ERRORED despite open PR under real branch
```

The queried branch printed above (`on-the-record-issue-9999-silent-failure-fixture`)
is the dash-form directory basename, not the real branch
(`issue-9999/silent-failure-fixture`) — the lookup missed the fake PR
(registered only under the real, slash-form branch) and fell through to
`DEAD-ERRORED`, even though the fixture represents a session whose work is
done and whose PR is open. This is the bug, reproduced live against the
real pre-fix `diagnose_health()`.

**After** (`git stash pop`, post-fix code, same fixture, same fake PR
registered under the real branch):

derived: `python3 /tmp/issue2834_repro.py after` — result:
```
    [fake gh pr lookup] queried branch='issue-9999/silent-failure-fixture'
[after] dirname='on-the-record-issue-9999-silent-failure-fixture' real_branch='issue-9999/silent-failure-fixture'
[after] diagnose_health() -> {'state': None, 'next_action': 'none', 'detail': 'completion, not a health diagnosis', 'dirty_files': 0, 'minutes_since_checkpoint': None}
FIX CONFIRMED: correctly diagnosed as completion (not DEAD-ERRORED)
```

The queried branch printed above is now the real, slash-form branch — the
lookup matches the fake PR, and `diagnose_health()` returns the completion
shape (`state: None`) instead of `DEAD-ERRORED`.

**Negative control** (post-fix code, same fixture, but the fake PR lookup
is registered under a branch name that the fixture never checks out —
i.e. no PR exists anywhere for the real branch):

derived: `python3 /tmp/issue2834_repro.py negative` — result:
```
    [fake gh pr lookup] queried branch='issue-9999/silent-failure-fixture'
[negative] dirname='on-the-record-issue-9999-silent-failure-fixture' real_branch='issue-9999/silent-failure-fixture'
[negative] diagnose_health() -> {'state': 'DEAD-ERRORED', 'next_action': 'respawn', 'detail': "issue-9999/silent-failure-fixture: pid 83229 부재, PR 없음, 커밋 없음, session_verdict='crashed'", 'dirty_files': 0, 'minutes_since_checkpoint': None}
NEGATIVE CONTROL CONFIRMED: genuinely dead session still reports DEAD-ERRORED
```

A genuinely dead, PR-less session is still correctly diagnosed as
`DEAD-ERRORED` post-fix — the fix does not fold this case into
"completion" or otherwise quiet the diagnosis; it now looks up the
correct key and reports whatever that correct lookup honestly finds.

The repro script (`/tmp/issue2834_repro.py`, a scratch evidence harness
outside the committed tree — not a permanent test file) constructs the
workspace with real `git init`/`checkout -b`/`commit`, a real dead pid,
and calls `watchdog.diagnose_health()` directly.

## Open findings

None — the named site and every sweep-found sibling instance in both
repos were either fixed (four sites, this repo) or, for the one
non-instance found, confirmed out of scope.

canonical: `sed -n '225,247p' gates/flows.py` (reproduced in full under
Deviations above) — the `_cwd_repo_name` function derives a repo short
name, not a branch, and its return value is never passed to any
branch/PR-lookup call in that file — not an instance of this bug, left
unchanged.

## Next steps

None outstanding.

acceptance: `python3 -m pytest -q -m "not slow"` — result:
```
16 failed, 570 passed, 3 xfailed
```

`loop_state: landed` — fix committed, evidence captured live against the
real code path in this same record, PR opened referencing this record.
