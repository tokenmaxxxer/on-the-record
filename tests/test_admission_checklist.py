#!/usr/bin/env python3
"""Issue #2100: deterministic pre-spawn admission checklist.

Per checklist item: omitting the precondition refuses the dispatch with the
item's name, creates no session and no workspace, and writes exactly one
`admission_refused` ledger event. The checklist is a data table — a test
appends a synthetic row to prove no new gate code is needed per item.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn

from _spawn_test_support import *  # noqa: F401,F403

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import ci


_ROLE_SOURCE_STUB = {"source": "none", "skills": [], "skill_dirs": [],
                     "skill_sha": None}


def _board_repo(td):
    """A minimal on-board target repo: git + approvers.md marker."""
    work = Path(td) / "repo"
    work.mkdir()
    run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
    run("git", "init", "-q")
    marker = work / spawn.MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("approver-login\n")
    return work


class _LedgerSpy:
    def __init__(self):
        self.events = []

    def __call__(self, entry):
        self.events.append(entry)

    def named(self, event):
        return [e for e in self.events if e.get("event") == event]


class AdmissionGateTable(unittest.TestCase):
    """The single admission loop over the ADMISSION_CHECKS table."""

    # --- item 1: approve token ------------------------------------------
    def test_missing_approve_token_refuses_named(self):
        """Regression of the 3x APPROVE-token incident: the issue is
        phase-2 (some role approved) but the spawned role differs and its
        token is not published => refused at admission, not mid-flight."""
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_issue_comments",
                                   return_value=([], True)), \
                 mock.patch.object(ci, "_approved_roles_on_issue",
                                   return_value={"product"}):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": 7,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertEqual(refused, "approve-token")
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "approve-token")
        self.assertEqual(events[0]["issue"], 7)

    def test_published_token_for_role_admits(self):
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_issue_comments",
                                   return_value=([], True)), \
                 mock.patch.object(ci, "_approved_roles_on_issue",
                                   return_value={"implementation"}), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": 7,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertIsNone(refused)
        self.assertEqual(ledger.named("admission_refused"), [])

    def test_phase1_issue_needs_no_token(self):
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            with mock.patch.object(spawn, "ledger_write", _LedgerSpy()), \
                 mock.patch.object(spawn, "_issue_comments",
                                   return_value=([], True)), \
                 mock.patch.object(ci, "_approved_roles_on_issue",
                                   return_value=set()):
                verdict = spawn._admission_check_approve_token({
                    "cwd": str(work), "role": "implementation", "issue": 7,
                    "single_phase": False})
        self.assertIs(verdict, True)

    # --- item 2: directive completeness ---------------------------------
    def test_directive_assembly_failure_refuses_named(self):
        """A role whose spec file does not exist cannot have its directive
        assembled — refusal at admission, not a mid-flight surprise."""
        ledger = _LedgerSpy()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "ledger_write", ledger):
            refused = spawn.admission_gate({
                "cwd": td, "role": "no-such-role-2100", "issue": None,
                "single_phase": False, "skills": None,
                "max_turns": 200, "allow_unlimited_turns": False})
        self.assertEqual(refused, "directive-completeness")
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "directive-completeness")

    def test_skill_resolver_fail_closed_is_admission_refusal(self):
        """The resolvers fail-closed via sys.exit on unknown skill names —
        the exit propagates with its original actionable message
        (pre-#2100 behavior preserved) AND the refusal is recorded under
        the checklist item's name."""
        ledger = _LedgerSpy()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "ledger_write", ledger), \
             mock.patch.object(spawn, "resolved_skill_sources",
                               side_effect=SystemExit("--skills: unknown")):
            with self.assertRaises(SystemExit):
                spawn.admission_gate({
                    "cwd": td, "role": "implementation", "issue": None,
                    "single_phase": False,
                    "skills": "definitely-not-a-skill",
                    "max_turns": 200, "allow_unlimited_turns": False})
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "directive-completeness")

    # --- item 3: watch registration -------------------------------------
    def test_unwritable_watch_state_refuses_named(self):
        ledger = _LedgerSpy()
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "repo"
            work.mkdir()
            blocker = Path(td) / "not-a-dir"
            blocker.write_text("regular file")  # ROSTER parent mkdir fails
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "ROSTER",
                                   blocker / "state" / "active.json"), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": 7,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertEqual(refused, "watch-registration")
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "watch-registration")

    def test_adhoc_spawn_skips_watch_item(self):
        # No issue => no detached watcher is ever armed; item passes.
        self.assertIs(spawn._admission_check_watch_registration(
            {"issue": None}), True)

    # --- item 4: budget caps --------------------------------------------
    def test_explicit_unlimited_without_override_refuses_named(self):
        ledger = _LedgerSpy()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "ledger_write", ledger), \
             mock.patch.object(spawn, "resolve_role_source",
                               lambda role, repo_root: _ROLE_SOURCE_STUB):
            refused = spawn.admission_gate({
                "cwd": td, "role": "implementation", "issue": None,
                "single_phase": False, "skills": None,
                "max_turns": 0, "allow_unlimited_turns": False})
        self.assertEqual(refused, "budget-caps")
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "budget-caps")

    def test_unlimited_with_override_admits(self):
        self.assertIs(spawn._admission_check_budget_caps(
            {"max_turns": 0, "allow_unlimited_turns": True}), True)

    def test_default_cap_admits(self):
        self.assertIs(spawn._admission_check_budget_caps(
            {"max_turns": spawn.DEFAULT_SESSION_MAX_TURNS,
             "allow_unlimited_turns": False}), True)

    # --- item 5: board validity (issue #2123) ---------------------------
    def test_missing_board_marker_refuses_named(self):
        """The live 2026-08-23 incident, reconstructed at admission: the
        target's remote default branch lacks docs/specs/approvers.md =>
        refused with item `board-validity` before any session starts,
        instead of stranding a 5-minute session at its record write."""
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_repo_slug",
                                   return_value="owner/target"), \
                 mock.patch.object(spawn, "_board_marker_probe",
                                   return_value=False), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": None,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertEqual(refused, "board-validity")
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "board-validity")

    def test_present_board_marker_admits(self):
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_repo_slug",
                                   return_value="owner/target"), \
                 mock.patch.object(spawn, "_board_marker_probe",
                                   return_value=True), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": None,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertIsNone(refused)
        self.assertEqual(ledger.named("admission_refused"), [])
        self.assertEqual(ledger.named("admission_gate_fail_open"), [])

    def test_board_probe_gh_failure_fails_open(self):
        """gh/network failure during the contents probe follows the
        `admission_gate_fail_open` convention (issue #680): ledger event,
        spawn proceeds."""
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_repo_slug",
                                   return_value="owner/target"), \
                 mock.patch.object(spawn, "_board_marker_probe",
                                   return_value=None), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": None,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertIsNone(refused)  # admission passes
        events = ledger.named("admission_gate_fail_open")
        self.assertEqual([e["item"] for e in events], ["board-validity"])
        self.assertEqual(ledger.named("admission_refused"), [])

    def test_local_only_target_skips_board_probe(self):
        """No resolvable remote slug => nothing to probe: the workspace
        materializes from the local checkout, where board.py's own marker
        check governs. Not a gh failure — no fail-open event."""
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "_repo_slug", return_value=None):
            verdict = spawn._admission_check_board_validity({"cwd": td})
        self.assertIs(verdict, True)

    def test_board_marker_probe_verdicts(self):
        """The gh contents probe maps: HTTP 200 => True (present),
        HTTP 404 => False (confirmed missing), anything else => None."""
        import pipeline

        def _cp(rc, stderr=""):
            return subprocess.CompletedProcess(
                args=[], returncode=rc, stdout="", stderr=stderr)
        with mock.patch.object(pipeline.subprocess, "run",
                               return_value=_cp(0)):
            self.assertIs(spawn._board_marker_probe("o/r"), True)
        with mock.patch.object(pipeline.subprocess, "run",
                               return_value=_cp(1, "gh: Not Found (HTTP 404)")):
            self.assertIs(spawn._board_marker_probe("o/r"), False)
        with mock.patch.object(pipeline.subprocess, "run",
                               return_value=_cp(1, "connection reset")):
            self.assertIsNone(spawn._board_marker_probe("o/r"))
        with mock.patch.object(
                pipeline.subprocess, "run",
                side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=60)):
            self.assertIsNone(spawn._board_marker_probe("o/r"))

    # --- item 6: degenerate task (issue #2293) ---------------------------
    def test_bare_numeric_task_without_issue_refuses_named(self):
        """Consumer incident (2026-08-25): `spawn.py implementation 538` —
        a typo for `--issue 538` — silently spawned a live agent whose
        entire mission was the string "538"."""
        ledger = _LedgerSpy()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "ledger_write", ledger), \
             mock.patch.object(spawn, "resolve_role_source",
                               lambda role, repo_root: _ROLE_SOURCE_STUB):
            refused = spawn.admission_gate({
                "cwd": td, "role": "implementation", "issue": None,
                "task": "538", "single_phase": False, "skills": None,
                "max_turns": 200, "allow_unlimited_turns": False})
        self.assertEqual(refused, "degenerate-task")
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "degenerate-task")

    def test_hash_and_negative_shaped_tasks_also_refuse(self):
        # `-538` is the before-landing-warrant-hunt bypass in the prior
        # delivery (PR #2306): argparse's own negative-number handling
        # lets a leading-dash digit string through as a plain positional.
        for shaped_task in ("#538", "-538", "  538  "):
            with self.subTest(task=shaped_task):
                self.assertIs(spawn._admission_check_degenerate_task(
                    {"issue": None, "task": shaped_task}), False)

    def test_real_task_text_admits(self):
        self.assertIs(spawn._admission_check_degenerate_task(
            {"issue": None, "task": "fix the login bug"}), True)

    def test_issue_scoped_numeric_task_admits(self):
        # --issue was given -- whatever the task text looks like is not
        # this check's concern.
        self.assertIs(spawn._admission_check_degenerate_task(
            {"issue": 538, "task": "538"}), True)

    def test_force_adhoc_task_overrides(self):
        self.assertIs(spawn._admission_check_degenerate_task(
            {"issue": None, "task": "538", "force_adhoc_task": True}), True)

    def test_no_task_key_admits(self):
        # Ctx dicts built before this item existed (older callers/tests)
        # carry no "task" key at all -- must not refuse on absence.
        self.assertIs(spawn._admission_check_degenerate_task(
            {"issue": None}), True)

    def test_force_adhoc_task_admits_and_no_workspace_change(self):
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": None,
                    "task": "538", "force_adhoc_task": True,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertIsNone(refused)
        self.assertEqual(ledger.named("admission_refused"), [])

    # --- fail-open ------------------------------------------------------
    def test_gh_failure_fails_open_with_ledger_event(self):
        """Mirrors the returned-PR gate convention (issue #680): a broken
        gh must not turn admission into a new stall class — the spawn
        proceeds and a fail-open ledger event records the blind spot."""
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_issue_comments",
                                   return_value=([], False)), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB):
                refused = spawn.admission_gate({
                    "cwd": str(work), "role": "implementation", "issue": 7,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        self.assertIsNone(refused)  # admission passes
        events = ledger.named("admission_gate_fail_open")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "approve-token")
        self.assertEqual(ledger.named("admission_refused"), [])

    def test_crashing_check_fails_open_not_stalls(self):
        ledger = _LedgerSpy()
        row = ("crashing-check",
               lambda ctx: (_ for _ in ()).throw(RuntimeError("boom")))
        spawn.ADMISSION_CHECKS.append(row)
        try:
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB), \
                 tempfile.TemporaryDirectory() as td:
                refused = spawn.admission_gate({
                    "cwd": td, "role": "implementation", "issue": None,
                    "single_phase": False, "skills": None,
                    "max_turns": 200, "allow_unlimited_turns": False})
        finally:
            spawn.ADMISSION_CHECKS.remove(row)
        self.assertIsNone(refused)
        events = ledger.named("admission_gate_fail_open")
        self.assertEqual([e["item"] for e in events], ["crashing-check"])

    # --- table-driven proof ---------------------------------------------
    def test_synthetic_table_row_is_enforced_without_new_gate_code(self):
        """Acceptance (issue #2100): the checklist is data. Registering a
        synthetic extra check by appending one table row is enough for the
        existing loop to enforce it — no new gate code."""
        ledger = _LedgerSpy()
        row = ("synthetic-precondition", lambda ctx: ctx.get("synthetic-ok",
                                                             False))
        spawn.ADMISSION_CHECKS.append(row)
        try:
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB), \
                 tempfile.TemporaryDirectory() as td:
                ctx = {"cwd": td, "role": "implementation", "issue": None,
                       "single_phase": False, "skills": None,
                       "max_turns": 200, "allow_unlimited_turns": False}
                refused = spawn.admission_gate(dict(ctx))
                admitted = spawn.admission_gate(dict(ctx, **{"synthetic-ok": True}))
        finally:
            spawn.ADMISSION_CHECKS.remove(row)
        self.assertEqual(refused, "synthetic-precondition")
        self.assertIsNone(admitted)
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "synthetic-precondition")


