"""Watchdog / health / board-sweep cluster, extracted from spawn.py
(issue #2105, extraction 4/N).

Pure move — no behavior change. spawn.py imports this module and re-exports
every moved name, so external callers and tests keep addressing them as
`spawn.<name>`.

Patching-compat mechanism (copied from relay.py/roster.py/plumbing.py,
extractions 1-3): every cross-function reference here resolves at call time
through `_sp` — the spawn module object, injected by spawn.py right after it
imports this module (guarded so only the canonical spawn/__main__ module
binds it), so `mock.patch.object(spawn, "<name>")` patches stay visible to
the moved code. Names that still live in spawn.py and are reached through
`_sp` include `ROOT`, `MARKER`, `BOARD`, `board`, `reconcile`, `_alive`,
`ledger_check_and_stamp`, `ledger_write`, `_repo_slug`, `_repo_identity`,
`_workspace_index_load`, `_workspace_base`, `_events_path`, `_append_event`,
`session_end_verdict`, `_count_structural_denials`, the roster/lease
functions (`_roster_load`, `_roster_own`, `lease_renew`,
`lease_reconcile_sweep`, `roster_register`, `_watcher_looks_real`), and the
respawn/comment helpers — each a seam for a later extraction.

Module-level constants whose values bind at import time (default-argument
values and derived paths) moved here WITH their users: `POLL_STATE`,
`POLL_INTERVAL_SEC`, `WATCHDOG_STATE`, `WATCHDOG_*_MIN`/thresholds,
`DEADLOCK_MIN_REPEATS`, `WATCHDOG_LOCK_PATH`,
`WATCHDOG_FRESHNESS_STATE_PATH`, `STANDING_RED_STATE`,
`STANDING_RED_CADENCE_MIN` — spawn.py re-exports them by assignment.
`ROOT` and `STATE_ROOT` are recomputed here with the exact expressions
spawn.py uses (same file directory, same env var, evaluated in the same
import pass), because they feed import-time defaults; run-time references
still go through `_sp` so patches on spawn attributes are seen.
`watchdog_canonical_guard`'s default `module_path=Path(__file__)` now names
watchdog.py instead of spawn.py — both live in the same checkout directory,
so the canonical-vs-workspace verdict is identical.
"""
from __future__ import annotations
import contextlib
import fcntl
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

# Import-time anchors — same expressions as spawn.py (same directory, same
# env), needed here because they feed default-argument values below.
ROOT = Path(__file__).resolve().parent
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")


POLL_STATE = ROOT / "runs" / "poll_state.json"
POLL_INTERVAL_SEC = 60  # 이슈 #782 스코프-확장(operator, 2026-08-11): 15분은 stall/deadlock 포착이 너무 늦다 — 1분


def poll_due(now: float | None = None, poll_state: Path = POLL_STATE,
             interval: float = POLL_INTERVAL_SEC) -> bool:
    """`spawn.py poll-due` (이슈 #782 req #7): `runs/poll_state.json` 의
    마지막 폴 시각을 원자적으로 확인+갱신한다. True 를 돌려주면 그 호출이
    바로 '지금 폴링 틱을 돌려도 된다'는 허가이자 갱신 — `directive.sh`
    가 매 턴 `UserPromptSubmit` 훅에서 부르므로, 같은 1분 창 안의 다음
    호출들은 False 를 받아 백그라운드 `watchdog` 를 또 띄우지 않는다."""
    now = time.time() if now is None else now
    lock_path = poll_state.with_name(poll_state.name + ".lock")
    lock_path.parent.mkdir(exist_ok=True)
    with open(lock_path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            try:
                st = json.loads(poll_state.read_text())
            except (OSError, ValueError):
                st = {}
            last = st.get("last_poll")
            due = last is None or (now - last) >= interval
            if due:
                st["last_poll"] = now
                poll_state.parent.mkdir(exist_ok=True)
                poll_state.write_text(json.dumps(st, ensure_ascii=False))
            return due
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


WATCHDOG_STATE = ROOT / "runs" / "watchdog_state.json"
WATCHDOG_SILENCE_MIN = 90     # 이슈 #90 proposal, signal 1
WATCHDOG_NO_COMMIT_MIN = 71   # 이슈 #90 proposal, signal 4 (0.5 * p90 ≈ 142.6)
WATCHDOG_DENIAL_THRESHOLD = 3 # 이슈 #90 proposal, signal 3
WATCHDOG_HEARTBEAT_ONLY_MIN = 18  # 이슈 #1966, signal 7: 하트비트만-성장 관측 창(분)
_DELEGATION_RE = re.compile(
    r"run_in_background|백그라운드|delegate|background worker", re.IGNORECASE)


def _watchdog_state_load() -> dict:
    try:
        return json.loads(_sp.WATCHDOG_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _watchdog_state_save(d: dict) -> None:
    _sp.WATCHDOG_STATE.parent.mkdir(exist_ok=True)
    _sp.WATCHDOG_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))



def _classify_log_lines_heartbeat_only(text: str, now: float,
                                        window_min: float = WATCHDOG_HEARTBEAT_ONLY_MIN
                                        ) -> str:
    """이슈 #1966: `text`(로그 스캔 구간)를 줄 단위 JSONL 로 구조적 파싱해
    최근 `window_min`분간의 타임스탬프 있는 활동이 `tool_progress`
    하트비트 줄만으로 이뤄져 있는지 판정한다 — `_count_structural_denials()`
    (spawn.py:3614)와 같은 구조적 파싱 관용(파싱 실패 줄은 조용히 건너뜀)을
    따른다, 단어/정규식 매치가 아니다.

    반환: `"heartbeat-only"`(창 안 타임스탬프 있는 활동이 하나 이상 있고
    전부 `tool_progress`), `"healthy"`(창 안에 substantive 줄이 하나라도
    있거나 창 안에 타임스탬프 있는 활동이 아예 없음), `"unmeasurable"`(스캔
    구간 전체에 `tool_progress` 태그가 단 하나도 없어 — 이 트랜스크립트가
    애초에 하트비트를 찍는 종류인지 판별할 근거가 없음 — 조용히 STALLED로
    오판하지 않고 명시적으로 "판정 불가"를 돌려준다)."""
    timestamped: list[tuple[float, bool]] = []
    saw_heartbeat_tag = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict):
            continue
        ts_raw = obj.get("timestamp")
        if not isinstance(ts_raw, str):
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        is_heartbeat = obj.get("type") == "tool_progress"
        if is_heartbeat:
            saw_heartbeat_tag = True
        timestamped.append((ts, is_heartbeat))
    if not saw_heartbeat_tag:
        return "unmeasurable"
    window_start = now - window_min * 60
    in_window = [is_hb for ts, is_hb in timestamped if ts >= window_start]
    if in_window and all(in_window):
        return "heartbeat-only"
    return "healthy"


_HEALTH_REFUSAL_TYPES = ("gate-refusal", "harness-refusal", "sandbox-refusal")
DEADLOCK_MIN_REPEATS = 3  # 스코프-확장 코멘트: "짧은 간격으로 반복" 최소 재현 횟수


def _deadlock_signature(work: str | None, min_repeats: int = DEADLOCK_MIN_REPEATS
                         ) -> str | None:
    """`work` 워크스페이스의 `.events.jsonl` 꼬리를 읽어, 마지막
    `progress` 이벤트(있으면) 이후로 같은 거부/게이트-거부 signature 가
    `min_repeats` 번 이상 반복됐으면 그 signature 문자열을, 아니면 None
    을 돌려준다 — DEADLOCKED 판정의 유일한 근거(이슈 #782 스코프-확장
    코멘트: "같은 에러/거부 signature 가 짧은 간격으로 반복, 새 진행
    이벤트 없음"). 순수 읽기: 이벤트 파일에 아무것도 쓰지 않는다."""
    if not work:
        return None
    events_path = _sp._events_path(work)
    if not events_path.exists():
        return None
    events = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    last_progress_ts = max(
        (e.get("ts", -1) for e in events if e.get("type") == "progress"),
        default=-1)
    tail = [e for e in events
            if e.get("type") in _sp._HEALTH_REFUSAL_TYPES and e.get("ts", -1) > last_progress_ts]
    if len(tail) < min_repeats:
        return None
    sigs = [json.dumps(e.get("detail"), sort_keys=True, ensure_ascii=False)
            for e in tail[-min_repeats:]]
    if len(set(sigs)) == 1:
        return sigs[0]
    return None


def _pr_state_from_index(pr_index: dict, branch: str) -> int | None:
    """이슈 #1508 요구 2: `closure_sweep._pr_index_all()`(gates/closure_sweep.py:91)
    이 이미 만든 브랜치->{number,state} 벌크 인덱스에서 OPEN/MERGED 만
    "배달됨"으로 센다 — `_pr_open_or_merged_for_branch()`(spawn.py:1162)와
    같은 시맨틱을 별도 `gh` 호출 없이 재현한다."""
    pr = pr_index.get(branch)
    if pr is None:
        return None
    return pr.get("number") if pr.get("state") in ("OPEN", "MERGED") else None


