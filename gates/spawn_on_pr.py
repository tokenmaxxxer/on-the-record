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
import state_paths  # noqa: E402

# issue #2609: NOT the merge-gating identity axis anymore --
# gates/merge_gate.py::required_verification_missing() now gates purely on
# a self-declared, counted `verifies_subject` field (Option 2,
# docs/issue-2593/reports/architecture-module-boundary-definition+
# architecture-decomposition-strategy-386ff408.md) -- no kind/name matching
# anywhere in the merge path. This tuple exists only so THIS automation's
# own auto-spawn tick (missing_verification/spawn_missing_for_pr below)
# knows which two of the retired ~44-entry role catalog's skills to invite when the
# subject board hasn't landed a qualifying record yet -- a role-selection
# choice, not an obligation check. Generalizing or removing named role
# selection here is issue #2610's separate surface (the role catalog / the
# role catalog's retirement) -- not absorbed into this issue.
AUTO_SPAWN_ROLES = ("execution-observation", "conformance-review")

# issue #2609: the actual obligation threshold -- how many independent
# qualifying records (`verifies_subject: true`, author != subject's own
# deliverable author) a subject needs before merge_gate.py allows its
# merge. A count, not a vocabulary: it says how many, never which ones.
REQUIRED_INDEPENDENT_VERIFICATIONS = 2


def verifying_record_count(subject_board: dict, subject_author: str | None = None) -> int:
    """issue #2609: count of records in `subject_board`
    (`board(root)[subject]`, `{filename stem: frontmatter}`) that
    self-declare `verifies_subject: true` (frontmatter -- the same
    self-declaration pattern already used for `author:`) and whose
    `author:` differs from `subject_author`. No `kind:` value, filename, or
    skill name participates -- replaces the old closed two-kind tuple that
    used to decide this for `merge_gate.py::required_verification_missing`.

    `subject_author` (the subject's own deliverable-record `author:`) reuses
    the existing self-verification guard `applicable_record_kinds()` already
    used (issue #2241 stage 5): a record authored by the deliverable's own
    author does not count toward the requirement. `subject_author=None`
    (e.g. local standalone call, no deliverable landed yet) skips the guard.
    Pure function, no I/O."""
    count = 0
    for _name, fm in subject_board.items():
        if fm.get("verifies_subject") != "true":
            continue
        if subject_author is not None and fm.get("author") == subject_author:
            continue
        count += 1
    return count

# 틱당 스폰 상한(issue #1360) — 자동 워치독 틱 하나가 한 번에 스폰하는
# (subject, role) 쌍의 개수를 제한하는 예산 백스톱. 초과분은 조용히
# 버리지 않고 몇 건이 미뤄졌는지 한 줄로 찍는다.
SPAWN_CAP = 4

# issue #1476: park state store that stops re-spawning every tick while a
# (subject, role) pair is waiting on human approval. Keys are
# "<subject>/<role>"; values carry `blocked` (bool), `pr_number` (int,
# informational only — see issue #2238 below), `parked` (bool), and
# `attempts` (int, issue #2238 item 2).
#
# issue #2238 (this file's should_park()/spawn_missing_for_pr() defect):
# the original design treated an unchanged `pr_number` as the re-arm
# signal ("no new commit on the branch"). That is unsound — a PR number
# changing is exactly as likely to mean "this very mechanism respawned
# the role and its session opened a fresh PR" as "a human pushed a new
# commit". A self-created PR is not evidence of human progress, so
# `pr_number` no longer participates in the park/re-arm decision at all
# (see should_park() below) — it is kept in the state dict purely for
# operator-visible debugging. The only re-arm signals now are real
# EXTERNAL ones: `blocked` is derived from
# `gates/ci.py:_approved_roles_on_issue()` (approver allowlist, exact
# `APPROVE issue-<n>/<role>` string match — a human posting an approval
# comment), and a merge to main is handled upstream of this state
# entirely — once a role's record lands, `missing_verification()` stops
# reporting that (subject, role) pair as missing, so it never reaches
# this park logic again regardless of park_state's contents.
#
# issue #2240: this is the orchestrator's cross-tick memory, not
# target-repo state — anchored via state_paths, never `root` (the target
# repo). See the item-3 investigation note in
# docs/issue-2238/reports/silent-failure-audit+diagnose-first-86a93666.md:
# this scope question was already fixed by #2240/PR #2247 before this
# issue was worked — `_park_state_path()` below already routes through
# `state_paths.orchestrator_state_path()`, not `root`.
PARK_STATE_FILENAME = "spawn_on_pr_parked.json"

