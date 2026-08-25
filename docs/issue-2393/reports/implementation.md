---
issue: 2393
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2291/reports/implementation.md
    sha: 75390fc383bd5138d2ed34c80dd6b0422500dde1
code_under_review:
  - spawn.py
  - roster.py
type: fix
breaking: none
verdict: pass
---

# issue-2393 — implementation record

## What was done

Two changes to `spawn.py`, one to `roster.py`, plus one live operational
action against the real state file.

canonical: `git diff HEAD -- spawn.py roster.py` (this checkout, this
session) — the full diff; summarized below, not paraphrased beyond
locating call sites.

1. **`spawn.py:_record_spawn_attempt()`** (spawn.py:901) — added a guard:
   if `os.environ.get("PYTEST_CURRENT_TEST")` is set, the function
   returns `None` without writing to `runs/spawn-attempts.jsonl`. Both
   call sites that consume the returned `attempt_id` (spawn.py:1728 and
   spawn.py:2643) already guard on `if attempt_id is not None`, so no
   other code needed to change — verified by reading both sites in this
   session before making the change.
2. **`spawn.py:_prune_spawn_attempts()`** (new, spawn.py, after
   `_load_spawn_attempts()`) — rewrites `SPAWN_ATTEMPTS_PATH`, keeping:
   attempts with no outcome yet recorded (always), `"halted"`-outcome
   attempts younger than `SPAWN_ATTEMPTS_RETENTION_SEC` (7 days, same
   value as `roster.APPROVAL_WAIT_LEDGER_TTL_SEC`), and dropping
   `"session-log"` outcomes immediately. Only rewrites the file when
   something is actually droppable.
3. **`roster.py:spawn_attempt_sweep()`** (roster.py:494, end of the
   function) — calls `_sp._prune_spawn_attempts(now=now)` once per sweep.
4. **One-time historical cleanup** of the live
   `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl`
   (the canonical checkout's real state file — not a path in this repo
   checkout): backed up first, then rewrote it dropping every record
   whose `issue` field is `31` or `7`.

acceptance: `cp` the live file to a sibling `.bak-issue-2393-20260825T094422Z`,
then a `python3 -c "..."` script filtering out `issue in (31, 7)` and
rewriting atomically (`os.replace`) — result:

```
total before: 341
dropped: 300 {31: 232, 7: 68}
kept: 41
rewrote /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl
```

derived: 341 (before) is more than the issue's reported 285 because real,
unrelated concurrent sessions on this host kept appending to the shared
live file while this session worked — confirmed immediately before this
prune by re-reading the same file with a per-issue tally (see `## Why`,
last paragraph, for why age-based rotation alone can't reach these
records and a one-time filter was required).

## Why

**Decision (acceptance bullet 1): not recorded at all, via a
`PYTEST_CURRENT_TEST` guard at the point of writing — not a marker + a
watchdog-side filter, and not per-test-file isolation.**

Rejected alternatives:
- **Marker + watchdog-side filter** (tag the record, teach
  `spawn_attempt_sweep()` to skip tagged records): more moving parts than
  needed for zero informational value — a test-suite halt is already
  visible in pytest's own failure output, so there is nothing the durable
  trace adds for a test-origin attempt. A marker is the right shape when
  the record is worth keeping but shouldn't count toward reporting, which
  is not the case here.
- **Per-test-file isolation** (the codebase's existing convention —
  canonical: `tests/_spawn_test_support.py`'s `isolated_role_model_config()`,
  read in this session, patches a shared-state path to a private tmp dir
  per test — the precedent initially expected to apply here): rejected
  after finding the actual write path (`## What did not work` below).
  Patching call sites is fragile against *future* tests: any new test
  that calls `spawn.main()`/`_spawn_one()` with an `--issue`/`issue=`
  value and forgets the isolation helper reproduces this exact flood
  again — the recurrence this issue exists to close off. A guard in the
  one function that actually writes needs no test author to remember
  anything, present or future.

