#!/usr/bin/env python3
"""issue-2073 — `check_runner.parse_checks`/`run_checks` 의 단위테스트.

초점은 두 가지다:
1. 인터프리터 허용목록에 `node`/`npx`/`deno`/`bun` 이 들어가, 산출물
   파싱 명령이 `file-existence` 로 오분류돼 한 번도 실행되지 않던 경로
   (tm-dicequest#44 가 초록으로 통과한 그 경로)가 닫힌다.
2. 선언된 런타임 산출물을 건드리는 명령은 `artifact-smoke` 타입으로
   분류되고 실제로 실행된다 — 선언이 없으면 분류 결과는 오늘과 같다.

네트워크·GitHub 없이 돈다.

  python3 gates/test_check_runner.py

issue-1323 req 2 의 단위테스트도 여기 있다 — 원래 `tests/test_check_runner.py`
에 있었지만, 같은 모듈을 검사하는 두 파일이 베이스네임을 공유하면
`gates/test_duplicate_test_basenames.py` 가 잡는 pytest 수집 충돌이 난다.
검사 대상 모듈 옆(`gates/`)에 한 파일로 합쳤다.
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import check_runner
import check_runner as cr


def _types(section, artifacts=None):
    return [c["type"] for c in check_runner.parse_checks(section, artifacts)]


def t_node_command_without_declaration_classifies_as_test_not_file_existence():
    """조사된 결함: `node --check dist/bundle.js` 가 `file-existence` 로
    분류돼 명령이 실행되는 대신 'dist 라는 파일이 있나'만 봤다."""
    section = "\n- check: `node --check dist/bundle.js`\n"
    assert _types(section) == ["test"], check_runner.parse_checks(section)


def t_npx_deno_bun_are_on_the_interpreter_allowlist():
    for verb in ("npx", "deno", "bun"):
        section = f"\n- check: `{verb} run x.js`\n"
        assert _types(section) == ["test"], (verb, check_runner.parse_checks(section))
    assert set(("node", "npx", "deno", "bun")) <= set(check_runner.INTERPRETERS)


def t_declared_artifact_command_classifies_as_artifact_smoke():
    section = "\n- check: `node --input-type=module --check dist/bundle.js`\n"
    checks = check_runner.parse_checks(section, ["dist/bundle.js"])
    assert [c["type"] for c in checks] == ["artifact-smoke"], checks
    assert checks[0]["artifact"] == "dist/bundle.js", checks
    assert checks[0]["command"] == "node --input-type=module --check dist/bundle.js"


def t_source_level_command_stays_test_even_with_a_declaration():
    section = "\n- check: `python3 -m pytest tests/test_sync.py -q`\n"
    assert _types(section, ["dist/bundle.js"]) == ["test"]


def t_classification_is_byte_identical_without_a_declaration():
    section = """
- check: `python3 -m pytest gates/test_x.py -q`
- check: `node --check dist/bundle.js`
- check: `docs/specs/artifact-smoke-contract.md`
- grep: ARTIFACT-SMOKE
- check: grep: ARTIFACT-SMOKE
- check: the reviewer agrees it reads well
"""
    assert check_runner.parse_checks(section) == \
        check_runner.parse_checks(section, None) == \
        check_runner.parse_checks(section, [])


def t_bare_path_still_classifies_as_file_existence():
    section = "\n- check: `README.md`\n"
    assert _types(section) == ["file-existence"]


def t_unclassifiable_check_is_still_judgment_and_refused_by_the_runner():
    section = "\n- check: the page looks right to a human\n"
    checks = check_runner.parse_checks(section, ["dist/bundle.js"])
    assert [c["type"] for c in checks] == ["judgment"], checks
    try:
        check_runner.run_checks(Path("."), checks)
    except check_runner.JudgmentCheckError:
        return
    raise AssertionError("judgment 검사는 실행 거부돼야 한다")


def t_artifact_smoke_check_actually_runs_and_fails_on_a_broken_artifact():
    """이 게이트의 요점: 산출물이 파싱되지 않으면 검사가 FAIL 이어야
    한다 — 존재만으로 통과하던 예전 file-existence 분류와의 차이."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "dist").mkdir()
        # node 가 없는 환경에서도 도는 파싱 검사로 같은 형태를 만든다:
        # 산출물이 존재하지만 파싱에 실패하는 경우.
        (repo / "dist" / "bundle.py").write_text("def broken(:\n")
        checks = [{"type": "artifact-smoke", "raw": "r",
                    "command": "python3 -m py_compile dist/bundle.py",
                    "artifact": "dist/bundle.py"}]
        results = check_runner.run_checks(repo, checks)
    assert results[0]["status"] == "fail", results
    assert results[0]["type"] == "artifact-smoke", results
    assert results[0]["artifact"] == "dist/bundle.py", results


def t_artifact_smoke_check_passes_when_the_artifact_parses():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "dist").mkdir()
        (repo / "dist" / "bundle.py").write_text("def fine():\n    return 1\n")
        checks = [{"type": "artifact-smoke", "raw": "r",
                    "command": "python3 -m py_compile dist/bundle.py",
                    "artifact": "dist/bundle.py"}]
        results = check_runner.run_checks(repo, checks)
    assert results[0]["status"] == "pass", results


