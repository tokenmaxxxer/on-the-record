#!/usr/bin/env python3
"""issue #3228 round 2 -- gates.silent_failure_new_findings, the diff-
scoped advisory counterpart to silent-failure-lint-guard.sh's write-time
block. Verifies the load-bearing property: a finding on a line the diff
did NOT add (pre-existing debt) is never reported, only findings on lines
the diff actually introduced -- otherwise this would flag nearly every
PR against this repo's own measured 86.7% pre-existing violation rate
(PR #3237).

Uses a real temporary git repo (subprocess git, no mocks) so
`gates.changed_files`/`_sf_added_line_numbers` exercise real `git diff`
output, not a stand-in.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import gates  # noqa: E402


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                           text=True, timeout=30, check=True)


def _make_repo() -> Path:
    tmp = tempfile.mkdtemp(prefix="otr-sf-new-findings-")
    repo = Path(tmp)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "a@b.c")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "checkout", "-q", "-b", "main")
    (repo / "a.py").write_text(
        "import subprocess\n"
        "\n"
        "def old_call():\n"
        "    subprocess.run(['echo', 'pre-existing'])\n",
        encoding="utf-8")
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(repo))
    _git(repo, "fetch", "-q", "origin")
    _git(repo, "branch", "-q", "-f", "origin/main", "main")
    return repo


def test_pre_existing_finding_on_untouched_line_is_not_reported():
    repo = _make_repo()
    # a new file added by this "PR" -- the old file's own pre-existing
    # missing-timeout call is never touched.
    (repo / "b.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "b.py")
    _git(repo, "commit", "-q", "-m", "unrelated addition")

    bad = gates.silent_failure_new_findings(repo)
    assert not any("a.py" in b for b in bad), bad


def test_new_call_on_an_added_line_is_reported():
    repo = _make_repo()
    text = (repo / "a.py").read_text(encoding="utf-8")
    (repo / "a.py").write_text(
        text + "\ndef new_call():\n    subprocess.run(['echo', 'new'])\n",
        encoding="utf-8")
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-q", "-m", "add a new bad call site")

    bad = gates.silent_failure_new_findings(repo)
    assert any("a.py" in b and "SF001" in b for b in bad), bad
    # the pre-existing call's own line must not ALSO be reported -- only
    # the newly-added one.
    assert sum(1 for b in bad if "a.py" in b and "SF001" in b) == 1, bad


def test_changed_python_file_the_lint_cannot_parse_is_reported():
    repo = _make_repo()
    (repo / "c.py").write_text("def broken(:\n", encoding="utf-8")
    _git(repo, "add", "c.py")
    _git(repo, "commit", "-q", "-m", "add a syntax-broken file")

    bad = gates.silent_failure_new_findings(repo)
    assert any("c.py" in b for b in bad), bad


def test_no_python_changes_reports_nothing():
    repo = _make_repo()
    (repo / "readme.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "readme.md")
    _git(repo, "commit", "-q", "-m", "docs only")

    assert gates.silent_failure_new_findings(repo) == []


def test_added_line_numbers_reads_multiple_hunks():
    repo = _make_repo()
    (repo / "a.py").write_text(
        "import subprocess\n"
        "\n"
        "def old_call():\n"
        "    subprocess.run(['echo', 'pre-existing'])\n"
        "\n"
        "NEW_TOP = 1\n"
        "\n"
        "def another():\n"
        "    NEW_BOTTOM = 2\n"
        "    return NEW_BOTTOM\n",
        encoding="utf-8")
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-q", "-m", "two separate hunks")

    added = gates._sf_added_line_numbers(repo, "a.py")
    assert added is not None
    text = (repo / "a.py").read_text(encoding="utf-8").splitlines()
    top_line = next(i for i, l in enumerate(text, 1) if "NEW_TOP" in l)
    bottom_line = next(i for i, l in enumerate(text, 1) if "NEW_BOTTOM = 2" in l)
    assert top_line in added
    assert bottom_line in added
    old_call_line = next(i for i, l in enumerate(text, 1) if "pre-existing" in l)
    assert old_call_line not in added
