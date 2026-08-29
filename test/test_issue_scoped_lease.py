"""issue #2241 stage 1: `roster.lease_key()` generalizes the roster/lease
key's second half from a role name to any session-scoped disambiguator
string. These tests prove a non-role-keyed lease renews, hits
flat-progress, and expires+requeues identically to a role-keyed one, and
that the role-keyed shape stays byte-identical to what it was before this
stage."""
import unittest

import spawn


class _NullLock:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class LeaseKeyShapeTest(unittest.TestCase):
    def test_skill_keyed_shape_byte_identical(self):
        self.assertEqual(spawn.lease_key(2284, "implementation"),
                          "issue-2284/implementation")

    def test_nonskill_disambiguator_uses_same_shape(self):
        self.assertEqual(spawn.lease_key(2284, "lease-scope-token"),
                          "issue-2284/lease-scope-token")


class LeaseRenewIdenticalTest(unittest.TestCase):
    def test_renew_identical_for_skill_and_nonskill_key(self):
        now = 1_000_000.0
        entry_skill = {"issue": 2284, "skill": "implementation"}
        entry_nonskill = {"issue": 2284, "skill": "implementation"}
        key_skill = spawn.lease_key(2284, "implementation")
        key_nonskill = spawn.lease_key(2284, "lease-scope-token")

        advisories_skill = spawn.lease_renew(key_skill, entry_skill, now=now)
        advisories_nonskill = spawn.lease_renew(key_nonskill, entry_nonskill, now=now)

        self.assertEqual(advisories_skill, advisories_nonskill)
        self.assertEqual(entry_skill["lease_expires_at"],
                          entry_nonskill["lease_expires_at"])
        self.assertEqual(entry_skill["lease_flat_renewals"],
                          entry_nonskill["lease_flat_renewals"])
        self.assertEqual(entry_skill["lease_progress"],
                          entry_nonskill["lease_progress"])

    def test_flat_progress_advisory_fires_identically(self):
        now = 1_000_000.0
        for key in (spawn.lease_key(2284, "implementation"),
                    spawn.lease_key(2284, "lease-scope-token")):
            entry = {"issue": 2284, "skill": "implementation"}
            advisories = []
            for i in range(spawn.LEASE_FLAT_RENEWALS_K + 1):
                advisories = spawn.lease_renew(key, entry, now=now + i)
            self.assertEqual(len(advisories), 1)
            self.assertIn("flat-progress", advisories[0])


class LeaseExpireAndRequeueIdenticalTest(unittest.TestCase):
    def test_reconcile_sweep_requeues_nonskill_key_identically(self):
        now = 1_000_000.0
        key_skill = spawn.lease_key(2284, "implementation")
        key_nonskill = spawn.lease_key(2284, "lease-scope-token")
        d_all = {
            key_skill: {"issue": 2284, "skill": "implementation", "pid": 0,
                        "lease_expires_at": now - 10},
            key_nonskill: {"issue": 2284, "skill": "implementation", "pid": 0,
                           "lease_expires_at": now - 10},
        }
        events = []
        orig = (spawn.ledger_write, spawn._alive, spawn._roster_locked,
                spawn._roster_load, spawn._roster_save,
                spawn.deadman_check, spawn.deadman_mark)
        spawn.ledger_write = lambda ev: events.append(ev)
        spawn._alive = lambda pid: False
        spawn._roster_locked = lambda: _NullLock()
        spawn._roster_load = lambda: dict(d_all)
        spawn._roster_save = lambda d: None
        spawn.deadman_check = lambda now=None: 0
        spawn.deadman_mark = lambda now=None: None
        try:
            count = spawn.lease_reconcile_sweep(root=spawn.ROOT, d_all=d_all,
                                                 now=now)
        finally:
            (spawn.ledger_write, spawn._alive, spawn._roster_locked,
             spawn._roster_load, spawn._roster_save,
             spawn.deadman_check, spawn.deadman_mark) = orig

        self.assertEqual(count, 2)
        self.assertEqual(d_all, {})
        requeued = {e["key"] for e in events if e["event"] == "lease_expired_requeued"}
        self.assertEqual(requeued, {key_skill, key_nonskill})


if __name__ == "__main__":
    unittest.main()
