---
issue: 2413
role: execution-observation
loop_state: cleared
upstream:
  - path: docs/issue-2413/reports/implementation.md (untracked on this
      branch — lives on branch issue-2413/implementation / PR #2418; read
      via `git show bd3036db:docs/issue-2413/reports/implementation.md`)
    sha: bd3036dba91db953184f484bc9381eb8ed0b617f
  - path: spawn.py (issue #2413 fix, untracked on this branch)
    sha: bd3036dba91db953184f484bc9381eb8ed0b617f
  - path: roster.py (issue #2413 fix, untracked on this branch)
    sha: bf2640a464219e4863da432c68864c5e351b0209
  - path: tests/test_watch_hardening.py (issue #2413 fix, untracked on
      this branch)
    sha: bd3036dba91db953184f484bc9381eb8ed0b617f
subject: PR #2418 (issue-2413/implementation, still OPEN at observation
  time). Round 1 (HEAD `f98a4af8`): its five acceptance-criteria claims
  about `_prune_spawn_attempts()`'s pid-liveness-plus-retention-age bound
  and `spawn_attempt_sweep()`'s per-tick subject dedup. Round 2 (HEAD
  `bd3036db`, the CHANGES-round commit "fix missing-ts default in
  outcome-is-`None` prune branch"): this observation's own round-1 open
  finding (a record with no `ts` key at all was kept forever) as fixed by
  changing `ts = a.get("ts", now)` to `ts = a.get("ts")` in
  `_prune_spawn_attempts()`.
test: round 1 — independent re-derivation from source in a separate `git
  worktree` checked out at the PR's HEAD (not trusting the PR's own
  transcripts) — ran the PR's own pytest suite, then built an
  independently-authored 422-line synthetic `spawn-attempts.jsonl` (not
  reusing the PR's own fixture) and ran the actual pre-fix (commit
  `2ca4b4de`) and post-fix `_prune_spawn_attempts()`/
  `spawn_attempt_sweep()` code against it directly, plus a real
  backgrounded `sleep 120` process for the live-in-flight claim, plus a
  targeted probe of the `ts`-fallback branch. Round 2 — two fresh, separate
  `git worktree`s at the pre-fix (`f98a4af8`) and post-fix (`bd3036db`)
  commits, an independently-authored repro script (not the PR's own new
  test cases) exercising a `ts`-key-absent record across 4 simulated years
  at both commits, plus the PR's own two new unit tests and its full
  regression suite re-run in the post-fix worktree.
result: passed
assertedBy: execution-observation session, issue-2413 (build-now delivery)
---

# issue-2413 — execution-observation record

## What was done

Independently verified PR #2418's five acceptance-criteria claims by
reading the actual `spawn.py`/`roster.py` source at the PR's HEAD
(`f98a4af8`) in a separate `git worktree` (`/tmp/eo-2413-verify`, outside
this branch's own tree, so this observation never mutates or depends on
the code it is checking), re-running its test suite, and independently
reproducing its live and before/after demonstrations from scratch rather
than replaying its transcripts.

### Claim 1 — liveness test + bound stated with reasoning

canonical: `f98a4af8:spawn.py:1002-1032` (`_pid_is_alive`) and
`f98a4af8:spawn.py:1047-1069` (`_prune_spawn_attempts`'s outcome-is-`None`
branch), read directly in the `/tmp/eo-2413-verify` worktree.

`_pid_is_alive()` uses `os.kill(pid, 0)`, treating only
`ProcessLookupError` as dead and any other `OSError` (e.g.
`PermissionError` for a pid owned by another user) as alive. The
outcome-is-`None` branch keeps a record iff `_pid_is_alive(pid)` OR the
record's age is under `SPAWN_ATTEMPTS_RETENTION_SEC` — the same 7-day
constant the adjacent `halted` branch already uses (confirmed by reading
both branches side by side; no new knob introduced). Result: PASS — the
test and bound are present in source, matching PR #2418's own claim.

### Claim 2 — a genuinely in-flight attempt is kept, demonstrated live

