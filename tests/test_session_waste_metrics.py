"""Tests for scripts/session_waste_metrics.py — issue #2409's per-turn
waste-breakdown instrument (exploratory-Bash classification, hook-refusal
counting, redundant-same-file-re-read counting).

Run: python3 -m pytest tests/test_session_waste_metrics.py -q
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import session_waste_metrics as sw  # noqa: E402


def _write(lines: list) -> str:
    f = tempfile.NamedTemporaryFile("w", suffix=".session.log", delete=False,
                                    encoding="utf-8")
    for line in lines:
        f.write(json.dumps(line) + "\n")
    f.close()
    return f.name


def _tool_use(tool_use_id, name, input_=None):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": tool_use_id, "name": name, "input": input_ or {}}]}}


def _tool_result(tool_use_id, content="", is_error=False):
    return {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tool_use_id,
         "content": content, "is_error": is_error}]}}


# --------------------------------------------------------------- classify_bash

def test_pytest_variants_classified():
    assert sw.classify_bash("pytest -q") == "pytest"
    assert sw.classify_bash("python3 -m pytest tests/ -q") == "pytest"
    assert sw.classify_bash("python -m pytest -q") == "pytest"


def test_git_and_gh_classified():
    assert sw.classify_bash("git status --short") == "git"
    assert sw.classify_bash("gh pr create --title x") == "gh"


def test_leading_env_assignment_stripped_before_classifying():
    assert sw.classify_bash("FOO=bar git log -1") == "git"


def test_exploratory_shapes_classified_other():
    assert sw.classify_bash("grep -rn foo .") == "other"
    assert sw.classify_bash("find . -name '*.py'") == "other"
    # a compound command led by a non-git/gh/pytest token is "other",
    # matching how the issue's own 9,555-call count classified calls
    assert sw.classify_bash("echo hi && git status") == "other"


def test_empty_command_is_other():
    assert sw.classify_bash("") == "other"


# ------------------------------------------------- bash_classification_summary

def test_bash_classification_counts_and_share():
    events = [
        _tool_use("t1", "Bash", {"command": "pytest -q"}), _tool_result("t1"),
        _tool_use("t2", "Bash", {"command": "git status"}), _tool_result("t2"),
        _tool_use("t3", "Bash", {"command": "grep -rn foo ."}), _tool_result("t3"),
        _tool_use("t4", "Bash", {"command": "find . -name x"}), _tool_result("t4"),
    ]
    summary = sw.bash_classification_summary(events)
    assert summary == {"total": 4, "pytest": 1, "git": 1, "gh": 0,
                       "other": 2, "other_share": 0.5}


def test_bash_classification_empty_state_no_bash_calls():
    summary = sw.bash_classification_summary([])
    assert summary["total"] == 0
    assert summary["other_share"] is None


# ------------------------------------------------------------- hook_refusals

def test_hook_refusal_shape_matched_and_gate_extracted():
    events = [
        _tool_use("t1", "Bash", {"command": "git commit -m x"}),
        _tool_result("t1", content=(
            "PreToolUse:Bash hook error: "
            "[${CLAUDE_PLUGIN_ROOT}/hooks/pretooluse-dispatcher.sh]: "
            "heredoc-command-refusal-gate: heredoc-shaped commit "
            "message body detected"), is_error=True),
    ]
    report = sw.hook_refusals(events)
    assert report == {"total": 1, "by_gate": {"heredoc-command-refusal-gate": 1}}


def test_non_hook_error_not_counted_as_a_refusal():
    events = [
        _tool_use("t1", "Bash", {"command": "false"}),
        _tool_result("t1", content="Exit code 1\nsome ordinary failure", is_error=True),
    ]
    assert sw.hook_refusals(events) == {"total": 0, "by_gate": {}}


def test_multiple_gates_tallied_separately():
    events = [
        _tool_use("t1", "Edit", {"file_path": "docs/x/reports/implementation.md"}),
        _tool_result("t1", content=(
            "PreToolUse:Edit hook error: [/a/pretooluse-dispatcher.sh]: "
            "record-claim-guard: state claim with no canonical citation"),
            is_error=True),
        _tool_use("t2", "Bash", {"command": "gh pr create --body \"$(cat <<EOF\nx\nEOF\n)\""}),
        _tool_result("t2", content=(
            "PreToolUse:Bash hook error: [/a/pretooluse-dispatcher.sh]: "
            "heredoc-command-refusal-gate: heredoc-shaped --body detected"),
            is_error=True),
    ]
    report = sw.hook_refusals(events)
    assert report["total"] == 2
    assert report["by_gate"] == {"record-claim-guard": 1,
                                 "heredoc-command-refusal-gate": 1}


# --------------------------------------------------------- redundant_file_reads

def test_redundant_reads_collapse_across_offsets():
    events = [
        _tool_use("t1", "Read", {"file_path": "spawn.py", "offset": 1}), _tool_result("t1"),
        _tool_use("t2", "Read", {"file_path": "spawn.py", "offset": 500}), _tool_result("t2"),
        _tool_use("t3", "Read", {"file_path": "spawn.py", "offset": 900}), _tool_result("t3"),
    ]
    report = sw.redundant_file_reads(events)
    assert report["by_file"] == {"spawn.py": 3}
    assert report["top"] == [("spawn.py", 3)]


def test_single_read_not_flagged_as_redundant():
    events = [_tool_use("t1", "Read", {"file_path": "spawn.py"}), _tool_result("t1")]
    assert sw.redundant_file_reads(events)["by_file"] == {}


# ----------------------------------------------------------- named_offender_counts

def test_named_offenders_match_by_basename_regardless_of_directory():
    events = [
        _tool_use("t1", "Read", {"file_path": "/work/issue-9/spawn.py"}), _tool_result("t1"),
        _tool_use("t2", "Read", {"file_path": "/work/issue-9/spawn.py"}), _tool_result("t2"),
        _tool_use("t3", "Read",
                 {"file_path": "docs/issue-9/reports/implementation.md"}), _tool_result("t3"),
    ]
    offenders = sw.named_offender_counts(events, ["spawn.py", "implementation.md"])
    assert offenders == {"spawn.py": 2, "implementation.md": 0}


# -------------------------------------------------------------- per_turn_breakdown

def test_per_turn_breakdown_one_row_per_tool_use():
    events = [
        _tool_use("t1", "Bash", {"command": "pytest -q"}), _tool_result("t1"),
        _tool_use("t2", "Read", {"file_path": "spawn.py"}), _tool_result("t2"),
        _tool_use("t3", "Bash", {"command": "git commit -m x"}),
        _tool_result("t3", content=(
            "PreToolUse:Bash hook error: [/a/pretooluse-dispatcher.sh]: "
            "heredoc-command-refusal-gate: refused"), is_error=True),
    ]
    rows = sw.per_turn_breakdown(events)
    assert rows[0] == {"turn": 0, "tool": "Bash", "bash_class": "pytest"}
    assert rows[1] == {"turn": 1, "tool": "Read", "file_path": "spawn.py"}
    assert rows[2]["hook_refused"] == "heredoc-command-refusal-gate"


# --------------------------------------------------------------- analyze / batch

def test_analyze_empty_state_no_events():
    report = sw.analyze(_write([]))
    assert report["bash"]["total"] == 0
    assert report["hook_refusals"]["total"] == 0
    assert report["per_turn"] == []


def test_batch_summary_rolls_up_across_sessions():
    p1 = _write([_tool_use("t1", "Bash", {"command": "grep foo ."}), _tool_result("t1")])
    p2 = _write([
        _tool_use("t1", "Bash", {"command": "git status"}), _tool_result("t1"),
        _tool_use("t2", "Bash", {"command": "sed -n 1,5p x"}), _tool_result("t2"),
    ])
    summary = sw.batch_summary([p1, p2])
    assert summary["sessions"] == 2
    assert summary["bash_total"] == 3
    assert summary["bash_other_share"] == 2 / 3


def test_analyze_missing_path_reads_as_empty_not_an_exception():
    report = sw.analyze("/no/such/path.session.log")
    assert report["bash"]["total"] == 0
