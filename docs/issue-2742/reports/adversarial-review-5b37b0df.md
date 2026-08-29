---
issue: 2742
role: adversarial-review-5b37b0df
author: adversarial-review-5b37b0df
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent re-verification of PR #2794's own deliverable
loop_state: complete
upstream:
  - path: PR #2794 (branch issue-2742/adversarial-review+secure-coding-authorization-access-control-92b45f13), commits cf0e4bb7 + 88c4a858
    sha: 88c4a8589d090f5d0b27f311fb6ecc0678f56f8a
  - path: docs/issue-2742/reports/adversarial-review+secure-coding-authorization-access-control-9d4adb47.md (prior re-verification, no new findings)
    sha: same-commit
---

# issue-2742 — adversarial-review-5b37b0df record

## What was done

canonical: `gh pr view 2794 --repo tokenmaxxxer/on-the-record` (read this
session) — PR #2794 is a mid-clone/disarm-race fix to the issue #2742
bootstrap signal guard, `OPEN`, `Closes #2742`.

canonical: `docs/issue-2742/reports/adversarial-review+secure-coding-authorization-access-control-9d4adb47.md`
(read this session) — the prior independent re-verification pass re-ran the
delivered test suite and overhead numbers and found nothing new, but did
not itself construct adversarial inputs to `_workspace_target_is_fresh()`
or independently re-trace the ordering argument behind fix 2. This
session's task was to attack exactly that gap.

