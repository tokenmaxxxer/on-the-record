#!/usr/bin/env python3
"""issue-1323 req 4 — `merge_gate` 단위테스트. fixture 보드/코멘트만
쓴다, 네트워크 없음. `gh` 는 argv 모양만 monkeypatch 로 검증한다
(`tests/test_check_runner.py` 의 `post_comment` 테스트 관례와 같다).

  python3 -m pytest tests/test_merge_gate.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))
import check_runner as cr  # noqa: E402
import merge_gate as mg  # noqa: E402


def test_parse_check_runner_result_all_pass():
    results = [{"check": "`a`", "type": "test", "status": "pass", "output": ""}]
    body = cr.format_comment(results)
    assert mg.parse_check_runner_result(body) == {"passed": 1, "total": 1}


def test_parse_check_runner_result_partial_fail():
    results = [
        {"check": "`a`", "type": "test", "status": "pass", "output": ""},
        {"check": "`b`", "type": "test", "status": "fail", "output": ""},
    ]
    body = cr.format_comment(results)
    assert mg.parse_check_runner_result(body) == {"passed": 1, "total": 2}


def test_parse_check_runner_result_non_matching_text():
    assert mg.parse_check_runner_result("hello, this is not a check-runner comment") is None


@pytest.fixture()
def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    docs = repo / "docs" / "issue-9002" / "reports"
    docs.mkdir(parents=True)
    (docs / "implementation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    (docs / "execution-observation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    (docs / "conformance-review.md").write_text("---\nloop_state: landed\n---\nbody\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_latest_check_runner_comment_builds_expected_argv(monkeypatch, fixture_repo):
    captured = {}

    def fake_run(argv, cwd, capture_output, text):
        captured["argv"] = argv
        captured["cwd"] = cwd
        class R:
            returncode = 0
            stdout = '{"comments": []}'
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = mg.latest_check_runner_comment(fixture_repo, 42)
    assert result is None
    assert captured["argv"] == ["gh", "pr", "view", "42", "--json", "comments"]
    assert captured["cwd"] == fixture_repo


def test_required_verification_missing_none(fixture_repo):
    assert mg.required_verification_missing(fixture_repo, "issue-9002") == []


def test_required_verification_missing_some(tmp_path):
    repo = tmp_path / "repo2"
    docs = repo / "docs" / "issue-9003" / "reports"
    docs.mkdir(parents=True)
    (docs / "execution-observation.md").write_text("---\nloop_state: landed\n---\nbody\n")
    assert mg.required_verification_missing(repo, "issue-9003") == ["conformance-review"]


def test_evaluate_comment_missing(monkeypatch, fixture_repo):
    monkeypatch.setattr(mg, "latest_check_runner_comment", lambda repo, pr: None)
    result = mg.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result["allowed"] is False
    assert any("코멘트" in r for r in result["reasons"])


def test_evaluate_check_runner_failing(monkeypatch, fixture_repo):
    body = cr.format_comment([
        {"check": "`a`", "type": "test", "status": "fail", "output": ""}])
    monkeypatch.setattr(mg, "latest_check_runner_comment", lambda repo, pr: body)
    result = mg.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result["allowed"] is False


def test_evaluate_verification_missing(monkeypatch, tmp_path):
    repo = tmp_path / "repo3"
    docs = repo / "docs" / "issue-9004" / "reports"
    docs.mkdir(parents=True)
    body = cr.format_comment([
        {"check": "`a`", "type": "test", "status": "pass", "output": ""}])
    monkeypatch.setattr(mg, "latest_check_runner_comment", lambda r, pr: body)
    result = mg.evaluate(repo, repo, 42, "issue-9004")
    assert result["allowed"] is False
    assert any("검증 기록" in r for r in result["reasons"])


def test_evaluate_all_clear(monkeypatch, fixture_repo):
    body = cr.format_comment([
        {"check": "`a`", "type": "test", "status": "pass", "output": ""}])
    monkeypatch.setattr(mg, "latest_check_runner_comment", lambda repo, pr: body)
    result = mg.evaluate(fixture_repo, fixture_repo, 42, "issue-9002")
    assert result == {"allowed": True, "reasons": []}
