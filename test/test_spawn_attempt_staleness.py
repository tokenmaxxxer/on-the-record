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


class AttemptSupersededTest(unittest.TestCase):
    """issue #2511 residual (reopened after #2594 landed): cwd-invalid's
    class re-check looks at the halted attempt's own recorded `cwd` —
    for the fixture that motivated the reopen, that string is a repo
    slug (`tokenmaxxxer/on-the-record`) that can never become a
    directory, so the class re-check stays False forever even after a
    later respawn of the same (issue, role) succeeds. `_attempt_superseded`
    answers a different question: has this (issue, role) since been
    attempted successfully, regardless of this attempt's own arguments.

    Unlike the other four classes, this check has no live filesystem/git/gh
    state of its own to re-derive from — it leans on a past `outcome ==
    "session-log"` entry in spawn-attempts.jsonl. A before-landing
    warrant-hunt on this function flagged that trusting the recorded
    outcome alone, without any live re-check, breaks with the rest of the
    design's "always re-derive, never just replay a recorded claim"
    principle; the fix re-checks that the referenced session log file
    still actually exists on disk (`test_false_when_the_log_path_no_longer_exists`
    covers the negative direction of that re-check)."""

    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.real_log = Path(self._td.name) / "session.log"
        self.real_log.write_text("session output\n", encoding="utf-8")

    def test_true_when_a_later_attempt_for_the_same_subject_succeeded(self):
        attempt = {"issue": 2576, "role": "r", "ts": 100.0}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "r", "ts": 200.0},
        }
        outcomes = {"b": {"outcome": "session-log", "detail": str(self.real_log)}}
        self.assertTrue(spawn._attempt_superseded("a", attempt, attempts, outcomes))

    def test_false_when_no_later_attempt_exists(self):
        attempt = {"issue": 2576, "role": "r", "ts": 100.0}
        attempts = {"a": attempt}
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, {}))

    def test_false_when_the_later_attempt_also_halted(self):
        attempt = {"issue": 2576, "role": "r", "ts": 100.0}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "r", "ts": 200.0},
        }
        outcomes = {"b": {"outcome": "halted", "detail": "still broken"}}
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, outcomes))

    def test_false_when_the_successful_attempt_is_earlier_not_later(self):
        attempt = {"issue": 2576, "role": "r", "ts": 200.0}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "r", "ts": 100.0},
        }
        outcomes = {"b": {"outcome": "session-log", "detail": str(self.real_log)}}
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, outcomes))

    def test_false_when_the_successful_attempt_is_a_different_subject(self):
        attempt = {"issue": 2576, "role": "r", "ts": 100.0}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "other-role", "ts": 200.0},
            "c": {"issue": 1, "role": "r", "ts": 200.0},
        }
        outcomes = {
            "b": {"outcome": "session-log", "detail": str(self.real_log)},
            "c": {"outcome": "session-log", "detail": str(self.real_log)},
        }
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, outcomes))

    def test_false_when_ts_is_missing(self):
        attempt = {"issue": 2576, "role": "r"}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "r", "ts": 200.0},
        }
        outcomes = {"b": {"outcome": "session-log", "detail": str(self.real_log)}}
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, outcomes))

    def test_false_when_the_log_path_no_longer_exists(self):
        """warrant-hunt finding: a recorded `session-log` outcome alone is
        just a past claim, not live evidence — if the referenced log file
        has since been cleaned up (workspace prune), there is nothing left
        to re-derive supersession from, so this stays conservatively
        unresolved rather than trusting the stale claim verbatim."""
        attempt = {"issue": 2576, "role": "r", "ts": 100.0}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "r", "ts": 200.0},
        }
        pruned_log = str(Path(self._td.name) / "already-pruned.log")
        outcomes = {"b": {"outcome": "session-log", "detail": pruned_log}}
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, outcomes))

    def test_false_when_detail_is_missing(self):
        attempt = {"issue": 2576, "role": "r", "ts": 100.0}
        attempts = {
            "a": attempt,
            "b": {"issue": 2576, "role": "r", "ts": 200.0},
        }
        outcomes = {"b": {"outcome": "session-log", "detail": ""}}
        self.assertFalse(spawn._attempt_superseded("a", attempt, attempts, outcomes))


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


