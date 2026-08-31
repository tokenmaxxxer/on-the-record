---
issue: 2924
role: silent-failure-audit+refactoring-legacy-seam-selection-140f0858
author: silent-failure-audit+refactoring-legacy-seam-selection-140f0858
skills: silent-failure-audit (skill-repository(c05de12)), refactoring-legacy-seam-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: on-the-record/checks/macos_bash32_compat.py
    sha: same-commit
  - path: roster.py
    sha: same-commit
  - path: watchdog.py
    sha: same-commit
---

# issue-2924 — silent-failure-audit+refactoring-legacy-seam-selection-140f0858 record

## What was done

Build-now bypass (CORE_BUILD_NOW=1) — delivered directly, no phase-1 proposal round.

**Part 1 — the standing check** (`on-the-record/checks/macos_bash32_compat.py`,
`on-the-record/checks/test_macos_bash32_compat.py`): a dependency-free static
lint over the live population, run every `pytest` invocation. Two rule
families: (a) GNU-only shell constructs with no recognized portable
fallback — `flock` used anywhere without a `command -v flock` guard in the
same file, `stat -c` with no `stat -f` fallback on the same line, bare
`sed -i`/`date -d`/`readlink -f`/`grep -P`, and `"${arr[@]}"` expanded
under `set -u`/`-o nounset` without the `${arr[@]+"${arr[@]}"}`
bash-3.2-safe guard marker; (b) a `/proc/` reference in a live `.py` file
outside `KNOWN_PROC_SITES = {"roster.py", "watchdog.py"}` flags a *new*
`/proc` dependency until it is explicitly reviewed and added.

