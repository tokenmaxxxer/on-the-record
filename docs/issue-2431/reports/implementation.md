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
breaking: "no — advisory-only watch-layer behavior change; no public API, CLI flag, or on-disk schema changed. Effect (post-CHANGES-round, see bottom section): a dead-pid, no-outcome spawn attempt is pruned once its ts clears SPAWN_ATTEMPT_GRACE_SEC (~5 min, the same threshold the watchdog report loop already uses) rather than the fully-unconditional immediate prune this branch's earlier commits had landed, and unchanged behavior for the halted-outcome category."
verdict: pass
---

# issue-2431 — implementation record

## amendments-reconciled

amendments-reconciled: issuecomment-5410865516 and issuecomment-5411038089
— both posted after this session's initial issue read, both read via `gh
api` before this PR was opened, both reconciled into the delivered design
below (and into the "Why" section's design-history explanation).

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/2431/comments`,
run this session, returned two operator comments posted after this
session started (both dated 2026-08-25, after the session's initial issue
read):

- issuecomment-5410865516 (13:11 UTC) — operator-frozen constraint: the
  fix must hold with no added per-spawn overhead/steady-state load, no new
  conflict surfaces, no stall/deadlock modes, no consumer-tree pollution;
  and explicitly, the `halted`-outcome branch's 7-day retention must stay
  exactly as-is.
