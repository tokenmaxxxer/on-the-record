"""Tests for report-framing-check.sh (issue #320's semantic-effect framing)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "report-framing-check.sh"
REPO_ROOT = HOOKS_DIR.parent.parent

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

# issue-2039's own landed record carries skill-verdict: lines under
# docs/issue-2039/reports/ -- citing that issue makes these a
# >=1-mounted-skill delivery per issue #2044.
MOUNTED_SKILL_NO_UTILIZATION_REPORT = (
    "1단계 승인 요청: 이슈 #2039. [이슈 #2039] 스킬 검증 의무 · "
    "implementation → merge\n"
    "per-skill verdict 의무를 훅으로 강제하지 않던 문제를 해결했습니다. "
    "그동안 마운트된 스킬이 실제로 쓰였는지 아무도 확인할 수 없는 "
    "비용을 치렀는데, 이제 skill-verdict-guard 훅이 자동으로 검사해 "
    "새로 가능해졌습니다. 아직 gates.py CI 경로 연동은 남았습니다."
)

MOUNTED_SKILL_WITH_UTILIZATION_REPORT = (
    "1단계 승인 요청: 이슈 #2039. [이슈 #2039] 스킬 검증 의무 · "
    "implementation → merge\n"
    "per-skill verdict 의무를 훅으로 강제하지 않던 문제를 해결했습니다. "
    "그동안 마운트된 스킬이 실제로 쓰였는지 아무도 확인할 수 없는 "
    "비용을 치렀는데, 이제 skill-verdict-guard 훅이 자동으로 검사해 "
    "새로 가능해졌습니다. 마운트된 스킬 implementation-blueprint 는 설계 "
    "단계에 적용했고, tech-feasibility 는 이번 변경과 관련이 없어 "
    "not-applicable 로 판단했습니다. 아직 gates.py CI 경로 연동은 "
    "남았습니다."
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
        cwd=str(REPO_ROOT),
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


def t_mounted_skill_delivery_without_utilization_is_blocked():
    r = _run(MOUNTED_SKILL_NO_UTILIZATION_REPORT)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["decision"] == "block"
    assert "skills-utilization" in out["reason"]


def t_mounted_skill_delivery_with_utilization_is_silent():
    r = _run(MOUNTED_SKILL_WITH_UTILIZATION_REPORT)
    assert r.returncode == 0
    assert r.stdout == ""


def t_zero_skill_delivery_is_unaffected():
    # issue #320 carries no skill-verdict line under its reports/ -> the
    # fifth element is not required even though this is otherwise a
    # complete report.
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
