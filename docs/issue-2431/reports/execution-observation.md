---
issue: 2431
role: execution-observation
author: execution-observation
loop_state: cleared
upstream:
  - path: docs/issue-2431/reports/implementation.md (untracked on this
      branch — lives on branch issue-2431/implementation / PR #2434, read
      via `git show 6531f56f:docs/issue-2431/reports/implementation.md`)
    sha: 6531f56fde8d5ea9199819c4d6f97227232d405f
  - path: spawn.py (issue #2431 fix, untracked on this branch)
    sha: 6531f56fde8d5ea9199819c4d6f97227232d405f
  - path: roster.py (unchanged by this PR — `spawn_attempt_sweep()`, read
      to check the sweep/prune interaction the PR's own record claims)
    sha: 6531f56fde8d5ea9199819c4d6f97227232d405f
subject: PR #2434 (issue-2431/implementation, OPEN at observation time,
  HEAD `6531f56fde8d5ea9199819c4d6f97227232d405f`) — its five
  acceptance-criteria claims about `_prune_spawn_attempts()` dropping a
  confirmed-dead-pid, no-outcome record with no calendar bound at all,
  while leaving the `halted`-outcome branch's 7-day
  `SPAWN_ATTEMPTS_RETENTION_SEC` untouched
test: independent re-derivation from source in a separate `git worktree`
  (main at `5007bd23`, pre-fix baseline) plus the PR's own already-checked-
  out workspace (PR HEAD `6531f56f`) — the original 434/199-record real
  backlog no longer exists on this machine (already fully consumed by the
  implementation session's own live demo), so this session built a fresh,
  independently-authored backlog using genuinely real dead pids (actual
  `subprocess.Popen`/`.wait()` exits, real recent timestamps, not mocked
  ages) and ran the actual pre-fix and post-fix `_prune_spawn_attempts()`/
  `spawn_attempt_sweep()` code against it directly in isolated
  `MUSTER_STATE_ROOT` dirs, plus the PR's own pytest suite
result: failed
assertedBy: execution-observation session, issue-2431 (build-now delivery)
---

# issue-2431 — execution-observation record

## What was done

Independently verified PR #2434's five acceptance-criteria claims by
reading the actual `spawn.py`/`roster.py` source at the PR's HEAD
(`6531f56f`, in this session's own checked-out implementation workspace)
against a separate `git worktree` of `main` (`5007bd23`, fork point,
pre-fix), re-running the PR's test suite, and independently reproducing
its live before/after demonstration from scratch rather than replaying
its transcripts or reusing its numbers.

### Claim 1 — dead-pid, no-outcome records pruned without the 7-day wait

canonical: `6531f56f:spawn.py` `_prune_spawn_attempts()`'s outcome-is-
`None` branch, diffed word-for-word against `5007bd23:spawn.py` (main)
via `git diff 5007bd23 6531f56f -- spawn.py` (this session's own command,
run in the execution-observation worktree) — result:
```
-            ts = a.get("ts")
-            aged_out = (not isinstance(ts, (int, float))
-                        or now - ts >= SPAWN_ATTEMPTS_RETENTION_SEC)
-            if _pid_is_alive(pid) or not aged_out:
+            if _pid_is_alive(pid):
                 keep_ids.add(aid)
```
The old branch kept a record if `_pid_is_alive(pid) or not aged_out`
(7-day age check as a fallback); the new branch keeps it iff
`_pid_is_alive(pid)` — no age check at all once liveness is confirmed
negative, confirmed by this diff. canonical: this session's own diff
transcript above.

### Claim 2 — reasoning stated for the shorter bound

canonical: `6531f56f:spawn.py` inline comment above the branch (read
directly in the implementation workspace), and PR #2434's commit messages
(`278c0d7c`, `791856c7`, read via `git log` in that same workspace).
States: an alive pid is kept at any age (unchanged); a confirmed-dead pid
gets no calendar wait at all once liveness is confirmed negative, because
`_pid_is_alive()` returning `False` is already a final answer — nothing
is learned by waiting longer, per operator guidance on the issue
(`issuecomment-5411038089`). The only case meant to carry a time bound is
`_pid_is_alive()`'s own ambiguous-`OSError` path, already handled
conservatively (treated as alive) inside that helper. The reasoning is
present in source, not just in the PR description, and matches the
mid-flight operator comment it cites. canonical: this session's own
execution transcript (`git log` output, this turn) and commit-pinned read
at `6531f56f:spawn.py`'s comment block.

### Claim 3 — live demonstration against the real backlog

The original `runs/spawn-attempts.jsonl` this issue and PR #2434 cite
(434, then 199, real orphans) no longer exists anywhere on this machine —
checked every sibling workspace under `~/.tokenmaxxxer/work/` and the
implementation session's own workspace.

acceptance: `wc -l ~/.tokenmaxxxer/work/on-the-record-issue-2431-implementation/runs/spawn-attempts.jsonl` — result:
```
wc: .../runs/spawn-attempts.jsonl: No such file or directory
```
consistent with the PR's own claim of driving it to 0 and idempotent
thereafter (this session did not stop at that consistency check — see
below).

Rather than trust that number secondhand, this session built an
independently-authored backlog of genuinely real dead pids — not mocked
ages — by actually spawning and waiting on 20 real subprocesses, plus one
real still-alive `sleep 60`, plus a recent and an 8-day-old
`halted`-outcome record.

acceptance: `python3 gen_backlog.py` (this session's own script,
`subprocess.Popen(["true"]).wait()` x20 for real dead pids, one real
`sleep 60` left running, `time.time()` for real "just now" timestamps) —
result:
```
generated {'n_dead': 20, 'alive_pid': <real pid>, 'n_records': 25}
alive pid still running: True
```

acceptance: the identical 25-line file, copied into two isolated
`MUSTER_STATE_ROOT` dirs, run through the real `_prune_spawn_attempts()`
— once against `main` (`5007bd23`, `/tmp/otr-2431-main` worktree), once
against PR HEAD (`6531f56f`, implementation workspace) — result:
```
# main (before):
BEFORE (main branch): dropped = 2      # only the 8-day-old halted record
remaining: 23                          # 20 dead-pid orphans all survived

# PR HEAD (after), same 25-line source file, fresh copy:
AFTER (PR branch), pass 1: dropped = 22   # 20 dead-pid orphans + 2 old-halted lines
remaining: 3                              # alive pid + recent halted (2 lines)
```
canonical: this session's own execution transcript above — 20 of 20 real
dead-pid orphans dropped in one pass on PR HEAD; 0 of 20 dropped on
`main` under the identical input, reproducing the issue's own "0
dropped" finding on this session's own independently-built real-pid
fixture rather than the PR's stale count.

acceptance: a second `_prune_spawn_attempts()` pass on the PR-HEAD state,
run later in the same session after real wall-clock time had elapsed —
result:
```
AFTER (PR branch), pass 2 (idempotency check): dropped = 1
```
canonical: this session's own execution transcript above — idempotent
for the orphans already gone (no re-drop), and the one further line
dropped is the previously-alive `sleep 60` record, which had genuinely
exited between passes (checked separately via `ps -p <pid>`, which
returned no such process at pass-2 time, canonical: this session's own
`ps` transcript) — the liveness gate tracked a real alive-to-dead
transition correctly across two real points in time, not a static
snapshot.

### Claim 4 — watchdog stops re-emitting within one tick, demonstrated

acceptance: a single real dead pid, freshly recorded (`ts` a fraction of
a second old, well under `roster.SPAWN_ATTEMPT_GRACE_SEC` = 300s), run
through `roster.spawn_attempt_sweep()` (the actual watchdog-tick entry
point, not `_prune_spawn_attempts()` directly) on PR HEAD — result:
```
sweep report count (tick 1, record is seconds old): 0
remaining after sweep: 0
```
canonical: this session's own execution transcript above — the record is
gone after exactly one tick and produces zero further report lines on
any later tick (nothing remains to re-emit); the literal claim ("stops
re-emitting within one tick, not within a week") holds on this
reproduction.

This same reproduction also surfaced a gap the PR's own record does not
mention and did not test — see "Open findings" below: the record
disappeared with zero reports ever having fired for it, which contradicts
the PR's own commit-message claim that `spawn_attempt_sweep()` "still
gets a report chance for free."

acceptance: the identical scenario (single real dead pid, `ts` a fraction
of a second old) run through `roster.spawn_attempt_sweep()` on `main`
(`5007bd23`) for contrast — result:
```
sweep report count (tick 1, main branch, record is seconds old): 0
remaining after sweep (main branch): 1
```
canonical: this session's own execution transcript above — on `main` the
record survives the first tick (report count also 0, but the line stays
on disk, eligible for a future tick's report once
`SPAWN_ATTEMPT_GRACE_SEC` elapses); on PR HEAD it is already gone under
the same input. The difference is the finding in the next section.

### Claim 5 — the `halted`-outcome branch's 7-day retention is untouched

acceptance: `git diff 5007bd23 6531f56f -- spawn.py | grep -A5 'halted'`
(this session's own command) — result:
```
         elif outcome.get("outcome") == "halted":
             outcome_ts = outcome.get("ts", now)
             if not isinstance(outcome_ts, (int, float)) or \
```
canonical: this session's own diff transcript above — zero `+`/`-` lines
appear inside the `elif outcome.get("outcome") == "halted":` block; the
entire change is confined to the sibling outcome-is-`None` branch and its
comment. The same before/after run quoted under Claim 3 backs this up
behaviorally (derived: transcript under Claim 3): the recent `halted`
record (well inside the 7-day window) survived on both `main` and PR
HEAD; the 8-day-old `halted` record was dropped on both `main` and PR
HEAD identically (2 lines each) — same behavior, not just same source
text.

### Test suite

acceptance: `python3 -m pytest tests/test_watch_hardening.py tests/test_spawn_pipeline.py -q -n0` (implementation workspace, PR HEAD) — result:
```
124 passed in 4.11s
```
canonical: this session's own execution transcript above — matches PR
#2434's own record's count.

acceptance: `git diff 5007bd23 6531f56f -- tests/test_watch_hardening.py`
(this session's own command) — result: the diff shows the four
new/rewritten cases
(`test_dead_pid_pruned_immediately_even_when_ts_is_fresh`,
`test_dead_pid_pruned_regardless_of_old_retention_window`,
`test_halted_branch_retention_is_unchanged`, plus the missing-`ts`
rewrite) all calling `spawn._prune_spawn_attempts()` directly — none
calls `roster.spawn_attempt_sweep()`. canonical: this session's own diff
transcript, this command, confirming the sweep/prune interaction
exercised for Claim 4 above is genuinely untested by this PR.

## Why

canonical: this session's own worktree reads and command transcripts
quoted under "What was done" above (`/tmp/otr-2431-main` at `5007bd23`,
the implementation workspace at `6531f56f`) are the basis for every claim
in this section.

Re-derived from source rather than trusting PR #2434's own transcripts,
per this role's purpose (cf. `docs/issue-2413/reports/
execution-observation.md`'s precedent for the same fix's first, wrong-
bound round). Because the exact real backlog the PR's own live demo used
is already gone, replaying its printed numbers would only be trusting its
transcript a second time; building a fresh, independently-authored
real-pid fixture and running the actual pre-fix and post-fix code against
it directly closes that same trust gap instead.

The report/prune-interaction finding came from asking the adversarial
question this role exists to ask about Claim 4 specifically: the PR's own
commit message asserts `spawn_attempt_sweep()` "still gets a report
chance for free" — that is a falsifiable claim about *ordering* within one
call, not just about the prune outcome, and it was not exercised by any
new test (all new tests call `_prune_spawn_attempts()` directly, never
`spawn_attempt_sweep()`, derived: diff transcript under "Test suite"
above). Testing it directly, with a record fresher than
`SPAWN_ATTEMPT_GRACE_SEC` (300s) — the realistic case, since the issue's
own filing describes the real orphans as dying "within seconds" of the
spawn attempt being recorded — surfaced that the claim does not hold for
exactly that realistic case: report happens before prune in *source
order* within the function, but the report step's own age gate (`now -
ts < SPAWN_ATTEMPT_GRACE_SEC: continue`) skips reporting for a record
that fresh, and prune then removes it unconditionally at the end of the
same call — so it is never reported at all, not "reported once, then
pruned" (derived: transcripts under Claim 4 above).

This does not reopen the fix's core approach — liveness-gated, no-bound
pruning for the confirmed-dead-and-orphaned case is exactly what the
issue and operator guidance ask for, and Claims 1, 2, 3, and 5 all hold
(derived: sections above) — the finding is narrower: the PR's stated
justification for why this change is safe with respect to the
pre-existing `spawn_attempt_sweep()` visibility mechanism (issue #2291)
does not hold for the majority shape of the real backlog this issue
itself describes, and nothing in the current test suite catches that.

## Upstream basis

- `docs/issue-2431/reports/implementation.md` (untracked on this branch —
  PR #2434 / branch issue-2431/implementation, sha `6531f56f`) — PR
  #2434's own record, whose five claims this observation checks against
  source and live reproduction rather than restates.
- `spawn.py`, `tests/test_watch_hardening.py` at PR #2434 HEAD
  (`6531f56fde8d5ea9199819c4d6f97227232d405f`) — read and executed
  directly in the already-checked-out implementation workspace, not from
  the PR's own quoted excerpts.
- `spawn.py`, `roster.py` at `5007bd23` (this branch's own `main` fork
  point, pre-fix) — read and executed directly in a separate `git
  worktree` (`/tmp/otr-2431-main`) to produce the before/after comparison
  independently rather than trust the PR's own before-state description.
- `roster.py`'s `spawn_attempt_sweep()` (unchanged by this PR) — read and
  executed directly (not just cited) to check the report/prune-ordering
  claim in PR #2434's commit message.
- Issue #2431 itself — the five acceptance checks this record addresses
  one by one, and both operator comments quoted in the PR's own commit
  messages (`issuecomment-5410865516` and `issuecomment-5411038089`, read
  via `gh issue view 2431 --comments`, this session's own command).

## Open findings

1. `spawn_attempt_sweep()`'s "report chance for free" claim (`roster.py`,
   and PR #2434's commit message `791856c7`/code comment, canonical:
   commit-pinned read at `6531f56f:roster.py:435-511` and the commit
   message text, this session's own read) does not hold for a dead-pid,
   no-outcome record younger than `roster.SPAWN_ATTEMPT_GRACE_SEC` (300s)
   at the time of its first watchdog tick — which is the realistic case
   for this issue's own backlog (filed as dying "within seconds" of the
   spawn attempt being recorded, and `DEADMAN_INTERVAL_SEC` defaults to
   120s, so most real orphans will be first swept well inside the 300s
   grace window, canonical: commit-pinned read at `6531f56f:spawn.py:1138`,
   `os.environ.get("OTR_DEADMAN_INTERVAL_SEC", "120")`). For that case,
   `_prune_spawn_attempts()` (now called unconditionally at the end of
   the same `spawn_attempt_sweep()` call, with no age check) removes the
   record before the report step's own age gate ever opens for it — the
   record is silently dropped with zero "no outcome recorded" reports
   ever having fired, reproducing the specific pre-workspace-crash
   visibility gap issue #2291 built this whole mechanism to close.
   canonical: this session's own execution transcript under "Claim 4"
   above (PR HEAD: report count 0, 0 remaining after one tick; `main`,
   same input: report count 0, 1 remaining, eligible for a future tick's
   report). Not covered by any of the new or rewritten tests in
   `tests/test_watch_hardening.py` — all of them call
   `spawn._prune_spawn_attempts()` directly, none call
   `roster.spawn_attempt_sweep()` (derived: `git diff 5007bd23 6531f56f
   -- tests/test_watch_hardening.py`, read under "Test suite" above).
   Resolution path: either accept the traded-off loss of this specific
   visibility (the operator's mid-flight guidance is unambiguous that a
   confirmed-dead pid needs no grace at all, and this may be an
   intentional, acceptable trade — the human's call, not this
   observation's), or give `spawn_attempt_sweep()` a one-tick deferral
   for a dead-pid record it hasn't yet had a chance to report (e.g. skip
   pruning a record on the same tick it would first become reportable,
   mirroring the "report before prune" intent the PR's own text already
   claims), plus a test that actually calls
   `roster.spawn_attempt_sweep()` (not just `_prune_spawn_attempts()`)
   with a record fresher than `SPAWN_ATTEMPT_GRACE_SEC`.

## Next steps

None from this record's own scope — `loop_state: cleared`, matching
`docs/issue-2413/reports/execution-observation.md`'s precedent for this
record kind (no repo-defined terminal-state override exists for
`execution-observation` records). The five acceptance-claim checks, the
test-suite run, and the report/prune-interaction reproduction quoted
above under "What was done" cover the full scope this record set out to
check. Whether open finding 1 blocks landing PR #2434, is accepted as a
deliberate trade-off already implied by the operator's mid-flight
guidance, or is filed as a fast follow-up is the human's call, not this
observation's to decide.
