#!/usr/bin/env python3
"""issue-1112 — consult self-hosted-hook-injection 회귀 테스트.

근본원인: `role_settings()`가 `cwd`가 on-the-record 체크아웃으로
잡히면(예: `-C` 없이 orchestrator 자기 자신의 작업 디렉터리) 자기
`hooks.json`(self_hosted_hooks())의 SessionStart/UserPromptSubmit 훅
세트를 매번 병합해 넣는다. #1097의 core-plugin 오버라이드 문장이 겨냥한
"core"-마켓플레이스 훅(freelunch/scout/warrant 등)과는 별개의 두 번째
주입 경로다 — 재시도 포함 매 시도마다 새 `claude -p` 프로세스가 이
주입 비용을 다시 치르며, 고정된 `CONSULT_TIMEOUT` 안에서 턴 예산을
잠식해 2026-08-12T17:29 / 2026-08-13T00:15:38 판단 JSON 미검출 재현과
합치한다. 구조적 수정: `role_settings()`에
`inject_self_hosted_hooks: bool = True` 키워드를 추가하고,
`consult_cmd()`/`_run_panel_session()` 두 판단-전용(저장소 미변경)
호출부만 `False`로 끈다. `spawn_cmd()` 계열(발급 경로)은 그대로 켜져
있어야 한다 — 그 세션은 실제로 저장소에 쓰기 때문에 board-gate/
approval-gate 등 자기 게이트가 필요하다.

네트워크·GitHub 없이 도는 것만(`gates/test_acceptance_gate.py`와 같은 관례).

  python3 gates/test_consult_json_parse.py
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


def _fake_run_no_json_both_attempts(calls):
    def fake_run(cmd, **kw):
        calls.append(kw.get("input", ""))
        text = "스카우트를 먼저 진행하겠습니다... (판단 JSON 없이 끝남)"
        payload = json.dumps({"result": text, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    return fake_run


def t_both_attempts_exhausted_raises_with_reported_symptom():
    """재현 대상 실패 형태: 두 시도(원본 + 재시도) 모두 판단 JSON 을
    못 찾으면, consult_cmd() 는 이슈가 인용한 정확한 증상 문구를 담은
    RuntimeError 를 내고, 트레이스에도 error: 줄이 남는다."""
    calls = []
    orig_run = spawn.subprocess.run
    orig_plugin_dirs = spawn.plugin_dirs
    orig_core_plugin_dirs = spawn.core_plugin_dirs
    orig_trace_path = spawn._consult_trace_path
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        spawn.subprocess.run = _fake_run_no_json_both_attempts(calls)
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue: root / "docs" / "consult-log.md"

        raised = None
        try:
            spawn.consult_cmd("implementation", "복잡한 설계 질문", cwd=str(root))
        except RuntimeError as e:
            raised = e

        assert raised is not None, "both attempts exhausted must raise RuntimeError"
        assert "모델 출력에서 판단 JSON 을 못 찾음" in str(raised)
        assert "재시도" in str(raised)
        assert len(calls) == 2, f"expected exactly one retry, got {len(calls)} attempts"

        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "error:" in trace
    finally:
        spawn.subprocess.run = orig_run
        spawn.plugin_dirs = orig_plugin_dirs
        spawn.core_plugin_dirs = orig_core_plugin_dirs
        spawn._consult_trace_path = orig_trace_path
        tmp.cleanup()


def _make_on_the_record_checkout(root: Path) -> Path:
    """`self_hosted_hooks()`가 진짜라고 인식할, 최소한의
    `on-the-record/hooks/hooks.json` 을 가진 체크아웃 픽스처."""
    hooks_dir = root / "on-the-record" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (hooks_dir / "hooks.json").write_text(json.dumps({
        "hooks": {
            "SessionStart": [{"hooks": [{"type": "command",
                                          "command": "on-the-record/hooks/self-update.sh"}]}]
        }
    }), encoding="utf-8")
    return root


def t_consult_cmd_settings_never_carry_self_hosted_hooks():
    """opt-out 이 실제로 배선됐는지: cwd 가 진짜 on-the-record 체크아웃
    모양이어도 consult_cmd() 가 만드는 settings 에는 그 hooks.json 이
    안 실린다 — 파라미터만 있고 안 쓰이는 회귀를 잡는다."""
    calls = []
    written_settings = []
    orig_run = spawn.subprocess.run
    orig_plugin_dirs = spawn.plugin_dirs
    orig_core_plugin_dirs = spawn.core_plugin_dirs
    orig_trace_path = spawn._consult_trace_path

    def fake_run(cmd, **kw):
        calls.append(kw.get("input", ""))
        settings_idx = cmd.index("--settings") + 1
        written_settings.append(json.loads(Path(cmd[settings_idx]).read_text()))
        payload = json.dumps({"result": '{"answer": "ok", "confidence": "low", "caveats": []}',
                               "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

    tmp = tempfile.TemporaryDirectory()
    try:
        root = _make_on_the_record_checkout(Path(tmp.name))
        spawn.subprocess.run = fake_run
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue: root / "docs" / "consult-log.md"

        spawn.consult_cmd("implementation", "질문", cwd=str(root))

        assert written_settings, "settings file must have been read by fake_run"
        assert "hooks" not in written_settings[0], \
            "consult_cmd() settings must not carry self-hosted hooks.json"
    finally:
        spawn.subprocess.run = orig_run
        spawn.plugin_dirs = orig_plugin_dirs
        spawn.core_plugin_dirs = orig_core_plugin_dirs
        spawn._consult_trace_path = orig_trace_path
        tmp.cleanup()


def t_run_panel_session_settings_never_carry_self_hosted_hooks():
    """같은 opt-out 이 `_run_panel_session()` 에도 배선됐는지 — 헌트가
    지적한 형제 호출부 드리프트를 이 테스트가 닫는다."""
    root = _make_on_the_record_checkout(Path(tempfile.mkdtemp()))
    try:
        s = spawn.role_settings("implementation", str(root), inject_self_hosted_hooks=False)
        assert "hooks" not in s, \
            "_run_panel_session()'s role_settings() call must opt out of self-hosted hooks"

        s_default = spawn.role_settings("implementation", str(root))
        assert "hooks" in s_default, \
            "sanity: default role_settings() call (spawn_cmd's) must still inject hooks"
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


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
