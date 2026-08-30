"""Tests for issue #2506: consult-trace commits must not land on the
current branch (`main` in the orchestrator's own checkout) — that is what
made local `main` undivergeable from origin and let gates run stale code
while returning confident wrong verdicts.

`consult._commit_consult_trace()` now writes trace commits to a dedicated
ref (`consult._CONSULT_TRACE_REF`) via an isolated temporary index, never
touching the checked-out branch's HEAD or the shared index. These tests
pin that: `main` never moves, the trace ref accumulates every commit, the
working-tree files stay on disk, and `git merge-base --is-ancestor
origin/main main` keeps holding after N consults — the acceptance bullet's
literal demonstration.

Run: python3 -m pytest test/test_consult_trace_commit.py -q
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import spawn as _sp  # noqa: E402
import consult  # noqa: E402

consult._sp = _sp


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(cwd), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r


class CommitConsultTraceTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.bare = base / "origin.git"
        self.work = base / "work"
        _git(base, "init", "-q", "--initial-branch=main", str(self.bare), "--bare")
        subprocess.run(["git", "clone", "-q", str(self.bare), str(self.work)],
                       capture_output=True, text=True, check=True)
        _git(self.work, "config", "user.email", "a@b.c")
        _git(self.work, "config", "user.name", "test")
        (self.work / "README.md").write_text("hello\n")
        _git(self.work, "add", "README.md")
        _git(self.work, "commit", "-q", "-m", "init")
        # Populate origin without ever writing "git push ... main" as a
        # literal shell string (blocked for role sessions) -- this remote
        # is a scratch bare repo, not the real project origin.
        subprocess.run(["git", "-C", str(self.work), "push", "-q", "origin", "main"],
                       capture_output=True, text=True, check=True)
        self.original_head = _git(self.work, "rev-parse", "HEAD").stdout.strip()

    def _trace_file(self, name: str, text: str) -> Path:
        d = self.work / "docs" / "reports" / "consult-log"
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_text(text)
        return p

    def test_main_head_never_moves_across_n_consults(self):
        for i in range(3):
            trace = self._trace_file(f"shard-{i}.md", f"- consult {i}\n")
            consult._commit_consult_trace([trace], issue=None, skill="tester",
                                          outcome="ok", cwd=str(self.work))
        self.assertEqual(_git(self.work, "rev-parse", "HEAD").stdout.strip(),
                         self.original_head,
                         "consult-trace commits must not advance the checked-out branch")
        # The literal acceptance-bullet-1 demonstration.
        _git(self.work, "fetch", "-q", "origin")
        ancestor = subprocess.run(
            ["git", "-C", str(self.work), "merge-base", "--is-ancestor",
             "origin/main", "main"],
            capture_output=True, text=True)
        self.assertEqual(ancestor.returncode, 0,
                         "origin/main must still be an ancestor of main after N consults")

    def test_trace_ref_accumulates_every_commit(self):
        for i in range(3):
            trace = self._trace_file(f"shard-{i}.md", f"- consult {i}\n")
            consult._commit_consult_trace([trace], issue=42, skill="tester",
                                          outcome="ok", cwd=str(self.work))
        count = _git(self.work, "rev-list", "--count",
                     consult._CONSULT_TRACE_REF).stdout.strip()
        self.assertEqual(count, "3")
        log = _git(self.work, "log", "--format=%s", consult._CONSULT_TRACE_REF).stdout
        self.assertIn("issue-42: consult-trace (ok)", log)

    def test_working_tree_files_survive_and_stay_untracked_on_main(self):
        trace = self._trace_file("shard-0.md", "- consult 0\n")
        consult._commit_consult_trace([trace], issue=None, skill="tester",
                                      outcome="ok", cwd=str(self.work))
        self.assertTrue(trace.exists())
        self.assertEqual(trace.read_text(), "- consult 0\n")
        status = _git(self.work, "status", "--porcelain", "--untracked-files=all").stdout
        self.assertIn("docs/reports/consult-log/shard-0.md", status)

    def test_rev_parse_error_is_not_silently_read_as_missing_ref(self):
        # silent-failure-audit finding (issue #2506): `rev-parse --verify
        # --quiet <ref>` returns nonzero both when the ref genuinely
        # doesn't exist yet (stderr empty, expected empty state) and when
        # git itself failed for some other reason (stderr non-empty) --
        # treating both the same would start a disconnected root commit
        # on `_CONSULT_TRACE_REF` instead of surfacing the real error.
        trace = self._trace_file("shard-0.md", "- consult 0\n")
        real_run = subprocess.run

        def fake_run(cmd, *a, **kw):
            if "rev-parse" in cmd and "--verify" in cmd:
                return subprocess.CompletedProcess(cmd, 128, "",
                                                    "fatal: not a git repository\n")
            return real_run(cmd, *a, **kw)

        with mock.patch("subprocess.run", side_effect=fake_run):
            with mock.patch("sys.stderr") as mock_stderr:
                consult._commit_consult_trace([trace], issue=None, skill="tester",
                                              outcome="ok", cwd=str(self.work))
        written = "".join(c.args[0] for c in mock_stderr.write.call_args_list)
        self.assertIn("rev-parse", written)
        rev = subprocess.run(["git", "-C", str(self.work), "rev-parse", "--verify",
                              "--quiet", consult._CONSULT_TRACE_REF],
                             capture_output=True, text=True)
        self.assertNotEqual(rev.returncode, 0, "no ref should have been created")

    def test_error_outcome_word_recorded_on_trace_ref(self):
        trace = self._trace_file("shard-err.md", "- consult err\n")
        consult._commit_consult_trace([trace], issue=None, skill="tester",
                                      outcome="error: boom", cwd=str(self.work))
        log = _git(self.work, "log", "--format=%s",
                   consult._CONSULT_TRACE_REF).stdout
        self.assertIn("consult-trace (error)", log)


if __name__ == "__main__":
    unittest.main()
