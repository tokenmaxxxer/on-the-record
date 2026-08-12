#!/usr/bin/env python3
"""post-landing verification obligation — issue #1098 (northpole req#3, req#5).

`gh pr merge`가 성공하면, 그 PR을 landed한 issue/role에 대해 "실배선
검증이 아직 안 됐다"는 상태를 파일로 남긴다. `reexecution_gate.py`가 이미
가진 pass/fail/error verdict를 재구현하지 않고, 그 verdict가 obligation의
`opened_at` 이후에 찍히면 obligation을 resolve한다 — 실행은
`reexecution_gate.py`에게 맡기고, 이 모듈은 "아직 검증 안 됨"이라는 상태
그 자체만 추적한다(ADR docs/issue-1098/decisions/2026-08-12-post-landing-obligation.md).

obligation은 절대 조용히 삭제되지 않는다 — resolve는 상태만
`"resolved"`로 바꿀 뿐 레코드를 지우지 않는다(감사 가능).

  python3 gates/landing_obligation.py open --issue <n> --role <role> \
      --pr <n> --sha <sha> [--repo <경로>]
  python3 gates/landing_obligation.py resolve --issue <n> --role <role> \
      --pr <n> [--repo <경로>]
"""
from __future__ import annotations
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import reexecution_gate  # noqa: E402

OPEN = "open"
RESOLVED = "resolved"
FAILING = "failing"


@dataclass(frozen=True)
class Obligation:
    status: str  # open | resolved | failing
    pr: int
    sha: str
    issue: int
    role: str
    opened_at: float


def obligation_path(repo: Path, issue: int, role: str, pr: int) -> Path:
    return repo / ".landing-obligations" / f"{issue}-{role}-{pr}.json"


def open_obligation(repo: Path, issue: int, role: str, pr: int,
                     sha: str) -> Path:
    """새 obligation을 `"open"` 상태로 쓴다. 이미 있으면 덮어쓰지 않고 그대로
    돌려준다 — 같은 랜딩에 대한 중복 호출이 opened_at을 갱신해 이미 진행
    중인 검증의 타임스탬프를 지우지 않게 한다."""
    path = obligation_path(repo, issue, role, pr)
    if path.exists():
        return path
    obligation = Obligation(OPEN, pr, sha, issue, role, time.time())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(obligation), ensure_ascii=False,
                                indent=2))
    return path


def read_obligation(repo: Path, issue: int, role: str,
                     pr: int) -> Obligation | None:
    path = obligation_path(repo, issue, role, pr)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    return Obligation(**data)


def _write(repo: Path, issue: int, role: str, pr: int,
           obligation: Obligation) -> Path:
    path = obligation_path(repo, issue, role, pr)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(obligation), ensure_ascii=False,
                                indent=2))
    return path


def resolve_with_reexecution_verdict(repo: Path, issue: int, role: str,
                                      pr: int) -> Obligation | None:
    """`.reexecution/<issue>-<role>.json`의 verdict를 읽어 obligation 상태를
    갱신한다. obligation이 없으면 아무것도 하지 않고 None. verdict가 없거나
    obligation의 opened_at보다 먼저 찍힌 것이면 상태를 바꾸지 않는다 — 랜딩
    "이후"에 실제로 재실행됐다는 것만 resolve의 근거로 인정한다."""
    obligation = read_obligation(repo, issue, role, pr)
    if obligation is None:
        return None
    verdict = reexecution_gate.read_verdict(repo, issue, role)
    if verdict is None or verdict.timestamp < obligation.opened_at:
        return obligation
    if verdict.kind == reexecution_gate.PASS:
        new_status = RESOLVED
    else:
        new_status = FAILING
    updated = Obligation(new_status, obligation.pr, obligation.sha,
                          obligation.issue, obligation.role,
                          obligation.opened_at)
    _write(repo, issue, role, pr, updated)
    return updated


def list_open_obligations(repo: Path) -> list[Obligation]:
    """상태가 `"open"` 또는 `"failing"`인 obligation을 전부 돌려준다 —
    resolve되지 않은, 즉 아직 검증 의무가 남아 있는 것들."""
    root = repo / ".landing-obligations"
    if not root.is_dir():
        return []
    result = []
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        obligation = Obligation(**data)
        if obligation.status in (OPEN, FAILING):
            result.append(obligation)
    return result


def _arg(argv: list[str], name: str, default: str | None = None) -> str | None:
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("open", "resolve"):
        print("landing_obligation: 첫 인자는 open 또는 resolve")
        return 2
    action = argv[0]
    rest = argv[1:]
    issue = _arg(rest, "--issue")
    role = _arg(rest, "--role")
    pr = _arg(rest, "--pr")
    repo = Path(_arg(rest, "--repo", ".")).resolve()
    if not (issue and role and pr):
        print("landing_obligation: --issue --role --pr 모두 필요하다")
        return 2
    if action == "open":
        sha = _arg(rest, "--sha")
        if not sha:
            print("landing_obligation open: --sha 필요하다")
            return 2
        path = open_obligation(repo, int(issue), role, int(pr), sha)
        print(f"landing_obligation: opened ({path})")
        return 0
    obligation = resolve_with_reexecution_verdict(repo, int(issue), role,
                                                    int(pr))
    if obligation is None:
        print("landing_obligation: no obligation on record")
        return 1
    print(f"landing_obligation: {obligation.status}")
    return 0 if obligation.status == RESOLVED else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
