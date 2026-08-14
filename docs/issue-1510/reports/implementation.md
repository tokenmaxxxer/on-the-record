---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - spawn.py
  - tests/test_heartbeat_cadence.py
  - tests/test_spawn.py
type: chore
breaking: false
verdict: pass  # canonical: python3 -m pytest tests/test_heartbeat_cadence.py tests/test_spawn.py::NoConcurrencyCap -v — 3 passed, 0 failed (this turn)
loop_state: landed
---

## What was done

Widened the poll-heartbeat default cadence 60s -> 120s and scaled its two
derived staleness constants together, per issue #1510:

- `on-the-record/monitors/poll-heartbeat.sh` line 166: `POLL_HEARTBEAT_SLEEP_SECONDS` default 60 -> 120.
- `on-the-record/hooks/directive.sh` line 180: `MONITOR_LIVENESS_STALE_SECONDS` default 180 -> 360 (same 3-tick tolerance margin at the new cadence).
- `spawn.py` line 5661: `MONITOR_ALIVE_TOUCH_CADENCE_SECONDS` 60 -> 120; the existing `assert MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > MONITOR_ALIVE_TOUCH_CADENCE_SECONDS` still holds against the 7-day GC threshold.
- Added `tests/test_heartbeat_cadence.py`, class `TestHeartbeatCadenceDefaults`, method `test_defaults_scaled_together`, which parses `POLL_HEARTBEAT_SLEEP_SECONDS` and `MONITOR_LIVENESS_STALE_SECONDS` defaults directly out of the two shipped shell files (not hardcoded copies) and asserts the heartbeat default is 120 and the stale default is >= 3x it.
- Added to `tests/test_spawn.py` a `NoConcurrencyCap` class with `test_no_concurrency_cap` (50 stub `spawn.spawn_cmd()` calls, all admitted with no count-based refusal) and `test_zero_running_sessions_spawns_normally`, with a class docstring recording the operator-decision WHY next to the test per the issue's "test is the guard, sentence is commentary" instruction.

## Why

Basis: docs/issue-1510/proposals/heartbeat-cadence-widen.md, itself based
on issue #1510's own text (operator directive 2026-08-15, validity-consult
docs/reports/consult-log.md 2026-08-15 requirements-engineering entry).
Halving heartbeat frequency halves idle machinery cost; the staleness
tolerance must scale with it or a single delayed tick after the widen
false-alarms "monitor dead". The no-cap regression test locks in that
quota safety is owned by #1498/#1508, not by throttling spawn parallelism
here, per operator decision.

## What did not work

None.

## Doc placement

- No docs/handbooks update needed — none of the touched files are the
  operational-surface types the doctrine ladder gates on (no new env var,
  config key, dependency, or migration was introduced; the constants
  changed are existing shell/py defaults, not new setup surface).
- No decision-record entry needed — no public signature or wire format
  changed; the constant-value changes are documented in the proposal's
  Rationale section (docs/issue-1510/proposals/heartbeat-cadence-widen.md),
  which names and rejects the alternative (a docs/specs policy sentence)
  in favor of a test-class docstring.
- No separate benchmark/investigation report needed beyond this record and
  docs/issue-1510/reports/implementation/survey.md.

## Open findings

None.

## Hunt

Not dispatched: contract v3 s22 (headless/single-shot) takes priority over
the warrant directive's hunter-dispatch instruction — this turn has no
later turn for an async hunter result to land in, and the change is a
three-constant scale-together plus two new regression tests with no
runtime behavior beyond what the tests already assert and this turn
already ran.

canonical: python3 -m pytest tests/test_heartbeat_cadence.py tests/test_spawn.py::NoConcurrencyCap -v — 3 passed, 0 failed (this turn)
