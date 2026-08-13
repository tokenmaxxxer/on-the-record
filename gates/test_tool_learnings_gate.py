"""issue #1199 (step 1) — hermetic tests for gates/tool_learnings_gate.py.

In-memory literals only, no network, no filesystem outside pytest's own
tmp_path fixture — mirrors test_playbook_depth_gate.py's convention.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tool_learnings_gate import evaluate, classify_entry, main, _blocks_from_text


COMPLETE_ENTRY = (
    "## diagram-design\n"
    "tool: diagram-design (github.com/cathrynlavery/diagram-design)\n"
    "adoption evidence: 1.2k GitHub stars, cited in 3 independent "
    "docs-tooling roundups\n"
    "problem: hand-drawn architecture diagrams drift from the code they "
    "describe and nobody notices until a review catches it\n"
    "how: generates diagrams from a typed spec co-located with the code, "
    "so a diagram is regenerated (not hand-edited) whenever the spec "
    "changes\n"
    "learning: technical-writing's diagram rules -> require diagrams to "
    "be spec-derived, not freehand, for any diagram citing a live "
    "interface\n"
    "source: https://github.com/cathrynlavery/diagram-design"
)


def _drop_facet(entry: str, facet_line_prefix: str) -> str:
    return "\n".join(
        line for line in entry.splitlines()
        if not line.strip().lower().startswith(facet_line_prefix)
    )


def test_complete_entry_accepted():
    r = classify_entry(COMPLETE_ENTRY)
    assert r["accepted"]
    assert r["reasons"] == []


def test_missing_tool_facet_rejected():
    entry = _drop_facet(COMPLETE_ENTRY, "tool:")
    r = classify_entry(entry)
    assert not r["accepted"]
    assert any("tool:" in reason for reason in r["reasons"])


def test_missing_adoption_evidence_rejected():
    entry = _drop_facet(COMPLETE_ENTRY, "adoption evidence:")
    r = classify_entry(entry)
    assert not r["accepted"]
    assert any("adoption-evidence" in reason for reason in r["reasons"])


def test_missing_problem_facet_rejected():
    entry = _drop_facet(COMPLETE_ENTRY, "problem:")
    r = classify_entry(entry)
    assert not r["accepted"]
    assert any("problem:" in reason for reason in r["reasons"])


def test_missing_how_facet_rejected():
    entry = _drop_facet(COMPLETE_ENTRY, "how:")
    r = classify_entry(entry)
    assert not r["accepted"]
    assert any("how:" in reason for reason in r["reasons"])


def test_missing_learning_upgrade_target_rejected():
    entry = COMPLETE_ENTRY.replace(
        "learning: technical-writing's diagram rules -> require diagrams "
        "to be spec-derived, not freehand, for any diagram citing a live "
        "interface\n",
        "learning: this tool is neat\n",
    )
    r = classify_entry(entry)
    assert not r["accepted"]
    assert any("learning:" in reason for reason in r["reasons"])


def test_missing_source_citation_rejected():
    entry = _drop_facet(COMPLETE_ENTRY, "source:")
    r = classify_entry(entry)
    assert not r["accepted"]
    assert any("source" in reason for reason in r["reasons"])


def test_evaluate_passes_within_cap():
    text = COMPLETE_ENTRY
    report = evaluate(text, cap=3)
    assert report["accepted_count"] == 1
    assert report["cap_ok"]
    assert report["passed"]


def test_evaluate_fails_over_cap():
    text = "\n\n".join([COMPLETE_ENTRY.replace("diagram-design", f"tool-{i}") for i in range(4)])
    report = evaluate(text, cap=3)
    assert report["accepted_count"] == 4
    assert not report["cap_ok"]
    assert not report["passed"]


def test_evaluate_fails_when_no_entries_found():
    report = evaluate("# Just a heading\nno entries here.", cap=5)
    assert report["entries"] == []
    assert not report["passed"]


def test_main_exit_code_pass(tmp_path, capsys):
    f = tmp_path / "learnings.md"
    f.write_text(COMPLETE_ENTRY)
    rc = main([str(f), "--role", "technical-writing", "--cap", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "PASS" in out


def test_main_exit_code_fail_missing_target(tmp_path):
    rc = main([str(tmp_path / "nonexistent.md"), "--role", "x", "--cap", "5"])
    assert rc == 1


def test_blocks_from_text_splits_headings():
    text = "## a\nbody a\n## b\nbody b\n"
    blocks = _blocks_from_text(text)
    assert len(blocks) == 2
