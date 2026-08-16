#!/usr/bin/env python3
"""issue #1681: fixture-only, no-network tests for gates/gh_budget.py."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gh_budget


def _fixed_snapshot(remaining: int, ok: bool = True, reset: int | None = None):
    calls = {"n": 0}

    def fetch(root):
        calls["n"] += 1
        return remaining, ok, reset
    fetch.calls = calls
    return fetch


class TestPerClassBudget(unittest.TestCase):
    def test_watchdog_exhausts_while_orchestration_still_passes(self):
        fetch = _fixed_snapshot(1000)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 2, "sweep": 5}, reserve=100,
            fetch_snapshot=fetch)

        r1 = budget.charge("watchdog")
        r2 = budget.charge("watchdog")
        r3 = budget.charge("watchdog")  # exhausts its own budget of 2
        self.assertTrue(r1["ok"])
        self.assertTrue(r2["ok"])
        self.assertFalse(r3["ok"])
        self.assertEqual(r3["reason"], gh_budget.BUDGET_EXHAUSTED)

        # orchestration is not a metered class -> always passes, even
        # while watchdog is exhausted.
        r4 = budget.charge("orchestration")
        self.assertTrue(r4["ok"])

    def test_reserve_floor_never_crossed_by_metered_class(self):
        fetch = _fixed_snapshot(105)
        budget = gh_budget.GhBudget(
            Path("."), classes={"sweep": 1000}, reserve=100,
            fetch_snapshot=fetch)

        # plenty of per-class budget left, but only 5 points stand
        # between the account remaining (105) and the reserve (100).
        r1 = budget.charge("sweep", cost=5)
        self.assertTrue(r1["ok"])
        self.assertEqual(r1["remaining"], 100)

        r2 = budget.charge("sweep", cost=1)  # would push remaining to 99
        self.assertFalse(r2["ok"])
        self.assertEqual(r2["reason"], gh_budget.BUDGET_EXHAUSTED)
        self.assertEqual(r2["remaining"], 100)  # untouched by the refused charge

    def test_orchestration_draws_reserve_even_at_zero_metered_budget(self):
        fetch = _fixed_snapshot(100)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 0}, reserve=100,
            fetch_snapshot=fetch)

        self.assertFalse(budget.charge("watchdog")["ok"])
        # account remaining sits exactly at the reserve floor; an
        # unmetered orchestration call must still succeed.
        self.assertTrue(budget.charge("orchestration")["ok"])

    def test_snapshot_fetched_once_per_tracker_no_network(self):
        fetch = _fixed_snapshot(1000)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 50}, reserve=0,
            fetch_snapshot=fetch)

        for _ in range(10):
            budget.charge("watchdog")
        self.assertEqual(fetch.calls["n"], 1)
        self.assertEqual(budget.fetch_calls, 1)

    def test_unmetered_class_never_touches_snapshot(self):
        fetch = _fixed_snapshot(1000)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 5}, reserve=0,
            fetch_snapshot=fetch)
        budget.charge("orchestration")
        budget.charge("orchestration")
        # unmetered charges never trigger the snapshot fetch at all.
        self.assertEqual(fetch.calls["n"], 0)

    def test_fail_open_when_snapshot_fetch_fails(self):
        fetch = _fixed_snapshot(None, ok=False)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 5}, reserve=100,
            fetch_snapshot=fetch)
        # metered class still enforces its own point budget even when
        # the account-level snapshot is unavailable.
        self.assertTrue(budget.charge("watchdog")["ok"])

    def test_exhausted_result_carries_reset_as_until(self):
        fetch = _fixed_snapshot(1000, reset=1700000000)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 1}, reserve=0,
            fetch_snapshot=fetch)
        budget.charge("watchdog")  # consumes the only point
        r = budget.charge("watchdog")
        self.assertFalse(r["ok"])
        self.assertEqual(r["until"], 1700000000)

    def test_ok_result_has_no_until_key_requirement_but_ok_true(self):
        fetch = _fixed_snapshot(1000, reset=1700000000)
        budget = gh_budget.GhBudget(
            Path("."), classes={"watchdog": 5}, reserve=0,
            fetch_snapshot=fetch)
        r = budget.charge("watchdog")
        self.assertTrue(r["ok"])


class TestBudgetMessage(unittest.TestCase):
    def test_matches_board_sweep_convention(self):
        self.assertEqual(
            gh_budget.budget_message("board-sweep", 0),
            "[watchdog] board-sweep: 미집계 (rate-limit, remaining=0)")

    def test_distinct_source_label(self):
        self.assertEqual(
            gh_budget.budget_message("requirement-drift", 0),
            "[watchdog] requirement-drift: 미집계 (rate-limit, remaining=0)")

    def test_includes_until_when_reset_known(self):
        self.assertEqual(
            gh_budget.budget_message("board-sweep", 0, until=1700000000),
            "[watchdog] board-sweep: 미집계 (rate-limit, remaining=0) "
            "(budget-exhausted until 1700000000)")


if __name__ == "__main__":
    unittest.main()
