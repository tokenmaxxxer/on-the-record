"""Operator-only actions for the northpole E2E harness (issue #776, spec §4).

This module performs everything the harness OPERATOR does before and after a
live session — instantiating a clean fixture-target working copy, and
capturing the requirement text / transcript. It does not launch a live
Claude Code session itself: that launch is an integration point the operator
wires to their own session-launch mechanism (issue #776 step 3).
"""

import os
import shutil
import subprocess
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
FIXTURE_TEMPLATE_DIR = HARNESS_DIR / "fixture-target"

# issue #847: harness-only env vars for the steady-state faithful-GitHub-host
# scenario. Never read by anything a normal plugin install path reads.
NORTHPOLE_HARNESS_GH_REPO_ENV = "NORTHPOLE_HARNESS_GH_REPO"
NORTHPOLE_HARNESS_GH_TOKEN_ENV = "NORTHPOLE_HARNESS_GH_TOKEN"
DEFAULT_HARNESS_GH_REPO = "JiwonJung94/northpole-harness-fixture"

REPRESENTATIVE_REQUIREMENT = (
    "The CLI's --version flag currently crashes with a stack trace instead "
    "of printing the version — fix it, and make sure the fix is tested."
)


def instantiate_fixture_target(dest_dir, seed_remote_dir=None):
    """Copy a clean working copy of the fixture-target template to dest_dir.

    dest_dir must not already exist. Returns the Path to the new copy.

    seed_remote_dir (issue #831): when given, a bare repo is created at
    that path and wired as `origin` before returning — the steady-state
    (remote-present) scenario spec'd in
    docs/issue-831/reports/architecture.md "Harness scenario spec". When
    None (default, unchanged from before #831), the fixture has no
    remote — the no-remote scenario `ensure_target_remote` (spawn.py)
    must handle.
    """
    dest = Path(dest_dir)
    if dest.exists():
        raise FileExistsError(f"{dest} already exists; the harness requires a clean checkout")
    shutil.copytree(FIXTURE_TEMPLATE_DIR, dest)
    # Real installed targets are git checkouts; deliverable-guard.sh's
    # git-root walk silently allows when no .git is reachable, so an
    # un-initialized fixture never exercises the guard (issue #817).
    subprocess.run(["git", "init"], cwd=str(dest), check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(dest), check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=harness@example.com", "-c", "user.name=harness",
         "commit", "-m", "harness fixture initial commit"],
        cwd=str(dest), check=True, capture_output=True,
    )
    if seed_remote_dir is not None:
        remote = Path(seed_remote_dir)
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", str(remote)],
                       check=True, capture_output=True)
    return dest


def resolve_harness_github_token():
    """issue #847: NORTHPOLE_HARNESS_GH_TOKEN first, else the ambient `gh`
    CLI auth token (`gh auth token` — https://cli.github.com/manual/gh_auth_token,
    prints the token for the account `gh auth login` already authenticated).
    Never raises: a missing env var and a missing/failed `gh` both resolve
    to None so the caller degrades to UNMEASURED-with-reason, not a crash.
    """
    token = os.environ.get(NORTHPOLE_HARNESS_GH_TOKEN_ENV, "").strip()
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def resolve_harness_github_host():
    """issue #847: resolve the faithful GitHub host for the steady-state
    scenario (candidate 1: a real throwaway repo + harness-only token;
    candidate 3: explicit empty-state branch). Returns
    {"available": True, "repo", "token"} when both are resolvable, else
    {"available": False, "reason"}. Never raises, and "available": False
    must be reported by callers as UNMEASURED-with-reason — never a crash,
    never a silent PASS against a non-GitHub stand-in.
    """
    repo = os.environ.get(NORTHPOLE_HARNESS_GH_REPO_ENV, DEFAULT_HARNESS_GH_REPO)
    token = resolve_harness_github_token()
    if not token:
        return {
            "available": False,
            "reason": (
                f"no {NORTHPOLE_HARNESS_GH_TOKEN_ENV} set and no ambient "
                "`gh auth token` available; the steady-state faithful-"
                "GitHub-host scenario cannot run against a real host"
            ),
        }
    return {"available": True, "repo": repo, "token": token}


