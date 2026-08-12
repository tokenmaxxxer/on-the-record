#!/usr/bin/env python3
"""issue #1017 (northpole req#6) — `requirement_linkage` 라이브-파이어
테스트(issue #914 mechanism b): 모듈을 실제로 import·호출해 두 가지
서로 다른 결과(위반 있음/없음)가 실제로 나오는지 증명한다.

  python3 gates/test_requirement_linkage.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import requirement_linkage


def t_check_issue_body_denies_body_with_no_requirement_citation():
    bad = requirement_linkage.check_issue_body(
        1099, "This issue does not name any requirement at all.")
    assert bad, "no requirement citation and no infra tag must be denied"


def t_check_issue_body_allows_body_citing_a_requirement_id():
    bad = requirement_linkage.check_issue_body(
        1099, "This closes the loop for R001.")
    assert bad == [], bad


def t_check_issue_body_allows_infrastructure_tagged_body():
    bad = requirement_linkage.check_issue_body(
        1099, "Pure infra work.\ninfrastructure/no-direct-requirement")
    assert bad == [], bad


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
