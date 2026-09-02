#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3059, criterion 2.

Exists so that criterion can be stated as a plain `check:` line
(`python3 gates/probe_unmapped_reason.py`) instead of a shell one-liner
with quotes nested inside an issue body.

Calls `check_runner.parse_checks` directly (no subprocess, no network)
against two minimal Acceptance bodies:

- a bare `grep` check (no `bash -c` wrapper) must classify as judgment
  with `reason == "unmapped-interpreter"`.
- a genuinely prose check (no backtick command at all) must classify as
  judgment WITHOUT that reason -- this is the symmetric negative case:
  the fix must not start labelling prose as an unmapped interpreter.

Run as `python3 gates/probe_unmapped_reason.py` from the repo root, no
arguments. Prints `ok` and exits 0 on success; prints a message to
stderr and exits non-zero otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_runner  # noqa: E402

BARE_GREP_SECTION = "## Acceptance\n- x\n  - check: `grep -n foo bar.md`\n"
PROSE_SECTION = (
    "## Acceptance\n"
    "- check: the documented invocation line, run as written, "
    "produces two workspaces\n"
)


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    grep_checks = check_runner.parse_checks(BARE_GREP_SECTION)
    if len(grep_checks) != 1:
        _fail("expected exactly 1 check from the bare-grep Acceptance "
              f"section, got {len(grep_checks)}: {grep_checks!r}")
    grep_item = grep_checks[0]
    if grep_item.get("type") != "judgment":
        _fail("expected a bare `grep` check with no `bash -c` wrapper to "
              f"classify as judgment, got {grep_item!r}")
    if grep_item.get("reason") != "unmapped-interpreter":
        _fail("expected the bare `grep` check to carry "
              "reason == 'unmapped-interpreter' (issue #3059) -- "
              f"got {grep_item!r}")

    prose_checks = check_runner.parse_checks(PROSE_SECTION)
    if len(prose_checks) != 1:
        _fail("expected exactly 1 check from the prose Acceptance "
              f"section, got {len(prose_checks)}: {prose_checks!r}")
    prose_item = prose_checks[0]
    if prose_item.get("type") != "judgment":
        _fail(f"expected a genuinely prose check to classify as "
              f"judgment, got {prose_item!r}")
    if "reason" in prose_item:
        _fail("a genuinely prose check must not carry a 'reason' key at "
              f"all -- got {prose_item!r}. The fix must not start "
              "labelling prose as an unmapped interpreter.")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
