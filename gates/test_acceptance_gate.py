#!/usr/bin/env python3
"""issue-310 — `acceptance_gate.check_issue_body`의 단위테스트.

네트워크·GitHub 없이 도는 것만(`test_gates.py`/`test_closes_gate_ci.py` 와
같은 관례). `pr_reference.py`/`check()`와의 배선은 `check_issue_body`가
순수 함수라 여기서 직접 검증한다 — `gates/test_closes_gate_ci.py` 가
`pr_reference.check_body`를 검증하는 것과 같은 분리.

  python3 gates/test_acceptance_gate.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import acceptance_gate


def t_prose_only_acceptance_blocks():
    body = """## Acceptance
- It should work correctly and users should be happy.
- The team agrees this is done.
"""
    bad = acceptance_gate.check_issue_body(310, body)
    assert bad, "prose-only Acceptance should be a violation"


def t_artifact_reference_passes():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
- empty state: not applicable — regression test, no empty-state case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_gates_workflow_path_no_longer_passes():
    """issue-499: `.github/workflows/` was retired by #460 and is no
    longer an accepted executable-artifact reference."""
    body = """## Acceptance
- CI job at `.github/workflows/ci.yml` must be green.
- empty state: not applicable — CI status has no empty-state case.
- provenance: executed-live
"""
    assert acceptance_gate.check_issue_body(310, body) != []


def t_gate_colon_line_passes():
    body = """## Acceptance
- gate: acceptance_gate
- empty state: not applicable — gate invocation has no empty-state case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_unverifiable_escape_passes():
    body = """## Acceptance
unverifiable: this is a subjective UX judgment with no mechanical check.
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_missing_acceptance_section_blocks():
    body = "## Request\nDo the thing.\n"
    bad = acceptance_gate.check_issue_body(310, body)
    assert bad, "missing '## Acceptance' section should fail closed"


def t_acceptance_heading_case_and_level_insensitive():
    body = """### acceptance
- `test/foo.py` passes.
- empty state: not applicable — regression test, no empty-state case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(310, body) == []


def t_only_reads_acceptance_section_not_whole_body():
    body = """## Acceptance
No artifact here, just prose.

## Out of scope
- `gates/unrelated.py` mentioned here should not count.
"""
    bad = acceptance_gate.check_issue_body(310, body)
    assert bad, "an artifact reference outside the Acceptance section must not count"


def t_artifact_reference_without_empty_state_or_provenance_blocks():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
"""
    bad = acceptance_gate.check_issue_body(416, body)
    assert bad, "artifact reference with no empty state/provenance must block"
    assert any("empty state" in b for b in bad), bad
    assert any("provenance" in b for b in bad), bad


def t_empty_state_and_provenance_present_passes():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
- empty state: `gates/test_acceptance_gate.py::t_missing_acceptance_section_blocks`
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(416, body) == []


def t_unverifiable_exempts_empty_state_and_provenance():
    body = """## Acceptance
unverifiable: this is a subjective UX judgment with no mechanical check.
"""
    assert acceptance_gate.check_issue_body(416, body) == []


def t_empty_state_not_applicable_passes():
    body = """## Acceptance
- `gates/test_acceptance_gate.py` run and shown passing.
- empty state: not applicable — pure read-only query, no "nothing exists yet" case.
- provenance: executed-unit
"""
    assert acceptance_gate.check_issue_body(416, body) == []


def t_all_three_violations_reported_together():
    """issue-555: prose-only + no empty state + no provenance, all at
    once, must appear in the SAME refusal, not one per round-trip."""
    body = """## Acceptance
