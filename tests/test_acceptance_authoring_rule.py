#!/usr/bin/env python3
"""issue-1323 req 1 — `acceptance_authoring_rule.check_issue_body`의
단위테스트. 네트워크·GitHub 없이 도는 것만(`gates/test_acceptance_gate.py`와
같은 관례).

  python3 -m pytest tests/test_acceptance_authoring_rule.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import acceptance_authoring_rule as rule


def test_full_suite_assigned_to_builder_is_a_violation():
    body = """## Acceptance
- check: `python3 -m pytest tests/` — full test suite must pass, no regression.
"""
    bad = rule.check_issue_body(1313, body)
    assert bad, "full-suite regression with no builder-exemption should violate"


def test_full_suite_exempted_from_builder_passes():
    # issue #1323's own Acceptance third bullet, verbatim shape.
    body = """## Acceptance
- check: `bash tests/run-orchestrate-tests.sh` passes (no regression) — executed by the req-2 runner itself once it exists; until then by the phase's verification role, not the builder.
"""
    assert rule.check_issue_body(1323, body) == []


def test_builder_scoped_new_tests_only_passes():
    body = """## Acceptance
- check: `python3 -m pytest tests/test_new_feature.py` — new: covers the added behavior.
"""
    assert rule.check_issue_body(1234, body) == []


def test_no_acceptance_section_is_not_this_gates_concern():
    # existence is acceptance_gate.py's job, not this rule's.
    assert rule.check_issue_body(1, "no acceptance section here") == []


def test_entire_test_suite_phrase_without_exemption_violates():
    body = """## Acceptance
- check: `bash tests/run-orchestrate-tests.sh` — entire test suite must pass.
"""
    bad = rule.check_issue_body(999, body)
    assert bad, "entire test suite requirement with no exemption should violate"


def _run_all():
    fns = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok     {fn.__name__}")


if __name__ == "__main__":
    _run_all()
