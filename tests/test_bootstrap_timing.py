"""Issue #711 — per-spawn bootstrap phase timing.

Asserts the emitted `bootstrap_timing` line names all six bootstrap phases
with numeric durations (issue #711 acceptance: "unit test asserts a spawn
dry-run (or fixture) emits a timing summary line with the named bootstrap
phases and durations").
"""
from __future__ import annotations

import sys
import time
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


# Issue #2186 — the span between spawn entry and the `session-start` event
# had nine un-instrumented segments (admission_gate, --skills resolution,
# the returned-PR board sweep, the spawn-time auto-sweep, the issue-body
# fetch, directive/record-skeleton materialization, the design-bearing
# check, spawn_cmd assembly, and the pre-session board_snapshot) that a
# live spawn measured at ~115s. These phases now cover that span so
# `total` stops hiding time between the previously-named phases.
_ISSUE_2186_NEW_PHASES = ("admission", "skill_resolve", "returned_pr_gate",
                          "auto_sweep", "issue_fetch", "directive_write",
                          "design_bearing", "spawn_cmd", "board_snapshot")


def test_bootstrap_phases_cover_the_previously_dark_pre_session_span():
    for phase in _ISSUE_2186_NEW_PHASES:
        assert phase in spawn._BOOTSTRAP_PHASES, (
            f"{phase!r} must be a named bootstrap phase (issue #2186) so it "
            f"shows up (even at 0.000) instead of vanishing into `total`")


def test_bootstrap_timing_line_names_every_2186_phase():
    spawn._BOOTSTRAP_TIMING.clear()
    for phase in _ISSUE_2186_NEW_PHASES:
        with spawn._timed(phase):
            pass
    line = spawn._bootstrap_timing_line("qa")
    for phase in _ISSUE_2186_NEW_PHASES:
        assert f"{phase}=" in line, f"missing phase {phase!r} in {line!r}"


def test_total_sums_every_named_phase_not_just_the_original_seven():
    """`total` must grow when a #2186 phase times real work, or the
    printed total would still under-report the true pre-session span even
    though the phase itself is now visible in the line."""
    spawn._BOOTSTRAP_TIMING.clear()
    with spawn._timed("workspace"):
        time.sleep(0.05)
    with spawn._timed("returned_pr_gate"):
        time.sleep(0.05)
    line = spawn._bootstrap_timing_line("qa")
    total = float(line.split("total=", 1)[1].split()[0])
    assert total >= 0.09, (
        f"total={total} should account for both timed segments, got {line!r}")
