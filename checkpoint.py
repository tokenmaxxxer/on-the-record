"""Harness-decided checkpointing for session workspaces (issue #2215).

Pure workspace-path functions — unlike watchdog.py/roster.py/lifecycle.py
(extractions from spawn.py that resolve cross-module references through the
`_sp` compat shim), this module has no dependency on spawn's own mutable
state. It is imported bare (`import checkpoint`) by any module that needs
it, the same way gates/board_read.py is imported directly rather than
routed through `_sp`.

Design, from the issue #2215 survey: closest to dura's polling model — a
harness-decided tick commits a snapshot of the workspace to a private ref
under `refs/checkpoints/<branch>`, touching neither HEAD, the current
branch, nor the index. Tracked changes come from `git stash create` (which
builds a commit object without side effects on the worktree/index/stash
list — that is `create`, not `push`/`save`). Untracked files are folded in
separately through a throwaway `GIT_INDEX_FILE`, so the real index is never
staged into, then combined as a second commit parent — the same shape the
issue's Cline survey note describes ("stash create plus a synthesized
third-parent commit to capture untracked files"; here it is a second
parent because there is at most one of {stash, untracked-tree} missing at a
time).
"""
from __future__ import annotations
import os
import subprocess
import tempfile
import time

CHECKPOINT_REF_NS = "refs/checkpoints"


def _git(work: str, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(work), *args],
                           capture_output=True, text=True, env=env)


def _checkpoint_ref(work: str, ref_ns: str = CHECKPOINT_REF_NS) -> str | None:
    branch = _git(work, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if not branch or branch == "HEAD":
        return None  # detached HEAD — no stable branch name to key the ref on
    return f"{ref_ns}/{branch}"


def checkpoint_workspace(work: str, ref_ns: str = CHECKPOINT_REF_NS) -> dict:
    """Snapshot every dirty file in `work` (tracked + untracked) onto a
    private ref. Returns `{"ref": str|None, "commit": sha|None,
    "dirty_files": int}`; `ref`/`commit` are None on a clean tree — no ref
    is created for an empty checkpoint (issue #2215 empty-state contract)."""
    status = _git(work, "status", "--porcelain")
    if status.returncode != 0:
        return {"ref": None, "commit": None, "dirty_files": 0}
    dirty_files = len([line for line in status.stdout.splitlines() if line.strip()])
    if dirty_files == 0:
        return {"ref": None, "commit": None, "dirty_files": 0}

    ref = _checkpoint_ref(work, ref_ns)
    if ref is None:
        return {"ref": None, "commit": None, "dirty_files": dirty_files}

    head = _git(work, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {"ref": None, "commit": None, "dirty_files": dirty_files}
    head_sha = head.stdout.strip()

    stash = _git(work, "stash", "create")
    stash_sha = stash.stdout.strip() or None
    commit_sha = stash_sha

    with tempfile.TemporaryDirectory() as tmp:
        tmp_index = os.path.join(tmp, "checkpoint-index")
        env = {**os.environ, "GIT_INDEX_FILE": tmp_index}
        # Base the throwaway index on the stash's tree (tracked changes),
        # not HEAD's — otherwise adding untracked files on top of HEAD's
        # tree would silently drop the tracked modifications.
        base_tree = f"{stash_sha}^{{tree}}" if stash_sha else head_sha
        _git(work, "read-tree", base_tree, env=env)
        untracked = _git(work, "ls-files", "--others", "--exclude-standard", env=env)
        untracked_files = [f for f in untracked.stdout.splitlines() if f]
        if untracked_files:
            _git(work, "add", "--", *untracked_files, env=env)
            tree = _git(work, "write-tree", env=env).stdout.strip()
            if tree:
                parents = [p for p in (head_sha, stash_sha) if p]
                parent_args = [a for p in parents for a in ("-p", p)]
                commit = subprocess.run(
                    ["git", "-C", str(work), "commit-tree", tree, *parent_args,
                     "-m", f"checkpoint: {dirty_files} dirty file(s)"],
                    capture_output=True, text=True, env=env)
                if commit.stdout.strip():
                    commit_sha = commit.stdout.strip()

    if not commit_sha:
        return {"ref": None, "commit": None, "dirty_files": dirty_files}
    updated = _git(work, "update-ref", ref, commit_sha)
    if updated.returncode != 0:
        return {"ref": None, "commit": None, "dirty_files": dirty_files}
    return {"ref": ref, "commit": commit_sha, "dirty_files": dirty_files}


def checkpoint_health(work: str, ref_ns: str = CHECKPOINT_REF_NS,
                       now: float | None = None) -> dict:
    """The two fields `diagnose_health()` surfaces per workspace (issue
    #2215): the current dirty-file count (raw `git status --porcelain`,
    independent of whether a checkpoint has fired yet) and minutes since the
    last checkpoint commit, or None when no checkpoint ref exists for this
    branch yet."""
    now = time.time() if now is None else now
    status = _git(work, "status", "--porcelain")
    dirty_files = (len([line for line in status.stdout.splitlines() if line.strip()])
                   if status.returncode == 0 else 0)
    ref = _checkpoint_ref(work, ref_ns)
    minutes_since_checkpoint = None
    if ref is not None:
        committed = _git(work, "log", "-1", "--format=%ct", ref)
        if committed.returncode == 0 and committed.stdout.strip():
            try:
                commit_ts = int(committed.stdout.strip())
                minutes_since_checkpoint = max(0.0, (now - commit_ts) / 60.0)
            except ValueError:
                pass
    return {"dirty_files": dirty_files, "minutes_since_checkpoint": minutes_since_checkpoint}


def cleanup_checkpoint_ref(work: str, ref_ns: str = CHECKPOINT_REF_NS) -> bool:
    """issue #2215 acceptance: checkpoint refs must not survive past session
    end, and must never leak into a push/PR — `update-ref -d` only removes
    the ref pointer, so this cannot touch HEAD, the branch, or the index.
    Returns True whether it deleted a ref or found nothing to delete."""
    ref = _checkpoint_ref(work, ref_ns)
    if ref is None:
        return True
    exists = _git(work, "show-ref", "--verify", "--quiet", ref)
    if exists.returncode != 0:
        return True
    deleted = _git(work, "update-ref", "-d", ref)
    return deleted.returncode == 0
