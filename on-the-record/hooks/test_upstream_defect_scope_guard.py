"""Tests for upstream-defect-scope-guard.sh (issue #1131 req#4, scoped by
issue #1171: deny only within the upstream-defect channel's own flow,
never a session's own delivery PR against origin).

`tokenmaxxxer/on-the-record` is this repo's own git origin, so it now
stands in for "origin delivery PR" cases. A distinct repo
(`someorg/some-upstream`) stands in for "non-origin upstream target"
cases, and `CLAUDE_ROLE=upstream-defect-report` stands in for "channel's
own flow" cases regardless of target repo.
"""
import json
import os
import subprocess
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "upstream-defect-scope-guard.sh"
NON_ORIGIN_REPO = "someorg/some-upstream"


def _run(command, extra_env=None):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": os.getcwd(),
    })
    env = dict(os.environ)
    env["ORCHESTRATE_OFF"] = ""
    env.pop("CLAUDE_ROLE", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(GUARD)],
        input=payload, capture_output=True, text=True, env=env, timeout=20,
    )


def _run_as_channel(command):
    return _run(command, extra_env={"CLAUDE_ROLE": "upstream-defect-report"})


# --- channel-scope: denied on every covered surface, regardless of target --

def t_gh_pr_create_against_non_origin_target_is_denied():
    r = _run("gh pr create --repo %s --title x --body y" % NON_ORIGIN_REPO)
    assert r.returncode == 2
    assert "req#4" in r.stderr


def t_gh_pr_create_with_gh_repo_env_prefix_non_origin_is_denied():
    r = _run("GH_REPO=%s gh pr create --title x --body y" % NON_ORIGIN_REPO)
    assert r.returncode == 2


def t_gh_api_pulls_post_non_origin_is_denied():
    r = _run(
        "gh api --method POST repos/%s/pulls "
        "-f title=x -f head=y -f base=main" % NON_ORIGIN_REPO
    )
    assert r.returncode == 2


def t_gh_api_graphql_create_pull_request_is_denied_in_channel_role():
    r = _run_as_channel(
        "gh api graphql -f query='mutation { createPullRequest(input: {}) { "
        "pullRequest { id } } }'"
    )
    assert r.returncode == 2


def t_hub_pull_request_is_denied_in_channel_role():
    r = _run_as_channel("hub pull-request -m 'x'")
    assert r.returncode == 2


def t_curl_pulls_endpoint_non_origin_is_denied():
    r = _run(
        "curl -X POST -H 'Authorization: token x' "
        "https://api.github.com/repos/%s/pulls "
        "-d '{\"title\":\"x\"}'" % NON_ORIGIN_REPO
    )
    assert r.returncode == 2


def t_curl_graphql_create_pull_request_is_denied_in_channel_role():
    r = _run_as_channel(
        "curl -X POST https://api.github.com/graphql "
        "-d '{\"query\":\"mutation { createPullRequest(input: {}) { pullRequest { id } } }\"}'"
    )
    assert r.returncode == 2


def t_gh_pr_create_is_denied_in_channel_role_even_against_origin():
    r = _run_as_channel(
        "gh pr create --repo tokenmaxxxer/on-the-record --title x --body y"
    )
    assert r.returncode == 2


# --- origin delivery PR: allowed on every covered surface ------------------

def t_gh_pr_create_against_origin_is_allowed():
    r = _run("gh pr create --repo tokenmaxxxer/on-the-record --title x --body y")
    assert r.returncode == 0


def t_gh_pr_create_with_no_repo_flag_is_allowed():
    # no explicit target -> gh defaults to the origin repo.
    r = _run("gh pr create --title x --body y")
    assert r.returncode == 0


def t_gh_api_pulls_post_against_origin_is_allowed():
    r = _run(
        "gh api --method POST repos/tokenmaxxxer/on-the-record/pulls "
        "-f title=x -f head=y -f base=main"
    )
    assert r.returncode == 0


def t_curl_pulls_endpoint_against_origin_is_allowed():
    r = _run(
        "curl -X POST -H 'Authorization: token x' "
        "https://api.github.com/repos/tokenmaxxxer/on-the-record/pulls "
        "-d '{\"title\":\"x\"}'"
    )
    assert r.returncode == 0


# --- untouched behavior ------------------------------------------------

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
