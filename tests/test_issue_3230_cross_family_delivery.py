"""Tests for issue #3230's async cross-family delivery path:
`spawn._deliver_cross_family_amendment()`, `spawn._launch_cross_family_delivery()`,
and the `cross-family-deliver` CLI subcommand that wires them together.

These cover the piece round 2/PR#3240/PR#3250 named as missing and this
round built: the callback call site that resolves the deferred
skill_judge match and hands it to the existing amendment channel (issue
#3129) once Popen has already fired.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "on-the-record" / "hooks"))

import spawn  # noqa: E402
import amendment_channel  # noqa: E402


class DeliverCrossFamilyAmendmentTest(unittest.TestCase):
    """`_deliver_cross_family_amendment()`: resolves the real match off the
    dispatch path and writes an amendment only when it found something and
    can attribute a repo."""

    def _seeded_skill_dir(self, root, name="accessibility-aria-and-contrast-rules"):
        d = root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: >-\n  Use when X.\n---\n\n# body\n",
            encoding="utf-8")
        return d

    def test_nonempty_match_writes_amendment_with_add_only_note(self):
        with tempfile.TemporaryDirectory() as td:
            skill_dir = self._seeded_skill_dir(Path(td))
            write_calls = []
            with mock.patch.object(
                    spawn, "_cross_family_skill_matches_with_consult",
                    lambda *a, **k: ([skill_dir], "completed")), \
                 mock.patch.object(amendment_channel, "repo_slug_for_cwd",
                                   lambda cwd: "acme/widget"), \
                 mock.patch.object(
                     amendment_channel, "write_amendment",
                     lambda state_dir, repo, issue, note="":
                         write_calls.append((state_dir, repo, issue, note)) or 3):
                spawn._deliver_cross_family_amendment(
                    "/tmp/some-worker-cwd", 4242, "implementation", None,
                    "do the task")
        self.assertEqual(len(write_calls), 1)
        state_dir, repo, issue, note = write_calls[0]
        self.assertEqual(repo, "acme/widget")
        self.assertEqual(issue, "4242")
        self.assertIn("accessibility-aria-and-contrast-rules", note)
        self.assertIn("add-only", note)

    def test_empty_match_never_writes_amendment(self):
        write_calls = []
        with mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                               lambda *a, **k: ([], "no-candidates")), \
             mock.patch.object(amendment_channel, "write_amendment",
                               lambda *a, **k: write_calls.append(1)):
            spawn._deliver_cross_family_amendment(
                "/tmp/some-worker-cwd", 4242, "implementation", None, "task")
        self.assertEqual(write_calls, [])

    def test_matcher_exception_is_swallowed_never_raises(self):
        with mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                               mock.Mock(side_effect=RuntimeError("boom"))):
            # Must not raise -- this runs inside a detached subprocess
            # nobody joins.
            spawn._deliver_cross_family_amendment(
                "/tmp/some-worker-cwd", 4242, "implementation", None, "task")

    def test_unresolvable_repo_slug_skips_write(self):
        with tempfile.TemporaryDirectory() as td:
            skill_dir = self._seeded_skill_dir(Path(td))
            write_calls = []
            with mock.patch.object(
                    spawn, "_cross_family_skill_matches_with_consult",
                    lambda *a, **k: ([skill_dir], "completed")), \
                 mock.patch.object(amendment_channel, "repo_slug_for_cwd",
                                   lambda cwd: None), \
                 mock.patch.object(amendment_channel, "write_amendment",
                                   lambda *a, **k: write_calls.append(1)):
                spawn._deliver_cross_family_amendment(
                    "/tmp/some-worker-cwd", 4242, "implementation", None, "task")
        self.assertEqual(write_calls, [])

    def test_write_amendment_failure_does_not_raise(self):
        with tempfile.TemporaryDirectory() as td:
            skill_dir = self._seeded_skill_dir(Path(td))
            with mock.patch.object(
                    spawn, "_cross_family_skill_matches_with_consult",
                    lambda *a, **k: ([skill_dir], "completed")), \
                 mock.patch.object(amendment_channel, "repo_slug_for_cwd",
                                   lambda cwd: "acme/widget"), \
                 mock.patch.object(amendment_channel, "write_amendment",
                                   lambda *a, **k: None):
                spawn._deliver_cross_family_amendment(
                    "/tmp/some-worker-cwd", 4242, "implementation", None, "task")


class LaunchCrossFamilyDeliveryTest(unittest.TestCase):
    """`_launch_cross_family_delivery()`: fires a detached subprocess with
    the task text in a temp file (never a pipe) and never raises."""

    def test_launches_detached_subprocess_with_expected_args(self):
        popen_calls = []

        class _FakeProc:
            pid = 999

        def fake_popen(cmd, **kwargs):
            popen_calls.append((cmd, kwargs))
            return _FakeProc()

        with tempfile.TemporaryDirectory() as td:
            cwd = str(Path(td) / "work")
            Path(cwd).mkdir()
            with mock.patch.object(spawn.subprocess, "Popen", fake_popen):
                spawn._launch_cross_family_delivery(
                    cwd, 4242, "implementation", "alpha,beta", "the task text")
        self.assertEqual(len(popen_calls), 1)
        cmd, kwargs = popen_calls[0]
        self.assertIn("cross-family-deliver", cmd)
        # skill name rides the positional `task` slot, right after the
        # role -- `--skill` is already claimed by main()'s stage-0 lookup
        # branch (checked before role dispatch), so this subcommand can't
        # use it (spawn.py comment on `_launch_cross_family_delivery`).
        deliver_idx = cmd.index("cross-family-deliver")
        self.assertEqual(cmd[deliver_idx + 1], "implementation")
        self.assertIn("--issue", cmd)
        self.assertIn("4242", cmd)
        self.assertIn("--skills", cmd)
        self.assertIn("alpha,beta", cmd)
        self.assertIn("--task-file", cmd)
        task_file = cmd[cmd.index("--task-file") + 1]
        self.assertEqual(Path(task_file).read_text(encoding="utf-8"),
                         "the task text")
        self.assertTrue(kwargs.get("start_new_session"))
        Path(task_file).unlink()

    def test_popen_oserror_does_not_raise(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = str(Path(td) / "work")
            Path(cwd).mkdir()
            with mock.patch.object(spawn.subprocess, "Popen",
                                   mock.Mock(side_effect=OSError("no fork"))):
                spawn._launch_cross_family_delivery(
                    cwd, 4242, "implementation", None, "task")


class CrossFamilyDeliverRoleTest(unittest.TestCase):
    """`spawn.py cross-family-deliver` CLI subcommand: reads --task-file,
    deletes it, and hands off to `_deliver_cross_family_amendment()`."""

    def test_reads_and_deletes_task_file_then_delivers(self):
        fd, task_path = tempfile.mkstemp()
        import os
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("task text from file")
        calls = []
        with mock.patch.object(
                sys, "argv",
                ["spawn.py", "cross-family-deliver", "implementation", "--issue", "4242",
                 "--task-file", task_path, "-C", "/tmp/some-cwd"]), \
             mock.patch.object(
                 spawn, "_deliver_cross_family_amendment",
                 lambda cwd, issue, skill, skills_csv, task_text:
                     calls.append((cwd, issue, skill, skills_csv, task_text))):
            rc = spawn.main()
        self.assertEqual(rc, 0)
        self.assertFalse(Path(task_path).exists())
        self.assertEqual(len(calls), 1)
        cwd, issue, skill, skills_csv, task_text = calls[0]
        self.assertEqual(cwd, "/tmp/some-cwd")
        self.assertEqual(issue, 4242)
        self.assertEqual(skill, "implementation")
        self.assertEqual(task_text, "task text from file")

    def test_missing_issue_or_skill_exits_nonzero(self):
        with mock.patch.object(sys, "argv",
                               ["spawn.py", "cross-family-deliver",
                                "--task-file", "/tmp/does-not-matter"]):
            with self.assertRaises(SystemExit) as ctx:
                spawn.main()
        self.assertNotEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