def t_format_comment_names_the_artifact_smoke_type():
    results = [{"check": "r", "type": "artifact-smoke", "status": "pass"}]
    out = check_runner.format_comment(results)
    assert "(artifact-smoke)" in out, out
    assert "1/1 passed" in out, out


# --- issue-2233: bare `.py` gate path runs through pytest, doesn't crash --


def t_bare_py_gate_path_is_wrapped_to_run_through_pytest():
    """이 저장소가 실제로 가장 흔히 쓰는 `gate: \\`tests/test_x.py\\`` 형태
    (인터프리터 접두 없음) — 직접 exec 하면 실행권한이 없어 크래시하거나
    (issue #2233, PR #2223 라이브 실행에서 실측), 있어도 셔뱅 없인 뜻대로
    안 돈다. `python3 -m pytest`로 감싼다."""
    section = "\n- check: `tests/test_workspace_checkpoint.py`\n"
    checks = check_runner.parse_checks(section)
    assert checks == [{"type": "test", "raw": "`tests/test_workspace_checkpoint.py`",
                        "command": "python3 -m pytest tests/test_workspace_checkpoint.py"}]


def t_py_gate_path_with_explicit_interpreter_is_left_alone():
    section = "\n- check: `python3 -m pytest gates/test_x.py -q`\n"
    checks = check_runner.parse_checks(section)
    assert checks[0]["command"] == "python3 -m pytest gates/test_x.py -q"


def t_run_checks_records_a_failure_instead_of_crashing_on_unexecutable_command():
    """`OSError`(예: 실행권한 없음)를 잡아 FAIL 결과로 기록한다 — 검사
    하나를 못 돌린다고 러너 전체가 죽으면 안 된다(issue #2233)."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        target = repo / "not_executable.py"
        target.write_text("print(1)\n")
        # 실행권한을 명시적으로 뺀다 (checkout 직후엔 보통 이 상태다).
        target.chmod(0o644)
        checks = [{"type": "test", "raw": "r", "command": "./not_executable.py"}]
        results = check_runner.run_checks(repo, checks)
    assert results[0]["status"] == "fail", results
    assert "실행할 수 없다" in results[0]["output"], results


# --- issue-1323 req 2 (원래 tests/test_check_runner.py) --------------------


@pytest.fixture()
def fixture_pr_branch(tmp_path):
    """A local git repo/branch standing in for a PR branch checkout."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "existing.txt").write_text("hello world\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n")
    (repo / "tests" / "test_bad.py").write_text(
        "def test_bad():\n    assert False\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "pr-branch"], cwd=repo, check=True)
    return repo


def test_parse_checks_classifies_test_grep_file_existence_judgment():
    section = """
- check: `python3 -m pytest tests/test_ok.py`
- check: grep: hello world
- check: `existing.txt`
- check: this should just work somehow, trust me
"""
    checks = cr.parse_checks(section)
    kinds = [c["type"] for c in checks]
    assert kinds == ["test", "grep", "file-existence", "judgment"]


def test_run_checks_executes_test_check_for_real(fixture_pr_branch):
    checks = [{"type": "test", "raw": "`python3 -m pytest tests/test_ok.py`",
               "command": "python3 -m pytest tests/test_ok.py"}]
    results = cr.run_checks(fixture_pr_branch, checks)
    assert results[0]["status"] == "pass"


def test_run_checks_reports_failing_test(fixture_pr_branch):
    checks = [{"type": "test", "raw": "`python3 -m pytest tests/test_bad.py`",
               "command": "python3 -m pytest tests/test_bad.py"}]
    results = cr.run_checks(fixture_pr_branch, checks)
    assert results[0]["status"] == "fail"


def test_run_checks_grep_and_file_existence(fixture_pr_branch):
    checks = [
        {"type": "grep", "raw": "grep: hello world", "pattern": "hello world"},
        {"type": "file-existence", "raw": "`existing.txt`", "path": "existing.txt"},
        {"type": "file-existence", "raw": "`missing.txt`", "path": "missing.txt"},
    ]
    results = cr.run_checks(fixture_pr_branch, checks)
    assert [r["status"] for r in results] == ["pass", "pass", "fail"]


def test_run_checks_refuses_judgment_shaped_check(fixture_pr_branch):
    checks = [{"type": "judgment", "raw": "the team agrees this is good"}]
    with pytest.raises(cr.JudgmentCheckError):
        cr.run_checks(fixture_pr_branch, checks)


def test_format_comment_is_one_structured_block():
    results = [
        {"check": "`a`", "type": "test", "status": "pass", "output": ""},
        {"check": "`b`", "type": "file-existence", "status": "fail", "output": ""},
    ]
    body = cr.format_comment(results)
    assert body.count("## Acceptance check-runner result") == 1
    assert "1/2 passed" in body
    assert "[PASS]" in body and "[FAIL]" in body


def test_post_comment_builds_expected_gh_argv(monkeypatch, fixture_pr_branch):
    captured = {}

    def fake_run(argv, cwd, capture_output, text):
        captured["argv"] = argv
        captured["cwd"] = cwd
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    ok = cr.post_comment(42, "hello", fixture_pr_branch)
    assert ok is True
    assert captured["argv"] == ["gh", "pr", "comment", "42", "--body", "hello"]
    assert captured["cwd"] == fixture_pr_branch


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
