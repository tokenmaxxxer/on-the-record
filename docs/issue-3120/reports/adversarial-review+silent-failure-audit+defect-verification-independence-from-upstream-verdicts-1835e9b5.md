---
issue: 3120
role: adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1835e9b5
author: adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1835e9b5
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3133's own deliverable against issue #3120's layers 1/2
code_under_review: eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41
loop_state: landed
type: defect-verification-record
breaking: false
verdict: Layers 1/2 of PR #3133 verified Present against issue #3120 --
  rc=95 gets a distinct [watchdog-stale-code] label (confirmed distinct
  from [watchdog-crash] and from a silent tick by producing all three),
  the exec restart genuinely self-heals a real HEAD change end-to-end
  against the unstubbed script, the freshness check is untouched, and
  both suites match the PR's claimed counts. One corroborated, not new,
  residual: the exec-target TOCTOU race the PR itself already disclosed
  as an open finding is real and reachable at ~12% under active
  contention -- confirmed independently, not a surprise the PR hid, and
  its failure mode is not fully silent (bash's own stderr line still
  reaches the same channel). The platform-Monitor-wrapper open finding
  is honestly hedged; it could have cited process start-time invariance
  under exec (a no-risk argument) to narrow it further, but full
  end-to-end closure requires touching a live, hard-to-reverse resource
  this session also chose not to touch, for the same reason PR #3133 did
  not.
upstream:
  - path: PR #3133 (github.com/tokenmaxxxer/on-the-record/pull/3133),
      fetched as local ref pr-3133-review, head commit eec9a051 -- the
      deliverable under review
    sha: eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41
---

# issue-3120 — adversarial-review+silent-failure-audit+defect-verification-independence-from-upstream-verdicts-1835e9b5 record

## What was done

Independent, builder-blind verification of PR #3133 against issue
#3120's layers 1 and 2 only. `probe_dead_heartbeat_is_rearmed.py` is
layer 3 (issue #3125, not started) and `probe_wake_notice_clears.py`
belongs to PR #3132 -- both untracked on this branch and correctly out
of scope for PR #3133, confirmed later in this record.

canonical: `gh issue view 3120` output (full body, Acceptance section,
three must-nots, Withdrawn section) and `gh pr view 3133` output (state:
OPEN, additions 897/deletions 2, trailer `Advances #3120`) -- both read
in full before any check ran. Also read
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5507212053`
(the sequencing comment PR #3133's own record cites) -- confirms the
layer-1/2 vs. wake-notice vs. layer-3 file-ownership split independently
of PR #3133's own account of it.

PR #3133 was fetched as `refs/pull/3133/head` -> local ref
`pr-3133-review` (head `eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41`) and
checked out in a disposable `git worktree` at `/tmp/pr3133-worktree`,
removed at the end of this session (`git worktree remove --force`,
confirmed via `git worktree list` showing only this session's own
worktree afterward). All commands below ran against that worktree or
against further disposable clones made from it, never against this
session's own `issue-3120/adversarial-review+...` branch, which carries
none of PR #3133's commits, so every PR-#3133-only path named below
(the two new gate probes, the PR's own record file) is untracked on
this branch.

### Acceptance check 1 (layer 1) -- probe_heartbeat_rc95_is_classified.py (untracked on this branch, PR #3133 only)

acceptance: `bash -c "python3 gates/probe_heartbeat_rc95_is_classified.py"` in `pr3133-worktree` -- result:
```
ok
```
rc=0.

### Acceptance check 2 (layer 2) -- probe_heartbeat_survives_head_change.py (untracked on this branch, PR #3133 only)

acceptance: `bash -c "python3 gates/probe_heartbeat_survives_head_change.py"` in `pr3133-worktree` -- result:
```
ok
```
rc=0.

### Acceptance check 3 -- on-the-record/monitors/test_poll_heartbeat.py

acceptance: `bash -c "python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q"` in `pr3133-worktree` -- result:
```
46 passed in 24.24s
```
Matches the PR's own claimed count exactly.

### Acceptance check 4 -- tests/ -q

acceptance: `bash -c "python3 -m pytest tests/ -q"` in `pr3133-worktree` -- result:
```
254 passed, 2 warnings in 11.45s
```
Matches the PR's own claimed count exactly and the spawning brief's
stated main baseline (254).

### test/ -q (not in this issue's Acceptance list, reported separately per the spawning brief)

acceptance: `bash -c "python3 -m pytest test/ -q"` in `pr3133-worktree` -- result:
```
15 failed, 548 passed, 3 xfailed in 32.22s
```
derived: `python3 -m pytest test/ -q 2>&1 | grep -c ^FAILED` -- result:
`15`, confirming the count above rather than restating it. The failing
node IDs (`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) match the PR's own
claimed pre-existing-failure list. derived:
`grep -l -E "poll.heartbeat|watchdog" test/test_convention_equivalence.py test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_artifact_skill_pairing.py test/test_spawn_skill_judge_haiku_timeout_overlap.py`
-- result: no match, empty output -- none of the five failing files
import or reference `poll-heartbeat.sh`, `watchdog.py`, or `spawn.py`'s
watchdog role. Pre-existing, owned by #3091, unrelated to this diff --
confirmed, not merely cited.

