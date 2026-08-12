"""Tests for deviation-log-guard.sh (issue #803's deviation loop)."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "deviation-log-guard.sh"


def _git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def _init_repo(repo, branch="issue-803/implementation"):
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("init\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "checkout", "-q", "-B", branch)


def _write_transcript(repo, assistant_texts):
    transcript = repo / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as fh:
        for text in assistant_texts:
            fh.write(json.dumps({
                "type": "assistant",
                "message": {"role": "assistant", "content": text},
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


def t_no_marker_is_silent():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, ["ran the tests, all green."])
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_traceless_deviation_is_blocked():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["this is a deviation, classifying as inline-fix now."]
        )
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "deviation-log.md" in ctx


def t_logged_deviation_passes():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        log_dir = repo / "docs" / "issue-803" / "reports"
        log_dir.mkdir(parents=True)
        log = log_dir / "deviation-log.md"
        log.write_text("# Deviation log\n\n- 2026-08-12 inline-fix: swapped helper.\n")
        _git(repo, "add", "docs/issue-803/reports/deviation-log.md")
        _git(repo, "commit", "-q", "-m", "record deviation")
        transcript = _write_transcript(
            repo, ["this is a deviation, classifying as inline-fix now."]
        )
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_claude_role_set_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["this is a deviation, classifying as inline-fix now."]
        )
        r = _run(repo, transcript, role="qa")
        assert r.returncode == 0
        assert r.stdout == ""


def t_orchestrate_off_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(
            repo, ["this is a deviation, classifying as inline-fix now."]
        )
        r = _run(repo, transcript, orchestrate_off="1")
        assert r.returncode == 0
        assert r.stdout == ""


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


def t_off_issue_branch_uses_docs_reports_path():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo, branch="main")
        transcript = _write_transcript(
            repo, ["this is a deviation, classifying as inline-fix now."]
        )
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "docs/reports/deviation-log.md" in ctx