class AdmissionRefusalCreatesNothing(unittest.TestCase):
    """A refusal is a single admission error BEFORE the session starts:
    `_spawn_one` returns nonzero having created no workspace, no branch,
    no roster entry, and no session process."""

    def test_refused_spawn_creates_no_workspace_and_no_session(self):
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            workspaces, popens = [], []
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_issue_comments",
                                   return_value=([], True)), \
                 mock.patch.object(ci, "_approved_roles_on_issue",
                                   return_value={"product"}), \
                 mock.patch.object(spawn, "issue_workspace",
                                   side_effect=lambda *a: workspaces.append(a)), \
                 mock.patch.object(spawn, "roster_register",
                                   side_effect=AssertionError("no roster write")), \
                 mock.patch.object(spawn.subprocess, "Popen",
                                   side_effect=lambda *a, **k: popens.append(a)):
                rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                      unattended=True, issue=7, bounded=False)
        self.assertEqual(rc, 1)
        self.assertEqual(workspaces, [])   # no workspace created
        self.assertEqual(popens, [])       # no session process
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "approve-token")

    def test_board_validity_refusal_creates_no_workspace_and_no_session(self):
        """Issue #2123 acceptance: a target whose remote default branch
        lacks the marker is refused at admission — no session started, no
        workspace left behind."""
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            workspaces, popens = [], []
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "_repo_slug",
                                   return_value="owner/target"), \
                 mock.patch.object(spawn, "_board_marker_probe",
                                   return_value=False), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB), \
                 mock.patch.object(spawn, "issue_workspace",
                                   side_effect=lambda *a: workspaces.append(a)), \
                 mock.patch.object(spawn, "roster_register",
                                   side_effect=AssertionError("no roster write")), \
                 mock.patch.object(spawn.subprocess, "Popen",
                                   side_effect=lambda *a, **k: popens.append(a)):
                rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                      unattended=True, issue=None,
                                      bounded=False)
        self.assertEqual(rc, 1)
        self.assertEqual(workspaces, [])   # no workspace created
        self.assertEqual(popens, [])       # no session process
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "board-validity")

    def test_degenerate_task_refusal_creates_no_workspace_and_no_session(self):
        """Issue #2293 acceptance: a bare-numeric adhoc task is refused at
        admission -- no isolated workspace, no session, before an adhoc
        spawn ever reaches its (new, issue #2293) isolation step."""
        with tempfile.TemporaryDirectory() as td:
            work = _board_repo(td)
            ledger = _LedgerSpy()
            workspaces, popens = [], []
            with mock.patch.object(spawn, "ledger_write", ledger), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda role, repo_root: _ROLE_SOURCE_STUB), \
                 mock.patch.object(spawn, "_repo_slug", return_value=None), \
                 mock.patch.object(spawn, "issue_workspace",
                                   side_effect=lambda *a: workspaces.append(a)), \
                 mock.patch.object(spawn, "roster_register",
                                   side_effect=AssertionError("no roster write")), \
                 mock.patch.object(spawn.subprocess, "Popen",
                                   side_effect=lambda *a, **k: popens.append(a)):
                rc = spawn._spawn_one(str(work), "implementation", "538",
                                      unattended=True, issue=None,
                                      bounded=False)
        self.assertEqual(rc, 1)
        self.assertEqual(workspaces, [])   # no workspace created
        self.assertEqual(popens, [])       # no session process
        events = ledger.named("admission_refused")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["item"], "degenerate-task")


