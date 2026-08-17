"""Tests for report-framing-check.sh (issue #320's semantic-effect framing)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "report-framing-check.sh"

ADDRESS_ONLY_REPORT = (
    "1단계 승인 요청: 이슈 #320, PR #481 이 올라왔습니다. "
    "[이슈 #320] 프레이밍 추가 · implementation → merge"
)

FOUR_ELEMENT_REPORT = (
    "1단계 승인 요청: 이슈 #320. [이슈 #320] 프레이밍 추가 · "
    "implementation → merge\n"
    "PR 보고를 address-only 로 보내던 문제를 해결했습니다. "
    "그동안 운영자가 매번 원문을 다시 읽어야 하는 비용을 치렀는데, "
    "이제 report-framing-check 훅이 자동으로 검사해 새로 가능해졌습니다. "
    "아직 hooks.json 의 다른 이벤트는 검토가 남았습니다."
)


def _run(message, role=None, orchestrate_off="", stop_hook_active=False):
    payload = json.dumps({
        "last_assistant_message": message,
        "stop_hook_active": stop_hook_active,
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_address_only_reply_is_blocked():
    r = _run(ADDRESS_ONLY_REPORT)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "reason" in out


def t_four_element_reply_is_silent():
    r = _run(FOUR_ELEMENT_REPORT)
    assert r.returncode == 0
    assert r.stdout == ""


def t_non_report_reply_is_silent():
    r = _run("네, 알겠습니다. 다음 단계로 진행하겠습니다.")
    assert r.returncode == 0
    assert r.stdout == ""


def t_role_session_is_noop():
    r = _run(ADDRESS_ONLY_REPORT, role="qa")
    assert r.returncode == 0
    assert r.stdout == ""


def t_orchestrate_off_is_noop():
    r = _run(ADDRESS_ONLY_REPORT, orchestrate_off="1")
    assert r.returncode == 0
    assert r.stdout == ""


def t_malformed_payload_fails_closed():
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    r = subprocess.run(["bash", str(HOOK)], input="not json",
                        capture_output=True, text=True, env=env, timeout=20)
    assert r.returncode == 2


def t_stop_hook_active_emits_nothing_for_address_only_reply():
    # issue #1725: a stop_hook_active turn must emit nothing at all, even
    # for a scenario that otherwise blocks with decision:"block".
    r = _run(ADDRESS_ONLY_REPORT, stop_hook_active=True)
    assert r.returncode == 0
    assert r.stdout == ""
