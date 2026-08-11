#!/usr/bin/env python3
"""issue #659 Axis 2 — plan_order_blocked: execution-plan order enforcement.

  python3 gates/test_plan_order_blocked.py
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import flows  # noqa: E402


class PlanOrderBlocked(unittest.TestCase):
    def test_empty_plan_is_empty(self):
        self.assertEqual(flows.plan_order_blocked([]), [])

    def test_single_step_no_dependency_is_empty(self):
        plan = [{"step": 1, "roles": ["implementation"], "done": False}]
        self.assertEqual(flows.plan_order_blocked(plan), [])

    def test_all_done_has_no_blocks(self):
        plan = [
            {"step": 1, "roles": ["a"], "done": True},
            {"step": 2, "roles": ["b"], "done": True},
        ]
        self.assertEqual(flows.plan_order_blocked(plan), [])

    def test_premature_sequential_step_refused(self):
        plan = [
            {"step": 1, "roles": ["product-discovery"], "done": False},
            {"step": 2, "roles": ["architecture"], "done": False},
        ]
        blocked = flows.plan_order_blocked(plan)
        self.assertEqual(blocked, [
            {"step": 2, "prerequisite_step": 1, "prerequisite_done": False},
        ])

    def test_parallel_roles_within_one_step_never_block_each_other(self):
        plan = [
            {"step": 1, "roles": ["a", "b"], "done": True},
            {"step": 2, "roles": ["c", "d"], "done": False},
        ]
        self.assertEqual(flows.plan_order_blocked(plan), [])

    def test_parallel_steps_sharing_step_number_never_block_each_other(self):
        plan = [
            {"step": 1, "roles": ["console"], "done": False},
            {"step": 1, "roles": ["audit"], "done": False},
        ]
        self.assertEqual(flows.plan_order_blocked(plan), [])

    def test_later_step_reports_nearest_undone_prerequisite(self):
        plan = [
            {"step": 1, "roles": ["a"], "done": True},
            {"step": 2, "roles": ["b"], "done": False},
            {"step": 3, "roles": ["c"], "done": False},
        ]
        blocked = flows.plan_order_blocked(plan)
        self.assertEqual(blocked, [
            {"step": 3, "prerequisite_step": 2, "prerequisite_done": False},
        ])


if __name__ == "__main__":
    unittest.main()
