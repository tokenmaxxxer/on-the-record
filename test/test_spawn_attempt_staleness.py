"""issue #2511: the watchdog's `[spawn-attempt]` sweep used to replay a
`"halted"` outcome's recorded `detail` verbatim on every tick forever (only
gated by the report-cadence ledger, never by whether the blocking condition
still held) — so a spawn-attempt failure that had already been fixed hours
or days earlier kept being reported as if it were still live. This caused a
real misdiagnosis and a duplicate spawn (issue body, 2026-08-26).

The fix classifies each `"halted"` reason into one of five known failure
classes and re-checks that class's actual blocking condition before ever
reporting it again — never elapsed time alone, since a missing tag or a
still-full disk does not fix itself. These tests cover the per-class
re-check (`spawn._halt_condition_cleared`) and the end-to-end sweep
behavior (`roster.spawn_attempt_sweep`): a cleared halt stops being
reported and is marked resolved exactly once; a still-blocked halt keeps
reporting at full volume, now carrying the original attempt's timestamp.

  python3 -m pytest test/test_spawn_attempt_staleness.py
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

import spawn
import roster

sys.path.insert(0, str((Path(spawn.ROOT) / "gates").resolve()))
import requirement_linkage  # noqa: E402
import acceptance_gate  # noqa: E402


def _git_repo(path: Path, origin: str | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    if origin:
        subprocess.run(["git", "remote", "add", "origin", origin],
                        cwd=path, check=True)
    return path


class ClassifyHaltReasonTest(unittest.TestCase):
    def test_requirement_tag_message_classified(self):
        reason = ("이슈 #2379 가 요구 연결이 없다:\n  - x\n  세션을 안 띄운다 ...")
        self.assertEqual(spawn._classify_halt_reason(reason), "requirement-tag")

    def test_acceptance_format_message_classified(self):
        reason = "이슈 #2400 는 phase-2 승인(implementation)을 받았지만 ..."
        self.assertEqual(spawn._classify_halt_reason(reason), "acceptance-format")

    def test_enospc_bytes_message_classified(self):
        reason = "스폰을 거부한다: /a/b 에 여유 공간이 부족하다 (10MB 가용, ...)"
        self.assertEqual(spawn._classify_halt_reason(reason), "enospc")

    def test_enospc_inodes_message_classified(self):
        reason = "스폰을 거부한다: /a/b 에 여유 inode 가 부족하다 (10개 가용, ...)"
        self.assertEqual(spawn._classify_halt_reason(reason), "enospc")

    def test_workspace_origin_mismatch_classified(self):
        reason = ("작업 경로에 다른 레포가 있다 (origin 불일치): /w "
                   "— 기대: https://x, 실제: https://y")
        self.assertEqual(spawn._classify_halt_reason(reason),
                          "workspace-origin-mismatch")

    def test_cwd_invalid_variants_classified(self):
        for reason in (
            "-C 가 존재하지 않는 디렉터리다: foo\n  ...",
            "-C 가 git 레포 안이 아니다: foo\n  ...",
            "-C 가 레포 루트가 아니라 그 하위 디렉터리다: foo\n  ...",
        ):
            self.assertEqual(spawn._classify_halt_reason(reason), "cwd-invalid")

    def test_unrecognized_message_is_unknown(self):
        self.assertEqual(spawn._classify_halt_reason("some other crash"), "unknown")


class HaltConditionClearedCwdInvalidTest(unittest.TestCase):
    def test_still_missing_directory_is_not_cleared(self):
        attempt = {"cwd": "/does/not/exist-issue-2511"}
        self.assertFalse(
            spawn._halt_condition_cleared("cwd-invalid", attempt, ""))

    def test_now_valid_repo_root_is_cleared(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            repo = _git_repo(Path(td) / "repo")
            attempt = {"cwd": str(repo)}
            self.assertTrue(
                spawn._halt_condition_cleared("cwd-invalid", attempt, ""))

    def test_subdirectory_of_a_repo_stays_uncleared(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            repo = _git_repo(Path(td) / "repo")
            sub = repo / "sub"
            sub.mkdir()
            attempt = {"cwd": str(sub)}
            self.assertFalse(
                spawn._halt_condition_cleared("cwd-invalid", attempt, ""))

    def test_missing_cwd_field_is_conservative_not_cleared(self):
        self.assertFalse(spawn._halt_condition_cleared("cwd-invalid", {}, ""))


class HaltConditionClearedEnospcTest(unittest.TestCase):
    def test_still_below_threshold_is_not_cleared(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            reason = f"스폰을 거부한다: {td} 에 여유 공간이 부족하다 (1MB 가용, 임계값 357MB)"
            with mock.patch.dict(os.environ,
                                  {"MUSTER_MIN_FREE_BYTES": str(10 ** 18)}):
                self.assertFalse(
                    spawn._halt_condition_cleared("enospc", {}, reason))

    def test_now_above_threshold_is_cleared(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            reason = f"스폰을 거부한다: {td} 에 여유 공간이 부족하다 (1MB 가용, 임계값 357MB)"
            with mock.patch.dict(os.environ,
                                  {"MUSTER_MIN_FREE_BYTES": "1",
                                   "MUSTER_MIN_FREE_INODES": "1"}):
                self.assertTrue(
                    spawn._halt_condition_cleared("enospc", {}, reason))

    def test_unparseable_reason_is_conservative_not_cleared(self):
        self.assertFalse(
            spawn._halt_condition_cleared("enospc", {}, "garbage"))


class HaltConditionClearedWorkspaceOriginTest(unittest.TestCase):
    def test_mismatch_persists_while_work_dir_still_has_wrong_origin(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = _git_repo(Path(td) / "work", origin="https://github.com/a/wrong")
            reason = (f"작업 경로에 다른 레포가 있다 (origin 불일치): {work} "
                      f"— 기대: https://github.com/a/expected, 실제: https://github.com/a/wrong")
            self.assertFalse(
                spawn._halt_condition_cleared("workspace-origin-mismatch", {}, reason))

    def test_cleared_once_origin_is_fixed_to_match(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = _git_repo(Path(td) / "work", origin="https://github.com/a/wrong")
            subprocess.run(["git", "remote", "set-url", "origin",
                             "https://github.com/a/expected"], cwd=work, check=True)
            reason = (f"작업 경로에 다른 레포가 있다 (origin 불일치): {work} "
                      f"— 기대: https://github.com/a/expected, 실제: https://github.com/a/wrong")
            self.assertTrue(
                spawn._halt_condition_cleared("workspace-origin-mismatch", {}, reason))

    def test_cleared_once_the_conflicting_workspace_dir_is_gone(self):
        """Matches the issue's own observed case: 'halted on an origin
        mismatch for a workspace directory that no longer exists' — that
        specific conflict can never recur once the directory is gone."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work-already-deleted"
            reason = (f"작업 경로에 다른 레포가 있다 (origin 불일치): {work} "
                      f"— 기대: https://github.com/a/expected, 실제: https://github.com/a/wrong")
            self.assertTrue(
                spawn._halt_condition_cleared("workspace-origin-mismatch", {}, reason))