class SpawnAttemptSweepSupersededFixTest(unittest.TestCase):
    """issue #2511 residual, mirrored from the two live fixtures named in
    the reopen comment (`runs/spawn-attempts.jsonl` on the canonical
    checkout, issue-2576/silent-failure-audit-ec09cf78 and
    issue-1/implementation-af260856): a cwd-invalid halt whose recorded
    `cwd` is a repo slug (never a directory, so the class re-check can
    never clear it) must stop replaying once the same (issue, role) has
    a later successful attempt; a requirement-tag halt with no such later
    success must keep reporting exactly as #2594 left it."""

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

    def _append(self, event: dict) -> None:
        with self.attempts_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")

    def test_cwd_invalid_superseded_by_later_successful_attempt_stops_replaying(self):
        halted_ts = 1787801373.7906659
        self._append({"event": "spawn_attempt",
                       "attempt_id": "2576:silent-failure-audit-ec09cf78:2909352:1787801373790",
                       "issue": 2576, "role": "silent-failure-audit-ec09cf78",
                       "pid": 2909352, "cwd": "tokenmaxxxer/on-the-record",
                       "ts": halted_ts})
        self._append({"event": "spawn_attempt_outcome",
                       "attempt_id": "2576:silent-failure-audit-ec09cf78:2909352:1787801373790",
                       "outcome": "halted",
                       "detail": ("-C 가 존재하지 않는 디렉터리다: "
                                  "tokenmaxxxer/on-the-record\n"
                                  "  cwd 는 레포 루트를 가리켜야 한다 — 경로를 "
                                  "다시 확인해라."),
                       "ts": halted_ts})
        # cwd is a bare repo slug, never a directory — the class re-check
        # (spawn._halt_condition_cleared) can never clear this on its own,
        # by design (that recorded argument belongs to this attempt and
        # this attempt's arguments never change).
        self.assertFalse(spawn._halt_condition_cleared(
            "cwd-invalid", {"cwd": "tokenmaxxxer/on-the-record"}, ""))

        # The re-run under the same (issue, role) succeeded and its
        # workspace/session log came into existence (later ts). The log
        # file has to actually exist on disk — _attempt_superseded()
        # re-verifies that, it does not just trust the recorded claim.
        real_log = Path(self._td.name) / "issue-2576-checkout.session.log"
        real_log.write_text("session output\n", encoding="utf-8")
        self._append({"event": "spawn_attempt",
                       "attempt_id": "2576:silent-failure-audit-ec09cf78:3111222:1787804000000",
                       "issue": 2576, "role": "silent-failure-audit-ec09cf78",
                       "pid": 3111222, "cwd": "/work/issue-2576-checkout",
                       "ts": halted_ts + 2000})
        self._append({"event": "spawn_attempt_outcome",
                       "attempt_id": "2576:silent-failure-audit-ec09cf78:3111222:1787804000000",
                       "outcome": "session-log",
                       "detail": str(real_log),
                       "ts": halted_ts + 2000})

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count, 0)
        printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn("RESOLVED", printed)
        self.assertIn("resolved_via=superseded", printed)
        self.assertNotIn("spawn halted pre-workspace", printed)

        # Fully swept away on the next tick — no more replay.
        with mock.patch("builtins.print") as mocked_print:
            count2 = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count2, 0)
        self.assertEqual(mocked_print.call_args_list, [])

    def test_requirement_tag_without_a_successful_retry_keeps_reporting(self):
        attempt_ts = 1787802757.7393403
        self._append({"event": "spawn_attempt",
                       "attempt_id": "1:implementation-af260856:3000953:1787802757739",
                       "issue": 1, "role": "implementation-af260856",
                       "pid": 3000953, "ts": attempt_ts})
        self._append({"event": "spawn_attempt_outcome",
                       "attempt_id": "1:implementation-af260856:3000953:1787802757739",
                       "outcome": "halted",
                       "detail": ("이슈 #1 가 요구 연결이 없다:\n"
                                  "  - 이슈 #1 본문이 요구 ID를 하나도 인용하지 "
                                  "않고, 명시적 태그도 없다."),
                       "ts": attempt_ts})
        # No other attempt exists for this (issue, role) — nothing
        # superseded it, and this class's recheck needs `cwd` (absent on
        # this fixture, matching the real live entry) so it also stays
        # unresolved. It must keep reporting at full volume.

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count, 1)
        printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn("spawn halted pre-workspace", printed)
        self.assertNotIn("RESOLVED", printed)


if __name__ == "__main__":
    unittest.main()
