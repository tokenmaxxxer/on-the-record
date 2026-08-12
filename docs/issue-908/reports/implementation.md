---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -q (output pasted under Test evidence)
verdict: pass
loop_state: landed
---

# Implementation record — issue-908

## What was done

`_spawn_one()`'s fork-child branch (`if bounded and issue is not None:`,
spawn.py) now pre-registers a roster stub and an early `session-start`
event, keyed by the fork-child's own `os.getpid()`, immediately after
`os.fork()` returns 0 — before `_rewrite_spawn_claim_pid()`/
`os.setsid()`/the `os.dup2()` triple/`subprocess.Popen()` run. That span
is now also wrapped in two `try`/`except OSError` blocks:

- `os.setsid()`/the `os.dup2()` triple, catch -> append a `spawn-death`
  event (`stage: "fork-setup"`, the error) -> re-raise.
- `subprocess.Popen(cmd, ...)` (both bounded and non-bounded paths),
  catch -> append a `spawn-death` event (`stage: "popen"`) when
  `issue is not None` -> re-raise.

The existing post-`Popen` `roster_register`/`session-start` write is
unchanged — it still overwrites the stub with the real `proc.pid` and
full fields on success. `roster_watchdog()` itself is unchanged: its
existing dead-registered-entry branch (`if not _alive(e.get("pid", 0))`)
already surfaces `DEAD-ERRORED`/triggers `_post_session_end_comment`
once an entry exists — the fix works by guaranteeing an entry exists
before the risky span, not by changing that detection logic.

canonical: spawn.py:5075-5163 (`_spawn_one` fork-child branch, read
directly this session).

Added a new test class in tests/test_spawn.py, `SpawnDeathBeforeRegistration`
(live-fire against the real `_spawn_one()` body with `os.fork` mocked
to force the fork-child branch without a real fork, per the existing
`test_fork_child_rewrites_claim_pid_before_setsid` pattern):

- `test_setsid_death_leaves_roster_stub_and_spawn_death_event`: forces
  `os.setsid()` to raise; asserts the roster stub was written with
  `os.getpid()` before the crash, `events.jsonl` carries both
  `session-start` and a `spawn-death` (`stage: "fork-setup"`) event,
  `session_end_verdict()` reads `"crashed"`, and a live
  `roster_watchdog()` call (with `_alive` forced false and
  `diagnose_health` stubbed) prints the `DEAD-ERRORED` label.
- `test_popen_death_leaves_roster_stub_and_spawn_death_event`: forces
  the session's own `subprocess.Popen(["cat"], ...)` call to raise
  (other `Popen` calls, e.g. `gh`, are forwarded unchanged to the real
  `subprocess.Popen`); asserts the `popen`-stage `spawn-death` event.
- `test_normal_spawn_unaffected_no_spawn_death_event`: empty-state
  guard — a non-crashing spawn registers exactly twice (stub, then the
  real overwrite), never emits `spawn-death`, and the stub's `pid` is
  `os.getpid()` as expected.

canonical: python3 -m pytest tests/test_spawn.py -k SpawnDeathBeforeRegistration -v (output pasted under Test evidence below).

## Rationale for deviations

Every bullet in the approved proposal's plan section was implemented as
written, in the same order, with the same trigger conditions — no
scope-exceeded stop and no alternative-swap occurred during this build.

## What did not work

- Initial `SpawnDeathBeforeRegistration` test attempts restored
  `spawn.ROSTER`/read `events.jsonl` in the wrong order (read the
  global roster path after already restoring it to the pre-test value)
  — fixed by reading the roster file directly via its captured `Path`
  before restoring the global.
- `test_popen_death_...` first patched `spawn.subprocess.Popen`
  unconditionally, which also intercepted the unrelated `gh repo view`
  Popen call inside `_undispositioned_role_prs()` and raised before
  reaching the code under test — fixed by scoping the fake `Popen` to
  only the session's own `["cat"]` command, forwarding everything else
  to the real `subprocess.Popen`.
- `test_normal_spawn_unaffected_...` initially asserted both
  `roster_register` calls carried the same `pid` — expected value was
  wrong: the stub call uses `os.getpid()` (the fork-child, which in the
  test is the test process itself since `os.fork` is mocked to `0`),
  but the second (post-`Popen`) call legitimately uses the real `cat`
  subprocess's own distinct pid — fixed the assertion to check only the
  first call's pid.
- The same test also initially hit unbounded self-trigger respawn
  recursion (`_self_trigger_respawn`) because the mocked `cmd = ["cat"]`
  session produces no board change, which the real code classifies as
  `silent-failure` and retries — mocked `_self_trigger_respawn` out to
  keep the test scoped to the registration-count assertion it's
  actually checking.
