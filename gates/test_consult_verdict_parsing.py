#!/usr/bin/env python3
"""issue-1097 — consult 출력-파싱 경로 회귀 테스트.

근본원인: `consult_cmd()`가 core_plugin_dirs()를 그대로 물기 때문에
freelunch/scout/warrant 같이 저장소 배달물을 겨냥한 core 훅이 자문
세션에도 꽂힌다. 복잡한 판단 질문에서 모델이 그 훅들을 따라 스카우트/
제안서 절차로 먼저 들어가 턴 예산을 다 쓰고, 끝의 판단 JSON을 한 번도
못 찍은 채 세션이 끝나는 사례가 2026-08-12T07:38:43Z/07:39:01Z 두 번
연속 재현됐다(docs/reports/consult-log.md). 구조적 수정:
- `consult_cmd()`의 프롬프트에 이 지시들이 자문 세션에는 적용되지 않는다는
  명시적 무효화 문장을 넣는다.
- 판단 JSON을 못 찾으면 더 강한 리마인더로 1회 자동 재시도한다.

네트워크·GitHub 없이 도는 것만(`gates/test_acceptance_gate.py`와 같은 관례).

  python3 gates/test_consult_verdict_parsing.py
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import spawn


# 2026-08-12T07:42:13Z 라이브 `spawn.py consult requirements-engineering`
# 실행에서 실제로 받은 model 응답 텍스트를 그대로 캡처한 것 — 이슈 #1097
# acceptance의 "captured real transcript" 조건.
CAPTURED_REAL_TRANSCRIPT_RESULT = (
    '{\n'
    '  "answer": "예, 이 저장소는 pytest를 테스트 프레임워크로 사용한다 '
    '(pytest.ini, conftest.py, gates/test_*.py 다수 확인).",\n'
    '  "confidence": "high",\n'
    '  "caveats": [\n'
    '    "다른 언어/모듈에서 별도 테스트 프레임워크를 병행 사용할 가능성은 확인하지 않음"\n'
    '  ]\n'
    '}'
)


def t_parses_captured_real_transcript():
    got = spawn._parse_consult_verdict(CAPTURED_REAL_TRANSCRIPT_RESULT)
    assert got is not None, "captured real transcript must parse"
    assert got["confidence"] == "high"


def t_still_none_when_no_json_present():
    got = spawn._parse_consult_verdict("스카우트를 먼저 진행하겠습니다... (판단 JSON 없이 끝남)")
    assert got is None


def t_retries_once_and_recovers_when_first_attempt_has_no_json():
    """재현된 실패 형태: 첫 시도가 판단 JSON 없이 끝나도, 두번째(재시도)
    시도가 JSON을 내면 consult_cmd()는 성공으로 복구된다."""
    calls = []

    def fake_run(cmd, **kw):
        calls.append(kw.get("input", ""))
        if len(calls) == 1:
            text = "스카우트를 먼저 진행하겠습니다... (판단 JSON 없이 끝남)"
        else:
            text = '{"answer": "가능", "confidence": "medium", "caveats": []}'
        payload = json.dumps({"result": text, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

    orig_run = spawn.subprocess.run
    orig_plugin_dirs = spawn.plugin_dirs
    orig_core_plugin_dirs = spawn.core_plugin_dirs
    orig_trace_path = spawn._consult_trace_path
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        spawn.subprocess.run = fake_run
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue, cwd=None: root / "docs" / "consult-log.md"

        result = spawn.consult_cmd("implementation", "복잡한 설계 질문", cwd=str(root))

        assert len(calls) == 2, f"expected exactly one retry, got {len(calls)} attempts"
        assert "재시도" in calls[1], "retry attempt must carry a reinforced reminder"
        assert result["answer"] == "가능"

        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "ok:" in trace
    finally:
        spawn.subprocess.run = orig_run
        spawn.plugin_dirs = orig_plugin_dirs
        spawn.core_plugin_dirs = orig_core_plugin_dirs
        spawn._consult_trace_path = orig_trace_path
        tmp.cleanup()


def t_prompt_overrides_repo_mutating_core_directives():
    """근본원인 고정: 프롬프트 자체가 스카우트/제안서/위임 절차를
    무효화한다고 명시하는지 — 회귀 시 이 문구가 빠지면 실패한다."""
    calls = []

    def fake_run(cmd, **kw):
        calls.append(kw.get("input", ""))
        payload = json.dumps({"result": '{"answer": "ok", "confidence": "low", "caveats": []}',
                               "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

    orig_run = spawn.subprocess.run
    orig_plugin_dirs = spawn.plugin_dirs
    orig_core_plugin_dirs = spawn.core_plugin_dirs
    orig_trace_path = spawn._consult_trace_path
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        spawn.subprocess.run = fake_run
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue, cwd=None: root / "docs" / "consult-log.md"

        spawn.consult_cmd("implementation", "질문", cwd=str(root))

        assert calls, "subprocess.run must be invoked"
        assert "적용되지 않는다" in calls[0], "prompt must override repo-mutating core directives"
    finally:
        spawn.subprocess.run = orig_run
        spawn.plugin_dirs = orig_plugin_dirs
        spawn.core_plugin_dirs = orig_core_plugin_dirs
        spawn._consult_trace_path = orig_trace_path
        tmp.cleanup()


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
