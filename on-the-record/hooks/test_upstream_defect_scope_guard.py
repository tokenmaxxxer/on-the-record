"""Tests for upstream-defect-scope-guard.sh (issue #1131 req#4)."""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "upstream-defect-scope-guard.sh"


def _run(command):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": os.getcwd(),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def t_gh_pr_create_is_denied():
    r = _run("gh pr create --repo tokenmaxxxer/on-the-record --title x --body y")
    assert r.returncode == 2
    assert "req#4" in r.stderr


def t_gh_pr_create_with_gh_repo_env_prefix_is_denied():
    r = _run("GH_REPO=tokenmaxxxer/on-the-record gh pr create --title x --body y")
    assert r.returncode == 2


def t_gh_api_pulls_post_is_denied():
    r = _run(
        "gh api --method POST repos/tokenmaxxxer/on-the-record/pulls "
        "-f title=x -f head=y -f base=main"
    )
    assert r.returncode == 2


def t_gh_api_graphql_create_pull_request_is_denied():
    r = _run(
        "gh api graphql -f query='mutation { createPullRequest(input: {}) { "
        "pullRequest { id } } }'"
    )
    assert r.returncode == 2


def t_hub_pull_request_is_denied():
    r = _run("hub pull-request -m 'x'")
    assert r.returncode == 2


def t_curl_pulls_endpoint_is_denied():
    r = _run(
        "curl -X POST -H 'Authorization: token x' "
        "https://api.github.com/repos/tokenmaxxxer/on-the-record/pulls "
        "-d '{\"title\":\"x\"}'"
    )
    assert r.returncode == 2


def t_curl_graphql_create_pull_request_is_denied():
    r = _run(
        "curl -X POST https://api.github.com/graphql "
        "-d '{\"query\":\"mutation { createPullRequest(input: {}) { pullRequest { id } } }\"}'"
    )
    assert r.returncode == 2


def t_gh_issue_create_is_allowed():
    r = _run(
        "gh issue create --repo tokenmaxxxer/on-the-record --title x --body y"
    )
    assert r.returncode == 0


def t_gh_issue_list_search_is_allowed():
    r = _run(
        "gh issue list --repo tokenmaxxxer/on-the-record --state open "
        "--search 'watcher stale pid'"
    )
    assert r.returncode == 0


def t_unrelated_command_is_allowed():
    r = _run("git status")
    assert r.returncode == 0
