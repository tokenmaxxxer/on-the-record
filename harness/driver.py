"""Operator-only actions for the northpole E2E harness (issue #776, spec §4).

This module performs everything the harness OPERATOR does before and after a
live session — instantiating a clean fixture-target working copy, and
capturing the requirement text / transcript. It does not launch a live
Claude Code session itself: that launch is an integration point the operator
wires to their own session-launch mechanism (issue #776 step 3).
"""

import json
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


def extract_session_id(cli_result):
    """issue #878: `cli_result` is the parsed JSON object a `claude -p
    --output-format json` run returns. The orchestrator's own session_id is
    only knowable AFTER that turn ends (it is not assignable up front) — this
    is the one place the harness driver learns it, exactly like a real
    install's `spawn.py` roster capture does for the same field. Returns
    None (never a fabricated id) when the result carries no session_id."""
    if not cli_result:
        return None
    return cli_result.get("session_id")


def poll_for_pr_ready(repo, branch, token=None, timeout_sec=600, interval_sec=15,
                       sleep=None):
    """issue #878 case 3: poll ground truth (`gh pr view`, the same check
    run5's account already performs manually per the proposal) until the
    delegated PR on `branch` is OPEN and MERGEABLE, or `timeout_sec` elapses.

    Returns {"ready": True, "number": int} on success, or
    {"ready": False, "reason": str} on timeout — never raises on a normal
    not-yet-ready poll (a `gh` invocation failure just counts as "not yet",
    the timeout is what surfaces the eventual UNMEASURED-with-reason)."""
    import time as _time
    sleep = sleep or _time.sleep
    env = dict(os.environ, **({"GH_TOKEN": token} if token else {}))
    deadline = _time.monotonic() + timeout_sec
    while True:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--head", branch,
             "--json", "number,mergeable,state", "--jq", ".[0]"],
            capture_output=True, text=True, env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            try:
                pr = json.loads(result.stdout)
            except ValueError:
                pr = None
            if pr and pr.get("state") == "OPEN" and pr.get("mergeable") == "MERGEABLE":
                return {"ready": True, "number": pr["number"]}
        if _time.monotonic() >= deadline:
            return {"ready": False,
                    "reason": f"no OPEN/MERGEABLE PR for branch {branch!r} "
                              f"on {repo!r} within {timeout_sec}s"}
        sleep(interval_sec)


def resume_orchestrator_session(session_id, nudge, cwd=None, timeout_sec=None):
    """issue #878 case 3: the harness's own `--resume`-invoke — the process
    that ran the orchestrator's first `-p` turn has already exited
    (`code.claude.com/docs/en/headless.md` "Background tasks at exit"; a
    dead `-p` process cannot be revived in-process, only a NEW invocation
    with `--resume` continues it). Runs `claude -p "<nudge>" --resume
    "<session_id>" --output-format json` and returns the parsed JSON result.

    Returns {"ok": True, "result": <parsed json>} on success, or
    {"ok": False, "reason": str} when `claude` is missing, the resume
    invocation fails, or its stdout is not parseable JSON — never raises,
    never fabricates a result.

    issue #886: without `--permission-mode` (or with `acceptEdits`) this
    resumed turn can only auto-accept file edits, not Bash — `gh pr
    merge`, `git fetch`, and `spawn.py` invocations all get denied
    (measured PR #885, `.permission_denials`). `bypassPermissions` is the
    same headless default #700 already uses for real role spawns; it
    only lifts the HOST permission prompt — PreToolUse-hooked gates
    (gh-write-allow-gate.sh, merge-allow-gate.sh, deliverable-guard) still
    run regardless of this mode. One precise boundary: those hooks only
    ever emit "allow", never "deny", so any Bash shape outside their own
    allow-lists previously fell back on the host's default-deny — under
    bypassPermissions that default-deny is gone (issue #886 hunt,
    docs/issue-886/reports/implementation/hunt-issue-886-permission-mode-fix.md).
    This is an existing property of the same mode #700 already runs in
    production role spawns, not a regression this diff introduces."""
    try:
        proc = subprocess.run(
            ["claude", "-p", nudge, "--resume", session_id,
             "--permission-mode", "bypassPermissions",
             "--output-format", "json"],
            cwd=cwd, capture_output=True, text=True, timeout=timeout_sec,
        )
    except FileNotFoundError:
        return {"ok": False, "reason": "claude CLI not found on this host"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": f"--resume invocation exceeded {timeout_sec}s"}
    if proc.returncode != 0:
        return {"ok": False,
                "reason": f"--resume invocation exited {proc.returncode}: "
                          f"{proc.stderr.strip()[:500]}"}
    try:
        result = json.loads(proc.stdout)
    except ValueError:
        return {"ok": False, "reason": "--resume output was not valid JSON"}
    return {"ok": True, "result": result}


def drive_multiturn_completion(first_turn_result, repo, branch, nudge,
                                token=None, poll_timeout_sec=600,
                                poll_interval_sec=15, resume_timeout_sec=None,
                                sleep=None):
    """issue #878: the driver-side shape of the multi-turn completion loop
    (proposal case 3) — capture session_id from the first turn, poll ground
    truth for the delegated PR, and RESUME the orchestrator session so the
    orchestrator itself does the merge + final_report (never the driver
    acting on the PR itself — Rejected alternative C in the proposal, that
    would make the signal PASS on the driver's actions, not the
    orchestrator's).

    Returns a dict always carrying "final_report" (possibly None) and
    "unmeasured_reason" (possibly None) — exactly one of the two is
    non-None on any path, so `harness/signals.py` either sees a genuine
    final_report or an explicit UNMEASURED marker, never a fabricated one:
      - no session_id captured from the first turn -> unmeasured_reason
      - PR never becomes ready within poll_timeout_sec -> unmeasured_reason
      - the --resume invocation itself fails/is unavailable -> unmeasured_reason
      - --resume succeeds -> final_report := the resumed result's own
        `final_report` field if present, else the whole resumed result
        (the orchestrator's reply IS the report; callers reading the real
        transcript still validate its 4 parts via signals.py unchanged).
    """
    session_id = extract_session_id(first_turn_result)
    if not session_id:
        return {"final_report": None,
                "unmeasured_reason": "no session_id in the first turn's "
                                      "--output-format json result"}
    readiness = poll_for_pr_ready(repo, branch, token=token,
                                   timeout_sec=poll_timeout_sec,
                                   interval_sec=poll_interval_sec, sleep=sleep)
    if not readiness["ready"]:
        return {"final_report": None, "unmeasured_reason": readiness["reason"]}
    resumed = resume_orchestrator_session(
        session_id, nudge, timeout_sec=resume_timeout_sec)
    if not resumed["ok"]:
        return {"final_report": None, "unmeasured_reason": resumed["reason"]}
    result = resumed["result"]
    final_report = result.get("final_report") if isinstance(result, dict) else None
    return {"final_report": final_report or result, "unmeasured_reason": None}


def capture_transcript(raw_log):
    """Post-hoc transcript capture (spec §4): the harness never steers the run
    mid-flight. This is a placeholder structural parser the operator fills in
    once wired to a real session-launch mechanism (step 3) — it does not
    invent transcript content itself.

    Returns raw_log unchanged; callers own the actual parsing once a real
    session transcript format is available.
    """
    return raw_log
