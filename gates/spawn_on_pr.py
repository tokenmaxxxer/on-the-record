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
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn  # noqa: E402
import closure_sweep  # noqa: E402
import ci as _ci  # noqa: E402

PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")

# 틱당 스폰 상한(issue #1360) — 자동 워치독 틱 하나가 한 번에 스폰하는
# (subject, role) 쌍의 개수를 제한하는 예산 백스톱. 초과분은 조용히
# 버리지 않고 몇 건이 미뤄졌는지 한 줄로 찍는다.
SPAWN_CAP = 4

# issue #1476: 승인-대기 상태에서 매 틱 재스폰하던 것을 막는 park 상태
# 저장소 — `root`(대상 레포) 기준 상대경로. 키는 "<subject>/<role>",
# 값은 {"blocked": bool, "pr_number": int} — 두 필드 모두 구조화 신호다:
# `pr_number`(`_pr_open_or_merged_for_branch`가 이미 매 틱 조회하는 값)가
# 안 바뀌었으면 브랜치에 새 커밋이 없었다는 뜻이고(요구 2의 "새 커밋"
# 재무장 트리거), `blocked`는 `gates/ci.py:_approved_roles_on_issue()`
# (승인자 allowlist, `APPROVE issue-<n>/<role>` 문자열 완전일치 — 프로즈
# 매칭이 아니다)로 구한다. 두 신호가 이전 틱과 완전히 같을 때만 park —
# 결코 경과 시간만으로 재무장하지 않는다.
PARK_STATE_REL = Path("runs") / "spawn_on_pr_parked.json"


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


def _park_state_path(root: Path) -> Path:
    return root / PARK_STATE_REL


def load_park_state(root: Path) -> dict[str, dict]:
    """park 상태를 읽는다. 파일이 없거나(첫 틱) 깨졌으면 빈 사전 — 빈
    사전은 "park 후보 없음"과 같은 뜻이라 이 함수 하나만으로 fail-safe
    하다."""
    p = _park_state_path(root)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def _save_park_state(root: Path, state: dict[str, dict]) -> None:
    p = _park_state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def is_approval_blocked(root: Path, issue: int, role: str) -> bool:
    """구조화 신호: `gates/ci.py:_approved_roles_on_issue()`(승인자
    allowlist 계정의 `APPROVE issue-<n>/<role>` 코멘트, 문자열 완전일치)
    에 `role` 이 없으면 아직 승인-대기(blocked)다."""
    return role not in _ci._approved_roles_on_issue(root, issue)


def should_park(prior: dict | None, pr_number: int | None, blocked: bool) -> bool:
    """park 판정: 순수 함수. 이번 틱도 여전히 blocked 이고, 이전 틱
    기록(`prior`)이 있으며, 그 기록의 `pr_number`/`blocked` 가 이번 틱과
    완전히 같을 때만 park — 그중 하나라도 다르면(새 커밋으로 PR 번호가
    바뀌었거나, 승인 코멘트가 새로 달려 더 이상 blocked 가 아니면)
    재무장(park 아님)한다. `prior is None`(첫 틱 후보)은 언제나 park
    아님 — 아직 한 번도 시도해 본 적 없는 역할을 재시도로 오인하지
    않는다."""
    if not blocked or prior is None:
        return False
    return prior.get("blocked") is True and prior.get("pr_number") == pr_number


def parked_report(root: Path) -> list[tuple[str, str]]:
    """현재 park 상태에서 `blocked=True` 인 `(subject, role)` 쌍을
    돌려준다 — watchdog 출력이 park 된 항목을 waiting-for-human 으로
    계속 보여주는 데 쓴다(요구 3, watch-coverage 불가침)."""
    out = []
    for key, entry in sorted(load_park_state(root).items()):
        if entry.get("parked"):
            subject, _, role = key.partition("/")
            out.append((subject, role))
    return out


def unpark(root: Path, subject: str, role: str) -> bool:
    """명시적 unpark(요구 2의 세 번째 재무장 트리거) — park 항목을
    지운다. 지울 게 있었으면 True."""
    state = load_park_state(root)
    key = f"{subject}/{role}"
    if key in state:
        del state[key]
        _save_park_state(root, state)
        return True
    return False


