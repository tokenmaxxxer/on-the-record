#!/usr/bin/env python3
"""수용기준 실행가능성 게이트 — 이슈의 `## Acceptance` 절이 실행가능한
산출물(테스트/게이트/CI job)을 가리키는지, 또는 명시적으로
`unverifiable:` 로 이유를 대는지 검사한다(issue-310).

프로즈만 있는 Acceptance 는 통과가 아니다 — 문장 하나로 요구사항을
"닫는" 네 가지 우회(약속/메모/리스트 한 줄/문서 문장) 중 마지막 형태를
막는 것이 이 게이트의 목적이다. `gh` 호출이 없어 네트워크 없이
단위테스트 가능하다(`record_enums`/`classify()` 와 같은 관례).

COMMAND-IDENTITY (issue #1696): `provenance: executed-live`로 표시한
`check:`는 커맨드 SURFACE 를 지목한다 — installed line(예: crontab
엔트리)이나 README 에 문서화된 실행법. 그 체크를 만족시켰다는 증거는
그 커맨드를 그대로(byte-identical, environment-independent — 결과를
바꾸는 `PYTHONPATH=`/`cd`/venv 활성화 같은 크러치 없이) 실행한
기록이어야 한다. 겉보기엔 동등한 커맨드(예: 체크가 지목한 installed
`python3 -m pkg` 대신 `python3 -m pkg.cli`를 실행)로는 증명이 안 된다 —
이는 fake-success 벡터다(pilot-devdigest PR #6 에서 실측: 다이제스트
파일이 존재했고 기록도 정직해 보였지만, 실제 크론 라인은 무엇도
실행하지 못했다). 이 게이트 자체는 존재-검사만 하고(값의 진실은
검사하지 않음, 위 참고), 커맨드가 실제로 일치하는지는
`gates/requirement_met.py`의 결정론적 레이어가 별도로 검사한다 — diff에
기록된 `acceptance: <command> — result: ...` 커맨드가 체크가 이름 붙인
커맨드 표면과 다르면 semantic verdict 와 무관하게 블록한다.

  python3 gates/acceptance_gate.py <issue-number> [--repo <경로>]
  python3 gates/acceptance_gate.py --sweep [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest

_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")
_ARTIFACT_REF = re.compile(
    r"`[^`]*(?:tests?/|gates/)[^`]*`"
    r"|^\s*[-*]?\s*(gate|check)\s*:\s*\S+",
    re.IGNORECASE | re.MULTILINE,
)
_UNVERIFIABLE = re.compile(r"^\s*[-*]?\s*unverifiable\s*:\s*\S",
                            re.IGNORECASE | re.MULTILINE)
# issue-416: 행동 주장(실행가능 산출물 참조)에 붙는 두 필드. 둘 다 존재-검사만 한다
# — 값의 진실은 검사하지 않는다(모듈 docstring/decision doc 에 명시).
_EMPTY_STATE = re.compile(
    r"^\s*[-*]?\s*empty state\s*:\s*\S", re.IGNORECASE | re.MULTILINE)
_PROVENANCE = re.compile(
    r"^\s*[-*]?\s*provenance\s*:\s*(executed-live|executed-unit|read)\b",
    re.IGNORECASE | re.MULTILINE)

# issue-2229: 위반 메시지마다 "통과하는 형식"을 구체적으로 가리킨다 — 무엇이
# 빠졌는지만 말하고 어떤 형식이면 통과하는지는 안 알려주면 작성자가 추측해야
# 한다. 이 저장소의 유일한 출처(single source of truth) 문서를 인용한다.
_FORMAT_DOC = "on-the-record/directive/acceptance-format.md"


def _acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음, 테스트 용이).

    `## Acceptance`(또는 임의 레벨 헤딩의 "acceptance") 절이 아예 없으면
    검사 불가 — fail closed, 통과가 아니라 위반으로 취급한다. 절이
    있으면 실행가능한 산출물 참조(백틱으로 감싼 `test/`/`gates/` 아래
    경로, 또는 `gate:`/`check:` 줄) 또는 `unverifiable:` 로 시작하는
    명시적 이유 줄 중 하나를 요구한다. `.github/workflows/` 는 #460 으로
    저장소에서 완전히 삭제되어 더 이상 실행가능한 산출물이 될 수 없으므로
    받아들이지 않는다(issue-499).
    """
    body = body or ""
    section = _acceptance_section(body)
    if section is None:
        return [f"이슈 #{issue} 본문에 '## Acceptance' 절이 없다 — "
                f"수용기준 없이는 실행가능성을 검사할 수 없고, 검사 불가는 "
                f"통과가 아니다. 통과하는 형식은 {_FORMAT_DOC} 를 봐라."]
    if _UNVERIFIABLE.search(section):
        return []
    # issue-555: 모든 위반을 한 번에 모아서 반환한다 — 하나 발견 즉시
    # return 하면 다음 라운드에서 새 위반이 또 하나씩만 드러난다.
    bad = []
    if not _ARTIFACT_REF.search(section):
        bad.append(f"이슈 #{issue}의 'Acceptance' 절이 프로즈뿐이다 — 실행가능한 "
                   f"산출물(백틱으로 감싼 test/, gates/ 경로, 또는 'gate:'/'check:' "
                   f"줄)을 가리키거나, 검증 불가능한 이유를 "
                   f"'unverifiable: <이유>' 로 명시해야 한다. 통과하는 형식은 "
                   f"{_FORMAT_DOC} 를 봐라.")
    # issue-416: 실행가능 산출물 참조가 있으면(=행동 주장) empty state/provenance
    # 존재를 추가로 요구한다. unverifiable: 은 위에서 이미 둘 다 면제했다.
    if not _EMPTY_STATE.search(section):
        bad.append(
            f"이슈 #{issue}의 'Acceptance' 절이 실행가능 산출물을 참조하지만 "
            f"'empty state: <경로 또는 설명>' 줄이 없다 — 초기/빈 상태가 "
            f"코퍼스에 있는지 명시해야 한다(또는 "
            f"'empty state: not applicable — <이유>'). 통과하는 형식은 "
            f"{_FORMAT_DOC} 를 봐라."
        )
    if not _PROVENANCE.search(section):
        bad.append(
            f"이슈 #{issue}의 'Acceptance' 절이 실행가능 산출물을 참조하지만 "
            f"'provenance: executed-live|executed-unit|read' 줄이 없다 — "
            f"행동 주장이 실제 실행으로 확인됐는지, 읽기로만 판단했는지 "
            f"명시해야 한다(읽기(`read`)로 판단했다면 그 사실도 명시적이어야 "
            f"한다 — 이 게이트는 `read` 를 금지하지 않고 보이게만 만든다). "
            f"통과하는 형식은 {_FORMAT_DOC} 를 봐라."
        )
    return bad