`PYTEST_CURRENT_TEST` (not e.g. `"pytest" in sys.modules`) because it is
scoped to the *execution* of a test — set only while a test is actually
running, including per-xdist-worker, per pytest's own documented
behavior — not merely "pytest is importable", so a hypothetical real
`spawn.py spawn` CLI invocation launched from a pytest-managed
environment (outside a test's own execution window) would not be
mis-suppressed; only invocations pytest itself is actively driving are.

**Rotation policy (acceptance bullet 4 — R8 Surface from #2291's
conformance review, "this file has no rotation today"):** mirrors
`spawn_attempt_sweep()`'s own reporting rules (canonical: roster.py:435-494,
`spawn_attempt_sweep()`, read in this session) instead of a flat age
cutover, because a flat cutoff would either drop attempts the sweep still
needs (unresolved ones — a delayed halt would go undetected) or keep
attempts the sweep will never look at again — `"session-log"` outcomes
are filtered out by `spawn_attempt_sweep()`'s own
`if outcome.get("outcome") != "halted": continue` (roster.py:472) and are
never reported, so there is no reason to hold onto them once recorded.
`"halted"` outcomes are kept for a retention window because
`spawn_attempt_sweep()`'s ledger dedup (`ledger_check_and_stamp`,
roster.py:486) is a *recurring* reminder — it re-surfaces after its TTL
window, not once-and-done — so pruning a halted record right after its
first report would silently kill that recurring reminder while the
underlying halt might still be live. 7 days reuses
`roster.APPROVAL_WAIT_LEDGER_TTL_SEC`'s existing convention (roster.py:504)
for how long an operational trace file with a TTL-gated advisory stays
before it ages out.

**Why the one-time cleanup can't rely on the new rotation policy:** the
existing junk records are *unresolved* — the tests that produced them
mock out `_spawn_one` (or everything downstream of it) before it ever
reaches the point that calls `_record_spawn_outcome()`, so no outcome is
ever recorded for them.

acceptance: `python3 -c "..."` tallying resolved vs unresolved attempts
by issue number, against the live file before the historical prune —
result:

```
resolved by issue: {2293: 1, 2286: 3, 304: 2, 2348: 6, 2383: 4, 2393: 1, 2382: 2, 2395: 1}
unresolved by issue: {31: 232, 7: 68, 2395: 1}
```

derived: every one of the 232 issue-31 and 68 issue-7 attempts above is
unresolved (0 appear in the resolved tally), confirming the rotation
policy's "always keep unresolved" rule would never age these out — hence
the explicit one-time filter by issue number instead.

## What did not work

