#!/usr/bin/env python3
"""issue-1024 — `requirement_intake_consult.check_issue_body`의 단위테스트.

네트워크·GitHub 없이 도는 것만(`gates/test_acceptance_gate.py`와 같은
관례).

  python3 gates/test_requirement_intake_consult.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import requirement_intake_consult


def t_consult_trace_passes():
    body = """## Request
Add a new feature.

validity-consult: requirements-engineering run 2026-08-12, feasible.
"""
    assert requirement_intake_consult.check_issue_body(1024, body) == []


def t_skip_trivial_passes():
    body = """## Request
Fix a typo in the README.

validity-consult-skip: trivial
"""
    assert requirement_intake_consult.check_issue_body(1024, body) == []


def t_neither_flagged():
    body = """## Request
Add a new feature with no consult recorded.
"""
    bad = requirement_intake_consult.check_issue_body(1024, body)
    assert bad, "no consult trace and no skip tag should be a violation"


def t_arbitrary_skip_reason_rejected():
    """The vocabulary is closed to `trivial` only — an arbitrary named
    reason must not pass (post-proposal hunt finding)."""
    body = """## Request
A risk-bearing ask.

validity-consult-skip: this touches auth but I'm skipping anyway
"""
    bad = requirement_intake_consult.check_issue_body(1024, body)
    assert bad, "arbitrary skip reason should not pass the closed vocabulary"


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