class HaltConditionClearedGhBackedClassesTest(unittest.TestCase):
    """requirement-tag / acceptance-format both delegate to a gh-backed
    gates.<x>.check(root, issue) — mocked here so the test never calls gh."""

    def test_requirement_tag_cleared_once_check_reports_clean(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            attempt = {"issue": 2379, "cwd": td}
            with mock.patch.object(requirement_linkage, "check", return_value=[]):
                self.assertTrue(
                    spawn._halt_condition_cleared("requirement-tag", attempt, "x"))

    def test_requirement_tag_stays_uncleared_while_check_still_flags_it(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            attempt = {"issue": 2379, "cwd": td}
            with mock.patch.object(requirement_linkage, "check",
                                    return_value=["still missing"]):
                self.assertFalse(
                    spawn._halt_condition_cleared("requirement-tag", attempt, "x"))

    def test_acceptance_format_cleared_once_check_reports_clean(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            attempt = {"issue": 2400, "cwd": td}
            with mock.patch.object(acceptance_gate, "check", return_value=[]):
                self.assertTrue(
                    spawn._halt_condition_cleared("acceptance-format", attempt, "x"))

    def test_missing_issue_or_cwd_is_conservative_not_cleared(self):
        with mock.patch.object(requirement_linkage, "check", return_value=[]):
            self.assertFalse(
                spawn._halt_condition_cleared("requirement-tag", {"issue": 2379}, "x"))
            self.assertFalse(
                spawn._halt_condition_cleared("requirement-tag", {"cwd": "/tmp"}, "x"))


class HaltConditionClearedUnknownClassTest(unittest.TestCase):
    def test_unknown_class_never_reports_cleared(self):
        self.assertFalse(
            spawn._halt_condition_cleared("unknown", {"issue": 1, "cwd": "/tmp"}, "x"))


class SpawnAttemptSweepReplayFixTest(unittest.TestCase):
    """End-to-end: the exact live shape from the issue — a `-C` halt that
    was blocking (the given path did not exist), gets fixed, and the next
    sweep tick must stop replaying it as a live halt."""

    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        patches = [
            mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path),
            mock.patch.object(spawn, "ledger_write", lambda ev: None),
            mock.patch.object(spawn, "ledger_check_and_stamp",
                               lambda *a, **k: True),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _write_attempt(self, attempt_id, issue, role, cwd, reason, ts):
        with self.attempts_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": attempt_id,
                                  "issue": issue, "role": role, "pid": 4242,
                                  "cwd": cwd, "ts": ts}) + "\n")
            fh.write(json.dumps({"event": "spawn_attempt_outcome",
                                  "attempt_id": attempt_id, "outcome": "halted",
                                  "detail": reason, "ts": ts}) + "\n")

    def test_live_halt_stops_replaying_once_the_condition_clears(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "not-yet-created"
            reason = (f"-C 가 존재하지 않는 디렉터리다: {missing}\n"
                      f"  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.")
            attempt_ts = time.time() - 3600
            self._write_attempt("2576:orchestrator:1:1", 2576, "orchestrator",
                                 str(missing), reason, attempt_ts)

            # Tick 1: the path still does not exist — reported as a live
            # halt, carrying the original attempt's timestamp.
            count1 = roster.spawn_attempt_sweep(d_all={})
            self.assertEqual(count1, 1)

            # The orchestrator fixes the argument: the path now exists and
            # is a real repo root.
            _git_repo(missing)

            # Tick 2: same recorded reason, but the condition now checks out
            # clear — must NOT be reported as a live halt again.
            with mock.patch("builtins.print") as mocked_print:
                count2 = roster.spawn_attempt_sweep(d_all={})
            self.assertEqual(count2, 0)
            printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
            self.assertIn("RESOLVED", printed)
            self.assertNotIn("spawn halted pre-workspace", printed)

            # Tick 3: fully swept away — nothing left to say about it.
            with mock.patch("builtins.print") as mocked_print:
                count3 = roster.spawn_attempt_sweep(d_all={})
            self.assertEqual(count3, 0)
            self.assertEqual(mocked_print.call_args_list, [])

    def test_still_blocked_halt_keeps_reporting_at_full_volume(self):
        """Non-goal guard: a halt whose condition still holds must never be
        dropped or quieted — it keeps reporting on every tick it's asked."""
        missing = Path("/definitely/not/a/real/path-issue-2511")
        reason = (f"-C 가 존재하지 않는 디렉터리다: {missing}\n"
                  f"  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.")
        attempt_ts = time.time() - 60
        self._write_attempt("2999:role:1:1", 2999, "role", str(missing),
                             reason, attempt_ts)

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count, 1)
        printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn("spawn halted pre-workspace", printed)
        self.assertIn("attempted at", printed)

    def test_report_line_carries_the_original_attempt_timestamp(self):
        missing = Path("/definitely/not/a/real/path-issue-2511-b")
        reason = f"-C 가 존재하지 않는 디렉터리다: {missing}\n  ..."
        attempt_ts = 1_700_000_000.0  # 2023-11-14T22:13:20Z
        self._write_attempt("3000:role:1:1", 3000, "role", str(missing),
                             reason, attempt_ts)

        with mock.patch("builtins.print") as mocked_print:
            roster.spawn_attempt_sweep(d_all={})
        printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn(roster._iso(attempt_ts), printed)


if __name__ == "__main__":
    unittest.main()
