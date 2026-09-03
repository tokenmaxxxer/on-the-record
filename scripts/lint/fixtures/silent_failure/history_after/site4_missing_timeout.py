"""Real repaired code (issue #3228 site 4), verbatim excerpt from the
current scripts/issue-3127/verify_preregistration.py: every subprocess
call site now passes an explicit `timeout=` and turns a real timeout
into a synthetic non-zero returncode rather than letting the caller
block forever."""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

GIT_TIMEOUT = 10
GH_TIMEOUT = 30
_TIMEOUT_RETURNCODE = 124


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    full_args = ["git", "-C", str(repo_root), *args]
    try:
        return subprocess.run(full_args, capture_output=True, text=True,
                               timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=full_args, returncode=_TIMEOUT_RETURNCODE, stdout="",
            stderr=f"timed out after {GIT_TIMEOUT}s")


def _run_gh(args: list) -> subprocess.CompletedProcess:
    full_args = ["gh", *args]
    try:
        return subprocess.run(full_args, capture_output=True, text=True,
                               timeout=GH_TIMEOUT)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=full_args, returncode=_TIMEOUT_RETURNCODE, stdout="",
            stderr=f"timed out after {GH_TIMEOUT}s")


def repo_owner_repo() -> Optional[str]:
    r = _run_gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    if r.returncode != 0:
        return None
    name = r.stdout.strip()
    return name or None