def diagnose_health(key: str, entry: dict, root: Path = ROOT,
                     now: float | None = None, state: dict | None = None,
                     anomalies: list[str] | None = None,
                     pr_index: dict | None = None) -> dict:
    """이슈 #782 스코프-확장, 이슈 #1966 확장: 살아있는(또는 방금 죽은) 로스터
    엔트리 하나를 HEALTHY/STALLED/STALLED-HEARTBEAT-ONLY(advisory)/
    DEADLOCKED/DEAD-ERRORED 다섯 상태 중 하나로 진단하고
    next-action 을 매긴다. 완료(정상 session-end + PR)는 이 함수의 대상이
    아니다 — `roster_watchdog()`의 기존 completion 경로가 다룬다; 여기는
    "완료가 아닌데 뭐가 문제인가"만 답한다.

    반환: `{"state": str, "next_action": str, "detail": str}`. 완료로
    판정되면(죽었는데 verdict=="normal" 이거나 PR 이 있음) `state` 는
    `None` — 호출부가 그 경우를 건너뛴다는 신호.

    원자료(raw ground truth)만 쓴다: `_alive()`(raw ps), 세션 로그
    mtime/내용(`watchdog_check_one()`), `_pr_open_or_merged_for_branch()`
    — 새 `gh`/git 호출 타입을 추가하지 않는다(프로포절 제약).

    `anomalies`: 호출부가 같은 틱에서 이미 `watchdog_check_one()` 을
    돌렸으면 그 결과를 넘긴다 — `watchdog_check_one()` 은 로그 오프셋
    상태를 소비하는 부수효과가 있어(signal 2/3), 한 틱에 두 번 부르면
    두 번째 호출이 빈 텍스트만 보고 신호를 놓친다. 생략하면(단독/테스트
    호출) 이 함수가 직접 한 번 돌린다.

    `pr_index`: 이슈 #1508 요구 2 — 호출부가 같은 틱에서 이미
    `closure_sweep._pr_index_all()` 벌크 조회를 돌렸으면 그 인덱스를
    넘긴다. 넘기면 dead-entry PR 확인이 `_pr_state_from_index()`로
    인덱스만 보고 끝나 이 호출에서 `gh`를 안 부른다. 생략하면(단독/테스트
    호출, 또는 벌크 조회를 아직 안 도는 호출부) 기존
    `_pr_open_or_merged_for_branch()` 개별 `gh pr list` 로 되돌아간다."""
    now = time.time() if now is None else now
    pid = entry.get("pid", 0)
    work = entry.get("work")
    branch = Path(work).name if work else None
    alive = _sp._alive(pid)
    if not alive:
        verdict = _sp.session_end_verdict(
            work, Path(entry["log"]) if entry.get("log") else None, now=now) \
            if work else None
        if branch is None:
            pr_number = None
        elif pr_index is not None:
            pr_number = _sp._pr_state_from_index(pr_index, branch)
        else:
            pr_number = _sp._pr_open_or_merged_for_branch(root, branch)
        if verdict == "normal" or pr_number is not None:
            return {"state": None, "next_action": "none",
                    "detail": "completion, not a health diagnosis"}
        return {"state": "DEAD-ERRORED", "next_action": "respawn",
                "detail": f"{key}: pid {pid} 부재, PR 없음, "
                          f"session_verdict={verdict!r}"}
    deadlock_sig = _sp._deadlock_signature(work)
    if deadlock_sig is not None:
        return {"state": "DEADLOCKED", "next_action": "surface-repeating-cause",
                "detail": f"{key}: 같은 거부 signature 반복, 새 진행 없음 — {deadlock_sig[:200]}"}
    if anomalies is None:
        anomalies = _sp.watchdog_check_one(key, entry, now=now, state=state)
    if any(a.startswith("log-silence") or a.startswith("watcher-silent")
           for a in anomalies):
        return {"state": "STALLED", "next_action": "resume-watch",
                "detail": f"{key}: idle > {_sp.WATCHDOG_SILENCE_MIN}분, RUNNING"}
    if any(a.startswith("heartbeat-only-growth") for a in anomalies):
        # 이슈 #1966: log-silence 는 안 잡히지만(mtime 계속 갱신) 최근
        # WATCHDOG_HEARTBEAT_ONLY_MIN 분간 tool_progress 하트비트만 관측된
        # 경우 — advisory 전용 서브상태. next_action 은 STALLED 와 동일하게
        # "resume-watch"(재관찰만) 로, kill/spawn-거부/게이트-블록 경로는
        # 이 상태에서 전혀 도달 불가하다.
        return {"state": "STALLED-HEARTBEAT-ONLY", "next_action": "resume-watch",
                "detail": f"{key}: 최근 {_sp.WATCHDOG_HEARTBEAT_ONLY_MIN}분간 "
                          f"tool_progress 하트비트만 관측, RUNNING (advisory)"}
    if any(a.startswith("flat-progress") for a in anomalies):
        # Issue #2101 mechanism 2: the lease was renewed
        # LEASE_FLAT_RENEWALS_K+ times with an unchanged progress indicator
        # and no valid declared wait exempted it — advisory-only sub-state
        # in the #1966 classifier vocabulary. next_action is the same
        # "resume-watch" (re-observe only); no kill/refuse/gate-block path
        # is reachable from this state.
        return {"state": "STALLED-FLAT-PROGRESS", "next_action": "resume-watch",
                "detail": f"{key}: lease renewed {_sp.LEASE_FLAT_RENEWALS_K}+ "
                          f"times with a flat progress indicator, RUNNING "
                          f"(advisory)"}
    return {"state": "HEALTHY", "next_action": "none",
            "detail": f"{key}: 최근 로그 성장, RUNNING"}


def _session_resume_claim(session_id: str, now: float | None = None) -> bool:
    """이슈 #878: `session_id` 하나에 대해 지난
    `SESSION_RESUME_CLAIM_TTL_SEC` 안에 이미 resume-invoke 를 찍은 적
    없으면 True(=지금 이 호출이 그 유일한 소유자, 찍는다), 있으면
    False(=이미 다른 엔트리가 같은 세션을 깨웠다, 침묵) — `spawn.py
    poll-due` 가 이미 쓰는 원자적 체크+스탬프(ledger_check_and_stamp)를
    그대로 락으로 재사용한다(hunt 발견: session_id 는 엔트리가 아니라
    프로세스 단위라 별도 키 네임스페이스가 필요하다)."""
    return _sp.ledger_check_and_stamp(
        f"session-resume:{session_id}", now=now, ttl=_sp.SESSION_RESUME_CLAIM_TTL_SEC)


