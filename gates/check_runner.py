#!/usr/bin/env python3
"""결정적 체크러너 — 이슈의 `## Acceptance` 절에 있는 실행가능한
검사(test/grep/file-existence)를 PR 브랜치에 대해 실제로 실행하고,
구조화된 결과를 PR 코멘트 하나로 남긴다(issue-1323 req 2).

LLM 세션이 아니라 기계 단계다 — 판단(judgment)이 필요한 검사는 이
러너의 범위 밖이며, 조용히 건너뛰지 않고 명시적으로 거부한다.

  python3 gates/check_runner.py <pr-number> <issue-number> [--repo <경로>]
"""
from __future__ import annotations
import re
import shlex
import subprocess
import sys
from pathlib import Path

# acceptance_gate.py 의 실행가능-산출물 admission 정규식과 같은 계열:
# 백틱으로 감싼 test/gates 경로, 또는 'check:'/'gate:' 줄.
_SECTION_HEADING = re.compile(r"(?im)^#{1,6}\s*acceptance\b.*$")
_NEXT_HEADING = re.compile(r"(?m)^#{1,6}\s")
_CHECK_LINE = re.compile(
    r"^\s*[-*]?\s*(?:check|gate)\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_BACKTICK_CMD = re.compile(r"`([^`]+)`")
_GREP_PREFIXED = re.compile(r"^\s*grep\s*:\s*(.+)$", re.IGNORECASE)


def _acceptance_section(body: str) -> str | None:
    m = _SECTION_HEADING.search(body)
    if not m:
        return None
    rest = body[m.end():]
    nxt = _NEXT_HEADING.search(rest)
    return rest[: nxt.start()] if nxt else rest


def parse_checks(section: str) -> list[dict]:
    """Acceptance 절 텍스트에서 각 `check:`/`gate:` 줄을 뽑아 분류한다.

    분류: `test`(백틱 안이 실행가능 shell/pytest 명령), `grep`
    (`grep:` 접두 패턴), `file-existence`(백틱 안이 명령이 아니라
    맨 파일 경로), `judgment`(무엇에도 해당하지 않음 — 실행 거부 대상).
    """
    checks = []
    for m in _CHECK_LINE.finditer(section):
        raw = m.group(1).strip()
        gm = _GREP_PREFIXED.match(raw)
        if gm:
            checks.append({"type": "grep", "raw": raw, "pattern": gm.group(1).strip()})
            continue
        bm = _BACKTICK_CMD.search(raw)
        if bm:
            cmd = bm.group(1).strip()
            tokens = cmd.split()
            looks_like_command = bool(tokens) and (
                "/" in tokens[0] and tokens[0].count(".") >= 1
                or tokens[0] in ("python3", "python", "bash", "sh", "pytest")
            )
            if looks_like_command:
                checks.append({"type": "test", "raw": raw, "command": cmd})
            else:
                checks.append({"type": "file-existence", "raw": raw, "path": cmd})
            continue
        checks.append({"type": "judgment", "raw": raw})
    return checks


class JudgmentCheckError(Exception):
    """A check could not be classified as test/grep/file-existence."""


def run_checks(repo: Path, checks: list[dict]) -> list[dict]:
    """`checks`를 `repo`(PR 브랜치 체크아웃) 기준으로 실제 실행한다.

    `judgment` 타입은 실행하지 않고 명시적 에러를 낸다 — 이 러너는
    기계적으로 판정 가능한 검사만 다룬다.
    """
    results = []
    for chk in checks:
        kind = chk["type"]
        if kind == "judgment":
            raise JudgmentCheckError(
                f"판단이 필요한 검사는 체크러너 범위 밖이다: {chk['raw']!r}")
        if kind == "test":
            r = subprocess.run(shlex.split(chk["command"]), cwd=repo,
                                capture_output=True, text=True)
            results.append({
                "check": chk["raw"], "type": kind,
                "status": "pass" if r.returncode == 0 else "fail",
                "output": (r.stdout + r.stderr)[-2000:],
            })
        elif kind == "grep":
            r = subprocess.run(["grep", "-r", chk["pattern"], "."], cwd=repo,
                                capture_output=True, text=True)
            results.append({
                "check": chk["raw"], "type": kind,
                "status": "pass" if r.returncode == 0 else "fail",
                "output": r.stdout[-2000:],
            })
        elif kind == "file-existence":
            exists = (repo / chk["path"]).exists()
            results.append({
                "check": chk["raw"], "type": kind,
                "status": "pass" if exists else "fail",
                "output": f"{chk['path']} {'exists' if exists else 'missing'}",
            })
        else:
            raise JudgmentCheckError(
                f"알 수 없는 검사 타입: {kind!r} ({chk['raw']!r})")
    return results


def format_comment(results: list[dict]) -> str:
    """구조화된 마크다운 PR 코멘트 본문 하나를 만든다."""
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "pass")
    lines = [f"## Acceptance check-runner result: {passed}/{total} passed", ""]
    for r in results:
        mark = "PASS" if r["status"] == "pass" else "FAIL"
        lines.append(f"- [{mark}] ({r['type']}) {r['check']}")
    return "\n".join(lines)


def post_comment(pr: int, body: str, repo: Path) -> bool:
    """이 러너에서 유일하게 `gh`를 호출해 PR 에 코멘트를 남기는 함수."""
    r = subprocess.run(["gh", "pr", "comment", str(pr), "--body", body],
                        cwd=repo, capture_output=True, text=True)
    return r.returncode == 0


def _issue_view_body(repo: Path, issue: int) -> str | None:
    r = subprocess.run(["gh", "issue", "view", str(issue), "--json", "body"],
                        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    data = json.loads(r.stdout)
    return data.get("body", "")


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: check_runner.py <pr-number> <issue-number> [--repo <경로>]")
        return 1
    pr, issue = int(sys.argv[1]), int(sys.argv[2])
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()

    body = _issue_view_body(repo, issue)
    if body is None:
        print(f"이슈 #{issue} 본문을 읽을 수 없다(`gh issue view` 실패)")
        return 1
    section = _acceptance_section(body)
    if section is None:
        print(f"이슈 #{issue}에 '## Acceptance' 절이 없다")
        return 1
    checks = parse_checks(section)
    try:
        results = run_checks(repo, checks)
    except JudgmentCheckError as e:
        print(f"거부: {e}")
        return 1
    comment = format_comment(results)
    print(comment)
    post_comment(pr, comment, repo)
    return 0 if all(r["status"] == "pass" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
