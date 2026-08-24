#!/usr/bin/env python3
"""issue #2196 Acceptance — the watchdog heartbeat must not re-emit
identical, non-actionable lines every tick:

  1. board-sweep per-PR subject-mapping failures on permanently
     unmappable (old-branch-name) PRs are reported once, then collapsed
     to a single count line on later ticks with unchanged repo state —
     a two-tick regression.
  2. a single transient gh failure produces no warning line; N
     consecutive failures still does (both directions).
  3. genuinely new/changed conditions still emit on the tick they
     appear (suppression must not silence new information).

  python3 -m pytest tests/test_watchdog_heartbeat_noise.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))
import closure_sweep  # noqa: E402
import gh_delta  # noqa: E402
import spawn  # noqa: E402


def _fake_run(cmd, **kwargs):
    if cmd[:3] == ["gh", "api", "rate_limit"]:
        return mock.Mock(returncode=0, stdout=json.dumps(
            {"resources": {"graphql": {"remaining": 5000}}}), stderr="")
    if cmd[:3] == ["gh", "repo", "view"]:
        return mock.Mock(returncode=0, stdout="owner/repo\n", stderr="")
    return mock.Mock(returncode=0, stdout="", stderr="")


@pytest.fixture()
def board_repo(tmp_path):
    root = tmp_path / "repo"
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "docs" / "specs" / "approvers.md").write_text("x\n")
    spawn._repo_slug_cache_clear()
    return root


def _printed_lines(fake_print):
    return [c.args[0] for c in fake_print.call_args_list if c.args]


def _delta_with_unmappable_prs(pr_numbers, branches):
    """A `gh_delta.fetch_delta` stub classifying as "delta" with the given
    PR numbers changed, plus a `closure_sweep._pr_index_all` stub mapping
    each to a non-`issue-<n>/<role>` branch name."""
    items = [{"number": n, "pull_request": {}} for n in pr_numbers]
    index = {branches[n]: {"number": n, "state": "OPEN", "body": ""}
              for n in pr_numbers}
    return items, index


class TestPerPrMappingFailureSuppression:
    """Acceptance bullet 1: two consecutive full-rescan/delta ticks with
    unchanged repo state produce no repeated per-PR mapping-failure
    lines."""

    def test_two_ticks_unchanged_state_suppresses_repeat_lines(self, board_repo):
        pr_numbers = [2006, 2017]
        branches = {2006: "old-feature-branch", 2017: "another-legacy-branch"}
        items, index = _delta_with_unmappable_prs(pr_numbers, branches)

        with mock.patch("subprocess.run", side_effect=_fake_run), \
             mock.patch("gh_delta.fetch_delta",
                        return_value=(items, "cursor-1", "delta")), \
             mock.patch("closure_sweep._pr_index_all", return_value=(index, True)), \
             mock.patch("closure_sweep.next_categories", return_value=([], [])):
            with mock.patch("builtins.print") as fake_print:
                spawn._board_wide_sweep(board_repo)
            tick1_lines = _printed_lines(fake_print)

            with mock.patch("builtins.print") as fake_print:
                spawn._board_wide_sweep(board_repo)
            tick2_lines = _printed_lines(fake_print)

        # tick 1: both PRs are new — each gets its own mapping-failure line.
        assert any("PR #2006" in l and "subject 매핑 실패" in l for l in tick1_lines)
        assert any("PR #2017" in l and "subject 매핑 실패" in l for l in tick1_lines)

        # tick 2: repo state unchanged — no per-PR mapping-failure line
        # repeats for either PR.
        assert not any("PR #2006" in l and "subject 매핑 실패" in l for l in tick2_lines)
        assert not any("PR #2017" in l and "subject 매핑 실패" in l for l in tick2_lines)
        # the two previously-reported PRs collapse into one count line
        # instead of vanishing without a trace.
        assert any("2건" in l and "이전에 보고된 매핑-불가 PR" in l for l in tick2_lines)

    def test_genuinely_new_unmappable_pr_still_emits_on_its_own_tick(self, board_repo):
        branches = {2006: "old-feature-branch"}
        items, index = _delta_with_unmappable_prs([2006], branches)

        with mock.patch("subprocess.run", side_effect=_fake_run), \
             mock.patch("gh_delta.fetch_delta",
                        return_value=(items, "cursor-1", "delta")), \
             mock.patch("closure_sweep._pr_index_all", return_value=(index, True)), \
             mock.patch("closure_sweep.next_categories", return_value=([], [])):
            with mock.patch("builtins.print"):
                spawn._board_wide_sweep(board_repo)  # tick 1: #2006 seen

            # tick 2: #2006 unchanged, plus a brand-new unmappable PR #3099.
            branches2 = {2006: "old-feature-branch", 3099: "yet-another-legacy"}
            items2, index2 = _delta_with_unmappable_prs([2006, 3099], branches2)
            with mock.patch("gh_delta.fetch_delta",
                            return_value=(items2, "cursor-2", "delta")), \
                 mock.patch("closure_sweep._pr_index_all", return_value=(index2, True)):
                with mock.patch("builtins.print") as fake_print:
                    spawn._board_wide_sweep(board_repo)
            tick2_lines = _printed_lines(fake_print)

        assert any("PR #3099" in l and "subject 매핑 실패" in l for l in tick2_lines)
        assert not any("PR #2006" in l and "subject 매핑 실패" in l for l in tick2_lines)


class TestTransientGhFailureSuppression:
    """Acceptance bullet 2: a single transient gh failure produces no
    warning line; N consecutive failures still does (both directions)."""

    def test_requirement_drift_single_failure_suppressed_then_warns_on_streak(
            self, board_repo, capsys):
        (board_repo / "docs" / "specs" / "requirement-digest.md").write_text(
            "- R001: something [open] (source: #1)\n")

        with mock.patch.object(spawn, "_board_read", return_value=(None, {"source": None})):
            spawn.requirement_drift(board_repo)  # tick 1: transient
            out1 = capsys.readouterr().out
            spawn.requirement_drift(board_repo)  # tick 2: still transient
            out2 = capsys.readouterr().out
            spawn.requirement_drift(board_repo)  # tick 3: consecutive streak hits threshold
            out3 = capsys.readouterr().out

        assert "gh 실패" not in out1
        assert "gh 실패" not in out2
        assert "gh 실패" in out3

    def test_requirement_drift_success_resets_streak(self, board_repo, capsys):
        (board_repo / "docs" / "specs" / "requirement-digest.md").write_text(
            "- R001: something [open] (source: #1)\n")
        empty_board = {"issues": {}, "prs": {}}

        with mock.patch.object(spawn, "_board_read", return_value=(None, {"source": None})):
            spawn.requirement_drift(board_repo)
            spawn.requirement_drift(board_repo)
            capsys.readouterr()

        with mock.patch.object(spawn, "_board_read", return_value=(empty_board, {"source": "live"})):
            spawn.requirement_drift(board_repo)  # success resets the streak
            capsys.readouterr()

        with mock.patch.object(spawn, "_board_read", return_value=(None, {"source": None})):
            spawn.requirement_drift(board_repo)  # single failure after reset
            out = capsys.readouterr().out

        assert "gh 실패" not in out
