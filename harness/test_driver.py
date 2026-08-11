"""Regression test for issue #817: the instantiated fixture must be a real
git checkout so deliverable-guard.sh's git-root walk finds a root to deny
against, mirroring every real installed target."""

import subprocess
import tempfile
from pathlib import Path

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
