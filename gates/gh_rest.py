#!/usr/bin/env python3
"""issue #1569: gh REST(`gh api repos/{owner}/{repo}/...`) 로 이슈/PR 본문을
읽는 공용 헬퍼. `gh issue view` / `gh pr view` 는 GraphQL 쿼터(시간당 5000)를
쓰는데, 이 쿼터는 PR/이슈 조회에 쓰이는 GraphQL 쿼터와 같은 풀을 공유한다.
REST 쿼터는 별도 풀이라 GraphQL 이 소진되어도 살아있다 — gates/hooks 의
읽기 전용 조회(본문 읽기)를 REST 로 옮기면 그 교차 풀 결합이 없어진다.

owner/repo 는 `git remote get-url origin` 으로 얻는다(로컬 git 명령, 쿼터
소비 없음) — `gh repo view` 는 그 자체로 또 GraphQL 호출이라 쓰지 않는다.

fail-closed 는 그대로다: REST 호출이 실패하면 None 을 돌려주고, 호출부가
"검사 불가는 통과가 아니다"로 거부한다."""
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

_REMOTE_RE = re.compile(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$")


def owner_repo(repo: Path, run: Callable | None = None) -> tuple[str, str] | None:
    run = run or subprocess.run
    try:
        r = run(["git", "remote", "get-url", "origin"], cwd=repo,
                capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    m = _REMOTE_RE.search(r.stdout.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _api_json(repo: Path, path: str, run: Callable | None = None) -> dict | None:
    run = run or subprocess.run
    owner_and_repo = owner_repo(repo, run=run)
    if owner_and_repo is None:
        return None
    owner, name = owner_and_repo
    try:
        r = run(["gh", "api", f"repos/{owner}/{name}/{path}"], cwd=repo,
                capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def fetch_issue(repo: Path, issue: int, run: Callable | None = None) -> dict | None:
    """title/body 를 한 번의 REST 호출로 함께 읽는다(제목+본문 둘 다
    필요한 호출부가 두 번 왕복하지 않도록)."""
    data = _api_json(repo, f"issues/{issue}", run)
    if data is None:
        return None
    return {"title": data.get("title", "") or "", "body": data.get("body", "") or ""}


def fetch_issue_body(repo: Path, issue: int, run: Callable | None = None) -> str | None:
    """이슈 본문. 실패(REST 실패, git remote 실패, gh 없음 포함) 시 None."""
    data = _api_json(repo, f"issues/{issue}", run)
    if data is None:
        return None
    return data.get("body", "") or ""


def fetch_issue_title(repo: Path, issue: int, run: Callable | None = None) -> str | None:
    data = _api_json(repo, f"issues/{issue}", run)
    if data is None:
        return None
    return data.get("title", "") or ""


def fetch_pr_body(repo: Path, pr: int, run: Callable | None = None) -> str | None:
    data = _api_json(repo, f"pulls/{pr}", run)
    if data is None:
        return None
    return data.get("body", "") or ""


def fetch_pr_title(repo: Path, pr: int, run: Callable | None = None) -> str | None:
    data = _api_json(repo, f"pulls/{pr}", run)
    if data is None:
        return None
    return data.get("title", "") or ""
