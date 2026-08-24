#!/usr/bin/env python3
"""issue #2240 Acceptance gate — orchestrator cross-tick state (gh_delta
cursors, the watchdog drift/noise caches, spawn_on_pr's park/merged-seen
state, spawn_on_approve's attempted state, closure_sweep's out-of-index-seen/
backoff/board-sweep-queue/accumulation-trend caches, the board snapshot) is
anchored via gates/state_paths.py's STATE_ROOT, never via `root / "runs"`
composed from whatever target repo a caller passes in. `root` here always
stands in for a freshly-cloned target/consumer repo — none of these
accessors may write into it.

  python3 -m pytest tests/test_state_root_scoping.py -v
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import board_read  # noqa: E402
import closure_sweep  # noqa: E402
import gh_delta  # noqa: E402
import spawn  # noqa: E402
import spawn_on_approve  # noqa: E402
import spawn_on_pr  # noqa: E402
import state_paths  # noqa: E402


def _fresh_target_repo(tmp_path):
    """A freshly-cloned target/consumer repo — no runs/ of its own, no
    state directory at all yet (first-ever tick)."""
    root = tmp_path / "target-repo"
    root.mkdir()
    return root


class TestEmptyStateFirstTick:
    """A first-ever tick against a fresh target repo with no state
    directory: every accessor resolves to the orchestrator-scoped
    location and returns empty state, not an error."""

    def test_gh_delta_cursor_path_is_orchestrator_scoped(self, tmp_path):
        _fresh_target_repo(tmp_path)
        path = gh_delta.cursor_path("issues")
        assert path.parent == state_paths.STATE_ROOT
        assert not path.exists()

    def test_watchdog_drift_cache_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        path = spawn._requirement_drift_cache_path(root)
        assert path.parent == state_paths.STATE_ROOT
        assert spawn._load_requirement_drift_cache(path) == {}
        assert not (root / "runs").exists()

    def test_watchdog_noise_state_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        path = spawn._watchdog_noise_state_path(root)
        assert path.parent == state_paths.STATE_ROOT
        assert spawn._load_watchdog_noise_state(path) == {}
        assert not (root / "runs").exists()

    def test_park_state_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        path = spawn_on_pr._park_state_path(root)
        assert path.parent == state_paths.STATE_ROOT
        assert spawn_on_pr.load_park_state(root) == {}
        assert not (root / "runs").exists()

    def test_board_snapshot_path_is_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        path = board_read.snapshot_path(root)
        assert path.parent == state_paths.STATE_ROOT
        assert not (root / "runs").exists()

    def test_merged_seen_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        assert spawn_on_pr.load_merged_seen(root) == set()
        assert not (root / "runs").exists()

    def test_attempted_state_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        assert spawn_on_approve.load_attempted(root) == {}
        assert not (root / "runs").exists()

    def test_out_of_index_seen_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        assert closure_sweep._load_out_of_index_seen(root) == set()
        assert not (root / "runs").exists()

    def test_backoff_state_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        assert closure_sweep.load_backoff_state(root) == {"sweeps": {}, "recheck": {}}
        assert not (root / "runs").exists()

    def test_board_sweep_queue_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        assert closure_sweep.load_board_sweep_queue(root) == []
        assert not (root / "runs").exists()

    def test_accumulation_trend_empty_and_orchestrator_scoped(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        trend = closure_sweep.accumulation_trend(root)
        assert trend.get("has_prior") is False
        assert not (root / "runs").exists()


class TestNeverWritesIntoConsumerTree:
    """Saving state through each accessor must never create files inside
    the target repo's own working tree, whichever way scoping resolves."""

    def test_full_write_cycle_stays_out_of_target_repo(self, tmp_path):
        root = _fresh_target_repo(tmp_path)

        cpath = gh_delta.cursor_path("issues")
        gh_delta._atomic_write_json(cpath, {"since": "2026-08-25T00:00:00+00:00"})

        dpath = spawn._requirement_drift_cache_path(root)
        spawn._save_requirement_drift_cache(dpath, {"1": {"title": "x", "body": "y"}})

        npath = spawn._watchdog_noise_state_path(root)
        spawn._save_watchdog_noise_state(npath, {"gh_failure_streaks": {"probe": 1}})

        spawn_on_pr._save_park_state(
            root, {"issue-1/implementation": {"blocked": True, "pr_number": 7}})

        assert not (root / "runs").exists()
        assert list(root.iterdir()) == []
        assert cpath.exists()
        assert dpath.exists()
        assert npath.exists()
        assert spawn_on_pr._park_state_path(root).exists()


class TestShouldParkLiveDemonstration:
    """Acceptance provenance (c): should_park() actually parks on the
    second identical tick, driven through the real load/save cycle (issue
    #2238 — should_park() had never parked anything because `prior` was
    always empty, since the state that would have supplied it was never
    persisted anywhere ticks could find it twice)."""

    def test_second_identical_tick_parks(self, tmp_path):
        root = _fresh_target_repo(tmp_path)
        key = "issue-9999/conformance-review"

        # tick 1: first sighting, no prior record -> never parks.
        state = spawn_on_pr.load_park_state(root)
        parked_tick1 = spawn_on_pr.should_park(state.get(key), 42, True)
        state[key] = {"blocked": True, "pr_number": 42, "parked": parked_tick1}
        spawn_on_pr._save_park_state(root, state)
        assert parked_tick1 is False

        # tick 2: identical blocker (same pr_number, still blocked) ->
        # parks, because tick 1's record is now actually findable.
        state = spawn_on_pr.load_park_state(root)
        parked_tick2 = spawn_on_pr.should_park(state.get(key), 42, True)
        assert parked_tick2 is True