def spawn_missing_for_pr(root: Path, cwd: str, dry_run: bool = False,
                          issue_states: dict[int, str] | None = None,
                          spawn_cap: int = SPAWN_CAP) -> list[tuple[str, str]]:
    """`missing_verification()` 이 찾은 `(subject, role)` 쌍 중 최대
    `spawn_cap` 개를 등록+스폰한다. 초과분은 스폰하지 않고, 몇 건이
    미뤄졌는지 한 줄 찍는다(issue #1360 — no silent cap). `dry_run=True`
    면 등록/스폰 없이 (캡 적용된) 쌍만 돌려준다(테스트용, 실제 세션을
    띄우지 않는다).

    issue #1476: 후보 쌍마다 이전 park 상태(`load_park_state`)가 있고
    이번 틱의 `pr_number`가 그 상태와 같으면(새 커밋 없음) `is_approval_
    blocked()`(구조화 신호)로 확인해 여전히 승인-대기면 park 하고
    스폰하지 않는다. `is_approval_blocked()`(gh 호출)는 바로 이 경우 —
    이전 park 기록이 있고 `pr_number`가 같을 때만 호출한다: 후보를 처음
    보는 틱은 gh 를 전혀 안 건드리고 그냥 스폰한다(기존 동작 그대로)."""
    all_pairs: list[tuple[str, str, int | None]] = []
    for subject, roles in missing_verification(root, issue_states=issue_states).items():
        pr_number = spawn._pr_open_or_merged_for_branch(root, f"{subject}/implementation")
        for role in roles:
            all_pairs.append((subject, role, pr_number))

    park_state = load_park_state(root)
    to_spawn: list[tuple[str, str, int | None, int]] = []
    parked_now: list[tuple[str, str]] = []
    for subject, role, pr_number in all_pairs:
        issue = int(subject.split("-", 1)[1])
        key = f"{subject}/{role}"
        prior = park_state.get(key)
        if prior is not None and prior.get("pr_number") == pr_number and prior.get("blocked"):
            blocked = is_approval_blocked(root, issue, role)
            if should_park(prior, pr_number, blocked):
                parked_now.append((subject, role))
                park_state[key] = {"blocked": True, "pr_number": pr_number, "parked": True}
                continue
            if not blocked:
                park_state.pop(key, None)
        to_spawn.append((subject, role, pr_number, issue))

    if parked_now:
        print(f"[spawn-on-pr] park={len(parked_now)}건 waiting-for-human "
              f"(승인-대기 상태 변화 없음): {parked_now}")

    pairs3 = to_spawn[:spawn_cap]
    deferred = len(to_spawn) - len(pairs3)
    if deferred > 0:
        print(f"[spawn-on-pr] cap={spawn_cap} 초과로 {deferred}건 미룸 "
              f"(다음 틱 또는 backfill_closed() 로 처리)")

    pairs = [(subject, role) for subject, role, _pr, _issue in pairs3]
    if dry_run:
        return pairs
    for subject, role, pr_number, issue in pairs3:
        task = (f"이슈 #{issue}: {role} — {subject}/implementation 브랜치에 랜딩된 "
                f"커밋에 대해 아직 기록이 없다. PR 생성 시 자동 스폰됨 (spawn_on_pr.py).")
        spawn.roster_register(
            f"issue-{issue}/{role}",
            {"role": role, "issue": issue, "expects_pr": True, "work": cwd},
        )
        spawn._spawn_one(cwd, role, task, unattended=True, issue=issue, bounded=True)
        park_state[f"{subject}/{role}"] = {"blocked": True, "pr_number": pr_number, "parked": False}
    _save_park_state(root, park_state)
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
    unpark_p = sub.add_parser(
        "unpark", help="park 된 (subject, role) 을 명시적으로 재무장한다(issue #1476 요구 2).")
    unpark_p.add_argument("--subject", required=True, help="예: issue-1163")
    unpark_p.add_argument("--role", required=True, help="예: conformance-review")
    args = parser.parse_args(argv)
    if args.command == "backfill-closed":
        pairs = backfill_closed(ROOT, str(ROOT), dry_run=not args.live)
        mode = "LIVE" if args.live else "DRY-RUN"
        print(f"[backfill-closed] {mode}: {len(pairs)}건")
        for subject, role in pairs:
            print(f"  {subject} / {role}")
        return 0
    if args.command == "unpark":
        cleared = unpark(ROOT, args.subject, args.role)
        print(f"[unpark] {args.subject}/{args.role}: "
              f"{'재무장됨' if cleared else 'park 기록 없음'}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
