"""Operator-only actions for the northpole E2E harness (issue #776, spec §4).

This module performs everything the harness OPERATOR does before and after a
live session — instantiating a clean fixture-target working copy, and
capturing the requirement text / transcript. It does not launch a live
Claude Code session itself: that launch is an integration point the operator
wires to their own session-launch mechanism (issue #776 step 3).
"""

import shutil
import subprocess
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
FIXTURE_TEMPLATE_DIR = HARNESS_DIR / "fixture-target"

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