class BudgetCapPlumbing(unittest.TestCase):
    """Item 4 plumbing: max-turns pass-through with a default."""

    def test_spawn_cmd_carries_max_turns_flag(self):
        # Issue #2262: the actual --max-turns flag is the resolved cap
        # plus a wrap-up allowance (see tests/test_session_turn_budget.py
        # for that widening itself) -- pinned to 0 here so this test keeps
        # covering only the original item-4 pass-through concern.
        with mock.patch.dict(os.environ, {"MUSTER_WRAP_UP_ALLOWANCE_TURNS": "0"}):
            cmd, _ = spawn.spawn_cmd("/tmp/s.json", "implementation",
                                     unattended=False, max_turns=37)
        self.assertEqual(cmd[cmd.index("--max-turns") + 1], "37")

    def test_spawn_cmd_without_max_turns_is_unchanged(self):
        cmd, _ = spawn.spawn_cmd("/tmp/s.json", "implementation",
                                 unattended=False)
        self.assertNotIn("--max-turns", cmd)

    def test_resolver_default_and_precedence(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MUSTER_SESSION_MAX_TURNS", None)
            self.assertEqual(spawn._resolve_session_max_turns(None),
                             spawn.DEFAULT_SESSION_MAX_TURNS)
        with mock.patch.dict(os.environ,
                             {"MUSTER_SESSION_MAX_TURNS": "55"}):
            self.assertEqual(spawn._resolve_session_max_turns(None), 55)
            self.assertEqual(spawn._resolve_session_max_turns(9), 9)


if __name__ == "__main__":
    unittest.main()
