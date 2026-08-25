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


# --- issue #2231 residual gaps (from #2233's closing comment) ----------


def t_measurement_language_prose_bullet_classifies_as_judgment_not_file_existence():
    """PR #2222 live repro (issue #2210's Acceptance): a backtick names a
    script incidentally while the actual criterion is a comparative
    timing measurement. Falling through to file-existence mechanically
    FAILed a correct PR for a reason unrelated to its substance."""
    section = (
        "\n- check: an 8KB heredoc write through the real "
        "`pretooluse-dispatcher.sh` completes in a time comparable to a "
        "1KB one — measured, with both numbers in the record\n"
    )
    assert _types(section) == ["judgment"], check_runner.parse_checks(section)


def t_bare_artifact_path_without_measurement_language_stays_file_existence():
    """The fix is narrow: a bare artifact citation (no measurement
    language) is unaffected — t_bare_path_still_classifies_as_file_existence
    already pins the base case; this pins a slightly fuller sentence that
    still describes plain presence, not a measured comparison."""
    section = "\n- check: the generated digest lands at `digest.json`\n"
    assert _types(section) == ["file-existence"]


def t_cross_family_bare_identifier_classifies_as_judgment_not_file_existence():
    """issue #2278 regression pin — issue #2213 / PR #2255 live FAIL: a
    per-spawn measurement description backticks a bare identifier
    (`cross_family`), not a path. The old default (file-existence) FAILed
    a correct, execution-verified PR because no file named `cross_family`
    exists in the tree."""
    section = ("\n- check: per-spawn `cross_family` timing is recorded "
               "for 10+ spawns\n")
    assert _types(section) == ["judgment"], check_runner.parse_checks(section)


def t_work_in_english_skill_name_classifies_as_judgment_not_file_existence():
    """issue #2278 regression pin — issue #2208 / PR #2218 live FAIL: the
    backtick names a skill, not a path — old default FAILed 1/2 and
    blocked the merge gate until manually overridden."""
    section = ("\n- check: `work-in-english` is bound statically and "
               "verified by re-running the retrieval pipeline\n")
    assert _types(section) == ["judgment"], check_runner.parse_checks(section)


def t_genuinely_missing_path_shaped_artifact_still_classifies_as_file_existence_and_fails():
    """issue #2278: the inversion is narrow — a backtick that DOES look
    like a path (known extension, here `.json`) stays file-existence and
    genuinely FAILs when the file is actually absent."""
    section = "\n- check: the report lands at `missing_report.json`\n"
    checks = check_runner.parse_checks(section)
    assert [c["type"] for c in checks] == ["file-existence"], checks
    with tempfile.TemporaryDirectory() as td:
        results = check_runner.run_checks(Path(td), checks)
    assert results[0]["status"] == "fail", results


def t_bare_conventional_filename_and_dotfile_still_classify_as_file_existence_and_fail():
    """issue #2278 hunt finding: an extensionless conventional filename
    (`LICENSE`) or a dotfile (`.gitignore`) is still a real path — must
    stay file-existence and genuinely FAIL when absent, not silently
    downgrade to judgment (which would never mechanically check it)."""
    for token in ("LICENSE", ".gitignore"):
        section = f"\n- check: `{token}` is present at the repo root\n"
        checks = check_runner.parse_checks(section)
        assert [c["type"] for c in checks] == ["file-existence"], (token, checks)
        with tempfile.TemporaryDirectory() as td:
            results = check_runner.run_checks(Path(td), checks)
        assert results[0]["status"] == "fail", (token, results)


def t_all_judgment_checks_do_not_abort_run_checks_when_pre_filtered():
    """issue #2231 gap (a): main() must partition judgment out BEFORE
    calling run_checks, not discover the abort via JudgmentCheckError —
    otherwise an Acceptance section that is entirely judgment-shaped
    (PRs #2228/#2218) gets zero checks run and, historically, zero PR
    comment posted. This test pins the partition contract main() relies
    on: filtering type != 'judgment' always yields a run_checks-safe
    list, even when that list is empty."""
    section = "\n- check: the page looks right to a human\n"
    checks = check_runner.parse_checks(section)
    mechanical = [c for c in checks if c["type"] != "judgment"]
    judgment = [c for c in checks if c["type"] == "judgment"]
    assert mechanical == []
    assert len(judgment) == 1
    # run_checks is never called with judgment items by main() — nothing
    # to assert-not-raise here beyond the partition itself, since calling
    # run_checks([]) trivially returns [].
    assert check_runner.run_checks(Path("."), mechanical) == []


def t_format_no_checks_comment_reports_judgment_items_distinctly():
    j = [{"raw": "the page looks right to a human"}]
    out = check_runner.format_no_checks_comment(j)
    assert check_runner.NO_CHECKS_MARKER in out
    assert "the page looks right to a human" in out
    # byte-identical to the original empty-state text when there's
    # genuinely nothing (issue #2233's existing contract, unchanged):
    assert check_runner.format_no_checks_comment() == check_runner.format_no_checks_comment(None)


def t_format_comment_lists_skipped_judgment_items_outside_the_pass_total():
    results = [{"check": "`a`", "type": "test", "status": "pass", "output": ""}]
    skipped = [{"raw": "reviewers agree this reads well"}]
    out = check_runner.format_comment(results, skipped)
    assert "1/1 passed" in out
    assert "reviewers agree this reads well" in out


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
