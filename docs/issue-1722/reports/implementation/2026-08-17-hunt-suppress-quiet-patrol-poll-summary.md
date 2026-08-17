---
proposal: docs/issue-1722/proposals/suppress-quiet-patrol-poll-summary.md
---

# Hunt record — suppress-quiet-patrol-poll-summary

## after-proposal — stance 1: does the quiet-tick suppression of `[patrol-poll] checked N role(s), M promotion(s)` in on-the-record/monitors/poll-heartbeat.sh break a sibling test suite that asserts the opposite for the same scenario?

Verdict: FINDING — the diff regresses gates/test_poll_heartbeat_patrol.py, a pre-existing sibling test suite (issue #1598) that drives the same poll-heartbeat.sh and asserts the summary line DOES fire on a quiet tick (0 promotions, no crash); 2 of its 3 tests now fail.
Kind: composition
Seed: git diff -- on-the-record/monitors/poll-heartbeat.sh on-the-record/monitors/test_poll_heartbeat.py (patrol summary printf wrapped in `if [ "${_patrol_promotions}" != "0" ] || [ "${_patrol_crashed}" = "1" ]; then ... fi`)
cap_seconds: not provided by dispatcher
tier: not provided by dispatcher
diff_stat_lines: 163 insertions(+), 2 deletions(-) across 2 files (git diff --stat)
started_at: 2026-08-17T19:40:00+09:00
ended_at: 2026-08-17T20:10:00+09:00

### Reproduce
```
python3 gates/test_poll_heartbeat_patrol.py
```
(run from repo root, on this working tree with the diff applied)

For comparison, on unmodified HEAD (`git stash` before running, `git stash pop` after) the same command passes all 3 tests.

### Observed
With the diff applied:
```
ok  t_kill_switch_suppresses_and_traces
FAIL t_no_board_role_zero_side_effects: 
FAIL t_patrol_invoked_only_on_nth_tick: 

2/3 failed: ['t_no_board_role_zero_side_effects', 't_patrol_invoked_only_on_nth_tick']
```
Both failures are `assert "[patrol-poll] checked 1 role(s), 0 promotion(s)" in r.stdout` — the fake patrol_promote.py in that suite returns zero promotions (a quiet tick with one configured role, no crash), so poll-heartbeat.sh's new gate now suppresses the line those tests require.

With `git stash` (diff removed) and the identical command:
```
ok  t_patrol_invoked_only_on_nth_tick
ok  t_kill_switch_suppresses_and_traces
ok  t_no_board_role_zero_side_effects

3/3 passed
```

### Expected
The diff's own test suite (on-the-record/monitors/test_poll_heartbeat.py) was updated to match the new quiet-tick-suppresses-summary behavior, but gates/test_poll_heartbeat_patrol.py — an independent, pre-existing suite covering the same code path (added under issue #1598, per its own docstring) — was not touched, so it still encodes the pre-#1722 contract ("checked 1 role(s), 0 promotion(s)" must appear on every patrol-due tick regardless of promotion count) and now fails against the changed script. Landing this diff without updating or retiring gates/test_poll_heartbeat_patrol.py leaves a red/stale test suite in the repo that nothing in the diff or its own test run surfaced (the task's own verification only ran on-the-record/monitors/test_poll_heartbeat.py, never gates/test_poll_heartbeat_patrol.py).