Note: this session's own checkout (branch `issue-2742/adversarial-review-5b37b0df`)
does not carry PR #2794's `spawn.py` changes or its new test file — all
`spawn.py`/test-file paths cited below (untracked on this branch, they
live only on PR #2794's branch) were read and executed against a separate
worktree, `/tmp/wt2794`, checked out at commit `88c4a8589d090f5d0b27f311fb6ecc0678f56f8a`
(`git worktree add /tmp/wt2794 pr2794`, `pr2794` = `origin/pull/2794/head`,
fetched this session).

**Attack on `_workspace_target_is_fresh(cwd, target_path, issue)`** — ran it
directly against seven synthetic target states.

acceptance: seven-case adversarial probe of `_workspace_target_is_fresh()`,
run this session in `/tmp/wt2794` (worktree of commit `88c4a858`, PR #2794's
branch, untracked on this session's own branch) — result:
```
A) empty dir, issue-scoped:                          True
B) missing-parent target, issue-scoped:               True
C) stray non-git non-empty dir, issue-scoped:         True
D) symlink->real dir (no .git in target), issue-scoped: True
E) same symlink, adhoc (issue=None):                  True
F) partial .git leftover (same-lease reuse), issue-scoped: False
G) same leftover, adhoc:                              True
```
Full command in "Verification" below.

canonical: `sed -n '2932,3018p' spawn.py` in `/tmp/wt2794` (commit
`88c4a858`, untracked on this session's own branch), read this session —
`issue_workspace()`'s own self-reuse branch (`src == work`), issue-scoped
reuse branch (`.git` exists → fetch, never re-clone), adhoc
unconditional-wipe branch (`issue is None and (work/".git").exists()` →
`shutil.rmtree` then fall through to fresh clone), and incomplete-clone
guard (`_workspace_clone_incomplete(work)` → `sys.exit`, no clone attempted)
match cases A, B, E, F, G above exactly — no finding on those five.

Cases C and D are real gaps in the fresh/not-fresh classification taken in
isolation, reported as findings below with reachability analysis, since
neither is reachable through this system's own code paths today.

**Finding 1 (PLAUSIBLE, low severity)**: `_workspace_target_is_fresh()`
classifies "fresh" solely by `.git` absence, not by "does real content
exist." Case C above shows a directory holding real non-git content at the
deterministic target path is classified fresh and thus eligible for
`shutil.rmtree()` on signal.

derived: `git show 88c4a858:test/test_bootstrap_signal_guard.py | grep -n
"_slow_run_net" -A5` run this session — the PR's own gap-1 fault injection
(`test_signal_during_clone_removes_partial_workspace`) produces this exact
shape (content, no `.git`) by mocking `_run_net`, and it is correctly wiped
there because it is this same attempt's own in-progress clone output, not
third-party content — that is the only writer of this deterministic path
in the real system, and real `git clone` creates `.git` as its first
filesystem operation, so a non-git non-empty directory at this exact path
does not arise from any live code path today. No blocking action; a
scoping note only.

**Finding 2 (not a live bug, verified safe)**: same "fresh" answer for a
symlink at the target path pointing to a real directory holding real
content (case D above).

acceptance: `shutil.rmtree(symlink_target, ignore_errors=True)` on a
symlink to a directory containing `precious.txt`, run this session — result:
```
before rmtree: real_dir exists: True / symlink exists: True / precious.txt exists: True
after rmtree(symlink, ignore_errors=True): real_dir exists: True / symlink exists (lexists): True / precious.txt exists: True
```
Full script in "Verification" below. `shutil.rmtree()` refuses to traverse
a symlink argument and raises `OSError: Cannot call rmtree on a symbolic
link`; `ignore_errors=True` swallows that, so both the linked-to content
and the symlink survive — the misclassification causes no data loss, only
a harmless leftover symlink artifact. No action needed.

**Attack on fix 2's ordering (session-log boundary)**:

acceptance: `grep -n '_record_spawn_outcome(attempt_id, "session-log"\|subprocess.Popen(\|_disarm_bootstrap_signal_guard(_bootstrap_signal_guard)' spawn.py`
run this session in `/tmp/wt2794` — result:
```
4168:            _record_spawn_outcome(attempt_id, "session-log", str(log_path))
4173:            _disarm_bootstrap_signal_guard(_bootstrap_signal_guard)
4244:                        wproc = subprocess.Popen(
4309:            proc = subprocess.Popen(
```
Both `_record_spawn_outcome(..., "session-log", ...)` (4168) and
`_disarm_bootstrap_signal_guard()` (4173) run strictly before either
`Popen()` call (4244, 4309) that launches the real session process —
derived: the grep output above, line order alone settles it, no ambiguity
to resolve via comments. There is no window where a real, running child
session exists while the guard is still capable of treating its workspace
as "no session ever started." The window that does exist — real bootstrap
work (branch setup, roster registration, directive writes) in the target
workspace before line 4168 — is correctly in-scope for full deletion on
signal by this fix's own design: no session has started yet, so that
content belongs to this same not-yet-committed attempt.

**Attack on the disarm-race defense without `try`/`finally`**: the crashed
session's own "Open findings" flagged that arm/disarm are not wrapped in
`try`/`finally`, so an exception between arm and the normal disarm call
sites leaves the handler installed.

derived: `sed -n '2675,2716p' spawn.py` in `/tmp/wt2794`, read this session
— result (excerpt):
```
    try:
        ...
        return _spawn_one(...)
    except (SystemExit, Exception) as e:
        ...
        if attempt_id is not None:
            reason = (e.code if isinstance(e, SystemExit) else
                      f"{type(e).__name__}: {e}")
            _record_spawn_outcome(attempt_id, "halted", reason)
        raise
```
Any exception out of `_spawn_one()` (including every `sys.exit()` in
`issue_workspace()`) is caught at this outer `try`, and
`_record_spawn_outcome(attempt_id, "halted", ...)` runs synchronously in
the same stack unwind, before this frame returns control to anything that
could receive an unrelated later signal — derived: the code excerpt above,
read this session, not re-quoted from either prior record. Because
`_arm_bootstrap_signal_guard()`'s handler checks `attempt_id in
_SPAWN_ATTEMPT_OUTCOME_WRITTEN` before doing anything (fix 2's own defense,
independent of whether disarm ran), a signal arriving after this `except`
block runs is a no-op for this attempt_id even with the handler still
technically installed. The missing `try`/`finally` is a real structural
gap in isolation, but fix 2's independent dedupe check already closes the
only door it could open — derived: the excerpt above, re-traced live this
session rather than accepted from the crashed session's prior verdict.

**Adhoc path**: attacked directly above (cases E, G).

acceptance: `python3 -m pytest -q` on the two adhoc-path tests from
`88c4a858:test/test_bootstrap_signal_guard.py` (untracked on this session's
own branch) — `BootstrapSignalGuardReviewGapsTest::test_signal_during_adhoc_clone_also_removes_partial_workspace`
and `BootstrapSignalGuardReviewGapsTest::test_adhoc_leftover_at_target_path_is_wiped_not_preserved`
— run this session in `/tmp/wt2794` — result: `2 passed`.

**`_workspace_target_path()` double-call structural note**:

acceptance: 200-iteration timing of `spawn._workspace_target_path()` plus a
call-site grep, run this session in `/tmp/wt2794` — result:
```
_workspace_target_path: 4.522ms/call over 200 calls
grep -n '_workspace_target_path(' spawn.py:
2957:    origin, work_str = _workspace_target_path(cwd, issue, skill)   # inside issue_workspace()
3111:        _, target_path = _workspace_target_path(cwd, issue, skill)  # inside _create_workspace_with_signal_guard()
```
derived: `4.522ms x 2 calls = ~9.04ms` per fresh-clone bootstrap — matches
the PR's own ~4.2ms-per-call figure, independently re-measured rather than
copied. Negligible against a multi-second network clone/fetch; out of
scope as a performance concern, not a correctness one.

## Why

Per the `adversarial-review` skill's premise — an artifact's own author, or
a reviewer who only re-runs the author's own tests, is not positioned to
find what those tests didn't think to check — this session's job was to
construct inputs the delivered test suite (`88c4a858:test/test_bootstrap_signal_guard.py`,
untracked on this session's own branch, re-read this session) does not
cover, and to independently re-trace the "why this is safe" arguments in
the PR body rather than accept them once tests pass. The prior verification
session (9d4adb47) had already re-derived the pytest/overhead numbers;
duplicating that would not surface anything new, so this session spent its
effort on the classification function and the two ordering/race arguments
instead.

skill-verdict: adversarial-review — applied: invoked; this session's entire
task was constructing adversarial inputs to `_workspace_target_is_fresh()`
(seven synthetic states) and independently re-tracing the ordering/race
arguments in `spawn.py` directly, rather than re-trusting either the PR's
own claims or the prior verification session's record — canonical: every
`derived:`/`acceptance:` line in this record cites a command this session
itself ran this turn.
skill-verdict: work-in-english — applied: invoked; this record, all
`derived:`/`acceptance:` transcripts, and the commit/PR text for this
delivery are written in English; the final summary to the user is in
Korean.

## Upstream basis

- PR #2794 (branch
  `issue-2742/adversarial-review+secure-coding-authorization-access-control-92b45f13`),
  commits `cf0e4bb75fc8ab0eefa147e25a1197a480021acc` (the fix) and
  `88c4a8589d090f5d0b27f311fb6ecc0678f56f8a` (deviation log) — the
  deliverable under review; not modified by this session — canonical: `gh
  pr view 2794` output, read this session.
- `docs/issue-2742/reports/adversarial-review+secure-coding-authorization-access-control-9d4adb47.md`
  — the prior independent re-verification pass, `loop_state: complete`, no
  new findings — canonical: file read in full this session, and `git show
  ddff9a44747f29474453e7c51d5e241a74da3c1f --stat` run this session.
- `spawn.py` at commit `88c4a858` (worktree `/tmp/wt2794`, untracked on
  this session's own branch), read directly this session:
  `_workspace_target_is_fresh()` (line 3065), `_create_workspace_with_signal_guard()`
  (line 3092), `issue_workspace()` (line 2932), and `_arm_bootstrap_signal_guard()`
  / `_disarm_bootstrap_signal_guard()` (lines 1110/1162) — canonical: `grep -n
  "_arm_bootstrap_signal_guard\|_disarm_bootstrap_signal_guard\b" spawn.py`
  run this session (see "Verification" below for the full output) and the
  `sed`/`grep` excerpts quoted throughout "What was done" above.

## Open findings

- Finding 1 (PLAUSIBLE, low severity, see "What was done"):
  `_workspace_target_is_fresh()` classifies fresh/not-fresh solely by
  `.git` presence. Not reachable through any live code path today —
  canonical: reachability analysis in "What was done" above, derived: the
  gap-1 fault-injection test excerpt cited there. Resolution path: a
  one-line comment on `_workspace_target_is_fresh()` noting the check is
  intentionally `.git`-only would be a nice-to-have; not worth blocking
  this PR over.
- Finding 2 (not a live bug, see "What was done"): the symlink
  misclassification causes no data loss — acceptance: the `rmtree`
  transcript quoted in "What was done" and repeated in "Verification"
  below. No action needed.
- The two structural notes from the crashed session's own record
  (`_workspace_target_path()` running twice per fresh-clone bootstrap; no
  `try`/`finally` around arm/disarm) were independently re-traced this
  session rather than re-quoted — acceptance: the timing/grep result and
  the `except (SystemExit, Exception)` excerpt, both in "What was done"
  above — and both are confirmed genuinely out of scope: the double call
  costs derived: `4.522ms x 2 = ~9.04ms` against a multi-second network
  clone, and the missing `try`/`finally` is closed in practice by fix 2's
  independent `_SPAWN_ATTEMPT_OUTCOME_WRITTEN` dedupe check plus the
  synchronous `_record_spawn_outcome()` call in `main()`'s exception
  handler (excerpt quoted above).
- Not re-executed this session: the three CLI-level live acceptance
  demonstrations (decline a real spawn and show the watchdog line; kill a
  real spawn mid-bootstrap and show its line; list
  `~/.tokenmaxxxer/work/` after a decline). These require driving the real
  `spawn.py` CLI through an actual GitHub-backed spawn attempt. The prior
  verification session (9d4adb47) also did not re-drive these at the CLI
  level, relying instead on the delivered test suite's real fork+signal
  fault injection (`88c4a858:test/test_bootstrap_signal_guard.py`,
  untracked on this session's own branch, re-run this session — see
  "Verification" below), which exercises the identical code paths without
  the network dependency. This session made the same choice for the same
  reason.

## Next steps

`loop_state: complete`.

acceptance: `git status --short` in this session's own checkout
(`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2742-adversarial-review-5b37b0df`)
run this session — result:
```
?? docs/issue-2742/reports/adversarial-review-5b37b0df.md
```
This PR's code (`spawn.py`, its test file) is unmodified by this session —
only this record is added. Nothing further is planned beyond opening this
record's PR.

## Verification

Every check below was run by this session this turn.

acceptance: `_workspace_target_is_fresh()` seven-case adversarial probe, run
in `/tmp/wt2794` — command:
```
python3 - <<'EOF'
import sys, os, shutil, tempfile
sys.path.insert(0, ".")
import spawn
with tempfile.TemporaryDirectory() as td:
    empty_target = os.path.join(td, "empty-target"); os.makedirs(empty_target)
    print("A)", spawn._workspace_target_is_fresh("/some/src", empty_target, 42))
    missing_parent_target = os.path.join(td, "no-such-parent", "nested-target")
    print("B)", spawn._workspace_target_is_fresh("/some/src", missing_parent_target, 42))
    stray = os.path.join(td, "stray-target"); os.makedirs(stray)
    open(os.path.join(stray, "important.txt"), "w").write("real content")
    print("C)", spawn._workspace_target_is_fresh("/some/src", stray, 42))
    real_dir = os.path.join(td, "real-important-dir"); os.makedirs(real_dir)
    open(os.path.join(real_dir, "precious.txt"), "w").write("do not delete me")
    symlink_target = os.path.join(td, "symlink-target"); os.symlink(real_dir, symlink_target)
    print("D)", spawn._workspace_target_is_fresh("/some/src", symlink_target, 42))
    print("E)", spawn._workspace_target_is_fresh("/some/src", symlink_target, None))
    partial = os.path.join(td, "partial-target"); os.makedirs(os.path.join(partial, ".git"))
    print("F)", spawn._workspace_target_is_fresh("/some/src", partial, 42))
    print("G)", spawn._workspace_target_is_fresh("/some/src", partial, None))
EOF
```
result: `A) True`, `B) True`, `C) True`, `D) True`, `E) True`, `F) False`,
`G) True`.

acceptance: symlink-rmtree safety probe, run this session — command:
```
python3 - <<'EOF'
import os, shutil, tempfile
with tempfile.TemporaryDirectory() as td:
    real_dir = os.path.join(td, "real-important-dir"); os.makedirs(real_dir)
    open(os.path.join(real_dir, "precious.txt"), "w").write("do not delete me")
    symlink_target = os.path.join(td, "symlink-target"); os.symlink(real_dir, symlink_target)
    print("before:", os.path.isdir(real_dir), os.path.lexists(symlink_target),
          os.path.exists(os.path.join(real_dir, "precious.txt")))
    shutil.rmtree(symlink_target, ignore_errors=True)
    print("after:", os.path.isdir(real_dir), os.path.lexists(symlink_target),
          os.path.exists(os.path.join(real_dir, "precious.txt")))
