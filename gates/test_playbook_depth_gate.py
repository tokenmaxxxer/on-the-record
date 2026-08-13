"""issue #1174 (c) — hermetic tests for gates/playbook_depth_gate.py.

No network, no filesystem outside pytest's own tmp_path fixture — every
sample playbook text is an in-memory literal.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from playbook_depth_gate import evaluate, classify_block, main, _blocks_from_text


DECISION_RULE = (
    "- When the field type is a boolean, use a toggle switch, not a "
    "checkbox — checkboxes read as list-membership, not on/off state. "
    "source: Nielsen Norman Group, 'Checkboxes vs Toggle Switches' (2018)"
)
REMOVAL_RULE = (
    "- When a screen has more than 7 primary actions, drop the least-used "
    "ones behind a secondary menu (progressive disclosure) to reduce "
    "visual noise. source: Krug, Don't Make Me Think, 3rd ed., ch. 4"
)
GLOSSARY_LINE = "- Affordance is a property of an object that suggests its own usage."

# Derived from tokenmaxxxer/technical-writing-rulebook#25's actual
# playbook format (playbook/doc-type-selection.md, issue-1174/
# operational-playbook branch): numbered ("1. ") ordered-list rules,
# not heading or "-"/"*" blocks.
NUMBERED_DECISION_RULE = (
    "1. When the reader's stated goal is \"I want to learn by doing and "
    "have no working knowledge yet,\" choose **tutorial** — a tutorial "
    "puts the reader \"on rails\" toward one fixed destination with "
    "exact steps and no decision points, because a beginner cannot yet "
    "evaluate branches. source: https://diataxis.fr/start-here/"
)
NUMBERED_REMOVAL_RULE = (
    "6. When a single draft's outline mixes conceptual \"why\" prose "
    "with numbered action steps, split it into two documents rather "
    "than keep the mixed draft as one. **REMOVAL**: cut whichever half "
    "doesn't match the file's own doc-type before publishing, don't "
    "keep both halves \"for completeness.\" source: https://diataxis.fr/"
)
NUMBERED_DOT_RULE = (
    "1) When the reader already has baseline competence and states a "
    "concrete task, choose **how-to guide**, not tutorial — how-to "
    "guides help the reader reach a destination of their choosing. "
    "source: https://diataxis.fr/"
)


def test_decision_rule_accepted_as_addition():
    r = classify_block(DECISION_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"
    assert r["reasons"] == []


def test_removal_rule_accepted_as_removal():
    r = classify_block(REMOVAL_RULE)
    assert r["accepted"]
    assert r["category"] == "removal"


def test_glossary_block_rejected():
    r = classify_block(GLOSSARY_LINE)
    assert not r["accepted"]
    assert any("glossary" in reason for reason in r["reasons"])


def test_uncited_rule_rejected():
    uncited = "- When the field is numeric, use a stepper control instead of free text."
    r = classify_block(uncited)
    assert not r["accepted"]
    assert any("source" in reason for reason in r["reasons"])


def test_evaluate_passes_when_floor_met_and_removal_present():
    text = "\n\n".join([DECISION_RULE] * 4 + [REMOVAL_RULE])
    report = evaluate(text, floor=5, axes=["control-selection"])
    assert report["accepted_count"] == 5
    assert report["count_ok"]
    assert report["missing_removal_axes"] == []
    assert report["passed"]


def test_evaluate_fails_all_additive_playbook():
    text = "\n\n".join([DECISION_RULE] * 6)
    report = evaluate(text, floor=5, axes=["control-selection"])
    assert report["count_ok"]
    assert report["missing_removal_axes"] == ["control-selection"]
    assert not report["passed"]


def test_evaluate_fails_short_of_floor():
    text = DECISION_RULE
    report = evaluate(text, floor=5, axes=[])
    assert not report["count_ok"]
    assert not report["passed"]


def test_evaluate_glossary_shaped_file_never_reaches_floor():
    text = "\n\n".join([GLOSSARY_LINE] * 10)
    report = evaluate(text, floor=5, axes=[])
    assert report["accepted_count"] == 0
    assert not report["passed"]


def test_main_exit_code_pass(tmp_path):
    f = tmp_path / "playbook.md"
    f.write_text("\n\n".join([DECISION_RULE] * 2 + [REMOVAL_RULE]))
    rc = main([str(f), "--role", "ux-engineering", "--floor", "3", "--axes", "control-selection"])
    assert rc == 0


def test_main_exit_code_fail(tmp_path):
    f = tmp_path / "playbook.md"
    f.write_text(GLOSSARY_LINE)
    rc = main([str(f), "--role", "ux-engineering", "--floor", "3"])
    assert rc == 1


def test_main_missing_target(tmp_path):
    rc = main([str(tmp_path / "nope.md"), "--role", "x", "--floor", "1"])
    assert rc == 1


def test_numbered_decision_rule_accepted_as_addition():
    r = classify_block(NUMBERED_DECISION_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"
    assert r["reasons"] == []


def test_numbered_removal_rule_accepted_as_removal():
    r = classify_block(NUMBERED_REMOVAL_RULE)
    assert r["accepted"]
    assert r["category"] == "removal"


def test_numbered_dot_style_rule_accepted():
    r = classify_block(NUMBERED_DOT_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"


def test_evaluate_numbered_playbook_meets_floor_and_axis():
    text = "\n\n".join(
        [NUMBERED_DECISION_RULE] * 4 + [NUMBERED_REMOVAL_RULE]
    )
    report = evaluate(text, floor=5, axes=["doc-type-selection"])
    assert report["accepted_count"] == 5
    assert report["count_ok"]
    assert report["missing_removal_axes"] == []
    assert report["passed"]


def test_main_reads_directory(tmp_path):
    d = tmp_path / "playbook"
    d.mkdir()
    (d / "a.md").write_text(DECISION_RULE)
    (d / "b.md").write_text(REMOVAL_RULE)
    rc = main([str(d), "--role", "ux-engineering", "--floor", "2"])
    assert rc == 0


# issue #1174 gate fix 2 — real content pulled from
# tokenmaxxxer/technical-writing-rulebook PR #25, branch
# issue-1174/operational-playbook, playbook/minimalism-scoping.md rule 2
# and playbook/doc-type-selection.md's "## Rules" section marker.
RELOCATION_RULE = (
    "2. When a section explains background the reader does not need to "
    "complete the immediate task, move it to an explanation doc or a "
    "collapsed/linked aside rather than inline it — Carroll's minimalism "
    "principle is \"the smallest amount of information necessary to "
    "achieve the reader's goals,\" and unrequested background is exactly "
    "the surplus that principle targets. source: "
    "https://en.wikipedia.org/wiki/Minimalism_(technical_communication)"
)
BARE_SECTION_HEADER = "## Rules"


def test_relocation_rule_accepted_via_move_verb():
    r = classify_block(RELOCATION_RULE)
    assert r["accepted"]
    assert r["category"] == "addition"
    assert r["reasons"] == []


def test_bare_section_header_not_counted_as_block():
    text = f"{BARE_SECTION_HEADER}\n\n{RELOCATION_RULE}"
    blocks = _blocks_from_text(text)
    assert len(blocks) == 1
    assert blocks[0].strip() == RELOCATION_RULE.strip()


def test_evaluate_real_minimalism_axis_excerpt_counts_relocation_rule():
    text = f"{BARE_SECTION_HEADER}\n\n{RELOCATION_RULE}\n\n{REMOVAL_RULE}"
    report = evaluate(text, floor=2, axes=["minimalism-scoping"])
    assert report["accepted_count"] == 2
    assert report["count_ok"]
    assert report["passed"]
