#!/usr/bin/env python3
"""역할별 플러그인 환경으로 에이전트를 띄운다. on-the-record 의 핵심 동작 하나.

  python3 spawn.py <역할> <맡길 일> [-C <작업 디렉터리>] [--dry-run]
  python3 spawn.py review "PR 12 를 리뷰해라"
  python3 spawn.py qa "/testrun:testrun smoke" -C ~/work/some-repo

**왜 스크립트가 필요한가**: `--settings` 는 덮어쓰기가 아니라 **병합**이다. 역할
파일에 qa 플러그인만 적어도 사용자 전역 설정의 플러그인 17개가 그대로 딸려온다 —
"코딩 에이전트가 qa 룰북까지 본다"는 원래 문제의 다른 얼굴이다. 전역 목록을 읽어
역할이 켜지 않은 것을 전부 `false` 로 덮어야 격리가 성립한다(실측 확인).

`--settings` 는 사용자 설정보다 우선순위가 높으므로 이 덮어쓰기가 이긴다.

**CLAUDE_CONFIG_DIR 로 통째 격리하지 않는 이유**: 설정은 완전히 갈리지만 macOS
키체인 항목이 설정 디렉터리에 묶여 있어 인증이 끊긴다("Not logged in"). 인증을
그대로 쓰는 것이 컨테이너 대신 샌드박스를 고른 이유이므로, 그 이점을 버리지 않는다.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import contextlib
import re
import fcntl
import hashlib
import io
import json
import math
import os
import signal
import stat
import string
import subprocess
import sys
import traceback
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Issue #2105 extraction 1/N: relay / returned-PR machinery lives in relay.py.
# spawn.py stays the entry point and re-exports the moved names so external
# callers and the test suite keep addressing them as `spawn.<name>`. relay
# resolves every cross-module reference through the module object injected
# here, so `mock.patch.object(spawn, ...)` patches stay visible to the moved
# code (also correct when this file runs as `__main__`).
sys.path.insert(0, str(ROOT))
import relay
# The canonical import name ("spawn") and the CLI entry ("__main__") own the
# binding; a side-load under another name (e.g. tests loading spawn.py as
# "spawn_mod" via importlib) must not steal it from the canonical module, or
# `mock.patch.object(spawn, ...)` patches would stop reaching relay.
if relay._sp is None or __name__ in ("spawn", "__main__"):
    relay._sp = sys.modules[__name__]
_open_role_prs = relay._open_role_prs
_undispositioned_role_prs = relay._undispositioned_role_prs
_print_returned_pr_surfaced = relay._print_returned_pr_surfaced
_STRANDED_PUSH_COMMENT_MARKER = relay._STRANDED_PUSH_COMMENT_MARKER
_post_stranded_push_comment = relay._post_stranded_push_comment
_subject_issue_state = relay._subject_issue_state
_flag_stale_returned_branch = relay._flag_stale_returned_branch
_current_issue_task_text = relay._current_issue_task_text
ensure_pushed = relay.ensure_pushed

# Issue #2105 extraction 2/N: roster / spawn-claim / lease machinery lives in
# roster.py. Same mechanism as relay.py above: spawn.py stays the entry point
# and re-exports the moved names; roster resolves every cross-module reference
# through the module object injected here, so `mock.patch.object(spawn, ...)`
# patches stay visible to the moved code.
import roster
if roster._sp is None or __name__ in ("spawn", "__main__"):
    roster._sp = sys.modules[__name__]
_roster_locked = roster._roster_locked
_roster_load = roster._roster_load
_roster_save = roster._roster_save
_roster_own = roster._roster_own
_watcher_looks_real = roster._watcher_looks_real
_alive = roster._alive
roster_register = roster.roster_register
roster_remove = roster.roster_remove
_declared_wait = roster._declared_wait
_declared_wait_object_exists = roster._declared_wait_object_exists
_declared_wait_valid = roster._declared_wait_valid
_lease_progress_indicator = roster._lease_progress_indicator
lease_renew = roster.lease_renew
_lease_requeue = roster._lease_requeue
_sweep_completion_in_flight = roster._sweep_completion_in_flight
deadman_mark = roster.deadman_mark
deadman_check = roster.deadman_check
lease_reconcile_sweep = roster.lease_reconcile_sweep
_spawn_claim_path = roster._spawn_claim_path
_acquire_spawn_claim = roster._acquire_spawn_claim
_rewrite_spawn_claim_pid = roster._rewrite_spawn_claim_pid
_release_spawn_claim = roster._release_spawn_claim

# Issue #2105 extraction 3/N: ledger + gh plumbing lives in plumbing.py. Same
# mechanism as relay.py/roster.py above: spawn.py stays the entry point and
# re-exports the moved names; plumbing resolves every cross-module reference
# through the module object injected here, so `mock.patch.object(spawn, ...)`
# patches stay visible to the moved code. NETWORK_TIMEOUT and
# RECONCILE_LEDGER_TTL_SEC moved with their functions (default-argument
# values bind at import time) and are re-exported by assignment below.
import plumbing
if plumbing._sp is None or __name__ in ("spawn", "__main__"):
    plumbing._sp = sys.modules[__name__]
_run_net = plumbing._run_net
_repo_slug_cache_clear = plumbing._repo_slug_cache_clear
_repo_slug = plumbing._repo_slug
_repo_name = plumbing._repo_name
_etag_cache_path = plumbing._etag_cache_path
_approval_record_path = plumbing._approval_record_path
_issue_comments_uncached = plumbing._issue_comments_uncached
_issue_comments_more_pages = plumbing._issue_comments_more_pages
_issue_comments = plumbing._issue_comments
_split_gh_api_i_output = plumbing._split_gh_api_i_output
_write_etag_cache = plumbing._write_etag_cache
_reconcile_ledger_lock_path = plumbing._reconcile_ledger_lock_path
_reconcile_ledger_locked = plumbing._reconcile_ledger_locked
_reconcile_ledger_load = plumbing._reconcile_ledger_load
_reconcile_ledger_save = plumbing._reconcile_ledger_save
ledger_check_and_stamp = plumbing.ledger_check_and_stamp
ledger_stamp = plumbing.ledger_stamp
ledger_write = plumbing.ledger_write
_resolve_gh_token = plumbing._resolve_gh_token
_git_env = plumbing._git_env
RECONCILE_LEDGER_TTL_SEC = plumbing.RECONCILE_LEDGER_TTL_SEC

# Issue #2105 extraction 4/N: the watchdog/health/board-sweep cluster lives
# in watchdog.py. Same mechanism as relay.py/roster.py/plumbing.py above:
# spawn.py stays the entry point and re-exports the moved names; watchdog
# resolves every cross-module reference through the module object injected
# here, so `mock.patch.object(spawn, ...)` patches stay visible to the moved
# code. Constants that feed import-time bindings (default args, derived
# paths) moved with their users and are re-exported by assignment below.
import watchdog
if watchdog._sp is None or __name__ in ("spawn", "__main__"):
    watchdog._sp = sys.modules[__name__]
POLL_STATE = watchdog.POLL_STATE
POLL_INTERVAL_SEC = watchdog.POLL_INTERVAL_SEC
poll_due = watchdog.poll_due
WATCHDOG_STATE = watchdog.WATCHDOG_STATE
WATCHDOG_SILENCE_MIN = watchdog.WATCHDOG_SILENCE_MIN
WATCHDOG_NO_COMMIT_MIN = watchdog.WATCHDOG_NO_COMMIT_MIN
WATCHDOG_DENIAL_THRESHOLD = watchdog.WATCHDOG_DENIAL_THRESHOLD
WATCHDOG_HEARTBEAT_ONLY_MIN = watchdog.WATCHDOG_HEARTBEAT_ONLY_MIN
_DELEGATION_RE = watchdog._DELEGATION_RE
_watchdog_state_load = watchdog._watchdog_state_load
_watchdog_state_save = watchdog._watchdog_state_save
_classify_log_lines_heartbeat_only = watchdog._classify_log_lines_heartbeat_only
_HEALTH_REFUSAL_TYPES = watchdog._HEALTH_REFUSAL_TYPES
DEADLOCK_MIN_REPEATS = watchdog.DEADLOCK_MIN_REPEATS
_deadlock_signature = watchdog._deadlock_signature
_pr_state_from_index = watchdog._pr_state_from_index
diagnose_health = watchdog.diagnose_health
_session_resume_claim = watchdog._session_resume_claim
_resume_orchestrator_session = watchdog._resume_orchestrator_session
_maybe_resume_for_ready_pr = watchdog._maybe_resume_for_ready_pr
_REQ_ID_RE = watchdog._REQ_ID_RE
_NORTHPOLE_REQ_RE = watchdog._NORTHPOLE_REQ_RE
_requirement_drift_cache_path = watchdog._requirement_drift_cache_path
_load_requirement_drift_cache = watchdog._load_requirement_drift_cache
_save_requirement_drift_cache = watchdog._save_requirement_drift_cache
_fetch_issue_or_pr_via_cache = watchdog._fetch_issue_or_pr_via_cache
_board_read = watchdog._board_read
_board_pr_index = watchdog._board_pr_index
_DIGEST_LIVE_ENTRY_RE = watchdog._DIGEST_LIVE_ENTRY_RE
parse_digest_live_entries = watchdog.parse_digest_live_entries
requirement_drift = watchdog.requirement_drift
_roster_target_repos = watchdog._roster_target_repos
_board_wide_sweep_all = watchdog._board_wide_sweep_all
_WATCHDOG_GH_BUDGET_CLASSES = watchdog._WATCHDOG_GH_BUDGET_CLASSES
_HEAD_REF_SUBJECT_RE = watchdog._HEAD_REF_SUBJECT_RE
_board_wide_sweep = watchdog._board_wide_sweep
WATCHDOG_LOCK_PATH = watchdog.WATCHDOG_LOCK_PATH
WATCHDOG_FRESHNESS_STATE_PATH = watchdog.WATCHDOG_FRESHNESS_STATE_PATH
_proc_start_time = watchdog._proc_start_time
watchdog_lock_acquire = watchdog.watchdog_lock_acquire
_cross_workspace_board_sweep_lock_path = watchdog._cross_workspace_board_sweep_lock_path
cross_workspace_board_sweep_lock_acquire = watchdog.cross_workspace_board_sweep_lock_acquire
watchdog_current_head = watchdog.watchdog_current_head
watchdog_freshness_check = watchdog.watchdog_freshness_check
watchdog_canonical_guard = watchdog.watchdog_canonical_guard
STANDING_RED_STATE = watchdog.STANDING_RED_STATE
STANDING_RED_CADENCE_MIN = watchdog.STANDING_RED_CADENCE_MIN
_PYTEST_FAILED_RE = watchdog._PYTEST_FAILED_RE
_standing_red_state_load = watchdog._standing_red_state_load
_standing_red_state_save = watchdog._standing_red_state_save
_standing_red_tree_hash = watchdog._standing_red_tree_hash
_standing_red_load_contract = watchdog._standing_red_load_contract
_standing_red_parse_failed_ids = watchdog._standing_red_parse_failed_ids
standing_red_check = watchdog.standing_red_check
roster_watchdog = watchdog.roster_watchdog

# Issue #2105 extraction 5/N: the session-events/workspace-index/watch
# cluster lives in events.py. Same mechanism as the four extractions above:
# spawn.py stays the entry point and re-exports the moved names; events.py
# resolves every cross-module reference through the module object injected
# here, so `mock.patch.object(spawn, ...)` patches stay visible to the
# moved code. Import-time constants moved with their users and are
# re-exported by assignment below.
import events
if events._sp is None or __name__ in ("spawn", "__main__"):
    events._sp = sys.modules[__name__]
EVENTS_SUFFIX = events.EVENTS_SUFFIX
OFFSET_SUFFIX = events.OFFSET_SUFFIX
WATCH_CRASH_RC = events.WATCH_CRASH_RC
WATCH_WALLCLOCK_RC = events.WATCH_WALLCLOCK_RC
WORKSPACE_INDEX = events.WORKSPACE_INDEX
_GATE_DENY_RE = events._GATE_DENY_RE
_GATE_HOOK_RE = events._GATE_HOOK_RE
_HARNESS_REFUSAL_PATTERNS = events._HARNESS_REFUSAL_PATTERNS
_LEGACY_WORKSPACE_KEY_RE = events._LEGACY_WORKSPACE_KEY_RE
_PROGRESS_BASH_PREFIXES = events._PROGRESS_BASH_PREFIXES
_PR_URL_RE = events._PR_URL_RE
_SANDBOX_REFUSAL_PATTERNS = events._SANDBOX_REFUSAL_PATTERNS
_ambiguous_watch_exit = events._ambiguous_watch_exit
_append_event = events._append_event
_await_bounded = events._await_bounded
_classify_refusal_text = events._classify_refusal_text
_count_structural_denials = events._count_structural_denials
_event_count = events._event_count
_events_path = events._events_path
_flush_correlated_refusals = events._flush_correlated_refusals
_flush_unverified = events._flush_unverified
_git_head = events._git_head
_live_roster_matches = events._live_roster_matches
_live_session_start_index = events._live_session_start_index
_lookup_roster_entry = events._lookup_roster_entry
_lookup_workspace_entry = events._lookup_workspace_entry
_offset_path = events._offset_path
_origin_pr_prefix = events._origin_pr_prefix
_prior_event_details = events._prior_event_details
_read_offset = events._read_offset
_rearm_watcher_detached = events._rearm_watcher_detached
_repo_identity = events._repo_identity
_roster_fallback_entry = events._roster_fallback_entry
_tool_result_text = events._tool_result_text
_watch = events._watch
_watch_all = events._watch_all
_workspace_index_load = events._workspace_index_load
_workspace_index_locked = events._workspace_index_locked
_workspace_index_put = events._workspace_index_put
_write_offset = events._write_offset

# Issue #2105 extraction 6/N: the consult / verb / judge / panel machinery
# lives in consult.py. Same mechanism as the five extractions above:
# spawn.py stays the entry point and re-exports the moved names; consult.py
# resolves every cross-module reference through the module object injected
# here, so `mock.patch.object(spawn, ...)` patches stay visible to the
# moved code. Import-time constants moved with their users and are
# re-exported by assignment below.
import consult
if consult._sp is None or __name__ in ("spawn", "__main__"):
    consult._sp = sys.modules[__name__]
CONSULT_TIMEOUT = consult.CONSULT_TIMEOUT
SKILL_JUDGE_TIMEOUT_DEFAULT = consult.SKILL_JUDGE_TIMEOUT_DEFAULT
PANEL_TIMEOUT = consult.PANEL_TIMEOUT
JUDGE_TIMEOUT = consult.JUDGE_TIMEOUT
JUDGE_MAX_ROLES_PER_MERGE = consult.JUDGE_MAX_ROLES_PER_MERGE
_JUDGE_EXCLUDED_CORE_PLUGINS = consult._JUDGE_EXCLUDED_CORE_PLUGINS
_JUDGE_ROLE_EXCLUSIONS = consult._JUDGE_ROLE_EXCLUSIONS
_PanelMessagingUnavailable = consult._PanelMessagingUnavailable
_VERB_INSTRUCTIONS = consult._VERB_INSTRUCTIONS
_VERB_JSON_SHAPE = consult._VERB_JSON_SHAPE
_VERB_REQUIRED_KEY = consult._VERB_REQUIRED_KEY
_append_consult_trace = consult._append_consult_trace
_append_judge_trace = consult._append_judge_trace
_append_panel_turn = consult._append_panel_turn
_commit_consult_trace = consult._commit_consult_trace
_compress_diff = consult._compress_diff
_consult_cmd_and_env = consult._consult_cmd_and_env
_consult_evidence_suffix = consult._consult_evidence_suffix
_consult_or_record_error = consult._consult_or_record_error
_consult_root = consult._consult_root
_consult_trace_path = consult._consult_trace_path
_cross_family_skill_matches_with_consult = consult._cross_family_skill_matches_with_consult
_evidence_stamp_summary = consult._evidence_stamp_summary
_extract_sendmessage_turns = consult._extract_sendmessage_turns
_judge_cmd_and_env = consult._judge_cmd_and_env
_judge_prefilter = consult._judge_prefilter
_judge_roles_run_today = consult._judge_roles_run_today
_judge_trace_path = consult._judge_trace_path
_judge_validate = consult._judge_validate
_panel_degrade = consult._panel_degrade
_panel_record_path = consult._panel_record_path
_panel_slug = consult._panel_slug
_parse_consult_verdict = consult._parse_consult_verdict
_parse_verb_json = consult._parse_verb_json
_persist_consult_raw_output = consult._persist_consult_raw_output
_readonly_bash_allow = consult._readonly_bash_allow
_readonly_plugin_dirs = consult._readonly_plugin_dirs
_readonly_settings = consult._readonly_settings
_run_panel_session = consult._run_panel_session
_skill_judge_consult = consult._skill_judge_consult
_skill_judge_timeout = consult._skill_judge_timeout
_verb_cmd = consult._verb_cmd
consult_cmd = consult.consult_cmd
draft_cmd = consult.draft_cmd
ideate_cmd = consult.ideate_cmd
judge_cmd = consult.judge_cmd
panel_cmd = consult.panel_cmd
review_cmd = consult.review_cmd

# 이슈 #1274: roster_watchdog() 의 반환값(anomaly count, rc>=0)과 절대 겹치지
# 않도록 고른 예약 종료 코드 — watchdog CLI 분기가 처리 못 한 예외를 이
# 코드로 종료해, 파이썬 기본 트레이스백 종료(exit 1)가 anomaly_count==1 과
# 구분 안 되는 문제를 없앤다. poll-heartbeat.sh 는 rc>=128(시그널 사망) 이거나
# rc==이 값일 때만 [watchdog-crash] 를 찍는다.
WATCHDOG_CRASH_SENTINEL = 97
# 이슈 #1456: #1360 재발(구코드를 5시간 물고 있던 워치독) 방지용 예약
# 종료 코드 — WATCHDOG_CRASH_SENTINEL 과 마찬가지로 roster_watchdog() 의
# 정상 반환값(anomaly count, rc>=0)과 겹치지 않게 고른 상수다.
WATCHDOG_LOCKED_SENTINEL = 96          # 이미 다른 인스턴스가 락을 쥐고 있다
WATCHDOG_STALE_CODE_SENTINEL = 95      # 체크아웃 HEAD 가 시작 시점과 달라졌다
WATCHDOG_NONCANONICAL_SENTINEL = 94    # 워치독 자신이 canonical 체크아웃 밖이다

# 이슈 #878: 오케스트레이터 자신의 (headless `-p`) 세션 ID를 전달하는 환경
# 변수 이름 — 이 프로세스(spawn.py)를 부른 오케스트레이터 프로세스가 이미
# 알고 있을 때만(interactive 세션은 모른다/필요없다; harness driver 는
# `claude -p --output-format json` 의 첫 턴 결과에서 얻은 뒤 다음 스폰부터
# export 한다) 심어준다. 이름 자체는 새 스케줄러가 아니라 기존 roster 엔트리
# 필드 하나를 채우는 관례일 뿐이다.
ORCHESTRATOR_SESSION_ID_ENV = "ORCHESTRATOR_SESSION_ID"
# 이슈 #878 after-proposal hunt 발견: session_id 는 프로세스 단위지 roster
# 엔트리 단위가 아니다 — 같은 오케스트레이터 세션이 무장한 여러 엔트리가
# 같은 폴 창에서 동시에 ready 가 되면 이 TTL 로 session_id 당 딱 한 번만
# resume-invoke 가 나가게 한다(ledger_check_and_stamp 를 그대로 락으로
# 재사용, 새 락 프리미티브를 만들지 않는다).
SESSION_RESUME_CLAIM_TTL_SEC = 15 * 60
USER_SETTINGS = Path.home() / ".claude" / "settings.json"

# 이슈 #857: 로스터(ROSTER)/워크스페이스 인덱스(WORKSPACE_INDEX)가 기본으로
# 가리키는 상태 루트. 기본값은 기존 동작과 동일(설치 디렉터리 아래
# runs/) — MUSTER_STATE_ROOT 를 주면 그쪽을 대신 쓴다. 하네스가 띄우는
# fixture 세션에 관측 세션과 다른 값을 주면, 같은 플러그인 설치를
# 공유하고 같은 --issue 번호를 써도 로스터/워크스페이스 인덱스 파일
# 자체가 물리적으로 갈려 서로의 항목을 볼 수 없다(PR #855 finding 5).
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")

NETWORK_TIMEOUT = plumbing.NETWORK_TIMEOUT   # fetch/pull/push (moved with _run_net)
CLONE_TIMEOUT = 180    # clone — bigger initial transfer


_BOOTSTRAP_TIMING: dict[str, float] = {}
_BOOTSTRAP_PHASES = ("workspace", "branch", "rulebook", "core", "gh_token", "settings",
                     "cross_family")


@contextlib.contextmanager
def _timed(phase: str):
    """부트스트랩 단계 하나의 소요 시간을 `_BOOTSTRAP_TIMING`에 누적한다
    (이슈 #711) — `_spawn_one` 제어 흐름·종료 코드는 그대로, 측정만 덧붙인다."""
    t0 = time.monotonic()
    try:
        yield
    finally:
        _BOOTSTRAP_TIMING[phase] = _BOOTSTRAP_TIMING.get(phase, 0.0) + (time.monotonic() - t0)


def _bootstrap_timing_line(role: str) -> str:
    parts = [f"{p}={_BOOTSTRAP_TIMING.get(p, 0.0):.3f}" for p in _BOOTSTRAP_PHASES]
    total = sum(_BOOTSTRAP_TIMING.get(p, 0.0) for p in _BOOTSTRAP_PHASES)
    parts.append(f"total={total:.3f}")
    return f"[{role}] bootstrap_timing " + " ".join(parts)


def _rulebook_ttl_min() -> float:
    v = os.environ.get("MUSTER_RULEBOOK_TTL")
    if v is None:
        return 15.0
    try:
        return float(v)
    except ValueError:
        return 15.0


def _ttl_marker(d: Path) -> Path:
    """클론 밖, `runs/` 아래 마커를 둔다(이슈 #296) — 클론 안에 두면
    untracked 파일이 남아 `git status --porcelain` 이 영영 비지 않고,
    그 결과 `(커밋 안 된 변경 있음)`/`+커밋안됨` 이 모든 클론에 상시로 붙는다."""
    key = hashlib.sha256(str(d.resolve()).encode()).hexdigest()[:16]
    return ROOT / "runs" / "ttl-markers" / key


def _pull_is_fresh(d: Path) -> bool:
    """TTL 창 안이면 True — 이번엔 `git pull` 을 건너뛴다(이슈 #285 P4).
    `MUSTER_RULEBOOK_TTL=0` 이면 항상 False(매번 pull, 오늘의 동작)."""
    ttl_min = _rulebook_ttl_min()
    if ttl_min <= 0:
        return False
    m = _ttl_marker(d)
    try:
        age_s = time.time() - m.stat().st_mtime
    except OSError:
        return False
    return age_s < ttl_min * 60


def _mark_pulled(d: Path) -> None:
    try:
        marker = _ttl_marker(d)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(time.time()))
    except OSError:
        pass


def _migrate_legacy_ttl_marker(d: Path) -> None:
    """이슈 #313: #297 은 새 마커를 쓸 곳만 `runs/ttl-markers/` 로
    옮겼다 — pre-#297 코드가 클론 안에 이미 써 둔 `.muster-last-pull` 은
    그대로 남아, 지우기 전까진 `git status --porcelain` 이 영영 비지
    않는다(untracked, gitignore 안 됨). 그 결과 `checkout_version()` 의
    dirty 접미사가 그 클론에 매 spawn 마다 상시로 붙는다. 매번 확인해서
    지운다 — 있으면 지우고 없으면 조용히 넘어간다(그 자체로 멱등)."""
    legacy = d / ".muster-last-pull"
    try:
        legacy.unlink()
    except OSError:
        pass


def _mkt(d: Path) -> Path:
    return d / ".claude-plugin" / "marketplace.json"


def _rulebook_lock_path(d: Path) -> Path:
    """`d` 옆에 두는 락 파일 경로 — 클론 디렉터리 안이 아니라 형제
    (`git status --porcelain` 을 깨끗하게 유지, #296 의 TTL 마커와 같은 이유)."""
    return d.parent / (d.name + ".lock")


@contextlib.contextmanager
def _locked_rulebook_dir(d: Path):
    """`d` 를 채우는(clone/pull) 구간을 프로세스 간에 직렬화한다. `ROSTER` 의
    lock 패턴(spawn.py:1732-1739)과 동일한 `fcntl.flock` 관용구 — 커널이
    보유 프로세스가 죽으면 자동으로 lock 을 푼다, 그래서 별도 stale-lock
    회수 코드가 필요 없다(issue #773)."""
    lock_path = _rulebook_lock_path(d)
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        f = open(lock_path, "w")
    except OSError:
        # 부모 디렉터리를 만들거나 락 파일을 열 수 없다(예: 읽기 전용
        # 루트) — 락 없이 진행한다. 아래 clone/pull 자체가 곧 같은 이유로
        # 실패해 fail-closed 로 떨어진다.
        yield
        return
    with f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def self_hosted_hooks(cwd: str) -> dict | None:
    """스폰 대상이 on-the-record 자기 자신이면 그 hooks.json 의 "hooks" 값을,
    아니면 None 을 돌려준다(이슈 #508).

    자기 자신 판정은 `<cwd>/on-the-record/hooks/hooks.json` 존재 여부다 — 이
    저장소는 플러그인 매니페스트를 `on-the-record/` 서브디렉터리에 담고
    있고, 자기 자신을 스폰 대상으로 삼을 때만 그 경로가 cwd 아래 나타난다.
    체크인된 `.claude/settings.json` 을 쓰지 않는 이유는
    `require_no_repo_config`(스폰이 임의 대상 레포에 대해 도는 별도 검사)와
    충돌하기 때문 — 여기서 --settings 임시 파일에 병합해 넣으면 그 검사를
    아예 건드리지 않는다.

    `${CLAUDE_PLUGIN_ROOT}` 는 컨슈머 설치 경로에서는 Claude CLI 가
    `--plugin-dir` 로 채우지만, 여기서는 그 경로로 로드하지 않으므로 직접
    치환한다 — on-the-record 레포 안의 플러그인 루트로.
    """
    root = Path(cwd).resolve()
    hooks_path = root / "on-the-record" / "hooks" / "hooks.json"
    if not hooks_path.is_file():
        return None
    try:
        raw = hooks_path.read_text()
    except OSError as e:
        print(f"self_hosted_hooks: {hooks_path} 를 못 읽어 훅 주입을 건너뛴다: {e}",
              file=sys.stderr)
        return None
    plugin_root = str(hooks_path.parent.parent)
    text = raw.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)
    try:
        parsed = json.loads(text)
    except ValueError as e:
        # 여기서 조용히 None 을 돌려주면 self-hosted 세션이 훅 없이 정상
        # 종료처럼 보인다 — 깨진 hooks.json 이 "가드가 다 붙었다"로 오독되는
        # 케이스다(실측: before-landing hunt, issue #508).
        print(f"self_hosted_hooks: {hooks_path} 파싱 실패, 훅 주입을 건너뛴다: {e}",
              file=sys.stderr)
        return None
    return parsed.get("hooks")


def _workspace_bash_allow(cwd: str) -> list[str]:
    """이슈 #558: 이 스폰의 격리된 워크스페이스(cwd) 안에서 정당한 venv
    생성/pip install/워크스페이스 test/ 스크립트 실행을 스폰 시점에 미리
    허용한다. `Bash(cd {cwd}*)` 처럼 `cd` 뒤에 트레일링 와일드카드만 붙이면
    `cd {cwd} && rm -rf ~` 같은 임의 셸까지 통과한다 — after-proposal
    warrant-hunt(stance 0)가 잡아낸 실패 모양이라, 각 항목은 `cd` 뒤에 올
    명령 자체까지 구체적으로 명시한다. `cwd` 는 *어디*를, 나머지 패턴은
    *무엇*을 좁힌다 — 이 스폰과 다른 cwd 를 받은 스폰은 다른 문자열을
    받는다."""
    venv = f"{cwd}/venv"
    return [
        f"Bash(cd {cwd} && python3 -m venv venv)",
        f"Bash(python3 -m venv {venv})",
        f"Bash(cd {cwd} && {venv}/bin/pip install *)",
        f"Bash({venv}/bin/pip install *)",
        f"Bash(cd {cwd} && python3 test/*.py)",
        f"Bash(cd {cwd} && {venv}/bin/python3 test/*.py)",
    ]


def role_settings(role: str, cwd: str | None = None,
                   inject_self_hosted_hooks: bool = True) -> dict:
    """역할의 샌드박스 경계 + 전역 플러그인 차단.

    **룰북을 켜는 일은 여기서 하지 않는다.** 그건 `--plugin-dir` 이 한다
    (plugin_dirs 참고). 설정으로 켜려면 마켓플레이스를 등록하고 설치해야
    하는데, 그 경로에는 조용한 함정이 셋 있고 전부 "의도한 것과 다른 커밋이
    붙는다"로 끝난다.

    남는 일은 두 가지다: 역할이 선언한 샌드박스를 펼치는 것, 그리고 사용자
    전역 플러그인을 빠짐없이 끄는 것. 후자는 `--settings` 가 교체가 아니라
    **병합**이라 필요하다 — 안 끄면 qa 룰북만 적은 세션에 전역 17개가 딸려
    온다.
    """
    f = ROOT / "roles" / f"{role}.json"
    if not f.exists():
        have = ", ".join(sorted(p.stem for p in (ROOT / "roles").glob("*.json")))
        sys.exit(f"모르는 역할: {role}  (있는 것: {have})")
    spec = json.loads(f.read_text())

    s = {k: v for k, v in spec.items() if k not in ("marketplace", "path", "repo")}

    # 역할 파일의 env 는 **기본값**이지 강제가 아니다. 이미 환경에 있으면 그쪽이 이긴다 —
    # 안 그러면 bench 처럼 격리된 워크스페이스를 넘기려는 호출이 조용히 무시되고,
    # 실행이 실제 워크스페이스에 쓰게 된다(실제로 그렇게 오염시켰다).
    # 역할 파일이 기본값으로 적은 값 자체에도 `~` 와 `$VAR` 가 들어갈 수 있다 —
    # 절대경로를 박지 않으려면 그래야 한다. 여기서 먼저 펴지 않으면 아래의
    # safe_substitute 는 한 번만 도므로 `$QA_WORKSPACE` → `$HOME/...` 로 끝나고,
    # 안 풀린 `$` 때문에 역할이 아예 안 뜬다(실측 2026-07-27: qa 가 그랬다).
    for k in list(s.get("env", {})):
        if k in os.environ:
            s["env"][k] = os.environ[k]
        else:
            v = s["env"][k]
            if isinstance(v, str):
                s["env"][k] = os.path.expanduser(os.path.expandvars(v))

    # 샌드박스 경로는 그 env 를 **참조**해야 한다. 같은 값을 두 곳에 적으면 위의
    # 덮어쓰기가 조용히 무력화된다 — env 는 격리된 경로를 가리키는데 경계는 원래
    # 경로만 허용하는 상태가 되고, 그건 "격리했다고 믿는 오염"이다.
    # 해석된 env 를 기준으로 펼친다: 역할 파일이 선언했지만 os.environ 에 없는
    # 값도 있고, 환경이 이긴 값도 여기 이미 반영돼 있다.
    resolved = {**os.environ, **s.get("env", {})}
    fs = s.get("sandbox", {}).get("filesystem", {})
    for key in ("allowWrite", "denyWrite", "denyRead"):
        if key in fs:
            fs[key] = [string.Template(p).safe_substitute(resolved) for p in fs[key]]
            unresolved = [p for p in fs[key] if "$" in p]
            if unresolved:
                # 안 풀린 변수를 그대로 넘기면 경계가 존재하지 않는 경로를 가리킨다.
                sys.exit(f"[{role}] sandbox.filesystem.{key} 의 변수를 풀 수 없다: "
                         f"{', '.join(unresolved)}")

    # 이슈 #695: 롤-세션 샌드박스를 role_settings() 가 중앙에서 끈다.
    # roles/*.json 이 어떤 sandbox.enabled 값을 선언하든 여기서 무조건
    # 거짓으로 강제한다 — 반복된 차단 버그(#38/#58/#65/#72/#153, 2026-08-11
    # tas 리포트)의 비용이 경계의 보호 가치를 넘어섰다는 운영자 결정.
    # 이 결과로 예전에 여기 있던 레지스트리/웹 도메인 병합(#38/#58),
    # 기본값 스위치 개방(#72), 패키지 캐시 allowRead 마운트(#38)는 전부
    # 도달 불가능해져 issue-695 에서 함께 제거했다.
    if "sandbox" in s:
        s["sandbox"]["enabled"] = False

    # 전역 플러그인은 전부 끈다. 켜야 할 것을 적는 게 아니라 꺼야 할 것을
    # 빠짐없이 적는 쪽이라, 전역에 플러그인이 새로 깔려도 새지 않는다.
    s["enabledPlugins"] = {}
    try:
        globals_ = json.loads(USER_SETTINGS.read_text()).get("enabledPlugins", {})
    except (OSError, ValueError):
        globals_ = {}
    for name in globals_:
        s.setdefault("enabledPlugins", {}).setdefault(name, False)

    # 갱신 — 이슈 #742 (2026-08-11): 아래 세 문단(WebSearch/WebFetch/Read/
    # Grep/Glob, 워크스페이스-bash 패턴, MUSTER_MCP_ALLOW)이 서술하는
    # "permissions.allow 에 규칙이 없으면 거부된다" 는 판정 근거는 #58/#65/
    # #153/#558 당시(headless 세션이 --permission-mode acceptEdits 로 떴던
    # 시절)의 것이다. #700(커밋 b762681, 2026-08-11 10:38)이 실제 롤 스폰
    # 경로(spawn_cmd()/consult_cmd())를 --permission-mode bypassPermissions
    # 로 옮긴 뒤로는 이 permissions.allow 목록 전체가 그 경로들에서 더 이상
    # 판정에 관여하지 않는다 — Anthropic 문서
    # (code.claude.com/docs/en/permission-modes): "Allow rules have no
    # effect in bypassPermissions because everything else is already
    # approved." 이슈-742 phase-1 조사가 이 사실을 4패턴 라이브 프로브로
    # 실측했다(거부 0건). bypassPermissions 아래서 도구 호출을 실제로
    # 판정하는 층은 PreToolUse/PermissionRequest 훅뿐이다.
    #
    # 그런데도 목록을 지우지 않는 이유 둘: (1) role_settings() 는
    # `--dry-run` 경로(main() 의 a.dry_run 분기)에서도 호출되는데 그
    # 경로는 claude 프로세스를 아예 안 띄우므로 permission-mode 자체가
    # 없다 — 거기 출력되는 permissions.allow 는 이 함수가 만드는 그대로다;
    # (2) 롤 스폰이 bypassPermissions 아닌 모드로 되돌아가면(#700 이전
    # 상태) 이 목록이 그 즉시 다시 유효한 경계가 된다 — 지금 지우면 그
    # 되돌림이 이 항목들 없이 조용히 일어난다.
    #
    # WebSearch/WebFetch 는 두 층에서 막힌다(이슈 #65, #58 후속). #58 은 샌드박스
    # NETWORK 층(allowedDomains)만 열었다 — TOOL-PERMISSION 층은 별개로, (당시)
    # headless 세션은 --permission-mode acceptEdits 로 뜨고 답할 사람이 없어서
    # permissions.allow 에 규칙이 없는 도구는 그냥 거부됐다(#58 조사가 놓친 지점).
    # 모든 역할에 적용한다(#58 과 동일한 operator 결정: option B) — 샌드박스
    # 활성 여부와 무관하다, 이 층은 샌드박스가 아니라 CLI 권한 프롬프트이므로.
    # Read/Grep/Glob 도 같은 이유로 추가한다(이슈 #153) — 읽기 전용 조회이고
    # 도달 가능한 경로는 여전히 sandbox.filesystem.allowRead/denyRead 가 정한다;
    # 이 층은 그 경계를 넓히지 않는다. Bash 하위 패턴은 "읽기 전용"으로 안전하게
    # 한정할 수 없어 제외한다(survey 3절).
    allow = s.setdefault("permissions", {}).setdefault("allow", [])
    for tool in ("WebSearch", "WebFetch", "Read", "Grep", "Glob"):
        if tool not in allow:
            allow.append(tool)

    # 이슈 #558: 격리된 워크스페이스(cwd) 안에서 정당한 venv 생성/pip
    # install/워크스페이스 test/ 스크립트 실행은 하네스 권한(2층)에 막혔다
    # (당시) — headless 세션은 답할 사람이 없어 permissions.allow 에 없는
    # 명령은 그냥 거부됐다(2026-08-09 soongsil-course-registration 런
    # 실측; 위 갱신 문단 참고 — #700 이후 실제 롤 스폰에는 더 안 해당). 위의
    # Bash 하위 패턴 제외 사유(바로 위 주석)는 "경로 앵커 없는" 패턴에만
    # 해당한다 — 여기 항목은 이 스폰의 cwd 로 완전히 앵커링되므로 별개다.
    # cwd 가 없으면(레지스트리 점검 등 워크스페이스 없는 호출) 아무것도
    # 추가하지 않는다.
    if cwd is not None:
        for pattern in _workspace_bash_allow(cwd):
            if pattern not in allow:
                allow.append(pattern)

    # MUSTER_MCP_ALLOW: 같은 TOOL-PERMISSION 층 결함이 사용자가 직접 붙인
    # MCP 서버에도 그대로 있다 — 서버 연결은 되는데(`mcp_servers` 에
    # "connected" 로 뜬다) 도구 호출은 permissions.allow 에 규칙이 없어
    # #58/#65 와 똑같이 거부된다(실측: reasona issue-3, world-data MCP).
    # #58/#65 와 다른 점은 대상이 tokenmaxxxer 가 아는 고정 도구가 아니라
    # **사용자마다 다른 이름의 개인 MCP 서버**라는 것 — 코드에 이름을 박을
    # 수 없다. 그래서 운영자가 스폰 시점에 콤마로 나열한다
    # (MUSTER_ROLE_MODEL/MUSTER_AGENT_GH_TOKEN/MUSTER_WORK_DIR 와 같은
    # 환경변수 관례). 빈 문자열/공백뿐인 항목은 미설정과 동일하게 버린다.
    #
    # `mcp__` 접두사만 받는다 — 이 통로는 MCP 도구 permission 층의 구멍을
    # 메우는 것이 유일한 목적이고, Write/Edit/Bash 처럼 board-gate/
    # approval-gate 가 지키는 도구까지 여는 우회로가 되면 안 된다. 접두사가
    # 안 맞는 항목은 조용히 버린다 — 운영자가 실수로 `MUSTER_MCP_ALLOW=Bash`
    # 를 넣어도 게이트가 지키는 표면은 넓어지지 않는다.
    extra_mcp = [t.strip() for t in os.environ.get("MUSTER_MCP_ALLOW", "").split(",")
                 if t.strip().startswith("mcp__")]
    for tool in extra_mcp:
        if tool not in allow:
            allow.append(tool)

    # on-the-record 가 자기 자신을 대상으로 스폰할 때만, 자기 hooks.json 을
    # 병합해 넣는다 — 컨슈머 설치 경로 밖에서는 늘 inert 였다(이슈 #508).
    if cwd is not None and inject_self_hosted_hooks:
        injected = self_hosted_hooks(cwd)
        if injected:
            s["hooks"] = injected
    return s



# 역할 순서. 보드를 읽을 때 이 순서로 보여준다.
ROLES = ("product-discovery", "interaction-design", "technical-feasibility",
         "implementation", "execution-observation", "conformance-review",
         "defect-verification", "issue-retrospective", "release-engineering",
         "user-discovery", "requirements-engineering", "refactoring-legacy",
         "test-authoring", "observability", "incident-response",
         "capacity-planning", "knowledge-management",
         "ux-engineering", "api-design", "architecture", "security-threat-model",
         "data-modeling", "performance-engineering", "accessibility", "secure-coding",
         "ml-engineering", "data-engineering",
         "market-analysis", "finance-unit-economics", "pricing", "sales", "marketing",
         "growth-analytics", "customer-support", "partnerships-bd", "pr-communications",
         "risk-management", "legal-compliance",
         "technical-writing", "brand-design", "content-design", "localization", "devrel")
BOARD = "docs"                          # v3: subject trees live at docs/issue-<n>/
MARKER = "docs/specs/approvers.md"      # 보드 opt-in + 승인자 allowlist (v3)
REQUIREMENT_DIGEST_MARKER = "docs/specs/requirement-digest.md"  # issue #1695
# 계약 v1 이 쓰던 자리. 아직 v2 로 안 옮긴 레포를 **말해주기 위해서만** 본다
LEGACY = {"conformance-review": "review-record.md",
          "technical-feasibility": "feasibility-record.md",
          "release-engineering": "state.md",
          "product-discovery": "product-record.md"}


def slug(cwd: str) -> str:
    """레포 디렉터리 이름 (계약 v2 §9).

    v1 은 origin 리모트에서 <owner>-<repo> 를 뽑았는데, 그건 폐지된
    `$QA_WORKSPACE` 의 레포 간 경로 때문에만 있던 것이다. 리모트 없는 레포에서
    깨지지 않는 것이 §9 가 이 규칙을 고른 이유다.
    """
    return Path(cwd).resolve().name


def init_board(cwd: str, login: str | None = None) -> int:
    """대상 레포를 보드로 선언한다: docs/specs/approvers.md 를 만든다.

    v3: 계약 심기는 폐지됐다 — 정본은 core 플러그인에만 있고, 레포 사본은
    해시 검사로 강제 동일해져 정보량이 0이었다. 보드 표식이자 승인자
    allowlist 인 approvers.md 만 있으면 된다. **사용자의 파일이다** —
    이미 있으면 절대 덮지 않는다.
    """
    root = Path(cwd).resolve()
    dest = root / MARKER
    if dest.exists():
        print(f"이미 있다: {dest}")
        init_requirement_digest(cwd)
        return 0
    if not login:
        r = subprocess.run(["gh", "api", "user", "--jq", ".login"],
                           capture_output=True, text=True)
        login = r.stdout.strip() if r.returncode == 0 else ""
    if not login:
        sys.exit("승인자 로그인을 모른다. gh auth login 을 하거나 "
                 "init --login <github-login> 으로 준다.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"- {login}\n", encoding="utf-8")
    print(f"보드로 선언했다: {dest}  (approver: {login})")
    init_requirement_digest(cwd)

    # issue #2022: 로컬 작업 트리에만 쓰고 끝내면, 신선한 클론에서 스폰한
    # 세션이 approvers.md 를 못 봐서 board-gate 에 막혀 죽는다(실측:
    # skill-repository #50). 커밋하고 push 까지 해야 다음 스폰이 성공한다.
    rels = [MARKER]
    if (root / REQUIREMENT_DIGEST_MARKER).exists():
        rels.append(REQUIREMENT_DIGEST_MARKER)
    try:
        subprocess.run(["git", "-C", str(root), "add", *rels],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit",
                        "-m", "board-setup: init approvers.md",
                        "-m", "Subject: board-setup"],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"보드 파일을 커밋하지 못했다: "
                 f"{e.stderr.strip() if e.stderr else e}")
    push = subprocess.run(["git", "-C", str(root), "push"],
                          capture_output=True, text=True)
    if push.returncode != 0:
        sys.exit(f"보드 파일을 커밋했지만 push 하지 못했다 — 이 파일들이 "
                 f"리모트에 올라가기 전까지는 모든 스폰이 board-gate 에 막혀 "
                 f"실패한다: {push.stderr.strip() if push.stderr else push}")
    print(f"보드 파일을 커밋하고 push 했다.")
    return 0


def init_requirement_digest(cwd: str) -> bool:
    """대상 레포에 `docs/specs/requirement-digest.md` 스텁을 만든다
    (issue #1695).

    요구 연결 게이트(`require_requirement_linkage`)는 이슈 본문의 `R\\d+`
    인용만 보고 이 파일 자체를 읽지 않는다 — 새 레포에는 인용할 R-ID가
    아예 없어서 첫 스폰이 막힌다. 이 스텁은 사람이 첫 이슈에 R1 을 바로
    적어 넣을 수 있는 형식 예시를 준다. `gates/requirement_digest.py` 의
    생성기는 재사용하지 않는다 — 그건 `docs/specs/requirements.md` 레지스트리를
    읽어야 하는데, 갓 init 된 레포엔 그 파일도 없다.

    이미 있으면 절대 덮지 않는다 — approvers.md 와 같은 처분.
    """
    root = Path(cwd).resolve()
    dest = root / REQUIREMENT_DIGEST_MARKER
    if dest.exists():
        print(f"이미 있다: {dest}")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "# Requirement Digest\n"
        "\n"
        "이 레포가 향하는 살아있는 요구사항 목록. 요구 연결 게이트(issue #1017)는\n"
        "새로 드래프트되는 이슈 본문이 아래 형식의 R-ID를 인용하기를 기대한다.\n"
        "\n"
        "## R-entry format\n"
        "\n"
        "각 항목은 반드시 한 줄이다(줄바꿈 없음) — 그 안의 <설명> 과 <출처>는\n"
        "여러 절로 이루어진 자유 형식 텍스트여도 된다(issue #2077). 정확한\n"
        "문법(파서 — `spawn.py::requirement_drift` — 가 그대로 받아들이는 형태):\n"
        "\n"
        "  - R<n>: <설명, 자유 형식> [<status>] (source: <출처, 자유 형식>)\n"
        "\n"
        "<설명>과 <출처>는 쉼표·세미콜론·마침표를 포함한 여러 절이어도 되고,\n"
        "<출처>는 `#<issue-number>` 로 국한되지 않는다 — \"user directive\n"
        "2026-08-23, issue #1\" 처럼 issue 번호를 포함하지 않는 자유 텍스트도\n"
        "허용된다. `[<status>]` 는 공백 없는 단일 토큰이어야 한다.\n"
        "\n"
        "예(한 줄 설명):\n"
        "  - R1: 사용자가 X 를 할 수 있어야 한다 [enforced] (source: #12)\n"
        "\n"
        "예(문서화된 자유 형식 — multi-clause, 자유 형식 source):\n"
        "  - R1: A browser-playable character-growth RPG whose progression "
        "systems benchmark Random Dice 2 — deterministic no-gacha "
        "Dice-Tree acquisition, in-match merge 1→7 pips with 7-pip "
        "Awakening, Supporter-analog companions [live] (source: user "
        "directive 2026-08-23, issue #1)\n"
        "\n"
        "## Entries\n"
        "\n"
        "(아직 없음 — 첫 이슈를 드래프트할 때 R1 부터 여기에 추가한다)\n",
        encoding="utf-8")
    print(f"요구 원장 스텁을 만들었다: {dest}")
    return True


def require_board(cwd: str, override: bool) -> None:
    """대상 레포가 보드인지(approvers.md 가 있는지) 본다. 없으면 멈춘다.

    core 의 게이트가 어차피 보드·실행 쓰기를 거부하므로, 세션을 태우기 전에
    같은 사실을 말해주는 것뿐이다 — 버려질 세션에 과금하지 않는다.
    """
    root = Path(cwd).resolve()
    if (root / MARKER).is_file():
        return
    if override:
        return
    sys.exit(
        f"대상 레포에 {MARKER} 가 없다: {root}\n"
        f"  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:\n"
        f"    python3 spawn.py init -C {root}\n"
        f"  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.")


REPO_CONFIG = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks",
               ".claude/agents", ".mcp.json")


def require_no_repo_config(cwd: str, override: bool) -> None:
    """대상 레포가 자기 Claude 설정을 들고 있으면 멈춘다.

    **on-the-record 의 샌드박스는 이걸 못 막는다.** 설정 우선순위는
    `--settings` > `<레포>/.claude/settings.json` > `~/.claude/settings.json` 인데,
    on-the-record 는 양 끝만 읽고 가운데를 안 본다. 그리고 `hooks` 는 덮어쓰기가 아니라
    **더해지고**, 훅 명령은 선언한 `sandbox.filesystem` 정책을 받지 않는다.

    실측 2026-07-27. `denyWrite` 와 `denyRead` 를 선언한 역할 설정으로 띄웠는데,
    레포가 커밋해 둔 SessionStart 훅이 **denyWrite 경로에 쓰고 denyRead 인
    `~/.claude/settings.json` 을 읽어냈다.** 사용자 권한 그대로, 프롬프트 없이,
    `env={**os.environ}` 을 통째로 들고. 레포를 클론해서 on-the-record 를 겨눈 것만으로
    성립한다.

    계약 파일과 같은 처분을 한다 — 경고가 아니라 정지, 그리고 명시적 opt-out.
    사고가 아니라 결정이 되게.

    신뢰는 **내용 해시에 고정**된다: --trust-repo-config 로 한 번 통과시키면
    그 시점의 .claude/ 내용 다이제스트를 기록하고, 이후 스폰은 내용이 같을
    때만 자동 통과한다. 내용이 바뀌면 다시 멈춘다 — "어제 읽어본 훅"이 아닌
    "오늘 바뀐 훅"이 무검토로 도는 일을 막는다.
    """
    root = Path(cwd).resolve()
    rogue = [p for p in REPO_CONFIG if (root / p).exists()]
    if not rogue:
        return

    import hashlib
    h = hashlib.sha256()
    for rel in sorted(rogue):
        p = root / rel
        h.update(rel.encode())
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    h.update(str(f.relative_to(p)).encode())
                    h.update(f.read_bytes())
        else:
            h.update(p.read_bytes())
    digest = h.hexdigest()

    # MUSTER_TOKENMAXXXER_HOME: 실제 ~/.tokenmaxxxer 대신 쓸 경로. 테스트가
    # 실제 홈을 건드리지 않고 격리하기 위한 오버라이드(이슈#367) — 기본은
    # 그대로 Path.home().
    home_override = os.environ.get("MUSTER_TOKENMAXXXER_HOME")
    tokenmaxxxer_home = Path(home_override) if home_override else Path.home() / ".tokenmaxxxer"
    pins = tokenmaxxxer_home / "trusted-repo-config.json"
    try:
        table = json.loads(pins.read_text())
    except (OSError, ValueError):
        table = {}
    key = str(root)

    if override:
        table[key] = digest
        pins.parent.mkdir(parents=True, exist_ok=True)
        pins.write_text(json.dumps(table, indent=2))
        print(f"[trust] 레포 설정을 이 내용({digest[:12]})으로 신뢰 고정했다: "
              f"{', '.join(rogue)}", file=sys.stderr)
        return
    if table.get(key) == digest:
        return          # 전에 읽고 신뢰한 그 내용 그대로다

    changed = key in table
    sys.exit(
        f"대상 레포가 자기 Claude 설정을 들고 있다: {', '.join(rogue)}\n"
        f"  {root}\n"
        + ("  전에 신뢰했던 내용에서 **바뀌었다** — 다시 읽어보고 판단해야 한다.\n"
           if changed else "")
        + f"  그 훅들은 on-the-record 가 선언한 샌드박스 경계를 **받지 않는다**. 띄우면\n"
        f"  denyRead 로 막은 경로까지 읽힌다(실측). 내용을 직접 읽어보고,\n"
        f"  믿을 수 있으면 --trust-repo-config 로 명시한다 — 이 내용 해시로\n"
        f"  고정되어, 같은 내용인 동안은 다시 묻지 않는다.")


def require_acceptance_gate(cwd: str, issue: int | None) -> None:
    """issue #441: phase-2 세션은 이슈의 `## Acceptance` 가 실행가능한
    산출물을 가리키지 않으면 아예 안 띄운다(`gates/acceptance_gate.py`,
    issue #310) — 머지 시점이 아니라 세션 시작 전에 거절한다, #424 가 요구한
    "잘못된 상태에서 나가는 배선" 모양 그대로.

    phase 판정은 `gates/ci.py._approved_roles_on_issue` 와 같은 술어를
    쓴다: 승인자 계정의 `APPROVE issue-<n>/<role>` 코멘트가 이슈에 하나라도
    있으면 phase-2(issue #312, phase 는 role 이 아니라 이슈의 속성). phase-1
    이슈는 Acceptance 가 아직 초안 단계이므로 건드리지 않는다.

    `--issue` 없이 스폰하면(보드 밖 작업) 검사할 이슈가 없어 통과시킨다.
    `gh` 조회 실패는 통과가 아니라 차단이다 — 검사 불가를 통과로 읽지
    않는다는 게이트들의 공통 원칙(`acceptance_gate.py`/`ci.py` 동일).
    """
    if issue is None:
        return
    root = Path(cwd).resolve()
    if not (root / MARKER).is_file():
        return  # require_board 가 이미 --no-contract 없이는 여기까지 안 보낸다
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import acceptance_gate as _acceptance_gate
    approved_roles = _ci._approved_roles_on_issue(root, issue)
    if not approved_roles:
        return  # phase-1: Acceptance 가 아직 초안, 게이트 대상 아님
    bad = _acceptance_gate.check(root, issue)
    if not bad:
        return
    sys.exit(
        f"이슈 #{issue} 는 phase-2 승인({', '.join(sorted(approved_roles))})을 "
        f"받았지만 'Acceptance' 절이 실행가능한 산출물을 가리키지 않는다:\n"
        + "\n".join(f"  - {b}" for b in bad)
        + f"\n  세션을 안 띄운다 — 프로즈만 있는 Acceptance 로는 델리버리를 "
        f"검증할 수 없다(issue #310, #441).")


def require_requirement_linkage(cwd: str, issue: int | None) -> None:
    """issue #1017 (northpole req#6): 이슈가 아직 phase-2 승인을 받지
    않았으면(=드래프트/phase-1 단계) 요구 ID 인용 또는 명시적
    `infrastructure/no-direct-requirement` 태그를 요구한다.
    `require_acceptance_gate` 와 반대 방향의 phase 게이트다 — 그쪽은
    phase-2 승인 **후에만** 발동해 Acceptance 절의 실행가능성을 검사하고,
    이쪽은 phase-2 승인 **전에만**(=아직 새로 드래프트되는 중) 발동해
    요구 연결을 검사한다. 이미 phase-2 승인을 받은 기존 이슈는 이 게이트가
    절대 소급 차단하지 않는다(제안서 제약: "Advisory stays advisory for
    existing issues (no retroactive blocking)").

    두 번째 소급 방지: phase-2 승인 전이라도, 이 이슈로 `issue-<n>/*`
    브랜치가 이미 하나라도 있으면(=이 기능이 생기기 전에 이미 최소 한 번
    스폰돼 phase-1 이 진행 중인 기존 이슈) 새 게이트가 재스폰을 막지
    않는다 — before-landing 워런트 헌트(stance 1)가 실측한 그대로, 이
    조건이 없으면 phase-2 승인만으로 "기존 이슈"를 가려내다가 아직
    미승인인 기존 phase-1 이슈까지 소급 차단해 그 이슈의 애초 phase-1
    세션(요구 연결을 처음 정하는 바로 그 세션)조차 못 띄우는
    닭-달걀 모순이 생긴다. `issue-<n>/*` 브랜치가 전혀 없는 이슈만 "새
    이슈"로 보고 이 게이트를 적용한다.
    """
    if issue is None:
        return
    root = Path(cwd).resolve()
    if not (root / MARKER).is_file():
        return
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import requirement_linkage as _requirement_linkage
    approved_roles = _ci._approved_roles_on_issue(root, issue)
    if approved_roles:
        return  # phase-2: 이미 승인됐다 — 소급 차단하지 않는다
    br = subprocess.run(
        ["git", "for-each-ref",
         f"refs/heads/issue-{issue}/**", f"refs/remotes/*/issue-{issue}/**"],
        cwd=root, capture_output=True, text=True)
    if br.returncode == 0 and br.stdout.strip():
        return  # 이 이슈로 스폰된 적이 이미 있다(로컬 또는 원격) — 소급 차단하지 않는다
    bad = _requirement_linkage.check(root, issue)
    if not bad:
        return
    sys.exit(
        f"이슈 #{issue} 가 요구 연결이 없다:\n"
        + "\n".join(f"  - {b}" for b in bad)
        + f"\n  세션을 안 띄운다 — 요구 ID(`R\\d+` 또는 'northpole req#<n>')를 "
        f"인용하거나 'infrastructure/no-direct-requirement' 태그를 달아야 "
        f"한다(issue #1017, northpole req#6).")


def lint_issue(cwd: str, issue: int) -> list[str]:
    """issue #2088: `require_acceptance_gate`/`require_requirement_linkage` 와
    같은 body-only 게이트를 스폰 없이 미리 돌려본다 — 전자는 phase-2 승인
    후 Acceptance 절의 실행가능성을, 후자는 phase-2 승인 전 요구 연결을
    검사한다(두 게이트는 서로 반대 phase 에서만 발동한다, 위 두 함수의
    docstring 참고). 두 함수와 달리 `sys.exit` 하지 않고 위반을 전부 모아
    반환한다 — 스폰을 시도해 첫 게이트에서 막히고서야 두 번째 위반을
    알게 되는 왕복(issue #2088 리포로 실측: 5회 스폰 거절)을 없앤다.
    """
    root = Path(cwd).resolve()
    violations: list[str] = []
    if not (root / MARKER).is_file():
        return violations  # require_board 가 이미 --no-contract 없이는 여기까지 안 보낸다
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    import acceptance_gate as _acceptance_gate
    import requirement_linkage as _requirement_linkage
    approved_roles = _ci._approved_roles_on_issue(root, issue)
    if approved_roles:
        bad = _acceptance_gate.check(root, issue)
        violations.extend(f"acceptance: {b}" for b in bad)
        return violations  # phase-2: require_requirement_linkage 도 소급 차단하지 않는다
    br = subprocess.run(
        ["git", "for-each-ref",
         f"refs/heads/issue-{issue}/**", f"refs/remotes/*/issue-{issue}/**"],
        cwd=root, capture_output=True, text=True)
    if br.returncode == 0 and br.stdout.strip():
        return violations  # 이미 스폰된 적 있는 이슈 — 소급 차단하지 않는다
    bad = _requirement_linkage.check(root, issue)
    violations.extend(f"requirement-linkage: {b}" for b in bad)
    return violations


def _approvers(root: Path) -> set[str]:
    """`docs/specs/approvers.md` 한 줄에 하나씩 적힌 GitHub 로그인."""
    p = root / MARKER
    if not p.is_file():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*(\S+)", line)
        if m:
            out.add(m.group(1))
    return out


def _pr_for_branch(root: Path, branch: str) -> int | None:
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number", "-q", ".[0].number"],
                       cwd=root, capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def _open_pr_for_branch(root: Path, branch: str) -> int | None:
    """`_pr_for_branch`(spawn.py:1071)의 `--state all` 은 브랜치 재사용 시
    이미 머지된 과거 라운드 PR 을 먼저 돌려줄 수 있다 — `_watch`의
    `pr-opened` 판정에 그대로 쓰면 새로 열린 PR 대신 머지된 PR 을
    보고한다(issue #576). 여기선 OPEN 만 센다. `_pr_for_branch` 자체를
    좁히지 않는 이유: `approve_scope`(spawn.py:1225)는 이미 머지된
    phase-1 PR 코멘트에 달린 승인도 찾아야 해서 `--state all`이 필요하다.
    """
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "open",
                        "--json", "number", "-q", ".[0].number"],
                       cwd=root, capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def _pr_open_or_merged_for_branch(root: Path, branch: str) -> int | None:
    """`_pr_for_branch`의 `--state all` 은 머지 없이 닫힌 PR 도 "있음"으로
    센다 — outcome-derivation 의 already_delivered 판정에 그대로 쓰면
    실패한 세션을 delivered 로 오분류한다(issue #484 after-proposal
    hunt). 여기서는 OPEN/MERGED 만 "배달됨"으로 센다.
    """
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number,state"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        prs = json.loads(r.stdout)
    except ValueError:
        return None
    for pr in prs:
        if pr.get("state") in ("OPEN", "MERGED"):
            return pr.get("number")
    return None


def _merged_pr_for_branch(root: Path, branch: str) -> int | None:
    """`_pr_open_or_merged_for_branch`(spawn.py:1082) 의 MERGED 전용 버전 —
    이슈 #587 §12 event-4(remediation PR merged) 는 OPEN 은 세지 않는다,
    아직 안 끝난 PR 을 merged 로 오탐하면 안 되므로."""
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number,state"],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        prs = json.loads(r.stdout)
    except ValueError:
        return None
    for pr in prs:
        if pr.get("state") == "MERGED":
            return pr.get("number")
    return None


_UPSTREAM_PATH = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)


def _record_upstream(record: Path) -> dict[str, str]:
    """기록의 `upstream:` 목록에서 path 만 뽑는다 (첫 빌드 판별용).

    frontmatter 의 중첩 블록이라 frontmatter() 의 평면 파서로는 안 잡힌다.
    """
    try:
        text = record.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)
    if len(block) < 3:
        return {}
    return {m.group(1): "" for m in _UPSTREAM_PATH.finditer(block[1])}


def _front_role(root: Path, subject: str, roles: dict) -> str | None:
    """그 subject 의 front record — subject 를 처음 연 역할 (첫 빌드 승인 게이트).

    upstream 이 빈 역할이 하나뿐이면 그게 체인 루트다. 못 가리면 관례 순서
    (product, 아니면 feasibility)로 물러난다.
    """
    rootless = [r for r in roles
                if not _record_upstream(root / BOARD / subject / "reports" / f"{r}.md")]
    if len(rootless) == 1:
        return rootless[0]
    for r in ("product-discovery", "technical-feasibility"):
        if r in roles:
            return r
    return None


def approve_scope(cwd: str, issue: int) -> int:
    """s19 의 정확한 문자열 댓글을 승인자 allowlist 로 검증하고, front record 를
    `scope-approved` 로 올리는 커밋을 직접 쓴다 (이슈 #115).

    승인은 여전히 사람의 몫이다 — 이 함수는 그 결정을 **표현하는 방법**(댓글)에서
    **기록에 반영하는 방법**(커밋)으로 옮길 뿐, 어느 역할도 스스로 승인하지
    못한다는 규칙은 그대로 둔다.
    """
    root = Path(cwd).resolve()
    subject = f"issue-{issue}"
    approvers = _approvers(root)
    if not approvers:
        sys.exit(f"승인자 목록이 비어 있다: {root / MARKER}")

    roles = board(root).get(subject)
    if not roles:
        sys.exit(f"{subject} 의 보드 기록이 없다: {root / BOARD / subject / 'reports'}")

    front = _front_role(root, subject, roles)
    if not front:
        sys.exit(f"{subject} 의 front record 를 판별할 수 없다.")

    record_path = root / BOARD / subject / "reports" / f"{front}.md"
    fm = frontmatter(record_path)
    state = fm.get("loop_state")
    if state == "scope-approved":
        print(f"이미 scope-approved 다: {record_path}")
        return 0
    if state != "scope-proposed":
        sys.exit(f"{record_path} 의 loop_state 가 scope-proposed 가 아니다 "
                 f"(지금: {state or '(없음)'}) — 승인 대상이 아니다.")

    needle = f"APPROVE {subject}/scope"
    pr = _pr_for_branch(root, f"{subject}/{front}")
    # 이슈 댓글이 승인 정본이다 — 먼저 본다. PR 댓글은 PR 이 있을 때만 보는
    # fallback 이지 대등한 소스가 아니다(issue-126: 위치 드리프트로 승인을
    # 놓친 사례가 있었다). 순서를 바꾸지 말 것.
    comments, issue_ok = _issue_comments(root, issue)
    pr_ok = True
    if pr:
        pr_comments, pr_ok = _issue_comments(root, pr)
        comments += pr_comments
    match = next((c for c in comments
                  if c["body"].strip() == needle and c["login"] in approvers), None)
    if not match:
        where = f"이슈 #{issue}" + (f" 또는 PR #{pr}" if pr else "")
        if not issue_ok or not pr_ok:
            sys.exit(f"이슈/PR 코멘트를 읽지 못했다 ({where}) — gh 호출이 실패했다. "
                     f"승인 코멘트가 없는지조차 확인할 수 없다.")
        sys.exit(f"승인 코멘트를 못 찾았다: 정확히 \"{needle}\" 를 "
                 f"{', '.join(sorted(approvers))} 중 한 계정이 {where} 에 달아야 한다.")

    text = record_path.read_text(encoding="utf-8")
    new_text = re.sub(r"(?m)^loop_state:.*$", "loop_state: scope-approved", text, count=1)
    if new_text == text:
        sys.exit(f"{record_path} 에서 loop_state 줄을 찾지 못해 고치지 못했다.")
    record_path.write_text(new_text, encoding="utf-8")

    # git add/commit 이 중간에 실패하면(정체성 없음, 훅 거부, 락, 디스크 없음)
    # 파일은 scope-approved 인데 커밋은 없는 상태가 남는다 — 다음 호출이
    # idempotency 가드(state == "scope-approved")에 걸려 커밋 없이 성공을
    # 보고한다(실측: warrant-hunter, 2026-07-30). 파일 쓰기를 되돌려 그 상태를
    # 만들지 않는다.
    rel = str(record_path.relative_to(root))
    try:
        subprocess.run(["git", "-C", str(root), "add", rel],
                       check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(root), "commit", "-m",
                        f"{subject}: scope-approved (approved by {match['login']} "
                        f"via spawn.py approve-scope)"],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        record_path.write_text(text, encoding="utf-8")
        sys.exit(f"커밋 실패 — 기록을 되돌렸다({record_path}), 다시 시도해도 된다: "
                 f"{e.stderr.strip() if e.stderr else e}")

    print(f"{subject}: {front} 기록을 scope-approved 로 올리고 커밋했다 — "
          f"{match['login']} 의 승인. push 는 별도로 한다.")
    return 0


def frontmatter(p: Path) -> dict[str, str]:
    """맨 앞 `---` 블록만 얕게 읽는다. 값의 트레일링 주석은 떼어낸다 —
    계약 §2: 주석을 허용하지 않는 파서는 **게이트 결함이지 기록의 위반이 아니다**."""
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    body = text.split("---", 2)
    if len(body) < 3:
        return {}
    out = {}
    for line in body[1].splitlines():
        k, sep, v = line.partition(":")
        if sep and k.strip() and not k.startswith((" ", "-", "\t")):
            out[k.strip()] = v.split("#")[0].strip()
    return out


def board(root: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Read the board: subject (issue-<n>) -> role -> frontmatter (v3 s10).

    A subject is a docs/issue-<n>/ tree; role records sit in its reports/.
    """
    docs = root / BOARD
    if not docs.is_dir():
        return {}
    found = {}
    for d in sorted(p for p in docs.iterdir() if p.is_dir()):
        if not d.name.startswith("issue-"):
            continue
        if not re.match(r"^issue-[0-9]+$", d.name):
            print(f"board: 숫자가 아닌 issue-* 디렉터리라 보드에서 뺀다: "
                  f"{d.name}", file=sys.stderr)
            continue
        rep = d / "reports"
        roles = {r: frontmatter(rep / f"{r}.md") for r in ROLES
                 if (rep / f"{r}.md").is_file()}
        if roles:
            found[d.name] = roles
    return found


def status(cwd: str) -> list[str]:
    """보드를 **읽는다**. 쓰지 않는다 (protocol.md §1).

    상태는 에이전트의 것이다. on-the-record 가 이걸 고치기 시작하면 룰북의 전이 게이트를
    우회하게 된다 — 게이트는 기록 쓰기를 가로채 막지만, 그 파일을 밖에서 고치면
    문지기를 안 거친다.
    """
    root = Path(cwd).resolve()
    out = [f"프로젝트: {slug(cwd)}   경로: {root}"]

    if not (root / MARKER).is_file():
        out.append(f"⚠ {MARKER} 없음 — 보드 opt-in 이자 승인자 allowlist 다. "
                   f"`spawn.py init` 으로 만든다.")
    b = board(root)
    if b:
        for subject, roles in b.items():
            out.append(f"subject: {subject}")
            for r in ROLES:
                fm = roles.get(r)
                if fm is None:
                    continue
                bits = [f"loop_state: {fm.get('loop_state', '(없음)')}"]
                if fm.get("verdict"):          # feasibility. coding 이 여기 깨어난다(§3)
                    bits.append(f"verdict: {fm['verdict']}")
                out.append(f"  [{r}] " + "   ".join(bits))
            missing = [r for r in ROLES if r not in roles]
            if missing:
                out.append(f"  (기록 없음: {', '.join(missing)})")
        return out

    # 보드가 없다. "아무 일도 없다"와 "옛 자리에 있다"는 정반대 처분을 받아야 한다.
    stale = sorted(r for r, name in LEGACY.items()
                   if (root / name).exists() or (root / "docs" / name).exists())
    if stale:
        out.append(f"보드 없음. 계약 v1 자리에 기록이 있다: {', '.join(stale)}")
        out.append("  이 레포는 v3 이전 판이다. v3 는 docs/issue-<n>/reports/<역할>.md 다.")
    else:
        out.append("보드 없음 (docs/issue-<n>/). 아직 아무 역할도 기록을 쓰지 않았다.")
    return out


def _base(cwd: str) -> str:
    """비교 기준 ref. origin/HEAD 가 가리키는 기본 브랜치를 우선 쓴다."""
    p = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
                       capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip()
    for cand in ("origin/main", "origin/master"):
        if subprocess.run(["git", "-C", cwd, "rev-parse", "--verify", "-q", cand],
                          capture_output=True).returncode == 0:
            return cand
    return "origin/main"          # 없으면 그대로 실패시켜 "검사 불가"로 보고한다


def gate_report(cwd: str) -> list[str]:
    """세션이 무엇을 건드렸는지 결정론적으로 본다. LLM 0회.

    **막지는 않는다.** 세션이 끝난 뒤라 되돌릴 수 없고, on-the-record 는 판정하지 않는다.
    대신 조용히 넘어가지도 않는다 — 보호 경로(인증·시크릿·마이그레이션·CI 설정)를
    건드렸거나 실재하지 않는 패키지를 넣었으면 사람이 알아야 한다.

    게이트가 못 돌아도 그것을 "이상 없음"으로 말하지 않는다. 검사 불가와 통과는
    정반대 처분을 받아야 한다는 게 게이트의 원칙이고, 보고에도 같이 적용된다.
    """
    sys.path.insert(0, str(ROOT / "gates"))
    try:
        import ci, gates
        # 비교 기준을 레포에서 찾는다. origin/main 을 고정하면 기본 브랜치가
        # master·develop 인 레포에서 매번 "검사 불가"가 뜨고, 그러면 게이트가
        # 있으나 마나가 된다.
        gates.BASE = os.environ.get("GATE_BASE") or _base(cwd)
        bad = ci.check(Path(cwd).resolve())
    except Exception as e:                       # git 아님, base 부재, import 실패 등
        return [f"[게이트] 검사 불가 — {type(e).__name__}: {str(e)[:120]}"]
    return ["[게이트] 이상 없음"] if not bad else \
           ["[게이트] 확인 필요:"] + [f"  - {b}" for b in bad]


def ownership_report(cwd: str, role: str, delta: list) -> list[str]:
    """이 세션이 **자기 것이 아닌** 보드 경로를 건드렸는지 사후로 본다.

    세션 안에서는 룰북과 core 의 게이트가 막는다. 이건 그 게이트가 어떤
    이유로든 안 돌았을 때 흔적이라도 남기려는 것이다 — 새 훅이 trap 을
    빠뜨려 fail-open 이 되거나, 룰북 하나가 아직 마이그레이션 안 됐거나.
    막지는 않는다(이미 쓴 뒤다). 대신 조용히 넘어가지도 않는다.
    """
    bad = []
    for p in delta:
        m = re.match(r"^docs/(issue-[0-9]+)/reports/(.+)$", p)
        if not m:
            continue
        rest = m.group(2)
        if rest == f"{role}.md" or rest.startswith(f"{role}/"):
            continue
        if role == "technical-feasibility" and rest.startswith("spikes/"):
            continue
        if role == "release-engineering" and rest.startswith("postmortems/"):
            continue
        bad.append(f"  - {p} (다른 역할의 기록)")
    if not bad:
        return []
    return [f"[소유권] {role} 이 자기 것이 아닌 보드 경로를 건드렸다 — "
            f"세션 안의 게이트가 안 돌았다는 뜻이다 (계약 §11):"] + bad




def _is_new_commit(cwd: str, before_head: str | None, after_head: str | None) -> bool:
    """`after_head` 가 `before_head` 위에 실제로 새 커밋을 얹었는지 판단한다.

    단순히 `after_head != before_head` 로는 부족하다 — 기존에 있던 브랜치나
    커밋으로 체크아웃만 해도 HEAD 는 바뀌지만 새 커밋은 없다. before_head 가
    after_head 의 조상(ancestor)인지까지 확인해야 "진짜 새 커밋"이라고 말할 수
    있다. before_head 가 None (아직 커밋이 없던 새 레포)이면 after_head 가
    있는 것만으로 새 커밋이다.
    """
    if after_head is None:
        return False
    if before_head is None:
        return True
    if before_head == after_head:
        return False
    c = subprocess.run(
        ["git", "-C", cwd, "merge-base", "--is-ancestor", before_head, after_head],
        capture_output=True, text=True,
    )
    return c.returncode == 0


def board_snapshot(cwd: str) -> dict[str, str]:
    """보드 파일들의 내용 해시. 세션 전후를 비교해 §6 의 '바뀐 보드'를 잰다.

    git 이 아니라 파일 내용을 재는 이유: 세션이 커밋했든 안 했든 바뀐 것은
    바뀐 것이고, 계약 §6 의 단위는 커밋이 아니라 보드다.
    """
    base = Path(cwd).resolve()
    docs = base / BOARD
    if not docs.is_dir():
        return {}
    out: dict[str, str] = {}
    for d in sorted(docs.glob("issue-*")):
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                out[str(p.relative_to(base))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def session_result(stdout: str) -> dict:
    """--output-format json 의 결과 오브젝트. 파싱 불가면 빈 dict — 모르는
    것을 성공으로 취급하지 않는다."""
    try:
        got = json.loads(stdout)
        return got if isinstance(got, dict) else {}
    except ValueError:
        return {}


# issue #476 round 3, candidate E (refusal-cost-parity). 등록된 refusal/
# null-result 어휘만 인정한다 — 자유 문장이 아니라 이 닫힌 집합과 정확히
# 일치해야 한다("REFUSAL: <state> — <reason>" 형태), 그래야 역할 세션이
# 임의 텍스트로 스스로를 이 경로에 밀어넣지 못한다. rounds 1-2 의
# loop_state 어휘(H2)와 issue #983 의 role-session 변형에서 이미 쓰는
# 이름들을 재사용한다 — 새 어휘를 이 라운드가 새로 발명하지 않는다.
REGISTERED_NULL_RESULT_STATES = frozenset({
    "hypothesis-not-falsifiable",
    "evidence-log-unreadable",
    "nothing-to-do",
})

_NULL_RESULT_RE = re.compile(
    r"(?m)^REFUSAL:\s*(?P<state>[a-z0-9-]+)\s*—\s*(?P<reason>\S.*)$"
)


def _null_result_declared(result: dict) -> str | None:
    """`result["result"]` 최종 텍스트에서 등록된 REFUSAL 선언을 찾는다.

    이슈 #476 라운드 3, candidate E 의 게이밍-저항 근거: 세션이 쓸 수 있는
    자유 텍스트가 아니라 `REGISTERED_NULL_RESULT_STATES` 라는 닫힌 집합과
    정확히 일치하는 토큰만 인정한다 — 세션이 아무 문구나 써서 이 경로로
    스스로를 밀어넣을 수 없다. 실패 신호: 이 집합 밖의 새 loop_state 가
    실제로 필요해지면(다른 플러그인이 새 refusal 어휘를 등록하면) 이 상수를
    갱신하지 않는 한 그 세션은 조용히 다시 `silent-failure` 로 떨어진다 —
    그래서 이 목록은 코드 리뷰에서 다른 플러그인의 loop_state 어휘 변경과
    함께 갱신 대상으로 다뤄야 한다.
    """
    text = result.get("result")
    if not isinstance(text, str):
        return None
    m = _NULL_RESULT_RE.search(text)
    if not m:
        return None
    state = m.group("state")
    if state not in REGISTERED_NULL_RESULT_STATES:
        return None
    return state


def classify(rc: int, result: dict, delta: list, blocked: list) -> str:
    """세션 하나의 처분. 판정하지 않는다 — 이름만 붙인다 (보고 전용).

    순서가 곧 의미다. 보드가 움직였으면 일부가 막혔어도 그 run 은
    progressed 이고(거부 건수는 따로 찍힌다), 사람 게이트가 서 있으면 그게
    가장 행동 가능한 사실이다.

    refused 와 silent-failure 를 가르는 이유: 게이트가 막아서 아무것도 안
    바뀐 것은 **시스템이 작동한 것**이고, 아무것도 안 바뀌었는데 막힌 것도
    없는 것은 아무도 이유를 모르는 것이다. 실측 2026-07-27 — reflect 를
    띄웠더니 룰북 게이트가 §20 필수 섹션 없음을 이유로 쓰기를 거부했고,
    세션은 그 이유를 또렷이 말하고 끝났는데 분류는 '침묵-사망'이라고 했다.
    이 레포의 원칙("검사 불가와 이상 없음은 정반대 처분을 받아야 한다")이
    여기에도 그대로 적용된다.

    `refused-null-result` (issue #476 round 3, candidate E): 위와 같은
    도구-거부(permission_denials) 없이, 세션이 등록된 REFUSAL 어휘로
    "이 작업은 애초에 할 게 없었다/검증 불가였다"를 명시적으로 선언하고
    끝난 경우. 지금까지는 이 경로가 `silent-failure`(죽은 세션과 동일
    라벨)로 떨어져 있었다 — 이슈 #476 이 지목한 바로 그 비대칭: "정직한
    거부/무결과 보고가 조용한 죽음과 똑같이 실패로 읽힌다." 이 라벨은
    별도 카운터로만 쓰인다(§ fail_closed_downgrade 는 이 라벨을 건드리지
    않는다) — 커밋/PR 없이도 "실패"로 깎이지 않는다는 게 이 후보의
    전부다.
    """
    if rc != 0 or result.get("is_error"):
        return "errored"
    if delta:
        return "progressed"
    if blocked:
        return "waiting-on-human"
    if result.get("permission_denials"):
        return "refused"
    if _null_result_declared(result) is not None:
        return "refused-null-result"
    return "silent-failure"


# 이슈 #1124: `spawn.py clean` 이 세션 로그를 지워도 되는지 판단할 때
# `fail_closed_downgrade` 가 실제로 확정하는, "커밋이 origin 에 닿았다"는
# 라벨 두 개만 "landed" 로 친다. 그 외(refused/errored/silent-failure 등)는
# 유일한 증거인 로그를 지우지 않고 archive 한다.
LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}


def _ledger_log_outcomes() -> dict[str, str]:
    """`runs/ledger.jsonl` 을 `{log 경로: 마지막 outcome}` 으로 접는다.
    파일이 없으면 빈 dict — clean 은 ledger 없이도 동작해야 한다(빈 상태)."""
    p = ROOT / "runs" / "ledger.jsonl"
    out: dict[str, str] = {}
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        log = entry.get("log")
        outcome = entry.get("outcome")
        if log and outcome:
            out[log] = outcome
    return out


def session_end_verdict(work: str, log_path: Path | None, now: float | None = None,
                        alive_fn=None) -> str:
    """워크스페이스 하나의 세션-종료 3분법: `normal` / `crashed` / `stalled` /
    `in-progress` (이슈 #132).

    `<work>.events.jsonl` 에서 마지막 `session-start` 를 찾고, 그 뒤에
    `session-end` 가 이미 왔는지부터 본다 — 죽었다고 보고된 pid 가 사실은
    그 찰나에 정상 종료했을 수도 있는 벤인 레이스를, `_alive()` 보다 먼저
    확인해 `normal` 로 되돌린다. 매치가 없을 때만 `_alive()`/로그 mtime 을
    본다.

    `log_path` 는 호출자가 넘긴다 — 이 함수가 스스로 고정 접미사로
    재구성하면 세대별로 고유해진 로그 명명 규약(이슈 #192,
    `_session_log_path()`)을 놓친다.
    """
    now = time.time() if now is None else now
    alive_fn = _alive if alive_fn is None else alive_fn
    events_path = _events_path(work)
    if not events_path.exists():
        return "normal"
    events = []
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict):
            events.append(ev)
    start_idx = None
    for i in range(len(events) - 1, -1, -1):
        if events[i].get("type") == "session-start":
            start_idx = i
            break
    if start_idx is None:
        return "normal"
    if any(ev.get("type") == "session-end" for ev in events[start_idx + 1:]):
        return "normal"
    detail = events[start_idx].get("detail") or {}
    pid = detail.get("pid")
    if not alive_fn(pid):
        return "crashed"
    if log_path is not None and log_path.exists():
        silent_min = (now - log_path.stat().st_mtime) / 60
        if silent_min > WATCHDOG_SILENCE_MIN:
            return "stalled"
    return "in-progress"


def fail_closed_downgrade(outcome: str, issue: int | None, blocked: list,
                          new_commit: bool, uncommitted: list,
                          already_delivered: bool = False,
                          push_succeeded: bool = False) -> str:
    """`classify()` 뒤에 붙는 별도 단계 — git 상태로 `progressed` 를
    검증한다. `classify()` 자체는 손대지 않는다: git 상태를 모르고, 기존
    계약(rc/result/delta/blocked)과 기존 테스트를 그대로 둔다.

    `issue is not None` 스폰만 대상이다 — 전용 git 워크스페이스가 있는
    경로만 커밋 여부를 검사할 수 있다.

    `blocked` 를 먼저 확인한다 (hunt-phase1 발견 반영): `classify()` 는
    delta 를 blocked 보다 먼저 보므로, 보드가 움직였고 동시에 사람 게이트가
    아직 서 있는 run 은 오늘도 "progressed" 로 분류된다. 그런 run 을 커밋이
    없다고 FAILED 로 깎으면 정직한 blocked 신호를 완전히 지워버린다 — 그래서
    `blocked` 가 비어있지 않으면 이 다운그레이드는 아예 건드리지 않는다.

    `already_delivered` (issue #129 phase 2): 이 세션 자신의 before→after
    HEAD 델타만 보면, 같은 브랜치에서 이전 phase 가 이미 커밋+PR 을 남긴
    뒤 이번 세션이 검증만 하고 새 커밋 없이 끝난 경우를 "실패"로 오분류한다
    — 브랜치에 이미 PR 이 있다는 사실을 호출부에서 확인해 넘긴다. 미커밋
    변경이 남아있으면(더러운 트리) 여전히 다운그레이드한다: "이미 배달됨" 이
    "이번 세션이 남긴 새 변경도 안전하다"를 의미하지 않는다.

    `silent-failure` 업그레이드 (issue #484): `classify()` 는 docs 보드
    델타만 보므로, 이미 배달된 작업 위에 재실행되어 아무것도 할 게 없던
    세션이나 docs 밖(코드) 커밋만 남긴 세션은 델타가 비어 `silent-failure`
    로 잡힌다. 여기서도 `already_delivered`/`new_commit`+push-성공 사실은
    `classify()` 의 원판정과 무관하게 그대로 유효하므로, 같은 신호로
    `silent-failure` 를 끌어올린다 — `progressed` 경로의 다운그레이드
    로직과 대칭이지만 방향이 반대다.
    """
    if outcome == "silent-failure" and issue is not None and not blocked:
        if uncommitted:
            return outcome
        if already_delivered:
            return "progressed"
        if new_commit and push_succeeded:
            return "progressed"
        return outcome
    if outcome != "progressed" or issue is None:
        return outcome
    if blocked:
        return outcome
    if new_commit and uncommitted:
        return "progressed-dirty-tree"
    if uncommitted:
        return "failed-no-commit"
    if new_commit or already_delivered:
        return outcome
    return "failed-no-commit"


def _recovery_policy_module():
    """`gates/recovery_policy.py` 를 지연 import 한다 — 다른 `gates.*` 지연
    import 자리(예: 라인 1667)와 같은 패턴."""
    sys.path.insert(0, str(ROOT / "gates"))
    import recovery_policy
    return recovery_policy


def _reconcile_pr_expected_missing(expected: dict, observed: dict, verdict: str | None,
                                    recovery_state_dir: Path | None = None) -> list[dict]:
    """이슈 #1678: `pr-expected-missing` 죽음을 무조건 `respawn` 으로
    이름 붙이던 걸 `recovery_policy.classify_from_state()` 의 판정으로
    바꾼다 — cap 과 실패-서명 반복을 보고 ESCALATE 할지, 커밋 유무로
    RESPAWN_IDENTICAL/RESPAWN_WITH_HANDOFF 를 가릴지 결정한다.

    `expected["issue"]` 가 없으면(카운터를 걸 (issue, role) 이 없음) 상태
    파일을 건드리지 않고 커밋 유무만으로 즉시 판정한다 — 기존
    `test_expects_pr_missing_not_in_progress_is_respawn` 류처럼 `issue`
    없이 부르는 순수-비교 호출부는 여전히 상태 I/O 없이 동작한다.
    """
    role = expected.get("role")
    branch = expected.get("branch")
    issue = expected.get("issue")
    has_commit = bool(observed.get("new_commit"))
    failure_signature = observed.get("failure_signature")
    death_id = observed.get("death_id")
    base_detail = (f"role={role} branch={branch}: "
                   f"expects_pr=True pr_number=None session_verdict={verdict!r}")

    if issue is not None and role:
        recovery_policy = _recovery_policy_module()
        kwargs = {}
        if recovery_state_dir is not None:
            kwargs["state_dir"] = recovery_state_dir
        policy_verdict = recovery_policy.classify_from_state(
            issue, role, has_commit=has_commit, has_pr=False,
            failure_signature=failure_signature, death_id=death_id, **kwargs)
    else:
        policy_verdict = ("RESPAWN_WITH_HANDOFF" if has_commit
                           else "RESPAWN_IDENTICAL")

    if policy_verdict == "ESCALATE":
        return [{
            "kind": "pr-expected-missing",
            "detail": f"{base_detail} policy=ESCALATE (cap reached or repeat failure signature)",
            "next_action": "manual-review",
        }]
    return [{
        "kind": "pr-expected-missing",
        "detail": f"{base_detail} policy={policy_verdict}",
        "next_action": "respawn",
        "handoff": policy_verdict == "RESPAWN_WITH_HANDOFF",
    }]


def reconcile(expected: dict, observed: dict, recovery_state_dir: Path | None = None) -> list[dict]:
    """이슈-492 step 2 (ADR: `docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md`).

    순수 함수: 로스터/보드/PR/git 에서 이미 읽은 값을 받아 비교만 한다 —
    여기서 새 `gh` 호출을 하지 않는다. 예외 하나(이슈 #1678): `pr-expected-missing`
    가지에서 `expected["issue"]` 가 있으면 `recovery_policy.classify_from_state()`
    를 불러 per-(issue, role) 재기동 카운터를 읽고 쓴다 — 이건 `gh`/git 재조회가
    아니라 이 reconcile 자신의 판정 상태이므로 순수성 취지(외부 세계 재조회
    없음)는 유지된다.

    `expected = {"expects_pr": bool, "role": str, "branch": str, "issue": int|None}`
    `observed = {"session_verdict": str, "pr_number": int|None,
                 "loop_state": str|None, "new_commit": bool,
                 "failure_signature": str|None}`

    반환: `[{"kind": str, "detail": str, "next_action": str}, ...]` —
    divergence 없으면 빈 리스트. next_action 집합은 닫혀 있다: `respawn`,
    `resume-watch`, `manual-review`, `none` 뿐 (ADR Decision 3).

    규칙 순서(이슈의 실측 예시 그대로):
    1. `session_verdict == "crashed"` → `respawn` — kill -9 등으로 세션이
       죽었는데 침묵하지 않는다.
    2. `session_verdict == "stalled"` → `resume-watch` — #132 의 관찰-전용
       standing decision 그대로, 자동 재무장은 안 하고 이름만 붙인다.
    3. PR 을 기대했는데(`expects_pr`) 아직 없고(`pr_number is None`) 세션이
       진행 중도 아니면(`session_verdict != "in-progress"`) → `respawn` —
       이슈의 "push 없이 죽음" 예시.
    4. 위 어디에도 안 걸리는데 입력 자체가 앞뒤가 안 맞으면(예:
       `loop_state` 는 있는데 `session_verdict` 가 없거나 인식 불가) →
       `manual-review` — 침묵 대신 사람 검토로 보낸다.
    5. 그 외엔 divergence 없음(빈 리스트) — 깨끗한 경우.
    """
    verdict = observed.get("session_verdict")
    known_verdicts = ("normal", "crashed", "stalled", "in-progress")

    if verdict == "crashed":
        return [{
            "kind": "session-crashed",
            "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                       "session_verdict=crashed",
            "next_action": "respawn",
        }]
    if verdict == "stalled":
        return [{
            "kind": "session-stalled",
            "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                       "session_verdict=stalled",
            "next_action": "resume-watch",
        }]
    if (expected.get("expects_pr") and observed.get("pr_number") is None
            and verdict != "in-progress"):
        return _reconcile_pr_expected_missing(expected, observed, verdict,
                                               recovery_state_dir=recovery_state_dir)
    # 이슈 #1678 review D2: PR 이 존재하거나 세션이 정상 종료로 끝난
    # 건강한 (issue, role) 은 재기동 카운터를 초기화한다 — 아니면 일시적
    # flake 두 번이 이후의 진짜 죽음까지 영구히 ESCALATE 로 몰아간다.
    _issue = expected.get("issue")
    _role = expected.get("role")
    if _issue is not None and _role and (
            observed.get("pr_number") is not None or verdict == "normal"):
        recovery_policy = _recovery_policy_module()
        kwargs = {}
        if recovery_state_dir is not None:
            kwargs["state_dir"] = recovery_state_dir
        recovery_policy.reset_state(_issue, _role, **kwargs)
    if verdict is None:
        if observed.get("loop_state") is not None:
            # loop_state 는 관측됐는데 session_verdict 가 없다 — 앞뒤가
            # 안 맞는 입력, 침묵 대신 사람 검토로 보낸다.
            return [{
                "kind": "inconsistent-observed-state",
                "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                           f"session_verdict=None loop_state={observed.get('loop_state')!r}",
                "next_action": "manual-review",
            }]
        return []
    if verdict not in known_verdicts:
        return [{
            "kind": "inconsistent-observed-state",
            "detail": f"role={expected.get('role')} branch={expected.get('branch')}: "
                       f"session_verdict={verdict!r} loop_state={observed.get('loop_state')!r}",
            "next_action": "manual-review",
        }]
    return []


def _build_expected(entry: dict) -> dict:
    """로스터 엔트리 → `reconcile()` 의 `expected` 입력. 새 스키마 없음 —
    `roster_register()` 가 이미 쓰는 필드(`role`, `expects_pr`)와 워크
    경로에서 도출한 브랜치 이름만 쓴다."""
    work = entry.get("work")
    branch = Path(work).name if work else None
    return {
        "expects_pr": bool(entry.get("expects_pr")),
        "role": entry.get("role"),
        "branch": branch,
        "issue": entry.get("issue"),
    }


def _build_observed(root: Path, entry: dict) -> dict:
    """로스터 엔트리 → `reconcile()` 의 `observed` 입력. 기존 리더만 쓴다
    (`session_end_verdict`, `_pr_open_or_merged_for_branch`, `board`,
    `_is_new_commit`) — 새 `gh` 호출을 추가하지 않는다."""
    work = entry.get("work")
    log = entry.get("log")
    verdict = session_end_verdict(work, Path(log) if log else None) if work else None
    branch = Path(work).name if work else None
    pr_number = _pr_open_or_merged_for_branch(root, branch) if branch else None
    loop_state = None
    issue = entry.get("issue")
    role = entry.get("role")
    if issue is not None and role:
        subject = f"issue-{issue}"
        loop_state = board(root).get(subject, {}).get(role, {}).get("loop_state")
    new_commit = False
    if work:
        after_head = _git_head(work)
        new_commit = _is_new_commit(work, entry.get("before_head"), after_head)
    return {
        "session_verdict": verdict,
        "pr_number": pr_number,
        "loop_state": loop_state,
        "new_commit": new_commit,
        "death_id": entry.get("ts"),
    }


ROSTER = STATE_ROOT / "active.json"


def _format_roster_row(key: str, e: dict, ws_idx: dict,
                        now: float | None = None) -> tuple[bool, list[str]]:
    """`key`/`e`(로스터 엔트리 하나) 를 `ps` 출력 줄 목록으로 순수하게
    변환한다 — 부수효과(roster_remove 등) 없음, 테스트가 실제 프로세스를
    띄우지 않고 합성 상태로 직접 부를 수 있는 지점 (이슈 #1462).

    돌려주는 `bool` 은 "살아있음" — 호출자가 정리 대상 여부를 판단하는 데
    쓴다. 행 하나는 자기 자신의 `work`/`log` 필드만 표시한다 — 다른
    키(`ws_idx` 포함)의 값으로 대체하는 폴백은 어디에도 없다(행 격리
    불변식, requirement 3)."""
    now = time.time() if now is None else now
    pid = e.get("pid")
    pid = pid if isinstance(pid, int) else 0
    alive = _alive(pid)
    if "ts" in e and isinstance(e.get("ts"), (int, float)):
        age = f"{(int(now) - int(e['ts'])) // 60}분"
    else:
        # 이슈 #1462: ts 가 없으면 epoch(0) 을 기준으로 나이를 계산하지
        # 않는다 — "29778226분" 처럼 터무니없는 나이를 찍던 버그.
        age = "unknown"
    pid_disp = pid if pid else "unknown"
    if alive:
        state = "RUNNING"
    else:
        # 이슈 #1462 requirement 2: 세션-종료~재스폰 갭은 RUNNING/pid 0 이
        # 아니라 truthful terminal state(마지막으로 알려진 pid 를 들고)로
        # 보여야 한다.
        state = "ENDED"
    lines = [
        f"{state:14s} {e.get('role','?'):12s} issue-{e.get('issue','?')}  "
        f"{age}  pid {pid_disp}",
        f"               log: {e.get('log','')}",
        f"               work: {e.get('work','')}",
    ]
    work = e.get("work")
    ws_key = f"{_repo_identity(work)}/{key}" if work else key
    ws_entry = ws_idx.get(ws_key)
    watcher_pid = ws_entry.get("watcher_pid") if ws_entry else None
    role = key.split("/", 1)[1] if "/" in key else None
    if watcher_pid is None:
        lines.append("               워처: UNWATCHED")
    elif not alive:
        # 이슈 #1462 requirement 4: 세션이 정상 종료해서 이 행 자체가 이미
        # ENDED 이면, 워처의 by-design 동반 종료를 DEAD 로 오라벨하지
        # 않는다 — 그건 세션이 살아있는데 워처만 죽은 경우의 라벨이다.
        lines.append(f"               워처: exited-with-session (pid {watcher_pid})")
    elif _watcher_looks_real(watcher_pid, e.get("issue"), role):
        armed_at = ws_entry.get("watcher_armed_at")
        armed_mins = (int(now) - int(armed_at)) // 60 \
            if armed_at is not None else "?"
        own_sid = os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None
        sid = e.get("session_id")
        if sid is not None and sid != own_sid:
            # 이슈 #1013 block E: 워처가 살아있어도 이 워처를 무장한
            # 세션이 나(호출자)와 다르면 로컬 소유를 암시하지 않는다.
            lines.append(f"               워처: pid {watcher_pid}  "
                         f"armed {armed_mins}분 전  (다른 세션 소유)")
        else:
            lines.append(f"               워처: pid {watcher_pid}  "
                         f"armed {armed_mins}분 전  follow=True")
    else:
        lines.append(f"               워처: DEAD(pid {watcher_pid})")
    return alive, lines


def roster_ps() -> int:
    """돌고 있는 역할 세션들. 죽은 항목은 표시 후 정리한다.

    이슈 #559: 각 살아있는 세션마다 붙은 워처(있으면)를 함께 보여준다 —
    "워처가 무장됐는지 죽었는지 바깥에서 알 방법이 없다"는 관찰에 대한
    응답. `ROSTER`(`issue-<n>/<role>` 키)와 `WORKSPACE_INDEX`(레포 접두사
    포함 키)를 `_watch`/`watchdog_check_one`과 같은 방식으로 조인한다."""
    d = _roster_load()
    if not d:
        print("돌고 있는 역할 세션 없음")
        return 0
    ws_idx = _workspace_index_load()
    dead = []
    for key, e in sorted(d.items()):
        alive, lines = _format_roster_row(key, e, ws_idx)
        for line in lines:
            print(line)
        if not alive:
            dead.append(key)
    for k in dead:
        roster_remove(k)
    return 0


RECONCILE_LEDGER = ROOT / "runs" / "reconcile_ledger.json"



# ------------------------------------------------------------- issue #2101
# Watch-layer hardening: five self-correcting mechanisms, all ADVISORY-ONLY
# per the watch-coverage policy (watch-class checks never block, refuse, or
# kill — they print advisories, write ledger events, and return items to
# dispatchable state; the requeue path is deliberately detector-free).
#
# Constants (module-level defaults, env-overridable at import time):
#   OTR_LEASE_TTL_MIN            lease TTL in minutes for an in-progress
#                                roster claim (default 90 — one missed-renewal
#                                window, same order as WATCHDOG_SILENCE_MIN)
#   OTR_LEASE_FLAT_RENEWALS_K    renewals with an unchanged progress indicator
#                                before the flat-progress advisory (default 3)
#   OTR_DEADMAN_INTERVAL_SEC     expected watchdog/monitor tick cadence
#                                (default 120s, the poll-heartbeat Monitor
#                                sleep cadence)
#   OTR_DEADMAN_STALE_INTERVALS  tick intervals without a coverage-OK marker
#                                before the dead-man advisory fires (default 5)
LEASE_TTL_MIN = float(os.environ.get("OTR_LEASE_TTL_MIN", "90"))
LEASE_FLAT_RENEWALS_K = int(os.environ.get("OTR_LEASE_FLAT_RENEWALS_K", "3"))
DEADMAN_INTERVAL_SEC = float(os.environ.get("OTR_DEADMAN_INTERVAL_SEC", "120"))
DEADMAN_STALE_INTERVALS = int(os.environ.get("OTR_DEADMAN_STALE_INTERVALS", "5"))
# Coverage-OK marker (mechanism 4). Lives under STATE_ROOT so the checker
# needs no knowledge of any board — it is about the watch layer itself.
DEADMAN_MARKER = STATE_ROOT / "watch-coverage-ok"
# Declared wait state (mechanism 5): a session records what it awaits in a
# machine-readable file inside its workspace. Supported object forms:
# "issue:<n>" (a board subject, checked against docs/issue-<n>/) or a
# filesystem path (absolute, or relative to the workspace).
DECLARED_WAIT_FILENAME = ".waiting-on.json"


def watchdog_check_one(key: str, entry: dict, now: float | None = None,
                       state: dict | None = None) -> list[str]:
    """이슈 #90 phase-2: 살아있는 세션 하나에 대해 관찰만 하는(observe-only)
    이상 신호 목록을 돌려준다. 세션의 프로세스·프롬프트·워크트리는 건드리지
    않는다 — 로그 mtime/내용, 로스터 필드, git 상태만 읽는다.

    `state` 를 넘기면 그 dict 를 제자리에서 갱신하고 저장하지 않는다(테스트
    용). 생략하면 `runs/watchdog_state.json` 을 읽고 쓴다.
    """
    now = time.time() if now is None else now
    anomalies: list[str] = []
    log_path = Path(entry["log"]) if entry.get("log") else None
    work = entry.get("work")
    ts = entry.get("ts", 0)
    elapsed_min = (now - ts) / 60

    # signal 1: 로그 무응답 — 프로포절 §Anomaly-signal-list #1
    if log_path is not None and log_path.exists():
        mtime = log_path.stat().st_mtime
        silent_min = (now - mtime) / 60
        if silent_min > WATCHDOG_SILENCE_MIN:
            anomalies.append(
                f"log-silence: {int(silent_min)}분째 로그 무응답 ({log_path})")

    # 마지막 스캔 이후 새로 쓰인 로그 내용만 본다 — 신호 2/3
    own_state = state if state is not None else _watchdog_state_load()
    st = own_state.get(key, {"offset": 0})
    text = ""
    start_offset = st.get("offset", 0)
    new_offset = start_offset
    if log_path is not None and log_path.exists():
        # 로그가 이전 스캔 오프셋보다 짧아졌다면 그 사이 세션이 재시작되며
        # 로그가 truncate 된 것이다(spawn 은 같은 경로를 "w" 로 다시 연다) —
        # 옛 오프셋을 그대로 쓰면 새 세션의 신호 2/3 이 로그가 옛 길이를
        # 다시 넘어설 때까지 조용히 못 잡힌다. 이 경우 처음부터 다시 읽는다.
        if log_path.stat().st_size < start_offset:
            start_offset = 0
        with log_path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(start_offset)
            raw = fh.read()
            # 이슈 #994 구조적 파싱은 줄 단위 JSON 이라 마지막 줄이 쓰기
            # 도중(같은 spawn 프로세스가 다음 이벤트를 쓰는 사이) 잘려 있으면
            # 그 스캔에서는 그냥 건너뛴다 — 하지만 offset 을 파일 끝까지
            # 밀어버리면 다음 틱은 그 뒤부터 읽으므로 잘렸던 줄이 영영
            # 다시 오지 않는다(실제 거부가 그 줄에 있었다면 영구 유실).
            # 마지막 줄바꿈까지만 커밋하고 미완성 꼬리는 다음 스캔에 남긴다.
            if raw and not raw.endswith("\n"):
                split_at = raw.rfind("\n")
                committed = raw[:split_at + 1] if split_at != -1 else ""
            else:
                committed = raw
            text = committed
            fh.seek(start_offset)
            fh.read(len(committed))
            new_offset = fh.tell()
    own_state[key] = {"offset": new_offset}
    if state is None:
        _watchdog_state_save(own_state)

    # signal 2: 백그라운드-위임 언급 — 시점 무관, 매치 즉시 신고
    if _DELEGATION_RE.search(text):
        anomalies.append(f"background-delegation-phrasing: {log_path}")

    # signal 3: 반복된 거부된 도구 호출 (이번 스캔 구간 내) — 이슈 #994:
    # 단어 매치가 아니라 구조적 tool_result/is_error 만 센다.
    new_denials = _count_structural_denials(text)
    if new_denials >= WATCHDOG_DENIAL_THRESHOLD:
        anomalies.append(
            f"denied-tool-calls: 이번 스캔 구간에 {new_denials}건")

    # signal 7 (이슈 #1966): mtime 은 계속 움직이지만(log-silence 는 안 잡힘)
    # 최근 WATCHDOG_HEARTBEAT_ONLY_MIN 분간 tool_progress 하트비트 줄만
    # 기록된 경우 — advisory 전용, STALLED 는 아니다(diagnose_health 에서
    # 별도 서브상태로 분리).
    hb_status = _classify_log_lines_heartbeat_only(text, now)
    if hb_status == "heartbeat-only":
        anomalies.append(
            f"heartbeat-only-growth: 최근 {WATCHDOG_HEARTBEAT_ONLY_MIN}분간 "
            f"tool_progress 하트비트만 기록됨 ({log_path})")

    # signal 4: 반환점 지났는데 커밋 없음 — 이슈 스코프 스폰만 (before_head 필요)
    before_head = entry.get("before_head")
    if work and before_head and elapsed_min > WATCHDOG_NO_COMMIT_MIN:
        r = subprocess.run(
            ["git", "-C", str(work), "rev-list", "--count",
             f"{before_head}..HEAD"],
            capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip() == "0":
            anomalies.append(
                f"no-commits-late: {int(elapsed_min)}분 경과, "
                f"{before_head} 이후 커밋 0건")

    # signal 5 (이슈 #488): 자동 무장한 워처가 죽었거나 애초에 없으면 신고한다
    # — 죽은 워처는 조용히 넘어가면 auto-arm 의 요구("워처 없는 스폰 불가")를
    # 관측 시점에서 다시 어기는 셈이라, watchdog 틱마다 여기서 잡는다.
    ws_key = f"{_repo_identity(work)}/{key}" if work else key
    ws_entry = _workspace_index_load().get(ws_key)
    if ws_entry is not None:
        watcher_pid = ws_entry.get("watcher_pid")
        watcher_role = key.split("/", 1)[1] if "/" in key else None
        if watcher_pid is None:
            anomalies.append(f"watcher-missing: {key} 에 등록된 워처가 없다")
        elif not _watcher_looks_real(watcher_pid, entry.get("issue"), watcher_role):
            anomalies.append(
                f"watcher-dead: 워처 pid {watcher_pid} 가 죽어 있거나(또는 다른 "
                f"프로세스가 그 pid 를 물려받았거나) — spawn.py watch --issue "
                f"<n> --role <role> --rearm 로 재무장하라 (non-blocking)")
        else:
            # signal 6 (이슈 #782): 워처 pid 는 살아 있고 신원도 진짜인데
            # (_watcher_looks_real 통과) 워처 자신의 로그가 무장 이후로
            # mtime 이 안 움직인다 — 2026-08-11 실측 실패 모드(첫 줄에서
            # 멈춘 watch --follow): pid 는 살아 있어 watcher-dead 로는
            # 안 잡힌다. `watcher_armed_at` 을 못 읽으면(구 로스터 엔트리)
            # 판정하지 않는다 — 없는 기준선으로 조용한 오탐을 내지 않는다.
            armed_at = ws_entry.get("watcher_armed_at")
            watcher_log = Path(str(work) + ".watcher.log") if work else None
            if armed_at is not None and watcher_log is not None and watcher_log.exists():
                w_mtime = watcher_log.stat().st_mtime
                silence_min = (now - max(w_mtime, float(armed_at))) / 60
                if silence_min > WATCHDOG_SILENCE_MIN:
                    anomalies.append(
                        f"watcher-silent: 워처 pid {watcher_pid} 는 살아 있지만 "
                        f"{int(silence_min)}분째 로그 무응답 ({watcher_log}) — "
                        f"spawn.py watch --issue <n> --role <role> --rearm 로 "
                        f"재무장하라 (non-blocking)")

    return anomalies



def _roster_reconcile_unreported(issue: int | None = None) -> int:
    """`spawn.py reconcile --unreported [--issue N]` (이슈 #534): roster 는
    session-end 직후 곧바로 지워지므로(`roster_remove()`, spawn.py:3988)
    끝난 세션의 흔적을 담지 못한다 — 대신 세션이 끝나도 지워지지 않는
    `_workspace_index_put()` 의 workspace 인덱스(`WORKSPACE_INDEX`)를
    훑는다. `verdict == "normal"` 인데 `_SESSION_END_COMMENT_MARKER`
    코멘트가 아직 없는 엔트리를 "미보고"로 찍는다 — self-trigger/watchdog
    이 둘 다 놓친 경우(프로세스가 코멘트 줄에 닿기 전에 죽는 등)를
    오케스트레이터가 아무 때나 한 번의 호출로 회복하는 창구다."""
    idx = _workspace_index_load()
    total = 0
    found_any = False
    for key, e in sorted(idx.items()):
        m = re.search(r"(?:^|/)issue-(\d+)/", key)
        if not m:
            continue
        issue_n = int(m.group(1))
        if issue is not None and issue_n != issue:
            continue
        found_any = True
        work = e.get("work")
        if not work:
            continue
        # 이슈 #1283: workspace 가 이미 `clean` 에 지워졌다고 여기서
        # 건너뛰면(구 #1124 조치), session-end(normal) 인데 아직 미보고인
        # 세션이 영영 사라진다 — session_end_verdict/`_issue_comments`
        # 둘 다 없는 workspace 를 이미 안전하게 다루므로(survey 참고)
        # 여기서 따로 건너뛸 필요가 없다.
        log = e.get("log")
        verdict = session_end_verdict(work, Path(log) if log else None)
        if verdict != "normal":
            continue
        # 이슈 #533: 마커는 `_post_session_end_comment` 가 실제로 코멘트에
        # 박아 둔 bare `issue-<n>/<role>` 형태여야 한다 — workspace 인덱스
        # `key` 는 이제 레포 접두사가 붙어 그대로 쓰면 마커가 영원히
        # 안 맞아 매번 미보고로 오탐한다.
        m2 = re.search(r"issue-\d+/[^/]+$", key)
        roster_key = m2.group(0) if m2 else key
        marker = _SESSION_END_COMMENT_MARKER.format(key=roster_key)
        # `_issue_comments`가 `ok=False`(코멘트를 못 읽음)면 마커 부재를
        # 확인할 수 없다 — "확인 못 함은 통과가 아니다"(#287) 원칙대로
        # 미보고 쪽으로 넘어간다(중복 코멘트를 감수).
        comments, ok = _issue_comments(Path(work), issue_n)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
        total += 1
        print(f"[reconcile --unreported] {key}: session-end(normal) 미보고 "
              f"— issue #{issue_n}, work={work}, log={log}")
    if not found_any:
        print("reconcile --unreported: 대상 workspace 엔트리 없음")
    elif not total:
        print("reconcile --unreported: 미보고 없음")
    return total


_REMEDIATION_MERGE_COMMENT_MARKER = "[watch] remediation-merged: {path}"


def _remediation_merge_sweep(root: Path, issue: int) -> int:
    """`spawn.py reconcile --remediation-merged --issue N` (이슈 #587 §12
    event 4): `docs/issue-<n>/decisions/remediation-*.md` 중 `status: open`
    인 기록의 `routed_to` 역할 브랜치(`issue-<n>/<role>`, 관례는
    `remediation_spawn.py` 의 멱등성 체크와 동일)가 머지됐으면 §12 형식의
    한 줄 코멘트를 이슈에 남긴다.

    `_roster_reconcile_unreported`와 같은 read-then-check 멱등 패턴: 고정
    마커가 이미 있으면 건너뛴다 — 같은 remediation 기록에 두 번 코멘트를
    달지 않는다."""
    decisions_dir = root / BOARD / f"issue-{issue}" / "decisions"
    if not decisions_dir.is_dir():
        return 0
    slug = _repo_slug(root)
    posted = 0
    for rem_path in sorted(decisions_dir.glob("remediation-*.md")):
        fm = frontmatter(rem_path)
        if fm.get("status") != "open":
            continue
        routed_to = fm.get("routed_to")
        if not routed_to or routed_to == "UNRESOLVED":
            continue
        round_n = fm.get("round", "?")
        candidate_pr = fm.get("candidate_pr", "?")
        marker = _REMEDIATION_MERGE_COMMENT_MARKER.format(
            path=f"docs/issue-{issue}/decisions/{rem_path.name}")
        comments, ok = _issue_comments(root, issue)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
        branch = f"issue-{issue}/{routed_to}"
        merged_pr = _merged_pr_for_branch(root, branch)
        if merged_pr is None:
            continue
        if not slug:
            continue
        body = (f"{marker}\n\n"
                f"Remediation merged: PR #{merged_pr} resolves round {round_n} "
                f"of PR #{candidate_pr}\n"
                f"https://github.com/{slug}/pull/{merged_pr}")
        r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                            "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
        if r.returncode == 0:
            posted += 1
        else:
            print(f"[spawn] 이슈 #{issue} remediation-merged 코멘트 게시 실패: "
                  f"{r.stderr.strip()}", file=sys.stderr)
    return posted


def roster_reconcile(issue: int | None = None, unreported: bool = False,
                      remediation_merged: bool = False,
                      root: Path | None = None) -> int:
    """`spawn.py reconcile [--issue N] [--unreported] [--remediation-merged]`
    — 이슈-492 step 2 CLI verb, 이슈 #534 로 `--unreported` 모드가, 이슈
    #587 round 2 로 `--remediation-merged` 모드가 추가됐다.

    `unreported=True` 면 `_roster_reconcile_unreported()` 로 위임한다 —
    roster 가 아니라 workspace 인덱스를 보는, 다른 데이터소스/다른 질문
    (divergence 가 아니라 "미보고 session-end")이라 별도 함수로 분리했다.

    `remediation_merged=True` 면 `_remediation_merge_sweep(target_root,
    issue)` 로 위임한다 — `target_root` 는 `root` (호출자의 `-C` 대상)가
    주어지면 그것, 아니면 `ROOT`(spawn.py 자신의 체크아웃)다. 이슈 #587
    round 3: `_remediation_merge_sweep` 이 항상 `ROOT` 로만 불려서 다른
    레포를 대상으로 한 CLI 호출에서 조용히 no-op 됐던 결함의 수정 —
    `issue` 가 없으면 대상을 특정할 수 없으므로 아무 것도 하지 않고 0 을
    반환한다.

    기본 모드(둘 다 False)는 그대로다: 로스터(살아있는 것 + 죽은 것
    전부, `watchdog --auto-respawn` 의 스캔 범위와 같다)를 훑어 엔트리마다
    `reconcile()` 을 한 번씩 돌린다. `--issue` 를 주면 그 이슈 번호의
    엔트리로만 좁힌다. divergence 한 줄씩 찍고, 종료 코드는 divergence 총
    개수(0 = 깨끗함) — `roster_watchdog` 의 반환값과 같은 관례
    (spawn.py:1752-1755)."""
    if unreported:
        return _roster_reconcile_unreported(issue)
    if remediation_merged:
        if issue is None:
            return 0
        target_root = root if root is not None else ROOT
        return _remediation_merge_sweep(target_root, issue)
    d = _roster_load()
    if issue is not None:
        d = {k: e for k, e in d.items() if e.get("issue") == issue}
    if not d:
        print("reconcile: 대상 로스터 엔트리 없음")
        return 0
    total = 0
    for key, e in sorted(d.items()):
        divergences = reconcile(_build_expected(e), _build_observed(ROOT, e),
                                 recovery_state_dir=ROOT / ".on-the-record" / "recovery-state")
        for div in divergences:
            total += 1
            print(f"[reconcile] {key}: {div['kind']}: {div['detail']} "
                  f"-> next_action={div['next_action']}")
    if not total:
        print("reconcile: divergence 없음")
    return total




RESPAWN_STATE = ROOT / "runs" / "respawn_state.json"
RESPAWN_MAX_ATTEMPTS = 2
# 이슈 #678: no-progress 스트릭이 매 재스폰마다 진행을 인정해 리셋되더라도,
# 토큰 비용 백스톱으로 전체 재스폰 횟수에 독립적인 절대 상한을 둔다 —
# 진짜 진행 중인 작업(스트릭 리셋)을 방해하지 않을 만큼 넉넉히, 그러나
# 무한하지 않게: RESPAWN_MAX_ATTEMPTS 의 4배.
RESPAWN_ABSOLUTE_MAX = RESPAWN_MAX_ATTEMPTS * 4
_CRASH_COMMENT_MARKER = "[on-the-record] {key}: crashed, respawn cap ({cap}) reached"
_STALL_COMMENT_MARKER = "[on-the-record] {key}: stalled"


def _respawn_state_load() -> dict:
    try:
        return json.loads(RESPAWN_STATE.read_text())
    except (OSError, ValueError):
        return {}


def _respawn_state_save(d: dict) -> None:
    RESPAWN_STATE.parent.mkdir(exist_ok=True)
    RESPAWN_STATE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def _post_crash_comment(root: Path, issue: int, key: str, work: str, log: str,
                        trigger: str = "crashed", absolute: bool = False) -> None:
    """재스폰 상한 도달 시 이슈에 남기는 코멘트. 멱등: 고정 마커 문자열을
    기존 코멘트에서 먼저 찾는다(`_issue_comments`/`approve_scope` 와 같은
    read-then-check 패턴) — 워치독을 반복 호출해도 두 번째 코멘트는 없다.

    `trigger` (이슈 #247): 어느 경로가 상한을 채웠는지(예:
    `watchdog-observed-crashed` / `self-triggered-abandoned`) 본문에
    남긴다 — 마커 문자열 자체는 이슈 #132 부터 쓰던 그대로 둔다. 멱등성
    키는 트리거 종류와 무관하게 key+상한 하나여야 두 경로가 같은
    attempt-cap 예산을 공유한다는 프로포절의 결정이 그대로 성립한다.

    `absolute` (이슈 #678): no-progress 스트릭 상한(`RESPAWN_MAX_ATTEMPTS`)
    이 아니라 `RESPAWN_ABSOLUTE_MAX` 총 시도 상한이 찼을 때 True — 마커의
    `cap` 값 자체가 달라지므로(2 vs `RESPAWN_ABSOLUTE_MAX`) 두 캡은 서로
    다른 멱등성 키를 쓰고, 어느 쪽이 찼는지가 코멘트 본문에서도 구분된다."""
    cap = RESPAWN_ABSOLUTE_MAX if absolute else RESPAWN_MAX_ATTEMPTS
    marker = _CRASH_COMMENT_MARKER.format(key=key, cap=cap)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    cap_label = "absolute total-respawn ceiling" if absolute else "no-progress respawn cap"
    body = (f"{marker}\n\n"
            f"trigger: {trigger}\nworkspace: {work}\nlog: {log}\n\n"
            f"All {cap} automatic respawns exhausted ({cap_label}) — needs human intervention.")
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[spawn] 이슈 #{issue} 크래시-캡 코멘트 게시 실패 (사람 개입 필요 경고가 "
              f"전달되지 않았다): {r.stderr.strip()}", file=sys.stderr)


def _post_stall_comment(root: Path, issue: int, key: str, work: str, log: str) -> None:
    """이슈 #325: `stalled` 판정을 최초 1회 이슈 코멘트로 남긴다.

    `stalled` 는 재스폰을 트리거하지 않는다(관찰-전용 정책, 이슈 #132 —
    바뀌지 않는다) — 다만 지금까지는 그 판정이 워치독을 부른 터미널의
    `print()` 한 줄로만 남아, 진행 중인 세션과 조용히 멈춘 세션이 밖에서
    구분되지 않았다. `_post_crash_comment` 와 같은 read-then-check
    멱등 패턴: 고정 마커가 이미 있으면 아무것도 하지 않는다."""
    marker = _STALL_COMMENT_MARKER.format(key=key)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    body = (f"{marker}\n\n"
            f"workspace: {work}\nlog: {log}\n\n"
            f"Session judged stalled — automatic respawn will not trigger "
            f"(observation-only policy). Needs human check.")
    subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                    "-f", f"body={body}"], cwd=root, capture_output=True, text=True)


_SESSION_END_COMMENT_MARKER = "[watch] {key}: session-end:"


def _pr_list_call_ok(root: Path, branch: str) -> bool:
    """`_pr_open_or_merged_for_branch()`(spawn.py:1049)와 같은 `gh pr list`
    호출이되, PR 상태 판정 로직은 재사용하고 이건 그 밑에 깔린 `gh` 호출
    자체가 성공했는지만 본다 — "PR 없음"과 "확인 못 함"을 구별하는 데 쓴다
    (이슈 #534, 프로포절의 empty-state 규정: `gh` 호출이 실패하면
    `(pr-check-failed)` 접미사를 붙인다)."""
    r = subprocess.run(["gh", "pr", "list", "--head", branch, "--state", "all",
                        "--json", "number,state"],
                       cwd=root, capture_output=True, text=True)
    return r.returncode == 0


def _post_session_end_comment(root: Path, issue: int, key: str, work: str,
                              log: str) -> None:
    """이슈 #534: 세션 종료(`normal`)를 GitHub 이슈 코멘트로 durable 하게
    남긴다 — 오케스트레이터의 대화 상태(재무장 루프)가 아니라 이 코멘트가
    "세션이 끝났다"는 사실을 관찰할 다리가 되도록 한다.

    `crashed`/`stalled` 는 이 함수의 범위가 아니다 — 이미
    `_post_crash_comment`/`_post_stall_comment` 가 처리한다. 이 함수는
    `verdict == "normal"` 인 세션에만 코멘트를 남긴다.

    `_post_stall_comment`/`_post_crash_comment` 와 같은 멱등 read-then-check
    패턴: 고정 마커(`{key}` 까지만 — PR 유무와 무관하게 한 번만 남긴다)가
    이미 있으면 아무것도 하지 않는다.
    """
    verdict = session_end_verdict(work, Path(log) if log else None)
    if verdict != "normal":
        return
    marker = _SESSION_END_COMMENT_MARKER.format(key=key)
    comments, ok = _issue_comments(root, issue)
    if ok and any(marker in c.get("body", "") for c in comments):
        return
    slug = _repo_slug(root)
    if not slug:
        return
    branch = subprocess.run(["git", "-C", work, "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    pr_number = _pr_open_or_merged_for_branch(root, branch) if branch else None
    if pr_number is not None:
        line = f"PR https://github.com/{slug}/pull/{pr_number} opened"
    elif branch and not _pr_list_call_ok(root, branch):
        line = "no PR (pr-check-failed)"
    else:
        line = "no PR"
    body = f"{marker} {line}\n\nworkspace: {work}\nlog: {log}"
    r = subprocess.run(["gh", "api", f"repos/{slug}/issues/{issue}/comments",
                        "-f", f"body={body}"], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[spawn] 이슈 #{issue} session-end 코멘트 게시 실패: {r.stderr.strip()}",
              file=sys.stderr)


def _respawn_fingerprint(work: str) -> dict:
    """이슈 #678: no-progress 스트릭 판정에 쓰는 지문 — git HEAD sha 와
    `board_snapshot()` 의 안정적 해시(정렬된 dict 를 직렬화해 해시하므로,
    같은 내용이면 dict 순서가 달라도 같은 해시). 두 재스폰 시점의 지문이
    같으면 "그 사이에 관측 가능한 진행이 없었다"는 뜻이다."""
    board = board_snapshot(work)
    board_hash = hashlib.sha256(
        json.dumps(board, sort_keys=True).encode("utf-8")).hexdigest()
    return {"head": _git_head(work), "board": board_hash}


_CONTINUATION_PREAMBLE = (
    "workspace contains uncommitted work from the previous session — "
    "verify briefly, then commit/push/PR; do not redo"
)

_RECORD_PATH_RE = re.compile(r"docs/issue-\d+/(reports|proposals)/")


def _classify_workspace_completion(work: str, role: str) -> str:
    """이슈 #1982: 재스폰 시점 dirty workspace 를 "finished"/"unfinished" 로
    분류한다. `git status --porcelain` 이 비어 있으면(clean) 바로
    "unfinished". dirty 라도, 변경분에 이 저장소의 record-shape 규약이
    요구하는 경로(`docs/issue-<n>/reports/**`, `docs/issue-<n>/proposals/**`)
    아래 파일이 없으면 "unfinished". 있으면 그 파일을 읽어 frontmatter 를
    걷어낸 본문이 비어있지 않은 경우에만(= frontmatter-only 스텁이 아닌
    경우에만) "finished" — 프로포절의 conservative-default 결정: 신호가
    모호하거나 얇으면 항상 "unfinished" 쪽으로 판정한다."""
    st = subprocess.run(["git", "-C", work, "status", "--porcelain", "-uall"],
                        capture_output=True, text=True)
    lines = [l for l in st.stdout.splitlines() if l.strip()]
    if not lines:
        return "unfinished"
    record_paths = []
    for line in lines:
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if _RECORD_PATH_RE.search(path):
            record_paths.append(path)
    for rel in record_paths:
        full = Path(work) / rel
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8", errors="replace")
        body = text
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                body = text[end + 4:]
        if body.strip():
            return "finished"
    return "unfinished"


def _respawn_or_cap(key: str, work: str, issue: int, role: str, log: str,
                    session_start_ts, state: dict, trigger: str) -> None:
    """공유 재스폰 시퀀스: 원자적 클레임 확인, 상한(`RESPAWN_MAX_ATTEMPTS`)
    확인, `.task.txt` 를 통한 `_spawn_one()` 재생, 상한 도달 시 캡-코멘트.

    이슈 #678: `attempts` 는 이제 no-progress *스트릭* 이다 — 직전 재스폰
    시점에 저장해둔 지문(`_respawn_fingerprint()`)과 지금 지문이 다르면
    (새 커밋 또는 보드 델타) 진행이 있었다고 보고 스트릭을 0 으로 리셋한
    뒤 이번 시도를 1 로 센다. 지문이 없으면(최초 재스폰) 비교할 것이
    없으므로 진행/무진행 어느 쪽으로도 치지 않고 오늘처럼 스트릭을
    1부터 시작한다. `total_attempts` 는 스트릭과 무관하게 매 재스폰마다
    증가하는 별도 카운터로, `RESPAWN_ABSOLUTE_MAX` 총 상한과 비교한다 —
    스트릭이 계속 리셋돼도 무한정 재스폰하지 않게 하는 토큰 비용
    백스톱(프로포절의 명시적 결정).

    이슈 #132 워치독 `crashed` 경로(`_auto_respawn_check()`)와 이슈 #247
    self-trigger 경로(`_spawn_one()` 자신이 정상 종료하며 미커밋 작업을
    감지한 경우, spawn.py `_self_trigger_respawn()`)가 이 시퀀스를
    그대로 공유한다 — 재스폰 로직을 두 벌 두지 않고, attempt-cap 카운터도
    `key` 하나로 공유해 두 경로가 같은 예산을 쓴다(프로포절의 명시적
    결정). `trigger` 는 어느 쪽이 불렀는지 로그/코멘트에 남겨 사람이
    나중에 구분할 수 있게 한다.

    `session_start_ts` 로 세션마다 다른 클레임 키(`.respawn-claim-{ts}`)를
    만든다 — 두 트리거가 같은 세션(같은 ts)을 동시에 관측해도, 실제 락은
    이 원자적 파일 생성 하나뿐이다: O_CREAT|O_EXCL 은 POSIX 에서 프로세스
    간에도 원자적이라 정확히 하나만 이 파일을 만들 수 있다(실측:
    warrant-hunter 리포트, 이슈 #132).
    """
    events_path = _events_path(work)
    events = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    already_claimed = any(
        ev.get("type") == "respawn-attempt"
        and isinstance(ev.get("detail"), dict)
        and ev["detail"].get("session_start_ts") == session_start_ts
        for ev in events)
    if already_claimed:
        return
    prior = state.get(key, {})
    attempts = prior.get("attempts", 0)
    total_attempts = prior.get("total_attempts", 0)
    prev_fingerprint = prior.get("fingerprint")
    cur_fingerprint = _respawn_fingerprint(work)
    if prev_fingerprint is not None and cur_fingerprint != prev_fingerprint:
        attempts = 0
    root = Path(work)
    # Issue #2068: level-triggered guard — re-read the subject issue's
    # state at act time, before any respawn or cap-comment side effect.
    # CLOSED => never respawn (7 stale respawns in one night came from this
    # path trusting branch existence alone); flag the branch for cleanup
    # instead. A failed gh lookup fails open — same convention as the
    # returned-PR gate (issue #680): a broken gh must not silently strand a
    # crashed-but-legitimate session, and fail-closed here would trade a
    # noise bug for an observation-loss bug.
    issue_state, state_ok = _subject_issue_state(root, issue)
    if not state_ok:
        print(f"[respawn] {key}: issue-state lookup failed — failing open "
              f"(returned-PR gate convention, issue #680)", file=sys.stderr)
        ledger_write({"event": "issue_state_gate_fail_open", "source": "respawn",
                      "issue": issue, "role": role, "ts": int(time.time())})
    elif issue_state == "CLOSED":
        _flag_stale_returned_branch(issue, role, f"issue-{issue}/{role}",
                                    source="respawn")
        return
    if total_attempts >= RESPAWN_ABSOLUTE_MAX:
        _post_crash_comment(root, issue, key, work, log, trigger, absolute=True)
        return
    if attempts >= RESPAWN_MAX_ATTEMPTS:
        _post_crash_comment(root, issue, key, work, log, trigger)
        return
    claim_path = Path(str(work) + f".respawn-claim-{session_start_ts}")
    try:
        fd = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        return
    task_path = Path(str(work) + ".task.txt")
    if not task_path.exists():
        print(f"[respawn] {key}: {trigger} 인데 {task_path} 가 없어 재스폰 불가 "
              f"— 사람이 직접 재스폰해야 한다", file=sys.stderr)
        return
    task = task_path.read_text(encoding="utf-8")
    # Issue #2068 requirement 2: re-read the task from the CURRENT issue at
    # respawn time — the stored `.task.txt` is the text captured at original
    # spawn and can be stale (observed producing zero-output sessions that
    # concluded "nothing to do"). Fetch failure falls back to the stored
    # text (fail-open, issue #680 convention).
    current_task = _current_issue_task_text(root, issue)
    if current_task is not None:
        task = current_task
    if _classify_workspace_completion(work, role) == "finished":
        task = _CONTINUATION_PREAMBLE + "\n\n" + task
    attempt_n = attempts + 1
    total_attempt_n = total_attempts + 1
    _append_event(events_path, "respawn-attempt",
                  {"session_start_ts": session_start_ts, "attempt": attempt_n})
    state[key] = {"attempts": attempt_n, "total_attempts": total_attempt_n,
                  "fingerprint": cur_fingerprint}
    _respawn_state_save(state)
    print(f"[respawn] {key}: {trigger} — 재스폰 시도 {attempt_n}/{RESPAWN_MAX_ATTEMPTS} "
          f"(총 {total_attempt_n}/{RESPAWN_ABSOLUTE_MAX})",
          file=sys.stderr)
    _spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)


def _auto_respawn_check(key: str, entry: dict, state: dict) -> None:
    """죽은 로스터 엔트리 하나에 대해 `crashed` 인지 판정하고, 그렇다면
    `_respawn_or_cap()` 에 넘긴다. `stalled`/`normal`/`in-progress` 는
    재스폰을 걸지 않는다(관찰-전용 계약 유지, 이슈 #132) — 다만 `stalled`
    는 최초 1회 이슈 코멘트로 남는다(이슈 #325): 재스폰하지 않는 것과
    아무도 모르게 재스폰하지 않는 것은 다르다."""
    work = entry.get("work")
    issue = entry.get("issue")
    role = entry.get("role")
    if not work or issue is None or not role:
        return
    log_path = Path(entry["log"]) if entry.get("log") else None
    verdict = session_end_verdict(work, log_path)
    print(f"[watchdog] {key}: {verdict}")
    if verdict == "stalled":
        _post_stall_comment(Path(work), issue, key, work, entry.get("log", ""))
        return
    if verdict != "crashed":
        return
    events_path = _events_path(work)
    events = []
    if events_path.exists():
        for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if isinstance(ev, dict):
                events.append(ev)
    start_ts = None
    for ev in reversed(events):
        if ev.get("type") == "session-start":
            start_ts = (ev.get("detail") or {}).get("ts")
            break
    _respawn_or_cap(key, work, issue, role, entry.get("log", ""), start_ts, state,
                    "watchdog-observed-crashed")


_ABANDONED_WORK_OUTCOMES = ("uncommitted-work", "failed-no-commit", "silent-failure")


def _self_trigger_respawn(outcome: str, roster_key: str, work: str, issue: int,
                          role: str, log: str, session_start_ts) -> None:
    """이슈 #247/#675: `_spawn_one()` 자신이 정상 종료(`session-end` 가 이미
    남는다)했지만 outcome 이 미커밋-방치 신호(`uncommitted-work`/
    `failed-no-commit`) 이거나, 원인 없이 그냥 멈춘 `silent-failure` 일 때,
    다음 `spawn.py watchdog` 틱을 기다리지 않고 지금 이 자리에서 바로
    `_respawn_or_cap()` 을 부른다.

    `roster_watchdog()`/`_auto_respawn_check()` 의 crashed 판정은 이
    경우에 절대 못 걸린다 — `roster_remove()` 가 `proc.wait()` 직후
    동기적으로 로스터 엔트리를 지우고, `session-end` 이벤트도 이미
    남으므로(spawn.py `_spawn_one()` 끝부분), 이후 어떤 워치독 틱도
    dead-but-registered 엔트리를 볼 수 없다(survey.md). `refused`/
    `waiting-on-human` 은 정당한 게이트 거부/대기이지 이 결함의 모양이
    아니라서 여기서 건드리지 않는다(프로포절의 두 번째 기각안). 다만
    `silent-failure` 는 `fail_closed_downgrade()` 를 이미 거쳐 실제로는
    진행됐다고 판명되면 `progressed` 로 승격되므로, 여기 도달하는
    `silent-failure` 는 이미 원인 없는(causeless) 경우로 걸러져 있다.
    """
    if outcome not in _ABANDONED_WORK_OUTCOMES:
        return
    state = _respawn_state_load()
    trigger = ("self-triggered-causeless" if outcome == "silent-failure"
               else "self-triggered-abandoned")
    _respawn_or_cap(roster_key, work, issue, role, log, session_start_ts, state,
                    trigger)




def roster_kill(issue: int, role: str) -> int:
    d = _roster_load()
    key = f"issue-{issue}/{role}"
    e = d.get(key)
    if not e:
        print(f"로스터에 없다: {key}", file=sys.stderr)
        return 1
    pid = e.get("pid", 0)
    if _alive(pid):
        os.kill(pid, 15)
        print(f"종료 신호를 보냈다: {key} (pid {pid}). 워크스페이스와 라이브 "
              f"로그는 남는다 — 재스폰이 이어받는다.")
    else:
        print(f"이미 죽어 있다: {key}")
    roster_remove(key)
    return 0


def _core_candidates() -> list[tuple[str, Path]]:
    """core_root() 가 순서대로 보는 로컬 오버라이드 후보 (라벨, 경로).
    관리 클론(runs/rulebooks/tokenmaxxxer-core)은 이 목록 밖 — 둘 다
    없을 때만 core_root() 가 그리로 떨어지는 별도 단계라 후보가 아니다.
    """
    return [
        ("TOKENMAXXXER_CORE", os.environ.get("TOKENMAXXXER_CORE")),
        ("TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core",
         "$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core"),
    ]


def _skill_repo_valid(d: Path) -> bool:
    """`d` 를 `resolved_skill_dirs()` 가 이미 쓰는 것과 같은 바로 그 기준으로
    "실제 체크아웃"으로 본다: non-dot 서브디렉터리가 하나라도 있는
    디렉터리(요구사항 2 — env/sibling/managed 세 경로 모두 같은 바)."""
    if not d.is_dir():
        return False
    return any(p.is_dir() and not p.name.startswith(".") for p in d.iterdir())


def _skill_repo_managed_root() -> Path | None:
    """관리 클론(이슈 #1789): env 도 형제 체크아웃도 없을 때 on-the-record 가
    직접 `https://github.com/tokenmaxxxer/skill-repository` 를 관리 영역에
    받아 쓴다 — `core_root()` 가 이미 쓰는 다섯 단계
    (로컬 오버라이드 확인은 호출자 쪽에서 이미 끝남 → 관리 디렉터리 유효성
    확인 → 신선하면 재사용 → 아니면 pull-or-clone → 재확인) 를 그대로
    따른다. 네트워크가 죽었을 때 기존 관리 클론이 있으면 그걸 그대로 쓴다
    (오프라인 재사용, 요구사항 1).

    저장소 최상위가 아니라 그 안의 `skills/` 서브디렉터리를 돌려준다 —
    env(`MUSTER_SKILL_REPO`)와 sibling(`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) 두 경로 모두 실측상 이미 `skills/` 를 직접 가리키고
    있고(레포 최상위에는 skills 외에도 docs/scripts/install.sh 가 있다),
    `resolved_skill_dirs()` 는 그 셋을 구분 없이 같은 root 로 받는다 —
    요구사항 2 의 "env-pointed checkout 과 동일한 스킬 해석"이 성립하려면
    관리 클론도 같은 `skills/` 레벨을 돌려줘야 한다."""
    d = ROOT / "runs" / "rulebooks" / "skill-repository"
    d.parent.mkdir(parents=True, exist_ok=True)
    with _locked_rulebook_dir(d):
        skills_dir = d / "skills"
        if _skill_repo_valid(skills_dir):
            if not _pull_is_fresh(d):
                _run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"],
                         "[skill-repo] pull")
                _mark_pulled(d)
            return skills_dir
        try:
            print("[skill-repo] skill-repository 를 받는 중", file=sys.stderr)
            _run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/skill-repository.git",
                     str(d)], "[skill-repo] clone", timeout=CLONE_TIMEOUT)
            _mark_pulled(d)
        except OSError:
            pass
        if _skill_repo_valid(skills_dir):
            return skills_dir
    return None


def _skill_repo_root() -> Path | None:
    """`--skills` 가 마운트할 skill-repository 체크아웃 루트. 순서:
    `MUSTER_SKILL_REPO` env > 형제 클론 (`$TOKENMAXXXER_RULEBOOKS/
    skill-repository`) > 관리 클론(이슈 #1789 — skill-repository가 공개된
    뒤로는 on-the-record 소유 클론이 다른 관리 체크아웃과 같은 fallback을
    쓸 수 있다). 셋 다 없으면 `None`."""
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        p = Path(os.path.expanduser(os.path.expandvars(env_value)))
        if p.is_dir():
            return p
    sibling = os.path.expandvars("$TOKENMAXXXER_RULEBOOKS/skill-repository")
    if "$" not in sibling:
        p = Path(os.path.expanduser(sibling))
        if p.is_dir():
            return p
    return _skill_repo_managed_root()


def resolved_skill_dirs(skills_csv: str | None,
                         repo_root: Path | None) -> list[Path]:
    """`--skills a,b,c` 를 skill-repository 체크아웃 안의 디렉터리 목록으로
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로).
    이름 하나라도 `<repo_root>/<name>` 으로 해석되지 않으면 워크스페이스/
    브랜치를 건드리기 전에 fail-closed(이슈 #1742 요구사항 2)."""
    names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not names:
        return []
    if repo_root is None:
        sys.exit("--skills: skill-repository 체크아웃을 못 찾았다 — "
                  "MUSTER_SKILL_REPO 나 $TOKENMAXXXER_RULEBOOKS/skill-repository 를 확인하고, "
                  "관리 클론도 시도했지만(네트워크나 기존 클론 없음) 실패했다")
    available = sorted(p.name for p in repo_root.iterdir()
                        if p.is_dir() and not p.name.startswith("."))
    unknown = [n for n in names if n not in available]
    if unknown:
        sys.exit(f"--skills: 모르는 스킬 {', '.join(unknown)} "
                  f"— 쓸 수 있는 이름: {', '.join(available)}")
    return [repo_root / n for n in names]


def _installed_plugin_skill_dirs() -> dict[str, list[tuple[str, Path, str]]]:
    """`~/.claude/plugins/installed_plugins.json` (실제 shape:
    `{"plugins": {"<name>@<marketplace>": [{"installPath":...,
    "version"|"gitCommitSha":...}, ...]}}`, `_installed()` 와 같은 파일)을
    읽어 설치된 각 플러그인의 `skills/<name>/` 서브디렉터리를 이름별로
    인덱싱한다: name -> [(qualifier "<name>@<marketplace>", 디렉터리,
    version-or-sha 문자열), ...]. 파일이 없거나 못 읽으면 빈 매핑(이슈
    #1774 요구사항 4: 이 함수는 `--skills` 가 실제로 이름을 낼 때만
    불린다)."""
    p = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        data = json.loads(p.read_text())
    except (OSError, ValueError):
        return {}
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        return {}
    index: dict[str, list[tuple[str, Path, str]]] = {}
    for qualifier, entries in plugins.items():
        if not isinstance(entries, list):
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            install_path = e.get("installPath")
            if not install_path:
                continue
            skills_root = Path(install_path) / "skills"
            if not skills_root.is_dir():
                continue
            version = e.get("version") or e.get("gitCommitSha") or "?"
            for skill_dir in skills_root.iterdir():
                if skill_dir.is_dir() and not skill_dir.name.startswith("."):
                    index.setdefault(skill_dir.name, []).append(
                        (str(qualifier), skill_dir, str(version)))
    return index


def _local_skill_dirs(root: Path) -> dict[str, Path]:
    """`root` 바로 아래의 디렉터리들을 이름 -> 경로로 나열한다(이슈 #1774
    tiers 3/4 공용 — 호출자가 어느 root 를 넘기는지로만 tier 가 갈린다).
    `root` 가 없으면 빈 매핑."""
    if not root.is_dir():
        return {}
    return {p.name: p for p in root.iterdir()
            if p.is_dir() and not p.name.startswith(".")}


def _skill_content_hash(skill_dir: Path) -> str:
    """tier 3/4 소스 정체성(이슈 #1774): 저장소 sha 도 플러그인 버전도 없는
    로컬 디렉터리라, `SKILL.md` 내용의 sha256 을 그 대신 쓴다(proposal
    Rationale: 이 저장소의 스킬 정의 관례가 이미 `SKILL.md` 를 정식 정의
    파일로 취급한다). `SKILL.md` 가 없으면 빈 바이트의 해시."""
    try:
        data = (skill_dir / "SKILL.md").read_bytes()
    except OSError:
        data = b""
    return hashlib.sha256(data).hexdigest()


def _describe_skill_match(m: dict) -> str:
    """에러 메시지/태스크 문구에 쓸, 소스 하나를 사람이 읽는 한 줄로."""
    if m["source"] == "skill-repo":
        return f"skill-repository({m['sha']})"
    if m["source"] == "plugin":
        return f"plugin {m['plugin']}@{m['version']}"
    if m["source"] == "local-user":
        return f"~/.claude/skills ({m['path']})"
    if m["source"] == "local-repo":
        return f".claude/skills ({m['path']})"
    return m["source"]


def resolved_skill_sources(skills_csv: str | None, repo_root: Path | None,
                            home: Path | None = None,
                            target_repo_root: Path | None = None) -> list[dict]:
    """이슈 #1774: `--skills a,b,c` 를 네 소스(skill-repository, 설치된
    플러그인, `~/.claude/skills`, 타깃 저장소 `.claude/skills`)에 걸쳐
    푼다. `skills_csv` 가 비면 빈 목록(마운트 없음, byte-identical 경로 —
    이 경우 네 소스 중 어느 것도 읽지 않는다, 요구사항 4).

    이름 하나가 소스 하나에서만 잡히면 그 소스로 확정. 소스 두 개 이상에서
    잡히면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) 워크스페이스/
    브랜치를 건드리기 전에 fail-closed, 잡힌 소스를 전부 이름 붙여
    보고한다 — 어느 tier 도 다른 tier 를 조용히 가리지 않는다(이슈 #1774
    SCOPE EXTENSION). 어디서도 안 잡히면 오늘과 같은 fail-closed.

    각 소스가 가리키는 디렉터리에 `hooks/` 서브디렉터리가 있으면 —
    스킬 마운트는 가이던스 전용이라는 원칙 위반 — 역시 워크스페이스/
    브랜치 전에 fail-closed(네 소스 모두 동일 규칙).

    반환값은 이름당 dict 하나: 최소 `name`/`source`/`dir` 를 들고, 소스별
    정체성 필드(`sha`|`plugin`+`version`|`path`+`content_sha256`)가
    추가된다."""
    names = [n.strip() for n in (skills_csv or "").split(",") if n.strip()]
    if not names:
        return []
    home = home or Path.home()
    plugin_index = _installed_plugin_skill_dirs()
    tier3 = _local_skill_dirs(home / ".claude" / "skills")
    tier4 = (_local_skill_dirs(target_repo_root / ".claude" / "skills")
             if target_repo_root is not None else {})
    results = []
    for name in names:
        matches: list[dict] = []
        if repo_root is not None and repo_root.is_dir():
            cand = repo_root / name
            if cand.is_dir() and not name.startswith("."):
                matches.append({"source": "skill-repo", "dir": cand,
                                 "sha": skill_repo_sha(repo_root)})
        for qualifier, plugin_skill_dir, version in plugin_index.get(name, []):
            matches.append({"source": "plugin", "dir": plugin_skill_dir,
                             "plugin": qualifier, "version": version})
        if name in tier3:
            d = tier3[name]
            matches.append({"source": "local-user", "dir": d, "path": str(d),
                             "content_sha256": _skill_content_hash(d)})
        if name in tier4:
            d = tier4[name]
            matches.append({"source": "local-repo", "dir": d, "path": str(d),
                             "content_sha256": _skill_content_hash(d)})
        if not matches:
            sys.exit(
                f"--skills: 모르는 스킬 {name} — skill-repository, 설치된 "
                f"플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills "
                f"어디에도 없다")
        if len(matches) > 1:
            sys.exit(
                f"--skills: {name} 가 둘 이상의 소스에서 겹친다 — "
                f"{', '.join(_describe_skill_match(m) for m in matches)} "
                f"(precedence 는 검색 순서일 뿐 충돌을 가리지 않는다)")
        m = matches[0]
        if (m["dir"] / "hooks").is_dir():
            sys.exit(
                f"--skills: {name} ({_describe_skill_match(m)}) 가 hooks/ "
                f"를 들고 있다 — 스킬 마운트는 가이던스 전용이다(집행은 "
                f"core 훅뿐)")
        m["name"] = name
        results.append(m)
    return results


def skill_repo_sha(repo_root: Path) -> str:
    """`repo_root` 체크아웃이 물고 있는 커밋(짧은 sha). `rulebook_version()`
    과 같은 shape — git 실패는 조용히 "?" 로 대체."""
    p = subprocess.run(["git", "-C", str(repo_root), "rev-parse", "--short=7", "HEAD"],
                        capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else "?"


# 이슈 #1955: 전이용 역할-소스 허용목록(#1758)/rulebook 해석 경로 은퇴 —
# 매핑은 더 이상 대상 저장소의 선택적 파일이 아니라 여기 고정된다. 43개
# 역할 전부가 예전 docs/specs 아래 허용목록 파일과 값이 같다(그 파일이
# 이미 모든 역할을 매핑하고 있었다 — 이 상수는 그 내용을 그대로 옮긴 것).
_ROLE_SKILLS = {
    'accessibility': ['accessibility-aria-and-contrast-rules'],
    'api-design': ['api-design-error-design', 'api-design-http-semantics', 'api-design-payload-design', 'api-design-resource-modeling', 'api-design-tool-landscape', 'api-design-versioning-evolution'],
    'architecture': ['architecture-coupling-classification', 'architecture-decomposition-strategy', 'architecture-dependency-direction', 'architecture-interface-contract-shape', 'architecture-module-boundary-definition'],
    'brand-design': ['brand-design-brand-consistency-governance', 'brand-design-brand-identity-strategy', 'brand-design-color-visibility', 'brand-design-logo-clear-space-size', 'brand-design-typography-pairing'],
    'capacity-planning': ['capacity-planning-cost-attribution-at-trigger', 'capacity-planning-demand-shape-and-forecast-method', 'capacity-planning-expansion-trigger-threshold-sizing', 'capacity-planning-headroom-band-and-degradation-risk', 'capacity-planning-safety-buffer-sizing-by-criticality'],
    'conformance-review': ['conformance-review-requirement-extraction', 'conformance-review-sampling-derivation', 'conformance-review-traceability-and-evidence', 'conformance-review-verdict-assignment', 'conformance-review-verification-method-selection', 'conformance-review-finding-record', 'conformance-review-severity-classification'],
    'content-design': ['content-design-operational-playbook'],
    'customer-support': ['customer-support-escalation-path', 'customer-support-five-whys-recurring-scope', 'customer-support-kcs-article-authoring', 'customer-support-research-log', 'customer-support-sla-tier-priority', 'customer-support-subtraction-comprehensibility'],
    'data-engineering': ['data-engineering-data-quality', 'data-engineering-failure-handling', 'data-engineering-pipeline-design'],
    'data-modeling': ['data-modeling-datavault', 'data-modeling-inmon', 'data-modeling-kimball', 'data-modeling-structure'],
    'defect-verification': ['defect-verification-evidence-artifact-completeness', 'defect-verification-independence-from-upstream-verdicts', 'defect-verification-reproduction-evidence-quality', 'defect-verification-severity-band-assignment', 'verify-finding-record', 'verify-severity-classification'],
    'devrel': ['devrel-channel-convention', 'devrel-content-comprehensibility', 'devrel-program-subtraction'],
    'finance-unit-economics': ['finance-unit-economics-cac-payback', 'finance-unit-economics-evidence-chain', 'finance-unit-economics-ltv-cac-band', 'finance-unit-economics-ltv-churn-assumption', 'finance-unit-economics-proposal-shape', 'finance-unit-economics-sensitivity-scenario'],
    'growth-analytics': ['growth-analytics-experiment-trust', 'growth-analytics-funnel-stage-attribution', 'growth-analytics-metric-selection', 'growth-analytics-reporting-reduction', 'growth-analytics-segmentation'],
    'implementation': ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint'],
    'incident-response': ['incident-response-action-item-quality', 'incident-response-blameless-language-editing', 'incident-response-rca-method-selection', 'incident-response-severity-classification-scoping', 'incident-response-timeline-construction', 'incident-response-tool-landscape'],
    'interaction-design': ['interaction-design-form-control-and-layout'],
    'issue-retrospective': ['issue-retrospective-timeline-comprehensibility-and-subtraction-rules'],
    'knowledge-management': ['knowledge-management-curation-pruning', 'knowledge-management-structure-findability', 'knowledge-management-taxonomy-tagging', 'knowledge-management-supersession-lifecycle', 'knowledge-management-pattern-extraction'],
    'legal-compliance': ['legal-compliance-consent-ux', 'legal-compliance-cross-border-transfer', 'legal-compliance-lawful-basis-selection', 'legal-compliance-license-compatibility', 'legal-compliance-research-log', 'legal-compliance-retention-minimization', 'legal-compliance-vendor-dpa'],
    'localization': ['localization-locale-convention-formatting', 'localization-pluralization-and-grammar', 'localization-rtl-and-script-support', 'localization-string-externalization', 'localization-text-expansion-and-layout'],
    'market-analysis': ['market-analysis-competitor-mapping', 'market-analysis-evidence-rigor', 'market-analysis-five-forces', 'market-analysis-jtbd-fit', 'market-analysis-mece-proposal'],
    'marketing': ['marketing-channel-selection', 'marketing-message-persuasion', 'marketing-positioning-differentiation', 'marketing-scope-pruning', 'marketing-segment-targeting'],
    'ml-engineering': ['ml-engineering-evaluation-discipline', 'ml-engineering-ml-test-score-scoring', 'ml-engineering-model-provenance-versioning', 'ml-engineering-rollout-promotion-rollback', 'ml-engineering-serving-pattern-selection', 'ml-engineering-slo-definition-tradeoffs'],
    'observability': ['observability-cardinality-budget', 'observability-explorability', 'observability-methodology-selection', 'observability-phase-trace', 'observability-signal-golden', 'observability-signal-red', 'observability-signal-use'],
    'partnerships-bd': ['partnerships-bd-deal-structure-selection', 'partnerships-bd-exclusivity-and-scope-terms', 'partnerships-bd-governance-cadence-and-kpi', 'partnerships-bd-negotiation-positioning', 'partnerships-bd-term-sheet-comprehensibility-and-convention'],
    'performance-engineering': ['performance-engineering-operational-playbook'],
    'pr-communications': ['pr-communications-message-planning-and-evaluation-rules'],
    'pricing': ['pricing-design-rigor', 'pricing-method-family', 'pricing-scope-gate', 'pricing-tier-structure', 'pricing-verdict-report'],
    'product-discovery': ['product-discovery-guardrail-metric-status', 'product-discovery-hypothesis-preregistration', 'product-discovery-jtbd-problem-framing', 'product-discovery-opportunity-solution-tree-branching', 'product-discovery-rice-ice-prioritization', 'product-discovery-assumption-mapping', 'product-discovery-guardrail-metrics', 'product-discovery-hypothesis-testing', 'product-discovery-one-pager', 'product-discovery-opportunity-solution-tree'],
    'refactoring-legacy': ['refactoring-legacy-characterization-test-scope', 'refactoring-legacy-refactoring-step-decomposition', 'refactoring-legacy-seam-selection', 'refactoring-legacy-strangler-fig-migration', 'refactoring-legacy-verification-cadence'],
    'release-engineering': ['release-engineering-branching-release-strategy', 'release-engineering-changelog-entry-categorization', 'release-engineering-deployment-rollout-strategy', 'release-engineering-release-cadence-and-toil', 'release-engineering-rollback-and-recovery', 'release-engineering-semver-bump-selection', 'release-engineering-error-budget-policy', 'release-engineering-postmortem', 'release-engineering-readiness-checklist', 'release-engineering-rollout-plan'],
    'requirements-engineering': ['requirements-engineering-rules'],
    'risk-management': ['risk-management-aggregation-consolidation', 'risk-management-appetite-tolerance-threshold', 'risk-management-likelihood-impact-scale', 'risk-management-monitoring-review-cadence', 'risk-management-response-strategy-selection'],
    'sales': ['sales-objection-handling', 'sales-pitch-scoping-and-messaging-handoff', 'sales-qualification-and-discovery'],
    'secure-coding': ['secure-coding-authorization-access-control', 'secure-coding-cryptography-secrets-management', 'secure-coding-dependency-supply-chain-security', 'secure-coding-input-validation-injection-defense', 'secure-coding-session-authentication'],
    'security-threat-model': ['security-threat-model-threat-modeling-decision-rules'],
    'technical-feasibility': ['technical-feasibility-build-vs-buy-dependency-health', 'technical-feasibility-license-and-regulatory-risk', 'technical-feasibility-reversibility-and-spike-scoping', 'technical-feasibility-threat-model-disposition', 'technical-feasibility-verdict-and-timebox-selection', 'technical-feasibility-build-vs-buy', 'technical-feasibility-license-scan', 'technical-feasibility-reversibility-tag', 'technical-feasibility-spike-report', 'technical-feasibility-stride-table'],
    'technical-writing': ['technical-writing-doc-type-selection', 'technical-writing-minimalism-scoping', 'technical-writing-persuasion-trust', 'technical-writing-structure-comprehension', 'technical-writing-style-guide-compliance', 'technical-writing-tool-landscape'],
    'test-authoring': ['test-authoring-isolation-and-fixture-strategy'],
    'upstream-defect-report': ['upstream-defect-report-subtraction', 'upstream-defect-report-comprehensibility', 'upstream-defect-report-convention'],
    'user-discovery': ['user-discovery-evidence-strength-tagging', 'user-discovery-follow-up-ladder-depth', 'user-discovery-question-design-past-behavior', 'user-discovery-saturation-stopping-rule', 'user-discovery-switch-timeline-causal-forces', 'user-discovery-verdict-prevalence-reporting'],
    'ux-engineering': ['ux-engineering-color-visibility', 'ux-engineering-control-selection', 'ux-engineering-layout-grouping', 'ux-engineering-navigation-depth', 'ux-engineering-research-log', 'ux-engineering-surface-contrast'],
}


def resolve_role_source(role: str, repo_root: Path | None) -> dict:
    """`role` 을 skill-repository 가이던스로 무조건 해석한다(이슈 #1955:
    전이용 역할-소스 허용목록/rulebook 해석 경로 은퇴, #1758 이 얼린 phase 5
    제약 이행 — 매핑 없는 역할이라는 상태 자체가 더 이상 없다).

    이름을 `resolved_skill_dirs()` 로 푼다(모르는 이름은 이미 거기서
    워크스페이스/브랜치 전에 fail-closed). 풀린 디렉터리 중 하나라도
    `hooks/` 서브디렉터리를 들고 있으면 — skill-repository 는 가이던스
    전용이라는 얼어붙은 프로그램 원칙 위반 — 역시 워크스페이스/브랜치 전에
    fail-closed. {"source": "skill-repo", "skill_dirs": [...],
    "skills": [이름...], "skill_sha": <첫 디렉터리의 부모 저장소 sha>} 를
    돌려준다."""
    names = _ROLE_SKILLS.get(role, [])
    skill_dirs = resolved_skill_dirs(",".join(names), repo_root)
    hooked = [d for d in skill_dirs if (d / "hooks").is_dir()]
    if hooked:
        sys.exit(
            f"resolve_role_source: 역할 {role!r} 이 매핑한 스킬 중 "
            f"{', '.join(d.name for d in hooked)} 가 hooks/ 를 들고 있다 — "
            f"skill-repository 는 가이던스 전용이다(훅 없음, 이슈 #1758)")
    return {"source": "skill-repo", "skill_dirs": skill_dirs,
            "skills": [d.name for d in skill_dirs],
            "skill_sha": skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}


def _skill_source_roster_row(m: dict) -> dict:
    """이슈 #1774 요구사항 3: 마운트된 스킬 한 줄의 로스터/기록용 row —
    소스별로 정체성 필드 shape 가 다르다(proposal `## What will be done`
    item 6)."""
    if m["source"] == "skill-repo":
        return {"name": m["name"], "source": "skill-repo", "sha": m["sha"]}
    if m["source"] == "plugin":
        return {"name": m["name"], "source": "plugin",
                "plugin": m["plugin"], "version": m["version"]}
    return {"name": m["name"], "source": m["source"], "path": m["path"],
            "content_sha256": m["content_sha256"]}


def _skill_roster_fields(skill_sources: list[dict], skill_sha: str | None) -> dict:
    """`--skills` 로 마운트된 스킬들의 로스터/기록 필드. `skills_detail` 은
    쓰였을 때 항상 붙어 소스별 identity(요구사항 3)를 나른다. 오늘의 flat
    `skills`/`skills_sha` shape 는 전부 skill-repo 매치일 때만 additive 로
    같이 붙는다(empty-state 요구: skill-repo-only 조합은 오늘 shape 유지) —
    안 쓰면(빈 목록) 키 자체가 없다."""
    if not skill_sources:
        return {}
    fields = {"skills_detail": [_skill_source_roster_row(m) for m in skill_sources]}
    if all(m["source"] == "skill-repo" for m in skill_sources):
        fields["skills"] = [m["name"] for m in skill_sources]
        fields["skills_sha"] = skill_sha
    return fields


def _role_source_roster_fields(role_source: dict) -> dict:
    """이슈 #1758 요구사항 3 계승, 이슈 #1955 로 단순화: 로스터 엔트리마다
    항상 붙는 resolution 필드. source 는 이제 언제나 skill-repo(rulebook
    해석 경로는 은퇴했다) — resolution_source/resolution_skills/
    resolution_skill_sha 를 채운다."""
    return {"resolution_source": "skill-repo",
            "resolution_skills": role_source["skills"],
            "resolution_skill_sha": role_source["skill_sha"]}


# sibling: core_version
def core_root() -> Path:
    """tokenmaxxxer-core 체크아웃 루트. 없으면 멈춘다.

    core 는 상호작용 프로토콜의 게이트(보드·승인·gh-guard)와 정본 계약을
    들고 있다. 없이 띄우면 역할은 그대로 돌지만 아무도 이탈을 막지 않는다 —
    조용히 보호가 사라지는 쪽이라 경고가 아니라 정지다.
    """
    for _label, cand in _core_candidates():
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return p
    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
    # 로컬 우선은 개발용 오버라이드일 뿐이다.
    d = ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    try:
        d.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    with _locked_rulebook_dir(d):
        if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
            _migrate_legacy_ttl_marker(d)
            if not _pull_is_fresh(d):
                _run_net(["git", "-C", str(d), "pull", "-q", "--ff-only"], "[core] pull")
                _mark_pulled(d)
            return d
        try:
            print("[core] tokenmaxxxer-core 를 받는 중", file=sys.stderr)
            _run_net(["git", "clone", "-q",
                     "https://github.com/tokenmaxxxer/tokenmaxxxer-core.git",
                     str(d)], "[core] clone", timeout=CLONE_TIMEOUT)
            _mark_pulled(d)
        except OSError:
            pass
        if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
            return d
    sys.exit(
        "tokenmaxxxer-core 를 찾지 못했고 받지도 못했다. 역할 세션은 core 없이\n"
        "  뜨지 않는다 — 프로토콜 게이트와 정본 계약이 거기 있다.\n"
        "  네트워크를 확인하거나 체크아웃을 두고 $TOKENMAXXXER_CORE 로 가리켜라.")


# sibling: core_root
def core_version() -> str:
    """core_root() 가 실제로 고를 체크아웃이 **무엇인지** — 읽기 전용, pull 도
    clone 도 하지 않는다. checkout_version() 의 core 쪽 대칭 — 로컬 오버라이드를
    건드리지 않으면서 무엇이 도는지만 매 spawn 로그·ledger 에 남긴다(이슈
    #218: 같은 sha 가 며칠째 안 바뀌어도 로그에 안 남아 stale 게이트로 계속
    돌았다).
    """
    def git(d: Path, *a: str) -> str:
        p = subprocess.run(["git", "-C", str(d), *a], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else ""

    def describe(d: Path, label: str) -> str:
        sha = git(d, "rev-parse", "--short", "HEAD") or "?"
        date = git(d, "log", "-1", "--format=%cs") or "?"
        dirty = " (커밋 안 된 변경 있음)" if git(d, "status", "--porcelain") else ""
        return f"{sha}{dirty} ({date}, {label})"

    for label, cand in _core_candidates():
        if not cand:
            continue
        p = Path(os.path.expanduser(os.path.expandvars(cand)))
        if "$" in str(p):
            continue
        if (p / "core" / ".claude-plugin" / "plugin.json").is_file():
            return describe(p, label)
    d = ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"
    if (d / "core" / ".claude-plugin" / "plugin.json").is_file():
        _migrate_legacy_ttl_marker(d)
        return describe(d, "on-the-record 클론")
    return "버전 불명 (core 체크아웃 없음)"


def core_plugin_dirs() -> list[Path]:
    """core 마켓플레이스가 선언한 플러그인 전부 — marketplace.json 이 정본이다.

    마켓플레이스 설치가 아니라 `--plugin-dir` 로 붙인다(실측 2026-07-27,
    CLI 2.1.220: 디렉터리로 넘긴 플러그인의 훅이 headless 에서 그대로
    발화한다). 설치를 거치지 않으므로 캐시·클론 갈라짐도 유령 등록 항목도
    이 경로에는 없다.

    core 플러그인은 scope-gate·hunt-guard 같은 공유 강제 장치라 role 자체
    확장(plugin_dirs())과 달리 하나라도 빠지면 조용히 넘길 수 없다 — 선언은
    됐는데 디렉터리가 없으면 즉시 sys.exit (이슈 #282: 4개짜리 하드코드
    튜플이 marketplace.json 이 다섯 번째로 늘린 warrant 를 계속 빠뜨렸는데
    아무 신호도 없었다).
    """
    root = core_root()
    plugins = json.loads(_mkt(root).read_text())["plugins"]
    out = []
    for p in plugins:
        src = p.get("source") or f"./{p['name']}"
        if not isinstance(src, str):
            continue                      # {source: github, ...} 같은 원격 지정 — core 는 항상 로컬
        sub = (root / src.lstrip("./")).resolve()
        if not (sub / ".claude-plugin" / "plugin.json").is_file():
            sys.exit(f"core 플러그인 '{p['name']}' 이 marketplace.json 에는 선언됐지만 "
                      f"{sub / '.claude-plugin' / 'plugin.json'} 이 없다 — 조용히 건너뛰지 않는다.")
        out.append(sub)
    return out


def drive(cwd: str, unattended: bool, limit: int = 12) -> int:
    """드라이버의 유일한 계약상 임무: 더 띄울 게 없으면 멈춘다.

    "누구를 다음에 띄울지"는 기계가 평가하는 라우팅 표가 아니라 오케스트레이터가
    보드(기록, loop_state)를 직접 읽고 내리는 판단이다(이슈 #120) — 그래서
    drive 는 스스로 역할을 고르지 않는다. 자동으로 고를 표가 없으므로 이
    호출은 항상 즉시 멈춘다; 남은 인자는 향후 호출부 호환을 위해 받되 쓰지
    않는다.

    이슈 #492 (ADR): `reconcile()` 이 낸 divergence 를 소비하는 것으로
    바뀐다 — 로스터를 읽어 엔트리마다 `reconcile()` 을 돌리고 결과와
    `next_action` 을 출력한다. #120 계약은 그대로다: drive() 는 여전히
    아무 역할도 스스로 고르지 않고, 무엇을 띄울지는 오케스트레이터의
    판단으로 남긴다 — 여기서 respawn/resume-watch 를 자동 실행하지 않는다.
    """
    root = Path(cwd).resolve()
    d = _roster_load()
    if not d:
        print("[drive] 돌고 있는 역할 세션 없음 — 보고할 divergence 없음. 멈춘다.",
              file=sys.stderr)
        return 0
    found = False
    for key, e in sorted(d.items()):
        divergences = reconcile(_build_expected(e), _build_observed(root, e),
                                 recovery_state_dir=root / ".on-the-record" / "recovery-state")
        for div in divergences:
            found = True
            print(f"[drive] {key}: {div['kind']}: {div['detail']} "
                  f"-> next_action={div['next_action']}", file=sys.stderr)
    if not found:
        print("[drive] divergence 없음 — 다음 역할을 자동으로 고르는 라우팅 "
              "표는 없다(이슈 #120). 오케스트레이터가 보드를 읽고 판단한다. "
              "띄울 게 없다고 보고 멈춘다.", file=sys.stderr)
    return 0


def _claude_version() -> str:
    try:
        out = subprocess.run(["claude", "--version"], capture_output=True,
                             text=True, timeout=30)
        return out.stdout.strip().splitlines()[0] if out.stdout.strip() else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def require_doctor(version: str | None = None) -> None:
    """이 CLI 버전에서 훅이 headless 로 도는 것을 doctor 가 실측했는지 본다.

    룰북 집행 전체가 '플러그인 훅이 -p 세션에서 돈다'는 한 문장 위에 서
    있는데, 그 문장은 공식 문서에 없다 — 실측(2026-07-27, 2.1.220)뿐이다.
    CLI 는 자동 업데이트되므로, 버전이 바뀌면 게이트 전부가 소리 없이
    사라질 수 있다. 그래서 버전마다 한 번, 실측을 다시 요구한다.
    """
    v = version if version is not None else _claude_version()
    ok = ROOT / "runs" / "doctor-ok"
    if not v:
        sys.exit("claude --version 을 읽지 못했다. claude 가 PATH 에 있나?")
    if not ok.is_file() or ok.read_text().strip() != v:
        if version is not None:
            # 명시된 버전(테스트 포함)에는 프로브를 태우지 않는다 — 옛 계약
            # 그대로 정지한다.
            sys.exit(
                f"이 CLI({v})에서 훅이 headless 로 도는 것을 아직 실측하지 않았다.\n"
                f"먼저 돌려라: python3 spawn.py doctor   (실 세션 1회, 소액 과금)")
        # 미측정 버전이면 그 자리에서 잰다 — 사용자에게 명령 하나를 더
        # 요구할 이유가 없다. 프로브 세션 1회(하이쿠, 소액)가 돈다.
        print(f"[doctor] CLI {v} 는 아직 실측 전이다 — 훅 발화 프로브를 "
              f"먼저 돌린다 (실 세션 1회, 소액 과금)", file=sys.stderr)
        if doctor() != 0 or not (ok.is_file() and ok.read_text().strip() == v):
            sys.exit(
                f"이 CLI({v})에서 플러그인 훅이 headless 로 발화하지 않는다 — "
                f"게이트 전부가 조용히 사라지는 버전이라 스폰을 막는다.")


def doctor() -> int:
    """프로브 플러그인 하나로 실 세션을 띄워 UserPromptSubmit / PreToolUse 가
    실제로 발화하는지 잰다. 성공하면 runs/doctor-ok 에 CLI 버전을 적는다."""
    v = _claude_version()
    if not v:
        print("claude --version 실패", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as td:
        plug = Path(td) / "probe"
        (plug / ".claude-plugin").mkdir(parents=True)
        (plug / "hooks").mkdir()
        (plug / ".claude-plugin" / "plugin.json").write_text(json.dumps(
            {"name": "muster-probe", "version": "0.0.0",
             "description": "hook-firing canary"}))
        ups, pre = Path(td) / "ups", Path(td) / "pre"
        (plug / "hooks" / "hooks.json").write_text(json.dumps({"hooks": {
            "UserPromptSubmit": [{"hooks": [
                {"type": "command", "command": f"touch {ups}"}]}],
            "PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": f"touch {pre}"}]}],
        }}))
        work = Path(td) / "work"
        work.mkdir()
        subprocess.run(["git", "init", "-q", str(work)], check=False)
        # --model haiku: 프로브의 관심사는 훅 로딩이지 모델이 아니다. 싸게 간다.
        subprocess.run(
            ["claude", "-p", "--plugin-dir", str(plug), "--model", "haiku",
             "--max-turns", "2", "--output-format", "json"],
            cwd=work, input="Run this exact bash command and nothing else: echo ok",
            text=True, capture_output=True, timeout=180)
        fired_ups, fired_pre = ups.is_file(), pre.is_file()
    print(f"UserPromptSubmit: {'발화' if fired_ups else '침묵'} / "
          f"PreToolUse: {'발화' if fired_pre else '침묵'}  (CLI {v})")
    if fired_ups and fired_pre:
        d = ROOT / "runs"
        d.mkdir(exist_ok=True)
        (d / "doctor-ok").write_text(v)
        print("doctor-ok 기록. 이 버전에서 스폰이 열린다.")
        return 0
    print("훅이 headless 에서 발화하지 않는다 — 이 CLI 버전으로는 룰북 집행이 "
          "성립하지 않는다. 스폰은 계속 막힌다.", file=sys.stderr)
    return 1


ROLE_MODEL_CONFIG = ROOT / "role_model.txt"


def read_role_model_config() -> str:
    """이슈#60: repo-root role_model.txt 에서 기본 모델 값을 읽는다. 파일이
    없거나 읽기 오류가 나면 미설정과 동일하게 "" 를 돌려준다."""
    try:
        return ROLE_MODEL_CONFIG.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def resolved_role_model(cli_model: str | None = None, role: str | None = None,
                         single_phase: bool = False,
                         design_bearing_verdict: bool | None = None) -> tuple[str, str] | str:
    """이슈#93: env > config > built-in default("sonnet"). MUSTER_ROLE_MODEL 이
    (strip 후) 비어 있지 않으면 그것이 이긴다 — config 는 그때는 아예 안 읽힌
    값처럼 무시된다. 둘 다 비어 있으면 "sonnet" — --model 이 항상 붙는다,
    호출자의(비쌀 수 있는) 세션 모델을 조용히 물려받지 않도록.

    이슈#1736: `cli_model` 이(strip 후) 비어 있지 않으면 최우선으로 이긴다
    — 단일 스폰에 대한 per-invocation 오버라이드, env/config 는 아예 안
    읽힌 것처럼 건너뛴다. 생략하면(기본값 None) 이전 동작과 byte-identical.

    이슈#2070: `role` 이 주어지면(기존 세 rung 이 전부 비었을 때만) built-in
    `"sonnet"` 종착점 대신 `gates/model_routing.py`의 구조적 라우팅 계층을
    태운다 — `--model` 과 `MUSTER_ROLE_MODEL`/`role_model.txt` 는 그대로
    최우선으로 이긴다(회귀 없음). 반환값은 (model, rule) 튜플로 바뀌지만
    `role` 을 생략하면(기본값 None) 이전 세 rung 은 그대로이고 반환값도
    문자열 하나 그대로다 — byte-identical."""
    cli_value = (cli_model or "").strip()
    if cli_value:
        return (cli_value, "cli-override") if role is not None else cli_value
    env_value = (os.environ.get("MUSTER_ROLE_MODEL") or "").strip()
    if env_value:
        return (env_value, "env-override") if role is not None else env_value
    config_value = read_role_model_config()
    if config_value:
        return (config_value, "config-override") if role is not None else config_value
    if role is not None:
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import model_routing
        policy = model_routing.load_policy(ROOT)
        return model_routing.route_model(role, single_phase, design_bearing_verdict, policy)
    return "sonnet"


def spawn_cmd(settings_path: str, role: str, unattended: bool,
              core_plugins: list | None = None,
              plugins: list | None = None,
              model: str | None = None,
              skill_dirs: list | None = None,
              skill_repo_sha_value: str | None = None,
              single_phase: bool = False,
              design_bearing_verdict: bool | None = None,
              max_turns: int | None = None) -> tuple[list[str], dict[str, str]]:
    """세션 argv 와 env **추가분**. 호출자가 os.environ 위에 얹는다.

    --permission-mode bypassPermissions (issue #700): 샌드박스 제거(#695/#697)
    이후 모든 Bash 가 승인 분류기 앞에 서는데 headless 는 답할 사람이 없어
    allowlist 밖 명령이 전부 죽는다(실측 2026-08-11: issue-698 세션이
    `git add`/`gh issue view` 에서 failed-no-commit). 운영자 결정으로
    bypassPermissions 가 기본값이다 — 집행은 훅(PreToolUse exit 2)이 계속
    맡고, bypassPermissions 는 훅을 끄지 않는다(#697 이전의 acceptEdits
    실측과 동일 근거).

    TOKENMAXXXER_SPAWNED: 스폰된 세션의 프롬프트는 오케스트레이터가 쓴
    텍스트이지 사람 턴이 아니다. core 의 mint 훅이 이 도장을 보고 발행을
    거른다. UNATTENDED 와 별개다 — 그쪽은 "사람이 없다"는 사실이고, 겹쳐
    쓰면 attended 스폰이 깨진다.
    """
    cmd = ["claude", "-p", "--settings", settings_path,
           "--permission-mode", "bypassPermissions",
           "--output-format", "stream-json", "--verbose"]
    # Issue #2100 item 4: session turn budget pass-through. `None` keeps
    # today's argv byte-identical (callers that never resolved a budget);
    # `_spawn_one` always passes the resolved cap. <= 0 means an explicit,
    # admission-approved unlimited run — no flag is attached.
    if max_turns is not None and max_turns > 0:
        cmd += ["--max-turns", str(max_turns)]
    # 룰북도 core 와 같은 길로 붙는다 — 디렉터리로 넘긴 플러그인의 훅은
    # headless 에서 그대로 발화하고(실측 2026-07-27, CLI 2.1.220), 설치를
    # 안 거치므로 캐시-클론 갈라짐도 유령 등록 항목도 이 경로엔 없다.
    for p in (plugins or []):
        cmd += ["--plugin-dir", str(p)]
    for p in (core_plugins or []):
        cmd += ["--plugin-dir", str(p)]
    # 이슈 #1742: --skills 로 마운트한 스킬 디렉터리. rulebook/core 뒤에
    # 붙는다 — 순서는 우선순위가 아니라 추가분(additive)이라 어디 붙어도
    # 무방하지만, skill_dirs 가 falsy 면(기본값) 이 루프가 아무 것도 안 붙여
    # no-flag 경로의 argv 를 바이트 단위로 그대로 둔다.
    for p in (skill_dirs or []):
        cmd += ["--plugin-dir", str(p)]
    # MUSTER_ROLE_MODEL / role_model.txt (이슈#93): 역할 세션이 쓰는 모델을
    # 고정한다. env > config > built-in "sonnet". 둘 다 비어있어도 built-in
    # 이 이겨 --model 이 항상 붙는다 — haiku 프로브(doctor())는 이 함수를
    # 거치지 않으므로 영향 없다.
    role_model, model_rule = resolved_role_model(
        model, role=role, single_phase=single_phase,
        design_bearing_verdict=design_bearing_verdict)
    if role_model:
        cmd += ["--model", role_model]
    env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1",
           # 이슈 #2070: roster 기록용 — `_spawn_one()` 이 실제 subprocess env
           # 로 넘기기 전에 이 두 내부 키를 꺼내 roster 엔트리에 옮겨 담는다.
           "_MODEL_ROUTING_MODEL": role_model or "",
           "_MODEL_ROUTING_RULE": model_rule}
    # Two-account model (core README): role sessions act as the AGENT
    # account. MUSTER_AGENT_GH_TOKEN, if set, becomes the session's GH_TOKEN
    # so gh in the container/sandbox authenticates as the agent — never the
    # user. gh-guard denies the human's acts in role sessions regardless.
    # 샌드박스 안에서는 macOS 키링이 안 보여 gh 토큰이 무효로 읽힌다(실측).
    # 그래서 토큰을 env 로 명시 주입한다: 에이전트 토큰이 있으면 그것,
    # 없으면(1계정 기본) 사용자의 gh 토큰을 꺼내 넘긴다. gh-guard 가
    # 역할 세션의 사람-행위 명령은 어차피 막는다.
    # `_resolve_gh_token()` 과 로직을 공유한다(중복 제거, 이슈 발견:
    # 오케스트레이터 자신의 git 호출은 이 로직이 없어서 인증 없이 돌았다) —
    # 캐시도 공유해서, 이 스폰에서 `_fetch_or_halt()` 가 먼저 불렸다면
    # `gh auth token` 을 또 shell-out 하지 않는다.
    agent_token = _resolve_gh_token()
    if agent_token:
        env["GH_TOKEN"] = agent_token
        env["GIT_TERMINAL_PROMPT"] = "0"
    if unattended:
        env["TOKENMAXXXER_UNATTENDED"] = "1"
    if skill_dirs:
        env["MUSTER_SKILLS"] = ",".join(Path(p).name for p in skill_dirs)
        env["MUSTER_SKILL_REPO_SHA"] = skill_repo_sha_value or "?"
    # 룰북 게이트는 core 공유 라이브러리를
    # ${CLAUDE_PLUGIN_ROOT_CORE:-<상대경로>/core} 로 참조한다(이슈#182). 이
    # 변수를 주입하지 않으면 상대 fallback 이 룰북 클론 내부를 가리켜
    # 실배포에서 해석 실패 → 무가드 source 와 결합 시 게이트 전면
    # fail-open. core_plugins 는 core_plugin_dirs() 가 이미 해결해
    # --plugin-dir 로 넘기는 그 경로이므로, 여기서 재사용하면 "주입된
    # 경로 == 실제 로드된 core 플러그인 경로" 불변식이 코드 구조로
    # 보장된다.
    core_dir = next((p for p in (core_plugins or []) if Path(p).name == "core"), None)
    if core_dir:
        env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
    else:
        print("spawn_cmd: core_plugins 에 'core' 엔트리가 없다 — "
              "CLAUDE_PLUGIN_ROOT_CORE 미주입, 게이트가 fallback 경로로 "
              "빠질 수 있다", file=sys.stderr)
    return cmd, env


def ensure_target_remote(cwd: str, unattended: bool) -> None:
    """`origin` 원격 유무를 역할 스폰 전에 정리한다(이슈 #831).

    #830 실측: 헤드리스 top-level 세션이 `--issue` 없는 첫 스폰은 통과하고
    (issue_workspace 를 안 거치므로), 실제 작업을 시키는 두 번째 `--issue`
    스폰에서야 `issue_workspace`(4303행)의 무조건 `sys.exit` 에 걸렸다 —
    사람이 답할 수 없는 프로세스 안에서 사람에게 묻는 모양(req#5 FAIL).
    이 게이트를 `main()` 스폰 분기 앞으로 당겨, 그 질문이 원래
    `docs/handbooks/setup.md` 가 문서화한 대로 사람이 실제로 있는
    top-level 대화에서만 나오게 한다. `docs/issue-831/decisions/
    2026-08-11-setup-preflight-remote-gate.md` 의 결정을 그대로 구현한다.
    """
    r = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    if r.stdout.strip():
        return
    fail_msg = (f"대상 레포에 origin 원격이 없다: {cwd} — 이슈/PR 모델은 "
                f"GitHub 원격이 전제다 (계약 v3 s10). 최초 1회, attended "
                f"세션(--unattended 없이)에서 먼저 설정하라.")
    if unattended:
        sys.exit(fail_msg)
    print("대상 레포에 GitHub 원격(origin)이 없다. 최초 1회 설정이 필요하다:\n"
          "  y  — gh repo create --private --source . --push 로 새로 만든다\n"
          "  <기존 원격 URL>  — 그 원격을 origin 으로 붙인다\n"
          "  (그 외 입력/빈 입력)  — 거절, 아무것도 안 한다")
    answer = input("설정할까? [y/<URL>/N]: ").strip()
    if answer.lower() == "y":
        subprocess.run(["gh", "repo", "create", "--private", "--source", cwd,
                        "--push"], cwd=cwd, check=True)
    elif answer:
        subprocess.run(["git", "-C", cwd, "remote", "add", "origin", answer],
                       check=True)
    else:
        sys.exit(fail_msg)
    r = subprocess.run(["git", "-C", cwd, "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    origin = r.stdout.strip()
    if not origin:
        sys.exit(fail_msg)
    ledger_write({"event": "remote_setup_confirmed", "cwd": str(Path(cwd).resolve()),
                  "origin": origin, "ts": int(time.time())})


def positive_int(s: str) -> int:
    """argparse type=: `--issue` 는 1 이상만 유효하다 — 0/음수/거대정수는
    존재할 수 없는 이슈 번호이므로 파싱 시점에 바로 거부한다(#288 N3)."""
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError(f"양의 정수가 아니다: {s}")
    return v


def _workspace_base() -> Path:
    """워크스페이스 루트: `MUSTER_WORK_DIR` 오버라이드, 기본
    `~/.tokenmaxxxer/work` (이슈 #1179 — 이전엔 `clean` CLI 분기와
    `issue_workspace()` 두 곳에 이 네 줄이 따로 있었다)."""
    base = os.environ.get("MUSTER_WORK_DIR")
    return Path(base) if base else Path.home() / ".tokenmaxxxer" / "work"


def _live_workspaces() -> dict[Path, dict]:
    """살아있는(pid alive) 로스터 엔트리를 워크스페이스 절대경로로 인덱싱."""
    roster = _roster_load()
    live = {}
    for e in roster.values():
        if _alive(e.get("pid", 0)):
            live[Path(e["work"]).resolve()] = e
    return live


# 이슈 #1179 (reopen): 훅이 워크스페이스 안에 직접 심어놓는 자체 부기
# 파일 — 사용자가 만든 내용이 아니라 harness 자신의 상태 마커라
# untracked 로 남아도 "미보존 작업"이 아니다. 이 목록에 없는 파일은
# 전부 그대로 dirty 취급(안전 기본값 유지) — 이름을 아는 것만 뺀다.
_HARNESS_NOISE_BASENAMES = frozenset({
    ".pull-check", ".shallow-check", ".orchestrate-greeted",
    ".warrant-hunt.count", ".warrant-hunt.lock",
    # 파이썬 바이트코드 캐시 — 어느 리포에서도 소스에서 재생성되는
    # 순수 파생물이라 "미보존 작업"일 수가 없다(실측 최다 노이즈,
    # 320개 워크스페이스 중 335건).
    "__pycache__",
    # project-rich 리포의 테스트/빌드 산출물 — `file` 로 확인한 SQLite
    # db 와 컴파일된 JS/HTML 번들, 소스 아님(실측: project-rich-issue-*
    # 워크스페이스 다수가 이 파일 하나 때문에만 dirty 로 잡혔다).
    "fundamentals.db", "fundamentals.db-shm", "fundamentals.db-wal",
    "web_out_snapshot", "web_out",
})


def _workspace_clean_state(w: Path, live: dict[Path, dict]) -> tuple[str | None, str]:
    """워크스페이스 하나가 지워도 안전한지 판정한다. `(reason, detail)` —
    `reason` 이 `None` 이면 안전(지워도 됨), 아니면 남기는 이유
    (`"live"`/`"dirty"`) 와 사람이 읽을 상세 문자열.

    `roster_clean()`(수동)과 `auto_sweep()`(자동, 이슈 #1179)이 같은 판정을
    쓴다 — 두 곳에 독립적으로 안전 검사를 두면 한쪽만 고치고 다른 쪽은
    #1124 보장이 조용히 깨진다."""
    e = live.get(w.resolve())
    if e is not None:
        return ("live",
                f"실행 중인 세션 있음: issue-{e.get('issue', '?')}/"
                f"{e.get('role', '?')}, pid {e.get('pid', '?')}")
    raw_st = subprocess.run(["git", "-C", str(w), "status", "--porcelain"],
                            capture_output=True, text=True).stdout.strip()
    # untracked(`??`)이면서 harness 자체 마커 파일인 줄만 걸러낸다 —
    # staged/tracked 변경(M/D/A 등)은 절대 걸러내지 않는다: 실측
    # (2026-08-13, 이 머신) 잔여 320개 워크스페이스 중 293개가 이
    # 마커 파일들 때문에 dirty 로 잘못 잡혔다.
    st_lines = [ln for ln in raw_st.splitlines()
                if not (ln[:2] == "??"
                        and os.path.basename(ln[3:].rstrip("/"))
                        in _HARNESS_NOISE_BASENAMES)]
    st = "\n".join(st_lines)
    ahead = subprocess.run(
        ["git", "-C", str(w), "log", "--branches", "--not", "--remotes",
         "--oneline"], capture_output=True, text=True).stdout.strip()
    if ahead:
        # 레거시 워크스페이스는 생성 뒤 다시 fetch 된 적이 없어, 브랜치가
        # 이미 origin 에 머지됐어도 로컬 remote-tracking ref 가 그 사실을
        # 모른다 — "ahead" 로 영원히 오판된다(실측, accessibility-rulebook
        # issue-19: fetch 전 2건 ahead, fetch 후 0건). 작업트리가 이미
        # 깨끗할 때만 한 번 fetch 로 갱신하고 재판정한다 — fetch 는
        # 로컬을 지우지 않으니 안전.
        if not st:
            try:
                subprocess.run(["git", "-C", str(w), "fetch", "-q", "--all"],
                               capture_output=True, text=True, timeout=30)
            except (subprocess.TimeoutExpired, OSError):
                pass
            ahead = subprocess.run(
                ["git", "-C", str(w), "log", "--branches", "--not",
                 "--remotes", "--oneline"],
                capture_output=True, text=True).stdout.strip()
    if st or ahead:
        detail = "미보존 작업 있음"
        if st:
            detail += f"  [미커밋 {len(st.splitlines())}건]"
        if ahead:
            detail += f"  [미push 커밋 {len(ahead.splitlines())}건]"
        return ("dirty", detail)
    return (None, "")


def _delete_workspace(w: Path, wb: Path, log_outcomes: dict[str, str],
                       archive_dir: Path) -> None:
    """안전 판정을 이미 통과한 워크스페이스 하나를 지운다. 디렉터리는
    그대로 삭제, 형제 파일(로그 등)은 ledger outcome 이 `LANDED_OUTCOMES`
    밖이면(refused/errored/silent-failure 등) 유일한 증거이므로 지우지
    않고 `<wb>/.archived-logs/` 로 옮긴다(이슈 #1124). 실패하면
    예외를 그대로 던진다 — 호출자가 removed/failed 집계를 한다."""

    def _chmod_retry(func, path, exc_info):
        # Go 모듈 캐시 등 읽기 전용 디렉터리/파일에서 rmtree 가
        # PermissionError 로 죽는 문제(이슈 #229). POSIX 에서 파일
        # 삭제는 그 파일 자체가 아니라 부모 디렉터리의 쓰기 권한이
        # 좌우하므로, 실패한 경로와 그 부모 모두에 쓰기 권한을 주고
        # 한 번 재시도한다.
        os.chmod(path, stat.S_IWRITE)
        parent = os.path.dirname(path)
        if parent:
            os.chmod(parent, stat.S_IWRITE | stat.S_IEXEC | stat.S_IREAD)
        func(path)

    import shutil
    if sys.version_info >= (3, 12):
        shutil.rmtree(w, onexc=_chmod_retry)
    else:
        shutil.rmtree(
            w, onerror=lambda func, path, exc_info: _chmod_retry(
                func, path, exc_info))
    # 세대별 로그(`.session.<ts>.<pid>.log`, 이슈 #192)와
    # `.events.jsonl`/`.events.offset`/`.task.txt`/
    # `.respawn-claim-*` 같은 형제 산출 파일을 전부 글롭으로 잡는다 —
    # 접미사를 하나씩 나열하면 다음에 하나 더 생길 때 또 빠뜨린다.
    for sibling in w.parent.glob(w.name + ".*"):
        if not sibling.is_file():
            continue
        outcome = log_outcomes.get(str(sibling))
        if outcome is not None and outcome not in LANDED_OUTCOMES:
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(sibling), str(archive_dir / sibling.name))
        else:
            sibling.unlink()


def roster_clean(wb: Path, issue: int | None) -> int:
    """`spawn.py clean [--issue N]`: 안전한 것만 지운다 — 미커밋 변경 없음 +
    origin 에 없는 커밋 없음. 워크스페이스 디렉터리는 그 조건만 지키면
    그대로 삭제한다(이슈 #1124 범위 밖). 형제 파일(로그 등)은
    `_delete_workspace()` 가 archive-or-delete 판정을 한다."""
    live = _live_workspaces()
    log_outcomes = _ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"

    scope = f"-issue-{issue}-" if issue is not None else None
    removed = kept = failed = 0
    for w in sorted(wb.glob("*")) if wb.is_dir() else []:
        if not (w / ".git").is_dir():
            continue
        if scope is not None and scope not in w.name:
            continue
        reason, detail = _workspace_clean_state(w, live)
        if reason is not None:
            print(f"남김 ({detail}): {w.name}")
            kept += 1
            continue
        try:
            _delete_workspace(w, wb, log_outcomes, archive_dir)
        except Exception as ex:
            print(f"실패 (삭제 중 예외): {w.name}  [{ex}]")
            failed += 1
            continue
        print(f"지움: {w.name}")
        removed += 1
    summary = f"정리 끝 — 지움 {removed}, 남김 {kept}"
    if failed:
        summary += f", 실패 {failed}"
    print(summary)
    return 0


# 이슈 #1465: poll-heartbeat.sh 의 alive 마커는 세션 시작 시 한 번만
# touch 된다(60초 tick 루프가 시작하기 전, monitors/poll-heartbeat.sh:100-108
# 부근) — 그 스크립트 자신의 tick cadence 상수가 `POLL_HEARTBEAT_SLEEP_SECONDS`
# 기본값 60초다. GC 임계값은 그 cadence 보다 안전하게 커야 한다(그렇지
# 않으면 아직 살아있는 세션의 마커까지 지울 수 있다) — 7일로 잡아 세션이
# 하루 이상 이어져도 안전하게 남긴다.
MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = 120
MONITOR_ALIVE_STALE_THRESHOLD_SECONDS = 7 * 24 * 3600
assert MONITOR_ALIVE_STALE_THRESHOLD_SECONDS > MONITOR_ALIVE_TOUCH_CADENCE_SECONDS

LEGACY_MONITOR_ALIVE_DIRNAME = ".orchestrate-monitor-alive"


def _monitor_alive_root() -> Path:
    """`~/.claude/tokenmaxxxer/monitor-alive` — poll-heartbeat.sh 가 alive
    마커를 쓰는 곳과 같은 해시 규약(이슈 #947/#1280 relocation).
    `MUSTER_TOKENMAXXXER_HOME` 오버라이드는 `~/.tokenmaxxxer`용이라 여기엔
    안 쓴다 — 대신 이 GC 전용 오버라이드로 테스트를 격리한다."""
    override = os.environ.get("MUSTER_MONITOR_ALIVE_ROOT")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "tokenmaxxxer" / "monitor-alive"


def gc_monitor_alive(root: Path | None = None,
                      now: float | None = None,
                      threshold_seconds: float = MONITOR_ALIVE_STALE_THRESHOLD_SECONDS
                      ) -> dict[str, int]:
    """`~/.claude/tokenmaxxxer/monitor-alive/<hash24>/` 아래 stale 마커
    디렉터리를 지운다. `alive` 파일의 mtime(없으면 디렉터리 자체의 mtime)이
    `threshold_seconds` 보다 오래됐으면 지운다. 한 항목에서 나는 오류는
    전체 GC 를 죽이지 않는다(watch-coverage 는 observe-only 라 정리 실패로
    죽으면 안 된다, 이슈 #1465 요구사항 4) — per-entry try/except 로 흡수하고
    `errors` 카운트만 올린다."""
    if root is None:
        root = _monitor_alive_root()
    if now is None:
        now = time.time()
    removed = kept = errors = 0
    try:
        entries = sorted(root.glob("*")) if root.is_dir() else []
    except OSError:
        return {"removed": 0, "kept": 0, "errors": 1}
    for entry in entries:
        try:
            if not entry.is_dir():
                continue
            alive_marker = entry / "alive"
            try:
                mtime = alive_marker.stat().st_mtime
            except OSError:
                mtime = entry.stat().st_mtime
            age = now - mtime
            if age > threshold_seconds:
                import shutil
                shutil.rmtree(entry)
                removed += 1
            else:
                kept += 1
        except OSError:
            errors += 1
    return {"removed": removed, "kept": kept, "errors": errors}


def detect_legacy_monitor_alive_dirs(repo_root: Path) -> list[Path]:
    """`.orchestrate-monitor-alive/` 레거시 디렉터리(relocation 이전,
    이슈 #947/#1280)를 리포트만 한다 — 절대 지우지 않는다(이슈 #1465
    요구사항 3)."""
    try:
        candidate = repo_root / LEGACY_MONITOR_ALIVE_DIRNAME
        if candidate.is_dir():
            return [candidate]
    except OSError:
        pass
    return []


def monitor_alive_gc_cli(cwd: Path) -> int:
    """`spawn.py gc-monitor-alive` — heartbeat 시작 시 poll-heartbeat.sh 가
    호출한다(non-fatal, `|| true`로 감싸 호출됨). GC 자체는 위 함수들에서
    이미 예외를 흡수하지만, 이 진입점도 한 번 더 감싸 정말로 절대 죽지
    않게 한다."""
    try:
        stats = gc_monitor_alive()
        print(f"monitor-alive gc: removed {stats['removed']}, "
              f"kept {stats['kept']}, errors {stats['errors']}")
    except Exception as ex:
        print(f"monitor-alive gc: 실패 (예외, non-fatal) [{ex}]")
    try:
        for legacy in detect_legacy_monitor_alive_dirs(cwd):
            print(f"[legacy-monitor-alive] {legacy} — 레거시 디렉터리, "
                  f"수동 확인 필요 (자동 삭제 안 함)")
    except Exception as ex:
        print(f"monitor-alive gc: 레거시 탐지 실패 (예외, non-fatal) [{ex}]")
    return 0


def _dir_size_bytes(w: Path) -> int:
    """워크스페이스 디렉터리 전체 크기(바이트) — `du` 대신 순수 파이썬으로,
    심볼릭 링크는 따라가지 않는다(순환 방지, 대부분 워크스페이스엔 없다)."""
    total = 0
    for p in w.rglob("*"):
        if p.is_file() and not p.is_symlink():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def _clean_auto_enabled() -> bool:
    """`MUSTER_CLEAN_AUTO` — 기본 on. `MUSTER_KEEP_SSH` 와 같은 boolean
    파싱 관례(spawn.py:5351 부근)를 따른다."""
    return os.environ.get("MUSTER_CLEAN_AUTO", "") not in (
        "0", "false", "no", "off")


def _clean_max_age_days() -> float:
    """`MUSTER_CLEAN_MAX_AGE_DAYS` — 기본 14일."""
    return float(os.environ.get("MUSTER_CLEAN_MAX_AGE_DAYS", "14"))


def _clean_max_bytes() -> int:
    """`MUSTER_CLEAN_MAX_BYTES` — 기본 5GiB."""
    return int(os.environ.get("MUSTER_CLEAN_MAX_BYTES", str(5 * 1024**3)))


def auto_sweep(wb: Path, max_age_days: float, max_bytes: int,
               now: float | None = None) -> dict[str, int]:
    """이슈 #1179: 스폰-타임 자동 정리. `roster_clean()` 과 같은 안전 판정
    (`_workspace_clean_state()`)만 지운다 — 살아있는 세션, 미커밋/미push
    작업은 절대 건드리지 않는다(#1124 보장 유지).

    두 단계 bound: 1) `max_age_days` 보다 오래된 안전 워크스페이스는
    무조건 지운다. 2) 그러고도 안전 워크스페이스 총합 크기가
    `max_bytes` 를 넘으면, 오래된 것부터 더 지워서 bound 아래로 낮춘다.
    나이만으로는 스폰이 늘면 디스크가 계속 자라고, 크기만으로는 방금
    생긴 워크스페이스도 지울 수 있다 — 두 축을 다 잡는다(각 축이 막는
    실패 모드가 다르다).

    `now`: 테스트가 `time.time()` 대신 고정 시각을 주입한다."""
    now = now if now is not None else time.time()
    live = _live_workspaces()
    log_outcomes = _ledger_log_outcomes()
    archive_dir = wb / ".archived-logs"
    max_age_sec = max_age_days * 86400

    candidates = []  # (mtime, size, path)
    if wb.is_dir():
        for w in sorted(wb.glob("*")):
            if not (w / ".git").is_dir():
                continue
            reason, _detail = _workspace_clean_state(w, live)
            if reason is not None:
                continue
            try:
                mtime = w.stat().st_mtime
            except OSError:
                continue
            candidates.append([mtime, None, w])

    removed = failed = 0

    def _reap(entry) -> None:
        nonlocal removed, failed
        try:
            _delete_workspace(entry[2], wb, log_outcomes, archive_dir)
            removed += 1
        except Exception as ex:
            print(f"[auto-sweep] 실패 (삭제 중 예외): {entry[2].name}  [{ex}]",
                  file=sys.stderr)
            failed += 1

    remaining = []
    for entry in candidates:
        if now - entry[0] > max_age_sec:
            _reap(entry)
        else:
            remaining.append(entry)

    if max_bytes > 0 and remaining:
        for entry in remaining:
            entry[1] = _dir_size_bytes(entry[2])
        remaining.sort(key=lambda e: e[0])  # 오래된 것부터
        total = sum(e[1] for e in remaining)
        i = 0
        while total > max_bytes and i < len(remaining):
            entry = remaining[i]
            total -= entry[1]
            _reap(entry)
            i += 1

    if removed or failed:
        print(f"[auto-sweep] 지움 {removed}" + (f", 실패 {failed}" if failed else ""),
              file=sys.stderr)
    return {"removed": removed, "failed": failed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", nargs="?", help="역할. 생략하면 상태만 보여준다")
    ap.add_argument("task", nargs="?", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("consult_question", nargs="?",
                    help="consult <역할> \"<질문>\": 세 번째 위치 인자로 질문을 받는다")
    ap.add_argument("panel_question", nargs="?",
                    help="panel <역할A> <역할B> \"<질문>\": 네 번째 위치 인자로 질문을 받는다")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    ap.add_argument("--no-contract", action="store_true",
                    help="대상 레포에 계약이 없어도 띄운다. 보드를 안 쓸 작업에만")
    ap.add_argument("--trust-repo-config", action="store_true",
                    help="대상 레포의 .claude/ 설정·훅을 신뢰한다. 읽어본 뒤에만")
    ap.add_argument("--issue", type=positive_int,
                    help="이 이슈 번호로 스폰한다: issue-<n>/<역할> 브랜치를 만들고 프롬프트에 명시")
    ap.add_argument("--model",
                    help="이 스폰 한 번만 쓸 모델 오버라이드: --model > "
                         "MUSTER_ROLE_MODEL > role_model.txt > \"sonnet\" (이슈#1736). "
                         "judge prefilter/validator 의 하드코딩 haiku 는 영향받지 않는다")
    ap.add_argument("--skills", default=None,
                    help="쉼표로 구분한 스킬 이름 목록을 skill-repository 체크아웃"
                         "(MUSTER_SKILL_REPO 또는 형제-클론)에서 마운트한다"
                         "(이슈 #1742). 생략하면 스폰 argv/env 는 이전과 동일")
    ap.add_argument("--merge", help="judge <역할> --merge <sha>: 판단할 머지의 커밋 sha")
    ap.add_argument("--unattended", action="store_true",
                    help="사람이 없는 실행. mint 는 안 되고, 휴먼 게이트는 선다")
    ap.add_argument("--limit", type=int, default=12,
                    help="drive: 한 번에 띄울 최대 횟수 (기본 12, 폭주 방지)")
    ap.add_argument("--login", help="init: approvers.md 에 넣을 GitHub 로그인 (기본: gh api user)")
    ap.add_argument("--stall-timeout", type=float, default=5.0,
                    help="분 단위. role task/watch 가 이벤트 없이 블록하는 최대 시간 (기본 5)")
    ap.add_argument("--role", dest="watch_role",
                    help="watch: 같은 이슈에 역할이 여럿 기록돼 있을 때 지정")
    ap.add_argument("--follow", action="store_true",
                    help="watch: 이벤트마다 재무장하지 않고 session-end 까지 "
                         "_await_bounded 를 반복 호출하며 스트리밍한다")
    ap.add_argument("--rearm", action="store_true",
                    help="watch: 죽은 워처를 non-blocking 으로 재무장하고 즉시 "
                         "리턴한다 — --follow 와 달리 호출자가 죽어도 워처는 "
                         "살아남는다 (이슈 #1133)")
    ap.add_argument("--self-heal", action="store_true",
                    help="watch --follow: auto-arm 워처 전용. stall/wall-clock "
                         "에서 리턴 대신 진행 상태를 리셋하고 루프를 계속 돌아 "
                         "session-end 까지 스스로 재무장한다 (이슈 #927). "
                         "대화형 호출에는 쓰지 않는다")
    ap.add_argument("--max-wait", type=float, default=None,
                    help="분 단위. watch --follow 반복 전체에 걸친 wall-clock "
                         "상한 — 활동(로그 증가)이 있어도 이 시간이 지나면 "
                         "리턴한다 (기본 없음=비활성, 이슈 #645)")
    ap.add_argument("--no-wait", action="store_true",
                    help="spawn --issue: fork 직후 _await_bounded 없이 즉시 "
                         "리턴한다 — 재개 명령(spawn.py watch)을 찍는다 (이슈 #645)")
    ap.add_argument("--despite-returned", action="store_true",
                    help="[DEPRECATED, 이슈 #1239] no-op — 게이트가 이제 "
                         "항상 non-blocking surfacing 이라 스폰을 거절하지 "
                         "않으므로 무시할 것이 없다. CLI 호환성을 위해 남아 "
                         "있을 뿐 (이슈 #680)")
    ap.add_argument("--single-phase", action="store_true",
                    help="스폰하는 세션에 CORE_BUILD_NOW=1 을 실어 phase-1 "
                         "제안 라운드를 건너뛰게 한다(contract v3 s19a 우회, "
                         "이슈 #1672/#1978). 스포너가 명시적으로 결정할 "
                         "때만 켠다 — 세션 스스로는 절대 켤 수 없다.")
    ap.add_argument("--max-turns", type=int, default=None,
                    help="spawn: session turn budget passed through as claude "
                         "--max-turns (issue #2100 item 4). Default: "
                         "MUSTER_SESSION_MAX_TURNS env or "
                         f"{DEFAULT_SESSION_MAX_TURNS}. 0 or negative means "
                         "unlimited and is refused at admission unless "
                         "--allow-unlimited-turns is also given")
    ap.add_argument("--allow-unlimited-turns", action="store_true",
                    help="spawn: explicit override letting --max-turns 0 "
                         "(unlimited) pass the budget-caps admission check "
                         "(issue #2100 item 4)")
    ap.add_argument("--all", action="store_true",
                    help="watch: 워크스페이스 인덱스 전체를 다중화해 스트리밍한다 "
                         "(오케스트레이터가 대화당 한 번 무장하는 집계 뷰, 이슈 #488)")
    ap.add_argument("--until-idle", action="store_true",
                    help="watch --all: 워치 중인 세션이 모두 session-end 를 "
                         "남기면(또는 인덱스가 비어 있으면) 영원히 블록하지 "
                         "않고 리턴한다 (--all 하고만 쓴다, 이슈 #559)")
    ap.add_argument("--auto-respawn", action="store_true",
                    help="watchdog: crashed 세션에 한해 최대 2회 자동 재스폰, "
                         "상한 도달 시 이슈 코멘트 (기본 off, 관찰-전용 유지)")
    ap.add_argument("--unreported", action="store_true",
                    help="reconcile: roster 대신 workspace 인덱스를 훑어, "
                         "session-end(normal) 인데 아직 [watch] 코멘트가 없는 "
                         "엔트리를 찍는다 (이슈 #534, 압축/재시작 뒤 복구용 단일 스윕)")
    ap.add_argument("--remediation-merged", action="store_true",
                    help="reconcile --issue N: docs/issue-N/decisions/remediation-*.md 중 "
                         "status: open 인 기록의 routed_to 역할 브랜치가 머지됐으면 "
                         "이슈에 코멘트를 남긴다 (이슈 #587 round 2, §12 event 4)")
    ap.add_argument("--post", action="store_true",
                    help="closure-sweep: 위반을 해당 이슈에 코멘트로도 남긴다 (기본은 stdout 만)")
    ap.add_argument("--json", action="store_true",
                    help="flows: 사람용 표 대신 flows-schema.md 계약대로 JSON 을 stdout 에 찍는다")
    a = ap.parse_args()

    if a.role == "init":
        # 보드로 선언한다(approvers.md). on-the-record 가 남의 레포에 쓰는 유일한 경우.
        return init_board(a.cwd, a.login)
    if a.role == "ps":
        return roster_ps()
    if a.role == "recut-if-absorbed":
        return recut_if_absorbed_cli(str(Path(a.cwd).resolve()))
    if a.role == "watchdog":
        # 이슈 #1219: `-C` (기본값 ".") 를 그대로 넘긴다 — 컨슈머 세션은
        # 타깃 프로젝트를, dev 세션(cwd == 이 체크아웃)은 이 체크아웃
        # 자신을 본다. 이전에는 이 호출이 `-C` 를 무시하고 전역 ROOT(=이
        # 체크아웃)만 스캔해, 컨슈머 세션이 on-the-record 자신의
        # 이슈/PR/다이제스트를 받는 원인이었다.
        # 이슈 #1274: 예약 센티널로만 진짜(파이썬 레벨) 크래시를 신호한다 —
        # roster_watchdog() 의 정상 반환값(anomaly count)과 절대 안 겹치게.
        # 이슈 #1456: 틱을 돌리기 전에 canonical-체크아웃 가드 -> 단일-인스턴스
        # 락 -> 시작 HEAD 기록 순으로 통과해야 한다; 틱을 돌린 뒤에는
        # 코드-신선도를 다시 확인해 구코드로 계속 도는 것을 막는다.
        ok, msg = watchdog_canonical_guard()
        if not ok:
            print(msg)
            return WATCHDOG_NONCANONICAL_SENTINEL
        ok, msg = watchdog_lock_acquire()
        if not ok:
            print(msg)
            return WATCHDOG_LOCKED_SENTINEL
        startup_head = watchdog_current_head()
        try:
            rc = roster_watchdog(auto_respawn=a.auto_respawn, all_scope=a.all,
                                  root=Path(a.cwd).resolve())
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return WATCHDOG_CRASH_SENTINEL
        if startup_head is not None:
            fresh, msg = watchdog_freshness_check(
                startup_head, state_path=WATCHDOG_FRESHNESS_STATE_PATH)
            if not fresh:
                if msg:
                    print(msg)
                return WATCHDOG_STALE_CODE_SENTINEL
        return rc
    if a.role == "poll-due":
        return 0 if poll_due(poll_state=POLL_STATE) else 1
    if a.role == "deadman-check":
        # Issue #2101 mechanism 4: standalone freshness check of the watch
        # layer's coverage-OK marker, callable from the UserPromptSubmit/Stop
        # poll hooks — deliberately independent of the watchdog process.
        # rc is the advisory count (0 fresh / 1 stale), never a block.
        return deadman_check()
    if a.role == "gc-monitor-alive":
        return monitor_alive_gc_cli(Path(a.cwd).resolve())
    if a.role == "reconcile":
        return roster_reconcile(a.issue, unreported=a.unreported,
                                 remediation_merged=a.remediation_merged,
                                 root=Path(a.cwd).resolve())
    if a.role == "flows":
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import flows
        return flows.flows(a.cwd, a.json, all_scope=a.all)
    if a.role == "roles-due":
        # board_condition 평가기 — 판단(judgment) 잔여만 (issue #896 step 2).
        # 표준 발동(test-authoring 등)은 이제 항상-켜짐 훅이 맡고, 여기는
        # 스폰 여부까지 판단이 필요한 나머지 역할만 surfaced-only 로 보고한다.
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import roles_due as _roles_due
        due = _roles_due.roles_due(Path(a.cwd).resolve())
        lines = _roles_due.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "needs-due":
        # need-detector 평가기 — 대상 프로젝트가 이 역할의 실제 산출물을
        # "필요로 하는지" 판정한다 (issue #1160 step 3 machinery).
        # roles-due 와 마찬가지로 advisory-only: 절대 자동 스폰하지 않는다.
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import need_detector as _need_detector
        due = _need_detector.needs_due(
            Path(a.cwd).resolve(), root=Path(__file__).parent.resolve())
        lines = _need_detector.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "closure-sweep":
        # 보드 전체를 훑어 이슈-PR 종결 불일치를 보고한다 — 명시적 단발 호출
        # (approve-scope 와 마찬가지로 watchdog 틱에 자동으로 안 물린다, 이슈 #135).
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import closure_sweep
        root = Path(a.cwd).resolve()
        issue_states, _ = closure_sweep.issue_state_index_all(root)
        violations, skips = closure_sweep.find_violations(root, issue_states=issue_states)
        if skips:
            print("종결 일관성 스윕: 확인 불가")
            print(f"{len(skips)}건 확인 못함: " +
                  ", ".join(s.get("subject", "?") for s in skips))
            if violations:
                print("(부분적으로 확인된 위반)")
                print(closure_sweep.format_report(violations))
            if a.post and violations:
                closure_sweep.post_sweep_comments(root, violations)
            return 2
        if not violations:
            print("종결 일관성 스윕: 위반 없음")
            return 0
        print("종결 일관성 스윕: 위반 발견")
        print(closure_sweep.format_report(violations))
        if a.post:
            closure_sweep.post_sweep_comments(root, violations)
        return 1
    if a.role == "consult":
        if not a.task or not a.consult_question:
            sys.exit('사용법: spawn.py consult <역할> "<질문>" [--issue <n>]')
        try:
            verdict = consult_cmd(a.task, a.consult_question, issue=a.issue, cwd=a.cwd,
                                  model=a.model)
        except Exception as e:
            sys.exit(f"consult 실패(트레이스는 남았다): {e}")
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
        return 0
    if a.role in ("ideate", "draft", "review"):
        if not a.task or not a.consult_question:
            sys.exit(f'사용법: spawn.py {a.role} <역할> "<{a.role} 요청>" [--issue <n>]')
        verb_fn = {"ideate": ideate_cmd, "draft": draft_cmd, "review": review_cmd}[a.role]
        try:
            result = verb_fn(a.task, a.consult_question, issue=a.issue, cwd=a.cwd)
        except Exception as e:
            sys.exit(f"{a.role} 실패(트레이스는 남았다): {e}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if a.role == "judge":
        if not a.task or not a.merge:
            sys.exit('사용법: spawn.py judge <역할> --merge <sha> [-C <repo>]')
        try:
            result = judge_cmd(a.task, a.merge, cwd=a.cwd)
        except Exception as e:
            sys.exit(f"judge 실패(트레이스는 남았다): {e}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    if a.role == "findings-due":
        # 자문(consult) 계열과 달리 advisory-only — 절대 자동으로 이슈를 파지
        # 않는다(이슈 #1202 requirement 4). roles-due/needs-due 와 같은
        # print-only 모양.
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import findings_due as _findings_due
        due = _findings_due.findings_due(Path(a.cwd).resolve())
        lines = _findings_due.format_report(due)
        for line in lines:
            print(line)
        return 0
    if a.role == "panel":
        if not a.task or not a.consult_question or not a.panel_question:
            sys.exit('사용법: spawn.py panel <역할A> <역할B> "<질문>" [--issue <n>]')
        if a.task == a.consult_question:
            sys.exit("panel 은 서로 다른 두 역할이 필요하다 — 같은 역할을 두 번 줬다")
        try:
            verdict = panel_cmd(a.task, a.consult_question, a.panel_question,
                                 issue=a.issue, cwd=a.cwd, model=a.model)
        except Exception as e:
            sys.exit(f"panel 실패(트레이스는 남았다): {e}")
        print(json.dumps(verdict, indent=2, ensure_ascii=False))
        return 0
    if a.role == "kill":
        if not a.task or a.issue is None:
            sys.exit("사용법: spawn.py kill <역할> --issue <n>")
        return roster_kill(a.issue, a.task)
    if a.role == "watch":
        if a.all:
            if a.issue is not None:
                sys.exit("사용법: spawn.py watch --all 은 --issue 와 함께 못 쓴다")
            return _watch_all(a.stall_timeout, until_idle=a.until_idle)
        if a.until_idle:
            sys.exit("사용법: spawn.py watch --until-idle 은 --all 과 함께만 쓴다")
        if a.issue is None:
            sys.exit("사용법: spawn.py watch --issue <n> [--role <역할>] "
                     "[--stall-timeout <분>], 또는 spawn.py watch --all")
        # 이슈 #554: `kill <역할> --issue N` 과 같은 위치 인자 문법을
        # `watch` 에도 허용한다 — `--role` 이 이미 있으면 그게 우선한다.
        watch_role = a.watch_role or a.task
        if a.rearm:
            return _rearm_watcher_detached(a.issue, watch_role, a.stall_timeout,
                                            repo=_repo_identity(a.cwd), cwd=a.cwd)
        return _watch(a.issue, watch_role, a.stall_timeout, follow=a.follow,
                      repo=_repo_identity(a.cwd), max_wait_min=a.max_wait,
                      self_heal=a.self_heal)
    if a.role == "clean":
        return roster_clean(_workspace_base(), a.issue)
    if a.role == "doctor":
        # 훅 발화 실측. 버전마다 한 번 — 룰북 집행의 전제조건이다.
        return doctor()
    if a.role == "approve":
        sys.exit("v3: 승인은 파일 발행이 아니라 GitHub 행위다 — 오케스트레이터가\n"
                 "  사용자와의 대화에서 gh pr review --approve / gh pr merge 로 중계한다.")
    if a.role == "approve-scope":
        if a.issue is None:
            sys.exit("사용법: spawn.py approve-scope --issue <n> [-C <레포>]")
        return approve_scope(a.cwd, a.issue)
    if a.role == "lint":
        # issue #2088: 스폰 전에 body-only 게이트(acceptance shape, requirement
        # linkage)만 미리 돌려본다 — 세션을 안 띄운다, 위반은 전부 찍는다.
        if a.issue is None:
            sys.exit("사용법: spawn.py lint --issue <n> [-C <레포>]")
        violations = lint_issue(a.cwd, a.issue)
        if violations:
            print(f"이슈 #{a.issue} lint: 위반 {len(violations)}건")
            for v in violations:
                print(f"  - {v}")
            return 1
        print(f"이슈 #{a.issue} lint: 위반 없음")
        return 0
    if a.role == "drive":
        # 보드가 지목하는 역할을 하나씩, 멈출 때까지.
        require_board(a.cwd, a.no_contract)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_doctor()
        ensure_target_remote(a.cwd, a.unattended)
        return drive(a.cwd, a.unattended, a.limit)
    if not a.role:
        print("\n".join(status(a.cwd)))
        print("\n역할:")
        for p in sorted((ROOT / "roles").glob("*.json")):
            try:
                meta = json.loads(p.read_text())
            except ValueError:
                meta = {}
            print(f"  {p.stem:12s} {meta.get('decides','')}  — {meta.get('use_when','')}")
        return 0
    if not a.task:
        sys.exit("맡길 일이 없다. 사용법: spawn.py <역할> \"<맡길 일>\" [-C <경로>]")

    # --dry-run 은 세션을 안 태운다. 계약 검사는 버려질 세션을 막으려는 것이므로
    # 아무것도 안 띄우는 호출까지 막을 이유가 없다.
    require_board(a.cwd, a.no_contract or a.dry_run)
    # 드라이런도 막는다 — 레포가 자기 훅을 들고 있으면 그건 세션을 띄우기
    # 전에 알아야 할 사실이지, 띄우고 나서 알 일이 아니다.
    require_no_repo_config(a.cwd, a.trust_repo_config)
    require_acceptance_gate(a.cwd, a.issue)
    require_requirement_linkage(a.cwd, a.issue)
    if a.dry_run:
        cwd_path = Path(a.cwd)
        if not cwd_path.is_dir():
            sys.exit(f"-C 가 디렉터리가 아니다: {a.cwd}")
        out = role_settings(a.role, a.cwd)
        # MUSTER_ROLE_MODEL / role_model.txt (이슈#93): spawn_cmd 는 이
        # dry-run 경로를 안 타므로(세션을 안 띄우니까) --model 부착 여부가
        # 여기 안 보이면 이슈#31 acceptance 커맨드(`--dry-run`)로는 이 기능을
        # 검증할 수 없다(실측:
        # docs/reports/2026-07-29-hunt-muster-role-model-build.md). resolved_role_model()
        # 로 spawn_cmd 와 동일한 env > config > built-in "sonnet" 경로를 태워,
        # 둘 다 비어있어도 built-in 값을 키에 넣는다.
        role_model = resolved_role_model(a.model)
        if role_model:
            out["model"] = role_model
        print(json.dumps(out, indent=2, ensure_ascii=False))
        if role_model:
            # 실제 스폰 시 spawn_cmd 가 argv 에 붙이는 것과 같은 두 토큰을
            # 여기서도 보여준다 — 이슈#31 acceptance("--dry-run 이 --model
            # sonnet 을 보여준다")가 겨냥하는 문구 그대로.
            print(f"--model {role_model}")
        return 0
    require_doctor()
    ensure_target_remote(a.cwd, a.unattended)
    return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue,
                      bounded=a.issue is not None,
                      stall_timeout_min=a.stall_timeout,
                      no_wait=a.no_wait,
                      despite_returned=a.despite_returned,
                      model=a.model, skills=a.skills,
                      single_phase=a.single_phase,
                      max_turns=a.max_turns,
                      allow_unlimited_turns=a.allow_unlimited_turns)


_GH_TOKEN_CACHE: str | None = None


_FETCHED_THIS_SPAWN: dict[str, float] = {}

# 이슈 #1507 — work_dir 별 부트스트랩 fetch 기록(origin/main sha + fetch
# 시각). 세션이 절대-부재 주장을 쓰기 전에 이 기록이 이미 있어야 한다.
_BOOTSTRAP_FETCH_RECORD: dict[str, dict] = {}


def bootstrap_fetch_and_record_sha(work_dir: str,
                                    label: str = "부트스트랩 fetch") -> dict:
    """이슈 #1507 — 세션의 첫 verification/absence-claim 단계보다 먼저
    `git fetch --prune`으로 origin 을 갱신하고 origin/main(또는 origin/HEAD
    가 가리키는 기본 브랜치) 의 sha 와 fetch 시각을 기록한다.

    `checkout_issue_branch()`가 부트스트랩 중 가장 먼저 이 함수를 부른다 —
    세션이 아직 아무 검증도 하지 않은 시점이다. fail-closed: fetch 가
    실패하면 `_fetch_or_halt`와 같은 house style 로 즉시 중단한다.

    반환값 `{"sha": <40자 hex>, "fetched_at": <ISO8601 UTC>}` 은
    `_BOOTSTRAP_FETCH_RECORD[work_dir]`에도 저장되어 이후
    `get_bootstrap_fetch_record()`로 조회할 수 있다 — 절대-부재 주장을
    쓰는 시점에 "verified against origin/main at <sha>, fetched
    <timestamp>" 문구를 채우는 근거가 된다(gates/repo_scope.py 확장)."""
    r = _run_net(["git", "-C", work_dir, "fetch", "--prune", "-q", "origin"],
                label, env=_git_env())
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(f"{label}: fetch 실패 — {r.stderr.strip()[:200]}")
    base = _base(work_dir)
    sha_r = subprocess.run(["git", "-C", work_dir, "rev-parse", base],
                           capture_output=True, text=True)
    sha = sha_r.stdout.strip() if sha_r.returncode == 0 else ""
    record = {"sha": sha, "fetched_at": datetime.now(timezone.utc).isoformat()}
    _BOOTSTRAP_FETCH_RECORD[str(Path(work_dir).resolve())] = record
    return record


def get_bootstrap_fetch_record(work_dir: str) -> dict | None:
    """이슈 #1507 — `bootstrap_fetch_and_record_sha()`가 이 work_dir 에
    이미 남긴 기록을 조회한다. 없으면 None(아직 부트스트랩 fetch 전)."""
    return _BOOTSTRAP_FETCH_RECORD.get(str(Path(work_dir).resolve()))


def _fetch_or_halt(work_dir: str, label: str, after=None) -> None:
    """fail-closed fetch. returncode 만 보면 놓치는 실패가 있다 — 실측:
    core issue-90 관찰 세션에서 `git fetch origin`이 stderr 에 "failed to
    store: 100001"을 남기고도 exit 0으로 끝났다. returncode != 0 이거나
    stderr 에 "failed to store"가 있으면 낡은 코드로 조용히 진행하는 대신
    중단한다(ensure_pushed 의 2380/2420 라인과 같은 house style).

    `after`(있으면)는 halt 여부 판정 **전에** 실행한다 — 신규 clone 직후의
    `remote set-head origin -a` 처럼, fetch 가 fail-closed 로 halt 하더라도
    반드시 시도돼야 하는 부수 효과가 있어서다. 순서를 반대로 하면(halt
    먼저) fetch 가 실패할 때마다 그 부수 효과가 영영 안 돌 수 있다 — 신규
    clone 경로 한정으로, `.git`은 이미 생겨 재사용 분기로 넘어가 버려 다시
    시도할 기회 자체가 없다(hunt 발견, composition-regression stance).

    같은 프로세스 안에서 같은 work_dir 을 이미 fetch 했으면 다시 네트워크로
    나가지 않는다(이슈 #285 P3 — `issue_workspace()` 다음의
    `checkout_issue_branch()` 가 수 초 뒤 같은 경로를 또 fetch 하던 것).
    최초 fetch 가 실패하면 이 함수가 바로 sys.exit 하므로 성공한 fetch만
    "fresh" 로 기록된다 — 두 번째 호출자가 halt 를 건너뛰는 일은 없다."""
    key = str(Path(work_dir).resolve())
    if key in _FETCHED_THIS_SPAWN:
        if after is not None:
            after()
        return
    r = _run_net(["git", "-C", work_dir, "fetch", "-q", "origin"], label,
                env=_git_env())
    if after is not None:
        after()
    if r.returncode != 0 or "failed to store" in r.stderr:
        sys.exit(f"{label}: fetch 실패 — {r.stderr.strip()[:200]}")
    _FETCHED_THIS_SPAWN[key] = time.monotonic()


def _write_role_sidecar(work: str, issue: int, role: str) -> None:
    """이슈 #1814: 워크스페이스 루트에 `.on-the-record/role.json` 을 남긴다 —
    네 개의 브랜치-정규식 사이트 중 셸 훅 세 곳(approval-gate.sh,
    pr-preflight.sh, contract-guard.sh)이 이미 로컬 `git rev-parse` 로
    풀던 워크스페이스에서 role 을 직접 읽게 하는 명시적 캐리어. 실패해도
    fail-open — 사이트들은 이 파일이 없으면 기존 브랜치-정규식 파싱으로
    그대로 떨어진다.

    이슈 #1891: 이 사이드카는 세션마다 바뀌는 워크스페이스-로컬 상태라
    git 이 절대 스테이징하면 안 된다 — issue #1882/PR #1890 에서 실제로
    커밋됐다가 머지 전에 걸러진 근접 사고. 스폰 시점에 워크스페이스의
    `.git/info/exclude` 에 추가한다(레포 `.gitignore` 는 건드리지 않는다).
    fresh-clone 경로의 자격증명 유출 방지 exclude 블록(issue_workspace()
    쪽)과 별개의 관심사라 여기서 직접 쓴다 — 호출부 3곳 모두를 한 곳에서
    커버한다."""
    d = Path(work) / ".on-the-record"
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / "role.json").write_text(
            json.dumps({"role": role, "issue": issue}) + "\n", encoding="utf-8")
        ex = Path(work) / ".git" / "info" / "exclude"
        ex.parent.mkdir(parents=True, exist_ok=True)
        existing = ex.read_text() if ex.exists() else ""
        if ".on-the-record/role.json" not in existing:
            with ex.open("a") as fh:
                fh.write(".on-the-record/role.json\n")
    except OSError as e:
        print(f"경고: {work} 에 role.json 사이드카를 쓰지 못했다 ({e})",
              file=sys.stderr)


def issue_workspace(cwd: str, issue: int, role: str) -> str:
    """이슈 스폰마다 on-the-record 소유의 격리 클론을 만든다.

    산출물이 PR 로만 돌아오는 모델에서 역할 세션이 사용자의 체크아웃을
    공유할 이유가 없다 — 공유하면 동시 스폰 둘이 같은 .git/index 와 현재
    브랜치를 두고 경합한다(실측: issue-45 와 issue-59 coding 세션이 한
    트리에서 충돌 직전까지 갔다). 로컬에서 클론하고 origin 을 실제 원격으로
    되돌려 push/gh 가 GitHub 로 가게 한다. 재스폰이면 기존 작업 디렉토리를
    fetch 로 재사용한다 — 진행 중이던 브랜치 작업을 버리지 않는다.
    """
    src = Path(cwd).resolve()
    r = subprocess.run(["git", "-C", str(src), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    origin = r.stdout.strip()
    # 샌드박스는 HTTP 프록시만 뚫려 있다 — ssh(22번)는 나갈 수 없으므로
    # 작업 클론의 origin 은 기본으로 https 로 정규화한다. 회사 정책이 ssh
    # 원격만 허용하면 MUSTER_KEEP_SSH=1 로 끈다 — 그 경우 세션 안 push 는
    # 실패하지만, 세션 뒤 on-the-record 가 호스트 환경(사용자의 ssh 키)에서
    # push/PR 를 대신한다(아래 ensure_pushed).
    if os.environ.get("MUSTER_KEEP_SSH", "") not in ("", "0", "false", "no", "off"):
        pass
    else:
        m = re.match(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$", origin)
        if m:
            origin = "https://github.com/%s.git" % m.group(1)
    if not origin:
        sys.exit(f"대상 레포에 origin 원격이 없다: {src} — 이슈/PR 모델은 "
                 f"GitHub 원격이 전제다 (계약 v3 s10)")
    # 보호 경로 밖이어야 한다: on-the-record 가 ~/.claude/plugins/ 아래 설치되면
    # ROOT/runs/work 도 그 아래가 되는데, 거긴 Claude Code 의 전역 sensitive
    # 경로라 역할 세션의 Write 가 전부 거부된다(실측: phase 2 가 코드 한 줄
    # 못 쓰고 $2.68 을 태웠다). 기본은 ~/.tokenmaxxxer/work, 오버라이드는
    # MUSTER_WORK_DIR.
    work_base = _workspace_base()
    # 이름은 origin 의 레포명에서 뽑는다 — 디렉토리 이름(slug)을 쓰면
    # 워크스페이스를 -C 로 다시 넘겼을 때 이름이 이중으로 붙는다(실측:
    # ...-issue-45-coding-issue-45-coding). origin 은 위에서 이미 읽었다.
    repo_name = re.sub(r"\.git$", "", origin.rstrip("/").rsplit("/", 1)[-1]) or slug(cwd)
    work = work_base / f"{repo_name}-issue-{issue}-{role}"
    # cwd 가 이미 이 (이슈,역할)의 워크스페이스면 그대로 쓴다 — 중첩 금지.
    if src == work.resolve():
        _fetch_or_halt(str(src), "재사용 워크스페이스")
        _write_role_sidecar(str(src), issue, role)
        return str(src)
    if (work / ".git").exists():
        # 이 경로가 우리가 만든 워크스페이스가 아니라 우연히 같은 이름으로
        # 미리 놓인 남의 레포일 수 있다(#288 N5) — origin 이 다르면 그건
        # 네트워크 문제가 아니라 신원 불일치이므로 fetch 를 시도하기 전에
        # 여기서 끊는다.
        rw = subprocess.run(["git", "-C", str(work), "remote", "get-url", "origin"],
                            capture_output=True, text=True)
        work_origin = rw.stdout.strip()
        def _norm(u):
            # ssh/https 형태 차이는 신원이 아니다 — MUSTER_KEEP_SSH 가 두
            # 스폰 사이에 토글되면 `origin`(위에서 이미 그 시점의 env로
            # 정규화됨)과 예전에 클론된 work_origin 의 스킴이 다를 수
            # 있으므로, 비교 직전에 둘 다 무조건 https 형태로 다시 맞춘다
            # (실측: warrant hunt, MUSTER_KEEP_SSH 토글이 진짜 재사용을
            # "다른 레포"로 오판).
            u = re.sub(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$",
                       r"https://github.com/\1", u)
            return re.sub(r"\.git$", "", u.rstrip("/"))
        if _norm(work_origin) != _norm(origin):
            sys.exit(f"작업 경로에 다른 레포가 있다 (origin 불일치): {work} "
                     f"— 기대: {origin}, 실제: {work_origin or '(없음)'}")
        _fetch_or_halt(str(work), "재사용 워크스페이스")
        _write_role_sidecar(str(work), issue, role)
        return str(work)
    work.parent.mkdir(parents=True, exist_ok=True)
    c = _run_net(["git", "clone", "-q", str(src), str(work)], "작업 클론",
                timeout=CLONE_TIMEOUT)
    if c.returncode != 0:
        sys.exit(f"작업 클론을 만들지 못했다: {c.stderr.strip()[:200]}")
    subprocess.run(["git", "-C", str(work), "remote", "set-url", "origin",
                    origin], capture_output=True, text=True)
    # https push 자격증명: 디스크에 토큰을 남기지 않고 env(GH_TOKEN)를 읽는
    # credential helper 를 작업 클론에만 심는다.
    ex = work / ".git" / "info" / "exclude"
    lines = [".muster-cache/"]
    # 이슈 #289 H1: Claude Code 샌드박스는 홈 디렉터리의 이 dotfile 들을
    # 워크스페이스 루트에 오버레이한다 — 밖에서 보면 없고, 세션 안에서만
    # `git status`에 untracked 로 잡힌다. `git add -A` 한 번이면
    # .mcp.json/.gitconfig 같은 자격증명성 파일이 공개 레포에 커밋된다.
    # .muster-cache/ 와 같은 방식(워크스페이스 로컬 exclude)으로 막는다.
    lines += [".bashrc", ".bash_profile", ".profile", ".zshrc",
              ".zprofile", ".gitconfig", ".gitmodules", ".mcp.json",
              ".claude/", ".idea", ".vscode", ".ripgreprc"]
    skipped = lines
    try:
        ex.parent.mkdir(parents=True, exist_ok=True)
        existing = ex.read_text() if ex.exists() else ""
        missing = [ln for ln in lines if ln.rstrip("/") not in existing]
        skipped = missing
        if missing:
            with ex.open("a") as fh:
                for ln in missing:
                    fh.write(ln + "\n")
    except OSError as e:
        print(f"경고: 워크스페이스 {work} 의 자격증명 유출 방지 exclude 항목을 "
              f"쓰지 못했다 ({e}) — 빠진 항목: {', '.join(skipped)}",
              file=sys.stderr)
    subprocess.run(["git", "-C", str(work), "config", "credential.helper",
                    "!f() { echo username=x-access-token; echo password=$GH_TOKEN; }; f"],
                   capture_output=True, text=True)
    # clone 은 clone 시점 src 의 HEAD 를 origin/HEAD 로 물려받는다 — 방금
    # origin 을 실제 원격으로 바꿨으니 origin/HEAD 도 그 원격 기준으로
    # 다시 계산해야 `_base()`가 오염된 기본 브랜치를 읽지 않는다. `after=`
    # 로 넘겨서 fetch 가 fail-closed 로 halt 하더라도 먼저 시도되게 한다.
    _fetch_or_halt(str(work), "신규 워크스페이스", after=lambda: subprocess.run(
        ["git", "-C", str(work), "remote", "set-head", "origin", "-a"],
        capture_output=True, text=True))
    _write_role_sidecar(str(work), issue, role)
    return str(work)


def _recut_absorbed_branch(cwd: str, br: str):
    """`br` 이 이미 로컬에 체크아웃돼 있다고 가정하고, base 에 흡수됐는지
    검사해 필요하면 재컷한다 (untracked 작업은 stash 로 보존). 스폰 시점
    `checkout_issue_branch()` 와 세션 자신의 mid-run 재검사
    (`recut_if_absorbed_cli`, 이슈 #784) 양쪽에서 재사용하는 공유 헬퍼 —
    로직은 #732 가 이미 검증한 것 그대로, 호출 시점만 늘어난다.

    반환값은 최종 `git checkout`/`checkout -B` 의 CompletedProcess."""
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    base = _base(cwd)
    ahead = git("rev-list", "--count", f"{base}..{br}")
    remote_ahead = git("rev-list", "--count", f"{base}..origin/{br}")
    local_zero = ahead.returncode == 0 and ahead.stdout.strip() == "0"
    # 로컬은 0-ahead 라도 origin/br 이 base 보다 앞서 있으면, 이
    # 워크스페이스의 로컬 ref 가 그저 stale 한 것뿐이지 브랜치 자체가
    # base 에 흡수된 게 아니다 — 그 상태에서 base 로 재설정하면 다른
    # 워크스페이스가 이미 push 해 둔 커밋을 조용히 버린다 (이슈 #719).
    # remote_ahead 조회가 실패하면(원격 브랜치 없음 등) 로컬 판단만으로
    # 진행 — 오늘과 동일한 fail-open.
    remote_stale_only = (
        local_zero and remote_ahead.returncode == 0
        and remote_ahead.stdout.strip() != "0"
    )
    if remote_stale_only:
        print(f"[spawn] {br} 는 로컬만 {base} 에 흡수된 것처럼 보인다 — "
              f"origin/{br} 이 앞서 있어 재컷 대신 origin 을 따라간다.",
              file=sys.stderr)
        return git("checkout", "-B", br, f"origin/{br}")
    if local_zero:
        print(f"[spawn] {br} 는 {base} 에 완전히 흡수돼 커밋이 없다 — "
              f"로컬 브랜치를 지우고 새로 판다.", file=sys.stderr)
        # 흡수된 브랜치는 base 대비 영원히 0-ahead 라 재컷 없이는
        # 이 워크스페이스가 다시 PR 을 열 수 없다 (issue-732). 그런데
        # 워크스페이스에 untracked 파일만 있으면(커밋된 고유 작업은
        # 없음) `checkout -B` 가 그 파일들과 base 트리 사이의 경로
        # 충돌로 실패할 수 있어 조용히 no-op 재컷으로 빠진다. 재컷
        # 전에 untracked 파일을 stash 로 치워 뒀다가 재컷 뒤 새
        # 브랜치 위에 다시 풀어준다 — 절대 조용히 버리지 않는다.
        stash_marker = f"checkout_issue_branch-preserve-{br}"
        # 이전 실행이 push 와 pop 사이에서 중단됐다면 stash 가
        # working tree 에는 안 보이는 채로 남아있을 수 있다 (`git
        # status --porcelain` 은 stash 를 보지 않는다) — 그 상태로
        # clean 의 보존 가드를 통과하면 워크스페이스 전체가 지워지며
        # 안에 숨은 작업까지 조용히 사라진다. 재컷 전에 먼저 회수한다.
        leftover = git("stash", "list", "--grep", stash_marker)
        if leftover.returncode == 0 and leftover.stdout.strip():
            pop_r = git("stash", "pop", "-q")
            if pop_r.returncode != 0:
                print(f"[spawn] {br} 의 이전 실행이 남긴 stash 를 "
                      f"복구하지 못했다 — 수동 확인 필요: "
                      f"git -C {cwd} stash list", file=sys.stderr)
        untracked = git("ls-files", "--others", "--exclude-standard")
        has_untracked = (
            untracked.returncode == 0 and untracked.stdout.strip() != ""
        )
        if has_untracked:
            stash_r = git("stash", "push", "-u", "-q", "-m", stash_marker)
            has_untracked = stash_r.returncode == 0
        # -B 는 br 이 현재 체크아웃된 브랜치여도(재사용 워크스페이스가
        # 이미 그 위에 있는 경우) 지우지 않고 그대로 재설정한다 —
        # `branch -D` 는 체크아웃된 브랜치는 못 지운다.
        r = git("checkout", "-B", br, base)
        if r.returncode != 0:   # base 없음(원격 없음 등) — 현 HEAD 에서라도 재설정
            r = git("checkout", "-B", br)
        if has_untracked:
            pop_r = git("stash", "pop", "-q")
            if pop_r.returncode != 0:
                print(f"[spawn] {br} 재컷은 됐지만 보존해 둔 untracked "
                      f"작업을 자동으로 못 풀었다(충돌) — 수동 확인 "
                      f"필요: git -C {cwd} stash list / "
                      f"git -C {cwd} stash show -p", file=sys.stderr)
        return r
    return git("checkout", br)


def recut_if_absorbed_cli(cwd: str) -> int:
    """`spawn.py recut-if-absorbed -C <cwd>` — mid-run 세션이 자기 자신의
    브랜치를 재검사한다 (이슈 #784). 스폰 이후 이미 살아있는 세션은
    `checkout_issue_branch()`를 다시 부르지 않으므로, 그 세션이 떠 있는 동안
    orchestrator 가 phase-1 PR 을 `--delete-branch`로 머지하면 로컬 브랜치가
    base 에 흡수된 채로 조용히 남는다 — 다음 `git commit`/`gh pr create` 가
    "No commits between main and issue-<n>/<role>"로 실패하기 직전까지
    아무도 모른다. `absorbed-branch-recut-guard.sh`(PreToolUse/Bash)가 그
    커맨드들 직전에 이 함수를 호출한다.

    roster/cross-process 조회 없이 세션 자신의 현재 `HEAD` 에서 브랜치
    이름을 얻는다 — `issue-<n>/<role>` 모양이 아니면(분리 HEAD, 무관한
    브랜치 등) 아무 것도 안 하고 0 을 반환한다(오늘과 동일하게 fail-open).
    """
    br_r = subprocess.run(["git", "-C", cwd, "symbolic-ref", "--short", "-q", "HEAD"],
                          capture_output=True, text=True)
    br = br_r.stdout.strip()
    if br_r.returncode != 0 or not re.fullmatch(r"issue-\d+/[A-Za-z0-9_-]+", br):
        return 0
    # 흡수 여부 판단(local_zero/remote_ahead)이 최신 원격 상태를 봐야 하니
    # 이 브랜치와 base 만 갱신한다 — 실패해도(네트워크 등) 로컬 판단만으로
    # 진행하는 기존 fail-open 을 그대로 따른다.
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin", br],
                   capture_output=True, text=True)
    base = _base(cwd)
    subprocess.run(["git", "-C", cwd, "fetch", "-q", "origin",
                    base.removeprefix("origin/")],
                   capture_output=True, text=True)
    r = _recut_absorbed_branch(cwd, br)
    if r.returncode != 0:
        print(f"[recut-if-absorbed] {br} 재검사 실패: {r.stderr.strip()[:200]}",
              file=sys.stderr)
        return 1
    return 0


def checkout_issue_branch(cwd: str, issue: int, role: str) -> str:
    """대상 레포에서 issue-<n>/<역할> 브랜치를 만든다(있으면 갈아탄다).

    core 의 board-gate R4 가 보드 쓰기를 이 브랜치에서만 허용하므로, 스폰
    전에 서 있어야 세션이 첫 쓰기부터 막히지 않는다. base 는 원격 기본
    브랜치 — 역할 산출물은 main 에서 갈라져 PR 로만 돌아간다 (계약 v3 s10).
    """
    br = f"issue-{issue}/{role}"
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    # 이슈 #1507 — 세션의 첫 verification/absence-claim 단계보다 먼저
    # 이 fetch --prune 이 origin/main sha 를 기록해야 한다.
    bootstrap_fetch_and_record_sha(cwd, "브랜치 체크아웃")
    _fetch_or_halt(cwd, "브랜치 체크아웃")
    if git("rev-parse", "--verify", "-q", br).returncode == 0:
        # 재사용 워크스페이스의 로컬 브랜치가 base 에 완전히 흡수된 채로
        # 남아있을 수 있다 (머지 후 --delete-branch 는 원격만 지운다, 로컬
        # ref 는 그대로 살아남는다 — 실측: issue-441, issue-428 survey 의
        # issue-999 픽스처). 그 상태로 그냥 checkout 하면 이후 커밋이 없는
        # 한 origin 대비 0-ahead 브랜치로 PR 을 열게 되어 "No commits
        # between main and issue-<n>/<role>" 로 조용히 실패한다. base 대비
        # 커밋이 하나도 없으면 (완전 흡수) 로컬 ref 를 지우고 base 에서
        # 새로 판다 — 진행 중 작업(유니크 커밋 있음)은 오늘과 동일하게
        # 그대로 재사용한다.
        r = _recut_absorbed_branch(cwd, br)
    elif git("rev-parse", "--verify", "-q", f"origin/{br}").returncode == 0:
        # rev-parse --verify -q br 는 로컬 ref 만 본다 — 워크스페이스가 새로
        # 클론된 직후라면 origin 에는 이미 있는 브랜치도 로컬엔 없어, 여기서
        # base 로 새로 파면 origin 의 기존 이력을 버리고 영구 분기한다
        # (실측: issue-235 phase 2). origin 전용이면 그걸 트래킹해 만든다.
        r = git("checkout", "-b", br, f"origin/{br}")
    else:
        base = _base(cwd)
        r = git("checkout", "-b", br, base)
        if r.returncode != 0:      # base 없음(원격 없음 등) — 현 HEAD 에서라도 만든다
            r = git("checkout", "-b", br)
    if r.returncode != 0:
        sys.exit(f"브랜치 {br} 로 못 갈아탔다: {r.stderr.strip()[:200]}")
    return br


def _session_log_path(cwd: str) -> Path:
    """이슈-스코프 세션 하나의 라이브 로그 경로 — 타임스탬프+PID 접미사로
    세대마다 고유하게 만든다 (이슈 #192). 같은 워크스페이스로 재스폰해도
    이전 세대의 로그(`<work>.session.<ts>.<pid>.log`)를 truncate-open 으로
    덮어쓰지 않는다. `ts` 는 `time.strftime` 이라 사전순 정렬이 생성 순서와
    일치한다."""
    ts = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    return Path(str(cwd) + f".session.{ts}.{os.getpid()}.log")


_ACCEPTANCE_CHECK_LINE = re.compile(r"^\s*-\s*check\s*:\s*(.+)$", re.MULTILINE)

_STORYBOARD_RE = re.compile(r"storyboard|스토리보드", re.IGNORECASE)


def _artifact_smoke_task_lines(body: str | None) -> str:
    """이슈 #2073: 스폰 과제 뒤에 붙는 최대 두 줄의 조건부 코-인젝션.

    (a) 본문이 `runtime-artifacts:` 를 선언했거나(또는 선언은 없지만
        생성물/브라우저 어휘 자문 스코어러가 울리면) artifact-smoke
        트리거 한 줄 — 선언된 경로를 그대로 이름한다.
    (b) 이슈가 design-bearing 이면서 선언된 design-artifacts 중 하나가
        스토리보드면 live-screen 검증 한 줄.

    어느 조건도 안 걸리면 빈 문자열을 돌려준다 — 오늘의 과제 텍스트와
    바이트 단위로 같아야 한다. 새 네트워크 호출은 하지 않는다(본문은
    이미 받아온 것). gates 모듈을 못 불러오면 조용히 빈 문자열이다.
    """
    if not body:
        return ""
    try:
        sys.path.insert(0, str((ROOT / "gates").resolve()))
        import artifact_smoke_rule as _asr
        import design_artifacts_gate as _dag
        import design_bearing_classifier as _dbc
    except Exception:
        return ""

    out = ""
    try:
        declared = _asr.parse_declaration(body)
    except Exception:
        declared = None
    if declared:
        out += (
            "\n\nARTIFACT-SMOKE(이슈 #2073): 이 이슈는 런타임 산출물을 "
            f"선언했다 — {', '.join(declared)}. 이 산출물 자체를 파싱하거나 "
            "실행하는 검사가 최소 하나 있어야 한다(소스 유닛 테스트도, "
            "재생성 diff 도 그 자리를 대신하지 못한다). 허용 동사와 계약은 "
            "docs/specs/artifact-smoke-contract.md 에 있다.\n")
    elif declared is None:
        try:
            advisory = _asr.advisory_line(0, body)
        except Exception:
            advisory = None
        if advisory:
            out += (
                "\n\nARTIFACT-SMOKE(이슈 #2073): 이 이슈 본문이 생성물/"
                "브라우저 산출물 어휘를 담고 있는데 `runtime-artifacts:` "
                "선언이 없다 — 배송되는 산출물이 있으면 선언하고, 그 산출물을 "
                "실제로 파싱/실행하는 검사를 `## Acceptance` 에 하나 둬라"
                "(docs/specs/artifact-smoke-contract.md).\n")

    try:
        verdict = _dbc.check_issue_body(0, body)
        design_bearing = bool(verdict and verdict.get("design_bearing"))
        design_artifacts = _dag.parse_declaration(body) or []
    except Exception:
        design_bearing, design_artifacts = False, []
    storyboards = [p for p in design_artifacts if _STORYBOARD_RE.search(p)]
    if design_bearing and storyboards:
        out += (
            "\n\nVISUAL-VERIFICATION(이슈 #2073): 이 이슈는 design-bearing "
            f"이고 스토리보드({', '.join(storyboards)})를 선언했다 — 레코드에 "
            "`screen-verified:` 줄을 남겨라: docs/issue-<n>/_assets/ 아래의 "
            "실화면 스크린샷 경로와, 그 스토리보드에 비춘 한 줄 판정. 판정 "
            "내용은 네 몫이다(게이트는 줄과 파일의 존재만 본다).\n")
    return out


def _goal_pin_block(title: str | None, body: str | None) -> str:
    """이슈 #1652 (northpole req#6): 제목 + '## Acceptance' 의 'check:'
    불릿을 스폰 프롬프트에 그대로(verbatim) 박아, 스폰된 역할 세션이
    첫 턴부터 원본 목표를 본다 — 코멘트 히스토리 등 오염된 문맥은 절대
    섞지 않는다. Acceptance 절이 없거나 check: 불릿이 하나도 없으면
    빈 문자열을 돌려준다(오늘의 프롬프트와 바이트 단위로 동일해야
    한다 — 빈 헤더를 주입하지 않는다).
    """
    title = (title or "").strip()
    body = body or ""
    sys.path.insert(0, str((ROOT / "gates").resolve()))
    import acceptance_gate as _acceptance_gate
    section = _acceptance_gate._acceptance_section(body)
    if section is None:
        return ""
    checks = [c.strip() for c in _ACCEPTANCE_CHECK_LINE.findall(section)]
    checks = [c for c in checks if c]
    if not checks:
        return ""
    lines = []
    if title:
        lines.append(f"이슈 제목(원본 목표): {title}")
    lines.append("Acceptance 기준(원본, verbatim):")
    for c in checks:
        lines.append(f"- check: {c}")
    return "\n".join(lines) + "\n"


# 이슈 #1978: directive.sh(tokenmaxxxer-core, contract v3 s19a)가 매
# 세션에 SessionStart 로 이미 내보내는 "Build-now bypass" 불릿을 그대로
# 미러링한다(제안서 Rationale: 새 문구를 지어내면 두 서술이 계약 개정마다
# 따로 드리프트한다) — 2인칭 "your issue" 프레이밍만 스폰-시점 프리픽스로
# 조정했을 뿐, 문장 자체는 바꾸지 않는다.
_SINGLE_PHASE_CONTRACT_LINE = (
    "- Build-now bypass (contract v3 s19a): when the task that spawned this "
    "session explicitly authorizes delivery-only — its environment carries "
    "CORE_BUILD_NOW=1, set by the spawner, never by you — skip the proposal "
    "round and deliver directly: build on issue-<n>/{role}, commit code and "
    "your record, and open one PR carrying the work. Without "
    "CORE_BUILD_NOW=1 the default two-phase flow is unchanged; a session "
    "cannot grant itself this bypass by setting the variable on its own.\n"
)

_SKILL_USE_SENTENCE_RE = re.compile(r"(Use\b[^.]*\.)", re.S)


def _skill_trigger_line(skill_dir: Path) -> str | None:
    """`skill_dir/SKILL.md` 프론트매터의 `description:` 필드에서 "Use ..."로
    시작하는 트리거 문장을 뽑는다. 파일/프론트매터/description/트리거 문장
    중 무엇이든 없으면 None — 예외를 던지지 않는다(호출부가 이름만이라도
    싣는 empty-state 처리를 하도록).

    폴딩 블록 스칼라(`description: >-`)를 포함해 여러 줄 description 을
    다루려면 전체 YAML 파서가 필요하지만, 이 함수가 필요한 건 딱 한
    문장뿐이라(제안서 Rationale) 프론트매터 블록만 떼어내 정규식으로
    훑는다."""
    md = skill_dir / "SKILL.md"
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        return None
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not fm:
        return None
    dm = re.search(r"(?m)^description:[ \t]*(.*(?:\n(?:[ \t]+.*)?)*)", fm.group(1))
    if not dm:
        return None
    desc = dm.group(1).strip()
    desc = desc.lstrip(">|-+").strip()
    desc = desc.strip("\"'")
    desc = re.sub(r"\s+", " ", desc)
    um = _SKILL_USE_SENTENCE_RE.search(desc)
    return um.group(1).strip() if um else None


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset({"a", "the", "use", "when", "or", "and", "is", "an"})
# 이슈 #2040: raw-overlap 시절의 고정 임계값(_CROSS_FAMILY_MIN_OVERLAP=2)은
# BM25 점수 스케일로 옮겨오지 않는다 — score > 0 (질의-문서 토큰이 하나라도
# 겹치면 IDF 가중치가 붙어 양수) 를 바닥으로 쓴다. 재현: 16쌍 리플레이에서
# conformance-review-severity-classification 이 16/16 -> 7/16 로, model-routing
# 은 5/16 -> 5/16 로 남았다(docs/issue-2040/reports/implementation/survey.md
# BM25 spike, floor=score>0 그대로 재사용) — 그 잔여 오탐(모두 model-routing
# 류의 "의도적으로 광범위한" 트리거)을 걷어내는 건 임계값 조정이 아니라
# consult-judge 단계의 몫이다(제안서 Rationale).
_BM25_K1 = 1.5
_BM25_B = 0.75
_CROSS_FAMILY_CONSULT_TOPN = 8  # 이슈 본문: consult 에 넘기는 BM25 상위 후보 수


def _tokenize(text: str) -> set[str]:
    """소문자화 + 비영숫자 분리 + 작은 불용어 목록 제거. "Use when" 처럼
    트리거 문장이면 어디에나 있는 일반 단어가 그 자체로 매치를 만들지
    않게 한다(제안서 What will be done)."""
    return {t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS}


def _cross_family_candidate_corpus(role: str, repo_root: Path | None,
                                    home: Path | None = None,
                                    target_repo_root: Path | None = None
                                    ) -> list[tuple[str, Path, str]]:
    """이슈 #2055: `_bm25_cross_family_scores` 의 후보 코퍼스를 skill-repository
    단일 소스에서 네 소스(skill-repository, 설치된 플러그인, `~/.claude/skills`,
    타깃 저장소 `.claude/skills`)로 넓힌다 — `resolved_skill_sources()`(이슈
    #1774)와 같은 해석 규칙을 재사용한다: 이름 하나가 소스 두 개 이상에
    걸리면(같은 tier 안의 플러그인-대-플러그인 충돌 포함) fail-closed, 잡힌
    소스를 전부 이름 붙여 보고한다. `hooks/` 서브디렉터리를 든 후보는
    코퍼스에서 조용히 제외된다(스킬 마운트는 가이던스 전용 원칙 — 이건
    사용자가 이름을 지목한 `--skills` 가 아니라 자동 탐색이라 fail-closed
    가 아니라 그냥 후보에서 빠진다).

    반환은 (name, dir, source) 튜플 목록 — source 는 `_describe_skill_match()`
    가 아는 값(`"skill-repo"|"plugin"|"local-user"|"local-repo"`)과 같은
    어휘를 쓴다. family 안 스킬(`_ROLE_SKILLS[role]`)은 호출자가 이미
    걸러내던 대로 여기서도 걸러 반환에서 뺀다.

    `home`/`target_repo_root` 를 생략하면(`None`) 해당 tier 는 아예 안
    읽는다 — 기존 호출부(테스트 포함)가 skill-repository tier 만 보는
    오늘의 동작을 그대로 유지하기 위한 명시적 opt-in 이다. 설치된 플러그인
    tier 는 `_installed_plugin_skill_dirs()` 자체가 이름이 실제로 필요할
    때만 파일을 읽으므로 별도 게이트가 필요 없다."""
    family_names = set(_ROLE_SKILLS.get(role, []))
    matches: dict[str, list[tuple[str, Path]]] = {}

    def add(source: str, name: str, d: Path) -> None:
        if (d / "hooks").is_dir():
            return
        matches.setdefault(name, []).append((source, d))

    if repo_root is not None and repo_root.is_dir():
        for name, d in _local_skill_dirs(repo_root).items():
            add("skill-repo", name, d)
    for name, entries in _installed_plugin_skill_dirs().items():
        for _qualifier, d, _version in entries:
            add("plugin", name, d)
    if home is not None:
        for name, d in _local_skill_dirs(home / ".claude" / "skills").items():
            add("local-user", name, d)
    if target_repo_root is not None:
        for name, d in _local_skill_dirs(target_repo_root / ".claude" / "skills").items():
            add("local-repo", name, d)

    corpus: list[tuple[str, Path, str]] = []
    for name, ms in matches.items():
        if name in family_names:
            continue
        if len(ms) > 1 and len({_skill_content_hash(d) for _, d in ms}) == 1:
            # 실제 운영 환경에서는 `~/.claude/skills` 가 skill-repository 를
            # 그대로 미러링해두는 경우가 흔하다 — 같은 이름이 같은
            # `SKILL.md` 내용을 가리키면 어느 tier 를 골라도 채점 결과가
            # 바이트 단위로 같으므로, 이건 "가리기"가 아니라 중복이다.
            # fail-closed 는 내용이 실제로 갈릴 때만 발동한다.
            ms = ms[:1]
        if len(ms) > 1:
            described = ", ".join(f"{source}({d})" for source, d in ms)
            sys.exit(f"cross-family 후보 스킬 {name} 가 둘 이상의 소스에서 "
                      f"겹친다 — {described} (이슈 #2055: 네 소스 중 어느 "
                      f"tier 도 다른 tier 를 조용히 가리지 않는다)")
        source, d = ms[0]
        corpus.append((name, d, source))
    return corpus


def _bm25_cross_family_scores(task_text: str, role: str,
                               repo_root: Path | None,
                               home: Path | None = None,
                               target_repo_root: Path | None = None
                               ) -> list[tuple[float, str, Path, str]]:
    """`task_text` 를 질의로, 역할의 family 밖 스킬 각각의 "Use ..." 트리거
    문장을 문서로 삼아 Okapi BM25(k1=1.5, b=0.75, 표준 기본값)로 채점한다
    — 트리거 문장은 집합으로 토큰화되므로 문서 내 항 빈도(f)는 항상 1
    (존재/부재만 본다, 트리거 문장 반복 서술 여부에 좌우되지 않기 위함).
    score > 0(질의와 최소 한 토큰 겹침) 인 것만 이름 오름차순 타이브레이크로
    내림차순 정렬해 돌려준다 — floor 근거는 위 상수 주석.

    이슈 #2055: 후보 코퍼스는 `_cross_family_candidate_corpus()` 가 네 소스에
    걸쳐 해석한다 — 각 행이 source 라벨을 달고 나온다(반환 튜플의 4번째
    자리). `home`/`target_repo_root` 를 생략하면(오늘의 호출부 호환)
    각각 `Path.home()`, 빈 tier 로 취급된다."""
    query_tokens = _tokenize(task_text)
    if not query_tokens:
        return []
    corpus = _cross_family_candidate_corpus(role, repo_root, home, target_repo_root)
    docs: list[tuple[str, Path, str, set[str]]] = []
    for name, d, source in corpus:
        trigger = _skill_trigger_line(d)
        if not trigger:
            continue
        docs.append((name, d, source, _tokenize(trigger)))
    if not docs:
        return []
    n = len(docs)
    avgdl = sum(len(toks) for _, _, _, toks in docs) / n
    df: dict[str, int] = {}
    for _, _, _, toks in docs:
        for t in toks:
            df[t] = df.get(t, 0) + 1
    scored: list[tuple[float, str, Path, str]] = []
    for name, d, source, toks in docs:
        dl = len(toks) or 1
        score = 0.0
        for t in query_tokens:
            if t not in toks:
                continue
            idf = math.log((n - df[t] + 0.5) / (df[t] + 0.5) + 1)
            score += idf * (_BM25_K1 + 1) / (1 + _BM25_K1 * (1 - _BM25_B + _BM25_B * dl / avgdl))
        if score > 0:
            scored.append((score, name, d, source))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored


def _cross_family_skill_matches(task_text: str, role: str,
                                 repo_root: Path | None,
                                 k: int = 2,
                                 home: Path | None = None,
                                 target_repo_root: Path | None = None) -> list[Path]:
    """BM25 프리필터의 상위 k 개(이슈 #2040 — 예전 raw-overlap 채점을
    대체, 호출부/시그니처는 그대로다). consult-judge 단계 없이 이 함수
    단독으로도 오늘의 fail-open 경로(자문 에러시 이 함수의 top-k)와
    동일한 모양을 낸다."""
    scored = _bm25_cross_family_scores(task_text, role, repo_root, home, target_repo_root)
    return [d for _, _, d, _ in scored[:k]]


# --------------------------------------------------------------- admission
# Issue #2100: deterministic pre-spawn admission checklist. Every named
# precondition is verified BEFORE any session is created — a missing item
# refuses the dispatch with the item's name, no session is created and no
# workspace is left behind. The checklist is DATA: one table of
# (name, predicate) rows driven by a single loop (`admission_gate()`) —
# adding an item is adding a table row, never new gate code.
#
# Predicate contract: return True (precondition present), False (missing —
# admission is refused, naming this item), or None (the check itself could
# not be evaluated because of a gh/network failure — fail-open per the
# returned-PR gate convention, issue #680: ledger event + proceed, so that
# admission never becomes a new stall class).

DEFAULT_SESSION_MAX_TURNS = 200


def _resolve_session_max_turns(cli_value: int | None) -> int:
    """Session turn budget: explicit CLI value > MUSTER_SESSION_MAX_TURNS
    env > built-in default. A value <= 0 means "unlimited" and is refused
    at admission unless explicitly overridden (issue #2100 item 4 — the
    Claude Agent SDK default is unlimited; production guidance is to
    always cap)."""
    if cli_value is not None:
        return cli_value
    env = os.environ.get("MUSTER_SESSION_MAX_TURNS")
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    return DEFAULT_SESSION_MAX_TURNS


def _admission_check_approve_token(ctx: dict) -> bool | None:
    """Item 1 (issue #2100): on a phase-2 issue the spawned role's APPROVE
    token must already be published — checked with the same predicate the
    consuming gate uses (`gates/ci.py._approved_roles_on_issue`, the exact
    scan the phase-2 merge gate later reads). This reconstructs the 3x
    APPROVE-token incident at admission time: phase-2 issue, role differs
    from every approved role, token not yet published => refuse now
    instead of stranding the session on the gate mid-flight."""
    issue, role = ctx.get("issue"), ctx["role"]
    if issue is None or ctx.get("single_phase"):
        return True  # adhoc spawn / explicit build-now bypass: no token gate
    root = Path(ctx["cwd"]).resolve()
    if not (root / MARKER).is_file():
        return True  # off-board work: no approver machinery to consult
    # Distinguish "no approval comments" from "could not read comments":
    # `_approved_roles_on_issue` deliberately collapses the two (it
    # fail-closes to phase-1), but admission must fail OPEN on a gh
    # failure — so probe the comment fetch first and fail open on error.
    _, ok = _issue_comments(root, issue)
    if not ok:
        return None  # gh/network failure — fail-open (ledger event + proceed)
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
    import ci as _ci
    approved = _ci._approved_roles_on_issue(root, issue)
    if not approved:
        return True  # phase-1 issue: no token is required yet
    return role in approved


def _admission_check_directive_completeness(ctx: dict) -> bool | None:
    """Item 2 (issue #2100): the co-injected directive items (record-format
    contract / single-vs-two-phase signal — core#195 lineage via
    `_SINGLE_PHASE_CONTRACT_LINE`; per-skill trigger lines — issue #1978)
    must assemble without error BEFORE spawn. An assembly failure here is
    an admission refusal, not a mid-flight surprise. This is deterministic
    local work (role spec file, skill-repository checkout, SKILL.md
    frontmatter), so a failure is a refusal — never fail-open."""
    role = ctx["role"]
    try:
        if not (ROOT / "roles" / f"{role}.json").is_file():
            return False  # role spec is the first directive ingredient
        # Two-phase signal: the contract line must format for this role.
        _SINGLE_PHASE_CONTRACT_LINE.format(role=role)
        # Per-skill trigger lines (issue #1978 B): resolve every skill
        # source the spawn body will resolve, and extract each trigger
        # line, exactly as the assembly code does.
        srcs = resolved_skill_sources(ctx.get("skills"), _skill_repo_root(),
                                      target_repo_root=Path(ctx["cwd"]))
        role_source = resolve_role_source(role, _skill_repo_root())
        for m in srcs:
            _skill_trigger_line(m["dir"])
        for d in role_source["skill_dirs"]:
            _skill_trigger_line(d)
    except Exception:
        # The directive cannot be assembled — refuse. SystemExit from the
        # fail-closed resolvers (unknown/invalid skill names) is NOT
        # caught here: `admission_gate()` records the named refusal and
        # re-raises it so the resolver's actionable message reaches the
        # caller unchanged (pre-#2100 behavior, still before any
        # workspace exists).
        return False
    return True


def _admission_check_watch_registration(ctx: dict) -> bool | None:
    """Item 3 (issue #2100): a live watch/monitor registration must be able
    to succeed for this session's terminal event — verified at admission,
    not after the fork. The auto-armed watcher (issue #488) is
    `sys.executable spawn.py watch --follow` plus a workspace-index /
    roster write under STATE_ROOT; verify those exact ingredients exist
    and the state directory accepts writes. Purely local — deterministic,
    so a failure is a refusal, never fail-open."""
    if ctx.get("issue") is None:
        return True  # adhoc spawns register in-roster in-process only
    if not Path(sys.executable).exists() or not Path(__file__).resolve().exists():
        return False
    try:
        ROSTER.parent.mkdir(parents=True, exist_ok=True)
        probe = ROSTER.parent / f".admission-watch-probe-{os.getpid()}"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError:
        return False
    return True


def _admission_check_budget_caps(ctx: dict) -> bool | None:
    """Item 4 (issue #2100): the spawn must carry a turn/budget cap. A
    resolved max-turns is always present (default applies when nothing is
    set); only an EXPLICIT unlimited (<= 0) without the override flag is
    refused."""
    max_turns = ctx.get("max_turns")
    if max_turns is None:
        return True  # resolver guarantees a default; None means "not plumbed here"
    if max_turns <= 0:
        return bool(ctx.get("allow_unlimited_turns"))
    return True


# The checklist table. One row per named precondition; `admission_gate()`
# is the only loop. Tests append synthetic rows here to prove that adding
# an item requires no new gate code (issue #2100 acceptance).
ADMISSION_CHECKS: list[tuple] = [
    ("approve-token", _admission_check_approve_token),
    ("directive-completeness", _admission_check_directive_completeness),
    ("watch-registration", _admission_check_watch_registration),
    ("budget-caps", _admission_check_budget_caps),
]


def admission_gate(ctx: dict) -> str | None:
    """Run every ADMISSION_CHECKS row against `ctx`. Returns the name of
    the first missing precondition (after writing ONE `admission_refused`
    ledger event naming it), or None when admission passes. A refusal is
    deterministic and NON-RETRYABLE by the caller — the fix is publishing
    the missing precondition, never retrying the same dispatch."""
    for name, predicate in ADMISSION_CHECKS:
        try:
            verdict = predicate(ctx)
        except SystemExit:
            # A fail-closed resolver exits with its own actionable message
            # (e.g. "--skills: unknown skill ..."). That IS a refusal of
            # this item: record it under the item's name, then let the
            # original exit propagate unchanged — still before any session
            # or workspace exists.
            ledger_write({"event": "admission_refused", "item": name,
                          "role": ctx.get("role"), "issue": ctx.get("issue"),
                          "ts": int(time.time())})
            raise
        except Exception as exc:
            # A check that crashes must not become a new stall class:
            # follow the returned-PR gate fail-open convention (issue
            # #680) — record the fact, let the spawn proceed.
            verdict = None
            print(f"admission check {name!r} crashed — fail-open: {exc}",
                  file=sys.stderr)
        if verdict is None:
            ledger_write({"event": "admission_gate_fail_open", "item": name,
                          "role": ctx.get("role"), "issue": ctx.get("issue"),
                          "ts": int(time.time())})
            continue
        if not verdict:
            ledger_write({"event": "admission_refused", "item": name,
                          "role": ctx.get("role"), "issue": ctx.get("issue"),
                          "ts": int(time.time())})
            return name
    return None


def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
               issue: int | None = None, bounded: bool = False,
               stall_timeout_min: float = 5.0, no_wait: bool = False,
               despite_returned: bool = False, model: str | None = None,
               skills: str | None = None, single_phase: bool = False,
               max_turns: int | None = None,
               allow_unlimited_turns: bool = False) -> int:
    """역할 하나를 띄우고, 무슨 일이 있었는지 원장에 남기고, 처분을 말한다.

    main() 과 drive() 가 같은 몸통을 쓴다 — 드라이버가 따로 스폰 경로를 들고
    있으면 둘이 갈라지고, 갈라진 쪽이 조용히 게이트 하나를 빠뜨린다.
    """
    # Issue #2100: pre-spawn admission checklist. Runs before ANY side
    # effect (workspace clone, branch, roster/index writes, session
    # process) — a refusal names the missing precondition, writes one
    # `admission_refused` ledger event (inside `admission_gate()`), and
    # returns without creating anything. Deterministic and non-retryable:
    # the caller must publish the missing precondition, not retry.
    resolved_max_turns = _resolve_session_max_turns(max_turns)
    _refused_item = admission_gate({
        "cwd": cwd, "role": role, "issue": issue,
        "single_phase": single_phase, "skills": skills,
        "max_turns": resolved_max_turns,
        "allow_unlimited_turns": allow_unlimited_turns,
    })
    if _refused_item is not None:
        print(f"[{role}] admission refused: missing precondition "
              f"'{_refused_item}' (issue #2100) — no session created, no "
              f"workspace left behind. This refusal is deterministic and "
              f"non-retryable: publish the missing precondition, then "
              f"dispatch again.", file=sys.stderr)
        return 1
    spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())
    _BOOTSTRAP_TIMING.clear()
    # 이슈 #2001: 크로스-패밀리 스코어링은 이 함수가 받은 원본 task 텍스트를
    # 대상으로 한다 — 아래에서 task 에 여러 안내 문단이 계속 덧붙는데, 그
    # 덧붙은 텍스트(스킬 목록 자체 등)가 스코어링 입력에 섞이면 결정론이
    # 스폰마다 달라진다.
    _cross_family_task_text = task
    cross_family_dirs: list[Path] = []
    # 이슈 #2076: skill_judge 자문이 이번 스폰에서 완료됐는지 fail-open
    # 했는지 — role_source 가 skill-repo 가 아니면 자문 자체가 안 불려
    # "not-run" 으로 남는다(아래 ledger_write 필드).
    skill_judge_outcome = "not-run"
    # 이슈 #1742/#1774: --skills 이름 검증(네 소스 모두)은 워크스페이스/
    # 브랜치를 건드리기 전에 끝난다(fail-closed, 요구사항 2) — 아래
    # 워크스페이스 생성보다 먼저 온다.
    skill_sources = resolved_skill_sources(skills, _skill_repo_root(),
                                            target_repo_root=Path(cwd))
    skill_dirs = [m["dir"] for m in skill_sources]
    # 오늘 shape 과 맞추기 위한 flat sha: 전부 skill-repo 매치일 때만 채운다
    # (요구사항: skill-repo-only 조합은 오늘의 skills/skills_sha shape 를
    # 그대로 유지한다) — 그 외 조합은 skills_detail 의 per-skill 소스로만
    # 표현되고 이 flat 필드는 None.
    skill_sha = (skill_sources[0]["sha"]
                 if skill_sources and all(m["source"] == "skill-repo"
                                           for m in skill_sources)
                 else None)
    # 이슈 #1955(이슈 #1758 phase 5 이행): skill-repository 해석도 같은
    # 이유로 워크스페이스/브랜치 생성보다 먼저 온다 — 역할이 매핑한 스킬
    # 이름이 모르는 이름이거나 hooks/ 를 들고 있으면 여기서 fail-closed.
    role_source = resolve_role_source(role, _skill_repo_root())
    # 이슈 #2061: skill_judge 자문(BM25 프리필터 + haiku 판단)을 워크스페이스
    # 클론/브랜치 체크아웃(~12s)과 겹치도록 그 전에 먼저 던진다 — 아래
    # "cross_family" 단계에서 join 만 한다. 자문은 읽기 전용(저장소 파일을
    # 건드리지 않는다, `_skill_judge_consult()` 의 override 문구)이라
    # 워크스페이스가 아직 없어도(원본 cwd 로) 안전하게 먼저 돌 수 있다.
    _cross_family_executor: concurrent.futures.ThreadPoolExecutor | None = None
    _cross_family_future = None
    if issue is not None and role_source["source"] == "skill-repo":
        _cross_family_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        _cross_family_future = _cross_family_executor.submit(
            _cross_family_skill_matches_with_consult,
            _cross_family_task_text, role, _skill_repo_root(), issue, cwd,
            home=Path.home(), target_repo_root=Path(cwd))
    if issue is not None:
        root = Path(cwd).resolve()
        # 이슈 #1239: #680 의 거절 게이트를 무조건적 surfacing 으로 대체한다
        # — 처분 안 된 PR 이 있어도 스폰은 결코 막지 않는다(북극-요구#1,
        # never-missed != never-spawn). `--despite-returned` 는 이제 아무
        # 것도 바꾸지 않는 no-op (CLI 호환성 보존, deprecation 안내만 찍는다).
        blockers, ok = _undispositioned_role_prs(root, exclude_issue=issue)
        if not ok:
            print(f"[{role}] returned-PR 게이트: gh 조회 실패 — fail-open 으로 "
                  f"통과시킨다 (이슈 #680)", file=sys.stderr)
            ledger_write({"event": "returned_pr_gate_fail_open", "role": role,
                          "issue": issue, "ts": int(time.time())})
        else:
            _print_returned_pr_surfaced(blockers, source="spawn")
        if despite_returned:
            print(f"[{role}] --despite-returned 는 더 이상 아무 효과가 없다 "
                  f"(deprecated, 이슈 #1239) — 게이트가 항상 non-blocking "
                  f"surfacing 이라 무시할 거절이 없다", file=sys.stderr)
        # 이슈 #1179: 워크스페이스 하나 더 만들기 전에 먼저 안전하게
        # 쓸어낸다(spawn-time sweep) — 정리는 사람이 `spawn.py clean` 을
        # 기억해야만 도는 게 아니라 기본으로 켜져 있어야 한다(northpole
        # req#7). 스윕 실패가 스폰 자체를 막으면 안 되므로 예외를 삼킨다.
        if _clean_auto_enabled():
            try:
                auto_sweep(_workspace_base(), _clean_max_age_days(),
                           _clean_max_bytes())
            except Exception as ex:
                print(f"[{role}] auto-sweep 실패(스폰은 계속): {ex}",
                      file=sys.stderr)
        # 격리 작업 클론에서 돈다 — 사용자의 체크아웃은 건드리지 않고,
        # 동시 스폰들이 서로의 index/브랜치를 밟지 않는다.
        with _timed("workspace"):
            cwd = issue_workspace(cwd, issue, role)
        claim_rejection = _acquire_spawn_claim(cwd, issue, role)
        if claim_rejection is not None:
            print(f"[{role}] {claim_rejection}", file=sys.stderr)
            return 1
        with _timed("branch"):
            br = checkout_issue_branch(cwd, issue, role)
        print(f"[{role}] 격리 작업 디렉토리: {cwd}  (브랜치 {br})", file=sys.stderr)
        # 원본(프리픽스 붙기 전) 맡길 일을 한 번만 저장 — 재스폰(다른 spawn.py
        # 프로세스일 수 있다)이 이걸 읽어 그대로 넘기면, 아래에서 프리픽스를
        # 다시 붙여도 중복되지 않는다 (이슈 #132).
        task_path = Path(str(cwd) + ".task.txt")
        if not task_path.exists():
            task_path.write_text(task, encoding="utf-8")
        # issue #1017 (northpole req#6): 이슈가 인용하는 요구 ID를 스폰
        # 텍스트에 그대로 실어, 스폰된 역할 세션이 첫 턴부터 어느 요구를
        # 섬기는지 안다. gh 조회 실패는 조용히 건너뛴다 — 이 줄이 없다고
        # 스폰 자체를 막을 이유는 없다(require_requirement_linkage 가 이미
        # phase-1 드래프트 시점에 구조적으로 막는다).
        req_line = ""
        goal_pin = ""
        body = None
        _design_artifacts_gate = None
        try:
            sys.path.insert(0, str((ROOT / "gates").resolve()))
            import gh_rest as _gh_rest
            import requirement_linkage as _requirement_linkage
            import design_artifacts_gate as _design_artifacts_gate
            issue_data = _gh_rest.fetch_issue(Path(cwd), issue)
            body = issue_data.get("body") if issue_data else None
            title = issue_data.get("title") if issue_data else None
            if body is not None:
                req_ids = _requirement_linkage.cited_requirement_ids(body)
                if req_ids:
                    req_line = f"이 이슈가 인용하는 요구: {', '.join(req_ids)}\n"
                goal_pin = _goal_pin_block(title, body)
        except Exception:
            req_line = ""
            goal_pin = ""
        task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                + req_line + goal_pin +
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n"
                f"완료의 정의: 변경이 이 브랜치에 **커밋**되고 push 되어 PR 로\n"
                f"제출된 상태다. 미커밋 변경은 존재하지 않는 것과 같다 —\n"
                f"세션을 끝내기 전에 반드시 커밋하라. push/PR 이 네트워크로\n"
                f"막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다.\n"
                f"체크포인트 커밋: 길거나 백그라운드로 넘기는 검증을 시작하기\n"
                f"전에 먼저 체크포인트 커밋을 해 두고, 검증이 끝난 뒤 amend 하거나\n"
                f"후속 커밋을 추가하라 — 검증부터 하고 나중에 커밋하는 습관은\n"
                f"세션이 검증 도중 끊길 때 미커밋 변경을 그대로 좌초시킨다.\n"
                f"경고: 이 턴은 headless 이고 단발이다 — 세션이 끝나면 이 프로세스도\n"
                f"끝난다. run_in_background 로 넘긴 작업은 부모 턴이 끝나는 순간 함께\n"
                f"죽는다(백그라운드 워커가 커밋·push 를 대신 끝내줄 것이라고 가정하지\n"
                f"마라 — 실측된 실패 패턴이다). 모든 작업은 이 턴 안에서 직접 끝내라.\n\n") + task
        # 이슈 #1978 (A): --single-phase 신호가 없으면 이 블록은 아무 것도
        # 안 붙인다 — 오늘의 프롬프트와 바이트 단위로 동일해야 한다는
        # 제안서 제약. B(스킬 트리거 줄)보다 먼저 온다(A before B, 제안서
        # 순서).
        if single_phase:
            task = task + "\n\n" + _SINGLE_PHASE_CONTRACT_LINE.format(role=role)
        if skill_sources:
            skill_lines = ", ".join(
                f"{m['name']}"
                + (f" — {_skill_trigger_line(m['dir'])}"
                   if _skill_trigger_line(m['dir']) else "")
                + f" ({_describe_skill_match(m)})"
                for m in skill_sources)
            task = task + (
                f"\n\n마운트된 스킬(--skills, 이슈 #1742/#1774): {skill_lines}\n")
        if role_source["source"] == "skill-repo":
            # 이슈 #1978 (B): 스킬 이름 옆에 SKILL.md 의 "Use ..." 트리거
            # 문장을 인라인한다(#1960 의 1/9 발화율 넛지를 대체) — 트리거
            # 문장이 없는 스킬도 이름은 절대 빠뜨리지 않는다(empty-state
            # 요구).
            # 이슈 #2001/#2040: family 밖 top-K(K=2) 크로스-패밀리 스킬을
            # add-only 로 얹는다 — 매치가 없으면 cross_family_dirs 는 빈
            # 목록이라 아래 줄들은 오늘과 바이트 단위로 동일하게 남는다.
            # 이슈 #2040: BM25 프리필터 + skill_judge 자문 판단(스폰당
            # 최대 자문 1회) — 소요 시간은 "cross_family" 단계로 측정해
            # 부트스트랩 타이밍 요약에 실린다(Acceptance: per-spawn latency).
            with _timed("cross_family"):
                # 이슈 #2061: 위에서 워크스페이스/브랜치 셋업보다 먼저 던져둔
                # 자문을 여기서 join 만 한다 — 이 단계의 측정치는 이제 겹친
                # 대기 시간이 아니라 순수 join 대기(자문이 셋업보다 오래
                # 걸린 나머지)만 반영한다.
                cross_family_dirs, skill_judge_outcome = (
                    _cross_family_future.result()
                    if _cross_family_future is not None else ([], "not-run"))
                if _cross_family_executor is not None:
                    _cross_family_executor.shutdown(wait=False)
            role_skill_lines = ", ".join(
                d.name + (f" — {_skill_trigger_line(d)}" if _skill_trigger_line(d) else "")
                for d in role_source["skill_dirs"]
            ) if role_source["skill_dirs"] else ", ".join(role_source["skills"])
            if cross_family_dirs:
                cross_family_lines = ", ".join(
                    d.name + (f" — {_skill_trigger_line(d)}" if _skill_trigger_line(d) else "")
                    for d in cross_family_dirs)
                role_skill_lines = (role_skill_lines + ", " + cross_family_lines
                                     if role_skill_lines else cross_family_lines)
                cross_family_clause = (
                    f" (이 중 {', '.join(d.name for d in cross_family_dirs)} 는 "
                    f"이번 과제 텍스트와의 키워드 매치로 추가된 크로스-패밀리 "
                    f"스킬 — 이슈 #2001)")
            else:
                cross_family_clause = ""
            task = task + (
                f"\n\n이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: "
                f"스킬 {role_skill_lines} "
                f"(skill-repository {role_source['skill_sha']}) 가이던스만 붙는다 — "
                f"집행은 core 훅뿐이다.{cross_family_clause}\n")
        # 이슈 #1960 phase B: 마운트된 스킬이 하나라도 있으면(--skills 든
        # 역할 매핑이든) 실체 작업을 시작하기 전에 그 목록을 이번 과제와
        # 대조해보라고 스폰 시점에 못박는다. 베이스라인 측정
        # (docs/issue-1960/reports/execution-observation/baseline-measurement.md)
        # 이 relevance-gated 세션 38개 전부에서 Skill 호출 0건을 보였다 —
        # 스킬이 안 맞아서가 아니라 애초에 호출을 고려하지 않는 구조적
        # 공백이라는 뜻이라, trigger 문구를 손보는 대신 이 지시문 한 줄을
        # 추가한다(단일 변경, 순차 적용).
        if skill_sources or role_source["skills"]:
            task = task + (
                "\n\n스킬 점검(이슈 #1960): 실체 작업을 시작하기 전에, 위에 "
                "마운트된 스킬 목록을 이번 과제와 대조하라. trigger 조건이 "
                "이번 과제에 그럴듯하게 들어맞는 스킬이 있으면 Skill 도구로 "
                "호출하고, 없으면 검토했다는 사실만 유념하고 넘어가라. "
                "invoke-before-apply(이슈 #2062): APPLICABLE 로 판단한 "
                "스킬은 적용하기 전에 반드시 Skill 도구로 그 스킬의 전체 "
                "SKILL.md 를 로드해야 한다 — not-applicable 로 판단한 "
                "스킬은 이 의무에서 면제된다(강제 로드도, 토큰 낭비도 "
                "없다).\n")
            # 이슈 #2039: 마운트된 스킬 하나마다 레코드에 한 줄씩 verdict를
            # 남겨야 한다 — 스킬을 조용히 무시하는 걸 불가능하게 만든다.
            # 스킬이 하나도 안 마운트되면 이 블록 전체가 안 붙으므로
            # (위 조건과 동일), 무-스킬 세션은 오늘과 바이트 단위로 같다.
            task = task + (
                "\n\n스킬-verdict 의무(이슈 #2039): 위에 마운트된 스킬 "
                "이름마다, 레코드에 `skill-verdict: <스킬명> — applied: "
                "<어디서/어떻게> | not-applicable: <한 줄 이유>` 형태의 줄을 "
                "정확히 하나씩 남겨야 한다 — 적용 여부 판단은 전적으로 이 "
                "세션의 몫이지만, 그 판단을 아예 안 밝히는 것은 더 이상 "
                "허용되지 않는다. applied: 줄은 위 invoke-before-apply "
                "의무에 따라 실제로 Skill 도구를 호출했다는 증거로 "
                "`invoked;` 를 자유 텍스트 맨 앞에 붙여야 한다(이슈 "
                "#2062) — not-applicable: 줄은 이 마커가 필요 없다.\n")
        # 이슈 #2014 (artifact-gate phase 3): `design-artifacts:` 선언이
        # 있으면 선언된 각 아티팩트 경로를, 그 basename 이 마운트된 스킬들의
        # 트리거 문장과 가장 많이 겹치는 스킬 하나와 짝지어 한 줄씩 붙인다
        # (#2013 parse_declaration + #1978B/#2001 tokenize/trigger 재사용,
        # 새 fetch 없음 — body 는 spawn.py:8085 에서 이미 받았다). 태그가
        # 없거나(parse_declaration 이 None) 어떤 아티팩트도 마운트된
        # 스킬과 겹치지 않으면 이 블록은 아무 것도 안 붙인다(제안서
        # Constraints — byte-identical on absence).
        declared_artifacts = _design_artifacts_gate.parse_declaration(body) \
            if body is not None and _design_artifacts_gate is not None else None
        if declared_artifacts:
            artifact_all_dirs = list(skill_dirs) + [
                d for d in role_source["skill_dirs"] if d not in skill_dirs]
            artifact_all_dirs = artifact_all_dirs + [
                d for d in cross_family_dirs if d not in artifact_all_dirs]
            pairing_lines = []
            for artifact_path in declared_artifacts:
                basename = Path(artifact_path).stem
                artifact_tokens = _tokenize(basename)
                if not artifact_tokens:
                    continue
                scored: list[tuple[int, str, Path]] = []
                for d in artifact_all_dirs:
                    trigger = _skill_trigger_line(d)
                    if not trigger:
                        continue
                    overlap = len(artifact_tokens & _tokenize(trigger))
                    if overlap > 0:
                        scored.append((overlap, d.name, d))
                if not scored:
                    continue
                scored.sort(key=lambda t: (-t[0], t[1]))
                _, best_name, best_dir = scored[0]
                pairing_lines.append(
                    f"{artifact_path} ↔ {best_name} — {_skill_trigger_line(best_dir)}")
            if pairing_lines:
                task = task + (
                    "\n\n아티팩트-스킬 짝짓기(이슈 #2014): 선언된 각 아티팩트를 "
                    "그것을 만드는 절차를 담은 스킬과 짝지었다.\n"
                    + "\n".join(pairing_lines) + "\n")
    # 이슈 #2073: 같은 body(새 fetch 없음, spawn.py 의 위 블록이 이미 받아온
    # 것)에서 두 개의 조건부 줄을 붙인다 — (a) `runtime-artifacts:` 가
    # 선언됐거나 자문 스코어러가 울리면 artifact-smoke 트리거 한 줄,
    # (b) 이슈가 design-bearing 이면서 선언된 design-artifacts 에
    # 스토리보드가 있으면 live-screen 검증 한 줄. 둘 다 조건이 없으면
    # 아무 것도 안 붙는다(제안서 Constraints — byte-identical on absence).
    # 스킬 마운트 여부와 무관하므로 위 스킬 블록 바깥에 둔다.
    task = task + _artifact_smoke_task_lines(body if issue is not None else None)
    # 이슈 #1955: 역할은 룰북을 아예 마운트하지 않는다 — rulebook 해석
    # 경로 자체가 은퇴했다(요구사항: 룰북 마운트가 "붙었지만 무시됨"이
    # 아니라 argv 에서 통째로 빠져야 한다는 #1758 요구사항 2를 무조건화).
    plugins: list[Path] = []
    # core_plugin_dirs() 를 print 보다 먼저 불러 core_root() 의 관리 클론
    # pull 이 먼저 일어나게 한다 — 순서가 뒤집히면(예전처럼 print 뒤에서
    # 부르면) 로그에는 pull 전 sha, ledger 에는 pull 후 sha 가 찍혀 같은
    # run 안에서 두 기록이 어긋난다.
    with _timed("core"):
        core_plugins = core_plugin_dirs()
    with _timed("settings"):
        s = role_settings(role, cwd)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(s, f)
            settings = f.name
    # --skills(#1742)와 역할 매핑 스킬(#1758/#1955)은 additive — 같은
    # --plugin-dir 마운트 목록에 합쳐 붙인다.
    all_skill_dirs = list(skill_dirs) + [d for d in role_source["skill_dirs"]
                                          if d not in skill_dirs]
    all_skill_dirs = all_skill_dirs + [d for d in cross_family_dirs
                                        if d not in all_skill_dirs]
    try:
        rulebook_desc = "skill-repo(이슈 #1955)"
        roster_resolution_fields = _role_source_roster_fields(role_source)
        print(f"[{role}] 플러그인 {len(plugins)}개, 룰북 {rulebook_desc}, "
              f"core 플러그인 {', '.join(p.name for p in core_plugins)}, "
              f"core {core_version()}, 작업 디렉터리 {cwd}", file=sys.stderr)
        print(_bootstrap_timing_line(role), file=sys.stderr)
        # 이슈 #2070: design-bearing 판정은 issue 본문에 대해서만 의미가
        # 있다 — 없으면(adhoc 스폰) None, gates 호출이 실패해도(gh 오류 등)
        # fail-open 으로 None 에 떨어진다(라우팅 계층 자체가 fail-open).
        design_bearing_verdict = None
        if issue is not None:
            try:
                sys.path.insert(0, str((ROOT / "gates").resolve()))
                import design_bearing_classifier
                _verdict = design_bearing_classifier.check(Path(cwd), issue)
                design_bearing_verdict = bool(_verdict and _verdict.get("design_bearing"))
            except Exception:
                design_bearing_verdict = None
        # 맡길 일은 stdin 으로 넘긴다. 인자로 주면 가변 인자 플래그가 삼키고,
        # 셸 보간을 거치면 신뢰할 수 없는 값의 $(…) 가 실행된다.
        cmd, extra_env = spawn_cmd(settings, role, unattended,
                                   core_plugins, plugins, model,
                                   all_skill_dirs,
                                   skill_sha or role_source["skill_sha"],
                                   single_phase=single_phase,
                                   design_bearing_verdict=design_bearing_verdict,
                                   max_turns=resolved_max_turns)
        # 이슈 #2070: roster 기록용 두 내부 키를 여기서 뽑아내 실제 subprocess
        # env 에는 안 들어가게 한다 — spawn_cmd() 가 심어준 신호일 뿐, 세션
        # 자신의 env 표면이 아니다.
        _model_routing_model = extra_env.pop("_MODEL_ROUTING_MODEL", "")
        _model_routing_rule = extra_env.pop("_MODEL_ROUTING_RULE", "")
        # 이슈 #1978 (A): --single-phase 신호일 때만 얹는다 — 없으면
        # extra_env 는 오늘과 바이트 단위로 동일한 채로 남는다.
        if single_phase:
            extra_env["CORE_BUILD_NOW"] = "1"
        if issue is not None:
            # 툴체인 캐시를 워크스페이스 안으로 — go 등이 홈(~/Library/...)에
            # 캐시·설정을 쓰려다 샌드박스에 막혀 빌드가 승인 프롬프트로
            # 빠졌다(실측: phase 2 가 go build 를 한 번도 못 돌림). 쓰기가
            # 전부 cwd 아래로 오면 샌드박스 안에서 승인 없이 돈다.
            wcache = os.path.join(cwd, ".muster-cache")
            extra_env.update({
                "GOCACHE": os.path.join(wcache, "go-build"),
                "GOMODCACHE": os.path.join(wcache, "gomod"),
                "GOENV": os.path.join(wcache, "goenv"),
                "GOPATH": os.path.join(wcache, "gopath"),
                "XDG_CACHE_HOME": os.path.join(wcache, "xdg"),
                "npm_config_cache": os.path.join(wcache, "npm"),
                "PIP_CACHE_DIR": os.path.join(wcache, "pip"),
                "CARGO_HOME": os.path.join(wcache, "cargo"),
            })
        before = board_snapshot(cwd)
        before_head = _git_head(cwd) if issue is not None else None
        t0 = time.monotonic()
        # stream-json 을 줄 단위로 받아 라이브 로그에 tee 한다 — "지금 뭐
        # 하는 중인가"가 세션이 끝나기 전에도 보이게. 최종 result 이벤트가
        # 옛 --output-format json 의 결과 오브젝트와 같은 필드를 든다.
        log_path = (_session_log_path(cwd) if issue is not None
                    else ROOT / "runs" / "last-session.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{role}] 라이브 로그: {log_path}", file=sys.stderr)
        result = {}
        roster_key = f"issue-{issue}/{role}" if issue is not None else f"adhoc/{role}/{os.getpid()}"
        events_path = _events_path(cwd)
        offset_path = _offset_path(cwd)
        is_parent_return = False
        if bounded and issue is not None:
            _workspace_index_put(issue, role, str(cwd), str(log_path))
            # 부모(호출한 CLI 콜)는 이벤트 하나 또는 stall 시간까지만 기다리고
            # 리턴한다 — 자식이 세션을 끝까지 몰고 간다 (이슈 #114). setsid 로
            # 자식을 새 세션에 놓아, 부모가 속한 프로세스 그룹에 신호가 가도
            # 자식은 안 죽는다. settings 임시파일은 자식이 아직 쓰는 중이라
            # 부모 쪽 finally 에서 지우면 안 된다 (is_parent_return 이 막는다).
            #
            # 기다리기 전에 offset 을 지금의 파일 끝으로 민다. events.jsonl 은
            # append-only 이고 같은 워크스페이스로 재스폰하면 이전 세션의 줄이
            # 그대로 남아 있어서, offset 이 그 앞을 가리키면 새 스폰이 **과거
            # 이벤트**로 즉시 리턴한다 — 세션은 계속 도는데 호출자는 끝났다고
            # 듣는다. 실측 2026-07-30(core issue-53 phase 2): 78분 전 phase 1 이
            # 남긴 pr-opened 로 복귀했다. 이 스폰이 소비할 수 있는 것은 이
            # 세션이 낸 이벤트뿐이어야 한다 (이슈 #142).
            _write_offset(offset_path, _event_count(events_path))
            child_pid = os.fork()
            if child_pid == 0:
                # 이슈 #908: fork-child 설정(setsid/dup2)과 Popen() 은 첫
                # roster_register/session-start (아래, Popen 뒤) 이전에
                # 실행된다 — 그 구간에서 죽으면(SIGKILL/segfault 포함, 예외를
                # 던지지 않는 죽음도) roster_watchdog() 은 등록된 엔트리만
                # 스캔하므로 구조적으로 못 본다(실측: #895/#907, 흔적 없는
                # 사망). 이 구간에 들어가기 전에 자신의 pid 로 로스터 스텁과
                # 이른 session-start 를 먼저 남겨, 어떻게 죽든
                # roster_watchdog() 의 기존 dead-entry 경로가 이 엔트리를
                # 보게 한다. try/except 는 죽음 자체를 잡는 게 아니라(신호로
                # 죽으면 못 잡는다) 사람이 읽을 spawn-death 이벤트를 남기는
                # 용도로만 아래에서 덧붙인다.
                _early_roster_entry = {
                    "pid": os.getpid(), "role": role,
                    "issue": issue, "ts": int(time.time()),
                    "work": str(cwd), "log": str(log_path),
                    "expects_pr": issue is not None,
                    "session_id": os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None,
                    "before_head": before_head,
                    "wrapper_pid": os.getpid(),
                    "model": _model_routing_model,
                    "model_rule": _model_routing_rule,
                }
                _early_roster_entry.update(_skill_roster_fields(skill_sources, skill_sha))
                _early_roster_entry.update(roster_resolution_fields)
                roster_register(roster_key, _early_roster_entry)
                _append_event(events_path, "session-start",
                              {"pid": os.getpid(), "ts": time.time()})
            if child_pid > 0:
                is_parent_return = True
                # 이슈 #488: watch 는 여태 사람/오케스트레이터가 스폰마다 따로
                # 재무장해야 하는 opt-in 이었다 — 재무장을 깜빡하면 세션이
                # 조용히 끝났다(실측: #472/#473/#484/#173 재스폰 라운드).
                # 여기서 스폰 자신이 `spawn.py watch --follow` 를 detached
                # 프로세스로 띄우고 그 pid 를 workspace index 에 등록한다.
                # 워처를 못 띄우면 스폰 자체를 완료로 치지 않는다 — 구조적으로
                # "워처 없는 스폰"이 불가능해야 한다는 요구이기 때문이다.
                watcher_log = Path(str(cwd) + ".watcher.log")
                resolved_watch_cwd = str(Path(cwd).resolve())
                try:
                    with watcher_log.open("a", encoding="utf-8") as wf:
                        wproc = subprocess.Popen(
                            [sys.executable, str(Path(__file__).resolve()),
                             "-C", resolved_watch_cwd,
                             "watch", "--issue", str(issue), "--role", role,
                             "--follow", "--self-heal",
                             "--stall-timeout", str(stall_timeout_min)],
                            stdin=subprocess.DEVNULL, stdout=wf,
                            stderr=subprocess.STDOUT, start_new_session=True,
                        )
                except OSError as exc:
                    print(f"[{role}] 워처 자동 무장 실패 — 스폰을 완료로 치지 "
                          f"않는다: {exc}", file=sys.stderr)
                    return 1
                _workspace_index_put(issue, role, str(cwd), str(log_path),
                                      watcher_pid=wproc.pid,
                                      watcher_armed_at=time.time())
                print(f"[{role}] 워처 자동 무장: pid {wproc.pid} "
                      f"(로그 {watcher_log})", file=sys.stderr)
                # 이슈 #1154: 워처는 `start_new_session=True` 로 detach 됐지만,
                # 아래 `_await_bounded()` 를 그대로 거치면 이 스폰 프로세스
                # 자신이 호출자의 bounded 호출 안에 계속 살아 있는다 —
                # `_rearm_watcher_detached()`(#1133/#1149) 가 등록 직후 바로
                # 리턴해 살아남는 것과 달리, 여기는 그 리턴이 `no_wait` 뒤에만
                # 있어서 기본 경로(non-`--no-wait`)의 워처가 호출자와 함께
                # 죽는 걸로 관측됐다(이슈 #1154 8/8). 등록 직후 항상 리턴해
                # `_rearm_watcher_detached()` 와 같은 모양으로 맞춘다.
                # 기존 bounded 진행 대기가 필요하면 별도
                # `spawn.py watch --issue <n> --role <role>` 호출로 이어본다.
                print(f"[{role}] 스폰은 리턴했지만 세션은 계속 돈다 — 상태는 "
                      f"spawn.py ps, 이어보려면 spawn.py watch --issue "
                      f"{issue} --role {role}", file=sys.stderr)
                return 0
            try:
                _rewrite_spawn_claim_pid(cwd)
                os.setsid()
                # 부모(호출자)가 물려준 stdout/stderr 를 그대로 두면, 곧 띄울
                # claude 서브프로세스가 Popen() 에서 stdout/stderr 를 안 지정해도
                # 그 fd 를 그대로 상속해 세션 끝까지 파이프를 쥐고 있는다 —
                # 부모가 bounded 리턴으로 먼저 나가도, 호출자가 그 파이프의 EOF
                # 를 기다리고 있었다면 여전히 세션 끝까지 블록한다 (실측: 헌트로
                # 발견). devnull 로 갈아치워 파이프 소유권을 끊는다.
                devnull_fd = os.open(os.devnull, os.O_RDWR)
                os.dup2(devnull_fd, 0)
                os.dup2(devnull_fd, 1)
                os.dup2(devnull_fd, 2)
                os.close(devnull_fd)
            except OSError as exc:
                _append_event(events_path, "spawn-death",
                              {"pid": os.getpid(), "stage": "fork-setup",
                               "error": str(exc)})
                raise
        try:
            proc = subprocess.Popen(
                cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, env={**os.environ, **extra_env}, start_new_session=True,
            )
        except OSError as exc:
            if issue is not None:
                _append_event(events_path, "spawn-death",
                              {"pid": os.getpid(), "stage": "popen",
                               "error": str(exc)})
            raise
        roster_register(roster_key, {
            "pid": proc.pid, "role": role,
            "issue": issue, "ts": int(time.time()),
            "work": str(cwd), "log": str(log_path),
            "expects_pr": issue is not None,  # 이슈 #492: reconcile() 의 expected 입력
            # 이슈 #2070: 이 스폰에 실제로 --model 로 붙은 값과, 그것을 고른
            # 규칙(`cli-override`/`env-override`/`config-override`/
            # `role-tier:<name>`/`design-bearing-override`/
            # `single-phase-tier:<name>`/`default-tier:<name>`/
            # `fail-open-default`) — model-vs-outcome 효율을 나중에
            # #1991/#2015 대비 측정 가능하게.
            "model": _model_routing_model,
            "model_rule": _model_routing_rule,
            # 이슈 #878: 이 스폰을 무장한 오케스트레이터 자신의 세션 ID —
            # `ORCHESTRATOR_SESSION_ID_ENV` 로 호출자(인터랙티브 호스트나
            # harness driver)가 심어준 값을 그대로 옮겨 담는다. spawn.py
            # 자신은 이 값을 지어내지 않는다 — 없으면 None(해당 세션은
            # headless-resume 대상이 아니라는 신호, 케이스 1 의 라이브
            # notify 경로만 쓴다).
            "session_id": os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None,
            "before_head": before_head,  # 이슈 #90 watchdog signal 4 재료
            # `pid`(claude 서브프로세스)는 proc.wait() 리턴과 함께 정상
            # 종료에서도 먼저 죽는다 — push/게이트·소유권 리포트/classify/
            # ledger_write 를 거쳐야 session-end 가 남는 후처리 구간
            # (spawn.py:proc.wait()~_append_event("session-end")) 동안은
            # `pid` 만으로 생존을 재는 소비자가 이 구간을 크래시로 오판한다
            # (이슈 #224 hunt 발견). 그 구간까지 살아있는 이 fork-child(또는
            # non-bounded 경로에서는 현재 프로세스) 자신의 pid 를 별도
            # 필드로 남겨 `_watch --follow` 의 크래시 판정이 여기 대신
            # 참조하게 한다 — `pid`(roster_kill 의 SIGTERM 대상)의 기존
            # 의미는 그대로 둔다.
            "wrapper_pid": os.getpid(),
            # 이슈 #1742/#1774: --skills 사용 시에만 채운다 — 안 쓰면 키
            # 자체가 없어서(빈 값이 아니라) no-flag 경로의 JSON shape 는
            # 그대로다.
            **_skill_roster_fields(skill_sources, skill_sha),
            **roster_resolution_fields,
        })
        if issue is not None:
            # 크래시가 roster_remove/종료 이벤트 사이에서 나면 이 이전엔
            # events.jsonl 에 아무 흔적도 안 남았다(실측: survey.md 사건 #2) —
            # append-only 라 크래시에도 살아남는 이 기록이 session_end_verdict
            # 의 기준선이다 (이슈 #132).
            # session_start_ts 를 변수로 남겨 두는 이유(이슈 #247): 이 세션
            # 자신이 정상 종료하며 미커밋 작업을 남기면, 아래 self-trigger
            # 호출이 워치독처럼 events.jsonl 을 다시 읽어 이 ts 를 재구성할
            # 필요 없이 같은 값을 그대로 재스폰 claim 키로 쓴다.
            # 이슈 #132 의 워치독-전용 재스폰은 ~10-15분 워치독 주기가 자연히
            # 세대 사이를 벌려 놓아 초 단위(int) ts 충돌이 실무에서 안 났지만,
            # self-trigger 는 그 간격 없이 곧바로 다음 세대를 낳을 수 있다 —
            # 초 단위로 자르면 같은 초 안에서 시작한 서로 다른 세대의
            # session_start_ts 가 우연히 같아져 `_respawn_or_cap()` 의
            # already_claimed 검사가 남의 respawn-attempt 를 자기 것으로
            # 오인하고 상한 확인도 없이 조용히 빠져나갈 수 있다(실측:
            # 어써샬-브로큰 헌트). 초 단위로 자르지 않아 충돌 창을 좁힌다.
            session_start_ts = time.time()
            _append_event(events_path, "session-start",
                          {"pid": proc.pid, "ts": session_start_ts})
        try:
            proc.stdin.write(task)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass
        pr_seen = _prior_event_details(events_path, "pr-opened") if issue is not None else set()
        # 이슈 #232: 층(게이트/하네스/샌드박스) 단위 dedup — 예전엔 불리언
        # 하나(gate_refusal_seen)가 세 층을 전부 한 라벨로 뭉갰다. 키는
        # ("gate", <게이트명>, <사유>) / ("harness", <detail>) /
        # ("sandbox", <detail>) — 층·게이트·정규화된 텍스트별로 구분한다
        # (이슈 #246 결함 2: 텍스트를 안 실으면 같은 층의 서로 다른 두 거부가
        # 첫 번째 것에 가려진다).
        # 이슈 #235: per-line 분류는 세션의 마지막 result 줄에만 실리는
        # permission_denials 로 상관돼야 한다(Claude Code 스트림에서 result
        # 는 항상 맨 끝 줄) — 그 전까지는 emit 하지 않고 여기 모아 둔다.
        # is_error 는 "이 도구 호출이 실패했다"지 "거부됐다"가 아니라는
        # 구분이 결함의 뿌리였다(제안서 요구사항 1). 값은 이제
        # (이벤트 타입, detail, tool_name) — tool_name 은 이슈 #246 결함 3의
        # 건별 상관관계에 쓰인다(아래 tool_use_names).
        pending_refusals: dict = {}
        # 이슈 #246 결함 3: 각 tool_use 블록의 id -> name — 뒤이어 오는
        # tool_result 블록의 tool_use_id 를 통해 어느 도구 호출이 거부됐는지
        # 건별로 되짚는다. 두 필드 모두 이미 파싱 중인 스트림에 있던 것이라
        # 새 계측이 아니다(제안서 제약).
        # 이슈 #558: 값이 name 단독에서 (name, command) 로 바뀌었다 — Bash
        # 블록이면 command, 아니면 None. 이미 진행 리포팅(아래 elif name ==
        # "Bash")이 뽑던 값을 재사용한다.
        tool_use_names: dict[str, tuple[str, str | None]] = {}
        # 이슈 #246 결함 1: 터미널 result 줄을 실제로 파싱했는지 — 스트림이
        # 그 줄 전에 끝나면(크래시/kill/truncation, S1) 또는 그 줄이 malformed
        # JSON 이면(S3, 위의 `except ValueError: continue`) 이 플래그는 False 로
        # 남고, 루프가 끝난 뒤 남은 pending_refusals 를 unverified-refusal 로
        # 대신 flush 한다.
        result_seen = False
        # A URL the session **read** is indistinguishable from a PR it
        # **opened** unless the owner/repo is checked: octocat/Hello-World/pull/1
        # is GitHub's own documentation example and appears in gh help output.
        # 실측 2026-07-30 — 그 URL 하나로 pr-opened 가 서고 스폰이 조기 복귀했다
        # (이슈 #142). origin 을 못 읽으면 접두사는 None 이고 예전처럼 전부 받는다.
        pr_prefix = _origin_pr_prefix(cwd) if issue is not None else None
        # br 의 실제(또는 과거) PR 번호를 세션당 한 번만 gh 로 풀고 메모이즈한다.
        # 후보 URL 마다 부르면 gh 서브프로세스가 후보 수만큼 뜨고, 이 호출이
        # `for line in proc.stdout:` 루프 안이라 gh 가 네트워크에서 블록하는
        # 동안 세션의 stdout 파이프가 차면 세션 자신이 멈춘다 — _pr_for_branch
        # 는 URL 이 아니라 브랜치의 함수라 세션 안에서 값이 같다(PR #184 리뷰).
        # PR 이 아직 없으면(None) 다음 후보에서 다시 풀어, 일시적 gh 실패 후
        # 재시도 성질은 유지한다.
        pr_number: int | None = None
        # 연속으로 같은 file_path 에 나는 Write/Edit progress 를 억제하는
        # 상태 — 직전에 기록한 progress 이벤트의 file_path(Write/Edit 가
        # 아니었으면 None)를 들고 있는다.
        last_progress_file: str | None = None
        with open(log_path, "w", encoding="utf-8") as lf:
            for line in proc.stdout:
                lf.write(line)
                lf.flush()
                if issue is not None:
                    for m in _PR_URL_RE.findall(line):
                        if pr_prefix and not m.startswith(pr_prefix):
                            continue
                        if m in pr_seen:
                            continue
                        if pr_number is None:
                            pr_number = _open_pr_for_branch(Path(cwd), br)
                        if pr_number is not None and int(m.rsplit("/", 1)[-1]) == pr_number:
                            pr_seen.add(m)
                            _append_event(events_path, "pr-opened", m)
                            if issue is not None:
                                # 이슈 #782: 이벤트 채널이 완료를 확정적으로
                                # 안 순간 원장에 찍어 둔다 — 뒤이은 폴링
                                # 틱의 ledger_check_and_stamp() 가 같은 키를
                                # 보면 TTL 안이라 조용히 넘어간다(Acceptance
                                # test 2).
                                ledger_stamp(
                                    f"health-repair:{issue}:{role}:pr-expected-missing")
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                if obj.get("type") == "result":
                    result = obj
                    # `result` 줄은 "언제나 스트림의 마지막 줄"이라고 문서화만
                    # 돼 있을 뿐 강제되지 않는다(이슈 #235 실행-관찰 연구,
                    # research-evidence.md:160-164) — 두 번째 `result` 줄이
                    # 오면 result_seen 이 이미 True 라 이 블록을 건너뛰어
                    # pending_refusals 를 다시 flush 하지 않는다. 옛
                    # refusals_seen 집합이 세션 전체에 걸쳐 지녔던 "한 번만
                    # flush" 성질을 대신한다(이슈 #246 헌트 finding 5).
                    if not result_seen:
                        result_seen = True
                        if issue is not None:
                            raw_denials = result.get("permission_denials")
                            if isinstance(raw_denials, list):
                                # 확정된 리스트(비었을 수도 있음) — 이슈 #246
                                # 결함 3: 후보마다 tool_name 으로 건별 상관시킨다.
                                _flush_correlated_refusals(events_path, pending_refusals,
                                                           raw_denials)
                            else:
                                # 이슈 #246 결함 1 (S2): permission_denials 가
                                # absent/None/truthy-non-list — 형태를 신뢰할
                                # 수 없다. 상관은 시도하지 않고 이미 분류된
                                # 후보를 unverified-refusal 로 정직하게
                                # 남긴다.
                                _flush_unverified(events_path, pending_refusals)
                elif issue is not None and obj.get("type") == "user":
                    for block in (obj.get("message") or {}).get("content") or []:
                        if not isinstance(block, dict) or block.get("type") != "tool_result":
                            continue
                        if not block.get("is_error"):
                            continue
                        text = _tool_result_text(block.get("content"))
                        tool_use_id = block.get("tool_use_id")
                        name_cmd = (tool_use_names.get(tool_use_id)
                                   if isinstance(tool_use_id, str) else None)
                        tool_name, tool_command = name_cmd if name_cmd else (None, None)
                        classified = _classify_refusal_text(text, command=tool_command)
                        if classified is None:
                            continue
                        ev_type, key, detail = classified
                        if key not in pending_refusals:
                            pending_refusals[key] = (ev_type, detail, tool_name)
                elif issue is not None and obj.get("type") == "assistant":
                    # gate-refusal/pr-opened 와 같은 파싱 결과(obj)를 재사용한다
                    # — 이 줄에 대해 json.loads 를 두 번 부르지 않는다.
                    for block in (obj.get("message") or {}).get("content") or []:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        name = block.get("name")
                        inp = block.get("input") or {}
                        command = str(inp.get("command") or "") if name == "Bash" else None
                        # 이슈 #246 결함 3: 이 tool_use 의 id -> (name, command) 를
                        # 기록해 둔다 — 뒤이어 올 tool_result 의 tool_use_id 가
                        # 이걸 통해 어느 도구 호출이 거부됐는지 되짚는다.
                        # Write/Edit/Bash 로 좁히지 않고 전부 기록한다(진행
                        # 리포팅과 달리 상관관계는 모든 도구가 대상). command 는
                        # 이슈 #558: Bash 가 아니면 None.
                        block_id = block.get("id")
                        if isinstance(block_id, str) and isinstance(name, str):
                            tool_use_names[block_id] = (name, command)
                        if name in ("Write", "Edit"):
                            fp = inp.get("file_path")
                            if fp and fp != last_progress_file:
                                last_progress_file = fp
                                _append_event(events_path, "progress",
                                             {"kind": "tool_use", "detail": f"{name} {fp}"})
                        elif name == "Bash":
                            if command.startswith(_PROGRESS_BASH_PREFIXES):
                                last_progress_file = None
                                _append_event(events_path, "progress",
                                             {"kind": "tool_use",
                                              "detail": f"{command[:60]} 실행"})
        if issue is not None and not result_seen and pending_refusals:
            # 이슈 #246 결함 1 (S1/S3): 스트림이 result 줄 없이 EOF 에
            # 닿았다(크래시/kill/truncation, 또는 터미널 줄 자체가 malformed
            # JSON) — 이미 층 분류된 후보를 잃지 않고 unverified-refusal 로
            # 남긴다.
            _flush_unverified(events_path, pending_refusals)
        rc = proc.wait()
        roster_remove(roster_key)
    finally:
        if not is_parent_return:
            os.unlink(settings)
    if result.get("result"):
        print(result["result"])                  # 세션의 마지막 답 — 기존 UX
    elif not result:
        print(f"[{role}] 결과 이벤트를 받지 못했다 — 라이브 로그를 봐라: {log_path}",
              file=sys.stderr)

    after = board_snapshot(cwd)
    delta = sorted(p for p in set(before) | set(after)
                   if before.get(p) != after.get(p))
    # 사람 게이트에 막힌 줄을 자동으로 판별하던 표는 없다(이슈 #120) —
    # classify() 는 이제 이 경로로는 waiting-on-human 을 못 낸다.
    blocked: list = []

    uncommitted = []
    after_head = None
    if issue is not None:
        after_head = _git_head(cwd)
        st = subprocess.run(["git", "-C", cwd, "status", "--porcelain"],
                            capture_output=True, text=True)
        uncommitted = [l for l in st.stdout.splitlines() if l.strip()]
        if uncommitted:
            print(f"[{role}] 세션이 미커밋 변경 {len(uncommitted)}건을 남기고 "
                  f"끝났다 — 커밋되지 않은 작업은 PR 에 존재하지 않는다. "
                  f"같은 이슈로 재스폰하면 이 워크스페이스를 이어받아 커밋부터 "
                  f"끝낼 수 있다:\n  " + "\n  ".join(uncommitted[:10]),
                  file=sys.stderr)
        try:
            push_result = ensure_pushed(cwd, issue, role)
        finally:
            # ensure_pushed() 안의 `gh`/`git` 호출이 예외를 던져도(이슈 #719
            # hunt: gh 바이너리 부재 등) 클레임은 반드시 풀려야 한다 — 안
            # 그러면 release 지점을 여기로 늦춘 바로 그 변경이 클레임을
            # stale-timeout 까지 새게 만드는 회귀가 된다.
            _release_spawn_claim(cwd, os.getpid())
    else:
        push_result = None
    gates = gate_report(cwd) + ownership_report(cwd, role, delta)
    outcome = classify(rc, result, delta, blocked)
    if outcome == "silent-failure" and uncommitted:
        outcome = "uncommitted-work"
    elif outcome == "silent-failure" and push_result and push_result["status"] == "push-rejected":
        outcome = "push-rejected"
        print(f"[{role}] 호스트 push 가 거부됐다 — 커밋은 로컬에 있다: "
              f"{push_result['reason']}", file=sys.stderr)
    new_commit = issue is not None and _is_new_commit(cwd, before_head, after_head)
    already_delivered = False
    push_succeeded = push_result is not None and push_result["status"] not in (
        "push-rejected", "pr-create-failed")
    if issue is not None and not blocked and not new_commit:
        branch = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True).stdout.strip()
        if branch:
            already_delivered = _pr_open_or_merged_for_branch(Path(cwd), branch) is not None
    downgraded = fail_closed_downgrade(outcome, issue, blocked, new_commit, uncommitted,
                                       already_delivered, push_succeeded)
    if downgraded != outcome:
        if downgraded == "progressed-dirty-tree":
            print(f"[{role}] 페일-클로즈드: progressed 로 자기보고 했고 새 "
                  f"커밋도 있지만(before {before_head}, after {after_head}) "
                  f"워크스페이스에 미커밋 변경 {len(uncommitted)}건이 남았다 — "
                  f"{outcome} 를 progressed-dirty-tree 로 표기한다. 기대한 것: "
                  f"이 세션이 끝나기 전에 트리까지 clean. 관찰한 것: 커밋은 "
                  f"있으나 더러운 트리.",
                  file=sys.stderr)
        elif outcome == "silent-failure" and downgraded == "progressed":
            reason = ("이미 브랜치에 open/merged PR 이 있다" if already_delivered
                      else "새 커밋이 push 됐다")
            print(f"[{role}] silent-failure 로 자기보고 됐지만 관측된 git/PR "
                  f"상태가 배달을 보여준다({reason}) — {outcome} 를 progressed "
                  f"로 끌어올린다. 기대한 것: docs 보드 델타로 성공을 포착. "
                  f"관찰한 것: 델타는 없지만 실제로는 배달됨.",
                  file=sys.stderr)
        else:
            print(f"[{role}] 페일-클로즈드: progressed 로 자기보고 했지만 "
                  f"새 커밋이 없고(before {before_head}, after {after_head})"
                  + (f" 미커밋 변경 {len(uncommitted)}건도 남았다" if uncommitted else "")
                  + f" — {outcome} 를 failed-no-commit 으로 깎는다. 기대한 것: "
                  f"이 세션이 끝나기 전에 실제 커밋. 관찰한 것: 커밋 없음"
                  + (" + 더러운 트리" if uncommitted else "") + ".",
                  file=sys.stderr)
        outcome = downgraded
    denials = result.get("permission_denials") or []
    ledger_write({
        "ts": int(time.time()), "role": role, "cwd": str(Path(cwd).resolve()),
        "repo": _repo_name(Path(cwd).resolve()),
        "session_id": result.get("session_id"),
        "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"), "rc": rc, "outcome": outcome,
        "board_delta": delta, "denials": len(denials),
        "duration_s": round(time.monotonic() - t0, 1),
        "rulebook": rulebook_desc,
        "core": core_version(),
        "gates": gates,
        "log": str(log_path),
        "push_reason": push_result.get("reason") if push_result else None,
        "skill_judge_outcome": skill_judge_outcome,
    })

    for line in gates:
        print(line, file=sys.stderr)
    print(f"[{role}] {outcome}"
          + (f", 보드 변화 {len(delta)}건" if delta else ", 보드 무변화")
          + (f", 비용 ${result.get('total_cost_usd'):.2f}"
             if isinstance(result.get("total_cost_usd"), (int, float)) else ""),
          file=sys.stderr)
    sid = f" (session {result.get('session_id')})" if result.get("session_id") else ""
    if denials:
        print(f"[{role}] 거부된 도구 호출 {len(denials)}건 — 게이트가 막았거나 "
              f"답할 사람이 없어 거부됐다. 무엇을 막았는지는 세션 출력에 있다",
              file=sys.stderr)
    if outcome == "refused":
        print(f"[{role}] 게이트가 막아서 보드가 안 바뀌었다 — 이건 실패가 아니라 "
              f"규칙이 지켜진 것일 수 있다. 위 거부 사유를 읽고 맡길 일을 "
              f"고쳐서 다시 띄워라{sid}", file=sys.stderr)
    if outcome == "silent-failure":
        print(f"[{role}] exit 0 인데 보드도 안 바뀌고 막힌 것도 없다 — 성공이 "
              f"아니라 실측된 침묵-사망 모드다. 세션 로그를 확인하라{sid}",
              file=sys.stderr)
    if outcome == "refused-null-result":
        print(f"[{role}] 등록된 REFUSAL 어휘로 무결과를 선언하고 끝났다 — "
              f"커밋/보드 델타가 없어도 이건 실패가 아니라 정직한 거부다"
              f"(이슈 #476 round 3, candidate E){sid}", file=sys.stderr)
    if bounded and issue is not None:
        # 자식(detach 된 프로세스)만 여기 닿는다 — 부모는 이미 fork 직후
        # _await_bounded 에서 리턴했다. session-end 를 self-trigger 보다
        # **먼저** 남긴다(이슈 #247 hunt finding 1). self-trigger 가 상한
        # 안이면 `_respawn_or_cap()` -> `_spawn_one(..., bounded=True)` 를
        # 재귀 호출하는데, 그 재귀 호출은 새 세대가 자기 `session-start` 를
        # 남길 때까지 `_await_bounded()` 에서 이 프로세스 자신을 블록한다.
        # session-end 를 그 뒤로 미루면(제안서의 원래 문구가 그랬다) 이
        # 세션 자신의 session-end 가 events.jsonl 에 새 세대의 session-start
        # **뒤에** 찍힌다 — `session_end_verdict()` 는 마지막
        # session-start(새 세대의 것) 뒤에 session-end 가 있는지만 보므로,
        # 이 순서에서는 그 자리에 남의(이 세션 자신의) session-end 를 보고
        # 새 세대가 진짜 죽어도 영원히 `normal` 로 오판한다 — 이 이슈가
        # 넓히려는 바로 그 안전망이 재귀 지점에서 스스로 꺼진다(실측:
        # 어써샬-브로큰 헌트, 실제 재귀 이벤트 시퀀스로 재현). 먼저
        # session-end 를 남기면 새 세대의 session-start 가 이 세션 자신의
        # session-end **뒤에** 오므로 그 오판이 구조적으로 불가능해진다.
        push_reason = push_result.get("reason") if push_result else None
        _append_event(events_path, "session-end",
                      {"outcome": outcome, "reason": push_reason}
                      if push_reason is not None else outcome)
        # 이슈 #782: session-end 를 이미 확정적으로 아는 순간 원장에 찍는다
        # — 뒤이은 폴링 틱이 이 세션을 죽었다고(DEAD-ERRORED/session-crashed)
        # 다시 보고하지 않게 한다(Acceptance test 2/3).
        ledger_stamp(f"health-repair:{issue}:{role}:session-crashed")
        ledger_stamp(f"health:{issue}:{role}:DEAD-ERRORED")
        # 이슈 #534: session-end 직후, self-trigger 재스폰과 같은 자리에서
        # durable 코멘트도 남긴다 — roster_watchdog() 틱이 이 엔트리를 볼
        # 무렵엔 roster_remove()(spawn.py:3988)가 이미 지워버린 뒤라
        # _self_trigger_respawn()과 같은 dead-entry-invisible 레이스를
        # 그대로 겪는다.
        _post_session_end_comment(Path(cwd), issue, roster_key, cwd, str(log_path))
        _self_trigger_respawn(outcome, roster_key, cwd, issue, role,
                              str(log_path), session_start_ts)
        os._exit(rc if isinstance(rc, int) else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
