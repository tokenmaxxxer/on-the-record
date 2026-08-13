"""Tests for quality-bar-gate.sh (issue #1156).

Mirrors merge-allow-gate.sh's own test harness shape: a fake `gh` on PATH
returning canned `gh pr view --json files,headRefName,author` JSON, and a
throwaway git checkout (record files + their commit authors) as the
target repo. No network.
"""
import json
import os
import stat
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
GUARD = HOOKS_DIR / "quality-bar-gate.sh"


def _run(cmd, tmp_path, pr_json, extra_env=None):
    gh_dir = tmp_path / "bin"
    gh_dir.mkdir(exist_ok=True)
    gh = gh_dir / "gh"
    gh.write_text(
        "#!/usr/bin/env bash\n"
        "if [ \"$1\" = pr ] && [ \"$2\" = view ]; then\n"
        "  cat <<'JSON'\n%s\nJSON\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n" % json.dumps(pr_json)
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)

    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": cmd},
        "cwd": str(tmp_path),
        "session_id": "test-session",
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
    env["PATH"] = str(gh_dir) + os.pathsep + env.get("PATH", "")
    env.update(extra_env or {})
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=30,
    )


def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "a@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "acct-a"], cwd=tmp_path, check=True)


def _commit_record(tmp_path, issue, role, verdict_lines, author_name):
    d = tmp_path / "docs" / f"issue-{issue}" / "reports"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{role}.md"
    p.write_text("\n".join(verdict_lines) + "\n")
    subprocess.run(["git", "add", str(p)], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", f"user.name={author_name}", "-c", "user.email=x@example.com",
         "commit", "-q", "-m", "record"],
        cwd=tmp_path, check=True,
    )


def t_no_bar_scoped_files_is_noop(tmp_path):
    _init_repo(tmp_path)
    pr_json = {
        "files": [{"path": "README.md"}],
        "headRefName": "issue-1/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 1", tmp_path, pr_json)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def t_bar_scoped_no_record_is_denied(tmp_path):
    _init_repo(tmp_path)
    pr_json = {
        "files": [{"path": "components/Widget.svelte"}],
        "headRefName": "issue-2/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 2", tmp_path, pr_json)
    assert r.returncode == 2
    out = json.loads(r.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "ux-engineering" in out["hookSpecificOutput"]["permissionDecisionReason"]


def t_bar_met_record_from_different_account_is_allowed(tmp_path):
    _init_repo(tmp_path)
    _commit_record(tmp_path, 3, "ux-engineering",
                    ["quality_bar_verdict: bar-met"], "acct-reviewer")
    pr_json = {
        "files": [{"path": "components/Widget.svelte"}],
        "headRefName": "issue-3/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 3", tmp_path, pr_json)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def t_bar_met_record_authored_by_producer_itself_is_denied(tmp_path):
    _init_repo(tmp_path)
    _commit_record(tmp_path, 4, "ux-engineering",
                    ["quality_bar_verdict: bar-met"], "acct-producer")
    pr_json = {
        "files": [{"path": "components/Widget.svelte"}],
        "headRefName": "issue-4/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 4", tmp_path, pr_json)
    assert r.returncode == 2
    out = json.loads(r.stdout)
    assert "same account" in out["hookSpecificOutput"]["permissionDecisionReason"]


def t_third_consecutive_bar_not_met_escalates(tmp_path):
    _init_repo(tmp_path)
    _commit_record(
        tmp_path, 5, "ux-engineering",
        [
            "quality_bar_verdict: bar-not-met",
            "quality_bar_verdict: bar-not-met",
            "quality_bar_verdict: bar-not-met",
        ],
        "acct-reviewer",
    )
    pr_json = {
        "files": [{"path": "components/Widget.svelte"}],
        "headRefName": "issue-5/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 5", tmp_path, pr_json)
    assert r.returncode == 2
    out = json.loads(r.stdout)
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "ESCALATE" in reason
    assert "open_decision_item" in reason


def t_orchestrate_off_kill_switch(tmp_path):
    _init_repo(tmp_path)
    pr_json = {
        "files": [{"path": "components/Widget.svelte"}],
        "headRefName": "issue-6/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 6", tmp_path, pr_json, extra_env={"ORCHESTRATE_OFF": "1"})
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def t_gh_pr_merge_with_chained_command_is_unreached():
    pass


def t_chained_command_falls_through(tmp_path):
    _init_repo(tmp_path)
    pr_json = {
        "files": [{"path": "components/Widget.svelte"}],
        "headRefName": "issue-7/ux-engineering",
        "author": {"login": "acct-producer"},
    }
    r = _run("gh pr merge 7 && rm -rf /tmp/whatever", tmp_path, pr_json)
    assert r.returncode == 0
    assert r.stdout.strip() == ""
