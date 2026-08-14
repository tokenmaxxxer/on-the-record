---
code_under_review:
  - spawn.py
  - tests/test_ps_state_rows.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_ps_state_rows.py -v (executed this turn; 5 passed) — basis for verdict below.
verdict: pass
loop_state: landed
---

# Implementation record (#1462)

## Upstream

Basis: docs/issue-1462/proposals/2026-08-14-ps-truthful-state-rows.md.
canonical: `APPROVE issue-1462/implementation` comment plus the follow-up
hold-lift comment, both read via `gh issue view 1462 --comments` this turn.

## What was done

Fixed `spawn.py ps` (`roster_ps()`, spawn.py:2190) to render truthful
terminal-state rows in the session-end -> respawn gap:

- `_alive(pid)` (spawn.py:2168) now treats `pid <= 0` as not-alive before
  calling `os.kill` — `os.kill(0, 0)` targets the caller's own process
  group and always succeeds, which was making a roster entry with a
  missing/zero `pid` render `alive=True` (`RUNNING pid 0`).
- Extracted a new pure function `_format_roster_row(key, entry, ws_idx,
  now)` that renders one row with no side effects, so tests drive it with
  synthetic state instead of spawning real processes. `roster_ps()` now
  calls it per row and only handles the `roster_remove()` cleanup
  side-effect itself.
- Age rendering: `ts` is read with `entry.get("ts")` and checked for
  presence/type; when absent, the row shows `unknown` instead of doing
  epoch(0)-based minute arithmetic.
- Terminal-state label: a not-alive row renders `ENDED` (never `RUNNING`),
  carrying the last-known pid (or `unknown` if the pid itself is falsy).
- Watcher lifecycle: watcher rendering moved out of the `if alive:`-only
  branch. When the row itself is not alive and a watcher entry exists, it
  renders `exited-with-session (pid ...)` instead of `DEAD(pid ...)` — the
  `DEAD` label is now reserved for a live session whose watcher actually
  died.
- Row isolation: `work`/`log` are read only from the row's own entry;
  `_format_roster_row` never substitutes another row's fields, verified by
  `test_row_workspace_isolation` with two synthetic entries carrying
  distinct issue numbers in their `work` paths.

## Why

Reproduces the report-only defect (issue #1462, consult-log 2026-08-14):
`spawn.py ps` showed `RUNNING pid 0`, an epoch-garbage age, an empty log,
a foreign workspace path, and a `DEAD`-labeled watcher during the gap
between a session ending and its respawn — misleading the operator into
diagnosing a monitoring outage that wasn't happening (self-heal had
already re-armed the real watcher).

## Acceptance

canonical: python3 -m pytest tests/test_ps_state_rows.py -v (executed this
turn, output pasted below)

acceptance: python3 -m pytest tests/test_ps_state_rows.py -v — result: pass

```
tests/test_ps_state_rows.py::test_gap_row_not_running PASSED             [ 20%]
tests/test_ps_state_rows.py::test_gap_row_not_running_empty_state PASSED [ 40%]
tests/test_ps_state_rows.py::test_missing_timestamp_renders_unknown PASSED [ 60%]
tests/test_ps_state_rows.py::test_row_workspace_isolation PASSED         [ 80%]
tests/test_ps_state_rows.py::test_watcher_lifecycle_label PASSED         [100%]
5 passed in 0.06s
```

canonical: pytest output pasted directly above (this turn, no SKIPPED
lines, hand count 5 matches pasted "5 passed").

The four Acceptance-named tests plus the empty-state fixture were
executed this turn, output above. Row isolation was not reproduced
against the actual unidentified upstream write path that corrupts a
roster entry's own `work` field (out of scope per proposal) — this closes
the renderer's own isolation guarantee only.

## What did not work

None.

## Open findings

None.
