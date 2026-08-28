#!/usr/bin/env python3
"""스킬 조합으로 에이전트를 띄운다. on-the-record 의 핵심 동작 하나.

이슈 #2572: 유일한 스폰 형태는 `--skills` 다 — 역할-포지셔널 스폰
(`spawn.py implementation "<task>"`)과 맨 태스크 스폰(`spawn.py "<task>"`,
이슈 #2555)은 은퇴했고 둘 다 `--skills` 를 이름하는 메시지로 거절된다.

  python3 spawn.py --skills <스킬>[,<스킬>...] "<맡길 일>" --issue <n> [-C <작업 디렉터리>] [--dry-run]
  python3 spawn.py --skills conformance-review-verdict-assignment "PR 12 를 리뷰해라" --issue 12
  python3 spawn.py --skills testing "/testrun:testrun smoke" --issue 34 -C ~/work/some-repo

**왜 스크립트가 필요한가**: `--settings` 는 덮어쓰기가 아니라 **병합**이다. 스킬
세션 설정에 qa 플러그인만 적어도 사용자 전역 설정의 플러그인 17개가 그대로 딸려온다 —
"코딩 에이전트가 qa 룰북까지 본다"는 원래 문제의 다른 얼굴이다. 전역 목록을 읽어
스킬이 켜지 않은 것을 전부 `false` 로 덮어야 격리가 성립한다(실측 확인).

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
import shutil
import signal
import stat
import string
import subprocess
import sys
import threading
import traceback
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _derive_slug_from_task(task_text: str) -> str:
    """Issue #2555 (Step C): derive a branch/record-filename-safe slug from
    bare task text, when `spawn.py "<task>"` is called with no role/slug
    positional at all.

    Deterministic on `task_text` alone -- a respawn into the same
    workspace must land on the same branch/record (docs/issue-2548/
    reports/architecture.md, Identity section: "appending a fresh
    disambiguator on every spawn would change the branch/filename on
    every retry of the same work unit"), so this cannot mint a random
    disambiguator the way `roster.new_lease_disambiguator()` does for the
    skill axis. Task text is free-form (often Korean, often long) and a
    branch/filename slug is one `^issue-[^/]+/([^/]+)$` path segment, so
    an ASCII-only prefix is trimmed off for readability and an 8-hex-char
    digest of the full text is always appended -- the digest alone
    carries uniqueness/determinism; the prefix is a human hint only."""
    ascii_part = re.sub(r"[^a-z0-9]+", "-", task_text.strip().lower()).strip("-")
    digest = hashlib.sha1(task_text.encode("utf-8")).hexdigest()[:8]
    return f"{ascii_part[:40].strip('-')}-{digest}" if ascii_part else digest


# issue #2348: hook-fires/deviation-log per-session sharding -- both are
# standalone leaf modules (no callback into spawn.py), so no `_sp`
# injection is needed the way consult.py/roster.py/lifecycle.py require.
import deviation_log
import hook_fires
_hook_fires_aggregate = hook_fires._hook_fires_aggregate
_deviation_log_aggregate = deviation_log._deviation_log_aggregate
_deviation_log_path = deviation_log._deviation_log_path

# issue #2637: docs/reports/product/priorities.md per-entry sharding, same
# conflict-elimination shape as the two imports above -- see priorities.py's
# module docstring.
import priorities
_priorities_aggregate = priorities.priorities_aggregate
_priorities_entry_path = priorities._priorities_entry_path

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
_roster_load_checked = roster._roster_load_checked
_claim_only_live_sessions = roster._claim_only_live_sessions
_roster_save = roster._roster_save
_roster_own = roster._roster_own
_watcher_looks_real = roster._watcher_looks_real
_alive = roster._alive
lease_key = roster.lease_key
new_lease_disambiguator = roster.new_lease_disambiguator
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
spawn_attempt_sweep = roster.spawn_attempt_sweep
SPAWN_ATTEMPT_GRACE_SEC = roster.SPAWN_ATTEMPT_GRACE_SEC
_surface_approval_wait = roster._surface_approval_wait
APPROVAL_WAIT_EXPIRING_FRACTION = roster.APPROVAL_WAIT_EXPIRING_FRACTION
APPROVAL_WAIT_LEDGER_TTL_SEC = roster.APPROVAL_WAIT_LEDGER_TTL_SEC
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
WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD = watchdog.WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD
_watchdog_noise_state_path = watchdog._watchdog_noise_state_path
_load_watchdog_noise_state = watchdog._load_watchdog_noise_state
_save_watchdog_noise_state = watchdog._save_watchdog_noise_state
_watchdog_note_gh_failure = watchdog._watchdog_note_gh_failure
_watchdog_note_unmappable_pr = watchdog._watchdog_note_unmappable_pr
_watchdog_note_unmappable_subject_branch = watchdog._watchdog_note_unmappable_subject_branch
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
_count_structural_delegations = events._count_structural_delegations
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
_SKILL_JUDGE_PERF_MIN_EVENTS = consult._SKILL_JUDGE_PERF_MIN_EVENTS
_MIN_PLAUSIBLE_JUDGE_WALL_S = consult._MIN_PLAUSIBLE_JUDGE_WALL_S
_LEDGER_TAIL_READ_BYTES = consult._LEDGER_TAIL_READ_BYTES
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
_composed_consult_skill_source = consult._composed_consult_skill_source
_compress_diff = consult._compress_diff
_consult_background_log_path = consult._consult_background_log_path
_consult_cmd_and_env = consult._consult_cmd_and_env
_consult_evidence_suffix = consult._consult_evidence_suffix
_consult_log_aggregate = consult._consult_log_aggregate
_consult_or_record_error = consult._consult_or_record_error
_consult_root = consult._consult_root
_consult_session_shard_id = consult._consult_session_shard_id
_consult_trace_dir = consult._consult_trace_dir
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
_skill_judge_p90_cutoff = consult._skill_judge_p90_cutoff
_skill_judge_perf_samples = consult._skill_judge_perf_samples
_skill_judge_timeout = consult._skill_judge_timeout
_percentile = consult._percentile
_verb_cmd = consult._verb_cmd
consult_cmd = consult.consult_cmd
draft_cmd = consult.draft_cmd
ideate_cmd = consult.ideate_cmd
judge_cmd = consult.judge_cmd
panel_cmd = consult.panel_cmd
review_cmd = consult.review_cmd

# Issue #2105 extraction 7/N (a): the skill-resolution machinery lives in
# skills.py. Same mechanism as the six extractions above: spawn.py stays
# the entry point and re-exports the moved names; skills.py resolves every
# cross-module reference through the module object injected here, so
# `mock.patch.object(spawn, ...)` patches stay visible to the moved code.
import skills
if skills._sp is None or __name__ in ("spawn", "__main__"):
    skills._sp = sys.modules[__name__]
_STATIC_POLICY_SKILLS = skills._STATIC_POLICY_SKILLS
_available_skills_clause = skills._available_skills_clause
_carries_hooks = skills._carries_hooks
_core_candidates = skills._core_candidates
_describe_skill_match = skills._describe_skill_match
_installed_plugin_skill_dirs = skills._installed_plugin_skill_dirs
_local_skill_dirs = skills._local_skill_dirs
_role_source_roster_fields = skills._role_source_roster_fields
_skill_content_hash = skills._skill_content_hash
_skill_identity_key = skills._skill_identity_key
_skill_repo_managed_root = skills._skill_repo_managed_root
_skill_repo_root = skills._skill_repo_root
_skill_repo_valid = skills._skill_repo_valid
_skill_roster_fields = skills._skill_roster_fields
_skill_source_roster_row = skills._skill_source_roster_row
_split_skill_qualifier = skills._split_skill_qualifier
_collapse_identical_matches = skills._collapse_identical_matches
skill_branch_slug = skills.skill_branch_slug
resolve_static_policy_source = skills.resolve_static_policy_source
resolve_role_family_source = skills.resolve_role_family_source
merge_composed_skill_source = skills.merge_composed_skill_source
resolve_skill_source = skills.resolve_skill_source
resolved_skill_dirs = skills.resolved_skill_dirs
resolved_skill_sources = skills.resolved_skill_sources
skill_repo_sha = skills.skill_repo_sha

# Issue #2105 extraction 7/N (b): the reconcile-CLI / respawn / workspace
# clean-sweep + monitor-alive GC lifecycle machinery lives in lifecycle.py.
# Same mechanism again. `reconcile()`, `_build_expected`/`_build_observed`
# and `watchdog_check_one` stay here (source-pinned by gates/test_boundary.py
# and gates/test_watch_rearm_registry.py); lifecycle.py reaches them via
# the injected module object. Import-time constants moved with their users
# and are re-exported by assignment below.
import lifecycle
if lifecycle._sp is None or __name__ in ("spawn", "__main__"):
    lifecycle._sp = sys.modules[__name__]
RESPAWN_STATE = lifecycle.RESPAWN_STATE
RESPAWN_MAX_ATTEMPTS = lifecycle.RESPAWN_MAX_ATTEMPTS
RESPAWN_ABSOLUTE_MAX = lifecycle.RESPAWN_ABSOLUTE_MAX
MONITOR_ALIVE_TOUCH_CADENCE_SECONDS = lifecycle.MONITOR_ALIVE_TOUCH_CADENCE_SECONDS
MONITOR_ALIVE_STALE_THRESHOLD_SECONDS = lifecycle.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS
LEGACY_MONITOR_ALIVE_DIRNAME = lifecycle.LEGACY_MONITOR_ALIVE_DIRNAME
_ABANDONED_WORK_OUTCOMES = lifecycle._ABANDONED_WORK_OUTCOMES
_CONTINUATION_PREAMBLE = lifecycle._CONTINUATION_PREAMBLE
_CRASH_COMMENT_MARKER = lifecycle._CRASH_COMMENT_MARKER
_HARNESS_NOISE_BASENAMES = lifecycle._HARNESS_NOISE_BASENAMES
_RECORD_PATH_RE = lifecycle._RECORD_PATH_RE
_REMEDIATION_MERGE_COMMENT_MARKER = lifecycle._REMEDIATION_MERGE_COMMENT_MARKER
_SESSION_END_COMMENT_MARKER = lifecycle._SESSION_END_COMMENT_MARKER
_STALL_COMMENT_MARKER = lifecycle._STALL_COMMENT_MARKER
_auto_respawn_check = lifecycle._auto_respawn_check
_classify_workspace_completion = lifecycle._classify_workspace_completion
_clean_auto_enabled = lifecycle._clean_auto_enabled
_clean_max_age_days = lifecycle._clean_max_age_days
_clean_max_bytes = lifecycle._clean_max_bytes
_delete_workspace = lifecycle._delete_workspace
_dir_size_bytes = lifecycle._dir_size_bytes
_live_workspaces = lifecycle._live_workspaces
_live_workspaces_union = lifecycle._live_workspaces_union
_monitor_alive_root = lifecycle._monitor_alive_root
_post_crash_comment = lifecycle._post_crash_comment
_post_session_end_comment = lifecycle._post_session_end_comment
_post_stall_comment = lifecycle._post_stall_comment
_pr_list_call_ok = lifecycle._pr_list_call_ok
_prune_orphaned_sidecars = lifecycle._prune_orphaned_sidecars
_remediation_merge_sweep = lifecycle._remediation_merge_sweep
_respawn_fingerprint = lifecycle._respawn_fingerprint
_respawn_or_cap = lifecycle._respawn_or_cap
_respawn_state_load = lifecycle._respawn_state_load
_respawn_state_save = lifecycle._respawn_state_save
_roster_reconcile_unreported = lifecycle._roster_reconcile_unreported
_self_trigger_respawn = lifecycle._self_trigger_respawn
_sibling_checkout_roots = lifecycle._sibling_checkout_roots
_sibling_live_sessions = lifecycle._sibling_live_sessions
_sidecar_workspace_name = lifecycle._sidecar_workspace_name
_workspace_base = lifecycle._workspace_base
_workspace_clean_state = lifecycle._workspace_clean_state
_workspace_merge_trigger_status = lifecycle._workspace_merge_trigger_status
auto_sweep = lifecycle.auto_sweep
detect_legacy_monitor_alive_dirs = lifecycle.detect_legacy_monitor_alive_dirs
gc_monitor_alive = lifecycle.gc_monitor_alive
monitor_alive_gc_cli = lifecycle.monitor_alive_gc_cli
roster_clean = lifecycle.roster_clean
roster_kill = lifecycle.roster_kill

# Issue #2105 extraction 8/N: board/approval/lint/report/session-verdict
# machinery lives in board.py. Same mechanism as extractions 1-7 above:
# spawn.py stays the entry point and re-exports the moved names; board.py
# resolves every cross-module reference through the injected module object,
# so `mock.patch.object(spawn, ...)` patches stay visible to the moved code.
import board as _board_mod
if _board_mod._sp is None or __name__ in ("spawn", "__main__"):
    _board_mod._sp = sys.modules[__name__]
_approvers = _board_mod._approvers
_base = _board_mod._base
_format_roster_row = _board_mod._format_roster_row
_front_role = _board_mod._front_role
_is_new_commit = _board_mod._is_new_commit
_ledger_log_outcomes = _board_mod._ledger_log_outcomes
_merged_pr_for_branch = _board_mod._merged_pr_for_branch
_null_result_declared = _board_mod._null_result_declared
_open_pr_for_branch = _board_mod._open_pr_for_branch
_pr_for_branch = _board_mod._pr_for_branch
_pr_open_or_merged_for_branch = _board_mod._pr_open_or_merged_for_branch
_record_upstream = _board_mod._record_upstream
_recovery_policy_module = _board_mod._recovery_policy_module
_session_commit_count = _board_mod._session_commit_count
approve_scope = _board_mod.approve_scope
board = _board_mod.board
_skill_axis_report_names = _board_mod._skill_axis_report_names
_lease_slugs_for_issue = _board_mod._lease_slugs_for_issue
_issue_num = _board_mod._issue_num
board_snapshot = _board_mod.board_snapshot
classify = _board_mod.classify
fail_closed_downgrade = _board_mod.fail_closed_downgrade
frontmatter = _board_mod.frontmatter
gate_report = _board_mod.gate_report
init_board = _board_mod.init_board
init_requirement_digest = _board_mod.init_requirement_digest
lint_issue = _board_mod.lint_issue
ownership_report = _board_mod.ownership_report
require_acceptance_gate = _board_mod.require_acceptance_gate
require_board = _board_mod.require_board
require_no_repo_config = _board_mod.require_no_repo_config
require_repo_root = _board_mod.require_repo_root
require_requirement_linkage = _board_mod.require_requirement_linkage
roster_ps = _board_mod.roster_ps
session_end_verdict = _board_mod.session_end_verdict
session_result = _board_mod.session_result
slug = _board_mod.slug
status = _board_mod.status

# Issue #2105 extraction 8/N: spawn-pipeline machinery (settings/rulebook/
# core resolution, spawn_cmd, issue workspace + checkout/bootstrap,
# directive-assembly helpers, admission) lives in pipeline.py. Same
# mechanism as above.
import pipeline as _pipeline_mod
if _pipeline_mod._sp is None or __name__ in ("spawn", "__main__"):
    _pipeline_mod._sp = sys.modules[__name__]
_admission_check_approve_token = _pipeline_mod._admission_check_approve_token
_admission_check_board_validity = _pipeline_mod._admission_check_board_validity
_board_marker_probe = _pipeline_mod._board_marker_probe
_admission_check_budget_caps = _pipeline_mod._admission_check_budget_caps
_admission_check_degenerate_task = _pipeline_mod._admission_check_degenerate_task
_admission_check_directive_completeness = _pipeline_mod._admission_check_directive_completeness
_admission_check_watch_registration = _pipeline_mod._admission_check_watch_registration
_artifact_smoke_task_lines = _pipeline_mod._artifact_smoke_task_lines
_bootstrap_timing_line = _pipeline_mod._bootstrap_timing_line
_claude_version = _pipeline_mod._claude_version
_cross_family_candidate_corpus = _pipeline_mod._cross_family_candidate_corpus
_fetch_or_halt = _pipeline_mod._fetch_or_halt
_goal_pin_block = _pipeline_mod._goal_pin_block
_locked_rulebook_dir = _pipeline_mod._locked_rulebook_dir
_mark_pulled = _pipeline_mod._mark_pulled
_migrate_legacy_ttl_marker = _pipeline_mod._migrate_legacy_ttl_marker
_mkt = _pipeline_mod._mkt
_pull_is_fresh = _pipeline_mod._pull_is_fresh
_report_managed_clone_staleness = _pipeline_mod._report_managed_clone_staleness
_resolve_session_max_turns = _pipeline_mod._resolve_session_max_turns
_rulebook_lock_path = _pipeline_mod._rulebook_lock_path
_rulebook_ttl_min = _pipeline_mod._rulebook_ttl_min
_session_log_path = _pipeline_mod._session_log_path
_skill_trigger_line = _pipeline_mod._skill_trigger_line
_skill_frontmatter = _pipeline_mod._skill_frontmatter
_skill_frontmatter_description = _pipeline_mod._skill_frontmatter_description
_skill_frontmatter_axis = _pipeline_mod._skill_frontmatter_axis
_skill_bm25_document = _pipeline_mod._skill_bm25_document
_skill_declared_phrases = _pipeline_mod._skill_declared_phrases
_timed = _pipeline_mod._timed
_tokenize = _pipeline_mod._tokenize
_ttl_marker = _pipeline_mod._ttl_marker
_verify_branch_base_sane = _pipeline_mod._verify_branch_base_sane
_workspace_bash_allow = _pipeline_mod._workspace_bash_allow
_write_role_sidecar = _pipeline_mod._write_role_sidecar
admission_gate = _pipeline_mod.admission_gate
bootstrap_fetch_and_record_sha = _pipeline_mod.bootstrap_fetch_and_record_sha
checkout_issue_branch = _pipeline_mod.checkout_issue_branch
checkout_issue_branch_for_skill = _pipeline_mod.checkout_issue_branch_for_skill
_checkout_named_branch = _pipeline_mod._checkout_named_branch
core_plugin_dirs = _pipeline_mod.core_plugin_dirs
core_root = _pipeline_mod.core_root
core_version = _pipeline_mod.core_version
ensure_target_remote = _pipeline_mod.ensure_target_remote
get_bootstrap_fetch_record = _pipeline_mod.get_bootstrap_fetch_record
positive_int = _pipeline_mod.positive_int
read_role_model_config = _pipeline_mod.read_role_model_config
recut_if_absorbed_cli = _pipeline_mod.recut_if_absorbed_cli
recut_corrupted_cli = _pipeline_mod.recut_corrupted_cli
require_doctor = _pipeline_mod.require_doctor
resolved_role_model = _pipeline_mod.resolved_role_model
role_settings = _pipeline_mod.role_settings
self_hosted_hooks = _pipeline_mod.self_hosted_hooks
spawn_cmd = _pipeline_mod.spawn_cmd
await_approval_cmd = _pipeline_mod.await_approval_cmd
_checkpoint_poll_seconds = _pipeline_mod._checkpoint_poll_seconds
_checkpoint_wait_max_seconds = _pipeline_mod._checkpoint_wait_max_seconds
AWAIT_APPROVAL_TIMEOUT_RC = _pipeline_mod.AWAIT_APPROVAL_TIMEOUT_RC

import directive_assembly
if directive_assembly._sp is None or __name__ in ("spawn", "__main__"):
    directive_assembly._sp = sys.modules[__name__]
_CHECKPOINT_CONTRACT_BLOCK = directive_assembly._CHECKPOINT_CONTRACT_BLOCK
_checkpoint_contract_block = directive_assembly._checkpoint_contract_block
_checkpoint_index_block = directive_assembly._checkpoint_index_block
DIRECTIVE_DIR = directive_assembly.DIRECTIVE_DIR
DEFAULT_SESSION_MAX_TURNS = directive_assembly.DEFAULT_SESSION_MAX_TURNS
_COMPLETION_PROSE = directive_assembly._COMPLETION_PROSE
_LANDING_BATCHING_PROSE = directive_assembly._LANDING_BATCHING_PROSE
_TURN_BUDGET_PROSE = directive_assembly._TURN_BUDGET_PROSE
_REPO_DISCOVERY_PROSE = directive_assembly._REPO_DISCOVERY_PROSE
_KNOWN_PATHS_PROSE = directive_assembly._KNOWN_PATHS_PROSE
_TASK_LOOKUP_PROSE = directive_assembly._TASK_LOOKUP_PROSE
_HOOK_CONTRACT_PROSE = directive_assembly._HOOK_CONTRACT_PROSE
_SKILL_CHECK_PROSE = directive_assembly._SKILL_CHECK_PROSE
_SKILL_VERDICT_PROSE = directive_assembly._SKILL_VERDICT_PROSE
directive_section_files = directive_assembly.directive_section_files
materialize_directive_sections = directive_assembly.materialize_directive_sections
_directive_system_prompt_block = directive_assembly._directive_system_prompt_block
_stamp_additive_record_fields = directive_assembly._stamp_additive_record_fields
write_record_skeleton = directive_assembly.write_record_skeleton
composition_breakdown = directive_assembly.composition_breakdown
_SKILL_USE_SENTENCE_RE = directive_assembly._SKILL_USE_SENTENCE_RE
_TOKEN_RE = directive_assembly._TOKEN_RE
_STOPWORDS = directive_assembly._STOPWORDS
_CROSS_FAMILY_CONSULT_TOPN = directive_assembly._CROSS_FAMILY_CONSULT_TOPN
# 이슈 #2507: 고정 role->skill 표 은퇴 이후 cross_family 매치가 스폰의
# 유일한 과제-맞춤 스킬 소스가 됐다 — 예전 add-only 층의 기본값(k=2)은
# "표 위에 조금 더 얹는" 용도였지, "표를 대체하는" 용도가 아니었다. 옛
# `_ROLE_SKILLS` 항목 길이 분포(1~10, 중앙값 근처)에 맞춰 5로 올린다.
_COMPOSED_SKILLS_TOPK = 5
_bm25_cross_family_scores = directive_assembly._bm25_cross_family_scores
_cross_family_skill_matches = directive_assembly._cross_family_skill_matches

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

# 이슈 #2417: 호스트 디스크/inode 고갈은 on-the-record 소관 밖이다 — 실측
# 워크스페이스 25개, 50~121MB (평균 ~60MB, 이슈에 적힌 ~119MB 는 상한 근처
# 값). clone 을 실제로 시도하기 전에 여유 바이트/inode 를 한 번 확인해,
# 실패가 "origin 불일치"/파묻힌 git 에러/watchdog rc=97 로 흩어지는 대신
# 바로 원인을 이름 붙여 거부한다. 임계값 = 워크스페이스 하나 상한(~119MB)
# 의 3배 — 동시 스폰 여러 개가 같은 틱에 클론해도 헤드룸이 남게. 알고
# 진행하려는 컨슈머는 MUSTER_SKIP_SPACE_CHECK=1 로 끄거나
# MUSTER_MIN_FREE_BYTES/MUSTER_MIN_FREE_INODES 로 임계값 자체를 바꾼다.
MIN_FREE_BYTES_DEFAULT = 3 * 119 * 1024 * 1024   # ~357MB
MIN_FREE_INODES_DEFAULT = 1000


def _spawn_capacity_check(path) -> None:
    """`path` 아래 clone 을 시도하기 전에 여유 바이트/inode 를 확인한다
    (이슈 #2417). 부족하면 clone 근처도 안 가고 거부한다 — 메시지는 여유량과
    임계값을 이름으로 남긴다. `path` 자체가 아직 없으면(신규 워크스페이스
    디렉터리) 존재하는 조상 디렉터리로 올라가서 잰다."""
    if os.environ.get("MUSTER_SKIP_SPACE_CHECK", "") not in ("", "0", "false", "no", "off"):
        return
    probe = Path(path)
    while not probe.exists():
        probe = probe.parent
    try:
        usage = shutil.disk_usage(probe)
    except OSError:
        return  # 못 재면 예전처럼 fail-open — clone 자체의 에러 경로가 처리한다
    min_bytes = int(os.environ.get("MUSTER_MIN_FREE_BYTES", MIN_FREE_BYTES_DEFAULT))
    if usage.free < min_bytes:
        sys.exit(
            f"스폰을 거부한다: {probe} 에 여유 공간이 부족하다 "
            f"({usage.free // (1024 * 1024)}MB 가용, 임계값 {min_bytes // (1024 * 1024)}MB) "
            f"— clone 을 시도하기 전에 미리 막는다. 정책: 워크스페이스 상한 "
            f"실측치(~119MB)의 3배를 동시-스폰 헤드룸으로 둔다. 알고 진행하려면 "
            f"MUSTER_SKIP_SPACE_CHECK=1."
        )
    try:
        st = os.statvfs(probe)
    except (OSError, AttributeError):
        return
    free_inodes = st.f_favail
    min_inodes = int(os.environ.get("MUSTER_MIN_FREE_INODES", MIN_FREE_INODES_DEFAULT))
    if free_inodes and free_inodes < min_inodes:
        sys.exit(
            f"스폰을 거부한다: {probe} 에 여유 inode 가 부족하다 "
            f"({free_inodes}개 가용, 임계값 {min_inodes}개) — clone 을 시도하기 전에 "
            f"미리 막는다. 알고 진행하려면 MUSTER_SKIP_SPACE_CHECK=1."
        )


def _workspace_clone_incomplete(work: Path) -> bool:
    """`work` 에 `.git` 은 있지만 clone 이 끝까지 못 간 상태인지(ENOSPC 등으로
    중간에 죽어 partial tree 만 남은 경우) 판별한다 (이슈 #2417). HEAD 가
    가리키는 커밋이 없거나 `git status` 자체가 에러면 — 남의 레포가 아니라
    미완성 클론이다; 그 다음에 오는 origin-mismatch 판정은 여기를 통과한,
    완결된(그러나 진짜 다른) 레포에만 적용된다."""
    head = subprocess.run(["git", "-C", str(work), "rev-parse", "--verify", "-q", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return True
    status = subprocess.run(["git", "-C", str(work), "status", "--porcelain"],
                            capture_output=True, text=True)
    return status.returncode != 0


_BOOTSTRAP_TIMING: dict[str, float] = {}
# 이슈 #2186: 예전에는 workspace/branch/rulebook/core/gh_token/settings/
# cross_family 일곱 단계만 쟀다 — 그 사이(admission_gate, --skills 검증,
# returned-PR 보드 스윕, auto-sweep, 이슈 본문 fetch, 디렉티브/레코드
# 스켈레톤 쓰기, design-bearing 판정, spawn_cmd 조립, board_snapshot)에
# 아무 계측도 없는 구간이 있었고, 그 구간이 실측 스폰 하나에서 115s를
# 먹었다(스폰 발행 epoch 대비 events.jsonl 의 session-start epoch). 아래
# 아홉 단계가 그 구간을 마저 덮어, `total`이 spawn-entry-to-session-start
# 전체 구간을 (겹친 백그라운드 대기를 이중 계산하지 않고) 설명하게 한다.
_BOOTSTRAP_PHASES = ("admission", "skill_resolve", "workspace", "branch",
                     "returned_pr_gate", "auto_sweep", "rulebook", "core",
                     "gh_token", "settings", "cross_family", "issue_fetch",
                     "directive_write", "design_bearing", "spawn_cmd",
                     "board_snapshot")



# 이슈 #2560: 고정 43개 역할 이름 튜플 `ROLES`는 여기서 완전히 삭제됐다 —
# 역할/슬러그 신원은 더 이상 닫힌 집합에 속하지 않는다 (issue-2548
# architecture record, Identity/Consumers item d). 이슈 #2610: 남아있던
# 마지막 닫힌 카탈로그(44개 role 이름 -> 정의)도 삭제됐다 — 그 파일의
# 열 곳이 넘는 소비자는 전부 카탈로그 조회 없이 동작하도록 다시 짜였다.
BOARD = "docs"                          # v3: subject trees live at docs/issue-<n>/
MARKER = "docs/specs/approvers.md"      # 보드 opt-in + 승인자 allowlist (v3)
REQUIREMENT_DIGEST_MARKER = "docs/specs/requirement-digest.md"  # issue #1695
# 계약 v1 이 쓰던 자리. 아직 v2 로 안 옮긴 레포를 **말해주기 위해서만** 본다.
# 이슈 #2651: 예전엔 역할 이름 -> 파일명 dict 였다 — identity 키가 board.py 를
# 거쳐 소비자 화면에 그대로 찍혔다. 여기 필요한 건 "이 파일이 있는가"뿐이라
# identity 축을 없애고 파일명만 남긴다.
LEGACY_FILES = ("review-record.md", "feasibility-record.md", "state.md",
                "product-record.md")


REPO_CONFIG = (".claude/settings.json", ".claude/settings.local.json", ".claude/hooks",
               ".claude/agents", ".mcp.json")


_UPSTREAM_PATH = re.compile(r"^\s*-\s*path:\s*(\S+)", re.M)


# issue #476 round 3, candidate E (refusal-cost-parity). 등록된 refusal/
# null-result 어휘만 인정한다 — 자유 문장이 아니라 이 닫힌 집합과 정확히
# 일치해야 한다("REFUSAL: <state> — <reason>" 형태), 그래야 세션이
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


# 이슈 #1124: `spawn.py clean` 이 세션 로그를 지워도 되는지 판단할 때
# `fail_closed_downgrade` 가 실제로 확정하는, "커밋이 origin 에 닿았다"는
# 라벨 두 개만 "landed" 로 친다. 그 외(refused/errored/silent-failure 등)는
# 유일한 증거인 로그를 지우지 않고 archive 한다.
LANDED_OUTCOMES = {"progressed", "progressed-dirty-tree"}


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


ROSTER = STATE_ROOT / "active.json"


RECONCILE_LEDGER = ROOT / "runs" / "reconcile_ledger.json"

# 이슈 #2291: 부트스트랩(워크스페이스/로스터/세션 로그가 아직 없는) 구간의
# spawn-attempt 흔적. `STATE_ROOT`(#2240)에 앵커링 — ROSTER/DEADMAN_MARKER
# 와 같은 관례로, 이 모듈 자신의(캐치아웃) STATE_ROOT 이지 호출자가 넘긴
# 대상 레포 경로가 아니다. append-only JSONL: 프로세스가 이 구간 중
# 어디서든 죽어도(halt 든 하드 크래시든) 이미 쓴 줄은 그대로 남는다 —
# load-modify-save 였다면 그 창에서 죽었을 때 파일 자체가 손상될 수 있다.
SPAWN_ATTEMPTS_PATH = STATE_ROOT / "spawn-attempts.jsonl"


def _append_spawn_attempt_event(entry: dict) -> None:
    SPAWN_ATTEMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SPAWN_ATTEMPTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _record_spawn_attempt(issue: int | None, role: str, pid: int,
                           cwd: str | None = None) -> str | None:
    """이슈 #2291: 네트워크/워크스페이스 작업 전, spawn 시도를 durable 하게
    남긴다 — `_fetch_or_halt()`(pipeline.py) 류의 fail-closed halt 가
    stdout/stderr 로만 나가 컨슈머가 파이프(`2>&1 | tail`)로 삼켜버리면
    그 halt 는 오늘 어디에도 흔적이 없다(실측: 이슈 #2291 컨슈머 리포트).
    반환하는 attempt_id 를 `_record_spawn_outcome()`에 넘겨 이 시도의
    처분(halt 사유 또는 세션 로그 경로)을 잇는다.

    이슈 #2511: `cwd`(spawn 호출에 넘겨진 `-C` 값 그대로, 아직 검증 전)를
    같이 남긴다 — `spawn_attempt_sweep()`이 halt 사유를 클래스 분류해
    "그 조건이 지금도 살아있는가"를 다시 물을 때(`_halt_condition_cleared`)
    각 클래스가 필요로 하는 경로 근거가 이것이다. 없으면 재확인이 불가능해
    보수적으로 "아직 안 풀림"으로 남는다(아래 `_halt_condition_cleared`
    참고).

    이슈 #2393: `PYTEST_CURRENT_TEST` 가 서 있으면(pytest 가 테스트 하나를
    도는 동안 자동으로 세팅/해제 — xdist 워커에서도 마찬가지) 아예 안
    남긴다. 단위 테스트가 issue=31/7 같은 합성 값으로 `main()`/`_spawn_one()`
    을 직접 호출해(`tests/test_auto_sweep_nonblocking.py` 등, main() 은
    `MUSTER_STATE_ROOT` 격리 없이 in-process 호출됨) 이 모듈 자신의(캐치아웃)
    STATE_ROOT — 이 체크아웃의 `runs/` — 를 오염시켰다(실측: 이슈 #2393,
    285 건 중 282 건이 이 경로). 테스트가 halt 하면 pytest 자신의 출력이 이미
    그 실패를 보여주므로 durable 부트스트랩-halt 트레이스가 여기서 낼 추가
    정보가 없다 — 매 테스트 호출마다 개별 isolation(예:
    `tests/_spawn_test_support.py`의 `isolated_role_model_config()`류
    컨텍스트 매니저)을 요구하는 대신, 근원에서 한 번에 막는다: 그러면 이
    가드를 놓친 새 테스트가 미래에 같은 홍수를 재현할 길이 없다."""
    if os.environ.get("PYTEST_CURRENT_TEST") is not None:
        return None
    ts = time.time()
    attempt_id = f"{issue}:{role}:{pid}:{int(ts * 1000)}"
    _append_spawn_attempt_event({"event": "spawn_attempt", "attempt_id": attempt_id,
                                  "issue": issue, "role": role, "pid": pid, "cwd": cwd,
                                  "ts": ts})
    return attempt_id


# 이슈 #2291: 한 attempt_id 당 이 프로세스 안에서 처분은 한 번만 — 세션
# 로그 경로가 정해진(성공) 뒤 `_spawn_one()` 안에서 무관한 예외가 나도
# (예: Popen 실패) main() 의 halt-catch 가 그걸 halt 로 덮어써 이미 로스터/
# 세션-로그가 존재하기 시작한 시도를 "부트스트랩 halt"로 오분류하면 안 된다
# — 그 이후 실패는 기존 dead-entry 워치독 보고(diagnose_health 등)의 몫이다.
_SPAWN_ATTEMPT_OUTCOME_WRITTEN: set[str] = set()


def _record_spawn_outcome(attempt_id: str, outcome: str, detail: str) -> None:
    """이슈 #2291: `attempt_id`(위)의 처분을 남긴다 — `outcome` 은
    `"halted"`(halt 사유 문자열을 `detail`에) 또는 `"session-log"`
    (세션 로그 경로를 `detail`에, 성공 경로). 같은 attempt_id 로 두 번째
    호출은 no-op(위 주석)."""
    if attempt_id in _SPAWN_ATTEMPT_OUTCOME_WRITTEN:
        return
    _SPAWN_ATTEMPT_OUTCOME_WRITTEN.add(attempt_id)
    _append_spawn_attempt_event({"event": "spawn_attempt_outcome",
                                  "attempt_id": attempt_id, "outcome": outcome,
                                  "detail": detail, "ts": time.time()})


def _load_spawn_attempts() -> tuple[dict, dict, dict]:
    """`SPAWN_ATTEMPTS_PATH`를 읽어 (attempts, outcomes, resolved) — 셋
    다 attempt_id 로 키가 잡힌 dict. 워치독의 `spawn_attempt_sweep()`
    (roster.py)이 소비한다. `resolved`는 이슈 #2511 추가분 —
    `spawn_attempt_resolved` 이벤트(sweep 이 halt 조건 재확인으로 "풀렸다"
    판정한 시점에 한 번만 쓴다)로, 한 번 채워지면 그 attempt_id 는 다시
    재확인/재보고 대상이 아니라는 뜻이다."""
    attempts: dict = {}
    outcomes: dict = {}
    resolved: dict = {}
    try:
        lines = SPAWN_ATTEMPTS_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return attempts, outcomes, resolved
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if not isinstance(ev, dict):
            continue
        aid = ev.get("attempt_id")
        if not aid:
            continue
        if ev.get("event") == "spawn_attempt":
            attempts[aid] = ev
        elif ev.get("event") == "spawn_attempt_outcome":
            outcomes[aid] = ev
        elif ev.get("event") == "spawn_attempt_resolved":
            resolved[aid] = ev
    return attempts, outcomes, resolved


# 이슈 #2511: halt 사유 문자열을 클래스로 분류한다. 분류는 sys.exit 메시지
# 접두사로 하는데, 그 메시지들은 board.py/spawn.py 안의 고정 f-string
# 템플릿이라(사용자가 자유 입력하는 텍스트가 아니다) 접두사 매칭이
# 안정적이다. 이슈가 이름을 붙인 세 클래스(요구 연결 누락/ENOSPC/워크스페이스
# origin 불일치) + acceptance-format(이슈 acceptance 절 3번째 불릿이 명시적으로
# 이름 붙임) + cwd-invalid(이슈 #2576 스폰에서 실측된 "-C 가 존재하지 않는
# 디렉터리다" 류 — require_repo_root()의 세 sys.exit 분기, 같은 재확인
# 방식: 그 경로가 지금 존재/레포/레포-루트인지 다시 물으면 된다).
_HALT_CLASS_PATTERNS = (
    ("requirement-tag", re.compile(r"^이슈 #\d+ 가 요구 연결이 없다")),
    ("acceptance-format", re.compile(r"^이슈 #\d+ 는 phase-2 승인")),
    ("enospc", re.compile(r"^스폰을 거부한다: .+ 에 여유 (?:공간|inode)")),
    ("workspace-origin-mismatch",
     re.compile(r"^작업 경로에 다른 레포가 있다 \(origin 불일치\): ")),
    ("cwd-invalid", re.compile(r"^-C 가 (?:존재하지 않는 디렉터리다|"
                                r"git 레포 안이 아니다|레포 루트가 아니라)")),
)


def _classify_halt_reason(reason: str) -> str:
    """`reason`(halt outcome 의 `detail`)을 위 패턴으로 분류한다. 매칭되는
    게 없으면 `"unknown"` — `_halt_condition_cleared()`는 unknown 클래스를
    항상 "아직 안 풀림"으로 본다(재확인할 방법을 모르면 계속 보고하는 게
    watch-coverage 불변식과 같은 보수적 방향)."""
    reason = reason or ""
    for name, pat in _HALT_CLASS_PATTERNS:
        if pat.search(reason):
            return name
    return "unknown"


def _norm_git_remote_url(u: str) -> str:
    """origin 비교용 정규화 — `issue_workspace()`(위, origin 불일치 halt를
    내는 바로 그 코드)의 `_norm()`과 동일하게 유지해야, 재확인이 최초
    판정과 다른 기준으로 "풀렸다"고 오판하지 않는다."""
    u = re.sub(r"^(?:ssh://)?git@github\.com[:/](.+?)(?:\.git)?$",
               r"https://github.com/\1", u or "")
    return re.sub(r"\.git$", "", u.rstrip("/"))


def _halt_condition_cleared(cls: str, attempt: dict, reason: str) -> bool:
    """이슈 #2511 핵심: `cls`(위 분류)의 blocking 조건이 **지금** 다시 봐도
    여전히 살아있는지 재확인한다. `True`면 "풀렸다"(resolved) — sweep 이
    더는 이 halt 를 라이브로 보고하지 않는다.

    설계 결정(레코드의 "staleness 판정 방식" 절 그대로): 모든 클래스가
    "그 조건을 다시 확인한다"(re-check) 방식이지, 경과 시간(expiry)만으로
    풀렸다고 표시하는 클래스는 하나도 없다 — 다섯 클래스 전부 조건이
    자연히 사라지지 않고(태그는 누가 안 달면 안 달린 채 영원하고, 디스크는
    안 지우면 안 차고, origin 불일치/불량 cwd 는 아무도 안 고치면 그대로다)
    시간이 지난다고 저절로 참이 되는 술어가 아니다 — "N분 지났으니 풀린
    셈 친다"는 판정은 여전히 안 고쳐진 스폰을 "풀렸다"로 오분류할 길을
    남긴다(이슈의 must-not 그대로: "a missing tag does not fix itself").

    판정 불가(경로 정보가 없다/재확인 자체가 실패한다/알 수 없는 클래스)는
    전부 `False`(아직 안 풀림) — 확신 없을 때는 계속 라이브로 보고한다."""
    cwd = attempt.get("cwd")
    try:
        if cls == "requirement-tag" or cls == "acceptance-format":
            issue = attempt.get("issue")
            if issue is None or not cwd:
                return False
            root = Path(cwd)
            if not root.is_dir():
                return False
            root = root.resolve()
            gates_dir = str((ROOT / "gates").resolve())
            if gates_dir not in sys.path:
                sys.path.insert(0, gates_dir)
            if cls == "requirement-tag":
                import requirement_linkage as _rl
                return not _rl.check(root, issue)
            import acceptance_gate as _ag
            return not _ag.check(root, issue)
        if cls == "cwd-invalid":
            if not cwd:
                return False
            p = Path(cwd)
            if not p.is_dir():
                return False
            resolved_p = p.resolve()
            r = subprocess.run(
                ["git", "-C", str(resolved_p), "rev-parse", "--show-toplevel"],
                capture_output=True, text=True)
            if r.returncode != 0:
                return False
            return Path(r.stdout.strip()).resolve() == resolved_p
        if cls == "enospc":
            m = re.search(r"^스폰을 거부한다: (.+?) 에 여유 (공간|inode)", reason or "")
            if not m:
                return False
            probe = Path(m.group(1))
            while not probe.exists():
                parent = probe.parent
                if parent == probe:
                    return False
                probe = parent
            try:
                usage = shutil.disk_usage(probe)
            except OSError:
                return False
            min_bytes = int(os.environ.get("MUSTER_MIN_FREE_BYTES", MIN_FREE_BYTES_DEFAULT))
            if usage.free < min_bytes:
                return False
            try:
                st = os.statvfs(probe)
            except (OSError, AttributeError):
                return True
            free_inodes = st.f_favail
            min_inodes = int(os.environ.get("MUSTER_MIN_FREE_INODES", MIN_FREE_INODES_DEFAULT))
            return not (free_inodes and free_inodes < min_inodes)
        if cls == "workspace-origin-mismatch":
            reason = reason or ""
            m = re.search(r"^작업 경로에 다른 레포가 있다 \(origin 불일치\): (\S+) ", reason)
            if not m:
                return False
            work = Path(m.group(1))
            if not work.is_dir():
                # 이슈 실측 그대로: 더는 존재하지 않는 워크스페이스 디렉터리에
                # 대한 origin 불일치는, 그 특정 충돌이 재현될 대상 자체가
                # 없어졌다는 뜻이라 풀린 것으로 본다.
                return True
            m2 = re.search(r"기대: (\S+), 실제: (\S*)", reason)
            if not m2:
                return False
            expected = m2.group(1)
            rw = subprocess.run(["git", "-C", str(work), "remote", "get-url", "origin"],
                                capture_output=True, text=True)
            actual = rw.stdout.strip()
            return _norm_git_remote_url(actual) == _norm_git_remote_url(expected)
    except Exception as e:
        # 이슈 #2511 silent-failure-audit: 조용히 False 만 돌려주면 "아직도
        # 안 풀렸다"(정상 케이스)와 "재확인 자체가 깨졌다"(버그)가 구분이
        # 안 된다 — 둘 다 같은 halt 라인이 계속 반복되므로, 후자를 겪는
        # 운영자는 재확인 메커니즘이 죽어 있다는 걸 알 방법이 없다. 판정
        # 자체는 여전히 보수적으로 False(=아직 안 풀림)로 두되(watch-coverage
        # 불변식은 그대로), 예외가 났다는 사실만 별도 한 줄로 드러낸다.
        print(f"[spawn-attempt] recheck 자체가 예외로 실패했다(class={cls!r}): "
              f"{type(e).__name__}: {e} — 조건은 보수적으로 '아직 안 풀림'으로 "
              f"본다.", file=sys.stderr)
        return False
    return False  # unknown class


# 이슈 #2511 residual (PR #2594 재오픈 코멘트, PR #2608 리뷰 코멘트): 클래스
# 기반 재확인(`_halt_condition_cleared`)은 halt 사유가 "이슈/워크스페이스의
# 지금 상태"의 함수일 때만 통한다. `cwd-invalid`/`workspace-origin-mismatch`
# 처럼 halt 가 그 *시도 자신이 넘긴 인자*(재시도해도 절대 안 바뀌는 문자열 —
# 예: 이슈 #2576 이 -C 에 리포 슬러그를 준 시도)에 매인 클래스는, 그 뒤
# 같은 작업이 인자를 고쳐 재시도해 실제로 성공했어도 원래 레코드의 재확인은
# 영원히 "아직 안 풀림"을 돌려준다 — 원래 레코드 자체가 안 바뀌기 때문이다.
# cwd 필드가 없는(#2594 이전에 쓰인) 레거시 레코드도 같은 증상이다: `cwd`가
# 없으면 `_halt_condition_cleared`는 판정 불가로 항상 False.
#
# 이 함수는 그 잔여를 별도로 묻는다: "같은 작업(issue + role family)에 대한
# 더 나중 시도가 성공했는가?" — 그렇다면 이 halt 는 그 자체 조건이 지금
# 재확인으로 어떻게 나오든 상관없이 풀린 것으로 본다. `_halt_condition_cleared`
# 를 대체하지 않는다 — `roster.spawn_attempt_sweep()`이 그 재확인이 False 를
# 돌려준 *뒤에만* 이 함수를 추가로 묻는 순서를 유지한다(클래스 기반 재확인은
# 여전히 1급 메커니즘).
#
# "같은 작업" 매칭 규칙: role 에서 `roster.new_lease_disambiguator()`가 붙이는
# lease 분해자(`secrets.token_hex(4)` — 정확히 8자리 소문자 hex, role 끝에
# `-{hex8}`로 붙는다)를 뗀 나머지를 "role family"로 본다. 정확 role 문자열
# 매칭(#2608 이 시도했던 방식)은 실측 재시도 쌍(이슈 #2576:
# `silent-failure-audit-ec09cf78` 실패 -> `silent-failure-audit-c678659a`
# 성공)에서 절대 맞지 않는다 — 분해자가 매 시도마다 새로 뽑히는 게 재시도의
# 정상 모양이지 예외가 아니기 때문이다(#2608 리뷰 코멘트). family 로
# 넓히되 issue 번호는 여전히 정확히 일치해야 한다 — 안 그러면
# `issue-1/implementation-af260856`(아무도 태그를 안 달 이슈, 검증 픽스처)
# 같은 무관한 halt 까지 다른 이슈의 같은 family 성공 때문에 조용히 풀린 것으로
# 오판할 길이 열린다.
#
# 증거 위치: `attempts`/`outcomes`(둘 다 `_load_spawn_attempts()`가
# `SPAWN_ATTEMPTS_PATH`에서 읽어온 것 — 호출부가 이미 갖고 있어 새로
# 읽지 않는다)에서 issue+family 가 같고 timestamp 가 이 halt 보다 나중이며
# outcome 이 `"session-log"`인 항목을 찾는다. 이게 실제로 가능한 건
# `_prune_spawn_attempts()`가 이제 session-log 처분도 halted 와 같은
# `SPAWN_ATTEMPTS_RETENTION_SEC` 창 동안 보존하기 때문이다 — PR #2608 은
# 정확히 여기서 실패했다: session-log 는 그 PR 이 열렸던 시점까지 매 sweep
# (watchdog 틱, ~2분마다) 끝에 즉시 지워졌으므로, 재시도가 성공한 바로 다음
# 틱이면 이미 그 증거가 사라져 있었다(격리된 사본으로 만든 데모에서만
# 재현됐다 — 실제 운영 레저에는 애초에 `session-log` outcome 이 하나도
# 없었다는 게 그 PR 리뷰의 실측). 이 잔여 작업이 채택한 해법은 그 비대칭을
# spawn-attempts.jsonl 안에서 없애는 것(retention 대칭화)이지, PR/보드 같은
# 외부 소스를 새로 얹는 게 아니다 — 레코드 기록서 "staleness 판정" 절에
# 대안(외부 증거원)을 왜 안 골랐는지와 함께 남긴다.
_LEASE_DISAMBIGUATOR_SUFFIX_RE = re.compile(r"-[0-9a-f]{8}$")


def _role_family(role: str) -> str:
    """`role`에서 lease 분해자 접미사를 떼 role family 를 돌려준다. 접미사가
    없으면(분해자 없이 role 을 직접 넘긴 옛 호출부/테스트 픽스처) role 을
    그대로 돌려준다 — family 는 "role 에서 알아낼 수 있는 가장 넓은, 그러나
    여전히 issue 번호와 함께 써야 안전한 식별자"이지, "항상 접미사가 있다"는
    가정이 아니다."""
    return _LEASE_DISAMBIGUATOR_SUFFIX_RE.sub("", role or "")


def _attempt_superseded(attempt_id: str, attempt: dict, attempts: dict,
                         outcomes: dict) -> bool:
    """`attempt`(halt 가 아직 클래스 재확인으로는 안 풀린 것으로 나온 시도)가
    같은 작업(issue + role family)에 대한 더 나중의 성공한(`"session-log"`)
    시도로 superseded 됐는지 본다. 위 모듈 주석 참고 — 매칭 규칙과 증거
    위치의 근거는 거기 있다.

    보수적 기본값: issue/role/ts 중 하나라도 없거나 타입이 안 맞으면
    `False`(판정 불가 — 아직 안 풀림 쪽으로) — `_halt_condition_cleared`와
    같은 fail-safe 방향."""
    issue = attempt.get("issue")
    role = attempt.get("role")
    my_ts = attempt.get("ts")
    if issue is None or not role or not isinstance(my_ts, (int, float)):
        return False
    family = _role_family(role)
    for other_id, other in attempts.items():
        if other_id == attempt_id:
            continue
        if other.get("issue") != issue:
            continue
        other_role = other.get("role")
        if not other_role or _role_family(other_role) != family:
            continue
        other_ts = other.get("ts")
        if not isinstance(other_ts, (int, float)) or other_ts <= my_ts:
            continue
        outcome = outcomes.get(other_id)
        if outcome is not None and outcome.get("outcome") == "session-log":
            return True
    return False


# 이슈 #2393 (R8, #2291 conformance review, "Surface" — 이 파일은 append-only
# 로만 자라고 오늘까지 rotation 이 없었다): PR #2371 이 남긴 해법 그대로 —
# "prune spawn-attempts.jsonl 는 한 엔트리의 처분이 sweep 되어 보고까지 끝난
# 뒤" 이되, `spawn_attempt_sweep()`(roster.py)의 실제 보고 규칙을 그대로
# 따른다: outcome 이 `"halted"` 인 시도는 `ledger_check_and_stamp` TTL 주기마다
# 반복 재보고되는 게 의도된 동작이라(미해결 halt 를 계속 상기) 그 재보고
# 창을 죽이지 않도록 보존 기간을 둔다 — `APPROVAL_WAIT_LEDGER_TTL_SEC`
# 와 같은 7일(roster.py); outcome 이 아직 없는(sweep 이 아직 판정 중일 수
# 있는) 시도는 나이와 무관하게 항상 남긴다 — 지우면 늦게 오는 진짜 halt
# 판정을 sweep 이 영영 놓친다.
#
# 이슈 #2511 residual (PR #2608 리뷰 코멘트로 확정된 실측): outcome 이
# `"session-log"`(성공)인 시도는 `spawn_attempt_sweep()`의 보고 규칙상
# 애초에 라이브 halt 로 보고된 적이 없다는 점은 그대로지만, 그렇다고
# "보존 대상이 아니다"는 더는 맞지 않는다 — `_attempt_superseded()`(위)가
# "같은 작업에 대한 더 나중의 성공한 시도가 있었는가"를 이 레코드로
# 답한다. 예전처럼 나이와 무관하게 바로 지우면, halted 시도가 재시도돼
# 성공한 바로 다음 watchdog 틱(spawn_attempt_sweep 자신이 매 틱 끝에 이
# prune 을 부른다 — roster.py)에 그 성공 증거가 이미 없다: PR #2608 이
# "session-log outcome 을 later attempt 로 찾아 supersession 을 증명한다"는
# 접근으로 냈다가, 운영 레저에 `session-log` outcome 이 하나도 없다는(전부
# sweep 한 번 안에 지워진다) 실측으로 리뷰에서 막힌 게 정확히 이 경로다.
# 그래서 halted 분기와 retention 을 대칭으로 맞춘다 — 같은
# `SPAWN_ATTEMPTS_RETENTION_SEC`(7일) 창, 새 knob 없이: 이 halt 가 아직
# 살아서 재보고될 수 있는 최대 기간 동안은, 그 halt 를 superseded 로 만들
# 성공 증거도 최소한 그만큼 살아있어야 한다는 게 이 대칭의 근거다(그
# 창보다 더 길게 남길 이유는 없다 — 그 창을 넘긴 halted 시도는 이미
# `_prune_spawn_attempts()`가 지워 재보고 대상이 아니므로, supersede 할
# 대상 자체가 없다).
#
# 기록서("staleness 판정" 절)에 남긴 대안 검토: PR/보드 상태 같은 외부
# 소스(예: `board.py._merged_pr_for_branch`)로 증거를 옮기는 방안도
# 검토했으나 기각했다 — 이 오케스트레이터는 `-C`로 넘어온 임의의 대상
# 레포 위에서 돈다(GitHub 가 아닐 수도 있고, 브랜치 네이밍 관례가
# 레포마다 다를 수 있다), 매 watchdog 틱마다 halted 상태인 subject 수만큼
# 네트워크 API 호출을 추가하며, 이미 이 파일 안에 있는(append-only,
# crash-safe, 이미 감사된) 메커니즘의 retention 창 하나를 대칭으로 맞추는
# 것보다 새 외부 의존성을 얹는 쪽이 훨씬 무겁다.
SPAWN_ATTEMPTS_RETENTION_SEC = 7 * 24 * 3600


def _pid_is_alive(pid) -> bool:
    """이슈 #2413: `_prune_spawn_attempts()`의 prune 패스 중에만 하는
    on-demand 체크(signal 0 kill) — 지속 폴링이 아니라 watchdog 틱마다
    prune 이 도는 그 순간에만 값을 묻는다(추가 steady-state 부하 없음).
    `ProcessLookupError` 만 "죽었다"로 본다: `PermissionError`(다른
    유저 소유 pid — 그래도 존재)나 그 밖의 `OSError` 는 생사를 확신할
    수 없다는 뜻이라 보수적으로 "살아있다"로 취급한다 — 판정이 불확실할
    때 실행 중인 spawn 을 실수로 지우는 쪽보다, 안 지워질 orphan 레코드가
    하루이틀 더 남는 쪽이 낫다. `pid` 가 숫자 문자열로 직렬화돼 있어도
    (레저 손상/드리프트로 실제 있었던 사례 — commit cea0f583) int 로
    변환해 실제로 OS 에 물어본다: 변환 없이 non-int 를 바로 죽었다고
    보면, 살아있는 pid 가 문자열로만 인코딩된 레코드를 오검사로
    지워버릴 수 있다."""
    if isinstance(pid, str) and pid.strip().lstrip("-").isdigit():
        try:
            pid = int(pid)
        except ValueError:
            return False
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    else:
        return True


# 이슈 #2468: check_runner.py 의 임시 PR worktree(`tempfile.mkdtemp`)와
# consult.py/spawn.py 의 settings.json(`tempfile.NamedTemporaryFile`)는
# 정상 종료 경로에서만 지워진다 — SIGKILL/하드크래시는 try/finally 로도
# 못 잡는다(파이썬이 신호를 볼 기회 자체가 없다). 생성 시점에 소유 PID 를
# 여기 남겨 두면, 나중에 `_pid_is_alive()`(위, #2413 에서 이미 증명된
# 패턴)로 그 PID 가 죽었는지만 물어 지운다 — 살아있는 소유자의 자원은
# 나이와 무관하게 항상 보존한다(그 함수 자신의 보수적 정책을 그대로
# 물려받는다: 판정이 불확실하면 살아있다고 본다). append-only(줄을 쓰는
# 도중 죽어도 이미 쓴 줄은 안전하다 — SPAWN_ATTEMPTS_PATH 와 같은 이유).
TMP_RESOURCE_LEDGER_PATH = STATE_ROOT / "tmp-resources.jsonl"


def _record_tmp_resource(path, pid: int, kind: str) -> None:
    """`path`(worktree 디렉터리 또는 settings.json 파일)를 소유 `pid`와
    함께 남긴다. 호출부는 실제 정리 책임을 지는 프로세스가 자기 자신의
    `os.getpid()`로 불러야 한다 — spawn.py 의 `bounded` 스폰처럼 만든
    프로세스(부모)와 실제로 쓰고 지우는 프로세스(fork 자식)가 갈리는
    경우, 부모 pid 를 남기면 부모가 정상 리턴한 직후 `_pid_is_alive()`가
    바로 False 를 돌려줘 아직 자식이 쓰고 있는 자원을 오삭제하게 된다
    (이슈 #2468 설계 검토에서 실측)."""
    if os.environ.get("PYTEST_CURRENT_TEST") is not None:
        return
    TMP_RESOURCE_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TMP_RESOURCE_LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"path": str(path), "pid": pid, "kind": kind,
                              "ts": time.time()}, ensure_ascii=False) + "\n")


def tmp_resource_sweep(ledger_path: Path | None = None) -> int:
    """이슈 #2468 GC 스윕 — `_prune_spawn_attempts()`와 같은 자세(통짜
    재쓰기, PID 생존만으로 판정)로 orphan worktree/settings.json 을
    지운다. 이미 정상 경로로 지워진 자원(레저에는 있지만 디스크엔 없음)은
    그냥 레저에서 빠진다 — 지운 걸로 세지 않는다. 반환값은 이번 호출에서
    실제로 지운 자원 개수(워치독 로그용 — anomaly_count 에는 안 얹는다:
    이건 이상 신호가 아니라 정상적인 자기치유다)."""
    ledger_path = ledger_path or TMP_RESOURCE_LEDGER_PATH
    try:
        lines = ledger_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    kept = []
    removed = 0
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        path = entry.get("path")
        if not path:
            continue
        p = Path(path)
        if not p.exists():
            continue  # 이미 정상 경로로 지워졌다 — 레저에서도 조용히 뺀다
        if _pid_is_alive(entry.get("pid")):
            kept.append(line)
            continue
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        else:
            with contextlib.suppress(OSError):
                p.unlink()
        removed += 1
    if len(kept) != len(lines):
        ledger_path.write_text(
            "".join(ln + "\n" for ln in kept), encoding="utf-8")
    return removed


def _prune_spawn_attempts(now: float | None = None) -> int:
    """`SPAWN_ATTEMPTS_PATH`를 다시 써서 위 정책에 안 걸리는 이벤트만
    남긴다. 돌려주는 값은 지운 줄 수(0 이면 파일을 건드리지 않는다 —
    watchdog 틱마다 매번 재쓰기하지 않는다). 파일 append 자체는 부트스트랩
    구간의 크래시 안전성 때문에 append-only 로 유지되지만(위
    `SPAWN_ATTEMPTS_PATH` 주석), 이 prune 은 그 창 밖에서(watchdog 틱마다,
    `spawn_attempt_sweep()` 이 호출) 별도로 도는 유지보수 동작이라 통짜
    재쓰기로 해도 그 크래시-안전성 근거를 안 건드린다."""
    now = time.time() if now is None else now
    try:
        lines = SPAWN_ATTEMPTS_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    attempts, outcomes, resolved = _load_spawn_attempts()
    keep_ids = set()
    for aid, a in attempts.items():
        outcome = outcomes.get(aid)
        if outcome is not None and outcome.get("outcome") == "halted" and aid in resolved:
            # 이슈 #2511: sweep 이 이미 "풀렸다"고 판정해 한 번 알렸다 —
            # session-log 처분과 같은 대접(더는 보고 대상이 아니므로 즉시
            # 정리). halted 분기 고유의 7일 재보고 창(SPAWN_ATTEMPTS_RETENTION_SEC)
            # 은 "아직 안 풀린" halt 를 오케스트레이터가 알아챌 시간을 주려는
            # 것이라 이미 풀린 시도에는 적용할 이유가 없다.
            continue
        if outcome is None:
            # 이슈 #2413: outcome 이 없다고 무조건 영원히 유지하면(원래
            # 동작) 프로세스가 진작 죽어 다시는 outcome 을 못 쓸 시도
            # (SIGKILL/OOM/하드 크래시)까지 매 틱 그대로 남아
            # spawn_attempt_sweep() 이 "no outcome recorded"를 영원히
            # 재보고한다(실측: 434건 중 419건이 pytest fixture 이슈
            # 31/7 의 orphan — #2393 origin guard 이전에 쌓인 것들).
            # 살아있는 spawn(pid 생존)은 나이와 무관하게 절대 안 지운다
            # — "in-flight 시도가 실행 중인 spawn 밑에서 지워지면 안
            # 된다"는 요구사항 그대로.
            #
            # 이슈 #2431: pid 가 죽었을 때 #2413 은 halted 분기와 같은
            # SPAWN_ATTEMPTS_RETENTION_SEC(7일) 창을 그대로 재사용했다 —
            # "새 knob 을 만들지 않는다"는 의도는 맞았지만, 그 7일 창은
            # halted 분기 고유의 이유(미해결 halt 를 오케스트레이터가
            # 알아채고 조치할 시간을 준다)로 존재하는 것이라 여기엔
            # 적용되지 않는다: pid 가 이미 죽었다고 확인된 순간부터는
            # "알아채고 조치할" 대상 자체가 없다 — 기다림은 순수 비용이다
            # (실측: 라이브 백로그 434건이 전부 7일 미만의 죽은 pid라
            # #2418 은 0건을 지웠다). 오퍼레이터 가이던스(이슈 #2431,
            # issuecomment-5411038089, 2026-08-25 mid-flight)로 확정: 애초에
            # 달력 기반 유예 자체가 불필요하다 — `_pid_is_alive()`가 False를
            # 반환한 순간 그 결론(진짜 죽었다)은 이미 확정이라 더 기다려도
            # 새로 알아낼 게 없다. 시간이 걸려야 하는 유일한 케이스는
            # `_pid_is_alive()` 자신이 판정을 확신 못 하는 경우(모호한
            # `OSError`)뿐인데, 그건 이미 그 함수 안에서 "확신 없으면
            # 살아있다고 본다"로 보수적으로 처리돼 있어(docstring 참고)
            # 여기까지 내려오지 않는다. 그래서 이 분기는 나이 계산을 아예
            # 하지 않는다: pid 가 죽었다고 확인되면 바로 다음 prune pass
            # (이 watchdog 틱)에 지운다. `spawn_attempt_sweep()`(roster.py)
            # 은 이 함수를 호출하기 전에 같은 호출 안에서 먼저 보고 루프를
            # 돌리므로(그 시점에 이미 `SPAWN_ATTEMPT_GRACE_SEC` 를 넘겼다면)
            # 지우기 전에 보고할 기회를 여전히 얻는다 — 별도 유예 없이도
            # "지우기 전에 최소 한 번은 보고"가 정상 호출 경로에서 그대로
            # 성립한다. halted 분기의 7일 창은 이 변경으로 전혀 건드리지
            # 않는다(아래 elif, 여전히 SPAWN_ATTEMPTS_RETENTION_SEC 그대로;
            # issuecomment-5410865516 이 명시적으로 요구한 그대로).
            #
            # CHANGES 라운드(execution-observation, PR #2438 merged로 지적):
            # 위 "나이 계산을 아예 안 한다"는 결론에는 구멍이 있었다 —
            # `SPAWN_ATTEMPT_GRACE_SEC`(300초, roster.py) 이내에 pid 가 죽는
            # 빠른 크래시는, 바로 그 틱에서 `spawn_attempt_sweep()` 의 보고
            # 루프 자신이 "아직 부트스트랩 유예 중"이라며 보고를 건너뛰는데
            # (그 루프의 게이트가 정확히 `now - ts < SPAWN_ATTEMPT_GRACE_SEC`),
            # 뒤이어 같은 호출이 부르는 이 prune 은 나이를 전혀 안 보고 pid
            # 죽음만으로 바로 지워버려 — 그 시도는 단 한 번도 보고되지 않고
            # 사라진다. #2291/#2393/#2413/#2431 전체 체인이 없애려는 바로 그
            # "무보고 침묵 halt" 클래스를 그대로 재도입하는 회귀였다.
            #
            # 고쳐서: pid 죽음 확인과 별개로 `SPAWN_ATTEMPT_GRACE_SEC` 를
            # 넘기기 전에는 지우지 않는다 — 보고 루프가 reportable 여부를
            # 판정하는 것과 정확히 같은 문턱이라, 한 시도가 처음 prune
            # 대상 나이에 닿는 바로 그 틱은 늘 보고 루프가 먼저 그 시도를
            # 검토하는 바로 그 틱이기도 하다(report 루프가 먼저 돌고 나서
            # prune 이 도는 같은 `spawn_attempt_sweep()` 호출 안이므로) —
            # "지우기 전 최소 한 번 보고"가 report 루프의 성공 여부에
            # 기대는 게 아니라 이 문턱을 공유하는 것 자체로 보장된다. 이
            # 문턱은 halted 분기의 7일 `SPAWN_ATTEMPTS_RETENTION_SEC`과는
            # 다른, 훨씬 짧은 `SPAWN_ATTEMPT_GRACE_SEC`(300초 =
            # CLONE_TIMEOUT+NETWORK_TIMEOUT+60) 이다 — 근거가 다르다: halted
            # 쪽은 "오케스트레이터가 알아채고 조치할 시간"이고, 여기는
            # "이 워치독 틱의 보고 루프가 이 레코드를 검토할 기회를 최소
            # 한 번 갖게 하는 것"뿐이다. 이미 살아있는 spawn을 나이로
            # 보호하려는 목적이 전혀 아니므로 — 살아있는 pid 는 위에서
            # 나이와 무관하게 항상 keep 이고, 이 문턱은 "죽은 pid" 시도에만
            # 적용된다. `ts` 가 없거나 숫자가 아니면(레저 손상/드리프트)
            # 유예를 계산할 근거 자체가 없어 즉시 prune 대상으로 본다
            # (missing-ts 에 대한 기존 동작 유지).
            pid = a.get("pid")
            if _pid_is_alive(pid):
                keep_ids.add(aid)
            else:
                ts = a.get("ts")
                if isinstance(ts, (int, float)) and \
                        now - ts < SPAWN_ATTEMPT_GRACE_SEC:
                    keep_ids.add(aid)
                # else: 죽었다고 확인됐고, 보고 루프가 이 시도를 검토할 수
                # 있었던 문턱(SPAWN_ATTEMPT_GRACE_SEC)도 이미 넘겼다(또는
                # ts 가 없어 유예를 계산할 수 없다) — prune 대상
                # (keep_ids 에 안 넣는다).
        elif outcome.get("outcome") == "halted":
            outcome_ts = outcome.get("ts", now)
            if not isinstance(outcome_ts, (int, float)) or \
                    now - outcome_ts < SPAWN_ATTEMPTS_RETENTION_SEC:
                keep_ids.add(aid)  # halted — 재보고 TTL 창 동안 유지
        elif outcome.get("outcome") == "session-log":
            # 이슈 #2511 residual: 이 시도는 절대 라이브 halt 로 보고되지
            # 않지만(sweep 의 보고 루프가 애초에 건너뛴다), 다른 halted
            # 시도의 `_attempt_superseded()` 재확인이 읽는 증거이기도
            # 하다 — halted 분기와 같은 창(SPAWN_ATTEMPTS_RETENTION_SEC)
            # 동안 대칭으로 유지한다(근거는 이 파일의
            # `SPAWN_ATTEMPTS_RETENTION_SEC` 정의 옆 주석). 이 창을 넘기면
            # 지운다 — 그 시점이면 supersede 할 수 있었던 halted 시도
            # 자신도 이미 위 분기에서 지워졌으므로 이 레코드가 답할 질문이
            # 남아있지 않다.
            outcome_ts = outcome.get("ts", now)
            if not isinstance(outcome_ts, (int, float)) or \
                    now - outcome_ts < SPAWN_ATTEMPTS_RETENTION_SEC:
                keep_ids.add(aid)
    kept_lines = []
    dropped = 0
    for line in lines:
        try:
            ev = json.loads(line)
        except ValueError:
            dropped += 1
            continue
        aid = ev.get("attempt_id") if isinstance(ev, dict) else None
        if aid in keep_ids:
            kept_lines.append(line)
        else:
            dropped += 1
    if dropped:
        tmp_path = SPAWN_ATTEMPTS_PATH.with_suffix(".jsonl.tmp")
        tmp_path.write_text(
            "".join(line + "\n" for line in kept_lines), encoding="utf-8")
        tmp_path.replace(SPAWN_ATTEMPTS_PATH)
    return dropped


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

    # signal 2 (이슈 #2217): 구조적 background-delegation tool_use 만 센다 —
    # 단어 매치는 우리 자신이 주입하는 headless 경고 프롬프트에도 걸려
    # 100% 세션에서 오탐했다. 시점 무관, 매치 즉시 신고.
    if _count_structural_delegations(text) > 0:
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
                f"<n> --session <session> --rearm 로 재무장하라 (non-blocking)")
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
                        f"spawn.py watch --issue <n> --session <session> --rearm 로 "
                        f"재무장하라 (non-blocking)")

    return anomalies


