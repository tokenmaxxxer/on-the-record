---
issue: 2393
role: execution-observation
author: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2393/reports/implementation.md
    sha: 512eec2c1179a572e5b8818a484894bbd3ce678e
  - path: spawn.py
    sha: 512eec2c1179a572e5b8818a484894bbd3ce678e
  - path: roster.py
    sha: 512eec2c1179a572e5b8818a484894bbd3ce678e
subject: PR #2400 (issue-2393/implementation, "skip pytest-origin
  spawn-attempt records, rotate + prune the trace"), commits
  f6487073/512eec2c (HEAD), branch issue-2393/implementation, checked out
  into an independent git worktree at /tmp/pr2400-src (untracked in this
  tree, removed after this observation)
test: independent re-execution of all four of issue #2393's Acceptance
  bullets, plus the record's regression-check and prune-policy unit
  check, from a fresh worktree checkout of the PR branch and fresh
  isolated MUSTER_STATE_ROOT scratch dirs this session created,
  independent of the PR's own pasted output
result: passed
assertedBy: execution-observation session for issue-2393, independent of
  PR #2400's authoring (implementation) session
---

# issue-2393 — execution-observation record

## What was done

canonical: `git fetch origin pull/2400/head:pr-2400-check && git worktree
add /tmp/pr2400-src pr-2400-check` — an independent checkout of the PR's
`spawn.py`/`roster.py` change, never the PR's pasted transcripts taken as
given. Re-executed each of issue #2393's four Acceptance bullets
independently.

### Bullet 1 — decided approach, stated in the record

canonical: `sed -n '901,924p' spawn.py` (PR worktree, this session) —
read the `_record_spawn_attempt()` docstring directly, and the
implementation record's own `## Why` section: both state the approach
(`PYTEST_CURRENT_TEST` guard, not-recorded-at-all, not a marker) and the
rejected alternatives (marker + watchdog filter; per-test-file
isolation) with reasons for each. This bullet is a documentation
requirement, not an executable one; satisfied by direct read, no
re-derivation needed.

### Bullet 2 — before/after, test suite → watchdog tick, zero new reports

Reproduced independently, not by re-running the PR's own pasted
transcript: checked out the pre-fix parent commit's `spawn.py`/`roster.py`
(`git checkout ce7fadd7 -- spawn.py roster.py`, the commit immediately
before `f6487073`) into the same PR worktree, with a fresh
`MUSTER_STATE_ROOT` scratch dir this session created.

canonical: `python3 -m pytest tests/test_default_single_phase_flip.py
tests/test_checkpoint_mode.py -q` (pre-fix code) then `python3 -c
"import time, spawn, roster; roster.spawn_attempt_sweep(now=time.time()+400)"`
— result:

```
25 passed in 2.64s
--- spawn-attempts.jsonl after BEFORE run ---
7 /tmp/eo-2393-state-before/spawn-attempts.jsonl
Counter({31: 5, 7: 2})
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: ...
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: ...
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: ...
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: ...
[spawn-attempt] issue-31/implementation: spawn halted pre-workspace: ...
[spawn-attempt] issue-7/implementation: spawn halted pre-workspace: ...
[spawn-attempt] issue-7/implementation: spawn halted pre-workspace: ...
BEFORE-FIX simulated tick, reports: 7
```

derived: exact match to the record's own BEFORE evidence — same 5+2
split by issue, same 7 reports.

canonical: `git checkout pr-2400-check -- spawn.py roster.py` (restoring
the fix, fresh scratch state dir), same two commands — result:

```
25 passed in 2.53s
wc: /tmp/eo-2393-state-after/spawn-attempts.jsonl: 그런 파일이나 디렉터리가 없습니다
AFTER-FIX simulated tick, reports: 0
```

derived: 7 to 0, independently reproduced. `spawn-attempts.jsonl` is
never created (no test-origin attempt is ever written), so the watchdog
tick has nothing to report.

### Bullet 3 — genuine pre-workspace halt still reported, live forced halt

canonical: `git init -q /tmp/eo-2393-no-board-repo` (fresh scratch repo,
no `docs/specs/approvers.md`), `PYTEST_CURRENT_TEST` unset, then
`python3 spawn.py implementation "eo-2393 forced halt test" --issue
888777 -C /tmp/eo-2393-no-board-repo --unattended` — a different issue
number than either the record's own live-halt demo or the two
test-fixture numbers, chosen specifically to rule out any
issue-number-based special-casing in the guard — result:

