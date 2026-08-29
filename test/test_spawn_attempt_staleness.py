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


class SkillFamilyTest(unittest.TestCase):
    """issue #2511 residual: `_skill_family()` strips the trailing 8-hex-char
    lease disambiguator (`roster.new_lease_disambiguator()` ==
    `secrets.token_hex(4)`) that `spawn.py:1990-1991` appends to every role
    string, so retries of the same work (a fresh disambiguator each time,
    the normal shape of a retry — not an edge case, per PR #2608's review)
    compare equal on the part that identifies the work item itself."""

    def test_strips_trailing_lease_disambiguator(self):
        self.assertEqual(spawn._skill_family("silent-failure-audit-ec09cf78"),
                          "silent-failure-audit")

    def test_the_real_issue_2576_retry_pair_matches_after_stripping(self):
        # Real fixture (runs/spawn-attempts.jsonl live ledger + issue #2576
        # session-end comments): halted as -ec09cf78, later succeeded as
        # -c678659a — same family, different lease disambiguator.
        self.assertEqual(spawn._skill_family("silent-failure-audit-ec09cf78"),
                          spawn._skill_family("silent-failure-audit-c678659a"))

    def test_skill_without_a_disambiguator_suffix_passes_through(self):
        self.assertEqual(spawn._skill_family("orchestrator"), "orchestrator")

    def test_composite_skill_skill_keeps_its_plus_joined_family(self):
        self.assertEqual(
            spawn._skill_family("silent-failure-audit+diagnose-first-ae8ab737"),
            "silent-failure-audit+diagnose-first")

    def test_short_hex_like_suffix_is_not_mistaken_for_the_8char_disambiguator(self):
        # Only an exact 8-lowercase-hex-char trailing group is a lease
        # disambiguator; a shorter or differently-shaped trailing token is
        # part of the family name and must not be stripped.
        self.assertEqual(spawn._skill_family("implementation-af26085"),
                          "implementation-af26085")


class AttemptSupersededTest(unittest.TestCase):
    """issue #2511 residual: `_attempt_superseded()` — the fallback the
    class-based re-check (`_halt_condition_cleared`) cannot provide for
    attempt-bound classes (`cwd-invalid`, `workspace-origin-mismatch`) or
    cwd-less legacy records. Matching rule and evidence-location rationale
    are in the function's own docstring and the module comment above it in
    spawn.py."""

    def test_later_successful_attempt_same_issue_and_family_supersedes(self):
        attempts = {
            "a1": {"issue": 2576, "role": "silent-failure-audit-ec09cf78", "ts": 100.0},
            "a2": {"issue": 2576, "role": "silent-failure-audit-c678659a", "ts": 200.0},
        }
        outcomes = {"a2": {"outcome": "session-log", "detail": "/log/path"}}
        self.assertTrue(
            spawn._attempt_superseded("a1", attempts["a1"], attempts, outcomes))

    def test_no_later_attempt_at_all_is_not_superseded(self):
        # Matches issue-1/implementation-af260856: nobody will ever retry
        # this issue, so there is no later attempt of any kind.
        attempts = {"a1": {"issue": 1, "role": "implementation-af260856", "ts": 100.0}}
        outcomes = {}
        self.assertFalse(
            spawn._attempt_superseded("a1", attempts["a1"], attempts, outcomes))

    def test_later_attempt_that_also_halted_does_not_supersede(self):
        attempts = {
            "a1": {"issue": 2576, "role": "silent-failure-audit-ec09cf78", "ts": 100.0},
            "a2": {"issue": 2576, "role": "silent-failure-audit-c678659a", "ts": 200.0},
        }
        outcomes = {"a2": {"outcome": "halted", "detail": "still broken"}}
        self.assertFalse(
            spawn._attempt_superseded("a1", attempts["a1"], attempts, outcomes))

    def test_earlier_successful_attempt_does_not_supersede_a_later_halt(self):
        # A success that happened BEFORE this halt cannot be its retry.
        attempts = {
            "a1": {"issue": 2576, "role": "silent-failure-audit-old", "ts": 200.0},
            "a2": {"issue": 2576, "role": "silent-failure-audit-ec09cf78", "ts": 300.0},
        }
        outcomes = {"a1": {"outcome": "session-log", "detail": "/log/path"}}
        self.assertFalse(
            spawn._attempt_superseded("a2", attempts["a2"], attempts, outcomes))

    def test_success_on_a_different_issue_does_not_supersede(self):
        """Over-broadening guard: same role family, different issue — must
        not silence issue-1/implementation-af260856 just because some other
        issue's implementation succeeded."""
        attempts = {
            "a1": {"issue": 1, "role": "implementation-af260856", "ts": 100.0},
            "a2": {"issue": 2, "role": "implementation-deadbeef", "ts": 200.0},
        }
        outcomes = {"a2": {"outcome": "session-log", "detail": "/log/path"}}
        self.assertFalse(
            spawn._attempt_superseded("a1", attempts["a1"], attempts, outcomes))

    def test_success_on_a_different_skill_family_does_not_supersede(self):
        """Over-broadening guard: same issue, different role family — an
        unrelated skill's success on the same issue must not silence this
        halt."""
        attempts = {
            "a1": {"issue": 2587, "role": "requirement-tag-fix-de7d3bcf", "ts": 100.0},
            "a2": {"issue": 2587, "role": "technical-writing-cba98765", "ts": 200.0},
        }
        outcomes = {"a2": {"outcome": "session-log", "detail": "/log/path"}}
        self.assertFalse(
            spawn._attempt_superseded("a1", attempts["a1"], attempts, outcomes))

    def test_missing_issue_or_skill_or_ts_is_conservative_not_superseded(self):
        attempts = {"a2": {"issue": 1, "role": "implementation-deadbeef", "ts": 200.0}}
        outcomes = {"a2": {"outcome": "session-log", "detail": "x"}}
        for attempt in ({"role": "implementation-af260856", "ts": 100.0},
                         {"issue": 1, "ts": 100.0},
                         {"issue": 1, "role": "implementation-af260856"}):
            self.assertFalse(
                spawn._attempt_superseded("a1", attempt, attempts, outcomes))


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

    def _write_attempt(self, attempt_id, issue, skill, cwd, reason, ts):
        with self.attempts_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": attempt_id,
                                  "issue": issue, "role": skill, "pid": 4242,
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


