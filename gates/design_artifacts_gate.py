#!/usr/bin/env python3
"""artifact-gate phase 2 (#2013) — a design-bearing issue (#2012) declares
its required intermediate design artifacts via a `design-artifacts:` line
in its own issue body; this gate checks that the declared paths exist in
the working tree before `gh pr create` is allowed to run (wired into
on-the-record/hooks/pr-preflight.sh, ported inline the same way that hook
already ports gates/pr_reference.py::check_body).

Existence and minimal shape only, never content (proposal's frozen
principle, docs/issue-2013/proposals/design-artifact-existence-gate.md
"Rationale"/"Out of scope"): this module never opens a declared artifact
file to judge whether it is a real user scenario or a placeholder line.

Byte-inert when no `design-artifacts:` declaration is present
(`parse_declaration` returns None) — a mechanical issue sees no new check.

Fail-closed on gh/network trouble (phase-2 approval amendment on #2013,
replacing the proposal's original fail-open-on-infrastructure-trouble
constraint): `check()` returns an actionable violation, never an empty
list, when the issue body itself cannot be fetched — a gate that opens on
a broken `gh` is bypassable by breaking `gh`.

  python3 gates/design_artifacts_gate.py <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest

# closed shape (proposal "What will be done" #1): the tag line itself,
# followed by a bulleted list or a fenced block, one path per line —
# mirrors design_research_consult.py's regex-only, network-free parsing.
_TAG_RE = re.compile(r"^\s*[-*]?\s*design-artifacts\s*:\s*$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(\S+)\s*$")
_FENCE_RE = re.compile(r"^\s*```")


def _tag_re(tag: str) -> re.Pattern:
    """이슈 #2073: 선언 태그 이름만 다른 두 번째 닫힌-어휘 선언
    (`runtime-artifacts:`)이 생기면서, 태그별로 파서를 복사하는 대신
    이 모듈의 계약을 넓힌다(complexity-coupling rule 4 — 새 모듈 간
    의존 간선 대신 기존 계약 확장). 파서는 하나, 태그는 N개."""
    if tag == "design-artifacts":
        return _TAG_RE
    return re.compile(rf"^\s*[-*]?\s*{re.escape(tag)}\s*:\s*$", re.IGNORECASE)


def parse_declaration(body: str, tag: str = "design-artifacts") -> list[str] | None:
    """`design-artifacts:` 태그가 없으면 None(byte-inert 경로). 태그가
    있으면 바로 다음의 불릿 목록 또는 펜스 블록에서 경로 목록을 뽑는다
    (빈 목록이면 빈 리스트를 돌려준다 — 태그는 있되 아무 것도 선언하지
    않은 경우)."""
    lines = (body or "").splitlines()
    tag_re = _tag_re(tag)
    tag_idx = None
    for i, line in enumerate(lines):
        if tag_re.match(line):
            tag_idx = i
            break
    if tag_idx is None:
        return None

    rest = lines[tag_idx + 1:]
    i = 0
    while i < len(rest) and rest[i].strip() == "":
        i += 1
    if i < len(rest) and _FENCE_RE.match(rest[i]):
        i += 1
        paths = []
        while i < len(rest) and not _FENCE_RE.match(rest[i]):
            stripped = rest[i].strip()
            if stripped:
                paths.append(stripped)
            i += 1
        return paths

    paths = []
    while i < len(rest):
        m = _BULLET_RE.match(rest[i])
        if not m:
            break
        paths.append(m.group(1))
        i += 1
    return paths


# issue #2037: a `design-artifacts:` tag with trailing content on the same
# line (e.g. "design-artifacts: a.md, b.md") is not the contract shape --
# _TAG_RE requires nothing after the colon, so parse_declaration falls
# through to None exactly like an issue with no declaration at all. That
# byte-inert result must instead be refused loudly (observed live,
# tm-webfolio #5), quoting the required tag+bullet shape.
_MALFORMED_TAG_RE = re.compile(r"^\s*[-*]?\s*design-artifacts\s*:\s*\S+", re.IGNORECASE)


def malformed_declaration_line(body: str, tag: str = "design-artifacts") -> str | None:
    """설계-산출물 선언이 있는 태그 줄이지만 계약 형태(태그 줄 단독 +
    불릿/펜스)에 맞지 않는 경우 그 줄을 그대로 돌려준다. 계약 형태를
    만족하거나(태그 다음이 비어있음) 태그 자체가 없으면 None."""
    malformed_re = _MALFORMED_TAG_RE if tag == "design-artifacts" else re.compile(
        rf"^\s*[-*]?\s*{re.escape(tag)}\s*:\s*\S+", re.IGNORECASE)
    for line in (body or "").splitlines():
        if malformed_re.match(line):
            return line.strip()
    return None


def missing_artifacts(repo: Path, declared_paths: list[str]) -> list[str]:
    """선언된 경로 중 저장소 루트 기준으로 존재하지 않는 것만 순서대로
    돌려준다(모두 존재하면 빈 리스트)."""
    return [p for p in declared_paths if not (repo / p).exists()]


def check(repo: Path, issue: int) -> list[str]:
    body = gh_rest.fetch_issue_body(repo, issue)
    if body is None:
        return [f"이슈 #{issue} 본문을 읽을 수 없다(`gh api repos/.../issues/{issue}` 실패) — "
                f"design-artifacts 게이트는 검사 불가를 통과로 취급하지 않는다(fail-closed)."]
    declared = parse_declaration(body)
    if declared is None:
        malformed = malformed_declaration_line(body)
        if malformed is not None:
            return [f"이슈 #{issue}의 design-artifacts 선언이 잘못된 형태다: {malformed!r} "
                    f"— 태그 줄에 내용이 바로 붙어 있다. 필요한 형태: "
                    f"'design-artifacts:' 태그 줄 다음에 '- path/one.md' 불릿 목록(또는 "
                    f"```fenced``` 블록) — 태그 줄 자체는 콜론 뒤에 아무 것도 오면 안 된다."]
        return []
    missing = missing_artifacts(repo, declared)
    if not missing:
        return []
    listed = "\n".join(f"  - {p}" for p in missing)
    return [f"이슈 #{issue}가 선언한 design-artifacts 중 다음 경로가 작업 트리에 없다:\n"
            f"{listed}"]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: design_artifacts_gate.py <issue-number> [--repo <경로>]")
        return 1
    issue = int(sys.argv[1])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    violations = check(repo, issue)
    if violations:
        for v in violations:
            print(v)
        return 0
    print(f"design-artifacts: 이슈 #{issue}는 선언된 산출물이 없거나 모두 존재한다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