def _resume_orchestrator_session(session_id: str, nudge: str,
                                  cwd: str | None = None) -> subprocess.Popen | None:
    """이슈 #878 케이스 2: 이미 `end_turn` 으로 끝난 헤드리스 오케스트레이터
    프로세스 그 자체는 인프로세스로 되살릴 수 없다(생존해 있는 프로세스가
    하나도 없다) — `claude -p "<nudge>" --resume "<session_id>"` 로 새
    프로세스를 띄우는 것이 유일한 경로다(survey 인용:
    code.claude.com/docs/en/headless.md "Background tasks at exit"). 그
    새 턴이 verify→merge→rebuild/re-check→`final_report` 를 스스로
    수행한다 — 이 함수는 그 턴을 놓는 것만 하고 기다리지 않는다(watchdog
    틱을 블록하지 않는다는 기존 observe-only 계약과 동일).

    `claude` 실행 파일이 없거나(테스트/부분 설치 환경) Popen 자체가
    실패하면 None — 호출부가 UNMEASURED-shaped 로 보고할 신호.

    이슈 #886: `--permission-mode` 를 안 주면(또는 `acceptEdits` 를 주면)
    이 재개 턴은 파일 편집만 자동승인되고 Bash(`gh pr merge`, `git
    fetch`, `spawn.py`)는 그대로 거부된다 — `acceptEdits` 는 편집 전용
    이지 Bash 자동승인이 아니다(PR #885 실측, `.permission_denials`).
    `bypassPermissions` 는 #700 이 실제 롤 스폰 경로에 이미 쓰는 것과
    같은 헤드리스 기본값이며, 여는 것은 호스트 권한 프롬프트뿐이다 —
    PreToolUse 훅으로 걸린 게이트(gh-write-allow-gate.sh,
    merge-allow-gate.sh, deliverable-guard)는 이 모드와 무관하게 여전히
    실행된다. 단, 정확한 경계 하나: 이 훅들은 "allow" 만 내고 "deny"
    는 내지 않는 설계라, 자기 허용목록 밖의 셰이프(예: `gh repo delete`,
    `git push --force`)에 대해서는 원래 host 기본-거부에 기대고 있었다
    — bypassPermissions 아래서는 그 기본-거부 자체가 없다(issue #886
    hunt 실측, docs/issue-886/reports/implementation/
    hunt-issue-886-permission-mode-fix.md). 이는 #700 이 이미 프로덕션
    롤 스폰에 쓰는 동일 모드의 기존 속성이며, 이 diff 가 새로 만든
    회귀는 아니다."""
    try:
        return subprocess.Popen(
            ["claude", "-p", nudge, "--resume", session_id,
             "--permission-mode", "bypassPermissions"],
            cwd=cwd, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        # issue #910 finding #1: a Popen failure here (e.g. the `claude`
        # binary is missing/unspawnable) was previously indistinguishable
        # from the ordinary claim-skip path in _maybe_resume_for_ready_pr —
        # both returned False with no roster/record trace. Record it here
        # so the caller's event carries the real cause.
        return ("popen-failed", str(exc))


def _maybe_resume_for_ready_pr(key: str, entry: dict, pr_number: int) -> bool:
    """이슈 #878: 죽은(=역할 세션이 끝난) roster 엔트리가 PR 을 남겼을 때,
    그 스폰을 무장한 오케스트레이터가 headless 세션이었다면(`session_id`
    가 찍혀 있으면) `--resume` 으로 그 세션을 재개해 merge→rebuild/
    re-check→`final_report` 턴을 잇는다. 인터랙티브 세션(`session_id`
    없음)은 케이스 1 의 라이브 `watch --follow` notify 경로가 이미
    맡으므로 여기서는 아무것도 하지 않는다(중복 트리거 방지).

    반환: 실제로 resume 를 쐈으면 True, 건너뛰었으면(session_id 없음/이미
    다른 엔트리가 같은 세션을 깨움/Popen 실패) False.

    이슈 #910 finding #1: Popen 실패와 claim-skip 은 이전에는 둘 다
    아무 기록 없이 False 로 수렴했다 — 어느 쪽인지 events.jsonl 에 남긴다."""
    session_id = entry.get("session_id")
    if not session_id:
        return False
    work = entry.get("work")
    events_path = _sp._events_path(work) if work else None
    if not _sp._session_resume_claim(session_id):
        if events_path is not None:
            _sp._append_event(events_path, "resume-skipped-claimed",
                          {"session_id": session_id, "pr_number": pr_number})
        return False
    nudge = (f"delegated PR #{pr_number} ({key}) is ready — verify, merge, "
             f"rebuild/re-check, and emit the 4-part final_report.")
    proc = _sp._resume_orchestrator_session(session_id, nudge, cwd=work)
    if isinstance(proc, tuple) and proc[0] == "popen-failed":
        if events_path is not None:
            _sp._append_event(events_path, "resume-attempt-failed",
                          {"session_id": session_id, "pr_number": pr_number,
                           "reason": proc[1]})
        return False
    return proc is not None


_REQ_ID_RE = re.compile(r"\bR(\d+)\b")
_NORTHPOLE_REQ_RE = re.compile(r"northpole\s+req\s*#\s*(\d+)", re.IGNORECASE)


def _requirement_drift_cache_path(root: Path) -> Path:
    return root / "runs" / "requirement_drift_cache.json"


def _load_requirement_drift_cache(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_requirement_drift_cache(path: Path, data: dict) -> None:
    # issue #1688: same atomic temp+rename pattern as
    # gates/gh_delta.py::_atomic_write_json (that helper is module-private,
    # so this is a small local duplicate rather than reaching into it).
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".req-drift-", suffix=".tmp")
    except OSError:
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_name, path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def _fetch_issue_or_pr_via_cache(root: Path, number: int) -> dict | None:
    """issue #1688: single-number detail fetch for delta-mode
    requirement-drift rechecks, routed through `gates.gh_cache.cached_get`
    (shared ETag cache, #1682) rather than a bare `gh` call."""
    slug = _sp._repo_slug(root)
    if not slug:
        return None
    sys.path.insert(0, str((_sp.ROOT / "gates").resolve()))
    import gh_cache
    data, ok, _billed = gh_cache.cached_get(f"repos/{slug}/issues/{number}", root=root)
    if not ok or not isinstance(data, dict):
        return None
    return data


def _board_read(root: Path) -> tuple[dict | None, dict]:
    """Issue #2103: the shared multi-item board read. Delegates to
    `gates.board_read.board_read` (single GraphQL board query + delta reads
    over a cached snapshot) and routes its fail-open signal to the ledger
    as an advisory `board_read_fail_open` event — a gh/network failure
    serves the stale snapshot and never crashes the calling sweep.

    Returns `(board, meta)`; `board` is None only when gh failed AND no
    snapshot exists (or the repo has no slug — non-GitHub checkout)."""
    board_slug = _sp._repo_slug(root)
    if not board_slug:
        return None, {"source": None, "api_calls": 0,
                      "last_sweep_at": None, "error": "no repo slug"}
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import board_read as board_read_mod

    def _fail_open(detail: str) -> None:
        _sp.ledger_write({"event": "board_read_fail_open", "repo": board_slug,
                      "detail": detail, "ts": time.time()})

    return board_read_mod.board_read(root, board_slug, on_fail_open=_fail_open)


def _board_pr_index(root: Path) -> dict | None:
    """Issue #2103: `closure_sweep._pr_index_all`-shaped branch->PR index
    served from the shared board read (snapshot/delta) — replaces per-branch
    `gh pr list` loops in the poll tick. None when the board is unreadable
    (caller falls back to the per-branch helper, preserving today's
    fail-open behavior)."""
    board, _meta = _sp._board_read(root)
    if board is None:
        return None
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import board_read as board_read_mod
    return board_read_mod.pr_index(board)


_DIGEST_LIVE_ENTRY_RE = re.compile(
    r"^- (R\d+): (.+?) \[(\S+)\] \(source: (.+)\)$", re.M)


def parse_digest_live_entries(digest_text: str) -> dict[str, tuple[str, str, str]]:
    """`requirement-digest.md` 의 `- R<n>: <paraphrase> [<status>]
    (source: <source>)` 줄들을 `id -> (paraphrase, status, source)` 로
    파싱한다 (issue #2077).

    각 항목은 한 줄(줄바꿈 없음)이어야 하지만, `<paraphrase>` 와
    `<source>` 는 여러 절로 이루어진 자유 형식 텍스트여도 된다 —
    `source:` 를 `#<issue-number>` 형태로 강제하지 않는다(문서화된
    자유 형식 예: tm-dicequest R1/R2 의 "user directive 2026-08-23,
    issue #1"). `[<status>]` 만 공백 없는 단일 토큰이어야 한다."""
    return {
        m.group(1): (m.group(2), m.group(3), m.group(4))
        for m in _sp._DIGEST_LIVE_ENTRY_RE.finditer(digest_text)
    }


def requirement_drift(root: Path, changed_numbers: set[int] | None = None) -> None:
    """이슈 #930 (northpole req#6): digest 에 살아있는(=stale 아닌) 요구
    각각이 열린 이슈/PR 중 최소 하나에서 언급되는지, 그리고 열린
    proposal/PR 이 요구 ID 를 하나라도 인용하는지 점검한다. `_board_wide_sweep`
    의 `accumulation_trend()` 와 같은 계약 — 결과를 출력만 하고
    `anomaly_count` 에는 절대 합산하지 않는다(advisory, non-blocking).
    `gh` 실패는 조용히 건너뛴다(watch 계열 불가침 원칙 — 이 스윕 자체는
    블로킹 게이트가 아니라 이 함수도 그 계약을 넘지 않는다). 틱당 비용은
    O(열린 이슈/PR 수) + O(digest 요구 수) — `accumulation_trend()` 가 같은
    틱에서 이미 지불하는 것과 같은 자릿수.

    이슈 #1688: `changed_numbers` 가 주어지면(델타 모드) 그 번호들만
    `gates.gh_cache.cached_get` 으로 다시 조회하고, 나머지는
    `runs/requirement_drift_cache.json` 에 저장된 이전 판정용 본문을 그대로
    재사용한다 — `None` 이면(기본) 기존처럼 열린 이슈/PR 전체를 재훑는다."""
    digest_path = root / "docs" / "specs" / "requirement-digest.md"
    if not digest_path.exists():
        return
    digest_text = digest_path.read_text(encoding="utf-8", errors="replace")
    # issue #1017: 각 살아있는 요구의 (이미 파싱된) 다이제스트 줄을
    # 통째로 잡아둔다 — id 집합만 뽑던 이전 판과 달리, 아래 next-action
    # 출력이 paraphrase/source 를 다시 gh 로 조회하지 않고 이 메모리에서
    # 바로 쓴다(제안서 Accumulation 절이 명시한 "이미 파싱된 다이제스트
    # 엔트리 재사용, 새 gh 호출 없음").
    # issue #2077: `source:` 는 `#<number>` 로만 국한되지 않는다 —
    # 문서화된 자유 형식(tm-dicequest R1/R2)은 "user directive
    # 2026-08-23, issue #1" 같은 multi-clause 자유 텍스트도 허용한다.
    # 괄호 밖 마지막 ")"까지 통째로 캡처해서 그대로 보존한다(숫자
    # 강제 파싱 없음 — 아래 next-action 출력도 원문을 그대로 쓴다).
    live_entries = _sp.parse_digest_live_entries(digest_text)
    live_ids = set(live_entries) or set(
        re.findall(r"^- (R\d+):", digest_text, re.M))
    if not live_ids:
        return

    cache_path = _sp._requirement_drift_cache_path(root)
    if changed_numbers is None:
        # Issue #2103: full mode reads open issues+PRs from the shared board
        # read (snapshot + delta; was two `gh issue list`/`gh pr list` calls
        # per full-mode tick). A stale fail-open board is still usable here —
        # this signal is advisory and a slightly stale citation index beats
        # no verdict (same trade the old list calls could not make).
        full_board, _board_meta = _sp._board_read(root)
        if full_board is None:
            print("[watchdog] requirement-drift: gh 실패 — 판정 불가 (advisory, 미집계)")
            return
        all_items = [item
                     for group in (full_board["issues"], full_board["prs"])
                     for item in group.values()
                     if item.get("state") == "OPEN"]
        # issue #1688: full-mode run also refreshes the verdict cache so a
        # later delta-mode tick can reuse today's fetch for unchanged numbers.
        cache = {str(item.get("number")): {"title": item.get("title", ""),
                                            "body": item.get("body", "") or ""}
                 for item in all_items if item.get("number") is not None}
        _sp._save_requirement_drift_cache(cache_path, cache)
    else:
        # issue #1688: delta mode — only re-fetch the changed numbers (via
        # the shared gh_cache), reuse the on-disk verdict cache for the rest.
        cache = _sp._load_requirement_drift_cache(cache_path)
        all_items = []
        any_fetch_ok = not changed_numbers
        failed_numbers: list[int] = []
        for num in sorted(changed_numbers):
            item = _sp._fetch_issue_or_pr_via_cache(root, num)
            if item is None:
                failed_numbers.append(num)
                continue
            any_fetch_ok = True
            # issue #2078: a live refetch may show the number merged/closed
            # since it was last cached as open — drop it from the index
            # entirely instead of re-flagging it as an open uncited PR.
            if item.get("state") not in (None, "open"):
                cache.pop(str(num), None)
                continue
            all_items.append(item)
            cache[str(num)] = {"title": item.get("title", ""),
                                "body": item.get("body", "") or ""}
        for key, val in cache.items():
            try:
                key_num = int(key)
            except ValueError:
                continue
            if key_num in changed_numbers:
                continue
            all_items.append({"number": key_num, "title": val.get("title", ""),
                               "body": val.get("body", "")})
        _sp._save_requirement_drift_cache(cache_path, cache)
        if not any_fetch_ok:
            print("[watchdog] requirement-drift: gh 실패 — 판정 불가 (advisory, 미집계)")
            return
        if failed_numbers:
            # 리뷰 non-blocking 노트: 델타 모드에서 개별 번호 조회 실패는
            # 조용히 사라지지 않고 이 한 줄로 남는다 — 해당 번호는 이번
            # 틱에서 재평가 안 되고 캐시된 이전 판정을 그대로 쓴다.
            print(f"[watchdog] requirement-drift: 조회 실패 {failed_numbers} — "
                  "이전 캐시 판정 유지")

    # 이슈 #1219: gates 코드는 언제나 이 체크아웃(ROOT)에서 온다 — root 가
    # 컨슈머의 타깃 프로젝트일 때 거기엔 gates/ 가 없다.
    sys.path.insert(0, str((_sp.ROOT / "gates").resolve()))
    try:
        import requirement_linkage as _requirement_linkage
        infra_tag = _requirement_linkage._INFRA_TAG
    except ImportError:
        # advisory 계약(이 함수 docstring): gh 실패처럼 import 실패도
        # 이 스윕 전체를 죽이지 않고 조용히 건너뛴다 — infra-tag 예외
        # 없이 기존 동작으로 계속한다.
        infra_tag = None

    mentioned_reqs: set[str] = set()
    unreferenced_open = []
    for item in all_items:
        text = f"{item.get('title', '')}\n{item.get('body', '') or ''}"
        found = set(_sp._REQ_ID_RE.findall(text)) | set(
            f"R{n.zfill(3)}" for n in _sp._NORTHPOLE_REQ_RE.findall(text))
        # _REQ_ID_RE 는 "R001" 형태의 raw 캡처가 아니라 숫자만 잡으므로
        # digest ID 형식(R\d+)과 직접 비교하려면 원문 재검색이 더 정확하다.
        raw_ids = set(re.findall(r"\bR\d+\b", text))
        mentioned_reqs |= raw_ids
        # 이슈 #1080: gates/requirement_linkage.py::check_issue_body 가 이미
        # 인정하는 infra-tag 예외를 여기서도 그대로 존중한다 — 같은
        # _INFRA_TAG 리터럴을 import 해서 두 검사가 서로 어긋나지 않게 한다.
        if infra_tag is not None and infra_tag in text:
            continue
        if not (raw_ids or _sp._NORTHPOLE_REQ_RE.search(text)):
            unreferenced_open.append(item.get("number"))

    unmentioned_live = sorted(live_ids - mentioned_reqs)
    # issue #1142: `enforced` (배송 완료, 라이브 enforcement 경로 있음) 요구는
    # 인용 없이도 드리프트로 잡지 않는다 — `open`(미배송) 요구만 인용을
    # 요구한다. 다이제스트 파싱 실패 등으로 상태를 못 얻은 id 는 기존처럼
    # 보수적으로(=open 취급) 계속 플래그한다.
    unmentioned_live = [
        rid for rid in unmentioned_live
        if live_entries.get(rid, (None, "open", None))[1] == "open"
    ]
    unreferenced_open = sorted(unreferenced_open)
    if unmentioned_live:
        # issue #1017: 바래 ID 목록 대신, 요구마다 다이제스트 paraphrase/
        # source 와 — 있으면 — 요구 인용이 전혀 없는 열린 이슈/PR(연결
        # 후보) 을 named next-action 으로 출력한다.
        for rid in unmentioned_live:
            paraphrase, _status, source = live_entries.get(
                rid, ("(다이제스트에 paraphrase 없음)", "open", "?"))
            candidates = unreferenced_open[:5]
            cand_note = (f" 후보(요구 인용이 전혀 없는 열린 이슈/PR): {candidates}"
                         if candidates else "")
            print(f"[watchdog] requirement-drift: 요구 {rid} — 다이제스트: "
                  f"\"{paraphrase}\" (source: {source}) — 열린 이슈/PR "
                  f"어디에도 인용되지 않는다.{cand_note}")
    if unreferenced_open:
        print(f"[watchdog] requirement-drift: 요구 ID 를 전혀 인용하지 않는 "
              f"열린 이슈/PR {unreferenced_open}")


def _roster_target_repos(d_all: dict) -> list[Path]:
    """이슈 #1276 요구#1: 로스터 엔트리(live + returned-undisposed — 처분된
    엔트리는 `roster_remove()`가 지우므로 `_roster_load()`가 담는 건 항상
    이 둘뿐이다)의 `work`(각 엔트리가 등록될 때 넘겨받은 -C/cwd) 필드에서
    distinct 타깃 레포를 뽑는다. 등장 순서를 안정적으로 유지하려고
    `dict`(Python 3.7+ 삽입 순서 보존) 를 dedup 에 쓴다."""
    repos: dict[Path, None] = {}
    for e in d_all.values():
        work = e.get("work")
        if not work:
            continue
        repos.setdefault(Path(work).resolve(), None)
    return list(repos)


def _board_wide_sweep_all(root: Path, d_all: dict) -> int:
    """이슈 #1276 요구#2/#3/#4: `_board_wide_sweep`(closure_sweep +
    spawn_coverage)를 arm-root 하나가 아니라 arm-root(seed/default) +
    로스터가 가리키는 distinct 타깃 레포마다 돈다. 로스터가 비어 있으면
    오늘과 동일하게 arm-root 하나만 스윕한다(empty-state parity). 매 틱
    로스터를 다시 읽으므로 새 레포로의 스폰이 재무장 없이 다음 틱부터
    잡힌다. 각 레포의 출력 줄은 그 레포 라벨로 접두된다 — 멀티보드 출력의
    귀속을 지킨다. 보드가 아닌(docs/specs/approvers.md 없는) 로스터
    레포는 매 틱 노이즈 없이 한 줄만 찍고 건너뛴다(#1245/#1275 와 합성).
    이슈 #1280: arm-root 자체도 보드가 아니면(예: 비-보드 레포에서 무장된
    세션) 스윕 대상에서 조용히 제외된다 — 라인도 찍지 않는다. 그래도
    로스터가 가리키는 보드 타깃은 계속 스윕한다(#1276 요구를 살린다).
    arm-root 의 비-git 검증은 CLI 진입점(#1275)에서 이미 끝난 뒤라
    여기서는 건드리지 않는다."""
    root = root.resolve()
    targets: dict[Path, None] = {root: None}
    for repo in _sp._roster_target_repos(d_all):
        targets.setdefault(repo, None)
    count = 0
    for repo in targets:
        label = _sp._repo_identity(repo)
        if not (repo / _sp.MARKER).exists():
            if repo == root:
                continue
            print(f"[watchdog] board-sweep: {label} — 로스터 타깃 레포지만 "
                  f"보드 아님({_sp.MARKER} 없음), 건너뜀")
            continue
        got, lock_msg = _sp.cross_workspace_board_sweep_lock_acquire(repo)
        if not got:
            print(f"[watchdog] board-sweep: {label} 건너뜀 (다른 워크스페이스가 스윕 중) — {lock_msg}")
            continue
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            count += _sp._board_wide_sweep(repo)
        for line in buf.getvalue().splitlines():
            print(f"[{label}] {line}")
    return count


# 이슈 #1688 blocker 2: gh_budget(#1681, gates/gh_budget.py — 이미 merged,
# PR #1685)로 워치독 클래스를 미터링한다. 계정 리저브 바닥은 closure_sweep
# 의 기존 가드 문턱과 동일하게 맞춰 이중 가드를 만들지 않는다. 예산 값은
# 틱당 최대 gh 호출 수(call_budget=8)의 몇 배로 넉넉히 잡아, 정상 동작에서
# 절대 안 걸리고 실제 폭주(무한 루프성 재시도 등)에서만 백스톱으로 걸리게
# 한다.
_WATCHDOG_GH_BUDGET_CLASSES = {"watchdog": 200}


_HEAD_REF_SUBJECT_RE = re.compile(r"^issue-(\d+)/")


def _board_wide_sweep(root: Path) -> int:
    """이슈 #464: closure_sweep/spawn_coverage 를 한 틱씩 돌려 보고만 한다
    (observe-only, roster_watchdog 계약과 동일). 위반/미커버 이슈 수를
    합쳐서 돌려준다 — gh 실패(skips 있음 / open_issues=None)도 "깨끗함"이
    아니라 이상 신호 1건으로 센다(조용한 실패가 진행과 구분 안 되는 결함을
    재현하지 않기 위해).

    이슈 #1219: `root` 는 스캔 대상(보드) — 컨슈머 세션이면 타깃 프로젝트다.
    gates 코드 자체는 언제나 이 체크아웃(ROOT)에서 임포트한다 — 타깃
    프로젝트엔 gates/ 가 없다.

    이슈 #1498: gh 를 부르는 신호들(spawn-on-pr, closure-sweep,
    spawn-coverage, issue #2173 이 더한 spawn-on-approve)은 모두 요구
    1(쿼터 바닥) · 요구 3(스윕 백오프) · 요구 5(틱당 호출 예산)의
    게이팅을 받는다 — 로컬 전용 신호(`accumulation_trend`,
    `requirement_drift`)는 게이팅 없이 항상 돈다.

    이슈 #1554 요구 1/3: 세 신호는 `closure_sweep.next_categories()`로
    이번 틱에 돌릴 카테고리(최대 `call_budget`개)만 골라 돈다 — 나머지는
    드롭되지 않고 `runs/board_sweep_queue.json`에 이월되어 다음 틱(들)에
    반드시 돈다(watch-coverage 불가침 계약). 예산=8 은 오늘의
    call_budget 과 같은 값을 유지해 기존 관측 동작(사실상 매 틱 세
    카테고리 다 돔)을 그대로 보존한다.

    이슈 #1688: 백오프/레이트리밋 가드를 통과하면, 카테고리를 고르기 전에
    `gates.gh_delta.fetch_delta(root, slug, "issues")` 를 틱당 정확히 1회
    부른다 — 이 틱의 유일한 조건부 프로브. `"no-change"` 면 상세 조회를
    전부 건너뛰고(`accumulation_trend()` 만 예외로 계속 돈다),
    `"delta"` 면 closure-sweep/requirement-drift 를 델타의 이슈/PR 번호로만
    좁히고, `"full-rescan"`/`"error"`/(비-GitHub 레포라 `slug` 가 없는 경우)
    는 오늘의 전체 로직으로 그대로 떨어진다."""
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import closure_sweep
    import spawn_coverage
    import spawn_on_pr
    import spawn_on_approve
    import gh_delta
    import gh_budget
    count = 0
    call_budget = 8
    budget: "gh_budget.GhBudget | None" = None

    def _charge_watchdog_budget(source: str, cost: int = 1) -> bool:
        result = budget.charge("watchdog", cost=cost)
        if not result["ok"]:
            print(gh_budget.budget_message(source, result["remaining"], result.get("until")))
        return result["ok"]

    def _run_local_only_signals(changed_numbers: set[int] | None = None,
                                 skip_requirement_drift: bool = False) -> None:
        # 이슈 #512 요구사항 4 / #930 요구#6: advisory only — 아무것도
        # 막지 않고 anomaly count 에도 합산하지 않는다. gh 를 쓰지 않으므로
        # 쿼터 바닥/백오프와 무관하게 항상 돈다.
        trend = closure_sweep.accumulation_trend(root)
        print(f"[watchdog] {closure_sweep.format_accumulation_trend(trend)}")
        if skip_requirement_drift:
            return
        _sp.requirement_drift(root, changed_numbers=changed_numbers)

    backoff_state = closure_sweep.load_backoff_state(root)
    if not closure_sweep.sweep_should_run(backoff_state, "board-sweep"):
        closure_sweep.save_backoff_state(root, backoff_state)
        print("[watchdog] board-sweep: 건너뜀 (백오프 간격, gh 호출 없음)")
        _run_local_only_signals()
        return count

    remaining, guard_ok = closure_sweep.rate_limit_remaining(root)
    calls_made = 1
    # 이슈 #1745: 방금 위에서 이미 `gh api rate_limit` 을 한 번 불렀다 —
    # GhBudget 이 자기 스냅샷을 또 부르면 같은 틱에 같은 쿼리가 두 번
    # 나간다. 방금 받은 결과를 preseed 해 두 번째 호출을 없앤다.
    budget = gh_budget.GhBudget(root, classes=_sp._WATCHDOG_GH_BUDGET_CLASSES,
                                 reserve=closure_sweep._RATE_LIMIT_GUARD_THRESHOLD,
                                 preseeded_snapshot=(remaining, guard_ok))
    if guard_ok and remaining < closure_sweep._RATE_LIMIT_GUARD_THRESHOLD:
        closure_sweep.record_sweep_result(backoff_state, "board-sweep", True)
        closure_sweep.save_backoff_state(root, backoff_state)
        count += 1
        print(f"[watchdog] board-sweep: 미집계 (rate-limit, remaining={remaining})")
        _run_local_only_signals()
        return count

    # 이슈 #1688: 틱당 단일 변경-커서 프로브. gh_budget(#1681, landed —
    # gates/gh_budget.py) 미터링을 프로브 자체보다 먼저 건다 — 예산 소진이면
    # 프로브조차 안 나가고 이번 틱은 로컬 신호만 돈다.
    slug = _sp._repo_slug(root)
    delta_items: list[dict] | None = None
    delta_classification: str | None = None
    changed_numbers: set[int] = set()
    if slug:
        if not _charge_watchdog_budget("board-sweep gh_delta probe"):
            count += 1
            _run_local_only_signals()
            return count
        try:
            delta_items, _delta_cursor, delta_classification = gh_delta.fetch_delta(
                root, slug, "issues", include_prs=True)
        except Exception as ex:
            delta_classification = "error"
            print(f"[watchdog] gh_delta 프로브 예외: {ex}", file=sys.stderr)

        if delta_classification == "error":
            print("[watchdog] board-sweep: gh_delta 프로브 실패 (error 분류) — "
                  "보수적으로 오늘의 전체 로직으로 폴백")
        elif delta_classification == "no-change":
            closure_sweep.record_sweep_result(backoff_state, "board-sweep", False)
            closure_sweep.save_backoff_state(root, backoff_state)
            print("[watchdog] board-sweep: no-change (delta empty) — "
                  "상세 조회/전체 재훑기 건너뜀")
            _run_local_only_signals(skip_requirement_drift=True)
            return count
        elif delta_classification == "full-rescan":
            print("[watchdog] board-sweep: full-rescan (gh_delta 분류 — 커서 "
                  "없음/손상, 페이지 오버플로, 또는 재훑기 주기 도래 중 하나; "
                  "gh_delta 는 구체적 사유 문자열을 노출하지 않는다) — "
                  "오늘의 전체 로직으로 폴백")
        elif delta_classification == "delta":
            pr_numbers: set[int] = set()
            for it in (delta_items or []):
                n = it.get("number")
                if not isinstance(n, int):
                    continue
                if "pull_request" in it:
                    pr_numbers.add(n)
                else:
                    changed_numbers.add(n)
            if pr_numbers:
                # 이슈 #1688 blocker 1: PR 만 바뀐 틱은 이슈 번호가 델타에
                # 안 잡힌다 — 각 PR 을 headRefName(issue-<n>/<role>)으로
                # subject 이슈에 매핑해 narrowing set 에 합친다.
                # closure_sweep._pr_index_all 은 이 파일이 이미 다른
                # 경로(closure-sweep 처리)에서 쓰는 동일한 `gh pr list`
                # 인덱스 — PR 변경이 있을 때만(무변경 틱엔 안 나감) 도는
                # 추가 1회 호출이다.
                pr_index, pr_index_ok = closure_sweep._pr_index_all(root)
                if pr_index_ok and pr_index is not None:
                    number_to_branch = {v.get("number"): k for k, v in pr_index.items()}
                    for prn in sorted(pr_numbers):
                        branch = number_to_branch.get(prn)
                        m = _sp._HEAD_REF_SUBJECT_RE.match(branch) if branch else None
                        if m:
                            changed_numbers.add(int(m.group(1)))
                        else:
                            print(f"[watchdog] board-sweep: PR #{prn} 변경 감지했으나 "
                                  f"subject 매핑 실패 (브랜치={branch!r}, issue-<n>/<role> "
                                  "형식 아님) — 이 PR 은 narrowing 에서 무시")
                else:
                    print(f"[watchdog] board-sweep: PR {sorted(pr_numbers)} 변경 감지했으나 "
                          "PR 인덱스 조회 실패 — subject 매핑 불가, 이 PR 들은 narrowing 에서 무시")
            print(f"[watchdog] board-sweep: delta {len(changed_numbers)}건 "
                  f"변경 {sorted(changed_numbers)} — 해당 subject/이슈만 재평가")
    delta_mode = slug is not None and delta_classification == "delta"

    this_tick, carried_over = closure_sweep.next_categories(root, call_budget)
    if carried_over:
        print(f"[watchdog] board-sweep: 이월 (예산) {carried_over}")

    if this_tick and not _charge_watchdog_budget("board-sweep sweep calls", cost=len(this_tick)):
        count += 1
        closure_sweep.record_sweep_result(backoff_state, "board-sweep", False)
        closure_sweep.save_backoff_state(root, backoff_state)
        _run_local_only_signals(changed_numbers=changed_numbers if delta_mode else None)
        return count

    issue_states, issue_states_ok = (None, True)
    if ("spawn-on-pr" in this_tick or "closure-sweep" in this_tick
            or "spawn-on-approve" in this_tick):
        issue_states, issue_states_ok = closure_sweep.issue_state_index_all(root)
        calls_made += 1

    rate_limited_this_tick = False

    # 이슈 #1745: 이번 틱에 PR 인덱스가 필요한 카테고리가 둘 이상이면
    # 벌크 PR 인덱스를 여기서 한 번만 가져와 공유한다 — 각자
    # `closure_sweep._pr_index_all()` 을 따로 부르면 `gh api .../pulls`
    # 페이지네이션이 틱당 여러 번 나간다(#1745 관측; issue #2173 은
    # spawn-on-approve 를 이 공유 대상에 더했다).
    _pr_index_consumers = sum(c in this_tick for c in
                              ("spawn-on-pr", "closure-sweep", "spawn-on-approve"))
    shared_pr_index: dict | None = None
    if _pr_index_consumers >= 2:
        shared_pr_index, _ = closure_sweep._pr_index_all(root)

    if "spawn-on-pr" in this_tick:
        try:
            spawned = spawn_on_pr.spawn_missing_for_pr(
                root, str(root), issue_states=issue_states, pr_index=shared_pr_index)
            if spawned:
                print(f"[watchdog] spawn-on-pr: {len(spawned)}건 스폰: {spawned}")
            parked = spawn_on_pr.parked_report(root)
            if parked:
                # issue #1476: park 된 항목도 watch-coverage 는 유지한다 — 스폰만
                # 건너뛰고 waiting-for-human 으로 계속 보인다.
                print(f"[watchdog] spawn-on-pr: waiting-for-human {len(parked)}건: {parked}")
        except Exception as ex:
            count += 1
            print(f"[watchdog] spawn-on-pr 실패: {ex}", file=sys.stderr)

    if "closure-sweep" in this_tick:
        # 이슈 #1688: delta 모드면 board() 를 델타의 이슈/PR 번호로 필터한
        # subjects 만 넘겨 그 subject 만 재평가한다(전체 보드 아님).
        sweep_subjects = None
        if delta_mode:
            sweep_subjects = {}
            for subj, roles in _sp.board(root).items():
                parts = subj.split("-", 1)
                if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) in changed_numbers:
                    sweep_subjects[subj] = roles
        violations, skips = closure_sweep.find_violations(
            root, subjects=sweep_subjects, issue_states=issue_states,
            pr_index=shared_pr_index)
        calls_made += 1
        if violations:
            count += len(violations)
            print(f"[watchdog] closure-sweep: 위반 {len(violations)}건")
            print(closure_sweep.format_report(violations))
        rate_limited_this_tick = bool(skips) and not issue_states_ok
        if skips:
            count += 1
            print(f"[watchdog] closure-sweep: 확인 불가 (gh 실패) {len(skips)}건")

    if "spawn-on-approve" in this_tick:
        # 이슈 #2173: APPROVE 코멘트 관측 -> phase-2 즉시 스폰 시도. delta
        # 모드면 이번 틱에 바뀐 이슈 번호로만 좁힌다(closure-sweep 과 같은
        # narrowing) — 승인 코멘트 자체가 이슈 코멘트 델타로 잡힌다. 후보
        # subject 는 board() 가 아니라 로컬 issue-*/* 브랜치에서 나오므로
        # (spawn_on_approve.py 참고) closure-sweep 처럼 board() 를 거쳐
        # 필터하지 않고, 바뀐 이슈 번호 집합을 곧장 넘긴다.
        approve_subjects = (
            {f"issue-{n}" for n in changed_numbers} if delta_mode else None)
        try:
            spawned2 = spawn_on_approve.spawn_phase2(
                root, str(root), subjects=approve_subjects,
                issue_states=issue_states, pr_index=shared_pr_index)
            if spawned2:
                print(f"[watchdog] spawn-on-approve: {len(spawned2)}건 스폰: {spawned2}")
        except Exception as ex:
            count += 1
            print(f"[watchdog] spawn-on-approve 실패: {ex}", file=sys.stderr)

    _run_local_only_signals(changed_numbers=changed_numbers if delta_mode else None)

    if "spawn-coverage" in this_tick:
        open_issues = spawn_coverage._list_open_issues(root)
        calls_made += 1
        if open_issues is None:
            count += 1
            rate_limited_this_tick = True
            print("[watchdog] spawn-coverage: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가")
        else:
            uncovered = spawn_coverage.find_uncovered(
                open_issues, _sp.board(root), datetime.now(timezone.utc))
            if uncovered:
                count += len(uncovered)
                print(f"[watchdog] spawn-coverage: 커버되지 않은 이슈 {uncovered}")

    closure_sweep.record_sweep_result(backoff_state, "board-sweep", rate_limited_this_tick)
    closure_sweep.save_backoff_state(root, backoff_state)
    if calls_made > call_budget:
        count += 1
        print(f"[watchdog] board-sweep: 예산 초과 ({calls_made}건 > {call_budget})")
    return count


