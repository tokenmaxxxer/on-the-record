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

issue #1360 hotfix: `missing_verification()` 은 보드 전체(닫힌 이슈
포함)를 스캔해 60초 틱마다 오래된 subject 를 재귀 스폰하고 있었다 —
#1323 요구 3은 "PR 생성" 이벤트 트리거였지 보드 전체 백필이 아니었다
(27건의 재귀 스폰 사고, docs/issue-1360 참조). 이제 이슈가 아직 OPEN 인
subject 만 대상으로 하고, 틱당 스폰 개수를 `SPAWN_CAP` 으로 캡핑하며,
닫힌 이슈의 검증 부채는 `backfill_closed()`(opt-in, dry-run 기본) 로만
다룬다.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn  # noqa: E402
import closure_sweep  # noqa: E402

PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")

# 틱당 스폰 상한(issue #1360) — 자동 워치독 틱 하나가 한 번에 스폰하는
# (subject, role) 쌍의 개수를 제한하는 예산 백스톱. 초과분은 조용히
# 버리지 않고 몇 건이 미뤄졌는지 한 줄로 찍는다.
SPAWN_CAP = 4


def applicable_roles(subject_board: dict, roles: tuple[str, ...] = PR_TRIGGERED_ROLES) -> list[str]:
    """`subject_board`(`board(root)[subject]`, `{role: frontmatter}`) 에서
    아직 기록이 없는 `roles` 서브셋을 `roles` 가 나열한 순서 그대로
    돌려준다. 순수 함수, I/O 없음."""
    return [r for r in roles if r not in subject_board]


def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
    """`issue_states`(issue #-> state 사전) 에서 `issue` 가 OPEN 인지
    판정한다. 사전이 없거나(gh 실패/truncated) `issue` 가 사전에 없으면
    (조회 불가) 안전한 쪽으로 fail-closed — OPEN 이 아니라고 본다: 상태를
    모르는 subject 를 자동 스폰하지 않는 편이 이 게이트가 고치려는
    사고(board-wide 재귀 스폰)를 반복하지 않는다."""
    if issue_states is None:
        return False
    return issue_states.get(issue) == "OPEN"


def missing_verification(root: Path, issue_states: dict[int, str] | None = None
                          ) -> dict[str, list[str]]:
    """보드 전체를 훑어 `{subject: [빠진 role, ...]}` 을 만든다. 대상
    조건: PR 이 실제로 열려있거나 머지되어 있고(트리거는 "PR 생성"이지
    "어떤 브랜치에든 커밋이 존재함"이 아니므로), AND 그 subject 의
    이슈가 아직 OPEN 이어야 한다(issue #1360) — 닫힌 이슈의 검증 부채는
    이 자동 경로의 스코프 밖이다(`backfill_closed()` 가 opt-in 으로
    다룬다).

    `issue_states` 는 이슈번호 -> state 사전(선택) — 주어지지 않으면
    `closure_sweep.issue_state_index_all()` 로 한 번에 가져온다(호출자가
    이미 같은 틱에서 가져온 사전이 있으면 그걸 재사용해 `gh` 중복 호출을
    피한다, closure_sweep 의 같은 패턴)."""
    out: dict[str, list[str]] = {}
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if not ok:
            issue_states = None
    b = spawn.board(root)
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        pr_number = spawn._pr_open_or_merged_for_branch(root, f"{subject}/implementation")
        if pr_number is None:
            continue
        issue = int(subject.split("-", 1)[1])
        if not _issue_is_open(issue, issue_states):
            continue
        out[subject] = missing
    return out


