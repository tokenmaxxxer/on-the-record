---
issue: 2413
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: spawn.py (issue #2393 pytest-origin guard + prune)
    sha: 92de58089f21abc7ee95abb53ef94f07335d22ca
code_under_review:
  - path: spawn.py
    sha: same-commit
  - path: roster.py
    sha: same-commit
  - path: tests/test_watch_hardening.py
    sha: same-commit
type: fix
breaking: "no — advisory-only watch-layer behavior change; no public API, CLI flag, or on-disk schema changed. Effect is strictly narrower retention of an internal jsonl trace and fewer duplicate print lines."
verdict: pass
---

# issue-2413 — implementation record

## What was done

canonical: python3 -m pytest tests/test_watch_hardening.py -v and direct
python3 -c "..." invocations of spawn._prune_spawn_attempts() /
roster.spawn_attempt_sweep() run in this session — full transcripts
quoted in the fenced blocks below.

Fixed the two mechanisms named in the issue:

1. **Unbounded retention of unresolved spawn-attempt records**
   (`spawn.py`). `_prune_spawn_attempts()`'s `outcome is None` branch
   kept every attempt with no recorded outcome forever. Added a liveness
   probe `_pid_is_alive(pid)` (cheap on-demand `os.kill(pid, 0)`, called
   only during the prune pass — no polling) and changed the branch's
   rule to: **keep if the pid is still alive (regardless of age), or if
   the record is younger than `SPAWN_ATTEMPTS_RETENTION_SEC`** (the same
   7-day constant the adjacent `halted` branch already uses — no new
   knob). Drop otherwise.

2. **No per-tick dedupe in the watchdog emit loop** (`roster.py`,
   `spawn_attempt_sweep()`). The existing dedup gate
   (`ledger_check_and_stamp(f"spawn-attempt-halt:{attempt_id}")`) is
   keyed by `attempt_id`, not by subject — so many different attempt_ids
   naming the same `(issue, role)` each independently pass the gate and
   each print a line in the same tick. Added an in-memory
   `reported_subjects` set scoped to one `spawn_attempt_sweep()` call:
   after the first line for a subject prints in a tick, later
   attempt_ids for that same subject are skipped for the rest of that
   tick. The per-attempt_id ledger gate is left in place unchanged
   (still governs cross-tick re-surfacing cadence).

3. Added test coverage in `tests/test_watch_hardening.py` (the existing
   home for issue #2101/#2291-class watch-layer mechanism tests): a
   `SpawnAttemptPruneLiveness` class covering — live pid survives past
   retention, dead pid within retention is kept, dead pid past retention
   is pruned, and `_pid_is_alive` unit behavior directly — plus a
   `SpawnAttemptSweepDedup` class covering many attempt_ids for one
   subject collapsing to a single printed line per tick. Real pytest
   transcript:

```
$ python3 -m pytest tests/test_watch_hardening.py -v
...
tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_live_pid_survives_regardless_of_age PASSED
tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_dead_pid_within_retention_is_kept PASSED
tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_dead_pid_past_retention_is_pruned PASSED
tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_pid_is_alive_helper PASSED
tests/test_watch_hardening.py::SpawnAttemptSweepDedup::test_many_attempt_ids_same_subject_prints_once_per_tick PASSED
============================== 31 passed in 4.84s ===============================
```
31 = the pre-existing suite (26, unchanged, still green) plus the new
`SpawnAttemptPruneLiveness`/`SpawnAttemptSweepDedup` classes added by
this change. Also re-ran the broader spawn suite for collateral-damage
coverage:

```
$ python3 -m pytest tests/test_spawn_pipeline.py tests/test_standing_red_watch.py
============================== 97 passed in 45.31s ==============================
```

### Live-in-flight demonstration (real process, real pid)

canonical: python3 -c "..." invocation of spawn._prune_spawn_attempts()
against the live sleep-120 pid and a confirmed-dead pid, run in this
session — output quoted verbatim in the fence below.

Spawned a real `sleep 120` background process, hand-wrote a
`spawn-attempts.jsonl` record naming its real pid with a fresh timestamp
and no outcome, ran the fixed `_prune_spawn_attempts()` directly against
it alongside a synthetic dead-pid/8-day-old record:

```
$ ps -p $REAL_PID -o pid,cmd
    PID CMD
3772285 sleep 120
$ python3 -c "... spawn._prune_spawn_attempts() ..."
dropped: 1
--- remaining ---
{"event": "spawn_attempt", "attempt_id": "999:implementation:3772285:1787659457099", "issue": 999, "role": "implementation", "pid": 3772285, "ts": 1787659457.0992565}
```

The live pid's record survived; the dead/aged record (pid 3783134,
verified dead by forking and reaping the child, timestamped eight days
old) was the single line the same run dropped.

### Before/after measurement

canonical: python3 -c "..." invocations of the actual
_prune_spawn_attempts()/spawn_attempt_sweep() code, once with this
change stashed out (git stash) and once with it applied, run in this
session against a synthetic reproduction — full transcripts quoted
below.

`runs/spawn-attempts.jsonl` (gitignored — see `.gitignore` line 1) did
not exist in this worktree: this is a fresh per-issue checkout with no
live muster daemon ever having spawned through it, so the filing-time
counts could not be re-measured directly here. Built a same-shape
synthetic reproduction instead — total 431 lines: 305 `spawn_attempt`
records for issue 31 and 114 for issue 7 (all dead-pid, ten-days-old,
no-outcome — the exact shape the issue describes as pre-#2393-guard
fixture orphans), plus seven "real" records: two genuinely in-flight
(live pids, fresh timestamps), three recently `halted`, and two
`session-log`-succeeded. Ran the actual `_prune_spawn_attempts()` and
`spawn_attempt_sweep()` code paths against a copy of it, once on the
pre-fix code (`git stash` of this same diff) and once on the fixed code.
Real terminal transcripts:

```
$ python3 -c "... UNFIXED spawn_attempt_sweep(d_all={}) on the 431-line file ..."
watchdog lines emitted in tick 1 (UNFIXED code): 422
spawn_attempt_sweep() count return value: 422
per-subject line counts (top 5): [('issue-31/implementation', 305), ('issue-7/implementation', 114), ('issue-2410/implementation', 1), ('issue-2411/implementation', 1), ('issue-2412/implementation', 1)]
lines remaining in file after unfixed prune: 427
```

```
$ python3 -c "... FIXED spawn_attempt_sweep(d_all={}) on a fresh copy of the same 431-line file ..."
=== FIXED CODE: watchdog tick 1 ===
  [spawn-attempt] issue-2410/implementation: spawn halted pre-workspace: network fetch failed
  [spawn-attempt] issue-2411/implementation: spawn halted pre-workspace: network fetch failed
  [spawn-attempt] issue-2412/implementation: spawn halted pre-workspace: network fetch failed
  [spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 864080s after spawn attempt (pid 3892806) — process likely died before it could report why
  [spawn-attempt] issue-7/implementation: spawn halted pre-workspace: no outcome recorded 864069s after spawn attempt (pid 3892806) — process likely died before it could report why
watchdog lines emitted tick 1 (FIXED): 5 count= 5

lines remaining in file after FIXED prune: 8
per-issue spawn_attempt records remaining:
  issue 2400: 1
  issue 2401: 1
  issue 2410: 1
  issue 2411: 1
  issue 2412: 1

=== FIXED CODE: watchdog tick 2 (same tick cadence) ===
watchdog lines emitted tick 2 (FIXED): 0 count= 0
```

Reading straight off those two transcripts: total file lines went from
431 to 427 under the unfixed prune (only the two `session-log` pairs
ever got dropped there, matching the pre-existing behavior for that
branch) versus 431 down to 8 under the fixed prune in one run; issue-31's
and issue-7's `spawn_attempt` records went from 305 and 114 respectively
down to zero each; and the watchdog's per-tick line count for that one
notification went from 422 down to 5, with the second tick already at
zero either way (ledger dedup on the surviving subjects is unchanged).
The two genuinely in-flight records (fresh timestamps, live pids) never
printed in either tick — correctly still inside
`SPAWN_ATTEMPT_GRACE_SEC` — and their file records survived the prune,
accounting for the `issue 2400: 1` / `issue 2401: 1` lines in the
post-fix breakdown above.

## Why

canonical: python3 -c "..." transcripts quoted under "What was done"
above are this session's own live runs of the exact functions this
section reasons about.

**Liveness test**: `os.kill(pid, 0)` — the standard zero-cost/zero-side-
-effect way to probe whether a pid is live without actually signaling
it. Only a clean `ProcessLookupError` (no such process) is treated as
"dead"; `PermissionError` (pid exists, owned by another user) and any
other `OSError` are treated as "alive" — an inconclusive check must
never cause a live spawn to be pruned out from under it, per the
operator constraint. Run only inside `_prune_spawn_attempts()`'s
existing once-per-tick pass (itself only invoked from
`spawn_attempt_sweep()`, already once per watchdog tick) — no new
polling loop, no added steady-state cost.

**Age bound**: reused `SPAWN_ATTEMPTS_RETENTION_SEC` (seven days) rather
than adding a new constant. The `halted` branch already uses this exact
window as "how long a reported halt keeps re-surfacing before its trace
is dropped"; treating an unresolved (`outcome is None`) record
symmetrically — "how long an unreported halt gets to keep being a
candidate for `spawn_attempt_sweep()` to report, before its trace is
dropped" — reuses the idiom the file's own comments already draw a
halted/unresolved parallel around, instead of a second TTL knob that
would need its own justification and its own drift risk against the
first.

**Boolean chosen**: `keep = pid_is_alive OR NOT aged_out` (equivalently:
`prune = NOT pid_is_alive AND aged_out`). Two things have to hold
simultaneously to justify deletion — confirmed dead, and old enough
that `spawn_attempt_sweep()` already had a full retention window's
worth of ticks to report it (it becomes reportable after
`SPAWN_ATTEMPT_GRACE_SEC`, much shorter than the seven-day retention, so
this is not a race — by the time an entry ages out under the new rule
it has had days of reportable ticks, not a narrow window). A pid that's
alive is never pruned, at any age — the hard requirement ("must never
be pruned out from under a running spawn") dominates the age check
unconditionally. A pid that's dead but young is kept so a fast crash
(e.g. killed within seconds of forking) isn't erased before
`SPAWN_ATTEMPT_GRACE_SEC` even lets `spawn_attempt_sweep()` consider
reporting it once, let alone the full retention window of re-report
visibility the `halted` branch's own reported entries get.

**Watchdog dedupe key**: chose subject (`lease_key(issue, role)`) over
attempt_id for the per-tick collapse, because the existing
per-attempt_id ledger gate was never the thing producing duplicate
lines in a single notification — each attempt_id is only ever iterated
once per tick (it's a dict key), so there was never a same-attempt_id
repeat within one tick. The actual flood was distinct attempt_ids
sharing one subject, each independently novel to the ledger and
therefore each admitted. Deduping by subject directly targets that: at
most one printed line per `(issue, role)` per tick, while leaving the
attempt_id-keyed cross-tick re-surfacing cadence
(`ledger_check_and_stamp`'s own TTL) untouched.

## What did not work

canonical: this session's own before-landing warrant-hunter dispatch
(stance 0, "assume the gate just touched is bypassable") and the
follow-up python3 -c "..." reproduction and pytest run, both executed in
this session — transcripts quoted verbatim below.

Initial `_pid_is_alive(pid)` guarded liveness with `isinstance(pid, int)`
and returned `False` (dead) for anything else with no OS probe. The
warrant-hunter reproduced a bypass: a `pid` field serialized as a numeric
string (plausible after ledger corruption/hand-repair — this repo has a
real precedent, commit cea0f583 "root-cause implementation.json
corruption") was treated as certainly dead even though the identical pid,
checked as an `int`, was genuinely alive:

```
$ python3 -c "... _pid_is_alive(str(mypid)) vs _pid_is_alive(mypid), then _prune_spawn_attempts() on a str-pid record aged past retention ..."
_pid_is_alive(str pid): False
_pid_is_alive(int pid): True
dropped: 1
remaining ids: set()
```

`_prune_spawn_attempts()` deleted the genuinely-alive record solely
because its `pid` was a string, violating the "never prune a live
in-flight attempt" invariant. Fixed by coercing digit-only string `pid`
values to `int` before the liveness check (spawn.py `_pid_is_alive`,
~10 lines added to the docstring/coercion branch). Added
`test_string_encoded_live_pid_survives_past_retention` and a
`str(os.getpid())` assertion in `test_pid_is_alive_helper` to
`tests/test_watch_hardening.py`; full suite re-run green after the fix:

```
$ python3 -m pytest tests/test_watch_hardening.py -v
...
============================== 32 passed in 0.94s ==============================
```

## Upstream basis

canonical: git log / git show on this worktree's own history, read this
session.

- Issue #2393 / PR #2400 (commit `92de58089f21abc7ee95abb53ef94f07335d22ca`,
  "issue-2393: skip pytest-origin spawn-attempt records, rotate + prune
  the trace") — introduced `_prune_spawn_attempts()`, its `halted`-branch
  `SPAWN_ATTEMPTS_RETENTION_SEC` idiom, and the `PYTEST_CURRENT_TEST`
  origin guard on `_record_spawn_attempt()` that stopped new fixture
  pollution but left the unbounded `outcome is None` branch and the
  pre-existing orphan backlog untouched.
- Issue #2291 (`spawn.py` around the spawn-attempt trace block,
  `roster.py`'s `spawn_attempt_sweep()`) — the durable pre-workspace
  bootstrap-halt trace mechanism this fix must keep intact:
  `SPAWN_ATTEMPT_GRACE_SEC`, the halted/unresolved reporting split, and
  the `ledger_check_and_stamp` cross-tick dedup this change layers a
  same-tick subject dedup on top of without altering.

## Open findings

None. Resolution path: not applicable — no open findings to resolve.

## Next steps

None remain for this fix — implementation, the live-pid demonstration,
the before/after measurement, the before-landing warrant-hunter dispatch
and its follow-up fix, and the test runs are all finished.