def check(repo: Path, issue: int) -> list[str]:
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
                f"검사 불가는 통과가 아니다."]
    return check_issue_body(issue, body)


def sweep_issue_bodies(open_issues: list[dict]) -> dict[int, list[str]]:
    """issue #2229: 열린 이슈 전체에 `check_issue_body`를 돌려, 위반이
    있는 이슈만 모아 반환한다 — {이슈번호: [위반 메시지, ...]}. 위반이
    없는 이슈는 키 자체가 없다(전부 통과면 빈 사전).

    `open_issues` 는 `{"number": int, "body": str}` 사전 리스트
    (`gh issue list --json number,body` 모양) — 순수, 네트워크 없음
    (gates/spawn_coverage.py 의 find_uncovered 관례와 동일). 빈
    리스트(열린 이슈 0건)는 빈 사전을 깨끗하게 반환한다 — 에러가
    아니다.
    """
    out: dict[int, list[str]] = {}
    for it in open_issues:
        number = it.get("number")
        if number is None:
            continue
        bad = check_issue_body(number, it.get("body") or "")
        if bad:
            out[number] = bad
    return dict(sorted(out.items()))


def _list_open_issue_bodies(repo: Path) -> list[dict] | None:
    """`gh issue list --json number,body` — gates/spawn_coverage.py 의
    `_list_open_issues` 와 같은 관례(단발 스윕 커맨드, 데몬 아님).
    `gh` 실패는 None(검사 불가, 통과 아님)."""
    r = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--json", "number,body",
         "--limit", "1000"],
        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def sweep(repo: Path) -> dict[int, list[str]] | None:
    """저장소의 열린 이슈 전체를 스윕한다(issue #2229) — 스폰 시점 한
    이슈씩이 아니라, 지금 스폰 불가능한 열린 이슈 전부를 한 번에 알려준다.
    `gh` 조회 실패는 None — 호출부가 종료 코드를 정한다."""
    open_issues = _list_open_issue_bodies(repo)
    if open_issues is None:
        return None
    return sweep_issue_bodies(open_issues)


def format_sweep_report(bad_by_issue: dict[int, list[str]]) -> str:
    if not bad_by_issue:
        return "acceptance-sweep: 스폰 불가능한 열린 이슈 없음"
    lines = [f"acceptance-sweep: 스폰 불가능한 열린 이슈 {len(bad_by_issue)}건"]
    for issue, bad in bad_by_issue.items():
        lines.append(f"  이슈 #{issue}:")
        for b in bad:
            lines.append(f"    - {b}")
    return "\n".join(lines)


def main() -> int:
    if "--sweep" in sys.argv:
        repo = Path(".").resolve()
        if "--repo" in sys.argv:
            repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()
        bad_by_issue = sweep(repo)
        if bad_by_issue is None:
            print("acceptance-sweep: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가",
                  file=sys.stderr)
            return 1
        print(format_sweep_report(bad_by_issue))
        return 1 if bad_by_issue else 0

    if len(sys.argv) < 2:
        print("usage: acceptance_gate.py <issue-number> [--repo <경로>] | "
              "acceptance_gate.py --sweep [--repo <경로>]")
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
