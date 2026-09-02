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
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))

import amends_index  # noqa: E402


def _scratch_checkout() -> Path:
    """A self-contained scratch copy of just the modules
    `gates/amends_index.py`'s CLI needs (mirrors the copytree fixture the
    other test classes in this module already use)."""
    tmp = Path(tempfile.mkdtemp())
    for rel in ("docs", "gates", "amends.py", "amends_backlink.py"):
        src = ROOT / rel
        dst = tmp / rel
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.write_bytes(src.read_bytes())
    return tmp


class CliRepoRootResolutionTest(unittest.TestCase):
    """Issue #3134 repair round 3, finding 4: `check()` reported
    `docs/specs/amends-index.md` missing right after `--update` had just
    written it, because the CLI's no-arg default resolved `repo` from the
    invoking process's cwd instead of this checkout's own root -- `--update`
    and `check` agreed only when invoked from the exact same directory.
    Reproduces the literal complaint (run `--update` then `check`, both
    with no positional arg, in a scratch repo) and the specific
    subdirectory case that exposed it."""

    def setUp(self):
        self.repo = _scratch_checkout()

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _run(self, *args, cwd):
        return subprocess.run(
            [sys.executable, str(self.repo / "gates" / "amends_index.py"), *args],
            cwd=str(cwd), capture_output=True, text=True, timeout=30,
        )

    def test_update_then_check_agree_from_the_scratch_repo_root(self):
        r1 = self._run("--update", cwd=self.repo)
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        r2 = self._run(cwd=self.repo)
        self.assertEqual(
            r2.returncode, 0,
            "check() must pass immediately after --update wrote the same "
            "index it is about to check: " + r2.stdout + r2.stderr,
        )

    def test_check_still_agrees_when_invoked_from_a_subdirectory(self):
        # The exact repro: `--update` from the repo root (as a human
        # naturally would), then a bare `check` run one level down.
        r1 = self._run("--update", cwd=self.repo)
        self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
        r2 = self._run(cwd=self.repo / "gates")
        self.assertEqual(
            r2.returncode, 0,
            "the no-arg default must anchor to the checkout root, not the "
            "invoking process's cwd: " + r2.stdout + r2.stderr,
        )


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


class CheckStagedScopingTest(unittest.TestCase):
    """Issue #3134 repair round 3, findings 1+2: a correcting session's
    own first commit of its own unlinked `amends:` record must not be
    denied (finding 1), and a pre-existing unresolved edge elsewhere in
    the tree must never block an unrelated session's commit (finding 2).
    `check_staged()` is the commit-time replacement for `check()` that
    the real hook (`amends-index-preflight.sh`) now calls."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.repo = Path(self._tmp)
        for rel in ("docs", "gates", "amends.py", "amends_backlink.py"):
            src = ROOT / rel
            dst = self.repo / rel
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.write_bytes(src.read_bytes())

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write(self, rel, content):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return rel

    def test_correcting_sessions_own_unlinked_commit_is_not_denied(self):
        self._write(
            "docs/issue-97001/reports/target.md",
            "---\nissue: 97001\nrole: target\n---\n\n"
            "## Limitation\n\nsome claim\n",
        )
        corrector = self._write(
            "docs/issue-97001/reports/corrector.md",
            "---\nissue: 97001\nrole: corrector\n"
            "amends: docs/issue-97001/reports/target.md#limitation"
            "  # actually wrong\n---\n\n## Correction\n\ntext\n",
        )
        # The exact shape a correcting session's own first commit stages:
        # target (already landed, untouched here) plus its own new
        # corrector -- no backlink can exist yet, by construction.
        bad = amends_index.check_staged(self.repo, {corrector})
        self.assertEqual(
            bad, [],
            "a structurally-valid amends: edge must never be denied at "
            "commit time merely for being unlinked pre-landing: " + repr(bad),
        )

    def test_unrelated_session_commit_never_blocked_by_a_foreign_unresolved_edge(self):
        # A pre-existing broken edge, unrelated to the commit under test.
        self._write(
            "docs/issue-97002/reports/dangling-corrector.md",
            "---\nissue: 97002\nrole: dangling-corrector\n"
            "amends: docs/issue-97002/reports/does-not-exist.md#nope"
            "  # broken on purpose\n---\n\n## Correction\n\ntext\n",
        )
        unrelated = self._write(
            "docs/issue-97003/reports/unrelated.md",
            "---\nissue: 97003\nrole: unrelated\n---\n\nnothing to do with "
            "amends: at all.\n",
        )
        bad = amends_index.check_staged(self.repo, {unrelated})
        self.assertEqual(
            bad, [],
            "an unrelated session's own commit must never be denied by "
            "someone else's unresolved edge elsewhere in the tree: "
            + repr(bad),
        )

    def test_a_commit_introducing_a_dangling_target_is_still_denied(self):
        corrector = self._write(
            "docs/issue-97004/reports/corrector.md",
            "---\nissue: 97004\nrole: corrector\n"
            "amends: docs/issue-97004/reports/does-not-exist.md#nope"
            "  # broken\n---\n\n## Correction\n\ntext\n",
        )
        bad = amends_index.check_staged(self.repo, {corrector})
        self.assertTrue(
            bad, "a genuinely malformed edge this commit itself introduces "
            "must still be refused -- check_staged() is scoped, not "
            "toothless.")


class CheckLandingTest(unittest.TestCase):
    """check_landing() is the merge-time counterpart -- run after the
    automatic apply step, it must still catch a residual unlinked edge
    among this PR's own staged paths."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.repo = Path(self._tmp)
        for rel in ("docs", "gates", "amends.py", "amends_backlink.py"):
            src = ROOT / rel
            dst = self.repo / rel
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                dst.write_bytes(src.read_bytes())

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write(self, rel, content):
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return rel

    def test_still_missing_backlink_denies_at_landing(self):
        self._write(
            "docs/issue-97005/reports/target.md",
            "---\nissue: 97005\nrole: target\n---\n\n"
            "## Limitation\n\nsome claim\n",
        )
        corrector = self._write(
            "docs/issue-97005/reports/corrector.md",
            "---\nissue: 97005\nrole: corrector\n"
            "amends: docs/issue-97005/reports/target.md#limitation"
            "  # actually wrong\n---\n\n## Correction\n\ntext\n",
        )
        # No apply step run -- simulates a landing attempt where the
        # automatic caller (amends_landing.land()) never fired.
        bad = amends_index.check_landing(self.repo, {corrector})
        self.assertTrue(
            bad, "check_landing() must still refuse an edge left unlinked "
            "at merge time.")

    def test_passes_once_the_apply_step_has_run(self):
        self._write(
            "docs/issue-97006/reports/target.md",
            "---\nissue: 97006\nrole: target\n---\n\n"
            "## Limitation\n\nsome claim\n",
        )
        corrector = self._write(
            "docs/issue-97006/reports/corrector.md",
            "---\nissue: 97006\nrole: corrector\n"
            "amends: docs/issue-97006/reports/target.md#limitation"
            "  # actually wrong\n---\n\n## Correction\n\ntext\n",
        )
        amends_index.write_backlinks(self.repo)
        amends_index.update(self.repo)
        bad = amends_index.check_landing(self.repo, {corrector})
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
