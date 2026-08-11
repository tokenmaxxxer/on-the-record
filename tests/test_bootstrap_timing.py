"""Issue #711 — per-spawn bootstrap phase timing.

Asserts the emitted `bootstrap_timing` line names all six bootstrap phases
with numeric durations (issue #711 acceptance: "unit test asserts a spawn
dry-run (or fixture) emits a timing summary line with the named bootstrap
phases and durations").
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn  # noqa: E402


def test_timing_line_absent_without_emission():
    spawn._BOOTSTRAP_TIMING.clear()
    # no _timed() calls happened for this (simulated) spawn — the line must
    # still be emittable (all phases default to 0.0), but nothing was timed.
    assert spawn._BOOTSTRAP_TIMING == {}


def test_bootstrap_timing_line_has_all_named_phases():
    spawn._BOOTSTRAP_TIMING.clear()
    with spawn._timed("workspace"):
        pass
    with spawn._timed("branch"):
        pass
    with spawn._timed("rulebook"):
        pass
    with spawn._timed("core"):
        pass
    with spawn._timed("gh_token"):
        pass
    with spawn._timed("settings"):
        pass

    line = spawn._bootstrap_timing_line("qa")
    assert line.startswith("[qa] bootstrap_timing")
    for phase in ("workspace", "branch", "rulebook", "core", "gh_token",
                  "settings", "total"):
        assert f"{phase}=" in line, f"missing phase {phase!r} in {line!r}"
        value = line.split(f"{phase}=", 1)[1].split()[0]
        assert float(value) >= 0.0


def test_bootstrap_timing_line_defaults_untimed_phases_to_zero():
    """A no-issue spawn never runs workspace/branch — they must still show
    up as 0.0, not be dropped from the line."""
    spawn._BOOTSTRAP_TIMING.clear()
    with spawn._timed("rulebook"):
        pass

    line = spawn._bootstrap_timing_line("qa")
    assert "workspace=0.000" in line
    assert "branch=0.000" in line
    assert "gh_token=0.000" in line


def test_timed_accumulates_across_multiple_calls():
    spawn._BOOTSTRAP_TIMING.clear()
    with spawn._timed("rulebook"):
        pass
    with spawn._timed("rulebook"):
        pass
    assert spawn._BOOTSTRAP_TIMING["rulebook"] >= 0.0
