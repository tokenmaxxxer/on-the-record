"""Regression test for issue #817: the instantiated fixture must be a real
git checkout so deliverable-guard.sh's git-root walk finds a root to deny
against, mirroring every real installed target."""

import subprocess
import tempfile
from pathlib import Path

import driver
from driver import instantiate_fixture_target


def test_instantiated_fixture_has_reachable_git_root():
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture-copy"
        instantiate_fixture_target(dest)

        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(dest),
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert Path(result.stdout.strip()).resolve() == dest.resolve()


def test_instantiated_fixture_has_no_remote_by_default():
    """Issue #831 no-remote scenario: unless seed_remote_dir is given, the
    fixture matches today's existing no-remote behavior."""
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture-copy"
        instantiate_fixture_target(dest)

        result = subprocess.run(
            ["git", "-C", str(dest), "remote", "get-url", "origin"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert result.stdout.strip() == ""


def test_instantiated_fixture_seeds_remote_when_requested():
    """Issue #831 steady-state scenario: seed_remote_dir wires a resolvable
    origin before the fixture is handed to a session."""
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture-copy"
        remote = Path(tmp) / "fixture-origin.git"
        instantiate_fixture_target(dest, seed_remote_dir=remote)

        result = subprocess.run(
            ["git", "-C", str(dest), "remote", "get-url", "origin"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == str(remote)


def test_resolve_harness_github_host_unmeasured_when_absent(monkeypatch):
    """issue #847: no token env var and no ambient `gh auth token` must
    resolve to an explicit UNMEASURED-with-reason dict, never raise."""
    monkeypatch.delenv("NORTHPOLE_HARNESS_GH_TOKEN", raising=False)
    monkeypatch.delenv("NORTHPOLE_HARNESS_GH_REPO", raising=False)

    def fake_run(cmd, **kwargs):
        assert cmd == ["gh", "auth", "token"]
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="not logged in")

    monkeypatch.setattr(driver.subprocess, "run", fake_run)

    host = driver.resolve_harness_github_host()

    assert host == {
        "available": False,
        "reason": (
            "no NORTHPOLE_HARNESS_GH_TOKEN set and no ambient `gh auth "
            "token` available; the steady-state faithful-GitHub-host "
            "scenario cannot run against a real host"
        ),
    }


def test_resolve_harness_github_host_unmeasured_when_gh_missing(monkeypatch):
    """issue #847: `gh` not installed at all must also degrade to
    UNMEASURED-with-reason, not a crash (FileNotFoundError)."""
    monkeypatch.delenv("NORTHPOLE_HARNESS_GH_TOKEN", raising=False)

    def fake_run(cmd, **kwargs):
        raise FileNotFoundError("gh: command not found")

    monkeypatch.setattr(driver.subprocess, "run", fake_run)

    host = driver.resolve_harness_github_host()

    assert host["available"] is False
    assert "reason" in host


def test_resolve_harness_github_host_available_from_env_token(monkeypatch):
    """issue #847: an explicit NORTHPOLE_HARNESS_GH_TOKEN must be used
    directly, with no ambient `gh auth token` subprocess call at all
    (no network attempted when the env var already answers the question)."""
    monkeypatch.setenv("NORTHPOLE_HARNESS_GH_TOKEN", "test-token-123")
    monkeypatch.setenv("NORTHPOLE_HARNESS_GH_REPO", "someorg/somerepo")

    def fake_run(cmd, **kwargs):
        raise AssertionError("must not shell out when the env token is already set")

    monkeypatch.setattr(driver.subprocess, "run", fake_run)

    host = driver.resolve_harness_github_host()

    assert host == {"available": True, "repo": "someorg/somerepo", "token": "test-token-123"}


def test_resolve_harness_github_host_unmeasured_when_token_is_whitespace(monkeypatch):
    """issue #847 hunt finding: a whitespace-only NORTHPOLE_HARNESS_GH_TOKEN
    must not count as a real token — it must fall through to the ambient
    `gh auth token` check (and UNMEASURED-with-reason when that also
    fails), never be accepted as-is."""
    monkeypatch.setenv("NORTHPOLE_HARNESS_GH_TOKEN", "   ")

    def fake_run(cmd, **kwargs):
        assert cmd == ["gh", "auth", "token"]
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")

    monkeypatch.setattr(driver.subprocess, "run", fake_run)

    host = driver.resolve_harness_github_host()

    assert host["available"] is False


def test_resolve_harness_github_host_defaults_repo(monkeypatch):
    """issue #847: NORTHPOLE_HARNESS_GH_REPO unset falls back to the
    provisioned fixture repo named in issue #847's operator-consent
    comment."""
    monkeypatch.setenv("NORTHPOLE_HARNESS_GH_TOKEN", "test-token-123")
    monkeypatch.delenv("NORTHPOLE_HARNESS_GH_REPO", raising=False)

    host = driver.resolve_harness_github_host()

    assert host["repo"] == "JiwonJung94/northpole-harness-fixture"


def test_seed_steady_state_github_host_unmeasured_when_absent(monkeypatch):
    """issue #847: with no repo/token configured, seed_steady_state_github_host
    must report UNMEASURED-with-reason and must never attempt to push or
    touch dest_dir's remotes."""
    monkeypatch.delenv("NORTHPOLE_HARNESS_GH_TOKEN", raising=False)

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "fixture-copy"
        instantiate_fixture_target(dest)

        def fake_run(cmd, **kwargs):
            if cmd[:2] == ["gh", "auth"]:
                return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="")
            raise AssertionError(f"must not push/reset when host is unavailable: {cmd}")

        monkeypatch.setattr(driver.subprocess, "run", fake_run)

        result = driver.seed_steady_state_github_host(dest)

        monkeypatch.undo()
        assert result["available"] is False
        assert "reason" in result
        remote_check = subprocess.run(
            ["git", "-C", str(dest), "remote", "get-url", "origin"],
            capture_output=True, text=True,
        )
        assert remote_check.returncode != 0
