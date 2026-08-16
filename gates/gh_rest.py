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


def _split_gh_api_i_output(stdout: str) -> tuple[int | None, dict, str]:
    """`gh api -i` output (status line + headers + blank line + body)
    parsed for the status code and `Etag` header — issue #1681, same
    parse shape as `spawn._split_gh_api_i_output`, duplicated here so
    gh_rest.py stays dependency-free of spawn.py."""
    if "\r\n\r\n" in stdout:
        head, body = stdout.split("\r\n\r\n", 1)
        sep = "\r\n"
    elif "\n\n" in stdout:
        head, body = stdout.split("\n\n", 1)
        sep = "\n"
    else:
        return None, {}, stdout
    lines = head.split(sep)
    status = None
    if lines:
        for p in lines[0].split():
            if p.isdigit():
                status = int(p)
                break
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return status, headers, body


def _pr_poll_cache_path(repo: Path) -> Path:
    return repo / ".git" / "gh-read-cache" / "pr-poll.json"


def fetch_open_prs(repo: Path, run: Callable | None = None,
                    cache_path: Path | None = None) -> list[dict] | None:
    """issue #1681 hot path: the recurring PR-poll helper, REST + ETag-
    conditional (never GraphQL — `gh pr list --json` bills GraphQL
    quota, `gh api .../pulls` does not). Follows
    `patrol_board.find_board_issue`'s `gh api -i` + `If-None-Match` +
    304 pattern: an unchanged poll costs one REST call and bills no
    fresh data transfer, reusing the cached list on a 304. Returns
    `None` on any `gh`/git/parse failure (fail-closed, same convention
    as the other fetch_* helpers in this module)."""
    run = run or subprocess.run
    owner_and_repo = owner_repo(repo, run=run)
    if owner_and_repo is None:
        return None
    owner, name = owner_and_repo

    cache_path = cache_path or _pr_poll_cache_path(repo)
    etag = None
    cached_data = None
    try:
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            etag = cached.get("etag")
            cached_data = cached.get("raw")
            if not isinstance(etag, str):
                etag, cached_data = None, None
    except (OSError, ValueError, UnicodeDecodeError):
        etag, cached_data = None, None

    cmd = ["gh", "api", "-X", "GET", f"repos/{owner}/{name}/pulls",
           "-f", "state=open", "-f", "per_page=100", "-i"]
    if etag:
        cmd = cmd + ["-H", f"If-None-Match: {etag}"]
    try:
        r = run(cmd, cwd=repo, capture_output=True, text=True)
    except OSError:
        return None

    status, headers, body = _split_gh_api_i_output(r.stdout)
    # `gh api` exits non-zero on HTTP 304 — the status must be parsed
    # before the returncode check, or the cache-hit path never fires
    # (same pitfall noted at patrol_board.py:239-243).
    if r.returncode != 0 and status != 304:
        return None
    if status == 304:
        return cached_data

    try:
        data = json.loads(body)
    except ValueError:
        return None
    if not isinstance(data, list):
        return None

    new_etag = headers.get("etag")
    if new_etag:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({"etag": new_etag, "raw": data}),
                                   encoding="utf-8")
        except OSError:
            pass
    return data
