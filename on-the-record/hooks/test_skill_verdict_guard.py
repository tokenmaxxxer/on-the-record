"""Tests for skill-verdict-guard.sh (issue #2039's per-mounted-skill
verdict obligation)."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK = HOOKS_DIR / "skill-verdict-guard.sh"
GATES_DIR = HOOKS_DIR.parent.parent / "gates"


def _git(repo, *args):
    subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )


def _init_repo(repo, branch="issue-2039/implementation"):
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("init\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "checkout", "-q", "-B", branch)


def _write_transcript(repo, first_user_text):
    transcript = repo / "transcript.jsonl"
    with transcript.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "type": "user",
            "message": {"role": "user", "content": first_user_text},
        }) + "\n")
        fh.write(json.dumps({
            "type": "assistant",
            "message": {"role": "assistant", "content": "did the work."},
        }) + "\n")
    return transcript


def _run(repo, transcript, orchestrate_off="", stop_hook_active=False):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = orchestrate_off
    payload = json.dumps({
        "transcript_path": str(transcript),
        "stop_hook_active": stop_hook_active,
    })
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
        cwd=str(repo),
    )


_MOUNTED_LINE = (
    "마운트된 스킬(--skills, 이슈 #1742/#1774): "
    "implementation-blueprint (Use whenever...) (trigger match)\n"
)

_ROLE_MAPPED_LINE = (
    "이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: "
    "스킬 implementation-blueprint, code-architecture "
    "(skill-repository abc1234) 가이던스만 붙는다 — 집행은 core 훅뿐이다.\n"
)


def _write_record(repo, body, role="implementation"):
    d = repo / "docs" / "issue-2039" / "reports"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{role}.md"
    p.write_text(body)
    return p


def t_zero_mounted_skills_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, "no skill lines here, just the task.")
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_missing_skill_verdict_line_is_blocked():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(repo, "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "implementation-blueprint" in ctx


def t_empty_reason_skill_verdict_line_is_blocked():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(
            repo,
            "---\nloop_state: landed\n---\n\n"
            "skill-verdict: implementation-blueprint —\n\n"
            "## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        assert "implementation-blueprint" in ctx


def t_both_assembly_points_union_without_double_count():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE + "\n" + _ROLE_MAPPED_LINE)
        _write_record(
            repo,
            "---\nloop_state: landed\n---\n\n"
            "skill-verdict: implementation-blueprint — applied: used it.\n"
            "skill-verdict: code-architecture — not-applicable: n/a.\n\n"
            "## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_satisfied_skill_verdicts_pass():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(
            repo,
            "---\nloop_state: landed\n---\n\n"
            "skill-verdict: implementation-blueprint — applied: used it at spawn.py:8181.\n\n"
            "## What did not work\nNone.\n")
        r = _run(repo, transcript)
        assert r.returncode == 0
        assert r.stdout == ""


def t_stop_hook_active_emits_nothing():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(repo, "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n")
        r = _run(repo, transcript, stop_hook_active=True)
        assert r.returncode == 0
        assert r.stdout == ""


def t_malformed_payload_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        r = subprocess.run(
            ["bash", str(HOOK)],
            input="not json", capture_output=True, text=True,
            env=dict(os.environ, ORCHESTRATE_OFF=""), timeout=20, cwd=str(repo),
        )
        assert r.returncode == 2
        assert r.stdout == ""


def t_orchestrate_off_is_noop():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        transcript = _write_transcript(repo, _MOUNTED_LINE)
        _write_record(repo, "---\nloop_state: landed\n---\n\n## What did not work\nNone.\n")
        r = _run(repo, transcript, orchestrate_off="1")
        assert r.returncode == 0
        assert r.stdout == ""
