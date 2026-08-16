#!/usr/bin/env python3
"""issue-1665 — `assumption_ledger.check_issue_body`/`invented_assumptions`
단위테스트.

네트워크·GitHub 없이 도는 것만(`gates/test_requirement_intake_consult.py`
와 같은 관례).

  python3 gates/test_assumption_ledger.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import assumption_ledger


def t_missing_both_flagged():
    body = """## Request
Add a new feature with several moving parts and no assumptions recorded.
"""
    bad = assumption_ledger.check_issue_body(1665, body)
    assert bad, "no Assumptions section and no skip tag should be a violation"


def t_well_formed_ledger_passes():
    body = """## Request
Add a new feature.

## Assumptions
- stated: the user asked for a REST endpoint.
- inferred: the endpoint should return JSON, matching the rest of the API.
- invented: rate limiting at 100 req/min (no basis given by the user).
"""
    assert assumption_ledger.check_issue_body(1665, body) == []


def t_skip_mechanical_passes():
    body = """## Request
Fix a typo in the README.

assumptions-skip: mechanical
"""
    assert assumption_ledger.check_issue_body(1665, body) == []


def t_out_of_vocabulary_tag_fails():
    body = """## Request
Add a new feature.

## Assumptions
- stated: the user asked for a REST endpoint.
- guessed: this seemed like a good idea.
"""
    bad = assumption_ledger.check_issue_body(1665, body)
    assert bad, "an out-of-vocabulary tag should not pass the closed vocabulary"


def t_arbitrary_skip_reason_rejected():
    """The vocabulary is closed to `mechanical` only — an arbitrary named
    reason must not pass (mirrors #1024/#1653 anti-arbitrary discipline)."""
    body = """## Request
A risk-bearing ask.

assumptions-skip: this is basically obvious so I'm skipping anyway
"""
    bad = assumption_ledger.check_issue_body(1665, body)
    assert bad, "arbitrary skip reason should not pass the closed vocabulary"


def t_empty_assumptions_section_fails():
    body = """## Request
Add a new feature.

## Assumptions

## Out of scope
Nothing else.
"""
    bad = assumption_ledger.check_issue_body(1665, body)
    assert bad, "an Assumptions section with no entries should be a violation"


def t_invented_helper_returns_only_invented():
    body = """## Request
Add a new feature.

## Assumptions
- stated: the user asked for a REST endpoint.
- inferred: the endpoint should return JSON.
- invented: rate limiting at 100 req/min.
- invented: a Redis-backed cache in front of it.
"""
    invented = assumption_ledger.invented_assumptions(body)
    assert invented == [
        "rate limiting at 100 req/min.",
        "a Redis-backed cache in front of it.",
    ], invented


def t_invented_helper_empty_when_no_section():
    body = """## Request
Fix a typo.

assumptions-skip: mechanical
"""
    assert assumption_ledger.invented_assumptions(body) == []


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