# issue #2238 item 2: a second, independent backstop. Even with a correct
# park rule (item 1), N respawns of the same (subject, role) pair with no
# intervening merge must stop and say so loudly — not loop forever, and
# not silently no-op if some future bug defeats the park rule again. A
# small constant is enough; it is threaded through spawn_missing_for_pr()
# as an optional parameter so a caller can override it without editing
# this file.
MAX_RESPAWN_ATTEMPTS = 4

# issue #2165: subject 의 `<subject>/implementation` PR 이 MERGED 로
# 확인된 사실은 종결적이다 — 한 번 확인되면 이후 틱에서 다시 확인할
# 필요가 없다(오히려 `gh` 호출이 그 틱에 실패해 fail-open 으로 OPEN 을
# 돌려주면 재스폰 위험이 생긴다). `closure_sweep.py`의
# out-of-index-seen 캐시(issue #1643)와 같은 모양: 한 번 확인된 subject
# 집합을 남기고, 이후 틱은 `gh` 를 부르기 전에 이 집합부터 확인한다.
# issue #2240: 이건 오케스트레이터 틱간 기억이다 — repo-local 이 아니라
# state_paths 로 앵커링된다(대상 레포는 절대 아니다).
MERGED_SEEN_STATE_FILENAME = "spawn_on_pr_merged_seen.json"


def applicable_record_kinds(subject_board: dict, kinds: tuple[str, ...] = AUTO_SPAWN_ROLES,
                             subject_author: str | None = None) -> list[str]:
    """`subject_board`(`board(root)[subject]`, `{filename stem: frontmatter}`)
    에서 아직 record-kind 가 없는 `kinds` 서브셋을 `kinds` 가 나열한 순서
    그대로 돌려준다(issue #2241 stage 5 — role 이름이 아니라 각 항목의
    `kind:` frontmatter 값으로 매칭한다).

    한 항목의 `kind:` 값이 `kinds` 안에 있으면 그걸로 매칭한다. 그렇지
    않으면(필드 자체가 없거나 — stage 1 이전 레코드, additive-only 라
    소급 적용 안 됨 — 또는 필드는 있지만 stage 1 이전부터 산발적으로 쓰인
    비정형 값, 예: `kind: record`, `docs/specs/record-kind-vocabulary.md`
    의 닫힌 어휘 밖) 파일명 stem 이 `kinds` 안에 있으면 그것으로
    대신 매칭한다(legacy fallback, `board-gate.sh` R5 의 `author:`-부재
    fallback 과 같은 모양) — `kind:` 매칭과 파일명 매칭은 OR 관계라,
    둘 중 하나만 맞아도 충족으로 친다. `kind:` 값이 무엇이든 파일명이
    `kinds` 안에 있으면 항상 매칭되므로, stage 1 이전/이후 어느 subject 도
    오늘과 같은(또는 더 넓은, kind: 필드만 새로 붙은 새 파일명도 잡는)
    목록을 돌려준다.

    `subject_author` 를 주면(subject 의 `implementation` 레코드
    `author:` 값) 자기 자신을 검증하는 셀프-verification 을 막는다 —
    항목의 `author:` 가 `subject_author` 와 같으면 그 kind 는 "충족됨"에
    안 들어간다(issue #2241 stage 5 Constraints: record-kind 만으로는
    부족하고 author-identity 도 달라야 한다). `subject_author` 가 없으면
    (예: 로컬 단독 호출) 이 검사를 건너뛴다. 순수 함수, I/O 없음.

    issue #2609: 더 이상 머지-게이팅 의무(merge_gate.py::
    required_verification_missing)를 뒷받침하지 않는다 — 그건 이제
    `verifying_record_count()`(자기-선언 `verifies_subject` 필드 카운트,
    kind 무관)로 완전히 분리됐다. 이 함수는 `missing_verification()`/
    `spawn_missing_for_pr()`의 auto-spawn 틱 전용으로 남는다 — kinds 인자
    기본값(`AUTO_SPAWN_ROLES`)이 어떤 두 스킬을 자동 초대할지 결정할 뿐,
    머지를 막을지 여부와는 무관하다."""
    satisfied = set()
    for name, fm in subject_board.items():
        kind_field = fm.get("kind")
        matched = kind_field if kind_field in kinds else (name if name in kinds else None)
        if matched is None:
            continue
        if subject_author is not None and fm.get("author") == subject_author:
            continue
        satisfied.add(matched)
    return [k for k in kinds if k not in satisfied]


