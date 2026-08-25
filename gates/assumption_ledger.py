#!/usr/bin/env python3
"""assumption 원장 게이트 — 드래프트된 이슈 본문이 `## Assumptions` 절에
닫힌 어휘(stated/inferred/invented)로 태그된 항목들을 갖는지, 또는
닫힌 어휘 `assumptions-skip: mechanical` 태그를 갖는지 검사한다
(issue-1665, northpole req#6).

'scribe not inventor' 를 결정론적으로 강제한다 — orchestrate 디렉티브가
말로만 요구하던 것을 여기서 기계적으로 검사한다. `acceptance_gate.py`
와 같은 presence-only 원칙: 항목의 진실(정말 invented 인지)은 판단하지
않는다 — 태그가 닫힌 어휘 중 하나인지, 절이 존재하는지만 본다.
`gh` 호출 없이 단위테스트 가능하다(`requirement_intake_consult.py`와
같은 관례).

  python3 gates/assumption_ledger.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest

_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*assumptions\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")
# 닫힌 어휘: stated/inferred/invented 만 허용한다.
_ENTRY = re.compile(
    r"^\s*[-*]?\s*(stated|inferred|invented)\s*:\s*\S",
    re.IGNORECASE | re.MULTILINE)
_ANY_TAG_LIKE_ENTRY = re.compile(
    r"^\s*[-*]?\s*(stated|inferred|invented|\w[\w-]*)\s*:\s*\S",
    re.IGNORECASE | re.MULTILINE)
_INVENTED_ENTRY = re.compile(
    r"^\s*[-*]?\s*invented\s*:\s*(\S.*)$", re.IGNORECASE | re.MULTILINE)
# 닫힌 어휘: mechanical 만 허용한다 — 임의 이유 문자열로 스킵을 정당화하는
# 우회를 막는다(#1024/#1653 과 같은 원칙).
_SKIP = re.compile(
    r"^\s*[-*]?\s*assumptions-skip\s*:\s*mechanical\b",
    re.IGNORECASE | re.MULTILINE)


def _assumptions_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `assumptions-skip: mechanical` 이 본문 어디에든 있으면 통과(기계적
    요청). 아니면 `## Assumptions` 절이 있어야 하고, 그 절 안에 최소
    한 개 이상의 entry(`stated:`/`inferred:`/`invented:` 로 시작하는
    줄)가 있어야 하며, 절 안의 모든 tag-like 줄(`word:` 형태)이 닫힌
    어휘(stated/inferred/invented) 중 하나여야 한다. 절이 없거나,
    entry 가 하나도 없거나, out-of-vocabulary 태그가 있으면 위반.
    """
    body = body or ""
    if _SKIP.search(body):
        return []

    section = _assumptions_section(body)
    if section is None:
        return [
            f"이슈 #{issue} 본문에 '## Assumptions' 절도, "
            f"'assumptions-skip: mechanical' 생략 태그도 없다 — 드래프트된 "
            f"요구사항은 기본적으로 provenance 태그(stated/inferred/"
            f"invented)가 붙은 assumption 원장을 갖거나, 기계적 요청임을 "
            f"명시적으로 밝혀야 한다."
        ]

    entries = _ANY_TAG_LIKE_ENTRY.findall(section)
    if not entries:
        return [
            f"이슈 #{issue}의 '## Assumptions' 절에 항목이 없다 — 각 항목은 "
            f"stated:/inferred:/invented: 중 하나로 태그돼야 한다."
        ]

    valid = {"stated", "inferred", "invented"}
    bad_tags = sorted({t for t in entries if t.lower() not in valid})
    if bad_tags:
        return [
            f"이슈 #{issue}의 '## Assumptions' 절에 닫힌 어휘를 벗어난 "
            f"태그가 있다: {', '.join(bad_tags)} — stated:/inferred:/"
            f"invented: 만 허용된다."
        ]

    return []


def invented_assumptions(body: str) -> list[str]:
    """`## Assumptions` 절 안의 `invented:` 항목 텍스트 목록을 반환한다
    (orchestrator/directive 가 spawn 전 인간 확인을 요구할 수 있도록).

    닫힌 어휘 검사와 무관하게, 절이 있으면 그 안에서 `invented:` 로 시작하는
    모든 줄을 수집한다. 절이 없으면 빈 리스트.
    """
    body = body or ""
    section = _assumptions_section(body)
    if section is None:
        return []
    return [m.strip() for m in _INVENTED_ENTRY.findall(section)]


def check(repo: Path, issue: int) -> list[str]:
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
                f"검사 불가는 통과가 아니다."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: assumption_ledger.py <issue-number> [--repo <경로>]")
        return 1
    try:
        issue = int(sys.argv[1])
    except ValueError:
        print(f"usage: assumption_ledger.py <issue-number> [--repo <경로>] "
              f"— issue-number must be an integer, got {sys.argv[1]!r}")
        return 1
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