### Consumer condition (the issue's own stated bar): real script, real HEAD move, no stub of the defect path

The two gate probes above (and the PR's own six new pytest cases) all
drive `watchdog_rc` via a **fake `spawn.py`** that hardcodes the exit
code -- they never exercise the real `watchdog_freshness_check` /
`git fetch` + `merge --ff-only` path that actually produces rc=95 in
production. This session built a second, independent, fully unstubbed
reproduction of exactly that path:

- `/tmp/otr-bare.git` -- a bare clone of the PR worktree (real spawn.py,
  watchdog.py, on-the-record/monitors/poll-heartbeat.sh, unmodified).
- `/tmp/otr-checkout-a` -- a real clone of the bare repo, used as
  `TOKENMAXXXER_CHECKOUT` (this is the "checkout the consumer is armed
  against").
- `/tmp/otr-checkout-b` -- a second real clone, used only to commit and
  `git push` a trivial file (`EXTERNAL_MARKER.txt`) to the bare origin,
  simulating an external merge landing while checkout-a's tick is in
  flight -- exactly the "git pull, marketplace update, or ordinary
  merge" scenario the issue names.
- `/tmp/consumer_arm_root2` -- an ordinary, non-git, non-plugin-dev
  directory, run as the working directory `cwd` for `poll-heartbeat.sh`
  (the "session doing NO plugin development" the issue's acceptance
  text requires).

With checkout-a still at the old commit and the new commit already
pushed to the bare origin, running the real, unmodified
`poll-heartbeat.sh` (`TOKENMAXXXER_CHECKOUT=/tmp/otr-checkout-a`,
`POLL_HEARTBEAT_MAX_TICKS=1`, `POLL_HEARTBEAT_SLEEP_SECONDS=0`, no other
overrides, no fake spawn.py) produced:

```
[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀌었다 (시작=eec9a051c8d9 현재=fe95fca963f0) — 재기동 필요
[watchdog-stale-code] watchdog exited rc=95 (checkout HEAD changed — restarting)
[poll-heartbeat] stale code (rc=95) -- restarting via exec /tmp/otr-checkout-a/on-the-record/monitors/poll-heartbeat.sh
```
rc=0 (clean exit, not 127 -- the exec succeeded). derived: `git -C
/tmp/otr-checkout-a log -1 --oneline` after the run showed the new
commit, not the old one -- checkout-a's HEAD had genuinely moved. The
real `watchdog_freshness_check`'s own internal `git fetch` + `merge
--ff-only` did the pull, not this session.

A second run with `POLL_HEARTBEAT_MAX_TICKS=5` against a fresh pair of
clones and a second pushed external commit produced the same
classification/exec sequence and then exited 0 after the full 5-tick
bound, proving the post-exec process image ran four more complete loop
iterations (not just "didn't crash once") before terminating on its own
bound -- sustained liveness, not a one-shot fluke.

This is the consumer condition from the issue's acceptance text
("a session doing no plugin development survives a HEAD change under
it"), reproduced against the real, unmodified script with a real git
remote and a real HEAD move -- Present, and more end-to-end than either
gate probe (which both fake `spawn.py`'s watchdog role entirely).

### Distinguishability of rc=95 from crash and from silence

Produced all three conditions directly (not read from code), same real
script, one fake `spawn.py` varying only `TRI_RC`:
```
=== rc=95 (stale-code) ===
[watchdog-stale-code] watchdog exited rc=95 (checkout HEAD changed — restarting)
=== rc=97 (crash) ===
[watchdog-crash] watchdog exited rc=97
=== rc=0 (silent/clean tick) ===
(no classification line)
```
derived: three separate real invocations of `bash
on-the-record/monitors/poll-heartbeat.sh` in `pr3133-worktree`, only
`TRI_RC` varied. Present -- rc=95 is tellable apart from both other
conditions.

### Attacking the exec guard: independent measurement, then an adversarial race

Reproduced the PR's own core measurement independently, from scratch,
with a plain bash one-liner (no reference to the PR's own test scripts):
```
$ bash -c 'echo "before-exec pid=$$"; exec bash /tmp/definitely-does-not-exist-xyz.sh; echo "UNREACHABLE-after-exec"'
before-exec pid=3725024
bash: /tmp/definitely-does-not-exist-xyz.sh: 그런 파일이나 디렉터리가 없습니다
outer rc=127
```
Confirms: exec into a momentarily-absent file kills the process at
rc=127, "UNREACHABLE-after-exec" never printed. Matches the PR's claim.

The guard shape under review, `on-the-record/monitors/poll-heartbeat.sh:595-598`
in `pr3133-worktree` (derived: `git show HEAD:on-the-record/monitors/poll-heartbeat.sh | sed -n '595,598p'`):
```
      _exec_target="${CHECKOUT}/on-the-record/monitors/poll-heartbeat.sh"
      if [ -f "${_exec_target}" ]; then
        printf '[poll-heartbeat] stale code (rc=95) -- restarting via exec %s\n' "${_exec_target}"
        exec bash "${_exec_target}"
```
is a check-then-act pair, not atomic -- the PR's own record already
names this as an accepted, un-eliminated residual (its own "Open
findings" item 2, untracked on this branch). This session built an
adversarial stress harness against the exact same two-line shape (a
background racer deleting/recreating the target file in a tight loop,
no sleep, while 20000 foreground attempts raced the check-then-exec
window). derived: `bash /tmp/toctou_race.sh` (script written and run
this session, not part of either the PR's or this session's deliverable,
a scratch reproduction) -- result:
```
done: attempts=20000 exec_fail_hits=2431
```
2431/20000 = 12.155% (computed directly from this run's own printed
numbers). **The race is real and reachable** under active contention,
not a theoretical concern. This corroborates, rather than contradicts,
what PR #3133's own record already discloses as an open,
accepted-not-eliminated risk -- it is not a new defect this session
found that the PR hid.

On whether this makes the failure mode strictly worse (the spawning
brief's framing: "a death that at least prints a line" vs. "a silent
disappearance"): when the race is hit, bash itself still emits `"그런
파일이나 디렉터리가 없습니다"` ("No such file or directory") to
**stderr** before the process dies at rc=127, visible in the same
capture shown just above (`bash: /tmp/definitely-does-not-exist-xyz.sh:
그런 파일이나 디렉터리가 없습니다`) -- the same stderr channel the
issue's own captured live example shows being surfaced (canonical: `gh
issue view 3120` output, the line `[exited with code 1]` immediately
following the freshness-check message in the issue's "Captured live"
block). So this is not literally silent: it is a visible process death
with an unstructured (not `[watchdog-*]`-tagged) error line, which is a
downgrade in *classification quality* relative to the crash/stale-code
labels this same PR adds, but the resulting state -- monitor dead, no
restart, needs external re-arm -- is the same operational state as the
original, unclassified rc=95 defect this issue reports, not a new or
worse one. The finding is real and worth carrying forward, not a false
alarm and not a regression beyond what's already disclosed.

### The undisclosed-vs-honestly-hedged claim: platform Monitor wrapper (pid vs. pipe)

canonical: PR #3133's own record (untracked on this branch, read on the
PR's branch via `git show pr-3133-review:docs/issue-3120/reports/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md`)
names this explicitly as an open finding, not an assumption: fd-sharing
observed by read-only `/proc` inspection of its own live Monitor
process, but no live restart tested against the real wrapper, because
that process is a "shared, hard-to-reverse resource."

This session independently corroborated the fd-sharing observation on a
different live process (this session's own Monitor-wrapped
`poll-heartbeat.sh`, pid 3387957, parent 3387955 -- a different pid pair
than the PR session inspected). derived: `ls -la /proc/3387955/fd
/proc/3387957/fd` (run this session) -- result: both processes' fd 1
and fd 2 resolve to the identical socket inodes (`socket:[1053022360]`,
`socket:[1053022362]`) -- the same fd-sharing shape, on an independent
process.

Judgment on whether the open finding was more closable with available,
no-risk means: yes, partially. Two additional facts follow from POSIX
`exec()` semantics without touching any live process: `exec()` preserves
both the pid **and** the process's `starttime` (a kernel-tracked
per-process, not per-image, value that most liveness-watchers that
distinguish "the same process" from "a pid-reused impostor" rely on) --
neither is measurable by fd-inspection alone, and PR #3133's record
doesn't cite this invariant, though it would have strengthened the
"likely fine" case for free. What genuinely remains unclosable without
touching a live, hard-to-reverse resource is whether the actual platform
supervisor tracks anything *beyond* pid/fds/starttime/cmdline -- e.g. a
proprietary handshake or session token established once at spawn time
outside the inherited fds -- and that is not discoverable from inside
this sandbox. derived: `find "$CLAUDE_PLUGIN_ROOT_CORE" -iname
"*monitor*"` -- result: no implementation files found; the Monitor tool
available to this session is this session's own background-task
watcher, unrelated to the harness-external supervisor that tracks
`poll-heartbeat.sh`'s liveness. This session made the same choice PR
#3133 made, for the same reason: declined to signal, kill, or exec its
own live Monitor process to test this end-to-end, since doing so risks
this session's own monitoring for a result reasoning already makes
likely. Verdict: the hedge is warranted for the genuinely unclosable
part, but the record could have gone one step further using a no-risk
argument (start-time invariance) before landing on "open finding."

unverifiable: whether the wrapper tracks something exec breaks is itself
the open question this whole section addresses -- this session did not
touch the live supervisor to find out, for the risk reasons stated
above, so what follows is a reasoned hypothetical consequence, not an
observed defect. canonical: `gh issue view 3120` output, quoted verbatim
below (the layer-3 paragraph, which is what names the only recovery
path this issue currently documents for a dead monitor of any cause):
```
Layer 3 — automatic re-arm, not an instruction. SIGKILL and unexpected
exits remain. Today the only recovery is a [orchestrate][MONITOR-DEAD]
line in the injected directive telling the orchestrator to re-arm by
hand.
```
IF the wrapper does track something exec breaks (unverified, per above),
two concrete failure shapes follow, depending on what the supervisor
does next: (a) the supervisor surfaces that same
`[orchestrate][MONITOR-DEAD]` notice -- the same manual-re-arm path
quoted above, which layer 3 exists to eliminate -- even though nothing
is actually dead; or (b) if the supervisor auto-restarts on perceived
death, a second `poll-heartbeat.sh` process gets spawned alongside the
(still-alive) exec'd one -- a duplicate-monitor condition, distinct from
the "two live loops" finding issue #3120's own Withdrawn section says
was a false positive from that investigation (a subshell cmdline
artifact) -- this would be a different, newly-hypothetical mechanism for
the same symptom, not a repeat of the withdrawn one. Neither (a) nor (b)
is confirmed to occur; both are conditional on the unverified premise
above.

### Must-not: freshness check not removed or weakened

derived: `gh pr diff 3133 --repo tokenmaxxxer/on-the-record --name-only`
-- result: files touched are two docs/issue-3120 record paths (one
deviation-log entry), one docs/reports/product/priorities entry (all
untracked on this branch, PR #3133 only), the two new gate probes
(untracked on this branch), `on-the-record/monitors/poll-heartbeat.sh`,
`on-the-record/monitors/poll_heartbeat_delta.py`, and
`on-the-record/monitors/test_poll_heartbeat.py`. `watchdog.py` and
`spawn.py` (where `watchdog_freshness_check` and
`WATCHDOG_STALE_CODE_SENTINEL` live) are absent from this list -- the
freshness check itself is untouched. Present.

### Other must-nots

Must-not 2 (no manual re-arm treated as recovery): PR #3133 implements
an automatic `exec` restart, not an instruction to a human/model to
re-arm -- Present, not violated. Must-not 3 (no cadence shortening or
more-aggressive re-arm as a substitute): derived: `gh pr diff 3133
--repo tokenmaxxxer/on-the-record | grep -n "sleep_seconds\|POLL_INTERVAL_SEC"`
-- result: no hits; neither the loop's sleep default nor
`POLL_INTERVAL_SEC` is touched. Present.

### Scope discipline: layers 3 and the wake-notice fix correctly excluded

derived: `gh pr diff 3133 --repo tokenmaxxxer/on-the-record --name-only
| grep directive.sh` -- result: no hits; `on-the-record/hooks/directive.sh`
is never opened for writing by this PR. Present, confirmed by this
session's own diff inspection, not by citing PR #3133's own account of
its scope. The PR's `Advances #3120` trailer (not `Closes`) is correct
given the sequencing comment `issuecomment-5507212053` (canonical: `gh
api repos/tokenmaxxxer/on-the-record/issues/comments/5507212053` output,
read in full above), which independently confirms PR #3132 owns
`probe_wake_notice_clears.py` and issue #3125 owns
`probe_dead_heartbeat_is_rearmed.py`.

## Why

Chose to build an independent, fully unstubbed reproduction of the
consumer condition (real git remote, real `watchdog_freshness_check`
fetch/merge, real exec) rather than trusting the two gate probes' own
fake-`spawn.py` doubles, because the spawning brief's own framing
("Do this against the real script, not a stub") reads as skepticism
specifically of test-double-only verification -- the probes prove the
*classification and exec-triggering logic* work given a rc=95 signal,
but not that the signal itself, and the surrounding real git plumbing,
actually produces rc=95 the way production does. Building a disposable
bare-repo + two-clone rig closes exactly that gap without touching any
shared resource.

Chose to stress-test the TOCTOU race adversarially (a tight
delete/recreate racer against 20000 attempts) rather than reasoning
about "how narrow is narrow" in the abstract, per the
defect-verification-independence-from-upstream-verdicts skill's
guidance to re-derive rather than accept a prior session's
characterization -- the PR's record calls it "a much narrower window"
without a number; this session's own number (12.155%, see "Attacking
the exec guard" above) is offered as a concrete, independently-derived
data point, not a refutation, since an adversarial racer with no sleep
is a much more hostile environment than two real marketplace updates
landing within the same tick.

Chose not to touch this session's own live Monitor-wrapped
`poll-heartbeat.sh` process to close the pid-vs-pipe question fully
end-to-end, matching PR #3133's own stated reasoning: it is this
session's own active infrastructure, and breaking it to answer a
question that reasoning already makes likely is a bad trade. Did the
next-safest thing available -- independently corroborating the
fd-sharing observation on a second, different live process, and adding
the start-time-invariance argument the PR's record didn't use -- rather
than either accepting the PR's single data point uncritically or
declining to add anything.

## What did not work

None.

## Upstream basis

Issue #3120 (canonical: `gh issue view 3120` output, read in full) and
PR #3133 (canonical: `gh pr view 3133` output, `gh pr diff 3133
--name-only`, and the PR's own record, untracked on this branch, read
via `git show pr-3133-review:docs/issue-3120/reports/silent-failure-audit+implementation-blueprint+test-derivation-30cf84d0.md`
as it exists on the PR's own branch, head
`eec9a051c8d9d4dc4c68ebcfa4a3bcc0f9a6fe41`) are the deliverables this
record verifies. Sequencing comment `issuecomment-5507212053` read
directly via `gh api` rather than trusting either record's paraphrase
of it.

## Open findings

1. **Exec-target TOCTOU race, independently corroborated at 12.155%
   under active contention** (derived: `bash /tmp/toctou_race.sh` --
   result: `2431/20000` = 12.155%, see "Attacking the exec guard"
   above). Not new -- PR #3133's own record, untracked on this branch,
   already discloses this as an accepted, un-eliminated residual (its
   own "Open findings" item 2). This session's contribution is an
   independent, adversarial measurement of how reachable it is under
   contention, confirming it is a real, non-theoretical window rather
   than validating the PR's own "narrow" characterization by re-reading
   the code. Not a blocker on this PR's own stated acceptance (the
   issue's `must-not`s and `check:`s do not require the race be
   eliminated, only that the freshness check isn't weakened and manual
   re-arm isn't treated as recovery, both of which hold per the
   "Must-not" sections above). Resolution path, if a live incident ever
   motivates it: the PR's own record already names one
   (copy-then-exec-the-copy) -- unchanged by this finding.
2. **Platform Monitor wrapper pid-vs-pipe tracking remains genuinely
   open**, for the reason both this session and PR #3133 independently
   arrived at (see "The undisclosed-vs-honestly-hedged claim" section
   above): closing it fully requires an end-to-end test against a live,
   hard-to-reverse Monitor process, which is not worth the risk given
   how strongly the available no-risk evidence (fd-sharing on two
   independent processes, plus pid/starttime/cmdline invariance under
   POSIX `exec()`) already points toward "fine." Not a blocker on this
   PR's acceptance; the PR's honesty in naming it as open rather than
   assumed is itself the correct behavior and is preserved here.
3. **Layer 3 (`probe_dead_heartbeat_is_rearmed.py`, issue #3125) and the
   wake-notice fix (`probe_wake_notice_clears.py`, PR #3132) remain
   outside this PR's scope**, confirmed by this session's own diff
   inspection above (see "Scope discipline"), not by citing PR #3133's
   own account of it -- tracked by their respective owners, not by this
   record.

## Next steps

None from this session. Acceptance checks 1 through 4 above (the two
gate probes this PR owns and the two pytest suites) and the must-not
sections above (freshness-check-intact, no-manual-rearm-as-recovery,
no-cadence-shortening) were all independently re-derived as Present;
`test/`'s 15 pre-existing failures were re-confirmed unrelated and
reported separately per the spawning brief. A PR is opened from this
branch per the build-now bypass; it references issue #3120 as a plain
`#3120` (this is a verification record about a sibling PR, not a
closing delivery for the issue itself).

skill-verdict: adversarial-review — applied: invoked; treated PR #3133
as an artifact to independently attack rather than trust, per the
"Attacking the exec guard" and "consumer condition" sections above --
rebuilt the consumer-condition reproduction from scratch against the
real script instead of accepting the gate probes' own fake-spawn.py
doubles, and stress-raced the exec guard adversarially instead of
reading the code and accepting the PR's "narrow window" characterization.
skill-verdict: silent-failure-audit — applied: invoked; classified the
TOCTOU-race death as a non-silent failure (bash's stderr line still
reaches the same channel the issue's own captured example used) rather
than accepting the spawning brief's "silent disappearance" framing at
face value -- verified the actual stderr content directly before
concluding.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every check above was re-derived from the real script/real git state rather than cited from PR #3133's own record or the gate probes' prior PASS results, including building two reproductions (consumer-condition end-to-end, and the TOCTOU stress harness) neither of which existed before this session and neither of which reuses the PR's own test-double fixtures.
other mounted skills: not triggered (work-in-english followed as house convention without a separate invoke; implementation-audit/conformance-review-finding-record/parallel-decomposition do not match a solo two-layer verification task with no fan-out and no separate conformance-review board).
