"""Issue #2904 (rescoped 2026-08-31, issuecomment-5472355431): the
orchestrator must track what it spawned, and `gh` only shows a session
after it opens a PR. A session working for 15 minutes with no commit and
no PR is invisible to any `gh`-based check but its workspace already shows
`git status --porcelain` changes and, once one exists, its own record
file. `watchdog._live_session_workspace_summary()` (watchdog.py) reads
that local git state -- no `gh` call, no new polling loop -- and
`diagnose_health()`'s HEALTHY branch folds it into the same per-tick
`[poll-report] {key}: HEALTHY — ...` line the watchdog already prints for
every live roster entry, so a session doing nothing yet reports that
explicitly (empty state, not silence) and a later file touch changes the
line's text -- which `poll_heartbeat_delta.py`'s existing per-key diff
already re-emits on change and suppresses on no-change, with zero new
plumbing on the emission side."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn


def _tool_use_line(ts, name, **input_kwargs):
    return json.dumps({
        "type": "assistant", "timestamp": ts,
        "message": {"content": [
            {"type": "tool_use", "name": name, "input": input_kwargs}]},
    })


def _git(cwd, *a):
    return subprocess.run(["git", "-C", str(cwd), *a],
                           capture_output=True, text=True, check=True)


class WorkspaceSummaryTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.work = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        _git(self.work, "init", "-q")
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")

    def test_untouched_workspace_reports_explicit_empty_state(self):
        summary = watchdog._live_session_workspace_summary(str(self.work))
        self.assertEqual(summary, "손댄 파일 없음")

    def test_touched_files_are_named_not_just_counted(self):
        (self.work / "spawn.py").write_text("x")
        (self.work / "watchdog.py").write_text("y")
        summary = watchdog._live_session_workspace_summary(str(self.work))
        self.assertIn("2건", summary)
        self.assertIn("spawn.py", summary)
        self.assertIn("watchdog.py", summary)
        self.assertIn("기록 아직 없음", summary)

    def test_record_file_touch_is_named_as_started(self):
        record_dir = self.work / "docs" / "issue-2904" / "reports"
        record_dir.mkdir(parents=True)
        (record_dir / "x.md").write_text("# draft")
        summary = watchdog._live_session_workspace_summary(str(self.work))
        self.assertIn("기록 시작함", summary)
        self.assertIn("docs/issue-2904/reports/x.md", summary)

    def test_non_git_directory_fails_safe_not_raise(self):
        empty = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(empty)]))
        summary = watchdog._live_session_workspace_summary(str(empty))
        self.assertIn("실패", summary)


class DiagnoseHealthIncludesWorkspaceSummaryTest(unittest.TestCase):
    """Integration: the existing HEALTHY branch of `diagnose_health()` --
    the one already printed every tick for every live roster entry -- now
    carries the workspace summary in its `detail`, not a separate line."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.work = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        _git(self.work, "init", "-q")
        _git(self.work, "config", "user.email", "t@example.com")
        _git(self.work, "config", "user.name", "t")
        (self.work / "a.txt").write_text("1")
        _git(self.work, "add", "a.txt")
        _git(self.work, "commit", "-q", "-m", "c1")

    def _healthy(self):
        entry = {"pid": os.getpid(), "work": str(self.work), "log": None,
                 "issue": 2904, "skill": "demo"}
        return watchdog.diagnose_health("issue-2904/demo", entry,
                                        anomalies=[], root=self.work)

    def test_untouched_session_reports_empty_state_not_silence(self):
        health = self._healthy()
        self.assertEqual(health["state"], "HEALTHY")
        self.assertIn("손댄 파일 없음", health["detail"])

    def test_in_progress_file_touch_changes_the_reported_detail(self):
        before = self._healthy()["detail"]
        (self.work / "spawn.py").write_text("x")
        after = self._healthy()["detail"]
        self.assertNotEqual(before, after)
        self.assertIn("spawn.py", after)

    def test_dead_pid_never_gets_a_running_workspace_summary(self):
        """Source-of-truth check the issue explicitly asks for: a dead pid
        must never be reported as running. `_alive(pid)` (raw `os.kill`)
        gates entry into the branch that computes the workspace summary at
        all -- a dead entry takes the completion/dead-scan path instead
        (see `test_reconcile_crash_verdict_race.py`), never this one."""
        entry = {"pid": 999999999, "work": str(self.work), "log": None,
                 "issue": 2904, "skill": "demo"}
        health = watchdog.diagnose_health("issue-2904/demo", entry, root=self.work)
        self.assertNotEqual(health["state"], "HEALTHY")
        self.assertNotIn("손댄 파일", health["detail"])


