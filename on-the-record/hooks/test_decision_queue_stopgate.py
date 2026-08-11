"""Tests for decision-queue-stopgate.sh (issue #466, carrying #374's design)."""
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "decision-queue-stopgate.sh"


def _fake_checkout(tmp_path, flows_payload):
    """Writes a stub spawn.py at tmp_path that prints flows_payload for
    `flows --json` and points TOKENMAXXXER_CHECKOUT at it."""
    spawn_py = tmp_path / "spawn.py"
    spawn_py.write_text(
        "import sys, json\n"
        "print(json.dumps(" + repr(flows_payload) + "))\n"
    )
    return tmp_path


def _run(flows_payload, role=None, orchestrate_off="", last_assistant_message="ok",
         session_id="test-session", state_dir=None):
    with tempfile.TemporaryDirectory() as td:
        checkout = _fake_checkout(Path(td), flows_payload)
        env = dict(os.environ)
        env["TOKENMAXXXER_CHECKOUT"] = str(checkout)
        env["ORCHESTRATE_OFF"] = orchestrate_off
        if state_dir is not None:
            env["OTR_DECISION_QUEUE_STOPGATE_STATE_DIR"] = str(state_dir)
        else:
            env.pop("OTR_DECISION_QUEUE_STOPGATE_STATE_DIR", None)
        if role:
            env["CLAUDE_ROLE"] = role
        else:
            env.pop("CLAUDE_ROLE", None)
        payload = json.dumps({
            "last_assistant_message": last_assistant_message,
            "session_id": session_id,
        })
        return subprocess.run(
            ["bash", str(HOOK)],
            input=payload, capture_output=True, text=True, env=env, timeout=20,
        )


def t_empty_queue_is_silent():
    r = _run({"decision_queue": []})
    assert r.returncode == 0
    assert r.stdout == ""


def t_under_1h_item_is_silent():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 0.5},
    ]})
    assert r.returncode == 0
    assert r.stdout == ""


def t_1h_to_4h_item_gets_additional_context():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 2.0},
    ]})
    assert r.returncode == 0
    out = json.loads(r.stdout)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "#100" in ctx
    assert "PR#200" in ctx
    assert "2.0h" in ctx


def t_4h_plus_item_blocks():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 4.5},
    ]})
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "#100" in out["reason"]
    assert "PR#200" in out["reason"]


def t_mixed_tiers_reports_only_tier2_block():
    r = _run({"decision_queue": [
        {"issue": 1, "pr": 11, "age_hours": 0.2},
        {"issue": 2, "pr": 22, "age_hours": 2.0},
        {"issue": 3, "pr": 33, "age_hours": 5.0},
    ]})
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "#3" in out["reason"]


def t_orchestrate_off_is_silent():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 5.0},
    ]}, orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""


def t_role_session_is_silent():
    r = _run({"decision_queue": [
        {"issue": 100, "pr": 200, "age_hours": 5.0},
    ]}, role="implementation")
    assert r.returncode == 0
    assert r.stdout == ""


# --- issue #600: waiting-declaration turn-occupancy branch ---

def t_waiting_declaration_over_fresh_queue_blocks():
    with tempfile.TemporaryDirectory() as state_dir:
        r = _run({"decision_queue": [
            {"issue": 600, "pr": 615, "age_hours": 0.3},
        ]}, last_assistant_message="대기 중입니다. 사용자의 결정을 기다리는 중.",
            state_dir=state_dir)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["decision"] == "block"
        assert "규칙 4" in out["reason"] or "rule 4" in out["reason"]


def t_queue_relay_that_closes_turn_is_not_blocked_by_new_branch():
    with tempfile.TemporaryDirectory() as state_dir:
        r = _run({"decision_queue": [
            {"issue": 600, "pr": 615, "age_hours": 0.3},
        ]}, last_assistant_message=(
            "결정 큐: #600/PR#615 (0.3h). background 로 observation 을 걸고 "
            "턴을 닫습니다."
        ), state_dir=state_dir)
        assert r.returncode == 0
        assert r.stdout == ""


# --- issue #692: bound the waiting-declaration block to once per run ---

def t_consecutive_waiting_declaration_second_stop_not_blocked():
    """After one waiting-declaration block, a second consecutive Stop in
    the same session is not blocked."""
    with tempfile.TemporaryDirectory() as state_dir:
        queue = {"decision_queue": [
            {"issue": 692, "pr": 693, "age_hours": 0.3},
        ]}
        msg = "대기 중입니다. 사용자의 결정을 기다리는 중."
        r1 = _run(queue, last_assistant_message=msg, session_id="s1",
                   state_dir=state_dir)
        assert r1.returncode == 0
        out1 = json.loads(r1.stdout)
        assert out1["decision"] == "block"

        r2 = _run(queue, last_assistant_message=msg, session_id="s1",
                   state_dir=state_dir)
        assert r2.returncode == 0
        assert r2.stdout == ""


def t_waiting_declaration_block_reason_names_queue_items_and_escape():
    with tempfile.TemporaryDirectory() as state_dir:
        r = _run({"decision_queue": [
            {"issue": 692, "pr": 693, "age_hours": 0.3},
        ]}, last_assistant_message="대기 중입니다. 사용자의 결정을 기다리는 중.",
            session_id="s1", state_dir=state_dir)
        out = json.loads(r.stdout)
        assert "#692" in out["reason"]
        assert "PR#693" in out["reason"]
        assert "one-shot" in out["reason"].lower() or "One-shot" in out["reason"]


def t_latch_resets_after_non_waiting_stop_catches_later_stall():
    with tempfile.TemporaryDirectory() as state_dir:
        queue = {"decision_queue": [
            {"issue": 692, "pr": 693, "age_hours": 0.3},
        ]}
        waiting_msg = "대기 중입니다. 사용자의 결정을 기다리는 중."
        r1 = _run(queue, last_assistant_message=waiting_msg, session_id="s1",
                   state_dir=state_dir)
        assert json.loads(r1.stdout)["decision"] == "block"

        # A non-waiting Stop (arm marker present) resets the latch.
        r2 = _run(queue, last_assistant_message=(
            "background 로 observation 을 걸고 턴을 닫습니다."
        ), session_id="s1", state_dir=state_dir)
        assert r2.returncode == 0
        assert r2.stdout == ""

        # A later, unrelated bare waiting declaration is caught again.
        r3 = _run(queue, last_assistant_message=waiting_msg, session_id="s1",
                   state_dir=state_dir)
        assert r3.returncode == 0
        assert json.loads(r3.stdout)["decision"] == "block"
