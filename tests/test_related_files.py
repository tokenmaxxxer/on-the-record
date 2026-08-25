"""Tests for scripts/related_files.py — issue #2409's single-lookup file
map, replacing N ad-hoc grep/find calls a role session runs to locate the
files a task touches.

Run: python3 -m pytest tests/test_related_files.py -q
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import related_files as rf  # noqa: E402


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    return repo


def _commit_all(repo: Path, msg: str = "c") -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=repo, check=True)


def test_docs_tree_lists_only_the_issues_own_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "issue-42" / "reports").mkdir(parents=True)
    (repo / "docs" / "issue-42" / "reports" / "implementation.md").write_text("x")
    (repo / "docs" / "issue-43" / "reports").mkdir(parents=True)
    (repo / "docs" / "issue-43" / "reports" / "implementation.md").write_text("x")
    _commit_all(repo)
    tree = rf.docs_tree(42, repo)
    assert tree == ["docs/issue-42/reports/implementation.md"]


def test_docs_tree_empty_state_no_issue_directory(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "README.md").write_text("x")
    _commit_all(repo)
    assert rf.docs_tree(999, repo) == []


def test_issue_mentions_finds_all_three_phrasings_excludes_own_docs_tree(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "issue-42" / "reports").mkdir(parents=True)
    (repo / "docs" / "issue-42" / "reports" / "implementation.md").write_text(
        "mentions issue-42 itself\n")
    (repo / "a.py").write_text("# fixed in issue-42\n")
    (repo / "b.py").write_text("# see issue #42 for context\n")
    (repo / "c.py").write_text("# closes #42\n")
    (repo / "d.py").write_text("# unrelated file\n")
    _commit_all(repo)
    mentions = rf.issue_mentions(42, repo)
    assert mentions == ["a.py", "b.py", "c.py"]


def test_issue_mentions_does_not_false_positive_on_prefix_number(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("# issue-421 is unrelated\n")
    _commit_all(repo)
    assert rf.issue_mentions(42, repo) == []


def test_keyword_hits_case_insensitive(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.py").write_text("def Frobnicate():\n    pass\n")
    (repo / "b.py").write_text("nothing here\n")
    _commit_all(repo)
    hits = rf.keyword_hits(["frobnicate"], repo)
    assert hits == {"frobnicate": ["a.py"]}


def test_build_manifest_shape(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "docs" / "issue-7" / "reports").mkdir(parents=True)
    (repo / "docs" / "issue-7" / "reports" / "implementation.md").write_text("x")
    _commit_all(repo)
    manifest = rf.build_manifest(7, ["nope"], repo)
    assert manifest["issue"] == 7
    assert manifest["docs_tree"] == ["docs/issue-7/reports/implementation.md"]
    assert manifest["keyword_hits"] == {"nope": []}


def test_format_manifest_reports_none_for_empty_sections():
    manifest = {"issue": 7, "docs_tree": [], "issue_mentions": [], "keyword_hits": {}}
    text = rf.format_manifest(manifest)
    assert "(none)" in text
    assert "docs/issue-7/" in text


def test_cli_rejects_non_numeric_issue(capsys):
    rc = rf.main(["not-a-number"])
    assert rc == 1
    assert "must be a bare number" in capsys.readouterr().err
