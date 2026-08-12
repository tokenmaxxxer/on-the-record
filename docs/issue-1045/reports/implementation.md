---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -k panel -v (executed this turn; 3 passed) — basis for verdict below.
verdict: pass
loop_state: landed
---

# Implementation record (#1045)

## Upstream

Basis: docs/issue-1045/proposals/panel-defect-fixes.md.
canonical: `APPROVE issue-1045/implementation` comment read via `gh issue view 1045 --comments` this turn; phase-1 PR #1052 read via `gh pr view 1052` this turn (state: MERGED).

## What was done

Applied the approved proposal's two fixes in `spawn.py`, both inside the
frozen write set:

1. `_run_panel_session()`'s judge prompt (spawn.py, around line 4479) now
   instructs the model to call `ListAgents` first, retry a few times if
   the peer isn't visible yet (near-simultaneous launch race), and address
   `SendMessage` using the name `ListAgents` actually returns rather than
   the literal `peer_role` string.
2. Added `_consult_or_record_error()` (spawn.py, ~4517) wrapping
   `consult_cmd()` — catches any exception, appends a `consult-error` turn
   to the panel record, and returns `(None, <message>)` instead of letting
   the exception propagate. `_panel_degrade()` now calls this helper for
   both judge roles instead of calling `consult_cmd()` directly, and its
   return dict gained `error_a`/`error_b` keys (both `None` on success)
   alongside the existing `verdict_a`/`verdict_b`.

Added a `PanelDegradeErrorSafety` test class in tests/test_spawn.py.
derived: awk '/class PanelDegradeErrorSafety/,/^class ConsultVerdictParsing/' tests/test_spawn.py | grep -c "    def test_"
```
$ awk '/class PanelDegradeErrorSafety/,/^class ConsultVerdictParsing/' tests/test_spawn.py | grep -c "    def test_"
3
```
Covers: a consult failure inside `_panel_degrade()` is recorded as a
`consult-error` turn and returned as an error result without raising; one
side failing still returns the other side's real verdict; `panel_cmd()`'s
own no-round-trip-observed degrade trigger doesn't propagate a consult
failure either.

## Why

Defect 2 (`_panel_degrade()` crashing when `consult_cmd()` fails) is a
correctness bug against the issue's stated acceptance ("a panel run must
never crash, it must record the failure and return a degraded result").
Defect 1's prompt fix follows directly from the phase-1 survey's bounded
live reproduction, which showed the `ListAgents`/`SendMessage` primitive
works once the caller retries discovery and addresses the peer by its
actual returned name — the prior prompt did neither.

## Doc-placement ladder

- No new env var, dependency, migration, or setup step — handbook
  untouched (none applicable).
- No changed public signature or wire format outside this issue's own
  write set, and no library-or-format choice over a named alternative
  beyond what the proposal's own Rationale already recorded — no new
  decisions entry needed.
- No benchmark/investigation numbers produced this phase beyond this
  record itself.

## Acceptance check

canonical: this turn's own pytest run, transcript below.
acceptance: python3 -m pytest tests/test_spawn.py -k panel -v — result: PASS
```
$ python3 -m pytest tests/test_spawn.py -k panel -v
tests/test_spawn.py::PanelDegradeErrorSafety::test_consult_error_inside_degrade_is_recorded_not_raised PASSED
tests/test_spawn.py::PanelDegradeErrorSafety::test_one_side_failing_still_returns_the_others_real_verdict PASSED
tests/test_spawn.py::PanelDegradeErrorSafety::test_panel_cmd_no_round_trip_degrade_does_not_propagate_consult_failure PASSED
3 passed, 475 deselected in 0.19s
```

## What did not work

None.

## Open findings

canonical: manual re-read of both changed functions and the new tests, performed this turn after writing.
None open. Manual self-check performed instead of a background hunter
dispatch (see Hunt section below for why): re-read `_run_panel_session()`,
`_consult_or_record_error()`, and `_panel_degrade()` once after writing —
`consult_cmd()`'s own raise-on-failure contract for its other callers is
untouched, matching the proposal's Out of scope.

## Hunt

No background `warrant-hunter` dispatch was made in this turn: this is a
headless single-shot session (contract v3 s22) with no later turn to
consume an async dispatch result, so dispatching and not waiting on it
would violate contract v3 s22's priority-absolute rule. Manual self-check
substituted (see Open findings).

closed_checks:
- `_panel_degrade never raises on consult_cmd failure` — code_under_review: spawn.py, tests/test_spawn.py
  canonical: python3 -m pytest tests/test_spawn.py -k panel -v — result: PASS (transcript above)
