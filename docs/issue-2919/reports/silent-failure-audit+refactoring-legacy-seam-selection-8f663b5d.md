---
issue: 2919
role: silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d
author: silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d
skills: silent-failure-audit (skill-repository(c05de12)), refactoring-legacy-seam-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2919/reports/adversarial-review-95d4569a.md (the review that found this defect)
    sha: 2a1d4dd39c30073b9d5f6e2a1e6f5b6f2d5b6f2d  # same-commit not applicable -- read verbatim from the working tree, this session
  - path: PR #2935 (github.com/tokenmaxxxer/on-the-record/pull/2935), commits e2441a9b (fix) + 2585022d (deviation-log + product-priorities capture)
    sha: 2585022dc07e810730dcdaa8eeeaba3017c17950
---

# issue-2919 — silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d record

skill-verdict: silent-failure-audit — applied: invoked; loaded via Skill tool before implementing. canonical: this session's own tool-call transcript (Skill invocation of `silent-failure-audit`, this session). Used to require that every reclaim path — the existing `dead`/`forming` branches and the new max-age safety-valve branch — logs a distinct, non-collapsible message via `_poll_watchdog_log_append`, so a forced reclaim never reads identically to "no contention happened" or to a normal `dead`-owner reclaim (see the `_alive_stamp_write` diff below).
skill-verdict: refactoring-legacy-seam-selection — applied: invoked; loaded via Skill tool before choosing the fix's shape. canonical: this session's own tool-call transcript (Skill invocation, this session). Used per rule 6 (narrow the seam to the smallest enclosing scope): the fix is confined to the no-flock branch's acquire sequence inside `_alive_stamp_write` and the sibling `_alive_stamp_lock_owner_status` (already its own sprouted function from PR #2935) — the flock-present branch, the array-expansion code, and all patrol code are untouched, verified below.
skill-verdict: work-in-english — applied: invoked; loaded via Skill tool at session start. canonical: this session's own tool-call transcript (Skill invocation, this session). All code, comments, commit messages and this record are in English; this final paragraph is the only Korean-facing surface, per the skill's routing rule.
other mounted skills: not triggered (verify-finding-record and conformance-review-finding-record don't fit — this record is original fix work with its own live-reproduced verification, not a defect-verification or conformance-review record against someone else's deliverable).

## What was done

