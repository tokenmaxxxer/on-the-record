#!/usr/bin/env python3
"""issue #1199 (step 1) — per-role tool-landscape fold-in shape gate.

Sibling of gates/playbook_depth_gate.py, for a structurally different
program: instead of condition+choice+source decision-rule prose, a
tool-learnings entry is a fixed-field record — {tool, adoption evidence,
problem, how, learning} — plus a fetched-source citation. This gate
parses candidate entries out of a role's tool-learnings section, checks
every required facet is present, and enforces a per-role entry-count cap
(issue #1199: "bounded... not tool catalogs").

A candidate entry is one Markdown heading (`## `/`### `) or top-level
list item (`- `/`* `) under a "## Tool learnings" section, together with
its body text up to the next block of the same kind — same splitting
approach as playbook_depth_gate.py's `_blocks_from_text`.

  python3 gates/tool_learnings_gate.py <file-or-dir> --role <name> --cap <N>
  exit 0 pass / 1 fail; prints a per-entry reason table to stdout.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")
_LISTITEM_RE = re.compile(r"^\s*[-*]\s+(.*)$")

_TOOL_MARKER = re.compile(r"(?i)\btool\s*:")
_ADOPTION_MARKER = re.compile(
    r"(?i)\badoption\s*(evidence)?\s*:|\bstars?\b|\bdownloads?\b|\bmentions?\b"
)
_PROBLEM_MARKER = re.compile(r"(?i)\bproblem\s*:")
_HOW_MARKER = re.compile(r"(?i)\bhow\s*:")
_LEARNING_MARKER = re.compile(
    r"(?i)\blearning\s*:.*(?:->|→|upgrades?|deliverable|rule|judgment)"
)
_SOURCE_MARKER = re.compile(
    r"(?i)source\s*:|https?://|\(\d{4}\)"
)

REQUIRED_FACETS = [
    ("tool", _TOOL_MARKER, "no `tool:` facet"),
    ("adoption_evidence", _ADOPTION_MARKER, "no adoption-evidence facet"),
    ("problem", _PROBLEM_MARKER, "no `problem:` facet"),
    ("how", _HOW_MARKER, "no `how:` facet"),
    ("learning", _LEARNING_MARKER, "no `learning:` facet naming the upgraded deliverable/rule"),
    ("source", _SOURCE_MARKER, "no fetched-source citation"),
]


def _blocks_from_text(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        if _HEADING_RE.match(line) or _LISTITEM_RE.match(line):
            flush()
            current.append(line)
        elif current:
            current.append(line)
    flush()
    return [b for b in blocks if b.strip() and not _is_bare_header(b)]


def _is_bare_header(block: str) -> bool:
    lines = block.strip().splitlines()
    return bool(_HEADING_RE.match(lines[0])) and len(lines) == 1


def _summary(block: str) -> str:
    first_line = block.strip().splitlines()[0] if block.strip() else ""
    m = _HEADING_RE.match(first_line)
    if m:
        return m.group(2)[:80]
    m = _LISTITEM_RE.match(first_line)
    if m:
        return m.group(1)[:80]
    return first_line[:80]


def classify_entry(block: str) -> dict:
    """Returns {accepted, reasons, summary} for one candidate entry."""
    reasons = [msg for _, pattern, msg in REQUIRED_FACETS if not pattern.search(block)]
    return {
        "accepted": not reasons,
        "reasons": reasons,
        "summary": _summary(block),
    }


def evaluate(text: str, cap: int) -> dict:
    blocks = _blocks_from_text(text)
    results = [classify_entry(b) for b in blocks]
    accepted = [r for r in results if r["accepted"]]

    all_facets_ok = all(r["accepted"] for r in results) if results else True
    cap_ok = len(accepted) <= cap

    return {
        "entries": results,
        "accepted_count": len(accepted),
        "cap": cap,
        "all_facets_ok": all_facets_ok,
        "cap_ok": cap_ok,
        "passed": all_facets_ok and cap_ok and bool(results),
    }


def _read_text(target: Path) -> str:
    if target.is_dir():
        parts = []
        for p in sorted(target.rglob("*.md")):
            parts.append(p.read_text())
        return "\n\n".join(parts)
    return target.read_text()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--role", required=True)
    ap.add_argument("--cap", type=int, required=True)
    args = ap.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"FAIL: {target} does not exist", file=sys.stderr)
        return 1

    report = evaluate(_read_text(target), args.cap)

    for i, r in enumerate(report["entries"]):
        verdict = "ACCEPT" if r["accepted"] else "REJECT"
        reason = "; ".join(r["reasons"]) if r["reasons"] else "ok"
        print(f"{verdict} #{i}: {r['summary']!r} — {reason}")

    print(
        f"\nrole={args.role} accepted={report['accepted_count']} "
        f"cap={report['cap']} cap_ok={report['cap_ok']}"
    )
    if not report["cap_ok"]:
        print(
            f"FAIL: accepted entry count {report['accepted_count']} "
            f"exceeds cap {report['cap']}"
        )
    if not report["entries"]:
        print("FAIL: no tool-learnings entries found")

    if report["passed"]:
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
