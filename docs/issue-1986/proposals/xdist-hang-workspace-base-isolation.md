---
status: proposed
files:
  - tests/test_spawn_board_flows.py
---

Subject: #1986

## Request

Two measured reproductions: `ProgressEvents` in
tests/test_spawn_board_flows.py hung 22min under xdist during issue #1959,
and tests/test_spawn_directive_assembly.py hung >120s under default
addopts — both stranded role sessions. Diagnose the interplay and either
fix it or mark the family for serial execution with the measured cause
recorded. Acceptance: `timeout 120 python3 -m pytest
tests/test_spawn_directive_assembly.py tests/test_spawn_board_flows.py -q`
(default addopts) completes with 0 failed, run live.

## Constraints

- Must not change what `_spawn_one`/`auto_sweep` do for real callers —
  only the test's isolation.
- Fix must hold under both `-n auto` and `-n0` (survey found the hang is
  not xdist-specific).
- Stay inside tests/ per the survey's write-set finding; no production
  code needed.

## Rationale

The survey (docs/issue-1986/reports/implementation/survey.md) found via a
live faulthandler capture that the hang is `spawn._spawn_one` -> `auto_sweep`
-> `_workspace_clean_state` -> `git fetch --all` against the real,
unmocked `_workspace_base()` (`~/.tokenmaxxxer/work`, 2644 real
directories on this machine), not an xdist/thread/fork interplay as the
issue title speculated.

Two candidates considered:

1. **Serial-mark the family** (`@pytest.mark.slow` + exclude `slow` from
   default `addopts`) — this is what the issue's empty-state clause
   anticipates if no interplay fix is found. Rejected as the primary fix:
   it would only change *when* the tests run, not *whether* they still
   burn up to 30s x N real workspaces every time they do run (under `-m
   slow` or CI's full run) — the underlying scan-the-real-directory bug
   stays live and can still strand a `-m slow` run the same way issue
   #1959 was stranded. It also does not explain or fix why a single
   `-n0` run of `ProgressEvents` alone already exceeds a 120s budget on
   this machine, which the acceptance check's own timeout would still
   trip.
2. **Isolate `_workspace_base()` in the test** (chosen) — set
   `MUSTER_WORK_DIR` to the test's own `tempfile.mkdtemp()` for the
   duration of `_spawn_one`, via `mock.patch.dict(os.environ, {...})` in
   the shared `_run` helper. `_workspace_base()` already reads this exact
   env var (`spawn.py:6544`) — no production code changes. This fixes the
   actual defect (tests scanning real, unrelated machine state) rather
   than papering over its symptom with a marker, and keeps the tests fast
   and deterministic under both `-n auto` and serial execution.

## What will be done

- In tests/test_spawn_board_flows.py's `EventReporting._run` (shared by
  `EventReporting` and `ProgressEvents`), patch `MUSTER_WORK_DIR` to a
  test-scoped directory for the duration of the `_spawn_one` call,
  restoring the environment after.
- Re-run the exact acceptance command live and record the result in the
  phase-2 implementation record.

## Out of scope

- Fixing the `CORE_BUILD_NOW` env-leak-into-subprocess pollution noted in
  the survey (pre-existing, unrelated to this issue's acceptance check
  when run with a clean environment).
- Any change to `spawn.py` production behavior (`auto_sweep`,
  `_workspace_base`, `_workspace_clean_state`) — the defect is test
  isolation only.
- Adding a `slow`-exclusion default to `pytest.ini` — not needed once the
  actual defect is fixed, and changing default addopts is a broader
  policy call the issue does not ask for.

## Accumulation

This is a one-time fix to a single shared `_run` helper already reused by
both `EventReporting` and `ProgressEvents` — no per-test or per-file
repetition is introduced. Future `_spawn_one`-driving test classes should
reuse this same helper rather than duplicating the env-isolation inline;
if a third class needed its own bespoke `_spawn_one` harness, that would
be the trigger to extract the `MUSTER_WORK_DIR` patch into a standalone
test fixture — not needed at N=2.

## How you'll know it worked

`timeout 120 python3 -m pytest tests/test_spawn_directive_assembly.py
tests/test_spawn_board_flows.py -q` (default addopts, clean environment)
completes with 0 failed, run live, well inside the 120s budget.
