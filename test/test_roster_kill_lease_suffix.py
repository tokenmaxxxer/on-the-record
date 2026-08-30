"""issue #2139 round-2: `roster_kill()` silently reported "not in roster"
for a bare skill name even when a live, lease-suffixed session matched it
(reproduced in docs/issue-2139/reports/adversarial-review-6cda09d1.md
finding 5 — the CLI's own `kill <역할>` usage text invites exactly this
call shape). Zero test coverage existed on this path before this file."""
import unittest

import lifecycle
import spawn


class RosterKillLeaseSuffixTest(unittest.TestCase):
    def setUp(self):
        self.orig_load = spawn._roster_load
        self.orig_alive = spawn._alive
        self.orig_remove = spawn.roster_remove
        self.removed = []
        spawn.roster_remove = lambda key: self.removed.append(key)

    def tearDown(self):
        spawn._roster_load = self.orig_load
        spawn._alive = self.orig_alive
        spawn.roster_remove = self.orig_remove

    def test_bare_skill_name_resolves_to_sole_live_lease_suffixed_entry(self):
        key = "issue-973/implementation-156ce32b"
        spawn._roster_load = lambda: {key: {"pid": 4242, "skill": "implementation-156ce32b"}}
        spawn._alive = lambda pid: True
        killed = []
        orig_kill = lifecycle.os.kill
        lifecycle.os.kill = lambda pid, sig: killed.append((pid, sig))
        try:
            rc = lifecycle.roster_kill(973, "implementation")
        finally:
            lifecycle.os.kill = orig_kill
        self.assertEqual(rc, 0)
        self.assertEqual(killed, [(4242, 15)])
        self.assertEqual(self.removed, [key])

    def test_bare_skill_name_with_multiple_live_candidates_fails_loud_not_silent(self):
        roster = {
            "issue-973/implementation-156ce32b": {"pid": 1, "skill": "implementation-156ce32b"},
            "issue-973/implementation-a1b2c3d4": {"pid": 2, "skill": "implementation-a1b2c3d4"},
        }
        spawn._roster_load = lambda: roster
        spawn._alive = lambda pid: True
        rc = lifecycle.roster_kill(973, "implementation")
        self.assertEqual(rc, 1)
        self.assertEqual(self.removed, [])

    def test_bare_skill_name_with_no_live_candidates_reports_not_in_roster(self):
        spawn._roster_load = lambda: {}
        spawn._alive = lambda pid: True
        rc = lifecycle.roster_kill(973, "implementation")
        self.assertEqual(rc, 1)
        self.assertEqual(self.removed, [])

    def test_exact_lease_suffixed_key_still_matches_directly(self):
        key = "issue-973/implementation-156ce32b"
        spawn._roster_load = lambda: {key: {"pid": 4242, "skill": "implementation-156ce32b"}}
        spawn._alive = lambda pid: True
        killed = []
        orig_kill = lifecycle.os.kill
        lifecycle.os.kill = lambda pid, sig: killed.append((pid, sig))
        try:
            rc = lifecycle.roster_kill(973, "implementation-156ce32b")
        finally:
            lifecycle.os.kill = orig_kill
        self.assertEqual(rc, 0)
        self.assertEqual(killed, [(4242, 15)])
        self.assertEqual(self.removed, [key])


if __name__ == "__main__":
    unittest.main()