WATCHDOG_LOCK_PATH = STATE_ROOT / "watchdog.lock"
WATCHDOG_FRESHNESS_STATE_PATH = STATE_ROOT / "watchdog-freshness-state.json"


def _proc_start_time(pid: int) -> str | None:
    """`/proc/<pid>/stat` 필드 22(starttime, 부팅 이후 클럭틱)를 읽는다 (이슈
    #1456) — pid 만으론 크래시 뒤 재사용된 pid 를 "그 프로세스가 아직
    살아있다"고 오판한다(요구 1의 caveat 1). comm 필드가 괄호/공백을 담을 수
    있어 마지막 ')' 뒤부터 잘라 필드 3(state)부터 다시 센다."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return None
    rest = raw[raw.rfind(")") + 2:]
    fields = rest.split()
    if len(fields) < 20:
        return None
    return fields[19]  # starttime = 필드 22, state(필드3)부터 0-based 로 19번째


def watchdog_lock_acquire(lock_path: Path = WATCHDOG_LOCK_PATH,
                           pid: int | None = None) -> tuple[bool, str]:
    """`spawn.py watchdog` 단일-인스턴스 락(이슈 #1456 요구 1). 이미 살아있는
    인스턴스가 있으면 (False, 안내줄) — pid 재사용을 피하려 pid *와*
    프로세스 시작 시각이 둘 다 일치해야 "살아있다"로 본다. 죽은 프로세스가
    남긴 락(또는 pid 재사용으로 시작시각이 달라진 락)은 그대로 회수한다."""
    my_pid = pid if pid is not None else os.getpid()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(lock_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        existing = None
    if existing:
        other_pid = existing.get("pid")
        other_start = existing.get("start_time")
        if (isinstance(other_pid, int) and _sp._alive(other_pid)
                and _sp._proc_start_time(other_pid) == other_start):
            return False, (f"[watchdog] 이미 실행 중: pid={other_pid} "
                            f"start_time={other_start} — lock={lock_path}")
    lock_path.write_text(json.dumps({"pid": my_pid,
                                      "start_time": _sp._proc_start_time(my_pid)}))
    return True, ""


def _cross_workspace_board_sweep_lock_path(repo_root: Path) -> Path:
    """이슈 #1554 요구 2: board-wide 스윕 락의 위치는 *실행 중인 checkout*
    (`STATE_ROOT`, `ROOT`가 정의된 곳 — 워크스페이스마다 다르다)이 아니라
    *스윕 대상 레포의 identity*로 정해져야 한다 — 그래야 서로 다른
    워크스페이스에서 뜬 워치독들도 같은 파일을 놓고 경합한다(#1510
    single-instance 정책의 cross-workspace enforcement gap). `_workspace_base()`
    가 이미 `MUSTER_WORK_DIR`(기본 `~/.tokenmaxxxer/work`) 오버라이드를
    존중하므로, 그 부모 아래 고정 `locks/` 디렉터리를 쓴다 — 어느 체크아웃의
    spawn.py 가 이 코드를 실행하든 물리적으로 같은 경로가 나온다.
    `_repo_identity()`(순수 로컬, gh 호출 없음)를 키로 쓴다."""
    return (_sp._workspace_base().parent / "locks" /
            f"board-sweep-{_sp._repo_identity(repo_root)}.lock")


def cross_workspace_board_sweep_lock_acquire(
        repo_root: Path, pid: int | None = None) -> tuple[bool, str]:
    """이슈 #1554 요구 2: 레포 하나에 board-wide 스위퍼가 딱 하나만 뜨게
    한다. 세션별 헬스 워처(`roster_watchdog` 개별 엔트리)는 이 락을 타지
    않는다 — 여기 거치는 건 `_board_wide_sweep_all`이 부르는 board-wide
    스윕뿐이다. 락 자체는 `watchdog_lock_acquire`와 같은 pid+시작시각
    liveness 판정을 그대로 재사용한다(죽은 홀더의 락은 회수됨)."""
    return _sp.watchdog_lock_acquire(
        lock_path=_sp._cross_workspace_board_sweep_lock_path(repo_root), pid=pid)


def watchdog_current_head(cwd: Path = ROOT) -> str | None:
    """워치독이 코드를 로드한 체크아웃의 현재 HEAD (이슈 #1456 요구 2)."""
    r = subprocess.run(["git", "-C", str(cwd), "rev-parse", "HEAD"],
                        capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def watchdog_freshness_check(startup_head: str, cwd: Path = ROOT,
                              fetched_this_tick: bool = False,
                              state_path: Path | None = None) -> tuple[bool, str]:
    """틱마다 체크아웃 HEAD 를 시작 시점 HEAD 와 비교한다 (이슈 #1456 요구 2)
    — #1360 이 재발한 원인은 merge != deploy: 장수 워치독이 구코드를 계속
    물고 있었다. 이 틱이 아직 fetch 를 하지 않았으면(caveat 2), 비교 전에
    한 번 fetch 해 로컬 체크아웃을 최신 origin HEAD 에 맞춘다 — 기존
    per-spawn fetch cadence 가 이미 하는 일과 같은 모양이라 새 원격 호출
    경로를 늘리지 않는다. git 실패는 advisory 로 두고 틱을 막지 않는다
    (fail-open — 네트워크 문제로 매 틱을 재기동시키면 더 나쁘다).

    `state_path` 가 주어지면(이슈 #1755) 같은 HEAD 전환에 대해 안내줄을
    한 번만 낸다 — 틱마다 별도 CLI 서브프로세스로 재호출되므로(장수
    파이썬 프로세스가 아니다) 인메모리 dedup 은 불가능하고, `state_path`
    에 마지막으로 알린 HEAD 를 남겨 다음 서브프로세스 호출이 읽는다.
    `state_path=None` 이면 오늘의 동작(dedup 없음, 기존 테스트) 그대로다."""
    if not fetched_this_tick:
        subprocess.run(["git", "-C", str(cwd), "fetch", "--quiet", "origin"],
                        capture_output=True, text=True)
        pull = subprocess.run(["git", "-C", str(cwd), "merge", "--ff-only",
                                "--quiet", "origin/HEAD"],
                               capture_output=True, text=True)
        del pull  # 실패해도(로컬 커밋 등) advisory — HEAD 비교로 판정한다
    current = _sp.watchdog_current_head(cwd)
    if current is None:
        return True, ""
    if current == startup_head:
        return True, ""
    msg = (f"[watchdog] 코드-신선도: 체크아웃 HEAD 가 바뀌었다 "
           f"(시작={startup_head[:12]} 현재={current[:12]}) — "
           f"재기동 필요")
    if state_path is not None:
        try:
            last_alerted = json.loads(state_path.read_text()).get("last_alerted_head")
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            last_alerted = None
        if last_alerted == current:
            return False, ""
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"last_alerted_head": current}))
    return False, msg


