#!/usr/bin/env python3
"""issue-1323 req 2 — `check_runner`의 단위테스트. 네트워크 없이,
로컬 git fixture 저장소(PR 브랜치 스탠드인)에 대해서만 돈다.

  python3 -m pytest tests/test_check_runner.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import check_runner as cr


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
