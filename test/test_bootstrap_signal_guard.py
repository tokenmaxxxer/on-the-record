"""issue #2742: a spawn that never started (operator declined it at the
approval prompt, or the orchestrator's own Bash-tool call timed out mid-
bootstrap) used to be reported by the watchdog as a probable crash — "no
outcome recorded ... process likely died before it could report why" —
and left its cloned workspace, `.spawn-claim`, and `.task.txt` behind
(83-88MB observed live). Nothing died in either case; the caller went
away.

The general case is "the caller went away", not "the operator declined" —
a decline is one instance of it, an orchestrator tool-call timeout is
another, and both arrive at the spawn.py process as the same real signal
(SIGTERM/SIGINT). A genuine crash (SIGKILL/OOM) is not catchable by
Python at all, so it must and does keep producing the old generic line —
that divergence is exactly what tells the two cases apart, per the
issue's must-not (no timeout heuristic; the signal itself is the only
distinguishing evidence).

  python3 -m pytest test/test_bootstrap_signal_guard.py
"""
from __future__ import annotations
import json
import os
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import spawn
import roster


def _wait_for(path: Path, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.02)
    raise AssertionError(f"{path} never appeared — child never reached armed state")


class BootstrapSignalGuardCaughtSignalTest(unittest.TestCase):
    """Real signal delivered to a real forked process — the same
    real-process convention as tests/test_tmp_resource_gc.py's
    `_dead_pid()`, since a mocked call can't stand in for "the OS actually
    interrupted this process mid-syscall"."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        p = mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path)
        p.start()
        self.addCleanup(p.stop)

    def _fork_armed_child(self, work: Path, attempt_id: str, ready: Path) -> int:
        pid = os.fork()
        if pid == 0:
            try:
                armed = spawn._arm_bootstrap_signal_guard(attempt_id)
                armed[0]["cwd"] = str(work)
                ready.write_text("1")
                time.sleep(30)  # a real signal arrives long before this elapses
            except BaseException:
                os._exit(1)
            os._exit(0)
        return pid

    def test_sigterm_mid_bootstrap_reports_caller_departed_and_cleans_up(self):
        work = Path(self._td.name) / "ws"
        work.mkdir()
        (work / "marker").write_text("cloned")
        claim = spawn._spawn_claim_path(str(work))
        claim.write_text("{}")
        task_file = Path(str(work) + ".task.txt")
        task_file.write_text("do the thing")
        ready = Path(self._td.name) / "ready-term"

        pid = self._fork_armed_child(work, "2742:role:1:1", ready)
        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertFalse(work.exists())
        self.assertFalse(claim.exists())
        self.assertFalse(task_file.exists())
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "halted")
        self.assertIn("SIGTERM", outcomes[0]["detail"])
        self.assertIn("not a crash", outcomes[0]["detail"])
        self.assertNotIn("likely died", outcomes[0]["detail"])

    def test_sigint_mid_bootstrap_also_reports_caller_departed(self):
        work = Path(self._td.name) / "ws-int"
        work.mkdir()
        ready = Path(self._td.name) / "ready-int"

        pid = self._fork_armed_child(work, "2742:role:2:2", ready)
        _wait_for(ready)
        os.kill(pid, signal.SIGINT)
        os.waitpid(pid, 0)

        self.assertFalse(work.exists())
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertIn("SIGINT", outcomes[0]["detail"])

    def test_sigkill_mid_bootstrap_records_nothing_and_leaves_workspace(self):
        """The uncatchable case: no Python code runs at all, so nothing is
        recorded and nothing is cleaned up. This is the case that must
        keep producing the old generic line — it is a real, if rare, way
        for a spawn to actually die, and coverage of it must not narrow."""
        work = Path(self._td.name) / "ws-kill"
        work.mkdir()
        (work / "marker").write_text("cloned")
        ready = Path(self._td.name) / "ready-kill"

        pid = self._fork_armed_child(work, "2742:role:3:3", ready)
        _wait_for(ready)
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)

        self.assertTrue(work.exists())  # nothing could run to remove it
        if self.attempts_path.exists():
            events = [json.loads(l) for l in
                      self.attempts_path.read_text(encoding="utf-8").splitlines()]
            self.assertFalse(any(e.get("event") == "spawn_attempt_outcome"
                                  for e in events))

    def test_disarmed_after_session_log_survives_sigterm_untouched(self):
        """Once bootstrap succeeds (`_record_spawn_outcome(..., "session-
        log", ...)` already written) the guard must be off — a signal
        arriving after that point is the existing dead-entry watchdog's
        job, not this one's, and must never delete a workspace a real
        session may now be using."""
        work = Path(self._td.name) / "ws-live"
        work.mkdir()
        (work / "marker").write_text("session running")
        ready = Path(self._td.name) / "ready-live"
        attempt_id = "2742:role:4:4"

        def _child():
            armed = spawn._arm_bootstrap_signal_guard(attempt_id)
            armed[0]["cwd"] = str(work)
            spawn._record_spawn_outcome(attempt_id, "session-log", "/dev/null")
            spawn._disarm_bootstrap_signal_guard(armed)
            ready.write_text("1")
            time.sleep(30)

        pid = os.fork()
        if pid == 0:
            try:
                _child()
            except BaseException:
                os._exit(1)
            os._exit(0)
        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertTrue(work.exists())  # default SIGTERM: process ends, workspace untouched
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "session-log")


class BootstrapSignalGuardReviewGapsTest(unittest.TestCase):
    """PR #2782 came back CHANGES with two live gaps in the deletion path,
    both found by fault injection rather than timing luck (independent
    verification record, issue #2742). These reproduce each by the same
    means: force the exact window the review named, not a race and hope."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        p = mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path)
        p.start()
        self.addCleanup(p.stop)

    def test_signal_during_clone_removes_partial_workspace(self):
        """Gap 1: `_bootstrap_signal_guard[0]['cwd']` used to be populated
        only *after* `issue_workspace()` returned, and that call runs a
        real git clone/fetch. Fault-inject a slow clone (`_run_net`
        patched to create the target dir, signal readiness, then block)
        and confirm a signal landing squarely inside that window is still
        cleaned up -- proving `cwd` is now known to the handler before the
        clone, not after."""
        src = Path(self._td.name) / "src-repo"
        src.mkdir()
        subprocess.run(["git", "init", "-q", str(src)], check=True)
        subprocess.run(["git", "-C", str(src), "remote", "add", "origin",
                        "https://github.com/acme/widget.git"], check=True)
        work_base = Path(self._td.name) / "work-base"
        work_base.mkdir()
        ready = Path(self._td.name) / "ready-clone"
        issue, skill, attempt_id = 2742, "clonefault", "2742:role:5:5"

        with mock.patch.object(spawn, "_workspace_base", lambda: work_base):
            _, expected_target = spawn._workspace_target_path(
                str(src), issue, skill)
        self.assertIsNotNone(expected_target)
        expected_work = Path(expected_target)

        def _slow_run_net(cmd, desc, timeout=None):
            target_dir = Path(cmd[-1])
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "partial-marker").write_text("clone in progress")
            ready.write_text("1")
            time.sleep(30)  # a real signal arrives long before this elapses
            return subprocess.CompletedProcess(cmd, 0, "", "")

        patches = [
            mock.patch.object(spawn, "_workspace_base", lambda: work_base),
            mock.patch.object(spawn, "_run_net", _slow_run_net),
        ]

        pid = os.fork()
        if pid == 0:
            for p in patches:
                p.start()
            try:
                armed = spawn._arm_bootstrap_signal_guard(attempt_id)
                # the exact call site under test (_spawn_one uses this same
                # helper) -- not a hand-copy of the pattern.
                spawn._create_workspace_with_signal_guard(
                    str(src), issue, skill, armed)
            except BaseException:
                os._exit(1)
            os._exit(0)

        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertFalse(expected_work.exists(),
                          f"partial clone at {expected_work} survived a "
                          f"signal that landed mid-clone")
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "halted")
        self.assertIn("SIGTERM", outcomes[0]["detail"])
        self.assertIn(str(expected_work), outcomes[0]["detail"])

    def test_signal_during_adhoc_clone_also_removes_partial_workspace(self):
        """Gap 1 covers both `issue_workspace()` call sites in `_spawn_one`,
        not just the issue-scoped one: an adhoc (`issue is None`) spawn
        used to call `issue_workspace()` directly, never routing through
        `_create_workspace_with_signal_guard()` at all -- meaning the
        guard's `cwd` stayed `None` for the entire adhoc bootstrap, not
        just during the clone. Prove the adhoc call site is now wired the
        same way as the issue-scoped one."""
        src = Path(self._td.name) / "src-repo-adhoc"
        src.mkdir()
        subprocess.run(["git", "init", "-q", str(src)], check=True)
        subprocess.run(["git", "-C", str(src), "remote", "add", "origin",
                        "https://github.com/acme/adhocwidget.git"], check=True)
        work_base = Path(self._td.name) / "work-base-adhoc"
        work_base.mkdir()
        ready = Path(self._td.name) / "ready-adhoc-clone"
        target_marker = Path(self._td.name) / "adhoc-target-path"
        skill = "adhocclonefault"

        def _slow_run_net(cmd, desc, timeout=None):
            target_dir = Path(cmd[-1])
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "partial-marker").write_text("clone in progress")
            ready.write_text("1")
            time.sleep(30)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        patches = [
            mock.patch.object(spawn, "_workspace_base", lambda: work_base),
            mock.patch.object(spawn, "_run_net", _slow_run_net),
        ]

        pid = os.fork()
        if pid == 0:
            for p in patches:
                p.start()
            try:
                attempt_id = f"None:{skill}:{os.getpid()}:1"
                armed = spawn._arm_bootstrap_signal_guard(attempt_id)
                _, target = spawn._workspace_target_path(str(src), None, skill)
                target_marker.write_text(target)
                # the exact adhoc call site under test (issue=None).
                spawn._create_workspace_with_signal_guard(
                    str(src), None, skill, armed)
            except BaseException:
                os._exit(1)
            os._exit(0)

        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        expected_work = Path(target_marker.read_text())
        self.assertFalse(expected_work.exists(),
                          f"partial adhoc clone at {expected_work} survived "
                          f"a signal that landed mid-clone")
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "halted")

    def test_adhoc_leftover_at_target_path_is_wiped_not_preserved(self):
        """Second blind review's finding: `_workspace_target_is_fresh()`
        treats an adhoc target as fresh even when it already has a `.git`
        -- unlike the issue-scoped reuse case, because `issue_workspace()`
        itself documents (issue #2293) that an adhoc leftover at the
        pid-keyed path must never be silently inherited; it is wiped
        unconditionally before the fresh clone. Verify that claim by
        fault-injecting a signal while a real leftover already sits at the
        deterministic adhoc target -- the interrupted path must match what
        `issue_workspace()` would have done anyway (wipe), not preserve it
        like the issue-scoped reuse branch correctly does."""
        src = Path(self._td.name) / "src-repo-adhoc-leftover"
        src.mkdir()
        subprocess.run(["git", "init", "-q", str(src)], check=True)
        subprocess.run(["git", "-C", str(src), "remote", "add", "origin",
                        "https://github.com/acme/adhocleftover.git"], check=True)
        work_base = Path(self._td.name) / "work-base-adhoc-leftover"
        work_base.mkdir()
        ready = Path(self._td.name) / "ready-adhoc-leftover"
        target_marker = Path(self._td.name) / "adhoc-leftover-target-path"
        skill = "adhocleftoverfault"

        def _slow_run_net(cmd, desc, timeout=None):
            ready.write_text("1")
            time.sleep(30)
            return subprocess.CompletedProcess(cmd, 0, "", "")

        patches = [
            mock.patch.object(spawn, "_workspace_base", lambda: work_base),
            mock.patch.object(spawn, "_run_net", _slow_run_net),
        ]

        pid = os.fork()
        if pid == 0:
            for p in patches:
                p.start()
            try:
                _, target = spawn._workspace_target_path(str(src), None, skill)
                target_marker.write_text(target)
                leftover = Path(target)
                leftover.mkdir(parents=True)
                (leftover / ".git").mkdir()
                (leftover / "uncommitted.txt").write_text(
                    "stale leftover from a crashed prior adhoc spawn "
                    "(only reachable in practice via pid reuse)")
                attempt_id = f"None:{skill}:{os.getpid()}:2"
                armed = spawn._arm_bootstrap_signal_guard(attempt_id)
                spawn._create_workspace_with_signal_guard(
                    str(src), None, skill, armed)
            except BaseException:
                os._exit(1)
            os._exit(0)

        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        expected_work = Path(target_marker.read_text())
        self.assertFalse(expected_work.exists(),
                          "adhoc leftover with real content survived a "
                          "signal -- issue_workspace() itself would have "
                          "wiped it unconditionally had the process not "
                          "been interrupted")

    def test_signal_after_session_log_before_disarm_does_not_delete_workspace(self):
        """Gap 2 (the serious one): `_disarm_bootstrap_signal_guard()`
        resets SIGTERM/SIGINT with two separate, non-atomic
        `signal.signal()` calls. Fault-inject the exact gap by never
        calling disarm at all before the signal arrives -- the handler is
        still installed, exactly as it is in the live gap between the two
        `signal.signal()` calls, and this is the moment right after a real
        session's session-log outcome was recorded. Before the fix this
        deleted the live workspace and left no trace (`_record_spawn_outcome`
        dedupes by attempt_id, so the second call was a silent no-op)."""
        work = Path(self._td.name) / "ws-race"
        work.mkdir()
        (work / "marker").write_text("session running")
        ready = Path(self._td.name) / "ready-race"
        attempt_id = "2742:role:6:6"

        def _child():
            armed = spawn._arm_bootstrap_signal_guard(attempt_id)
            armed[0]["cwd"] = str(work)
            spawn._record_spawn_outcome(attempt_id, "session-log", "/dev/null")
            # Deliberately do NOT disarm -- reproduces the live gap: a
            # signal here still hits the old handler.
            ready.write_text("1")
            time.sleep(30)

        pid = os.fork()
        if pid == 0:
            try:
                _child()
            except BaseException:
                os._exit(1)
            os._exit(0)
        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertTrue(work.exists(),
                         "handler deleted a workspace already recorded as "
                         "session-log — the exact invisible-deletion bug")
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "session-log")

    def test_signal_during_reuse_fetch_does_not_delete_prior_work(self):
        """Regression found by an independent blind review of the gap-1 fix
        itself: pre-populating the guard's `cwd` with the best-effort
        target path is only safe when that target is about to be a fresh
        clone. If the target already has real prior work at it (an
        issue-scoped respawn reusing a previous attempt's checkout --
        `issue_workspace()`'s reuse branch only fetches, never re-clones),
        blindly pre-populating would make a signal during that fetch delete
        someone else's real, non-partial work. Fault-inject a signal
        landing during the reuse-branch's `_fetch_or_halt()` and confirm
        the prior work survives."""
        src = Path(self._td.name) / "src-repo2"
        src.mkdir()
        subprocess.run(["git", "init", "-q", str(src)], check=True)
        subprocess.run(["git", "-C", str(src), "config", "user.email", "t@t"], check=True)
        subprocess.run(["git", "-C", str(src), "config", "user.name", "t"], check=True)
        (src / "README").write_text("seed")
        subprocess.run(["git", "-C", str(src), "add", "README"], check=True)
        subprocess.run(["git", "-C", str(src), "commit", "-q", "-m", "seed"], check=True)
        subprocess.run(["git", "-C", str(src), "remote", "add", "origin",
                        "https://github.com/acme/widget2.git"], check=True)
        work_base = Path(self._td.name) / "work-base2"
        work_base.mkdir()
        issue, skill, attempt_id = 2742, "reusefault", "2742:role:7:7"

        with mock.patch.object(spawn, "_workspace_base", lambda: work_base):
            _, target = spawn._workspace_target_path(str(src), issue, skill)
        work = Path(target)
        # Simulate a previous attempt's real, non-partial checkout already
        # sitting at the deterministic target path -- exactly what the
        # reuse branch of issue_workspace() finds and only fetches.
        subprocess.run(["git", "clone", "-q", str(src), str(work)], check=True)
        subprocess.run(["git", "-C", str(work), "remote", "set-url", "origin",
                        "https://github.com/acme/widget2.git"], check=True)
        (work / "real-work.txt").write_text("uncommitted WIP from a prior attempt")
        ready = Path(self._td.name) / "ready-reuse"

        def _slow_fetch_or_halt(root, label, after=None):
            ready.write_text("1")
            time.sleep(30)  # a real signal arrives long before this elapses

        patches = [
            mock.patch.object(spawn, "_workspace_base", lambda: work_base),
            mock.patch.object(spawn, "_fetch_or_halt", _slow_fetch_or_halt),
        ]

        pid = os.fork()
        if pid == 0:
            for p in patches:
                p.start()
            try:
                armed = spawn._arm_bootstrap_signal_guard(attempt_id)
                spawn._create_workspace_with_signal_guard(
                    str(src), issue, skill, armed)
            except BaseException:
                os._exit(1)
            os._exit(0)

        _wait_for(ready)
        os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

        self.assertTrue(work.exists())
        self.assertTrue((work / "real-work.txt").exists(),
                         "reused workspace with real prior work was deleted "
                         "by a signal landing during its fetch refresh")
        events = [json.loads(l) for l in
                  self.attempts_path.read_text(encoding="utf-8").splitlines()]
        outcomes = [e for e in events if e.get("event") == "spawn_attempt_outcome"]
        self.assertEqual(len(outcomes), 1)
        self.assertEqual(outcomes[0]["outcome"], "halted")
        self.assertNotIn("removing partial workspace", outcomes[0]["detail"])

    def test_signal_during_self_reuse_never_targets_callers_own_checkout(self):
        """Same regression class, narrower case: when `cwd` already IS the
        deterministic target path (`issue_workspace()`'s self-reuse branch,
        `src == work`), the caller's own checkout must never be treated as
        this attempt's to delete -- not before `issue_workspace()` (it's
        not a fresh-clone target) and not after (the return value IS the
        caller's own directory)."""
        work_base = Path(self._td.name) / "work-base3"
        work_base.mkdir()
        with mock.patch.object(spawn, "_workspace_base", lambda: work_base):
            # A repo whose slug already matches its own deterministic
            # target path, so issue_workspace() takes the self-reuse
            # early-return (`src == work.resolve()`) instead of cloning.
            issue, skill = 2742, "selfreuse"
            probe_src = Path(self._td.name) / "probe"
            probe_src.mkdir()
            subprocess.run(["git", "init", "-q", str(probe_src)], check=True)
            subprocess.run(["git", "-C", str(probe_src), "remote", "add",
                            "origin", "https://github.com/acme/probe.git"],
                           check=True)
            _, target = spawn._workspace_target_path(str(probe_src), issue, skill)
        work = Path(target)
        work.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", str(probe_src), str(work)], check=True)
        subprocess.run(["git", "-C", str(work), "remote", "set-url", "origin",
                        "https://github.com/acme/probe.git"], check=True)

        with mock.patch.object(spawn, "_workspace_base", lambda: work_base), \
             mock.patch.object(spawn, "_fetch_or_halt", lambda *a, **k: None), \
             mock.patch.object(spawn, "_write_skill_sidecar", lambda *a, **k: None), \
             mock.patch.object(spawn, "_set_origin_head", lambda *a, **k: None):
            attempt_id = "2742:role:8:8"
            armed = spawn._arm_bootstrap_signal_guard(attempt_id)
            result = spawn._create_workspace_with_signal_guard(
                str(work), issue, skill, armed)
            self.assertEqual(str(Path(result).resolve()), str(work.resolve()))
            self.assertIsNone(armed[0]["cwd"],
                               "guard was armed against the caller's own "
                               "checkout via the self-reuse return path")
            spawn._disarm_bootstrap_signal_guard(armed)


