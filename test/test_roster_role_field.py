"""issue #1803: watch/roster explicit `role` field — dual-write,
field-read, legacy-fallback, and string-key byte-identity coverage."""
import unittest

import spawn


class WorkspaceIndexDualWriteTest(unittest.TestCase):
    def test_workspace_index_put_writes_role_field(self):
        d = {}
        orig_load = spawn._workspace_index_load
        orig_index = spawn.WORKSPACE_INDEX
        orig_locked = spawn._workspace_index_locked
        orig_repo = spawn._repo_identity
        spawn._workspace_index_load = lambda: d
        spawn._repo_identity = lambda work: "repo"

        class _NullLock:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        class _NullIndex:
            parent = type("P", (), {"mkdir": staticmethod(lambda **kw: None)})()

            def write_text(self, text):
                pass

        spawn._workspace_index_locked = lambda: _NullLock()
        spawn.WORKSPACE_INDEX = _NullIndex()
        try:
            spawn._workspace_index_put(1792, "implementation", "/w", "/l")
        finally:
            spawn._workspace_index_load = orig_load
            spawn.WORKSPACE_INDEX = orig_index
            spawn._workspace_index_locked = orig_locked
            spawn._repo_identity = orig_repo

        key = "repo/issue-1792/implementation"
        self.assertIn(key, d)
        self.assertEqual(d[key]["role"], "implementation")
        self.assertEqual(d[key]["work"], "/w")
        self.assertEqual(d[key]["log"], "/l")


class FieldReadPathTest(unittest.TestCase):
    def test_live_roster_matches_reads_field(self):
        matches = [("repo/issue-1792/implementation",
                     {"work": "w", "role": "implementation"})]
        roster = {"issue-1792/implementation": {"pid": 999999999, "work": "w"}}
        orig_load = spawn._roster_load
        orig_alive = spawn._alive
        spawn._roster_load = lambda: roster
        spawn._alive = lambda pid: True
        try:
            result = spawn._live_roster_matches(matches, 1792)
            self.assertEqual(result, matches)
        finally:
            spawn._roster_load = orig_load
            spawn._alive = orig_alive

    def test_roster_fallback_entry_reads_field(self):
        roster = {"issue-1792/implementation":
                   {"pid": 1, "work": "/w", "log": "/l", "role": "implementation"}}
        orig_load = spawn._roster_load
        orig_alive = spawn._alive
        orig_repo = spawn._repo_identity
        spawn._roster_load = lambda: roster
        spawn._alive = lambda pid: True
        spawn._repo_identity = lambda work: "repo"
        try:
            key, entry = spawn._roster_fallback_entry(1792, None, None)
            self.assertEqual(key, "repo/issue-1792/implementation")
            self.assertEqual(entry, {"work": "/w", "log": "/l"})
        finally:
            spawn._roster_load = orig_load
            spawn._alive = orig_alive
            spawn._repo_identity = orig_repo

    def test_ambiguous_watch_exit_reads_field(self):
        matches = [("repoA/issue-1792/implementation",
                     {"work": "/wa", "role": "implementation"})]
        with self.assertRaises(SystemExit) as ctx:
            spawn._ambiguous_watch_exit(1792, matches, None)
        self.assertIn("implementation", str(ctx.exception))


class LegacyFallbackPathTest(unittest.TestCase):
    """Empty state per acceptance §2: a roster with only legacy entries
    (no `role` field) behaves identically to today via the fallback."""

    def test_live_roster_matches_falls_back_to_key_split(self):
        matches = [("repo/issue-1792/implementation", {"work": "w"})]
        roster = {"issue-1792/implementation": {"pid": 999999999, "work": "w"}}
        orig_load = spawn._roster_load
        orig_alive = spawn._alive
        spawn._roster_load = lambda: roster
        spawn._alive = lambda pid: True
        try:
            result = spawn._live_roster_matches(matches, 1792)
            self.assertEqual(result, matches)
        finally:
            spawn._roster_load = orig_load
            spawn._alive = orig_alive

    def test_roster_fallback_entry_falls_back_to_key_split(self):
        roster = {"issue-1792/implementation": {"pid": 1, "work": "/w", "log": "/l"}}
        orig_load = spawn._roster_load
        orig_alive = spawn._alive
        orig_repo = spawn._repo_identity
        spawn._roster_load = lambda: roster
        spawn._alive = lambda pid: True
        spawn._repo_identity = lambda work: "repo"
        try:
            key, entry = spawn._roster_fallback_entry(1792, None, None)
            self.assertEqual(key, "repo/issue-1792/implementation")
            self.assertEqual(entry, {"work": "/w", "log": "/l"})
        finally:
            spawn._roster_load = orig_load
            spawn._alive = orig_alive
            spawn._repo_identity = orig_repo

    def test_ambiguous_watch_exit_falls_back_to_key_split(self):
        matches = [("repoA/issue-1792/implementation", {"work": "/wa"})]
        with self.assertRaises(SystemExit) as ctx:
            spawn._ambiguous_watch_exit(1792, matches, None)
        self.assertIn("implementation", str(ctx.exception))


class KeyByteIdentityTest(unittest.TestCase):
    def test_workspace_index_key_byte_identical_before_and_after(self):
        d = {}
        orig_load = spawn._workspace_index_load
        orig_index = spawn.WORKSPACE_INDEX
        orig_locked = spawn._workspace_index_locked
        orig_repo = spawn._repo_identity
        spawn._workspace_index_load = lambda: d
        spawn._repo_identity = lambda work: "repo"

        class _NullLock:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        class _NullIndex:
            parent = type("P", (), {"mkdir": staticmethod(lambda **kw: None)})()

            def write_text(self, text):
                pass

        spawn._workspace_index_locked = lambda: _NullLock()
        spawn.WORKSPACE_INDEX = _NullIndex()
        try:
            spawn._workspace_index_put(1792, "implementation", "/w", "/l")
        finally:
            spawn._workspace_index_load = orig_load
            spawn.WORKSPACE_INDEX = orig_index
            spawn._workspace_index_locked = orig_locked
            spawn._repo_identity = orig_repo

        keys = list(d.keys())
        self.assertEqual(keys, ["repo/issue-1792/implementation"])
        self.assertEqual(keys[0], "repo/issue-1792/implementation")


if __name__ == "__main__":
    unittest.main()