acceptance: real backgrounded `sleep 120` (pid 197738) + a confirmed-dead
pid (999999999, `os.kill` → `ProcessLookupError`), both aged 8 days past
`SPAWN_ATTEMPTS_RETENTION_SEC`, run through the actual
`spawn._prune_spawn_attempts()` from the PR-HEAD worktree — result:
```
$ sleep 120 &
REAL_PID=197738
$ python3 - "$REAL_PID" <<'EOF'   # writes both records, then calls spawn._prune_spawn_attempts(now=now)
...
EOF
pid_is_alive(live): True
pid_is_alive(dead): False
dropped: 1
remaining attempt_ids: ['live-real']
```
The live pid's record survived at 8 days past retention; the dead pid's
record was the one line dropped, in the same run. PASS, demonstrated
live rather than asserted.

### Claims 3 & 4 — before/after counts and watchdog dedup

`runs/spawn-attempts.jsonl` is gitignored (`.gitignore:1`, `runs/`) and
does not exist in either worktree used for this observation:
```
$ ls runs/spawn-attempts.jsonl
ls: cannot access 'runs/spawn-attempts.jsonl': No such file or directory
```
matching PR #2418's own stated reason (untracked, per-checkout state).
Built a fresh, independently-authored 422-line synthetic reproduction of
the issue's own numbers (305 dead-pid/10-day-old no-outcome records for
issue 31, 114 for issue 7, plus 3 genuinely-current records for issues
2410-2412 with dead pids just past `SPAWN_ATTEMPT_GRACE_SEC` but not
past retention — not the PR's own `/tmp/otr-2413-demo/` fixture, noticed
on disk but deliberately not reused as the basis for this check) and ran
it through the actual code at two commits directly, in two separate
worktrees:

acceptance: `roster.spawn_attempt_sweep(d_all={}, now=now)` run against
the 422-line synthetic file on commit `2ca4b4de` (pre-fix, this branch's
own fork point) — result:
```
UNFIXED tick1 watchdog lines: 422 count()= 422
top subjects: [('issue-31/implementation', 305), ('issue-7/implementation', 114), ('issue-2410/implementation', 1), ('issue-2411/implementation', 1), ('issue-2412/implementation', 1)]
remaining total after tick1: 422
remaining by issue: Counter({31: 305, 7: 114, 2410: 1, 2411: 1, 2412: 1})
```

acceptance: the same call against a fresh copy of the same 422-line file
on PR #2418 HEAD (`f98a4af8`, post-fix) — result:
```
BEFORE PRUNE watchdog tick lines: 5 count()= 5
  [spawn-attempt] issue-2410/implementation: ...
  [spawn-attempt] issue-2411/implementation: ...
  [spawn-attempt] issue-2412/implementation: ...
  [spawn-attempt] issue-31/implementation: ...
  [spawn-attempt] issue-7/implementation: ...
prune dropped: 0
remaining total: 3
remaining by issue: Counter({2410: 1, 2411: 1, 2412: 1})
AFTER PRUNE watchdog tick lines: 0 count()= 0
```
(`prune dropped: 0` here is correct, not a discrepancy: `roster.
spawn_attempt_sweep()` already calls `_prune_spawn_attempts()` internally
at the end of the same call that printed the 5 lines above, so the file
was already down to 3 records by the time this second, standalone prune
call ran on it.)

Reading the two transcripts together: pre-fix, one tick emits 422 lines
(one per attempt_id, no dedup, derived: transcript above) and drops 0
records; post-fix, the same data in the same call emits 5 lines (one per
`(issue, role)` subject — 305 issue-31 lines and 114 issue-7 lines each
collapse to 1, derived: transcript above) and the file drops from 422
records to 3 (419 orphans gone: 305 + 114 = 419; the 3 genuinely-current
records kept, derived: transcript above). A second tick on the pruned
file emits 0 lines (derived: transcript above). These are smaller
absolute totals than the issue's filed 434 total (305 + 114 orphans + 15
other, derived: issue #2413 filing text — not independently
re-measured here since the real, gitignored `runs/spawn-attempts.jsonl`
is absent in this worktree per the `ls` result above) — but the
419-orphan (305 + 114) shape and the 422-to-5 watchdog-line collapse
reproduce the claim on this session's own independently-built fixture.
PASS on both claims.

### Claim 5 — repeated identical lines within one tick are collapsed

