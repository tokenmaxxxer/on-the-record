"""Issue #3049: does `gate-registration-post-guard.sh` (the issue #2705
post-commit report companion) actually catch the four cwd shapes that
walk past `gate-registration-guard.sh`'s PreToolUse `--cached` read
without it noticing -- bare `pushd`, `pushd +N`/`-N`, an env-var-prefixed
`cd`, and `$CDPATH`?

`gates/probe_cwd_shapes.py` answers this for real: a fresh scratch git
repo per shape, the actual bash builtin genuinely moving the cwd, a real
bundled `git add ... && git commit ...`, independent ground truth that
the file is genuinely staged, and the unmodified `gate-registration-
post-guard.sh` script fed the real captured commit output. This module
is the pytest-shaped wrapper the issue's acceptance amendment names
(`python3 -m pytest tests/test_cwd_shape_coverage.py -q`), calling the
same `run_shape()` the standalone probe uses so both entry points share
one implementation -- partitioned per shape name (equivalence
partitioning: each of the four named shapes is its own class of input),
plus the two edges around it: the probe script's own exit code, and the
not-reproducible path when a bundled command fails outright.

  python3 -m pytest tests/test_cwd_shape_coverage.py -v
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "gates"))
import probe_cwd_shapes as pcs  # noqa: E402


def _shape(name: str) -> dict:
    for shape in pcs.SHAPES:
        if shape["name"] == name:
            return shape
    raise KeyError(name)


class CwdShapeCoverageTest(unittest.TestCase):
    """One test per named shape (issue #3049's population): each is run
    for real against the unmodified `gate-registration-post-guard.sh`
    and must match the documented status recorded in
    `docs/issue-3049/reports/...` and mirrored in
    `gates/probe_cwd_shapes.py::DOCUMENTED_STATUS`."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="otr-test-cwd-shapes-")
        self.addCleanup(self._td.cleanup)
        self.tmp_root = Path(self._td.name)

    def _assert_shape_matches_documented(self, name: str) -> None:
        shape = _shape(name)
        result = pcs.run_shape(shape, self.tmp_root)
        self.assertTrue(
            result["ok"],
            f"{name}: could not be reproduced against current bash -- "
            f"{result.get('reason')}",
        )
        self.assertEqual(
            result["status"], pcs.DOCUMENTED_STATUS[name],
            f"{name}: documented status {pcs.DOCUMENTED_STATUS[name]!r} does "
            f"not match this run's observed {result['status']!r} -- "
            f"companion report: {result['report_text']!r}",
        )

    def test_bare_pushd_matches_documented_status(self):
        self._assert_shape_matches_documented("bare-pushd")

    def test_pushd_plusN_matches_documented_status(self):
        self._assert_shape_matches_documented("pushd-plusN")

    def test_env_prefixed_cd_matches_documented_status(self):
        self._assert_shape_matches_documented("env-prefixed-cd")

    def test_cdpath_matches_documented_status(self):
        self._assert_shape_matches_documented("cdpath")

    def test_all_four_shapes_are_genuinely_staged_by_real_git(self):
        """Ground-truth check independent of the companion: every shape's
        bundled command must result in real git actually staging the
        probe file (the issue's must-not forbids concluding "caught" on
        the companion's own claim without this being true first)."""
        for shape in pcs.SHAPES:
            with self.subTest(shape=shape["name"]):
                result = pcs.run_shape(shape, self.tmp_root)
                self.assertTrue(
                    result["ok"],
                    f"{shape['name']}: not reproducible -- "
                    f"{result.get('reason')}",
                )


class ProbeScriptEntryPointTest(unittest.TestCase):
    """The standalone `check:` command the issue amendment names."""

    def test_probe_script_exits_zero_and_prints_ok(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "gates" / "probe_cwd_shapes.py")],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"probe_cwd_shapes.py failed:\nstdout={proc.stdout}\n"
            f"stderr={proc.stderr}",
        )
        self.assertIn("ok", proc.stdout.splitlines())


class MustNotClausesTest(unittest.TestCase):
    """Issue #3049's must-not clauses are constraints on how this issue is
    resolved, not runtime behavior of the shipped hooks -- so the
    checkable form is "this delivery's diff never touched either guard
    script", not a black-box input/output case. Verifies that mechanically
    against `origin/main` rather than trusting the record's own prose."""

    def test_neither_guard_script_was_modified_by_this_delivery(self):
        for rel in (
            "on-the-record/hooks/gate-registration-guard.sh",
            "on-the-record/hooks/gate-registration-post-guard.sh",
        ):
            with self.subTest(path=rel):
                diff = subprocess.run(
                    ["git", "diff", "origin/main", "--", rel],
                    cwd=REPO_ROOT, capture_output=True, text=True, timeout=15,
                )
                if diff.returncode != 0:
                    self.skipTest(f"no origin/main to diff against: {diff.stderr}")
                self.assertEqual(
                    diff.stdout, "",
                    f"{rel} was modified by this delivery -- issue #3049's "
                    f"must-not forbids extending the PreToolUse parser or "
                    f"widening either hook to fail closed:\n{diff.stdout}",
                )


class NotReproducibleEdgeTest(unittest.TestCase):
    """A shape whose bundled command cannot run at all must surface as a
    named not-reproducible failure with the attempt shown, not a silent
    pass or an uncaught crash -- the edge the issue's empty-state clause
    names for a shape that can't be reproduced against current bash."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory(prefix="otr-test-cwd-shapes-")
        self.addCleanup(self._td.cleanup)
        self.tmp_root = Path(self._td.name)

    def test_failing_bundled_command_reports_reason_not_a_crash(self):
        broken_shape = {
            "name": "broken-shape",
            "setup": lambda root, repo: None,
            "command": "false",
            "added_path": "gates/does_not_exist.py",
        }
        result = pcs.run_shape(broken_shape, self.tmp_root)
        self.assertFalse(result["ok"])
        self.assertIn("exited", result["reason"])


if __name__ == "__main__":
    unittest.main()