canonical: `git diff a40a6452 HEAD -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py`, this session (a40a6452 is PR #2935's fix commit, cherry-picked onto this branch as the starting point, per the spawning task's instruction to base on PR #2935's branch content). Closed the remaining forming-window race in `poll-heartbeat.sh`'s no-`flock` mkdir-based mutex, and added a second, pid-liveness-independent recovery path for the zombie/reap-uncertainty gap. Both defects were identified in `docs/issue-2919/reports/adversarial-review-95d4569a.md` (PR #2935's own adversarial review, merged as PR #2944), read in full this session before any code change.

**1. The forming-window race (adversarial-review-95d4569a point 1).** PR #2935's design split lock acquisition into two separate top-level bash commands: `mkdir "${_lockdir}"` to claim the lock, then a later `printf '%s' "$$" >"${_owner_pid_file}"` to publish the owner pid. The reviewer live-reproduced a holder whose shell was paused (`sleep 5`) between those two commands getting evicted by a waiter at the 3-second forming-grace mark, after which the holder's own orphaned pid write failed silently and it fell through into the shared stamp write with no lock held — reproducing the exact unprotected-concurrent-write shape PR #2923 was meant to close. canonical: `docs/issue-2919/reports/adversarial-review-95d4569a.md` lines 30, 75 (read this session).

Fix: collapsed lock-claim and identity-publication into one shell command. `_alive_stamp_write`'s no-`flock` branch now acquires via:
```bash
while ! ( set -o noclobber; printf '%s' "$$" >"${_lockfile}" ) 2>/dev/null; do
```
`set -o noclobber` makes the redirection open the file with `O_EXCL` — atomic exclusive-create at the kernel level, the same guarantee `mkdir` gave for a directory — and the same command's own `printf` writes the pid through the already-open file descriptor before control returns to the loop. There is no longer a bash-level command boundary between "the lockfile exists" and "the lockfile names its owner" for a scheduler pause to land in, because acquisition is one command instead of two. `_alive_stamp_lock_owner_status` was correspondingly changed to read a plain lockfile (`cat "${_lockfile}"`) instead of `${_lockdir}/owner.pid`, and release changed from `rm -f owner.pid; rmdir lockdir` to a single `rm -f "${_lockfile}"`.

Residual, stated precisely rather than claimed away: the `open()` and the `write()` that follows it inside that one command are still two separate kernel calls, so a reader could in principle observe the file between them (an empty lockfile, which `_alive_stamp_lock_owner_status` reports as `forming`, same as before). This residual cannot be widened by host load or OS scheduling the way the prior two-command gap could, because no other command from this script runs in between to be delayed — it is bounded by the CPU-instruction distance between two adjacent syscalls in the same process, not by a scheduler quantum. The `forming`-grace fallback (3 tries) stays in the code as a defensive backstop for this residual (and for a write killed mid-syscall), not as the primary acquisition mechanism it was before.

**2. The zombie/reap-uncertainty gap (adversarial-review-95d4569a point 2).** The reviewer established that `kill -0` cannot distinguish a genuinely live holder from an unreaped zombie, and that who reaps a crashed `poll-heartbeat.sh` in production — a Claude Code plugin Monitor, session-bound, with no repo-visible spawn/reap code — is not establishable from this repository:
```
docs/specs/platform-capabilities.md lines 26-53 and docs/handbooks/monitor-liveness.md,
read via Read/Bash tools this session -- poll-heartbeat.sh runs as a Claude Code plugin
Monitor, documented as "session-bound," auto-started, with "no plugin API for OS-level
scheduling" ... Who reaps a crashed poll-heartbeat.sh instance, and how quickly, is not
established anywhere in this repo
```
(quoted from `docs/issue-2919/reports/adversarial-review-95d4569a.md` line 36, itself citing those two files). The PR #2935 record's "a genuinely crashed holder's lock still recovers without deadlocking the tick" claim was therefore unverified for actual deployment: if a real zombie is never reaped, `kill -0` reports it alive forever and a waiter blocks forever.

Fix: added a second recovery path, independent of pid liveness entirely. Each waiter tracks its own wait-start time (`_wait_started="$(date +%s)"`); once its total wait exceeds `POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE` (default 60s, overridable for tests), it force-reclaims the lockfile regardless of what `_alive_stamp_lock_owner_status` reports, and logs the reclaim with a distinct message (`... force-reclaimed independent of liveness check ... not a normal stale-lock reclaim`) so it is never mistaken for an ordinary `dead`-owner reclaim in the watchdog log — silent-failure-audit's requirement that a fallback never reads identically to success or to a different, already-understood failure mode. The 60s default sits with deliberate margin above the longest legitimate hold this fix's own verification demonstrated (the review's 25s slow-but-alive holder) and well inside the 120s tick cadence, so a zombie-shadowed lock costs roughly one tick's delay rather than an unbounded wait.

acceptance: find a recovery path independent of pid liveness, or state the assumption plainly — result: both. code_ref: `on-the-record/monitors/poll-heartbeat.sh` lines 276-309 (this session's Read tool, the `_alive_stamp_lock_max_age` block quoted immediately above) implements the non-pid-liveness path AND states its own trade-off inline, verbatim, in the code comment. The trade-off, stated precisely and not claimed as an unqualified guarantee: if a holder is still genuinely alive and legitimately working past 60s — not demonstrated as realistic for a write this small (a JSON `printf` + `mv`), but not provable impossible from this repo either — the valve force-reclaims it anyway and a second writer proceeds concurrently: the same unprotected-write failure shape this issue exists to close, deliberately reintroduced for holds beyond 60s in exchange for guaranteeing forward progress against a hold that never legitimately ends. No mechanism available to this repository can distinguish "genuinely still working" from "zombie that will never be reaped" from the outside.

**3. Tests.** Updated the three existing mutex regression tests (owner-status unit test, slow-live-holder eviction-avoidance test, crash-recovery test) for the lockdir→lockfile rename and the new splice anchor (the acquire loop's closing `done`, since there is no longer a separate pid-write line to anchor on). Added `t_alive_stamp_mutex_max_age_recovers_unreaped_holder_issue_2919`, which deliberately never reaps its self-killed worker A (unlike the sibling crash-recovery test, which reaps A promptly by design) so `kill -0` on A's pid keeps succeeding like a real zombie would, and asserts worker B still recovers via the max-age valve within a bounded time, with the distinct log line present. Also updated the crash-recovery test's docstring to name this gap explicitly and point at the new test, rather than let the reviewer's disclosure go unaddressed in the code the reviewer attacked.

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py`, this session:
```
ok  t_alive_stamp_lock_owner_status_establishes_liveness_issue_2919
ok  t_alive_stamp_mutex_max_age_recovers_unreaped_holder_issue_2919
ok  t_alive_stamp_mutex_never_evicts_slow_live_holder_issue_2919
ok  t_alive_stamp_mutex_recovers_crashed_holder_issue_2919
ok  t_alive_stamp_write_survives_missing_flock_issue_2919
...(37 further pre-existing tests, all ok)...
42/42 passed
```
4 mutex tests (3 updated + 1 new, derived: `git diff a40a6452 HEAD -- on-the-record/monitors/test_poll_heartbeat.py | grep -c '^+def t_'` → 1 new `def t_` line, plus the 3 existing mutex `def t_` lines already present pre-fix) and 38 pre-existing unrelated tests (derived: 42 total − 4 mutex = 38, arithmetic on the `42/42 passed` figure above) all pass, showing no regression to patrol, board-sweep, array-guard, or returned-PR-marker behavior.

**4. Live proof under real bash 3.2 with `flock` removed from PATH**, per the task's explicit ask to prove the result the way the reviewer attacked it. `docker pull bash:3.2` (official image, confirmed present this session), then:

- flock absence confirmed under the restricted PATH used for every run below: derived: `docker run --rm bash:3.2 bash -c 'PATH=/usr/local/bin:/bin command -v flock; echo rc=$?'` → `rc=1` (all needed binaries — `bash`, `mv`, `cat`, `rm`, `sleep`, `date` — resolve under that same restricted PATH; only `flock`, at `/usr/bin/flock` in this image, is excluded).
- **Mutual exclusion under real contention.** The real `_alive_stamp_lock_owner_status` and fixed `_alive_stamp_write` were extracted verbatim from the working tree via the test suite's own `_write_mutex_harness` helper (not a hand-copy), spliced with ENTER/EXIT instrumentation, and run as 8 concurrent sibling bash processes (one holding 1.5s, seven holding 0.3s, staggered 0.05s apart) inside a single `docker run --init` container so `kill -0` between siblings observes real shared-PID-namespace process state (an earlier attempt using one `docker run` per worker was discarded — see "What did not work"). derived: `python3 /tmp/otr-2919-verify/run_stress2.py 6 8`, this session:
```
run 0: rc=0 workers_logged=8/8 overlaps=[] ok=True
run 1: rc=0 workers_logged=8/8 overlaps=[] ok=True
run 2: rc=0 workers_logged=8/8 overlaps=[] ok=True
run 3: rc=0 workers_logged=8/8 overlaps=[] ok=True
run 4: rc=0 workers_logged=8/8 overlaps=[] ok=True
run 5: rc=0 workers_logged=8/8 overlaps=[] ok=True

6/6 runs clean
```
Zero ENTER/EXIT interval overlaps across all 6 runs × 8 workers = 48 worker executions (derived: 6×8=48, arithmetic on the run count and worker count both shown above) and zero worker exit-code failures. This directly answers the reviewer's own regression shape (their unmodified 8-writer run hit the false-positive reclaim mechanism in 5 of 6 runs under the pre-this-fix code, per `docs/issue-2919/reports/adversarial-review-95d4569a.md` point 1) with the fixed code under the same real-bash-3.2/no-flock conditions.
- **Crash recovery.** Worker A entered, held 1s, then `kill -9 $$`'d itself (confirmed via the container's own `Killed` message); worker B, contending 0.3s after A started, recovered and completed. derived: `docker run --rm --init --network none -v /tmp/otr-2919-verify/crash2:/work bash:3.2 bash /work/inner_crash.sh`, this session:
```
1788157147. ENTER A pid=8
1788157148. SELFKILL A pid=8
1788157149. [log:B] [alive-stamp-lock] stale lockfile /work/stamp.lockfile (owner pid 8 confirmed dead) reclaimed after 2s wait
1788157150. ENTER B pid=17
1788157150. EXIT B pid=17
```
B's own exit code was 0 (derived: same command's process return code, this session); total recovery (A's SIGKILL to B's ENTER) was ≈2s per the timestamps above. Timestamp precision in this container is 1-second granularity (`date +%N` is a no-op under the image's busybox `date` — derived: `docker run --rm bash:3.2 date +%s.%N` → trailing bare dot, no fractional digits, this session) — the ENTER/EXIT ordering check is still meaningful at that granularity for these hold durations (0.3-1.5s), but sub-second overlaps below 1s could in principle be masked; the host-bash automated regression tests in the committed suite use `date +%s.%N` successfully (GNU coreutils `date`, real nanosecond precision, confirmed via the `python3 on-the-record/monitors/test_poll_heartbeat.py` run above) and are the tests actually gating CI, not this one-off container run.

**5. Overhead.** derived: this session's benchmark script (`/tmp/otr-2919-verify/bench.py`, not committed — a one-off timing harness), 12 repetitions × 50 ticks each, `POLL_HEARTBEAT_MAX_TICKS=50 POLL_HEARTBEAT_SLEEP_SECONDS=0`, same restricted-PATH-without-flock harness the existing `t_alive_stamp_write_survives_missing_flock_issue_2919` test uses, against the pre-this-fix commit (`a40a6452`, PR #2935's fix) and this fix:
```
old (PR#2935 fix): median=0.25ms
new (this fix): median=0.25ms
```
No measurable regression. derived: `git diff a40a6452 HEAD -- on-the-record/monitors/poll-heartbeat.sh | grep -A2 '_alive_stamp_has_flock.*-eq 1'` → empty output, this session — zero lines changed inside the `if [ "${_alive_stamp_has_flock}" -eq 1 ]` branch body — the flock-present path (every Linux host) is untouched.

## Why

Per refactoring-legacy-seam-selection rule 4 (base the Sprout/Wrap-vs-full-seam choice on confidence and budget), the fix stayed inside the existing sprouted `_alive_stamp_lock_owner_status`/`_alive_stamp_write` seam PR #2935 already established rather than introducing a new abstraction — the defect was a sequencing bug inside an already-isolated function, not a reason to widen the seam (rule 6).

Three alternative designs were considered and rejected for the forming-window race:

- **Re-verify ownership immediately before the critical-section write** (read back `owner.pid`, confirm it still equals `$$`), the resolution path the adversarial review itself suggested. Rejected: traced through concretely, this does not close the race. If a challenger reclaims the lock and a third process (or the same challenger) recreates it with a different pid between the original holder's write and its read-back, the original holder's own write could itself have just overwritten the new legitimate holder's pid file — a read-back-after-write only re-confirms what was just written, it cannot detect a write that arrives after the read-back check but before the original holder's critical-section write. This narrows the window without closing it — the opposite of what the task asked for.
- **Atomic rename from a pre-populated staging directory** (`mkdir` a uniquely-named temp dir, write the pid inside it while invisible, then rename it onto the shared lockdir name). Rejected on portability grounds specific to this issue: the shared lockdir name may already exist (held by a contender), and portable `mv` without GNU's `-T` flag moves a source directory *into* an existing destination directory rather than atomically replacing it — this is exactly the platform this issue is about (macOS ships BSD `mv`, which has no `-T` equivalent), so this design would have reintroduced a macOS-specific defect while fixing a macOS-specific one.
- **A single-command noclobber file write** (chosen). Portable POSIX shell behavior available in bash 3.2 (the `O_EXCL`-backed `noclobber` redirection is documented bash behavior, not GNU/BSD-specific), requires no new external binary, and structurally removes the two-command gap rather than narrowing it or working around it with a second check. Also reduces external-process forks on the fast path versus the mkdir+printf+mv+rm+rmdir sequence it replaces (no overhead regression measured, point 5 above), rather than merely avoiding a regression.

For the zombie/reap-uncertainty gap, the task's own framing named two options: find a recovery path not solely reliant on pid liveness, or document the assumption plainly. The `acceptance:` line under point 2 in "What was done" above covers which of the two was pursued and why (both, with the trade-off stated inline in the code) — not repeated here to keep this section to rationale rather than a second outcome claim.

## What did not work

- The first attempt at the real-bash-3.2 concurrency proof launched each worker as its own separate `docker run` container. derived: this session's own first-attempt transcript — this produced clean-looking results (no logged overlaps), but the setup was not trustworthy: separate `docker run` invocations get separate PID namespaces, so `kill -0 <pid>` from one worker's container checking another worker's recorded pid is checking an unrelated process table — close to meaningless for the `alive`/`dead` branches (though the atomic-noclobber-write mutual-exclusion property itself, being a pure filesystem guarantee, was not actually invalidated by this mistake). Rebuilt as a single `docker run --init` container running all workers as real background sibling processes (shared PID namespace) before trusting the result — point 4 above is from the corrected setup.
- The same per-worker-container setup broke crash recovery entirely at first, for an unrelated reason: `kill -9 $$` where `$$` was the container's own PID-1 process did not terminate it. canonical: `docker run --rm bash:3.2 bash -c 'kill -9 $$; echo after'` → printed `after` (Linux's PID-namespace-init signal special-casing ignores default-action signals for a namespace's PID 1 unless something like `docker run --init` inserts a real init as PID 1), versus `docker run --rm --init bash:3.2 bash -c 'kill -9 $$; echo after'` → produced container exit code 137 (killed) and no `after` output, this session. Fixed by adding `--init` to every container invocation in this session's verification scripts; not a production concern, since `poll-heartbeat.sh` never runs as a container's own PID 1 in deployment.

## Upstream basis

- `docs/issue-2919/reports/adversarial-review-95d4569a.md` (commit `2a1d4dd3`, read from the working tree this session) — identified both defects fixed here (points 1 and 2, "Open findings").
- PR #2935 (github.com/tokenmaxxxer/on-the-record/pull/2935), commits `e2441a9b` + `2585022d`, cherry-picked onto this branch (`git cherry-pick -x e2441a9b 2585022d`, this session) as the base this fix builds on, per the spawning task's instruction.
- `docs/specs/platform-capabilities.md` and `docs/handbooks/monitor-liveness.md` — basis for the zombie/reap-uncertainty finding's platform-capability boundary; already cited and read in full by the adversarial review, re-confirmed present at the cited paths this session via `git ls-files`.
- `on-the-record/monitors/poll-heartbeat.sh`, `on-the-record/monitors/test_poll_heartbeat.py` — the files modified. All specific line-range claims above are from this session's own Read-tool views and `git diff`/`grep -n` output against the working tree.
- `docker.io/library/bash:3.2` — the real bash-3.2 execution environment for this session's live concurrency and crash-recovery proof (point 4 above), pulled and run this session.

## Open findings

None from this session's own fix. Two items the fix intentionally does not resolve, stated rather than hidden:

- The forming-window residual (a reader observing the lockfile between its `open()` and `write()` inside the single atomic command) is not literally zero-width — see point 1's "Residual, stated precisely" paragraph above. Not treated as an open defect requiring further work: it is bounded by inter-syscall CPU-instruction distance, not by anything schedulable from outside the process, and is materially different in kind from the multi-second host-load-pause window this issue reports.
- The max-age valve's 60s trade-off (point 2 above) is a deliberate, permanent property of any pid-liveness-based lock recovering from an unverifiable-reap-timing platform, not a bug to close later — closing it would require either a platform-provided prompt-reap guarantee this repo cannot obtain, or abandoning pid-based liveness entirely for a mechanism this repo also has no primitive for. Resolution path, if ever revisited: none available from this repository alone; would need a platform capability change outside this repo's control.

## Next steps

None — `loop_state: landed`. All acceptance-shaped checks from the spawning task (forming-window close, honest residual statement, zombie/reap-uncertainty either-fixed-or-documented, live proof under real bash 3.2 with flock removed including a crashed holder, must-not checks) are addressed above with `derived:`/canonical citations from this session's own tool calls.
