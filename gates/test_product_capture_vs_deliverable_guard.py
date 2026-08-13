"""Acceptance test for issue #1118: product-capture-stopgate.sh vs
deliverable-guard.sh, composing both real hook scripts (subprocess),
per the issue's four named scenarios.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
STOPGATE = HOOKS_DIR / "product-capture-stopgate.sh"
GUARD = HOOKS_DIR / "deliverable-guard.sh"


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


def _write_transcript(repo, user_texts, name="transcript.jsonl"):
    transcript = repo / name
    with transcript.open("w", encoding="utf-8") as fh:
        for text in user_texts:
            fh.write(json.dumps({
                "type": "user",
                "message": {"role": "user", "content": text},
            }) + "\n")
    return transcript


def _run_stopgate(repo, transcript, session_id=None, state_dir=None, role=None):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    if role:
        env["CLAUDE_ROLE"] = role
    else:
        env.pop("CLAUDE_ROLE", None)
    if state_dir is not None:
        env["OTR_PRODUCT_CAPTURE_STATE_DIR"] = str(state_dir)
    payload = {"transcript_path": str(transcript)}
    if session_id is not None:
        payload["session_id"] = session_id
    return subprocess.run(
        ["bash", str(STOPGATE)],
        input=json.dumps(payload), capture_output=True, text=True, env=env,
        timeout=20, cwd=str(repo),
    )


def _run_guard(repo, file_path):
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
        "cwd": str(repo),
    }
    return subprocess.run(
        ["bash", str(GUARD)],
        input=json.dumps(payload), capture_output=True, text=True, env=env,
        timeout=20, cwd=str(repo),
    )


def t_capture_write_path_permitted_end_to_end():
    # (a) regression guard for the already-landed #1111 fix: neither
    # hook's logic denies the capture write path.
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        for rel in (
            "docs/reports/product/requirements.md",
            "docs/issue-123/reports/product/requirements.md",
        ):
            r = _run_guard(repo, str(repo / rel))
            assert r.returncode == 0, r.stderr


def t_injected_directive_only_transcript_does_not_flag():
    # (b) Fix 2: category-matching text that sits only inside an injected
    # wrapper block must not flag.
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        injected = (
            "<system-reminder>우선순위는 아래 순서대로 — the project must "
            "support offline mode.</system-reminder>"
        )
        transcript = _write_transcript(repo, [injected, "read this file please"])
        r = _run_stopgate(repo, transcript, session_id="sess-1118-b")
        assert r.returncode == 0
        assert r.stdout == ""


def t_undischargeable_flag_does_not_repeat_on_consecutive_stops():
    # (c) Fix 3: two consecutive invocations, same session_id, unchanged
    # transcript/doc state -> flag on first call, suppressed on second.
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        state_dir = repo / "state"
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r1 = _run_stopgate(
            repo, transcript, session_id="sess-1118-c", state_dir=state_dir
        )
        assert r1.returncode == 0
        out1 = json.loads(r1.stdout)
        assert "requirements.md" in out1["hookSpecificOutput"]["additionalContext"]

        r2 = _run_stopgate(
            repo, transcript, session_id="sess-1118-c", state_dir=state_dir
        )
        assert r2.returncode == 0
        assert r2.stdout == ""


def t_empty_state_bootstrap_still_works():
    # (d) regression guard for #566's bootstrap-on-first-flag: no
    # docs/product/ directory at all -> still bootstraps and flags.
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _init_repo(repo)
        assert not (repo / "docs").exists()
        transcript = _write_transcript(
            repo, ["the project must support offline mode."]
        )
        r = _run_stopgate(repo, transcript, session_id="sess-1118-d")
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "requirements.md" in out["hookSpecificOutput"]["additionalContext"]
        doc = repo / "docs" / "issue-123" / "reports" / "product" / "requirements.md"
        assert doc.exists()
        assert "Requirements" in doc.read_text()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        else:
            print(f"PASS {t.__name__}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
