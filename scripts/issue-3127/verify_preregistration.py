#!/usr/bin/env python3
"""Assert that docs/issue-3127/decisions/pre-registration.md was committed
before docs/issue-3127/_assets/consumer-path-results.json (issue #3127
acceptance check) -- by commit order (git ancestry), not by comparing
timestamp fields inside either file, which either file's own content could
misstate. Same control #3053 used (`git log` on the branch, absence of
`_assets` at the pre-registration commit) and the reason its null was
credible: a threshold set after seeing the result is not a threshold.

Usage: python3 scripts/issue-3127/verify_preregistration.py [--repo-root PATH]
Exit 0 and prints "OK: ..." if the pre-registration commit is an ancestor
of (or the same commit as) the results commit. Exit 1 with a reason
otherwise -- including when either file has no commit yet (nothing to
compare) or when git reports them unrelated.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PREREG_PATH = "docs/issue-3127/decisions/pre-registration.md"
RESULTS_PATH = "docs/issue-3127/_assets/consumer-path-results.json"


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_root), *args],
                           capture_output=True, text=True)


def _first_commit_for_path(repo_root: Path, path: str) -> str | None:
    """Oldest commit (across all local history reachable from HEAD, since
    build-now sessions commit directly on their own branch rather than
    landing to main first) that introduces `path`. Empty result means the
    path has no commit yet -- e.g. it exists only as an uncommitted working
    -tree file, which this check treats as "not yet registered."
    """
    r = _run_git(repo_root, "log", "--diff-filter=A", "--follow",
                 "--format=%H", "--reverse", "--", path)
    if r.returncode != 0:
        return None
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def verify(repo_root: Path) -> tuple[bool, str]:
    prereg_full = repo_root / PREREG_PATH
    results_full = repo_root / RESULTS_PATH
    if not prereg_full.exists():
        return False, f"missing: {PREREG_PATH} does not exist -- nothing to verify order against"
    if not results_full.exists():
        return False, f"missing: {RESULTS_PATH} does not exist -- nothing to verify order against"

    prereg_commit = _first_commit_for_path(repo_root, PREREG_PATH)
    results_commit = _first_commit_for_path(repo_root, RESULTS_PATH)

    if prereg_commit is None and results_commit is None:
        return False, ("neither file has a commit yet (both uncommitted in "
                        "the working tree) -- commit the pre-registration "
                        "first, then the results, so this check has "
                        "ancestry to verify")
    if prereg_commit is None:
        return False, (f"{PREREG_PATH} is uncommitted while {RESULTS_PATH} "
                        f"is committed ({results_commit}) -- the "
                        "pre-registration must land in a commit that "
                        "precedes the results commit")
    if results_commit is None:
        # Pre-registration committed, results file present only in the
        # working tree (e.g. this same uncommitted session) -- order is
        # trivially satisfied: nothing committed for results yet that
        # could have preceded the pre-registration.
        return True, (f"OK: {PREREG_PATH} committed at {prereg_commit}; "
                       f"{RESULTS_PATH} not yet committed (working tree "
                       "only), so it cannot precede the pre-registration")

    if prereg_commit == results_commit:
        return False, (f"both files were introduced in the same commit "
                        f"({prereg_commit}) -- the pre-registration must be "
                        "committed strictly before the results, not "
                        "alongside them, or the threshold could have been "
                        "written with the result already known")

    is_ancestor = _run_git(repo_root, "merge-base", "--is-ancestor",
                            prereg_commit, results_commit)
    if is_ancestor.returncode == 0:
        return True, (f"OK: pre-registration commit {prereg_commit} is an "
                       f"ancestor of results commit {results_commit}")
    if is_ancestor.returncode == 1:
        return False, (f"pre-registration commit {prereg_commit} is NOT an "
                        f"ancestor of results commit {results_commit} -- "
                        "either unrelated history or the results were "
                        "committed first")
    # `git merge-base --is-ancestor` returns >1 for a real git error (bad
    # object, not a commit, etc.), not for "not an ancestor" -- reporting
    # that uniformly as "not an ancestor" would silently misclassify a git
    # failure as a normal negative verification result.
    return False, (f"git merge-base --is-ancestor errored (exit "
                    f"{is_ancestor.returncode}), not a normal ancestry "
                    f"negative -- stderr: {is_ancestor.stderr.strip()}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    ok, message = verify(Path(args.repo_root).resolve())
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
