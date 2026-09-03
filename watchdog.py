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

import checkpoint

# The spawn module object; set by spawn.py on import. All cross-module lookups
# resolve through it at call time so monkeypatches on spawn attributes are seen.
_sp = None

# Import-time anchors — same expressions as spawn.py (same directory, same
# env), needed here because they feed default-argument values below.
ROOT = Path(__file__).resolve().parent
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")

sys.path.insert(0, str(ROOT / "gates"))
import state_paths  # noqa: E402


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
WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD = 3  # 이슈 #2196: 단발 gh 실패는 억제, N틱 연속이면 경보
FLAPPING_WINDOW_SEC = 15 * 60  # 이슈 #2969: A->B->A 왕복이 이 창 안에서 일어나면 flapping


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


def _session_tick_lines(key: str, entry: dict, state: dict | None,
                         verdict: str | None) -> list[str]:
    """One session's raw activity for this tick (#3293 stage 2).

    Reuses the workspace-scan timestamp `_session_progress_state()` already
    stamped into `state`, so the window shown is exactly the window the
    verdict was computed over -- a second, independently-derived window
    would let the files listed and the verdict disagree.

    Any failure returns no lines. The `[poll-report]` line above has already
    printed, so a broken payload costs detail, never the tick itself.
    """
    try:
        sys.path.insert(0, str(ROOT / "gates"))
        import tick_payload  # noqa: PLC0415
        import session_progress  # noqa: PLC0415
    except Exception:
        return []
    since = None
    if state is not None:
        since = state.get(f"{key}:last_workspace_scan_ts")
    if since is None:
        since = time.time() - POLL_INTERVAL_SEC
    calls = []
    log = entry.get("log")
    if log:
        # `recent_tool_calls()` returns (tool_name, command) tuples; reading
        # them as dicts is what made the first live tick of this payload say
        # "calls: none readable" for a session that had made calls. The
        # narrower `except` below is deliberate -- a broad one turned that
        # type error into a plausible-looking empty result, which is the
        # exact failure shape this payload exists to stop hiding.
        try:
            calls = list(session_progress.recent_tool_calls(
                Path(log), tick_payload.MAX_CALLS_PER_SESSION * 2))
        except (OSError, ValueError):
            calls = []
    try:
        return tick_payload.session_block(key, entry, since,
                                          verdict or "UNKNOWN", calls)
    except Exception:
        return []


def _idle_tick_lines(root: Path) -> list[str]:
    """The outstanding-work summary an empty-roster tick carries (#3293).

    Reads only what is already cached for this tick -- no new `gh` calls, no
    new polling loop. A lookup that fails contributes nothing rather than a
    guess, and the caller's own empty-state line still reaches the
    orchestrator either way.
    """
    try:
        sys.path.insert(0, str(ROOT / "gates"))
        import tick_payload  # noqa: PLC0415
    except Exception:
        return []
    outstanding: dict[str, list] = {}
    try:
        board, _meta = _board_read(root)
    except Exception:
        board = None
    if isinstance(board, dict):
        try:
            prs = [str(k) for k in (_board_pr_index(root) or {})]
            if prs:
                outstanding["open PRs"] = prs
        except Exception:
            pass
    try:
        return tick_payload.idle_block(outstanding)
    except Exception:
        return []


def _session_progress_state(key: str, entry: dict, state: dict | None) -> str:
    """`gates/session_progress.py` wrapper (issue #3275).

    Feeds the classifier all three signals rather than one. Log growth alone
    says a session is breathing; it took the workspace and the tool history
    to tell breathing from advancing:

    - the workspace, compared against the timestamp of the last tick that
      looked at it (`state`), with the harness's own writes excluded so a
      live session does not look busy on `.on-the-record/` churn -- that
      exclusion is what makes mtime usable here despite
      `_confirmed_progress_seen()`'s reasons for refusing it outright;
    - the recent tool calls, so a session polling `ps` in a loop is WAITING;
    - and, when the workspace answer is unavailable, neither is guessed.

    Lazy-imported the same way every other root -> gates crossing in this
    file is (`gates/spawn_on_pr.py` imports `spawn` at its own top level, so
    a module-load import here would close a cycle). Any failure to load or
    classify returns UNKNOWN -- this signal must never be the reason a
    healthy session gets reported as idle.
    """
    try:
        sys.path.insert(0, str(ROOT / "gates"))
        import session_progress  # noqa: PLC0415
    except Exception:
        return "UNKNOWN"
    log = entry.get("log")
    work = entry.get("work")
    changed = None
    if state is not None and work:
        seen_key = f"{key}:last_workspace_scan_ts"
        prev_ts = state.get(seen_key)
        state[seen_key] = time.time()
        if prev_ts is not None:
            try:
                changed = session_progress.workspace_touched_since(
                    Path(work), prev_ts)
            except Exception:
                changed = None
    try:
        return session_progress.classify(Path(log) if log else None,
                                          workspace_changed=changed)
    except Exception:
        return "UNKNOWN"


def _live_session_workspace_summary(work: str) -> str:
    """이슈 #2904 (재구성, 2026-08-31 이슈 코멘트): `gh`는 세션이 PR을 열어야
    비로소 그 존재를 본다 — 커밋도 PR도 없는 15분짜리 진행 중 세션은 `gh`
    로는 완전히 안 보인다. 워크스페이스는 그 순간부터 보인다: 로컬
    `git status --porcelain` 하나로 지금 손대는 파일과 기록(record) 시작
    여부를 매 틱 보고한다 — 새 `gh` 호출 없음, 새 폴링 루프 없음(이미 도는
    이 watchdog 틱에 얹는다). 아무 것도 안 건드린 세션도 "아직 없음"을
    보고한다 — 침묵이 아니라 명시적 빈 상태(이슈가 요구하는 empty-state
    계약)."""
    # `-uall`: a brand-new record file lives under a directory
    # (`docs/issue-<n>/reports/`) that does not exist yet on any tracked
    # branch -- plain `--porcelain` collapses a wholly-untracked directory
    # to one `?? docs/` line, which would hide exactly the "record
    # started" case this function exists to name.
    st = subprocess.run(["git", "-C", work, "status", "--porcelain", "-uall"],
                        capture_output=True, text=True)
    if st.returncode != 0:
        return "워크스페이스 상태 확인 실패(git status)"
    lines = [l for l in st.stdout.splitlines() if l.strip()]
    if not lines:
        return "손댄 파일 없음"
    paths = []
    record_started = False
    for line in lines:
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path)
        if _sp._RECORD_PATH_RE.search(path):
            record_started = True
    paths.sort()
    shown = ", ".join(paths[:5])
    more = f" (+{len(paths) - 5}개 더)" if len(paths) > 5 else ""
    record_note = "기록 시작함" if record_started else "기록 아직 없음"
    return f"손댄 파일 {len(paths)}건: {shown}{more}, {record_note}"


