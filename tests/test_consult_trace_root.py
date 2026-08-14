#!/usr/bin/env python3
"""issue-1313 — consult-family trace/record paths anchored consistently.

Root cause: `_consult_trace_path()`/`_persist_consult_raw_output()`/
`_panel_record_path()` anchored to the plugin `ROOT`, while
`_commit_consult_trace()` computed the git root from `-C`/cwd. When a
consult targets any repo other than the plugin clone, the two roots
diverge: the trace line lands in the plugin repo, then
`p.relative_to(root)` raises `ValueError` and a successful consult is
reported as a failure. The fix funnels all four functions through one
`_consult_root(cwd)` anchor: the target repo when `-C`/cwd is given,
falling back to `ROOT` otherwise.

Runs with real git repos (no network/GitHub), same fixture shape as
`tests/test_gates.py`'s `_scratch_git_clone()`/`_consult_fake_run()`.

  python3 -m pytest tests/test_consult_trace_root.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn

ROOT = Path(__file__).parent.parent


def _git_repo(td: str, name: str) -> Path:
    root = Path(td) / name
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=root, check=True)
    (root / "README.md").write_text("scratch\n")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True)
    return root


def _fake_run_ok(orig_run):
    def fake_run(cmd, **kw):
        if cmd[0] != "claude":
            return orig_run(cmd, **kw)
        text = '{"answer": "판단 결과", "confidence": "high", "caveats": []}'
        payload = json.dumps({"result": text, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    return fake_run


def _fake_run_no_json(orig_run):
    def fake_run(cmd, **kw):
        if cmd[0] != "claude":
            return orig_run(cmd, **kw)
        text = "판단 JSON 없이 끝남"
        payload = json.dumps({"result": text, "is_error": False})
        return subprocess.CompletedProcess(cmd, 0, stdout=payload, stderr="")
    return fake_run


class ConsultTraceRootBase(unittest.TestCase):
    def setUp(self):
        self._orig_run = spawn.subprocess.run
        self._orig_plugin_dirs = spawn.plugin_dirs
        self._orig_core_plugin_dirs = spawn.core_plugin_dirs
        self.addCleanup(setattr, spawn.subprocess, "run", self._orig_run)
        self.addCleanup(setattr, spawn, "plugin_dirs", self._orig_plugin_dirs)
        self.addCleanup(setattr, spawn, "core_plugin_dirs", self._orig_core_plugin_dirs)
        spawn.plugin_dirs = lambda role, spec: [Path("/fake/plugin")]
        spawn.core_plugin_dirs = lambda: []


class ConsultTraceRootTargetRepo(ConsultTraceRootBase):
    """(1) `-C <target>` anchors trace + commit at the target repo."""

    def test_trace_and_commit_land_in_target_repo_no_issue(self):
        with tempfile.TemporaryDirectory() as td:
            target = _git_repo(td, "target")
            spawn.subprocess.run = _fake_run_ok(self._orig_run)

            verdict = spawn.consult_cmd("requirements-engineering", "질문", issue=None, cwd=str(target))

            self.assertEqual(verdict["answer"], "판단 결과")
            trace = target / "docs" / "reports" / "consult-log.md"
            self.assertTrue(trace.exists())
            self.assertIn("outcome='ok:", trace.read_text())
            status = subprocess.run(["git", "-C", str(target), "status", "--porcelain"],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout.strip(), "", "trace commit should leave a clean tree")
            log = subprocess.run(["git", "-C", str(target), "log", "-1", "--format=%s"],
                                 capture_output=True, text=True, check=True)
            self.assertIn("consult-trace (ok)", log.stdout)
            # plugin repo must NOT have received the trace line
            plugin_trace = ROOT / "docs" / "reports" / "consult-log.md"
            if plugin_trace.exists():
                self.assertNotIn(str(target), plugin_trace.read_text())

    def test_trace_and_commit_land_under_target_repo_issue_tree(self):
        with tempfile.TemporaryDirectory() as td:
            target = _git_repo(td, "target")
            spawn.subprocess.run = _fake_run_ok(self._orig_run)

            spawn.consult_cmd("requirements-engineering", "질문", issue=9999, cwd=str(target))

            trace = target / "docs" / "issue-9999" / "reports" / "consult-log.md"
            self.assertTrue(trace.exists())
            status = subprocess.run(["git", "-C", str(target), "status", "--porcelain"],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout.strip(), "")


class ConsultTraceRootNoTarget(ConsultTraceRootBase):
    """(2) no explicit target keeps anchoring at the plugin repo (no regression)."""

    def test_no_cwd_anchors_at_plugin_root(self):
        self.assertEqual(spawn._consult_trace_path(None, None),
                         ROOT / "docs" / "reports" / "consult-log.md")
        self.assertEqual(spawn._consult_trace_path(9999, None),
                         ROOT / "docs" / "issue-9999" / "reports" / "consult-log.md")
        self.assertEqual(spawn._panel_record_path(None, "q", None),
                         ROOT / "docs" / "reports" / "panel" / "q.md")


class ConsultTraceRootSharedAnchor(ConsultTraceRootBase):
    """(3) trace path and commit root share one anchor, so relative_to
    cannot raise (the issue's reproduction)."""

    def test_relative_to_does_not_raise_with_target_cwd(self):
        with tempfile.TemporaryDirectory() as td:
            target = _git_repo(td, "target")
            trace_path = spawn._consult_trace_path(None, str(target))
            commit_root = spawn._consult_root(str(target))
            # this is exactly what _commit_consult_trace() does internally
            rel = trace_path.relative_to(commit_root)
            self.assertEqual(str(rel), "docs/reports/consult-log.md")

    def test_consult_with_target_cwd_does_not_raise_or_report_error(self):
        with tempfile.TemporaryDirectory() as td:
            target = _git_repo(td, "target")
            spawn.subprocess.run = _fake_run_ok(self._orig_run)
            # must not raise ValueError from relative_to() and must return
            # a verdict (successful consult, not reported as a failure)
            verdict = spawn.consult_cmd("requirements-engineering", "질문", issue=None, cwd=str(target))
            self.assertIsInstance(verdict, dict)
            self.assertIn("answer", verdict)


class ConsultTraceRootSideFilesAndPanel(ConsultTraceRootBase):
    """(4) raw-failure side files and panel record paths use the same anchor."""

    def test_raw_failure_side_file_lands_in_target_repo(self):
        with tempfile.TemporaryDirectory() as td:
            target = _git_repo(td, "target")
            spawn.subprocess.run = _fake_run_no_json(self._orig_run)

            with self.assertRaises(RuntimeError):
                spawn.consult_cmd("requirements-engineering", "질문", issue=None, cwd=str(target))

            side_dir = target / "docs" / "reports" / "consult-raw-failures"
            self.assertTrue(side_dir.exists())
            self.assertTrue(any(side_dir.iterdir()))
            status = subprocess.run(["git", "-C", str(target), "status", "--porcelain"],
                                    capture_output=True, text=True, check=True)
            self.assertEqual(status.stdout.strip(), "",
                            "raw side file must be committed alongside the trace")

    def test_panel_record_path_anchors_to_target_cwd(self):
        with tempfile.TemporaryDirectory() as td:
            target = _git_repo(td, "target")
            path = spawn._panel_record_path(None, "some-question", str(target))
            self.assertEqual(path, target / "docs" / "reports" / "panel" / "some-question.md")
            self.assertEqual(spawn._consult_root(str(target)), target.resolve())


if __name__ == "__main__":
    unittest.main()
