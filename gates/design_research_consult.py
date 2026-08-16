#!/usr/bin/env python3
"""디자인 연구 자문 게이트 — 새로 작성된 이슈 본문이 `design-research:`
트레이스 참조 또는 닫힌 어휘 `design-research-skip: mechanical` 태그 중
하나를 가지는지 검사한다(issue-1653).

`requirement_intake_consult.py`(issue-1024, 타당성 축)와도, #1017의
요구사항 ID 인용 검사와도, `acceptance_gate.py`(#310, 수용기준 축)와도
다르다 — 이 게이트는 오직 "디자인이 개입된 이슈가 드래프트되기 전에
prior-art/방법론 조사 + 파생 리스크 + 효과성 검증 계획이 트레이스로
남았는가, 아니면 명시적으로 기계적(mechanical)이라 생략됐는가"만 본다.
`gh` 호출 없이 단위테스트 가능하다(`requirement_intake_consult.py`와
같은 관례).

  python3 gates/design_research_consult.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest

_RESEARCH_REF = re.compile(
    r"^\s*[-*]?\s*design-research\s*:\s*\S", re.IGNORECASE | re.MULTILINE)
# 닫힌 어휘: mechanical 만 허용한다 — 임의 이유 문자열은 #1024와 동일하게
# 자기평가 우회(디자인이 개입된 요청도 아무 사유나 대며 스킵)를 막는다.
_RESEARCH_SKIP = re.compile(
    r"^\s*[-*]?\s*design-research-skip\s*:\s*mechanical\b",
    re.IGNORECASE | re.MULTILINE)


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `design-research: <ref>` (prior-art/방법론 조사 + 파생 리스크 +
    효과성 검증 계획 트레이스 참조) 또는 닫힌 어휘
    `design-research-skip: mechanical` (디자인 결정이 없는 기계적 변경이라
    생략) 중 하나가 본문 어디에든 있으면 통과. 둘 다 없으면 위반.
    """
    body = body or ""
    if _RESEARCH_REF.search(body):
        return []
    if _RESEARCH_SKIP.search(body):
        return []
    return [
        f"이슈 #{issue} 본문에 'design-research: <ref>' 트레이스 참조도, "
        f"'design-research-skip: mechanical' 생략 태그도 없다 — 디자인이 "
        f"개입된 이슈는 기본적으로 prior-art/방법론 조사와 파생 리스크, "
        f"효과성 검증 계획을 거치거나, 기계적 변경임을 명시적으로 밝혀야 "
        f"한다."
    ]


def check(repo: Path, issue: int) -> list[str]:
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
                f"검사 불가는 통과가 아니다."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: design_research_consult.py <issue-number> [--repo <경로>]")
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
