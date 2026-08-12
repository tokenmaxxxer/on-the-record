# issue #908 — implementation current-state survey (phase 1)

subject: issue-908
role: implementation

Scout skip: pure bugfix on an internal lifecycle-tracing mechanism
(fork-child spawn setup / roster-and-event registration ordering inside
`spawn.py`), no product-facing surface and no external design decision
open — the finding already names the exact fix shape. Scout directive's
first skip condition applies.

## Write set (frozen for the proposal)

- `spawn.py` — `_spawn_one()` fork-child setup span and the roster/event
  registration ordering around it; `roster_watchdog()`'s dead-registered
  branch is read-only inspected (no change expected there, see below).
- `tests/test_spawn.py` — a new regression-guard test class exercising a
  forced pre-registration death and asserting roster/event traces plus
  `roster_watchdog()` surfacing.
- the role's own phase-2 record (written after approval, per contract
  v3 s19; not written this session).

No new dependency, no new env var, no schema/migration — this is a
control-flow reordering inside one already-imported module.

## Current state (re-derived this session)

derived: `git log --oneline -1`
```
0e04a3c issue-930: requirement digest & drift-guard design (product-discovery, phase 1) (#936)
```

`_spawn_one()`'s fork-child branch (`if bounded and issue is not None:`),
current line numbers —

canonical: `grep -n "os.setsid()\|os.dup2(devnull_fd, 0)\|proc = subprocess.Popen(\|roster_register(roster_key" spawn.py`, re-run this session:
```
5118:            os.setsid()
5126:            os.dup2(devnull_fd, 0)
5130:        proc = subprocess.Popen(
5134:        roster_register(roster_key, {
```

- `os.fork()` happens earlier (~5075); the child falls through to
  `_rewrite_spawn_claim_pid(cwd)` (5117), `os.setsid()` (5118), three
  `os.dup2()` calls (5126-5128), then (unconditionally, both bounded and
  non-bounded paths) `subprocess.Popen()` (5130-5133) — **no**
  `try`/`except` around any of it.
- The first roster write, `roster_register(roster_key, {...})`, is at
  5134 — after all of the above.
- The first `events.jsonl` write (`_append_event(..., "session-start",
  ...)`) is further downstream (~5177), after the roster write —
  canonical: `spawn.py:5177` read this session, matches the phase-1
  defect-verification finding's own citation.
- canonical: docs/issue-908/reports/defect-verification.md (merged
  finding, PR #933), read this session — that record's re-run-live
  citations confirm an `OSError` anywhere in 5117-5133 (e.g. `Popen`
  raising `FileNotFoundError` when `claude` is missing from `PATH`, or
  `setsid`/`dup2` failing) kills the fork-child with zero trace in
  either roster or events.

`roster_watchdog()`'s death-detection (spawn.py:2349-2458) —

canonical: `python3 -c "src=open('spawn.py').read().splitlines(); print(src[2372].strip(), '|', src[2394].strip())"`, re-run this session:
```
d = _roster_load() | if not _alive(e.get("pid", 0)):
```

- The loop at 2382 (`for key, e in sorted(d.items()):`) iterates only
  `_roster_load()` — a dict keyed by roster entries that already exist.
  A delegation that died before line 5134 was never written into that
  dict, so it is structurally invisible to this loop; the dead-entry
  branch (2395-2431: `_post_session_end_comment`, `diagnose_health`
  `dead_report`, `_maybe_resume_for_ready_pr`) never runs for it —
  canonical: spawn.py:2382-2431, read this session.
- This branch's own machinery, however, already does the right thing
  once an entry exists: `diagnose_health()` (spawn.py:2167-2216, read
  this session) calls `session_end_verdict()` (spawn.py:1566-1611, read
  this session) and, when the pid is dead and the verdict is not
  `"normal"`, returns `{"state": "DEAD-ERRORED", "next_action":
  "respawn", ...}` — which `roster_watchdog()` prints and folds into
  `anomaly_count` (2411-2417), and `_auto_respawn_check()` (2429-2430,
  when `auto_respawn=True`) can act on. So the surfacing mechanism this
  issue asks for already exists in `roster_watchdog()`; what is missing
  is only that a pre-registration death never reaches it because no
  roster entry and no `session-start` event exist yet at the moment it
  dies.
- `session_end_verdict()`'s own defaults matter here — canonical:
  spawn.py:1584-1585 and spawn.py:1599-1606, read this session: with no
  `events.jsonl` at all, or no `session-start` event found, it returns
  `"normal"` — a false-negative for a death that happened before the
  first `session-start` write. Only when a `session-start` event exists
  and its `detail.pid` is dead does it correctly return `"crashed"`.

## What this implies for the fix

Two things must both move earlier than the risky span (5117-5133), not
just be wrapped in `try`/`except`:

1. A roster entry for `roster_key`, keyed by the fork-child's own pid
   (`os.getpid()`, stable for the whole span since it runs in the
   fork-child process before `Popen` gives a separate `proc.pid`) —
   pre-registered before entering the risky span, so
   `roster_watchdog()`'s existing dead-registered-entry path picks it up
   the moment the pid dies (no watchdog-side change needed).
2. A `session-start` event using the same pid, written at the same early
   point — so `session_end_verdict()` does not fall into its "no
   session-start seen -> normal" default and instead correctly reads
   `"crashed"`.

Wrapping the risky span itself in `try`/`except OSError` is then useful
on top of (1)+(2) for a distinct, named `spawn-death` event carrying the
actual exception and the stage (`fork-setup` vs `popen`) — better for a
human reading `events.jsonl` than inferring the cause from a dead pid
alone — but is not by itself sufficient: an OS-level kill (e.g. SIGKILL,
segfault) that never raises a catchable Python exception would bypass a
bare `try`/`except` entirely, while the pre-registration (1)+(2) still
catches it on the next `roster_watchdog()` tick because it only depends
on the pid being dead, not on an exception having been raised.

`roster_watchdog()` itself needs no change — its existing
dead-registered-entry branch already surfaces `DEAD-ERRORED` correctly
once the entry and the `session-start` event exist early enough; the fix
is entirely in `_spawn_one()`'s ordering.

## Alternatives considered

- **Only wrap 5117-5133 in `try`/`except` and write an event on catch,
  without moving the roster/event writes earlier.** Rejected: does not
  cover a non-Python-exception death (kill signal, segfault) — the
  before-registration silent-death class the issue describes is not
  limited to Python-raised `OSError`s, and `roster_watchdog()` still
  cannot see the entry at all if the process dies without ever running
  the `except` clause. Pre-registering the roster entry with the
  fork-child's own pid is the only approach that stays correct incl.
  under a signal-shaped death.
- **Extend `roster_watchdog()`'s death-detection to also scan for
  processes that hold the workspace lock but have no roster entry at
  all** (a positive, out-of-band leak scan instead of moving
  registration earlier). Rejected: the survey above shows
  `roster_watchdog()`'s existing dead-registered-entry path already does
  the right thing (`diagnose_health` -> `DEAD-ERRORED`) — building a
  second, parallel unregistered-process scanner duplicates that logic and
  adds a new failure surface (how would it correlate an orphan process to
  an issue/role without the roster entry it's meant to detect the absence
  of?) for no gain over simply registering earlier, which is a strictly
  smaller, more localized change.

## Accumulation

Not accumulation-cost-shaped — a single reordering fix inside one
function plus one matching regression-test class; no per-item cost that
grows with usage.
