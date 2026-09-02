"""Issue #3134 repair round: the independent verification of PR #3143
graded must-not 1 Surface partly because `tests/` never exercised
`gates/amends_index.py::check()` against the ACTUAL repo tree -- every
prior test built a synthetic in-memory dict. This module closes that
gap: it runs `check()` against `ROOT` itself (sanity: the tree this
commit lands should be self-consistent) and, separately, against a real
on-disk copy of the tree with an unlinked amendment injected, confirming
`check()` fails closed there too -- not just against a fixture
`amends_index.render_index()` was itself written to satisfy.

Test derivation: Given the real repository tree, When `check()` runs
against it with no modification, Then it returns no blocking reasons
(the committed `docs/specs/amends-index.md` and every amended target's
backlink are self-consistent as of this commit). Given the real tree
copied to a temp directory with one extra unlinked `amends:` edge
written to disk, When `check()` runs against that copy, Then it reports
at least one blocking reason naming the unlinked amendment.

  python3 -m pytest tests/test_amends_index_wiring.py -q
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))

import amends_index  # noqa: E402


class RealTreeSelfConsistencyTest(unittest.TestCase):
    def test_check_passes_against_the_actual_committed_tree(self):
        bad = amends_index.check(ROOT)
        self.assertEqual(
            bad, [],
            "the committed docs/specs/amends-index.md and every amended "
            "target's backlink must already match what the real tree's "
            "amends: edges resolve to -- this landing must not itself "
            "introduce drift: " + repr(bad),
        )


class RealTreeUnlinkedAmendmentTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.repo = Path(self._tmp)
        # A real on-disk copy, not a synthetic dict -- check() must walk
        # the actual filesystem glob (docs/issue-*/reports/**/*.md), not
        # just resolve an in-memory records mapping.
        for rel in ("docs", "gates", "amends.py", "amends_backlink.py"):
            src = ROOT / rel
            dst = self.repo / rel
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.write_bytes(src.read_bytes())

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_check_fails_closed_on_an_unlinked_amendment_in_a_real_copy(self):
        target_dir = self.repo / "docs" / "issue-88888" / "reports"
        target_dir.mkdir(parents=True)
        target = target_dir / "wiring-test-target.md"
        target.write_text(
            "---\nissue: 88888\nrole: wiring-test\n---\n\n"
            "## Limitation\n\nsome claim\n",
            encoding="utf-8",
        )
        corrector = target_dir / "wiring-test-corrector.md"
        corrector.write_text(
            "---\nissue: 88888\nrole: wiring-test-corrector\n"
            "amends: docs/issue-88888/reports/wiring-test-target.md#limitation"
            "  # wiring test\n---\n\n## Correction\n\ntext\n",
            encoding="utf-8",
        )

        bad = amends_index.check(self.repo)
        self.assertTrue(
            bad, "check() must refuse: a real amends: edge landed on disk "
            "with neither the index regenerated nor the target's backlink "
            "written."
        )
        joined = " ".join(bad)
        self.assertIn("wiring-test-target.md", joined)

    def test_check_passes_once_both_the_index_and_the_backlink_are_landed(self):
        target_dir = self.repo / "docs" / "issue-88888" / "reports"
        target_dir.mkdir(parents=True)
        target = target_dir / "wiring-test-target.md"
        target.write_text(
            "---\nissue: 88888\nrole: wiring-test\n---\n\n"
            "## Limitation\n\nsome claim\n",
            encoding="utf-8",
        )
        corrector = target_dir / "wiring-test-corrector.md"
        corrector.write_text(
            "---\nissue: 88888\nrole: wiring-test-corrector\n"
            "amends: docs/issue-88888/reports/wiring-test-target.md#limitation"
            "  # wiring test\n---\n\n## Correction\n\ntext\n",
            encoding="utf-8",
        )

        amends_index.write_backlinks(self.repo)
        amends_index.update(self.repo)
        self.assertEqual(amends_index.check(self.repo), [])


if __name__ == "__main__":
    unittest.main()
