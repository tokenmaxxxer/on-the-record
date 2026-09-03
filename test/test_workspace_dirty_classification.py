"""Issue #3266: `spawn.py clean --dry-run` kept 279 of 298 workspaces on
one machine (19G) because `_workspace_untracked_not_ignored()` counted any
non-gitignored untracked file as "unpreserved work" -- including the
`.on-the-record/` scaffolding every session gets at startup and the report
stub every session creates and a crashed session never fills. Those are
exactly the workspaces most worth reclaiming, and the old predicate
refused every one of them.

This file exercises the seam directly: `_is_harness_scaffolding_path()`,
`_report_stub_has_no_content()`, and their combination
`_is_reclaimable_untracked_noise()`, plus the end-to-end effect on
`_workspace_clean_state()` via `_workspace_untracked_not_ignored()`. A
workspace whose only untracked files are harness scaffolding and an empty
report stub must classify as reclaimable (`reason is None`); a workspace
holding a report with real body content, or any other untracked file
(e.g. an experiment artifact), must stay dirty.

  python3 -m pytest test/test_workspace_dirty_classification.py -q
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

import spawn


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(cwd), *args],
                        capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"git {args} in {cwd} failed: {r.stderr}"
    return r


def _make_pushed_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    (path / "f.txt").write_text("x\n")
    _git(path, "add", "f.txt")
    _git(path, "commit", "-q", "-m", "init")
    remote = path.parent / (path.name + "-remote.git")
    _git(path.parent, "init", "-q", "--bare", str(remote))
    _git(path, "remote", "add", "origin", str(remote))
    _git(path, "push", "-q", "-u", "origin", "HEAD")
    return remote


_EMPTY_STUB = """---
issue: 3266
role: some-role
author: some-role
skills: some-skill (skill-repository(abc123))
verifies_subject: false
loop_state: in-progress
upstream:
  - path: <docs/issue-3266/... or code path this record builds on>
    sha:
---

# issue-3266 -- some-role record

## What was done

<!-- fill: the delivered work, concretely -->

## Why

<!-- fill: rationale for the approach taken -->

## What did not work

None.

## Next steps

<!-- fill while loop_state is non-terminal -->
"""

_FILLED_REPORT = """---
issue: 3266
role: some-role
author: some-role
skills: some-skill (skill-repository(abc123))
verifies_subject: false
loop_state: done
upstream:
  - path: docs/issue-3266/proposals/foo.md
    sha: same-commit
---

# issue-3266 -- some-role record

## What was done

Implemented the reclaimable-untracked-noise classification in
lifecycle.py and added tests.

## Why

Disk was filling unbounded because the cleaner treated every stub the
same as real work.
"""


class HarnessScaffoldingPathTest(unittest.TestCase):
    def test_on_the_record_file_is_scaffolding(self):
        self.assertTrue(
            spawn._is_harness_scaffolding_path(".on-the-record/role.json"))

    def test_on_the_record_nested_directive_is_scaffolding(self):
        self.assertTrue(spawn._is_harness_scaffolding_path(
            ".on-the-record/directive/turn-budget.md"))

    def test_unrelated_dotfile_is_not_scaffolding(self):
        self.assertFalse(spawn._is_harness_scaffolding_path(".pull-check"))

    def test_docs_path_is_not_scaffolding(self):
        self.assertFalse(spawn._is_harness_scaffolding_path(
            "docs/issue-3266/reports/foo.md"))


class ReportStubHasNoContentTest(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.w = Path(self._td.name)

    def _write(self, rel: str, text: str) -> None:
        p = self.w / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def test_empty_skeleton_stub_has_no_content(self):
        self._write("docs/issue-3266/reports/some-role.md", _EMPTY_STUB)
        self.assertTrue(spawn._report_stub_has_no_content(
            self.w, "docs/issue-3266/reports/some-role.md"))

    def test_filled_report_has_content(self):
        self._write("docs/issue-3266/reports/some-role.md", _FILLED_REPORT)
        self.assertFalse(spawn._report_stub_has_no_content(
            self.w, "docs/issue-3266/reports/some-role.md"))

    def test_one_line_consult_log_entry_has_content(self):
        """Regression guard: a short consult-log entry under the same
        reports/ tree (no frontmatter, one real line) must never be read
        as an empty stub just because it is short."""
        self._write(
            "docs/issue-3266/reports/consult-log/20260903T000000-1.md",
            "- 2026-09-03T00:00:00Z | skill=candidates | outcome='ok'\n")
        self.assertFalse(spawn._report_stub_has_no_content(
            self.w,
            "docs/issue-3266/reports/consult-log/20260903T000000-1.md"))

    def test_non_report_path_is_never_a_stub(self):
        """A file outside docs/issue-<n>/reports/ never matches, even if
        its content happens to look empty -- this predicate only ever
        exempts the one path shape the issue names."""
        self._write("docs/issue-3266/_assets/manifest.json", "")
        self.assertFalse(spawn._report_stub_has_no_content(
            self.w, "docs/issue-3266/_assets/manifest.json"))

    def test_missing_file_has_no_content_but_is_not_a_crash(self):
        self.assertFalse(spawn._report_stub_has_no_content(
            self.w, "docs/issue-3266/reports/does-not-exist.md"))


class WorkspaceClassificationEndToEndTest(unittest.TestCase):
    """The full seam: `_workspace_clean_state()` via
    `_workspace_untracked_not_ignored()`, matching the acceptance's
    reclaimable/never-reclaimed pair."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.root = Path(self._td.name)

    def _clean_state(self, w: Path):
        return spawn._workspace_clean_state(w, live={}, unreadable=None)

    def test_stub_plus_scaffolding_only_workspace_is_reclaimable(self):
        w = self.root / "stub-only"
        _make_pushed_repo(w)
        (w / "docs" / "issue-3266" / "reports").mkdir(parents=True)
        (w / "docs" / "issue-3266" / "reports" / "some-role.md").write_text(
            _EMPTY_STUB)
        (w / ".on-the-record").mkdir()
        (w / ".on-the-record" / "role.json").write_text("{}")
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)

    def test_workspace_with_filled_report_is_never_reclaimed(self):
        w = self.root / "real-report"
        _make_pushed_repo(w)
        (w / "docs" / "issue-3266" / "reports").mkdir(parents=True)
        (w / "docs" / "issue-3266" / "reports" / "some-role.md").write_text(
            _FILLED_REPORT)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미추적", detail)

    def test_workspace_with_other_untracked_file_stays_dirty(self):
        """An empty stub sitting alongside an unrelated untracked file
        (e.g. an experiment artifact) must not make the whole workspace
        reclaimable -- only the stub itself is noise."""
        w = self.root / "stub-plus-artifact"
        _make_pushed_repo(w)
        (w / "docs" / "issue-3266" / "reports").mkdir(parents=True)
        (w / "docs" / "issue-3266" / "reports" / "some-role.md").write_text(
            _EMPTY_STUB)
        (w / "docs" / "issue-3266" / "_assets").mkdir()
        (w / "docs" / "issue-3266" / "_assets" / "manifest.json").write_text(
            "{}")
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미추적", detail)


if __name__ == "__main__":
    unittest.main()