def reset_and_push_fixture_to_github(dest_dir, repo, token):
    """issue #847: reset repo (a real GitHub repo, e.g. the harness-only
    fixture host) to a clean state and push dest_dir's current HEAD as its
    sole default-branch history, so every steady-state run starts the
    delegated role from the same clean slate. Deletes every other branch
    via the GitHub REST API through `gh api`
    (https://cli.github.com/manual/gh_api) so no prior run's
    issue-<n>/<role> branches linger, then force-pushes dest_dir's HEAD.

    Callers must only reach this after resolve_harness_github_host() has
    already confirmed availability — a failure here is a real harness
    defect (raises subprocess.CalledProcessError), not an expected empty
    state.
    """
    remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    env = dict(os.environ, GH_TOKEN=token)

    default_branch = subprocess.run(
        ["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
        capture_output=True, text=True, env=env, check=True,
    ).stdout.strip()
    branches = subprocess.run(
        ["gh", "api", f"repos/{repo}/branches", "--paginate", "--jq", ".[].name"],
        capture_output=True, text=True, env=env, check=True,
    ).stdout.splitlines()
    for branch in branches:
        branch = branch.strip()
        if branch and branch != default_branch:
            subprocess.run(
                ["gh", "api", "-X", "DELETE", f"repos/{repo}/git/refs/heads/{branch}"],
                capture_output=True, text=True, env=env, check=True,
            )

    subprocess.run(
        ["git", "-C", str(dest_dir), "push", "--force", remote_url,
         f"HEAD:refs/heads/{default_branch}"],
        capture_output=True, text=True, check=True,
    )
    subprocess.run(
        ["git", "-C", str(dest_dir), "remote", "add", "origin", remote_url],
        capture_output=True, text=True, check=True,
    )
    return {"remote_url": remote_url, "pushed_ref": default_branch}


def seed_steady_state_github_host(dest_dir):
    """issue #847: wire dest_dir's `origin` to the real, harness-only
    GitHub fixture host and reset it to a clean state each run (candidate
    1), or report UNMEASURED-with-reason when no repo/token is configured
    (candidate 3's empty-state branch) — never raises, and never lets the
    caller proceed against a non-GitHub stand-in silently.

    Returns resolve_harness_github_host()'s dict; on success it also
    carries "remote_url" and "pushed_ref".
    """
    host = resolve_harness_github_host()
    if not host["available"]:
        return host
    pushed = reset_and_push_fixture_to_github(dest_dir, host["repo"], host["token"])
    return {**host, **pushed}


def get_representative_requirement():
    """The one representative requirement (spec §2), given verbatim as the
    first and only message to a fresh plain session."""
    return REPRESENTATIVE_REQUIREMENT


def run_build(target_dir):
    """pip install -e . inside target_dir; returns {"exit_code", "stdout", "stderr"}."""
    result = subprocess.run(
        ["pip", "install", "-e", "."],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
    )
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def run_version_check(target_dir):
    """fixture-target --version inside target_dir; returns {"exit_code", "stdout", "stderr"}."""
    result = subprocess.run(
        ["fixture-target", "--version"],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
    )
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def run_tests(target_dir):
    """pytest inside target_dir; returns {"exit_code", "stdout", "stderr"}."""
    result = subprocess.run(
        ["pytest"],
        cwd=str(target_dir),
        capture_output=True,
        text=True,
    )
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def capture_transcript(raw_log):
    """Post-hoc transcript capture (spec §4): the harness never steers the run
    mid-flight. This is a placeholder structural parser the operator fills in
    once wired to a real session-launch mechanism (step 3) — it does not
    invent transcript content itself.

    Returns raw_log unchanged; callers own the actual parsing once a real
    session transcript format is available.
    """
    return raw_log
