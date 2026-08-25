#!/usr/bin/env python3
"""issue-1664 (northpole req#6) — `stale_revert_guard` 단위/라이브 테스트.
issue-2314 가 바이너리 파일(PNG) 회귀 테스트를 추가하며 `tests/`에서
`gates/`로 옮겼다 — 검사 대상 모듈 옆에 두는 게 이 저장소의 관례
(`gates/test_merge_gate.py`의 같은 이유)이고, 옮기지 않으면 두 디렉터리가
같은 베이스네임을 공유해 `gates/test_duplicate_test_basenames.py`가 잡는
충돌 모양을 스스로 만들게 된다.

  python3 -m pytest gates/test_stale_revert_guard.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
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


# ---- issue-2314: binary files must not crash the gate -------------------

def _commit_binary(repo: Path, path: str, content: bytes, msg: str) -> str:
    (repo / path).write_bytes(content)
    _run(repo, "add", path)
    _run(repo, "commit", "-q", "-m", msg)
    return _run(repo, "rev-parse", "HEAD").strip()


_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40  # NUL byte -- git's own binary-detection heuristic needs it


def test_git_show_binary_path_does_not_crash(tmp_path):
    repo = _init_repo(tmp_path)
    _commit_binary(repo, "logo.png", _PNG_BYTES, "add png")
    result = srg._git_show(repo, "HEAD", "logo.png")  # must not raise
    assert isinstance(result, str)


def test_git_show_non_utf8_but_git_sees_as_text_round_trips_by_byte(tmp_path):
    """warrant-hunt 2026-08-25 회귀: 디코드 실패시 ""로 폴백하면 git 이
    바이너리로 보지 않는(NUL 없는) 파일에 non-UTF-8 바이트 하나만 있어도
    내용 전체가 사라져 classify()가 "추가된 줄 없음"으로 오판하고 진짜
    stale revert 를 조용히 ALLOW 했다. surrogateescape 는 실패 없이 원본
    바이트를 구분 가능하게 보존해야 한다."""
    repo = _init_repo(tmp_path)
    content = b"line1\nFIX_caf\xe9_validate\nline2\n"
    _commit_binary(repo, "app.py", content, "non-utf8 byte, no NUL")
    shown = srg._git_show(repo, "HEAD", "app.py")
    assert shown != ""
    assert shown.encode("utf-8", errors="surrogateescape") == content


def test_changed_paths_excludes_binary(tmp_path):
    repo = _init_repo(tmp_path)
    base = _commit(repo, "app.py", "line1\nline2\n", "init")
    head = _commit(repo, "app.py", "line1\nline2\nline3\n", "text change")
    _commit_binary(repo, "shot.png", _PNG_BYTES, "add screenshot")
    head = _run(repo, "rev-parse", "HEAD").strip()
    paths = srg.changed_paths(repo, base, head)
    assert paths == ["app.py"], paths  # shot.png (binary) excluded, app.py (text) kept


def test_check_pr_binary_file_does_not_crash_and_still_refuses_genuine_stale_revert(tmp_path):
    """issue-2314 라이브 재현: PR 이 PNG(바이너리)와 진짜 stale revert 를
    함께 들고 오면, 예전엔 `_git_show`가 UnicodeDecodeError 로 죽었다.
    고친 뒤에는 크래시 없이 진짜 stale revert 만 REFUSE 로 잡아야 한다."""
    repo = _init_repo(tmp_path)
    _commit(repo, "app.py", "line1\nline2\nline3\n", "init")
    _run(repo, "branch", "pr-branch")

    # base HEAD grows: an unrelated screenshot, then a real fix
    _commit_binary(repo, "logo.png", _PNG_BYTES, "base grows: adds screenshot")
    _commit(repo, "app.py", "line1\nFIX\nline2\nline3\n", "security fix")

    # stale PR branch: overlapping edit that lacks FIX, plus its own screenshot
    _run(repo, "checkout", "-q", "pr-branch")
    _commit_binary(repo, "shot.png", _PNG_BYTES, "add screenshot")
    _commit(repo, "app.py", "line1\nOLDLINE2\nline3\n", "unrelated stale change")
    stale_head = _run(repo, "rev-parse", "HEAD").strip()
    _run(repo, "checkout", "-q", "main")

    mb = _run(repo, "merge-base", "main", stale_head).strip()
    refusals = srg.check_pr(repo, "main", mb, stale_head)  # must not raise
    assert refusals, "the genuine app.py stale revert must still be refused"
    assert any("app.py" in r["reason"] for r in refusals)
    assert not any("png" in r["reason"] for r in refusals)


def test_check_pr_refuses_stale_revert_of_non_utf8_line_git_does_not_treat_as_binary(tmp_path):
    """warrant-hunt 2026-08-25 회귀 재현: 수정된 줄에 non-UTF-8 바이트가
    하나 섞여 있으면(NUL 없음, git 은 바이너리로 안 봄) changed_paths()의
    바이너리 필터는 통과한다. `_git_show`가 이걸 ""로 지워버리면 진짜
    stale revert 가 조용히 ALLOW 된다 -- surrogateescape 로 고친 뒤에는
    여전히 REFUSE 되어야 한다."""
    repo = _init_repo(tmp_path)
    _commit(repo, "app.py", "line1\nline2\nline3\n", "init")
    _run(repo, "branch", "pr-branch")

    _commit_binary(repo, "app.py",
                    b"line1\nFIX_caf\xe9_validate\nline2\nline3\n",
                    "security fix (non-utf8 byte)")

    _run(repo, "checkout", "-q", "pr-branch")
    _commit(repo, "app.py", "line1\nOLDLINE2\nline3\n", "unrelated stale change")
    stale_head = _run(repo, "rev-parse", "HEAD").strip()
    _run(repo, "checkout", "-q", "main")

    mb = _run(repo, "merge-base", "main", stale_head).strip()
    numstat = _run(repo, "diff", "--numstat", f"{mb}..main")
    assert "-\t-\t" not in numstat, "fixture must stay non-binary per git, else this doesn't test the regression"

    refusals = srg.check_pr(repo, "main", mb, stale_head)
    assert refusals, "genuine stale revert of a non-UTF-8-but-non-binary line must still be REFUSEd"
    assert any("app.py" in r["reason"] for r in refusals)
