"""Claude auth is not GitHub auth (issue #3245).

With only `~/.claude/.credentials.json` seeded, both arms still died before
any task work: the acceptance gate could not read the issue body and the
workspace fetch was refused with "Password authentication is not supported
for Git operations". The gate reported that as an Acceptance-format
problem -- a third failure in this experiment arriving under someone
else's name.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "consumer-path"))

import run_pair  # noqa: E402


class AnArmCanReachGitHubTest(unittest.TestCase):
    def setUp(self):
        self.src = Path(tempfile.mkdtemp())
        (self.src / ".config" / "gh").mkdir(parents=True)
        (self.src / ".config" / "gh" / "hosts.yml").write_text(
            "github.com:\n    oauth_token: NOT-A-REAL-TOKEN\n", encoding="utf-8")
        self.home = Path(tempfile.mkdtemp())

    def test_gh_auth_lands_in_the_arm_home(self):
        r = run_pair.seed_arm_github_auth(self.home, self.src)
        self.assertTrue(r["seeded"], r.get("reason"))
        self.assertTrue((self.home / ".config" / "gh" / "hosts.yml").is_file())

    def test_git_gets_a_credential_helper_pointing_at_gh(self):
        run_pair.seed_arm_github_auth(self.home, self.src)
        cfg = (self.home / ".gitconfig").read_text(encoding="utf-8")
        self.assertIn("auth git-credential", cfg)
        self.assertIn("https://github.com", cfg)

    def test_git_gets_a_committer_identity(self):
        run_pair.seed_arm_github_auth(self.home, self.src)
        cfg = (self.home / ".gitconfig").read_text(encoding="utf-8")
        self.assertIn("[user]", cfg)
        self.assertIn("email", cfg)

    def test_the_copy_is_not_world_readable(self):
        run_pair.seed_arm_github_auth(self.home, self.src)
        mode = (self.home / ".config" / "gh" / "hosts.yml").stat().st_mode
        self.assertEqual(mode & 0o077, 0)

    def test_no_token_content_is_returned(self):
        r = run_pair.seed_arm_github_auth(self.home, self.src)
        self.assertNotIn("NOT-A-REAL-TOKEN", json.dumps(r))

    def test_a_launcher_with_no_gh_auth_fails_visibly(self):
        empty = Path(tempfile.mkdtemp())
        r = run_pair.seed_arm_github_auth(self.home, empty)
        self.assertFalse(r["seeded"])
        self.assertIn("no gh auth", r["reason"])

    def test_both_arms_get_byte_identical_auth(self):
        # Anything differing between arms is a confound.
        a, b = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
        run_pair.seed_arm_github_auth(a, self.src)
        run_pair.seed_arm_github_auth(b, self.src)
        for rel in (".config/gh/hosts.yml", ".gitconfig"):
            self.assertEqual((a / rel).read_bytes(), (b / rel).read_bytes())


if __name__ == "__main__":
    unittest.main()
