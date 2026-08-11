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
