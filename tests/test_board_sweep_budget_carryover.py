#!/usr/bin/env python3
"""issue #1554 req 1/3 — per-tick gh-call budget for board-wide sweeps with
carry-over: a deferred sweep category is never dropped, and full coverage of
all categories is reached within ceil(categories/budget) ticks. Hermetic —
pure local state, no gh/subprocess calls.

  python3 -m pytest tests/test_board_sweep_budget_carryover.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import closure_sweep  # noqa: E402


def test_budget_one_needs_three_ticks_no_drop(tmp_path):
    """N categories, budget=1 per tick: each tick runs exactly one category,
    and across N ticks every category ran exactly once — no drops, no
    repeats before the round is exhausted."""
    root = tmp_path
    total = len(closure_sweep.BOARD_SWEEP_CATEGORIES)
    seen: list[str] = []
    for _tick in range(total):
        this_tick, carried_over = closure_sweep.next_categories(root, budget=1)
        assert len(this_tick) == 1
        seen.extend(this_tick)
    assert sorted(seen) == sorted(closure_sweep.BOARD_SWEEP_CATEGORIES)
    assert len(seen) == len(set(seen))  # no repeats within the round


def test_carry_over_persists_across_process_boundary(tmp_path):
    """The pending queue is state on disk, not in-memory only — a fresh
    call (simulating the next watchdog tick's process) still sees the
    carried-over remainder."""
    root = tmp_path
    this_tick, carried_over = closure_sweep.next_categories(root, budget=1)
    assert len(carried_over) == len(closure_sweep.BOARD_SWEEP_CATEGORIES) - 1

    reloaded = closure_sweep.load_board_sweep_queue(root)
    assert reloaded == carried_over


def test_empty_state_zero_calls_clean(tmp_path):
    """Empty state (issue's empty-state check): a repo with no prior queue
    file starts a fresh round and, with a budget covering all categories,
    reports full coverage and no carry-over in a single tick."""
    root = tmp_path
    this_tick, carried_over = closure_sweep.next_categories(
        root, budget=len(closure_sweep.BOARD_SWEEP_CATEGORIES))
    assert sorted(this_tick) == sorted(closure_sweep.BOARD_SWEEP_CATEGORIES)
    assert carried_over == []


def test_zero_budget_defers_everything_never_drops(tmp_path):
    """budget<=0 must still preserve every category as carry-over — a
    caller that computes budget=0 this tick (e.g. quota fully exhausted)
    must not lose coverage."""
    root = tmp_path
    this_tick, carried_over = closure_sweep.next_categories(root, budget=0)
    assert this_tick == []
    assert sorted(carried_over) == sorted(closure_sweep.BOARD_SWEEP_CATEGORIES)


def test_round_restarts_after_full_coverage(tmp_path):
    """After a full round is drained, the next call starts a fresh round
    instead of silently going idle forever — sweeps keep recurring."""
    root = tmp_path
    total = len(closure_sweep.BOARD_SWEEP_CATEGORIES)
    for _ in range(total):
        closure_sweep.next_categories(root, budget=1)
    # queue is now empty on disk; the next call must refill, not return [].
    this_tick, _carried = closure_sweep.next_categories(root, budget=1)
    assert this_tick != []