EOF
```
result: `before: True True True` / `after: True True True` — nothing
deleted.

acceptance: `python3 -m pytest -q` on `88c4a858:test/test_bootstrap_signal_guard.py`
(untracked on this session's own branch) run this session in `/tmp/wt2794`
— result:
```
...........                                                              [100%]
11 passed in 30.85s
```

acceptance: full-suite failing-test-name SET, `origin/main` (worktree
`/tmp/wt-main`) vs commit `88c4a858` (worktree `/tmp/wt2794`), run this
session — `python3 -m pytest -q` in both, `grep '^FAILED'` each into a
file, `diff`:
```
/tmp/wt-main:  16 failed, 557 passed, 3 xfailed
/tmp/wt2794:   16 failed, 564 passed, 3 xfailed
diff /tmp/main_failed.txt /tmp/pr_failed.txt  ->  no output (IDENTICAL SETS)
```
No new bug: the 16 failing names are set-identical on both sides (compared
as a set of names, not counts); the delta in passed count is exactly the 11
new signal-guard tests.

acceptance: `git diff origin/main -- roster.py | wc -l` run this session in
`/tmp/wt2794` — result: `0`. Watchdog reporting/sweep path untouched;
monitor/watch machinery not quieter — nothing in `roster.py` changed, and
the sweep-level test (exercising `roster.spawn_attempt_sweep()`
end-to-end) is part of the 11 passing tests above.

acceptance: `git diff origin/main -- spawn.py | grep -nE '^[+-].*\brole\b' |
wc -l` run this session in `/tmp/wt2794` — result: `0`. No retired role
axis reappears in any reshaped form.

acceptance: overhead, independent 20,000-iteration
`_arm_bootstrap_signal_guard`/`_disarm_bootstrap_signal_guard` loop, run
this session directly against `/tmp/wt2794`'s `spawn.py` module (fresh
script, not copied from either prior record) — result: `7.23us/cycle`.
Against PR #2782's `8.0us` baseline and the two prior sessions' `8.07us`
and `7.51us` measurements, all four are within measurement noise of each
other — no regression, independently re-confirmed.

acceptance: `_workspace_target_path()` per-call cost and double-call site
count — command and result already quoted in "What was done" above.

## What did not work

None.