def subject_deliverable_record(subject_board: dict) -> tuple[str | None, dict]:
    """Resolve the subject's own (non-observer) deliverable record from
    `subject_board` (`board(root)[subject]`) — issue #2575: the literal
    `subject_board.get("implementation", {})` lookup silently returns an
    empty dict once the deliverable's filename is a slug (#2555), so it
    can never distinguish "no deliverable landed yet" from "deliverable
    landed under a different name". This resolves it the same way
    `applicable_record_kinds()` already resolves the two PR-triggered
    kinds (issue #2241 stage 5): the record whose `kind:` frontmatter is
    `implementation`, or (legacy fallback — a record written before
    #2555 never carried a `kind:` line at all) whose filename stem is
    literally `implementation`. Returns `(slug, frontmatter)`, or
    `(None, {})` when the subject has no such record in `subject_board`
    yet — `None` is the loud form of "not found" (a caller can check
    `slug is None` directly, unlike a `.get(x, {})` empty dict, which
    reads identically whether the key is absent or genuinely empty)."""
    for name, fm in subject_board.items():
        kind_field = fm.get("kind")
        if kind_field == "implementation" or (kind_field is None and name == "implementation"):
            return name, fm
    return None, {}


def subject_deliverable_branch(subject: str, pr_index: dict[str, dict] | None) -> str | None:
    """Resolve the subject's own (non pr-observer) branch from `pr_index`
    (`closure_sweep._pr_index_all()`'s branch -> `{number, state, ...}`
    map) — issue #2575's lease/branch axis replacement for the literal
    `f"{subject}/implementation"`: the `{subject}/<slug>` branch among
    this subject's indexed PRs whose slug is not one of the two fixed
    auto-spawned observer roles (`AUTO_SPAWN_ROLES`, issue #2609 --
    a role-selection list, not the merge-gating axis; see that constant's
    own comment). Used where `subject_deliverable_record`
    cannot help — the deliverable PR may still be open and unmerged, so
    `board()` (landed records only) has nothing to resolve against yet,
    but the PR index already does.

    `None` when `pr_index` itself is unavailable (gh degraded — the
    caller has no branch name to fall back to either, same as today),
    or when zero or more than one candidate branch matches: zero is the
    ordinary "no deliverable PR yet" case every caller already treats as
    "nothing to do this tick"; more than one is a genuine ambiguity this
    function refuses to guess through rather than silently picking one."""
    if pr_index is None:
        return None
    prefix = f"{subject}/"
    candidates = [b for b in pr_index
                  if b.startswith(prefix) and b[len(prefix):] not in AUTO_SPAWN_ROLES]
    return candidates[0] if len(candidates) == 1 else None


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
    """`subject` 의 deliverable(옵저버가 아닌) 세션이 로스터에 살아있는
    pid 로 남아있으면 True(issue #1697 두 번째 재현, issue-1696) — 활성
    fix 세션 중에 옵저버를 스폰하면 옵저버 브랜치가 fix 커밋 이전 main
    에서 잘려, 나중에 fix 가 머지되면 옵저버 record PR 이 719줄급
    REVERT 로 보이는 stale-base 사고가 난다(#1664 계열).

    issue #2575: `f"{subject}/implementation"` 이라는 고정 로스터 키는
    슬러그 신원(#2555) 아래서는 어느 세션의 키와도 안 맞는다 — 이
    subject 소속(`f"{subject}/"` 접두어) 로스터 엔트리 중, 고정된 두
    자동-스폰 관찰자 role(`AUTO_SPAWN_ROLES`, issue #2609 — 머지-게이팅
    축이 아니라 role-선택 목록)이 아닌 것을 찾는다: 이 두 관찰자는 여전히
    리터럴 role 이름으로 스폰되므로(`spawn_missing_for_pr` 참고) 배제로
    걸러도 안전하고, deliverable 세션 하나가 subject 당 하나라는
    불변식(#1697이 막는 stale-base 사고의 전제)을 그대로 쓴다 — subject 를
    slug 로 매핑하는 새 표를 만들지 않는다. 로스터에 그런 항목이 없거나
    pid 가 이미 죽었으면 False — 오래된/고아 로스터 항목으로 영원히
    스폰을 막지 않는다(`spawn._alive()`가 실제 프로세스 생존을 본다)."""
    prefix = f"{subject}/"
    for key, entry in spawn._roster_load().items():
        if not key.startswith(prefix):
            continue
        if key[len(prefix):] in AUTO_SPAWN_ROLES:
            continue
        pid = entry.get("pid")
        if spawn._alive(pid if isinstance(pid, int) else 0):
            return True
    return False


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
    unmappable_branch_already_reported = 0
    for subject, subject_board in b.items():
        _slug, subject_fm = subject_deliverable_record(subject_board)
        subject_author = subject_fm.get("author")
        missing = applicable_record_kinds(subject_board, subject_author=subject_author)
        if not missing:
            continue
        if merged_seen is None:
            merged_seen = load_merged_seen(root)
        if subject in merged_seen:
            # issue #2165: 이미 이전 틱에서 MERGED 로 확인됐다 — merge
            # 는 종결적 사실이라 이후 틱의 (혹은 fail-open 하는) 재확인을
            # 기다리지 않고 바로 건너뛴다.
            continue
        # issue #2575: `branch`는 subject_board(랜딩된 기록)가 아니라
        # pr_index(살아있는 PR)에서 구한다 — deliverable PR 이 아직 open
        # 이면 subject_board 에 그 기록이 없는 게 정상이라(위
        # subject_deliverable_record 가 (None, {}) 를 돌려줄 수 있다),
        # 그 경우에도 branch/PR 조회는 여전히 가능해야 한다.
        branch = subject_deliverable_branch(subject, pr_index)
        if branch is None:
            # 이슈 #2196 category 3: 브랜치가 삭제된 오래된 subject 는 이
            # 조건이 영구적이라 매 틱 재출력하면 wall of noise 가 된다 —
            # board-sweep 의 _watchdog_note_unmappable_pr 과 같은 one-shot
            # 마커: 처음 보는 subject 만 개별 줄로 찍고, 이후는 개수로 접는다.
            if spawn._watchdog_note_unmappable_subject_branch(root, subject):
                print(f"[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 "
                      f"찾지 못했다 — 이번 틱은 건너뜀 (missing={missing})")
            else:
                unmappable_branch_already_reported += 1
            continue
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
        out[subject] = missing
    if unmappable_branch_already_reported:
        print(f"[spawn-on-pr] {unmappable_branch_already_reported}건 이전에 보고된 "
              "매핑-불가 subject — 계속 무시 (반복 안 찍음)")
    return out


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


