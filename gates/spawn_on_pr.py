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
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn  # noqa: E402
import closure_sweep  # noqa: E402
import ci as _ci  # noqa: E402
import skip_eligibility  # noqa: E402
import state_paths  # noqa: E402

PR_TRIGGERED_ROLES = ("execution-observation", "conformance-review")

# 틱당 스폰 상한(issue #1360) — 자동 워치독 틱 하나가 한 번에 스폰하는
# (subject, role) 쌍의 개수를 제한하는 예산 백스톱. 초과분은 조용히
# 버리지 않고 몇 건이 미뤄졌는지 한 줄로 찍는다.
SPAWN_CAP = 4

# issue #1476: 승인-대기 상태에서 매 틱 재스폰하던 것을 막는 park 상태
# 저장소. 키는 "<subject>/<role>", 값은 {"blocked": bool, "pr_number": int}
# — 두 필드 모두 구조화 신호다: `pr_number`(`_pr_open_or_merged_for_branch`가
# 이미 매 틱 조회하는 값)가 안 바뀌었으면 브랜치에 새 커밋이 없었다는
# 뜻이고(요구 2의 "새 커밋" 재무장 트리거), `blocked`는
# `gates/ci.py:_approved_roles_on_issue()`(승인자 allowlist, `APPROVE
# issue-<n>/<role>` 문자열 완전일치 — 프로즈 매칭이 아니다)로 구한다. 두
# 신호가 이전 틱과 완전히 같을 때만 park — 결코 경과 시간만으로
# 재무장하지 않는다.
# issue #2240: 이건 오케스트레이터의 틱간 기억이지 대상 레포 상태가
# 아니다 — `root`(대상 레포) 기준이 아니라 state_paths 를 통해 앵커링된다.
PARK_STATE_FILENAME = "spawn_on_pr_parked.json"

# issue #2165: subject 의 `<subject>/implementation` PR 이 MERGED 로
# 확인된 사실은 종결적이다 — 한 번 확인되면 이후 틱에서 다시 확인할
# 필요가 없다(오히려 `gh` 호출이 그 틱에 실패해 fail-open 으로 OPEN 을
# 돌려주면 재스폰 위험이 생긴다). `closure_sweep.py`의
# out-of-index-seen 캐시(issue #1643)와 같은 모양: 한 번 확인된 subject
# 집합을 남기고, 이후 틱은 `gh` 를 부르기 전에 이 집합부터 확인한다.
# issue #2240: 이건 오케스트레이터 틱간 기억이다 — repo-local 이 아니라
# state_paths 로 앵커링된다(대상 레포는 절대 아니다).
MERGED_SEEN_STATE_FILENAME = "spawn_on_pr_merged_seen.json"


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


def _pr_number_for_branch(root: Path, branch: str,
                           pr_index: dict[str, dict] | None) -> int | None:
    """`pr_index`(있으면, `closure_sweep._pr_index_all()` 모양)에서
    OPEN/MERGED PR 번호를 찾는다. 인덱스가 없으면(잘렸거나 실패)
    `spawn._pr_open_or_merged_for_branch()`(브랜치당 `gh` 한 번)으로
    되돌아간다 — 이슈 #1498 요구 5: 인덱스가 있는 정상 경로는 subject 수와
    무관하게 O(1) gh 호출만 쓴다."""
    if pr_index is not None:
        entry = pr_index.get(branch)
        if entry is not None and entry.get("state") in ("OPEN", "MERGED"):
            return entry.get("number")
        return None
    return spawn._pr_open_or_merged_for_branch(root, branch)


