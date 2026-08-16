#!/usr/bin/env python3
"""issue-1653 — `design_research_consult.check_issue_body`의 단위테스트.

네트워크·GitHub 없이 도는 것만(`gates/test_requirement_intake_consult.py`와
같은 관례).

  python3 gates/test_design_research_consult.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import design_research_consult


def t_research_trace_passes():
    body = """## Request
Redesign the onboarding flow.

design-research: tech-feasibility run 2026-08-16, prior-art + risk + effectiveness plan.
"""
    assert design_research_consult.check_issue_body(1653, body) == []


def t_skip_mechanical_passes():
    body = """## Request
Fix a typo in the README.

design-research-skip: mechanical
"""
    assert design_research_consult.check_issue_body(1653, body) == []


def t_neither_flagged():
    body = """## Request
Redesign the checkout flow with no research recorded.
"""
    bad = design_research_consult.check_issue_body(1653, body)
    assert bad, "no research trace and no skip tag should be a violation"


def t_arbitrary_skip_reason_rejected():
    """The vocabulary is closed to `mechanical` only — an arbitrary named
    reason must not pass (mirrors #1024's closed-vocabulary discipline)."""
    body = """## Request
A design-bearing ask.

design-research-skip: this changes the UX but I'm skipping anyway
"""
    bad = design_research_consult.check_issue_body(1653, body)
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
