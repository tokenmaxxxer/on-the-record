"""Live-fire tests for heredoc-command-refusal-gate.sh (issue #1976).

  python3 on-the-record/hooks/test_heredoc_command_refusal_gate.py
"""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "on-the-record" / "hooks" / "heredoc-command-refusal-gate.sh"

_HEREDOC_COMMIT = (
    'git commit -m "$(cat <<\'EOF\'\n'
    'a title\n'
    '\n'
    'a body\n'
    'EOF\n'
    ')"'
)

_HEREDOC_PR_CREATE = (
    'gh pr create --title "t" --body "$(cat <<\'EOF\'\n'
    'a body\n'
    'EOF\n'
    ')"'
)


def _run(command: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": os.getcwd(),
        "session_id": "test-session",
    })
    env = dict(os.environ)
    env.pop("OTR_ROLE_BIND_STATE_DIR", None)
    env["CLAUDE_ROLE"] = "implementation"
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", str(SCRIPT)], input=payload,
                           capture_output=True, text=True, env=env)


def t_role_session_heredoc_commit_is_denied_with_sanctioned_alternative(tmp_path: Path):
    r = _run(_HEREDOC_COMMIT)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "-m \"<title line>\" -m \"<body line>\"" in r.stderr, repr(r.stderr)


def t_role_session_heredoc_pr_create_is_denied_with_sanctioned_alternative(tmp_path: Path):
    r = _run(_HEREDOC_PR_CREATE)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "--body-file <path>" in r.stderr, repr(r.stderr)


def t_role_session_two_flag_commit_is_untouched(tmp_path: Path):
    r = _run('git commit -m "a title" -m "a body"')
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert r.stderr == "", repr(r.stderr)


def t_role_session_body_file_pr_create_is_untouched(tmp_path: Path):
    r = _run('gh pr create --title "t" --body-file /tmp/pr-body.md')
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert r.stderr == "", repr(r.stderr)


def t_orchestrator_session_heredoc_commit_is_untouched(tmp_path: Path):
    # gh-write-allow-gate.sh already owns the orchestrator's benign quoted-
    # heredoc allow path for the gh verbs it recognizes — this gate must
    # never regress that, and git commit is an orchestrator concern outside
    # issue #1976's role-session scope.
    r = _run(_HEREDOC_COMMIT, extra_env={"CLAUDE_ROLE": ""})
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert r.stderr == "", repr(r.stderr)


def t_kill_switch_suppresses_denial(tmp_path: Path):
    r = _run(_HEREDOC_COMMIT, extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)


def t_heredoc_issue_comment_is_also_denied(tmp_path: Path):
    command = (
        'gh issue comment 12 --body "$(cat <<\'EOF\'\n'
        'a comment\n'
        'EOF\n'
        ')"'
    )
    r = _run(command)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "--body-file <path>" in r.stderr, repr(r.stderr)


if __name__ == "__main__":
    import tempfile
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            t(Path(td))
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