- Initially expected the fix to center on the four call sites the issue
  cited (`tests/test_auto_sweep_nonblocking.py:94,159`,
  `tests/test_admission_checklist.py:390`, `tests/test_spawn_pipeline.py:1215`,
  `tests/test_spawn_board_flows.py:103`) — read all four in this session
  and found they all call `spawn._spawn_one()` directly without passing
  `attempt_id`.

  canonical: `grep -rn "_record_spawn_attempt(" --include=*.py .` (this
  checkout, this session) — result:

  ```
  spawn.py:901:def _record_spawn_attempt(issue: int | None, role: str, pid: int) -> str:
  spawn.py:1695:    attempt_id = (_record_spawn_attempt(a.issue, a.role, os.getpid())
  spawn.py:2091:    작업 전에 이미 `_record_spawn_attempt()`로 남긴 durable 시도 id — 세션
  roster.py:441:    `_record_spawn_attempt()`/`_record_spawn_outcome()` now append that
  ```

  derived: `_record_spawn_attempt()` has exactly one caller in the whole
  repo — `main()` at spawn.py:1695. derived: so the four cited test call
  sites (all `_spawn_one()` direct calls, none going through `main()`)
  structurally cannot write to `spawn-attempts.jsonl`; the issue's
  citations were evidence that those specific numbers are fixture
  values, not a pointer to the write path.

  acceptance: reproduced against an isolated `MUSTER_STATE_ROOT`, running
  only `tests/test_auto_sweep_nonblocking.py` and
  `tests/test_admission_checklist.py` (two of the four cited files) —
  result:

  ```
  34 passed in 7.75s
  --- records after BEFORE-fix suite run (fast subset) ---
  wc: /tmp/otr-2393-demo/isolated-state/spawn-attempts.jsonl: 그런 파일이나 디렉터리가 없습니다
  ```

  derived: zero records written — confirms these files are not the write
  path. Broadening the search across every test file calling
  `spawn.main()` for real found the actual source:
  `tests/test_default_single_phase_flip.py` (module constant `_ISSUE =
  31`, real role `"implementation"`, calls the real `spawn.main()` with
  only `_spawn_one` mocked, so the real attempt-recording code inside
  `main()` runs) and `tests/test_checkpoint_mode.py` (same shape,
  `_ISSUE = 7`).

  acceptance: same isolated `MUSTER_STATE_ROOT`, running
  `tests/test_default_single_phase_flip.py tests/test_checkpoint_mode.py`
  against the pre-fix code (`git stash push --keep-index -- spawn.py
  roster.py`) — result:

  ```
  25 passed in 2.61s
  --- records after BEFORE-fix (unfixed spawn.py) run ---
  7 /tmp/otr-2393-demo/isolated-state/spawn-attempts.jsonl
  Counter({31: 5, 7: 2})
  ```

  derived: 7 records total — 5 for issue 31 and 2 for issue 7, from
  exactly these two files — this is the actual reproduction of the
  flood, and it also validates why a centralized guard (not per-file
  patches naming the issue's four citations) was the right call: the
  offending call sites were not the ones a surface reading of the issue
  text would suggest.

## Upstream basis

`docs/issue-2291/reports/implementation.md` @ `75390fc383bd5138d2ed34c80dd6b0422500dde1`
— the durable spawn-attempt trace and `spawn_attempt_sweep()` this
issue's fix modifies, including its own R8 conformance-review note
(quoted in `## Why` above) proposing exactly the rotation shape
implemented here.

canonical: `git log --format="%H" -1 -- docs/issue-2291/reports/implementation.md`
(this checkout, this session) — result: `75390fc383bd5138d2ed34c80dd6b0422500dde1`.

## Open findings

- R7 (#2291's own conformance review: "`--issue`-less ad-hoc spawns get
  no durable trace/watchdog visibility") remains open — out of scope for
  this issue, unrelated to the test-noise problem #2393 addresses.
  canonical: docs/issue-2291/reports/implementation.md:161-168, read in
  this session.
- A backup of the live state file
  (`spawn-attempts.jsonl.bak-issue-2393-20260825T094422Z`, sibling to
  `spawn-attempts.jsonl` in the canonical checkout's `runs/`) is left in
  place as a one-time safety copy of the pre-prune state — not part of
  any rotation policy, left for manual review/deletion.

## Next steps

None — `loop_state: landed`.

## Acceptance evidence

Environment note: this worktree is not the canonical `on-the-record`
checkout, so `spawn.py watchdog` needed `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1`
to run at all below — a pre-existing, unrelated guard (issue #1456).
canonical: watchdog output naming this guard, quoted verbatim in this
session's own terminal capture before the override was set.

**Bullet 1 — decided approach:** see `## Why` above.

**Bullet 2 — before/after, test suite -> watchdog tick, measured.**
Reproduced the flood against an isolated `MUSTER_STATE_ROOT`
(`/tmp/otr-2393-demo/isolated-state`, outside this checkout and outside
the canonical checkout) using the two offending test files found above,
then called the actual `roster.spawn_attempt_sweep()` — the function
`watchdog.py`'s real tick calls — before and after the fix, toggling via
`git stash push --keep-index -- spawn.py roster.py` / `git stash pop` in
this same checkout.

acceptance: BEFORE (fix stashed out) — `python3 -m pytest
tests/test_default_single_phase_flip.py tests/test_checkpoint_mode.py -q`,
then `python3 -c "import time, spawn, roster; roster.spawn_attempt_sweep(now=time.time()+400)"` —
result:

```
25 passed in 2.61s
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432481) — process likely died before it could report why
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432481) — process likely died before it could report why
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432485) — process likely died before it could report why
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432485) — process likely died before it could report why
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432505) — process likely died before it could report why
[spawn-attempt] issue-7/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432508) — process likely died before it could report why
[spawn-attempt] issue-7/implementation: spawn halted pre-workspace: no outcome recorded 418s after spawn attempt (pid 2432543) — process likely died before it could report why
BEFORE-FIX simulated tick, reports: 7
```

acceptance: AFTER (fix restored via `git stash pop`, fresh state dir) —
same two commands — result:

```
25 passed in 2.65s
wc: /tmp/otr-2393-demo/isolated-state/spawn-attempts.jsonl: 그런 파일이나 디렉터리가 없습니다
AFTER-FIX simulated tick, reports: 0
```

derived: reports dropped from 7 (before) to 0 (after) for the identical
test run. A future-timestamp simulated tick (`now=time.time()+400`)
substitutes for a real 300s+ wait, since `SPAWN_ATTEMPT_GRACE_SEC` and
the ledger dedup window are not env-overridable — it calls the exact
same `spawn_attempt_sweep()` function the real watchdog tick calls, with
nothing else substituted.

**Bullet 3 — genuine pre-workspace halt still reported, live forced
halt (not a code read):**

acceptance: `python3 spawn.py implementation "test task" --issue 999001
-C /tmp/otr-2393-demo/no-board-repo --unattended` against a real git repo
with no board file, `PYTEST_CURRENT_TEST` unset (real, non-test CLI
invocation) — result:

```
대상 레포에 docs/specs/approvers.md 가 없다: /tmp/otr-2393-demo/no-board-repo
  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:
    python3 spawn.py init -C /tmp/otr-2393-demo/no-board-repo
  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.
```

acceptance: `cat "$MUSTER_STATE_ROOT/spawn-attempts.jsonl"` immediately
after — result:

```
{"event": "spawn_attempt", "attempt_id": "999001:implementation:2445662:1787651014868", "issue": 999001, "role": "implementation", "pid": 2445662, "ts": 1787651014.8689508}
{"event": "spawn_attempt_outcome", "attempt_id": "999001:implementation:2445662:1787651014868", "outcome": "halted", "detail": "대상 레포에 docs/specs/approvers.md 가 없다: /tmp/otr-2393-demo/no-board-repo\n  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:\n    python3 spawn.py init -C /tmp/otr-2393-demo/no-board-repo\n  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.", "ts": 1787651014.869085}
```

acceptance: `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py
watchdog -C /tmp/otr-2393-demo/no-board-repo` (real watchdog CLI, same
`MUSTER_STATE_ROOT`) — result:

```
[spawn-attempt] issue-999001/implementation: spawn halted pre-workspace: 대상 레포에 docs/specs/approvers.md 가 없다: /tmp/otr-2393-demo/no-board-repo
```

derived: a real, non-test halt (issue 999001 — not a synthetic
test-fixture number, run with `PYTEST_CURRENT_TEST` unset) is recorded
and reported by the real `spawn.py watchdog` CLI — the fix distinguishes
test-origin from genuine.

**Bullet 4 — junk records pruned:** derived: see `## What was done` (4)
for the fenced `341 -> 41` prune output (300 dropped) and `## Why` for
the fenced resolved/unresolved tally explaining why the ongoing rotation
could not have done this automatically.

**Prune-policy unit check** (unresolved kept regardless of age,
`"session-log"` dropped immediately, `"halted"` kept within the 7-day
window and dropped past it):

acceptance: `python3 -c "..."` building four synthetic events (one of
each case: unresolved/old, resolved-session-log/old,
resolved-halted/recent, resolved-halted/8-days-old) and calling
`spawn._prune_spawn_attempts(now=now)` — result:

```
dropped: 4
remaining ids: ['a1', 'a3']
OK — matches expected policy (unresolved kept, session-log dropped immediately, halted kept within 7d, halted dropped past 7d)
```

derived: `a1` (unresolved) and `a3` (halted, recent) are the two events
constructed to survive; `a2` (session-log) and `a4` (halted, 8 days old)
are the two constructed to be dropped — the script's own assertion
(`assert remaining_ids == {'a1','a3'}`) did not raise, and its
`print("OK — ...")` line only executes after that assertion holds.

**Regression check** — full command:
`python3 -m pytest tests/test_default_single_phase_flip.py
tests/test_checkpoint_mode.py tests/test_auto_sweep_nonblocking.py
tests/test_admission_checklist.py tests/test_spawn_directive_assembly.py
tests/test_watchdog_freshness.py tests/test_watchdog_heartbeat_noise.py
tests/test_watchdog_local_signals.py tests/test_poll_watchdog_log.py -q`
(fix applied, default `MUSTER_STATE_ROOT`, this checkout) — result:

```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed, 131 passed in 28.78s
```

The one failure asserts `CORE_BUILD_NOW` is absent from a captured
child-process env, but this session's own environment carries
`CORE_BUILD_NOW=1` (this is a build-now delivery, contract v3 s19a) and
leaks into the real, unmocked `Popen` that test drives.

acceptance: same single test, `spawn.py`/`roster.py` stashed back to
pre-fix (`git stash push --keep-index -- spawn.py roster.py`) — result:

```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed in 20.05s
```

derived: identical failure before this session's fix — pre-existing,
unrelated to `spawn-attempts.jsonl`/watchdog reporting. `git stash pop`
immediately after restored the fix (confirmed via `git status
--porcelain` showing `spawn.py`/`roster.py` modified again, in this
session).

**Warrant hunt** (before-landing, stance 0 — "assume the gate just
touched is bypassable, find the bypass" — no prior `.warrant-hunt.count`
in this checkout or the canonical checkout, so dispatch count 0):
dispatched a `warrant:warrant-hunter` subagent (foreground, consumed in
this same turn per contract v3 s22's headless override) specifically
against the `PYTEST_CURRENT_TEST` guard — could a real spawn ever inherit
a stale `PYTEST_CURRENT_TEST` and go unrecorded?

canonical: this session's own before-landing hunter dispatch, its full
returned text quoted verbatim below (not paraphrased):

```
NO FINDING (stance: assume the gate just touched is bypassable — find the bypass)

I traced every path that can reach spawn.py's new _record_spawn_attempt() guard
(os.environ.get("PYTEST_CURRENT_TEST") is not None): the CLI entrypoint main()
(spawn.py:1771, sole caller), the auto-respawn path (lifecycle._respawn_or_cap()
-> _spawn_one() at lifecycle.py:469, which never passes attempt_id at all, so it
bypasses the guard's whole function structurally regardless of this diff), the
auto-armed watcher (spawn.py:2783, events.py:900, which never re-invokes
spawn.py spawn), and the real claude child Popen (spawn.py:2848-2850, which does
inherit the orchestrator's env). The only theoretically concerning chain -- a
real, unmocked claude child inheriting a stale PYTEST_CURRENT_TEST and later
performing its own genuine nested spawn -- has no actual trigger in this repo:
every test that drives _spawn_one()/main() mocks spawn.subprocess.Popen before
reaching the real child process (checked test_spawn_pipeline.py,
test_admission_checklist.py, test_spawn_board_flows.py), so no unmocked child
process exists in the suite that could carry the var forward. gates/test_*.py
scripts do run pytest.main() for real gate checks but don't dispatch spawns
through the guarded function, and pytest.main() cleans up the env var per-test
regardless.

No reproducible command exists that sets PYTEST_CURRENT_TEST in a genuinely
real (non-test) spawn.py spawn invocation's own environment, so per the
reproduction requirement this is NO FINDING.
```

## skill-verdict

skill-verdict: work-in-english — applied: invoked; loaded SKILL.md before
landing (session context and directives were Korean) — this record and
the commit message are in English; new code comments in spawn.py/roster.py
stayed Korean to match this project's existing per-file convention (the
skill's own guard: match surrounding style, never leave a file
half-and-half), and this repo's commit-message history is already
English (no project-convention conflict to flag).
other mounted skills: not triggered — pure bugfix/rotation-policy fix
with no cross-module coupling threshold crossed, no GoF pattern decision,
no data-structure/perf tradeoff, and no multi-module architecture
requiring the blueprint classify step (single coherent change to two
already-related modules, spawn.py and its own roster.py extraction).