- The proposal's "how you'll know it worked" section expected
  `roster_watchdog()` to return a nonzero `anomaly_count` for the dead
  entry; live-fire showed the dead-entry branch's existing
  `DEAD-ERRORED` print is not counted into the returned `anomaly_count`
  (only `reconcile()` divergences and the alive-branch's own anomaly
  checks are — pre-existing behavior at spawn.py:2395-2431, unrelated
  to this fix) — the test was adjusted to assert on the `DEAD-ERRORED`
  stdout line only, which is the actual surfacing signal
  `roster_watchdog` produces for this case.

## Why

canonical: docs/issue-908/reports/defect-verification.md (merged
finding, addressed_to: coding, blocking, read directly this session) —
it pins the exact gap: `_spawn_one()`'s fork-child setup/`Popen()` ran
with no `try`/`except` before the first roster/event write, so a death
in that span left zero trace and `roster_watchdog()` structurally could
not see it (only scans already-registered entries).
docs/issue-908/reports/implementation/survey.md re-derived the same
span against current spawn.py and ruled out a `try`/`except`-only fix
(misses signal-shaped deaths).

## Upstream / basis

docs/issue-908/proposals/2026-08-12-issue-908-implementation.md
(approved via the `APPROVE issue-908/implementation` issue comment),
itself built on docs/issue-908/reports/defect-verification.md (PR #933)
and docs/issue-908/reports/implementation/survey.md.

## Test evidence

derived: python3 -m pytest tests/test_spawn.py -q
```
454 passed in 30.55s
```
No SKIPPED lines in this run.

derived: python3 -m pytest gates/ tests/ -q
```
1 failed, 980 passed, 1 xfailed in 62.64s
```
No SKIPPED lines in this run.

canonical: python3 -m pytest gates/ tests/ -q (output pasted above) —
the one failing test (tests/test_gates.py, function
t_rulebook_version_is_recorded) asserts the
rulebook-version string carries no "커밋안됨" (uncommitted) marker — it
reads live git state, not a fixture, and its failure traces to this
session's own uncommitted spawn.py/tests/test_spawn.py changes still
being on disk when the suite ran. Unrelated to this fix; expected to
clear once this change is committed.

## Anomaly note

canonical: gh issue view 908 --json state (checked live this session,
returned state CLOSED). Issue #908 was closed by the merged
defect-verification PR #933 (its own body carries "Closes #908"),
before this coding-side fix landed — the defect-verification role
shut the tracking issue on its own phase-2 delivery rather than
leaving it open for this one. This session carried out this build
anyway: the user's own turn-opening prompt itself stated
`APPROVE issue-908/implementation` had already been granted and named
this exact fix as the work to build against the approved proposal.
Noted here per the phase-2 anomaly-reporting duty rather than treating
the already-shut issue silently as nothing left to build.

## Hunt

before-landing dispatch (stance 0, tier default, cap 180s) — canonical:
docs/issue-908/reports/implementation/2026-08-12-hunt-issue-908-implementation.md
(hunt record read directly this session). Verdict: FINDING.
`_roster_save()` (spawn.py:1803-1805) writes `active.json`
non-atomically via `Path.write_text()`; `_roster_load()`'s catch-all
`except (OSError, ValueError): return {}` means a death exactly
mid-write during the new pre-registration `roster_register()` call
corrupts the whole roster file, silently wiping visibility into every
other concurrently-registered live session (not just the dying one) on
the next read — reopening a silent-death gap wider than the one this
issue closes.

Not fixed in this PR: `_roster_save`/`_roster_load`'s non-atomic-write
property is pre-existing (unchanged by this diff, and already
reachable through the existing post-`Popen` `roster_register` call this
issue leaves untouched) — a general roster-durability defect, not
specific to the fork-child span this issue's frozen write set covers.
Fixing it (atomic write via temp-file + `os.replace`) is out of scope
per the proposal's write set and is the natural next issue.

canonical: gh pr list --search 908 --state all --json number,state (checked live this session, before this phase-2 session began writing code — showed PR #938 in the MERGED state). after-proposal dispatch: not re-run separately this session, since the approved proposal already carried its own merged after-proposal transition in that prior PR — there was no fresh after-proposal transition inside this phase-2 session to dispatch against.

## Open findings

One non-blocking finding from the before-landing hunt (above): roster
non-atomic-write durability gap, pre-existing, out of this issue's
frozen write set.

Resolution path: file a follow-up issue proposing atomic
`_roster_save()` (temp file + `os.replace`), scoped independently since
it touches every `roster_register()` call site, not just
`_spawn_one()`'s fork-child span.
