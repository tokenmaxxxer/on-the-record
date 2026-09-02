#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3050.

Demonstrates the supersession shape (`supersession.py`) against a
synthetic tree modeled on the issue's own live repro: a correcting
session cannot write into the record it corrects (board-gate.sh's
write-set isolation resolves ownership from the writing session's own
project root, not the path being written -- no write shape reaches the
original), so the correction lands as its own record instead, marked with
a `supersedes:` frontmatter field pointing at what it replaces.

This probe fails against current main: `supersession.py` does not exist
there, so the import below raises ModuleNotFoundError before any
assertion runs -- an honest failure, not a staged one.

Two artifacts, not one -- see `supersession.py`'s module docstring for why
"exactly one artifact survives" was rejected. This probe demonstrates and
asserts the two-artifact case, and states that decision in its output
(the amendment's fallback clause -- "if the chosen shape leaves exactly
one artifact, the probe asserts that instead" -- does not apply here).

Run as `python3 gates/probe_supersession_marker.py` from the repo root,
no arguments. Prints the demonstrated tree, the marker, and the resolved
verdict; exits 0 on success, non-zero with a message on stderr otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import supersession  # noqa: E402

ORIGINAL_PATH = "docs/issue-9101/reports/coding.md"
CORRECTION_PATH = "docs/issue-9101/reports/verification.md"

ORIGINAL_CONTENT = """---
issue: 9101
role: coding
loop_state: landed
---

# issue-9101 -- coding record

## What was done

Migrated the report generator; cited throughput as 4200 req/s, latency
p99 38ms, error rate 0.02%.
"""

REASON = "three of the four cited figures were fabricated, not measured"
MARKER = supersession.render_supersedes_field(ORIGINAL_PATH, REASON)

CORRECTION_CONTENT = f"""---
issue: 9101
role: verification
loop_state: landed
{MARKER}
---

# issue-9101 -- verification record

## What was done

Re-measured the report generator's own citations from source: throughput
4200 req/s (confirmed), latency p99 91ms (was cited as 38ms), error rate
0.4% (was cited as 0.02%), and a fourth figure the original omitted a
measurement basis for entirely.
"""


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    tree = {ORIGINAL_PATH: ORIGINAL_CONTENT, CORRECTION_PATH: CORRECTION_CONTENT}

    print("-- demonstrated tree (merged, no PR body / issue comments) --")
    for path in sorted(tree):
        print(f"  {path}")
    print(f"-- marker, as written in {CORRECTION_PATH}'s own frontmatter --")
    print(f"  {MARKER}")

    parsed_target = supersession.parse_supersedes(CORRECTION_CONTENT)
    if parsed_target != ORIGINAL_PATH:
        _fail(f"parse_supersedes on the correction's own content returned "
              f"{parsed_target!r}, expected {ORIGINAL_PATH!r} -- a reader "
              "of the tree could not follow the marker back to what it "
              "supersedes.")

    verdict = supersession.resolve_authoritative(tree)
    print(f"-- resolve_authoritative() verdict --\n  {verdict}")

    if verdict["authoritative"] != [CORRECTION_PATH]:
        _fail("expected exactly one authoritative artifact "
              f"({CORRECTION_PATH!r}), a reader following only the "
              f"in-tree marker; got {verdict['authoritative']!r}. Two "
              "artifacts survive in the tree (the ownership boundary "
              "forbids removing the original) but only one is "
              "authoritative -- content alone must say which.")
    if verdict["superseded"] != {ORIGINAL_PATH: CORRECTION_PATH}:
        _fail(f"expected {ORIGINAL_PATH!r} marked superseded by "
              f"{CORRECTION_PATH!r}; got {verdict['superseded']!r}")
    if verdict["conflicts"] or verdict["broken"]:
        _fail(f"demonstrated tree should have no conflicts/broken "
              f"references; got conflicts={verdict['conflicts']!r} "
              f"broken={verdict['broken']!r}")

    print("-- shape decision --")
    print("  Two artifacts, not one: the correcting session can only ever "
          "write its own record, never the one it corrects (no write "
          "shape reaches it -- issue #3050 root-cause comment). "
          "'Exactly one artifact survives' was rejected on that ground "
          "alone, before any content design question. Both files remain "
          "in the tree; the reader identifies the authoritative one from "
          f"the correction's own `supersedes:` field ({MARKER!r}), never "
          "from a PR body or issue comment.")

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
