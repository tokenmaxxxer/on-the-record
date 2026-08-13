"""issue-1202 requirement 5 — consult-sibling verbs (ideate/draft/review).

Extends the `gates/test_consult_json_parse.py` fixture style: fake
`subprocess.run` returns a canned session payload, `spawn.py`'s real
verb functions (`ideate_cmd`/`draft_cmd`/`review_cmd`) run against it, no
network/GitHub.

  python3 gates/test_consult_siblings.py
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


def _fake_run_ok(payload_json: str):
    def fake_run(cmd, **kw):
        payload = json.dumps({"result": payload_json, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    return fake_run


def _patched(root: Path, fake_run):
    """Context-manager-less patch/restore pair, same shape
    `test_consult_json_parse.py` already uses (opt-in per test, restored
    in `finally`)."""
    def _persist_raw_under(issue, ts, attempt, text):
        base = root / "docs" / (f"issue-{issue}" if issue is not None else "reports")
        out_dir = base / "reports" / "consult-raw-failures" if issue is not None \
            else base / "consult-raw-failures"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_ts = ts.replace(":", "").replace("+", "")
        path = out_dir / f"{safe_ts}-{attempt}.txt"
        path.write_text(text, encoding="utf-8")
        return path

    orig = {
        "run": spawn.subprocess.run,
        "plugin_dirs": spawn.plugin_dirs,
        "core_plugin_dirs": spawn.core_plugin_dirs,
        "trace_path": spawn._consult_trace_path,
        "persist_raw": spawn._persist_consult_raw_output,
    }
    spawn.subprocess.run = fake_run
    spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
    spawn.core_plugin_dirs = lambda: []
    spawn._consult_trace_path = lambda issue: root / "docs" / "consult-log.md"
    spawn._persist_consult_raw_output = _persist_raw_under
    return orig


def _restore(orig):
    spawn.subprocess.run = orig["run"]
    spawn.plugin_dirs = orig["plugin_dirs"]
    spawn.core_plugin_dirs = orig["core_plugin_dirs"]
    spawn._consult_trace_path = orig["trace_path"]
    spawn._persist_consult_raw_output = orig["persist_raw"]


def test_ideate_cmd_returns_traced_options_no_repo_writes():
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        payload = json.dumps({"options": ["A", "B"], "tradeoffs": ["A costs more"]})
        orig = _patched(root, _fake_run_ok(payload))
        try:
            result = spawn.ideate_cmd("implementation", "어떻게 나눌까?", cwd=str(root))
        finally:
            _restore(orig)

        assert result == {"options": ["A", "B"], "tradeoffs": ["A costs more"]}
        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "verb=ideate" in trace
        assert "ok:" in trace
        # No git/branch/PR side effect beyond the trace file itself.
        assert list(root.glob("**/*")) == [root / "docs", root / "docs" / "consult-log.md"]
    finally:
        tmp.cleanup()


def test_draft_cmd_returns_traced_draft_no_repo_writes():
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        payload = json.dumps({"draft": "초안 텍스트", "open_questions": ["범위는?"]})
        orig = _patched(root, _fake_run_ok(payload))
        try:
            result = spawn.draft_cmd("implementation", "README 초안", cwd=str(root))
        finally:
            _restore(orig)

        assert result["draft"] == "초안 텍스트"
        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "verb=draft" in trace
    finally:
        tmp.cleanup()


def test_review_cmd_returns_traced_findings_no_repo_writes():
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        payload = json.dumps({"findings": ["null 체크 누락"], "verdict": "보완 필요"})
        orig = _patched(root, _fake_run_ok(payload))
        try:
            result = spawn.review_cmd("implementation", "이 diff 검토", cwd=str(root))
        finally:
            _restore(orig)

        assert result["findings"] == ["null 체크 누락"]
        assert result["verdict"] == "보완 필요"
        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "verb=review" in trace
    finally:
        tmp.cleanup()


def test_verb_cmd_wrong_key_triggers_retry_then_raises():
    """ideate 요청에 `options` 키가 없는 JSON 만 두 번 다 돌아오면(자문의
    "answer" 미검출 재현과 같은 형태), 재시도 후 RuntimeError 로
    끝나고 트레이스에도 error: 가 남는다."""
    tmp = tempfile.TemporaryDirectory()
    try:
        root = Path(tmp.name)
        calls = []

        def fake_run(cmd, **kw):
            calls.append(kw.get("input", ""))
            payload = json.dumps({"result": '{"answer": "wrong key"}', "is_error": False})
            return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")

        orig = _patched(root, fake_run)
        try:
            raised = None
            try:
                spawn.ideate_cmd("implementation", "질문", cwd=str(root))
            except RuntimeError as e:
                raised = e
        finally:
            _restore(orig)

        assert raised is not None
        # 2 session attempts (base + 1 retry) + 2 git calls from
        # `_commit_consult_trace` (`add`, `commit`) share this same fake —
        # `spawn.subprocess.run` is patched globally, same as
        # `test_consult_json_parse.py`'s equivalent fixture.
        assert len(calls) == 4, f"expected 2 session attempts + 2 git calls, got {len(calls)}"
        trace = (root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        assert "error:" in trace
        assert "verb=ideate" in trace
    finally:
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
             if n.startswith("test_") and callable(f)]
    _run(tests)