```
대상 레포에 docs/specs/approvers.md 가 없다: /tmp/eo-2393-no-board-repo
  이 파일이 보드 opt-in 이자 승인자 allowlist 다. ...
```

canonical: `cat "$MUSTER_STATE_ROOT/spawn-attempts.jsonl"` — result: both
`spawn_attempt` and `spawn_attempt_outcome` (`"outcome": "halted"`)
events present for `888777:implementation:...`.

canonical: `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py
watchdog -C /tmp/eo-2393-no-board-repo` (real watchdog CLI entry point,
not the `roster.spawn_attempt_sweep()` function call used for bullet 2)
— result:

```
[spawn-attempt] issue-888777/implementation: spawn halted pre-workspace: 대상 레포에 docs/specs/approvers.md 가 없다: ...
```

derived: a genuine, non-test halt is recorded and reported end-to-end
through the real CLI, independently confirming both the write path and
the full `spawn.py watchdog` report path stay live for real halts.

### Bullet 4 — junk records pruned, rotation policy stated

**Rotation policy, independently re-verified by direct execution, not by
trusting the record's pasted script output:** canonical: built four
synthetic events (unresolved/old, resolved-session-log/old,
resolved-halted/recent, resolved-halted/8-days-old) against a fresh
scratch `MUSTER_STATE_ROOT` and called `spawn._prune_spawn_attempts(now=now)`
directly — result:

```
dropped: 4
remaining ids: ['a1', 'a3']
OK -- independent prune-policy check matches expected: a1(unresolved) and a3(halted, recent) kept; a2(session-log) and a4(halted, 8d old) dropped
```

derived: matches the record's own unit-check claim exactly, reproduced
with this session's own synthetic fixture rather than the record's
script text.

**Wiring — `roster.py`'s sweep calls the pruner every tick:** canonical:
`grep -n "_prune_spawn_attempts" roster.py spawn.py` (PR worktree) —
`roster.py:498` calls `_sp._prune_spawn_attempts(now=now)` at the end of
`spawn_attempt_sweep()`; `spawn.py:97` re-exports
`spawn_attempt_sweep = roster.spawn_attempt_sweep`, the same function
already exercised live for bullet 3's watchdog CLI run above — the
pruner sits on the real tick path, not a dead call.

**Historical one-time cleanup — the stated prune from 341 to 41 lines is
real, checked against the actual filesystem, but the live file has since
regrown:** canonical: `ls
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl*`
— result: both the current file and a
`spawn-attempts.jsonl.bak-issue-2393-20260825T094422Z` backup exist,
confirming the one-time prune ran as claimed and left the stated safety
copy.

canonical: a per-issue tally of the live file, this session, independent
of the record's own pasted tally — result:

```
357 lines total
Counter: {31: 210, 7: 86, 2348: 7, 2383: 6, 2395: 4, 2286: 3, 2393: 3, 304: 2, 2382: 2, 320: 2, ...}
```

derived: the live file has grown back well past the 41 lines the
one-time prune left it at, with issue 31 and issue 7 the dominant
contributors again. canonical: `git -C
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/ log --oneline -1`
— result: that checkout (the one that actually produces the live state
file) is at `6b94abf8` ("issue-2383: consult-trace"), which predates and
does not include `f6487073`/`512eec2c` — PR #2400 is unmerged there.
canonical: `grep -n PYTEST_CURRENT_TEST spawn.py` against that checkout —
result: no matches. derived: the regrowth is other concurrent sessions
on this host continuing to run the test suite against the unfixed
canonical checkout, which has no guard yet — expected given the fix has
not merged, not a defect in this PR's diff, and not evidence the guard
fails once deployed (bullet 2's fresh-worktree reproduction above shows
the guard works when the fixed code actually runs). Recorded as an Open
finding below since a future reader of the live file before merge could
otherwise mistake the regrowth for the fix not working.

### Regression check — reproduced exactly, including the ambient-env failure