def _pr_state_for_branch(root: Path, branch: str,
                          pr_index: dict[str, dict] | None) -> str | None:
    """`_pr_number_for_branch` 의 거울 — 번호 대신 상태 문자열
    (`"OPEN"`/`"MERGED"`)을 돌려준다(issue #1697 acceptance (b): merged
    subject 는 스폰 대상에서 빼야 하므로 상태 구분이 필요하다).
    `pr_index` 가 있으면 그 상태를 그대로 쓴다. 없으면(잘렸거나 실패)
    `spawn._pr_open_or_merged_for_branch()`로 PR 존재/번호를 먼저 확인하고,
    `spawn._merged_pr_for_branch()`로 그 번호가 MERGED 인지 가른다 — 두
    번째 조회가 실패하면(예: 테스트 환경에 `gh` 없음) OPEN 으로 fail-open
    한다: 이 함수의 목적은 merged 를 놓치지 않는 게 아니라 merged 를
    확신할 때만 스폰을 건너뛰는 것이다(#1360 의 issue-closed fail-closed
    와는 반대 방향 — 여기서 놓치면 그냥 오늘과 같은 스폰이지, 검증 부채가
    영영 안 도는 게 아니다)."""
    if pr_index is not None:
        entry = pr_index.get(branch)
        if entry is not None and entry.get("state") in ("OPEN", "MERGED"):
            return entry.get("state")
        return None
    number = spawn._pr_open_or_merged_for_branch(root, branch)
    if number is None:
        return None
    merged_number = spawn._merged_pr_for_branch(root, branch)
    return "MERGED" if merged_number == number else "OPEN"


def _implementation_session_active(root: Path, subject: str) -> bool:
    """`subject` 의 `<subject>/implementation` 세션이 로스터에 살아있는
    pid 로 남아있으면 True(issue #1697 두 번째 재현, issue-1696) — 활성
    fix 세션 중에 옵저버를 스폰하면 옵저버 브랜치가 fix 커밋 이전 main
    에서 잘려, 나중에 fix 가 머지되면 옵저버 record PR 이 719줄급
    REVERT 로 보이는 stale-base 사고가 난다(#1664 계열). 로스터에 항목이
    없거나 pid 가 이미 죽었으면 False — 오래된/고아 로스터 항목으로
    영원히 스폰을 막지 않는다(`spawn._alive()`가 실제 프로세스 생존을
    본다)."""
    entry = spawn._roster_load().get(f"{subject}/implementation")
    if entry is None:
        return False
    pid = entry.get("pid")
    return spawn._alive(pid if isinstance(pid, int) else 0)


