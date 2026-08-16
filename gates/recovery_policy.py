"""Bounded-retry recovery policy for a dead worker session (issue #1670).

Pure `classify()` decides RESPAWN_IDENTICAL / RESPAWN_WITH_HANDOFF / ESCALATE from
already-observed failure signals — it consumes the same kind of death signal
spawn.py's `reconcile()` already emits (`pr-expected-missing` -> respawn), it does
not re-derive git/gh state itself. `classify_from_state()` is a thin wrapper that
persists a per-(issue, role) respawn counter and last-failure-signature on disk so
callers don't have to thread that state through themselves.
"""

from __future__ import annotations

import json
from pathlib import Path

RESPAWN_IDENTICAL = "RESPAWN_IDENTICAL"
RESPAWN_WITH_HANDOFF = "RESPAWN_WITH_HANDOFF"
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

    반환: RESPAWN_IDENTICAL | RESPAWN_WITH_HANDOFF | ESCALATE.

    규칙 순서(이슈 acceptance 그대로):
    1. respawn_count >= cap, 또는 같은 실패 서명 반복 -> ESCALATE — 같은 벽에
       또 부딪히는 blind respawn 을 막는다(토큰 낭비 방지).
    2. 커밋은 있는데 PR 이 없음(has-commit-no-PR) -> RESPAWN_WITH_HANDOFF —
       이슈 #1660 케이스: 작업은 했는데 push/PR 을 못 낸 채 죽음.
    3. 커밋 전 죽음(pre-first-commit) -> RESPAWN_IDENTICAL — 잃을 작업이 없으니
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
        return RESPAWN_WITH_HANDOFF

    return RESPAWN_IDENTICAL


def _state_path(state_dir: Path, issue, role: str) -> Path:
    return Path(state_dir) / f"{issue}-{role}.json"


def _load_state(state_dir: Path, issue, role: str) -> dict:
    path = _state_path(state_dir, issue, role)
    if not path.exists():
        return {"respawn_count": 0, "last_failure_signature": None}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(state_dir: Path, issue, role: str, state: dict) -> None:
    path = _state_path(state_dir, issue, role)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def classify_from_state(
    issue,
    role: str,
    has_commit: bool,
    has_pr: bool,
    failure_signature: str | None,
    cap: int = DEFAULT_CAP,
    state_dir: Path = DEFAULT_STATE_DIR,
) -> str:
    """`classify()` 래퍼: 이 세션 자신의 (issue, role) 재기동 카운터/직전
    실패 서명을 디스크에서 읽고, 판단 후 갱신한다. 판단 자체는 여전히
    `classify()` 가 순수하게 한다 — 상태 I/O 는 여기 래퍼에만 있다."""
    state = _load_state(state_dir, issue, role)
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
    _save_state(state_dir, issue, role, state)
    return verdict
