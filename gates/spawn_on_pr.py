#!/usr/bin/env python3
"""PR 생성 시 board_condition 이 기계적으로 결정 가능한 검증 역할을 자동
스폰한다(issue-1323 req 3).

10개 board_condition 역할 중 "커밋이 브랜치에 랜딩했다 AND 이 커밋에 대한
기록이 아직 없다"만으로 판정되는 2개만 대상이다 — 나머지 8개는 컨텐츠
분류나 다른 역할의 기록을 전제조건으로 요구해 여기서 다루지 않는다
(docs/issue-1323/reports/implementation/survey-phase3-4.md).

`reconcile()`(spawn.py) 의 계약은 건드리지 않는다 — 이 모듈은
`_board_wide_sweep`(spawn.py) 이 이미 하는 것과 같은 board-wide 스윕
레이어에서 추가로 호출되는, closure_sweep/spawn_coverage 와 나란히
서는 세 번째 스윕이다.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import spawn  # noqa: E402

PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")


def applicable_roles(subject_board: dict, roles: tuple[str, ...] = PR_TRIGGERED_ROLES) -> list[str]:
    """`subject_board`(`board(root)[subject]`, `{role: frontmatter}`) 에서
    아직 기록이 없는 `roles` 서브셋을 `roles` 가 나열한 순서 그대로
    돌려준다. 순수 함수, I/O 없음."""
    return [r for r in roles if r not in subject_board]


def missing_verification(root: Path) -> dict[str, list[str]]:
    """보드 전체를 훑어 `{subject: [빠진 role, ...]}` 을 만든다. PR 이
    실제로 열려있거나 머지된 subject 만 대상이다 — 트리거는 "PR 생성"이지
    "어떤 브랜치에든 커밋이 존재함"이 아니기 때문이다."""
    out: dict[str, list[str]] = {}
    b = spawn.board(root)
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        pr_number = spawn._pr_open_or_merged_for_branch(root, f"{subject}/implementation")
        if pr_number is None:
            continue
        out[subject] = missing
    return out


def spawn_missing_for_pr(root: Path, cwd: str, dry_run: bool = False) -> list[tuple[str, str]]:
    """`missing_verification()` 이 찾은 `(subject, role)` 쌍마다 그 역할을
    등록+스폰한다. `dry_run=True` 면 등록/스폰 없이 쌍만 돌려준다(테스트
    용, 실제 세션을 띄우지 않는다)."""
    pairs: list[tuple[str, str]] = []
    for subject, roles in missing_verification(root).items():
        issue = int(subject.split("-", 1)[1])
        for role in roles:
            pairs.append((subject, role))
    if dry_run:
        return pairs
    for subject, role in pairs:
        issue = int(subject.split("-", 1)[1])
        task = (f"이슈 #{issue}: {role} — {subject}/implementation 브랜치에 랜딩된 "
                f"커밋에 대해 아직 기록이 없다. PR 생성 시 자동 스폰됨 (spawn_on_pr.py).")
        spawn.roster_register(
            f"issue-{issue}/{role}",
            {"role": role, "issue": issue, "expects_pr": True, "work": cwd},
        )
        spawn._spawn_one(cwd, role, task, unattended=True, issue=issue, bounded=True)
    return pairs
