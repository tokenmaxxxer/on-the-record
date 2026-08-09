# Survey — issue-557

Skip condition: pure bugfix. The issue's Acceptance checks fully determine
the fix (scope the follow cursor to the armed session, print the banner
once, tag emitted events) — no open design decision.

`spawn.py` (no `src/` split) implements `watch`/`--follow`:

- `_await_bounded(events_path, offset_path, stall_timeout_min, log_path)`
  (spawn.py:2598) reads `events.jsonl`, compares its line count to a
  persisted integer offset (`_read_offset` at spawn.py:2499 and
  `_write_offset` at spawn.py:2527, sidecar file `_offset_path(work)`),
  and prints the next unseen line. The offset is keyed only by workspace
  dir, not by session, so it carries over across sessions of the same
  (issue, role) workspace log.
- The "스폰은 리턴했지만" banner (around spawn.py:2626) prints inside
  `_await_bounded` whenever the consumed event isn't `session-end`.
  `_watch`'s `--follow` loop (spawn.py:2731) calls `_await_bounded` in a
  `while True:`, so the banner reprints on every poll iteration that
  surfaces a non-`session-end` event — not once per `watch --follow`
  invocation.
- Events are JSON lines `{"ts", "type", "detail"}` (`_append_event`,
  spawn.py:2195). A `session-start` event already carries
  `detail = {"pid": proc.pid, "ts": session_start_ts}` (around
  spawn.py:4079), but nothing reads it to scope which events belong to
  the live session — `_await_bounded` walks the flat sequence for the
  whole workspace log across all past and current sessions. The roster
  entry (`roster_register`, around spawn.py:4044) separately stores the
  same subprocess `pid` plus `wrapper_pid`; the workspace-index entry
  looked up in `_watch` (spawn.py:2734) does not carry `pid` itself, so
  `_watch` needs the roster lookup (already done around spawn.py:2810 for
  crash detection) to learn the live session's pid.

Write set: `spawn.py` (scope the follow cursor to the live session's
`session-start` index, gate the banner to print once per `--follow`
invocation, tag printed event lines with the session's pid/ts) and
`test_spawn.py` (new tests building a fixture workspace log with an older
session's events followed by a live session's, per the issue's Acceptance
checks).

## Accumulation

This changes two existing functions (`_await_bounded` gains two optional
parameters; `_watch` gains one lookup done once per call to compute the
session floor and tag) — not a pattern that repeats per future addition.
Nothing here scales with N: there is one `_await_bounded` call-site shape
(already called from `_watch`'s two branches), no new per-role or
per-issue file, and no inline subprocess/gh call being added.
