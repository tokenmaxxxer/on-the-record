---
proposal: docs/issue-1719/proposals/returned-pr-and-board-sweep-delta-fix.md
---

# Hunt record — returned-pr-and-board-sweep-delta-fix

## after-proposal — stance 1: board-sweep lock-skip carry-forward vs. first_tick's unconditional-emit contract

Verdict: FINDING — on the very first-ever tick (no persisted state file yet), a board-sweep lock-contention-skip line is silently swallowed instead of being emitted like every other first-tick line, and the skip text itself is persisted as the "known" board-sweep state with no indication anything was suppressed.
Kind: silent-failure
Seed: on-the-record/monitors/poll-heartbeat.sh lines ~301-320 (new BOARD_SWEEP_LOCK_SKIP_RE branch inside the per-key diff loop)
cap_seconds: (not specified by dispatcher)
tier: default
diff_stat_lines: poll-heartbeat.sh +32/-8 (per `git diff --stat`); test_poll_heartbeat.py +3 tests; test_poll_heartbeat_delta.py 1 test rewritten
started_at: 2026-08-17T18:31:00Z
ended_at: 2026-08-17T18:46:00Z

### Reproduce
```
awk '/^import json$/{f=1} f{print} /^PY$/{if(f)exit}' on-the-record/monitors/poll-heartbeat.sh | sed '$d' > /tmp/poll_delta.py

rm -rf /tmp/pollstate_test && mkdir -p /tmp/pollstate_test/runs
export POLL_HEARTBEAT_TEXT='[watchdog] board-sweep: 건너뜀 (다른 워크스페이스가 스윕 중)
[poll-report] session-a: ok'
python3 /tmp/poll_delta.py /tmp/pollstate_test/runs/poll_heartbeat_last_state.json "$(date +%s)"
```
(no prior `poll_heartbeat_last_state.json` exists, i.e. this is the genuine first-ever tick — `first_tick = True`)

### Observed
```
[poll-report] session-a: ok
```
The `[watchdog] board-sweep: ...건너뜀...` line never appears in stdout, even though `first_tick` is True for this run. The persisted state file afterward is:
```json
{"lines": {"watchdog:board-sweep": "[watchdog] board-sweep: 건너뜀 (...)", "poll-report:session-a": "[poll-report] session-a: ok"}, ...}
```
i.e. the lock-skip text itself got stored as the board-sweep key's "known previous line" (via `new_lines[key] = prev_lines.get(key, line)` falling back to `line` because `prev_lines` is `{}` on first tick) — with no line ever printed for it. Nothing in the output indicates a board-sweep line was suppressed; the tick looks identical to one where no board-sweep tag was present in the input at all.

Control (same first tick, but board-sweep line is a normal, non-skip result instead) DOES emit as expected:
```
export POLL_HEARTBEAT_TEXT='[watchdog] board-sweep: swept 3 items
[poll-report] session-a: ok'
python3 /tmp/poll_delta.py /tmp/pollstate_test2/runs/poll_heartbeat_last_state.json "$(date +%s)"
```
→ both lines print, confirming first_tick's "emit everything" contract holds for every category except this new lock-skip branch.

### Expected
Every other line-key on the genuine first tick is emitted unconditionally (`first_tick or changed or ALWAYS_RE.search(line)` — `first_tick` alone forces `to_emit.append(line)`). The new `BOARD_SWEEP_LOCK_SKIP_RE` branch instead does `continue` before that check ever runs, so it is the one code path that ignores `first_tick` entirely. On a genuinely first-ever tick where the two workspaces' watchdogs happen to race and this one loses the board-sweep lock, the operator should still see *some* indication of board-sweep status appear once (per the existing first-tick "emit the full initial state once" acceptance in gates/test_poll_heartbeat_delta.py::t_fresh_state_first_tick_always_emits) rather than the tag vanishing with zero signal that a suppression rule fired at all. Neither of the two companion test suites' new tests (`t_board_sweep_lock_skip_treated_as_no_change` in on-the-record/monitors/test_poll_heartbeat.py, board-sweep case in gates/test_poll_heartbeat_delta.py) start from a fresh/first tick — both seed tick 1 with a *real* (non-skip) board-sweep result first, so this first-tick-is-a-skip interaction is untested and currently wrong.