# sibling: core_version


# sibling: core_root


def drive(cwd: str, unattended: bool, limit: int = 12) -> int:
    """드라이버의 유일한 계약상 임무: 더 띄울 게 없으면 멈춘다.

    "누구를 다음에 띄울지"는 기계가 평가하는 라우팅 표가 아니라 오케스트레이터가
    보드(기록, loop_state)를 직접 읽고 내리는 판단이다(이슈 #120) — 그래서
    drive 는 스스로 고르지 않는다. 자동으로 고를 표가 없으므로 이
    호출은 항상 즉시 멈춘다; 남은 인자는 향후 호출부 호환을 위해 받되 쓰지
    않는다.

    이슈 #492 (ADR): `reconcile()` 이 낸 divergence 를 소비하는 것으로
    바뀐다 — 로스터를 읽어 엔트리마다 `reconcile()` 을 돌리고 결과와
    `next_action` 을 출력한다. #120 계약은 그대로다: drive() 는 여전히
    아무것도 스스로 고르지 않고, 무엇을 띄울지는 오케스트레이터의
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("role", nargs="?",
                    help="서브커맨드 이름(watch/kill/init/...), 또는 "
                         "--skills/--skill 스폰의 유일한 위치 인자인 "
                         "<맡길 일>. 생략하면 상태만 보여준다. 이슈 #2572: "
                         "역할-포지셔널 스폰(spawn.py implementation \"<일>\")은 "
                         "은퇴했다 — 세션 스폰은 --skills 로만 한다")
    ap.add_argument("task", nargs="?", help="맡길 일. 룰북 커맨드면 '/plugin:command 인자'")
    ap.add_argument("consult_question", nargs="?",
                    help="consult <role-or-skill> \"<질문>\": 세 번째 위치 인자로 질문을 받는다")
    ap.add_argument("panel_question", nargs="?",
                    help="panel <role-or-skill-A> <role-or-skill-B> \"<질문>\": 네 번째 위치 인자로 질문을 받는다")
    ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
    ap.add_argument("--dry-run", action="store_true", help="합쳐진 설정만 보고 안 띄운다")
    ap.add_argument("--no-contract", action="store_true",
                    help="대상 레포에 계약이 없어도 띄운다. 보드를 안 쓸 작업에만")
    ap.add_argument("--trust-repo-config", action="store_true",
                    help="대상 레포의 .claude/ 설정·훅을 신뢰한다. 읽어본 뒤에만")
    ap.add_argument("--issue", type=positive_int,
                    help="이 이슈 번호로 스폰한다: --skills 스폰이면 "
                         "issue-<n>/<skill>-<lease> 브랜치를(이슈 #2432/#2572), "
                         "그 외 서브커맨드는 issue-<n>/<slug> 브랜치를 만들고 "
                         "프롬프트에 명시. --skills 는 이제 이 인자가 필수다")
    ap.add_argument("--force-adhoc-task", action="store_true",
                    help="issue #2293: admit a task that looks like a bare "
                         "issue number (`538`, `#538`, `-538`) with no "
                         "--issue, instead of the default admission "
                         "refusal -- for the rare legitimate numeric-task "
                         "case")
    ap.add_argument("--model",
                    help="이 스폰 한 번만 쓸 모델 오버라이드: --model > "
                         "MUSTER_SKILL_MODEL > role_model.txt > \"sonnet\" (이슈#1736). "
                         "judge prefilter/validator 의 하드코딩 haiku 는 영향받지 않는다")
    ap.add_argument("--skills", default=None,
                    help="이슈 #2572: 유일한 스폰 형태 — "
                         "spawn.py --skills <스킬>[,<스킬>...] \"<맡길 일>\" "
                         "--issue <n>. 쉼표로 구분한 스킬 이름 목록을 네 소스 — "
                         "skill-repository 체크아웃(MUSTER_SKILL_REPO 또는 "
                         "형제-클론), 설치된 플러그인의 skills/, "
                         "~/.claude/skills, 타깃 저장소 .claude/skills — "
                         "에 걸쳐 해석해 마운트한다(이슈 #1742/#1774/#2488). "
                         "이름이 둘 이상의 소스에서 내용까지 다르게 겹치면, "
                         "또는 어느 소스에도 없으면 fail-closed — 워크스페이스/"
                         "브랜치 전에 모르는 스킬 이름을 그대로 찍어 거절한다"
                         "(우선순위 없음, docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md). "
                         "같은 이름이 둘 이상의 소스에서 잡혀도 내용이 "
                         "바이트 단위로 같으면(심링크로 같은 디렉터리를 두 "
                         "경로로 두 번 센 경우 등) 충돌로 보지 않는다(이슈 "
                         "#2579). 이름 앞에 소스 라벨을 붙여 "
                         "(skill-repo|plugin|local-user|local-repo):<이름> "
                         "형태로 소스를 항상 — 겹칠 때만이 아니라 언제나 — "
                         "명시할 수 있다(이슈 #2579): "
                         "--skills skill-repo:silent-failure-audit,diagnose-first. "
                         "한정자가 없으면 오늘처럼 이름만으로 찾는다. "
                         "이름한 스킬은 기준선(base)이고, 이번 과제 텍스트와 "
                         "매치되는 스킬은 여전히 그 위에 add-only 로 얹힌다 — "
                         "이름한 스킬이 매치를 대신하지 않는다(이슈 #2507 "
                         "add-only 합성, 그대로 유지). 브랜치/기록 이름은 "
                         "checkout_issue_branch_for_skill() 이 짓는다: "
                         "issue-<n>/<skill>-<lease-disambiguator>(이슈 #2432)")
    ap.add_argument("--skill", default=None,
                    help="이슈 #2241 stage 0: 역할 대신 스킬 이름(콤마로 여러 개 가능)으로 "
                         "곧장 가이던스를 해석한다. 사용: spawn.py --skill <스킬명> "
                         "\"<맡길 일>\" --issue <n>. 세션은 안 띄운다 — 해석 결과 JSON만 "
                         "찍는다. --role 경로는 이 옵션과 무관하게 그대로다")
    ap.add_argument("--merge", help="judge <role-or-skill> --merge <sha>: 판단할 머지의 커밋 sha")
    ap.add_argument("--unattended", action="store_true",
                    help="사람이 없는 실행. mint 는 안 되고, 휴먼 게이트는 선다")
    ap.add_argument("--limit", type=int, default=12,
                    help="drive: 한 번에 띄울 최대 횟수 (기본 12, 폭주 방지)")
    ap.add_argument("--login", help="init: approvers.md 에 넣을 GitHub 로그인 (기본: gh api user)")
    ap.add_argument("--push", action="store_true",
                    help="init: 보드 파일을 add+commit+push 까지 직접 한다 "
                         "(issue #2125). 없으면 리모트 검증만 하고, 미푸시면 "
                         "복붙 명령 블록을 출력하고 비0으로 끝난다")
    ap.add_argument("--stall-timeout", type=float, default=5.0,
                    help="분 단위. role task/watch 가 이벤트 없이 블록하는 최대 시간 (기본 5)")
    ap.add_argument("--session", dest="watch_session",
                    help="watch: 같은 이슈에 세션이 여럿 기록돼 있을 때 어느 "
                         "세션인지 지정하는 슬러그(예: implementation-abcd1234). "
                         "recut-corrupted: --issue 와 함께 대상 issue-<n>/<session> "
                         "브랜치를 고른다")
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
    ap.add_argument("--foreground", action="store_true",
                    help="consult: 기본(배경 fork, 이슈 #2569)을 끄고 예전처럼 "
                         "호출자 프로세스 안에서 끝까지 기다려 판단 JSON 을 "
                         "표준출력에 찍는다 — 매치+세션이 43-78s+ 걸릴 수 있어 "
                         "대화형 호출자를 그만큼 얼린다(스크립트/테스트처럼 "
                         "리턴값을 그 자리에서 바로 써야 할 때만 켠다)")
    ap.add_argument("--despite-returned", action="store_true",
                    help="[DEPRECATED, 이슈 #1239] no-op — 게이트가 이제 "
                         "항상 non-blocking surfacing 이라 스폰을 거절하지 "
                         "않으므로 무시할 것이 없다. CLI 호환성을 위해 남아 "
                         "있을 뿐 (이슈 #680)")
    ap.add_argument("--single-phase", action="store_true",
                    help="[DEPRECATED, 이슈 #2152: single-phase 가 이제 "
                         "기본값이라 이 플래그는 no-op 별칭이다 — 한 릴리스 "
                         "동안만 유지] 스폰하는 세션에 CORE_BUILD_NOW=1 을 "
                         "실어 phase-1 제안 라운드를 건너뛰게 한다(contract "
                         "v3 s19a 우회, 이슈 #1672/#1978). 스포너가 명시적으로 "
                         "결정할 때만 켠다 — 세션 스스로는 절대 켤 수 없다.")
    ap.add_argument("--two-phase", action="store_true",
                    help="이슈 #2152: design-bearing 작업을 위해 proposal-"
                         "first 두-단계 흐름으로 명시적으로 opt-in 한다 — "
                         "CORE_BUILD_NOW=1 스탬프와 build-now 계약 줄을 "
                         "생략하고 오늘까지의 기본 프리앰블을 그대로 "
                         "복원한다. 플래그가 없으면 기본값은 이제 "
                         "single-phase(build-now) 다.")
    ap.add_argument("--checkpoint", action="store_true",
                    help="issue #2129: single-session propose-approve-"
                         "implement. The session opens the proposal PR as "
                         "today, then pauses IN-CONTEXT on `spawn.py "
                         "await-approval` (declared wait, #2101 watchdog "
                         "exemption) and continues to phase-2 in the same "
                         "session on APPROVE; on timeout it exits with "
                         "today's returned-proposal semantics. Default "
                         "(no flag) behavior is byte-identical. Mutually "
                         "exclusive with --single-phase")
    ap.add_argument("--timeout", type=float, default=None,
                    help="await-approval: total bounded wait in seconds "
                         "(default CHECKPOINT_WAIT_MAX_SECONDS env or 1800)")
    ap.add_argument("--poll-interval", type=float, default=None,
                    help="await-approval: comment poll cadence in seconds "
                         "(default CHECKPOINT_POLL_SECONDS env or 60)")
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
    # Issue #2592: `--role` selected a session instance, not a role, and
    # its own name/help text said otherwise. Retired outright rather than
    # aliased (same precedent as #2572's retired role-positional/bare-task
    # spawn forms) — argparse's generic "unrecognized arguments" wouldn't
    # name the replacement, so intercept before parsing.
    if any(tok == "--role" or tok.startswith("--role=") for tok in sys.argv[1:]):
        sys.exit("spawn.py: --role 는 은퇴했다(이슈 #2592) — 세션을 고르는 "
                 "건 역할이 아니라 슬러그다. 대신 --session <slug> 를 써라")
    a = ap.parse_args()

    # Issue #2572: --skills is now the sole spawn form -- role-shaped
    # positional spawns (`spawn.py implementation "<task>"`) and the bare-
    # task form (`spawn.py "<task>"`, issue #2555) are both retired. This
    # flag tracks whether the current invocation used the surviving form,
    # so the generic fall-through further down (which used to launch a
    # role-named session) can refuse everything else instead.
    _via_skills = False
    _skills_branch_identity: tuple[str, str] | None = None
    if a.skills:
        # Same argparse-binding convention as `--skill` right below: with
        # only one positional slot left once a selector flag takes over
        # session identity, argparse binds the lone remaining token to
        # `a.role` (positional order is role/task/consult_question/...).
        # Read it as the task text, not a role name.
        task_text = a.role
        if not task_text:
            sys.exit('usage: spawn.py --skills <skill>[,<skill>...] '
                     '"<task>" --issue <n>')
        if a.issue is None:
            sys.exit('spawn.py --skills requires --issue <n> (issue #2572) '
                     '-- the skill-axis branch/lease naming '
                     '(checkout_issue_branch_for_skill, pipeline.py:1135) '
                     'has no adhoc/issue-less form')
        skill_names = [n.strip() for n in a.skills.split(",") if n.strip()]
        if not skill_names:
            sys.exit(f"--skills: empty skill list -- {a.skills!r}")
        # This only *names* the branch/record identity from what was
        # asked for -- actual resolution (does each name exist in one of
        # the four skill sources? does it carry hooks/?) still happens
        # inside `_spawn_one()`'s existing `resolved_skill_sources()` call
        # before any workspace/branch mutation (issue #1742/#1774
        # fail-closed contract, unchanged by this issue) and fails closed
        # naming exactly the unresolvable skill.
        a.task = task_text
        # 이슈 #2579: 브랜치/역할 이름은 스킬 *이름*으로만 짓는다(콜론을 쓰는
        # `<source>:<name>` 한정자를 그대로 슬러그에 넣으면 git 브랜치 이름이
        # 깨진다 — 실측: qualified 소스로 실제 스폰해서 재현). 실제 소스
        # 해석(`resolved_skill_sources()`)은 원본 `a.skills`(한정자 포함)를
        # 그대로 받으므로 여기서 한정자를 벗겨도 fail-closed 판정에는
        # 영향이 없다.
        skill_slug = skill_branch_slug(skill_names)
        disambiguator = new_lease_disambiguator()
        _skills_branch_identity = (skill_slug, disambiguator)
        a.role = f"{skill_slug}-{disambiguator}"
        _via_skills = True

    if a.skill:
        # 이슈 #2241 stage 0: 역할 axis 밖의 additive 경로. positional 은
        # `role`/`task` 순인데 `--skill` 을 쓰면 남는 positional 은 하나뿐이라
        # argparse 가 그걸 `a.role`(첫 positional)에 묶는다 — 그래서 여기서는
        # `a.role` 을 태스크 문구로 읽는다. 아래 role 분기(`a.role == "init"`
        # 등)보다 먼저 검사해야, 태스크 문구가 우연히 그 이름들과 겹쳐도
        # 잘못 걸리지 않는다. 세션을 안 띄우므로 roster/lease/board-gate/
        # merge_gate 는 이 스테이지에서 손대지 않는다(스테이지 1/3/5).
        task_text = a.role
        if not task_text:
            sys.exit('사용법: spawn.py --skill <스킬명>[,<스킬명>...] "<맡길 일>" --issue <n>')
        # before-landing warrant hunt (이슈 #2241 stage 0): `--skill " "` 나
        # `--skill ",,,"` 는 truthy 라 이 분기에 들어오지만, 쉼표로 쪼갠 뒤
        # 남는 이름이 없다 — `resolved_skill_dirs()`의 "이름 없으면 빈 목록"
        # 단축 경로(--skills 의 "생략하면 마운트 없음" 의미론)를 여기서 그대로
        # 타면 존재하지 않는 스킬을 요청한 게 조용히 "성공"(skills: [])으로
        # 보여 fail-closed 원칙을 깬다. `--skill` 은 `--skills` 와 달리
        # 이 분기 자체를 여는 필수 식별자이므로, 빈 이름은 여기서 명시적으로
        # 거절한다.
        skill_names = [n.strip() for n in a.skill.split(",") if n.strip()]
        if not skill_names:
            sys.exit(f"--skill: 빈 스킬 이름이다 — {a.skill!r}")
        skill_registry_root = _skill_repo_root()
        skill_source = resolve_skill_source(",".join(skill_names), skill_registry_root)
        print(json.dumps({
            "task": task_text,
            "issue": a.issue,
            "source": skill_source["source"],
            "skills": skill_source["skills"],
            "skill_sha": skill_source["skill_sha"],
        }, indent=2, ensure_ascii=False))
        return 0

    if a.role == "init":
        # 보드로 선언한다(approvers.md). on-the-record 가 남의 레포에 쓰는 유일한 경우.
        return init_board(a.cwd, a.login, push=a.push)
    if a.role == "ps":
        return roster_ps()
    if a.role == "recut-if-absorbed":
        return recut_if_absorbed_cli(str(Path(a.cwd).resolve()))
    if a.role == "rebase":
        # Issue #2403: mechanical rebase of the branch already checked
        # out at `-C <cwd>` onto current main -- no LLM session. Only the
        # conflict-free case is mechanical; a conflict aborts and asks for
        # a real session (conflict resolution needs judgment).
        return mechanical_rebase_cli(str(Path(a.cwd).resolve()))
    if a.role == "recut-corrupted":
        if not a.issue or not a.watch_session:
            sys.exit("사용법: spawn.py recut-corrupted --issue <n> --session <session> [-C cwd]")
        return recut_corrupted_cli(str(Path(a.cwd).resolve()), a.issue, a.watch_session)
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
        # issue #2610: removed. `roles_due.py` evaluated the (now-deleted)
        # 44-entry role catalog's `record_spec.use_when.trigger` per role
        # name to nudge "role X is due — its record is absent and the
        # changed paths match its trigger". That nudge was inherently
        # keyed on a closed set of role names — the operator's ruling on
        # #2610 is that a capability which cannot be provided without
        # enumerating identities is dropped, not reshaped into a new
        # enumeration, and no non-enumerated trigger registry replaces it.
        # Loud, not silent: anyone still invoking this prints the removal
        # reason and exits non-zero rather than reporting an empty list.
        print("spawn.py roles-due: removed (issue #2610) — depended on the "
              "retired role-name-keyed trigger catalog; no replacement.")
        return 1
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
        if a.foreground:
            try:
                verdict = consult_cmd(a.task, a.consult_question, issue=a.issue, cwd=a.cwd,
                                      model=a.model)
            except Exception as e:
                sys.exit(f"consult 실패(트레이스는 남았다): {e}")
            print(json.dumps(verdict, indent=2, ensure_ascii=False))
            return 0
        # 이슈 #2569: 기본은 배경 fork다 — cross-family 매치(skill_judge
        # 포함, 그대로 유지)와 자문 세션 실행을 합치면 43-78s+90s 대까지
        # 걸릴 수 있다(bootstrap_timing 실측 cross_family 구간과 같은
        # 원인) — 호출자 프로세스가 그 안에서 그대로 기다리면 대화형
        # 세션 하나를 몇 분씩 얼린다. `_spawn_one()` 이 실제 스폰 세션에
        # 쓰는 것과 같은 os.fork()+setsid()+표준입출력 dup2 패턴: 부모는
        # 즉시 리턴하고, 자식이 판단을 끝까지 몰아 트레이스에 커밋한다.
        log_path = _consult_background_log_path()
        role_for_log, task_for_log, cwd_for_log = a.task, a.consult_question, a.cwd
        issue_for_log, model_for_log = a.issue, a.model
        child_pid = os.fork()
        if child_pid == 0:
            os.setsid()
            log_fd = os.open(str(log_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            devnull_in = os.open(os.devnull, os.O_RDONLY)
            os.dup2(devnull_in, 0)
            os.dup2(log_fd, 1)
            os.dup2(log_fd, 2)
            os.close(devnull_in)
            os.close(log_fd)
            try:
                verdict = consult_cmd(role_for_log, task_for_log, issue=issue_for_log,
                                      cwd=cwd_for_log, model=model_for_log)
                print(json.dumps(verdict, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"consult 실패(트레이스는 남았다): {e}", file=sys.stderr)
            # os._exit() 는 인터프리터 정리(stdio 플러시 포함)를 건너뛴다 —
            # 위 print() 들이 파일로 리다이렉트된 stdout 의 블록 버퍼에만
            # 남아 로그 파일에는 한 줄도 안 남는 것으로 실측됐다. 명시적으로
            # 비운 뒤에 종료한다.
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(0)
        issue_hint = f" --issue {a.issue}" if a.issue is not None else ""
        print(f"[consult] 배경에서 돈다(pid {child_pid}) — 판단은 자문 트레이스에 "
              f"커밋된다: `spawn.py consult-log{issue_hint}` 로 확인. 단계별 "
              f"타이밍/원시 출력: {log_path}", file=sys.stderr)
        return 0
    if a.role == "consult-log":
        # 이슈 #2333: consult-log.md 는 이제 세션마다 다른 샤드 파일이라,
        # 오늘까지의 "파일 하나 cat" 만큼 쉬운 사람용/게이트용 단일-뷰가
        # 없어지면 안 된다 — 이 서브커맨드가 그 자리를 대신한다.
        print(_consult_log_aggregate(a.issue, cwd=a.cwd), end="")
        return 0
    if a.role == "hook-fires":
        # issue #2348: same reader shape as consult-log -- reconstructs the
        # pre-sharding single-file .orchestrate-hook-fires.log view.
        print(_hook_fires_aggregate(cwd=a.cwd), end="")
        return 0
    if a.role == "deviation-log":
        # issue #2348: same reader shape as consult-log -- reconstructs the
        # pre-sharding single-file deviation-log.md view for this issue
        # (+role, when this session's own $CLAUDE_ROLE names one).
        print(_deviation_log_aggregate(a.issue, role=os.environ.get("CLAUDE_ROLE"),
                                        cwd=a.cwd), end="")
        return 0
    if a.role == "deviation-log-path":
        # issue #2348: prints the exact shard path this session's own
        # deviation-log append belongs in -- a session never computes the
        # shard id itself, so two sessions' formulas can never drift apart.
        print(_deviation_log_path(a.issue, role=os.environ.get("CLAUDE_ROLE"), cwd=a.cwd))
        return 0
    if a.role == "priorities-log":
        # issue #2637: same reader shape as consult-log/deviation-log --
        # reconstructs the pre-sharding single-file
        # docs/reports/product/priorities.md view (legacy content first,
        # then new per-entry shards in filename order).
        print(_priorities_aggregate(a.issue, cwd=a.cwd), end="")
        return 0
    if a.role == "priorities-path":
        # issue #2637: prints the path THIS call's new priorities entry
        # belongs in -- unlike deviation-log-path, every call mints a
        # fresh path (one file per entry, not per session; see
        # priorities.py's module docstring), so this is safe to call again
        # for a second, unrelated entry in the same session.
        print(_priorities_entry_path(a.issue, cwd=a.cwd))
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
            sys.exit("사용법: spawn.py watch --issue <n> [--session <slug>] "
                     "[--stall-timeout <분>], 또는 spawn.py watch --all")
        # 이슈 #554: `kill <역할> --issue N` 과 같은 위치 인자 문법을
        # `watch` 에도 허용한다 — `--session` 이 이미 있으면 그게 우선한다.
        watch_session = a.watch_session or a.task
        if a.rearm:
            return _rearm_watcher_detached(a.issue, watch_session, a.stall_timeout,
                                            repo=_repo_identity(a.cwd), cwd=a.cwd)
        return _watch(a.issue, watch_session, a.stall_timeout, follow=a.follow,
                      repo=_repo_identity(a.cwd), max_wait_min=a.max_wait,
                      self_heal=a.self_heal)
    if a.role == "clean":
        return roster_clean(_workspace_base(), a.issue, Path(a.cwd).resolve())
    if a.role == "doctor":
        # 훅 발화 실측. 버전마다 한 번 — 룰북 집행의 전제조건이다.
        return doctor()
    if a.role == "await-approval":
        # Issue #2129: the deterministic in-session approval wait a
        # checkpoint-mode session runs at its phase-1/phase-2 boundary.
        # Positional `task` doubles as the session slug (same convention
        # as kill/watch); --session wins when both are given.
        wait_session = a.watch_session or a.task
        if a.issue is None or not wait_session:
            sys.exit("usage: spawn.py await-approval --issue <n> --session "
                     "<session> [--timeout <s>] [--poll-interval <s>] [-C <dir>]")
        return await_approval_cmd(a.cwd, a.issue, wait_session,
                                  timeout=a.timeout,
                                  interval=a.poll_interval)
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
    if a.role == "acceptance-sweep":
        # issue #2229: lint 는 이슈 하나씩만 검사한다 — 필지 후 아무도 그
        # 이슈에 lint 를 안 돌리면 조용히 스폰불가 상태로 남는다(#2229 관측:
        # 다섯 건이 우연한 발견으로만 잡혔다). 이 커맨드는 열린 이슈 전체를
        # 한 번에 훑어 지금 스폰 불가능한 것을 전부 보고한다(closure-sweep,
        # needs-due 와 같은 단발 스윕 커맨드 관례).
        sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
        import acceptance_gate as _acceptance_gate
        root = Path(a.cwd).resolve()
        bad_by_issue = _acceptance_gate.sweep(root)
        if bad_by_issue is None:
            print("acceptance-sweep: 이슈 목록을 읽을 수 없다 (gh 실패) — 판정 불가",
                  file=sys.stderr)
            return 1
        print(_acceptance_gate.format_sweep_report(bad_by_issue))
        return 1 if bad_by_issue else 0
    if a.role == "drive":
        # 보드가 지목하는 세션을 하나씩, 멈출 때까지.
        require_board(a.cwd, a.no_contract)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_doctor()
        ensure_target_remote(a.cwd, a.unattended)
        return drive(a.cwd, a.unattended, a.limit)
    if not a.role:
        print("\n".join(status(a.cwd)))
        return 0
    if not _via_skills:
        # 이슈 #2572: --skills 가 유일한 스폰 형태다 — 은퇴한 두 형태
        # (역할-포지셔널 `spawn.py <role> "<task>"`, 맨 태스크 `spawn.py
        # "<task>"`(이슈 #2555))는 둘 다 `_via_skills` 가 여전히 False 인 채
        # 여기 도달한다(위의 `--skills` 분기만 그 플래그를 True 로 뒤집는다,
        # 그리고 그 분기는 이미 `a.role`/`a.task` 를 스킬-슬러그/태스크로
        # 재배정하고 지나간다) — 위의 서브커맨드 분기(`init`/`ps`/`drive`/...)
        # 는 모두 그 안에서 return/sys.exit 하므로 여기까지 안 온다. 둘 다
        # `--skills` 를 이름하는 메시지로 거절한다.
        sys.exit(
            "spawn.py 는 이제 --skills 로만 세션을 스폰한다(이슈 #2572) — "
            "역할-포지셔널 스폰(`spawn.py <role> \"<task>\"`)과 맨 태스크 스폰"
            "(`spawn.py \"<task>\"`, 이슈 #2555)은 둘 다 은퇴했다. 사용법: "
            "spawn.py --skills <skill>[,<skill>...] \"<task>\" --issue <n>"
        )
    if a.checkpoint and a.single_phase:
        sys.exit("--checkpoint and --single-phase are mutually exclusive: "
                 "single-phase skips the proposal round entirely, checkpoint "
                 "pauses on it (issue #2129)")
    if a.checkpoint and a.issue is None:
        sys.exit("--checkpoint requires --issue <n>: the approval needle is "
                 "`APPROVE issue-<n>/<role>` on that issue (issue #2129)")

    if a.dry_run:
        # --dry-run 은 세션을 안 태운다. 계약 검사는 버려질 세션을 막으려는
        # 것이므로 아무것도 안 띄우는 호출까지 막을 이유가 없다 — 그래도
        # 드라이런은 막는다: 레포가 자기 훅을 들고 있으면 그건 세션을 띄우기
        # 전에 알아야 할 사실이지, 띄우고 나서 알 일이 아니다. attempt 기록
        # 대상이 아니므로(세션을 안 태움) 아래 non-dry-run 분기와 따로 돈다.
        # 이슈 #2395: cwd 가 존재하지 않음/git 레포 아님/레포 루트 아님 세
        # 경우를 require_board 의 "approvers.md 없다" 증상보다 먼저, 원인
        # 그대로 이름 붙여 멈춘다.
        require_repo_root(a.cwd, a.issue)
        # 이슈 #2395 CHANGES(PR #2404 conformance review, REQ-CWD-WRONGREPO):
        # require_acceptance_gate/require_requirement_linkage 는 이슈
        # 리서치 결과에 따라 여기서 거절할 수 있다 — 레포/이슈 해석 echo
        # 를 그 두 게이트보다 앞으로 옮겨, 거절되는 경우에도 오케스트레
        # 이터가 어느 레포/이슈로 해석됐는지 본다.
        _resolve_and_echo_issue(a.role, a.cwd, a.issue)
        require_board(a.cwd, a.no_contract or a.dry_run)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_acceptance_gate(a.cwd, a.issue)
        require_requirement_linkage(a.cwd, a.issue)
        out = role_settings(a.role, a.cwd)
        # MUSTER_SKILL_MODEL / role_model.txt (이슈#93): spawn_cmd 는 이
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
    # 이슈 #2291 CHANGES(PR #2371 conformance review R2/R4): require_board()
    # 부터 require_requirement_linkage() 까지 네 계약 게이트 — 그중 둘
    # (require_acceptance_gate/require_requirement_linkage)은 gh api 를
    # 불러 sys.exit() 로 fail-closed 할 수 있다 — 가 attempt 기록보다 앞에
    # 있으면, 이 이슈가 고치려던 바로 그 traceless halt 를 한 겹 더 이르게
    # 재현한다(#2305 의 같은 결함이 #2365 에도 R1/R3 로 이미 기록됨). 그래서
    # attempt 기록을 이 네 게이트보다도 앞으로, "여기부터 _spawn_one() 전체가
    # 부트스트랩(워크스페이스/로스터/세션 로그가 아직 없는) 구간"이라는
    # 이 분기의 맨 위로 옮긴다. `--issue` 없는 ad-hoc 스폰은 애초에
    # 로스터에 등록되지 않으므로(워치독이 대조할 대상이 없다) 추적하지 않는다.
    attempt_id = (_record_spawn_attempt(a.issue, a.role, os.getpid(), cwd=a.cwd)
                  if a.issue is not None else None)
    try:
        # 이슈 #2395: 위 dry-run 분기와 같은 이유로 네 계약 게이트보다
        # 먼저 — 이 게이트도 attempt_id 기록 뒤(traceless halt 방지)에
        # 있어야 한다.
        require_repo_root(a.cwd, a.issue)
        # 이슈 #2395 CHANGES: 위 dry-run 분기와 같은 이유로 이 게이트도
        # require_acceptance_gate/require_requirement_linkage 보다 먼저
        # — 그 두 게이트가 거절해도 echo 는 이미 찍혀 있다. 결과
        # (issue_data, 또는 조회 실패 시 None)를 아래 `_spawn_one()`에
        # 그대로 넘겨 gh 재조회를 피한다(acceptance check 2).
        _issue_data = _resolve_and_echo_issue(a.role, a.cwd, a.issue)
        require_board(a.cwd, a.no_contract)
        require_no_repo_config(a.cwd, a.trust_repo_config)
        require_acceptance_gate(a.cwd, a.issue)
        require_requirement_linkage(a.cwd, a.issue)
        require_doctor()
        ensure_target_remote(a.cwd, a.unattended)
        # 이슈 #2152: 기본값 반전 — 아무 플래그도 없으면 이제 single-phase
        # (build-now) 다. --two-phase 가 명시적으로 오늘까지의 proposal-first
        # 흐름으로 되돌린다. --checkpoint 는 phase-1 제안에서 멈춰야 하므로
        # (그 경계가 곧 승인 검사다) 다른 플래그와 무관하게 언제나 two-phase로
        # 취급한다 — 안 그러면 체크포인트 세션이 멈출 제안 라운드 자체가
        # build-now 로 건너뛰어져 버린다. --single-phase 는 이제 no-op
        # 별칭이다: 기본값이 이미 같은 결과이므로 값 자체는 계산에 넣지 않는다.
        effective_single_phase = not a.two_phase and not a.checkpoint
        return _spawn_one(a.cwd, a.role, a.task, a.unattended, a.issue,
                          bounded=a.issue is not None,
                          stall_timeout_min=a.stall_timeout,
                          no_wait=a.no_wait,
                          despite_returned=a.despite_returned,
                          model=a.model, skills=a.skills,
                          single_phase=effective_single_phase,
                          max_turns=a.max_turns,
                          allow_unlimited_turns=a.allow_unlimited_turns,
                          checkpoint=a.checkpoint,
                          force_adhoc_task=a.force_adhoc_task,
                          attempt_id=attempt_id,
                          skills_branch_identity=_skills_branch_identity,
                          issue_data=_issue_data)
    except (SystemExit, Exception) as e:
        # 이슈 #2291: `_fetch_or_halt()`류의 fail-closed halt(sys.exit)와,
        # 이 구간의 아무 uncaught exception 이나 — 컨슈머가 stdout/stderr 를
        # 파이프로 삼켜도(`2>&1 | tail`) durable 하게 남긴다. 이미
        # `_record_spawn_outcome()`을 (성공으로) 쓴 시도는 그 지점 이후에
        # 다른 예외가 나도 여기서 다시 안 건드린다 — halt 이든 아니든 한
        # attempt_id 에는 처분이 하나뿐이어야 sweep 쪽 판정이 단순하다.
        if attempt_id is not None:
            reason = (e.code if isinstance(e, SystemExit) else
                      f"{type(e).__name__}: {e}")
            reason = reason if isinstance(reason, str) else str(reason)
            _record_spawn_outcome(attempt_id, "halted", reason)
        raise


_GH_TOKEN_CACHE: str | None = None


_FETCHED_THIS_SPAWN: dict[str, float] = {}

# 이슈 #1507 — work_dir 별 부트스트랩 fetch 기록(origin/main sha + fetch
# 시각). 세션이 절대-부재 주장을 쓰기 전에 이 기록이 이미 있어야 한다.
_BOOTSTRAP_FETCH_RECORD: dict[str, dict] = {}

# 이슈 #2159: gitignore 돼 클론에 안 실리는 로컬 전용 의존성 디렉터리의
# 초기 집합.
_LOCAL_DEP_DIR_NAMES = ("node_modules", ".venv", "vendor")


def _find_local_dep_dirs(origin: str) -> dict[str, list[Path]]:
    """`origin` 루트와 그 바로 아래 한 단계 하위 디렉터리에서
    `_LOCAL_DEP_DIR_NAMES` 를 찾는다. 읽기만 한다 — 아무것도 쓰지 않는다."""
    root = Path(origin)
    found: dict[str, list[Path]] = {name: [] for name in _LOCAL_DEP_DIR_NAMES}
    candidates = [root]
    try:
        candidates += [p for p in root.iterdir()
                       if p.is_dir() and not p.name.startswith(".")]
    except OSError:
        pass
    for base in candidates:
        for name in _LOCAL_DEP_DIR_NAMES:
            d = base / name
            if d.is_dir():
                found[name].append(d)
    return found


def local_dependency_env(origin: str, work: str) -> dict[str, str]:
    """이슈 #2159: `work`(격리 작업 클론)에는 없고 `origin`(스폰을 부른
    체크아웃)에만 있는 로컬 전용 의존성 디렉터리를 가리키는 env var 를
    만든다. `work` 안으로 파일을 복사하거나 심볼릭링크하지 않는다 — 격리
    보장(이슈 #513)은 그대로 두고, 세션 env 에 원격 조회용 포인터만
    심는다.

    node_modules -> `NODE_PATH` (후보가 여럿이면 `os.pathsep` 로 이어
    붙인다 — Node 자신이 NODE_PATH 를 그렇게 파싱한다).
    .venv -> `VIRTUAL_ENV`, 그리고 site-packages 를 유일하게 특정할 수
    있을 때만 `PYTHONPATH` 도 함께. .venv 후보가 둘 이상이면 어느
    인터프리터가 맞는지 알 수 없으므로 통째로 건너뛴다.
    vendor/ 는 생태계마다(Go/PHP/Ruby/...) 쓰는 lookup var 가 서로 달라
    하나로 정할 수 없다 — 탐지는 하되 env 는 절대 만들지 않는다.

    `origin` 과 `work` 가 같은 경로면(자기 자신을 스폰 대상으로 재사용)
    빈 dict. `work` 의 같은 상대경로에 이미 그 디렉터리가 있으면(트래킹된
    vendored 디렉터리였거나, 이전 재스폰이 이미 그 자리에 설치해 뒀거나)
    그 항목은 만들지 않는다 — 이미 있는 걸 다른 경로로 덮어쓰면 버전이
    갈릴 수 있다."""
    origin_p = Path(origin).resolve()
    work_p = Path(work).resolve()
    if origin_p == work_p:
        return {}
    found = _find_local_dep_dirs(str(origin_p))

    def _not_in_work(d: Path) -> bool:
        try:
            rel = d.relative_to(origin_p)
        except ValueError:
            return True
        return not (work_p / rel).exists()

    env: dict[str, str] = {}
    node_dirs = [d for d in found["node_modules"] if _not_in_work(d)]
    if node_dirs:
        env["NODE_PATH"] = os.pathsep.join(str(d) for d in node_dirs)
    venvs = [d for d in found[".venv"] if _not_in_work(d)]
    if len(venvs) == 1:
        venv = venvs[0]
        env["VIRTUAL_ENV"] = str(venv)
        site_pkgs = sorted(venv.glob("lib/python*/site-packages"))
        if len(site_pkgs) == 1:
            env["PYTHONPATH"] = str(site_pkgs[0])
    # vendor/: 탐지만 하고 env 는 만들지 않는다(생태계별 lookup var 불명).
    return env


def _set_origin_head(work_dir: str) -> subprocess.CompletedProcess:
    """`origin/HEAD` 를 원격의 실제 기본 브랜치로 다시 계산한다.

    issue #2383 (#2379 근본원인 추적): `_base()`(board.py)는 `origin/HEAD`
    가 **존재하기만 하면** 그 값을 그대로 신뢰하고, 없을 때만
    `origin/main`/`origin/master` 로 폴백한다 — 존재하지만 오래된 값은
    걸러내지 않는다. 신규 클론 경로는 clone 직후 이 재계산을 이미
    거치지만(issue #221), **재사용** 경로(cwd 가 이미 이 워크스페이스이거나
    기존 워크스페이스를 fetch 만 하는 두 분기)는 `fetch`만 하고 이 재계산을
    건너뛰어 왔다 — 원격 기본 브랜치가 바뀌었거나 최초 set-head 가 조용히
    실패했던 워크스페이스는 재사용될 때마다 오염된 `origin/HEAD` 를 계속
    물고 간다. `_fetch_or_halt`의 `after=` 로 세 경로(신규/재사용 2곳)
    모두에서 fetch 직후 매번 호출한다."""
    return subprocess.run(["git", "-C", work_dir, "remote", "set-head", "origin", "-a"],
                          capture_output=True, text=True)


def checkout_staleness(root: Path = ROOT, fetch: bool = True) -> dict:
    """이슈 #2506: 이 코드(`root` — 보통 `spawn.ROOT`, 게이트가 로드된
    체크아웃 그 자체) 가 자신의 origin 대비 뒤처졌는지 검사한다.

    `merge_gate.staleness_for_pr()`(PR 브랜치가 base 대비 뒤처졌는지)와는
    다른 축이다 — 이건 게이트를 실행 중인 파이썬 코드 자체의 신선도다.
    2026-08-26 사고: 로컬 consult-trace 커밋이 쌓여 `main` 이 origin 을
    fast-forward 할 수 없게 됐고, 그 체크아웃에서 돈 `merge_gate.py` 가
    이미 고쳐진 `_exempt_own_role` 을 구버전으로 읽어 확신에 찬 오답을
    냈다(#2444 가 되돌아온 것처럼 보이는 유령 결함).

    `fetch=True`(기본) 면 먼저 `git fetch origin` 을 시도한다 — best-effort,
    실패해도 마지막으로 알려진 `origin/HEAD` 로 판정한다(오프라인에서 게이트
    전체를 막는 게 더 나쁘다). 작업 트리는 절대 건드리지 않는다 — reset/
    checkout/merge 없음, fetch 와 비교뿐(이슈의 must-not).

    `origin/HEAD` 를 못 구하면(원격 없는 합성 테스트 저장소, 이슈가 정의한
    empty state) `checked: False` 로 판정을 보류한다 — 불확실을 stale 로
    단정하면 legitimately-current 체크아웃까지 막는다(이슈의 must-not).

    Returns `{"checked": bool, "stale": bool, "behind": int,
    "fetch_ok": bool, "detail": str}`."""
    fetch_ok = True
    if fetch:
        r = subprocess.run(["git", "-C", str(root), "fetch", "--quiet", "origin"],
                           capture_output=True, text=True)
        fetch_ok = r.returncode == 0
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode != 0 or not head.stdout.strip():
        return {"checked": False, "stale": False, "behind": 0,
                "fetch_ok": fetch_ok, "detail": "HEAD 를 resolve 할 수 없다"}
    origin_head = subprocess.run(["git", "-C", str(root), "rev-parse", "origin/HEAD"],
                                 capture_output=True, text=True)
    if origin_head.returncode != 0 or not origin_head.stdout.strip():
        return {"checked": False, "stale": False, "behind": 0,
                "fetch_ok": fetch_ok, "detail": "origin/HEAD 를 resolve 할 수 없다"}
    local_sha = head.stdout.strip()
    origin_sha = origin_head.stdout.strip()
    if local_sha == origin_sha:
        return {"checked": True, "stale": False, "behind": 0,
                "fetch_ok": fetch_ok, "detail": ""}
    ancestor = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", origin_sha, local_sha],
        capture_output=True, text=True)
    if ancestor.returncode == 0:
        # local 이 origin 을 포함하고 앞서 있을 뿐(정상적인 WIP) -- 이
        # 이슈가 겨냥한 실패 모드가 아니다.
        return {"checked": True, "stale": False, "behind": 0,
                "fetch_ok": fetch_ok, "detail": ""}
    if ancestor.returncode not in (0, 1):
        # `--is-ancestor` 는 0(맞다)/1(아니다) 만 진짜 판정이다 -- 그 밖의
        # 코드는 git 자체가 실패한 것(예: 손상된 오브젝트)이라, 1 과
        # 똑같이 취급해 "뒤처지지 않았다"로 단정하면 이 이슈가 겨냥한
        # "확신에 찬 오답"을 판정 로직 안에서 그대로 재현하게 된다.
        return {"checked": False, "stale": False, "behind": 0, "fetch_ok": fetch_ok,
                "detail": f"merge-base --is-ancestor 판정 실패 — {ancestor.stderr.strip()[:200]}"}
    count = subprocess.run(
        ["git", "-C", str(root), "rev-list", "--count", f"{local_sha}..{origin_sha}"],
        capture_output=True, text=True)
    if count.returncode != 0 or not count.stdout.strip().isdigit():
        return {"checked": False, "stale": False, "behind": 0, "fetch_ok": fetch_ok,
                "detail": f"뒤처진 커밋 수를 셀 수 없다 — {count.stderr.strip()[:200]}"}
    behind_n = int(count.stdout.strip())
    return {"checked": True, "stale": behind_n > 0, "behind": behind_n,
            "fetch_ok": fetch_ok,
            "detail": (f"체크아웃({root})이 origin 대비 {behind_n}개 커밋 뒤처졌다 "
                       f"(로컬={local_sha[:12]} origin={origin_sha[:12]})")}


def issue_workspace(cwd: str, issue: int | None, role: str) -> str:
    """이슈 스폰마다 on-the-record 소유의 격리 클론을 만든다.

    산출물이 PR 로만 돌아오는 모델에서 세션이 사용자의 체크아웃을
    공유할 이유가 없다 — 공유하면 동시 스폰 둘이 같은 .git/index 와 현재
    브랜치를 두고 경합한다(실측: issue-45 와 issue-59 coding 세션이 한
    트리에서 충돌 직전까지 갔다). 로컬에서 클론하고 origin 을 실제 원격으로
    되돌려 push/gh 가 GitHub 로 가게 한다. 재스폰이면 기존 작업 디렉토리를
    fetch 로 재사용한다 — 진행 중이던 브랜치 작업을 버리지 않는다.

    Issue #2293 (scope addition, consumer incident 2026-08-25): an adhoc
    (`issue is None`) caller gets the same clone-isolation, keyed by pid
    instead of an issue number — there is no (issue, role) identity to
    resume across respawns for an adhoc task, so it always takes the
    fresh-clone path below rather than the reuse branches.
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
    # 경로라 세션의 Write 가 전부 거부된다(실측: phase 2 가 코드 한 줄
    # 못 쓰고 $2.68 을 태웠다). 기본은 ~/.tokenmaxxxer/work, 오버라이드는
    # MUSTER_WORK_DIR.
    work_base = _workspace_base()
    # 이름은 origin 의 레포명에서 뽑는다 — 디렉토리 이름(slug)을 쓰면
    # 워크스페이스를 -C 로 다시 넘겼을 때 이름이 이중으로 붙는다(실측:
    # ...-issue-45-coding-issue-45-coding). origin 은 위에서 이미 읽었다.
    repo_name = re.sub(r"\.git$", "", origin.rstrip("/").rsplit("/", 1)[-1]) or slug(cwd)
    work = (work_base / f"{repo_name}-issue-{issue}-{role}" if issue is not None
            else work_base / f"{repo_name}-adhoc-{role}-{os.getpid()}")
    # 이슈 #2417 (before-landing hunt): fresh-clone 분기 앞에만 두면 재사용
    # 분기(cwd==work 자기 재사용, 기존 .git 재사용) 두 곳은 여전히
    # `_fetch_or_halt` 로 바로 들어가 디스크가 거의 다 찼을 때 clone 이 아니라
    # fetch 에서 파묻힌 에러로 실패한다 — 같은 실패가 경로만 바뀐 것. 여기
    # 최상단에서 한 번 확인하면 세 분기(자기 재사용/기존 워크스페이스
    # 재사용/신규 clone) 모두 clone 이든 fetch든 쓰기 전에 걸린다.
    _spawn_capacity_check(work)
    # cwd 가 이미 이 (이슈,역할)의 워크스페이스면 그대로 쓴다 — 중첩 금지.
    if src == work.resolve():
        _fetch_or_halt(str(src), "재사용 워크스페이스",
                       after=lambda: _set_origin_head(str(src)))
        _write_role_sidecar(str(src), issue, role)
        return str(src)
    if issue is None and (work / ".git").exists():
        # Issue #2293 (before-landing warrant hunt): an adhoc task has no
        # identity to resume across respawns -- unlike the issue-scoped
        # reuse branch below, a leftover directory at this pid-keyed path
        # (a crashed prior adhoc spawn, or the OS reusing the pid once
        # its number wraps) must never be silently inherited. Wipe it and
        # fall through to the fresh-clone path, matching this function's
        # own docstring claim that adhoc always takes it.
        shutil.rmtree(work, ignore_errors=True)
    if (work / ".git").exists():
        # 이슈 #2417: origin 비교보다 먼저 — 여기 있는 `.git` 이 이전 clone
        # 이 ENOSPC 등으로 중간에 죽어 남긴 partial tree 일 수 있다. 그
        # 경우를 "남의 레포다(origin 불일치)"로 오판하면 실제 원인(디스크
        # 부족)도, 해법(지우고 재시도)도 안 보인다.
        if _workspace_clone_incomplete(work):
            sys.exit(
                f"워크스페이스가 불완전하다: {work} — 이전 clone 이 도중에 실패해 "
                f"(디스크 공간/inode 부족 등) 남의 레포가 아니라 partial 상태의 "
                f"미완성 클론으로 남아 있다. 해결: 지우고 재시도하라 — rm -rf {work}"
            )
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
        _fetch_or_halt(str(work), "재사용 워크스페이스",
                       after=lambda: _set_origin_head(str(work)))
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
    _fetch_or_halt(str(work), "신규 워크스페이스",
                   after=lambda: _set_origin_head(str(work)))
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


def _mechanical_rebase(cwd: str, push: bool = True) -> dict:
    """Issue #2403 — bring the branch already checked out at `cwd` current
    with `_base(cwd)` via plain git, no LLM session. Only the conflict-free
    case is handled mechanically: a rebase that needs conflict resolution
    is aborted and reported so the caller falls back to a real
    session (conflict resolution is a judgment call, not mechanical --
    rationale in docs/issue-2403/reports/implementation.md).

    Returns `{"status": "up-to-date"|"rebased"|"conflict"|"error",
    "behind": int, "detail": str}`. `push` uses `--force-with-lease`, safe
    against a concurrent push this process didn't see."""
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    br_r = git("symbolic-ref", "--short", "-q", "HEAD")
    if br_r.returncode != 0 or not br_r.stdout.strip():
        return {"status": "error", "behind": 0,
                "detail": "HEAD 가 브랜치를 가리키지 않는다(분리 HEAD) — rebase 대상 아님"}
    branch = br_r.stdout.strip()
    fetch = git("fetch", "origin")
    if fetch.returncode != 0:
        return {"status": "error", "behind": 0,
                "detail": f"git fetch origin 실패: {fetch.stderr.strip()}"}
    base = _base(cwd)
    behind = git("rev-list", "--count", f"HEAD..{base}")
    behind_n = (int(behind.stdout.strip())
                if behind.returncode == 0 and behind.stdout.strip().isdigit() else 0)
    if behind_n == 0:
        return {"status": "up-to-date", "behind": 0,
                "detail": f"{branch} 는 이미 {base} 기준 최신이다"}
    rb = git("rebase", base)
    if rb.returncode != 0:
        git("rebase", "--abort")
        return {"status": "conflict", "behind": behind_n,
                "detail": (f"{branch} 를 {base} 위로 rebase 하다 충돌 — 기계적으로 "
                            f"처리할 수 없다(rebase 는 abort 했다). 충돌 해소는 판단이 "
                            f"필요해 role 세션이 있어야 한다.")}
    if push:
        pushed = git("push", "--force-with-lease", "origin", f"HEAD:{branch}")
        if pushed.returncode != 0:
            return {"status": "error", "behind": behind_n,
                    "detail": f"rebase 는 됐지만 push 실패: {pushed.stderr.strip()}"}
    return {"status": "rebased", "behind": behind_n,
            "detail": f"{branch} 를 {base} 위로 rebase" + (" 하고 push 했다" if push else " 했다(push 안 함)")}


def mechanical_rebase_cli(cwd: str) -> int:
    """`spawn.py rebase -C <cwd>` — issue #2403 진입점. `_mechanical_rebase()`
    결과를 사람이 읽을 한 줄로 찍고, `up-to-date`/`rebased` 는 0, `conflict`
    는 (세션이 필요하다는 신호로) 2, 그 외 오류는 1 을 돌려준다."""
    result = _mechanical_rebase(cwd)
    print(f"[rebase] status={result['status']} behind={result['behind']} — {result['detail']}")
    if result["status"] in ("up-to-date", "rebased"):
        return 0
    if result["status"] == "conflict":
        return 2
    return 1
def _recut_corrupted_branch(cwd: str, br: str, base: str):
    """`br`(예: `issue-<n>/<role>`)을 같은 이름을 유지한 채, 지금 잡힌
    `merge-base(br, base)`를 새 base 로 밀어 재컷한다 (issue #2402).

    `_recut_absorbed_branch`(issue #784)와는 정반대 상황을 다룬다: 그쪽은
    "content 가 이미 base 에 흡수돼 버려도 되는" 브랜치라 base 로
    리셋하고, 여기는 "content 는 유효한데 spawn 시점 branch-cut 이 잘못된
    (오래된/무관한) parent 에서 갈라져 나온"(issue #2379) 브랜치라 그
    content(브랜치 자신의 커밋들)를 버리지 않고 올바른 base 위로
    옮겨 심는다 — `git rebase --onto`. 브랜치 이름이 그대로이므로 이
    함수가 끝난 뒤 호출자가 같은 이름으로 origin 에 force-push 하면 기존
    PR 은 (새로 열 필요 없이) 그 자리에서 깨끗한 merge-base 를 얻는다.

    반환값은 최종 git 호출(checkout 실패 시 checkout, 아니면 rebase)의
    CompletedProcess — returncode 로 성공 여부를 본다."""
    def git(*a):
        return subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
    checkout = git("checkout", "-B", br, f"origin/{br}")
    if checkout.returncode != 0:
        return checkout
    merge_base = git("merge-base", br, base)
    if merge_base.returncode != 0:
        return merge_base
    old_base = merge_base.stdout.strip()
    if not old_base:
        return merge_base
    return git("rebase", "--onto", base, old_base, br)


_ACCEPTANCE_CHECK_LINE = re.compile(r"^\s*-\s*check\s*:\s*(.+)$", re.MULTILINE)

_STORYBOARD_RE = re.compile(r"storyboard|스토리보드", re.IGNORECASE)


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


# The checklist table. One row per named precondition; `admission_gate()`
# is the only loop. Tests append synthetic rows here to prove that adding
# an item requires no new gate code (issue #2100 acceptance).
ADMISSION_CHECKS: list[tuple] = [
    ("approve-token", _admission_check_approve_token),
    ("directive-completeness", _admission_check_directive_completeness),
    ("watch-registration", _admission_check_watch_registration),
    ("budget-caps", _admission_check_budget_caps),
    ("board-validity", _admission_check_board_validity),
    ("degenerate-task", _admission_check_degenerate_task),
]


_ISSUE_NOT_PRE_RESOLVED = object()


def _resolve_and_echo_issue(role: str, cwd: str, issue: int | None) -> dict | None:
    """이슈 #2395 CHANGES(PR #2404 conformance review, REQ-REPRO/REQ-CWD-WRONGREPO):
    레포/이슈 해석 echo 를 `main()`이 `require_acceptance_gate`/
    `require_requirement_linkage` 를 부르기 *전에* 찍는다 — 그 두 게이트가
    거절해도(예: 이슈의 원인 사례인 "요구 연결 없음") 오케스트레이터는
    여전히 어느 레포/이슈로 해석됐는지 본다. 이전에는 이 echo 가
    `_spawn_one()` 안에서만 돌아, 그 두 게이트보다 뒤에 있었다(게이트가
    막으면 echo 자체가 안 찍힘).

    `--issue` 없는 호출은 검사 대상이 없다 — `None` 을 그대로 돌려준다.
    `gh` 조회 실패는 조용히 넘기지 않고 "확인 실패"라고 그대로 찍는다
    (확인 불가를 확인됨으로 읽지 않는다, 아래 `_spawn_one()`과 동일 원칙).
    """
    if issue is None:
        return None
    issue_data = None
    try:
        sys.path.insert(0, str((ROOT / "gates").resolve()))
        import gh_rest as _gh_rest
        issue_data = _gh_rest.fetch_issue(Path(cwd), issue)
    except Exception:
        issue_data = None
    resolved_owner = issue_data.get("owner") if issue_data else None
    resolved_repo = issue_data.get("repo") if issue_data else None
    title = issue_data.get("title") if issue_data else None
    if resolved_owner and resolved_repo:
        resolved_line = (f"해석된 레포/이슈: {resolved_owner}/{resolved_repo}#{issue}"
                          + (f" — {title}" if title else "") + "\n")
    else:
        resolved_line = (f"해석된 레포/이슈: 확인 실패 — cwd({cwd})가 가리키는 "
                          f"레포에서 이슈 #{issue} 를 못 읽었다(gh 조회 실패).\n")
    print(f"[{role}] {resolved_line.strip()}")
    return issue_data


def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
               issue: int | None = None, bounded: bool = False,
               stall_timeout_min: float = 5.0, no_wait: bool = False,
               despite_returned: bool = False, model: str | None = None,
               # 이슈 #2574: 이 기본값은 CLI 진입점(main())이 계산하는
               # `effective_single_phase`(--two-phase/--checkpoint 둘 다
               # 없을 때 True)와 항상 같아야 한다 — #2152 는 그 계산을
               # main() 안에만 넣고 이 함수 자신의 기본값은 고치지 않아,
               # `_spawn_one()`을 직접 부르는 네 호출부(옵저버 자동스폰)가
               # 값을 안 넘기면 여전히 예전 two-phase 로 떨어지는 조용한
               # 분기를 만들었다. 여기서 True 로 맞춰 두면, single_phase
               # 를 아예 안 넘기는 어떤 호출부(지금의 넷이든 앞으로 생길
               # 다섯 번째든)나 CLI 나 항상 같은 값을 받는다 — 갈라짐이
               # "나중에 발견되는" 게 아니라 "애초에 생길 수 없는" 구조가
               # 된다. 진짜 two-phase 가 필요한 호출부는 이 기본값에
               # 기대지 말고 반드시 `single_phase=False`(또는
               # `checkpoint=True`)를 명시해야 한다.
               skills: str | None = None, single_phase: bool = True,
               max_turns: int | None = None,
               allow_unlimited_turns: bool = False,
               checkpoint: bool = False,
               force_adhoc_task: bool = False,
               attempt_id: str | None = None,
               skills_branch_identity: tuple[str, str] | None = None,
               issue_data=_ISSUE_NOT_PRE_RESOLVED) -> int:
    """세션 하나를 띄우고, 무슨 일이 있었는지 원장에 남기고, 처분을 말한다.

    main() 과 drive() 가 같은 몸통을 쓴다 — 드라이버가 따로 스폰 경로를 들고
    있으면 둘이 갈라지고, 갈라진 쪽이 조용히 게이트 하나를 빠뜨린다.

    `attempt_id`(이슈 #2291, 옵션): main() 의 CLI 진입점이 네트워크/워크스페이스
    작업 전에 이미 `_record_spawn_attempt()`로 남긴 durable 시도 id — 세션
    로그 경로가 정해지는 시점(아래)에 그 시도의 성공 처분을 잇는다. halt
    처분은 이 함수가 아니라 호출자(main())가 SystemExit/Exception 을 잡아
    남긴다 — halt 는 이 함수 안 어디서든(admission_gate, 스킬 해석,
    `issue_workspace()`/`checkout_issue_branch()`의 `_fetch_or_halt` 등)
    일어날 수 있어, 그 지점들 하나하나를 계측하는 대신 호출부를 감싸는 쪽이
    새 halt 지점이 생겨도 놓치지 않는다. `None`(다른 호출부 — 예: 워치독
    자동-재스폰의 `_respawn_or_cap()`)이면 이 인자와 관련된 아무 것도 안
    쓴다 — 오늘의 동작 그대로.

    `issue_data`(이슈 #2395 CHANGES, 옵션): `main()`이 게이트 앞에서 이미
    `_resolve_and_echo_issue()`로 fetch-and-echo 를 끝냈으면 그 결과
    (dict 또는 조회 실패 시 `None`)를 여기로 넘긴다 — 이 함수는 그 값을
    재사용하고 echo 를 다시 찍지 않는다(gh 왕복 중복 방지). 기본값
    `_ISSUE_NOT_PRE_RESOLVED` 는 "아직 아무도 안 찍었다"는 뜻으로, 이
    함수가 직접 fetch 하고 echo 도 직접 찍는다 — `_respawn_or_cap()` 등
    `main()`을 거치지 않는 호출부의 오늘까지 동작 그대로."""
    # Issue #2100: pre-spawn admission checklist. Runs before ANY side
    # effect (workspace clone, branch, roster/index writes, session
    # process) — a refusal names the missing precondition, writes one
    # `admission_refused` ledger event (inside `admission_gate()`), and
    # returns without creating anything. Deterministic and non-retryable:
    # the caller must publish the missing precondition, not retry.
    # 이슈 #2186: admission_gate 자체가 첫 계측 대상이라, 클리어는 그 앞에서
    # 한 번만 — 여기서 안 하면 admission 을 잰 뒤 아래 옛 clear() 가 그
    # 기록을 지워버린다.
    _BOOTSTRAP_TIMING.clear()
    resolved_max_turns = _resolve_session_max_turns(max_turns)
    with _timed("admission"):
        _refused_item = admission_gate({
            "cwd": cwd, "role": role, "issue": issue, "task": task,
            "single_phase": single_phase, "skills": skills,
            "max_turns": resolved_max_turns,
            "allow_unlimited_turns": allow_unlimited_turns,
            "checkpoint": checkpoint,
            "force_adhoc_task": force_adhoc_task,
        })
    if _refused_item is not None:
        print(f"[{role}] admission refused: missing precondition "
              f"'{_refused_item}' (issue #2100) — no session created, no "
              f"workspace left behind. This refusal is deterministic and "
              f"non-retryable: publish the missing precondition, then "
              f"dispatch again.", file=sys.stderr)
        return 1
    # 이슈 #2382: `core_plugin_dirs()` 는 인자가 없다 — role/cwd/issue 어느
    # 것에도 안 걸리는, core 마켓플레이스 관리 클론(core_root()) pull 하나뿐
    # 이라 admission 만 넘으면(부수효과는 admission 뒤부터, 위 주석) 바로
    # 던져도 안전하다. 예전에는 이 pull 이 skill_resolve/workspace/branch/
    # directive_write/issue_fetch/board_snapshot 을 전부 기다린 뒤 "core"
    # 단계에서 처음 불렸다 — 그 사이 아무 것도 core_plugins 를 안 쓰므로
    # 순수 직렬 대기였다. 여기서 먼저 던지고 아래 "core" 단계에서는 join 만
    # 한다(cross_family 와 같은 패턴) — 그 사이의 거의 전체 부트스트랩과
    # 겹친다.
    _core_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    _core_future = _core_executor.submit(core_plugin_dirs)
    # 이슈 #2001: 크로스-패밀리 스코어링은 이 함수가 받은 원본 task 텍스트를
    # 대상으로 한다 — 아래에서 task 에 여러 안내 문단이 계속 덧붙는데, 그
    # 덧붙은 텍스트(스킬 목록 자체 등)가 스코어링 입력에 섞이면 결정론이
    # 스폰마다 달라진다.
    _cross_family_task_text = task
    # Issue #2135: labeled directive parts for the composition breakdown —
    # every append below registers itself via `_dp()` so the assembled
    # directive's per-source byte counts are printed at each spawn and
    # unit-testable through `composition_breakdown()`.
    _directive_parts: list[tuple[str, str]] = [("base-task", task)]

    def _dp(label: str, text: str) -> str:
        _directive_parts.append((label, text))
        return text
    # Issue #2204: the on-demand section files (populated below, issue
    # spawns only) delivered via --append-system-prompt instead of a
    # workspace-file + inline "Read X when Y" pointer — see
    # `_directive_system_prompt_block()`.
    _directive_section_texts: dict[str, str] = {}
    cross_family_dirs: list[Path] = []
    # 이슈 #2076: skill_judge 자문이 이번 스폰에서 완료됐는지 fail-open
    # 했는지 — role_source 가 skill-repo 가 아니면 자문 자체가 안 불려
    # "not-run" 으로 남는다(아래 ledger_write 필드).
    skill_judge_outcome = "not-run"
    # 이슈 #1742/#1774: --skills 이름 검증(네 소스 모두)은 워크스페이스/
    # 브랜치를 건드리기 전에 끝난다(fail-closed, 요구사항 2) — 아래
    # 워크스페이스 생성보다 먼저 온다.
    with _timed("skill_resolve"):
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
        # 이슈 #2507 (role retirement stage 6): 고정 role->skill 표
        # (`_ROLE_SKILLS`)이 아니라, 역할과 무관하게 항상 적용되는 POLICY
        # 스킬만 여기서 동기로 붙인다 — 과제-맞춤 매칭은 아래 cross_family
        # 자문(비동기)에 전부 넘긴다. 이름 해석은 여전히 워크스페이스/브랜치
        # 생성보다 먼저 온다(모르는 이름이거나 hooks/ 를 들고 있으면 여기서
        # fail-closed, 이슈 #1955 요구사항 그대로).
        skill_registry_root = _skill_repo_root()
        role_source = resolve_static_policy_source(skill_registry_root)
    # 이슈 #2061: skill_judge 자문(BM25 프리필터 + haiku 판단)을 워크스페이스
    # 클론/브랜치 체크아웃(~12s)과 겹치도록 그 전에 먼저 던진다 — 아래
    # "cross_family" 단계에서 join 만 한다. 자문은 읽기 전용(저장소 파일을
    # 건드리지 않는다, `_skill_judge_consult()` 의 override 문구)이라
    # 워크스페이스가 아직 없어도(원본 cwd 로) 안전하게 먼저 돌 수 있다.
    # 이슈 #2507: 이 자문이 이제 role 축 없는 스폰의 "유일한" 과제-맞춤
    # 스킬 소스다(예전엔 고정 표 위에 얹는 add-only 층이었다) — top-K 를
    # 2에서 `_COMPOSED_SKILLS_TOPK` 로 올려, role 이 예전에 주던 만큼의
    # 스킬 개수를 (표 대신 매치로) 계속 받게 한다.
    _cross_family_executor: concurrent.futures.ThreadPoolExecutor | None = None
    _cross_family_future = None
    if issue is not None:
        _cross_family_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        _cross_family_future = _cross_family_executor.submit(
            _cross_family_skill_matches_with_consult,
            _cross_family_task_text, role, _skill_repo_root(), issue, cwd,
            k=_COMPOSED_SKILLS_TOPK,
            home=Path.home(), target_repo_root=Path(cwd))
    if issue is None:
        # Issue #2293 (scope addition, consumer incident 2026-08-25): an
        # adhoc (no --issue) spawn used to run directly in the caller's
        # `-C` cwd -- a degenerate task there left 40 untracked files
        # inside the target repo's checkout and broke an unrelated PR's
        # build. Give it the same clone-isolation an issue-scoped spawn
        # already gets (`issue_workspace()`, keyed by pid here).
        with _timed("adhoc_workspace"):
            cwd = issue_workspace(cwd, issue, role)
        print(f"[{role}] adhoc 격리 작업 디렉토리: {cwd}", file=sys.stderr)
    # 이슈 #2382: adhoc 스폰(issue is None)은 아래 issue-스코프 블록 전체를
    # 건너뛰어 directive_write 가 없다 — 그런 스폰의 board_snapshot 은
    # cwd 가 애초에 안 바뀌므로 아무 것도 기다릴 필요가 없어, 이 두 변수가
    # 여전히 None 이면 (composition_breakdown 직전) 거기서 바로 던진다.
    _board_snapshot_executor: concurrent.futures.ThreadPoolExecutor | None = None
    _board_snapshot_future = None
    if issue is not None:
        root = Path(cwd).resolve()
        # 이슈 #1239: #680 의 거절 게이트를 무조건적 surfacing 으로 대체한다
        # — 처분 안 된 PR 이 있어도 스폰은 결코 막지 않는다(북극-요구#1,
        # never-missed != never-spawn). `--despite-returned` 는 이제 아무
        # 것도 바꾸지 않는 no-op (CLI 호환성 보존, deprecation 안내만 찍는다).
        if despite_returned:
            print(f"[{role}] --despite-returned 는 더 이상 아무 효과가 없다 "
                  f"(deprecated, 이슈 #1239) — 게이트가 항상 non-blocking "
                  f"surfacing 이라 무시할 거절이 없다", file=sys.stderr)
        # 이슈 #2186: 이 gh 조회(`gh pr list`)가 실측 스폰에서 un-instrumented
        # 115s의 프라임 서스펙트였다 — 워크스페이스 클론/브랜치 체크아웃과
        # 겹치도록 여기서 던지고 그 아래에서 join 하는 형태로 처음 옮겼다.
        # 이슈 #2201: 그 join 자체가 실측 스폰에서 여전히 6.608s(전체의
        # 21%)를 세션 시작 전 블로킹 경로에 남겼다 — 이 결과는
        # `_print_returned_pr_surfaced()`/ledger 이벤트로만 쓰이고
        # (`relay._print_returned_pr_surfaced`), cross_family 와 달리
        # 세션에 전달되는 task 텍스트 어디에도 안 실리므로 애초에 join
        # 할 이유가 없다 — auto_sweep(#2195)과 같은 완전 fire-and-forget
        # 데몬 스레드로 바꾼다. `ThreadPoolExecutor` 는 안 쓴다: submit()
        # 만 해도 concurrent.futures 의 atexit 훅(모듈 전역
        # `_threads_queues`)이 그 워커를 인터프리터 종료까지 join 해,
        # 이 이슈가 없애려는 블로킹이 프로세스 종료 시점으로 이름만
        # 바뀐 채 되살아난다(#2195 의 동일 추론, daemon=True 스레드는
        # 그 등록을 거치지 않는다).
        def _run_returned_pr_gate() -> None:
            t0 = time.monotonic()
            try:
                blockers, ok = _undispositioned_role_prs(root, exclude_issue=issue)
            except Exception as ex:
                print(f"[{role}] returned-pr 게이트 실패(스폰은 계속): {ex}",
                      file=sys.stderr)
                return
            elapsed = time.monotonic() - t0
            if not ok:
                print(f"[{role}] returned-PR 게이트: gh 조회 실패 — fail-open 으로 "
                      f"통과시킨다 (이슈 #680)", file=sys.stderr)
                ledger_write({"event": "returned_pr_gate_fail_open", "role": role,
                              "issue": issue, "ts": int(time.time())})
            else:
                _print_returned_pr_surfaced(blockers, source="spawn")
            print(f"[{role}] returned-pr 게이트(백그라운드) {elapsed:.3f}s 만에 "
                  f"끝남 (걸린 PR {len(blockers)}개)", file=sys.stderr)
        with _timed("returned_pr_gate"):
            _returned_pr_gate_thread = threading.Thread(
                target=_run_returned_pr_gate, daemon=True,
                name="returned-pr-gate")
            _returned_pr_gate_thread.start()
        # 이슈 #1179: 워크스페이스 하나 더 만들기 전에 먼저 안전하게
        # 쓸어낸다(spawn-time sweep) — 정리는 사람이 `spawn.py clean` 을
        # 기억해야만 도는 게 아니라 기본으로 켜져 있어야 한다(northpole
        # req#7). 스윕 실패가 스폰 자체를 막으면 안 되므로 예외를 삼킨다.
        # 이슈 #2195: 실측 스폰에서 이 스윕이 148.7s/154.3s(96%)를 먹었다.
        # returned_pr_gate/cross_family 와 달리 이 결과를 세션 시작 전에
        # 기다려야 할 이유가 없다 — 이번 스폰이 못 지운 워크스페이스는
        # 다음 스폰(혹은 다음 사이클)이 마저 지우면 그만인 housekeeping
        # 이라, join 대상 future 가 아니라 완전히 fire-and-forget 데몬
        # 스레드로 던진다. ThreadPoolExecutor 는 안 쓴다 — concurrent.futures
        # 는 제출된 작업을 atexit 에서 join 하므로(모듈 전역
        # `_threads_queues`), submit() 만 해도 인터프리터 종료가 스윕
        # 완료까지 다시 블록돼 버려 이 이슈가 없애려는 바로 그 블로킹이
        # 프로세스 종료 시점으로 이름만 바뀐 채 되살아난다. daemon=True
        # 스레드는 그 등록을 거치지 않아 프로세스가 스윕을 기다리지 않고
        # 나갈 수 있다.
        # 이슈 #2195 헌트: 이 디스패치만 재면 `bootstrap_timing`의
        # `auto_sweep=`이 실제 스윕이 얼마나 걸리든 늘 ~0.000 으로 찍혀,
        # 그 시간을 어디서도 볼 수 없게 된다 — #2186 이 바로 이런 "단계
        # 사이에 숨는 시간"을 없애려고 만든 계측 취지를 이 phase 하나에서
        # 되살려 죽이는 셈이다. 백그라운드 스레드 자신이 완료 시점에
        # 걸린 시간/결과를 stderr 로 찍어, 세션 시작을 막지 않으면서도
        # 그 시간이 완전히 안 보이게 되진 않게 한다 — bootstrap_timing
        # 줄에는 안 실리지만(그 줄은 세션 시작 전 블로킹 구간만 잰다),
        # 라이브 로그에는 남는다.
        with _timed("auto_sweep"):
            if _clean_auto_enabled():
                def _run_auto_sweep() -> None:
                    t0 = time.monotonic()
                    try:
                        outcome = auto_sweep(_workspace_base(),
                                              _clean_max_age_days(),
                                              _clean_max_bytes())
                    except Exception as ex:
                        print(f"[{role}] auto-sweep 실패(스폰은 계속): {ex}",
                              file=sys.stderr)
                        return
                    elapsed = time.monotonic() - t0
                    print(f"[{role}] auto-sweep(백그라운드) {elapsed:.3f}s "
                          f"만에 끝남 (지움 {outcome['removed']}, "
                          f"실패 {outcome['failed']})", file=sys.stderr)
                    # 이슈 #2443: 워크스페이스 디렉터리 정리와 같은
                    # 스폰타임/같은 백그라운드 스레드/같은 예외-흡수 계약으로
                    # 짝 디렉터리가 이미 없어진 sidecar 파일(세션 로그/
                    # events.jsonl/events.offset/watcher.log/task.txt)도
                    # 훑는다 — 새 트리거 지점을 만들지 않는다, 위
                    # auto_sweep() 과 같은 호출 안.
                    try:
                        sidecar_outcome = _prune_orphaned_sidecars(
                            _workspace_base(), _clean_max_age_days())
                    except Exception as ex:
                        print(f"[{role}] sidecar-prune 실패(스폰은 계속): {ex}",
                              file=sys.stderr)
                        return
                    if sidecar_outcome["removed"] or sidecar_outcome["failed"]:
                        print(f"[{role}] sidecar-prune(백그라운드) "
                              f"(지움 {sidecar_outcome['removed']}, "
                              f"실패 {sidecar_outcome['failed']})",
                              file=sys.stderr)
                threading.Thread(target=_run_auto_sweep, daemon=True,
                                  name="auto-sweep").start()
        # 격리 작업 클론에서 돈다 — 사용자의 체크아웃은 건드리지 않고,
        # 동시 스폰들이 서로의 index/브랜치를 밟지 않는다. 이슈 #2159:
        # 클론 전 cwd(= origin 체크아웃)를 따로 잡아 둔다 — 아래에서
        # cwd 가 격리 작업 경로로 덮어써지면 origin 쪽 경로는 이 변수로만
        # 남는다.
        origin_cwd = cwd
        with _timed("workspace"):
            cwd = issue_workspace(cwd, issue, role)
        claim_rejection = _acquire_spawn_claim(cwd, issue, role)
        if claim_rejection is not None:
            print(f"[{role}] {claim_rejection}", file=sys.stderr)
            # 이슈 #2382 컨포먼스 리뷰 발견: 이 리턴은 위에서 이미 던진
            # `_core_future`(core_plugin_dirs) 의 join 지점(아래 "core"
            # 단계) 보다 먼저다 — join 없이 그냥 리턴하면 future 가 갈 곳을
            # 잃는다. `ThreadPoolExecutor`는 daemon 스레드가 아니라
            # 인터프리터 종료를 그 워커가 끝날 때까지 블록한다(#2195/#2061
            # 의 그 이유로 auto_sweep/returned_pr_gate 는 raw daemon
            # 스레드를 쓴다) — join 없이 나가면 그 블로킹이 조용히
            # 되살아난다. 여기서 join 해 결과를 받는다: core_plugin_dirs()
            # 는 선언된 core 플러그인이 없으면 `sys.exit()`로 죽는
            # fail-loud 계약이라(pipeline.py, 이슈 #282) 그 예외는 삼키지
            # 않고 그대로 전파한다 — claim 거절 여부와 무관하게 core
            # 설정이 깨졌으면 시끄럽게 죽어야 한다는 원래 계약 그대로다.
            core_plugins = _core_future.result()
            _core_executor.shutdown(wait=False)
            return 1
        with _timed("branch"):
            if skills_branch_identity is not None:
                # 이슈 #2572/#2432: --skills 스폰은 스킬 축 네이밍
                # (`checkout_issue_branch_for_skill`, pipeline.py:1135)을
                # 실제로 쓴다 — 이 함수는 여태 테스트만 있고 프로덕션
                # 호출자가 없었다. `role` 은 main()에서 이미
                # `{skill_slug}-{disambiguator}` 로 조립돼 있어 결과 브랜치
                # 이름은 아래 직접 조립과 바이트 동일하지만, 이름-짓기를
                # 이 함수에 위임해 pipeline.py:1135 를 실제 호출자로 만든다.
                skill_slug, disambiguator = skills_branch_identity
                br = checkout_issue_branch_for_skill(cwd, issue, skill_slug,
                                                      disambiguator)
            else:
                # 이슈 #2555 (Step C): `role` 은 이제 스폰 시점에 정해지는
                # 슬러그다(레거시 역할 이름일 수도, 임의 슬러그일 수도 있다) —
                # 역할-전용 `checkout_issue_branch()` 대신 이름-짓기 결정이
                # 이미 끝난 브랜치 이름을 그대로 받는 `_checkout_named_branch()`
                # 를 직접 부른다. 오늘의 브랜치 이름(`issue-<n>/<role>`)과
                # 바이트 동일 — `checkout_issue_branch()` 자체가 이 한 줄이다.
                br = _checkout_named_branch(cwd, f"issue-{issue}/{role}")
        print(f"[{role}] 격리 작업 디렉토리: {cwd}  (브랜치 {br})", file=sys.stderr)
        # 원본(프리픽스 붙기 전) 맡길 일을 한 번만 저장 — 재스폰(다른 spawn.py
        # 프로세스일 수 있다)이 이걸 읽어 그대로 넘기면, 아래에서 프리픽스를
        # 다시 붙여도 중복되지 않는다 (이슈 #132).
        task_path = Path(str(cwd) + ".task.txt")
        if not task_path.exists():
            task_path.write_text(task, encoding="utf-8")
        # issue #1017 (northpole req#6): 이슈가 인용하는 요구 ID를 스폰
        # 텍스트에 그대로 실어, 스폰된 세션이 첫 턴부터 어느 요구를
        # 섬기는지 안다. gh 조회 실패는 조용히 건너뛴다 — 이 줄이 없다고
        # 스폰 자체를 막을 이유는 없다(require_requirement_linkage 가 이미
        # phase-1 드래프트 시점에 구조적으로 막는다).
        # 이슈 #2382: 이 gh 조회(`_gh_rest.fetch_issue`)는 아래 directive_write
        # 의 로컬 디스크 쓰기(섹션 파일/레코드 스켈레톤) 어느 쪽 결과에도
        # 안 걸린다 — 둘 다 br/cwd 만 있으면 되고 서로의 출력을 안 읽는다.
        # 예전에는 issue_fetch 가 directive_write **뒤에** 완전히 끝난
        # 다음에야 시작해, 순수 네트워크 왕복이 로컬 I/O 뒤에 그대로
        # 직렬로 얹혔다. 여기서 먼저 던지고(cross_family 와 같은 패턴),
        # directive_write 가 메인 스레드에서 겹쳐 도는 동안 배경에서
        # 돈다 — 아래 "issue_fetch" 단계는 이제 순수 join 대기만 잰다.
        def _run_issue_fetch() -> tuple[str, str, str | None, object | None,
                                         str | None, str | None, str | None]:
            try:
                sys.path.insert(0, str((ROOT / "gates").resolve()))
                import gh_rest as _gh_rest
                import requirement_linkage as _requirement_linkage
                import design_artifacts_gate as _design_artifacts_gate_mod
                issue_data = _gh_rest.fetch_issue(Path(cwd), issue)
                _body = issue_data.get("body") if issue_data else None
                _title = issue_data.get("title") if issue_data else None
                # 이슈 #2395: owner/repo 는 이 같은 `fetch_issue()` 응답에
                # 이미 실려 있다 — echo 를 위해 gh 를 또 부르지 않는다.
                _owner = issue_data.get("owner") if issue_data else None
                _repo = issue_data.get("repo") if issue_data else None
                _req_line = ""
                _goal_pin = ""
                if _body is not None:
                    req_ids = _requirement_linkage.cited_requirement_ids(_body)
                    if req_ids:
                        _req_line = f"이 이슈가 인용하는 요구: {', '.join(req_ids)}\n"
                    _goal_pin = _goal_pin_block(_title, _body)
                return _req_line, _goal_pin, _body, _design_artifacts_gate_mod, _title, _owner, _repo
            except Exception:
                return "", "", None, None, None, None, None
        # 이슈 #2395 CHANGES: `main()`이 게이트 앞에서 이미
        # `_resolve_and_echo_issue()`로 fetch-and-echo 를 끝냈으면
        # (`issue_data`가 `_ISSUE_NOT_PRE_RESOLVED`가 아니면) 이 async
        # fetch 자체를 던지지 않는다 — 안 그러면 성공 경로에서 gh 왕복이
        # 또 하나 늘어난다(acceptance check 2 위반). 아직 아무도 안
        # 찍었으면(`_respawn_or_cap()` 등 `main()`을 안 거친 호출) 오늘
        # 까지처럼 여기서 직접 async fetch 하고 echo 도 직접 찍는다.
        pre_resolved = issue_data is not _ISSUE_NOT_PRE_RESOLVED
        if not pre_resolved:
            _issue_fetch_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            _issue_fetch_future = _issue_fetch_executor.submit(_run_issue_fetch)
        # Issue #2135: materialize the on-demand directive section files and
        # the record skeleton into the workspace BEFORE assembling the
        # index — the trigger lines below reference files that must exist.
        with _timed("directive_write"):
            _directive_section_texts = directive_section_files(
                skills_mounted=bool(skill_sources or role_source["skills"]),
                checkpoint_block=(_checkpoint_contract_block(issue, role)
                                  if checkpoint else None))
            materialize_directive_sections(cwd, _directive_section_texts)
            # issue #2575: `_cross_family_task_text` (pristine, pre-mutation
            # task text — same var `_cross_family_skill_matches_with_consult`
            # already uses above) lets `write_record_skeleton()` decide
            # is_coding from the task itself instead of a role-name match.
            write_record_skeleton(cwd, issue, role, _cross_family_task_text,
                                   skill_sources=skill_sources)
        with _timed("issue_fetch"):
            if pre_resolved:
                body = issue_data.get("body") if issue_data else None
                title = issue_data.get("title") if issue_data else None
                resolved_owner = issue_data.get("owner") if issue_data else None
                resolved_repo = issue_data.get("repo") if issue_data else None
                req_line = ""
                goal_pin = ""
                _design_artifacts_gate = None
                try:
                    sys.path.insert(0, str((ROOT / "gates").resolve()))
                    import requirement_linkage as _requirement_linkage
                    import design_artifacts_gate as _design_artifacts_gate
                    if body is not None:
                        req_ids = _requirement_linkage.cited_requirement_ids(body)
                        if req_ids:
                            req_line = f"이 이슈가 인용하는 요구: {', '.join(req_ids)}\n"
                        goal_pin = _goal_pin_block(title, body)
                except Exception:
                    req_line = ""
                    goal_pin = ""
            else:
                (req_line, goal_pin, body, _design_artifacts_gate,
                 title, resolved_owner, resolved_repo) = _issue_fetch_future.result()
                _issue_fetch_executor.shutdown(wait=False)
        # 이슈 #2395: cwd 가 어느 레포로 해석됐는지(owner/repo#n) + 이슈
        # 제목을, 오케스트레이터 stdout 과 세션에 주입되는 지시문
        # 양쪽에 같은 문구로 찍는다 — 같은 이슈 번호가 레포마다 다른
        # 이슈를 가리키는 사고를 "조용한 오해"가 아니라 "눈에 보이는
        # 사실"로 바꾼다. gh 조회 실패(fetch_issue 가 None)는 조용히
        # 건너뛰지 않고, 확인 실패라고 그대로 말한다 — 확인 불가를
        # 확인됨으로 읽지 않는다.
        if resolved_owner and resolved_repo:
            resolved_line = (f"해석된 레포/이슈: {resolved_owner}/{resolved_repo}#{issue}"
                              + (f" — {title}" if title else "") + "\n")
        else:
            resolved_line = (f"해석된 레포/이슈: 확인 실패 — cwd({cwd})가 가리키는 "
                              f"레포에서 이슈 #{issue} 를 못 읽었다(gh 조회 실패).\n")
        if not pre_resolved:
            # 이슈 #2395 CHANGES: pre-resolved 면 `main()`이 게이트 앞에서
            # 이미 이 줄을 찍었다 — 여기서 또 찍으면 stdout 에 중복된다.
            print(f"[{role}] {resolved_line.strip()}")
        # Issue #2135 directive diet: the always-on preamble is a compact
        # invariant index. The long prose it used to carry (완료의 정의
        # full text, 체크포인트 커밋 rule, headless/run_in_background
        # warning, landing batching, repo-discovery guidance) lives
        # VERBATIM in {DIRECTIVE_DIR}/*.md, materialized above.
        # Issue #2204: those files no longer carry an inline "Read <file>
        # when <condition>" pointer here — a live-spawn measurement showed
        # sessions treat that pointer as "Read it now," burning ~46s of
        # sequential Read round trips before the first task action. Their
        # full text instead rides `--append-system-prompt`
        # (`_directive_system_prompt_block()`, wired into `spawn_cmd()`
        # below) — already in context at session start, zero round trips.
        task = _dp("issue-preamble-index",
                f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
                + resolved_line
                + req_line + goal_pin +
                f"gh issue view {issue} 로 이슈를 먼저 읽어라.\n"
                f"완료의 정의: 변경이 이 브랜치에 커밋되고 push 되어 PR 로 "
                f"제출된 상태다 — 미커밋 변경은 존재하지 않는 것과 같다.\n"
                f"레코드 스켈레톤: docs/issue-{issue}/reports/{role}.md 가 "
                f"미리 쓰여 있다 — 구조를 새로 만들지 말고 스켈레톤의 "
                f"섹션을 채워라(이슈 #2135).\n"
                f"\n") + task
        # 이슈 #1978 (A), 이슈 #2152 로 기본값 반전: `single_phase` 는 이제
        # CLI 기본값이 True 인 effective 값이다 — --two-phase 나
        # --checkpoint 가 없으면 이 블록이 기본으로 붙는다. B(스킬 트리거
        # 줄)보다 먼저 온다(A before B, 제안서 순서).
        if single_phase:
            task = task + _dp("single-phase-contract",
                "\n\n" + _SINGLE_PHASE_CONTRACT_LINE.format(role=role))
        # Issue #2129: --checkpoint appends the single-session
        # propose-approve-implement contract. Without the flag this block
        # appends NOTHING — the default directive stays byte-identical
        # (same constraint discipline as --single-phase above).
        if checkpoint:
            # Issue #2135: condensed inline invariant (the actionable wait
            # command stays inline); full contract prose verbatim in
            # {DIRECTIVE_DIR}/checkpoint-mode.md (materialized above).
            task = task + _dp("checkpoint-mode-index",
                              "\n\n" + _checkpoint_index_block(issue, role))
        if skill_sources:
            skill_lines = ", ".join(
                f"{m['name']}"
                + (f" — {_skill_trigger_line(m['dir'])}"
                   if _skill_trigger_line(m['dir']) else "")
                + f" ({_describe_skill_match(m)})"
                for m in skill_sources)
            task = task + _dp("mounted-skills", (
                f"\n\n마운트된 스킬(--skills, 이슈 #1742/#1774): {skill_lines}\n"))
        if role_source["source"] == "skill-repo":
            # 이슈 #1978 (B): 스킬 이름 옆에 SKILL.md 의 "Use ..." 트리거
            # 문장을 인라인한다(#1960 의 1/9 발화율 넛지를 대체) — 트리거
            # 문장이 없는 스킬도 이름은 절대 빠뜨리지 않는다(empty-state
            # 요구).
            # 이슈 #2001/#2040/#2507: 이번 과제 텍스트에 매치되는 top-K
            # 스킬을 얹는다 — 매치가 없으면 cross_family_dirs 는 빈 목록.
            # 이슈 #2040: BM25 프리필터 + skill_judge 자문 판단(스폰당
            # 최대 자문 1회) — 소요 시간은 "cross_family" 단계로 측정해
            # 부트스트랩 타이밍 요약에 실린다(Acceptance: per-spawn latency).
            with _timed("cross_family"):
                # 이슈 #2061: 위에서 워크스페이스/브랜치 셋업보다 먼저 던져둔
                # 자문을 여기서 join 만 한다 — 이 단계의 측정치는 이제 겹친
                # 대기 시간이 아니라 순수 join 대기(자문이 셋업보다 오래
                # 걸린 나머지)만 반영한다.
                if _cross_family_future is not None:
                    cross_family_dirs, skill_judge_outcome = _cross_family_future.result()
                else:
                    # 이슈 #2679: --issue 없는 스폰은 자문 자체를 안 던진다
                    # (위 `if issue is not None:`) — 이 줄이 없으면 성공
                    # 로그도 실패 로그도 안 남아 "자문이 성공했는지 아예
                    # 안 불렸는지" 를 로그만으로 구분할 수 없다.
                    cross_family_dirs, skill_judge_outcome = [], "not-run"
                    print(f"[{role}] skill_judge 자문 안 함 — --issue 없는 스폰이라 "
                          f"자문 자체를 안 던졌다 (not-run)", file=sys.stderr)
                if _cross_family_executor is not None:
                    _cross_family_executor.shutdown(wait=False)
            # 이슈 #2507: 고정 표(family) + 자문 추가(cross-family)라는
            # 두 층 구분이 없어졌다 — POLICY 스킬(정적) + 매치된 스킬(동적)
            # 을 하나의 마운트 목록으로 합친다(add-only, 이름 중복 제거).
            role_source = merge_composed_skill_source(role_source, cross_family_dirs)
            role_skill_lines = ", ".join(
                d.name + (f" — {_skill_trigger_line(d)}" if _skill_trigger_line(d) else "")
                for d in role_source["skill_dirs"]
            ) if role_source["skill_dirs"] else ", ".join(role_source["skills"])
            if cross_family_dirs:
                cross_family_clause = (
                    f" (이 중 {', '.join(d.name for d in cross_family_dirs)} 는 "
                    f"이번 과제 텍스트와의 매치로 구성된 스킬 — 이슈 #2001/#2507)")
            else:
                cross_family_clause = ""
            task = task + _dp("role-skill-triggers", (
                f"\n\n이번 과제에 대해 스킬이 구성됐다(skill-repository, 이슈 "
                f"#1955/#1758/#2507 — 고정 role->skill 표가 아니라 과제 텍스트 "
                f"매치): 스킬 {role_skill_lines} "
                f"(skill-repository {role_source['skill_sha']}) 가이던스만 붙는다 — "
                f"집행은 core 훅뿐이다.{cross_family_clause}\n"))
        # 이슈 #1960 phase B: 마운트된 스킬이 하나라도 있으면(--skills 든
        # POLICY 스킬이든) 실체 작업을 시작하기 전에 그 목록을 이번 과제와
        # 대조해보라고 스폰 시점에 못박는다. 베이스라인 측정
        # (docs/issue-1960/reports/execution-observation/baseline-measurement.md)
        # 이 relevance-gated 세션 38개 전부에서 Skill 호출 0건을 보였다 —
        # 스킬이 안 맞아서가 아니라 애초에 호출을 고려하지 않는 구조적
        # 공백이라는 뜻이라, trigger 문구를 손보는 대신 이 지시문 한 줄을
        # 추가한다(단일 변경, 순차 적용).
        if skill_sources or role_source["skills"]:
            # 이슈 #2039: 마운트된 스킬 하나마다 레코드에 한 줄씩 verdict를
            # 남겨야 한다 — 스킬을 조용히 무시하는 걸 불가능하게 만든다.
            # 스킬이 하나도 안 마운트되면 이 블록 전체가 안 붙으므로
            # (위 조건과 동일), 무-스킬 세션은 오늘과 바이트 단위로 같다.
            if issue is not None:
                # Issue #2135 diet: the full 스킬 점검(#1960)/invoke-before-
                # apply(#2062)/스킬-verdict(#2039, #2153) prose lives
                # verbatim in {DIRECTIVE_DIR}/skill-obligations.md
                # (materialized above); inline stays the condensed
                # invariant + Skill-tool trigger. Issue #2204: no inline
                # "Read that file" pointer — the same full prose already
                # rides `--append-system-prompt` (zero round trips).
                task = task + _dp("skill-obligations-index",
                    f"\n\n스킬 의무(이슈 #1960/#2039/#2062/#2153): 스킬 점검 "
                    f"— 마운트된 스킬 목록을 이번 과제와 대조하고, "
                    f"applicable 로 판단한 스킬은 적용 전에 반드시 Skill "
                    f"도구로 로드하라. 이번 세션에서 실제로 호출한 스킬 "
                    f"이름마다 레코드에 `skill-verdict: <스킬명> — applied: "
                    f"invoked; <어디서/어떻게> | not-applicable: <한 줄 "
                    f"이유>` 줄을 정확히 하나씩 남겨야 한다 (마운트만 되고 "
                    f"호출하지 않은 스킬은 이 줄이 필요 없다).\n")
            else:
                # Adhoc spawn: no workspace to materialize into — keep the
                # full prose inline (byte-identical to the pre-#2135 text).
                task = task + _dp("skill-obligations-full",
                                  "\n\n" + _SKILL_CHECK_PROSE
                                  + "\n\n" + _SKILL_VERDICT_PROSE)
        # 이슈 #2382: board_snapshot(cwd) 는 docs/issue-*/ 아래 파일 내용을
        # 해시한다 — 이 지점은 두 가지를 모두 지킨다: (a)
        # write_record_skeleton() 이 이미 그 트리 밑에 스켈레톤을 썼다(진짜
        # 의존성, "before" 스냅샷이 세션이 안 쓴 스켈레톤을 세션이 바꾼
        # 것으로 잘못 셀 수 있다), (b) 위 cross_family join
        # (`_cross_family_future.result()`) 이 이미 끝나 skill_judge 자문이
        # `docs/issue-<n>/reports/consult-log/`(consult.py) 에 남길 로그
        # 파일도 이미 다 써졌다 — 여기보다 일찍(예: directive_write 직후)
        # 던기면 그 consult-log 쓰기가 board_snapshot 의 "before"/"after"
        # 스냅샷 중 어느 쪽에 들어갈지 스레드 스케줄링에 따라 갈려, 세션이
        # 안 건드린 파일이 "다른 역할의 기록을 건드렸다"(계약 §11)로
        # 오탐될 수 있다(실측: 이 재배치 전 시도가
        # test_spawn_one_call_site_fires_after_own_session_end_event 를
        # 깼다). board_snapshot 은 issue_fetch/core/settings/
        # design_bearing/spawn_cmd 결과 중 어느 것도 안 읽는다 — 예전에는
        # 이 다섯을 전부 기다린 뒤(함수 맨 끝, session Popen 직전) 처음
        # 불렸다. 여기서 먼저 던지고 실제 사용 지점(맨 아래)에서 join 만
        # 한다.
        _board_snapshot_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        _board_snapshot_future = _board_snapshot_executor.submit(board_snapshot, cwd)
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
            # 이슈 #2507: `role_source["skill_dirs"]` 는 이미 위에서
            # cross_family_dirs 와 합쳐졌다 — 여기서 또 얹을 필요가 없다.
            artifact_all_dirs = list(skill_dirs) + [
                d for d in role_source["skill_dirs"] if d not in skill_dirs]
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
                task = task + _dp("artifact-skill-pairing", (
                    "\n\n아티팩트-스킬 짝짓기(이슈 #2014): 선언된 각 아티팩트를 "
                    "그것을 만드는 절차를 담은 스킬과 짝지었다.\n"
                    + "\n".join(pairing_lines) + "\n"))
    # 이슈 #2073: 같은 body(새 fetch 없음, spawn.py 의 위 블록이 이미 받아온
    # 것)에서 두 개의 조건부 줄을 붙인다 — (a) `runtime-artifacts:` 가
    # 선언됐거나 자문 스코어러가 울리면 artifact-smoke 트리거 한 줄,
    # (b) 이슈가 design-bearing 이면서 선언된 design-artifacts 에
    # 스토리보드가 있으면 live-screen 검증 한 줄. 둘 다 조건이 없으면
    # 아무 것도 안 붙는다(제안서 Constraints — byte-identical on absence).
    # 스킬 마운트 여부와 무관하므로 위 스킬 블록 바깥에 둔다.
    task = task + _dp("artifact-smoke",
                      _artifact_smoke_task_lines(body if issue is not None else None))
    # 이슈 #2382: adhoc 스폰(issue is None, 위 issue-스코프 블록을 안 탄
    # 경로)은 directive_write 가 없어 여태 못 던졌다 — cwd 가 이미 최종값
    # (안 바뀜)이므로 여기서 바로 던진다.
    if _board_snapshot_future is None:
        _board_snapshot_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        _board_snapshot_future = _board_snapshot_executor.submit(board_snapshot, cwd)
    # Issue #2135: measure-first instrument — per-source byte counts of the
    # assembled directive, at every spawn.
    print(f"[{role}] {composition_breakdown(_directive_parts)}",
          file=sys.stderr)
    # 이슈 #1955: 세션은 룰북을 아예 마운트하지 않는다 — rulebook 해석
    # 경로 자체가 은퇴했다(요구사항: 룰북 마운트가 "붙었지만 무시됨"이
    # 아니라 argv 에서 통째로 빠져야 한다는 #1758 요구사항 2를 무조건화).
    plugins: list[Path] = []
    # core_plugin_dirs() 를 print 보다 먼저 불러 core_root() 의 관리 클론
    # pull 이 먼저 일어나게 한다 — 순서가 뒤집히면(예전처럼 print 뒤에서
    # 부르면) 로그에는 pull 전 sha, ledger 에는 pull 후 sha 가 찍혀 같은
    # run 안에서 두 기록이 어긋난다. (이슈 #2382: pull 자체는 이미 admission
    # clear 직후 던져졌다 — 이 시점보다 훨씬 먼저다. 이 순서 요구는 여전히
    # 지켜진다.) 이 단계는 이제 순수 join 대기만 잰다(겹친 시간은 제외,
    # cross_family 와 같은 계측 관례).
    with _timed("core"):
        core_plugins = _core_future.result()
        _core_executor.shutdown(wait=False)
    with _timed("settings"):
        s = role_settings(role, cwd)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(s, f)
            settings = f.name
        # 이슈 #2468: `bounded and issue is not None`(아래)이면 이 파일의
        # 실제 소유자는 이 프로세스가 아니라 곧 뜰 fork 자식이다 — 여기서
        # 이 프로세스의 pid 로 남기면, 이 프로세스(부모)가 fork 직후 정상
        # 리턴하는 순간 `_pid_is_alive()`가 바로 False 가 되어 아직 자식이
        # 쓰고 있는 파일을 GC 스윕이 오삭제한다. 그 경로의 기록은 자식이
        # fork 직후 자기 pid 로 직접 남긴다(아래, fork 분기).
        if not (bounded and issue is not None):
            _record_tmp_resource(settings, os.getpid(), "settings")
    # --skills(#1742)와 구성된 스킬(#1758/#1955/#2507 — POLICY + 과제-매치)
    # 은 additive — 같은 --plugin-dir 마운트 목록에 합쳐 붙인다.
    # 이슈 #2507: `role_source["skill_dirs"]`가 이미 cross_family_dirs 와
    # 합쳐져 있다(issue-scoped 스폰; adhoc 은 cross_family_dirs 가 애초에
    # 빈 목록이라 이 필드가 POLICY 스킬뿐이다) — 여기서 또 얹을 필요가 없다.
    all_skill_dirs = list(skill_dirs) + [d for d in role_source["skill_dirs"]
                                          if d not in skill_dirs]
    try:
        rulebook_desc = "skill-repo(이슈 #1955)"
        roster_resolution_fields = _role_source_roster_fields(role_source)
        print(f"[{role}] 플러그인 {len(plugins)}개, 룰북 {rulebook_desc}, "
              f"core 플러그인 {', '.join(p.name for p in core_plugins)}, "
              f"core {core_version()}, 작업 디렉터리 {cwd}", file=sys.stderr)
        # 이슈 #2070: design-bearing 판정은 issue 본문에 대해서만 의미가
        # 있다 — 없으면(adhoc 스폰) None, gates 호출이 실패해도(gh 오류 등)
        # fail-open 으로 None 에 떨어진다(라우팅 계층 자체가 fail-open).
        design_bearing_verdict = None
        with _timed("design_bearing"):
            if issue is not None:
                try:
                    sys.path.insert(0, str((ROOT / "gates").resolve()))
                    import design_bearing_classifier
                    # 이슈 #2186: `body`는 위 "issue_fetch" 단계에서 이미
                    # `gh api repos/.../issues/{issue}`로 한 번 받아왔다 —
                    # 예전에는 여기서 `design_bearing_classifier.check()`가
                    # 같은 본문을 또 `gh_rest.fetch_issue_body()`로 받아와,
                    # 스폰마다 똑같은 REST 왕복을 두 번 태웠다. 이미 있는
                    # `body`를 `check_issue_body()`에 바로 넘겨 그 두 번째
                    # 왕복을 아예 없앤다(검사 불가 시 fail-open 하는 원래
                    # 의미는 그대로: `body`가 None 이면 판정도 None).
                    _verdict = (design_bearing_classifier.check_issue_body(issue, body)
                                if body is not None else None)
                    design_bearing_verdict = bool(_verdict and _verdict.get("design_bearing"))
                except Exception:
                    design_bearing_verdict = None
        # 맡길 일은 stdin 으로 넘긴다. 인자로 주면 가변 인자 플래그가 삼키고,
        # 셸 보간을 거치면 신뢰할 수 없는 값의 $(…) 가 실행된다.
        with _timed("spawn_cmd"):
            cmd, extra_env = spawn_cmd(settings, role, unattended,
                                       core_plugins, plugins, model,
                                       all_skill_dirs,
                                       skill_sha or role_source["skill_sha"],
                                       single_phase=single_phase,
                                       design_bearing_verdict=design_bearing_verdict,
                                       max_turns=resolved_max_turns,
                                       checkpoint=checkpoint,
                                       append_system_prompt=_directive_system_prompt_block(
                                           _directive_section_texts),
                                       skill_registry_root=skill_registry_root)
        # 이슈 #2070: roster 기록용 두 내부 키를 여기서 뽑아내 실제 subprocess
        # env 에는 안 들어가게 한다 — spawn_cmd() 가 심어준 신호일 뿐, 세션
        # 자신의 env 표면이 아니다.
        _model_routing_model = extra_env.pop("_MODEL_ROUTING_MODEL", "")
        _model_routing_rule = extra_env.pop("_MODEL_ROUTING_RULE", "")
        # 이슈 #1978 (A), 이슈 #2152 로 기본값 반전: effective single_phase
        # 가 참일 때만 얹는다 — 기본은 이제 참이므로 CORE_BUILD_NOW=1 은
        # 기본 스폰에 실린다; --two-phase/--checkpoint 면 빠진다.
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
            # 이슈 #2159: origin 체크아웃에만 있는 node_modules/.venv 를
            # 가리키는 env var — 파일은 옮기지 않는다(위 주석 참고).
            extra_env.update(local_dependency_env(origin_cwd, cwd))
        # 이슈 #2382: dispatch 는 위(directive_write 직후, 또는 adhoc 스폰이면
        # composition_breakdown 직전)에서 이미 던졌다 — 여기는 순수 join 만
        # 잰다. core/settings/design_bearing/spawn_cmd 를 거치는 동안 배경
        # 에서 겹쳐 돈다.
        with _timed("board_snapshot"):
            before = _board_snapshot_future.result()
            _board_snapshot_executor.shutdown(wait=False)
        before_head = _git_head(cwd) if issue is not None else None
        # 이슈 #2186: 이 지점이 fork/session-start 직전 — 로그로 나가는
        # bootstrap_timing 줄은 예전에 core/settings 단계 직후(더 위)에서
        # 찍혀, 그 뒤로 이어지는 (지금은 계측된) design_bearing/spawn_cmd/
        # board_snapshot 구간이 그 줄의 `total`에 전혀 안 실렸다 — 실제
        # session-start 이벤트 바로 앞으로 옮겨, `total`이 spawn 진입부터
        # session-start까지 전체 구간을 담게 한다.
        print(_bootstrap_timing_line(role), file=sys.stderr)
        t0 = time.monotonic()
        # stream-json 을 줄 단위로 받아 라이브 로그에 tee 한다 — "지금 뭐
        # 하는 중인가"가 세션이 끝나기 전에도 보이게. 최종 result 이벤트가
        # 옛 --output-format json 의 결과 오브젝트와 같은 필드를 든다.
        # Issue #2293 (scope addition): adhoc spawns now clone into their
        # own pid-keyed workspace above, so they get the same
        # timestamped+PID log path issue-scoped spawns already do
        # (pipeline.py `_session_log_path()`, issue #192) instead of a
        # single shared `runs/last-session.log` that a second mistake
        # could overwrite mid-session.
        log_path = _session_log_path(cwd)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{role}] 라이브 로그: {log_path}", file=sys.stderr)
        if attempt_id is not None:
            # 이슈 #2291: 이 지점 이후로는 세션 로그/로스터가 곧 존재한다 —
            # 부트스트랩 halt 구간을 이 시도의 성공으로 확정한다. roster_register
            # (아래, Popen 뒤)보다 먼저지만 몇 줄 차이라 워치독 틱(60초 간격)
            # 기준으로는 동시다.
            _record_spawn_outcome(attempt_id, "session-log", str(log_path))
        result = {}
        roster_key = lease_key(issue, role) if issue is not None else f"adhoc/{role}/{os.getpid()}"
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
                # 이슈 #2468: settings.json 의 실제 소유자는 이 fork
                # 자식이다(부모는 곧 정상 리턴해 죽는다) — 자기 pid 를
                # 이 구간 맨 처음(다른 실패 가능 지점보다 먼저)에 남겨,
                # 이후 어떻게 죽든(SIGKILL 포함) GC 스윕이 죽은 pid 로
                # 찾아 지울 수 있게 한다. 같은 이유로 바로 아래 로스터
                # 스텁도 이 구간 맨 앞에 있다(#908 주석 그대로).
                _record_tmp_resource(settings, os.getpid(), "settings")
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
                             "watch", "--issue", str(issue), "--session", role,
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
                # `spawn.py watch --issue <n> --session <session>` 호출로 이어본다.
                print(f"[{role}] 스폰은 리턴했지만 세션은 계속 돈다 — 상태는 "
                      f"spawn.py ps, 이어보려면 spawn.py watch --issue "
                      f"{issue} --session {role}", file=sys.stderr)
                # 이슈 #2201 헌트: 여기가 bounded 부모의 유일한 리턴 지점이고,
                # 이 함수가 끝나면 곧 `sys.exit()`(CLI 진입점)로 인터프리터가
                # 죽는다 — 데몬 스레드는 그 시점에 join 없이 그냥 죽으므로,
                # `returned_pr_gate` 백그라운드 스레드가 이 시점까지 못
                # 끝냈다면 surfacing/ledger 부수효과가 통째로 사라진다(발견:
                # docs/issue-2201/reports/implementation/2026-08-24-hunt-
                # bootstrap-cross-family-returned-pr-gate.md). 세션 시작을
                # 막지 않으려고 배경으로 던진 것이지 결과를 버려도 된다는
                # 뜻은 아니었다 — 여기서 짧게(gh 조회 실측 6.608s 대비
                # 넉넉한 상한) join 해 등록한다. 이미 끝났으면 즉시 리턴하고,
                # 아직이면 최대 이 상한만큼만 더 기다린다 — 세션은 이미
                # fork 로 독립했으니 이 대기는 대화형 세션에 전혀 안 보인다.
                _returned_pr_gate_thread.join(timeout=10.0)
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
            # 이슈 #2574: 이 스폰이 실제로 받은 single_phase 처분을 그대로
            # 남긴다 — lifecycle.py 의 워치독 재스폰(`_auto_respawn_check`)
            # 이 크래시한 세션을 되살릴 때, 원래 two-phase 였던 세션을
            # 조용히 build-now 로 승격시키지 않으려면(그 반대로 조용히
            # 강등시키지도 않으려면) 이 값을 읽어 그대로 다시 넘겨야 한다.
            "single_phase": single_phase,
            # Issue #2293: the raw task text, adhoc spawns only -- lets
            # watchdog.diagnose_health() tag every poll line for a
            # no-issue entry with the task it is actually running, so
            # HEALTHY can never read as "your issue-N spawn is fine".
            "task": task if issue is None else None,
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
        # 이슈 #2574: 이 프로세스 자신이 받은 single_phase 를 그대로 넘긴다
        # — 이 지점은 roster 엔트리를 다시 읽을 필요 없이 원래 처분을
        # 직접 알고 있는 유일한 재스폰 경로다.
        _self_trigger_respawn(outcome, roster_key, cwd, issue, role,
                              str(log_path), session_start_ts, single_phase)
        os._exit(rc if isinstance(rc, int) else 0)
    return rc


if __name__ == "__main__":
    sys.exit(main())
