"""Observe-only composite runaway signal (issue #2961 Acceptance:
`-k runaway_signal_observe_only`, `-k runaway_signal_discrimination`,
`-k subagent_in_flight`).

`runaway_signal.py` reuses `trajectory_analyzer`'s existing OpenHands-
calibrated stall signals (never invents a detector) and adds a
conjunction rule: a runaway verdict requires >= 2 independent signals,
never one, and a session blocked on its own subagent is never a runaway
regardless of what else is true.

  python3 -m pytest tests/test_runaway_signal.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import runaway_signal as rs  # noqa: E402
import trajectory_analyzer as ta  # noqa: E402


def _assistant_tool_use(tool_use_id, name, tool_input):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": tool_use_id, "name": name, "input": tool_input}],
        "usage": {"input_tokens": 1, "output_tokens": 1}}}


def _tool_result(tool_use_id, is_error=False, tool_use_result=None):
    ev = {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tool_use_id, "is_error": is_error,
         "content": "ok"}]}}
    if tool_use_result is not None:
        ev["tool_use_result"] = tool_use_result
    return ev


def _result_event(**overrides):
    base = {"type": "result", "num_turns": 10, "duration_ms": 1000,
            "total_cost_usd": 0.1, "terminal_reason": "completed",
            "subagent_stats": {"spawned": 0, "completed": 0, "failed": 0}}
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# runaway_signal_discrimination
# --------------------------------------------------------------------------

def _serial_exploration_trajectory_2240_shape():
    """68 unique greps + 1 repeated one (69 total, matching the issue's own
    #2240 anatomy) — no repeats crossing the OpenHands threshold, no
    monologue, no ping-pong. Must NOT read as a runaway."""
    events = []
    for i in range(69):
        tid = f"t{i}"
        events.append(_assistant_tool_use(tid, "Bash", {"command": f"grep -rn pattern{i} ."}))
        events.append(_tool_result(tid))
    events.append(_result_event())
    return events


def _repeated_call_trajectory():
    """The same failing Edit repeated 4x (>= STUCK_REPEAT_OBSERVATION) AND
    the same Read offset repeated 3x — two independent signals, crossing
    this module's conjunction floor. Must read as a runaway."""
    events = []
    for i in range(4):
        tid = f"edit{i}"
        events.append(_assistant_tool_use(
            tid, "Edit", {"file_path": "x.py", "old_string": "a", "new_string": "b"}))
        events.append(_tool_result(tid))
    for i in range(3):
        tid = f"read{i}"
        events.append(_assistant_tool_use(tid, "Read", {"file_path": "big.py", "offset": 100}))
        events.append(_tool_result(tid))
    events.append(_result_event())
    return events


def test_runaway_signal_discrimination_2240_shape_reports_no_runaway():
    verdict = rs.runaway_verdict(_serial_exploration_trajectory_2240_shape())
    assert verdict["runaway"] is False
    assert verdict["signals"] == []


def test_runaway_signal_discrimination_repeated_call_shape_reports_runaway():
    verdict = rs.runaway_verdict(_repeated_call_trajectory())
    assert verdict["runaway"] is True
    assert len(verdict["signals"]) >= rs.MIN_SIGNALS_FOR_RUNAWAY


def test_runaway_signal_discrimination_never_fires_on_a_single_signal():
    """Acceptance must-not: a single thrash signal alone never terminates
    (here: never even reads as a runaway verdict)."""
    events = []
    for i in range(4):
        tid = f"edit{i}"
        events.append(_assistant_tool_use(
            tid, "Edit", {"file_path": "x.py", "old_string": "a", "new_string": "b"}))
        events.append(_tool_result(tid))
    events.append(_result_event())
    verdict = rs.runaway_verdict(events)
    assert verdict["signals"] == ["repeated-action-observation"]
    assert verdict["runaway"] is False


# --------------------------------------------------------------------------
# subagent_in_flight
# --------------------------------------------------------------------------

def test_subagent_in_flight_session_never_reported_as_runaway_even_with_other_signals():
    """A session with clear repeated-call thrash but ALSO a foreground
    Task dispatch still awaiting its tool_result must report as blocked,
    never as a runaway (issue #2214's guarantee, reused unmodified by the
    new composite signal)."""
    events = _repeated_call_trajectory()[:-1]  # drop the result event
    events.append(_assistant_tool_use("task1", "Task", {"prompt": "explore"}))
    assert ta.subagent_in_flight(events) is True
    verdict = rs.runaway_verdict(events)
    assert verdict["runaway"] is False
    assert verdict["blocked_on_subagent"] is True
    assert verdict["signals"] == []


def test_subagent_in_flight_backgrounded_dispatch_not_yet_notified_blocks():
    events = [_assistant_tool_use("bg1", "Agent", {"prompt": "explore"}),
              _tool_result("bg1", tool_use_result={"isAsync": True, "status": "async_launched"})]
    assert ta.subagent_in_flight(events) is True
    assert rs.runaway_verdict(events)["blocked_on_subagent"] is True


def test_subagent_in_flight_settled_dispatch_does_not_block():
    events = [_assistant_tool_use("bg1", "Agent", {"prompt": "explore"}),
              _tool_result("bg1", tool_use_result={"isAsync": True, "status": "async_launched"}),
              {"type": "system", "subtype": "task_notification", "tool_use_id": "bg1",
               "status": "completed"}]
    events.append(_result_event(subagent_stats={"spawned": 1, "completed": 1, "failed": 0}))
    assert ta.subagent_in_flight(events) is False


# --------------------------------------------------------------------------
# runaway_signal_observe_only
# --------------------------------------------------------------------------

def test_runaway_signal_observe_only_returns_data_never_raises_or_exits():
    """The composite signal is a pure function: no SystemExit, no
    exception, on any trajectory shape it is asked to classify."""
    for events in (_serial_exploration_trajectory_2240_shape(),
                   _repeated_call_trajectory(), [], [{"type": "assistant"}]):
        verdict = rs.runaway_verdict(events)
        assert isinstance(verdict, dict)
        assert "runaway" in verdict


def test_runaway_signal_observe_only_zero_finished_sessions_zero_verdicts(tmp_path):
    """Acceptance empty state: zero finished sessions means zero verdicts
    recorded, not an error. A still-running log (no terminal `result`
    event) does not count as finished."""
    still_running = tmp_path / "still-running.session.log"
    lines = [json.dumps(_assistant_tool_use("t1", "Bash", {"command": "echo hi"})),
             json.dumps(_tool_result("t1"))]
    still_running.write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = tmp_path / "does-not-exist.session.log"
    verdicts = rs.finished_session_verdicts([still_running, missing])
    assert verdicts == []


def test_runaway_signal_observe_only_records_one_verdict_per_finished_session(tmp_path):
    finished = tmp_path / "finished.session.log"
    events = _repeated_call_trajectory()
    finished.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    verdicts = rs.finished_session_verdicts([finished])
    assert len(verdicts) == 1
    assert verdicts[0]["session_log"] == str(finished)
    assert verdicts[0]["runaway"] is True


def test_runaway_signal_observe_only_mixed_batch_only_counts_finished_ones(tmp_path):
    """Equivalence-partition gap the test-derivation skill's review of
    this suite surfaced: the zero-verdicts and one-verdict tests above
    each exercise a pure batch (all-unfinished, all-finished). The
    realistic call shape — a sweep over live workspace logs — is mixed;
    this exercises the actual per-path filtering logic those two edge
    cases can't."""
    still_running = tmp_path / "still-running.session.log"
    still_running.write_text(
        json.dumps(_assistant_tool_use("t1", "Bash", {"command": "echo hi"})) + "\n",
        encoding="utf-8")
    finished_ok = tmp_path / "finished-ok.session.log"
    finished_ok.write_text(
        "\n".join(json.dumps(e) for e in _serial_exploration_trajectory_2240_shape()) + "\n",
        encoding="utf-8")
    finished_runaway = tmp_path / "finished-runaway.session.log"
    finished_runaway.write_text(
        "\n".join(json.dumps(e) for e in _repeated_call_trajectory()) + "\n",
        encoding="utf-8")
    verdicts = rs.finished_session_verdicts([still_running, finished_ok, finished_runaway])
    assert {v["session_log"] for v in verdicts} == {str(finished_ok), str(finished_runaway)}
    by_log = {v["session_log"]: v for v in verdicts}
    assert by_log[str(finished_ok)]["runaway"] is False
    assert by_log[str(finished_runaway)]["runaway"] is True