def should_park(prior: dict | None, blocked: bool) -> bool:
    """Park decision: pure function. Park iff this (subject, role) pair
    was already identified as blocked on a prior tick (`prior` exists and
    `prior["blocked"]` is True) AND it is still blocked this tick.
    `prior is None` (first-ever candidate) is always False — a role that
    has never been tried is never mistaken for a retry.

    issue #2238: `pr_number` deliberately does NOT appear in this
    signature or decision anymore. The previous version parked only when
    `prior.get("pr_number") == pr_number`, treating a PR-number diff as
    "a human pushed a new commit, so retry." That is indistinguishable
    from "this mechanism's own respawn opened a fresh PR for the same
    still-blocked role" — the exact failure mode that let `spawn-on-pr`
    respawn issue-2208's observers 9x each. The only thing that may
    legitimately clear `blocked` now is a real external signal
    (`is_approval_blocked()`, an approver-allowlist comment) — the caller
    computes `blocked` from that signal every time this pair is
    rechecked, never from a bare identity comparison on `pr_number`."""
    if not blocked or prior is None:
        return False
    return prior.get("blocked") is True


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


def clear_ceiling(root: Path, subject: str | None = None, role: str | None = None
                   ) -> list[str]:
    """issue #2607: CEILING HIT 가 parked 시킨 쌍의 ceiling 상태
    (`ceiling_hit` 플래그 + `attempts` 카운터)만 지운다 — `blocked`/
    `parked` 는 손대지 않는다, 그래야 다음 틱에도 여전히 진짜 승인 신호
    (`is_approval_blocked()`)를 통해서만 재개된다. 운영자 결정: 카운터는
    자동 신호(승인, 경과 시간, PR 번호 변화)로 절대 되돌지 않는다 —
    이건 그 결정을 지키면서 사람이 명시적으로 실행하는 유일한 해제
    경로다.

    `subject`/`role` 을 둘 다 주면 그 쌍만 대상으로 한다(운영자가 이름을
    지정한 경우). 안 주면 현재 `ceiling_hit: True` 로 보고된 모든 쌍을
    대상으로 한다("currently reported" — CEILING HIT 줄이 방금 찍은
    바로 그 목록). 어느 경우든 그 쌍이 실제로 `ceiling_hit` 상태가
    아니면 건드리지 않는다 — 그 밖의 park 항목(승인 대기 중인 쌍 등)은
    범위 밖이다. 지워진 키 목록을 돌려준다(빈 목록 = 지울 게 없었음)."""
    state = load_park_state(root)
    if subject is not None and role is not None:
        keys = [f"{subject}/{role}"]
    else:
        keys = [key for key, entry in state.items() if entry.get("ceiling_hit")]
    cleared = []
    for key in keys:
        entry = state.get(key)
        if not entry or not entry.get("ceiling_hit"):
            continue
        state[key] = {**entry, "ceiling_hit": False, "attempts": 0}
        cleared.append(key)
    if cleared:
        _save_park_state(root, state)
    return cleared


