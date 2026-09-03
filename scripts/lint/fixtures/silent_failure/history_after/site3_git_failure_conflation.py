"""Real repaired code (issue #3228 sites 3 and 4), verbatim excerpt from
the current scripts/issue-3127/verify_preregistration.py. `_run_git` now
passes `timeout=` and turns a hung command into a synthetic returncode
instead of blocking forever (site 4); `_first_commit_for_path`'s
returncode-failure branch now raises `GitCommandError` instead of
returning the same `None` the legitimate-empty branch returns three
lines later (site 3)."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

GIT_TIMEOUT = 10
_TIMEOUT_RETURNCODE = 124


class GitCommandError(Exception):
    def __init__(self, args: tuple, returncode: int, stderr: str):
        self.args = args
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"`git {' '.join(args)}` failed (exit {returncode}): {stderr.strip()}")


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    full_args = ["git", "-C", str(repo_root), *args]
    try:
        return subprocess.run(full_args, capture_output=True, text=True,
                               timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=full_args, returncode=_TIMEOUT_RETURNCODE, stdout="",
            stderr=f"timed out after {GIT_TIMEOUT}s waiting for git {' '.join(args)}")


def _first_commit_for_path(repo_root: Path, path: str) -> Optional[str]:
    args = ("log", "--diff-filter=A", "--format=%H", "--reverse", "--", path)
    r = _run_git(repo_root, *args)
    if r.returncode != 0:
        raise GitCommandError(args, r.returncode, r.stderr)
    lines = [line for line in r.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    return lines[0]
