---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/stop-poll-rearm.sh
  - tests/test_monitor_liveness.py
  - docs/handbooks/monitor-liveness.md
---

## Request

The plugin's poll-heartbeat Monitor was suspected dead on 2026-08-14;
the correction comment established it was actually alive and just
TTL-quiet (a busy turn cadence kept winning the shared `poll_due()` race
before the Monitor's own tick). The issue asks for: (1) event-volume
reduction so a real busy stretch never gives the harness's auto-stop
policy a reason to kill the Monitor, (2) a liveness stamp written every
due tick, (3) turn-driven hooks that detect stamp staleness and tell the
orchestrator to re-arm, and (4) explicit documentation that full-idle
death (no turns at all) cannot self-heal from inside the session.

## Constraints

- Do not touch `pytest.ini` or `tests/test_spawn.py` — issue #1490's
  write set, in flight.
- Volume reduction applies to the Monitor event/stdout channel only; the
  full watchdog report must keep landing in the tick log file.
- New staleness-detection code in the turn-driven hooks must respect the
  existing `ORCHESTRATE_OFF=1` kill switch and `CLAUDE_ROLE` exclusion
  those hooks already use.
- The re-arm directive line fires once per staleness episode, not once
  per turn while stale (no per-turn spam).

## Rationale

The survey (docs/issue-1497/reports/implementation/survey.md) found
requirement 1 already implemented by #1117/#1220's line-keyed delta
suppression — an alternative considered and rejected here is building a
**new** suppression layer on top of it (e.g. a second dedup pass keyed
differently). Rejected because the existing diff already satisfies req
1's stated behavior (quiet no-change tick, delta-only signal tick, full
report still in the log); a second layer would duplicate logic for no
behavioral gain and risks the two suppression layers disagreeing on what
counts as "changed." The plan is instead to add tests that pin the
existing behavior, so a future edit to the diff block cannot silently
regress req 1 without breaking a test.

For the liveness stamp (req 2), a second alternative considered was
reusing `poll_state.json`'s existing `last_poll` field directly as the
liveness signal. Rejected because that field is shared across three
callers (poll-heartbeat.sh and poll-rearm.sh's two hook call sites,
survey's "Death-vs-TTL-quiet mechanics" section) — a hook stamping it
would make the Monitor look alive even when it is the hook, not the
Monitor, that is running, defeating the exact disambiguation this issue
exists to add. A separate, Monitor-tick-owned stamp file avoids that
conflation.

## What will be done

1. `poll-heartbeat.sh`: add a small liveness-stamp write
   (`runs/poll_heartbeat_alive.json`, flock-guarded like `poll_due()`)
   inside the tick loop, run on every loop iteration regardless of
   whether that iteration is due — so staleness reflects the loop's own
   wake cadence, not the shared TTL race. No change to the existing
   quiet-tick / delta-suppression logic (already correct per survey).
2. `directive.sh` and `stop-poll-rearm.sh`: add a staleness check that
   reads the new stamp, compares its age to 3x the poll interval
   (default 180s), and — when stale — emits one
   "poll-heartbeat monitor dead since <ts> — re-arm via Monitor tool"
   line. De-dup state (a small sibling file recording the last-notified
   staleness episode) prevents repeating the line every turn while the
   condition persists; a fresh stamp clears the episode silently. Missing
   stamp (monitor never started this session) is treated as stale from
   the first check, per the issue's "empty state" acceptance note.
3. `tests/test_monitor_liveness.py`: the four acceptance tests
   (`test_quiet_tick_emits_nothing`, `test_delta_tick_emits_only_delta`,
   `test_stale_stamp_directive`, `test_fresh_stamp_silent`), using the
   existing `POLL_HEARTBEAT_MAX_TICKS` / `POLL_HEARTBEAT_SLEEP_SECONDS`
   test hooks for the bounded-loop cases.
4. `docs/handbooks/monitor-liveness.md`: document the liveness-stamp
   mechanism, the staleness threshold, and — per requirement 4 — the
   structural limit that full-idle death (no user turn, no monitor tick)
   cannot self-heal from inside the session, since the detection hooks
   are themselves turn-driven.

## Out of scope

- Any change to `tests/test_spawn.py` or `pytest.ini` (issue #1490).
- Building a new quiet-tick suppression mechanism — req 1 is already met
  by #1117/#1220's existing delta diff; only tests are added for it.
- An OS-level scheduled-execution primitive (cron/launchd/systemd timer)
  for true session-independent wake — already recorded as out of scope
  in docs/issue-801/proposals/technical-feasibility.md's "Hard boundary"
  section and restated by requirement 4 here.
- Changing `poll_state.json` / `poll_due()`'s existing shared-TTL
  semantics — the new stamp is additive, not a replacement.

## How you'll know it worked

- `pytest tests/test_monitor_liveness.py -v` passes all four tests
  listed in the issue's Acceptance section.
- Reading `poll-heartbeat.sh` after the change shows the stamp write
  inside the loop body, unconditional on the due branch.
- Reading `directive.sh`/`stop-poll-rearm.sh` after the change shows the
  staleness check gated the same way as their existing
  `ORCHESTRATE_OFF`/`CLAUDE_ROLE` guards, and the de-dup state preventing
  repeat lines.
- `docs/handbooks/monitor-liveness.md` states the full-idle structural
  limit explicitly, not implied.