class SpawnAttemptSweepSupersessionTest(unittest.TestCase):
    """issue #2511 residual, end-to-end: the shape PR #2608 tried and failed
    to fix — a halt bound to its own recorded arguments (the `-C` value is a
    repo slug, e.g. 'tokenmaxxxer/on-the-record', that will never become a
    directory — the exact live issue-2576 fixture) never clears by
    class re-check alone, but a later successful retry for the same
    (issue, role-family) must still resolve it."""

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

    def _append(self, entry):
        with self.attempts_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")

    def _append_attempt(self, attempt_id, issue, skill, ts, cwd=None):
        self._append({"event": "spawn_attempt", "attempt_id": attempt_id,
                       "issue": issue, "role": skill, "pid": 4242, "cwd": cwd,
                       "ts": ts})

    def _append_halted(self, attempt_id, reason, ts):
        self._append({"event": "spawn_attempt_outcome", "attempt_id": attempt_id,
                       "outcome": "halted", "detail": reason, "ts": ts})

    def _append_session_log(self, attempt_id, ts, log_path="/log/path"):
        self._append({"event": "spawn_attempt_outcome", "attempt_id": attempt_id,
                       "outcome": "session-log", "detail": log_path, "ts": ts})

    def test_halt_superseded_by_a_later_successful_retry_stops_replaying(self):
        # Real fixture (runs/spawn-attempts.jsonl live ledger, issue #2576):
        # -C was given a repo slug, not a path — cwd-invalid re-checks this
        # as still-blocking forever, since the recorded string never
        # becomes a directory no matter how many times it's re-checked.
        reason = ("-C 가 존재하지 않는 디렉터리다: tokenmaxxxer/on-the-record\n"
                   "  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.")
        halted_ts = time.time() - 3600
        self._append_attempt("2576:silent-failure-audit-ec09cf78:1:1", 2576,
                              "silent-failure-audit-ec09cf78", halted_ts)
        self._append_halted("2576:silent-failure-audit-ec09cf78:1:1", reason,
                             halted_ts)

        # Tick 1, before the retry exists: class re-check cannot clear a
        # cwd-invalid halt whose recorded string is a slug, not a path — it
        # keeps reporting exactly as PR #2608 found in production.
        with mock.patch("builtins.print") as mocked_print:
            count1 = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count1, 1)
        printed1 = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn("spawn halted pre-workspace", printed1)

        # A later attempt for the same (issue, role-family) — different
        # lease disambiguator, the normal shape of a retry — succeeds.
        success_ts = halted_ts + 1800
        self._append_attempt("2576:silent-failure-audit-c678659a:2:2", 2576,
                              "silent-failure-audit-c678659a", success_ts)
        self._append_session_log("2576:silent-failure-audit-c678659a:2:2",
                                  success_ts)

        # Tick 2: class re-check still cannot clear it (the recorded slug
        # never becomes a directory), but supersession now can — the
        # heartbeat must no longer report this halt as live.
        with mock.patch("builtins.print") as mocked_print:
            count2 = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count2, 0)
        printed2 = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn("RESOLVED", printed2)
        self.assertIn("resolution=superseded", printed2)
        self.assertNotIn("spawn halted pre-workspace", printed2)

        # Tick 3: never replayed again.
        with mock.patch("builtins.print") as mocked_print:
            count3 = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count3, 0)
        self.assertEqual(mocked_print.call_args_list, [])

    def test_unrelated_halt_on_a_never_tagged_issue_keeps_reporting_unchanged(self):
        """Verification fixture named in the task: issue-1/implementation-
        af260856 — a requirement-tag halt on an issue nobody will ever tag,
        with no later successful attempt for that issue+role-family. Must
        keep reporting at full volume, completely unaffected by the
        supersession mechanism or by an unrelated issue's success."""
        reason = ("이슈 #1 가 요구 연결이 없다:\n  - 이슈 #1 본문이 요구 ID를 "
                   "하나도 인용하지 않는다.\n  세션을 안 띄운다.")
        halted_ts = time.time() - 3600
        self._append_attempt("1:implementation-af260856:1:1", 1,
                              "implementation-af260856", halted_ts)
        self._append_halted("1:implementation-af260856:1:1", reason, halted_ts)

        # An unrelated issue's same-family success must not leak across.
        other_success_ts = halted_ts + 60
        self._append_attempt("2:implementation-deadbeef:2:2", 2,
                              "implementation-deadbeef", other_success_ts)
        self._append_session_log("2:implementation-deadbeef:2:2",
                                  other_success_ts)

        with mock.patch("builtins.print") as mocked_print:
            count = roster.spawn_attempt_sweep(d_all={})
        self.assertEqual(count, 1)
        printed = "\n".join(str(c.args[0]) for c in mocked_print.call_args_list)
        self.assertIn("spawn halted pre-workspace", printed)
        self.assertNotIn("RESOLVED", printed)