def watchdog_canonical_guard(module_path: Path = Path(__file__)) -> tuple[bool, str]:
    """워치독 자신의 파일 경로가 canonical 보드 체크아웃 밖(예:
    `~/.tokenmaxxxer/work/*` 역할 워크스페이스)이면 시작을 거부한다 (이슈
    #1456 요구 3, #1360 재발 원인 그 자체 — 역할 워크스페이스에서 뜬
    독립 워치독이 rearm 을 못 받았다). `SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1`
    로 테스트/운영 오버라이드."""
    override = os.environ.get("SPAWN_WATCHDOG_ALLOW_NONCANONICAL", "")
    if override not in ("", "0", "false", "no", "off"):
        return True, ""
    resolved = module_path.resolve()
    try:
        resolved.relative_to(_sp._workspace_base().resolve())
    except ValueError:
        return True, ""
    return False, (f"[watchdog] 비-canonical 체크아웃에서 시작 거부: "
                    f"{resolved} — SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 로 재정의")


STANDING_RED_STATE = ROOT / "runs" / "standing_red_state.json"
# 이슈 #1491: #1490 fast-tier 예산(<=300s)에 맞춰 고른, 유한 주기(분).
# 값 자체는 phase-1 프로포절이 phase-2로 미룬 튜닝 대상이다.
STANDING_RED_CADENCE_MIN = 15
_PYTEST_FAILED_RE = re.compile(r"^FAILED (\S+)")


