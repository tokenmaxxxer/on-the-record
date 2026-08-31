"""issue #2908: the retired `muster` name (#83) is no longer a candidate
in poll_rearm_resolve_checkout() (on-the-record/hooks/poll-rearm.sh). It
was the stalest possible resolution -- a clone of a different, dead
repository (tokenmaxxxer/muster) that nothing ever refreshed -- and
strictly worse than falling through to the self-clone candidate that
already exists one step later in the same search order.

Run: python3 -m pytest test/test_engine_checkout_resolve_muster_retired.py -q
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POLL_REARM = REPO_ROOT / "on-the-record" / "hooks" / "poll-rearm.sh"


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args],
                           capture_output=True, text=True, check=True)


def _resolve(hook_script_path: Path, home: Path, extra_env: dict | None = None) -> str:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("TOKENMAXXXER_CHECKOUT", None)
    if extra_env:
        env.update(extra_env)
    script = f'source "{POLL_REARM}"\npoll_rearm_resolve_checkout "{hook_script_path}"\n'
    result = subprocess.run(["bash", "-c", script], capture_output=True,
                             text=True, timeout=30, env=env)
    return result.stdout.strip()


class MusterRetiredTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.home = base / "home"
        self.home.mkdir()
        # A hook-script location with no spawn.py ancestor within 4 levels
        # and no TOKENMAXXXER_CHECKOUT override, so resolution falls
        # through to the HOME-scoped candidates only.
        self.hook_dir = base / "plugin-root" / "hooks"
        self.hook_dir.mkdir(parents=True)
        (self.hook_dir / "poll-rearm.sh").write_text("")  # unused stand-in

    def tearDown(self):
        self._tmp.cleanup()

    def test_muster_present_alone_falls_through_to_self_clone_not_muster(self):
        # No network: `insteadOf`-rewrite the hardcoded self-clone URL to a
        # local bare repo so the fallthrough (candidate 6) is exercised
        # deterministically instead of skipped/flaky on an offline runner.
        muster = self.home / ".claude" / "tokenmaxxxer" / "muster"
        muster.mkdir(parents=True)
        (muster / "spawn.py").write_text("# retired clone\n")

        seed = self.home / "seed"
        seed.mkdir()
        _git(seed, "init", "-q")
        _git(seed, "config", "user.email", "t@example.com")
        _git(seed, "config", "user.name", "t")
        (seed / "spawn.py").write_text("# fresh clone\n")
        _git(seed, "add", "spawn.py")
        _git(seed, "commit", "-q", "-m", "seed")
        origin = self.home / "origin.git"
        _git(seed, "clone", "-q", "--bare", str(seed), str(origin))

        gitconfig = self.home / "gitconfig"
        gitconfig.write_text(
            f'[url "{origin}"]\n'
            '    insteadOf = https://github.com/tokenmaxxxer/on-the-record.git\n'
        )

        resolved = _resolve(self.hook_dir / "poll-rearm.sh", self.home,
                             extra_env={"GIT_CONFIG_GLOBAL": str(gitconfig),
                                        "GIT_CONFIG_NOSYSTEM": "1"})

        own = self.home / ".claude" / "tokenmaxxxer" / "on-the-record"
        self.assertNotEqual(resolved, str(muster),
                             "muster must never be the resolved checkout")
        self.assertEqual(resolved, str(own))
        self.assertTrue((own / "spawn.py").exists())

    def test_own_clone_wins_over_a_present_muster_clone(self):
        own = self.home / ".claude" / "tokenmaxxxer" / "on-the-record"
        own.mkdir(parents=True)
        (own / "spawn.py").write_text("# current own clone\n")
        muster = self.home / ".claude" / "tokenmaxxxer" / "muster"
        muster.mkdir(parents=True)
        (muster / "spawn.py").write_text("# retired clone\n")

        resolved = _resolve(self.hook_dir / "poll-rearm.sh", self.home)

        self.assertEqual(resolved, str(own))


if __name__ == "__main__":
    unittest.main()