def resolve_live_base(root: Path) -> str | None:
    """`root` 의 `origin` 을 fetch 하고, 그 시점의 base ref(`spawn._base()`
    가 고르는 origin/HEAD 또는 origin/main/master) 의 sha 를 돌려준다
    (issue #1697 acceptance (a)). `missing_verification`/
    `spawn_missing_for_pr` 는 오늘 `root` 의 로컬 git/gh 상태를 그대로
    읽기만 하고 스스로 fetch 하지 않는다 — 이 함수는 스폰 결정 시점
    자체를 최신 origin/main 에 앵커링해, main 이 스폰 사이에 움직인
    경우(moved-main fixture)에도 그 시점의 실제 main sha 를 반환한다.
    fetch 가 실패하면(오프라인 등) None — 호출부는 기존 로컬 상태로
    fail-open 한다."""
    r = subprocess.run(["git", "-C", str(root), "fetch", "-q", "origin"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    base = spawn._base(str(root))
    sha_r = subprocess.run(["git", "-C", str(root), "rev-parse", base],
                           capture_output=True, text=True)
    return sha_r.stdout.strip() if sha_r.returncode == 0 else None


def missing_verification(root: Path, issue_states: dict[int, str] | None = None,
                          pr_index: dict[str, dict] | None = None
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
    피한다, closure_sweep 의 같은 패턴). `pr_index` 도 마찬가지 —
    안 주면 `closure_sweep._pr_index_all()` 로 한 번에 가져온다(이슈
    #1498 요구 5: subject 당 `gh pr list --head` 대신 벌크 인덱스 한 번 +
    로컬 조인)."""
    out: dict[str, list[str]] = {}
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if not ok:
            issue_states = None
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)
    b = spawn.board(root)
    merged_seen: set[str] | None = None
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        if merged_seen is None:
            merged_seen = load_merged_seen(root)
        if subject in merged_seen:
            # issue #2165: 이미 이전 틱에서 MERGED 로 확인됐다 — merge
            # 는 종결적 사실이라 이후 틱의 (혹은 fail-open 하는) 재확인을
            # 기다리지 않고 바로 건너뛴다.
            continue
        branch = f"{subject}/implementation"
        pr_number = _pr_number_for_branch(root, branch, pr_index)
        if pr_number is None:
            continue
        issue = int(subject.split("-", 1)[1])
        if not _issue_is_open(issue, issue_states):
            continue
        pr_state = _pr_state_for_branch(root, branch, pr_index)
        if pr_state == "MERGED":
            merged_seen.add(subject)
            _save_merged_seen(root, merged_seen)
            spawn.ledger_write({
                "event": "spawn_on_pr_skip_merged",
                "subject": subject, "missing": missing,
            })
            print(f"[spawn-on-pr] {subject}: subject PR 이 이미 merged — "
                  f"옵저버 스폰 건너뜀 (missing={missing})")
            continue
        if _implementation_session_active(root, subject):
            spawn.ledger_write({
                "event": "spawn_on_pr_skip_active_implementation",
                "subject": subject, "missing": missing,
            })
            print(f"[spawn-on-pr] {subject}: implementation 세션이 아직 "
                  f"RUNNING — 옵저버 스폰 미룸 (missing={missing})")
            continue
        if "execution-observation" in missing:
            missing = _filter_execution_observation(root, subject, missing)
            if not missing:
                continue
        out[subject] = missing
    return out


def _filter_execution_observation(root: Path, subject: str,
                                   missing: list[str]) -> list[str]:
    """issue #745 Item 3 — `execution-observation` 스폰 자격을 세 축
    (변경 크기/비가역성/주장 어휘, `skip_eligibility.classify_for_subject`)
    으로 분류하고 ledger 에 population(R/S) 을 기록한다(20-PR 측정
    윈도우 재현용). population S(모두 low-risk) 면 `missing` 에서 뺀다;
    분류 자체가 실패하면(예: 브랜치/기록 없음) fail closed — required
    그대로 둔다."""
    try:
        classification = skip_eligibility.classify_for_subject(root, subject)
    except Exception:
        return missing
    spawn.ledger_write({
        "event": "execution_observation_classification",
        **classification,
    })
    if classification["skip_eligible"]:
        return [r for r in missing if r != "execution-observation"]
    return missing


def _park_state_path(root: Path) -> Path:
    """issue #2240: orchestrator cross-tick memory, not target-repo state —
    anchored via state_paths, never `root`. `root` is accepted for
    call-site symmetry with the rest of this module's `root`-scoped
    helpers; it is not used here."""
    return state_paths.orchestrator_state_path(PARK_STATE_FILENAME)


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


def load_merged_seen(root: Path) -> set[str]:
    """issue #2165: 이미 `pr_state == "MERGED"` 로 확인된 subject 집합.
    없거나(첫 실행) 깨졌으면 빈 집합 — `closure_sweep._load_out_of_index_seen`
    과 같은 fail-safe 모양."""
    p = state_paths.orchestrator_state_path(MERGED_SEEN_STATE_FILENAME)
    if not p.is_file():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return set()
    if not isinstance(data, list):
        return set()
    return {s for s in data if isinstance(s, str)}


def _save_merged_seen(root: Path, seen: set[str]) -> None:
    p = state_paths.orchestrator_state_path(MERGED_SEEN_STATE_FILENAME)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(seen)), encoding="utf-8")


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
                          spawn_cap: int = SPAWN_CAP,
                          backoff_state: dict | None = None,
                          pr_index: dict | None = None) -> list[tuple[str, str]]:
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
    보는 틱은 gh 를 전혀 안 건드리고 그냥 스폰한다(기존 동작 그대로).

    issue #1498 요구 4: 그 재확인 자체도 매 틱 부르지 않는다 —
    `closure_sweep.recheck_backoff()`(같은 `runs/gh_quota_backoff.json`,
    `recheck` 네임스페이스)로 게이팅해, 연속으로 변화 없던 키는 점점 뜸하게
    재확인한다. `backoff_state` 를 안 주면 이 함수가 직접 읽고 저장한다
    (호출부가 여러 재확인을 한 상태 객체로 묶고 싶으면 넘겨서 공유한다 —
    그때는 저장을 호출부가 책임진다).

    issue #1745: `pr_index` 를 주면(호출부가 같은 틱에서 이미
    `closure_sweep._pr_index_all()` 을 돌렸을 때) 이 함수는 다시 부르지
    않는다 — 한 틱 안에서 spawn-on-pr 과 closure-sweep 이 각자 같은 벌크
    PR 인덱스를 중복 조회하던 것(#1745 관측: 틱당 `pulls` 호출 2회)을
    없앤다. 생략하면(단독/테스트 호출) 기존처럼 직접 가져온다."""
    owns_backoff_state = backoff_state is None
    if backoff_state is None:
        backoff_state = closure_sweep.load_backoff_state(root)

    # issue #1498 요구 5: 벌크 PR 인덱스 한 번을 `missing_verification()` 과
    # 아래 subject 별 조인이 함께 재사용한다 — subject 수만큼 `gh pr list
    # --head` 를 부르지 않는다.
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)

    all_pairs: list[tuple[str, str, int | None]] = []
    for subject, roles in missing_verification(
            root, issue_states=issue_states, pr_index=pr_index).items():
        pr_number = _pr_number_for_branch(root, f"{subject}/implementation", pr_index)
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
            if not closure_sweep.recheck_backoff(backoff_state, key, False):
                # 이번 틱은 재확인 순번이 아니다 — gh 호출 없이 park 유지.
                parked_now.append((subject, role))
                park_state[key] = {"blocked": True, "pr_number": pr_number, "parked": True}
                continue
            blocked = is_approval_blocked(root, issue, role)
            if not blocked:
                closure_sweep.recheck_backoff(backoff_state, key, True)
            if should_park(prior, pr_number, blocked):
                parked_now.append((subject, role))
                park_state[key] = {"blocked": True, "pr_number": pr_number, "parked": True}
                continue
            if not blocked:
                park_state.pop(key, None)
        to_spawn.append((subject, role, pr_number, issue))

    if owns_backoff_state:
        closure_sweep.save_backoff_state(root, backoff_state)

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
    if pairs3:
        # 이슈 #1697 acceptance (a): 실제로 스폰하기 직전에 origin/main 을
        # 다시 fetch 해 그 시점의 sha 를 남긴다 — `missing_verification()`
        # 의 board/PR 판정은 이미 위에서 끝났지만, 옵저버 브랜치를 실제로
        # 자르는 건 `_spawn_one` -> `checkout_issue_branch()` 이고, 그
        # fetch 가 이번 스폰 배치와 같은 시점의 origin/main 을 보게 하려면
        # 여기서도 한 번 더 갱신해 둬야 워크스페이스가 오래 방치된
        # 워크스페이스 clone 이어도 스폰 시점 main 을 보게 된다.
        live_base_sha = resolve_live_base(root)
        print(f"[spawn-on-pr] live base sha={live_base_sha or '조회 실패(fail-open)'}")
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


def _missing_verification_closed(root: Path, issue_states: dict[int, str] | None,
                                  pr_index: dict[str, dict] | None = None
                                  ) -> dict[str, list[str]]:
    """`missing_verification()` 의 거울 — PR 이 있고 기록이 빠진 subject
    중 이슈가 CLOSED 인 것만 돌려준다(issue #1360 req 3, opt-in
    backfill 전용). `issue_states` 가 없거나(gh 실패) 이슈가 사전에
    없으면(조회 불가) 대상에서 제외한다 — 상태를 모르는 subject 를
    "닫혔다"고 넘겨짚지 않는다. `pr_index` 는 `missing_verification()` 과
    같은 벌크 인덱스 재사용(이슈 #1498 요구 5) — 안 주면 이 함수가 직접
    가져온다."""
    out: dict[str, list[str]] = {}
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)
    b = spawn.board(root)
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        pr_number = _pr_number_for_branch(root, f"{subject}/implementation", pr_index)
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