def _standing_red_state_load(path: Path = STANDING_RED_STATE) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _standing_red_state_save(d: dict, path: Path = STANDING_RED_STATE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _standing_red_tree_hash(root: Path = ROOT) -> str | None:
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def _standing_red_load_contract(root: Path):
    """이슈 #1518 계약 파서를 재사용한다 — 이 체크 자신은 tier 선택/예산
    로직을 다시 만들지 않는다(#1491 프로포절 Constraints).

    #2141 rescope (per #2137 verify-at-landing): the contract is read for
    the PLUGIN'S OWN checkout only — the target-repo contract surface
    (select_tier/no_contract_gap and the "target repos declare
    test-tiers.json by default" framing) is retired. standing_red_check
    enforces the scope before calling this."""
    gates_dir = str(_sp.ROOT / "gates")
    if gates_dir not in sys.path:
        sys.path.insert(0, gates_dir)
    import test_tier_contract
    return test_tier_contract.load_contract(root)


def _standing_red_parse_failed_ids(output: str) -> set[str]:
    """pytest 요약의 `FAILED <test_id> ...` 줄에서 테스트 id 만 뽑는다.
    매칭 없는 출력(다른 러너, 크래시 등)은 빈 set — 새 실패로 오인해
    소음을 만들지 않는 fail-closed 파싱이다."""
    ids: set[str] = set()
    for line in output.splitlines():
        m = _sp._PYTEST_FAILED_RE.match(line.strip())
        if m:
            ids.add(m.group(1))
    return ids


def standing_red_check(state: dict | None = None, now: float | None = None,
                        root: Path = ROOT,
                        own_checkout: Path | None = None) -> list[str]:
    """이슈 #1491: main 위 fast tier(이슈 #1518 계약)를 유한 주기로 돌려,
    새로 red 가 된 테스트를 관찰만 하는(observe-only) 신호 목록으로
    돌려준다. 절대 스위트를 고치거나, 이슈를 파거나, 세션을 스폰하지
    않는다 — 기존 watchdog 철학(watchdog_check_one) 그대로.

    req 3(플레이크): 같은 tree_hash 에서 두 번 연속 실패해야 신호가
    나간다 — 단, 이 상태 파일 자체가 처음(=이전에 `standing_red` 키가
    없던) 이면 그 첫 스캔에서 현재 red 전부를 baseline 으로 즉시
    한 번 보고한다(이슈 acceptance 의 empty-state 요구).
    req 4(중복 억제): 이미 보고된 red 는 같은 tree_hash 에서 재보고하지
    않는다 — tree_hash 가 바뀌면 그 테스트의 카운터가 리셋되며 재무장된다.

    `state` 를 넘기면 그 dict 를 제자리에서 갱신하고 저장하지 않는다
    (테스트용). 생략하면 `runs/standing_red_state.json` 을 읽고 쓴다.

    #2141 rescope (per #2137): standing-red watches the PLUGIN'S OWN
    suite only — `root` must be the plugin checkout (`own_checkout`,
    default `_sp.ROOT`). A consumer-board watchdog tick (root = target
    repo) returns [] without reading any contract or running anything:
    the target-repo default-suite half of this machinery is retired.
    """
    own = _sp.ROOT if own_checkout is None else own_checkout
    try:
        in_scope = Path(root).resolve() == Path(own).resolve()
    except OSError:
        in_scope = False
    if not in_scope:
        return []
    now = time.time() if now is None else now
    own_state = state if state is not None else _sp._standing_red_state_load()

    last_run = own_state.get("last_run")
    if last_run is not None and (now - last_run) / 60 < _sp.STANDING_RED_CADENCE_MIN:
        return []
    own_state["last_run"] = now

    contract = _sp._standing_red_load_contract(root)
    if contract is None:
        # 계약 없이 조용히 전체 스위트를 돌리지 않는다 — 이번 틱은 신호
        # 없이 넘어간다. (#2141: the plugin's own checkout always ships
        # `.on-the-record/test-tiers.json`; this branch survives only as
        # the fail-quiet path for a corrupt/missing contract file.)
        if state is None:
            _sp._standing_red_state_save(own_state)
        return []

    is_empty_state = "standing_red" not in own_state
    standing_red = own_state.setdefault("standing_red", {})

    try:
        import shlex
        cmd = shlex.split(contract.fast_command)
        result = subprocess.run(cmd, cwd=str(root), capture_output=True,
                                 text=True, timeout=contract.budget_seconds)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired):
        # advisory — 러너 자체가 못 뜨거나 예산을 넘겨도 틱을 막지 않는다.
        if state is None:
            _sp._standing_red_state_save(own_state)
        return []

    failing_ids = _sp._standing_red_parse_failed_ids(output)
    tree_hash = _sp._standing_red_tree_hash(root)

    signals: list[str] = []
    for test_id in sorted(failing_ids):
        prev = standing_red.get(test_id)
        same_tree = bool(prev) and prev.get("tree_hash") == tree_hash
        consecutive = (prev.get("consecutive_count", 0) + 1) if same_tree else 1
        reported_before = bool(same_tree and prev.get("reported"))
        should_report = (not reported_before) and (is_empty_state or consecutive >= 2)
        standing_red[test_id] = {
            "tree_hash": tree_hash,
            "consecutive_count": consecutive,
            "reported": reported_before or should_report,
        }
        if should_report:
            signals.append(
                f"standing-red: {test_id} — 새 red, tree {(tree_hash or '?')[:8]}")

    # 더 이상 실패하지 않는 테스트는 상태에서 지운다 — 재발 시 처음부터
    # (empty-state 아님, 플레이크 규칙대로) 다시 카운트된다.
    for test_id in list(standing_red):
        if test_id not in failing_ids:
            del standing_red[test_id]

    if state is None:
        _sp._standing_red_state_save(own_state)
    return signals


