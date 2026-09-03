"""A delivery subprocess must never be reinterpreted as a spawn.

`_launch_cross_family_delivery()` (issue #3230's async skill-judge fix)
launches `spawn.py cross-family-deliver <skill> --issue N --task-file P`
as a detached subprocess. It used to also pass `--skills <csv>` -- the
worker's skill set, carried as *data* to be delivered.

`main()` checks `if a.skills:` (spawn.py:~2485) long before it dispatches
`a.role == "cross-family-deliver"` (~2693), and that branch does not look
at `a.role` at all: with a selector flag present, argparse's lone remaining
positional is read as task text. So every delivery became a real spawn
whose `.task.txt` contained the literal string `cross-family-deliver` --
and that spawn, having an issue and a pending judge verdict, launched
another delivery. Measured on a consumer machine as workspaces growing
every tick while both `spawn_on_pr` and `spawn_on_approve` sweeps
independently reported nothing to spawn: 3,189 workspace directories and
34G at its worst, disk free down to 5.5GiB.

Two layers, because fixing the flag alone fixes only the flag:

  1. `LauncherArgvTest` -- the launcher does not put a spawn selector on
     the command line it builds.
  2. `InternalSubcommandGuardTest` -- and even if some future selector ends
     up there, a named internal subcommand still refuses to be a spawn.
     This is the property; (1) is one instance of it.

  python3 -m pytest tests/test_cross_family_deliver_is_never_a_spawn.py -q
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402


class LauncherArgvTest(unittest.TestCase):

    def _argv(self, skills_csv):
        captured = {}

        def _popen(cmd, **kwargs):
            captured["cmd"] = cmd
            raise OSError("not actually launching")

        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(spawn.subprocess, "Popen", _popen):
            spawn._launch_cross_family_delivery(
                tmp, 1066, "verification-before-completion", skills_csv, "task text")
        return captured.get("cmd", [])

    def test_launcher_never_passes_a_spawn_selector(self):
        argv = self._argv("silent-failure-audit,adversarial-review")
        self.assertNotIn("--skills", argv)
        self.assertNotIn("--skill", argv)

    def test_launcher_still_carries_the_skill_set_as_data(self):
        argv = self._argv("silent-failure-audit,adversarial-review")
        self.assertIn("--cross-family-skills", argv)
        self.assertEqual(argv[argv.index("--cross-family-skills") + 1],
                         "silent-failure-audit,adversarial-review")

    def test_the_subcommand_name_is_the_role_positional(self):
        argv = self._argv(None)
        self.assertIn("cross-family-deliver", argv)


class InternalSubcommandGuardTest(unittest.TestCase):
    """The property, independent of which flag happens to collide today."""

    def test_a_named_internal_subcommand_is_never_treated_as_a_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_file = Path(tmp) / "task.txt"
            task_file.write_text("delivered task text", encoding="utf-8")
            argv = ["spawn.py", "-C", tmp, "cross-family-deliver",
                    "verification-before-completion", "--issue", "1066",
                    "--task-file", str(task_file),
                    # the collision itself, forced back in on purpose
                    "--skills", "silent-failure-audit"]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(spawn, "_spawn_one") as spawn_one, \
                 mock.patch.object(spawn, "_deliver_cross_family_amendment") as deliver:
                rc = spawn.main()

        self.assertEqual(rc, 0)
        spawn_one.assert_not_called()
        deliver.assert_called_once()

    def test_the_delivery_still_happens_for_the_right_issue_and_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            task_file = Path(tmp) / "task.txt"
            task_file.write_text("delivered task text", encoding="utf-8")
            argv = ["spawn.py", "-C", tmp, "cross-family-deliver",
                    "verification-before-completion", "--issue", "1066",
                    "--task-file", str(task_file),
                    "--cross-family-skills", "silent-failure-audit"]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(spawn, "_spawn_one"), \
                 mock.patch.object(spawn, "_deliver_cross_family_amendment") as deliver:
                spawn.main()

        args = deliver.call_args.args
        self.assertEqual(args[1], 1066)
        self.assertEqual(args[2], "verification-before-completion")
        self.assertEqual(args[3], "silent-failure-audit")
        self.assertEqual(args[4], "delivered task text")


if __name__ == "__main__":
    unittest.main()
