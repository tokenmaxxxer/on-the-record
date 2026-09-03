"""Real pre-repair code (issue #3228 site 3), verbatim from
scripts/issue-3127/verify_preregistration.py at commit fb0bb0d3, trimmed
to the one function this defect lived in. `_run_git`'s caller checks
`r.returncode != 0` -- so the branch is not *missing* -- but the branch
returns `None`, the exact value the function also returns, three lines
later, for the unrelated and legitimate case of "git succeeded and
genuinely found nothing". A failed `git log` and an empty one become the
same observation. Repaired at scripts/issue-3127/verify_preregistration.py
(commit 1245c649 redesign, then 125cef42/8205c160): the returncode branch
now raises GitCommandError instead of returning the shared sentinel.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_root), *args],
                           capture_output=True, text=True)


def _first_commit_for_path(repo_root: Path, path: str) -> "str | None":
    """Oldest commit that introduces `path`. Empty result means the path
    has no commit yet -- e.g. it exists only as an uncommitted
    working-tree file, which this check treats as "not yet registered."
    """
    r = _run_git(repo_root, "log", "--diff-filter=A", "--follow",
                 "--format=%H", "--reverse", "--", path)
    if r.returncode != 0:
        return None
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None
