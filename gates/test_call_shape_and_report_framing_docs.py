#!/usr/bin/env python3
"""issue-731 — row 7 / row 23 proactive-doc acceptance check.

Asserts that on-the-record/commands/run.md (or a referenced style doc)
proactively names both #726-catalog conventions that were previously
only enforced by a gate/hook with no proactive statement:

(1) row 7 — call-shape-guard.sh's flag-consistency rule for call sites
    sharing the same (argv[0], argv[1]).
(2) row 23 — report-framing-check.sh's four-element report framing
    (resolved problem / prior cost / newly possible / still broken,
    issue #320).

  python3 gates/test_call_shape_and_report_framing_docs.py
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_MD = ROOT / "on-the-record" / "commands" / "run.md"


def t_run_md_states_flag_consistency_rule():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "argv[0]" in text and "argv[1]" in text, (
        "run.md 에 flag 모양 일관성 규칙(#726 row 7)이 없다")
    assert "flag" in text.lower()
    assert "call-shape-guard.sh" in text


def t_run_md_states_report_framing_convention():
    text = RUN_MD.read_text(encoding="utf-8")
    assert "의미론적 효과 프레이밍" in text
    for term in ("문제가 해결", "비용", "새로 가능", "남았는가"):
        assert term in text, f"run.md 에 프레이밍 요소 누락: {term}"


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
