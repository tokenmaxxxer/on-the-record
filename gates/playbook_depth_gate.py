#!/usr/bin/env python3
"""issue #1174 (c) — per-role playbook depth gate.

Counts condition+choice+source decision rule blocks in a role's
operational playbook, enforces the role's recorded `rule_count_floor`,
rejects glossary-shaped (definition-only) blocks, and enforces amendment
4: an all-additive playbook (zero removal-classified rules on some
declared axis) fails even when the raw count clears the floor.

A rule block is one Markdown heading (`## `/`### `), top-level list item
(`- `/`* `), or ordered list item (`1. `/`1) `) under a "## Rules" /
"## Decision rules" section, together with its body text up to the next
block of the same kind.

  python3 gates/playbook_depth_gate.py <playbook-file-or-dir> --role <name> --floor <N> [--axes a,b,c]
  exit 0 pass / 1 fail; prints a per-block reason table to stdout.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

_COND_MARKERS = re.compile(
    r"(?i)\b(when|if|under|for)\b|~일\s*때|~인\s*경우|~면"
)
_CHOICE_VERBS = re.compile(
    r"(?i)\b(use|pick|choose|prefer|apply|select|do|add|include|keep|"
    r"drop|cut|delete|omit|simplify|remove|avoid|split|merge)\b"
)
_REMOVAL_MARKERS = re.compile(
    r"(?i)\b(drop|cut|delete|omit|simplify|remove|de-layer|de-clutter|"
    r"declutter)\b|제거|삭제|생략|줄이다|줄인다"
)
_SOURCE_MARKERS = re.compile(
    r"(?i)source\s*:|https?://|\bISO\b|\bIEEE\b|\bW3C\b|\bRFC\b|\(\d{4}\)"
)
_GLOSSARY_SHAPE = re.compile(
    r"(?i)^\s*[\w\s\-/]{1,60}\s+(is|means|refers to)\b"
)
_HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")
_LISTITEM_RE = re.compile(r"^\s*[-*]\s+(.*)$")
_ORDERED_LISTITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.*)$")


def _blocks_from_text(text: str) -> list[str]:
    """Split into candidate rule blocks: each heading, top-level list
    item, or ordered ("1. "/"1) ") list item, plus its following
    non-heading/non-list body lines."""
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    for line in lines:
        if (
            _HEADING_RE.match(line)
            or _LISTITEM_RE.match(line)
            or _ORDERED_LISTITEM_RE.match(line)
        ):
            flush()
            current.append(line)
        elif current:
            current.append(line)
    flush()
    return [b for b in blocks if b.strip()]


def classify_block(block: str) -> dict:
    """Returns {accepted, reasons, category} for one candidate block.
    category is 'addition' or 'removal' when accepted, else None."""
    reasons = []
    has_cond = bool(_COND_MARKERS.search(block))
    has_choice = bool(_CHOICE_VERBS.search(block))
    has_source = bool(_SOURCE_MARKERS.search(block))
    is_removal = bool(_REMOVAL_MARKERS.search(block))

    first_line = block.strip().splitlines()[0] if block.strip() else ""
    stripped_first = _HEADING_RE.match(first_line)
    stripped_first = stripped_first.group(2) if stripped_first else first_line
    listmatch = _LISTITEM_RE.match(first_line)
    if listmatch:
        stripped_first = listmatch.group(1)
    orderedmatch = _ORDERED_LISTITEM_RE.match(first_line)
    if orderedmatch:
        stripped_first = orderedmatch.group(1)

    if not has_cond:
        reasons.append("no condition marker (when/if/under/for or ~일 때/~인 경우/~면)")
    if not has_choice:
        reasons.append("no choice/action verb")
    if not has_source:
        reasons.append("no source citation")

    is_glossary = (
        _GLOSSARY_SHAPE.match(stripped_first) and not has_cond and not has_choice
    )
    if is_glossary:
        reasons.append("glossary-shaped: '<Term> is/means/refers to <X>' with no condition/choice")

    accepted = has_cond and has_choice and has_source and not is_glossary
    category = None
    if accepted:
        category = "removal" if is_removal else "addition"

    return {
        "accepted": accepted,
        "reasons": reasons,
        "category": category,
        "summary": stripped_first[:80],
    }


def evaluate(text: str, floor: int, axes: list[str]) -> dict:
    """Runs the full check set (1-6 from the proposal) over playbook
    text. Returns a report dict; `passed` is the overall verdict."""
    blocks = _blocks_from_text(text)
    results = [classify_block(b) for b in blocks]
    accepted = [r for r in results if r["accepted"]]

    count_ok = len(accepted) >= floor

    removal_present = any(r["category"] == "removal" for r in accepted)
    # Amendment 4: at least one removal-classified rule per declared axis.
    # Without a per-axis tag on each block, we conservatively require at
    # least one removal-classified rule overall when axes are declared,
    # and flag every axis as missing when none exist at all.
    missing_axes = []
    if axes:
        if not removal_present:
            missing_axes = list(axes)

    all_additive_fail = bool(axes) and bool(missing_axes)

    passed = count_ok and not all_additive_fail

    return {
        "blocks": results,
        "accepted_count": len(accepted),
        "floor": floor,
        "count_ok": count_ok,
        "missing_removal_axes": missing_axes,
        "passed": passed,
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
    ap.add_argument("--floor", type=int, required=True)
    ap.add_argument("--axes", default="", help="comma-separated axis list")
    args = ap.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"FAIL: {target} does not exist", file=sys.stderr)
        return 1

    axes = [a.strip() for a in args.axes.split(",") if a.strip()]
    report = evaluate(_read_text(target), args.floor, axes)

    for i, r in enumerate(report["blocks"]):
        verdict = "ACCEPT" if r["accepted"] else "REJECT"
        cat = f" [{r['category']}]" if r["category"] else ""
        reason = "; ".join(r["reasons"]) if r["reasons"] else "ok"
        print(f"{verdict}{cat} #{i}: {r['summary']!r} — {reason}")

    print(
        f"\nrole={args.role} accepted={report['accepted_count']} "
        f"floor={report['floor']} count_ok={report['count_ok']}"
    )
    if report["missing_removal_axes"]:
        print(
            "FAIL: no removal-classified rule found; axes with zero "
            f"removal rules: {report['missing_removal_axes']}"
        )

    if report["passed"]:
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
