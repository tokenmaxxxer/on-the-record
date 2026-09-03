"""Issue #3293 stage 2: every wake carries the work, not just a verdict.

The defect these pin against is not a crash. It is three ticks in a row
that read HEALTHY-CONFIRMED while the session produced a wrong artifact --
so the tests below assert on what survives the filter and what a capped or
unreadable block says about itself, since a payload that quietly shortens
is the same blindness wearing a different label.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "gates"))
sys.path.insert(0, str(ROOT / "on-the-record" / "monitors"))

import tick_payload  # noqa: E402
import poll_heartbeat_delta as delta  # noqa: E402


class ItCarriesTheWorkTest(unittest.TestCase):
    def setUp(self):
        self.work = Path(tempfile.mkdtemp())

    def _write(self, rel: str) -> None:
        p = self.work / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")

    def test_lists_files_the_session_wrote(self):
        self._write("docs/brief.md")
        lines = tick_payload.session_block(
            "issue-9/s", {"work": str(self.work)}, time.time() - 60,
            "HEALTHY-CONFIRMED", [])
        self.assertIn("docs/brief.md", "\n".join(lines))

    def test_harness_writes_are_not_the_sessions_work(self):
        self._write(".on-the-record/state.json")
        self._write(".git/index")
        lines = tick_payload.session_block(
            "issue-9/s", {"work": str(self.work)}, time.time() - 60,
            "HEALTHY-CONFIRMED", [])
        self.assertIn("files: none since last tick", "\n".join(lines))

    def test_a_capped_block_says_it_was_capped(self):
        for i in range(tick_payload.MAX_FILES_PER_SESSION + 9):
            self._write(f"f{i}.md")
        text = "\n".join(tick_payload.session_block(
            "issue-9/s", {"work": str(self.work)}, time.time() - 60,
            "HEALTHY-CONFIRMED", []))
        self.assertIn("of 21", text)
        self.assertIn("9 more not shown", text)

    def test_repeated_identical_calls_collapse_with_a_count(self):
        out = tick_payload.collapse_calls([("Bash", "ps aux")] * 4)
        self.assertEqual(out, ["Bash: ps aux ×4"])

    def test_the_workspace_cd_prefix_does_not_eat_the_command(self):
        # First live tick regression: six distinct commands all rendered as
        # the same truncated `cd .../work/video_producer-…`.
        work = "/home/jwjung/.tokenmaxxxer/work/" + "video-producer-issue-32" * 3
        out = tick_payload.collapse_calls([
            ("Bash", f"cd {work} && git status --short"),
            ("Bash", f"cd {work} && python3 -m pytest -q"),
        ])
        self.assertEqual(out, ["Bash: git status --short",
                               "Bash: python3 -m pytest -q"])

    def test_a_newline_separator_after_the_cd_is_handled_too(self):
        # The `&&`-only first fix left the live payload unchanged: sessions
        # emit the cd and the command on separate lines.
        out = tick_payload.collapse_calls(
            [("Bash", "cd /home/jwjung/.tokenmaxxxer/work/w-1\ngit status")])
        self.assertEqual(out, ["Bash: git status"])

    def test_a_command_that_is_only_a_cd_is_still_shown(self):
        self.assertEqual(tick_payload.collapse_calls([("Bash", "cd /tmp")]),
                         ["Bash: cd /tmp"])

    def test_distinct_calls_are_not_collapsed(self):
        out = tick_payload.collapse_calls([("Bash", "ls"), ("Bash", "pwd")])
        self.assertEqual(out, ["Bash: ls", "Bash: pwd"])

    def test_a_missing_workspace_says_so_rather_than_reporting_none(self):
        text = "\n".join(tick_payload.session_block(
            "issue-9/s", {}, time.time() - 60, "UNKNOWN", []))
        self.assertIn("cannot list changes", text)
        self.assertNotIn("files: none", text)

    def test_unreadable_calls_are_distinguished_from_no_calls(self):
        text = "\n".join(tick_payload.session_block(
            "issue-9/s", {"work": str(self.work)}, time.time() - 60,
            "UNKNOWN", []))
        self.assertIn("calls: none readable", text)


class TheIdleTickStillSaysSomethingTest(unittest.TestCase):
    def test_it_names_outstanding_work(self):
        text = "\n".join(tick_payload.idle_block({"open PRs": ["11", "12"]}))
        self.assertIn("open PRs: 11, 12", text)

    def test_with_nothing_outstanding_it_points_at_stopping_the_monitor(self):
        text = "\n".join(tick_payload.idle_block({}))
        self.assertIn("monitor-stop", text)

    def test_it_is_never_a_bare_monitoring_active_placeholder(self):
        # Issue #1732 removed exactly that line; it must not come back.
        text = "\n".join(tick_payload.idle_block({})).lower()
        self.assertNotIn("monitoring active", text)


class TheFilterNeverSuppressesThePayloadTest(unittest.TestCase):
    """The payload's whole point is that an unchanged tick still shows it."""

    def _run(self, text: str, state: Path, now: int) -> str:
        env = dict(os.environ, POLL_HEARTBEAT_TEXT=text)
        r = subprocess.run(
            [sys.executable, str(ROOT / "on-the-record" / "monitors"
                                 / "poll_heartbeat_delta.py"), str(state),
             str(now)],
            env=env, capture_output=True, text=True, check=False)
        # Assert the exit code, not just stdout: the first draft of this
        # test omitted argv[2], and the resulting crash read as "the payload
        # was suppressed" -- a failed observation wearing an empty result's
        # clothes, which is the bug class this whole issue is about.
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_an_identical_payload_emits_again_on_the_next_tick(self):
        d = Path(tempfile.mkdtemp())
        state = d / "s.json"
        text = ("[poll-report] issue-9/s: HEALTHY-CONFIRMED — same\n"
                "[session] issue-9/s: HEALTHY-CONFIRMED\n"
                "    files (1):\n"
                "      docs/brief.md\n")
        self._run(text, state, 1000)
        second = self._run(text, state, 1120)
        self.assertIn("[session] issue-9/s", second)
        self.assertIn("docs/brief.md", second)

    def test_the_exemption_keys_on_shape_not_on_a_list_of_tags(self):
        # A payload line kind nobody remembered to list must still survive.
        self.assertTrue(delta.PAYLOAD_RE.match("    some future detail line"))


if __name__ == "__main__":
    unittest.main()
