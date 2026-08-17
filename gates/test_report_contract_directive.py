#!/usr/bin/env python3
"""issue-1706 — orchestrator report contract, encoded in the directive.

Asserts that on-the-record/commands/run.md states the report contract
that layers on top of report-framing-check.sh's four-element check
(issue #320): (1) a lead line stating the turn's outcome in one
sentence, before anything else; (2) the four frame parts in a fixed
order (resolved problem -> prior cost -> newly possible -> still
broken); (3) every status/defect claim carries an inline source ref;
(4) a bullet cap of <=5 per part. report-framing-check.sh itself is
untouched by this issue -- it still only gates the four parts' presence.

  python3 gates/test_report_contract_directive.py
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_MD = ROOT / "on-the-record" / "commands" / "run.md"


def t_run_md_states_lead_line_rule():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "선행 한 줄" in text or "lead line" in text
    assert "결론을 한 문장으로" in text


def t_run_md_states_fixed_part_order():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "4부 고정 순서" in text
    assert "해결된 문제 → 그 문제의 이전 비용 → 새로 가능해진 것 →" in text
    assert "아직 남은 것" in text


def t_run_md_states_per_claim_source_ref():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "주장별 근거 ref" in text
    assert "인라인으로 붙인다" in text


def t_run_md_states_bullet_cap():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "파트당 불릿 상한" in text
    assert "최대 5개" in text


def t_run_md_ties_contract_to_report_framing_check():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "report-framing-check" in text
    idx_hook = text.index("report-framing-check 훅은")
    idx_contract = text.index("보고 계약")
    assert idx_contract < idx_hook


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    import sys
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("t_") and callable(f)]
    _run(tests)
    sys.exit(0)
