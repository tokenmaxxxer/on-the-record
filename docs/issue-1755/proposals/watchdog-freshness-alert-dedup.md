---
status: proposed
files:
  - spawn.py
  - tests/test_watchdog_freshness.py
---

## Request

#1755: the watchdog's code-freshness notice (checkout HEAD changed since
session start) re-fires every ~2min tick until the process restarts. The
trigger is legitimate but the repetition is noise. Fix: alert once per
observed HEAD transition, stay quiet on repeat ticks with the same new
HEAD, and alert again only when the HEAD changes further.

## Constraints

- Single surface: `spawn.py`'s `watchdog_freshness_check` and its one CLI
  callsite (`watchdog` role), plus that function's existing test file.
- Design-research and assumptions are skipped per the issue's own
  `design-research-skip: mechanical` / `assumptions-skip: mechanical`
  tags — see `docs/issue-1755/reports/implementation/survey.md`.
- `watchdog_freshness_check`'s existing signature/behavior must stay
  backward compatible for its two current callers in
  `tests/test_watchdog_freshness.py` that pass no state argument.
- Test must run under the fast tier (`.on-the-record/test-tiers.json`
  `fast` command: `pytest -q -m "not slow"`), per the issue's stated
  check.

## Rationale

Two ways to dedup were available:

1. **In-memory dedup inside the long-lived watchdog loop** (a module-level
   variable remembering the last-alerted HEAD). Rejected: the repeat-tick
   invocations in the reported bug are separate CLI subprocess calls (`spawn.py
   watchdog` re-invoked per tick), not one long-lived Python process with
   persistent memory — an in-process variable would reset every tick and
   never dedup anything, which is the exact bug being fixed.
2. **State-file dedup keyed by last-alerted HEAD** (chosen): persist the
   last HEAD that was already alerted on to a small JSON file under
   `STATE_ROOT`, the same directory and JSON-file pattern
   `watchdog_lock_acquire` already uses for `WATCHDOG_LOCK_PATH`
   (`spawn.py:3342`, `spawn.py:3361`). This survives across the
   per-tick subprocess invocations, matching how the bug actually
   manifests, and reuses an established pattern instead of introducing a
   new persistence mechanism.

## What will be done

- Add `state_path: Path | None = None` to `watchdog_freshness_check`.
  When the HEAD comparison finds staleness: read `state_path` (if it
  exists) for a `last_alerted_head` field; if it already equals the
  current HEAD, return `(False, "")` (stale, but already alerted — no
  repeat message); otherwise write `{"last_alerted_head": current}` to
  `state_path` and return `(False, msg)` as before. `state_path=None`
  keeps today's behavior (no dedup, matching existing tests).
- Add a `WATCHDOG_FRESHNESS_STATE_PATH` constant beside
  `WATCHDOG_LOCK_PATH` and wire the CLI `watchdog` role callsite
  (`spawn.py:6971`) to supply it, and to only `print(msg)` when `msg` is
  non-empty (repeat-tick calls now return an empty message).
- Add unit tests to `tests/test_watchdog_freshness.py`: a three-tick
  simulation (HEAD changes, HEAD unchanged, HEAD changes again) asserting
  exactly two non-empty alert messages across the three calls sharing one
  `state_path`; and an empty-state case (no state file yet) asserting the
  first observation both alerts and seeds the state file.

## Out of scope

- Any change to the exit-sentinel / restart-signal behavior
  (`WATCHDOG_STALE_CODE_SENTINEL`) itself — only the printed alert
  message is deduped, not whether the tick reports itself stale.
- Other watchdog checks (lock acquisition, canonical-path guard) —
  untouched.

## Accumulation

This adds one JSON state file (path constant beside the existing
`WATCHDOG_LOCK_PATH`) written by one function, read/written by that same
function on each call — not a per-item inline `subprocess`/`gh` call
accumulating without a shared helper, and not a repeated-file/list pattern
(`roles/*.json`-style). If this dedup approach were needed for more
checks later, each would get its own single state-file constant next to
its own check function, following the same one-function-one-state-file
shape already established by `watchdog_lock_acquire` /
`WATCHDOG_LOCK_PATH` — there is no N-times-more growth path here, since
one state file already covers all future ticks of this one check for the
lifetime of the checkout.

## How you'll know it worked

- `python3 -m pytest -q tests/test_watchdog_freshness.py` passes,
  including the new three-tick dedup test and the empty-state test, run
  via the fast tier command from `.on-the-record/test-tiers.json`.
