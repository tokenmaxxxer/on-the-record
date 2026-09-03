"""An intentionally-absent skill repo must stay absent, not fall through.

`_skill_repo_root()` resolved `MUSTER_SKILL_REPO` first, and when that path
did not exist it simply continued to the next tier -- ending at the managed
clone, which is always populated. So "explicitly set to a path I made sure
does not exist" and "never set at all" produced the same answer.

That is what made R007 (issue #3245) unmeasurable for four rounds. The
experiment turns skills off by pointing `MUSTER_SKILL_REPO` at an absent
directory; the off arm silently picked up the managed clone and ran with
skills anyway. Every "tie" and "indistinguishable" verdict in that issue came
from comparing skills-on against skills-on. PR #3276 found it by noticing an
off-arm session log containing a real, successful `Skill` tool_use call
beside `mounted: []`.

A caller that sets the variable has already chosen which repository to use.
Silently overriding that choice is not a fallback, it is an accident.

  python3 -m pytest tests/test_issue_3277_skill_repo_absent_means_absent.py -q
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import skills  # noqa: E402
import spawn  # noqa: E402

skills._sp = spawn


class ExplicitlyAbsentMeansAbsentTest(unittest.TestCase):

    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.tmp = Path(self._t.name)
        self.addCleanup(self._t.cleanup)
        # A managed clone that exists and is populated -- the tier the old
        # code fell through to. If the fix works it is never reached here.
        self.managed = self.tmp / "managed"
        (self.managed / "some-skill").mkdir(parents=True)
        self._managed_patch = mock.patch.object(
            spawn, "_skill_repo_managed_root", return_value=self.managed)
        self._managed_patch.start()
        self.addCleanup(self._managed_patch.stop)

    def _resolve(self, env):
        """`env` values of None mean "unset this variable"."""
        setenv = {k: v for k, v in env.items() if v is not None}
        unset = [k for k, v in env.items() if v is None]
        buf = io.StringIO()
        with mock.patch.dict(os.environ, setenv, clear=False), \
             contextlib.redirect_stderr(buf):
            for k in unset:
                os.environ.pop(k, None)
            return skills._skill_repo_root(), buf.getvalue()

    def test_a_set_but_missing_path_resolves_to_none(self):
        missing = str(self.tmp / "deliberately-absent")
        root, _ = self._resolve({"MUSTER_SKILL_REPO": missing})
        self.assertIsNone(root, "fell through to a populated tier")

    def test_it_says_so_rather_than_failing_silently(self):
        missing = str(self.tmp / "deliberately-absent")
        _, err = self._resolve({"MUSTER_SKILL_REPO": missing})
        self.assertIn("MUSTER_SKILL_REPO", err)
        self.assertIn("fallback", err.lower() + err)

    def test_a_set_and_present_path_is_still_used(self):
        present = self.tmp / "real-repo"
        present.mkdir()
        root, _ = self._resolve({"MUSTER_SKILL_REPO": str(present)})
        self.assertEqual(root, present)

    def test_unset_still_falls_through_to_the_managed_clone(self):
        """The fix must not disable the fallback for callers who chose nothing."""
        root, _ = self._resolve({"MUSTER_SKILL_REPO": None,
                                  "TOKENMAXXXER_RULEBOOKS": None})
        self.assertEqual(root, self.managed)

    def test_an_empty_value_counts_as_unset(self):
        """`MUSTER_SKILL_REPO=` is the shell idiom for clearing a variable,
        not for naming an absent path."""
        root, _ = self._resolve({"MUSTER_SKILL_REPO": "",
                                  "TOKENMAXXXER_RULEBOOKS": None})
        self.assertEqual(root, self.managed)

    def test_a_path_that_is_a_file_not_a_directory_is_absent(self):
        f = self.tmp / "not-a-dir"
        f.write_text("x")
        root, _ = self._resolve({"MUSTER_SKILL_REPO": str(f)})
        self.assertIsNone(root)

    def test_tilde_and_vars_still_expand_before_the_check(self):
        present = self.tmp / "expanded"
        present.mkdir()
        with mock.patch.dict(os.environ, {"SOME_BASE": str(self.tmp)}):
            root, _ = self._resolve({"MUSTER_SKILL_REPO": "$SOME_BASE/expanded"})
        self.assertEqual(root, present)


if __name__ == "__main__":
    unittest.main()