class SpawnAttemptSweepReportsCallerDepartedDistinctlyTest(unittest.TestCase):
    """End-to-end through the watchdog sweep (issue #2742 acceptance bullet
    2): the SIGTERM-recorded outcome and a genuinely-dead (no outcome)
    attempt must produce different `[spawn-attempt]` lines."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path),
            mock.patch.object(spawn, "ledger_write", lambda ev: None),
            mock.patch.object(spawn, "ledger_check_and_stamp", lambda *a, **k: True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_declined_and_genuinely_dead_produce_different_lines(self):
        now = time.time()
        with self.attempts_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": "a1",
                                  "issue": 2741, "skill": "declined-role",
                                  "pid": 111, "cwd": "/tmp/does-not-matter-a",
                                  "ts": now - 5}) + "\n")
            fh.write(json.dumps({"event": "spawn_attempt_outcome",
                                  "attempt_id": "a1", "outcome": "halted",
                                  "detail": "caller departed before bootstrap "
                                            "finished (received SIGTERM) — "
                                            "this is not a crash, no session "
                                            "ever started",
                                  "ts": now - 4}) + "\n")
            fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": "a2",
                                  "issue": 2741, "skill": "killed-role",
                                  "pid": 222, "cwd": "/tmp/does-not-matter-b",
                                  "ts": now - (roster.SPAWN_ATTEMPT_GRACE_SEC + 30)}) + "\n")

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={}, now=now)

        self.assertEqual(count, 2)
        lines = [str(c.args[0]) for c in mocked_print.call_args_list]
        declined_line = next(l for l in lines if "declined-role" in l)
        killed_line = next(l for l in lines if "killed-role" in l)
        self.assertIn("SIGTERM", declined_line)
        self.assertIn("not a crash", declined_line)
        self.assertNotIn("likely died", declined_line)
        self.assertIn("likely died", killed_line)
        self.assertNotIn("SIGTERM", killed_line)
        self.assertNotEqual(declined_line, killed_line)


if __name__ == "__main__":
    unittest.main()
