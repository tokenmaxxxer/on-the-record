#!/usr/bin/env python3
"""PR 이슈참조 게이트 — PR 본문이 자기 이슈를 가리키는지 검사한다(issue-126).

`gates.check(names, d, cfg)`(라우터용, 로컬 워크트리 diff)나 `ci.py`의
`check(repo)`(로컬 워크트리 checkout)와 달리, 이 게이트는 PR 번호와 PR 본문이
필요하다 — 둘 다 로컬 체크아웃에는 없고 `gh pr view`로만 얻는다. 그래서
독립된 진입점으로 둔다: 기존 두 시그니처(`Path` 하나)에 억지로 끼워 넣으면
PR 번호를 몰래 스레딩해야 하고, 로컬 diff 전용이라는 두 진입점의 불변식이
깨진다.

  python3 gates/pr_reference.py <pr-number> [--repo <경로>]
  종료 코드 0 통과 / 1 차단
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

import acceptance_gate
import flows
import gh_rest
import human_comprehensibility

# phase-1 제안 PR은 `#<n>`만 있으면 된다 — 머지돼도 이슈를 닫으면 안 된다
# (Closes 는 자동 종료를 유발한다). phase-2 인도 PR만 Closes/Fixes/Resolves 를 요구한다.
_PLAIN_REF = re.compile(r"(?<!\w)#(\d+)")
_CLOSES_REF = re.compile(r"(?i)\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")


def check_body(issue: int, body: str, phase: str,
                plan: list[dict] | None = None) -> list[str]:
    """PR 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `plan`(issue-189 계약, `flows._plan_from_body`의 반환값)이 주어지고
    미완 스텝이 둘 이상이거나 유일한 미완 스텝이 마지막이 아니면(issue-228),
    phase-2 에서 closing 키워드를 요구하지 않고 오히려 차단한다 — 계획이
    남은 이슈를 첫 스텝의 머지가 조기 종결하지 못하게. 체크박스 저작이
    역순(issue-197의 #197처럼)이어도 fail-closed 쪽으로 안전하다.
    """
    body = body or ""
    violations: list[str] = []
    if not human_comprehensibility.first_paragraph_is_prose(body):
        violations.append("PR 본문의 첫 문단이 실질적인 산문이 아니다(트레일러 줄만 "
                           "있음) — 변경/이유/다음 단계를 서술하는 문단이 먼저 와야 한다.")
    if phase == "phase2":
        if plan:
            incomplete = [s for s in plan if not s["done"]]
            max_step = max(s["step"] for s in plan)
            only_last_incomplete = (
                len(incomplete) == 1 and incomplete[0]["step"] == max_step
            )
            if incomplete and not only_last_incomplete:
                m = _CLOSES_REF.search(body)
                if m and int(m.group(2)) == issue:
                    return violations + ["계획에 미완 스텝이 남아 있다 — 마지막 스텝의 "
                            "phase-2 PR에서만 Closes/Fixes/Resolves를 쓴다."]
                return violations
        m = _CLOSES_REF.search(body)
        if not m or int(m.group(2)) != issue:
            return violations + [f"PR 본문에 'Closes #{issue}'(또는 Fixes/Resolves)가 없다 — "
                    f"phase-2 인도 PR은 이슈를 명시적으로 닫아야 한다."]
        return violations
    refs = {int(n) for n in _PLAIN_REF.findall(body)}
    if issue not in refs:
        return violations + [f"PR 본문에 '#{issue}' 참조가 없다 — phase-1 제안 PR도 자기 "
                f"이슈를 본문에서 가리켜야 한다(Closes/Fixes/Resolves는 금지: "
                f"phase-1 머지가 이슈를 자동으로 닫으면 안 된다)."]
    return violations


def check(repo: Path, pr: int, issue: int, phase: str) -> list[str]:
    """REST(`gh api repos/.../pulls/<pr>`)로 PR 본문을 읽어 `check_body`에 위임한다.

    phase-2 에서는 이슈 본문도 읽어 `flows._plan_from_body`로 계획을
    파싱해 넘긴다(issue-228) — 이슈 본문을 못 읽으면 계획 상태를 알 수
    없으므로 fail-closed 차단.
    """
    body = gh_rest.fetch_pr_body(repo, pr)
    if body is None:
        return [f"PR #{pr} 본문을 읽을 수 없다(`gh api repos/.../pulls/{pr}` 실패) — 검사 불가는 통과가 아니다."]
    plan = None
    if phase == "phase2":
        issue_body = gh_rest.fetch_issue_body(repo, issue)
        if issue_body is None:
            return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
                    f"검사 불가는 통과가 아니다."]
        plan = flows._plan_from_body(issue_body)
        bad = check_body(issue, body, phase, plan)
        closes = _CLOSES_REF.search(body)
        if not bad and closes and int(closes.group(2)) == issue:
            bad = bad + acceptance_gate.check_issue_body(issue, issue_body)
        return bad
    return check_body(issue, body, phase, plan)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: pr_reference.py <pr-number> <issue-number> [phase1|phase2] [--repo <경로>]")
        return 1
    pr = int(sys.argv[1])
    issue = int(sys.argv[2])
    phase = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "phase1"
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    bad = check(repo, pr, issue, phase)
    if not bad:
        print("게이트 통과")
        return 0
    print("게이트 차단:")
    for b in bad:
        print(f"  - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
