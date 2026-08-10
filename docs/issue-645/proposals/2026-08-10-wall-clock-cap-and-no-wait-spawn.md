---
status: proposed
Subject: issue-645
files:
  - spawn.py
  - test_spawn.py
---

# Proposal — wall-clock cap on activity-reset waits + `--no-wait` spawn mode (issue #645)

## Request
Issue #645's 2026-08-10 comment adds two items beyond the already-designed
PreToolUse refusal (architecture role, PR #647, merged): (1)
`_await_bounded`'s stall clock resets on any session-log size change, so a
session that keeps logging holds the caller indefinitely — no hard
wall-clock return bound exists, in either the single-call path or
`watch --follow`'s repeated calls. (2) `spawn.py --issue` always ends in
`_await_bounded` (`bounded=True` unconditionally when `--issue` is given);
there is no fire-and-return mode, so the "always spawn in the background"
contract rule relies entirely on the harness's own `run_in_background`
option with no in-process fallback.

## Constraints (from the issue and survey)
- Must not change `_await_bounded`'s existing single-call semantics when
  the new bound is not requested — `_watch`'s current callers (non-`
  --follow` `spawn.py watch`) must behave identically to today.
- The wall-clock cap must be resumable, not terminal: on cap-hit, the
  caller must be able to re-poll the same unread events from the same
  `offset_path` — never drop or skip an event.
- `--no-wait` must still leave the caller with what it needs to resume
  observation via the existing `spawn.py watch` path (workspace, issue,
  role) — it's a fire-and-return, not a fire-and-forget; #645's own
  operator constraints (prior comments) treat orphaning a session as the
  worse failure class, so this flag must not become a new orphaning route.
- Distinct return/exit signaling per reason-for-return, following this
  file's own house style (`WATCH_CRASH_RC` precedent) rather than
  overloading the existing `0` used for both "event" and "stall."

## Rationale
Two shapes were considered for the wall-clock cap: (a) replace the
stall-reset clock with a pure wall-clock deadline, or (b) add a second,
independent wall-clock deadline alongside the existing stall clock. (a)
was rejected: the stall clock's reset-on-activity behavior is intentional
and already relied on by callers that want "come back only once truly
stuck" (the crash-detection path `WATCH_CRASH_RC` depends on the stall
semantics staying as-is) — replacing it would change behavior for every
existing caller, not just the new one requesting a cap, violating the
first constraint above. (b) is additive: a new optional parameter,
default `None`/disabled, so `_await_bounded`'s existing callers are
byte-for-byte unaffected and only a caller that opts in (the `--follow`
loop, once threaded through with a cap) gets the new bound.

For `--no-wait`, the alternative considered was leaning on harness-level
`run_in_background` alone (status quo) and treating this as out of scope
for `spawn.py` itself. Rejected per the issue's own text: harness
backgrounding prevents the *Claude Code turn* from blocking but does not
change `spawn.py`'s in-process behavior — the process still blocks inside
`_await_bounded` before returning, so a model that forgets to background
the harness call still gets no in-process fallback. An explicit `--no-wait`
flag on the `spawn` subcommand closes that gap independently of harness
behavior.

## What will be done
- `_await_bounded`: add an optional `max_wait_s: float | None = None`
  parameter. When set, the poll loop also checks elapsed wall-clock since
  entry (independent of `last_change`) and returns early with a distinct
  signal (a new return code, following the `WATCH_CRASH_RC` precedent —
  concretely `WATCH_WALLCLOCK_RC`) when `max_wait_s` is exceeded, without
  advancing `offset_path` past unread events. Default `None` preserves
  current behavior for every existing call site.
- `_watch`'s `--follow` loop: thread a wall-clock budget across repeated
  `_await_bounded` calls (start-of-loop timestamp, remaining budget passed
  as `max_wait_s` to each call, loop exits and reports "wall-clock cap
  hit — re-arm with spawn.py watch" once budget is exhausted) — bounding
  cumulative `--follow` runtime the way #451 already bounds per-call
  stall.
- `cmd_spawn`/`_spawn_one`: add a `--no-wait` argparse flag on the `spawn`
  subcommand. When set, `_spawn_one` returns immediately after
  fork/detach (skips the `_await_bounded` call at spawn.py:4280-4281),
  printing the workspace/log/`spawn.py watch --issue N --role <role>`
  resume command — mirroring the message `_await_bounded` itself already
  prints on a non-session-end event (spawn.py:2836-2838).
- Tests in `test_spawn.py`: cap-hit-vs-stall-hit-vs-event distinguished by
  return code; cap-hit does not advance `offset_path` (resumability);
  `--no-wait` returns promptly and the printed resume command round-trips
  through `spawn.py watch`.

## Accumulation
This adds one optional parameter to one existing function (`_await_bounded`)
and one optional flag to one existing subcommand (`spawn`) — not a new
per-item file or a repeated inline subprocess/`gh` call pattern. If a
future issue needs an *n*-th independent wall-clock-style bound elsewhere
in `spawn.py`, the right shape is the same one used here: thread another
optional parameter through the shared `_await_bounded` helper rather than
duplicating its poll loop at a new call site — the helper is already the
shared chokepoint, so this change reinforces rather than erodes that. No
new per-role or per-issue file is created by this proposal, so the
"roles/*.json-style repeated file" accumulation shape does not apply here.

## Out of scope
- The PreToolUse refusal hook itself (`blocking-call-guard.sh` and its
  tests) — already designed by the architecture role and proposed in
  `docs/issue-645/proposals/2026-08-10-blocking-call-pretooluse-refusal.md`;
  building it is this implementation role's phase-2 work once that
  role's own approval lands (see survey.md — no
  `APPROVE issue-645/implementation` exists yet).
- Documenting `--no-wait`/the wall-clock cap in `on-the-record/commands/run.md`'s
  turn-budget rules — deferred to phase 2, alongside the refusal hook's
  own doc line, so the contract text is updated once per role cycle
  instead of twice.
- Choosing or hardcoding a default wall-clock budget value — phase 2
  decides the number (likely mirroring `--stall-timeout`'s default scale)
  against what phase-2's own e2e testing shows is a reasonable cap for a
  chatty-but-productive session.

## How you'll know it worked
- `test_spawn.py` gains red/green pairs: a session that keeps growing its
  log file past `max_wait_s` returns `WATCH_WALLCLOCK_RC` (not blocking
  past the cap), and a session with no activity still returns via the
  existing stall path unchanged when `max_wait_s` is unset.
- A cap-hit case followed by a second `_await_bounded` call against the
  same `offset_path` observes the events the first call skipped (no event
  loss across a cap-triggered return).
- `spawn.py --issue N --no-wait ...` returns before any `_await_bounded`
  call executes (measurable: process exit before the stall-timeout window
  even without a running child), and the printed resume command, when run,
  reaches the same session via `spawn.py watch`.