class DeltaSuppressionForWorkspaceProgressTest(unittest.TestCase):
    """No new plumbing needed on the emission side: `poll_heartbeat_delta.py`
    already diffs each `[poll-report] {key}: ...` line against its prior
    tick's text for that same key -- unchanged detail (same files touched)
    stays quiet, changed detail (a new file touched) re-emits, matching the
    issue's must-not ("no general increase in heartbeat volume when
    nothing changed") and its acceptance ("mid-flight state is visible")
    at the same time."""

    def _run_delta(self, state_path, text, now):
        r = subprocess.run(
            ["python3", str(ROOT / "on-the-record/monitors/poll_heartbeat_delta.py"),
             str(state_path), str(now)],
            env={**os.environ, "POLL_HEARTBEAT_TEXT": text},
            capture_output=True, text=True)
        return r.stdout

    def test_unchanged_workspace_progress_line_suppressed_next_tick(self):
        tmp = Path(tempfile.mkdtemp())
        state_path = tmp / "state.json"
        line = "[poll-report] issue-2904/demo: HEALTHY — issue-2904/demo: 최근 로그 성장, RUNNING — 손댄 파일 없음"
        out1 = self._run_delta(state_path, line, 1000)
        self.assertIn("손댄 파일 없음", out1)
        out2 = self._run_delta(state_path, line, 1010)
        self.assertEqual(out2, "")

    def test_new_file_touched_reemits_the_changed_line(self):
        tmp = Path(tempfile.mkdtemp())
        state_path = tmp / "state.json"
        line1 = "[poll-report] issue-2904/demo: HEALTHY — issue-2904/demo: 최근 로그 성장, RUNNING — 손댄 파일 없음"
        self._run_delta(state_path, line1, 1000)
        line2 = "[poll-report] issue-2904/demo: HEALTHY — issue-2904/demo: 최근 로그 성장, RUNNING — 손댄 파일 1건: spawn.py, 기록 아직 없음"
        out2 = self._run_delta(state_path, line2, 1010)
        self.assertIn("spawn.py", out2)


class LastToolActivitySummaryTest(unittest.TestCase):
    """Issue #2904, second correction (issuecomment-5472429696): file diff
    is the result, the tool call is the act -- the same set of dirty files
    stays dirty whether the session spent the last two minutes actively
    grepping/reading/editing or doing nothing at all, so
    `_live_session_workspace_summary()` alone reproduces the exact defect
    this issue is about. `_last_tool_activity_summary()` reads the
    session's own transcript log -- the same file `watchdog_check_one()`
    already scans incrementally for anomaly detection -- for its last
    `tool_use` block, and reports it with an ABSOLUTE timestamp rather
    than a relative age specifically so an unchanged last-tool-call
    produces byte-identical text tick to tick (relative "Ns ago" text
    would defeat delta-suppression by changing every single tick even
    when nothing new happened)."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self._tmpdir.name) / "session.log"
        self.addCleanup(self._tmpdir.cleanup)

    def test_missing_log_reports_explicit_empty_state(self):
        summary = watchdog._last_tool_activity_summary(self.log_path)
        self.assertEqual(summary, "도구 호출 로그 없음")

    def test_log_with_no_tool_use_reports_explicit_empty_state(self):
        self.log_path.write_text('{"type": "assistant", "timestamp": "2026-08-31T00:58:00Z", "message": {"content": [{"type": "text", "text": "thinking"}]}}\n')
        summary = watchdog._last_tool_activity_summary(self.log_path)
        self.assertEqual(summary, "도구 호출 기록 없음")

    def test_names_the_tool_and_its_target_and_an_absolute_timestamp(self):
        self.log_path.write_text(
            _tool_use_line("2026-08-31T00:59:13Z", "Edit", file_path="watchdog.py") + "\n")
        summary = watchdog._last_tool_activity_summary(self.log_path)
        self.assertIn("Edit", summary)
        self.assertIn("watchdog.py", summary)
        self.assertIn("00:59:13", summary)

    def test_investigating_vs_stalled_distinguished_by_a_new_tool_call(self):
        """The exact scenario in the issue's own live demonstration: two
        minutes of unchanged `git status` output that were actually full
        of grep/Read/Edit/test activity. A later tool call must change
        this summary even though the workspace-level file set (checked
        separately) does not."""
        self.log_path.write_text(
            _tool_use_line("2026-08-31T00:58:20Z", "Grep", pattern="roster_watchdog") + "\n")
        first = watchdog._last_tool_activity_summary(self.log_path)
        with self.log_path.open("a") as f:
            f.write(_tool_use_line("2026-08-31T00:59:48Z", "Bash",
                                    command="python3 -m pytest test/x.py") + "\n")
        second = watchdog._last_tool_activity_summary(self.log_path)
        self.assertNotEqual(first, second)
        self.assertIn("Bash", second)

    def test_unchanged_log_produces_byte_identical_text_not_a_ticking_age(self):
        """This is the delta-suppression guarantee itself: call the
        function twice against the exact same (unappended) log and
        require byte-identical output -- a relative-age implementation
        would fail this by construction."""
        self.log_path.write_text(
            _tool_use_line("2026-08-31T00:58:20Z", "Read", file_path="spawn.py") + "\n")
        first = watchdog._last_tool_activity_summary(self.log_path)
        second = watchdog._last_tool_activity_summary(self.log_path)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
