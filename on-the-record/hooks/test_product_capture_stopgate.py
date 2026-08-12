"""Tests for product-capture-stopgate.sh (issue #566, carrying architecture's design)."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "product-capture-stopgate.sh"


def _git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def _init_repo(repo, branch="issue-123/product-capture"):
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("init\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "checkout", "-q", "-B", branch)


def _write_transcript(repo, user_texts):
    transcript = repo / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as fh:
        for text in user_texts:
            fh.write(json.dumps({
                "type": "user",
                "message": {"role": "user", "content": text},
            }) + "\n")
        fh.write(json.dumps({
            "type": "user",
            "message": {"role": "user", "content": [
                {"type": "tool_result", "content": "not authored text"}
            ]},
        }) + "\n")
    return transcript


def _run(repo, transcript, role=None, orchestrate_off=""):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    payload = json.dumps({"transcript_path": str(transcript)})
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
        cwd=str(repo),
    )


def t_no_flagged_sentence_is_silent():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, ["read this file please", "run the tests"])
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_flagged_requirement_with_no_doc_change_gets_additional_context():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "requirements.md" in ctx


def t_bootstrap_creates_missing_file_on_first_flag():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        doc = repo / "docs" / "issue-123" / "product" / "requirements.md"
        assert not doc.exists()
        _run(repo, transcript)
        assert doc.exists()
        assert "Requirements" in doc.read_text()


def t_flagged_requirement_with_matching_doc_diff_is_silent():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        doc_dir = repo / "docs" / "issue-123" / "product"
        doc_dir.mkdir(parents=True)
        doc = doc_dir / "requirements.md"
        doc.write_text("# Requirements\n\nAppend-only, newest entry last.\n")
        doc.write_text(doc.read_text() + "- offline mode support\n")
        _git(repo, "add", "docs/issue-123/product/requirements.md")
        _git(repo, "commit", "-q", "-m", "record requirement")
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_claude_role_set_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r = _run(repo, transcript, role="qa")
        assert r.returncode == 0
        assert r.stdout == ""


def t_orchestrate_off_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r = _run(repo, transcript, orchestrate_off="1")
        assert r.returncode == 0
        assert r.stdout == ""


def t_off_issue_branch_falls_back_to_repo_root_doc_path():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo, branch="main")
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        doc = repo / "docs" / "product" / "requirements.md"
        assert not doc.exists()
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "docs/product/" in ctx
        assert "docs/issue-" not in ctx
        assert doc.exists()
        assert "Requirements" in doc.read_text()


def t_off_issue_branch_empty_state_is_silent():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo, branch="main")
        transcript = _write_transcript(repo, ["read this file please", "run the tests"])
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""
        assert not (repo / "docs").exists()


def t_missing_transcript_path_fails_closed_silently():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        env = dict(os.environ)
        env["ORCHESTRATE_OFF"] = ""
        env.pop("CLAUDE_ROLE", None)
        r = subprocess.run(
            ["bash", str(HOOK)],
            input=json.dumps({"transcript_path": str(repo / "does-not-exist.jsonl")}),
            capture_output=True, text=True, env=env, timeout=20, cwd=str(repo),
        )
        assert r.returncode in (0, 2)
        assert r.stdout == ""