canonical: `python3 -m pytest tests/test_default_single_phase_flip.py
tests/test_checkpoint_mode.py tests/test_auto_sweep_nonblocking.py
tests/test_admission_checklist.py tests/test_spawn_directive_assembly.py
tests/test_watchdog_freshness.py tests/test_watchdog_heartbeat_noise.py
tests/test_watchdog_local_signals.py tests/test_poll_watchdog_log.py -q`
(fixed code, fresh `MUSTER_STATE_ROOT`, PR worktree) — result:

```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed, 131 passed in 2.15s
```

derived: same file and same counts as the record's own Executed
evidence. The failing test lives in `tests/test_spawn_directive_assembly.py`
(exists in this repo); the failing test case itself is
`SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`, a
pytest node id, not a filesystem path.

canonical: `env -u CORE_BUILD_NOW python3 -m pytest
tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
-q` — result:

```
1 passed in 1.14s
```

derived: confirms the failure is caused by this session's own ambient
`CORE_BUILD_NOW=1`, not this PR's diff. canonical: `git checkout ce7fadd7
-- spawn.py roster.py` (pre-fix code, `CORE_BUILD_NOW` still set), same
single test — result:

```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
1 failed in 1.06s
```

derived: identical failure on pre-fix code — confirms the failure
predates this PR's change and is unrelated to it, matching the record's
claim and the `docs/reports/deviation-log.md` 2026-08-25T10:03:37Z entry.
canonical: `git checkout pr-2400-check -- spawn.py roster.py` restored
the fix immediately after, confirmed via `git status --porcelain`
(clean) in this session.

## Why

Delegated scope was re-execution of the acceptance's "executed-live"
provenance requirement for all four named bullets, not re-derivation of
new design claims — same posture prior execution-observation records for
this issue family have taken
([[defect-verification-independence-from-upstream-verdicts]]). Bullet 2
and bullet 3 are the two claims a code read alone cannot stand in for
(both are behavioral, before/after and live-process claims), so both
were run from a fresh worktree and fresh scratch state directories this
session created, rather than trusting the record's own pasted terminal
output. Bullet 3's live halt used a distinct issue number specifically
to rule out any number-based special-casing in the guard — see Bullet 3
above for the literal command and output. The live-file regrowth
investigated in Bullet 4 above was not taken as a red flag at face
value, because the acceptance's own bullet 4 only requires the existing
junk be pruned and a rotation policy stated — not that the canonical
checkout be permanently immune to regrowth before the fix is merged
there, which is outside this PR's diff. derived: see Bullet 4 above
(`git -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/ log
--oneline -1`, run this session) for the command and output backing that
conclusion.

## Upstream basis

- `docs/issue-2393/reports/implementation.md`, untracked in this
  tree — lives on branch `issue-2393/implementation` at commit
  `512eec2c1179a572e5b8818a484894bbd3ce678e`, PR #2400 — the record
  whose Acceptance/Executed-evidence this session re-executed; quoted and
  compared inline above.
- `spawn.py`/`roster.py` at the same commit (PR worktree, same branch) —
  the `_record_spawn_attempt()` guard, `_prune_spawn_attempts()`, and
  `spawn_attempt_sweep()` wiring this session ran directly.
- `docs/issue-2348/reports/execution-observation.md`, this tree — prior
  execution-observation of a related PR in this same lineage; this
  observation's method (independent worktree, before/after via parent
  commit checkout, fresh scratch state dirs) follows its precedent.

## Open findings

- Informational, not a defect in PR #2400's diff: the live
  `spawn-attempts.jsonl` state file that the canonical
  `tokenmaxxxer` plugin checkout produces has continued growing past the
  implementation record's one-time prune point, because that canonical
  checkout has not merged PR #2400 and so still lacks the
  `PYTEST_CURRENT_TEST` guard — other concurrent sessions on this host
  keep running the test suite against that unfixed checkout. derived:
  see Bullet 4 above for the exact tally command, output, and the
  canonical checkout's HEAD commit confirming it predates this PR.
  Resolution path: none needed against this PR — this self-resolves once
  #2400 merges and the canonical checkout picks it up; noted here only
  so a future reader checking the live file before merge does not
  mistake ongoing regrowth for the guard failing (this session's own
  fresh-code reproduction in Bullet 2 above shows the guard does work
  once the fixed code actually runs).

## Next steps

None — `loop_state` above is this record kind's terminal value,
`handed-off`.
