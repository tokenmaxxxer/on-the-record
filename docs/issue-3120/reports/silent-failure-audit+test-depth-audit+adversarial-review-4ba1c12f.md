---
issue: 3120
role: silent-failure-audit+test-depth-audit+adversarial-review-4ba1c12f
author: silent-failure-audit+test-depth-audit+adversarial-review-4ba1c12f
skills: silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: true  # second independent, builder-blind verification of PR #3133's own deliverable against issue #3120's layers 1/2
code_under_review: eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41
loop_state: landed
type: defect-verification-record
breaking: false
verdict: PR #3133's owned scope (probe_heartbeat_rc95_is_classified.py,
  probe_heartbeat_survives_head_change.py, poll-heartbeat.sh layers 1/2)
  graded Present, agreeing with the first verification (PR #3141) on the
  checks and must-nots it already re-derived (see "Re-derivation" below
  for the exact commands/results). This session's own mandate was the
  AFTER-exec behavior PR #3141 did not cover: the alive-stamp write
  happens unconditionally at the top of every loop iteration, before the
  watchdog call that can trigger rc=95, so the write cadence measured
  live across repeated exec restarts never lengthens past
  sleep_seconds -- no false-dead window materializes; the exec runs in
  the loop's own process, confirmed by /proc pid+starttime invariance
  held constant across repeated exec cycles; poll_heartbeat_last_state.json
  survives exec unchanged and the always-emit membership added for
  watchdog-stale-code prevents suppression on byte-identical repeats,
  reproduced directly. All three hypothesized failure modes in this
  session's brief did not materialize, per the measurements below. macOS
  is Unverifiable -- no macOS host was available in this session.
upstream:
  - path: PR #3133 (github.com/tokenmaxxxer/on-the-record/pull/3133),
      fetched as local ref pr-3133-review, head commit eec9a051 -- the
      deliverable under review
    sha: eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41
  - path: docs/issue-3120/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1835e9b5.md
      (PR #3141, first independent verification of the same PR)
    sha: d4da990e122b0cf87baaa812ca25b8c36580c399
---

# issue-3120 — silent-failure-audit+test-depth-audit+adversarial-review-4ba1c12f record

## What was done

Second independent, builder-blind verification of PR #3133 against issue
#3120's layers 1 and 2 (rc=95 classification, exec-based self-heal). Not
a code change -- a verification record only, produced against a
disposable `git worktree` (`/tmp/pr3133-worktree`, removed at the end of
this session) checked out from `refs/pull/3133/head` (`pr-3133-review`,
head `eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41`). PR #3133 itself was
never edited, approved, or merged this session.

canonical: `gh issue view 3120 --repo tokenmaxxxer/on-the-record` output
(full body: the rc=95 defect, the wake-notice defect, the three-layer
prescription, the Withdrawn section, the acceptance-amendment splitting
the five checks across PR #3133/#3132) and `gh pr view 3133 --repo
tokenmaxxxer/on-the-record` output (state: OPEN, additions 897/deletions
2, trailer `Advances #3120`) -- both read in full before any check ran.

Scope, per the spawning brief: grade only what PR #3133 owns --
`gates/probe_heartbeat_rc95_is_classified.py` (untracked on this
session's own branch -- a new file introduced by PR #3133),
`gates/probe_heartbeat_survives_head_change.py` (untracked on this
session's own branch -- a new file introduced by PR #3133), and
`on-the-record/monitors/poll-heartbeat.sh` (pre-existing, tracked on
this branch, PR #3133 modifies it). `gates/probe_wake_notice_clears.py`
belongs to PR #3132 and is out of scope here.

### Re-derivation of the checks PR #3141 already covered

All ran fresh in `pr3133-worktree`, from a clean fetch of PR #3133's
actual head, not copied from PR #3141's record.

acceptance: `python3 gates/probe_heartbeat_rc95_is_classified.py` in
`pr3133-worktree` -- result:
```
ok
```
rc=0.

acceptance: `python3 gates/probe_heartbeat_survives_head_change.py` in
`pr3133-worktree` -- result:
```
ok
```
rc=0.

acceptance: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q` in `pr3133-worktree` -- result:
```
46 passed in 24.49s
```

acceptance: `python3 -m pytest tests/ -q` in `pr3133-worktree` -- result:
```
254 passed, 2 warnings in 10.19s
```
The 2 warnings are pinned-fixture-divergence warnings in
`test_skill_candidates_floor.py` (issue #3019), unrelated to this diff.

acceptance: `python3 -m pytest test/ -q` in `pr3133-worktree` -- result:
```
15 failed, 548 passed, 3 xfailed in 32.22s
```
derived: `python3 -m pytest test/ -q 2>&1 | grep -c ^FAILED` in
`pr3133-worktree` -- result: `15`. The 15 failing node IDs are in
`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`, and
`test_spawn_skill_judge_haiku_timeout_overlap.py`. derived: `grep -l -E
"poll.heartbeat|watchdog" test/test_convention_equivalence.py
test/test_local_dependency_env.py
test/test_spawn_cross_family_skill_selection.py
test/test_spawn_artifact_skill_pairing.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py` in
`pr3133-worktree` -- result: empty output, no match -- none of the five
failing files reference `poll-heartbeat.sh`, `watchdog.py`, or
`spawn.py`'s watchdog role. Matches PR #3133's own test-plan claim (15
failed/548 passed/3 xfailed) exactly, and confirms these are
pre-existing/owned by #3091, not introduced by this diff.

canonical: `git diff main pr-3133-review -- watchdog.py spawn.py` --
result: empty (no output) -- the freshness check itself
(`watchdog_freshness_check`) is untouched by this PR. must-not #1 (do
not remove/weaken the freshness check): Present.

canonical: `gh pr diff 3133 --repo tokenmaxxxer/on-the-record | grep -n
"^diff --git"` -- result: exactly 8 paths changed, no others. Three are
pre-existing files this session's own branch already tracks (PR #3133
modifies them): `on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/monitors/poll_heartbeat_delta.py`,
`on-the-record/monitors/test_poll_heartbeat.py`. Five are new files PR
#3133 introduces, untracked (untracked) on this session's own branch:
`gates/probe_heartbeat_rc95_is_classified.py` (untracked),
`gates/probe_heartbeat_survives_head_change.py` (untracked),
`docs/issue-3120/reports/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md`
(untracked -- the builder's own record), its own
`deviation-log/20260902T091133480683-db31d53292f19c61.md` sub-path
(untracked -- same record's deviation log), and
`docs/reports/product/priorities/20260902T091133530553-3645434.md`
(untracked -- a Stop-hook priorities capture). Confirms
`watchdog.py`/`spawn.py` are absent from the diff by the diff's own file
list, not merely by the two-file spot-check above.

must-not #2 (do not treat manual re-arm as recovery): Present. canonical:
`on-the-record/monitors/poll-heartbeat.sh` diff hunk (the `elif
[ "${watchdog_rc}" -eq 95 ]` / `exec bash "${_exec_target}"` block) --
this PR's mechanism is the `exec` self-heal, not an instruction to a
human/orchestrator; no `[MONITOR-DEAD]`-style prose-instruction text
anywhere in this PR's diff (confirmed by `gh pr diff 3133 | grep -n
"MONITOR-DEAD"` -- result: empty, no match).

must-not #3 (do not shorten cadence or re-arm more aggressively):
Present. canonical: `gh pr diff 3133 --repo tokenmaxxxer/on-the-record |
grep -n "sleep_seconds\|POLL_HEARTBEAT_SLEEP_SECONDS"` -- result: empty,
no match -- the sleep-cadence handling is untouched by the diff. This
session's own alive-stamp-cadence measurement below (experiment 1) is
direct evidence the cadence is unchanged across a restart in practice,
not just unchanged in the source text.

derived: `gh pr view 3141 --repo tokenmaxxxer/on-the-record --json body
-q .body` -- result: its test-plan section lists the identical 4
gate/pytest checks plus `test/ -q` re-derived above, all with matching
counts (`ok`, `ok`, `46 passed`, `254 passed`, `15 failed, 548 passed, 3
xfailed`) -- this session agrees with PR #3141 on every re-derived
check, no disagreement to record.

### This session's own emphasis: what happens AFTER the exec

PR #3141 verified the exec restart happens and the loop keeps ticking
(tick-count-based proof). canonical: `gh pr view 3141 --repo
tokenmaxxxer/on-the-record --json body -q .body` -- result: no mention
of real-time cadence, `/proc`, pid, or starttime anywhere in its body --
it did not measure real-time cadence across the restart boundary, did
not independently confirm the exec runs in the loop's own process
rather than the `$( )` subshell, and did not exercise the delta-state
file across a real restart. This session ran three additional empirical
experiments against the real, unmodified `poll-heartbeat.sh` copied out
of `pr-3133-review`.

**1. Alive-stamp cadence across repeated exec restarts.**

acceptance: standalone rig at `/tmp/exec_probe` (fake `spawn.py` whose
`watchdog` role always returns rc=95 and appends a JSON line
`{"pid":..., "ppid":..., "t": time.time()}` to a marker file on every
invocation; a real copy of `pr-3133-review`'s
`poll-heartbeat.sh`/`poll_heartbeat_delta.py`/`poll-rearm.sh` as the
exec target; `POLL_HEARTBEAT_SLEEP_SECONDS=2`,
`POLL_HEARTBEAT_MAX_TICKS=8`), run for ~22s -- result (marker.log,
timestamp column only):
```
1788343947.902802
1788343950.008670
1788343952.129767
1788343954.225013
1788343956.327966
1788343958.457369
1788343960.614624
1788343962.738948
1788343964.871263
1788343966.970253
1788343969.104401
```
derived: consecutive-difference computation over the column above --
result: gaps of 2.106, 2.121, 2.095, 2.103, 2.129, 2.157, 2.124, 2.132,
2.099, 2.134 seconds -- every gap is `sleep_seconds` (2) plus ~0.1-0.16s
of subprocess/exec overhead, none doubled or otherwise lengthened,
across 10 consecutive exec-triggering ticks (every listed tick returned
rc=95 and exec'd, confirmed by the fake spawn.py's own rc=95-only
branch).

canonical: `on-the-record/monitors/poll-heartbeat.sh` lines 482-484 in
`pr-3133-review` (`while true; do sleep "${sleep_seconds}";
_alive_stamp_write; ...`) -- `_alive_stamp_write` runs unconditionally
at the top of every loop iteration, immediately after `sleep` and before
the `poll-due`/watchdog call at line ~506-509 that can produce rc=95.
So the stamp is freshly written in the same iteration that later
detects staleness and execs -- the last stamp write before a restart and
the first stamp write after it are exactly `sleep_seconds` apart,
identical to steady-state. `on-the-record/hooks/directive.sh`'s
`_monitor_liveness_check_and_notify()` staleness threshold
(`MONITOR_LIVENESS_STALE_SECONDS:-360`, three cadences at the 120s
default) never sees a gap wider than one cadence from this mechanism.
This session's brief hypothesized "the fix trades a silent death for a
120s false-dead window on every HEAD change" -- the measurement above
does not show this happening.

**2. Exec runs in the loop's own process, not the subshell.**

canonical: `on-the-record/monitors/poll-heartbeat.sh` in
`pr-3133-review` -- `report="$(python3 "${CHECKOUT}/spawn.py" watchdog
--auto-respawn 2>&1)"; watchdog_rc=$?` is the only command substitution
involved in producing `watchdog_rc`, and it captures only the
watchdog's own stdout; `watchdog_rc` itself is read via `$?` OUTSIDE
that substitution. The `if [ "${watchdog_rc}" -eq 95 ]; then ...; exec
bash "${_exec_target}"; fi` block several lines later is a plain
top-level `if` in the loop body, never itself wrapped in `$( )`.

acceptance: launched `bash pr-3133-review`'s `poll-heartbeat.sh` in the
background against the same always-95 rig
(`POLL_HEARTBEAT_SLEEP_SECONDS=1`, `POLL_HEARTBEAT_MAX_TICKS=3`),
captured `$!` as the outer bash pid (32078), sampled `/proc/32078/comm`
and `/proc/32078/stat` field 22 (process start time) every 0.8s for
~9.6s -- result:
```
t=1 pid=32078 alive=yes comm=bash starttime=848792753
t=2 pid=32078 alive=yes comm=bash starttime=848792753
t=3 pid=32078 alive=yes comm=bash starttime=848792753
t=4 pid=32078 alive=yes comm=bash starttime=848792753
t=5 pid=32078 alive=yes comm=bash starttime=848792753
t=6 pid=32078 alive=yes comm=bash starttime=848792753
t=7 pid=32078 alive=yes comm=bash starttime=848792753
t=8 pid=32078 alive=yes comm=bash starttime=848792753
t=9 pid=32078 alive=yes comm=bash starttime=848792753
t=10 pid=32078 alive=yes comm=bash starttime=848792753
t=11 pid=32078 alive=yes comm=bash starttime=848792753
t=12 pid=32078 alive=yes comm=bash starttime=848792753
```
Same pid, same kernel-reported start time on all 12 samples while
multiple exec-triggering ticks fired underneath (the always-95 fake
guarantees at least 9 restarts in 9.6s at a 1s cadence). `/proc/<pid>/stat`
field 22 is the kernel's own process start time, a value that does NOT
change across `exec` within the same process but WOULD differ if the
pid had exited and a different process happened to reuse the number.
Had the exec instead fired inside the `$( )` subshell -- the mistake
this session was asked to rule out -- the subshell would exec and vanish
while the parent loop continued unaffected on stale code, a state
indistinguishable from a working fix to any probe that only checks "is
something still ticking." The pid+starttime invariance above rules this
out directly: the same process that started the loop is still the one
ticking after repeated restarts. Cleanup: `pkill -9 -f
poll-heartbeat.sh` after the sampling window (the always-95 rig loops
forever by design) -- result: `ps aux | grep -i "poll-heartbeat\|exec_probe" | grep -v grep`
returned empty, confirming no leftover process.

**3. Delta-state (`poll_heartbeat_last_state.json`) across exec.**

canonical: `cat ${CHECKOUT}/runs/poll_heartbeat_last_state.json` after
the always-95 rig's run in experiment 1 above -- result:
```
{"lines": {"watchdog:코드-신선도": "[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀘다 (시작=aaaaaaaaaaaa 현재=bbbbbbbbbbbb) — 재기동 필요", "fixed:hash:dd3633ea8459": "[watchdog-stale-code] watchdog exited rc=95 (checkout HEAD changed — restarting)"}, "last_emit_epoch": 1788344129, "surfaced_returned_pr_issues": []}
```
This is a real file under `${CHECKOUT}/runs/`, untouched by `exec`
(exec replaces the process image, not the filesystem) -- the state
carries content from before the most recent of the run's 10+ restarts
forward, not reset to empty.

canonical: `on-the-record/monitors/poll-heartbeat.sh`'s stdout from the
same run -- result (representative excerpt, the pattern repeats for
every one of the 10+ ticks):
```
[watchdog-stale-code] watchdog exited rc=95 (checkout HEAD changed — restarting)
[poll-heartbeat] stale code (rc=95) -- restarting via exec /tmp/exec_probe/checkout/on-the-record/monitors/poll-heartbeat.sh
```
The `[watchdog-stale-code]` line re-emits on every tick even though the
fake watchdog produces byte-identical text every time, which requires
`poll_heartbeat_delta.py`'s `ALWAYS_RE` extension. canonical:
`on-the-record/monitors/poll_heartbeat_delta.py` line 44 in
`pr-3133-review` -- result:
```
r"^\[(resume|orphaned|watchdog-crash|watchdog-stale-code|awaiting-approval)\]"
```
-- without this extension, the second and later occurrences of an
unchanged line would be suppressed by the line-keyed dedup. This
session's brief hypothesized two possible defects here: a state reset
(noisy re-emit-everything on the first post-exec tick) or a
preserved-but-suppressing state (the heal line gets swallowed as
"unchanged" on a repeat). Neither happened: state is preserved (ruling
out the reset), and the always-emit membership prevents suppression
(ruling out the swallow) -- both against literally identical repeated
text, the harder case than a real HEAD-hash change would present.

acceptance: `python3 -m pytest
on-the-record/monitors/test_poll_heartbeat.py::t_poll_heartbeat_delta_always_emits_stale_code_label
-v` in `pr3133-worktree` -- result:
```
PASSED
```
This shipped test (`on-the-record/monitors/test_poll_heartbeat.py:1789`
in `pr-3133-review`) drives `poll_heartbeat_delta.py` directly with
identical text on two successive ticks and asserts the line survives
both; this session's rig above corroborates that unit-level test against
the real end-to-end script rather than the delta script in isolation.

**4. macOS.** No macOS host was available in this session -- this
criterion is Unverifiable, not Present, and should not be read as "no
macOS-specific defect exists." canonical:
`on-the-record/monitors/poll-heartbeat.sh` lines 529-593 in
`pr-3133-review` (the layer-1/2 diff hunk) -- uses only
`printf`/`[ -f ]`/`exec bash <path>`, none of which are Linux-specific
the way the pre-existing `/proc`-based liveness pairing
(`watchdog.py`'s `_proc_start_time`, already documented in that file's
own comments as degraded-not-broken on macOS, issue #2924) is -- so the
new code in this PR does not obviously add a macOS-specific gap on top
of the pre-existing, disclosed one. This is a code-reading inference,
explicitly weaker than the measurements in 1-3 above, offered as
context rather than a verified claim, and left Unverifiable in the
verdict.

### silent-failure-audit pass over the new code

Enumerated the layer-1/2 diff's fallible-operation sites in
`on-the-record/monitors/poll-heartbeat.sh`. canonical: the diff hunk at
lines 529-593 of that file in `pr-3133-review`:

1. `[ -f "${_exec_target}" ]` guard before `exec bash "${_exec_target}"`
   -- Handled: an explicit check-then-act with a distinct advisory
   message (`restart target unavailable ... skipping restart this
   tick`) on the negative branch, not a bare skip. Matches the
   pre-existing `[ ! -f "${CHECKOUT}/spawn.py" ]` guard's pattern
   elsewhere in the same file (issue #2163, unchanged by this PR).
2. The check-then-exec window itself (the target file could be removed
   between the `[ -f ]` test and the `exec` a line later) -- the one
   path in the new code where a failure is not caught by anything in
   this diff; `exec` failing there kills the whole process with only
   bash's own uncaptured stderr line, no `[watchdog-...]`
   classification, no next tick. This re-opens a narrow version of the
   same silent-death shape the issue reports, scoped to a race window
   instead of every HEAD change. canonical: `gh pr view 3133 --repo
   tokenmaxxxer/on-the-record --json body -q .body` -- result contains
   the phrase "a residual TOCTOU open finding on the exec-target
   existence check", i.e. PR #3133 discloses this itself; canonical: `gh
   pr view 3141 --repo tokenmaxxxer/on-the-record --json body -q .body`
   -- result contains "stress-raced the check-then-exec window (20000
   attempts, tight racer) -- 12.155% hit rate", i.e. PR #3141
   independently measured and quantified it. This session did not
   re-run that stress race; it was PR #3141's assigned emphasis, and
   this session's own brief pointed at the AFTER-exec behavior instead.
   Recorded here as confirmed-by-reading against the diff and against
   both PRs' own text, not independently re-measured by this session.
3. `python3 "${CHECKOUT}/spawn.py" watchdog --auto-respawn 2>&1` itself
   is captured and its rc fully partitioned by the pre-existing
   `rc>=128||rc==97` crash branch, the new `rc==95` branch, and "any
   other value" falling through unlabeled by design (issue #1274:
   roster_watchdog's rc is an anomaly count, not a crash flag). No
   silent absorption here.

acceptance: `python3 -m pytest
on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_routine_nonzero_rc_gets_neither_label
-v` in `pr3133-worktree` -- result:
```
PASSED
```
confirming point 3 directly rather than by inspection alone. No new
Silently Absorbed site beyond the already-disclosed TOCTOU residual in
point 2.

### test-depth-audit pass over the six new tests in test_poll_heartbeat.py

canonical: `on-the-record/monitors/test_poll_heartbeat.py` lines
1609-1811 in `pr-3133-review`. `t_heartbeat_classifies_stale_code_rc95`
(1609), `t_heartbeat_rc95_not_confused_with_crash_rc97` (1631),
`t_heartbeat_routine_nonzero_rc_gets_neither_label` (1651),
`t_heartbeat_stale_code_restart_target_missing_skips_restart_not_crash`
(1675), `t_heartbeat_stale_code_execs_and_keeps_ticking` (1705),
`t_poll_heartbeat_delta_always_emits_stale_code_label` (1789) -- all six
are Genuine Assertion: each cites specific stdout substrings/counts that
would fail under a broken implementation, e.g. line 1780's exact
watchdog-invocation-count assertion (`n_watchdog_runs == expected`),
which fails identically whether the loop never restarts OR restarts but
does not reset its tick counter. `t_heartbeat_stale_code_execs_and_keeps_ticking`
is the strongest of the six: it exec's into a real copy of the actual
script under test (line 1724, `shutil.copyfile(POLL_HEARTBEAT,
exec_target)`), not a stub, making it a genuine integration test of the
self-heal mechanism rather than mock-dominated.

Coverage gap, not a live defect: none of the six shipped tests assert on
real-time cadence across a restart or on process pid/starttime
invariance. canonical: same line range above (1609-1811) -- no
`time.time()`/`/proc` reference appears in any of the six test bodies,
confirmed by reading that range in full -- exactly the two properties
this session had to build its own standalone rig to measure
(experiments 1-2 above), because the shipped suite proves the loop
keeps ticking (tick-count arithmetic) without proving how soon after a
restart it resumes ticking in wall-clock terms. This session's own
`/proc`/timestamp measurements (experiments 1-2 above, produced this
turn) found no defect there; naming this as a suite-hardening
opportunity for a future session, not a blocker to this PR's Present
grade.

## Why

The spawning brief specifically asked this session not to re-tread PR
#3141's already-covered ground but to attack the one dimension it did
not: post-exec behavior over real time and real process identity, which
static reading of the diff cannot settle on its own (the diff's own
comment "startup_head gets re-captured fresh in the new image" is a
narrative, not a measurement). Building disposable rigs that drive the
real, unmodified script and sampling `/proc` and the on-disk JSON state
directly turns three hypotheses (false-dead window, subshell exec,
suppressed heal-line) from claims into either falsified-with-evidence or
confirmed-with-evidence outcomes, per the three experiments above.

## What did not work

None.

## Upstream basis

- PR #3133, `github.com/tokenmaxxxer/on-the-record/pull/3133`, fetched
  as `refs/pull/3133/head` -> local ref `pr-3133-review`, head
  `eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41`. Reviewed in a disposable
  `git worktree` at `/tmp/pr3133-worktree`. acceptance: `git worktree
  remove --force /tmp/pr3133-worktree && git worktree list` -- result:
  only this session's own checkout listed, confirming the review
  worktree is gone.
- PR #3141 / `docs/issue-3120/reports/adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1835e9b5.md`,
  the first independent verification of the same PR, sha
  `d4da990e122b0cf87baaa812ca25b8c36580c399`. derived: `gh pr view 3141
  --repo tokenmaxxxer/on-the-record --json body -q .body` -- result: its
  test-plan section lists exactly the same 4 gate/pytest checks plus
  `test/ -q` this session re-ran above, confirming the overlap this
  record's "Re-derivation" section addresses.

## Open findings

- The exec-target TOCTOU race (already disclosed by PR #3133, already
  independently measured by PR #3141 at ~12% hit rate under stress
  contention -- canonical: `gh pr view 3133`/`gh pr view 3141` bodies,
  cited in full in the "silent-failure-audit pass" section above): still
  open, not re-measured by this session, tracked against layer 2's
  existing residual rather than a new finding. Resolution path:
  unchanged from PR #3141's record -- narrowing or closing it, if
  pursued, is separate follow-on work, not a blocker to this PR's
  Present grade since it was disclosed rather than hidden and is outside
  both this session's and the acceptance text's stated bar.
- macOS: Unverifiable in this session (no macOS host available in this
  session's own environment). Resolution path: a future session with
  macOS access should re-run `probe_heartbeat_survives_head_change.py`
  and this session's own alive-stamp/pid rigs there specifically, since
  the issue's own text calls out `exec` semantics under the Monitor
  wrapper and mkdir-lock fallback as macOS-divergent risk surfaces.
- Test-suite coverage gap: real-time cadence and process-identity across
  exec are not covered by the shipped `test_poll_heartbeat.py` suite
  (canonical: lines 1609-1811 of that file in `pr-3133-review`, no
  `time.time()`/`/proc` reference in any of the six new tests) -- closed
  empirically instead by this session's own experiments 1-2 above
  (produced this turn), which found no live defect. Open as a hardening
  opportunity, not a live defect. Resolution path: a future session
  could add a `POLL_HEARTBEAT_SLEEP_SECONDS`-driven timing assertion and
  a pid/starttime assertion to `test_poll_heartbeat.py` mirroring
  experiments 1-2, so this property is pinned in the suite rather than
  only verified ad hoc by verification sessions.

## Next steps

None -- this record is terminal (`loop_state: landed`). canonical: this
session's own actions this turn -- no `gh pr merge`, `gh pr review
--approve`, or edit to any file under `pr-3133-review`/PR #3133 was
issued at any point in this session, per the spawning brief's explicit
instruction to build, verify, and report without merging or editing the
PR under review.

## Skill verdicts

- skill-verdict: silent-failure-audit — applied: invoked; enumerated the
  layer-1/2 diff's fallible-operation sites in poll-heartbeat.sh
  (exec-target existence guard, the TOCTOU window, the rc partition).
  canonical: this session's own enumeration and classification produced
  this turn in the "silent-failure-audit pass over the new code" section
  above (diff hunk at `on-the-record/monitors/poll-heartbeat.sh` lines
  529-593 in `pr-3133-review`, cross-checked against
  `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py::t_heartbeat_routine_nonzero_rc_gets_neither_label -v` -- PASSED).
- skill-verdict: test-depth-audit — applied: invoked; classified all six
  new tests in test_poll_heartbeat.py as Genuine Assertion, identified
  one coverage gap (real-time cadence / process-identity across exec).
  canonical: this session's own classification produced this turn in
  the "test-depth-audit pass" section above (`on-the-record/monitors/test_poll_heartbeat.py`
  lines 1609-1811 in `pr-3133-review`).
- skill-verdict: adversarial-review — applied: invoked; this record is
  the structurally independent, builder-blind evaluator session the
  skill describes -- a fresh session with no shared context with PR
  #3133's or PR #3141's authoring sessions beyond their public `gh pr
  view` text, running its own experiments rather than accepting either
  PR's account at face value. canonical: this session's own three
  independent experiments produced this turn (alive-stamp cadence
  measurement, `/proc` pid+starttime sampling, delta-state inspection),
  none of which were requested or described by PR #3133's or PR #3141's
  own text -- the evaluator generated its own falsification attempts
  rather than re-stating the builder's or first verifier's claims.
- other mounted skills: not triggered (work-in-english and
  implementation-audit were not invoked via the Skill tool this
  session).