canonical: `f98a4af8:roster.py:467-505` (`spawn_attempt_sweep`'s
`reported_subjects` set), read directly — a plain local `set()` scoped
to one call, not a new ledger/state file. Evidence: same transcripts as
claims 3/4 above (422 identical-subject lines collapse to 5 total in one
`spawn_attempt_sweep()` call). PASS.

### Test suite

acceptance: `python3 -m pytest tests/test_watch_hardening.py -v` in the
PR-HEAD worktree — result:
```
============================== 32 passed in 0.89s ===============================
```
acceptance: `python3 -m pytest tests/test_spawn_pipeline.py
tests/test_standing_red_watch.py` — result:
```
============================== 97 passed in 8.75s ==============================
```
Both match PR #2418's own record's counts (derived: transcripts above).
The warrant-hunter's string-pid fix (`_pid_is_alive` coercing
digit-string pids before probing) and its test
(`test_string_encoded_live_pid_survives_past_retention`) ran as part of
the 32-test pass above, not just narrated in the PR's record.

### New finding, not in PR #2418's own record — a `ts`-missing record is kept forever

canonical: `f98a4af8:spawn.py:1064` (`ts = a.get("ts", now)` inside
`_prune_spawn_attempts()`'s outcome-is-`None` branch), read directly.

If the `ts` key is absent from a record, it falls back to the *current
call's* `now` parameter, so `now - ts` is always `0` and `aged_out` is
always `False`, regardless of how many watchdog ticks pass or how old
the record actually is.

acceptance: a dead pid (`os.kill` → `ProcessLookupError`) record with no
`ts` field, alongside a sibling with `ts: "not-a-number"`, run through
`spawn._prune_spawn_attempts()` on PR-HEAD, once at `now` and once with
`now` advanced 3 simulated years — result:
```
dropped: 1
remaining: ['no-ts-dead']
dropped after +3yr: 0
remaining after +3yr: ['no-ts-dead']
```
The `ts: "not-a-number"` sibling was correctly dropped (non-numeric `ts`
counts as `aged_out`); the `ts`-key-absent record was not dropped, even
3 simulated years later (derived: transcript above). CONFIRMED,
reproducible.

This is narrower than the issue's own 419-record backlog — the normal
writer, `f98a4af8:spawn.py:928-931` (`_record_spawn_attempt`), always
sets `ts`, so no currently-live orphan hits this path — but it is not
hypothetical: PR #2418's own fix for the sibling `pid`-as-string bug
cites a real precedent in this exact repo for this exact failure mode
(commit `cea0f583`, "root-cause implementation.json corruption" —
ledger records losing/gaining fields under hand-repair). A record that
loses its `ts` key the same way a record could gain a stringified `pid`
would be un-prunable forever under the fixed code, reproducing the
issue's own "kept forever" bug for a different missing field, silently.
Not covered by `tests/test_watch_hardening.py`'s new
`SpawnAttemptPruneLiveness` class (all five of its cases supply a
numeric `ts`) — confirmed by reading `f98a4af8:tests/
test_watch_hardening.py:479-624` directly.

## Round 2 — CHANGES-round fix for the missing-`ts` default

Re-review of PR #2418 after its CHANGES-round commit `bd3036db`
("fix missing-ts default in outcome-is-`None` prune branch"), which
addresses round 1's sole open finding above. Independently reproduced
from source rather than trusting the PR's own new record section or its
own new test cases as sufficient on their own.

canonical: `bd3036db:spawn.py:1069-1073` (the `outcome is None` branch of
`_prune_spawn_attempts()`), read directly in a fresh `git worktree`
(`/tmp/eo-2413-round2-fixed`, separate from round 1's worktrees and from
this branch's own tree). Diffed against round 1's HEAD (`f98a4af8`) to
confirm scope:
```
$ git diff f98a4af8 bd3036db --stat -- . ':!.orchestrate-hook-fires'
 docs/issue-2413/reports/implementation.md | 98 +++++++++++++++++++++++++++++--
 spawn.py                                  | 11 +++-
 tests/test_watch_hardening.py             | 29 +++++++++
 3 files changed, 131 insertions(+), 7 deletions(-)
```
Only the record, `spawn.py`, and the test file changed — no other
behavior moved in this round. The fix itself is a one-line default-value
change: `ts = a.get("ts", now)` → `ts = a.get("ts")`. A missing `ts` now
defaults to `None`, which fails the existing
`not isinstance(ts, (int, float))` check the same way a malformed `ts`
already did, making `aged_out = True` immediately — subject to the same
`_pid_is_alive(pid)` override every other record in this branch already
gets, so a live pid is still never pruned regardless of `ts`.

### Reproduction — independently authored, not the PR's own test cases

Wrote a standalone repro script (`/tmp/eo2413_round2_repro.py`, not
copied from the PR's own new `test_missing_ts_with_dead_pid_is_pruned`/
`test_missing_ts_with_live_pid_still_kept` cases) and ran it against two
fresh, separate worktrees — `f98a4af8` (round 1's HEAD, pre-this-fix) and
`bd3036db` (this fix) — via `SPAWN_ATTEMPTS_PATH=<worktree>/runs/
spawn-attempts.jsonl python3 /tmp/eo2413_round2_repro.py`, covering: a
dead-pid record with the `ts` key entirely absent, ticked across 4
simulated years; a live-pid record with `ts` entirely absent; a
non-numeric-`ts` sibling (the already-handled malformed case, checked for
regression); and a normal numeric-`ts` dead-pid record still inside
retention (checked for regression).

acceptance: repro script against pre-fix worktree (`f98a4af8`) — result:
```
=== dead pid, ts key entirely absent ===
tick 0 (+0yr): dropped=0 remaining=['no-ts-dead']
tick 1 (+1yr): dropped=0 remaining=['no-ts-dead']
tick 2 (+2yr): dropped=0 remaining=['no-ts-dead']
tick 3 (+3yr): dropped=0 remaining=['no-ts-dead']
=== live pid, ts key entirely absent ===
tick 0 (+0yr): dropped=0 remaining=['no-ts-live']
tick 1 (+1yr): dropped=0 remaining=['no-ts-live']
=== sibling regression check: ts non-numeric ===
dropped=1 remaining=[]
=== normal numeric ts, dead pid, within retention: still kept ===
dropped=0 remaining=['recent-dead']
```
acceptance: same repro script against post-fix worktree (`bd3036db`) —
result:
```
=== dead pid, ts key entirely absent ===
tick 0 (+0yr): dropped=1 remaining=[]
tick 1 (+1yr): dropped=0 remaining=[]
tick 2 (+2yr): dropped=0 remaining=[]
tick 3 (+3yr): dropped=0 remaining=[]
=== live pid, ts key entirely absent ===
tick 0 (+0yr): dropped=0 remaining=['no-ts-live']
tick 1 (+1yr): dropped=0 remaining=['no-ts-live']
=== sibling regression check: ts non-numeric ===
dropped=1 remaining=[]
=== normal numeric ts, dead pid, within retention: still kept ===
dropped=0 remaining=['recent-dead']
```
The dead-pid/missing-`ts` record now drops on the very first tick (dead
pid, no reason left to keep it) instead of surviving all 4 simulated
years, matching round 1's own reproduction of the gap and confirming the
fix closes it. The live-pid/missing-`ts` case, the malformed-`ts`
sibling, and the recent-numeric-`ts` case are byte-identical before and
after — no regression on any of the three cases this round's script also
checked. PASS.

### Test suite (post-fix worktree)

acceptance: `python3 -m pytest tests/test_watch_hardening.py -v -k
missing_ts` — result:
```
tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_missing_ts_with_dead_pid_is_pruned PASSED
tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_missing_ts_with_live_pid_still_kept PASSED
============================== 2 passed in 0.79s ===============================
```
acceptance: `python3 -m pytest tests/test_watch_hardening.py` (full file)
— result:
```
============================== 34 passed in 0.89s ===============================
```
34 = round 1's 32 plus these 2 new cases, matching the PR's own record.

acceptance: `python3 -m pytest tests/test_spawn_pipeline.py
tests/test_standing_red_watch.py` — result:
```
============================== 97 passed in 8.12s ==============================
```
No regressions, matching round 1's own count for these collateral suites.

### Checked the adjacent `halted` branch for the same pattern

canonical: `bd3036db:spawn.py:947-957` (`_record_spawn_outcome`), read
directly in `/tmp/eo-2413-round2-fixed`:
```
$ sed -n '947,957p' spawn.py
def _record_spawn_outcome(attempt_id: str, outcome: str, detail: str) -> None:
    ...
    _append_spawn_attempt_event({"event": "spawn_attempt_outcome",
                                  "attempt_id": attempt_id, "outcome": outcome,
                                  "detail": detail, "ts": time.time()})
```
The PR's own record notes `outcome_ts = outcome.get("ts", now)` (the
`halted` branch, a few lines below the fixed one) has the identical
shape and was deliberately left unchanged, reasoning that
`_record_spawn_outcome()` — the only writer of `spawn_attempt_outcome`
events — always sets `ts`. Reading the function directly (quoted above)
confirms `time.time()` is set unconditionally on every write, with no
optional/keyword path that could omit it, so a real `halted` outcome
record cannot have a missing `ts` the way a hand-written or
legacy-corrupted `spawn_attempt` record could. The PR's scope decision to
leave this branch alone checks out independently — not just restated.

### Round 1's open finding — resolved

canonical: this section's own "Reproduction" and "Test suite"
subsections above (this session's own transcripts, quoted verbatim) are
the basis for this verdict.

Round 1's one open finding (`_prune_spawn_attempts()`'s outcome-is-`None`
branch never ages out a record with no `ts` key at all) is fixed: the
"Reproduction" transcript above shows the dead-pid/missing-`ts` record
dropping on tick 0 post-fix versus surviving all 4 simulated years
pre-fix, and the "Test suite" transcript above shows both new unit tests
plus the full 34-test file and the 97-test collateral suites passing in
the post-fix worktree. No new gap surfaced while probing the fix itself
or its one adjacent lookalike (the `halted` branch, checked above).
Round 2 result: PASS, no open findings remain.

## Why

canonical: this session's own worktree reads and command transcripts
quoted under "What was done" above (`/tmp/eo-2413-verify` at
`f98a4af8`, `/tmp/eo-2413-base` at `2ca4b4de`) are the basis for every
claim in this section.

Re-derived from source rather than trusting PR #2418's own transcripts,
per this role's purpose (cf. `docs/issue-292/reports/
execution-observation.md`, untracked on this branch — a different
repo's checkout — a narration-only read reproduces the narration's own
blind spots). Building an independently-authored synthetic fixture
rather than reusing the PR's own left-behind `/tmp/otr-2413-demo/`
files, and running the actual pre-fix commit (`2ca4b4de`) directly
rather than trusting the PR's "stashed the diff" description of its own
before-state, closes the same trust gap for the before/after claims that
re-reading source closes for the liveness-test claim.

The `ts`-fallback finding came from asking the adversarial question this
role exists to ask — "is 'outcome is None, pid dead, old enough' the
*only* way this record shape can still leak?" — given
`_prune_spawn_attempts()`/`_pid_is_alive()` already handle one
malformed-field precedent (stringified `pid`) explicitly, by name,
citing a real corruption incident in this repo; the adjacent field
(`ts`) sharing the same corruption precedent but not the same defensive
handling was the natural next thing to probe, and probing it (rather
than assuming symmetry with the `pid` fix) is what surfaced a
reproducible, real gap.

This does not reopen or re-litigate the fix's overall approach (pid
liveness + reused retention window is sound, matches the operator's
"cut the noise, not the mechanism" constraint, and is the right
mechanism for the 419 orphans actually named in the issue) — the finding
is narrower: the mechanism is not fully general to every way a record's
outcome-is-`None`-and-orphaned state can arise, specifically a corrupted
record missing `ts` rather than missing `outcome`.

## Upstream basis

- `docs/issue-2413/reports/implementation.md` (untracked on this branch
  — PR #2418 / branch issue-2413/implementation, sha
  `335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8`) — PR #2418's own record,
  whose five claims and `SpawnAttemptPruneLiveness`/
  `SpawnAttemptSweepDedup` test descriptions this observation checks
  against source rather than restates.
- `docs/issue-2413/reports/implementation/
  2026-08-25-hunt-issue-2413-prune-fix.md` (untracked on this branch,
  same PR) — the before-landing warrant-hunter's string-pid finding,
  whose fix and test this observation re-ran rather than assumed.
- `spawn.py`, `roster.py`, `tests/test_watch_hardening.py` at PR #2418
  HEAD (`f98a4af895a0b336b461fac4003792cafc5efa11`) — read and executed
  directly in a separate `git worktree`, not from the PR's own quoted
  excerpts.
- `spawn.py`, `roster.py` at `2ca4b4de` (this branch's own fork point,
  pre-fix) — read and executed directly in a second separate worktree to
  produce the before/after comparison independently rather than trust
  the PR's "git stash" description of its own before-state.
- `docs/issue-2413/reports/implementation.md`'s "CHANGES round (PR
  #2418) — missing-`ts` gap" section (untracked on this branch, same PR,
  sha `bd3036dba91db953184f484bc9381eb8ed0b617f`) — PR #2418's own
  round-2 record of the `ts`-default fix, whose fix and new tests this
  observation's "Round 2" section re-derives from source and re-runs
  rather than restates.
- `spawn.py`, `tests/test_watch_hardening.py` at PR #2418 HEAD
  (`bd3036dba91db953184f484bc9381eb8ed0b617f`) — read and executed
  directly in a third separate `git worktree`
  (`/tmp/eo-2413-round2-fixed`), not from the PR's own quoted excerpts.
- Issue #2413 itself — the five acceptance checks this record addresses
  one by one, and the operator-frozen constraint comment (no added
  steady-state cost, no consumer-tree pollution). canonical:
  `f98a4af8:spawn.py:1-3` (`spawn.py`'s own module docstring, "on-the-record
  의 핵심 동작 하나" — `spawn.py`/`roster.py` are on-the-record's own
  operational scripts, not files installed into or templated onto a
  consumer repo's tree) and `f98a4af8:roster.py:467-510` (`_pid_is_alive`
  is called only from inside the existing once-per-tick
  `_prune_spawn_attempts()` pass, confirmed by reading its only two call
  sites) — both constraints satisfied by construction.

## Open findings

Round 1 found one open finding (quoted here for the record's own
continuity, then resolved below):

1. `_prune_spawn_attempts()`'s outcome-is-`None` branch never ages out a
   record whose `ts` field is entirely absent (as opposed to present but
   non-numeric, which it does correctly age out) — `ts = a.get("ts",
   now)` makes `now - ts` always `0`. See "New finding" above for the
   reproduction (derived: transcript there). A dead-pid record missing
   `ts` is kept forever, reproducing this issue's own "kept forever"
   failure for a field-corruption shape the PR's own fix already treats
   as a real, named precedent (commit `cea0f583`) for the sibling `pid`
   field, but does not extend the same defensive handling to. Resolution
   path (round 1): a small follow-up to `spawn.py:1064` — treat a missing
   `ts` the same as a non-numeric one (`aged_out = True` when the key is
   absent or not a number, instead of defaulting the value itself to
   `now`), plus a test case alongside the existing
   `SpawnAttemptPruneLiveness` class.

Resolution path (round 2): applied, verified, closed. PR #2418's commit
`bd3036db` implements exactly the resolution path stated above (`ts =
a.get("ts")`, no other branch change) and adds
`test_missing_ts_with_dead_pid_is_pruned`/
`test_missing_ts_with_live_pid_still_kept` to
`SpawnAttemptPruneLiveness`. canonical: "Round 2 — CHANGES-round fix for
the missing-`ts` default" above — this session's own independently
authored repro script (not the PR's new test cases) reproduces the
dead-pid/missing-`ts` record dropping on tick 0 post-fix versus surviving
4 simulated years pre-fix ("Reproduction" subsection transcripts above),
and the PR's own two new tests plus its full 34-test file and 97-test
collateral suites pass in the post-fix worktree ("Test suite" subsection
transcript above). No open findings remain.

## Next steps

None from this record's own scope — `loop_state: cleared`, matching
`docs/issue-292/reports/execution-observation.md`'s precedent (untracked
on this branch — a different repo's checkout) for this record kind (no
repo-defined terminal-state override exists for `execution-observation`
records). Nothing further is queued in this session: round 1's five
acceptance-claim checks and test-suite runs, plus round 2's independent
reproduction of the CHANGES-round `ts`-default fix, its test suite, and
its adjacent-branch check (canonical: "Round 2" section above, this
session's own transcripts), cover the full scope this record set out to
check. Whether and when to merge PR #2418 is the human's call, not this
observation's to decide.