def roster_watchdog(auto_respawn: bool = False, all_scope: bool = False,
                     root: Path = ROOT) -> int:
    """`spawn.py watchdog` — 살아있는 모든 역할 세션을 한 번 스캔해서 이상
    신호를 사람이 읽을 수 있게 출력한다. observe-only: 아무 것도 고치거나
    죽이지 않는다. 오케스트레이터가 10-15분 간격으로 반복 호출한다
    (이슈 #90 phase-2 프로포절).

    `auto_respawn=True` (이슈 #132): 죽은 로스터 엔트리도 스캔 대상에
    넣어(원래는 살아있는 것만 봤다) `session_end_verdict` 를 매겨, `crashed`
    에 한해서만 재스폰/상한-코멘트를 시도한다. `stalled` 는 여전히
    보고만 한다 — 아무 것도 고치거나 죽이지 않는다는 계약은 그대로다.

    반환값(이슈 #327): 이상 신호가 하나 이상 나온 로스터 엔트리 수 — 깨끗한
    스캔이면 0(기존과 동일), 아니면 0 초과. `spawn.py watchdog` CLI 가 이
    값을 그대로 프로세스 종료 코드로 쓴다(spawn.py:2445) — stdout 파싱 없이
    idle/deadlock/불필요한 작업이 있었는지 종료 코드만으로 알 수 있게 한다.
    `auto_respawn` 의 부작용(재스폰/상한-코멘트)은 이 변경과 무관 — 반환값만
    바뀐다.

    이슈 #1274: 이 rc 는 이상 신호 "개수"이지 크래시 플래그가 아니다 —
    poll-heartbeat.sh 등 호출부는 `rc != 0` 을 크래시로 오독하면 안 된다.
    진짜 크래시(watchdog 프로세스 자체가 죽었다는 뜻)는 이 함수의 반환값과
    별개의 두 경로로만 신호한다: (1) 시그널 사망 — 셸이 관측하는 종료
    코드가 128+N (예: SIGKILL=137, SIGSEGV=139); (2) `main()` 의 watchdog
    분기가 처리 못 한 예외를 잡아 `WATCHDOG_CRASH_SENTINEL`
    (spawn.py 정의, 현재 97) 로 종료하는 예약 코드 — 파이썬 기본
    트레이스백 종료(exit 1)를 그대로 두면 anomaly_count==1 과 구분이 안
    되므로 반드시 이 센티널을 거친다. 호출부는 `rc >= 128 or rc ==
    WATCHDOG_CRASH_SENTINEL` 일 때만 크래시로 표시해야 한다.

    이슈 #464: 로스터 스캔과 별도로, 매 틱마다 보드-전체(closure_sweep /
    spawn_coverage) 스윕도 한 번 돈다 — 로스터가 비어 있어도 건너뛰지
    않는다(로스터가 빈 상태에서 보드가 방치될 위험이 가장 크다). 위반/미커버
    이슈는 로스터 이상 신호와 같은 모양으로 출력되고 `anomaly_count`에
    합산된다. observe-only 계약은 그대로 — 아무것도 고치거나 닫지 않는다.

    이슈 #1219: `root` 는 이 워치독이 보는 보드다 — CLI 는 호출자의 `-C`
    (컨슈머 세션이면 타깃 프로젝트, dev 세션이면 이 체크아웃 자신)를 그대로
    넘긴다. 기본값 `ROOT`(spawn.py 자신의 체크아웃)는 CLI 를 거치지 않는
    직접 호출/테스트만을 위한 하위호환 폴백이다 — 워치독 코드(closure_sweep
    등 gates 모듈) 임포트는 항상 `ROOT` 를 쓰고(코드는 언제나 체크아웃에서
    온다), 보드 스캔 대상(이슈/PR/다이제스트)만 `root` 를 쓴다."""
    # 이슈 #1276: 로스터를 여기서 먼저 읽는다 — 보드 스윕이 로스터가
    # 가리키는 distinct 타깃 레포까지 커버해야 해서(요구#1), 로스터 스캔
    # 루프가 쓰는 `d_all` 과 같은 한 번의 읽기를 그대로 재사용한다.
    d_all = _sp._roster_load()
    anomaly_count = _sp._board_wide_sweep_all(root, d_all)
    # Issue #2101 mechanisms 3+4: level-triggered reconcile sweep (expired
    # leases requeued, claims without sessions and dangling declared waits
    # surfaced) + dead-man coverage marker check/refresh. Advisory-only;
    # requeued keys are popped from d_all so this tick's dead-entry loop
    # below does not re-report them.
    anomaly_count += _sp.lease_reconcile_sweep(root=root, d_all=d_all)
    # 이슈 #1491: standing-red 관찰은 살아있는 로스터와 무관하게 매 틱
    # 시도한다(자체 유한-주기 게이트로 실제 스위트 실행은 걸러낸다) —
    # 아래 `if not d` 조기 반환에 걸리지 않게 board-wide sweep 바로 뒤에
    # 둔다.
    for sr_signal in _sp.standing_red_check(root=root):
        anomaly_count += 1
        print(f"[standing-red] {sr_signal}")
    # 이슈 #1239: 워치독 틱마다 처분 안 된 issue-*/ PR 목록을 always-emit
    # 카테고리로 찍는다 — poll-heartbeat.sh 의 #1220 delta-suppression 이
    # `[returned-pr]` 태그 줄을 ALWAYS_RE 로 인식해 매 틱 살아남는다. 스폰
    # 시점뿐 아니라 매 60초 틱마다 방치를 보이게 하는 게 이 이슈의 요구다.
    blockers, ok = _sp._undispositioned_role_prs(root)
    if ok:
        _sp._print_returned_pr_surfaced(blockers, source="watchdog")
    # 이슈 #1013 block B: 자기 세션 소유(또는 소유 미기재=empty-state)
    # 엔트리로 스캔을 좁힌다. `--all` 이면 그대로 전체.
    d = _sp._roster_own(d_all, all_scope)
    if not all_scope:
        # 이슈 #1013 block D: 다른 세션 소유로 걸러진(own-scope 밖) 죽은
        # 엔트리는 관측-손실 방지를 위해 [orphaned] 로 계속 보고한다 —
        # 다만 own-scope 루프 밖이므로 아래의 `_auto_respawn_check()` 는
        # 결코 이들에 대해 불리지 않는다(다른 세션 소유 작업을 재스폰하지
        # 않는다).
        for key in sorted(set(d_all) - set(d)):
            e = d_all[key]
            if _sp._alive(e.get("pid", 0)):
                continue
            anomaly_count += 1
            print(f"[orphaned] {key}: session {e.get('session_id')} 소유, "
                  f"이 세션 소유 아님 — 재스폰하지 않음")
    if not d:
        print("돌고 있는 역할 세션 없음")
        if not anomaly_count:
            print("이상 신호 없음")
        return anomaly_count
    state = _sp._watchdog_state_load()
    respawn_state = _sp._respawn_state_load() if auto_respawn else {}
    issue_role_key = lambda e: (e.get("issue"), e.get("role"))
    # Issue #2103: one shared branch->PR index per poll tick, built lazily
    # from the cached board snapshot (delta read: 1 API call, usually) the
    # first time a dead entry needs a PR check — replaces the per-dead-entry
    # `gh pr list --head <branch>` calls (O(dead entries) per tick). None
    # (board unreadable) keeps the per-branch fallback inside
    # diagnose_health(), so failure behavior is unchanged.
    _poll_pr_index_cache: list = []

    def _poll_pr_index() -> dict | None:
        if not _poll_pr_index_cache:
            _poll_pr_index_cache.append(_sp._board_pr_index(root))
        return _poll_pr_index_cache[0]
    for key, e in sorted(d.items()):
        # 이슈 #492: 같은 틱에서 reconcile() 도 한 번 태운다 — 새 폴러가
        # 아니라 이 기존 스캔에 올라탄다(ADR 결정 4).
        divergences = _sp.reconcile(_sp._build_expected(e), _sp._build_observed(root, e),
                                 recovery_state_dir=root / ".on-the-record" / "recovery-state")
        if divergences:
            issue_n, role_n = issue_role_key(e)
            for div in divergences:
                dedup_key = f"health-repair:{issue_n}:{role_n}:{div['kind']}"
                if not _sp.ledger_check_and_stamp(dedup_key):
                    continue  # 이슈 #782: 이미 같은 TTL 창에서 보고됨 — 조용히
                anomaly_count += 1
                print(f"[reconcile] {key}: divergence — "
                      f"{div['kind']}: {div['detail']} -> {div['next_action']}")
        if not _sp._alive(e.get("pid", 0)):
            work = e.get("work")
            issue_n = e.get("issue")
            if work and issue_n is not None:
                # 이슈 #534: self-trigger 가 놓친(프로세스가 그 줄에 닿기 전에
                # 죽는 등) dead-but-registered 엔트리를 best-effort 로 잡는다
                # — 주 경로는 _spawn_one() 의 self-trigger 다, 이 틱이 아니다.
                _sp._post_session_end_comment(root, issue_n, key, work, e.get("log", ""))
            # 이슈 #782 스코프-확장(operator, 2026-08-11): 폴링 틱마다 세션별
            # 상태 한 줄을 찍는다. diagnose_health() 는 죽은 엔트리에 한해
            # `_pr_open_or_merged_for_branch()`(gh pr list)를 새로 부르므로,
            # 원장(TTL=RECONCILE_LEDGER_TTL_SEC)으로 그 비싼 재확인 빈도를
            # 60초 폴 간격과 분리한다 — dedup 은 반복 escalation 소음만
            # 거른다는 계약은 그대로, 여기서 걸러지는 건 gh 호출 자체다
            # (경보 전 hunt: dead-registered 엔트리가 15배 빈도로 gh 를
            # 때리는 문제).
            if _sp.ledger_check_and_stamp(f"poll-report-dead-check:{key}"):
                # Issue #2103: serve the dead-entry PR check from the shared
                # per-tick index (snapshot/delta) instead of a fresh
                # `gh pr list` per entry.
                dead_health = _sp.diagnose_health(key, e, state=state, root=root,
                                              pr_index=_poll_pr_index())
                state[f"{key}:dead_report"] = dead_health
            dead_health = state.get(f"{key}:dead_report")
            if dead_health is not None:
                dead_label = "COMPLETED" if dead_health["state"] is None else dead_health["state"]
                print(f"[poll-report] {key}: {dead_label} — {dead_health['detail']}")
                if dead_health["state"] is None:
                    # 이슈 #878 케이스 2: 완료(PR 존재) 이면서 이 엔트리를
                    # 무장한 오케스트레이터가 headless(session_id 있음) 였다면
                    # 여기서 --resume 을 쏜다 — 인터랙티브 케이스 1 은
                    # 라이브 notify 로 이미 처리되므로 session_id 없는 엔트리는
                    # 그대로 통과한다(중복 트리거 없음).
                    branch = Path(work).name if work else None
                    # Issue #2103: same shared index; per-branch `gh pr list`
                    # only as fallback when the board is unreadable.
                    tick_index = _poll_pr_index() if branch else None
                    if branch and tick_index is not None:
                        pr_number = _sp._pr_state_from_index(tick_index, branch)
                    else:
                        pr_number = _sp._pr_open_or_merged_for_branch(root, branch) if branch else None
                    if pr_number is not None and _sp._maybe_resume_for_ready_pr(key, e, pr_number):
                        print(f"[resume] {key}: PR #{pr_number} ready — "
                              f"resumed session {e.get('session_id')}")
            if auto_respawn:
                _sp._auto_respawn_check(key, e, respawn_state)
            continue
        anomalies = _sp.watchdog_check_one(key, e, state=state)
        # Issue #2101 mechanisms 1+2: renew this live entry's lease on the
        # same tick (the tick is the entry's watcher), recording the progress
        # indicator; a flat-progress anomaly (advisory) joins the same list
        # diagnose_health consumes. Persist the mutated lease fields.
        anomalies += _sp.lease_renew(key, e, root=root)
        _sp.roster_register(key, e)
        # 이슈 #782 스코프-확장: HEALTHY/STALLED/DEADLOCKED/DEAD-ERRORED 네
        # 상태로 진단하고, 완료가 아닌 진단 결과만 원장으로 게이팅해 보고한다
        # (완료는 위 reconcile()/아래 죽음-분기가 이미 다룬다). 같은 틱에서
        # 이미 계산한 anomalies 를 넘겨 watchdog_check_one() 의 오프셋
        # 소비를 두 번 겪지 않는다.
        health = _sp.diagnose_health(key, e, state=state, anomalies=anomalies, root=root)
        # 이슈 #782 스코프-확장: dedup 원장과 무관하게 매 틱 상태를 보고한다.
        print(f"[poll-report] {key}: {health['state']} — {health['detail']}")
        if health["state"] is not None and health["state"] != "HEALTHY":
            issue_n, role_n = issue_role_key(e)
            dedup_key = f"health:{issue_n}:{role_n}:{health['state']}"
            if _sp.ledger_check_and_stamp(dedup_key):
                anomaly_count += 1
                print(f"[health] {key}: {health['state']} — "
                      f"{health['detail']} -> {health['next_action']}")
        if anomalies:
            anomaly_count += 1
            print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건")
            for a in anomalies:
                print(f"  - {a}")
        else:
            print(f"[watchdog] {key}: 정상")
    _sp._watchdog_state_save(state)
    if not anomaly_count:
        print("이상 신호 없음")
    return anomaly_count

