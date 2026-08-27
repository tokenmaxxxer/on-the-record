"""issue #2593: `subject_deliverable_record()` used to resolve the
subject's deliverable by matching a hard-coded historical name
(`kind_field == "implementation"` / `name == "implementation"`) -- live and
reachable for most of this repo's board (fires whenever a subject's
deliverable still carries the old name), but blind to every subject whose
deliverable is named by the modern skill-slug convention (#2560/#2610):
those always got `(None, {})`, which `verifying_record_count()` reads as
"skip the self-verification guard" -- so a session could self-author two
`verifies_subject: true` records under its own subject and satisfy the
merge gate's independent-verification count without ever being caught.

Replaced with the same name-free, structural pattern
`subject_deliverable_branch()` already used (issue #2575): the deliverable
is whichever record does not itself self-declare `verifies_subject: true`;
ambiguous (zero or more than one candidate) refuses to guess, same as
`subject_deliverable_branch()`'s own "more than one match -> None"
contract. This exercises that fix against real records produced by
`spawn.write_record_skeleton()`, using slugs that were never
"implementation"/"coding" to prove the modern-naming gap is actually
closed."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import spawn  # noqa: E402
import spawn_on_pr  # noqa: E402


def _flip_to_true(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "verifies_subject: false" in text, text
    path.write_text(text.replace("verifies_subject: false", "verifies_subject: true", 1),
                     encoding="utf-8")


class ModernSlugDeliverableResolutionTest(unittest.TestCase):
    """A deliverable record named by the skill-slug convention -- never
    "implementation" or "coding" -- must still be found, and the
    self-verification guard must still fire against it."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def _board(self):
        return spawn.board(self.root)["issue-9001"]

    def test_single_modern_slug_deliverable_resolves_unambiguously(self):
        spawn.write_record_skeleton(str(self.root), 9001,
                                     "architecture-interface-contract-shape+coding-abc123")
        subject_board = self._board()
        slug, fm = spawn_on_pr.subject_deliverable_record(subject_board)
        self.assertEqual(slug, "architecture-interface-contract-shape+coding-abc123")
        self.assertEqual(fm.get("author"),
                          "architecture-interface-contract-shape+coding-abc123")

    def test_self_authored_verifying_records_are_excluded_for_modern_slug(self):
        # This is the live gap the audit found: under the old hard-coded
        # "implementation" match, this deliverable was never found (its
        # slug is not "implementation"), subject_author stayed None, and
        # verifying_record_count()'s self-verification guard never fired --
        # two self-authored records would have wrongly satisfied the
        # REQUIRED_INDEPENDENT_VERIFICATIONS count.
        deliverable = spawn.write_record_skeleton(
            str(self.root), 9001, "architecture-interface-contract-shape+coding-abc123")
        author = spawn.frontmatter(deliverable)["author"]
        p1 = spawn.write_record_skeleton(str(self.root), 9001, "self-verify-sub-a")
        p2 = spawn.write_record_skeleton(str(self.root), 9001, "self-verify-sub-b")
        for p in (p1, p2):
            text = p.read_text(encoding="utf-8")
            text = text.replace("verifies_subject: false", "verifies_subject: true", 1)
            text = text.replace(f"author: {p.stem}", f"author: {author}", 1)
            p.write_text(text, encoding="utf-8")

        subject_board = self._board()
        _slug, fm = spawn_on_pr.subject_deliverable_record(subject_board)
        self.assertEqual(fm.get("author"), author,
                          "deliverable must still resolve for a modern slug name")
        deficit = spawn_on_pr.verification_deficit(subject_board, subject_author=fm.get("author"))
        self.assertEqual(
            deficit, 2,
            "two verifies_subject:true records self-authored by the deliverable's own "
            "author must not satisfy the requirement")

    def test_two_independently_authored_records_still_satisfy_it(self):
        spawn.write_record_skeleton(str(self.root), 9001,
                                     "architecture-interface-contract-shape+coding-abc123")
        p1 = spawn.write_record_skeleton(str(self.root), 9001, "reviewer-alpha")
        p2 = spawn.write_record_skeleton(str(self.root), 9001, "reviewer-beta")
        _flip_to_true(p1)
        _flip_to_true(p2)
        subject_board = self._board()
        _slug, fm = spawn_on_pr.subject_deliverable_record(subject_board)
        deficit = spawn_on_pr.verification_deficit(subject_board, subject_author=fm.get("author"))
        self.assertEqual(deficit, 0)

    def test_ambiguous_multiple_non_verifying_records_refuses_to_guess(self):
        # Two records, neither self-declaring verifies_subject:true -- e.g.
        # a design doc and a build record under the same subject (this
        # issue's own board shape). No single "the deliverable" answer
        # exists; subject_deliverable_record() must say so rather than
        # picking one, exactly like subject_deliverable_branch()'s own
        # more-than-one-candidate contract.
        spawn.write_record_skeleton(str(self.root), 9001, "architecture-design-doc-xyz")
        spawn.write_record_skeleton(str(self.root), 9001, "coding-build-slug-abc")
        subject_board = self._board()
        slug, fm = spawn_on_pr.subject_deliverable_record(subject_board)
        self.assertIsNone(slug)
        self.assertEqual(fm, {})


if __name__ == "__main__":
    unittest.main()
