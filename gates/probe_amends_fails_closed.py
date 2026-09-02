#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3134.

Covers the degenerate cases `supersedes:` already handles
(`gates/probe_supersession_marker.py`'s sibling module,
`supersession.resolve_authoritative()`), one section grain lower: a
dangling target, a target section anchor that does not exist, two
records amending the same section with conflicting claims, and a cycle.
`amends.resolve_amendments()` must fail closed on each -- excluding the
edge from `amended` rather than picking a winner -- exactly as
`resolve_authoritative()` does for whole-artifact supersession.

This probe fails against current main: `amends.py` does not exist
there, so the import below raises ModuleNotFoundError before any
assertion runs.

Run as `python3 gates/probe_amends_fails_closed.py` from the repo root,
no arguments. Exits 0 on success, non-zero with a message on stderr
otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import amends  # noqa: E402


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def _record(heading: str, extra: str = "") -> str:
    return f"---\nissue: 1\nrole: coding\n{extra}---\n\n## {heading}\n\nbody\n"


def case_dangling_target() -> None:
    print("-- case: dangling target --")
    marker = amends.render_amends_field("docs/issue-1/reports/ghost.md",
                                          "Limitation", "reason")
    tree = {"docs/issue-2/reports/b.md": _record("Correction", f"{marker}\n")}
    verdict = amends.resolve_amendments(tree)
    if verdict["amended"]:
        _fail(f"dangling target: expected no entry in `amended`, got "
              f"{verdict['amended']!r}")
    if verdict["broken"] != ["docs/issue-1/reports/ghost.md"]:
        _fail(f"dangling target: expected it reported in `broken`, got "
              f"{verdict['broken']!r}")
    print(f"  ok: {verdict['broken']!r} -- fails closed, no winner picked")


def case_missing_section_anchor() -> None:
    print("-- case: section anchor that does not exist --")
    marker = amends.render_amends_field("docs/issue-1/reports/a.md",
                                          "NoSuchSection", "reason")
    tree = {
        "docs/issue-1/reports/a.md": _record("Limitation"),
        "docs/issue-2/reports/b.md": _record("Correction", f"{marker}\n"),
    }
    verdict = amends.resolve_amendments(tree)
    if verdict["amended"]:
        _fail(f"missing section: expected no entry in `amended`, got "
              f"{verdict['amended']!r}")
    if verdict["missing_section"] != ["docs/issue-1/reports/a.md#nosuchsection"]:
        _fail(f"missing section: expected it reported in `missing_section`, "
              f"got {verdict['missing_section']!r}")
    print(f"  ok: {verdict['missing_section']!r} -- fails closed, target's "
          "real section left untouched")


def case_conflicting_correctors() -> None:
    print("-- case: two records amending the same section, conflicting claims --")
    marker_b = amends.render_amends_field("docs/issue-1/reports/a.md",
                                            "Limitation", "claim: X is wrong")
    marker_c = amends.render_amends_field("docs/issue-1/reports/a.md",
                                            "Limitation", "claim: Y is wrong")
    tree = {
        "docs/issue-1/reports/a.md": _record("Limitation"),
        "docs/issue-2/reports/b.md": _record("Correction 1", f"{marker_b}\n"),
        "docs/issue-3/reports/c.md": _record("Correction 2", f"{marker_c}\n"),
    }
    verdict = amends.resolve_amendments(tree)
    if verdict["amended"]:
        _fail(f"conflict: expected no entry in `amended`, got "
              f"{verdict['amended']!r} -- content alone cannot say which "
              "corrector is real, so neither may win by default")
    expected_key = "docs/issue-1/reports/a.md#limitation"
    if verdict["conflicts"] != {expected_key: ["docs/issue-2/reports/b.md",
                                                 "docs/issue-3/reports/c.md"]}:
        _fail(f"conflict: expected both correctors listed under "
              f"{expected_key!r}, got {verdict['conflicts']!r}")
    print(f"  ok: {verdict['conflicts']!r} -- fails closed, both correctors "
          "held, neither authoritative")


def case_cycle() -> None:
    print("-- case: cycle (A amends a section of B, B amends a section of A) --")
    marker_a_amends_b = amends.render_amends_field(
        "docs/issue-2/reports/b.md", "Scope", "r1")
    marker_b_amends_a = amends.render_amends_field(
        "docs/issue-1/reports/a.md", "Limitation", "r2")
    tree = {
        "docs/issue-1/reports/a.md": _record("Limitation", f"{marker_a_amends_b}\n"),
        "docs/issue-2/reports/b.md": _record("Scope", f"{marker_b_amends_a}\n"),
    }
    verdict = amends.resolve_amendments(tree)
    if verdict["amended"]:
        _fail(f"cycle: expected no entry in `amended` on either end, got "
              f"{verdict['amended']!r} -- a mutual-correction loop cannot "
              "be resolved from content alone")
    if not verdict["cycles"]:
        _fail("cycle: expected the two edges reported under `cycles`, got "
              "an empty list")
    print(f"  ok: {verdict['cycles']!r} -- fails closed, human resolves the loop")


def main() -> None:
    for case in (case_dangling_target, case_missing_section_anchor,
                 case_conflicting_correctors, case_cycle):
        case()
    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
