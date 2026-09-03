"""Issue #3296: orchestrator state is memory ABOUT a repo, not one pile.

One plugin checkout sweeps several repositories -- that is normal use on a
machine where someone works on two projects at once. The board snapshot and
the delta cursor were single files shared by all of them, so one repo's
sweep overwrote the other's, and a `[video_producer]`-labelled
requirement-drift line listed on-the-record's issue numbers with nothing
anywhere recording the mismatch.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gates"))

import board_read  # noqa: E402
import gh_delta  # noqa: E402


class TwoReposDoNotShareOneFileTest(unittest.TestCase):
    def test_snapshots_are_separate_files(self):
        a = board_read.snapshot_path(Path("/x"), "owner/alpha")
        b = board_read.snapshot_path(Path("/y"), "owner/beta")
        self.assertNotEqual(a, b)

    def test_delta_cursors_are_separate_files(self):
        a = gh_delta.cursor_path("issues", "owner/alpha")
        b = gh_delta.cursor_path("issues", "owner/beta")
        self.assertNotEqual(a, b)

    def test_a_slugless_checkout_still_gets_one_stable_bucket(self):
        self.assertEqual(board_read.snapshot_path(Path("/x"), None),
                         board_read.snapshot_path(Path("/y"), None))

    def test_the_filename_survives_a_slash_in_the_slug(self):
        p = board_read.snapshot_path(Path("/x"), "owner/repo")
        self.assertNotIn("/", p.name)
        self.assertTrue(p.name.startswith("board_snapshot-"))

    def test_the_same_repo_keeps_the_same_file(self):
        self.assertEqual(board_read.snapshot_path(Path("/x"), "o/r"),
                         board_read.snapshot_path(Path("/x"), "o/r"))


class AMismatchedSnapshotIsNoticedTest(unittest.TestCase):
    """The filename separates them; the stamp is what lets a read notice."""

    def test_a_snapshot_naming_another_repo_is_treated_as_absent(self):
        import tempfile, json  # noqa: PLC0415
        d = Path(tempfile.mkdtemp())
        spath = d / "snap.json"
        spath.write_text(json.dumps({
            "version": board_read.SNAPSHOT_VERSION, "slug": "owner/other",
            "last_sweep_at": "2026-09-03T00:00:00Z",
            "sweep_seq": 1, "issues": {"3262": {}}, "prs": {}}),
            encoding="utf-8")
        calls = []

        def run(*a, **k):
            calls.append(a)
            raise AssertionError("full read attempted -- that is the point")

        # The mismatched snapshot must not be merged onto; the read falls
        # through to a full fetch, which this stub proves by being reached.
        with self.assertRaises(AssertionError):
            board_read.board_read(d, "owner/mine", run=run, path=spath)


class CompletionsGoToTheirOwnOrchestratorTest(unittest.TestCase):
    """The heartbeat printed 15 COMPLETED lines a tick, none of them ours."""

    def setUp(self):
        import tempfile  # noqa: PLC0415
        sys.path.insert(0, str(ROOT))
        import spawn  # noqa: PLC0415
        self.spawn = spawn
        self.prev = spawn.PENDING_COMPLETIONS
        spawn.PENDING_COMPLETIONS = Path(tempfile.mkdtemp()) / "q.jsonl"

    def tearDown(self):
        self.spawn.PENDING_COMPLETIONS = self.prev

    def _put(self, repo, key, ts=None):
        import time  # noqa: PLC0415
        self.spawn._record_session_completion(key, 1, "s", None, None, "ok",
                                              repo=repo)
        if ts is not None:
            lines = self.spawn.PENDING_COMPLETIONS.read_text(
                encoding="utf-8").splitlines()
            import json  # noqa: PLC0415
            out = []
            for line in lines:
                e = json.loads(line)
                if e["key"] == key:
                    e["ts"] = ts
                out.append(json.dumps(e))
            self.spawn.PENDING_COMPLETIONS.write_text(
                "\n".join(out) + "\n", encoding="utf-8")

    def test_only_this_repos_completions_are_returned(self):
        self._put("alpha", "issue-1/a")
        self._put("beta", "issue-2/b")
        mine, err, dropped = self.spawn._drain_pending_completions("alpha")
        self.assertIsNone(err)
        self.assertEqual([e["key"] for e in mine], ["issue-1/a"])

    def test_another_repos_completion_is_left_for_it(self):
        self._put("alpha", "issue-1/a")
        self._put("beta", "issue-2/b")
        self.spawn._drain_pending_completions("alpha")
        theirs, _, _ = self.spawn._drain_pending_completions("beta")
        self.assertEqual([e["key"] for e in theirs], ["issue-2/b"])

    def test_an_entry_with_no_repo_still_drains(self):
        # Written before the field existed; must not become undrainable.
        self._put(None, "issue-3/legacy")
        mine, _, _ = self.spawn._drain_pending_completions("alpha")
        self.assertEqual([e["key"] for e in mine], ["issue-3/legacy"])

    def test_an_undrained_foreign_entry_is_dropped_and_counted(self):
        import time  # noqa: PLC0415
        self._put("beta", "issue-2/old",
                  ts=time.time() - self.spawn.FOREIGN_COMPLETION_TTL_SEC - 60)
        mine, err, dropped = self.spawn._drain_pending_completions("alpha")
        self.assertEqual(mine, [])
        self.assertIsNone(err, "a drop is not a read failure")
        self.assertEqual(dropped, 1)


if __name__ == "__main__":
    unittest.main()
