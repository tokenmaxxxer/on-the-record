#!/usr/bin/env python3
"""issue #1682: 여러 소비자가 같은 `gh api` URL 을 반복 조회할 때, 소비자
수만큼 요청이 늘어나지 않도록 하는 공유 온디스크 ETag/본문 읽기-통과
캐시. `gates/closure_sweep.py:_conditional_issue_list` 와 같은
ETag-조건부 패턴을 쓰되, 워크트리 로컬(`.git/`)이 아니라
`~/.tokenmaxxxer/gh-cache/` 아래에 둬서 워크트리가 다른 여러 소비자(다른
subject 브랜치, 다른 role 세션)가 캐시를 공유한다 — 그것이 이 모듈의
존재 이유다.

PR #1683 코멘트의 amendment(2026-08-16, on-record operator): 두 소비자 ->
"최소 하나의 전체 본문 페치"로 완화됐다 — 두 번째 소비자의 304
재검증(revalidation)은 그 자체로 "캐시 히트"로 카운트되고 위반이 아니다
(표준 HTTP 캐시 시맨틱, 304 는 쿼터 소비가 거의 0).

같은 코멘트의 BINDING 조건 4: 캐시 파일 쓰기는 원자적이어야 한다
(temp+rename) — 동시 소비자가 이 모듈의 전제이므로."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

DEFAULT_CACHE_ROOT = Path.home() / ".tokenmaxxxer" / "gh-cache"


def _cache_file(cache_root: Path, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_root / f"{digest}.json"


def _split_gh_api_i_output(stdout: str) -> tuple[int | None, dict[str, str], str]:
    """`gh api -i` 출력(상태줄 + 헤더 + 빈줄 + 바디) 파싱.
    `spawn._split_gh_api_i_output` 와 같은 계약이지만, gh_rest.py 처럼 이
    이슈의 write set 은 spawn.py 를 건드리지 않으므로 로컬 복제한다."""
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
        for part in lines[0].split():
            if part.isdigit():
                status = int(part)
                break
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return status, headers, body


def _atomic_write_json(path: Path, data: dict) -> None:
    """temp+rename — 조건 4: 동시 소비자가 부분 쓰기 파일을 읽지 않도록."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".gh-cache-", suffix=".tmp")
    except OSError:
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_name, path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def cached_get(url: str, root: Path | None = None, run: Callable | None = None,
                cache_root: Path | None = None) -> tuple[object | None, bool, int]:
    """`gh api <url>` 을 공유 캐시를 거쳐 조건부로 부른다.

    반환: `(data, ok, billed_calls)`.
    - `data`: 파싱된 JSON 본문(캐시 히트 시 디스크의 캐시된 본문).
    - `ok`: `gh` 호출/파싱이 성공했는가.
    - `billed_calls`: 이번 호출에서 실제로 나간 `gh api` 프로세스 실행
      수(1 또는 0). 304 재검증도 amendment 에 따라 1로 센다(실호출이
      나갔으므로) — "0 실호출"은 오직 캐시가 아예 호출을 생략할 때뿐인데,
      이 모듈은 항상 최소 조건부 호출 1회를 낸다(신선도를 보장하려면
      재검증이 필요하기 때문).
    캐시가 없거나 깨졌으면 무조건 재조회로 폴백한다(fail-open, `
    closure_sweep._conditional_issue_list` 와 같은 정책)."""
    run = run or subprocess.run
    cache_root = cache_root or DEFAULT_CACHE_ROOT
    cache_file = _cache_file(cache_root, url)

    etag = None
    cached_data = None
    try:
        if cache_file.exists():
            cached = json.loads(cache_file.read_text(encoding="utf-8"))
            etag = cached.get("etag")
            cached_data = cached.get("data")
            if not isinstance(etag, str):
                etag, cached_data = None, None
    except (OSError, ValueError, UnicodeDecodeError):
        etag, cached_data = None, None

    cmd = ["gh", "api", url, "--method", "GET", "-i"]
    if etag:
        cmd = cmd + ["-H", f"If-None-Match: {etag}"]
    try:
        r = run(cmd, cwd=root, capture_output=True, text=True)
    except OSError:
        return None, False, 0
    if r.returncode != 0:
        return None, False, 1

    status, headers, body = _split_gh_api_i_output(r.stdout)
    if status == 304 and cached_data is not None:
        return cached_data, True, 1

    try:
        data = json.loads(body)
    except ValueError:
        return None, False, 1

    new_etag = headers.get("etag")
    if new_etag:
        _atomic_write_json(cache_file, {"etag": new_etag, "data": data})
    return data, True, 1
