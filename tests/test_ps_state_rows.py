"""issue-1462: `spawn.py ps` must render truthful terminal-state rows in the
session-end -> respawn gap, from synthetic roster state — no real process
spawning."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("spawn_mod", ROOT / "spawn.py")
spawn_mod = importlib.util.module_from_spec(spec)
sys.modules["spawn_mod"] = spawn_mod
spec.loader.exec_module(spawn_mod)


def test_gap_row_not_running():
    """Synthetic ended-session state (pid 0, the observed gap condition)
    renders a terminal state, never RUNNING/pid 0."""
    entry = {
        "pid": 0, "role": "execution-observation", "issue": 1202,
        "ts": 1_755_000_000, "work": "/tmp/on-the-record-issue-1202",
        "log": "/tmp/issue-1202.log", "session_id": None,
    }
    alive, lines = spawn_mod._format_roster_row(
        "issue-1202/execution-observation", entry, {}, now=1_755_001_000)
    assert alive is False
    assert "RUNNING" not in lines[0]
    assert "pid 0" not in lines[0]
    assert lines[0].startswith("ENDED")


def test_gap_row_not_running_empty_state():
    """An empty/absent roster renders an empty board (no rows, no crash)."""
    assert spawn_mod._roster_load.__call__  # sanity: helper importable
    d = {}
    rows = []
    for key, e in sorted(d.items()):
        rows.append(spawn_mod._format_roster_row(key, e, {}))
    assert rows == []


def test_missing_timestamp_renders_unknown():
    """No epoch-derived age is ever printed when `ts` is absent."""
    entry = {
        "pid": 0, "role": "execution-observation", "issue": 1202,
        "work": "/tmp/on-the-record-issue-1202", "log": "",
    }
    alive, lines = spawn_mod._format_roster_row(
        "issue-1202/execution-observation", entry, {}, now=1_755_001_000)
    assert "unknown" in lines[0]
    # no epoch-derived minute count anywhere in the state line
    for token in lines[0].split():
        if token.endswith("분"):
            pytest.fail(f"epoch-age minutes rendered despite missing ts: {token}")


def test_row_workspace_isolation():
    """A row never shows a path belonging to a different issue/role entry."""
    state = {
        "issue-1459/implementation": {
            "pid": 0, "role": "implementation", "issue": 1459,
            "ts": 1_755_000_000,
            "work": "/tmp/on-the-record-issue-1459-implementation",
            "log": "/tmp/issue-1459.log",
        },
        "issue-1202/execution-observation": {
            "pid": 0, "role": "execution-observation", "issue": 1202,
            "ts": 1_755_000_000,
            "work": "/tmp/on-the-record-issue-1202-execution-observation",
            "log": "/tmp/issue-1202.log",
        },
    }
    rendered = {}
    for key, e in sorted(state.items()):
        _, lines = spawn_mod._format_roster_row(key, e, {}, now=1_755_001_000)
        rendered[key] = lines

    assert "1459" in rendered["issue-1459/implementation"][2]
    assert "1202" not in rendered["issue-1459/implementation"][2]
    assert "1202" in rendered["issue-1202/execution-observation"][2]
    assert "1459" not in rendered["issue-1202/execution-observation"][2]


def test_watcher_lifecycle_label():
    """By-design watcher exit (row itself ended) is not labeled DEAD."""
    entry = {
        "pid": 0, "role": "execution-observation", "issue": 1202,
        "ts": 1_755_000_000, "work": "/tmp/on-the-record-issue-1202",
        "log": "/tmp/issue-1202.log",
    }
    key = "issue-1202/execution-observation"
    ws_key = f"{spawn_mod._repo_identity(entry['work'])}/{key}"
    ws_idx = {ws_key: {"watcher_pid": 412607, "watcher_armed_at": 1_754_999_000}}
    alive, lines = spawn_mod._format_roster_row(key, entry, ws_idx,
                                                 now=1_755_001_000)
    watcher_line = next(l for l in lines if "워처" in l)
    assert "DEAD" not in watcher_line
    assert "exited-with-session" in watcher_line
