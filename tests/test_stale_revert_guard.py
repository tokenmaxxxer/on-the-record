#!/usr/bin/env python3
"""issue-1664 (northpole req#6) — `stale_revert_guard` 단위/라이브 테스트.

  python3 -m pytest tests/test_stale_revert_guard.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import stale_revert_guard as srg  # noqa: E402


def _run(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo, "init", "-q", "-b", "main")
    _run(repo, "config", "user.email", "test@example.com")
    _run(repo, "config", "user.name", "Test")
    return repo


def _commit(repo: Path, path: str, content: str, msg: str) -> str:
    (repo / path).write_text(content)
    _run(repo, "add", path)
    _run(repo, "commit", "-q", "-m", msg)
    return _run(repo, "rev-parse", "HEAD").strip()


# ---- unit tests over classify() directly (pure, no network) ----

def test_refuse_stale_merge_base_and_reverted_lines_overlap_conflict():
    merge_base = "line1\nline2\nline3\n"
    base_head = "line1\nFIX\nline2\nline3\n"      # C added FIX
    head = "line1\nOLDLINE2\nline3\n"              # head overlaps that region, lacks FIX
    verdict = srg.classify(base_head, merge_base, head, path="f.txt")
    assert verdict["verdict"] == srg.REFUSE
    assert "f.txt" in verdict["reason"]


def test_allow_merge_base_includes_the_later_commit():
    merge_base = "line1\nFIX\nline2\nline3\n"
    base_head = "line1\nFIX\nline2\nline3\n"
    head = "line1\nFIX\nline2\nline3\nEXTRA\n"
    verdict = srg.classify(base_head, merge_base, head, path="f.txt")
    assert verdict["verdict"] == srg.ALLOW


def test_allow_intentional_removal_with_up_to_date_merge_base():
    merge_base = "line1\nFIX\nline2\nline3\n"
    base_head = "line1\nFIX\nline2\nline3\n"
    head = "line1\nline2\nline3\n"  # deliberately removes FIX, merge-base already had it
    verdict = srg.classify(base_head, merge_base, head, path="f.txt")
    assert verdict["verdict"] == srg.ALLOW


def test_allow_byte_identical_merge_base_equals_base_head():
    content = "line1\nline2\n"
    verdict = srg.classify(content, content, "anything else entirely\n", path="f.txt")
    assert verdict["verdict"] == srg.ALLOW


def test_allow_adversarial_no_overlapping_hunks_merges_cleanly():
    """독립 리뷰가 요구한 binding condition: stale 브랜치가 base 도 같이
    자란 파일을 겹치지 않는 hunk 로 co-edit 하면 git 3-way 병합이 깨끗이
    합쳐지고 REFUSE 되면 안 된다."""
    merge_base = "line1\nline2\nline3\nline4\nline5\n"
    base_head = "line1\nline2\nFIX\nline3\nline4\nline5\n"        # base grew: FIX inserted
    head = "line1\nline2\nline3\nline4\nline5\nHEAD_APPEND\n"      # head grew elsewhere, no overlap
    verdict = srg.classify(base_head, merge_base, head, path="f.txt")
    assert verdict["verdict"] == srg.ALLOW, verdict["reason"]


# ---- live: reconstruct the PR #1662 vs #1661 shape in a fixture repo ----

def test_live_stale_branch_refused_then_allowed_after_rebase(tmp_path):
    repo = _init_repo(tmp_path)
    _commit(repo, "app.py", "def handler():\n    return old_value()\n", "init")

    _run(repo, "branch", "pr-branch")  # merge-base for the PR

    # base HEAD gets the security fix (commit C) after the PR's merge-base
    _commit(repo, "app.py",
            "def handler():\n    validate(request)\n    return old_value()\n",
            "security fix: validate before use")

    # stale PR branch, cut before C, makes an overlapping edit that lacks the fix
    _run(repo, "checkout", "-q", "pr-branch")
    _commit(repo, "app.py", "def handler():\n    return new_value()\n",
            "unrelated feature change")
    stale_head = _run(repo, "rev-parse", "HEAD").strip()
    _run(repo, "checkout", "-q", "main")

    mb = _run(repo, "merge-base", "main", stale_head).strip()
    refusals = srg.check_pr(repo, "main", mb, stale_head)
    assert refusals, "stale branch reverting the just-added fix must be REFUSED"
    assert any("app.py" in r["reason"] for r in refusals)

    # rebase the same branch onto base HEAD -- the feature change replayed on
    # top of the fix, preserving both -- should now pass
    _run(repo, "checkout", "-q", "-b", "pr-branch-rebased", "main")
    _commit(repo, "app.py",
            "def handler():\n    validate(request)\n    return new_value()\n",
            "unrelated feature change (rebased)")
    rebased_head = _run(repo, "rev-parse", "HEAD").strip()
    mb2 = _run(repo, "merge-base", "main", rebased_head).strip()
    assert mb2 == _run(repo, "rev-parse", "main").strip()
    refusals2 = srg.check_pr(repo, "main", mb2, rebased_head)
    assert refusals2 == []
