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
    orig_persist_raw = spawn._persist_consult_raw_output
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        spawn.subprocess.run = _fake_run_no_json_both_attempts(calls)
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue: root / "docs" / "consult-log.md"
        spawn._persist_consult_raw_output = _persist_raw_under(root)

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
        spawn._persist_consult_raw_output = orig_persist_raw
        tmp.cleanup()


def _persist_raw_under(root: Path):
    """`_persist_consult_raw_output()`과 같은 경로 규칙(이슈 있으면
    issue 트리, 없으면 표준 reports/ 버킷)을, 실제 `ROOT` 대신 테스트
    fixture `root` 아래로 리다이렉트한다."""
    def _persist(issue, ts, attempt, text):
        base = root / "docs" / (f"issue-{issue}" if issue is not None else "reports")
        out_dir = base / "reports" / "consult-raw-failures" if issue is not None \
            else base / "consult-raw-failures"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_ts = ts.replace(":", "").replace("+", "")
        path = out_dir / f"{safe_ts}-{attempt}.txt"
        path.write_text(text, encoding="utf-8")
        return path
    return _persist


def _fake_run_long_no_json(calls):
    """00:35:18 재현 형태: 긴 다항 질문에 대해 설명만 길게 늘어놓고
    끝에 판단 JSON 객체를 한 번도 안 찍는다(트렁케이션과 구분하기 위해
    JSON 부재 자체를 재현)."""
    def fake_run(cmd, **kw):
        calls.append(kw.get("input", ""))
        text = (
            "이 트레이드오프에는 여러 축이 있습니다. 첫째, 성능과 유지보수성의 "
            "균형을 고려해야 하고, 둘째, 팀의 숙련도와 기존 코드베이스와의 "
            "일관성도 살펴야 합니다. 셋째, 장기적으로 이 결정이 다른 모듈에 "
            "미칠 영향도 검토가 필요합니다. 넷째, 마이그레이션 비용과 리스크도 "
            "무시할 수 없습니다. 이 모든 요소를 종합했을 때... "
        ) * 20
        payload = json.dumps({"result": text, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    return fake_run


def t_complex_question_persists_raw_output_on_parse_failure():
    """#1123 00:35:18 재현: 긴 다항 질문이 두 시도 모두 판단 JSON 없이
    끝나면, RuntimeError 메시지와 트레이스 줄 모두 원본 출력이 저장된
    사이드 파일 경로를 담고, 그 파일에는 실제 모델 출력 전문이 들어있다."""
    calls = []
    orig_run = spawn.subprocess.run
    orig_plugin_dirs = spawn.plugin_dirs
    orig_core_plugin_dirs = spawn.core_plugin_dirs
    orig_trace_path = spawn._consult_trace_path
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        spawn.subprocess.run = _fake_run_long_no_json(calls)
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue: root / "docs" / "consult-log.md"
        orig_persist_raw = spawn._persist_consult_raw_output
        spawn._persist_consult_raw_output = _persist_raw_under(root)

        long_question = (
            "다음 트레이드오프를 판단해줘: A안은 성능이 좋지만 유지보수가 "
            "어렵고, B안은 반대다. 팀 숙련도, 마이그레이션 비용, 장기 영향을 "
            "모두 고려했을 때 어느 쪽을 택해야 하고 그 이유는 무엇인가?"
        )
        raised = None
        try:
            spawn.consult_cmd("implementation", long_question, cwd=str(root))
        except RuntimeError as e:
            raised = e

        assert raised is not None, "both attempts exhausted must raise RuntimeError"
        assert "모델 출력에서 판단 JSON 을 못 찾음" in str(raised)
        assert "원본:" in str(raised), \
            "RuntimeError message must include the raw-output side-file path"

        raw_dir = root / "docs" / "reports" / "consult-raw-failures"
        raw_files = list(raw_dir.glob("*.txt"))
        assert len(raw_files) == 2, f"expected one raw file per attempt, got {raw_files}"
        assert "트레이드오프" in raw_files[0].read_text(encoding="utf-8")

        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "consult-raw-failures" in trace, \
            "trace line must point at the raw-output side file"
    finally:
        spawn.subprocess.run = orig_run
        spawn.plugin_dirs = orig_plugin_dirs
        spawn.core_plugin_dirs = orig_core_plugin_dirs
        spawn._consult_trace_path = orig_trace_path
        spawn._persist_consult_raw_output = orig_persist_raw
        tmp.cleanup()


def _fake_run_short_multi_clause_no_json(calls):
    """01:44/01:45 재현 형태: 짧지만(~60단어) 여러 판단절을 담은 질문에
    대해 판단 JSON 없이 끝난다 — 길이 단일 가설을 반증하는 케이스."""
    def fake_run(cmd, **kw):
        calls.append(kw.get("input", ""))
        text = "우선 A를 검토하고, B도 고려하고, C와의 상충도 살펴야 한다는 점에서..."
        payload = json.dumps({"result": text, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    return fake_run


def t_short_multi_clause_question_persists_raw_output_on_parse_failure():
    """#1123 두 번째 재현(길이-단일 가설 반증): 짧지만 여러 판단절을 담은
    질문도 같은 실패 모드를 재현하고, 같은 방식으로 원본이 저장된다."""
    calls = []
    orig_run = spawn.subprocess.run
    orig_plugin_dirs = spawn.plugin_dirs
    orig_core_plugin_dirs = spawn.core_plugin_dirs
    orig_trace_path = spawn._consult_trace_path
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        spawn.subprocess.run = _fake_run_short_multi_clause_no_json(calls)
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []
        spawn._consult_trace_path = lambda issue: root / "docs" / "consult-log.md"
        orig_persist_raw = spawn._persist_consult_raw_output
        spawn._persist_consult_raw_output = _persist_raw_under(root)

        short_question = "A를 할지, B를 할지, C와 상충은 없는지 판단해줘."
        raised = None
        try:
            spawn.consult_cmd("implementation", short_question, cwd=str(root))
        except RuntimeError as e:
            raised = e

        assert raised is not None, "both attempts exhausted must raise RuntimeError"
        assert "원본:" in str(raised), \
            "RuntimeError message must include the raw-output side-file path"

        raw_dir = root / "docs" / "reports" / "consult-raw-failures"
        raw_files = list(raw_dir.glob("*.txt"))
        assert len(raw_files) == 2, f"expected one raw file per attempt, got {raw_files}"
    finally:
        spawn.subprocess.run = orig_run
        spawn.plugin_dirs = orig_plugin_dirs
        spawn.core_plugin_dirs = orig_core_plugin_dirs
        spawn._consult_trace_path = orig_trace_path
        spawn._persist_consult_raw_output = orig_persist_raw
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
