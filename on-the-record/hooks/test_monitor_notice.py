"""Tests for the issue #947 monitor-unavailable degradation notice.

Exercises the grace-threshold/marker-presence decision logic embedded in
directive.sh's monitor-notice block in isolation -- no real Monitor
process is started; the "alive" marker poll-heartbeat.sh would write is
simulated directly via touch/os.utime. TOKENMAXXXER_CHECKOUT points the
invoked directive.sh at this repo checkout so poll_rearm_resolve_checkout
never attempts a network clone.

Red baseline (pre-hook): directive.sh had no monitor-notice logic at all
-- an absent alive marker past any elapsed time produced no output ever.
Green (this file): the notice fires exactly once, only when the marker
is absent-or-stale relative to this session's own recorded start time.
"""
import json
import os
import subprocess
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
HOOK = HOOKS_DIR / "directive.sh"

NOTICE_SNIPPET = "idle self-wake is unavailable in this session"


def _run(cwd, session_id, grace=1):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
    env["MONITOR_NOTICE_GRACE_SECONDS"] = str(grace)
    payload = json.dumps({"session_id": session_id})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env, cwd=str(cwd),
        timeout=20,
    )


def _marker_dir(cwd):
    return Path(cwd) / ".orchestrate-monitor-alive"


def test_first_observation_records_start_and_prints_no_notice(tmp_path):
    result = _run(tmp_path, "sess-1", grace=1)
    assert NOTICE_SNIPPET not in result.stdout
    starts = list(_marker_dir(tmp_path).glob(".session-*-start"))
    assert len(starts) == 1


def test_no_notice_inside_grace_window(tmp_path):
    _run(tmp_path, "sess-1", grace=999)
    result = _run(tmp_path, "sess-1", grace=999)
    assert NOTICE_SNIPPET not in result.stdout


def test_notice_fires_once_past_grace_with_no_alive_marker(tmp_path):
    _run(tmp_path, "sess-1", grace=1)
    time.sleep(1.2)
    result = _run(tmp_path, "sess-1", grace=1)
    assert NOTICE_SNIPPET in result.stdout

    # Second check after firing: never repeats for this session.
    result_again = _run(tmp_path, "sess-1", grace=1)
    assert NOTICE_SNIPPET not in result_again.stdout


def test_no_notice_when_alive_marker_fresh_for_this_session(tmp_path):
    _run(tmp_path, "sess-1", grace=1)
    marker_dir = _marker_dir(tmp_path)
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / "alive").touch()
    time.sleep(1.2)
    result = _run(tmp_path, "sess-1", grace=1)
    assert NOTICE_SNIPPET not in result.stdout


def test_stale_marker_from_earlier_session_does_not_suppress_notice(tmp_path):
    # Simulate a prior session's monitor having written the alive marker,
    # then dying, before the CURRENT session (sess-2) ever started --
    # the exact cross-session bleed the warrant hunt flagged.
    marker_dir = _marker_dir(tmp_path)
    marker_dir.mkdir(parents=True, exist_ok=True)
    stale_alive = marker_dir / "alive"
    stale_alive.touch()
    old_time = time.time() - 3600
    os.utime(stale_alive, (old_time, old_time))

    _run(tmp_path, "sess-2", grace=1)
    time.sleep(1.2)
    result = _run(tmp_path, "sess-2", grace=1)
    assert NOTICE_SNIPPET in result.stdout


def test_session_ids_that_a_char_substitution_sanitizer_would_collide_stay_independent(tmp_path):
    # Warrant-hunt finding (before-landing dispatch,
    # docs/issue-947/reports/implementation/2026-08-12-hunt-monitor-unavailable-notice-before-landing.md):
    # a char-substitution sanitizer maps "sess/a" and "sess?a" to the
    # identical "sess_a", letting session A's notified marker silently
    # suppress session B's own, independent notice. Session A: monitor
    # unavailable, gets notified. Session B (different id, same
    # substitution-collision class): also monitor-unavailable, must
    # still get its own notice.
    _run(tmp_path, "sess/a", grace=1)
    time.sleep(1.2)
    result_a = _run(tmp_path, "sess/a", grace=1)
    assert NOTICE_SNIPPET in result_a.stdout

    _run(tmp_path, "sess?a", grace=1)
    time.sleep(1.2)
    result_b = _run(tmp_path, "sess?a", grace=1)
    assert NOTICE_SNIPPET in result_b.stdout
