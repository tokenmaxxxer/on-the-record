#!/usr/bin/env python3
"""머지 게이트 — PR 하나가 머지될 자격이 있는지 판정한다(issue-1323
req 4): phase 2 의 check-runner 결과(전부 pass) + 필요한 검증 기록(req 3
이 스폰하는 2개 role) 이 모두 갖춰져야 `allowed`.

`.github/workflows/` 파일이 아니다 — 이 레포엔 그런 CI 표면이 없고,
role 세션은 그걸 추가하는 게 거절된다. `check_runner.py` 와 같은 자세로
PR 번호를 받는 스크립트다.

  python3 gates/merge_gate.py <pr> <subject> [--repo <경로>]
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import spawn_on_pr  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402

_RESULT_HEADER = re.compile(
    r"^## Acceptance check-runner result:\s*(\d+)/(\d+)\s*passed", re.MULTILINE)


def parse_check_runner_result(comment_body: str) -> dict | None:
    """`check_runner.format_comment()` 가 만드는 정확한 헤더 모양과
    맞춰본다. 안 맞으면 `None`."""
    m = _RESULT_HEADER.search(comment_body)
    if not m:
        return None
    return {"passed": int(m.group(1)), "total": int(m.group(2))}


def latest_check_runner_comment(repo: Path, pr: int) -> str | None:
    """이 모듈에서 유일하게 `gh` 를 호출하는 함수. 헤더 정규식에 맞는
    마지막 코멘트를 돌려준다."""
    r = subprocess.run(["gh", "pr", "view", str(pr), "--json", "comments"],
                        cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import json
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    comments = data.get("comments", [])
    for c in reversed(comments):
        body = c.get("body", "")
        if _RESULT_HEADER.search(body):
            return body
    return None


def required_verification_missing(root: Path, subject: str) -> list[str]:
    """req 3 의 role 목록을 재사용하는 얇은 래퍼 — 두 번째 목록을 만들지
    않는다."""
    b = spawn.board(root)
    subject_board = b.get(subject, {})
    return spawn_on_pr.applicable_roles(subject_board)


def evaluate(root: Path, repo: Path, pr: int, subject: str) -> dict:
    """`{"allowed": bool, "reasons": [str, ...]}`. 셋 다 깨끗해야
    `allowed`: check-runner 코멘트 존재, `passed == total`, 필요 검증
    기록 모두 존재."""
    reasons: list[str] = []
    comment = latest_check_runner_comment(repo, pr)
    if comment is None:
        reasons.append("check-runner 코멘트를 찾을 수 없다")
    else:
        result = parse_check_runner_result(comment)
        if result is None or result["passed"] != result["total"]:
            reasons.append(f"check-runner 결과가 전부 pass 가 아니다: {result}")
    missing = required_verification_missing(root, subject)
    if missing:
        reasons.append(f"필요한 검증 기록이 없다: {missing}")
    return {"allowed": not reasons, "reasons": reasons}


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: merge_gate.py <pr> <subject> [--repo <경로>]")
        return 1
    pr, subject = int(sys.argv[1]), sys.argv[2]
    repo = Path(".").resolve()
    if "--repo" in sys.argv:
        repo = Path(sys.argv[sys.argv.index("--repo") + 1]).resolve()
    result = evaluate(repo, repo, pr, subject)
    if result["allowed"]:
        print(f"허용: PR #{pr} ({subject}) 머지 자격 있음")
        return 0
    print(f"거절: PR #{pr} ({subject})")
    for reason in result["reasons"]:
        print(f"  - {reason}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