class PruneSpawnAttemptsSessionLogRetentionTest(unittest.TestCase):
    """issue #2511 residual: PR #2608 was closed unmerged because
    `_prune_spawn_attempts()` used to drop every `"session-log"` outcome at
    the end of the very sweep that recorded it — by the next watchdog tick
    (~2 minutes later, roster.py:667) the evidence a supersession check
    would need was already gone (PR #2608's review comment, citing
    spawn.py:1489 and the live ledger: 3 records, all halted, zero
    session-log after ~15 successful spawns that day). session-log outcomes
    must now survive at least `SPAWN_ATTEMPTS_RETENTION_SEC`, symmetric
    with halted outcomes, so `_attempt_superseded()` has something to read."""

    def setUp(self):
        import tempfile
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.attempts_path = Path(self._td.name) / "spawn-attempts.jsonl"
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(spawn, "SPAWN_ATTEMPTS_PATH", self.attempts_path).start()

    def _write(self, *entries):
        with self.attempts_path.open("w", encoding="utf-8") as fh:
            for e in entries:
                fh.write(json.dumps(e) + "\n")

    def test_fresh_session_log_outcome_survives_a_prune_pass(self):
        now = time.time()
        self._write(
            {"event": "spawn_attempt", "attempt_id": "x", "issue": 1,
             "role": "r-aaaaaaaa", "pid": 1, "cwd": None, "ts": now - 10},
            {"event": "spawn_attempt_outcome", "attempt_id": "x",
             "outcome": "session-log", "detail": "/log", "ts": now - 10},
        )
        dropped = spawn._prune_spawn_attempts(now=now)
        self.assertEqual(dropped, 0)
        attempts, outcomes, _ = spawn._load_spawn_attempts()
        self.assertIn("x", attempts)
        self.assertIn("x", outcomes)

    def test_session_log_outcome_older_than_retention_is_pruned(self):
        now = time.time()
        old_ts = now - spawn.SPAWN_ATTEMPTS_RETENTION_SEC - 1
        self._write(
            {"event": "spawn_attempt", "attempt_id": "x", "issue": 1,
             "role": "r-aaaaaaaa", "pid": 1, "cwd": None, "ts": old_ts},
            {"event": "spawn_attempt_outcome", "attempt_id": "x",
             "outcome": "session-log", "detail": "/log", "ts": old_ts},
        )
        dropped = spawn._prune_spawn_attempts(now=now)
        self.assertGreater(dropped, 0)
        attempts, outcomes, _ = spawn._load_spawn_attempts()
        self.assertNotIn("x", attempts)
        self.assertNotIn("x", outcomes)


if __name__ == "__main__":
    unittest.main()
