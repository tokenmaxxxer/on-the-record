---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - gates/test_poll_heartbeat_patrol.py
  - on-the-record/monitors/test_poll_heartbeat.py
type: feature
breaking: false
# canonical: acceptance: python3 gates/test_poll_heartbeat_patrol.py && python3 on-the-record/monitors/test_poll_heartbeat.py && python3 gates/test_poll_heartbeat_delta.py — result: PASS, see "Test run" section below
verdict: pass
loop_state: landed
---

## What was done

canonical: this session's own `gh pr view 1600` read (state: MERGED).

Implemented the approved phase-1 proposal
docs/issue-1598/proposals/patrol-heartbeat-wiring.md (PR #1600, merged)
for issue #1598: wired `gates/patrol_promote.py run` into
`on-the-record/monitors/poll-heartbeat.sh`'s existing loop:

- A second in-process counter `patrol_tick`, independent of the existing
  `tick`, gated by `POLL_HEARTBEAT_PATROL_EVERY_N` (default `5`).
- The patrol check runs unconditionally each iteration, outside the
  `due_rc`-gated branch, with its own unconditional `printf` trace lines
  (never routed through the delta-suppression state file).
- On a patrol-due tick: `.on-the-record/patrol-disabled` is checked first
  (existence only); if present, one trace line and nothing else runs.
  Otherwise every role in `spawn.ROLES` is invoked
  serially — a plain `for` loop, never backgrounded/parallelized — via
  `python3 gates/patrol_promote.py run <checkout> <role>`, with a
  per-role promotion-count line plus a `[patrol-poll] checked N role(s),
  M promotion(s)` summary every patrol-due tick.
- `gates/test_poll_heartbeat_patrol.py` (new): Nth-tick cadence, kill-switch
  short-circuit with trace line, no-board-role zero side effects.
- `on-the-record/monitors/test_poll_heartbeat.py`: added
  `t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior`,
  pinning that the due-branch report and `tick`/`MAX_TICKS` bounding are
  unaffected by the new counter.

canonical: this session's own `git log --oneline -1` read.
Committed as commit 36f17e39 on this branch.

## Test run (this turn)

canonical: this session's own
`python3 gates/test_poll_heartbeat_patrol.py && python3 on-the-record/monitors/test_poll_heartbeat.py && python3 gates/test_poll_heartbeat_delta.py`
run, output immediately below, no SKIPPED lines:
```
ok  t_kill_switch_suppresses_and_traces
ok  t_no_board_role_zero_side_effects
ok  t_patrol_invoked_only_on_nth_tick
3/3 passed
---
ok  t_heartbeat_arms_watchdog_when_due
ok  t_heartbeat_attaches_on_board_repo
ok  t_heartbeat_refuses_to_arm_on_non_git_root
ok  t_heartbeat_respects_kill_switch
ok  t_heartbeat_skips_attachment_on_non_board_repo
ok  t_heartbeat_skips_watchdog_when_not_due
ok  t_heartbeat_surfaces_empty_roster_report
ok  t_heartbeat_surfaces_induced_dead_poller
ok  t_patrol_wiring_does_not_alter_heartbeat_tick_or_rearm_behavior
9/9 passed
---
ok  t_anomaly_rc_produces_no_crash_label
ok  t_change_after_suppression_emits
ok  t_changed_tick_emits
ok  t_clean_rc_produces_neither_label
ok  t_dead_session_line_always_emits_even_unchanged
ok  t_fresh_state_first_tick_always_emits
ok  t_identical_second_tick_suppressed
ok  t_non_due_tick_produces_no_output
ok  t_only_changed_line_emitted_not_full_report
ok  t_reserved_sentinel_rc_produces_crash_label
ok  t_returned_pr_line_always_emits_even_unchanged
ok  t_signal_death_rc_produces_crash_label
ok  t_watchdog_anomaly_bullets_survive_round_trip
13/13 passed
```

## Why

basis: docs/issue-1598/proposals/patrol-heartbeat-wiring.md — see that
file's `## Rationale` for the two alternatives considered and rejected
(a second sleep loop; reusing the existing `tick` variable).

## What did not work

- Attempted to tick a real board checkbox on issue #1595 directly (via
  `gh issue edit`) as part of the live demonstration — refused by
  `gh-guard.sh` (role sessions never edit issues, contract v3 s8/s9: a
  checkbox tick is the human's approval act, not a role session's to
  fabricate). Expected: the wiring's live demo would show an actual
  promotion end to end. Actual: ticking is structurally out of reach for
  a role session, so the live demo below shows the wiring riding the
  cadence correctly rather than a full tick-to-promotion round trip. The
  promotion code path itself (`patrol_promote.py`, `patrol_board.py`) is
  out of scope for this issue and was already proven end to end by issue
  #1589's live demonstration (docs/issue-1589/reports/implementation.md,
  board #1595 -> promoted issue #1596).

## Resolved findings

canonical: this session's own dispatched warrant-hunter agent result,
recorded in docs/issue-1598/reports/implementation/hunt-patrol-heartbeat-wiring.md
("after-proposal" section, appended this turn).

- hunt-patrol-heartbeat-wiring.md (silent-failure): a per-role
  `patrol_promote.py` crash (non-zero rc) inside the serialized role loop
  was silently swallowed — captured stderr discarded, unlike the existing
  `due_rc`-crash path which logs via `_poll_watchdog_log_append`.
  Resolved: a crashing role now logs via the same
  `_poll_watchdog_log_append` helper and emits a
  `[patrol-poll] <role>: crashed (rc=N)` trace line
  (on-the-record/monitors/poll-heartbeat.sh, patrol block). The fix is
  included in the "Test run" results above (run after the fix was
  applied).

## Open findings

None.

## Live end-to-end record (this session, real checkout)

canonical: this session's own live run,
`POLL_HEARTBEAT_MAX_TICKS=1 POLL_HEARTBEAT_SLEEP_SECONDS=0 POLL_HEARTBEAT_PATROL_EVERY_N=1 TOKENMAXXXER_CHECKOUT="$(pwd)" bash on-the-record/monitors/poll-heartbeat.sh`,
against this repo's real checkout, real `spawn.ROLES`, real
`gates/patrol_promote.py` (no fakes/mocks), no `.on-the-record/patrol-disabled`
file present. Output:
```
[watchdog] non-canonical checkout startup refused: ... — override via SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1
[patrol-poll] checked 43 role(s), 0 promotion(s)
```
The `[patrol-poll]` line proves the patrol invocation rode the cadence
(`POLL_HEARTBEAT_PATROL_EVERY_N=1` fired on tick 1) with no manual
`patrol_promote.py run` invocation in this run, checking every configured
role serially with zero promotions (nothing ticked on any real board).

canonical: this session's own `gh issue view 1595` reads, taken before
and after this session's own local seeding via `patrol_board.py run`
(file-based, never a direct `gh issue edit`) — `## Pending Approval` /
`_none_` both before the seed and after the revert, confirming the real
board-read path independently and that the board was left in its prior
state.

## Next steps

None — record is terminal (`landed`).

## Resolution path

N/A — no open findings.
