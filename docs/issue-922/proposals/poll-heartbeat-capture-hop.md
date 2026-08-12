---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
---

# Proposal — `poll-heartbeat.sh` capture-hop (issue #922 implementation, phase 1)

## Request

Implement the design approved in
`docs/issue-922/proposals/default-on-per-cycle-monitor-report.md`
(product-discovery, merged #925): make `poll-heartbeat.sh`'s per-tick
stdout carry `roster_watchdog()`'s already-computed rich report
(per-session health, mechanical actions taken, empty-state lines)
instead of the current bare `"poll tick: due/skipped"` line, so the
Monitor notification channel actually reaches the user with readable
content every ~60s cycle — always, quiet or not.

## Constraints

- No new detection or response logic — `roster_watchdog()`'s
  classification and auto-respawn/auto-resume behavior are reused
  unchanged (survey, "What already exists").
- `poll-heartbeat.sh` must still de-dup against the shared TTL gate
  (`poll_rearm_arm_if_due`) — this proposal changes what happens to the
  watchdog's stdout on a due tick, not the due/skip decision itself.
- Existing test hooks (`POLL_HEARTBEAT_MAX_TICKS`,
  `POLL_HEARTBEAT_SLEEP_SECONDS`) and the `ORCHESTRATE_OFF` kill switch
  must keep working unchanged.
- Session-bound / interactive-only boundary stays as documented by the
  approved design — no attempt to make this survive a session's death
  or run headless.

## Rationale

The survey's "Unknowns" section names two ways to capture the
watchdog's stdout: (a) run `spawn.py watchdog --auto-respawn` in the
foreground on a due tick, capturing its stdout directly, instead of the
current `nohup ... &` detached launch; or (b) leave the launch detached
and tail `poll-watchdog.log` from the byte offset held at the start of
the tick.

This proposal picks (a), foreground capture, and rejects (b). Reason:
(b) requires `poll-heartbeat.sh` to track and persist a byte offset
across loop iterations (new state, new failure mode if the log rotates
or is truncated between ticks — the log is a shared append target
`nohup` also writes crash-recovery output to per
`on-the-record/hooks/poll-rearm.sh`'s own append-redirect), and still
races the detached process for a well-defined "this tick's output ends
here" boundary. (a) has no such race: `poll-heartbeat.sh` already waits
synchronously on `poll_rearm_arm_if_due`'s own `python3 ... poll-due`
call each tick (`on-the-record/hooks/poll-rearm.sh`, `poll_rearm_arm_if_due`
body), so adding one more synchronous call in the same due-branch is a
same-shape change, not a new async-coordination primitive. The cost —
`poll-heartbeat.sh`'s loop blocks for the watchdog's own runtime once
per due tick instead of firing-and-forgetting it — is accepted because
the watchdog already runs on the same 60s cadence via the two
turn-driven hooks (directive.sh, stop-poll-rearm.sh) that call the same
`poll_rearm_arm_if_due`, so its runtime is already a known, bounded
cost paid elsewhere in the same window; this proposal does not add a
new instance of that cost, only surfaces the one instance's output.

## What will be done

- In `poll-heartbeat.sh`, when a tick is due, replace the detached
  `nohup python3 spawn.py watchdog --auto-respawn >>log 2>&1 &`
  launch's stdout handling for THIS caller's echo with a foreground
  invocation whose stdout+stderr are captured into a shell variable,
  then that captured text is echoed verbatim as this tick's own
  stdout (in place of, or in addition to, the current
  `"poll tick: due, watchdog armed"` line — the rich report replaces
  the bare line since the report already implies the tick was due).
  The underlying watchdog CLI call itself is `spawn.py watchdog
  --auto-respawn` — the same command `poll-rearm.sh` already issues;
  this proposal does not duplicate the watchdog run, it changes
  `poll-heartbeat.sh`'s own stdout-echo step for the due branch to
  surface that same run's output instead of a static string.
  (Exact mechanism: whether `poll-heartbeat.sh` calls the watchdog
  itself and `poll-rearm.sh`'s existing detached launch is left as-is
  in parallel, or `poll_rearm_arm_if_due` is given a capture-and-return
  variant callable from `poll-heartbeat.sh`, is an implementation
  decision made during phase 2, inside this frozen write set, per the
  constraint that no new detection/response logic is added — either
  shape reuses the identical `spawn.py watchdog --auto-respawn`
  invocation and prints its stdout.)
- The quiet-tick path (`"poll tick: skipped (within TTL)"`) is
  unchanged — no watchdog run happens on a skipped tick, so there is no
  report to surface; the issue's "always report" requirement binds to
  the watchdog's own already-existing empty-state lines on a due tick
  with nothing in flight, not to fabricating a report on a skipped
  tick.
- `test_poll_heartbeat.py` gains two cases matching the approved
  design's acceptance scenarios: (1) empty roster, clean board-wide
  sweep → captured stdout contains the two existing empty-state lines
  verbatim; (2) an induced dead-poller/stalled-watch fixture → captured
  stdout contains the corresponding `STALLED`/`watcher-dead`/
  `[poll-report]` line, and where `roster_watchdog()` already
  auto-repairs (crashed-entry respawn) a `[resume]` confirmation line
  is present; where it only surfaces, no fix is claimed.

## Out of scope

- The #801 self-wake boundary — unchanged, cited, not re-litigated
  (per the approved design).
- Any change to `roster_watchdog()`'s classification or
  auto-respawn/auto-resume logic itself.
- Making the model's decision to render notification content to the
  user mandatory-every-tick — no such platform lever exists (per the
  approved design); this proposal only makes the notification content
  rich, not the rendering decision forced.
- The #776 harness scenario wiring itself (execution-observation, step
  3 of the issue's plan) — this proposal covers step 2 only.

## How you'll know it worked

`test_poll_heartbeat.py`'s two new cases pass locally
(`python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py`, to
be run and its pasted output cited in the phase-2 record once phase 2
is approved) — asserting the captured stdout for a due tick contains
the rich per-session report shape (or the empty-state pair) rather than
the bare `"poll tick: due, watchdog armed"` line, and that a skipped
tick's stdout is unchanged.

## Accumulation

Not accumulation-cost-shaped: a fixed capture-hop inside an existing
60s-cadence script, adding no new per-session or per-turn cost — the
watchdog invocation this proposal surfaces already runs on the same
cadence via the two turn-driven hooks; no new state persists across
ticks (foreground capture, no offset-tracking).

## What did not work

None.