Population and enumeration bound:
```
derived: `python3 on-the-record/checks/macos_bash32_compat.py --verbose` -- result:
[macos-bash32-compat] population: 53 live .sh, 132 live .py (git ls-files '*.sh' '*.py' minus docs/ and test/tests paths)
[macos-bash32-compat] /proc dependency sites: 3 occurrence(s) in 2 file(s): roster.py, watchdog.py
[macos-bash32-compat] PASS
exit=0
```
Bound (`is_live()`, `on-the-record/checks/macos_bash32_compat.py`):
population is `git ls-files '*.sh' '*.py'`, excluding any path starting
`docs/` and any path matching `(^|/)(test|tests)/` or
`test_[^/]*\.py$`/`_test\.py$`. Excluded-as-test count, derived directly
(not via the check module, as an independent cross-check):
```
derived: `python3 -c "import sys; sys.path.insert(0,'on-the-record/checks');
import macos_bash32_compat as c, subprocess; out=subprocess.run(['git','ls-files','*.sh','*.py'],capture_output=True,text=True,check=True).stdout;
files=[p for p in out.splitlines() if p]; non_docs=[p for p in files if not p.startswith('docs/')];
print('non-docs:', len(non_docs)); print('live:', len([p for p in non_docs if c.is_live(p)]));
print('excluded-as-test:', len([p for p in non_docs if not c.is_live(p)]))"` -- result:
non-docs: 263
live: 185 (53 .sh + 132 .py)
excluded-as-test: 78
```
Excluded categories: `docs/` (139 `.sh`/`.py` paths — historical records
quoting old commands, never modified per this issue's must-not) and the
78 test files above.

GNU-only construct enumeration over the live `.sh` population, run
directly, independent of the check module's own logic:
```
derived: `LIVE_SH=$(git ls-files '*.sh' | grep -v '^docs/' | grep -Ev
'(^test/|^tests/|/test/|/tests/|test_.*\.py$|.*_test\.py$)'); for pat in
'stat -c' 'sed -i' 'date -d' 'readlink -f' 'grep -P' 'flock'; do echo
"$LIVE_SH" | xargs grep -ln -- "$pat"; done` -- result:
stat -c  -> on-the-record/hooks/decision-queue-stopgate.sh (only hit)
sed -i   -> (no hits)
date -d  -> (no hits)
readlink -f -> (no hits)
grep -P  -> (no hits)
flock    -> on-the-record/hooks/lint-test-on-edit.sh (comment only),
            on-the-record/monitors/poll-heartbeat.sh (real, #2919's file)
```
Empty state reported explicitly: `sed -i`, `date -d`, `readlink -f`,
`grep -P` — zero live sites. `lint-test-on-edit.sh`'s one match is a
comment (`# lock (flock) to serialize`), confirmed by grepping that file
alone for an actual invocation line and finding none:
```
derived: `grep -n 'flock' on-the-record/hooks/lint-test-on-edit.sh` -- result:
96:# lock (flock) to serialize the CPU-heavy test step across concurrent
```

`stat -c` finding: `on-the-record/hooks/decision-queue-stopgate.sh:73`
```
  mtime="$(stat -c %Y "$CACHE_FILE" 2>/dev/null || stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)"
```
already carries a `|| stat -f %m` BSD fallback on the same line.
```
canonical: `git log --format='%H %ad %s' --date=short -1 -S'stat -f %m' --
on-the-record/hooks/decision-queue-stopgate.sh` -- checked: ran directly -- result:
aa207739acf5998a4a024e03b5f83235665fa96c 2026-08-22 issue-2016 phase 2:
cut PreToolUse/Stop hook wall-clock via short-circuit + TTL cache (#2027)
```
This lands before this issue was filed, and `git show
aa207739acf5998a4a024e03b5f83235665fa96c:on-the-record/hooks/decision-queue-stopgate.sh`
carries the identical line — the fallback was never absent at any commit
this issue's population enumeration reaches. No code change made at this
site — GNU `stat -c %Y` and BSD/macOS `stat -f %m` both give epoch-seconds
mtime; this is the canonical portable idiom for the value, already
correct. `check_sh_file()` recognizes this line as safe (same-line
`stat -f` fallback), and
`test_decision_queue_stopgate_stat_c_fallback_is_recognized_safe`
(`on-the-record/checks/test_macos_bash32_compat.py`) pins it so a future
edit that drops the fallback trips the standing check.

Fail-then-pass proof against the pre-#2919 file
(`29d00cb553aec34cd7c87e950cd4b4153ead24de`, the parent of #2919's fix
commit `a826a010`) vs. current HEAD:
```
derived: `python3` one-liner calling `check_sh_file()` against `git show
29d00cb5...:on-the-record/monitors/poll-heartbeat.sh` and against the
current file -- result:
PRE-#2919 violations: 2
  on-the-record/monitors/poll-heartbeat.sh:163: `flock` used without a `command -v flock` guard anywhere in the file -- absent on macOS by default (issue #2919 shape)
  on-the-record/monitors/poll-heartbeat.sh:303: "${arr[@]}" expanded under set -u/-o nounset without the ${arr[@]+"${arr[@]}"} bash-3.2-safe guard -- an empty/unset array is unbound under bash 3.2 (issue #2919 shape)
HEAD violations: 0
```
This pair is now a standing regression test,
`test_would_have_caught_issue_2919_regressions`
(`on-the-record/checks/test_macos_bash32_compat.py`), run on every
`pytest` invocation:
```
canonical: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py -v -o addopts=""` -- checked: ran directly -- result:
test_current_head_is_clean PASSED
test_decision_queue_stopgate_stat_c_fallback_is_recognized_safe PASSED
test_new_proc_site_outside_reviewed_set_is_flagged PASSED
test_would_have_caught_issue_2919_regressions PASSED
4 passed in 0.08s
```

Independent confirmation under a real bash 3.2, not just static-lint
heuristics — a minimal snippet reproducing the pre-#2919 array pattern
and the bash-3.2-safe guard pattern, run via `docker run --rm bash:3.2`
(same image #2919's own session used):
```
derived: `docker run --rm bash:3.2 bash --version` -- result: GNU bash,
version 3.2.57(1)-release (x86_64-pc-linux-musl)
derived: `docker run --rm -v "$WD":/work bash:3.2 bash /work/pre_array.sh`
where pre_array.sh is `set -uo pipefail; IFS=' ' read -r -a ARR <<<"";
for x in "${ARR[@]}"; do echo "$x"; done; echo done` -- result:
/work/pre_array.sh: line 4: ARR[@]: unbound variable
exit=1
derived: `docker run --rm -v "$WD":/work bash:3.2 bash /work/head_array.sh`
where head_array.sh replaces the loop with the bash-3.2-safe
`${ARR[@]+"${ARR[@]}"}` guard -- result: done
exit=0
```
Caveat accounted for:
```
derived: `docker run --rm bash:3.2 sh -c 'command -v python3 || echo "NO
PYTHON3"; command -v git || echo "NO GIT"'` -- result: NO PYTHON3, NO GIT
```
Content was extracted with `git show` on the host; only the minimal
reproducing bash snippet (no python3/git dependency) was mounted into
the container. The same image also has a real `flock` binary
(`/usr/bin/flock`, confirmed via `docker run --rm bash:3.2 sh -c
'command -v flock'` -- result: `/usr/bin/flock`, musl-based util-linux),
so the flock-absence failure mode is not independently reproducible via
this image; that mode's necessity rests on #2919's own investigation
(macOS ships no `flock` by default) and on code inspection of the
`command -v flock` guard, not on this container.

**Part 2 — runtime-visible `/proc` degradation** (`roster.py`,
`watchdog.py`): `_watcher_looks_real()` (`/proc/<pid>/cmdline`) and
`_session_looks_real()` (`/proc/<pid>/cwd`, the #2749/PR #2823 pid-reuse
fix) in `roster.py` now call `_note_proc_identity_degraded(site)` — a
module-level, print-once-per-process helper — at the exact branch where
`/proc` absence (not merely this pid's `/proc` entry) makes the function
fall through to `_alive()`. `watchdog_lock_acquire()` in `watchdog.py`
(the #1456 single-instance lock, also reused by
`cross_workspace_board_sweep_lock_acquire()`) appends a `degraded_note`
to its returned refusal message when `other_start is None` — the exact
signature `/proc`-less `_proc_start_time()` always returns, which
otherwise makes `None == None` compare "identical" for any two distinct
processes and can wedge a new watchdog behind a reused-pid ghost forever
with no visible sign.

Only a message is added on the already-taken degrade branch; the
identity-check logic itself is untouched on Linux.
```
canonical: `git diff --cached -- roster.py watchdog.py` -- checked: ran
directly -- result: every changed hunk is either a new function
(`_note_proc_identity_degraded`), a new call to it inside an existing
`if not ...exists(): return True` branch, a new module-level constant
(`_PROC_AVAILABLE = os.path.isdir("/proc")`), or the `watchdog_lock_acquire`
ternary computing `degraded_note` -- no existing conditional, return
value, or comparison was changed.
```
Confirmed by running the existing test suite unchanged (no regressions)
plus new targeted tests (6 collected —
`derived: python3 -m pytest test/test_proc_identity_degradation_visibility.py
--collect-only -q -- result: 6 tests collected in 0.02s`):
```
canonical: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py
test/test_proc_identity_degradation_visibility.py test/test_self_update_pull_gate.py
-q -o addopts=""` -- checked: ran directly -- result: 15 passed in 0.97s
```

board.py's `/proc/<pid>` mention (`board.py:1277`, inside a docstring)
is prose about a mechanism that does not exist yet, not a live call,
and is deliberately excluded from `KNOWN_PROC_SITES`:
```
canonical: board.py:1270-1278 (git blame confirms this is prose, not code):
    알려진 한계(이슈 #2874 before-landing hunt): `alive_fn(wrapper_pid)` 는
    `os.kill(pid, 0)` 뿐이라 "그 pid 번호를 지금 누가 쥐고 있다"만 증명하지
    ...
    (신원 확인엔 `/proc/<pid>` 시작시각 비교 같은 새 메커니즘이
    필요하고, 그건 이 코드베이스 어디에도 아직 없다). PID 재사용 자체가
```
`check_py_file()`'s `_PROC_RE` only matches a `/proc/` immediately
inside a string-literal quote (`["']/proc/`); this backtick-quoted
Korean comment does not satisfy that pattern, and the narrowing was
verified necessary — an earlier substring-only `/proc/` regex false-
flagged this exact line before the narrowing:
```
derived: earlier draft of `on-the-record/checks/macos_bash32_compat.py`
using `_PROC_RE = re.compile(r"/proc/")` (no quote requirement), run via
`python3 on-the-record/checks/macos_bash32_compat.py --verbose` -- result:
[macos-bash32-compat] FAIL -- 1 violation(s):
  board.py: new /proc dependency outside the reviewed set ['roster.py', 'watchdog.py'] ...
```

**Part 3 — enumeration verification, no code change needed**: the
`stat -c` finding above is the population's only live GNU-only
construct, and it was already portable before this issue was filed — no
fix applied at that site.

## Why

The issue's core claim is that every existing check runs on Linux
bash 5.x with `/proc`, `flock`, and GNU `stat`/`sed`/`date`/`grep`
available, so a macOS-breaking change ships green. The response here is
not "audit once and patch what's broken today" (#2919 already did that
for poll-heartbeat.sh) but "add a check that would have caught #2919's
own two failures, prove it with a fail-then-pass pair against real
history, and wire it into something that actually runs" — per this
issue's acceptance criteria, a check with no demonstrated fail-then-pass
pair is unproven regardless of what else it does. That pair is
demonstrated above (Part 1).

The check is static and dependency-free (stdlib `re`/`subprocess`/
`pathlib` only) so it can run on every `pytest` invocation without
material wall-clock cost and stay quiet on a clean pass:
```
canonical: `python3 -m pytest on-the-record/checks/test_macos_bash32_compat.py -q -o addopts=""` -- checked: ran directly -- result: 4 passed in 0.08s
canonical: `python3 on-the-record/checks/macos_bash32_compat.py` (no --verbose flag, the standing-check invocation shape) -- checked: ran directly -- result: exit=0, zero stdout/stderr output (run() returns "" when ok and not verbose)
```
It does not itself require macOS or bash 3.2 to run (a dev-time/CI
check, not shipped code); the docker bash:3.2 run above is a one-time
independent corroboration that the static heuristic's classification
matches real bash-3.2 runtime behavior, not part of the standing check's
execution path.

`silent-failure-audit` classification
(`skill-verdict: silent-failure-audit — applied: invoked; this session's
own Skill tool call, guidance applied to the three already-identified
/proc sites`): all three were **Silently Absorbed** under the catalog's
"default-value substitution without recording that a fallback occurred"
pattern — `_alive()` is substituted for the identity check with nothing
recorded that this happened. Forward trace, each ending at "the program
continues as if the operation succeeded, with no indication that it
didn't" per the skill's Step 3 gate:
`_session_looks_real` degrades → `self_update_pull_cli()` sees a reused
pid as "session real" → refuses `git pull --ff-only` forever, no
self-healing (the #2749 hole, reopened on a `/proc`-less host).
`_watcher_looks_real` degrades → a crashed watcher with a reused pid
reads as alive → nothing prompts a respawn → silent watch coverage loss.
`watchdog_lock_acquire`'s `None == None` degrades → `_alive(other_pid)`
alone gates "already running" → a new watchdog instance can wedge behind
a dead process's reused pid, forever, with a message that read
identically to a genuine match (before this change). Remediation follows
the skill's Step 5 fix for this pattern: explicit visibility that a
fallback was used, not a behavior change — there is no substitute
identity mechanism on a `/proc`-less platform, and the issue's must-not
forbids weakening the Linux-side check to fake parity.

`refactoring-legacy-seam-selection` classification
(`skill-verdict: refactoring-legacy-seam-selection — applied: invoked;
this session's own Skill tool call, guidance applied to how the
roster.py/watchdog.py edits were shaped`): each site is a single,
clearly-localized point inside an otherwise-untouched legacy function —
rule 1 (Sprout Method) for `roster.py`'s
`_note_proc_identity_degraded()`, called from the exact branch closest
to the behavioral difference (rule 5), narrowed to that one branch
rather than restructuring `_watcher_looks_real()`/`_session_looks_real()`
(rule 6). `watchdog.py`'s fix is a single-line ternary inline rather than
a sprouted helper — rule 4 (confidence/budget over aesthetics): the
change is one conditional string: sprouting a one-line helper would be
aesthetic-only overhead the inline ternary doesn't lack in testability
(both branches are exercised directly by the two new
`WatchdogLockDegradedNoteTest` cases,
`derived: python3 -m pytest test/test_proc_identity_degradation_visibility.py::WatchdogLockDegradedNoteTest
-v -o addopts="" -- result: 2 passed`).

The 17 pre-existing test failures on the full suite are unrelated to
this change:
```
canonical: `git stash --include-untracked && python3 -m pytest -q
test/test_convention_equivalence.py harness/fixture-operator-experience/test_flow.py
test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py
tests/test_spawn_gate_wiring.py test/test_bootstrap_signal_guard.py -o addopts="";
git stash pop` -- checked: ran directly -- result: identical 17 test IDs
fail (network/git-remote/fixture-environment failures, none touching
roster.py/watchdog.py/spawn.py's identity-check code) with this issue's
changes fully reverted -- confirms pre-existing/environmental, not
introduced by this work
```

## What did not work

None.

## Upstream basis

- `on-the-record/checks/macos_bash32_compat.py` — the standing check
  (same-commit).
- `on-the-record/checks/test_macos_bash32_compat.py` — the fail-then-pass
  proof as a standing regression test, against
  `29d00cb553aec34cd7c87e950cd4b4153ead24de` (same-commit).
- `roster.py` — `_watcher_looks_real()`/`_session_looks_real()` runtime
  visibility (same-commit).
- `watchdog.py` — `watchdog_lock_acquire()` runtime visibility
  (same-commit).
- `test/test_proc_identity_degradation_visibility.py` — targeted tests
  for the Part 2 change (same-commit).
- `#2919` (`a826a0108515cc8198788f9b8d048e6fe4db058c`, parent
  `29d00cb553aec34cd7c87e950cd4b4153ead24de`) — the exact flock-guard and
  bash-3.2-safe-array-expansion patterns Part 1's check rules are built
  from.
- `#2749`/PR #2823 — the pid-reuse identity fix whose Linux-only
  effectiveness Part 2 makes visible.
- issue-2016 commit `aa207739acf5998a4a024e03b5f83235665fa96c` —
  predates this issue, already portable `stat -c`/`stat -f` site (Part 3
  finding).

## Open findings

None. Must-nots checked directly:
```
canonical: `git status --short docs/` -- checked: ran directly -- result:
?? docs/issue-2924/
(only this record's own untracked report directory -- no docs/ path
modified by this session's staged changes)
canonical: `git diff --cached --stat` -- checked: ran directly -- result:
 on-the-record/checks/macos_bash32_compat.py       | 212 ++
 on-the-record/checks/test_macos_bash32_compat.py  |  77 ++
 roster.py                                         |  33 ++
 test/test_proc_identity_degradation_visibility.py | 115 ++
 watchdog.py                                        |  19 +-
(no on-the-record/monitors/poll-heartbeat.sh hunk -- #2919's file untouched)
```
Linux `/proc` identity-check logic unchanged (see the `git diff --cached`
citation in "What was done" Part 2); no per-tick/per-spawn overhead added
(`_PROC_AVAILABLE` is a module-level constant computed once at import,
`_proc_identity_degradation_noted` is a single bool check per call, both
dwarfed by the `Path(...).exists()` stat every caller already performs
per call regardless of this change).

## Next steps

None — landed. A future `/proc` dependency outside `roster.py`/
`watchdog.py` will fail `macos_bash32_compat.py` until reviewed and
either made portable or given the same runtime-visible degradation
notice, then added to `KNOWN_PROC_SITES`.

other mounted skills: not triggered (work-in-english's language-policy
guidance was followed without a separate Skill-tool call; adversarial-
review, test-depth-audit, implementation-audit, and
technical-feasibility-reversibility-tag do not match this delivery
session's shape — no independent evaluator handoff, no test suite under
audit for depth classification, no spec-vs-implementation two-session
protocol, and no probe-resolution field being written).
