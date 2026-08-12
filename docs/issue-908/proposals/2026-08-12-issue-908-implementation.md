---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
---

## Request

#908: `_spawn_one()`'s fork-child setup (`os.setsid()`, three
`os.dup2()` calls, `subprocess.Popen()`) runs before the first roster
write (`roster_register`) and first event write (`session-start`), with
no `try`/`except` — a death in that span leaves zero trace, and
`roster_watchdog()`'s death-detection only scans already-registered
roster entries so it structurally cannot see a pre-registration death.
Per the merged phase-1 finding
(docs/issue-908/reports/defect-verification.md, addressed_to: coding,
blocking), fix `_spawn_one()` so a death in that span leaves a
roster/event trace `roster_watchdog()` can detect and surface, and add a
live-fire regression guard.

## Constraints

- No new dependency, env var, schema, or migration.
- `roster_watchdog()`'s existing dead-registered-entry surfacing
  (`diagnose_health` -> `DEAD-ERRORED` -> `anomaly_count`) must not be
  touched or duplicated — per the survey
  (docs/issue-908/reports/implementation/survey.md), it already does the
  right thing once an entry exists; the gap is purely that no entry
  exists yet during the risky span.
- Fix must not depend solely on catching a Python exception (a
  `try`/`except`-only fix misses a signal-shaped death) — see survey's
  "What this implies for the fix" and "Alternatives considered".
- The observation-loss regression guard (issue #923 lineage:
  `events.jsonl`/roster stays append-only and readable even on a mid-span
  crash) is inviolable and must not regress.

## Rationale

Considered wrapping only the risky span in `try`/`except OSError` and
writing a `spawn-death` event on catch, without moving any registration
earlier. Rejected because it only catches deaths that raise a Python
exception — a `SIGKILL` or segfault in that span would still leave
`roster_watchdog()` with nothing to iterate over, reproducing the exact
silent-loss shape the issue reports, just gated on cause instead of
timing. Chosen approach instead pre-registers a roster stub (keyed by
the fork-child's own `os.getpid()`, stable for the whole span) and an
early `session-start` event before entering the risky span, so
`roster_watchdog()`'s existing dead-entry path sees the entry regardless
of how the process died; `try`/`except` around the span is added on top
only to attach a named `spawn-death` event with the actual error for
human legibility, not as the sole detection mechanism.

## What will be done

- In `_spawn_one()`, move roster/event registration for the fork-child
  branch (`if bounded and issue is not None:`) to immediately before
  `_rewrite_spawn_claim_pid(cwd)`/`os.setsid()`: register a roster stub
  keyed by `roster_key` with `pid: os.getpid()` and write an early
  `session-start` event with the same pid.
- Wrap the `os.setsid()`/`os.dup2()` span in `try`/`except OSError`;
  on catch, append a `spawn-death` event (`stage: "fork-setup"`, the
  error) and re-raise (preserve the existing non-zero-exit crash
  behavior for other consumers).
- Wrap the (unconditional, both bounded and non-bounded paths)
  `subprocess.Popen()` call in `try`/`except OSError`; on catch, append a
  `spawn-death` event (`stage: "popen"`) when `issue is not None`, and
  re-raise.
- Leave the existing post-Popen `roster_register`/`session-start` write
  in place unchanged (it still runs on success and overwrites the stub
  with the real `proc.pid` and full fields).
- `roster_watchdog()` itself is unchanged — per the survey, its
  dead-registered-entry branch already surfaces `DEAD-ERRORED` once an
  entry exists.
- Add a regression-test class to `tests/test_spawn.py`: force
  `os.setsid()` to raise (fork-child path, `os.fork` mocked to `0` so no
  real fork happens) and assert (a) the roster stub was registered with
  `os.getpid()` before the crash, (b) `events.jsonl` carries both
  `session-start` and `spawn-death` (`stage: "fork-setup"`), (c)
  `session_end_verdict()` reads `"crashed"` (not the false-negative
  `"normal"`), (d) `roster_watchdog()` prints `DEAD-ERRORED` and returns
  a nonzero anomaly count for the dead entry. A second test forces
  `subprocess.Popen` to raise (non-bounded path) and asserts the
  `popen`-stage `spawn-death` event. A third test asserts a normal
  (non-crashing) spawn is unaffected — exactly one final roster
  registration, no `spawn-death` event (empty-state guard).

## Out of scope

- Any change to the poll-resume/`--resume` backstop itself (issue #883/
  #829) — it already fires off `roster_watchdog()`'s `DEAD-ERRORED`
  surfacing via `_auto_respawn_check`, unchanged by this fix.
- Any change to `session_end_verdict()`'s three-way logic itself — the
  fix works by ensuring an early `session-start` event exists, not by
  changing how the verdict function reads events.
- Any change outside `_spawn_one()`'s fork-child/Popen span.

## Accumulation

Not accumulation-cost-shaped: the two new `try`/`except` blocks and the
moved registration are a one-time reordering inside a single function's
already-existing control flow, not a growing inline `subprocess`/`gh`
call list or a repeated single-line edit across `roles/*.json`-style
files. Nothing here scales with how many more times this pattern is
touched.

## How you'll know it worked

- `python3 -m unittest tests.test_spawn -k SpawnDeathBeforeRegistration`
  passes, including the forced-death live-fire case (roster stub +
  `session-start` + `spawn-death` events present, `session_end_verdict`
  reads `"crashed"`, `roster_watchdog()` output contains
  `DEAD-ERRORED` and a nonzero anomaly count) and the empty-state case
  (normal completion unaffected).
- Full `tests/test_spawn.py` suite still passes (no regression to
  existing `_spawn_one`/`roster_watchdog`/`session_end_verdict`
  coverage).
