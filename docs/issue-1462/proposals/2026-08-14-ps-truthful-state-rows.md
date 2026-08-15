---
status: proposed
files:
  - spawn.py
  - tests/test_ps_state_rows.py
---

## Request

`spawn.py ps` renders a corrupted row during the gap between a session's
end and its next respawn: `RUNNING` with `pid 0`, an epoch-derived garbage
age, an empty log, a foreign-issue workspace path, and a by-design watcher
exit mislabeled `DEAD`. Make the row rendering truthful in this gap.

## Constraints

- Display-layer only — no change to when/how roster entries are written or
  removed.
- Scout skipped: pure bugfix, no design surface (see
  docs/issue-1462/reports/implementation/survey.md).

## Rationale

Considered leaving `_alive()` untouched and instead special-casing `pid ==
0` only inside `roster_ps()`. Rejected: `_alive()` is called from other
sites too (e.g. `watchdog_check_one` reachable code), and `os.kill(0, 0)`
succeeding for a non-existent-process pid is a defect in the helper
itself, not only in its `ps` caller — fixing it at the helper closes the
bug for every caller instead of only the one currently observed.

## What will be done

- `_alive(pid)`: treat `pid <= 0` as not alive (guards the `os.kill(0, 0)`
  self-process-group false positive) before calling `os.kill`.
- `roster_ps()`: read `ts` with `entry.get("ts")` (no `0` default) and
  render age as `unknown` when absent, instead of epoch-arithmetic minutes.
- `roster_ps()`: give the not-alive branch an explicit terminal label
  (`ENDED`) distinct from `RUNNING`, carrying the last-known pid.
- `roster_ps()`: move watcher rendering out of the `if alive:`-only branch
  so an ended row can still report its watcher, using a lifecycle label
  (`exited-with-session`) instead of `DEAD` when the row itself is the one
  that ended (not a live session with an actually-dead watcher).
- `roster_ps()`: never source `work`/`log` for a row from anything but
  that row's own entry — no fallback lookup into `ws_idx` or another
  roster key for display fields.
- Extract the per-row formatting into a small pure function so
  tests/test_ps_state_rows.py can drive it with synthetic state without
  spawning real processes.

## Accumulation

Not accumulation-shaped: this touches one existing function (`roster_ps()`)
and its two helpers (`_alive()`, a new pure row-formatter) in `spawn.py`.
It adds no new subprocess/`gh` call sites and no per-role repeated file —
`N` more `ps` invocations run the same fixed code path, not `N` more
copies of it.

## Out of scope

- Fixing whatever upstream process actually wrote a foreign `work` path
  into a roster entry (not reproduced/located in this pass — the fix here
  is the renderer's own row-isolation guarantee, which holds regardless of
  how an entry got corrupted).
- Changing roster write/removal timing, watchdog logic, or respawn logic.

## How you'll know it worked

- tests/test_ps_state_rows.py::test_gap_row_not_running,
  test_missing_timestamp_renders_unknown, test_row_workspace_isolation,
  test_watcher_lifecycle_label all pass.
