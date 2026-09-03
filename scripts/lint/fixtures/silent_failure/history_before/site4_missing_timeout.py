"""Real pre-repair code (issue #3228 site 4), verbatim from
scripts/issue-3127/verify_preregistration.py at commit fb0bb0d3: no
subprocess call in this file passed `timeout=`. A hung `git`/`gh`
process (lock contention, a stuck network read) blocked this check
forever instead of ever reporting that it could not observe an answer.
Repaired at commit 125cef42 ("timeout every subprocess call site")."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo_root), *args],
                           capture_output=True, text=True)


def repo_owner_repo() -> "str | None":
    r = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                         "-q", ".nameWithOwner"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gh repo view failed: {r.stderr}")
    return r.stdout.strip() or None
