"""R007 arms could not authenticate, and the failure named something else.

Every `claude -p` under an arm's isolated HOME failed on "Not logged in"
before any hook or the on/off skill manipulation ran, which a coarser
check then reported as a hook-firing regression. Ten rounds of the
experiment produced zero scored pairs on top of that.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "consumer-path"))

import prepare_arms  # noqa: E402


class AnArmCanAuthenticateTest(unittest.TestCase):
    def setUp(self):
        self.src = Path(tempfile.mkdtemp())
        (self.src / ".claude").mkdir()
        (self.src / ".claude" / ".credentials.json").write_text(
            json.dumps({"token": "SECRET-NOT-REAL"}), encoding="utf-8")
        self.home = Path(tempfile.mkdtemp())

    def test_the_credentials_file_lands_in_the_arm_home(self):
        r = prepare_arms.provision_credentials(self.home, self.src)
        self.assertTrue(r["provisioned"])
        self.assertTrue((self.home / ".claude" / ".credentials.json").is_file())

    def test_only_the_credentials_file_is_copied(self):
        (self.src / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        prepare_arms.provision_credentials(self.home, self.src)
        got = sorted(p.name for p in (self.home / ".claude").iterdir())
        self.assertEqual(got, [".credentials.json"])

    def test_the_copy_is_not_world_readable(self):
        prepare_arms.provision_credentials(self.home, self.src)
        mode = (self.home / ".claude" / ".credentials.json").stat().st_mode
        self.assertEqual(mode & 0o077, 0)

    def test_no_credential_content_is_returned(self):
        r = prepare_arms.provision_credentials(self.home, self.src)
        self.assertNotIn("SECRET-NOT-REAL", json.dumps(r))

    def test_a_missing_source_is_reported_not_skipped(self):
        empty = Path(tempfile.mkdtemp())
        r = prepare_arms.provision_credentials(self.home, empty)
        self.assertFalse(r["provisioned"])
        self.assertIn("no credentials file", r["reason"])


if __name__ == "__main__":
    unittest.main()
