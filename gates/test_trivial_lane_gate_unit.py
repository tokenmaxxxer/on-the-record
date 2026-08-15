#!/usr/bin/env python3
"""issue #1492/#914 — live-fire test for `gates/trivial_lane_gate.py`.

Invokes `trivial_lane_gate`'s own diff-reading helpers and `classify()`
against a real git repository built in a tmp dir — not just the pure
`classify()` unit tests already covered in
tests/test_trivial_lane_gate.py — and asserts >= 2 distinct outcomes
(allow vs. deny).

  python3 -m pytest gates/test_trivial_lane_gate.py
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import trivial_lane_gate  # noqa: E402


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                    capture_output=True, text=True)


def _build_diff(tmp_path: Path, docs_change: bool) -> Path:
    """builds a real git repo fixture used to live-fire trivial_lane_gate.py."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.email", "test@example.com")
    _run_git(repo, "config", "user.name", "test")
    (repo / "docs").mkdir()
    (repo / "docs" / "readme.md").write_text("hello\n")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-q", "-m", "init")
    _run_git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _run_git(repo, "checkout", "-q", "-b", "feature")
    if docs_change:
        (repo / "docs" / "readme.md").write_text("hello\nmore docs\n")
    else:
        (repo / "spawn.py.stub").write_text(
            "def f():\n" + "    pass\n" * 60)
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "change")
    _run_git(repo, "update-ref", "refs/heads/pull-1-head", "feature")
    return repo


def test_live_fire_docs_only_diff_allows():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _build_diff(Path(tmp), docs_change=True)
        rows = trivial_lane_gate._numstat(repo, "origin/main", "pull-1-head")
        deleted = trivial_lane_gate._deleted_paths(
            repo, "origin/main", "pull-1-head")
        lane_class, reason = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], deleted)
        assert lane_class == "docs-only"
        assert reason


def test_live_fire_semantic_diff_denies():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _build_diff(Path(tmp), docs_change=False)
        rows = trivial_lane_gate._numstat(repo, "origin/main", "pull-1-head")
        deleted = trivial_lane_gate._deleted_paths(
            repo, "origin/main", "pull-1-head")
        lane_class, reason = trivial_lane_gate.classify(
            rows, [r[2] for r in rows], deleted)
        assert lane_class is None
        assert "full pipeline" in reason


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__]))
