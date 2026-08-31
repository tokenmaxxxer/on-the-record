---
issue: 2919
role: silent-failure-audit+refactoring-legacy-seam-selection-b039601c
author: silent-failure-audit+refactoring-legacy-seam-selection-b039601c
skills: silent-failure-audit (skill-repository(c05de12)), refactoring-legacy-seam-selection (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2919/reports/adversarial-review-67ff85fb.md (finding 1 -- the defect this round fixes)
    sha: 29d00cb553aec34cd7c87e950cd4b4153ead24de
  - path: on-the-record/monitors/poll-heartbeat.sh, on-the-record/monitors/poll_heartbeat_delta.py, on-the-record/monitors/test_poll_heartbeat.py at PR #2948's branch tip
    sha: 2bdbb553c07e810730dcdaa8eeeaba3017c17950
---

# issue-2919 — silent-failure-audit+refactoring-legacy-seam-selection-b039601c record

skill-verdict: silent-failure-audit — applied: invoked; loaded via Skill tool before finalizing the fix. canonical: this session's own tool-call transcript (Skill invocation of `silent-failure-audit`, this session). Used to classify the new release-path branch in `_alive_stamp_write` (`on-the-record/monitors/poll-heartbeat.sh`, the `if [ "${_owner_pid_at_release}" = "$$" ]; then rm ...; else _poll_watchdog_log_append ...; fi` added this round, commit `c0ca440dd56bf554a1f97863fb732517f2030e9d`) as **Handled** (criteria a+e: logged with context via `_poll_watchdog_log_append`, distinguishable from an ordinary silent release) rather than Silently Absorbed — the defect this round fixes was itself exactly a Silently-Absorbed-shaped omission (an unconditional `rm -f` with no ownership check). The pre-existing `rm -f "${_lockfile}" 2>/dev/null || true` best-effort-cleanup pattern used throughout the surrounding dead/forming/max-age eviction branches (unchanged by this round, outside the write set) was left as-is: an `rm` failure there self-heals via the existing dead-holder recovery path on the next tick's contention, a bounded, already-reviewed cost from prior rounds, not a new gap this round introduces.
skill-verdict: refactoring-legacy-seam-selection — not-applicable: this fix adds a direct ownership check inline at the exact flagged release-path line, symmetric in style and location to the existing acquire-side ownership check a few lines above it in the same function — no seam-placement or Sprout-vs-Wrap-vs-object-seam decision arises, since nothing is being extracted into a new independently-testable unit or having an external dependency faked out for testing purposes.
other mounted skills: not triggered (work-in-english — all code, comments, commit messages, and this record are in English per standing policy, applied without needing the Skill tool since no Korean-language work surface arose in this session's writes; verify-finding-record — this is a fix-delivery record, not a defect-verification-outcome record under docs/issue-<n>/reports/defect-verification/).

## What was done

Round 4 on issue #2919's flock-absent mutex, closing the defect
`docs/issue-2919/reports/adversarial-review-67ff85fb.md` finding 1.
canonical: `docs/issue-2919/reports/adversarial-review-67ff85fb.md` lines
26-38, 111-114 (read this session) — the release path's unconditional
`rm -f "${_lockfile}"` never re-checked the lockfile still named its own
pid, so a holder force-reclaimed by the max-age valve while still
genuinely alive could, on its own later normal completion, delete a
different, currently-active holder's lockfile. That review live-reproduced
it with a 3-worker harness (worker A removes worker B's active lock,
worker D then enters alongside still-active B).

canonical: `gh pr view 2948 --json state,url` (this session) → `{"state":"OPEN", ...}` — the fix this round closes a defect in, PR #2948, is not merged.

Work sequence (each step its own commit, per the process note that two
earlier sessions on this issue died uncommitted):

1. commit `2a542b60492ee94d5f6444750612de12ce32391b` — brought in PR
   #2948's three code files (`poll-heartbeat.sh`, `poll_heartbeat_delta.py`,
   `test_poll_heartbeat.py`) via `git checkout
   origin/issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d
   -- <3 paths>`, per the spawning task's instruction to build on that
   branch's content as "the current best version." Targeted checkout of
   just those 3 files rather than a full branch merge: derived: `git diff
   --stat origin/main
   origin/issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d`
   (this session) showed the raw branch diff also carried unrelated docs
   deletions from other issues that had landed on `main` after PR #2948's
   branch point (not part of this fix).
2. commit `c0ca440dd56bf554a1f97863fb732517f2030e9d` — the fix: in
   `_alive_stamp_write`'s no-`flock` branch, before the final `rm -f
   "${_lockfile}"`, read the lockfile's current content back
   (`_owner_pid_at_release="$(cat ...)"`) and compare to `$$`; remove
   only on a match, otherwise skip the removal and log it distinctly via
   `_poll_watchdog_log_append`.
3. commit `938bd25d7700019e2a3d5e94e4d28eb669cd55bf` — a new regression
   test,
   `t_alive_stamp_mutex_evicted_live_holder_release_does_not_corrupt_other_holder_issue_2919`,
   reproducing the reviewer's exact A/B/D scenario using the existing
   `_write_mutex_harness`/`_run_mutex_worker` test infrastructure (real
   subprocesses running the actual extracted function bodies, no
   reimplementation). Asserts worker D's `ENTER` never precedes worker
   B's `EXIT`, and that A's release is logged as skipped, not silent.

derived: `python3 on-the-record/monitors/test_poll_heartbeat.py` (this session):
```
ok  t_unkeyed_line_insertion_suppresses_unchanged_lines_below

43/43 passed
```
(42 pre-existing tests plus the new one from step 3, all passing.)

**Live reproduction under the reported platform (bash 3.2, `flock`
absent from PATH), the reviewer's own attack scenario re-run against the
fixed code.** derived: a from-scratch harness
(`/tmp/otr-2919-verify4/{worker.sh,run_scenario1.sh,check_overlap.py}`,
scratch tooling, not committed — extracted the real
`_alive_stamp_lock_owner_status`/`_alive_stamp_write` function bodies
verbatim via `sed -n '170,403p' on-the-record/monitors/poll-heartbeat.sh`
this session, cross-checked via `diff` against the instrumented copy to
confirm only pure-instrumentation lines were added), run inside
`docker run --rm --init -v /tmp/otr-2919-verify4:/work -w /work bash:3.2
bash -c 'mv /usr/bin/flock /root/flock.bak; ...'` (this session; `flock`
confirmed present-then-removed via `command -v flock; echo rc=$?` →
`rc=1` after the move). Same A/B/D setup as the reviewer's own scenario
(A: `max_age=100`, holds 5-10s genuinely alive; B: `max_age=1-3`,
force-reclaims A's live lock 1-3s in, then holds 3-12s of its own; D:
`max_age=100`, contends after B has entered).

derived: `docker run --rm --init -v /tmp/otr-2919-verify4:/work -w
/work bash:3.2 bash -c 'mv /usr/bin/flock /root/flock.bak; bash
/work/run_scenario1.sh'` (this session, repeated 3 separate invocations),
final invocation's event log:
```
1788161116. ENTER A pid=12
1788161121. ENTER B pid=13
1788161126. PRE_RELEASE_OWNER_CHECK lockfile_currently_names=13 A pid=12
1788161126. [log:A] [alive-stamp-lock] release skipped: lockfile /work/run1/stamp.json.lockfile no longer names this holder (pid 12) -- current owner 13 (this holder was likely force-reclaimed by the max-age valve while still alive; removing would delete a live holder's lock)
1788161126. EXIT A pid=12
1788161133. PRE_RELEASE_OWNER_CHECK lockfile_currently_names=13 B pid=13
1788161133. EXIT B pid=13
1788161134. ENTER D pid=14
1788161134. PRE_RELEASE_OWNER_CHECK lockfile_currently_names=14 D pid=14
1788161134. EXIT D pid=14
```
In every invocation, A's `PRE_RELEASE_OWNER_CHECK` shows the lockfile
naming a different pid (B's) than A's own, and A's release is logged as
skipped rather than executed — the exact point the reviewer's own
instrumentation showed the old code silently deleting B's live lock.
D's `ENTER` is at or after B's `EXIT` in every invocation (shown above:
D enters at `1134`, strictly after B's `1133`). Sub-second ordering
between B's `EXIT` and D's `ENTER` could not be established from this
container's own `date` binary (see "What did not work"), so the
non-overlap claim for the B/D pair rests on the filesystem's own
happens-before guarantee rather than log-timestamp granularity:
derived: reading the fixed code (this session) — D's
`noclobber`-guarded `printf '%s' "$$" >"${_lockfile}"` uses `O_EXCL`
semantics and can only succeed once the path is absent, and the only
thing that removes B's own lockfile while B is genuinely alive is B's
own ownership-matched `rm -f` in its own release (the fix under test) —
so D's successful acquire is causally downstream of B's own `rm`, not
merely temporally close to it. derived: `python3 check_overlap.py
run1/events.log` (this session, run against each of the 3 invocations'
logs) reported the only detected critical-section interval overlap in
each case as A-vs-B (A `ENTER` before A `EXIT`, overlapping B's
`ENTER`-to-`EXIT`) — the pre-existing, already-disclosed max-age valve
trade-off from PR #2948, unchanged by this round, not the defect under
test; no B-vs-D overlap was reported in any of the 3 runs.

**Must-not-regress checks.** derived, this session: `git diff
2a542b60492ee94d5f6444750612de12ce32391b
c0ca440dd56bf554a1f97863fb732517f2030e9d --
on-the-record/monitors/poll-heartbeat.sh | grep -B2 -A8 'flock -x 200'`
→ empty (the `flock`-present branch is byte-identical, zero lines
changed); `grep -n '^while true\|^if command -v flock\|_alive_stamp_has_flock='
on-the-record/monitors/poll-heartbeat.sh` → both setup blocks (the
flock-detection block, and the pre-existing patrol-skills-query block)
remain before `while true` — no setup code moved into the hot loop;
`git diff 2a542b60492ee94d5f6444750612de12ce32391b
c0ca440dd56bf554a1f97863fb732517f2030e9d --
on-the-record/monitors/poll-heartbeat.sh | grep -i 'patrol\|role'` →
empty (patrol code and the retired role axis untouched); `git diff
2a542b60492ee94d5f6444750612de12ce32391b
c0ca440dd56bf554a1f97863fb732517f2030e9d --stat --
on-the-record/monitors/monitors.json` → empty (no Monitor-registration
change). derived: `docker run --rm -v
.../on-the-record/monitors:/m bash:3.2 bash -n /m/poll-heartbeat.sh` (this
session) → exits 0, no output — the fixed script parses cleanly under
real bash 3.2. The pre-existing regression tests for the two properties
prior rounds fixed both still pass unmodified, in the same full-suite
run cited above:
`t_alive_stamp_mutex_never_evicts_slow_live_holder_issue_2919`
(live-slow holder not evicted) and
`t_alive_stamp_mutex_recovers_crashed_holder_issue_2919` /
`t_alive_stamp_mutex_max_age_recovers_unreaped_holder_issue_2919`
(crashed/zombie holder recovers).

## Why

The reviewer's own record named the resolution path directly (canonical:
`docs/issue-2919/reports/adversarial-review-67ff85fb.md` line 113, read
this session): "the same fix the acquire side already received ... needs
to apply symmetrically to the release side -- read `${_lockfile}`'s
current content back and compare to `$$` immediately before the final
`rm -f`, and skip the removal (log it distinctly, per silent-failure-audit)
if it no longer names this process." This round implements exactly that,
at the exact line the review cited.

**Residual window, stated precisely (per the task's requirement and
#2935/#2948's own precedent of honest disclosure):** the `cat` (read)
and the `rm -f` (remove) that follows it are still two separate shell
commands, not one atomic operation — bash has no compare-and-delete
primitive, and no `flock` is available on this branch by definition. If
*this* holder's own eviction by the max-age valve lands in the exact gap
between its own ownership read and its own `rm`, the same failure shape
could in principle reappear: this holder's stale "yes, still mine"
decision, acted on one command later than it was true. This is not
eliminated, only narrowed: previously the window was this holder's
entire remaining hold-plus-write duration (reachable any time a holder
ran past the default `POLL_HEARTBEAT_ALIVE_LOCK_MAX_AGE`, which the
max-age valve's own design already concedes will happen); now it is
bounded by two adjacent syscalls with no other command from this script
able to run in between and widen it by host load or scheduling — the
identical honesty standard the round-3 noclobber acquire fix already
applies to its own `open()`/`write()` residual (canonical: code comment
at `on-the-record/monitors/poll-heartbeat.sh` lines 264-274, read this
session). A true atomic ownership-checked delete would need either
`flock` (unavailable, that is the premise of this branch existing) or an
inode-identity check via a held file descriptor (`-ef` against
`/dev/fd/N`) — which itself would still have a test-then-act command
boundary of its own — so it was not pursued as disproportionate
complexity for a residual already narrowed by orders of magnitude.

**Why not just remove the max-age valve as the cheap fix:** it is not
the fix — the valve is what makes the newly-fixed scenario reachable,
but it also remains the only recovery path for a lock held by a zombie
process the platform never reaps (`kill -0` cannot distinguish a live
holder from an unreaped one — canonical: `on-the-record/monitors/poll-heartbeat.sh`
lines 276-286, read this session; PR #2948's own disclosed trade-off).
Removing it would trade a now-narrowed, honestly-disclosed release-path
race for reintroducing an unbounded wait against a lock that can never
legitimately clear — explicitly listed as a must-not in this round's
task.

## What did not work

- The first draft of the scratch docker-based verification harness's
  higher-precision timestamp attempt (`sed -i 's/date +%s/date
  +%s.%N/g' worker.sh instrumented_extract.sh`) was applied to both the
  harness's own logging calls AND, by accident, the sourced copy of the
  real production code inside `instrumented_extract.sh` — this would
  have broken the real script's `$(( $(date +%s) - _wait_started ))`
  integer arithmetic had it been run against production code (it wasn't;
  this was caught in the scratch `/tmp` harness before any repository
  file was touched, and no repository file was ever affected). Fixed by
  regenerating `instrumented_extract.sh` fresh from the untouched
  `real_extract.sh` and re-applying only the pure-instrumentation lines.
  derived: `diff real_extract.sh instrumented_extract.sh` (this session,
  scratch dir) → 3 added lines, all `_harness_log`/`sleep` instrumentation
  calls, confirming no production `date +%s` call was altered in the
  regenerated copy.
- The `bash:3.2` Docker image's own `date` binary does not support `%N`
  (nanosecond) formatting — it returns a literal trailing `.` with no
  digits, which the first version of the scratch overlap-checking script
  (`check_overlap.py`, not committed) failed to parse (`int()` on
  `"1788160924."` raised `ValueError`, this session's own traceback).
  Fixed by parsing as float with the trailing dot stripped. Sub-second
  precision was not actually recoverable from this container's `date`,
  so the final B-vs-D non-overlap claim above relies on the filesystem's
  `O_EXCL` happens-before guarantee instead of log-timestamp ordering.

## Upstream basis

- `docs/issue-2919/reports/adversarial-review-67ff85fb.md` (commit
  `29d00cb553aec34cd7c87e950cd4b4153ead24de`, merged to `main` — canonical:
  `gh pr view 2949 --json state,mergedAt` this session →
  `{"mergedAt":"2026-08-31T07:14:04Z","state":"MERGED"}`) — finding 1,
  the specific defect this round closes, including its own
  live-reproduced `PRE_RELEASE_OWNER_CHECK` instrumentation and event
  log, which this round's harness deliberately re-derives independently
  (own `/tmp` scratch tooling, own docker run) rather than reuses.
- `origin/issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d`
  (PR #2948, commit `2bdbb553c07e810730dcdaa8eeeaba3017c17950`, open,
  not merged — canonical: `gh pr view 2948 --json state,mergedAt,headRefName`
  this session → `{"headRefName":"issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-8f663b5d","mergedAt":null,"state":"OPEN"}`)
  — the three code files brought in as this round's base (commit
  `2a542b60492ee94d5f6444750612de12ce32391b`), per the spawning task's
  instruction to build on "the current best version."
- `docs/issue-2919/reports/adversarial-review-95d4569a.md` — background
  only (the prior review whose two findings PR #2948 closed); not
  re-read directly this round since it is not this round's subject, only
  cited indirectly via adversarial-review-67ff85fb's and the code
  comments' own references to it.

## Open findings

- **The narrowed read-then-rm residual on the release path** (see "Why"
  above): not a defect discovered this round, but a known-and-disclosed
  property of this round's own fix, stated explicitly per the task's
  instruction to name any residual precisely. No further action
  proposed — an atomic alternative (inode-identity check via a held file
  descriptor) was considered and set aside as disproportionate
  complexity for a window already narrowed from a multi-second hold
  duration to two adjacent syscalls with nothing else in this script
  able to run between them.
- None else. The two items adversarial-review-67ff85fb itself carried
  forward from PR #2948's own disclosure (the acquire-side
  `open()`/`write()` sub-syscall gap, and the max-age valve's own
  >60s-alive-holder trade-off) are unchanged by this round and were not
  re-litigated.

## Next steps

None from this session — `loop_state: landed`. The fix, its regression
test, and this record are committed on
`issue-2919/silent-failure-audit+refactoring-legacy-seam-selection-b039601c`;
next step is opening the PR against `main`.
