---
status: proposed
files:
  - on-the-record/monitors/poll-heartbeat.sh
  - on-the-record/monitors/test_poll_heartbeat.py
  - gates/test_poll_heartbeat_patrol.py
---

## Request

Wire `gates/patrol_promote.py run` into the existing 120s poll-heartbeat
loop so a ticked board checkbox is promoted automatically, without a
human running `patrol_promote.py` by hand. Ride the loop at a reduced
cadence (~every 10 minutes) using its own counter, not the loop's
existing `tick`. Honor a kill-switch file. Skip roles that have no board
issue at zero extra cost.

## Constraints

- Must not touch the existing `tick`/`POLL_HEARTBEAT_MAX_TICKS`/rearm
  counting the loop already does — issue #1598 explicitly flags that a
  validity consult raised concern about reusing `#829`'s counting
  assumptions, and requires a regression test proving heartbeat/rearm
  behavior is byte-for-byte unchanged by this change.
- Idle patrol polls must cost 0 GitHub rate-limit points and 0 LLM
  tokens — `patrol_promote.py` already achieves this via
  `patrol_board.find_board_issue`'s ETag-conditional read; the wiring
  must not add a second, non-conditional read path.
- Kill-switch path is `.on-the-record/patrol-disabled` (E1/#1597's
  convention) — checked by plain existence, session builds directly
  against this path per the issue's stated parallel-safe note (E1 has
  not landed on this branch as of the survey).
- Only roles with an existing board issue get polled — zero calls for a
  role with none, in steady state.

## Rationale

Considered giving the promote-poll cadence its own long-period `sleep`
loop (a second background process, mirroring the pattern
`poll-heartbeat.sh` itself uses for the 120s cadence) instead of piggy-
backing on the existing loop's iterations. Rejected: issue #1598 asks
this to *ride* the existing heartbeat cadence specifically (not spawn a
second polling process), and a second sleep loop would double the number
of long-running background processes the monitor stack needs supervised
— more surface for the exact kind of counting/liveness bug the issue is
already worried about (#829's counting assumptions), for no benefit,
since the heartbeat already wakes every 120s regardless.

Considered reusing the loop's own `tick` variable directly (e.g. `if (
(tick % 5) == 0 )`) instead of adding a second counter. Rejected: the
issue's point 2 explicitly requires the promote-poll cadence to be its
own, separate state — sharing `tick` would make a future change to the
heartbeat's tick semantics (e.g. resetting `tick` on some other
condition) silently retime patrol promotion too, which is exactly the
coupling the validity consult flagged.

## What will be done

- In `on-the-record/monitors/poll-heartbeat.sh`, add a second in-process
  counter `patrol_tick=0`, incremented once per loop iteration
  independently of `tick`, gated by its own env var
  `POLL_HEARTBEAT_PATROL_EVERY_N` (default `5`, i.e. 5 x 120s = ~10
  minutes at the default sleep interval).
- The patrol_tick check runs unconditionally each loop iteration,
  **outside and independent of** the `if [ "${due_rc}" -eq 0 ]` branch —
  not folded into the due-gated `printed_text`/`diff_output`
  delta-suppression machinery, since that machinery only exists inside
  the due branch (warrant hunt finding, `hunt-patrol-heartbeat-wiring.md`:
  poll-due's TTL is shared with the turn-driven `directive.sh` hook, so a
  tick landing on the Nth patrol cadence is routinely non-due; folding
  patrol emission into the due-gated report would silently drop
  promotion trace lines on exactly those ticks). Patrol gets its own
  unconditional `printf` trace line, printed directly (not routed through
  the delta-suppression state file), so a patrol-due tick always prints
  something regardless of `due_rc`.
- On ticks where `patrol_tick % POLL_HEARTBEAT_PATROL_EVERY_N == 0`:
  - First check `.on-the-record/patrol-disabled` for existence; if
    present, `printf` one trace line (e.g. `[patrol-poll] disabled,
    skipped`) and do nothing else this tick.
  - Otherwise, for each role in `spawn.ROLES`, invoke
    `python3 gates/patrol_promote.py run <repo-root> <role>` and `printf`
    a one-line summary trace (role, promotions count, api_calls) per
    role with any promotions, plus a single `[patrol-poll] checked N
    role(s), M promotion(s)` summary line every patrol-due tick even
    when M is 0, so the tick is always observably distinguishable from a
    silently-skipped one. A role with no board issue costs the one
    ETag-conditional lookup `patrol_promote.py` already makes internally
    (0 billed calls in steady state); no separate skip-list is built in
    the shell loop, since `run_patrol_promote` already no-ops correctly
    for that case (confirmed in the survey).
- Add `gates/test_poll_heartbeat_patrol.py`: drives the real
  `poll-heartbeat.sh` (same harness pattern as
  `gates/test_poll_heartbeat_delta.py`) with a fake `patrol_promote.py`
  stub and `POLL_HEARTBEAT_PATROL_EVERY_N` set low, asserting (a) patrol
  is invoked only on every Nth tick, not every tick, (b) the kill-switch
  file suppresses invocation and produces the trace line, (c) a role
  with no fake board data still results in zero patrol side effects.
- Add one regression test to `on-the-record/monitors/test_poll_heartbeat.py`
  (or extend `gates/test_poll_heartbeat_delta.py`, whichever the existing
  suite structure fits better once inside the write set) asserting
  `tick`/`POLL_HEARTBEAT_MAX_TICKS` bounding and the existing
  watchdog/rearm-adjacent behavior produce identical output before and
  after this change, pinning that the new counter does not alter it.
- Live demonstration (acceptance): after landing, run the heartbeat
  script against a real repo checkout with a real board issue carrying a
  ticked checkbox, `POLL_HEARTBEAT_PATROL_EVERY_N=1` and a short sleep,
  and show the tick's trace line proving promotion rode the cadence path
  (no manual `patrol_promote.py run` invocation).

## Resolved findings

- `hunt-patrol-heartbeat-wiring.md` (design-error, after-proposal stance
  1): patrol emission folded into the due-gated delta-suppression
  machinery would silently drop trace lines on non-due ticks. Resolved
  above by giving patrol invocation its own unconditional emission path,
  independent of `due_rc`.

## Out of scope

- Any change to `patrol_promote.py` itself, `patrol_board.py`, or the
  rate-cap/anti-loop logic those already implement — this issue is pure
  wiring of an existing capability, not a change to promotion behavior.
- Building the kill-switch file writer/toggle (that is E1/#1597's own
  write set) — this session only reads the file's existence.
- Persisting `patrol_tick` across process restarts — it follows the same
  in-process-only convention the existing `tick` variable already uses;
  no new state file is introduced for the counter itself.

## How you'll know it worked

- `gates/test_poll_heartbeat_patrol.py` passes: Nth-tick cadence, own
  counter (not `tick`), kill-switch short-circuit with trace line, and
  no-board-issue role produces zero patrol side effects.
- The heartbeat/rearm regression test added to the existing suite passes,
  showing no change to pre-existing tick/watchdog/rearm output.
- The live demonstration run shows a real ticked checkbox promoted by the
  heartbeat path, with a trace line proving it rode the cadence, and no
  manual `patrol_promote.py` invocation in that run.
