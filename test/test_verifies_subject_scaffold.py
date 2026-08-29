"""issue #2609 (landing-comment follow-up): `verifies_subject` used to be
documented (`docs/handbooks/observer-verification.md`) but written by
nothing -- a session had to remember the handbook, and forgetting it
silently left `verifying_record_count()` at 0 forever. This exercises the
real construction path end-to-end: `spawn.write_record_skeleton()` (the
single call site every real role/skill record goes through) now stamps
`verifies_subject: false` into every skeleton regardless of role/skill
name, and a session's own self-declared flip to `true` is what
`spawn.board()` + `gates/merge_gate.py::required_verification_missing()`
see and count -- reproducing acceptance bullets 2 and 3 of issue #2609
against records produced by the real scaffold, not hand-built dicts, and
using arbitrary role names (never "execution-observation"/
"conformance-review") to prove no closed set of names participates."""
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
import merge_gate  # noqa: E402


def _flip_to_true(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "verifies_subject: false" in text, text
    path.write_text(text.replace("verifies_subject: false", "verifies_subject: true", 1),
                     encoding="utf-8")


class ScaffoldStampsTheFieldUniversallyTest(unittest.TestCase):
    """No role/kind name decides whether the key is present -- every
    skeleton gets it, arbitrary role name included."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def test_arbitrary_skill_name_gets_the_field_default_false(self):
        p = spawn.write_record_skeleton(self._tmpdir.name, 4242,
                                         "totally-unenumerated-slug-9f3a")
        text = p.read_text(encoding="utf-8")
        self.assertIn("verifies_subject: false", text)

    def test_named_legacy_skills_get_no_special_treatment(self):
        # Same stamp, same default -- "execution-observation" carries no
        # special meaning to the scaffold; it is retired even as a
        # spawn-on-pr auto-spawn target name (issue #2628), unrelated to
        # this stamp either way.
        p1 = spawn.write_record_skeleton(self._tmpdir.name, 4242, "execution-observation")
        p2 = spawn.write_record_skeleton(self._tmpdir.name, 4242, "some-other-skill-slug")
        self.assertEqual(p1.read_text(encoding="utf-8").count("verifies_subject: false"), 1)
        self.assertEqual(p2.read_text(encoding="utf-8").count("verifies_subject: false"), 1)

    def test_frontmatter_parses_the_stamped_default_as_false(self):
        p = spawn.write_record_skeleton(self._tmpdir.name, 4242, "some-slug")
        fm = spawn.frontmatter(p)
        self.assertEqual(fm.get("verifies_subject"), "false")

    def test_respawn_into_existing_workspace_never_overwrites_a_flip(self):
        p = spawn.write_record_skeleton(self._tmpdir.name, 4242, "some-slug")
        _flip_to_true(p)
        again = spawn.write_record_skeleton(self._tmpdir.name, 4242, "some-slug")
        self.assertIsNone(again)  # refuses to touch an existing record
        self.assertEqual(spawn.frontmatter(p).get("verifies_subject"), "true")


class EndToEndMergeGateTest(unittest.TestCase):
    """Real records, real board, real merge_gate -- not hand-built dicts."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        # the subject's own deliverable record -- verifying_record_count's
        # self-verification guard excludes records authored by whoever this
        # names.
        spawn.write_record_skeleton(str(self.root), 4242, "implementation")

    def _board(self):
        return spawn.board(self.root)["issue-4242"]

    def _missing(self):
        subject_board = self._board()
        _slug, subject_fm = spawn_on_pr.subject_deliverable_record(subject_board)
        subject_author = subject_fm.get("author")
        count = spawn_on_pr.verifying_record_count(subject_board, subject_author=subject_author)
        return max(0, spawn_on_pr.REQUIRED_INDEPENDENT_VERIFICATIONS - count)

    def test_zero_qualifying_records_refuses_naming_the_count(self):
        # acceptance bullet 2: fewer than REQUIRED_INDEPENDENT_VERIFICATIONS
        # -- the refusal is required_verification_missing()'s own return
        # value, not an assertion.
        self.assertEqual(self._missing(), 2)

    def test_one_scaffolded_record_flipped_true_still_refuses(self):
        p = spawn.write_record_skeleton(str(self.root), 4242, "reviewer-alpha-7c1d")
        _flip_to_true(p)
        self.assertEqual(self._missing(), 1)

    def test_two_scaffolded_records_from_other_authors_satisfy_the_requirement(self):
        # the load-bearing demonstration: two records produced through the
        # real write_record_skeleton() path, self-declared true by editing
        # the stamped default (exactly what a real session does), authored
        # by names other than the deliverable's ("implementation") --
        # merge_gate sees the requirement met.
        p1 = spawn.write_record_skeleton(str(self.root), 4242, "reviewer-alpha-7c1d")
        p2 = spawn.write_record_skeleton(str(self.root), 4242, "reviewer-beta-2e9f")
        _flip_to_true(p1)
        _flip_to_true(p2)
        self.assertEqual(self._missing(), 0)

    def test_two_self_authored_scaffolded_records_still_refuse(self):
        # acceptance bullet 3: two verifies_subject: true records both
        # authored by the deliverable's own author ("implementation") do
        # not count -- the self-verification guard, reused unchanged.
        p1 = spawn.write_record_skeleton(str(self.root), 4242, "implementation-sub-a")
        p2 = spawn.write_record_skeleton(str(self.root), 4242, "implementation-sub-b")
        for p in (p1, p2):
            text = p.read_text(encoding="utf-8")
            text = text.replace("verifies_subject: false", "verifies_subject: true", 1)
            text = text.replace("author: implementation-sub-a", "author: implementation", 1)
            text = text.replace("author: implementation-sub-b", "author: implementation", 1)
            p.write_text(text, encoding="utf-8")
        self.assertEqual(self._missing(), 2)


if __name__ == "__main__":
    unittest.main()
