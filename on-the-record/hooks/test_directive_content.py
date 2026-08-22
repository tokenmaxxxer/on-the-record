#!/usr/bin/env python3
"""issue #1660 (northpole req#6) — asserts `directive.sh` carries the
requirement-fidelity program's three obligations (design-research intake,
landing requirement-met grade, scope adherence at landing), each naming
its gate module, alongside the pre-existing #1024/#310 obligations. Text
presence only — no subprocess execution (same shape as the string checks
the rest of this repo's directive-content coverage uses).

  python3 -m pytest on-the-record/hooks/test_directive_content.py
"""
from __future__ import annotations
from pathlib import Path

_DIRECTIVE = (Path(__file__).parent / "directive.sh").read_text(encoding="utf-8")


def t_existing_1024_validity_consult_block_present():
    assert "VALIDITY CONSULT (issue #1024)" in _DIRECTIVE
    assert "validity-consult:" in _DIRECTIVE
    assert "validity-consult-skip: trivial" in _DIRECTIVE


def t_existing_310_acceptance_format_block_present():
    assert "ACCEPTANCE FORMAT" in _DIRECTIVE
    assert "acceptance_gate.py" in _DIRECTIVE


def t_design_research_intake_obligation_present_and_names_gate_module():
    assert "DESIGN-RESEARCH INTAKE (issue #1653)" in _DIRECTIVE
    assert "gates/design_research_consult.py" in _DIRECTIVE
    assert "design-research:" in _DIRECTIVE
    assert "design-research-skip: mechanical" in _DIRECTIVE


def t_landing_requirement_met_grade_obligation_present_and_names_gate_module():
    assert "LANDING REQUIREMENT-MET GRADE (issue #1651)" in _DIRECTIVE
    assert "gates/requirement_met.py" in _DIRECTIVE
    assert "builder-blind" in _DIRECTIVE
    assert "ADVISORY only and never blocks by itself" in _DIRECTIVE


def t_scope_adherence_obligation_present_and_names_gate_module():
    assert "SCOPE ADHERENCE AT LANDING (issue #1658)" in _DIRECTIVE
    assert "gates/scope_adherence.py" in _DIRECTIVE
    assert "scope:" in _DIRECTIVE


def t_verdict_asymmetry_obligation_present_and_names_gate_module():
    assert "VERDICT-ASYMMETRY AT MERGE (issue #1669)" in _DIRECTIVE
    assert "gates/verdict_gate.py" in _DIRECTIVE
    assert "ALLOW_MERGE" in _DIRECTIVE
    assert "never merge on the LLM verdict alone" in _DIRECTIVE


def t_stale_revert_obligation_present_and_names_gate_module():
    assert "STALE-REVERT AT MERGE (issue #1664)" in _DIRECTIVE
    assert "gates/stale_revert_guard.py" in _DIRECTIVE
    assert "REFUSED (rebase required)" in _DIRECTIVE


def t_response_ordering_obligation_present():
    assert "RESPONSE ORDERING (issue #2043" in _DIRECTIVE
    assert "OPENS with" in _DIRECTIVE
    assert "clearly separated" in _DIRECTIVE
    assert "pure-status turn" in _DIRECTIVE


def t_assumption_ledger_obligation_present_and_names_gate_module():
    assert "ASSUMPTION-LEDGER INVENTED-CONFIRM AT INTAKE (issue #1665)" in _DIRECTIVE
    assert "gates/assumption_ledger.py" in _DIRECTIVE
    assert "invented_assumptions()" in _DIRECTIVE
    assert "BLOCKS the" in _DIRECTIVE
    assert "spawn" in _DIRECTIVE


def t_new_obligations_appear_after_existing_1024_block_before_full_procedure():
    """Ordering sanity: the six new/existing blocks land alongside (not
    before) the pre-existing #1024 obligation, and before the directive's
    closing "Full procedure" line — same section of the injected text."""
    idx_1024 = _DIRECTIVE.index("VALIDITY CONSULT (issue #1024)")
    idx_design = _DIRECTIVE.index("DESIGN-RESEARCH INTAKE (issue #1653)")
    idx_req_met = _DIRECTIVE.index("LANDING REQUIREMENT-MET GRADE (issue #1651)")
    idx_scope = _DIRECTIVE.index("SCOPE ADHERENCE AT LANDING (issue #1658)")
    idx_verdict = _DIRECTIVE.index("VERDICT-ASYMMETRY AT MERGE (issue #1669)")
    idx_stale = _DIRECTIVE.index("STALE-REVERT AT MERGE (issue #1664)")
    idx_ledger = _DIRECTIVE.index("ASSUMPTION-LEDGER INVENTED-CONFIRM AT INTAKE (issue #1665)")
    idx_full_procedure = _DIRECTIVE.index("Full procedure: /orchestrate:run")
    assert idx_1024 < idx_design < idx_full_procedure
    assert idx_1024 < idx_req_met < idx_full_procedure
    assert idx_1024 < idx_scope < idx_full_procedure
    assert idx_1024 < idx_verdict < idx_full_procedure
    assert idx_1024 < idx_stale < idx_full_procedure
    assert idx_1024 < idx_ledger < idx_full_procedure


def _run(fn):
    try:
        fn()
        print(f"ok  {fn.__name__}")
        return True
    except AssertionError as e:
        print(f"FAIL {fn.__name__}: {e}")
        return False


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    results = [_run(t) for t in tests]
    ok = all(results)
    print(f"{sum(results)}/{len(results)} passed")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
