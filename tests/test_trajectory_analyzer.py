"""Tests for trajectory_analyzer.py — issue #2214's post-hoc trajectory
analyzer over session stream-json logs.

Run: python3 -m pytest tests/test_trajectory_analyzer.py -q
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import trajectory_analyzer as ta  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "trajectory_logs"


def _write(lines: list[dict]) -> str:
    f = tempfile.NamedTemporaryFile("w", suffix=".session.log", delete=False,
                                    encoding="utf-8")
    for line in lines:
        f.write(json.dumps(line) + "\n")
    f.close()
    return f.name


def _tool_use(tool_use_id, name, input_=None):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": tool_use_id, "name": name, "input": input_ or {}}]}}


def _tool_result(tool_use_id, is_error=False, text="ok"):
    return {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tool_use_id,
         "is_error": is_error, "content": text}]}}


def _text_only(text="thinking out loud"):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def _result(**overrides):
    base = {"type": "result", "is_error": False, "num_turns": 1,
            "permission_denials": [], "usage": {"iterations": []}}
    base.update(overrides)
    return base


# --- empty-state (fixture corpus) -----------------------------------------

def test_empty_log_on_disk_analyzes_to_all_zero_metrics():
    report = ta.analyze(str(FIXTURES / "empty_admission_error.session.log"))
    assert report["event_count"] == 0
    assert report["harness_fields"]["denial_count"] == 0
    assert report["harness_fields"]["subagent_stats"] is None
    assert report["repeated_tool_calls"] == {"observation_repeats": [], "error_repeats": []}
    assert report["repeated_read_offsets"] == []
    assert report["edits_per_file"] == {}
    assert report["tool_mix_over_time"] == []
    assert report["agent_monologue_max_run"] == 0
    assert report["ping_pong_detected"] is False
    assert report["blocked_on_subagent"] is False
    assert report["advisory"] == {"stalled": False, "reasons": [],
                                  "note": "advisory only — never terminates a session"}


def test_missing_log_path_also_degrades_cleanly():
    report = ta.analyze("/nonexistent/path/does-not-exist.session.log")
    assert report["event_count"] == 0
    assert report["advisory"]["stalled"] is False


# --- harness-native fields --------------------------------------------------

def test_harness_fields_read_from_result_event_not_regex():
    lines = [_result(permission_denials=[{"tool_name": "Bash", "tool_use_id": "t1"}],
                     num_turns=7, terminal_reason="completed",
                     total_cost_usd=0.42,
                     usage={"iterations": [{"type": "message"}, {"type": "message"}]})]
    report = ta.analyze(_write(lines))
    hf = report["harness_fields"]
    assert hf["denial_count"] == 1
    assert hf["permission_denials"][0]["tool_name"] == "Bash"
    assert hf["num_turns"] == 7
    assert hf["terminal_reason"] == "completed"
    assert hf["total_cost_usd"] == 0.42
    assert len(hf["usage_iterations"]) == 2


def test_no_result_event_yields_empty_harness_fields():
    lines = [_tool_use("t1", "Bash", {"command": "ls"})]
    report = ta.analyze(_write(lines))
    hf = report["harness_fields"]
    assert hf["denial_count"] == 0
    assert hf["subagent_stats"] is None
    assert hf["num_turns"] is None


# --- repeated (tool, input) calls ------------------------------------------

def test_repeated_identical_observation_flagged_at_threshold_four():
    lines = []
    for i in range(4):
        lines.append(_tool_use(f"t{i}", "Bash", {"command": "git status"}))
        lines.append(_tool_result(f"t{i}", is_error=False))
    report = ta.analyze(_write(lines))
    obs = report["repeated_tool_calls"]["observation_repeats"]
    assert len(obs) == 1
    assert obs[0]["count"] == 4
    assert obs[0]["tool"] == "Bash"
    assert report["advisory"]["stalled"] is True
    assert "repeated-action-observation" in report["advisory"]["reasons"]


def test_three_repeats_below_observation_threshold_not_flagged():
    lines = []
    for i in range(3):
        lines.append(_tool_use(f"t{i}", "Bash", {"command": "git status"}))
        lines.append(_tool_result(f"t{i}", is_error=False))
    report = ta.analyze(_write(lines))
    assert report["repeated_tool_calls"]["observation_repeats"] == []
    assert report["advisory"]["stalled"] is False


def test_repeated_identical_error_flagged_at_threshold_three():
    lines = []
    for i in range(3):
        lines.append(_tool_use(f"t{i}", "Bash", {"command": "run-flaky-thing"}))
        lines.append(_tool_result(f"t{i}", is_error=True, text="boom"))
    report = ta.analyze(_write(lines))
    err = report["repeated_tool_calls"]["error_repeats"]
    assert len(err) == 1
    assert err[0]["count"] == 3
    assert "repeated-action-error" in report["advisory"]["reasons"]


def test_different_inputs_are_not_grouped_together():
    lines = []
    for i in range(4):
        lines.append(_tool_use(f"t{i}", "Bash", {"command": f"echo {i}"}))
        lines.append(_tool_result(f"t{i}"))
    report = ta.analyze(_write(lines))
    assert report["repeated_tool_calls"]["observation_repeats"] == []


# --- repeated Read offsets ---------------------------------------------------

def test_repeated_read_offset_counted():
    lines = []
    for i in range(3):
        lines.append(_tool_use(f"t{i}", "Read", {"file_path": "spawn.py", "offset": 100}))
        lines.append(_tool_result(f"t{i}"))
    lines.append(_tool_use("t9", "Read", {"file_path": "spawn.py", "offset": 500}))
    lines.append(_tool_result("t9"))
    report = ta.analyze(_write(lines))
    offsets = report["repeated_read_offsets"]
    assert len(offsets) == 1
    assert offsets[0] == {"file_path": "spawn.py", "offset": 100, "count": 3}


# --- edits-per-file ----------------------------------------------------------

def test_edits_per_file_counts_edit_and_write():
    lines = [
        _tool_use("t1", "Edit", {"file_path": "a.py"}),
        _tool_result("t1"),
        _tool_use("t2", "Write", {"file_path": "a.py"}),
        _tool_result("t2"),
        _tool_use("t3", "Edit", {"file_path": "b.py"}),
        _tool_result("t3"),
    ]
    report = ta.analyze(_write(lines))
    assert report["edits_per_file"] == {"a.py": 2, "b.py": 1}


# --- tool mix over time -------------------------------------------------------

def test_tool_mix_over_time_buckets():
    lines = []
    for i in range(12):
        name = "Bash" if i % 2 == 0 else "Read"
        lines.append(_tool_use(f"t{i}", name, {}))
        lines.append(_tool_result(f"t{i}"))
    report = ta.analyze(_write(lines))
    buckets = report["tool_mix_over_time"]
    assert len(buckets) == 2  # 12 tool calls / bucket_size=10 -> [10, 2]
    assert sum(buckets[0].values()) == 10
    assert sum(buckets[1].values()) == 2


# --- agent monologue -----------------------------------------------------------

def test_agent_monologue_run_of_three_flagged():
    lines = [_text_only(), _text_only(), _text_only()]
    report = ta.analyze(_write(lines))
    assert report["agent_monologue_max_run"] == 3
    assert "agent-monologue" in report["advisory"]["reasons"]


def test_agent_monologue_run_of_two_not_flagged():
    lines = [_text_only(), _text_only()]
    report = ta.analyze(_write(lines))
    assert report["agent_monologue_max_run"] == 0


def test_tool_use_between_text_breaks_the_monologue_run():
    lines = [_text_only(), _text_only(),
             _tool_use("t1", "Bash", {"command": "ls"}), _tool_result("t1"),
             _text_only(), _text_only()]
    report = ta.analyze(_write(lines))
    assert report["agent_monologue_max_run"] == 0


# --- ping-pong -----------------------------------------------------------------

def test_ping_pong_alternation_of_six_detected():
    lines = []
    for i in range(6):
        name = "Read" if i % 2 == 0 else "Grep"
        lines.append(_tool_use(f"t{i}", name, {"x": i}))
        lines.append(_tool_result(f"t{i}"))
    report = ta.analyze(_write(lines))
    assert report["ping_pong_detected"] is True
    assert "ping-pong" in report["advisory"]["reasons"]


def test_five_alternations_below_ping_pong_threshold():
    lines = []
    for i in range(5):
        name = "Read" if i % 2 == 0 else "Grep"
        lines.append(_tool_use(f"t{i}", name, {"x": i}))
        lines.append(_tool_result(f"t{i}"))
    report = ta.analyze(_write(lines))
    assert report["ping_pong_detected"] is False


# --- subagent in flight -> never reported stalled (issue #2214 Acceptance) ----

def test_session_blocked_on_open_subagent_task_is_not_stalled():
    # A Task tool_use with no matching tool_result yet — same shape as a
    # live log tee'd mid-Task. No repeat signal is possible from the block
    # itself (an in-flight dispatch has no settled tool_result to count),
    # so ordinary, non-repeating preceding work must not read as stalled.
    lines = []
    for i in range(4):
        lines.append(_tool_use(f"t{i}", "Bash", {"command": f"echo step-{i}"}))
        lines.append(_tool_result(f"t{i}"))
    lines.append(_tool_use("task1", "Task", {"description": "background hunt"}))
    # no _tool_result for "task1" — the subagent is still running
    report = ta.analyze(_write(lines))
    assert report["blocked_on_subagent"] is True
    assert report["advisory"]["stalled"] is False
    assert report["advisory"]["reasons"] == []


def test_dead_subagent_does_not_permanently_suppress_unrelated_thrash():
    # Regression for a before-landing warrant-hunt finding (issue #2214,
    # docs/issue-2214/reports/implementation/2026-08-24-hunt-trajectory-analyzer.md):
    # a crashed/silently-dead backgrounded subagent (async-launch ack seen,
    # its task_notification never arrives) held blocked_on_subagent True
    # forever — an earlier `if not blocked:` gate then discarded real,
    # unrelated thrash (here: 4 identical repeated Bash calls) for the
    # rest of the session. blocked_on_subagent and stalled must be
    # reported independently.
    lines = []
    for i in range(4):
        lines.append(_tool_use(f"t{i}", "Bash", {"command": "git status"}))
        lines.append(_tool_result(f"t{i}"))
    lines.append(_tool_use("agent1", "Agent", {"subagent_type": "warrant:warrant-hunter"}))
    lines.append({"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "agent1", "is_error": False,
         "content": [{"type": "text", "text": "Async agent launched successfully."}]}]},
        "tool_use_result": {"isAsync": True, "status": "async_launched",
                            "agentId": "dead-agent"}})
    # no task_notification ever arrives for "agent1" — the subagent died silently
    report = ta.analyze(_write(lines))
    assert report["blocked_on_subagent"] is True
    assert report["advisory"]["stalled"] is True
    assert "repeated-action-observation" in report["advisory"]["reasons"]


def test_subagent_stats_spawned_exceeds_settled_marks_blocked():
    lines = [_result(subagent_stats={"spawned": 2, "completed": 1, "failed": 0,
                                     "killed": {"parent": 0, "user": 0, "system": 0}})]
    report = ta.analyze(_write(lines))
    assert report["blocked_on_subagent"] is True


def test_backgrounded_agent_launch_ack_is_not_settlement():
    # Real shape (verified against an on-disk log, issue #1761's session):
    # a backgrounded `Agent` dispatch gets an immediate synthetic
    # tool_result acking the launch (tool_use_result.isAsync=true,
    # status="async_launched") — that ack must NOT read as "settled".
    # Only a later `task_notification` system event does.
    lines = [
        _tool_use("agent1", "Agent", {"subagent_type": "warrant:warrant-hunter"}),
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "agent1", "is_error": False,
             "content": [{"type": "text", "text": "Async agent launched successfully."}]}]},
         "tool_use_result": {"isAsync": True, "status": "async_launched",
                             "agentId": "abc123"}},
        {"type": "system", "subtype": "task_progress", "tool_use_id": "agent1",
         "task_id": "abc123"},
    ]
    report = ta.analyze(_write(lines))
    assert report["blocked_on_subagent"] is True
    assert report["advisory"]["stalled"] is False


def test_backgrounded_agent_task_notification_settles_it():
    lines = [
        _tool_use("agent1", "Agent", {"subagent_type": "warrant:warrant-hunter"}),
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "agent1", "is_error": False,
             "content": [{"type": "text", "text": "Async agent launched successfully."}]}]},
         "tool_use_result": {"isAsync": True, "status": "async_launched",
                             "agentId": "abc123"}},
        {"type": "system", "subtype": "task_notification", "tool_use_id": "agent1",
         "task_id": "abc123", "status": "completed"},
    ]
    report = ta.analyze(_write(lines))
    assert report["blocked_on_subagent"] is False


def test_subagent_fully_settled_is_not_blocked():
    lines = [
        _tool_use("task1", "Task", {"description": "hunt"}),
        _tool_result("task1", text="NO FINDING"),
        _result(subagent_stats={"spawned": 1, "completed": 1, "failed": 0,
                                "killed": {"parent": 0, "user": 0, "system": 0}}),
    ]
    report = ta.analyze(_write(lines))
    assert report["blocked_on_subagent"] is False


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