def spawn_missing_for_pr(root: Path, cwd: str, dry_run: bool = False,
                          issue_states: dict[int, str] | None = None,
                          spawn_cap: int = SPAWN_CAP,
                          backoff_state: dict | None = None,
                          pr_index: dict | None = None,
                          max_respawn_attempts: int = MAX_RESPAWN_ATTEMPTS
                          ) -> list[tuple[str, str]]:
    """`missing_verification()` 이 찾은 `(subject, role)` 쌍 중 최대
    `spawn_cap` 개를 등록+스폰한다. 초과분은 스폰하지 않고, 몇 건이
    미뤄졌는지 한 줄 찍는다(issue #1360 — no silent cap). `dry_run=True`
    면 등록/스폰 없이 (캡 적용된) 쌍만 돌려준다(테스트용, 실제 세션을
    띄우지 않는다).

    issue #1476/#2238: for every candidate pair, if a prior park record
    (`load_park_state`) says it was already `blocked`, this recomputes
    `blocked` via `is_approval_blocked()` (a real external signal — an
    approver-allowlist comment) and parks again via `should_park()` if it
    is still blocked. issue #2238: unlike the original #1476 version,
    this recheck no longer requires the tick's `pr_number` to match the
    prior one — a PR number changing is not itself an external signal
    (see should_park()'s docstring); it is exactly what a self-created
    respawn would also produce, so gating the recheck on it defeated the
    park guard entirely. `is_approval_blocked()` (a `gh` call) still only
    fires for pairs that were already `blocked` on a prior tick — a
    candidate seen for the first time never touches `gh` here and just
    spawns (unchanged from before).

    issue #2238 item 2: independently of the park/re-arm decision above,
    every candidate about to be spawned is also checked against
    `max_respawn_attempts` — a hard ceiling on how many times the same
    (subject, role) pair may be spawned with no intervening merge, even
    if some future bug defeats the park rule again. Hitting the ceiling
    does not silently drop the pair: it is parked with `ceiling_hit:
    True` and reported loudly (`print` + `spawn.ledger_write`), the same
    silent-failure concern that motivated auditing `should_park()` in the
    first place — a guard that can fail without saying so is as bad as no
    guard.

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
        # issue #2575: subject 소속 PR 은 이제 slug 로 이름 붙으므로,
        # 브랜치 이름을 pr_index 에서 유도해야 한다(subject_deliverable_
        # branch — lease/branch 축, AUTO_SPAWN_ROLES 제외, issue #2609).
        branch = subject_deliverable_branch(subject, pr_index)
        pr_number = _pr_number_for_branch(root, branch, pr_index) if branch else None
        for role in roles:
            all_pairs.append((subject, role, pr_number))

    park_state = load_park_state(root)
    to_spawn: list[tuple[str, str, int | None, int]] = []
    parked_now: list[tuple[str, str]] = []
    ceiling_hit: list[tuple[str, str, int]] = []
    for subject, role, pr_number in all_pairs:
        issue = int(subject.split("-", 1)[1])
        key = f"{subject}/{role}"
        prior = park_state.get(key)
        if prior is not None and prior.get("blocked"):
            if not closure_sweep.recheck_backoff(backoff_state, key, False):
                # Not this tick's turn to recheck — stay parked, no gh call.
                parked_now.append((subject, role))
                park_state[key] = {**prior, "pr_number": pr_number, "parked": True}
                continue
            blocked = is_approval_blocked(root, issue, role)
            if not blocked:
                closure_sweep.recheck_backoff(backoff_state, key, True)
            if should_park(prior, blocked):
                parked_now.append((subject, role))
                park_state[key] = {**prior, "blocked": True, "pr_number": pr_number,
                                    "parked": True}
                continue
            # blocked cleared by a real external signal (an approval
            # comment) — fall through to spawn, still subject to the
            # respawn ceiling check below (issue #2238 item 2).
        attempts = (prior or {}).get("attempts", 0)
        if attempts >= max_respawn_attempts:
            ceiling_hit.append((subject, role, attempts))
            park_state[key] = {**(prior or {}), "blocked": True, "pr_number": pr_number,
                                "parked": True, "ceiling_hit": True, "attempts": attempts}
            continue
        to_spawn.append((subject, role, pr_number, issue))

    if owns_backoff_state:
        closure_sweep.save_backoff_state(root, backoff_state)

    if parked_now:
        print(f"[spawn-on-pr] park={len(parked_now)}건 waiting-for-human "
              f"(승인-대기 상태 변화 없음): {parked_now}")

    if ceiling_hit:
        for subject, role, attempts in ceiling_hit:
            spawn.ledger_write({
                "event": "spawn_on_pr_respawn_ceiling_hit",
                "subject": subject, "role": role, "attempts": attempts,
                "max_respawn_attempts": max_respawn_attempts,
            })
        print(f"[spawn-on-pr] CEILING HIT: {len(ceiling_hit)}건이 최대 재시도 "
              f"횟수({max_respawn_attempts})에 도달해 자동 스폰을 멈춘다 — "
              f"사람 개입 필요 (park_state 에 ceiling_hit=True 로 기록됨).")
        print(f"[spawn-on-pr]   해제: `python3 gates/spawn_on_pr.py clear-ceiling` "
              f"(특정 쌍만 지우려면 `--subject <subject> --role <role>` 추가)")
        print(f"[spawn-on-pr]   대상: {[(s, r, a) for s, r, a in ceiling_hit]}")

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
        # 이슈 #2574 disposition: single-phase(build-now). 이 스폰은 이미
        # 랜딩된 PR 커밋에 대한 검증 기록을 쓸 뿐 새 code_under_review 를
        # 여는 게 아니다 — proposal-first 두-단계 계약(v3 s19)이 지키려는
        # "제안 없이 코드부터 짜지 마라"는 여기 해당하지 않는다. 명시하지
        # 않으면 사람 Approve 를 기다리며 조용히 멈춘다(이슈 #2574 의 실측
        # 원인, issue-648/conformance-review 가 PR #650 에서 이 자리에
        # 걸려 있었다).
        spawn._spawn_one(cwd, role, task, unattended=True, issue=issue, bounded=True,
                         single_phase=True)
        key = f"{subject}/{role}"
        prior_attempts = park_state.get(key, {}).get("attempts", 0)
        park_state[key] = {"blocked": True, "pr_number": pr_number, "parked": False,
                            "attempts": prior_attempts + 1}
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
        _slug, subject_fm = subject_deliverable_record(subject_board)
        subject_author = subject_fm.get("author")
        missing = applicable_record_kinds(subject_board, subject_author=subject_author)
        if not missing:
            continue
        branch = subject_deliverable_branch(subject, pr_index)
        pr_number = _pr_number_for_branch(root, branch, pr_index) if branch else None
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
        # 이슈 #2574 disposition: single-phase(build-now) — 위
        # spawn_missing_for_pr() 자동 스폰과 같은 이유(닫힌 이슈에 랜딩된
        # 커밋에 대한 검증 기록 백필, 새 code_under_review 없음).
        spawn._spawn_one(cwd, role, task, unattended=True, issue=issue, bounded=True,
                         single_phase=True)
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
    clear_ceiling_p = sub.add_parser(
        "clear-ceiling",
        help="CEILING HIT 로 parked 된 쌍의 ceiling 상태만 지운다(issue #2607). "
             "생략하면 현재 ceiling_hit=True 로 보고된 모든 쌍이 대상.")
    clear_ceiling_p.add_argument("--subject", help="예: issue-1163 (--role 과 함께 지정)")
    clear_ceiling_p.add_argument("--role", help="예: conformance-review (--subject 와 함께 지정)")
    args = parser.parse_args(argv)
    if args.command == "clear-ceiling" and bool(args.subject) != bool(args.role):
        parser.error("clear-ceiling: --subject 와 --role 은 함께 주거나 둘 다 생략한다.")
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
    if args.command == "clear-ceiling":
        cleared = clear_ceiling(ROOT, args.subject, args.role)
        if cleared:
            print(f"[clear-ceiling] {len(cleared)}건 해제됨: {cleared}")
        elif args.subject and args.role:
            # issue #2607 silent-failure-audit: distinguish "that pair isn't
            # ceiling_hit (or doesn't exist)" from the global empty case
            # below -- both reporting the same generic line would leave an
            # operator who mistyped --subject/--role unable to tell a typo
            # from an already-clear pair.
            print(f"[clear-ceiling] {args.subject}/{args.role}: "
                  f"ceiling_hit 상태 아님 (지울 것 없음)")
        else:
            print("[clear-ceiling] 지울 ceiling 상태 없음")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
