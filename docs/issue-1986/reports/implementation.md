---
code_under_review:
  - tests/test_spawn_board_flows.py
loop_state: landed
type: fix
breaking: false
verdict: pass
---

Subject: #1986

## What was done

Implemented the approved phase-1 proposal
(docs/issue-1986/proposals/xdist-hang-workspace-base-isolation.md):
patched `MUSTER_WORK_DIR` to a per-test tmp directory around the
`spawn._spawn_one` call in `tests/test_spawn_board_flows.py`'s shared
`EventReporting._run` helper (used by both `EventReporting` and, via
delegation, `ProgressEvents`), so `auto_sweep`/`_workspace_clean_state`
inside `_spawn_one` scans the test's own empty tmp dir instead of the
real `~/.tokenmaxxxer/work` (2644 entries on this machine, per the
survey).

Two deviations surfaced while re-running the exact acceptance command
live (both logged in
docs/issue-1986/reports/implementation/deviation-log.md, both inline —
mechanical, inside the frozen write set, one-off) — see
`## Rationale for deviations` below.

## Rationale for deviations

1. A second hang site: `ReturnedPrGate`'s `_full_mock_scaffold` (call
   sites at tests/test_spawn_board_flows.py:2518,2581,2615,2644 —
   `derived: grep -n '_full_mock_scaffold(work)' tests/test_spawn_board_flows.py`)
   also calls `spawn._spawn_one` without workspace isolation, and stalled
   the same way once the first fix went in and this turn re-ran, live:

   ```
   pytest tests/test_spawn_board_flows.py -n0 -v
   ...
   tests/test_spawn_board_flows.py::ReturnedPrGate::test_spawn_one_despite_returned_is_deprecated_noop PASSED [ 89%]
   ```
   (exit 124, timed out; saved to /tmp/out_serial2.log). The approved
   proposal's build-plan section named only `EventReporting._run`.
   Extended the same `MUSTER_WORK_DIR` patch into `_full_mock_scaffold`
   — same defect class, same fix shape, needed for the acceptance
   command to run its full set without stalling, no alternative
   considered since the proposal's own rationale for choosing env
   isolation over serial-marking applies identically here.
2. 17 `EventReporting` cases threw `NameError: name '_event' is not
   defined`:

   ```
   pytest tests/test_spawn_board_flows.py -n0 -v
   ...
   17 failed, 117 passed in 12.17s
   ```
   (this turn's own run right after deviation 1's fix, saved to
   /tmp/out_serial3.log) — `tests/test_spawn_board_flows.py` does `from
   _spawn_test_support import *`, and Python's star-import skips
   underscore-prefixed names, so `_event` (defined in
   `_spawn_test_support.py`) never actually reached this file. Not
   mentioned in the proposal (the survey's hang diagnosis never got far
   enough to surface it — the hang always aborted the run first). The
   same defect class was already fixed in `test_spawn_gate_wiring.py`
   for issue #1959:
   `derived: sed -n '1,2p' tests/test_spawn_gate_wiring.py` shows
   `from _spawn_test_support import _event  # noqa: F401` alongside the
   star-import. Applied the identical fix here — one line, mechanical,
   inside the same frozen write-set file, and the only remaining path to
   a zero-failure result on the acceptance command.

## Why

Subject #1986's acceptance check is `timeout 120 python3 -m pytest
tests/test_spawn_directive_assembly.py tests/test_spawn_board_flows.py
-q` (default addopts), run live, checked against a zero-failure count
within the 120s budget. The phase-1 survey/proposal (approved via
`APPROVE issue-1986/implementation`) diagnosed the hang as `_spawn_one`
-> `auto_sweep` sweeping the real, unmocked machine workspace directory,
not an xdist-specific interplay, and specified isolating
`MUSTER_WORK_DIR` in the shared test helper as the fix. The two
deviations above (see `## Rationale for deviations`) were needed to
actually reach a zero-failure result on the acceptance command once the
primary fix removed the hang and exposed further test-collection state
underneath it.

## Upstream

docs/issue-1986/proposals/xdist-hang-workspace-base-isolation.md
docs/issue-1986/reports/implementation/survey.md

## What did not work

Nothing attempted was discarded — the primary fix from the approved
proposal worked as specified; the two deviations were straightforward
extensions/fixes of the same pattern, not failed alternative attempts.

## How you'll know it worked

canonical: acceptance: env -u CORE_BUILD_NOW timeout 120 python3 -m pytest tests/test_spawn_directive_assembly.py tests/test_spawn_board_flows.py -q — result: PASS

145 passed, 0 failed, 3.33s wall-clock, run live, default addopts
(`-n auto` from pytest.ini), this turn's own run saved to
/tmp/final2.log:

```
bringing up nodes...
bringing up nodes...

........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                        [100%]
145 passed in 3.33s
```

## Open findings

None outstanding for this issue's scope. The survey's noted
`CORE_BUILD_NOW` env-leak-into-subprocess item and any other
`_spawn_one`-driving test classes that may still lack workspace
isolation beyond the two fixed here (`EventReporting`/`ProgressEvents`,
`ReturnedPrGate`) were explicitly out of scope per the approved proposal
and were not re-audited beyond what the live acceptance run itself
exercises.
