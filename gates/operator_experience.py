#!/usr/bin/env python3
"""Mechanical checks for the issue #1006 operator-experience layer.

Two independent, non-LLM checks the harness scenario composes:

- `directive_has_blocks_a_through_d()`: `directive.sh` carries the
  marker strings for blocks A (first-contact gate), B (elicitation
  branch), C (mid-flight narration), D (completion traceability) — a
  static presence check, not a behavioral one.
- `has_testable_acceptance(text)`: whether a piece of operator text
  already carries a testable `## Acceptance`-shaped criterion, per the
  same shape ACCEPTANCE FORMAT already requires in `directive.sh`
  (a `check:`/`gate:` line, a backtick `test/`/`gates/` path, or the
  literal word "Acceptance"). This is the mechanical stand-in for the
  judgment call block B's elicitation branch makes — it decides whether
  a seeded utterance should trip elicitation, without simulating an LLM.

  python3 gates/operator_experience.py [<repo path>]
  exit 0 pass / 1 fail
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

_DIRECTIVE_REL = "on-the-record/hooks/directive.sh"

_BLOCK_MARKERS = {
    "A (first-contact)": "issue #1006 block A",
    "B (elicitation)": "REQUIREMENT ELICITATION (issue #1006 req#4)",
    "C (narration)": "issue #1006 req#5",
    "D (traceability)": "issue #1006 req#1",
}

_ACCEPTANCE_SHAPE = re.compile(
    r"acceptance|check:\s*\S|gate:\s*\S|`(test/|gates/)"
    , re.IGNORECASE,
)


def has_testable_acceptance(text: str) -> bool:
    return bool(_ACCEPTANCE_SHAPE.search(text))


def directive_has_blocks_a_through_d(root: Path) -> list[str]:
    path = root / _DIRECTIVE_REL
    if not path.exists():
        return [f"{_DIRECTIVE_REL} not found"]
    text = path.read_text(encoding="utf-8")
    problems = []
    for label, marker in _BLOCK_MARKERS.items():
        if marker not in text:
            problems.append(f"block {label} marker missing: {marker!r}")
    return problems


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    problems = directive_has_blocks_a_through_d(root)
    if problems:
        for p in problems:
            print(f"FAIL {p}")
        return 1
    print("PASS directive.sh carries blocks A-D")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
