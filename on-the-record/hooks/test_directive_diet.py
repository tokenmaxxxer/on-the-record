#!/usr/bin/env python3
"""issue #2102 -- orchestrate directive diet: byte-stable <=2.5KB index
with on-demand section files.

Live-fire (subprocess) checks on directive.sh's per-turn injection:
1. byte-stability: the rendered injection is byte-identical across turns
   of one session, both WITH and WITHOUT the monitor-available condition
   (the conditionally-printed idle-self-wake notice was the sole measured
   variance source -- issue #2102 baseline comment, 5/6 captures
   hash-identical); the notice now lands in .orchestrate-wake-notice.
2. size: the rendered always-on injection is <= 2560 bytes.
3. index integrity: every D/<section>.md file the index references
   exists under on-the-record/directive/ and is non-empty.

  python3 -m pytest on-the-record/hooks/test_directive_diet.py
"""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
DIRECTIVE_DIR = HOOKS_DIR.parent / "directive"
HOOK = HOOKS_DIR / "directive.sh"

SIZE_BUDGET = 2560


def _run(cwd, session_id="sess-diet", grace=None):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
    if grace is not None:
        env["MONITOR_NOTICE_GRACE_SECONDS"] = str(grace)
    payload = json.dumps({"session_id": session_id})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env,
        cwd=str(cwd), timeout=30,
    )


def _rendered(cwd, **kw):
    # Skip the one-time first-contact banner: pre-mark the workspace so
    # the measured output is the steady-state per-turn injection.
    (Path(cwd) / ".orchestrate-greeted").touch()
    return _run(cwd, **kw).stdout


def _alive_marker_dir(cwd):
    return (
        Path.home() / ".claude" / "tokenmaxxxer" / "monitor-alive" /
        hashlib.sha256(
            str(Path(cwd).resolve()).encode("utf-8", "surrogatepass")
        ).hexdigest()[:24]
    )


def test_injection_byte_identical_across_turns_monitor_unavailable(tmp_path):
    # No alive marker + 1s grace: the monitor-unavailable condition FIRES
    # on the second turn -- and the injection must not change by a byte.
    first = _rendered(tmp_path, grace=1)
    time.sleep(1.2)
    second = _rendered(tmp_path, grace=1)
    third = _rendered(tmp_path, grace=1)
    assert first == second == third
    # The condition did fire -- into the workspace file, not the blob.
    assert "idle self-wake is unavailable" in (
        (tmp_path / ".orchestrate-wake-notice").read_text()
    )


def test_injection_byte_identical_across_turns_monitor_available(tmp_path):
    # Fresh alive marker for this session: condition never fires; output
    # must equal the monitor-unavailable rendering byte-for-byte too.
    first = _rendered(tmp_path, grace=1)
    marker_dir = _alive_marker_dir(tmp_path)
    marker_dir.mkdir(parents=True, exist_ok=True)
    (marker_dir / "alive").touch()
    time.sleep(1.2)
    second = _rendered(tmp_path, grace=1)
    assert first == second
    assert not (tmp_path / ".orchestrate-wake-notice").exists()


def test_with_and_without_condition_render_identically(tmp_path):
    # The acceptance shape named by the task: render once with the
    # monitor-available condition and once without; byte-identical.
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    # a: monitor available (fresh alive marker before the session starts
    # is not enough -- it must be at/after session start, so touch after
    # the first observation turn).
    _rendered(a, grace=1)
    d = _alive_marker_dir(a)
    d.mkdir(parents=True, exist_ok=True)
    (d / "alive").touch()
    # b: monitor unavailable (no marker at all)
    _rendered(b, grace=1)
    time.sleep(1.2)
    out_available = _rendered(a, grace=1)
    out_unavailable = _rendered(b, grace=1)
    # Normalize the only legitimate per-workspace difference: none --
    # both cwds render against the same CHECKOUT, so the injected text
    # carries no cwd-derived bytes.
    assert out_available == out_unavailable


def test_always_on_injection_within_size_budget(tmp_path):
    out = _rendered(tmp_path)
    assert 0 < len(out.encode("utf-8")) <= SIZE_BUDGET, len(out.encode("utf-8"))


def test_every_index_referenced_section_file_exists_and_is_non_empty(tmp_path):
    out = _rendered(tmp_path)
    refs = sorted(set(re.findall(r"D/([a-z0-9-]+\.md)", out)))
    assert refs, "index references no section files -- diet regressed?"
    for name in refs:
        f = DIRECTIVE_DIR / name
        assert f.is_file(), f"index references missing section file {name}"
        assert f.stat().st_size > 0, f"section file {name} is empty"
    # And the inverse: no orphan section file the index never points at.
    on_disk = sorted(p.name for p in DIRECTIVE_DIR.glob("*.md"))
    assert on_disk == refs, (on_disk, refs)
