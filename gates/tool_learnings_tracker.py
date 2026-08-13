#!/usr/bin/env python3
"""issue #1199 — renders this issue's 43-item tool-learnings tracker as a
Markdown checklist. Sibling of gates/playbook_tracker.py, kept on a
distinct spec field (`tool_learnings_refs`, not `playbook_refs`) so this
program's landed-count never conflates with #1174's (issue #1199: "Runs
independently of #1174: separate issue, separate branches").

A role counts as landed once its `roles/specs/<role>.spec.json` carries
a non-empty `tool_learnings_refs` array — the mechanical signal that a
real tool-landscape fold-in landed and was wired back into the spec.

  python3 gates/tool_learnings_tracker.py [--roles-dir <dir>] [--specs-dir <dir>]
  prints a Markdown checklist to stdout; exit 0 always (rendering, not a
  gate — nothing here blocks a commit).
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def discover_roles(roles_dir: Path) -> list[str]:
    return sorted(p.stem for p in roles_dir.glob("*.json"))


def is_landed(role: str, specs_dir: Path) -> bool:
    spec_path = specs_dir / f"{role}.spec.json"
    if not spec_path.is_file():
        return False
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    refs = spec.get("tool_learnings_refs")
    return isinstance(refs, list) and len(refs) > 0


def render(roles: list[str], specs_dir: Path) -> str:
    landed = [r for r in roles if is_landed(r, specs_dir)]
    lines = [
        f"## Tool-learnings completion tracker ({len(landed)}/{len(roles)})",
        "",
    ]
    for role in roles:
        mark = "x" if role in landed else " "
        lines.append(f"- [{mark}] {role}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roles-dir", default=str(ROOT / "roles"))
    ap.add_argument("--specs-dir", default=str(ROOT / "roles" / "specs"))
    args = ap.parse_args(argv)

    roles = discover_roles(Path(args.roles_dir))
    print(render(roles, Path(args.specs_dir)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
