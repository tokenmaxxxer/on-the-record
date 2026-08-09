---
status: proposed
files:
  - spawn.py
  - test_spawn.py
  - docs/issue-557/reports/implementation/survey.md
---

## Request

`watch --issue N --follow` replays events from earlier sessions of the
same (issue, role) workspace log when a new session is live, prints the
"스폰은 리턴했지만 세션은 계속 돈다" banner once per poll iteration
instead of once per invocation, and does not tag emitted events with
their originating session — so a multiplexed consumer can't tell which
session an event belongs to. Skip condition (scout directive): pure
bugfix — the issue's three Acceptance checks fully determine the fix, no
design decision open.

## Constraints

- `_await_bounded`'s existing non-`--follow` behavior (one event or
  stall, then return) must be unchanged in shape — only the printed line
  gains an optional session tag and the banner gains an optional gate.
- The persisted offset file format (single integer, line count consumed)
  stays the same — no new sidecar file.
- No behavior change when a session's pid can't be determined (roster
  entry absent) — falls back to today's untagged, unscoped behavior
  rather than erroring.

## Rationale

Two ways to scope the cursor were considered:

- **Locate the live session's `session-start` line in `events.jsonl` and
  raise the persisted offset floor to it before consuming (chosen).**
  `session-start` already carries `{"pid", "ts"}` (spawn.py:4079); the
  roster lookup `_watch` already performs for crash detection
  (spawn.py:2810) gives the live pid. Bumping the floor once, before
  entering `_await_bounded`, reuses the existing offset mechanism with no
  new file or format.
- **Split `events.jsonl` into per-session files at session-start time.**
  Rejected: touches the write path (`_append_event`, every event emitter)
  instead of only the read path, and every consumer (`--all` multiplexed
  view, `_event_count`, ledger/report code) would need to learn the new
  per-session layout — much larger surface for the same fix.

## What will be done

- Add `_live_session_start_index(events_path, pid)`: scans
  `events.jsonl` for the last `session-start` event whose `detail.pid`
  matches, returns its line index.
- In `_watch`, look up the live session's pid from the roster entry
  (same lookup already done for crash detection) and compute this index
  once; if the persisted offset is behind it, raise the offset to it
  before the first `_await_bounded` call — so the follow cursor never
  starts before the armed session's own `session-start`. Capture that
  session-start event's `(pid, ts)` as a `session_tag`.
- Add `session_tag` and `show_banner` parameters to `_await_bounded`;
  print `session_tag` alongside every emitted event line, and pass
  `show_banner=False` on `--follow` iterations after the first one that
  already printed the banner.
- Tests in `test_spawn.py`: a fixture `events.jsonl` with an older
  session's events followed by a live session's `session-start` and
  events, asserting (1) no older-session event is emitted once `--follow`
  arms on the live session, (2) the banner prints at most once across
  multiple `_await_bounded` calls in a `--follow` run, (3) every emitted
  line carries the live session's pid/ts tag.

## Accumulation

One-time addition of a lookup helper and two optional parameters to one
existing function — not a pattern repeated per future session or event
type. No new per-issue or per-role file, no inline subprocess/gh call
accumulation.

## Out of scope

- Splitting `events.jsonl` into per-session files (rejected alternative
  above).
- Changing `_watch_all`'s multiplexed-view logic beyond what session
  tagging already exposes to it for free.
- Any change to `session-end`/crash-detection semantics.

## How you'll know it worked

`python3 test_spawn.py` passes, including the three new tests mapping
directly to the issue's three Acceptance checks: no pid-A event replayed
once pid-B is live and armed, banner appears at most once per invocation
across poll iterations, and every emitted event line carries the
originating session's pid/ts.
