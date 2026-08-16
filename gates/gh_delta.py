#!/usr/bin/env python3
"""issue #1682: 변경-커서(change-cursor) 프로브. 워치독 틱마다 이슈/PR
전체를 다시 훑는 대신, 마지막으로 관측한 `updated_at` 커서 이후로
`since=` 조건부 조회 1회(무변경 틱이면 정확히 1회, 상세 조회 0회)만
낸다.

PR #1683 코멘트의 5개 BINDING 조건(전부 "조용한 델타 누락" 리스크라 각각
red test 필요):
1. 페이지네이션: `per_page` + `Link: rel="next"` 를 따라간다 — burst 가
   1페이지를 넘어도 조용히 잘리지 않는다. `max_pages` 초과는 명시적
   `full-rescan`.
2. 커서 전진: 커서는 이번 틱에 관측한 모든 항목의 `updated_at` 최댓값이다
   (로컬 시계 아님 — 스큐 위험). `since` 는 `>=` 필터라 경계 항목이 다음
   틱에 다시 보일 수 있다 — 의도된 중복 허용(코드 아래 주석 참고).
   커서 파일이 없거나 깨졌으면 `full-rescan`. 그와 별도로
   `last_reconciliation` + `reconcile_interval_hours` 로 주기적(기본
   24시간) 강제 전체 재훑기 훅을 둔다 — corruption 이 아니어도 드리프트
   교정.
3. PR: `GET /pulls` 는 `since` 파라미터가 없다. 그래서 `resource="pulls"`
   여도 `repos/{slug}/issues` 를 부른다(이슈+PR 을 다 돌려주고 `since` 를
   지원) — 응답에서 `pull_request` 키 유무로 클라이언트 필터링한다.
"""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

_VALID_RESOURCES = ("issues", "pulls")


def cursor_path(root: Path, resource: str) -> Path:
    return root / "runs" / f"gh_delta_cursor_{resource}.json"


def _split_gh_api_i_output(stdout: str) -> tuple[int | None, dict[str, str], str]:
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
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".gh-delta-", suffix=".tmp")
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


def _load_cursor(path: Path) -> dict | None:
    """커서 파일을 읽는다. 없거나, JSON 이 깨졌거나, 필수 필드(`since`)가
    없으면 `None` — 호출부는 이걸 명시적 `full-rescan` 사유로 쓴다(조건
    2: corruption 을 조용히 `since=None` 으로 뭉개지 않는다)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("since"), str):
        return None
    return data


def _hours_between(earlier: str, later: str) -> float:
    try:
        t1 = datetime.fromisoformat(earlier.replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(later.replace("Z", "+00:00"))
    except ValueError:
        return float("inf")
    return (t2 - t1).total_seconds() / 3600.0


def fetch_delta(root: Path, slug: str, resource: str, run: Callable | None = None,
                 now: str | None = None, per_page: int = 100, max_pages: int = 20,
                 reconcile_interval_hours: float = 24.0, path: Path | None = None,
                 include_prs: bool = False
                 ) -> tuple[list[dict] | None, str | None, str]:
    """`(items, new_cursor_since, classification)`.

    `include_prs` (issue #1688 PR-only-drop fix, additive default
    `False` — existing callers see no behavior change): when `True` and
    `resource="issues"`, the returned items are NOT filtered down to
    non-PR issues only — both issues and PR items from the same
    `repos/{slug}/issues` response (issue #1682 condition 3: that
    endpoint already returns both) are returned, so a PR-only-changed
    tick is no longer silently dropped to an empty changed-set. No
    extra `gh` call is spent — the PR items were already in the single
    probe response and previously discarded by the `pull_request not in
    i` filter.

    `classification` in {"delta", "no-change", "full-rescan", "error"}.
    - "no-change": 304(또는 빈 목록) — 상세 조회 0회로 이어져야 한다는
      신호. 정확히 프로브 호출 1회만 나간다(2페이지 이상 절대 안 감).
    - "full-rescan": 커서가 없거나 깨졌거나, 재훑기 주기가 지났거나,
      `max_pages` 를 넘겨 페이지네이션이 중단된 경우 — 이번 결과가
      "전체가 아닐 수 있음"을 호출부에 명시적으로 알린다.
    - `resource="pulls"` 여도 실제로는 `repos/{slug}/issues` 를 부른다
      (`/pulls` 에는 `since` 가 없으므로, 조건 3)."""
    if resource not in _VALID_RESOURCES:
        raise ValueError(f"unknown resource: {resource!r}")
    run = run or subprocess.run
    now = now or datetime.now(timezone.utc).isoformat()
    cpath = path or cursor_path(root, resource)

    cur = _load_cursor(cpath)
    forced_rescan = False
    if cur is None:
        since = None
        etag = None
        last_reconcile = now
        forced_rescan = True
    else:
        since = cur["since"]
        etag = cur.get("etag")
        last_reconcile = cur.get("last_reconciliation", since)
        if _hours_between(last_reconcile, now) >= reconcile_interval_hours:
            since = None
            etag = None
            forced_rescan = True

    items: list[dict] = []
    page = 1
    got_304 = False
    new_etag = etag
    page_overflow = False
    while True:
        cmd = ["gh", "api", f"repos/{slug}/issues", "--method", "GET",
               "-f", "state=all", "-f", "sort=updated", "-f", "direction=asc",
               "-f", f"per_page={per_page}", "-f", f"page={page}", "-i"]
        if since:
            cmd = cmd + ["-f", f"since={since}"]
        if etag and page == 1:
            cmd = cmd + ["-H", f"If-None-Match: {etag}"]
        try:
            r = run(cmd, cwd=root, capture_output=True, text=True)
        except OSError:
            return None, (cur["since"] if cur else None), "error"
        if r.returncode != 0:
            return None, (cur["since"] if cur else None), "error"

        status, headers, body = _split_gh_api_i_output(r.stdout)
        if page == 1 and status == 304:
            got_304 = True
            break
        try:
            data = json.loads(body)
        except ValueError:
            return None, (cur["since"] if cur else None), "error"
        if not isinstance(data, list):
            return None, (cur["since"] if cur else None), "error"
        items.extend(data)
        if page == 1:
            new_etag = headers.get("etag")
        has_next = "rel=\"next\"" in headers.get("link", "")
        if not has_next or not data:
            break
        page += 1
        if page > max_pages:
            page_overflow = True
            break

    if page_overflow:
        classification = "full-rescan"
    elif forced_rescan:
        classification = "full-rescan"
    elif got_304 or not items:
        classification = "no-change"
    else:
        classification = "delta"

    if resource == "pulls":
        filtered = [i for i in items if "pull_request" in i]
    elif include_prs:
        filtered = items
    else:
        filtered = [i for i in items if "pull_request" not in i]

    updated_ats = [i.get("updated_at") for i in items if isinstance(i.get("updated_at"), str)]
    if updated_ats:
        new_since = max(updated_ats)
    elif since:
        new_since = since
    else:
        new_since = cur["since"] if cur else now

    new_last_reconcile = now if (forced_rescan and not page_overflow) else last_reconcile
    _atomic_write_json(cpath, {
        "since": new_since,
        "etag": new_etag,
        "last_reconciliation": new_last_reconcile,
    })
    return filtered, new_since, classification