def spawn_missing_for_pr(root: Path, cwd: str, dry_run: bool = False,
                          issue_states: dict[int, str] | None = None,
                          spawn_cap: int = SPAWN_CAP) -> list[tuple[str, str]]:
    """`missing_verification()` 이 찾은 `(subject, role)` 쌍 중 최대
    `spawn_cap` 개를 등록+스폰한다. 초과분은 스폰하지 않고, 몇 건이
    미뤄졌는지 한 줄 찍는다(issue #1360 — no silent cap). `dry_run=True`
    면 등록/스폰 없이 (캡 적용된) 쌍만 돌려준다(테스트용, 실제 세션을
    띄우지 않는다)."""
    all_pairs: list[tuple[str, str]] = []
    for subject, roles in missing_verification(root, issue_states=issue_states).items():
        for role in roles:
            all_pairs.append((subject, role))
    pairs = all_pairs[:spawn_cap]
    deferred = len(all_pairs) - len(pairs)
    if deferred > 0:
        print(f"[spawn-on-pr] cap={spawn_cap} 초과로 {deferred}건 미룸 "
              f"(다음 틱 또는 backfill_closed() 로 처리)")
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


def _missing_verification_closed(root: Path, issue_states: dict[int, str] | None
                                  ) -> dict[str, list[str]]:
    """`missing_verification()` 의 거울 — PR 이 있고 기록이 빠진 subject
    중 이슈가 CLOSED 인 것만 돌려준다(issue #1360 req 3, opt-in
    backfill 전용). `issue_states` 가 없거나(gh 실패) 이슈가 사전에
    없으면(조회 불가) 대상에서 제외한다 — 상태를 모르는 subject 를
    "닫혔다"고 넘겨짚지 않는다."""
    out: dict[str, list[str]] = {}
    b = spawn.board(root)
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        pr_number = spawn._pr_open_or_merged_for_branch(root, f"{subject}/implementation")
        if pr_number is None:
            continue
        issue = int(subject.split("-", 1)[1])
        if issue_states is None or issue_states.get(issue) != "CLOSED":
            continue
        out[subject] = missing
    return out


def backfill_closed(root: Path, cwd: str, dry_run: bool = True) -> list[tuple[str, str]]:
    """닫힌 이슈의 검증 부채를 훑어 스폰하는 opt-in CLI 전용 경로(issue
    #1360 req 3). 자동 틱(`spawn_missing_for_pr`)에서는 절대 호출하지
    않는다 — 사람이 명시적으로 `python3 gates/spawn_on_pr.py
    backfill-closed` 를 실행할 때만 쓴다. `dry_run` 기본값은 `True` —
    실제로 스폰하려면 호출자가 `--live` 로 명시해야 한다."""
    issue_states, ok = closure_sweep.issue_state_index_all(root)
    if not ok:
        issue_states = None
    pairs: list[tuple[str, str]] = []
    for subject, roles in _missing_verification_closed(root, issue_states).items():
        for role in roles:
            pairs.append((subject, role))
    if dry_run:
        return pairs
    for subject, role in pairs:
        issue = int(subject.split("-", 1)[1])
        task = (f"이슈 #{issue}: {role} — {subject}/implementation 브랜치에 랜딩된 "
                f"커밋에 대해 아직 기록이 없다(닫힌 이슈 백필, "
                f"backfill_closed() 로 opt-in 스폰됨).")
        spawn.roster_register(
            f"issue-{issue}/{role}",
            {"role": role, "issue": issue, "expects_pr": True, "work": cwd},
        )
        spawn._spawn_one(cwd, role, task, unattended=True, issue=issue, bounded=True)
    return pairs


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="spawn_on_pr — PR-triggered 검증 스폰 (issue #1360)")
    sub = parser.add_subparsers(dest="command", required=True)
    backfill = sub.add_parser(
        "backfill-closed",
        help="닫힌 이슈의 검증 부채를 훑는다. 기본은 dry-run(목록만 출력).")
    backfill.add_argument("--live", action="store_true",
                           help="실제로 등록+스폰한다(기본은 dry-run).")
    args = parser.parse_args(argv)
    if args.command == "backfill-closed":
        pairs = backfill_closed(ROOT, str(ROOT), dry_run=not args.live)
        mode = "LIVE" if args.live else "DRY-RUN"
        print(f"[backfill-closed] {mode}: {len(pairs)}건")
        for subject, role in pairs:
            print(f"  {subject} / {role}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
