#!/usr/bin/env python3
"""이슈 초안작성 게이트 — `## Acceptance` 절이 풀스위트/무회귀 검사를
빌더(builder)에게 떠넘기는지 검사한다(issue-1323 req 1).

issue-1313 의 빌더 세션은 이슈의 Acceptance 가 풀스위트 회귀를
요구했기 때문에 wall-clock 의 상당 부분을 그 실행에 썼다 — 기존
역할분리(빌더=자기주장 검사만, 실행-관측/정합성검토/결함검증=독립
검증)를 위반한 사례다. 이 게이트는 그 패턴을 초안 단계에서 막는다.

풀스위트/무회귀를 가리키는 문구가 있어도, 같은 절 안에 그것을
빌더에게서 면제하는 문구(검증 역할/체크러너/독립 검증에게 배정)가
함께 있으면 통과다 — issue #1323 자신의 Acceptance 세 번째 항목이
그 모범 예시다.

  python3 gates/acceptance_authoring_rule.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")

_FULL_SUITE_REF = re.compile(
    r"full[- ]suite|full regression|no regression|entire test suite"
    r"|all tests? pass|run-orchestrate-tests\.sh|run_orchestrate_tests"
    r"|full test suite",
    re.IGNORECASE,
)

_BUILDER_EXEMPT = re.compile(
    r"not the builder|not by the builder"
    r"|verification role|independent verification"
    r"|check-runner|check runner"
    r"|executed by[^.\n]*runner",
    re.IGNORECASE,
)


def _acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `## Acceptance` 절이 없으면 이 게이트가 판정할 대상이 없으므로
    빈 리스트를 반환한다 — 이 게이트는 절의 존재 자체가 아니라
    존재하는 절의 귀속(attribution)만 검사한다(`acceptance_gate.py`가
    존재 여부를 이미 담당).
    """
    body = body or ""
    section = _acceptance_section(body)
    if section is None:
        return []

    bad = []
    for m in _FULL_SUITE_REF.finditer(section):
        window_start = max(0, m.start() - 200)
        window_end = min(len(section), m.end() + 200)
        window = section[window_start:window_end]
        if _BUILDER_EXEMPT.search(window):
            continue
        line = section[section.rfind("\n", 0, m.start()) + 1:
                        section.find("\n", m.end())
                        if section.find("\n", m.end()) != -1 else len(section)]
        bad.append(
            f"이슈 #{issue}의 'Acceptance' 절이 풀스위트/무회귀 검사를 "
            f"빌더에게 떠넘긴다({line.strip()!r}) — 풀스위트/무회귀 검사는 "
            f"req 2의 체크러너 또는 독립 검증 역할에게 배정해야 하며, 그 "
            f"배정을 같은 절에 명시해야 한다(예: '검증 역할이 실행, 빌더가 "
            f"아님')."
        )
    return bad


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
        print("usage: acceptance_authoring_rule.py <issue-number> [--repo <경로>]")
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
