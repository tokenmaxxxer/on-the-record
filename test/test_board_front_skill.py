"""issue #2725: `_front_skill()` used to break a tie between multiple
rootless records by testing membership in two hardcoded names
(`product-discovery`, `technical-feasibility`) -- the fourth closed-set
membership test found by #2719's enumeration (#2626 finding A pattern).
Neither name is a mountable skill any more, but old on-disk records still
use them literally (e.g. `docs/issue-1199/reports/product-discovery.md`),
so the fallback was not dead: it silently picked one of several rootless
records with no signal that it was actually the front one, rather than
reporting "no front record" as the caller would read a `None`.

Replaced with a non-identity signal true of the records themselves: which
one was committed to the repo first. When that signal cannot resolve the
tie either (simultaneous commit, or no commit yet), `_front_skill` now
reports that distinctly (`ok=False`) instead of guessing -- callers no
longer confuse "cannot decide" with "no front record exists" (`ok=True,
front=None`)."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402  (binds board._sp as a side effect of import)
import board  # noqa: E402


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True,
                    capture_output=True, text=True)


def _write_record(root, subject, skill, body="---\nloop_state: scope-proposed\n---\n"):
    p = root / "docs" / subject / "reports" / f"{skill}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


class FrontSkillTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "test")

    def tearDown(self):
        self._tmp.cleanup()

    def test_single_rootless_fast_path_unchanged(self):
        subject = "issue-9"
        _write_record(self.root, subject, "coding")
        _git(self.root, "add", f"docs/{subject}/reports/coding.md")
        _git(self.root, "commit", "-q", "-m", "add coding")
        front, ok = board._front_skill(self.root, subject, {"coding": {}})
        self.assertEqual((front, ok), ("coding", True))

    def test_zero_rootless_reports_no_front_record(self):
        subject = "issue-9"
        _write_record(self.root, subject, "coding",
                       "---\nupstream:\n  - path: docs/issue-8/reports/x.md\n---\n")
        _git(self.root, "add", f"docs/{subject}/reports/coding.md")
        _git(self.root, "commit", "-q", "-m", "add coding")
        front, ok = board._front_skill(self.root, subject, {"coding": {}})
        self.assertEqual((front, ok), (None, True))

    def test_ambiguous_resolved_by_earliest_commit_not_hardcoded_name_order(self):
        """Committed in the OPPOSITE order the retired name-order fallback
        would have picked -- proves the winner comes from commit history,
        not from a name appearing first in a hardcoded tuple."""
        subject = "issue-9"
        _write_record(self.root, subject, "technical-feasibility")
        _git(self.root, "add", f"docs/{subject}/reports/technical-feasibility.md")
        _git(self.root, "commit", "-q", "-m", "first")
        _write_record(self.root, subject, "product-discovery")
        _git(self.root, "add", f"docs/{subject}/reports/product-discovery.md")
        _git(self.root, "commit", "-q", "-m", "second")
        skills = {"technical-feasibility": {}, "product-discovery": {}}
        front, ok = board._front_skill(self.root, subject, skills)
        self.assertEqual((front, ok), ("technical-feasibility", True))

    def test_tie_reports_cannot_decide_distinctly_from_no_front_record(self):
        subject = "issue-9"
        _write_record(self.root, subject, "a")
        _git(self.root, "add", f"docs/{subject}/reports/a.md")
        _git(self.root, "commit", "-q", "-m", "same commit")
        _write_record(self.root, subject, "b")
        _git(self.root, "add", f"docs/{subject}/reports/b.md")
        _git(self.root, "commit", "-q", "--amend", "--no-edit")
        front, ok = board._front_skill(self.root, subject, {"a": {}, "b": {}})
        self.assertEqual((front, ok), (None, False))
        # distinct from the zero-rootless "no front record" outcome:
        self.assertNotEqual(
            (front, ok),
            board._front_skill(self.root, "issue-does-not-exist", {}))

    def test_no_hardcoded_membership_test_on_a_name_list(self):
        """The acceptance criterion's own check (issue #2725): the retired
        shape `for r in (<two names>): if r in ...` is gone from the
        executable body -- checked on the code, not the docstring, which
        still mentions the two retired names to explain the history."""
        import inspect
        src = inspect.getsource(board._front_skill)
        code = src.split('"""', 2)[-1]
        self.assertNotIn("for r in (", code)
        self.assertNotIn('"product-discovery", "technical-feasibility"', code)


class ApproveScopeFrontRecordMessageTest(unittest.TestCase):
    """board.py:611's `approve_scope` caller: confirms the two new exit
    messages are distinct (ambiguous vs. no-front-record) instead of both
    reading as "front record 를 판별할 수 없다", per issue #2725's acceptance
    criterion on caller behavior."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "test")

    def tearDown(self):
        self._tmp.cleanup()

    def test_ambiguous_rootless_pair_exits_with_cannot_decide_message(self):
        _write_record(self.root, "issue-9", "a")
        _git(self.root, "add", "docs/issue-9/reports/a.md")
        _git(self.root, "commit", "-q", "-m", "same commit")
        _write_record(self.root, "issue-9", "b")
        _git(self.root, "add", "docs/issue-9/reports/b.md")
        _git(self.root, "commit", "-q", "--amend", "--no-edit")
        with mock.patch.object(spawn, "_approvers", return_value={"someone"}), \
             mock.patch.object(spawn, "board",
                                return_value={"issue-9": {"a": {}, "b": {}}}):
            with self.assertRaises(SystemExit) as ctx:
                board.approve_scope(str(self.root), 9)
        self.assertIn("결정할 수 없다", str(ctx.exception))

    def test_zero_rootless_exits_with_no_front_record_message_distinct(self):
        _write_record(self.root, "issue-9", "a",
                       "---\nupstream:\n  - path: docs/issue-8/reports/x.md\n---\n")
        _git(self.root, "add", "docs/issue-9/reports/a.md")
        _git(self.root, "commit", "-q", "-m", "add a")
        with mock.patch.object(spawn, "_approvers", return_value={"someone"}), \
             mock.patch.object(spawn, "board",
                                return_value={"issue-9": {"a": {}}}):
            with self.assertRaises(SystemExit) as ctx:
                board.approve_scope(str(self.root), 9)
        msg = str(ctx.exception)
        self.assertIn("열린 레코드가 없다", msg)
        self.assertNotIn("결정할 수 없다", msg)


if __name__ == "__main__":
    unittest.main()
