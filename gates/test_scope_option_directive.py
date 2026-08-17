#!/usr/bin/env python3
"""issue-1707 -- scope-option proposal duty, encoded in the directive.

Asserts on-the-record/hooks/directive.sh states: (1) the trigger subclass
(design-bearing AND scope-ambiguous) and the explicit non-overlap
statement against #1006 req#4's open-question path for all other vague
asks; (2) the option-block form -- exactly 2-3 options, each carrying
scope/cost/risk/non-goals fields, ordered by ascending scope size; (3) the
verifiable neutrality rule -- the literal token "recommended" (any case)
must not appear in the option block; (4) each option cites its
validity/risk consult trace.

  python3 gates/test_scope_option_directive.py
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIRECTIVE_SH = ROOT / "on-the-record" / "hooks" / "directive.sh"


def _text():
    return DIRECTIVE_SH.read_text(encoding="utf-8")


def t_states_trigger_subclass():
    text = _text()
    assert "SCOPE-OPTION PROPOSAL" in text
    assert "design-bearing" in text
    assert "scope-ambiguous" in text
    assert "BOTH design-bearing" in text and "AND\n  scope-ambiguous" in text


def t_states_non_overlap_with_1006_req4():
    text = _text()
    idx_scope_option = text.index("SCOPE-OPTION PROPOSAL")
    idx_req4 = text.index("REQUIREMENT ELICITATION")
    assert idx_req4 < idx_scope_option
    section = text[idx_scope_option:idx_scope_option + 1200]
    assert "Every\n  other vague ask" in section
    assert "keeps REQUIREMENT ELICITATION's open-question path\n  above unchanged" in section


def t_states_option_block_count_and_order():
    text = _text()
    normalized = " ".join(text.split())
    assert "exactly 2 or 3 options" in normalized
    assert "ordered by ascending scope size" in normalized
    assert "narrowest-scope option first" in normalized


def t_states_option_fields():
    text = _text()
    section = text[text.index("SCOPE-OPTION PROPOSAL"):text.index("VALIDITY CONSULT")]
    for field in ("\\`scope:\\`", "\\`cost:\\`", "\\`risk:\\`", "\\`non-goals:\\`"):
        assert field in section, field


def t_states_neutrality_rule_forbids_recommended_token():
    text = _text()
    section = text[text.index("SCOPE-OPTION PROPOSAL"):text.index("VALIDITY CONSULT")]
    assert "\\`recommended\\`" in section
    assert "case-insensitive" in section
    assert "MUST NOT appear" in section
    assert "no preference" in section


def t_states_consult_trace_per_option():
    text = _text()
    section = text[text.index("SCOPE-OPTION PROPOSAL"):text.index("VALIDITY CONSULT")]
    assert "\\`consult-trace:\\`" in section
    assert "validity/risk consult ref" in section


def t_states_consult_runs_on_vague_ask_before_options():
    # issue #1712: consult-ordering gap -- the validity consult runs on
    # the vague ask FIRST, before any option exists, and options derive
    # from its output.
    text = _text()
    section = text[text.index("SCOPE-OPTION PROPOSAL"):text.index("VALIDITY CONSULT")]
    normalized = " ".join(section.split())
    assert "ON THE VAGUE ASK ITSELF, first, before any option exists" in normalized
    assert "Derive the OPTION BLOCK from that consult's output" in normalized
    assert "may reference the same trace instead of re-running it" in normalized


def t_states_neutrality_rule_forbids_korean_synonyms():
    # issue #1712: neutrality rule additionally bars 권장 and 추천.
    text = _text()
    section = text[text.index("SCOPE-OPTION PROPOSAL"):text.index("VALIDITY CONSULT")]
    assert "권장" in section
    assert "추천" in section
    assert "MUST NOT appear" in section


def t_states_banner_mentions_option_path():
    # issue #1712: first-contact banner must mention the option path, not
    # just clarifying questions.
    text = _text()
    start = text.index("First time in this workspace")
    banner = text[start:text.index("EOF0", start)]
    assert "option block" in banner
    assert "design-bearing" in banner
    assert "scope-ambiguous" in banner


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
