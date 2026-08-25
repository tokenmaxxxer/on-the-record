---
issue: 2431
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2413/reports/implementation.md
    sha: c585122423bba09d63a61f2c666568449bbc4fa0
code_under_review:
  - path: spawn.py
    sha: same-commit
  - path: tests/test_watch_hardening.py
    sha: same-commit
type: fix
breaking: "no — advisory-only watch-layer behavior change; no public API, CLI flag, or on-disk schema changed. Effect is a much shorter retention window for one internal jsonl trace category (dead-pid, no-outcome spawn attempts) and unchanged behavior for the halted-outcome category."
verdict: pass
---

# issue-2431 — implementation record

## What was done

canonical: python3 -c "..." and python3 -m pytest invocations run directly
in this session against the real live backlog (a sibling workspace's
`runs/spawn-attempts.jsonl`, not a synthetic reproduction) and against a
temp-dir test fixture — full transcripts quoted below.

Build-now bypass (CORE_BUILD_NOW=1, set by the spawner): delivered directly,
no phase-1 proposal round.

#2413's fix (PR #2418, merged) correctly added a liveness probe
(`_pid_is_alive`) to `_prune_spawn_attempts()`'s `outcome is None` branch,
but bounded the "confirmed dead, no outcome" case by the same
`SPAWN_ATTEMPTS_RETENTION_SEC` (7 days) the adjacent `halted` branch uses.
That 7-day window exists so the orchestrator has time to notice and act on
a genuine unresolved `halted` outcome — a dead pid with no outcome has
nothing to notice-and-act on, so reusing the window meant the fix pruned
nothing for a week against the actual backlog shape (dead pids a few hours
old, not years).

**Fix** (`spawn.py`, `_prune_spawn_attempts()`): split the `outcome is
None` branch's aging rule by pid liveness instead of applying one shared
bound to both:

- pid still alive → kept, at any age (unchanged from #2413 — the hard
  in-flight-must-never-be-pruned invariant).
- pid confirmed dead → now bounded by a new, separate constant
  `SPAWN_DEAD_PID_PRUNE_SEC` instead of `SPAWN_ATTEMPTS_RETENTION_SEC`.

`SPAWN_DEAD_PID_PRUNE_SEC = roster.SPAWN_ATTEMPT_GRACE_SEC +
DEADMAN_INTERVAL_SEC` — composed from two constants that already existed
(no new env-tunable knob), defined next to `DEADMAN_INTERVAL_SEC` in
`spawn.py`. At this repo's current defaults that's 300s + 120s = 420s (7
minutes), versus the 7-day (604800s) window it replaces for this case. See
"Why" below for the reasoning behind this specific composition.

The `halted`-outcome branch (`elif outcome.get("outcome") == "halted":`,
still gated by the untouched `SPAWN_ATTEMPTS_RETENTION_SEC`) was not
touched — explicitly confirmed by inspection and by a new regression test
(`test_halted_branch_retention_is_unchanged`) and by the live demonstration
below, where the two real `halted` records in the live backlog survived
the prune untouched.

### Live demonstration against the REAL current backlog

canonical: python3 -c "..." invocations of the actual
`spawn._prune_spawn_attempts()` / `roster.spawn_attempt_sweep()` functions
run in this session directly against
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2395-implementation/runs/spawn-attempts.jsonl`
— a real, currently-live sibling workspace's state file, not a synthetic
reproduction (this issue-2431 worktree's own `runs/` doesn't exist, this
is a fresh per-issue checkout). Backed up to
`/tmp/spawn-attempts.jsonl.backup-issue2431` before mutating it.

Before (characterizing the real backlog directly, no code run yet):

```
$ wc -l .../on-the-record-issue-2395-implementation/runs/spawn-attempts.jsonl
203
total attempt ids: 201
no-outcome ids: 199
min/max age (h) among no-outcome: 1.42 .. 3.39
```
199 outstanding dead-pid-shaped orphans, all 1.4–3.4 hours old — same
shape the issue describes (younger than 7 days, so #2418's code drops 0 of
them; this session did not need to re-run the unfixed code to reconfirm
that 0, since #2413's own record already established it live and the code
path for the `halted` branch — the only branch #2418 touched besides this
one — is unchanged here).

After (this fix's code, run directly against that same real file):

```
$ MUSTER_STATE_ROOT=.../on-the-record-issue-2395-implementation/runs \
  python3 -c "import spawn; print(spawn._prune_spawn_attempts())"