- It should work correctly and users should be happy.
"""
    bad = acceptance_gate.check_issue_body(555, body)
    assert any("프로즈뿐" in b or "unverifiable" in b for b in bad), bad
    assert any("empty state" in b for b in bad), bad
    assert any("provenance" in b for b in bad), bad
    assert any("executed-live|executed-unit|read" in b for b in bad), bad
    assert len(bad) == 3, bad


def t_issue_2085_all_three_named_in_single_refusal():
    """issue-2085: drive an issue body missing check-grammar, empty-state,
    AND provenance all at once, and assert the single refusal names all
    three — reproduces the tm-dicequest#55 report where three separate
    spawn attempts each surfaced a different lone missing element."""
    body = """## Acceptance
It should work correctly and users should be happy with the result.
"""
    bad = acceptance_gate.check_issue_body(2085, body)
    assert len(bad) == 3, bad
    assert any("프로즈뿐" in b for b in bad), bad
    assert any("empty state" in b for b in bad), bad
    assert any("provenance" in b for b in bad), bad


def t_missing_section_message_points_at_format_doc():
    """issue-2229: the diagnostic must name the concrete passing shape,
    not just what's missing."""
    bad = acceptance_gate.check_issue_body(2229, "## Request\nDo it.\n")
    assert bad and all(acceptance_gate._FORMAT_DOC in b for b in bad), bad


def t_other_three_violation_messages_point_at_format_doc():
    bad = acceptance_gate.check_issue_body(
        2229, "## Acceptance\nIt should work.\n")
    assert len(bad) == 3, bad
    assert all(acceptance_gate._FORMAT_DOC in b for b in bad), bad


def t_issue_2229_own_repro_shape_caught_at_authoring_time():
    """issue-2229's own repro: gate:/empty state:/provenance: lines
    present but no '## Acceptance' heading at all — the exact shape
    that sat silently unspawnable for five issues tonight because the
    gate previously only fired as a spawn-time warning on the one issue
    being spawned. Constructed locally, not via a live `gh issue
    create` — role sessions never author issues (contract v3 s9,
    gh-guard); the pure `check_issue_body` function is the mechanism
    both the spawn-time gate and the new authoring-time sweep share, so
    exercising it directly here is exercising the same code path."""
    malformed_body = (
        "## What happened\n"
        "gate: some/thing\nempty state: n/a\nprovenance: executed-live\n"
    )
    bad = acceptance_gate.check_issue_body(999901, malformed_body)
    assert bad, ("gate:/empty state:/provenance: lines without a '## "
                 f"Acceptance' heading must still be caught; got {bad!r}")


def t_well_formed_test_issue_passes_at_authoring_time():
    well_formed_body = (
        "## Acceptance\n"
        "- `gates/test_acceptance_gate.py` run and shown passing.\n"
        "- empty state: repo with zero open issues sweeps cleanly.\n"
        "- provenance: executed-unit\n"
    )
    assert acceptance_gate.check_issue_body(999902, well_formed_body) == []


def t_sweep_empty_open_issues_returns_empty_dict():
    """issue-2229 acceptance empty state: a repo with zero open issues
    must sweep cleanly, not error."""
    assert acceptance_gate.sweep_issue_bodies([]) == {}


def t_sweep_reports_only_violating_issues():
    open_issues = [
        {"number": 1, "body": "## Acceptance\n- `gates/x.py` covers this\n"
                               "empty state: n/a\nprovenance: executed-unit\n"},
        {"number": 2, "body": "## What happened\nno acceptance here\n"},
    ]
    result = acceptance_gate.sweep_issue_bodies(open_issues)
    assert list(result.keys()) == [2], result
    assert result[2], result


def t_sweep_skips_entries_with_no_number():
    open_issues = [{"body": "## Acceptance\nprose only\n"}]
    assert acceptance_gate.sweep_issue_bodies(open_issues) == {}


def t_format_sweep_report_empty_is_clean():
    report = acceptance_gate.format_sweep_report({})
    assert "없음" in report, report


def t_format_sweep_report_lists_each_issue():
    report = acceptance_gate.format_sweep_report(
        {2216: ["reason a"], 2217: ["reason b"]})
    assert "#2216" in report and "#2217" in report, report
    assert "reason a" in report and "reason b" in report, report


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
