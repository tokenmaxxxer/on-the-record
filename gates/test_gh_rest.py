#!/usr/bin/env python3
"""issue #1569 — `gh_rest` 헬퍼의 hermetic 트랜스포트-스텁 테스트. 실제
네트워크/gh 없이, `run` 콜백을 주입해 REST 성공/실패/gh 부재를 재현한다.

  python3 gates/test_gh_rest.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest


def _ok(stdout: str):
    def run(argv, cwd=None, capture_output=True, text=True):
        if argv[:2] == ["git", "remote"]:
            return SimpleNamespace(returncode=0, stdout="git@github.com:owner/repo.git\n")
        return SimpleNamespace(returncode=0, stdout=stdout)
    return run


def _rest_fails():
    def run(argv, cwd=None, capture_output=True, text=True):
        if argv[:2] == ["git", "remote"]:
            return SimpleNamespace(returncode=0, stdout="git@github.com:owner/repo.git\n")
        return SimpleNamespace(returncode=1, stdout="")
    return run


def _no_gh():
    def run(argv, cwd=None, capture_output=True, text=True):
        return SimpleNamespace(returncode=127, stdout="")
    return run


def t_owner_repo_parses_ssh_remote():
    got = gh_rest.owner_repo(Path("."), run=_ok('{}'))
    assert got == ("owner", "repo"), got


def t_fetch_issue_body_returns_body_on_success():
    body = gh_rest.fetch_issue_body(Path("."), 1550, run=_ok('{"body": "hello"}'))
    assert body == "hello", body


def t_fetch_issue_body_returns_none_on_rest_failure():
    body = gh_rest.fetch_issue_body(Path("."), 1550, run=_rest_fails())
    assert body is None, body


def t_fetch_issue_body_returns_none_when_no_gh():
    body = gh_rest.fetch_issue_body(Path("."), 1550, run=_no_gh())
    assert body is None, body


def t_fetch_pr_body_returns_body_on_success():
    body = gh_rest.fetch_pr_body(Path("."), 42, run=_ok('{"body": "pr body"}'))
    assert body == "pr body", body


def t_fetch_issue_returns_title_and_body_together():
    got = gh_rest.fetch_issue(Path("."), 1550,
                               run=_ok('{"title": "t", "body": "b"}'))
    assert got == {"title": "t", "body": "b"}, got


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    _run([(n, f) for n, f in list(globals().items())
          if n.startswith("t_") and callable(f)])
