"""이슈 #1465: ~/.claude/tokenmaxxxer/monitor-alive/ 아래 stale 마커
디렉터리 GC — 임계값이 poll-heartbeat.sh 의 touch cadence 보다 커야 하고,
GC 실패는 non-fatal 이어야 하며, 레거시 .orchestrate-monitor-alive/ 는
지우지 않고 리포트만 해야 한다."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn  # noqa: E402


def _make_marker(root: Path, name: str, mtime: float, write_alive: bool = True) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    if write_alive:
        alive = d / "alive"
        alive.write_text("")
        os.utime(alive, (mtime, mtime))
    else:
        os.utime(d, (mtime, mtime))
    return d


def test_stale_dirs_removed(tmp_path):
    root = tmp_path / "monitor-alive"
    now = 1_000_000.0
    threshold = spawn.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS

    fresh = _make_marker(root, "fresh24charhash000000000", now - 60)
    stale = _make_marker(root, "stale24charhash000000000", now - threshold - 3600)

    stats = spawn.gc_monitor_alive(root=root, now=now)

    assert not stale.exists()
    assert fresh.exists()
    assert stats["removed"] == 1
    assert stats["kept"] == 1
    assert stats["errors"] == 0


def test_stale_dirs_removed_empty_root(tmp_path):
    root = tmp_path / "does-not-exist"
    stats = spawn.gc_monitor_alive(root=root, now=1_000_000.0)
    assert stats == {"removed": 0, "kept": 0, "errors": 0}


def test_threshold_above_touch_cadence():
    assert (spawn.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS
            > spawn.MONITOR_ALIVE_TOUCH_CADENCE_SECONDS)


def test_gc_failure_nonfatal(tmp_path):
    root = tmp_path / "monitor-alive"
    now = 1_000_000.0
    threshold = spawn.MONITOR_ALIVE_STALE_THRESHOLD_SECONDS
    stale = _make_marker(root, "unwritable24charhash00000", now - threshold - 3600)

    old_mode = root.stat().st_mode
    try:
        root.chmod(0o500)  # dir readable/executable, not writable -> rmtree of child fails
        stats = spawn.gc_monitor_alive(root=root, now=now)
        assert stats["errors"] >= 1
        assert stale.exists()
    finally:
        root.chmod(old_mode)

    # entry-point wrapper must never raise either
    spawn.monitor_alive_gc_cli(tmp_path)


def test_legacy_dir_reported_not_deleted(tmp_path, capsys):
    repo = tmp_path / "consumer-repo"
    legacy = repo / ".orchestrate-monitor-alive"
    legacy.mkdir(parents=True)
    (legacy / "marker").write_text("x")

    found = spawn.detect_legacy_monitor_alive_dirs(repo)

    assert found == [legacy]
    assert legacy.is_dir()
    assert (legacy / "marker").exists()

    os.environ["MUSTER_MONITOR_ALIVE_ROOT"] = str(tmp_path / "unused-monitor-alive")
    try:
        spawn.monitor_alive_gc_cli(repo)
    finally:
        del os.environ["MUSTER_MONITOR_ALIVE_ROOT"]
    out = capsys.readouterr().out
    assert "[legacy-monitor-alive]" in out
    assert str(legacy) in out
    assert legacy.is_dir()
