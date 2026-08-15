# Survey — issue-1462

Scout skip: pure bugfix (display-layer defect, spec leaves no design decision open).

## Write set
- `spawn.py` — `roster_ps()` (spawn.py:2190) is the only `ps` implementation
  (`if a.role == "ps": return roster_ps()` at spawn.py:5747-5748).
- tests/test_ps_state_rows.py — new file, does not exist yet.

## Current-state findings

- `_alive(pid)` (spawn.py:2168) calls `os.kill(pid, 0)`. When `pid == 0`,
  POSIX `kill(0, sig)` targets the caller's own process group, not PID 0 —
  it always succeeds. `roster_ps()` reads `pid = e.get("pid", 0)` (line
  2204) and feeds it straight to `_alive()`, so a roster entry with a
  missing/zero `pid` renders `alive=True` → `RUNNING`. This is the `RUNNING
  pid 0` symptom.
- `mins = (int(time.time()) - e.get("ts", 0)) // 60` (line 2206) runs
  unconditionally. A missing `ts` defaults to epoch 0, producing an age of
  tens of millions of minutes — the `29778226분` symptom.
- The not-alive branch has no explicit terminal-state label distinct from
  `RUNNING` — `DEAD(정리됨)` is the only alternative, and no branch
  differentiates "ended normally, respawn pending" from "process actually
  crashed". Watcher rendering (lines 2212-2235) is nested entirely inside
  `if alive:`, so an ended session never gets a watcher line at all, and a
  live-but-just-ended watcher (by-design exit at session end) has no way to
  be labeled anything other than `DEAD(pid ...)` if it's checked while
  still transitioning.
- Row isolation: `work = e.get("work")` (line 2213) is read from the row's
  own roster entry only — no cross-row fallback exists in `roster_ps()`
  today. The reproduction target is a roster entry whose own `work` field
  already holds a foreign path (as observed); the fix must guarantee the
  renderer never substitutes a *different* entry's `work`/`log` even
  defensively (e.g., never fall back to scanning `ws_idx` values for a
  path).

No alternative implementation approach was considered: this is a pure
bugfix to existing rendering logic with no design surface (per scout skip
condition above).
