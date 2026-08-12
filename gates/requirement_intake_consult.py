#!/usr/bin/env python3
"""요구사항 인테이크 타당성 자문 게이트 — 새로 작성된 이슈 본문이
`validity-consult:` 트레이스 참조 또는 닫힌 어휘 `validity-consult-skip:
trivial` 태그 중 하나를 가지는지 검사한다(issue-1024).

`acceptance_gate.py`가 검사하는 속성(수용기준이 실행가능 산출물을
가리키는가)과도, #1017 제안 모듈이 검사할 속성(요구사항 ID 인용 여부)과도
다르다 — 이 게이트는 오직 "드래프트 전에 타당성 자문(feasibility/
consistency/ordering)이 실행됐거나, 명시적으로 생략됐는가"만 본다.
`gh` 호출 없이 단위테스트 가능하다(`acceptance_gate.py`와 같은 관례).

  python3 gates/requirement_intake_consult.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

_CONSULT_REF = re.compile(
    r"^\s*[-*]?\s*validity-consult\s*:\s*\S", re.IGNORECASE | re.MULTILINE)
# 닫힌 어휘: trivial 만 허용한다 — 임의 이유 문자열은 사후 헌트에서 발견된
# 우회(자기평가로 "risk-bearing" 요청도 아무 사유나 대며 스킵)를 허용한다.
_CONSULT_SKIP = re.compile(
    r"^\s*[-*]?\s*validity-consult-skip\s*:\s*trivial\b",
    re.IGNORECASE | re.MULTILINE)


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `validity-consult: <ref>` (타당성 자문이 실행됐다는 트레이스 참조) 또는
    닫힌 어휘 `validity-consult-skip: trivial` (사소한/기계적 요청이라
    생략) 중 하나가 본문 어디에든 있으면 통과. 둘 다 없으면 위반.
    """
    body = body or ""
    if _CONSULT_REF.search(body):
        return []
    if _CONSULT_SKIP.search(body):
        return []
    return [
        f"이슈 #{issue} 본문에 'validity-consult: <ref>' 트레이스 참조도, "
        f"'validity-consult-skip: trivial' 생략 태그도 없다 — 요구사항 "
        f"인테이크는 기본적으로 타당성 자문(feasibility/consistency/"
        f"ordering)을 거치거나, 사소한 요청임을 명시적으로 밝혀야 한다."
    ]


def _issue_view_body(repo: Path, issue: int) -> str | None:
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "body"],
                       cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    data = json.loads(r.stdout)
    return data.get("body", "")


def check(repo: Path, issue: int) -> list[str]:
    body = _issue_view_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh issue view` 실패) — "
                f"검사 불가는 통과가 아니다."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: requirement_intake_consult.py <issue-number> [--repo <경로>]")
        return 1
    issue = int(sys.argv[1])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    bad = check(repo, issue)
    if not bad:
        print("게이트 통과")
        return 0
    print("게이트 차단:")
    for b in bad:
        print(f"  - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
