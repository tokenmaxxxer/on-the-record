---
proposal: none (build-now bypass, no phase-1 proposal — issue #2214)
---

# Hunt record — trajectory-analyzer

## before-landing — stance 0: assume the gate/guarantee just touched is bypassable — find a real input that breaks it.

Verdict: FINDING — a crashed/silently-dead backgrounded Task/Agent dispatch (isAsync ack seen, task_notification never arrives) makes `subagent_in_flight()` return True forever, which permanently zeroes the whole `advisory.stalled` report for the rest of the session — including real thrash signals (e.g. 5x identical repeated Bash calls) that have nothing to do with the dead subagent.
Kind: silent-failure
Seed: trajectory_analyzer.py `subagent_in_flight()` / `analyze()` (issue #2214 build-now delivery, no phase-1 proposal)
cap_seconds: 180
tier: size:200+lines/2-files
diff_stat_lines: ~691 (trajectory_analyzer.py + tests/test_trajectory_analyzer.py, new files)
started_at: 2026-08-24T00:00:00Z
ended_at: 2026-08-24T00:20:00Z

### Reproduce
```python
import json, tempfile
import trajectory_analyzer as ta

def tool_use(tid, name, input_=None):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": tid, "name": name, "input": input_ or {}}]}}

def tool_result(tid, is_error=False, text="ok"):
    return {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tid, "is_error": is_error, "content": text}]}}

lines = [
    # backgrounded subagent dispatch that then crashes silently -- no
    # task_notification ever arrives (process killed / crashed before it
    # could post its terminal notification), and the log never reaches a
    # terminal `result` event either.
    tool_use("agent1", "Agent", {"subagent_type": "warrant:warrant-hunter"}),
    {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "agent1", "is_error": False,
         "content": [{"type": "text", "text": "Async agent launched successfully."}]}]},
     "tool_use_result": {"isAsync": True, "status": "async_launched", "agentId": "abc123"}},
]
# Meanwhile the parent session itself gets stuck in real, unrelated
# repetition -- e.g. retrying the same health-check 5x -- a genuine
# stall signal that has nothing to do with waiting on the subagent.
for i in range(5):
    lines.append(tool_use(f"b{i}", "Bash", {"command": "git status"}))
    lines.append(tool_result(f"b{i}"))

f = tempfile.NamedTemporaryFile("w", suffix=".session.log", delete=False, encoding="utf-8")
for line in lines:
    f.write(json.dumps(line) + "\n")
f.close()

report = ta.analyze(f.name)
print("blocked_on_subagent:", report["blocked_on_subagent"])
print("observation_repeats:", report["repeated_tool_calls"]["observation_repeats"])
print("advisory:", report["advisory"])
```

### Observed
```
blocked_on_subagent: True
observation_repeats: [{'tool': 'Bash', 'input': {'command': 'git status'}, 'count': 5}]
advisory: {'stalled': False, 'reasons': [], 'note': 'advisory only — never terminates a session'}
```
`repeated_tool_calls` correctly detected a 5x identical-call thrash pattern (above the `STUCK_REPEAT_OBSERVATION = 4` threshold, unrelated to the subagent dispatch), but `analyze()`'s `if not blocked:` gate at line 340 discards it entirely because `subagent_in_flight()` is latched True by check (b) — an `isAsync` tool_result whose `tool_use_id` never reached `_task_notification_tool_use_ids()`. There is no timeout, no "gave up waiting" fallback, and no separation between "signals produced while polling the subagent" and "signals unrelated to the subagent that just happen to co-occur in the same log." A backgrounded subagent that dies without ever emitting `task_notification` (crash, OOM-kill, network drop before its terminal status post) is exactly the case the analyzer's own docstring flags as needing coverage — `subagent_stats.spawned > settled` (check c) is supposed to catch this once a `result` event exists, but check (b) fires first and returns `True` unconditionally in the loop over `uses`, so a `result` event with an honest `subagent_stats.killed` count is never even consulted for that tool_use_id (the function returns from inside the `for u in uses` loop before reaching the `subagent_stats` check).

### Expected
A dead/crashed subagent that never settles should not permanently and silently suppress the *entire* session's stall advisory. At minimum, `subagent_in_flight()`'s check (b) should stop treating an unsettled async dispatch as "in flight" once a terminal `result` event exists and `subagent_stats` shows it as no longer running (settled via completed/failed/killed, contradicting a lingering `isAsync` ack with no notification) — i.e. check (c) should be able to override/correct check (b) rather than being unreachable because (b) already returned. As implemented, one dead subagent silently and permanently blinds the entire advisory for the rest of the log, with no distinguishable signal that it happened (the report looks identical to "healthy, still legitimately waiting").
