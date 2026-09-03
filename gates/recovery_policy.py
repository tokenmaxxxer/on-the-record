"""Bounded-retry recovery policy for a dead worker session (issue #1670).

Pure `classify()` decides LOST_NOTHING / LOST_WORK_NEEDS_HANDOFF / ESCALATE from
already-observed failure signals — it consumes the same kind of death signal
spawn.py's `reconcile()` already emits (`pr-expected-missing` -> respawn), it does
not re-derive git/gh state itself. `classify_from_state()` is a thin wrapper that
persists a per-(issue, role) respawn counter and last-failure-signature on disk so
callers don't have to thread that state through themselves.
"""

from __future__ import annotations

import json
from pathlib import Path

# Issue #3267: these say what the death LOOKS LIKE, not what to do about
# it. Automatic respawn was removed in #3264, and a name that promises an
# action the code no longer takes is the same misleading-report defect this
# repository keeps finding -- except the misleading report is the
# identifier. A reader during the 2026-09-03 incident concluded from these
# names that RESPAWN_IDENTICAL was "unwired, so not a runaway path"; it is
# wired (spawn.py, watchdog.py), and the safety argument happened to be
# right for an unrelated reason.
LOST_NOTHING = "LOST-NOTHING"
LOST_WORK_NEEDS_HANDOFF = "LOST-WORK-NEEDS-HANDOFF"

# Old names kept as aliases so any importer still resolves (the issue's
# must-not). They are the same objects, not a second vocabulary.
RESPAWN_IDENTICAL = LOST_NOTHING
RESPAWN_WITH_HANDOFF = LOST_WORK_NEEDS_HANDOFF
ESCALATE = "ESCALATE"

DEFAULT_CAP = 2
DEFAULT_STATE_DIR = Path(".on-the-record/recovery-state")


def classify(failure_signals: dict) -> str:
    """순수 함수: 이미 관측된 실패 신호만 보고 판단한다 — git/gh 를 새로 읽지
    않는다 (이슈 #1670 acceptance: "Pure function on fixtures, no network").

    `failure_signals`:
      has_commit: bool
      has_pr: bool
      respawn_count: int — 이 (issue, role) 에 대해 이미 재기동한 횟수
      cap: int — 재기동 상한 (기본 2)
      failure_signature: str|None — 이번 죽음의 실패 서명
      last_failure_signature: str|None — 직전 죽음의 실패 서명

    반환: LOST_NOTHING | LOST_WORK_NEEDS_HANDOFF | ESCALATE.

    규칙 순서(이슈 acceptance 그대로):
    1. respawn_count >= cap, 또는 같은 실패 서명 반복 -> ESCALATE — 같은 벽에
       또 부딪히는 blind respawn 을 막는다(토큰 낭비 방지).
    2. 커밋은 있는데 PR 이 없음(has-commit-no-PR) -> LOST_WORK_NEEDS_HANDOFF —
       이슈 #1660 케이스: 작업은 했는데 push/PR 을 못 낸 채 죽음.
    3. 커밋 전 죽음(pre-first-commit) -> LOST_NOTHING — 잃을 작업이 없으니
       같은 브리프로 그대로 다시 시작.
    """
    cap = failure_signals.get("cap", DEFAULT_CAP)
    respawn_count = failure_signals.get("respawn_count", 0)
    signature = failure_signals.get("failure_signature")
    last_signature = failure_signals.get("last_failure_signature")

    same_signature_repeat = (
        signature is not None
        and last_signature is not None
        and signature == last_signature
    )

    if respawn_count >= cap or same_signature_repeat:
        return ESCALATE

    if failure_signals.get("has_commit"):
        return LOST_WORK_NEEDS_HANDOFF

    return LOST_NOTHING


def _state_path(state_dir: Path, issue, skill: str) -> Path:
    return Path(state_dir) / f"{issue}-{skill}.json"


def _load_state(state_dir: Path, issue, skill: str) -> dict:
    path = _state_path(state_dir, issue, skill)
    if not path.exists():
        return {"respawn_count": 0, "last_failure_signature": None}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(state_dir: Path, issue, skill: str, state: dict) -> None:
    path = _state_path(state_dir, issue, skill)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def classify_from_state(
    issue,
    skill: str,
    has_commit: bool,
    has_pr: bool,
    failure_signature: str | None,
    cap: int = DEFAULT_CAP,
    state_dir: Path = DEFAULT_STATE_DIR,
    death_id=None,
) -> str:
    """`classify()` 래퍼: 이 세션 자신의 (issue, role) 재기동 카운터/직전
    실패 서명을 디스크에서 읽고, 판단 후 갱신한다. 판단 자체는 여전히
    `classify()` 가 순수하게 한다 — 상태 I/O 는 여기 래퍼에만 있다.

    `death_id`(이슈 #1678 review D1): 호출자가 매 watchdog tick 마다
    reconcile() 를 다시 태우기 때문에, 같은 죽음을 여러 번 관측해도
    `death_id`(예: 로스터 엔트리의 세션 시작 ts) 가 바뀌지 않는 한
    `respawn_count` 를 다시 올리지 않는다 — 그래야 한 번의 죽음이 몇 분
    안에 cap 을 태우는 걸 막는다. `death_id=None`(기본값)이면 기존처럼
    호출마다 카운트한다 — death 신원을 모르는 호출부와의 하위호환.

    같은 death_id 로 다시 불리면(같은 죽음의 다음 tick) 상태를 전혀
    건드리지 않고 그 죽음에 대해 이미 낸 판정을 그대로 돌려준다 —
    재계산하면 `last_failure_signature` 가 자기 자신(방금 이 죽음이 남긴
    서명)과 같아져 same-signature-repeat 규칙이 오발화한다."""
    state = _load_state(state_dir, issue, skill)
    is_new_death = death_id is None or state.get("current_death_id") != death_id
    if not is_new_death and "current_verdict" in state:
        return state["current_verdict"]

    verdict = classify(
        {
            "has_commit": has_commit,
            "has_pr": has_pr,
            "respawn_count": state["respawn_count"],
            "cap": cap,
            "failure_signature": failure_signature,
            "last_failure_signature": state["last_failure_signature"],
        }
    )
    if verdict != ESCALATE:
        state["respawn_count"] += 1
    state["last_failure_signature"] = failure_signature
    state["current_death_id"] = death_id
    state["current_verdict"] = verdict
    _save_state(state_dir, issue, skill, state)
    return verdict


def reset_state(issue, skill: str, state_dir: Path = DEFAULT_STATE_DIR) -> None:
    """이슈 #1678 review D2: (issue, role) 이 건강한 상태(PR 존재/세션
    정상 종료)에 도달하면 재기동 카운터/직전 실패 서명을 지운다 — 일시적
    flake 두 번이 이후의 진짜 죽음까지 영구히 ESCALATE 로 몰아가지
    않도록."""
    path = _state_path(state_dir, issue, skill)
    path.unlink(missing_ok=True)
