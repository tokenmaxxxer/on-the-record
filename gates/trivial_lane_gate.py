#!/usr/bin/env python3
"""issue #1492 — trivial-lane machine-checked triviality gate.

Per docs/issue-1492/proposals/2026-08-15-trivial-lane-machine-gate.md
(approved), this module classifies a delivered diff into one of three
positive shape classes that license skipping the phase-1 proposal step
— never by a self-declared/prose label. `classify()` mirrors
`skip_eligibility.py`'s pure-data, I/O-free entry point (`classify_rows`)
and returns a `(class_name | None, reason)` pair, the same
return-a-reason-or-None shape `skip_eligibility.hard_to_revert_hit()`
uses, so a PR-time caller can report the violated clause on rejection.

Fail-closed default: `classify()` returns `(None, reason)` unless a
specific class positively matches — absence of a red flag is never
itself a match.

  python3 gates/trivial_lane_gate.py <pr-number> [--repo <path>]
  exit 0 (lane class matched, PR authored on/after effective_after)
  exit 1 (no class matched, or PR authored before effective_after)
"""
from __future__ import annotations
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Non-docs lines changed under this count, with zero non-docs lines
# outside docs/, still counts as docs-only (matches skip_eligibility's
# NON_DOCS_LINE_THRESHOLD precedent shape, tuned separately here since
# this gate answers a different question).
DOCS_LINE_THRESHOLD = 100

TEST_PATH_RE = re.compile(r"(^|/)test_[^/]+\.py$|(^|/)[^/]+_test\.py$")
DOCS_PATH_RE = re.compile(r"^docs/")

# This module's own landing date — the retroactivity cutoff (#362).
# Set to the date this gate lands; a PR authored before this date is
# never subject to the trivial lane, regardless of diff shape.
EFFECTIVE_AFTER = date(2026, 8, 15)


def is_rename_only(rows: list[tuple[int, int, str]]) -> tuple[bool, str]:
    """Class 1 — every changed path has zero added and zero removed
    lines (a pure rename with no content change, the shape git reports
    for a detected rename with `--numstat -M` when content is
    unchanged)."""
    if not rows:
        return False, "no changed paths — nothing to classify as a rename"
    non_zero = [path for a, r, path in rows if a != 0 or r != 0]
    if non_zero:
        return False, (
            f"rename-only requires zero added/removed lines on every "
            f"path; {non_zero[0]} has content changes"
        )
    return True, "all changed paths show zero added/removed lines"


def is_docs_only(rows: list[tuple[int, int, str]]) -> tuple[bool, str]:
    """Class 2 — every changed path is under docs/, and total changed
    lines (added+removed) stay under DOCS_LINE_THRESHOLD."""
    if not rows:
        return False, "no changed paths — nothing to classify as docs-only"
    non_docs = [path for _, _, path in rows if not DOCS_PATH_RE.match(path)]
    if non_docs:
        return False, (
            f"docs-only requires every changed path under docs/; "
            f"{non_docs[0]} is outside docs/"
        )
    total = sum(a + r for a, r, _ in rows)
    if total >= DOCS_LINE_THRESHOLD:
        return False, (
            f"docs-only requires total changed lines under "
            f"{DOCS_LINE_THRESHOLD}; got {total}"
        )
    return True, (
        f"all changed paths under docs/, {total} total changed lines "
        f"< {DOCS_LINE_THRESHOLD}"
    )


