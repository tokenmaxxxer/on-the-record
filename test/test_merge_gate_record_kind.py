"""issue #2609: `gates/spawn_on_pr.py::verifying_record_count` and
`gates/merge_gate.py::required_verification_missing` gate on a
self-declared, counted `verifies_subject` field -- no `kind:` value,
filename, or skill name decides the merge-gating obligation anymore (the
old closed two-name tuple this replaces is gone entirely, not
re-expressed under another name). The self-verification guard (a
qualifying record whose `author:` equals the subject's own `author:` does
not count) still blocks, reused unchanged in spirit from the old
`kind:`-matching version."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
import spawn_on_pr  # noqa: E402
import merge_gate  # noqa: E402


class VerifyingRecordCountTest(unittest.TestCase):
    def test_two_qualifying_records_different_authors_counts_both(self):
        board = {
            "a": {"verifies_subject": "true", "author": "role-a"},
            "b": {"verifies_subject": "true", "author": "role-b"},
        }
        count = spawn_on_pr.verifying_record_count(board, subject_author="implementation")
        self.assertEqual(count, 2)

    def test_record_without_verifies_subject_does_not_count(self):
        board = {
            "survey": {"author": "role-a"},
            "a": {"verifies_subject": "true", "author": "role-b"},
        }
        count = spawn_on_pr.verifying_record_count(board, subject_author="implementation")
        self.assertEqual(count, 1)

    def test_self_verification_guard_blocks_same_author_as_subject(self):
        board = {
            "a": {"verifies_subject": "true", "author": "implementation"},
            "b": {"verifies_subject": "true", "author": "role-b"},
        }
        count = spawn_on_pr.verifying_record_count(board, subject_author="implementation")
        self.assertEqual(count, 1)

    def test_no_subject_author_skips_the_guard(self):
        board = {"a": {"verifies_subject": "true", "author": "implementation"}}
        count = spawn_on_pr.verifying_record_count(board, subject_author=None)
        self.assertEqual(count, 1)

    def test_no_kind_or_filename_participates_arbitrary_names_count(self):
        # issue #2609's own rejected-alternative check: a design doc
        # authored under the same subject must NOT satisfy the requirement
        # just by existing -- only its own `verifies_subject: true` field
        # does. An arbitrarily-named file with that field set DOES count.
        board = {
            "2026-08-27-some-survey": {"author": "role-a"},
            "perf-a1b2c3d4": {"verifies_subject": "true", "author": "role-b"},
        }
        count = spawn_on_pr.verifying_record_count(board, subject_author="implementation")
        self.assertEqual(count, 1)


class OwnPrSuppliesVerificationTest(unittest.TestCase):
    def _run_with_show(self, stdout, returncode, subject, own_branch, subject_author):
        orig_run = subprocess.run
        seen_cmd = []

        def fake_run(cmd, capture_output, text):
            seen_cmd.append(cmd)
            self.assertEqual(cmd[:3], ["git", "-C", "/repo"])
            return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="")
        merge_gate.subprocess.run = fake_run
        try:
            result = merge_gate._own_pr_supplies_verification(
                Path("/repo"), subject, own_branch, subject_author)
        finally:
            merge_gate.subprocess.run = orig_run
        if seen_cmd:
            # regression lock for the silent-failure-audit fix: this must
            # read origin/<branch>, never the bare branch name -- `repo`
            # has no local branch of that exact name (see this function's
            # own docstring).
            self.assertIn(f"origin/{own_branch}:", seen_cmd[0][-1])
        return result

    def test_own_branch_supplies_qualifying_record(self):
        result = self._run_with_show(
            "---\nverifies_subject: true\nauthor: execution-observation\n---\n", 0,
            "issue-2204", "issue-2204/execution-observation", "implementation")
        self.assertTrue(result)

    def test_own_branch_record_missing_verifies_subject_field(self):
        result = self._run_with_show(
            "---\nauthor: execution-observation\n---\n", 0,
            "issue-2204", "issue-2204/execution-observation", "implementation")
        self.assertFalse(result)

    def test_own_branch_self_authored_does_not_count(self):
        result = self._run_with_show(
            "---\nverifies_subject: true\nauthor: implementation\n---\n", 0,
            "issue-2204", "issue-2204/execution-observation", "implementation")
        self.assertFalse(result)

    def test_other_subjects_pr_is_a_no_op(self):
        result = merge_gate._own_pr_supplies_verification(
            Path("/repo"), "issue-2204", "issue-9999/implementation", "implementation")
        self.assertFalse(result)

    def test_no_pr_context_is_a_no_op(self):
        result = merge_gate._own_pr_supplies_verification(
            Path("/repo"), "issue-2204", None, "implementation")
        self.assertFalse(result)


class RequiredVerificationMissingIntegrationTest(unittest.TestCase):
    def test_load_bearing_refusal_fewer_than_required_records(self):
        # issue #2609 acceptance bullet 2: a subject with fewer than
        # REQUIRED_INDEPENDENT_VERIFICATIONS qualifying records refuses.
        import spawn

        board = {
            "issue-2204": {
                "implementation": {"author": "implementation"},
                "a": {"verifies_subject": "true", "author": "role-a"},
            }
        }
        orig_board = spawn.board
        spawn.board = lambda root: board
        try:
            missing = merge_gate.required_verification_missing(Path("."), "issue-2204")
        finally:
            spawn.board = orig_board
        self.assertEqual(missing, 1)

    def test_two_qualifying_records_satisfies_the_requirement(self):
        import spawn

        board = {
            "issue-2204": {
                "implementation": {"author": "implementation"},
                "a": {"verifies_subject": "true", "author": "role-a"},
                "b": {"verifies_subject": "true", "author": "role-b"},
            }
        }
        orig_board = spawn.board
        spawn.board = lambda root: board
        try:
            missing = merge_gate.required_verification_missing(Path("."), "issue-2204")
        finally:
            spawn.board = orig_board
        self.assertEqual(missing, 0)

    def test_self_authored_records_alone_do_not_satisfy_the_requirement(self):
        # issue #2609 acceptance bullet 3: two verifies_subject: true
        # records both authored by the deliverable author still refuse.
        import spawn

        board = {
            "issue-2204": {
                "implementation": {"author": "implementation"},
                "a": {"verifies_subject": "true", "author": "implementation"},
                "b": {"verifies_subject": "true", "author": "implementation"},
            }
        }
        orig_board = spawn.board
        spawn.board = lambda root: board
        try:
            missing = merge_gate.required_verification_missing(Path("."), "issue-2204")
        finally:
            spawn.board = orig_board
        self.assertEqual(missing, 2)


if __name__ == "__main__":
    unittest.main()