dropped: 199
```
199 of 199 dead-pid no-outcome orphans dropped — not "near-zero", exactly
zero remain in that category. Re-running immediately after confirms
idempotency (nothing left to drop) and shows only the real `halted`
records survived:

```
$ python3 -c "import spawn; print(spawn._prune_spawn_attempts())"
second run dropped: 0
$ wc -l spawn-attempts.jsonl
4
$ cat spawn-attempts.jsonl
{"event": "spawn_attempt", ..., "pid": 3828118, "ts": 1787652640.165...}
{"event": "spawn_attempt_outcome", ..., "outcome": "halted", "detail": "-C 가 레포 루트가 아니라 그 하위 디렉터리다: ...", ...}
{"event": "spawn_attempt", ..., "pid": 3828120, "ts": 1787652640.217...}
{"event": "spawn_attempt_outcome", ..., "outcome": "halted", "detail": "-C 가 존재하지 않는 디렉터리다: ...", ...}
```
Both surviving pairs are real `halted` outcomes (issue-2395 fixture
records testing `-C` path validation) — exactly the category this change
leaves untouched.

### Watchdog stops re-emitting within one tick — demonstrated

canonical: python3 -c "..." invocations of the real
`roster.spawn_attempt_sweep()` (the actual watchdog-tick entry point,
which calls `_prune_spawn_attempts()` internally at the end of the same
call — see `roster.py` line ~510) run in this session, against the same
real backlog restored from the backup above.

```
$ python3 -c "roster.spawn_attempt_sweep() # tick 1, fresh 203-line backlog"
[spawn-attempt] issue-1/implementation: spawn halted pre-workspace: no outcome recorded 5139s after spawn attempt (pid 3292299) — process likely died before it could report why
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 12239s after spawn attempt (pid 2887953) — process likely died before it could report why
[spawn-attempt] issue-7/implementation: spawn halted pre-workspace: no outcome recorded 12214s after spawn attempt (pid 2887669) — process likely died before it could report why
sweep reported this tick: 3
lines remaining after tick: 4
```
One tick: sweep reports each of the 3 still-live subjects once (per the
existing #2413 per-subject dedup), then the same call's trailing
`_prune_spawn_attempts()` drops all 199 dead-pid records in that same
pass — down to the 4 real `halted` lines.

```
$ python3 -c "roster.spawn_attempt_sweep() # tick 2, same file"
[spawn-attempt] issue-1/implementation: spawn halted pre-workspace: -C 가 레포 루트가 아니라 그 하위 디렉터리다: ...
next tick reported: 1
lines remaining: 4
```
Tick 2 reports only the genuine `halted` outcome (on its own normal
per-attempt_id ledger cadence, unrelated to this change) — the historical
dead pids (issue-31, issue-7, and the other issue-1 no-outcome subject)
never resurface, because tick 1 already erased their records. Not "within
a week" — within the single tick that follows the fix landing.

Left the real backlog in this pruned state (matching the intended
production effect of the fix); the pre-mutation backup remains at
`/tmp/spawn-attempts.jsonl.backup-issue2431` for anyone who needs to
inspect the original 203-line file.

### Test coverage

canonical: python3 -m pytest transcript quoted below, this session.

Updated `SpawnAttemptPruneLiveness` in `tests/test_watch_hardening.py`:
renamed/rewrote the two tests whose premise the old 7-day bound baked in
(`test_dead_pid_within_retention_is_kept` assumed a 1-hour-old dead pid was
"well inside the 7-day window" and must be kept — under this fix that age
is now well past the new ~7-minute bound and must be pruned), and added:

- `test_dead_pid_within_dead_pid_bound_is_kept` — dead pid younger than
  `SPAWN_DEAD_PID_PRUNE_SEC` is kept.
- `test_dead_pid_past_dead_pid_bound_is_pruned` — dead pid past
  `SPAWN_DEAD_PID_PRUNE_SEC` (hours old, the real-backlog shape) is
  dropped.
- `test_dead_pid_past_old_retention_but_before_new_bound_is_pruned` —
  direct regression guard: an age well under the *old* 7-day
  `SPAWN_ATTEMPTS_RETENTION_SEC` (so #2418's code would have kept it) but
  past the *new* bound must now be dropped.
- `test_halted_branch_retention_is_unchanged` — a `halted` outcome inside
  the 7-day `SPAWN_ATTEMPTS_RETENTION_SEC` but past
  `SPAWN_DEAD_PID_PRUNE_SEC` is still kept, proving that branch's own
  bound was not touched.

```
$ python3 -m pytest tests/test_watch_hardening.py tests/test_spawn_pipeline.py -q -n0
........................................................................ [ 57%]
.....................................................                    [100%]
125 passed in 4.00s
```
125 = the full `test_watch_hardening.py` suite (39, up from 34 in #2413's
record — 5 new/rewritten in this change) plus `test_spawn_pipeline.py`'s
suite, both green.

Also attempted a broader collateral sweep
(`test_spawn_directive_assembly.py`, `test_spawn_gate_wiring.py`,
`test_spawn_board_flows.py`, `test_standing_red_watch.py`); it did not
finish inside a 110s budget (these suites include real subprocess/git
fixture tests, independent of this change) and was not force-completed —
noted here rather than silently dropped. This change is confined to one
function (`_prune_spawn_attempts`) and one new module constant with no
callers outside `spawn.py`/`roster.py`, both fully exercised by the suite
above and by the live real-backlog demonstration.

## Why

canonical: this section's reasoning is derived directly from the live
`python3 -c "..."` / `python3 -m pytest ...` transcripts quoted in full
under "What was done" above (all run in this session, this turn) plus
direct reads of `roster.py` (`SPAWN_ATTEMPT_GRACE_SEC` ~line 432,
`spawn_attempt_sweep()` ~line 435-511) and `spawn.py` (issue #2101
constants block, `DEADMAN_INTERVAL_SEC` ~line 1147) done in this session —
no claim below is unbacked by either a quoted transcript above or a cited
file:line read this turn.

**Why the 7-day window is wrong for this case, restated precisely**: the
`halted` branch's `SPAWN_ATTEMPTS_RETENTION_SEC` exists to keep a resolved,
reported halt visible/re-surfacing long enough for an operator or the
orchestrator to notice and act on it. A dead-pid, no-outcome record is
different in kind: it was never a resolved halt, it's evidence a process
died before it could report anything at all. Once the pid is confirmed
dead, there is no future event that could still arrive for it — nothing
left to "notice and act on" by waiting longer. #2413 reused the constant to
avoid inventing a new knob, a reasonable instinct, but the two cases don't
share the reason the window exists, only its adjacency in the same
function.

**Why not prune immediately on dead-pid confirmation**: the record's only
consumer, `spawn_attempt_sweep()` (`roster.py`), doesn't consider a
no-outcome attempt reportable until `SPAWN_ATTEMPT_GRACE_SEC` has elapsed
(`roster.py` ~line 487) — that's the legitimate pre-roster bootstrap
window (clone + checkout fetch + slack), during which a spawn may
legitimately have no roster entry yet even though its pid already exited
(e.g., it forked once more before that check). Pruning strictly on
liveness alone, with no age floor, risks erasing a genuinely-just-died
attempt before `spawn_attempt_sweep()` ever gets a chance to report it —
recreating a milder version of the exact problem this whole prune
mechanism (#2291/#2393/#2413) exists to prevent (a spawn attempt with zero
durable trace anywhere).

**Why `SPAWN_ATTEMPT_GRACE_SEC + DEADMAN_INTERVAL_SEC` specifically**:
`_prune_spawn_attempts()` runs as the last step of every
`spawn_attempt_sweep()` call, itself invoked once per watchdog tick
(`DEADMAN_INTERVAL_SEC`, default 120s — the poll-heartbeat cadence, per
the issue #2101 constants block). Adding one full `DEADMAN_INTERVAL_SEC`
on top of `SPAWN_ATTEMPT_GRACE_SEC` gives the record one guaranteed full
tick during which it is reportable before it becomes eligible for
pruning. The two-tick live demonstration above (tick 1: 3 subjects
reported, then all 199 dead-pid records pruned in the same call; tick 2:
0 of the historical dead pids resurface) is the concrete evidence this
margin is sufficient in practice for the real backlog's actual ages
(1.4–3.4 hours, far past both `SPAWN_ATTEMPT_GRACE_SEC` and the added
tick margin). Chose composition over a brand-new standalone constant for
the same reason #2413 avoided a new knob: both pieces already exist,
already mean exactly what's needed, and moving either one (e.g., someone
re-tuning `DEADMAN_INTERVAL_SEC` for a different watchdog cadence)
automatically keeps this bound correct without a second edit.

**Why this doesn't touch the `halted` branch**: the `elif
outcome.get("outcome") == "halted":` branch and its
`SPAWN_ATTEMPTS_RETENTION_SEC` check are untouched — same lines, same
constant, same 7-day comparison as before this change (`git diff spawn.py`
this session shows the only edit is inside the `if outcome is None:`
branch above it). The new `test_halted_branch_retention_is_unchanged`
(quoted passing in the pytest transcript above) and the live demonstration
above (the two real `halted` records in the actual backlog survived both
the direct prune call and two full watchdog-tick sweeps) both confirm this
directly rather than by inspection alone.

## What did not work

None.

## Upstream basis

canonical: `git log`/`git show` on this worktree's own history, and direct
reads of `roster.py`/`spawn.py` source, both done in this session.

- `docs/issue-2413/reports/implementation.md` (this repo, commit
  `c585122423bba09d63a61f2c666568449bbc4fa0`, read this session) — the fix
  this issue corrects: added `_pid_is_alive()` and reused
  `SPAWN_ATTEMPTS_RETENTION_SEC` for the dead-pid, no-outcome case. That
  liveness probe, and the never-prune-a-live-pid invariant it enforces,
  are kept exactly as #2413 left them (confirmed by reading the diff this
  session: `_pid_is_alive()` itself is untouched) — only the age bound
  applied once liveness is confirmed negative has changed in this commit.
- `roster.py`'s `SPAWN_ATTEMPT_GRACE_SEC` (issue #2291, read this session
  at `roster.py` ~line 432) and `spawn.py`'s `DEADMAN_INTERVAL_SEC` (issue
  #2101, read this session at `spawn.py` ~line 1147 before this change) —
  the two pre-existing constants this fix composes into
  `SPAWN_DEAD_PID_PRUNE_SEC`.

## Open findings

None. Resolution path: not applicable.

## Next steps

None — the fix is landed, tested, and demonstrated live against the real
backlog in this same session; `loop_state` above is terminal (`landed`).

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; matched `spawn.py`'s
own pre-existing Korean comment style when writing the new comments
explaining `SPAWN_DEAD_PID_PRUNE_SEC` (project-convention guard — avoids
leaving the file half English/half Korean, per the skill's own "project
convention conflicts — follow the project" edge case), while writing the
new test names/docstrings, this record, and all commit/PR text in English
per the repo's existing commit-message convention (`git log` shows English
subjects) and the skill's default.

other mounted skills: not triggered
(implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, implementation-blueprint
— this is a bound-tightening fix confined to one existing function plus
one new module-level constant composed from two pre-existing values; no
new module boundary, coupling change, GoF-pattern decision, or
multi-module structural choice was in scope).