def is_test_name_only(rows: list[tuple[int, int, str]],
                       deleted: set[str]) -> tuple[bool, str]:
    """Class 3 — every changed path matches a test-file naming
    pattern, no path is deleted, and total changed lines stay under
    DOCS_LINE_THRESHOLD (a proxy bound: `--numstat` carries no line
    content, so this predicate cannot itself distinguish an
    identifier/string-only edit from an assertion/control-flow edit —
    it is scoped to test-named paths with a small line budget, and any
    diff exceeding that budget or touching a non-test path falls
    through to `None`, the fail-closed default)."""
    if not rows:
        return False, "no changed paths — nothing to classify as test-name-only"
    if deleted:
        return False, (
            f"test-name-only requires no deletions; {sorted(deleted)[0]} "
            f"is deleted"
        )
    non_test = [path for _, _, path in rows if not TEST_PATH_RE.search(path)]
    if non_test:
        return False, (
            f"test-name-only requires every changed path to match a "
            f"test-file pattern; {non_test[0]} does not"
        )
    total = sum(a + r for a, r, _ in rows)
    if total >= DOCS_LINE_THRESHOLD:
        return False, (
            f"test-name-only requires total changed lines under "
            f"{DOCS_LINE_THRESHOLD}; got {total}"
        )
    return True, (
        f"all changed paths match a test-file pattern, {total} total "
        f"changed lines < {DOCS_LINE_THRESHOLD}, no deletions"
    )


def classify(rows: list[tuple[int, int, str]], changed_paths: list[str],
             deleted_paths: set[str]) -> tuple[str | None, str]:
    """Pure-data classification (no I/O) — the phase-2 test entry point.

    `changed_paths` is accepted per the proposal's frozen signature but
    is redundant with the paths already carried in `rows`; it is not
    read here since every predicate above already draws its paths from
    `rows`.
    """
    ok, reason = is_rename_only(rows)
    if ok:
        return "rename-only", reason
    ok, reason = is_docs_only(rows)
    if ok:
        return "docs-only", reason
    ok, reason = is_test_name_only(rows, deleted_paths)
    if ok:
        return "test-name-only", reason
    return None, (
        "no trivial-lane class matched (checked rename-only, docs-only, "
        "test-name-only) — diff requires the full pipeline"
    )


def _numstat(root: Path, base: str, ref: str) -> list[tuple[int, int, str]]:
    p = subprocess.run(
        ["git", "-C", str(root), "diff", "--numstat", "-M", f"{base}...{ref}"],
        capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        return []
    rows = []
    for line in p.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, r, path = parts[0], parts[1], parts[2]
        added = int(a) if a.isdigit() else 0
        removed = int(r) if r.isdigit() else 0
        rows.append((added, removed, path))
    return rows


def _deleted_paths(root: Path, base: str, ref: str) -> set[str]:
    p = subprocess.run(
        ["git", "-C", str(root), "diff", "--diff-filter=D", "--name-only",
         f"{base}...{ref}"],
        capture_output=True, text=True)
    if p.returncode != 0:
        return set()
    return {line for line in p.stdout.strip().splitlines() if line}


def _pr_authored_date(repo: str, pr_number: int) -> date | None:
    p = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo,
         "--json", "createdAt", "-q", ".createdAt"],
        capture_output=True, text=True)
    if p.returncode != 0 or not p.stdout.strip():
        return None
    ts = p.stdout.strip()
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).date()


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    if not argv:
        print("usage: trivial_lane_gate.py <pr-number> [--repo <path>]",
              file=sys.stderr)
        return 1
    pr_number = int(argv[0])
    repo = ROOT
    if "--repo" in argv:
        repo = Path(argv[argv.index("--repo") + 1])

    base_ref = f"origin/main"
    head_ref = f"pull/{pr_number}/head"
    rows = _numstat(repo, base_ref, head_ref)
    deleted = _deleted_paths(repo, base_ref, head_ref)
    changed_paths = [path for _, _, path in rows]

    lane_class, reason = classify(rows, changed_paths, deleted)
    if lane_class is None:
        print(f"trivial_lane_gate: refused — {reason}", file=sys.stderr)
        return 1

    authored = _pr_authored_date(str(repo), pr_number)
    if authored is not None and authored < EFFECTIVE_AFTER:
        print(
            f"trivial_lane_gate: refused — PR authored {authored} is "
            f"before effective_after {EFFECTIVE_AFTER} (#362 "
            f"retroactivity clause); matched class {lane_class!r} does "
            f"not apply retroactively",
            file=sys.stderr,
        )
        return 1

    print(lane_class)
    return 0


if __name__ == "__main__":
    sys.exit(main())
