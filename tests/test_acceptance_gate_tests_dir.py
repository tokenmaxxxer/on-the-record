#!/usr/bin/env python3
"""issue-1284 — _ARTIFACT_REF matched backticked `test/` but not `tests/`
(this repo's real test tree), rejecting real test paths as prose-only.

  python3 -m pytest -q tests/test_acceptance_gate_tests_dir.py
"""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "acceptance_gate", ROOT / "gates" / "acceptance_gate.py"
)
acceptance_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acceptance_gate)
check_issue_body = acceptance_gate.check_issue_body


def test_backticked_tests_dir_path_accepted():
    body = (
        "## Acceptance\n"
        "- `tests/test_spawn.py` covers this\n"
        "empty state: not applicable\n"
        "provenance: executed-unit\n"
    )
    violations = check_issue_body(1284, body)
    assert violations == [], (
        "expected a backticked tests/ path to satisfy the artifact-"
        f"reference check; got violations={violations!r}"
    )


def test_prose_only_still_rejected():
    body = (
        "## Acceptance\n"
        "- it should work correctly and pass the tests\n"
    )
    violations = check_issue_body(1284, body)
    assert violations != [], (
        f"expected prose-only body to still be flagged; got violations={violations!r}"
    )


def test_existing_test_dir_path_still_accepted():
    body = (
        "## Acceptance\n"
        "- `test/fixtures/example.py` covers this\n"
        "empty state: not applicable\n"
        "provenance: executed-unit\n"
    )
    violations = check_issue_body(1284, body)
    assert violations == [], (
        f"expected existing test/ singular path form to keep passing; got violations={violations!r}"
    )


def test_gates_dir_path_still_accepted():
    body = (
        "## Acceptance\n"
        "- `gates/acceptance_gate.py` enforces this\n"
        "empty state: not applicable\n"
        "provenance: executed-unit\n"
    )
    violations = check_issue_body(1284, body)
    assert violations == [], (
        f"expected existing gates/ path form to keep passing; got violations={violations!r}"
    )


def test_check_line_form_still_accepted():
    body = (
        "## Acceptance\n"
        "check: python3 -m pytest tests/ -k acceptance -q\n"
        "empty state: not applicable\n"
        "provenance: executed-unit\n"
    )
    violations = check_issue_body(1284, body)
    assert violations == [], (
        f"expected check: line form to keep passing; got violations={violations!r}"
    )
