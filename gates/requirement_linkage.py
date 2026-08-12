#!/usr/bin/env python3
"""요구 연결 앵커 게이트 (issue #1017, northpole req#6): 새로 드래프트된
이슈가 살아있는 요구 ID(`R\\d+` 또는 `northpole req#<n>`)를 인용하는지,
인용하지 않으면 명시적 `infrastructure/no-direct-requirement` 태그를
다는지 검사한다. drift guard(`spawn.py::requirement_drift`)는 이미
있는 이슈들을 사후에 훑어 advisory 로만 경고한다 — 이 게이트는 그
반대편, 이슈가 새로 드래프트되는(스폰되는) 시점에 구조적으로 막는다.
`acceptance_gate.py`와 같은 모양: 순수 `check_issue_body(issue, body)`
(네트워크 없이 단위테스트 가능) + `check(root, issue)` (gh 조회로
감싼다).

  python3 gates/requirement_linkage.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

_REQ_ID_RE = re.compile(r"\bR\d+\b")
_NORTHPOLE_REQ_RE = re.compile(r"northpole\s+req\s*#\s*\d+", re.IGNORECASE)
_INFRA_TAG = "infrastructure/no-direct-requirement"


def cited_requirement_ids(body: str) -> list[str]:
    """이슈 본문이 인용하는 요구 ID들 — 등장 순서를 보존한 중복제거
    리스트. spawn task 텍스트에 그대로 보여줄 때 순서가 안정적이어야
    한다(`spawn.py::_spawn_one`)."""
    body = body or ""
    seen: list[str] = []
    for m in _REQ_ID_RE.findall(body):
        if m not in seen:
            seen.append(m)
    for m in _NORTHPOLE_REQ_RE.findall(body):
        if m not in seen:
            seen.append(m)
    return seen


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    요구 ID 인용이 하나라도 있거나, 명시적 `infrastructure/no-direct-requirement`
    태그가 있으면 통과. 둘 다 없으면 위반 하나를 돌려준다."""
    body = body or ""
    if cited_requirement_ids(body):
        return []
    if _INFRA_TAG in body:
        return []
    return [f"이슈 #{issue} 본문이 요구 ID(`R\\d+` 또는 'northpole req#<n>')를 "
            f"하나도 인용하지 않고, 명시적 태그 '{_INFRA_TAG}' 도 없다 — "
            f"이 작업이 어느 요구를 향하는지 구조적으로 알 수 없다 "
            f"(issue #1017, northpole req#6)."]


def _issue_view_body(repo: Path, issue: int) -> str | None:
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "body"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    return data.get("body", "")


def check(repo: Path, issue: int) -> list[str]:
    body = _issue_view_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh issue view` 실패) — "
                f"검사 불가는 통과가 아니다."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    issue = int(sys.argv[1])
    repo = Path(".")
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1])
    bad = check(repo, issue)
    for b in bad:
        print(b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
