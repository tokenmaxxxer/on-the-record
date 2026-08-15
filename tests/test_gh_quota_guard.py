#!/usr/bin/env python3
"""issue #1498 Acceptance — GraphQL quota guard: quota floor on the
watchdog board-sweep path, a standing REST-only regression check, sweep
backoff on rate-limit errors, and re-check backoff for parked subjects.
All five tests mock `subprocess.run` — no network.

  python3 -m pytest tests/test_gh_quota_guard.py
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
import spawn  # noqa: E402


def _rate_limit_result(remaining: int):
    return mock.Mock(returncode=0, stdout=json.dumps(
        {"resources": {"graphql": {"remaining": remaining}}}), stderr="")


def _fake_run_factory(remaining: int):
    """A `subprocess.run` stub that answers every gh call this module's
    write-set functions can issue, recording every invocation."""
    calls: list[list[str]] = []

    def _run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:3] == ["gh", "api", "rate_limit"]:
            return _rate_limit_result(remaining)
        if cmd[:3] == ["gh", "issue", "list"]:
            return mock.Mock(returncode=0, stdout="[]", stderr="")
        if cmd[:3] == ["gh", "pr", "list"]:
            return mock.Mock(returncode=0, stdout="[]", stderr="")
        return mock.Mock(returncode=0, stdout="", stderr="")

    return _run, calls


@pytest.fixture()
def board_repo(tmp_path):
    root = tmp_path / "repo"
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "docs" / "specs" / "approvers.md").write_text("x\n")
    return root


def test_bulk_loop_skipped_below_floor(board_repo):
    """Below the 500 floor, `_board_wide_sweep` performs zero gh calls for
    the three gh-calling signals and emits exactly one report line."""
    fake_run, calls = _fake_run_factory(remaining=42)
    with mock.patch("subprocess.run", side_effect=fake_run):
        with mock.patch("builtins.print") as fake_print:
            count = spawn._board_wide_sweep(board_repo)

    assert count >= 1
    lines = [c.args[0] for c in fake_print.call_args_list if c.args]
    assert any("board-sweep" in line and "미집계" in line for line in lines)
    # only the rate_limit probe itself may have run — no bulk gh call.
    bulk_calls = [c for c in calls if c[:3] in (["gh", "issue", "list"],
                                                  ["gh", "pr", "list"])]
    assert bulk_calls == []


def test_graphql_free_watchdog_reads(board_repo):
    """Standing regression (req 2, 'verified, not migrated'): every gh call
    the watchdog/gate read paths under test make is REST (`gh api ...` or
    `... list --json ...`), never a bare GraphQL-backed `gh issue view` /
    `gh pr view` / `gh pr merge` subcommand."""
    fake_run, calls = _fake_run_factory(remaining=5000)
    with mock.patch("subprocess.run", side_effect=fake_run):
        spawn._board_wide_sweep(board_repo)

    graphql_backed = {("gh", "issue", "view"), ("gh", "pr", "view"), ("gh", "pr", "merge")}
    for cmd in calls:
        assert tuple(cmd[:3]) not in graphql_backed, f"GraphQL-backed subcommand used: {cmd}"


def test_sweep_backoff_on_rate_limit(tmp_path):
    """Consecutive rate-limit results double the sweep interval up to the
    stated max (8); a success resets it to 1."""
    root = tmp_path
    state = closure_sweep.load_backoff_state(root)

    assert closure_sweep.sweep_should_run(state, "board-sweep") is True
    closure_sweep.record_sweep_result(state, "board-sweep", True)
    assert state["sweeps"]["board-sweep"]["interval_ticks"] == 2

    closure_sweep.record_sweep_result(state, "board-sweep", True)
    assert state["sweeps"]["board-sweep"]["interval_ticks"] == 4
    closure_sweep.record_sweep_result(state, "board-sweep", True)
    assert state["sweeps"]["board-sweep"]["interval_ticks"] == 8
    closure_sweep.record_sweep_result(state, "board-sweep", True)
    assert state["sweeps"]["board-sweep"]["interval_ticks"] == 8  # capped

    closure_sweep.record_sweep_result(state, "board-sweep", False)
    assert state["sweeps"]["board-sweep"]["interval_ticks"] == 1
    assert state["sweeps"]["board-sweep"]["consecutive_rate_limit_errors"] == 0


def test_recheck_backoff(tmp_path):
    """A subject not changed across 3 consecutive re-checks is polled at a
    doubling interval capped at 16; any observed change resets it to 1."""
    root = tmp_path
    state = closure_sweep.load_backoff_state(root)
    key = "issue-1163/conformance-review"

    # first two no-change re-checks: still every tick (threshold not hit).
    assert closure_sweep.recheck_backoff(state, key, False) is True
    assert closure_sweep.recheck_backoff(state, key, False) is True
    # third consecutive no-change hits the threshold: interval doubles to
    # 2, and tick 3 % 2 != 0 -> not due this tick.
    assert closure_sweep.recheck_backoff(state, key, False) is False
    assert state["recheck"][key]["interval_ticks"] == 2

    # fourth consecutive no-change doubles again (capped at 16); tick 4 %
    # interval 4 == 0 -> due.
    assert closure_sweep.recheck_backoff(state, key, False) is True
    assert state["recheck"][key]["interval_ticks"] == 4

    # a change resets immediately.
    due = closure_sweep.recheck_backoff(state, key, True)
    assert due is True
    assert state["recheck"][key]["interval_ticks"] == 1
    assert state["recheck"][key]["consecutive_no_change"] == 0


def test_sweep_call_budget(board_repo):
    """A sweep over 400 synthetic already-covered subjects performs <= the
    stated per-tick call budget (8) of gh calls, resolving state via bulk
    list + local join rather than per-subject lookups."""
    docs = board_repo / "docs"
    for i in range(400):
        d = docs / f"issue-{i}" / "reports"
        d.mkdir(parents=True)
        (d / "implementation.md").write_text(
            "---\ncode_under_review:\n  - x\nloop_state: landed\n"
            "type: feature\nbreaking: false\nverdict: ok\n---\nbody\n")

    fake_run, calls = _fake_run_factory(remaining=5000)
    with mock.patch("subprocess.run", side_effect=fake_run):
        with mock.patch("builtins.print"):
            spawn._board_wide_sweep(board_repo)

    assert len(calls) <= 8, f"{len(calls)} gh calls for 400 subjects: {calls}"
