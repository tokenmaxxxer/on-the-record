# Survey — issue #1497 (poll-heartbeat monitor liveness + quiet ticks)

## Death-vs-TTL-quiet mechanics (per the correction comment, checked against spawn.py first)

canonical: spawn.py:2356-2381 (poll_due, read directly), on-the-record/hooks/poll-rearm.sh:59-99 (poll_rearm_arm_if_due, read directly), on-the-record/monitors/poll-heartbeat.sh:47,148-150 (source + call site, read directly)
derived: sed -n '2352,2382p' spawn.py

`poll_due()` (spawn.py:2356-2381) is a single shared TTL gate keyed on one
file, `runs/poll_state.json` (`last_poll`), guarded by an flock. It has
three callers: `poll-heartbeat.sh` (the Monitor tick loop, this issue's
subject), and `poll_rearm_arm_if_due()` (on-the-record/hooks/poll-rearm.sh),
called from both `directive.sh` (UserPromptSubmit) and
`stop-poll-rearm.sh` (Stop). Whichever caller asks first inside a given
60s window (`POLL_INTERVAL_SEC`, spawn.py:2353) gets `due=True` and stamps
`last_poll`; every other caller in the same window gets `due=False` and
does nothing observable.

This matches the correction comment's diagnosis: a busy orchestrator
session firing UserPromptSubmit/Stop hooks every turn keeps winning the
TTL race before the Monitor's own 60s-sleep tick gets a chance, so
`poll-heartbeat.sh`'s due-branch (poll-heartbeat.sh:150-275) never fires
— not because the Monitor process died, but because the shared gate was
already consumed elsewhere. There is currently no way to tell the two
apart from outside the Monitor process: `poll_state.json` records "a
tick happened somewhere," not "the Monitor's own loop is still
iterating."

## Requirement 1 (quiet ticks) — already implemented, not a gap

canonical: on-the-record/monitors/poll-heartbeat.sh:184-283 (read directly, the line-keyed diff block and the not-due branch)
derived: sed -n '174,283p' on-the-record/monitors/poll-heartbeat.sh

Issues #1117 and #1220 already built what req 1 asks for: a due tick's
watchdog report is line-keyed-diffed against
`runs/poll_heartbeat_last_state.json` (poll-heartbeat.sh:184-271) —
unchanged lines are suppressed, only new/changed lines print, a fixed
always-emit category list (the regex at poll-heartbeat.sh:201-204: resume/
orphaned/watchdog-crash/returned-pr plus session-status keywords) bypasses
suppression every tick, and a fully-suppressed tick prints nothing except
a bounded ~30min `[heartbeat]` line so the channel never goes fully
silent for long stretches (poll-heartbeat.sh:258-265). A not-due tick
already prints nothing at all (poll-heartbeat.sh:280-283, comment
explicitly notes the #1220 change from a "skipped" line to full
silence). The full watchdog report still lands in
`~/.claude/tokenmaxxxer/poll-watchdog.log` unconditionally
(poll-heartbeat.sh:128-141, 153) per this same reading — the
requirement's "full report still goes to the tick's log file" clause
already holds.

Not yet executed against the acceptance tests, since those tests do not
exist on this branch yet: requirement 1 appears to need no new
suppression code, only tests that assert the pre-existing behavior read
above. Phase 2 will write and run the acceptance tests against current
poll-heartbeat.sh rather than assume this holds.

## Requirement 2 (liveness stamp) — real gap

canonical: on-the-record/monitors/poll-heartbeat.sh:100-109, on-the-record/hooks/directive.sh:85,105 (read directly)

The only existing "alive" artifact is the workspace-keyed marker touched
by `poll-heartbeat.sh` at lines 100-109, once, before the `while true`
loop starts — it proves the Monitor process launched this session, not
that it is still iterating now. `directive.sh` reads it as
`mtime >= session_start` (directive.sh:105), a one-shot flag with no
staleness dimension. `poll_state.json`'s `last_poll` is shared across
three callers (above) and cannot distinguish "Monitor ticked" from
"a hook ticked."

Gap: no artifact records "the Monitor's own loop woke up at time T,"
independent of the TTL race and independent of session start. This is
what req 2 asks for and what would have disambiguated the 2026-08-14
incident.

## Requirement 3 (hook-driven staleness directive) — real gap

canonical: on-the-record/hooks/directive.sh, on-the-record/hooks/stop-poll-rearm.sh (full files, read directly)

`directive.sh` and `stop-poll-rearm.sh` currently only call
`poll_rearm_arm_if_due()` (arm/re-trip, not observe) and, in
`directive.sh`'s case, check the one-shot alive marker for the
"Monitor never started at all" case (northpole req#7, #1280). Neither
hook checks a stamp's age against a multiple-missed-ticks threshold, and
neither emits an explicit re-arm directive line. This is new.

## Existing conventions to reuse (Phase-1 rationale inputs)

- Kill switch: every hook/monitor here gates on `ORCHESTRATE_OFF=1` first
  (poll-heartbeat.sh:43, stop-poll-rearm.sh:26, poll-rearm.sh callers).
  New code follows the same convention.
- Role exclusion: stop-poll-rearm.sh:27 skips when `CLAUDE_ROLE` is set
  (a spawned role session is never the orchestrator) — the same guard
  belongs on any new staleness-check code added to these hooks.
- Atomic file state: `poll_due()`'s flock-guarded read-modify-write
  (spawn.py:2364-2381) is the established pattern for a shared timestamp
  file under `runs/`; a new stamp file should follow it rather than
  inventing an unlocked write.
- Test-hook overrides: `POLL_HEARTBEAT_MAX_TICKS` /
  `POLL_HEARTBEAT_SLEEP_SECONDS` (poll-heartbeat.sh:35-40, 144-145) are
  the established way to make the infinite tick loop testable; a new
  stamp-write should sit inside that same bounded-loop test harness
  rather than requiring a new mechanism.
- tests/test_spawn.py and pytest.ini are off-limits — issue #1490
  (parallel test-suite speedup) has them in flight; this issue's new
  test file (planned path, not yet created: tests slash
  test_monitor_liveness.py) is disjoint from both.

## Scout skip record

Skip condition: pure infrastructure correctness fix — the issue requires
matching an already-specified mechanism (poll_due() TTL gate, existing
delta-suppression, existing hook structure) to a corrected understanding
of its own failure mode; there is no product-shaped external category to
benchmark against (this is an internal ops/reliability surface, not a
user-facing product). No design decision here turns on what a
best-in-class comparable tool does — the shape of the fix is fully
determined by spawn.py's existing TTL semantics and the two hook files'
existing conventions, surveyed above. Scouting is skipped per the
scout-directive's "spec leaves no design decision open" condition.
