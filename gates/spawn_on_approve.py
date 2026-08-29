#!/usr/bin/env python3
"""issue #2173: APPROVE 코멘트가 관측되면 phase-2 세션을 그 board-sweep
틱 안에서 즉시 스폰 시도한다.

배경(#2173 라이브 관측 + on-the-record #2165 재현): default(two-session)
플로우에서 phase-2 를 시작시키는 자동 경로가 이 저장소에 전혀 없었다 —
`gates/spawn_on_pr.py`(#1360)는 PR 이 생겼을 때 고정된 두 observer role
(execution-observation/conformance-review)만 스폰하고, 승인 여부는 그
스폰을 park 할지 판정하는 데만 쓴다(`is_approval_blocked`). 체크포인트
(단일 세션, `pipeline.py:await_approval_cmd`, #2129) 모드만 승인을
폴링하지만 그건 세션 하나가 자기 자신을 위해 기다리는 것이지 board-wide
자동 스폰이 아니다. 그 결과 default 모드에서는 사람/오케스트레이터가
APPROVE 코멘트를 보고 `spawn.py <role> ... --issue <n>` 를 수동으로
다시 실행해야만 phase-2 가 시작됐다.

이 모듈은 `spawn_on_pr.py` 와 나란한 세 번째 board-wide 스윕 신호이지만
트리거 조건이 정반대다 — 그쪽은 "PR 이 생겼다"(PR 존재가 트리거 — issue
#2628 이후로는 role 고정이 아니라 subject 당 부족한 독립 verification
개수를 본다), 이쪽은 "이 role 이 승인됐다"(role 은 board 가 이미 아는 임의의
role, `gates/ci.py._approved_skills_on_issue` 술어로 판정) + "아직
phase-2 기록이 없다"(board 에 role 항목 없음, phase-1 은 record 를 쓰지
않는다는 계약 그대로) + "phase-1 PR 이 이미 열려 있다"(계속할 브랜치가
있어야 한다 — PR 이 아직 없으면 이어받을 phase-1 산출물 자체가 없다) +
"이 role 은 아직 자동 phase-2 스폰을 한 번도 시도된 적 없다"(마지막
조건이 #1360 의 27회 재귀 스폰 사고를 재현하지 않는 안전장치다 — 시도가
한 번이라도 있었으면 그 다음부터는 기존 auto-respawn/watchdog 진단
경로가 죽은 엔트리를 다룬다, 이 모듈이 매 틱 경쟁하며 다시 스폰하지
않는다).

PR 조회는 `spawn._pr_open_or_merged_for_branch()`(spawn.py 가 이미
공개로 노출하는 공유 primitive, `spawn_on_pr.py` 자신도 내부적으로 이걸
쓴다)를 그대로 재사용한다 — `spawn_on_pr.py` 의 private
`_pr_number_for_branch()`(park-state 스키마에 결합된 헬퍼)를 끌어오는
대신 이 얕은 조회 하나만 인라인한다(구현-복잡도 스킬 rule 4/7 판단,
issue #2173 레코드 참고).

시도-이력은 `spawn_on_pr.py` 의 PARK_STATE_FILENAME 을 재사용/일반화하지
않고 별도 파일에 둔다 — park 상태는 "승인 대기중 재확인 빈도"를 위한
전혀 다른 상태 기계이고, 이 모듈의 "이미 한 번 시도했다"는 그와
합쳐두면 두 의미가 한 파일에 섞인다(구현-복잡도 스킬 rule 6).
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn  # noqa: E402
import ci as _ci  # noqa: E402
import closure_sweep  # noqa: E402
import state_paths  # noqa: E402

_BRANCH_SUBJECT_SKILL_RE = re.compile(r"(?:^|/)(issue-\d+)/([A-Za-z0-9-]+)$")

# issue #1360 계열 백스톱과 같은 상수값 — 틱당 자동 phase-2 스폰 상한.
SPAWN_CAP = 4

# {subject}/{role} -> {"pr_number": int|None} 시도-이력. 값이 있으면 이
# (subject, role) 은 이미 한 번 자동 스폰됐다 — 다시 시도하지 않는다.
# issue #2240: 오케스트레이터 틱간 기억이다 — state_paths 로 앵커링된다
# (`root`, 즉 대상 레포 기준이 아니다).
ATTEMPTED_STATE_FILENAME = "spawn_on_approve_attempted.json"


def _attempted_state_path(root: Path) -> Path:
    """issue #2240: orchestrator cross-tick memory, not target-repo state —
    anchored via state_paths, never `root`. `root` is accepted for
    call-site symmetry with the rest of this module's `root`-scoped
    helpers; it is not used here."""
    return state_paths.orchestrator_state_path(ATTEMPTED_STATE_FILENAME)


def load_attempted(root: Path) -> dict[str, dict]:
    """시도-이력을 읽는다. 파일이 없거나(첫 틱) 깨졌으면 빈 사전 — 빈
    사전은 "아직 아무것도 자동 스폰한 적 없음"과 같은 뜻이라 이 함수
    하나만으로 fail-safe 하다."""
    p = _attempted_state_path(root)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def _save_attempted(root: Path, state: dict[str, dict]) -> None:
    p = _attempted_state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
    """`spawn_on_pr._issue_is_open` 과 같은 fail-closed 판정 — 상태를
    모르는 subject 를 자동 스폰하지 않는다."""
    if issue_states is None:
        return False
    return issue_states.get(issue) == "OPEN"


def _pr_number_for_branch(root: Path, branch: str,
                           pr_index: dict[str, dict] | None) -> int | None:
    if pr_index is not None:
        entry = pr_index.get(branch)
        if entry is not None and entry.get("state") in ("OPEN", "MERGED"):
            return entry.get("number")
        return None
    return spawn._pr_open_or_merged_for_branch(root, branch)


def _skill_session_active(root: Path, subject: str, skill: str) -> bool:
    """`subject/role` 로스터 엔트리가 살아있는 pid 로 남아있으면 True —
    이미 도는 세션 위에 또 스폰하지 않는다(`spawn_on_pr.py:
    _implementation_session_active` 와 같은 판정, role 을 일반화)."""
    entry = spawn._roster_load().get(f"{subject}/{skill}")
    if entry is None:
        return False
    pid = entry.get("pid")
    return spawn._alive(pid if isinstance(pid, int) else 0)


def _candidate_branches(root: Path) -> set[tuple[str, str]]:
    """로컬+원격 `issue-<n>/<role>` 브랜치를 (subject, role) 쌍으로
    나열한다 — 순수 로컬 git 조회, `gh` 비용 없음. `spawn.board(root)`
    로는 이 목적에 못 쓴다: board() 는 "적어도 하나의 role 기록이 이미
    landed 된" subject 만 돌려주는데(`board.py:board()`), 우리가 찾는
    대상은 정확히 그 반대 — 아직 어떤 role 기록도 없는(phase-1 뿐인)
    subject 다. `require_requirement_linkage` 가 단일 이슈에 쓰는 `git
    for-each-ref refs/heads/issue-{issue}/** ...` 조회의 전체-브랜치
    버전이다."""
    r = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname)",
         "refs/heads/issue-*/*", "refs/remotes/*/issue-*/*"],
        cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return set()
    out: set[tuple[str, str]] = set()
    for line in r.stdout.splitlines():
        m = _BRANCH_SUBJECT_SKILL_RE.search(line.strip())
        if m:
            out.add((m.group(1), m.group(2)))
    return out


def ready_for_phase2(root: Path, subjects: set[str] | None = None,
                      issue_states: dict[int, str] | None = None,
                      pr_index: dict[str, dict] | None = None
                      ) -> dict[str, list[str]]:
    """`{subject: [role, ...]}` — 이슈가 OPEN 이고, `role` 이 승인됐지만
    (`APPROVE issue-<n>/<role>`) board 에 아직 그 role 의 phase-2 기록이
    없고, 그 role 의 phase-1 PR 이 이미 열려 있으며(이어받을 브랜치가
    있다), 이 role 이 아직 자동 phase-2 스폰을 시도된 적 없고, 지금
    도는 세션이 없는 (subject, role) 쌍만 돌려준다.

    `subjects` 를 주면(예: delta 모드에서 이번 틱에 바뀐 이슈 번호로
    좁힌 `{"issue-123", ...}` 집합) 그 서브셋의 브랜치만 본다 — 안
    주면 로컬에 존재하는 모든 `issue-*/*` 브랜치를 본다.

    이슈 #2173 before-landing hunt: `pr_index` 를 안 주면(호출부가 이번
    틱에 이미 벌크 인덱스를 안 가져온 경우) 여기서 딱 한 번
    `closure_sweep._pr_index_all()` 로 가져온다 — `spawn_on_pr.py`의
    `missing_verification()` 과 같은 패턴. 이게 없으면
    `_pr_number_for_branch()` 가 후보 브랜치마다
    `spawn._pr_open_or_merged_for_branch()`(브랜치당 `gh pr list` 한
    번)로 폴백해, watchdog 의 틱당 호출 예산 회계에 안 잡히는
    O(브랜치 수) 실제 `gh` 호출을 낸다(실측: 브랜치 5개 -> gh 호출
    5회)."""
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)
    out: dict[str, list[str]] = {}
    b = spawn.board(root)
    attempted = load_attempted(root)
    candidates = _candidate_branches(root)
    if subjects is not None:
        candidates = {(s, r) for (s, r) in candidates if s in subjects}
    for subject, skill in sorted(candidates):
        parts = subject.split("-", 1)
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        issue = int(parts[1])
        if not _issue_is_open(issue, issue_states):
            continue
        if skill in b.get(subject, {}):
            continue  # phase-2 기록이 이미 있다 — 델리버리 끝
        key = f"{subject}/{skill}"
        if key in attempted:
            continue  # 이미 한 번 시도됐다 — auto-respawn/health 경로가 이어받는다
        approved = _ci._approved_skills_on_issue(root, issue)
        if skill not in approved:
            continue  # 아직 승인 안 됨 — phase-1 그대로
        branch = f"{subject}/{skill}"
        if _pr_number_for_branch(root, branch, pr_index) is None:
            continue  # phase-1 PR 이 아직 없다 — 이어받을 산출물이 없다
        if _skill_session_active(root, subject, skill):
            continue  # 이미 돌고 있다
        out.setdefault(subject, []).append(skill)
    return out


def spawn_phase2(root: Path, cwd: str, dry_run: bool = False,
                  subjects: set[str] | None = None,
                  issue_states: dict[int, str] | None = None,
                  spawn_cap: int = SPAWN_CAP,
                  pr_index: dict[str, dict] | None = None
                  ) -> list[tuple[str, str]]:
    """`ready_for_phase2()` 가 찾은 쌍 중 최대 `spawn_cap` 개를 등록+스폰
    한다. 초과분은 스폰하지 않고 몇 건이 미뤄졌는지 한 줄 찍는다(#1360
    의 no-silent-cap 관례). `dry_run=True` 면 등록/스폰 없이(캡 적용된)
    쌍만 돌려준다(테스트용, 실제 세션을 안 띄운다) — 이 경우 시도-이력도
    쓰지 않는다: 드라이런이 "시도했다"로 카운트되면 다음 실제 스윕이
    그 쌍을 영영 건너뛴다.

    이슈 #2173 before-landing hunt: `pr_index` 를 여기서도 한 번만
    확정해 `ready_for_phase2()` 와 아래 `attempted[branch]` 기록 루프가
    같은 인덱스를 공유하게 한다 — 안 그러면 이 함수의 로컬 `pr_index`
    가 여전히 `None` 인 채로 두 번째 폴백(스폰된 쌍마다 `gh pr list`
    한 번씩)을 낸다."""
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)
    pairs_all: list[tuple[str, str]] = []
    for subject, skills in ready_for_phase2(
            root, subjects=subjects, issue_states=issue_states,
            pr_index=pr_index).items():
        for skill in skills:
            pairs_all.append((subject, skill))

    pairs = pairs_all[:spawn_cap]
    deferred = len(pairs_all) - len(pairs)
    if deferred > 0:
        print(f"[spawn-on-approve] cap={spawn_cap} 초과로 {deferred}건 미룸 "
              f"(다음 틱에 처리)")
    if dry_run:
        return pairs

    attempted = load_attempted(root)
    for subject, skill in pairs:
        issue = int(subject.split("-", 1)[1])
        branch = f"{subject}/{skill}"
        task = (f"이슈 #{issue}: {skill} — APPROVE issue-{issue}/{skill} 코멘트가 "
                f"관측됐다. phase-2 로 계속한다: 기존 phase-1 PR({branch} 브랜치) "
                f"위에서 실제 작업과 기록을 커밋하라. (자동 스폰됨, "
                f"spawn_on_approve.py, issue #2173)")
        spawn.roster_register(
            f"issue-{issue}/{skill}",
            {"role": skill, "issue": issue, "expects_pr": True, "work": cwd},
        )
        # 이슈 #2574 disposition: single-phase(build-now). 이 스폰의
        # 전제 자체가 "APPROVE issue-<n>/<role> 코멘트가 이미 관측됐다"
        # 이므로(위 task 문구), phase-2 승인 조건은 이미 실제로
        # 충족됐다 — approval-gate.sh 는 CORE_BUILD_NOW 없이도 그 코멘트를
        # 직접 스캔해 통과시켰을 것이다. single_phase=True 를 명시하는
        # 것은 그 승인을 우회하는 게 아니라, 이 세션이 spawn.py 의
        # 시스템 프롬프트 주입(`_SINGLE_PHASE_CONTRACT_LINE`)을 통해 첫
        # 턴부터 "제안 라운드 없이 바로 phase-2 작업으로" 라는 것을
        # 알고 시작하게 한다 — task 문구가 이미 말하는 바와 정확히
        # 일치시키는 것.
        spawn._spawn_one(cwd, skill, task, unattended=True, issue=issue, bounded=True,
                         single_phase=True)
        attempted[branch] = {
            "pr_number": _pr_number_for_branch(root, branch, pr_index),
        }
    _save_attempted(root, attempted)
    return pairs
