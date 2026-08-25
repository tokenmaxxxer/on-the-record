#!/usr/bin/env python3
"""artifact-smoke 수용기준 규칙(이슈 #2073) — 런타임 산출물을 선언한
이슈의 `## Acceptance` 절이, 그 산출물 **자체**를 파싱/실행하는 검사를
최소 하나 갖고 있는지 초안 단계에서 검사한다.

배경(실측): tm-dicequest#26 과 #44 는 모든 수용검사가 초록인 채로 완전히
죽은 웹페이지를 하루에 두 번 배송했다. 공통 원인은 생성물/브라우저
산출물의 수용이 **간접적**이어도 됐다는 것 — 소스에 대한 유닛 테스트,
재생성 출력에 대한 diff 동등성. 어느 것도 배송되는 바이트를 실행하거나
파싱하지 않는다. #1696 의 COMMAND-IDENTITY 가 명령 표면에 대해 한 일을
이 규칙이 산출물에 대해 한다.

계약(docs/specs/artifact-smoke-contract.md):

  runtime-artifacts:
  - dist/index.html
  - dist/bundle.js

선언이 있으면, `## Acceptance` 절의 `check:`/`gate:` 줄 중 최소 하나가
백틱 명령 안에서 선언된 경로 하나를 허용목록(allowlist)에 있는
파싱/실행 동사와 함께 이름해야 한다. 그렇지 않으면 거부한다.

byte-inert on absence: `runtime-artifacts:` 태그가 없으면
(`parse_declaration` 이 None) 이 모듈은 빈 리스트를 돌려준다 — 기계적
이슈는 새 검사를 하나도 보지 않는다.

fail-closed: 이슈 본문을 못 읽으면 검사 불가를 통과로 취급하지 않는다.

의존 방향(이슈 #2073 제안서 Constraints): 이 모듈은 `gates/` 안의 leaf
다 — `spawn.py` 를 import 하지 않는다. 선언 파서는 복사하지 않고
`design_artifacts_gate.parse_declaration` 의 계약을 태그 인자로 넓혀
재사용한다(파서 하나, 태그 N개).

  python3 gates/artifact_smoke_rule.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design_artifacts_gate as _dag

TAG = "runtime-artifacts"

# 닫힌 허용목록 — 선언된 산출물 자체를 파싱하거나 실행하는 것으로
# 인정되는 명령의 첫 토큰. 열려 있으면 아무 명령이나 산출물 이름을
# 스치기만 해도 통과하므로(다시 fake-success), 목록은 명시적으로 닫아
# 두고 확장은 계약 문서를 고치는 것으로만 한다.
PARSE_EXECUTE_VERBS = frozenset({
    "node", "npx", "deno", "bun",
    "esbuild", "tsc", "swc",
    "playwright", "puppeteer",
    "chromium", "chrome", "google-chrome", "firefox",
    "html5validator", "xmllint", "tidy",
    "php",
})

# 재생성-diff / 소스-유닛만으로 때우는 대표 형태 — 거부 메시지에서
# "왜 이건 안 되는지" 를 구체적으로 짚어 주기 위한 힌트일 뿐,
# 판정 자체는 위 허용목록의 부재로 내려진다.
_INDIRECT_HINT = re.compile(r"\bdiff\b|재생성|regenerat|pytest|unittest", re.IGNORECASE)

_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")
_CHECK_LINE = re.compile(
    r"^\s*[-*]?\s*(?:check|gate)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_BACKTICK_CMD = re.compile(r"`([^`]+)`")

_OVERRIDE_YES = re.compile(
    r"^\s*[-*]?\s*artifact-smoke-override\s*:\s*yes\b", re.IGNORECASE | re.MULTILINE)

# 자문(advisory) 전용 스코어러 — 태그가 없는데 본문이 생성물/브라우저
# 산출물 냄새를 강하게 풍기면 한 줄 안내를 붙인다. #2012 의 코퍼스
# 보정이 보여준 대로 이 어휘는 기계적 이슈와 충돌이 잦으므로, 이 경로는
# 절대 거부 트리거가 아니다(제안서 Rationale).
_ARTIFACT_SIGNAL_KEYWORDS = frozenset({
    "browser", "bundle", "generated", "artifact", "page", "html",
    "dist", "build", "single-file", "esm", "module",
})
_ARTIFACT_MIN_OVERLAP = 3
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body or "")
    if not m:
        return None
    rest = (body or "")[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def parse_declaration(body: str) -> list[str] | None:
    """`runtime-artifacts:` 선언(불릿/펜스)을 뽑는다. 태그가 없으면 None."""
    return _dag.parse_declaration(body, TAG)


def malformed_declaration_line(body: str) -> str | None:
    return _dag.malformed_declaration_line(body, TAG)


def _commands(section: str) -> list[str]:
    """Acceptance 절의 `check:`/`gate:` 줄에서 백틱 명령만 뽑는다."""
    out = []
    for m in _CHECK_LINE.finditer(section or ""):
        for bm in _BACKTICK_CMD.finditer(m.group(1)):
            out.append(bm.group(1).strip())
    return out


def command_touches_artifact(command: str, declared: list[str]) -> str | None:
    """`command` 가 허용목록 동사로 시작하고 argv 안에서 선언된 경로
    하나를 이름하면 그 경로를, 아니면 None 을 돌려준다."""
    tokens = (command or "").split()
    if not tokens:
        return None
    verb = Path(tokens[0]).name
    if verb not in PARSE_EXECUTE_VERBS:
        return None
    for path in declared:
        if not path:
            continue
        for tok in tokens[1:]:
            if tok == path or tok.endswith("/" + path) or path in tok:
                return path
    return None


def artifact_smoke_checks(section: str, declared: list[str]) -> list[tuple[str, str]]:
    """(명령, 그 명령이 건드리는 선언 산출물) 쌍의 목록."""
    found = []
    for cmd in _commands(section):
        hit = command_touches_artifact(cmd, declared)
        if hit is not None:
            found.append((cmd, hit))
    return found


def advisory_line(issue: int, body: str) -> str | None:
    """태그가 없는데 산출물 어휘가 임계값을 넘으면 붙는 비-거부 안내."""
    if parse_declaration(body) is not None:
        return None
    overlap = _tokenize(body) & _ARTIFACT_SIGNAL_KEYWORDS
    if len(overlap) < _ARTIFACT_MIN_OVERLAP:
        return None
    listed = ", ".join(sorted(overlap))
    return (f"안내(거부 아님, 이슈 #{issue}): 본문이 생성물/브라우저 산출물 "
            f"어휘({listed})를 담고 있는데 `runtime-artifacts:` 선언이 없다 — "
            f"배송되는 산출물이 있다면 선언하고, 그 산출물을 실제로 파싱/실행하는 "
            f"검사를 `## Acceptance` 에 하나 두는 편이 좋다"
            f"(docs/specs/artifact-smoke-contract.md).")


def check_issue_body(issue: int, body: str) -> list[str]:
    """이슈 본문 텍스트만으로 판정한다(네트워크 없음).

    거부 문자열 목록을 돌려준다 — 빈 리스트면 통과. 선언이 없으면
    빈 리스트(byte-inert)."""
    body = body or ""

    declared = parse_declaration(body)
    if declared is None:
        malformed = malformed_declaration_line(body)
        if malformed is not None:
            return [f"이슈 #{issue}의 runtime-artifacts 선언이 잘못된 형태다: "
                    f"{malformed!r} — 태그 줄에 내용이 바로 붙어 있다. 필요한 형태: "
                    f"'runtime-artifacts:' 태그 줄 다음에 '- dist/bundle.js' 불릿 "
                    f"목록(또는 ```fenced``` 블록)."]
        return []

    if _OVERRIDE_YES.search(body):
        return []

    if not declared:
        return [f"이슈 #{issue}가 `runtime-artifacts:` 태그를 달았지만 산출물을 "
                f"하나도 선언하지 않았다 — 태그를 지우거나 배송되는 경로를 "
                f"불릿으로 적는다."]

    section = acceptance_section(body)
    if section is None:
        return [f"이슈 #{issue}가 런타임 산출물({', '.join(declared)})을 선언했는데 "
                f"`## Acceptance` 절이 없다 — 산출물을 파싱/실행하는 검사를 둘 곳이 "
                f"없다(fail-closed)."]

    if artifact_smoke_checks(section, declared):
        return []

    verbs = ", ".join(sorted(PARSE_EXECUTE_VERBS))
    listed = "\n".join(f"  - {p}" for p in declared)
    indirect = " 지금 있는 검사는 소스 유닛/재생성 diff 계열이다 — 그건 배송되는 " \
               "바이트가 브라우저에서 죽어도 초록으로 남는다(tm-dicequest#26/#44)." \
        if _INDIRECT_HINT.search(section) else ""
    return [f"이슈 #{issue}의 'Acceptance' 절에 선언된 런타임 산출물을 직접 "
            f"파싱/실행하는 검사가 하나도 없다.{indirect}\n"
            f"선언된 산출물:\n{listed}\n"
            f"최소 하나의 `check:` 가 위 경로 중 하나를 다음 동사 중 하나와 함께 "
            f"이름해야 한다: {verbs}\n"
            f"예: check: `node --input-type=module --check dist/bundle.js`"]


def check(repo: Path, issue: int) -> list[str]:
    """이슈 본문을 가져와 판정한다 — 못 가져오면 fail-closed."""
    sys.path.insert(0, str(Path(__file__).parent))
    import gh_rest
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` "
                f"실패) — artifact-smoke 규칙은 검사 불가를 통과로 취급하지 "
                f"않는다(fail-closed)."]
    return check_issue_body(issue, body)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: artifact_smoke_rule.py <issue-number> [--repo <경로>]")
        return 1
    try:
        issue = int(sys.argv[1])
    except ValueError:
        print(f"usage: artifact_smoke_rule.py <issue-number> [--repo <경로>] "
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
