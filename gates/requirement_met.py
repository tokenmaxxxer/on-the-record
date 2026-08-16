#!/usr/bin/env python3
"""requirement-met verification — issue #1651 (northpole req#6).

이슈의 `## Acceptance` 절 `- check:` 불릿을 등급 매긴다. 파서는
`check_runner.parse_checks`(acceptance_gate 와 같은 계열의 section
추출 + check/gate 줄 파서)를 재사용한다 — 새로 만들지 않는다.

두 겹의 판정이 섞이지 않게 분리한다:
- **결정적** 아티팩트-존재 서브체크(artifact_in_diff)만 블록한다: 기준이
  YES 로 채점됐는데 그 기준이 인용한 아티팩트(백틱 경로/커맨드)가 PR
  diff 안에 없으면 실패. 이건 LLM 판단이 아니라 문자열 포함 검사다.
- **의미론적** verdict(YES/NO/UNKNOWN, builder-blind 세션이 매긴 것)는
  advisory 로만 기록된다 — 그 자체로는 절대 블록하지 않는다(연구 근거:
  LLM judge 는 게임 가능/편향 — 토큰 하나로 35% FP, 모듈 docstring 참고
  대신 이슈 본문에 있음).

`- check:` 불릿이 0개인 이슈(예: `unverifiable:` 로만 채워진 절)는
'no gradable criteria' 로 구분되는 결과를 낸다 — 크래시도 아니고 기존
게이트들의 결과와 바이트 단위로 같지도 않은, 별도 상태다.

  python3 gates/requirement_met.py <issue-number> <pr-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import acceptance_gate  # noqa: E402
import check_runner  # noqa: E402
import gh_rest  # noqa: E402

YES = "YES"
NO = "NO"
UNKNOWN = "UNKNOWN"

_ARTIFACT = re.compile(r"`([^`]+)`")


def _cited_artifact(raw: str) -> str | None:
    """`- check:` 불릿 텍스트에서 인용된 아티팩트(백틱으로 감싼 경로/
    커맨드)를 뽑는다. 백틱이 없으면 아티팩트 미인용 — None."""
    m = _ARTIFACT.search(raw)
    if not m:
        return None
    return m.group(1).strip()


def grade(issue_body: str, diff: str, per_check_verdicts: dict[str, str]) -> dict:
    """순수 함수. `issue_body`의 Acceptance 절에서 `- check:` 불릿을 뽑아
    각각을 채점한다.

    `per_check_verdicts`: 불릿의 원문(`raw`, `check_runner.parse_checks`가
    돌려주는 그대로)을 키로 하는 YES/NO/UNKNOWN 매핑 — builder-blind
    세션이 낸 semantic verdict. 없는 키는 UNKNOWN 취급한다.

    반환값:
      {"empty_state": bool, "criteria": [...], "blocked": bool,
       "blocking_reasons": [str]}
    각 criterion: {"raw", "artifact", "verdict", "artifact_in_diff",
                   "blocking_fail"}.
    """
    issue_body = issue_body or ""
    diff = diff or ""
    section = acceptance_gate._acceptance_section(issue_body)
    if section is None:
        return {"empty_state": True, "criteria": [], "blocked": False,
                "blocking_reasons": [],
                "reason": "이슈 본문에 '## Acceptance' 절이 없다"}
    checks = check_runner.parse_checks(section)
    if not checks:
        return {"empty_state": True, "criteria": [], "blocked": False,
                "blocking_reasons": [],
                "reason": "Acceptance 절에 '- check:' 불릿이 0개다 "
                          "(예: unverifiable: 로만 채워짐) — 채점 가능한 "
                          "기준이 없다"}

    criteria = []
    blocking_reasons = []
    for chk in checks:
        raw = chk["raw"]
        artifact = _cited_artifact(raw)
        verdict = per_check_verdicts.get(raw, UNKNOWN)
        artifact_in_diff = bool(artifact) and artifact in diff
        blocking_fail = verdict == YES and not artifact_in_diff
        if blocking_fail:
            if artifact is None:
                blocking_reasons.append(
                    f"기준 '{raw}'이 YES 로 채점됐지만 인용된 아티팩트가 없다 "
                    f"(백틱으로 감싼 test/gates 경로 또는 커맨드 필요)")
            else:
                blocking_reasons.append(
                    f"기준 '{raw}'이 YES 로 채점됐지만 인용된 아티팩트 "
                    f"'{artifact}'이 PR diff 에 없다")
        criteria.append({
            "raw": raw, "artifact": artifact, "verdict": verdict,
            "artifact_in_diff": artifact_in_diff,
            "blocking_fail": blocking_fail,
        })
    return {"empty_state": False, "criteria": criteria,
            "blocked": bool(blocking_reasons),
            "blocking_reasons": blocking_reasons}


def _pr_diff(repo: Path, pr: int) -> str | None:
    r = subprocess.run(["gh", "pr", "diff", str(pr)], cwd=repo,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def check(repo: Path, issue: int, pr: int,
          per_check_verdicts: dict[str, str] | None = None) -> list[str]:
    """`gh`-wrapped 버전. `per_check_verdicts`는 builder-blind 세션이 낸
    semantic verdict 매핑 — 이 함수 자체는 그 세션을 스폰하지 않는다(그건
    호출부/오케스트레이터의 몫). 생략하면 모든 기준이 UNKNOWN 으로
    채점되고, UNKNOWN 은 절대 블록하지 않는다(YES 만 아티팩트 부재 시
    블록)."""
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
                f"검사 불가는 통과가 아니다."]
    diff = _pr_diff(repo, pr)
    if diff is None:
        return [f"PR #{pr} diff 를 읽을 수 없다(`gh pr diff {pr}` 실패) — "
                f"검사 불가는 통과가 아니다."]
    result = grade(body, diff, per_check_verdicts or {})
    if result["empty_state"]:
        return []
    return result["blocking_reasons"]


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: requirement_met.py <issue-number> <pr-number> [--repo <경로>]")
        return 1
    issue = int(sys.argv[1])
    pr = int(sys.argv[2])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    bad = check(repo, issue, pr)
    if not bad:
        print("게이트 통과 (또는 채점 가능한 기준 없음)")
        return 0
    print("게이트 차단:")
    for b in bad:
        print(f"  - {b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
