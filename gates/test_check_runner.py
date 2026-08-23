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
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_runner


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
