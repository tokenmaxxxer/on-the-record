"""R007's control arm needs "dispatch with no skills" (issue #3280).

`skills.py::resolved_skill_dirs()` has always treated an empty selector as
"mount nothing", on a byte-identical code path. Only the CLI refused: `if
a.skills:` could not tell `--skills ""` from the flag being absent, so an
empty value fell through to the retired-form error.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _spawn(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "spawn.py"), *args],
        capture_output=True, text=True, cwd=cwd or str(ROOT), timeout=120)


class AnEmptySelectorIsAControlArmTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)

    def _retired_form_error(self, out):
        return "은퇴했다" in out or "--skills 로만" in out

    def test_an_empty_selector_is_not_refused_as_a_retired_form(self):
        r = _spawn("--skills", "", "a task", "--issue", "1",
                   "-C", str(self.repo))
        self.assertFalse(self._retired_form_error(r.stdout + r.stderr),
                         r.stdout + r.stderr)

    def test_omitting_the_flag_is_still_refused(self):
        r = _spawn("a task", "--issue", "1", "-C", str(self.repo))
        self.assertTrue(self._retired_form_error(r.stdout + r.stderr),
                        "the retired bare-task spawn must stay retired")

    def test_a_selector_that_names_nothing_is_still_an_error(self):
        # The caller named something and it survived as nothing -- that is
        # a mistake, unlike a literally empty selector.
        r = _spawn("--skills", ",,", "a task", "--issue", "1",
                   "-C", str(self.repo))
        self.assertIn("empty skill list", r.stdout + r.stderr)

    def test_a_no_skills_arm_gets_its_own_identity(self):
        src = (ROOT / "spawn.py").read_text(encoding="utf-8")
        self.assertIn('else "no-skills"', src,
                      "a control arm must not borrow a skill name it "
                      "does not have")

    def test_an_unresolvable_named_skill_still_fails_closed(self):
        r = _spawn("--skills", "definitely-not-a-real-skill", "a task",
                   "--issue", "1", "-C", str(self.repo))
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
