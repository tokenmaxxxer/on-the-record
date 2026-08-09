---
code_under_review:
  - spawn.py
  - test_spawn.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-557

## What was done

`watch --follow`'s cursor used to be scoped only to the workspace log
file, not to the session live when it armed — so a new (issue, role)
session inherited the old persisted offset and could replay an earlier
session's events. Fixed in `spawn.py`:

- Added `_live_session_start_index(events_path, pid)`: finds the line
  index of the last `session-start` event matching the given pid.
- `_watch` now looks up the live session's pid from the roster entry
  (the same lookup already used for crash detection) and, if the
  persisted offset predates that session's `session-start` line, raises
  the offset floor to it before consuming any events — so an earlier
  session's events can never be emitted once a newer session has armed.
- `_await_bounded` gained two optional parameters: `session_tag`
  (printed alongside every emitted event line so multiplexed consumers
  can attribute it to its originating session) and `show_banner` (lets
  the `--follow` loop suppress the "스폰은 리턴했지만" banner after its
  first print, instead of reprinting it every poll iteration).
- `_watch`'s follow loop tracks a local `banner_shown` flag and passes
  `show_banner=not banner_shown` into each `_await_bounded` call.

Added `WatchFollowSessionScoping` to `test_spawn.py` with three tests
mapping directly to the issue's Acceptance checks: no replay of an
earlier session's events once a newer session is live and armed, the
banner prints at most once across a multi-event `--follow` run, and
every emitted line carries the live session's pid/ts tag. Updated the
existing `fake_await_bounded` test doubles in `test_spawn.py` to accept
`**kwargs` since `_await_bounded` is now called with the new keyword
arguments.

## Why

basis: docs/issue-557/proposals/2026-08-09-watch-follow-session-scoping.md

Issue #557: a `watch --issue N --follow` armed during a phase-2 session
interleaved a phase-1 session's events into the stream (session-start
for the old pid three times, followed by old progress and pr-opened
events reported after phase-2 events had already streamed), opening
with duplicate banner lines. The orchestrator cannot attribute events
to sessions and a replayed old session-end/pr-opened can drive wrong
routing.

## What did not work

None.

## Doc placement

- No new env var, dependency, migration, or setup step — no handbook
  update needed.
- The chosen approach (raise the offset floor via a `session-start`
  index lookup, vs. splitting `events.jsonl` per session) is recorded in
  the proposal's `## Rationale`; no separate decision doc needed.
- No benchmark/investigation numbers produced beyond this record and
  the survey.

## Hunt

Ran the full suite before landing:

```
$ python3 -m pytest test_spawn.py -q
338 passed in 21.43s
```

Confirmed both the new `WatchFollowSessionScoping` tests and the
existing `WatchFollow` regression tests (with their `fake_await_bounded`
doubles updated for the new kwargs) pass together.

Stance taken (cycling through the five hunt stances, this dispatch
landing on "assume the rule as written cannot hold — find the state
nothing maintains"): checked whether the pid-based session-start match
can misfire on pid reuse. `_live_session_start_index` picks the *last*
matching `session-start` line for a pid, and `_watch` only calls it with
the pid the roster currently reports as live — so even if an old, dead
session reused the same OS pid as a coincidence, the most recent
`session-start` line for that pid is definitionally the live session's
own (a session always appends its own `session-start` after any earlier
one with the same pid could have existed). No finding.

Given headless single-shot constraints (contract v3 s22: no delegated
work may cross a turn boundary unconsumed), this hunt was done inline
rather than dispatched as a background agent, since the diff is small
(2 files) and a background dispatch's result could not be consumed
before this turn ends.

## Open findings

None.