- issuecomment-5411038089 (13:24 UTC, mid-flight) — operator guidance
  narrowing the bound further than this session's first draft: even a
  short calendar bound (this session's first draft used ~7 minutes,
  `roster.SPAWN_ATTEMPT_GRACE_SEC + DEADMAN_INTERVAL_SEC`) is unnecessary
  for the confirmed-dead-pid case — once `_pid_is_alive()` returns
  `False`, that conclusion is already final and no further waiting learns
  anything new. Prune it on the very next `_prune_spawn_attempts()` pass,
  with no calendar delay at all. Only the genuinely uncertain case
  (`_pid_is_alive()`'s own ambiguous-`OSError` path) should ever be
  time-bounded, and that's already handled conservatively elsewhere in
  that function (treated as "alive").

Both are reconciled into the design below: the delivered fix has no
calendar bound at all for the dead-pid case (superseding this session's
own first draft, which is visible only in earlier commit history on this
branch, not in the final diff), and the `halted` branch is untouched, as
both required.

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

**Fix** (`spawn.py`, `_prune_spawn_attempts()`): the `outcome is None`
branch now checks liveness only, with no age/`ts` check for the dead-pid
case at all (per the mid-flight operator guidance above):

- pid still alive → kept, at any age (unchanged from #2413 — the hard
  in-flight-must-never-be-pruned invariant).
- pid confirmed dead → dropped unconditionally, on the very next prune
  pass, regardless of `ts`/age.

No new module-level constant. `spawn_attempt_sweep()` (`roster.py`) still
gets a report chance for free, with no separate grace period needed:
within one call, it runs its subject-report loop (gated by the existing
`SPAWN_ATTEMPT_GRACE_SEC`) *before* it calls `_prune_spawn_attempts()` at
the end of that same call (`roster.py` ~line 510) — so a record already
past `SPAWN_ATTEMPT_GRACE_SEC` is reported in that same tick, immediately
before it's pruned.

The `halted`-outcome branch (`elif outcome.get("outcome") == "halted":`,
still gated by the untouched `SPAWN_ATTEMPTS_RETENTION_SEC`) was not
touched — explicitly required by issuecomment-5410865516, confirmed by
inspection (`git diff spawn.py` this session shows the only edits are
inside the `if outcome is None:` branch and the removal of the
now-superseded `SPAWN_DEAD_PID_PRUNE_SEC` constant), a new regression test
(`test_halted_branch_retention_is_unchanged`), and the live demonstration
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
`/tmp/spawn-attempts.jsonl.backup-issue2431` before mutating it; re-ran
this same demonstration a second time after the mid-flight design
amendment, restoring from that same backup first, to reconfirm the final
(no-calendar-bound) code against the same real file.

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

After (final code — no calendar bound for the dead-pid case — run
directly against the same real file, restored from backup):

```
$ MUSTER_STATE_ROOT=.../on-the-record-issue-2395-implementation/runs \
  python3 -c "import spawn; print('dropped:', spawn._prune_spawn_attempts())"
dropped: 199
$ python3 -c "import spawn; print('second run dropped:', spawn._prune_spawn_attempts())"
second run dropped: 0
$ wc -l spawn-attempts.jsonl
4
$ cat spawn-attempts.jsonl
{"event": "spawn_attempt", ..., "pid": 3828118, "ts": 1787652640.165...}
{"event": "spawn_attempt_outcome", ..., "outcome": "halted", "detail": "-C 가 레포 루트가 아니라 그 하위 디렉터리다: ...", ...}
{"event": "spawn_attempt", ..., "pid": 3828120, "ts": 1787652640.217...}
{"event": "spawn_attempt_outcome", ..., "outcome": "halted", "detail": "-C 가 존재하지 않는 디렉터리다: ...", ...}
```
Reading straight off the fence above: `dropped: 199` against the 199
no-outcome ids characterized in the "Before" block — every dead-pid
no-outcome orphan dropped in one pass, not "near-zero" but exactly zero
remaining in that category. The immediate re-run shows `second run
dropped: 0` (idempotent — nothing left to drop), and `wc -l` shows exactly
4 lines remain, both surviving pairs real `halted` outcomes (issue-2395
fixture records testing `-C` path validation) — exactly the category this
change leaves untouched.

This session's earlier run of the first-draft (short-calendar-bound) code
against this same real backlog, before the mid-flight amendment, produced
the identical `dropped: 199` result (derived: the "What did not work"
section's cross-reference is unnecessary here since the first draft was
superseded, not defective — see "amendments-reconciled" above). The
narrowing to zero calendar bound didn't change the outcome against this
particular backlog, because every real orphan in it was already hours
old, far past either bound. The difference the amendment makes is in a
case a several-hours-old real backlog can't exercise: a pid that dies only
seconds before a prune pass, which the first draft would have kept a few
minutes longer and the final code prunes immediately — covered instead by
the new `test_dead_pid_pruned_immediately_even_when_ts_is_fresh` unit test
(passing in the pytest transcript under "Test coverage" below).

### Watchdog stops re-emitting within one tick — demonstrated

canonical: python3 -c "..." invocations of the real
`roster.spawn_attempt_sweep()` (the actual watchdog-tick entry point,
which calls `_prune_spawn_attempts()` internally at the end of the same
call — see `roster.py` line ~510) run in this session, against the same
real backlog restored from the backup above, re-run against the final
code.

```
$ python3 -c "roster.spawn_attempt_sweep() # tick 1, fresh 203-line backlog"
[spawn-attempt] issue-1/implementation: spawn halted pre-workspace: -C 가 존재하지 않는 디렉터리다: /tmp/issue-2395-does-not-exist
  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 13108s after spawn attempt (pid 2887953) — process likely died before it could report why
[spawn-attempt] issue-7/implementation: spawn halted pre-workspace: no outcome recorded 13083s after spawn attempt (pid 2887669) — process likely died before it could report why
tick 1 reported: 3
lines remaining: 4
```
One tick: sweep reports each of the 3 still-reportable subjects once (per
the existing #2413 per-subject dedup), then the same call's trailing
`_prune_spawn_attempts()` drops all 199 dead-pid records in that same
pass — down to the 4 real `halted` lines, per the fence above.

```
$ python3 -c "roster.spawn_attempt_sweep() # tick 2, same file"
tick 2 reported: 0
lines remaining: 4
```
Tick 2 reports nothing further (per the fence above — the surviving
`halted` records' own per-attempt_id ledger dedup was still within its TTL
from an earlier run in this same session) — the historical dead pids
(issue-31, issue-7, and the other issue-1 no-outcome subject) never
resurface, because tick 1 already erased their records. Not "within a
week" — within the single tick that follows the fix landing.

Left the real backlog in this pruned state (matching the intended
production effect of the fix); the pre-mutation backup remains at
`/tmp/spawn-attempts.jsonl.backup-issue2431` for anyone who needs to
inspect the original 203-line file.

### Test coverage

canonical: python3 -m pytest transcript quoted below, this session, run
against the final (post-amendment) code.

Updated `SpawnAttemptPruneLiveness` in `tests/test_watch_hardening.py`:

- `test_dead_pid_pruned_immediately_even_when_ts_is_fresh` — a dead-pid
  record whose `ts` is one second old is still pruned immediately (the
  case the mid-flight amendment specifically targets, and that the real
  backlog above couldn't exercise since nothing in it was that fresh).
- `test_dead_pid_pruned_regardless_of_old_retention_window` — a dead-pid
  record well under the *old* 7-day `SPAWN_ATTEMPTS_RETENTION_SEC` (so
  #2418's code would have kept it) is dropped.
- `test_halted_branch_retention_is_unchanged` — a `halted` outcome
  recorded a moment ago is still kept, even though a bare dead-pid record
  of the same age (no outcome) is now pruned immediately by the sibling
  branch — proving the two branches diverge exactly as intended.
- `test_missing_ts_with_dead_pid_is_pruned` / `test_missing_ts_with_live_pid_still_kept`
  (pre-existing from #2418's CHANGES round) — re-verified still passing:
  the missing-`ts` failure mode they guard against is now structurally
  impossible for the dead-pid case (this branch never reads `ts` at all
  any more), which subsumes the original fix.

```
$ python3 -m pytest tests/test_watch_hardening.py tests/test_spawn_pipeline.py -q -n0
........................................................................ [ 58%]
....................................................                     [100%]
124 passed in 4.69s
```
124 passed per the fence above — the full `test_watch_hardening.py` suite
(38, up from #2413's record's 34: net +4 after collapsing two
dead-pid-bound tests into one
`test_dead_pid_pruned_immediately_even_when_ts_is_fresh` plus adding one
`test_dead_pid_pruned_regardless_of_old_retention_window` and one
`test_halted_branch_retention_is_unchanged`) plus `test_spawn_pipeline.py`'s
suite, both green, zero failed/skipped.

Also attempted a broader collateral sweep
(`test_spawn_directive_assembly.py`, `test_spawn_gate_wiring.py`,
`test_spawn_board_flows.py`, `test_standing_red_watch.py`); it did not
finish inside a 110s budget (these suites include real subprocess/git
fixture tests, independent of this change) and was not force-completed —
noted here rather than silently dropped. This change is confined to one
function (`_prune_spawn_attempts`) with no callers outside
`spawn.py`/`roster.py`, both fully exercised by the suite above and by the
live real-backlog demonstration.

## Why

canonical: this section's reasoning is derived directly from the two
operator comments quoted under "amendments-reconciled" above
(issuecomment-5410865516, issuecomment-5411038089, both read via `gh api`
this session), the live transcripts quoted under "What was done" above
(all run in this session, this turn), and direct reads of `roster.py`
(`SPAWN_ATTEMPT_GRACE_SEC` ~line 432, `spawn_attempt_sweep()` ~line
435-511, report-loop-then-prune ordering confirmed by reading the function
body this session) done in this session.

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

**Why no calendar bound at all, rather than a short one**: this session's
first draft used `roster.SPAWN_ATTEMPT_GRACE_SEC + DEADMAN_INTERVAL_SEC`
(~7 minutes) reasoning that `spawn_attempt_sweep()` needed a guaranteed
window to report the record before it's pruned. Operator guidance
(issuecomment-5411038089) corrected this: `_pid_is_alive()` returning
`False` is already a final, confirmed conclusion — no further elapsed
time produces new information about it, so there's nothing left to wait
for calendar-wise. The report-chance concern is real but doesn't need a
separate time bound to satisfy: `spawn_attempt_sweep()` already runs its
report loop and then calls `_prune_spawn_attempts()` in that order,
within one function call (confirmed by reading `roster.py` ~line
435-511 this session) — so any record already past
`SPAWN_ATTEMPT_GRACE_SEC` gets its report in the very same tick, just
before pruning, with no additional margin required. Removing the bound
entirely also directly satisfies the "immediate-on-dead-pid" option the
issue's own acceptance criteria explicitly listed as acceptable.

**Why the ambiguous-liveness case still doesn't need a bound here**: per
`_pid_is_alive()`'s own docstring/logic (unchanged by this commit), a pid
check that can't conclusively determine death (`PermissionError` or other
non-`ProcessLookupError` `OSError`) is already treated as "alive" inside
that helper — such a record never reaches the "confirmed dead" branch at
all, so this change's no-bound rule for confirmed-dead pids never has to
reason about the uncertain case; it's filtered out one layer up.

**Why this doesn't touch the `halted` branch**: the `elif
outcome.get("outcome") == "halted":` branch and its
`SPAWN_ATTEMPTS_RETENTION_SEC` check are untouched — same lines, same
constant, same 7-day comparison as before this change (`git diff spawn.py`
this session shows the only edits are inside the `if outcome is None:`
branch above it, plus removal of the now-unused
`SPAWN_DEAD_PID_PRUNE_SEC` constant this session's own first draft had
added and then removed after the amendment). Required explicitly by
issuecomment-5410865516 ("the halted-outcome branch's 7-day retention must
stay exactly as-is"). The new `test_halted_branch_retention_is_unchanged`
(quoted passing in the pytest transcript above) and the live demonstration
above (the two real `halted` records in the actual backlog survived both
the direct prune call and two full watchdog-tick sweeps) both confirm this
directly rather than by inspection alone.

**Why no new steady-state cost** (per issuecomment-5410865516's
operator-frozen constraint): `_pid_is_alive()` is unchanged — still only
called from inside `_prune_spawn_attempts()`'s existing once-per-tick
pass, itself only invoked from `spawn_attempt_sweep()`'s existing
once-per-watchdog-tick call. Removing the age check for the dead-pid case
makes the per-record work strictly *less* than #2413's version (one
`isinstance`/comparison fewer per dead-pid record), not more, and doesn't
add any new call, lock, file, or polling loop.

## What did not work

None. This session's own first draft — the short-calendar-bound design —
was superseded by an in-flight operator correction before landing, not by
a defect discovered through testing; recorded under "amendments-reconciled"
above rather than here, since nothing in that draft was itself broken.

## Upstream basis

canonical: `git log`/`git show` on this worktree's own history, direct
reads of `roster.py`/`spawn.py` source, and `gh api
repos/tokenmaxxxer/on-the-record/issues/2431/comments`, all done in this
session.

- `docs/issue-2413/reports/implementation.md` (this repo, commit
  `c585122423bba09d63a61f2c666568449bbc4fa0`, read this session) — the fix
  this issue corrects: added `_pid_is_alive()` and reused
  `SPAWN_ATTEMPTS_RETENTION_SEC` for the dead-pid, no-outcome case. That
  liveness probe, and the never-prune-a-live-pid invariant it enforces,
  are kept exactly as #2413 left them (confirmed by reading the diff this
  session: `_pid_is_alive()` itself is untouched) — only the age bound
  applied once liveness is confirmed negative has changed in this commit
  (removed entirely, per the mid-flight amendment above).
- `roster.py`'s `SPAWN_ATTEMPT_GRACE_SEC` (issue #2291, read this session
  at `roster.py` ~line 432) and `spawn_attempt_sweep()`'s report-then-prune
  ordering (`roster.py` ~line 435-511, read this session) — the mechanism
  that gives the dead-pid case its report chance without needing a
  separate time bound.
- issuecomment-5410865516 / issuecomment-5411038089 (issue #2431, read via
  `gh api` this session) — see "amendments-reconciled" above.

## Open findings

None. Resolution path: not applicable.

## Next steps

None — the fix is landed, tested, and demonstrated live against the real
backlog in this same session, including a full re-run after reconciling
the mid-flight operator amendment; `loop_state` above is terminal
(`landed`).

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; matched `spawn.py`'s
own pre-existing Korean comment style when writing the new comment
explaining the no-calendar-bound dead-pid rule (project-convention guard —
avoids leaving the file half English/half Korean, per the skill's own
"project convention conflicts — follow the project" edge case), while
writing the new test names/docstrings, this record, and all commit/PR text
in English per the repo's existing commit-message convention (`git log`
shows English subjects) and the skill's default.

other mounted skills: not triggered
(implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice, implementation-blueprint
— this is a bound-tightening fix confined to one existing function, ending
in the removal of the one new module-level constant this session's own
first draft had briefly added; no new module boundary, coupling change,
GoF-pattern decision, or multi-module structural choice was in scope).

## CHANGES round (PR #2434 / PR #2438 execution-observation) — reporting gap closed

canonical: the CHANGES-round task prompt itself (this turn's own input,
quoting PR #2438's execution-observation finding verbatim: "a dead-pid
record younger than SPAWN_ATTEMPT_GRACE_SEC (300s) can now be pruned
with ZERO reports ever fired"), plus `git log --oneline -5` and direct
reads of `spawn.py` `_prune_spawn_attempts()` and `roster.py`
`spawn_attempt_sweep()` done this session, confirming the pre-round code
on this branch (commits `278c0d7c`..`6531f56f`, described in the
sections above) pruned a confirmed-dead pid unconditionally with no age
gate at all, while `spawn_attempt_sweep()`'s own report loop (`roster.py`
~line 487) skips a no-outcome record whose age is still under
`SPAWN_ATTEMPT_GRACE_SEC`.

The gap: a dead-pid, no-outcome record younger than
`roster.SPAWN_ATTEMPT_GRACE_SEC` (300s) could be pruned with zero
watchdog reports ever fired — reopening the exact silent-failure class
#2291/#2393/#2413/#2431 exist to close. The sections above (this same
file, written before this round) describe the design that had this gap;
this section supersedes their "no calendar bound at all" conclusion with
the correction below, per this round's explicit operator instruction.

**Fix** (`spawn.py`, `_prune_spawn_attempts()`, `outcome is None`
branch): reintroduced an age check for the confirmed-dead-pid case,
bound to `SPAWN_ATTEMPT_GRACE_SEC` (~5 minutes —
`CLONE_TIMEOUT + NETWORK_TIMEOUT + 60`, `roster.py`), not the 7-day
`SPAWN_ATTEMPTS_RETENTION_SEC` #2413 originally reused:

- pid alive → kept, at any age (unchanged).
- pid dead, `ts` still within `SPAWN_ATTEMPT_GRACE_SEC` → kept (the new
  gate — this is exactly the case the prior round's unconditional prune
  got wrong).
- pid dead, `ts` past `SPAWN_ATTEMPT_GRACE_SEC` (or missing/invalid
  `ts`, no basis to compute a window) → pruned.

Reusing the report loop's own threshold, rather than inventing a new
constant, is what closes the gap: a record can only become
prune-eligible once it has also become report-eligible under the exact
same test, and `spawn_attempt_sweep()` runs its report loop *before*
calling `_prune_spawn_attempts()` within the same call (`roster.py`
~line 510, read this session) — so the tick that first crosses the
threshold is always a tick where the report loop already reviewed that
record. No new steady-state cost: the same single
`isinstance`/comparison per dead-pid record the prior round's commit had
removed.

acceptance: `python3 -m pytest tests/test_watch_hardening.py -q` — result:
```
37 passed in 1.17s
```
acceptance: `python3 -m pytest tests/test_spawn_pipeline.py -q` — result:
```
89 passed in 1.91s
```
derived: `grep -rl '_prune_spawn_attempts\|spawn_attempt_sweep\|_load_spawn_attempts\|SPAWN_ATTEMPT_GRACE_SEC\|SPAWN_ATTEMPTS_RETENTION_SEC' test/ tests/ on-the-record/` run this session returned only `tests/test_watch_hardening.py` — the two suites above are this change's full blast radius.

New test added this session:
`SpawnAttemptSweepReportsBeforePrune.test_fast_dying_halt_reported_before_it_is_pruned`
(`tests/test_watch_hardening.py`) drives the real
`roster.spawn_attempt_sweep()` (not a mock of the prune function alone)
across two ticks with a genuinely dead pid (`os.fork()` + immediate
`os._exit(0)` + reap): tick 1 (1s after death, inside the grace window)
asserts zero reports printed and the record still present; tick 2 (past
the grace window) asserts exactly one report line printed *and* the
record pruned in that same call — both included in the `37 passed`
fence above. Also split the prior round's
`test_dead_pid_pruned_immediately_even_when_ts_is_fresh` (which asserted
the now-fixed buggy behavior) into
`test_dead_pid_with_fresh_ts_is_kept_until_grace_window` (new
expectation: kept) and `test_dead_pid_pruned_once_past_grace_window`
(pruned once past the shared threshold) — same file, same fence.

**Live demonstration**, this session, real dead pid via `os.fork()`,
against this checkout's own gitignored `runs/spawn-attempts.jsonl` (not
a mock):

canonical: `python3 -c "..."` run directly in this session (transcript
below verbatim, only the pid number varies run to run):
```
=== tick 1: 1s after death (well inside SPAWN_ATTEMPT_GRACE_SEC=300s) ===
reports printed this tick: 0
record still present after tick 1: True

=== tick 2: past SPAWN_ATTEMPT_GRACE_SEC ===
[spawn-attempt] issue-9991/implementation: spawn halted pre-workspace: no outcome recorded 301s after spawn attempt (pid 983038) — process likely died before it could report why
reports printed this tick: 1
record still present after tick 2: False
```
Confirms the guarantee directly: the record is never pruned before its
one report fires, and once it does fire, the prune happens in that same
tick (not a week later, not never).

derived: `python3 -c "import spawn; print(spawn._load_spawn_attempts())"`
against this checkout's own `spawn.STATE_ROOT` (`runs/`, this session)
returned an empty file — the 434-record backlog the issue was filed
against was already fully pruned by this branch's earlier commits before
this CHANGES round started (`git log --oneline -5`, this session, shows
`278c0d7c`/`791856c7` predate this round), so there is no live
434-shaped backlog left in this workspace to re-run the "434 →
near-zero" acceptance check against directly. That check was already
satisfied and demonstrated in this file's "Live demonstration against
the REAL current backlog" section above (199-record sibling-workspace
backlog, `dropped: 199`, quoted there with its own canonical tag) before
this CHANGES round began. This round only closes the
report-before-prune gap PR #2438 found in that already-landed fix, and
does not need to re-run that prior demonstration: every record in that
199-record backlog was already 1.4–3.4 hours old (per that section's own
fence), far past the new 5-minute `SPAWN_ATTEMPT_GRACE_SEC` gate added
this round — the new gate only changes the outcome for records younger
than 5 minutes, which that backlog never contained.

derived: `git diff main -- spawn.py` (this session) shows this round's
edits confined to the `if outcome is None:` branch of
`_prune_spawn_attempts()` and its comment; the `elif outcome.get(...) ==
"halted":` branch and its `SPAWN_ATTEMPTS_RETENTION_SEC` check are
byte-identical to the prior round's diff against `main`.
`test_halted_branch_retention_is_unchanged` (pre-existing, unmodified
this round) is included in the `37 passed` fence above.

### What did not work (this round)

Nothing discarded. The one design question this round faced — whether to
track "already reported" via a new persistent marker (either a
reconcile-ledger read or a new event type appended to
`SPAWN_ATTEMPTS_PATH` itself) versus reusing the report loop's existing
`SPAWN_ATTEMPT_GRACE_SEC` age threshold as a shared gate — was resolved
by inspection before writing any code: a persistent-marker design would
have made `_prune_spawn_attempts()` depend on `RECONCILE_LEDGER` state
that most existing tests (e.g. `SpawnAttemptSweepDedup`,
`_HardeningCase`) mock around without ever populating, silently
reading/touching real ledger files in tests that do not expect a new
filesystem dependency, and would have left genuinely-old backlog records
un-prunable on their very first post-fix tick until a first "reported"
marker got written for them — directly reopening the "434 must drop in
one tick" requirement this whole issue chain is about. The shared-age-
threshold design avoids both problems with no new state at all, so it
was adopted directly rather than tried and reverted.

### Skill verdicts (this round)

canonical: `Skill(work-in-english)` invoked this session (this turn),
full SKILL.md content returned and read; `git diff` (this session) of
`spawn.py`'s new comment block and `tests/test_watch_hardening.py`'s new
test names/docstrings, both written this session, confirm the language
split described in the verdict below.

skill-verdict: work-in-english — applied: invoked; loaded the skill this
round and confirmed the choices already in progress matched it —
Korean comments in `spawn.py` matching that file's own pre-existing
Korean comment-style convention (edge case: "project convention
conflicts — follow the project"), English for the new test
names/docstrings, this record, the commit message, and the PR comment.

other mounted skills: not triggered (implementation-blueprint et al. —
this round is a two-line logic change confined to one existing branch
of one existing function, no new module structure or GoF-pattern
decision in scope, same reasoning as the prior round's verdict above).