def _last_tool_activity_summary(log_path: Path | None) -> str:
    """이슈 #2904 (재구성 2차, 2026-08-31 두 번째 코멘트): 파일 diff는
    결과고 도구 호출은 행위다 — 이미 dirty 한 파일이 그대로 dirty 인 채로
    2분이 흘렀을 때, 그 2분이 grep/Read/Edit/테스트 실행으로 채워졌는지
    (투자 중) 아무 것도 안 했는지(정지)는 파일 상태만으로는 구별되지
    않는다(위 `_live_session_workspace_summary()`가 겪는 바로 그 반례,
    운영자가 이 세션 자신에게 실측했다). 그 구별은 세션 자신의
    트랜스크립트(`entry["log"]`, `watchdog_check_one()`이 이미 오프셋
    증분으로 읽는 바로 그 파일)에만 있다 — 이 함수는 그 로그의 마지막
    tool_use 이름과 절대 타임스탬프(HH:MM:SS UTC)를 읽는다. 새 이벤트를
    쓰지 않는다, 세션이 이미 쓰는 로그를 읽을 뿐이다.

    절대 타임스탬프를 쓰는 이유: "N초 전" 같은 상대 표현은 마지막 도구
    호출이 전혀 안 바뀌어도 틱마다 문자열이 달라져 delta-suppression을
    무력화한다(조용한 틱이 조용히 안 있게 된다) — 마지막 도구가 그대로면
    절대 타임스탬프도 그대로라 문자열이 안 바뀌고, 새 도구 호출이 있어야만
    바뀐다."""
    if log_path is None or not log_path.exists():
        return "도구 호출 로그 없음"
    try:
        size = log_path.stat().st_size
        with log_path.open("rb") as fh:
            fh.seek(max(0, size - 65536))
            raw = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return "도구 호출 로그 읽기 실패"
    last_tool = None
    last_ts = None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if not isinstance(obj, dict) or obj.get("type") != "assistant":
            continue
        ts_raw = obj.get("timestamp")
        ts = None
        if isinstance(ts_raw, str):
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).timestamp()
            except ValueError:
                ts = None
        for block in (obj.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if not name:
                continue
            inp = block.get("input") or {}
            detail = inp.get("file_path") or inp.get("command") or inp.get("pattern") or ""
            if isinstance(detail, str) and detail:
                detail = detail.strip().splitlines()[0][:40]
            else:
                detail = ""
            last_tool = f"{name} {detail}".strip()
            if ts is not None:
                last_ts = ts
    if last_tool is None:
        return "도구 호출 기록 없음"
    if last_ts is not None:
        stamp = datetime.fromtimestamp(last_ts, tz=timezone.utc).strftime("%H:%M:%S")
        return f"마지막 도구 호출: {last_tool} ({stamp} UTC)"
    return f"마지막 도구 호출: {last_tool}"


def _confirmed_progress_seen(key: str, entry: dict, state: dict | None) -> bool:
    """이슈 #2969: HEALTHY 를 "확인된 진행"과 "이상 신호 없음(미확인)"으로
    가른다 — mtime 은 워크스페이스 보존 커밋 같은 무관한 이유로도 움직일
    수 있어(이 이슈의 field report 가 제기한, 아직 미확정인 바로 그
    가설) 쓰지 않는다. 대신 세션 로그 파일의 실제 바이트 크기가 지난
    관측 이후 늘었는지를 틱 사이에 저장해 비교한다 — 로그가 없거나
    (`entry["log"]` 미기재) 이 함수를 가로지르는 상태 저장소가 없으면
    (`state=None`, 단발 호출) 진행을 확인할 방법이 없으므로 항상
    미확인으로 취급한다(추측하지 않는다)."""
    if state is None:
        return False
    log = entry.get("log")
    if not log:
        return False
    log_path = Path(log)
    try:
        cur_size = log_path.stat().st_size
    except OSError:
        return False
    size_key = f"{key}:last_seen_log_size"
    prev_size = state.get(size_key)
    state[size_key] = cur_size
    return prev_size is not None and cur_size > prev_size


def _record_verdict_and_check_flapping(key: str, verdict_state: str, now: float,
                                        state: dict | None) -> bool:
    """이슈 #2969: 짧은 창 안에서 A -> B -> A 로 왕복하는 verdict 는 그
    자체로 결함 신호다(FLAPPING) — 두 독립된 보고가 조용히 지나가게 두지
    않는다. `key`당 최근 3개 `(verdict_state, ts)` 만 남겨 셋째가 첫째와
    같고 둘째와는 달라야(진짜 왕복) 하고, "짧은 창"은 B 로 떠난 시점부터
    다시 A 로 돌아온 시점까지(둘째~셋째 관측 간격)로 잰다 — 첫 관측
    시점까지 포함해 재면 A 에 오래 머문 뒤 잠깐 흔들린 경우도 "왕복 폭"과
    무관하게 창을 넘겨버린다. 안정된(전환이 없거나 관측이 3회 미만인)
    이력은 항상 False — empty-state 는 조용히 통과한다. `state=None`
    (단발 호출)이면 이력을 남길 곳이 없으니 판정하지 않는다."""
    if state is None:
        return False
    hist_key = f"{key}:verdict_history"
    history = state.get(hist_key, [])
    history = history + [(verdict_state, now)]
    history = history[-3:]
    state[hist_key] = history
    if len(history) < 3:
        return False
    (s1, _t1), (s2, t2), (s3, t3) = history
    return s1 == s3 and s1 != s2 and (t3 - t2) <= FLAPPING_WINDOW_SEC


def diagnose_health(key: str, entry: dict, root: Path = ROOT,
                     now: float | None = None, state: dict | None = None,
                     anomalies: list[str] | None = None,
                     pr_index: dict | None = None,
                     commit_count: int | str | None = None,
                     confirm_pr_missing=None) -> dict:
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
    `_pr_open_or_merged_for_branch()` 개별 `gh pr list` 로 되돌아간다.

    `commit_count`(이슈 #2193, 이슈 #2795 로 원격-인지로 교체): 죽었는데
    완료가 아닌(PR 없음) 엔트리에 한해, 호출부가 이미 계산해 둔 "원격에
    아직 없는 커밋 개수"(예: `_sp._unrecovered_commit_count(work,
    entry.get("before_head"), _sp._git_head(work), branch)`) 를 넘기면
    셋 중 하나로 갈린다: 양의 정수 → `DEAD-UNRECOVERED-COMMITS`(진짜
    좌초), `_sp.UNPUSHED_STATUS_UNKNOWN` → `DEAD-REMOTE-STATE-UNKNOWN`
    (원격 상태 확인 불가 — healthy 로도 stranded 로도 읽지 않는다,
    이슈 #2792 와 같은 모양의 세 번째 상태), 그 외(0 또는 `None`, 기본값)
    → `DEAD-ERRORED`. 이 함수 자신은 그 값을 구하려고 새 `git` 호출
    타입을 추가하지 않는다(위 원자료 제약 그대로), 호출부가 이미 쓰는
    (before_head, HEAD, branch) 랜드마크 위에서 계산해 건네주는 형태다.
    생략하면(기본값 `None`, 기존 호출부) 이전과 동일하게 `DEAD-ERRORED`
    하나로만 갈린다 — 순수 추가라 기존 동작은 안 바뀐다.

    이슈 #2215: `work` 가 있으면 매 판정에 `dirty_files`(raw `git status
    --porcelain` 개수)와 `minutes_since_checkpoint`(마지막 체크포인트 ref
    커밋 이후 경과 분, ref 가 아직 없으면 `None`)를 얹는다 —
    `checkpoint.checkpoint_health()` 위임, 이 함수 자신은 새 `git` 호출을
    추가하지 않는다. 어느 분기로 빠지든(completion 포함) 이 두 필드는
    항상 붙는다 — 호출부가 균일한 shape 을 기대할 수 있게.

    `confirm_pr_missing`(이슈 #2941 finding 1): `pr_index`에서 이 브랜치의
    PR 이 안 보여 DEAD-* 로 확정하기 직전에만 불리는 0-인자 콜백 — 호출부가
    "오늘 이 틱의 `pr_index`가 search-API 인 delta read 출처였으면 직접
    connection 쿼리인 full read 로 한 번 더 확인한다"를 구현해 넘긴다
    (`roster_watchdog()`의 `_poll_pr_index_confirm_gone`). 콜백이 PR 번호를
    돌려주면 completion 으로 되돌아간다 — 인덱스가 아직 못 따라잡았을 뿐인
    걸 DEAD-ERRORED/respawn 으로 조용히 확정하지 않는다. 생략하면(기본값
    `None`, 기존 호출부) 이전과 동일하게 `pr_index`의 첫 답을 그대로
    믿는다 — 순수 추가라 기존 동작은 안 바뀐다."""
    now = time.time() if now is None else now
    pid = entry.get("pid", 0)
    work = entry.get("work")
    # Issue #2834: the real checked-out git branch, not the workspace
    # directory's basename — `issue_workspace()` names the directory
    # `<repo>-issue-<n>-<skill>` (dashes, filesystem-safe) while the git
    # branch is `issue-<n>/<skill>` (slash). Using the directory name as
    # the PR-completion lookup key below made every lookup miss every real
    # branch, so a session that actually finished and opened its PR was
    # reported as DEAD-ERRORED. Same primitive PR #2824 (issue #2795)
    # already switched to at board.py's two `_unrecovered_commit_count()`
    # call sites, for the identical reason.
    branch = _sp._current_branch(Path(work)) if work else None
    ckpt_fields = (checkpoint.checkpoint_health(work, now=now) if work
                   else {"dirty_files": 0, "minutes_since_checkpoint": None})
    # Issue #2293: a no-`--issue` (adhoc) roster entry's watchdog line must
    # say `adhoc` prominently -- otherwise the always-printed
    # `[poll-report]` HEALTHY line reads exactly like a normal issue-N
    # spawn's, which is how the consumer's diagnosis cycle burned real
    # time on a degenerate-task session that looked fine. Every diagnosis
    # this function returns goes through `_diagnosis()`, so tagging here
    # covers HEALTHY/STALLED/DEADLOCKED/DEAD-*/completion uniformly.
    adhoc_prefix = None
    if entry.get("issue") is None:
        task_hint = (entry.get("task") or "").strip()[:60]
        adhoc_prefix = (f'ADHOC task="{task_hint}"' if task_hint
                        else "ADHOC (no task recorded)")

    def _diagnosis(d: dict) -> dict:
        merged = {**d, **ckpt_fields}
        if adhoc_prefix and merged.get("detail"):
            merged["detail"] = f"{adhoc_prefix} — {merged['detail']}"
        if merged.get("state") is not None:
            # 이슈 #2969: 완료(state=None)는 verdict 가 아니라 관측 종료라
            # flapping 이력에 안 얹는다 — 종료 뒤 재사용된 키가 엉뚱한
            # 이전 세대의 이력과 섞이는 걸 막는다.
            merged["flapping"] = _record_verdict_and_check_flapping(
                key, merged["state"], now, state)
        return merged

    # 이슈 #2969: pid 가 살아있다는 사실만으로 "확인된 생존"을 주장하지
    # 않는다 — 등록 시점의 `start_time` 과 짝지어 재확인하고(`_paired_liveness`),
    # 짝짓기 자체를 세울 수 없으면(구 엔트리, 또는 `/proc` 없는 macOS —
    # 이슈 #2924) HEALTHY 로도 DEAD 로도 확정하지 않는 별도 상태로 멈춘다
    # — 이쪽이든 저쪽이든 추측하면 이 이슈가 고치려는 결함을 반복한다.
    liveness = _paired_liveness(pid, entry.get("start_time"))
    if liveness == "unconfirmed":
        return _diagnosis({"state": "LIVENESS-UNCONFIRMED", "next_action": "resume-watch",
                "detail": f"{key}: pid {pid} 살아있으나 시작시각 짝짓기를 세울 수 "
                          f"없음(시작시각 미기록 또는 /proc 부재) — 생존을 확인도 "
                          f"반증도 못함, HEALTHY 로도 DEAD 로도 확정하지 않음"})
    if liveness == "dead":
        # 이슈 #2874: wrapper_pid 를 넘겨 reconcile()/`_auto_respawn_check()`
        # 와 같은 신호로 판정한다 — 지금까지는 이 함수만 `pr_number` 로
        # 같은 후처리-꼬리 구간을 우회해 왔고(아래), reconcile 쪽엔 그 우회가
        # 없어 두 계통이 갈렸다(이슈 #2874 실측). PR 이 아직 없는 죽음에서도
        # 같은 구간을 같은 이유로 놓치지 않도록 두 신호를 함께 쓴다.
        verdict = _sp.session_end_verdict(
            work, Path(entry["log"]) if entry.get("log") else None, now=now,
            wrapper_pid=entry.get("wrapper_pid")) \
            if work else None
        if branch is None:
            pr_number = None
        elif pr_index is not None:
            pr_number = _sp._pr_state_from_index(pr_index, branch)
            if pr_number is None and confirm_pr_missing is not None:
                # 이슈 #2941 finding 1: 인덱스가 "없음"이라 말했다고 바로
                # DEAD-* 로 확정하지 않는다 — 위 docstring 참고.
                pr_number = confirm_pr_missing()
        else:
            pr_number = _sp._pr_open_or_merged_for_branch(root, branch)
        # 이슈 #2874: 이 함수의 `alive`(자식 pid)가 이미 죽었다고 본 뒤라,
        # `session_end_verdict()` 는 여기서 절대 "alive_fn(pid) 살아있음"
        # 갈래로 못 간다 — `wrapper_pid` 경유로만 나오는 `in-progress` 는
        # 항상 이 죽음-후처리-꼬리(위 주석)를 뜻하지, 세션이 실제로 아직
        # 실행 중이라는 뜻이 아니다. `normal`(이미 확정)과 나란히 "지금은
        # 알람 아님"으로 다룬다 — PR/커밋 유무와 무관하게, wrapper 가
        # 살아서 그 후처리를 마치는 중이라는 사실 자체가 "안 죽었다"의
        # 증거이기 때문이다.
        if verdict in ("normal", "in-progress") or pr_number is not None:
            return _diagnosis({"state": None, "next_action": "none",
                    "detail": "completion, not a health diagnosis"})
        if commit_count == _sp.UNPUSHED_STATUS_UNKNOWN:
            # 이슈 #2795: 원격 상태를 확인하지 못했다(ls-remote 실패,
            # 또는 원격 SHA 가 로컬에 없어 조상 관계를 못 따짐) — 이걸
            # HEALTHY/DEAD-ERRORED 로 fail-open 하면(=알람 없음) 진짜
            # 좌초가 조용히 넘어가고, DEAD-UNRECOVERED-COMMITS 로
            # fail-closed 하면(=알람) 이 이슈가 고치려는 바로 그 오탐을
            # 반복한다 — 그래서 "모른다"를 그 자체로 보고하는 세 번째
            # 상태를 쓴다(이슈 #2792 의 성공-플래그+데이터-없음 모양을
            # 되풀이하지 않는다).
            return _diagnosis({"state": "DEAD-REMOTE-STATE-UNKNOWN",
                    "next_action": "manual-review",
                    "detail": f"{key}: pid {pid} 부재, PR 없음, "
                              f"branch={branch} 의 원격 push 상태를 확인 "
                              f"못함(ls-remote 실패 또는 조상 관계 판단 "
                              f"불가) — 수동 확인 필요 "
                              f"(session_verdict={verdict!r})"})
        if commit_count:
            # 이슈 #2193: 죽었고 PR 도 없지만 커밋은 남았다 — plugin
            # reload 등으로 워처 자신이 함께 죽어 `ensure_pushed()` 가
            # 못 돈 경우의 대표 실패 모드. 일반 DEAD-ERRORED("respawn 해도
            # 잃을 것 없음")와 섞으면 이 커밋들이 침묵 속에 좌초한다 —
            # 브랜치명과 커밋 개수를 이름 붙여 별도 상태로 갈라낸다.
            # 이슈 #2795: 이 커밋 개수는 이제 원격에 실제로 없는 커밋만
            # 센 값이다(`_unrecovered_commit_count()`) — 이미 push 된
            # 커밋은 여기 도달하지 않는다(위 == 0 이면 아래 DEAD-ERRORED
            # 로 빠진다).
            return _diagnosis({"state": "DEAD-UNRECOVERED-COMMITS",
                    "next_action": "recover-unpushed",
                    "detail": f"{key}: pid {pid} 부재, PR 없음, "
                              f"branch={branch} 에 push 안 된 커밋 "
                              f"{commit_count}개 — 복구 필요 "
                              f"(session_verdict={verdict!r})"})
        return _diagnosis({"state": "DEAD-ERRORED", "next_action": "respawn",
                "detail": f"{key}: pid {pid} 부재, PR 없음, 커밋 없음, "
                          f"session_verdict={verdict!r}"})
    deadlock_sig = _sp._deadlock_signature(work)
    if deadlock_sig is not None:
        return _diagnosis({"state": "DEADLOCKED", "next_action": "surface-repeating-cause",
                "detail": f"{key}: 같은 거부 signature 반복, 새 진행 없음 — {deadlock_sig[:200]}"})
    if anomalies is None:
        anomalies = _sp.watchdog_check_one(key, entry, now=now, state=state)
    if any(a.startswith("log-silence") or a.startswith("watcher-silent")
           for a in anomalies):
        return _diagnosis({"state": "STALLED", "next_action": "resume-watch",
                "detail": f"{key}: idle > {_sp.WATCHDOG_SILENCE_MIN}분, RUNNING"})
    if any(a.startswith("heartbeat-only-growth") for a in anomalies):
        # 이슈 #1966: log-silence 는 안 잡히지만(mtime 계속 갱신) 최근
        # WATCHDOG_HEARTBEAT_ONLY_MIN 분간 tool_progress 하트비트만 관측된
        # 경우 — advisory 전용 서브상태. next_action 은 STALLED 와 동일하게
        # "resume-watch"(재관찰만) 로, kill/spawn-거부/게이트-블록 경로는
        # 이 상태에서 전혀 도달 불가하다.
        return _diagnosis({"state": "STALLED-HEARTBEAT-ONLY", "next_action": "resume-watch",
                "detail": f"{key}: 최근 {_sp.WATCHDOG_HEARTBEAT_ONLY_MIN}분간 "
                          f"tool_progress 하트비트만 관측, RUNNING (advisory)"})
    if any(a.startswith("flat-progress") for a in anomalies):
        # Issue #2101 mechanism 2: the lease was renewed
        # LEASE_FLAT_RENEWALS_K+ times with an unchanged progress indicator
        # and no valid declared wait exempted it — advisory-only sub-state
        # in the #1966 classifier vocabulary. next_action is the same
        # "resume-watch" (re-observe only); no kill/refuse/gate-block path
        # is reachable from this state.
        return _diagnosis({"state": "STALLED-FLAT-PROGRESS", "next_action": "resume-watch",
                "detail": f"{key}: lease renewed {_sp.LEASE_FLAT_RENEWALS_K}+ "
                          f"times with a flat progress indicator, RUNNING "
                          f"(advisory)"})
    workspace_summary = _live_session_workspace_summary(work) if work else "워크스페이스 없음"
    activity_summary = _last_tool_activity_summary(
        Path(entry["log"]) if entry.get("log") else None)
    # 이슈 #2969: 여기 도달했다는 건 위의 모든 anomaly 검사가 안 걸렸다는
    # 뜻뿐이다 — "확인했더니 성장했다"와 "아무것도 확인 안 했다"를 같은
    # 문장으로 찍던 게 이 이슈의 결함이다. `_confirmed_progress_seen()`
    # 은 로그 파일의 실제 바이트 크기가 지난 관측 이후 늘었는지만 본다
    # (워크스페이스 mtime 은 안 쓴다 — field report 의 미확정 가설과
    # 얽히지 않으려는 의도적 선택). 늘었으면 확인된 진행, 아니면(로그가
    # 없거나, 크기 변화가 없거나, 첫 관측이라 비교 기준이 없거나) 성장을
    # 주장하지 않는다 — "이상 신호는 없지만 확인도 안 됐다"를 그대로
    # 찍는다.
    if _confirmed_progress_seen(key, entry, state):
        # Issue #3275: log growth answers "is it breathing", not "is it
        # getting anywhere". A session waiting on a background dispatch
        # polls it in a loop and grows its log forever while producing
        # nothing -- and used to score HEALTHY-CONFIRMED the whole time.
        # `session_progress.classify()` reads the tool calls behind that
        # growth: all-observation means WAITING, a third state that is
        # reported and never counted as healthy progress. It answers
        # UNKNOWN rather than WAITING whenever it cannot prove idleness,
        # so a working session is never mislabelled idle.
        progress = _session_progress_state(key, entry, state)
        if progress == "WAITING":
            return _diagnosis({"state": "WAITING-ON-DISPATCH",
                    "next_action": "none",
                    "detail": f"{key}: 로그는 자라지만 최근 도구 호출이 전부 "
                              f"관측 전용이다 — 살아있으나 진행 없음(대기), "
                              f"RUNNING — {workspace_summary}; "
                              f"{activity_summary}"})
        return _diagnosis({"state": "HEALTHY-CONFIRMED", "next_action": "none",
                "detail": f"{key}: 로그 성장 확인됨, RUNNING — "
                          f"{workspace_summary}; {activity_summary}"})
    return _diagnosis({"state": "HEALTHY-UNCONFIRMED", "next_action": "none",
            "detail": f"{key}: 이상 신호 없음(로그 성장은 확인되지 않음), RUNNING — "
                      f"{workspace_summary}; {activity_summary}"})


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
    """이슈 #878: 죽은(=세션이 끝난) roster 엔트리가 PR 을 남겼을 때,
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
    """issue #2240: orchestrator cross-tick memory, not target-repo state —
    anchored via state_paths, never `root`. `root` is accepted for
    call-site symmetry with the rest of this module's `root`-scoped
    helpers; it is not used here."""
    return state_paths.orchestrator_state_path("requirement_drift_cache.json")


def _drift_cache_key(repo: str, number: int) -> str:
    """issue #3081: the cache is one orchestrator-scoped file shared across
    every repo the orchestrator sweeps (issue #2240 -- that sharing is
    correct and stays). What was missing is a repo dimension on each entry:
    a flat `str(number)` key collides across repos (two repos can both have
    a PR #3048) and, even without a literal collision, carried no way for a
    reader to tell whose entry it was. Keying by `repo:number` makes each
    entry self-scoping -- a lookup for one repo's number can never resolve
    to another repo's entry."""
    return f"{repo}:{number}"


def _load_requirement_drift_cache(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    data = data if isinstance(data, dict) else {}
    # issue #3081: entries written before this repo dimension existed carry
    # no `repo` key at all (a checkout with no resolvable `gh` slug still
    # gets one, `"repo": None` -- that is a legitimate, if degenerate,
    # attribution and must survive this filter). An entry with no `repo`
    # key cannot be retroactively attributed and keeps matching every
    # repo's lookups, which is exactly the leak this fix closes, so it is
    # dropped here rather than ridden along as unrecognized state forever.
    return {k: v for k, v in data.items() if isinstance(v, dict) and "repo" in v}


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


def _watchdog_noise_state_path(root: Path) -> Path:
    """issue #2240: orchestrator cross-tick memory, not target-repo state —
    anchored via state_paths, never `root`. `root` is accepted for
    call-site symmetry with the rest of this module's `root`-scoped
    helpers; it is not used here."""
    return state_paths.orchestrator_state_path("watchdog_noise_state.json")


def _load_watchdog_noise_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_watchdog_noise_state(path: Path, data: dict) -> None:
    # 이슈 #2196: _save_requirement_drift_cache 와 같은 atomic temp+rename
    # 관용의 작은 로컬 사본 — 소비자가 이 둘뿐이라 공유 헬퍼로 뽑지 않는다.
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent),
                                         prefix=".watchdog-noise-", suffix=".tmp")
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


def _watchdog_note_gh_failure(root: Path, signal: str, failed: bool) -> bool:
    """이슈 #2196: `signal` 이름별 연속 gh 실패 틱 수를 `root` 스코프
    영속 상태에 누적하고, 이번 틱에 경고 줄을 찍어야 하는지 돌려준다.
    성공(failed=False)이면 스트릭을 0 으로 리셋하고 항상 False. 실패면
    +1 하고, 연속 실패 수가 WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD 이상일
    때만 True — 단발 blip 은 억제하고(카테고리 2), 계속되는 실패는
    (진짜 액셔너블이므로) 매 틱 계속 경고한다."""
    path = _sp._watchdog_noise_state_path(root)
    state = _sp._load_watchdog_noise_state(path)
    streaks = state.setdefault("gh_failure_streaks", {})
    if not failed:
        changed = streaks.get(signal, 0) != 0
        streaks[signal] = 0
        if changed:
            _sp._save_watchdog_noise_state(path, state)
        return False
    streaks[signal] = streaks.get(signal, 0) + 1
    should_warn = streaks[signal] >= _sp.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD
    _sp._save_watchdog_noise_state(path, state)
    return should_warn


def _watchdog_note_unmappable_pr(root: Path, pr_number: int) -> bool:
    """이슈 #2196, 이슈 #2979 로 범위 축소: 브랜치명은
    issue-<n>/<skill>[+<skill>]-<lease> 형식이지만(즉 board subject
    형태다) 그 이슈가 지금 board 에 없는, subject 매핑 손실 PR 을(#2379
    corrupted-merge-base 류) `root` 스코프 영속 상태에 이미 한 번
    보고했는지로 판별한다. 브랜치가 애초에 그 형태가 아니었던
    non-subject PR(#2979 이전엔 여기 같이 섞였다)은 `_classify_narrowing_prs`
    가 이 함수를 아예 부르지 않고 개수로만 접는다 — 개별 줄 자체가 없다.
    처음 보는 PR 이면 True(=이번 틱에 개별 줄을 찍어라)를 돌려주고
    상태에 기록, 이미 본 PR 이면 False(=저장소 상태가 그대로면 같은
    사실을 매 틱 반복 보고하지 않는다) — #2165 sticky-cache/#2173
    spawn_on_approve 와 같은 one-shot 마커 관용."""
    path = _sp._watchdog_noise_state_path(root)
    state = _sp._load_watchdog_noise_state(path)
    seen = state.setdefault("unmappable_prs_reported", {})
    key = str(pr_number)
    if key in seen:
        return False
    seen[key] = True
    _sp._save_watchdog_noise_state(path, state)
    return True


def _watchdog_note_unmappable_subject_branch(root: Path, subject: str) -> bool:
    """이슈 #2196 category 3: `gates/spawn_on_pr.py`의 `missing_verification`
    이 `subject`의 deliverable 브랜치를 `pr_index`에서 찾지 못하는 조건은
    삭제된 오래된 브랜치처럼 영구적인 경우가 대부분이다 —
    `_watchdog_note_unmappable_pr`과 같은 one-shot 마커: 처음 보는
    subject 면 True(=이번 틱에 개별 줄로 보고)를 돌려주고 상태에 기록,
    이미 본 subject 면 False(=저장소 상태가 그대로면 반복 보고하지 않음)."""
    path = _sp._watchdog_noise_state_path(root)
    state = _sp._load_watchdog_noise_state(path)
    seen = state.setdefault("unmappable_subject_branch_reported", {})
    if subject in seen:
        return False
    seen[subject] = True
    _sp._save_watchdog_noise_state(path, state)
    return True


# 이슈 #3047: `board_now`에 없는 subject-shaped PR("mapping loss")은 최소
# 세 가지 서로 다른 원인에서 나온다 — 이 세 상수는 그중 어느 것을 실제로
# 확립했는지를 명시적으로 표현한다. 구분 없이 하나로 접으면(옛 동작) 새
# 이슈의 정상적인 "아직 첫 레코드 미병합" 상태에 손상-merge-base 진단과
# force-push 복구 문구가 그대로 붙는다(#3047 관측 사례).
_MAPPING_LOSS_CORRUPTED = "corrupted-merge-base"
_MAPPING_LOSS_NO_RECORD_YET = "no-record-yet"
_MAPPING_LOSS_UNCLASSIFIED = "unclassified"


def _classify_mapping_loss_cause(pr_index: dict, issue_n: int) -> str:
    """이슈 #3047: `issue_n`에 대한 mapping-loss 의 원인을, 이번 틱에 이미
    가져온 `pr_index`(branch -> {number, state, body}, `gh api
    repos/{slug}/pulls?state=all` 전체 페이지네이션 — #1702)만으로
    판별한다. 추가 `gh` 호출은 절대 하지 않는다 — 이 인덱스 자체가 델타가
    있을 때만 나가는, 이미 지불한 1회 호출이고(#1688), 틱 예산이 이
    경로를 델타-게이트한 이유가 그 1회조차 아끼려는 것이기 때문이다.

    신호: `issue-<n>/`로 시작하는 모든 branch 를 이 인덱스에서 훑어(같은
    subject 의 다른 skill-lease 브랜치들 포함, 병합 여부와 무관하게
    `state=all`로 이미 다 들어 있다) 그 상태들을 본다.

    - 그중 MERGED 가 하나라도 있으면: 이 subject 는 과거에 실제로 board
      에 반영된 레코드를 가졌었다는 뜻이고, 지금 그게 `board_now`에서
      사라진 것은 정상 궤적으로 설명되지 않는다 — #2379 corrupted-merge-base
      류의 진짜 신호로 남는다.
    - MERGED 는 없지만 CLOSED(병합 안 된 채 닫힘) 가 있으면: 이전 시도가
      왜 닫혔는지(정상적으로 상위 시도에 흡수됐는지, 손상을 감지하고
      스스로 포기했는지) 이 인덱스만으로는 갈리지 않는다 — 확립 못 한
      원인을 아무 쪽으로도 밀어넣지 않고 unclassified 로 명시한다.
    - 그 외(전부 OPEN 이거나 이 PR 자신뿐이면): 이 subject 가 첫 레코드를
      한 번도 병합한 적이 없다는 뜻이고, 이슈가 막 열려 아직 세션의
      첫 산출물이 안착하기 전인 정상 상태와 구별되지 않는다 —
      no-record-yet."""
    prefix = f"issue-{issue_n}/"
    states = [info.get("state") for branch, info in pr_index.items()
              if branch.startswith(prefix)]
    if any(s == "MERGED" for s in states):
        return _MAPPING_LOSS_CORRUPTED
    if any(s == "CLOSED" for s in states):
        return _MAPPING_LOSS_UNCLASSIFIED
    return _MAPPING_LOSS_NO_RECORD_YET


def _format_mapping_loss_line(prn: int, issue_n: int, branch: str, cause: str) -> str:
    """이슈 #3047: mapping-loss 한 건을 원인별로 다른 문장으로 찍는다.
    `recut-corrupted` remediation 문장은 `_MAPPING_LOSS_CORRUPTED` 에만
    붙는다 — 확립 못 한 원인(no-record-yet/unclassified)에는 force-push
    복구를 절대 제안하지 않는다(#3047 must-not)."""
    head = (f"[watchdog] board-sweep: PR #{prn} 변경 감지했으나 "
            f"issue-{issue_n} subject 가 board 매핑을 잃었다 (브랜치={branch!r})")
    if cause == _MAPPING_LOSS_CORRUPTED:
        return (f"{head} — 원인: corrupted-merge-base (이 subject 의 이전 "
                "병합 레코드가 있는데도 지금 board 에 없다) — "
                "issue-<n>/<skill>[+<skill>]-<lease> 산출물을 잘못된 base 에서 "
                "다시 잡아온(#2379) 브랜치라면 "
                "`spawn.py recut-corrupted --issue <n> --session <session>`(#2402)로 "
                "같은 이름 아래 재컷하라")
    if cause == _MAPPING_LOSS_NO_RECORD_YET:
        return (f"{head} — 원인: no-record-yet (이 subject 는 아직 병합된 "
                "레코드가 한 번도 없다 — 새 이슈의 정상 상태) — 조치 불필요, "
                "재컷 복구 대상 아님")
    return (f"{head} — 원인: unclassified (이 subject 에 병합 안 된 채 닫힌 "
            "PR 이 있어, 정상 흡수와 손상된 시도 포기를 이 인덱스만으로는 "
            "구별할 수 없다) — 사람이 직접 확인, 자동 재컷 복구를 임의로 "
            "적용하지 말 것")


def _classify_narrowing_prs(
        root: Path, pr_numbers: set[int], number_to_branch: dict[int, str | None],
        board_now: dict, pr_index: dict | None = None
        ) -> tuple[set[int], int, list[tuple[int, int, str, str]], int]:
    """이슈 #2979: 델타로 바뀐 PR 을 subject 이슈로 좁히면서, 두 상태를
    구분한다 — (a) 브랜치가 `issue-<n>/<skill>` 형태를 한 번도 아니었던
    PR(non-subject, 관측된 #1/#7/#26/#1985 류: `fix/...`, `plan/...`,
    브랜치 삭제로 `None`)과 (b) 브랜치는 그 형태이지만 그 이슈가 지금
    `board_now`에 없는 PR(subject mapping loss). (a)는 board 와 무관한 PR
    이라 언제나 개수로만 접고 개별 줄을 절대 찍지 않는다 — 매 틱 반복돼도
    one-shot 마커를 타지 않는다(찍을 개별 줄 자체가 없으므로 반복 억제가
    필요 없다). (b)는 subject 가 board 매핑을 잃은 상태이지만, 이슈
    #3047: 그 원인은 하나가 아니다 — `_classify_mapping_loss_cause`로
    `pr_index`(이미 이번 틱에 가져온 것, 추가 `gh` 호출 없음)만 보고
    corrupted-merge-base/no-record-yet/unclassified 셋 중 하나로 갈라
    반환한다. `_watchdog_note_unmappable_pr`의 기존 one-shot 마커로
    저장소 상태가 안 바뀌는 한 반복 보고하지 않는 것은 원인과 무관하게
    그대로 유지한다.

    `(changed_numbers, non_subject_count, mapping_loss_new,
    mapping_loss_already_reported)`. `changed_numbers`는 narrowing set 에
    합칠 이슈 번호(성공 매핑), `mapping_loss_new`는 이번 틱에 처음
    발견된 `(pr_number, issue_number, branch, cause)` 튜플 목록이다."""
    changed_numbers: set[int] = set()
    non_subject_count = 0
    mapping_loss_new: list[tuple[int, int, str, str]] = []
    mapping_loss_already_reported = 0
    for prn in sorted(pr_numbers):
        branch = number_to_branch.get(prn)
        m = _HEAD_REF_SUBJECT_RE.match(branch) if branch else None
        if not m:
            non_subject_count += 1
            continue
        issue_n = int(m.group(1))
        if f"issue-{issue_n}" in board_now:
            changed_numbers.add(issue_n)
            continue
        if _watchdog_note_unmappable_pr(root, prn):
            # 이슈 #3047 (silent-failure-audit): `pr_index`가 아예 안 넘어온
            # 것(호출자가 못 만들었다 -- 지금 생산 코드엔 없는 경로, 방어적
            # 케이스)과 실제로 가져왔는데 비어 있는 것은 다른 인식론적
            # 상태다 -- 전자를 후자로 조용히 뭉개 "no-record-yet"으로
            # 추측하면 이 이슈가 고치려는 결함을 인자 하나 좁은 범위에서
            # 재현하게 된다. 못 가져온 경우는 unclassified 로 명시한다.
            cause = (_classify_mapping_loss_cause(pr_index, issue_n)
                     if pr_index is not None else _MAPPING_LOSS_UNCLASSIFIED)
            mapping_loss_new.append((prn, issue_n, branch, cause))
        else:
            mapping_loss_already_reported += 1
    return changed_numbers, non_subject_count, mapping_loss_new, mapping_loss_already_reported


def _watchdog_note_spawn_coverage_delta(root: Path, uncovered: list[int]) -> list[int]:
    """이슈 #2979: spawn-coverage 는 매 틱 커버되지 않은 이슈의 전체
    집합을 그대로 다시 찍어 대부분 안 바뀌는 census 가 된다 — 실제 신호는
    이전 틱 대비 새로 늘어난 이슈뿐이다. 저장된 이전 집합과 비교해 새로
    늘어난 번호만 돌려주고, 상태를 이번 틱 집합으로 통째로 교체한다 —
    한 번 커버됐다가 다시 커버 안 되면(flap) 다음에 다시 나타날 때 또
    "새로" 로 잡힌다, sticky one-shot 이 아니다: 그 이슈는 실제로 다시
    커버 안 되는 상태로 바뀐 것이라 다시 신호할 가치가 있다."""
    path = _watchdog_noise_state_path(root)
    state = _load_watchdog_noise_state(path)
    seen = set(state.get("spawn_coverage_uncovered", []))
    current = set(uncovered)
    newly = sorted(current - seen)
    state["spawn_coverage_uncovered"] = sorted(current)
    _save_watchdog_noise_state(path, state)
    return newly


def _watchdog_note_ambiguous_deliverable_record(root: Path, subject: str) -> bool:
    """issue #2978 follow-up (PR #3021's independent-review finding):
    `gates/spawn_on_pr.py`'s `missing_verification` distinguishes "this
    subject has 0 non-verifying board records" (no deliverable ever
    landed, ordinary) from "2+ non-verifying board records with no
    `verifies_subject` marker to disambiguate" (a deliverable
    demonstrably DID land, which one is ambiguous -- #2593's own
    documented refuse-to-guess case). The second, combined with a branch
    also missing from `pr_index`, is a genuine anomaly worth reporting --
    but like `_watchdog_note_unmappable_subject_branch` above, the
    underlying board shape is durable (an old subject's ambiguous record
    set doesn't resolve itself), so it gets its own one-shot marker in a
    separate state bucket rather than reusing that function's (a
    different finding -- "record set is ambiguous", not "branch
    confirmed missing" -- must not collapse into the same reported-once
    key). Same True/False one-shot contract as its sibling."""
    path = _sp._watchdog_noise_state_path(root)
    state = _sp._load_watchdog_noise_state(path)
    seen = state.setdefault("ambiguous_deliverable_record_reported", {})
    if subject in seen:
        return False
    seen[subject] = True
    _sp._save_watchdog_noise_state(path, state)
    return True


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


def _board_read(root: Path, force_full: bool | None = None) -> tuple[dict | None, dict]:
    """Issue #2103: the shared multi-item board read. Delegates to
    `gates.board_read.board_read` (single GraphQL board query + delta reads
    over a cached snapshot) and routes its fail-open signal to the ledger
    as an advisory `board_read_fail_open` event — a gh/network failure
    serves the stale snapshot and never crashes the calling sweep.

    `force_full` defaults to `None` (unchanged: `board_read()` decides from
    `BOARD_READ_FORCE_FULL`/the sweep counter) — passing `True` is issue
    #2941 finding 1's confirm-before-gone path (see
    `_board_pr_index_with_meta`), never the steady-state default.

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

    return board_read_mod.board_read(root, board_slug, on_fail_open=_fail_open,
                                     force_full=force_full)


def _board_pr_index_with_meta(root: Path,
                              force_full: bool | None = None) -> tuple[dict | None, dict]:
    """Same as `_board_pr_index()` but also returns the `board_read()` meta
    (issue #2941 finding 1: `meta["source"]` distinguishes a direct 2-call
    full connection read from the search-API-backed `_delta_read()` steady
    state — the shared index's "no PR for this branch" answer is only as
    trustworthy as which of the two produced it). `force_full=None`
    (default) preserves `_board_pr_index()`'s existing behavior exactly."""
    board, meta = _sp._board_read(root, force_full=force_full)
    if board is None:
        return None, meta
    sys.path.insert(0, str(_sp.ROOT / "gates"))
    import board_read as board_read_mod
    return board_read_mod.pr_index(board), meta


def _board_pr_index(root: Path) -> dict | None:
    """Issue #2103: `closure_sweep._pr_index_all`-shaped branch->PR index
    served from the shared board read (snapshot/delta) — replaces per-branch
    `gh pr list` loops in the poll tick. None when the board is unreadable
    (caller falls back to the per-branch helper, preserving today's
    fail-open behavior)."""
    idx, _meta = _board_pr_index_with_meta(root)
    return idx


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
    `requirement_drift_cache.json`(이슈 #2240: 오케스트레이터 틱간 기억이라
    `gates/state_paths.py` 로 앵커링 — `root` 기준이 아니다)에 저장된 이전
    판정용 본문을 그대로 재사용한다 — `None` 이면(기본) 기존처럼 열린
    이슈/PR 전체를 재훑는다."""
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
    # issue #3081: the cache is one file shared across every repo the
    # orchestrator sweeps (issue #2240, correct and unchanged). `repo_slug`
    # is this sweep's attribution key -- every entry this tick writes or
    # reads is scoped to it via `_drift_cache_key`, so one repo's sweep can
    # never surface or retain another repo's entries. A checkout with no
    # resolvable slug (no `gh` remote) still gets a stable key (`None`,
    # cached per-root by `_repo_slug`) -- it just means every entry from
    # that checkout shares one bucket, same as before this fix.
    repo_slug = _sp._repo_slug(root)
    if changed_numbers is None:
        # Issue #2103: full mode reads open issues+PRs from the shared board
        # read (snapshot + delta; was two `gh issue list`/`gh pr list` calls
        # per full-mode tick). A stale fail-open board is still usable here —
        # this signal is advisory and a slightly stale citation index beats
        # no verdict (same trade the old list calls could not make).
        full_board, _board_meta = _sp._board_read(root)
        if full_board is None:
            # 이슈 #2196: 단발 gh blip 은 조용히 넘어간다 — 연속 N틱 실패면
            # (진짜 액셔너블) 그때부터 경고한다. 이슈 #2980: 이 조회 실패는
            # 그 자체로 독립된 상태다 — 다른 verdict 줄과 같은
            # `requirement-drift:` 채널이 아니라 별도 태그로 찍어서, 조회
            # 못 했다는 사실을 pass/violation 어느 쪽으로도 읽히지 않게 한다.
            if _sp._watchdog_note_gh_failure(root, "requirement-drift:full", True):
                print("[watchdog] requirement-drift-lookup-failed: gh 실패 — "
                      "조회 실패, 판정 없음 (advisory, 미집계)")
            return
        _sp._watchdog_note_gh_failure(root, "requirement-drift:full", False)
        all_items = [item
                     for group in (full_board["issues"], full_board["prs"])
                     for item in group.values()
                     if item.get("state") == "OPEN"]
        # issue #1688: full-mode run also refreshes the verdict cache so a
        # later delta-mode tick can reuse today's fetch for unchanged numbers.
        # issue #2980: `cached_at` records when this body was actually
        # observed, so a later retained-on-failure report can name it
        # instead of silently passing off stale data as a fresh judgment.
        # issue #3081: full mode is authoritative for *this repo's* current
        # open set, but the cache file also holds other repos' entries --
        # load first and only replace this repo's slice, or a full sweep of
        # repo A would erase repo B's memory outright.
        now_iso = datetime.now(timezone.utc).isoformat()
        cache = _sp._load_requirement_drift_cache(cache_path)
        cache = {k: v for k, v in cache.items() if v.get("repo") != repo_slug}
        for item in all_items:
            num = item.get("number")
            if num is None:
                continue
            cache[_sp._drift_cache_key(repo_slug, num)] = {
                "title": item.get("title", ""), "body": item.get("body", "") or "",
                "cached_at": now_iso, "repo": repo_slug, "number": num}
        _sp._save_requirement_drift_cache(cache_path, cache)
    else:
        # issue #1688: delta mode — only re-fetch the changed numbers (via
        # the shared gh_cache), reuse the on-disk verdict cache for the rest.
        cache = _sp._load_requirement_drift_cache(cache_path)
        all_items = []
        any_fetch_ok = not changed_numbers
        failed_numbers: list[int] = []
        # issue #2980: numbers this tick actually fetched (success or
        # confirmed-closed) — the reuse pass below skips only these, so a
        # changed number whose fetch failed but has a genuine prior cache
        # entry still falls through to the reuse pass and is actually
        # retained, not silently dropped out of the verdict alongside its
        # "이전 캐시 판정 유지" claim.
        fetched_numbers: set[int] = set()
        for num in sorted(changed_numbers):
            item = _sp._fetch_issue_or_pr_via_cache(root, num)
            if item is None:
                failed_numbers.append(num)
                continue
            any_fetch_ok = True
            fetched_numbers.add(num)
            key = _sp._drift_cache_key(repo_slug, num)
            # issue #2078: a live refetch may show the number merged/closed
            # since it was last cached as open — drop it from the index
            # entirely instead of re-flagging it as an open uncited PR.
            if item.get("state") not in (None, "open"):
                cache.pop(key, None)
                continue
            all_items.append(item)
            cache[key] = {"title": item.get("title", ""),
                           "body": item.get("body", "") or "",
                           "cached_at": datetime.now(timezone.utc).isoformat(),
                           "repo": repo_slug, "number": num}
        # issue #3081: only this repo's own entries feed the reuse pass --
        # this is the report-time filter. Without it, another repo's cached
        # entries (real numbers, real bodies, cached under this same shared
        # file) get read back in here and printed under this sweep's prefix
        # as if they were this repo's own open items.
        for val in cache.values():
            if val.get("repo") != repo_slug:
                continue
            key_num = val.get("number")
            if key_num is None or key_num in fetched_numbers:
                continue
            all_items.append({"number": key_num, "title": val.get("title", ""),
                               "body": val.get("body", "")})
        _sp._save_requirement_drift_cache(cache_path, cache)
        # 이슈 #2980: gh 연결성 신호(아래)와 "이번 틱에 평가할 데이터가
        # 있는지"는 별개다 — changed_numbers 전부가 fetch 에 실패해도,
        # 그중 캐시에 genuine prior 가 있는 번호는 재사용 패스에서 이미
        # all_items 로 들어왔고, 무관한 다른 열린 이슈/PR 도 캐시에서
        # 그대로 채워진다. 그래서 이 gh-연결성 신호는 더 이상 조기
        # return 을 하지 않는다 — return 했다면 changed_numbers 가 딱 1개뿐이고
        # 그게 genuine prior 를 가진 재조회 실패인, 가장 흔한 케이스에서
        # cache-retained 줄이 아예 찍히지 못했다(이슈 #2980 에서 실측).
        if not any_fetch_ok:
            # 이슈 #2196: 단발 gh blip 은 조용히 넘어간다 — 연속 N틱
            # 실패면 그때부터 경고한다. 이슈 #2980: full 모드와 같은 이유로
            # 독립 상태 태그를 쓴다 — verdict 채널과 섞이지 않는다.
            if _sp._watchdog_note_gh_failure(root, "requirement-drift:delta", True):
                print("[watchdog] requirement-drift-lookup-failed: gh 실패 — "
                      "조회 실패, 판정 없음 (advisory, 미집계)")
        else:
            _sp._watchdog_note_gh_failure(root, "requirement-drift:delta", False)
        if failed_numbers:
            # 이슈 #2589/#2980: 델타 모드에서 개별 번호 조회 실패는 조용히
            # 사라지지 않고 이 줄들로 남는다 — 캐시에 이전 판정이 있는
            # 번호는 그 판정을 유지한다고, 언제 관측된 것인지와 함께
            # 정확히 알리고(fresh judgment 로 오인되지 않게), 캐시가 없는
            # 번호는 "이전 캐시 판정 유지"라고 거짓 주장하지 않고 이번
            # 틱에서 전혀 평가되지 않은 unknown 이라는 사실을 그대로
            # 알린다 — 신규 subject 가 한 번도 가져본 적 없는 판정을
            # 물려받지 않는다.
            # issue #3081: keyed on repo+number, so a number whose only
            # cache entry belongs to a *different* repo (the failure mode
            # this fix targets -- a lookup fails precisely because the
            # cached entry is another repo's, not this repo's) cannot
            # match here. It falls to `uncached_failed` below and is
            # reported as unresolved, not silently retained as if this
            # repo had a genuine prior verdict for it.
            cached_failed = [n for n in failed_numbers
                              if _sp._drift_cache_key(repo_slug, n) in cache]
            uncached_failed = [n for n in failed_numbers
                                if _sp._drift_cache_key(repo_slug, n) not in cache]
            for n in cached_failed:
                observed_at = cache.get(_sp._drift_cache_key(repo_slug, n), {}).get(
                    "cached_at", "unknown")
                print(f"[watchdog] requirement-drift-cache-retained: 조회 실패 {n} — "
                      f"이전 캐시 판정 유지 (관측: {observed_at})")
            if uncached_failed:
                print(f"[watchdog] requirement-drift-unknown: 조회 실패 {uncached_failed} — "
                      "이전 판정 없음, unknown")
        if failed_numbers and not all_items:
            # 이슈 #2980 must-not: 이번 틱에 "조회 실패 때문에" 평가할
            # 데이터가 정말 하나도 없으면(fetch 도 실패, 재사용할 캐시도
            # 없음) 여기서 멈춘다 — 계속 진행하면 모든 살아있는 요구가
            # "인용 안 됨"으로 찍혀 조회 실패를 violation 으로 오판하는
            # 꼴이 된다. `failed_numbers` 를 반드시 함께 검사한다 — 실패가
            # 전혀 없는 틱(예: 유일하게 캐시됐던 번호가 이번에 merge/close
            # 로 정상 확인되어 all_items 가 비는 경우)까지 이 guard 로
            # 막으면, full 모드의 "정말로 열린 이슈/PR 이 하나도 없다"는
            # 정당한 상태와 똑같은 상황에서 delta 모드만 조용히 아무 것도
            # 안 찍는 새로운 침묵을 만든다(경고 헌팅으로 실측: #42 하나만
            # 캐시돼 있었고 이번 틱에 그게 closed 로 정상 재조회되면,
            # 실패가 전혀 없었는데도 이전 코드가 이 return 으로 살아있는
            # 요구의 진짜 위반을 그대로 삼켰다).
            return

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
                # 안 잡힌다 — 각 PR 을 headRefName(issue-<n>/<skill>[+<skill>]-<lease>)으로
                # subject 이슈에 매핑해 narrowing set 에 합친다.
                # closure_sweep._pr_index_all 은 이 파일이 이미 다른
                # 경로(closure-sweep 처리)에서 쓰는 동일한 `gh pr list`
                # 인덱스 — PR 변경이 있을 때만(무변경 틱엔 안 나감) 도는
                # 추가 1회 호출이다.
                pr_index, pr_index_ok = closure_sweep._pr_index_all(root)
                if pr_index_ok and pr_index is not None:
                    _sp._watchdog_note_gh_failure(root, "board-sweep:pr-index", False)
                    number_to_branch = {v.get("number"): k for k, v in pr_index.items()}
                    (mapped, non_subject_count, mapping_loss_new,
                     mapping_loss_already_reported) = _classify_narrowing_prs(
                        root, pr_numbers, number_to_branch, _sp.board(root), pr_index)
                    changed_numbers |= mapped
                    for prn, issue_n, branch, cause in mapping_loss_new:
                        # 이슈 #2979: 브랜치는 issue-<n>/<skill> 형태지만 그
                        # 이슈가 지금 board 에 없다 — non-subject 와 달리
                        # 무시할 수 없는 상태다. 이슈 #3047: 그 원인은
                        # 하나가 아니어서(corrupted-merge-base/no-record-yet/
                        # unclassified), `_classify_mapping_loss_cause`가 이미
                        # 정한 `cause`에 따라 다른 문장을 찍는다 —
                        # recut-corrupted remediation 은 corrupted-merge-base
                        # 에만 붙는다. one-shot: 저장소 상태가 그대로면
                        # 반복 안 찍는다.
                        print(_format_mapping_loss_line(prn, issue_n, branch, cause))
                    if mapping_loss_already_reported:
                        # 이슈 #2196: 이전에 이미 개별 보고된 매핑-손실
                        # subject 들은 저장소 상태가 그대로면 반복하지
                        # 않고, 한 줄짜리 카운트로 접는다.
                        print(f"[watchdog] board-sweep: {mapping_loss_already_reported}건 "
                              "이전에 보고된 매핑-손실 subject — 계속 무시 (반복 안 찍음)")
                    if non_subject_count:
                        # 이슈 #2979: 브랜치가 issue-<n>/<skill> 형태를 한
                        # 번도 아니었던 PR(board 와 무관, fix/... plan/...
                        # 또는 브랜치 삭제로 None) — 절대 개별 줄로 찍지
                        # 않고 항상 개수로만 접는다. recut-corrupted
                        # remediation 은 여기 붙지 않는다: board subject 가
                        # 아닌 항목에 적용될 조언이 아니다.
                        print(f"[watchdog] board-sweep: {non_subject_count}건 "
                              "non-subject PR (브랜치가 board subject 형태 아님) — "
                              "board 와 무관, 집계만")
                else:
                    # 이슈 #2196: PR 인덱스 조회 실패는 단발 gh blip 일 수
                    # 있다 — 연속 N틱 실패면 그때부터 경고한다.
                    if _sp._watchdog_note_gh_failure(root, "board-sweep:pr-index", True):
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

    issue_states, issue_states_status = (None, closure_sweep.ISSUE_INDEX_OK)
    if ("spawn-on-pr" in this_tick or "closure-sweep" in this_tick
            or "spawn-on-approve" in this_tick):
        issue_states, issue_states_status = closure_sweep.issue_state_index_all(root)
        calls_made += 1

    rate_limited_this_tick = False

    # 이슈 #1745: 이번 틱에 PR 인덱스가 필요한 카테고리가 둘 이상이면
    # 벌크 PR 인덱스를 여기서 한 번만 가져와 공유한다 — 각자
    # `closure_sweep._pr_index_all()` 을 따로 부르면 `gh api .../pulls`
    # 페이지네이션이 틱당 여러 번 나간다(#1745 관측). issue #2173
    # before-landing hunt: `spawn-on-approve` 는 소비자가 하나뿐인
    # 틱에서도 항상 벌크 인덱스를 받아야 한다 — `pr_index=None` 이면
    # `spawn_on_approve.ready_for_phase2()` 가 후보 브랜치마다 `gh pr
    # list` 를 한 번씩(O(branches), watchdog 예산에 안 잡힘) 부르는
    # 폴백으로 떨어진다. 그 폴백 자체는 `spawn_on_pr.py` 도 갖고 있는
    # 기존 경로지만, 그쪽은 `missing_verification()` 진입 전에 이미
    # board() 로 subject 수를 좁혀 실사용 빈도가 낮다 — 이쪽은 로컬 git
    # 브랜치 수만큼 그대로 늘어나므로 소비자 1개짜리 틱에서도 공유
    # 인덱스를 강제해 그 폴백이 절대 안 걸리게 한다.
    _pr_index_consumers = sum(c in this_tick for c in
                              ("spawn-on-pr", "closure-sweep", "spawn-on-approve"))
    shared_pr_index: dict | None = None
    if _pr_index_consumers >= 2 or "spawn-on-approve" in this_tick:
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
            for subj, skills in _sp.board(root).items():
                parts = subj.split("-", 1)
                if len(parts) == 2 and parts[1].isdigit() and int(parts[1]) in changed_numbers:
                    sweep_subjects[subj] = skills
        violations, skips = closure_sweep.find_violations(
            root, subjects=sweep_subjects, issue_states=issue_states,
            pr_index=shared_pr_index)
        calls_made += 1
        if violations:
            count += len(violations)
            print(f"[watchdog] closure-sweep: 위반 {len(violations)}건")
            print(closure_sweep.format_report(violations))
        # issue #2792: a real gh failure at the top-level fetch is a
        # rate-limit-relevant signal (backs off board-sweep's polling
        # interval below); a truncated index is a structural board-size
        # condition that backing off cannot fix, so it must not be
        # counted the same way `not issue_states_ok` used to (that
        # conflated the two — see closure_sweep.ISSUE_INDEX_* docstring).
        rate_limited_this_tick = (
            bool(skips) and issue_states_status == closure_sweep.ISSUE_INDEX_FAILED)
        if skips:
            count += 1
            # 이슈 #2196: 단발 gh blip 은 조용히 넘어간다 — 연속 N틱
            # 실패면 그때부터 경고한다. issue #2792: skip 사유를
            # 개수로 접어 gh 실패와 인덱스 절단을 라벨에서부터 구별한다
            # — 둘 다 "(gh 실패)"로 뭉뚱그리면 절단인데 실패로 오독한다.
            if _sp._watchdog_note_gh_failure(root, "closure-sweep", True):
                reason_counts: dict[str, int] = {}
                for s in skips:
                    r = s.get("reason", "?")
                    reason_counts[r] = reason_counts.get(r, 0) + 1
                print(f"[watchdog] closure-sweep: 확인 불가 {len(skips)}건 {reason_counts}")
        else:
            _sp._watchdog_note_gh_failure(root, "closure-sweep", False)

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
            # 이슈 #2979: 표준 집합을 매 틱 그대로 다시 찍지 않는다 —
            # 이전 틱 대비 새로 늘어난 이슈만 신호다. 총 건수는 anomaly
            # count 에 그대로 반영해(위) 심각도 판정을 흐리지 않는다.
            newly_uncovered = _watchdog_note_spawn_coverage_delta(root, uncovered)
            if newly_uncovered:
                print(f"[watchdog] spawn-coverage: 새로 커버되지 않음 {newly_uncovered} "
                      f"(표준 집합 {len(uncovered)}건)")

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


def _paired_liveness(pid: int, recorded_start_time: str | None) -> str:
    """이슈 #2969: `_alive()`(raw `ps`) 하나만으로 "확인된 생존"을 주장하지
    않는다 — pid 는 살아있어도 크래시 뒤 OS 가 재사용한 남의 프로세스일 수
    있다(이슈 #2749/#2823 이 워처/세션 신원 확인에 이미 쓰는 것과 같은
    구멍). 로스터 등록 시점에 함께 저장해 둔 `_proc_start_time(pid)` 값과
    지금 값을 짝지어(pair) 신원을 재확인한다.

    셋 중 하나를 돌려준다:
    - `"alive"`: 살아있고, 시작시각 짝짓기가 일치 — 확인된 생존.
    - `"dead"`: 죽어 있음, 또는 시작시각이 달라 pid 가 재사용됐다고 확인됨.
    - `"unconfirmed"`: 살아는 있지만 짝짓기 자체를 세울 수 없다(기록된
      시작시각이 없는 엔트리, 또는 `/proc` 없는 플랫폼 — 이슈 #2924) —
      "확인된 생존"도 "확인된 죽음"도 아니다, 어느 쪽으로도 추측하지
      않는다."""
    if not _sp._alive(pid):
        return "dead"
    if recorded_start_time is None:
        return "unconfirmed"
    cur_start = _proc_start_time(pid)
    if cur_start is None:
        return "unconfirmed"
    return "alive" if cur_start == recorded_start_time else "dead"


def watchdog_lock_acquire(lock_path: Path = WATCHDOG_LOCK_PATH,
                           pid: int | None = None) -> tuple[bool, str]:
    """`spawn.py watchdog` 단일-인스턴스 락(이슈 #1456 요구 1). 이미 살아있는
    인스턴스가 있으면 (False, 안내줄) — pid 재사용을 피하려 pid *와*
    프로세스 시작 시각이 둘 다 일치해야 "살아있다"로 본다. 죽은 프로세스가
    남긴 락(또는 pid 재사용으로 시작시각이 달라진 락)은 그대로 회수한다.

    이슈 #2924: `/proc` 없는 플랫폼(macOS)에서는 `_proc_start_time()` 이
    항상 `None` 을 돌려준다 — 락 기록 당시에도, 재확인 시에도. 그러면
    `None == None` 이 항상 참이 되어 시작시각 비교가 무조건 "일치"로
    보인다: pid 가 재사용된 무관한 프로세스도 "이미 실행 중"으로 오판돼
    새 워치독이 영원히 못 뜬다 — 시작시각 비교가 있는 것처럼 보이지만
    사실상 아무것도 검증하지 않는다. 그 저하 자체는 대체 메커니즘이 없어
    바꿀 수 없지만(이슈의 must-not: 리눅스 쪽을 약화해 맞추지 않는다),
    반환되는 안내줄에는 남긴다 — 이 함수의 호출자(spawn.py)는 실패 시
    이 메시지를 그대로 print 하므로, 여기 붙이면 그 자리에서 바로 보인다."""
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
            degraded_note = (
                " (start_time 신원 확인 불가 -- /proc 없는 플랫폼, pid 가 "
                "재사용된 무관한 프로세스여도 이 판정은 똑같이 나온다)"
                if other_start is None else "")
            return False, (f"[watchdog] 이미 실행 중: pid={other_pid} "
                            f"start_time={other_start}{degraded_note} — "
                            f"lock={lock_path}")
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
    `~/.tokenmaxxxer/work/*` 세션 워크스페이스)이면 시작을 거부한다 (이슈
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
    """`spawn.py watchdog` — 살아있는 모든 세션을 한 번 스캔해서 이상
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
    온다), 보드 스캔 대상(이슈/PR/다이제스트)만 `root` 를 쓴다.

    이슈 #3061: 이 함수가 stdout 에 찍는 리포트 텍스트는 poll-heartbeat.sh 를
    거쳐 on-the-record/monitors/poll_heartbeat_delta.py 로 흐른다 — 그 레이어가
    매 틱을 no-op wake(advanced nothing, idle-wake 로 집계)와 acted 로 갈라
    `.on-the-record/`(poll_heartbeat_last_state.json)에 누적한다. 빈 로스터
    틱("돌고 있는 스킬 세션 없음")도, anomaly_count==0 인 조용한 틱도 정확히
    하나의 idle-wake 로 집계될 뿐 결함으로 취급되지 않는다 — spawn 돼 있는
    세션이 정상적으로 mid-flight 라 이번 틱엔 나아갈 게 없는 것과, 워치독이
    뭔가를 놓친 것은 구별해야 하는 서로 다른 상태다. 집계/리포트 함수는
    `on-the-record/monitors/poll_heartbeat_delta.py::format_wake_outcomes`."""
    # 이슈 #2904: 자연 종료로 자기 roster 엔트리를 스스로 지운(아래 `d_all`
    # 로드보다 먼저, 이미 사라진 뒤라 dead-scan 이 못 보는) 세션의 완료
    # 사실을 큐에서 드레인해 always-emit `[poll-report] ...: COMPLETED`
    # 로 낸다 — `if not d:` 조기 리턴(로스터가 완전히 비면 여기서 함수가
    # 끝난다, 아래)보다 반드시 앞이어야, 등록된 세션이 하나도 없는 흔한
    # 틱에서도 이 신호가 여전히 나간다. 새 `gh`/git 호출도, 새 폴링 주기도
    # 추가하지 않는다 — 이미 도는 이 watchdog 틱에 얹을 뿐. 완료 자체는
    # anomaly_count 에 안 얹는다(이상 신호가 아니다 — 기존 dead-scan
    # COMPLETED 와 같은 대접). 큐를 못 읽은 경우(lock/디스크 실패)는
    # 반대로 이상 신호로 낸다 — 그러지 않으면 "이번 틱엔 완료 없음"과
    # "이번 틱은 확인을 못 했음"이 똑같은 침묵으로 보여, 이 큐 자신이
    # 이슈 #2904 가 겨냥하는 바로 그 결함(깨끗한 출력과 안 봤음이
    # 구별 안 됨)을 새로 만든다.
    anomaly_count = 0
    _pending_completions, _pc_err = _sp._drain_pending_completions()
    if _pc_err is not None:
        anomaly_count += 1
        print(f"[poll-report-drain-failed] pending-completions 큐를 못 읽음 "
              f"(완료 신호를 이번 틱엔 못 볼 수 있음) — {_pc_err}")
    for _pc in _pending_completions:
        pr = _pc.get("pr_number")
        pr_label = f"PR #{pr}" if pr is not None else "PR 없음"
        print(f"[poll-report] {_pc.get('key')}: COMPLETED — issue #{_pc.get('issue')}, "
              f"session {_pc.get('session_id')}, {pr_label}, outcome={_pc.get('outcome')!r}")
    # 이슈 #1276: 로스터를 여기서 먼저 읽는다 — 보드 스윕이 로스터가
    # 가리키는 distinct 타깃 레포까지 커버해야 해서(요구#1), 로스터 스캔
    # 루프가 쓰는 `d_all` 과 같은 한 번의 읽기를 그대로 재사용한다.
    d_all = _sp._roster_load()
    anomaly_count += _sp._board_wide_sweep_all(root, d_all)
    # Issue #2101 mechanisms 3+4: level-triggered reconcile sweep (expired
    # leases requeued, claims without sessions and dangling declared waits
    # surfaced) + dead-man coverage marker check/refresh. Advisory-only;
    # requeued keys are popped from d_all so this tick's dead-entry loop
    # below does not re-report them.
    anomaly_count += _sp.lease_reconcile_sweep(root=root, d_all=d_all)
    # 이슈 #2291: 워크스페이스/로스터가 아직 없던 부트스트랩 구간에서 halt 한
    # spawn 시도를 보고한다 — roster 대조 대상이 아예 없어(그 구간엔 로스터
    # 엔트리 자체가 없다) 오늘까지는 이 워치독이 완전히 못 보던 상태.
    anomaly_count += _sp.spawn_attempt_sweep(d_all=d_all)
    # 이슈 #2468: check_runner worktree / consult·spawn settings.json 이
    # SIGKILL/하드크래시로 orphan 되는 걸 지운다 — 위 spawn_attempt_sweep
    # 과 같은 틱(살아있는 로스터와 무관하게 매번, 워치독이 도는 한 언젠가는
    # 반드시 돈다는 게 이 체크포인트를 고른 이유 — spawn 시작 시점이었다면
    # 크래시 이후 다음 스폰이 있을 때까지, 어쩌면 영원히 안 돌 수 있다).
    # 이상 신호가 아니라 정상적인 자기치유라 anomaly_count 에는 안 얹는다
    # (`_prune_spawn_attempts()`의 반환값을 spawn_attempt_sweep 이 버리는
    # 것과 같은 이유).
    _sp.tmp_resource_sweep()
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
    blockers, ok = _sp._undispositioned_skill_prs(root)
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
        print("돌고 있는 스킬 세션 없음")
        # Issue #3293 stage 2: an idle tick carries what is still
        # outstanding. "The goal is done" and "nobody started the next
        # thing" both look like an empty roster, and the orchestrator
        # cannot tell them apart from silence -- so name the open work, or
        # say plainly that none was found, which is itself the signal that
        # the monitor can be stopped.
        for line in _idle_tick_lines(root):
            print(line)
        if not anomaly_count:
            print("이상 신호 없음")
        return anomaly_count
    state = _sp._watchdog_state_load()
    # Respawn removal (2026-09-03): dead-entry observation is now
    # unconditional. `auto_respawn` used to gate both the scan and the
    # relaunch; the relaunch is gone, and gating the *scan* behind a flag
    # is what made "a session died" invisible whenever the flag was off.
    # Observing a death is never the destructive part.
    respawn_state = _sp._respawn_state_load()
    issue_skill_key = lambda e: (e.get("issue"), e.get("skill"))
    # Issue #2103: one shared branch->PR index per poll tick, built lazily
    # from the cached board snapshot (delta read: 1 API call, usually) the
    # first time a dead entry needs a PR check — replaces the per-dead-entry
    # `gh pr list --head <branch>` calls (O(dead entries) per tick). None
    # (board unreadable) keeps the per-branch fallback inside
    # diagnose_health(), so failure behavior is unchanged.
    _poll_pr_index_cache: list = []
    _poll_pr_index_meta_cache: list = []

    def _poll_pr_index() -> dict | None:
        if not _poll_pr_index_cache:
            idx, meta = _sp._board_pr_index_with_meta(root)
            _poll_pr_index_cache.append(idx)
            _poll_pr_index_meta_cache.append(meta)
        return _poll_pr_index_cache[0]

    # 이슈 #2941 finding 1 (adversarial review, docs/issue-2941/reports/
    # adversarial-review-2c0dae04.md): 위 `_poll_pr_index()`의 steady-state
    # 경로(`_delta_read()`)는 그 자체가 GraphQL search(...) 호출이다 —
    # 이 PR 이 대체한 `gh pr list --head`(브랜치 필터, 생성 직후 지연 실측:
    # #2930/#2934/#2937/#2919 네 건) 와 같은 인덱싱-파이프라인 계열이다.
    # reconcile 과 poll-report 가 이제 같은 인덱스를 보므로, 그 인덱스가
    # 아직 안 따라잡았으면 둘 다 "없음"에 조용히 동의해 버려
    # `[reconcile-poll-disagreement]`(#2882) 가 잡아낼 신호 자체가 사라진다
    # — 그래서 "없음"을 근거로 respawn/DEAD-ERRORED 를 확정하기 직전에만,
    # 이 틱의 인덱스가 delta(search) 출처였던 경우에 한해 직접 커넥션 쿼리인
    # full read 를 강제로 한 번 더 돈다(#2103 의 Layer 1 — search 인덱스가
    # 아니라 `repository { pullRequests }` 직접 쿼리, Finding 1 이 지목한
    # 바로 그 architecturally-다른 경로). "없음"이 이미 아닌 흔한 경우엔
    # 전혀 안 불려 틱당 오버헤드가 그대로다; 같은 틱에 여러 엔트리가 확인이
    # 필요해도 한 번만 돈다(캐시).
    _poll_pr_index_confirm_cache: dict = {}

    def _poll_pr_index_confirm_gone(branch: str | None) -> int | None:
        if not branch:
            return None
        idx = _poll_pr_index()
        meta = _poll_pr_index_meta_cache[0] if _poll_pr_index_meta_cache else {}
        if meta.get("source") != "delta":
            # full/stale/None: already the architecturally-direct read (or
            # nothing better is available) — no confirmation to gain.
            return _sp._pr_state_from_index(idx, branch) if idx else None
        if "full" not in _poll_pr_index_confirm_cache:
            full_idx, _full_meta = _sp._board_pr_index_with_meta(root, force_full=True)
            _poll_pr_index_confirm_cache["full"] = full_idx
        full_idx = _poll_pr_index_confirm_cache["full"]
        return _sp._pr_state_from_index(full_idx, branch) if full_idx else None
    for key, e in sorted(d.items()):
        # 이슈 #492: 같은 틱에서 reconcile() 도 한 번 태운다 — 새 폴러가
        # 아니라 이 기존 스캔에 올라탄다(ADR 결정 4).
        # 이슈 #2941: `_poll_pr_index()`(아래 dead-entry 분기가 poll-report
        # 판정에 쓰는 것과 같은 공유 인덱스)를 여기서도 넘긴다 — reconcile
        # 과 poll-report 가 같은 엔트리를 두고 서로 다른 PR 조회 경로(개별
        # `gh pr list --head` 대 board 벌크 인덱스)를 봐서 생긴
        # [reconcile-poll-disagreement](43건 실측, PR #2930/#2934/#2937/
        # #2919 검증 네 건 확인)를 소스 통일로 없앤다. `confirm_pr_missing`
        # 은 finding 1 의 완화책(위 주석) — "없음"을 respawn 으로 확정하기
        # 직전에만 호출된다.
        _expected = _sp._build_expected(e)
        _entry_branch = _expected["branch"]
        divergences = _sp.reconcile(
            _expected,
            _sp._build_observed(root, e, pr_index=_poll_pr_index()),
            recovery_state_dir=root / ".on-the-record" / "recovery-state",
            confirm_pr_missing=lambda br=_entry_branch: _poll_pr_index_confirm_gone(br))
        if divergences:
            issue_n, skill_n = issue_skill_key(e)
            for div in divergences:
                dedup_key = f"health-repair:{issue_n}:{skill_n}:{div['kind']}"
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
                # Issue #2193: name the commit count on a dead-with-commits
                # entry — same (before_head, HEAD) landmark `_build_observed()`
                # already reads for `reconcile()`, just counted instead of
                # boolean.
                # Issue #2795: the count is now remote-aware — it asks
                # `origin/<branch>` directly instead of assuming "no PR"
                # means "not pushed", so commits already on the remote no
                # longer trip this alarm. Branch comes from the workspace's
                # actual checked-out ref (`_current_branch`), not
                # `Path(work).name` — the workspace directory is named
                # `<repo>-issue-<n>-<skill>` (dashes) while the branch is
                # `issue-<n>/<skill>` (slash); querying the directory name
                # would make `ls-remote` miss every real branch and
                # reintroduce this same false positive.
                commit_count = (_sp._unrecovered_commit_count(
                    work, e.get("before_head"), _sp._git_head(work),
                    _entry_branch)
                    if work else 0)
                dead_health = _sp.diagnose_health(key, e, state=state, root=root,
                                              pr_index=_poll_pr_index(),
                                              commit_count=commit_count,
                                              confirm_pr_missing=(
                                                  lambda br=_entry_branch:
                                                  _poll_pr_index_confirm_gone(br)))
                state[f"{key}:dead_report"] = dead_health
            dead_health = state.get(f"{key}:dead_report")
            # 이슈 #2874: 위에서 이미 계산한 `divergences`([reconcile])와
            # `dead_health`([poll-report])가 같은 세션을 두고 서로 다른
            # 처분(하나는 respawn, 다른 하나는 완료)을 낸 경우를 조용히
            # 묻지 않고 이름 붙여 찍는다. 이슈 #2874 실측 그 자체(reconcile
            # 은 crashed->respawn, poll-report 는 COMPLETED)를 겨냥한
            # 잔여-안전망이다 — 위 wrapper_pid 수정이 이 특정 원인은 이미
            # 없앴지만, 두 계통이 서로 다른 원자료(reconcile 은 항상
            # `_build_observed()`, poll-report 는 `pr_index`/commit_count
            # 까지 곁들인 `diagnose_health()`)로 판정하는 구조 자체는 남아
            # 있어 다른 원인으로도 다시 갈릴 수 있다 — 그 경우까지 "둘 중
            # 나중에 찍힌 쪽이 이긴다"로 조용히 묻히지 않게 한다.
            if dead_health is not None and dead_health.get("state") is None:
                crash_shaped = [div for div in divergences
                                if div.get("next_action") == "respawn"]
                if crash_shaped:
                    dedup_key = f"reconcile-poll-disagreement:{key}"
                    if _sp.ledger_check_and_stamp(dedup_key):
                        anomaly_count += 1
                        kinds = ", ".join(div["kind"] for div in crash_shaped)
                        print(f"[reconcile-poll-disagreement] {key}: reconcile "
                              f"says {kinds} (-> respawn) but poll-report says "
                              f"completion ({dead_health['detail']}) — the two "
                              "disagree; not resolved silently, needs a human look")
            if dead_health is not None:
                # 이슈 #2312: 위 dead_report 캐시는 ledger TTL 마다만
                # 재계산되지만, 이 print 자체는 원래 그 TTL 밖에 있어(주석
                # 그대로) 죽은 엔트리 하나가 COMPLETED/DEAD-* 를 매 틱
                # 무한 재출력했다 — active.json 엔트리가 절대 은퇴하지
                # 않는 근본 원인. pid 로 스코프한 `reported_terminal` 로
                # 이 터미널 상태를 한 번만 찍고, `pid` 는 재스폰마다
                # 바뀌므로 같은 key 가 재사용돼도(재스폰) 새 인스턴스는
                # 다시 한 번 보고된다.
                terminal_key = f"{key}:{e.get('pid', 0)}:reported_terminal"
                already_reported = state.get(terminal_key, False)
                if not already_reported:
                    dead_label = "COMPLETED" if dead_health["state"] is None else dead_health["state"]
                    print(f"[poll-report] {key}: {dead_label} — {dead_health['detail']}")
                    state[terminal_key] = True
                    # before-landing hunt (issue #2312): persist this flag
                    # right away instead of waiting for the end-of-tick
                    # save — another entry raising later in this same loop
                    # must not un-report an already-reported terminal state
                    # on the next tick.
                    _sp._watchdog_state_save(state)
                    if not e.get("expects_pr") and issue_n is None:
                        # 관찰할 것이 없다(PR 도 안 기대하고 이슈도 없음) —
                        # 지금 바로 은퇴시킨다.
                        _sp.roster_remove(key)
                if dead_health["state"] is None:
                    # 이슈 #878 케이스 2: 완료(PR 존재) 이면서 이 엔트리를
                    # 무장한 오케스트레이터가 headless(session_id 있음) 였다면
                    # 여기서 --resume 을 쏜다 — 인터랙티브 케이스 1 은
                    # 라이브 notify 로 이미 처리되므로 session_id 없는 엔트리는
                    # 그대로 통과한다(중복 트리거 없음).
                    # Issue #2834: real checked-out branch, not the
                    # workspace directory's basename (same fix as
                    # diagnose_health() above and PR #2824/issue #2795's
                    # board.py call sites).
                    branch = _sp._current_branch(Path(work)) if work else None
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
            _sp._auto_respawn_check(key, e, respawn_state)
            continue
        # 이슈 #2215: harness-decided, unconditional — 이 라이브 엔트리의
        # 워크스페이스를 매 폴 틱(POLL_INTERVAL_SEC)마다 체크포인트한다.
        # dura 처럼 HEAD/브랜치/인덱스를 건드리지 않는다; 세션이
        # 커밋을 잊어도 이 스냅샷은 남는다.
        work = e.get("work")
        if work:
            # 이슈 #2417: tempdir 이 꽉 찼거나 못 쓰면
            # `checkpoint_workspace()` 가 `tempfile.TemporaryDirectory()`
            # 에서 OSError(FileNotFoundError 포함)를 던진다 — 여기서 잡지
            # 않으면 이 예외가 `roster_watchdog()` 밖의 try/except 까지
            # 뚫고 나가 틱 전체를 WATCHDOG_CRASH_SENTINEL(rc=97)로 끝내며,
            # 이 틱에 아직 안 본 다른 로스터 엔트리들의 진단까지 함께
            # 날아간다. 체크포인트 하나 실패는 이상 신호로 보고하고 틱은
            # 계속 돈다 — observe-only 계약(아무 것도 고치거나 죽이지
            # 않는다)은 그대로.
            try:
                checkpoint.checkpoint_workspace(work)
            except OSError as exc:
                anomaly_count += 1
                print(f"[checkpoint] {key}: 워크스페이스 체크포인트 실패 "
                      f"(디스크/tempdir 문제로 보임, 이 틱은 계속 진행) — {exc}")
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
        # Issue #3293 stage 2: every tick also carries what this session
        # actually did -- files written, commands run -- unsuppressed, so
        # the orchestrator judges intervention from the work rather than
        # from a state label that says HEALTHY while the artifact is wrong.
        for line in _session_tick_lines(key, e, state, health["state"]):
            print(line)
        if health["state"] is not None and health["state"] not in (
                "HEALTHY-CONFIRMED", "HEALTHY-UNCONFIRMED"):
            issue_n, skill_n = issue_skill_key(e)
            dedup_key = f"health:{issue_n}:{skill_n}:{health['state']}"
            if _sp.ledger_check_and_stamp(dedup_key):
                anomaly_count += 1
                print(f"[health] {key}: {health['state']} — "
                      f"{health['detail']} -> {health['next_action']}")
        if health.get("flapping"):
            # 이슈 #2969: 짧은 창 안에서 왕복한 verdict 는 그 자체가 결함
            # 신호다 — 두 독립된 보고가 조용히 지나가지 않게 원장과
            # 무관하게 매번 찍는다(위 dedup 은 verdict 자체의 반복만
            # 거른다, flapping 신호는 그 dedup 을 우회해야 보인다).
            anomaly_count += 1
            print(f"[flapping] {key}: verdict 가 {FLAPPING_WINDOW_SEC // 60}분 "
                  f"창 안에서 왕복함 — 지금 {health['state']}, 두 관측이 서로 "
                  "모순됐을 수 있다, 사람이 확인 필요")
        if anomalies:
            anomaly_count += 1
            # name the signal class(es) inline, reusing each anomaly's existing "class: detail" label
            classes = dict.fromkeys(a.split(":", 1)[0] for a in anomalies)
            print(f"[watchdog] {key}: 이상 신호 {len(anomalies)}건 ({', '.join(classes)})")
            for a in anomalies:
                print(f"  - {a}")
        else:
            print(f"[watchdog] {key}: 정상")
    _sp._watchdog_state_save(state)
    if not anomaly_count:
        print("이상 신호 없음")
    return anomaly_count

