#!/usr/bin/env python3
"""Issue #2129: checkpoint mode — single-session propose-approve-implement
behind --checkpoint.

Covers: (1) default behavior without --checkpoint is byte-identical,
(2) the `await-approval` CLI verb's approved/timeout paths, (3) the #2101
declared-wait exemption during the checkpoint pause, (4) the admission
approve-token row cedes to checkpoint spawns (the boundary helper IS the
token check), (5) an end-to-end mocked-pipeline fixture: proposal artifacts,
declared wait, resume on a mid-wait APPROVE comment, phase-2 in the same
session; timeout leaves the proposal as the returned state.
"""
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import ci


_ROLE = "implementation"
_ISSUE = 7


def _git_repo(path: Path, origin: str | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run = lambda *a: subprocess.run(a, cwd=str(path), capture_output=True,
                                    text=True, check=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "t")
    (path / "f.txt").write_text("x")
    run("git", "add", "f.txt")
    run("git", "commit", "-q", "-m", "init")
    if origin:
        run("git", "remote", "add", "origin", origin)


class CheckpointDefaultUnchanged(unittest.TestCase):
    """Without --checkpoint, nothing about the spawn changes."""

    def test_spawn_one_defaults_checkpoint_off(self):
        import inspect
        sig = inspect.signature(spawn._spawn_one)
        self.assertIs(sig.parameters["checkpoint"].default, False)

    def test_contract_block_only_renders_under_flag(self):
        block = spawn._checkpoint_contract_block(_ISSUE, _ROLE)
        self.assertIn("Checkpoint mode (issue #2129", block)
        self.assertIn(f"APPROVE issue-{_ISSUE}/{_ROLE}", block)
        self.assertIn(f"await-approval --issue {_ISSUE} --role {_ROLE}", block)
        # The rendered helper command names this exact interpreter/script.
        self.assertIn(sys.executable, block)
        self.assertIn(str(Path(spawn.__file__).resolve()), block)

    def test_admission_default_path_unchanged(self):
        """Regression pair: WITHOUT checkpoint the approve-token row still
        refuses a phase-2 issue whose approved role differs; WITH
        checkpoint the row cedes to the in-session boundary check."""
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "repo"
            work.mkdir()
            marker = work / spawn.MARKER
            marker.parent.mkdir(parents=True)
            marker.write_text("- approver-login\n")
            subprocess.run(["git", "init", "-q"], cwd=work, check=True)
            with mock.patch.object(spawn, "_issue_comments",
                                   return_value=([], True)), \
                 mock.patch.object(ci, "_approved_roles_on_issue",
                                   return_value={"product"}):
                base_ctx = {"cwd": str(work), "role": _ROLE, "issue": _ISSUE,
                            "single_phase": False}
                self.assertIs(
                    spawn._admission_check_approve_token(dict(base_ctx)),
                    False)
                self.assertIs(
                    spawn._admission_check_approve_token(
                        {**base_ctx, "checkpoint": True}),
                    True)


class AwaitApprovalVerb(unittest.TestCase):
    """`spawn.py await-approval`: 0 approved / 3 timeout, declared wait
    written for the duration and removed on both exits."""

    def test_approved_path_returns_zero_and_clears_wait(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            seen_during = []

            def fake_approved(root, issue):
                seen_during.append(
                    (work / spawn.DECLARED_WAIT_FILENAME).exists())
                return {_ROLE}

            with mock.patch.object(ci, "_approved_roles_on_issue",
                                   fake_approved):
                rc = spawn.await_approval_cmd(str(work), _ISSUE, _ROLE,
                                              timeout=5, interval=0.01)
        self.assertEqual(rc, 0)
        self.assertTrue(seen_during and seen_during[0])
        self.assertFalse((work / spawn.DECLARED_WAIT_FILENAME).exists())

    def test_wait_file_reuses_2101_declared_wait_format(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            captured = {}

            def fake_approved(root, issue):
                captured["wait"] = json.loads(
                    (work / spawn.DECLARED_WAIT_FILENAME).read_text())
                return {_ROLE}

            with mock.patch.object(ci, "_approved_roles_on_issue",
                                   fake_approved):
                spawn.await_approval_cmd(str(work), _ISSUE, _ROLE,
                                         timeout=5, interval=0.01)
            wait = captured["wait"]
            self.assertEqual(wait["object"], f"issue:{_ISSUE}")
            self.assertEqual(wait["reason"], "approve-token")
            # `_declared_wait` (roster.py, the #2101 reader) accepts the
            # exact bytes the helper wrote (re-materialized here — the
            # helper removes the file when the pause ends).
            (work / spawn.DECLARED_WAIT_FILENAME).write_text(
                json.dumps(wait))
            self.assertIsNotNone(spawn._declared_wait(str(work)))

    def test_timeout_path_returns_three_and_clears_wait(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            with mock.patch.object(ci, "_approved_roles_on_issue",
                                   return_value=set()):
                rc = spawn.await_approval_cmd(str(work), _ISSUE, _ROLE,
                                              timeout=0.05, interval=0.01)
        self.assertEqual(rc, spawn.AWAIT_APPROVAL_TIMEOUT_RC)
        self.assertEqual(rc, 3)
        self.assertFalse((work / spawn.DECLARED_WAIT_FILENAME).exists())

    def test_env_defaults_are_read_at_call_time(self):
        with mock.patch.dict(os.environ,
                             {"CHECKPOINT_POLL_SECONDS": "7",
                              "CHECKPOINT_WAIT_MAX_SECONDS": "9"}):
            self.assertEqual(spawn._checkpoint_poll_seconds(), 7.0)
            self.assertEqual(spawn._checkpoint_wait_max_seconds(), 9.0)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CHECKPOINT_POLL_SECONDS", None)
            os.environ.pop("CHECKPOINT_WAIT_MAX_SECONDS", None)
            self.assertEqual(spawn._checkpoint_poll_seconds(), 60.0)
            self.assertEqual(spawn._checkpoint_wait_max_seconds(), 1800.0)


class DeclaredWaitExemptionDuringCheckpoint(unittest.TestCase):
    """#2101 mechanism 5: while the checkpoint wait file is present, K flat
    lease renewals produce NO STALLED-FLAT-PROGRESS advisory — even when
    the subject tree exists only in the workspace (proposal PR unmerged)."""

    def _flat_renewals(self, root: Path, work: Path) -> list[str]:
        entry = {"work": str(work)}
        out: list[str] = []
        with mock.patch.object(spawn, "_lease_progress_indicator",
                               return_value="flat"):
            for _ in range(spawn.LEASE_FLAT_RENEWALS_K + 1):
                out = spawn.lease_renew("issue-7/implementation", entry,
                                        root=root)
        return out

    def test_checkpoint_wait_exempts_flat_progress(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            work = Path(td) / "work"
            root.mkdir()
            work.mkdir()
            # Subject tree exists ONLY in the workspace — the live
            # checkpoint situation (proposal authored, PR open, unmerged).
            (work / spawn.BOARD / f"issue-{_ISSUE}").mkdir(parents=True)
            (work / spawn.DECLARED_WAIT_FILENAME).write_text(json.dumps(
                {"object": f"issue:{_ISSUE}", "reason": "approve-token"}))
            self.assertEqual(self._flat_renewals(root, work), [])

    def test_without_wait_file_advisory_still_fires(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            work = Path(td) / "work"
            root.mkdir()
            work.mkdir()
            advisories = self._flat_renewals(root, work)
            self.assertEqual(len(advisories), 1)
            self.assertIn("flat-progress", advisories[0])


def _fake_gh(bin_dir: Path, comments_file: Path) -> None:
    """A PATH-level gh stub: serves the issue-comments endpoint from
    `comments_file` (gh api --paginate --slurp shape: a list of pages);
    the ETag `-i` probe and every other endpoint fail, exercising the
    real fallback paths (fail-open / uncached refetch)."""
    gh = bin_dir / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"repo\" ] && [ \"$2\" = \"view\" ]; then\n"
        "  echo test/fixture\n"
        "  exit 0\n"
        "fi\n"
        "C=\"\"\n"
        "for a in \"$@\"; do\n"
        "  case \"$a\" in\n"
        "    -i) exit 1;;\n"
        "    repos/*/issues/*/comments) C=1;;\n"
        "  esac\n"
        "done\n"
        "if [ -n \"$C\" ]; then\n"
        f"  cat \"{comments_file}\" 2>/dev/null || echo '[[]]'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n")
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)


class CheckpointEndToEnd(unittest.TestCase):
    """Mocked-pipeline fixture per the spawn-pipeline e2e conventions:
    spawn_cmd is replaced by a shell script standing in for the claude
    session — it authors the proposal, commits it (the proposal-PR stand-in),
    runs the real `await-approval` helper as its ONE boundary command, and
    on approval continues to phase-2 in the same process."""

    def _run(self, approve_after: float | None, wait_max: str) -> Path:
        self.td = tempfile.TemporaryDirectory()
        td = Path(self.td.name)
        work = td / f"issue-{_ISSUE}-{_ROLE}"
        _git_repo(work, origin="https://github.com/test/fixture.git")
        marker = work / spawn.MARKER
        marker.parent.mkdir(parents=True)
        marker.write_text("- approver-login\n")
        subprocess.run(["git", "-C", str(work), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(work), "commit", "-qm", "board"],
                       check=True)

        comments = td / "comments.json"
        comments.write_text("[[]]")
        bin_dir = td / "bin"
        bin_dir.mkdir()
        _fake_gh(bin_dir, comments)

        session = td / "claude-session.sh"
        spawn_py = Path(spawn.__file__).resolve()
        session.write_text(
            "#!/bin/sh\n"
            "cat > /dev/null\n"                       # consume the directive
            f"mkdir -p docs/issue-{_ISSUE}\n"
            f"echo proposal > docs/issue-{_ISSUE}/proposal.md\n"
            "git add -A && git commit -qm phase1-proposal\n"
            f"if {sys.executable} {spawn_py} -C . await-approval "
            f"--issue {_ISSUE} --role {_ROLE}; then\n"
            "  echo phase2 > phase2.txt\n"
            "  git add -A && git commit -qm phase2-implementation\n"
            "fi\n"
            "exit 0\n")
        session.chmod(session.stat().st_mode | stat.S_IEXEC)

        if approve_after is not None:
            def post_approval():
                comments.write_text(json.dumps([[{
                    "user": {"login": "approver-login"},
                    "body": f"APPROVE issue-{_ISSUE}/{_ROLE}"}]]))
            timer = threading.Timer(approve_after, post_approval)
            timer.start()
            self.addCleanup(timer.cancel)

        env = {"PATH": f"{bin_dir}:{os.environ['PATH']}",
               "CHECKPOINT_POLL_SECONDS": "0.1",
               "CHECKPOINT_WAIT_MAX_SECONDS": wait_max}
        old_stdout, sys.stdout = sys.stdout, io.StringIO()
        old_roster = spawn.ROSTER
        spawn.ROSTER = td / "active.json"
        try:
            with mock.patch.dict(os.environ, env), \
                 mock.patch.object(spawn, "issue_workspace",
                                   lambda cwd, i, r: str(work)), \
                 mock.patch.object(spawn, "checkout_issue_branch",
                                   lambda cwd, i, r: f"issue-{_ISSUE}/{_ROLE}"), \
                 mock.patch.object(spawn, "spawn_cmd",
                                   lambda *a, **k: ([str(session)], {})), \
                 mock.patch.object(spawn, "ensure_pushed",
                                   lambda *a, **k: None), \
                 mock.patch.object(spawn, "_undispositioned_role_prs",
                                   lambda *a, **k: ([], True)), \
                 mock.patch.object(spawn, "_skill_repo_root",
                                   lambda: None), \
                 mock.patch.object(spawn, "resolved_skill_sources",
                                   lambda *a, **k: []), \
                 mock.patch.object(spawn, "resolve_role_source",
                                   lambda *a, **k: {"source": "none",
                                                    "skills": [],
                                                    "skill_dirs": [],
                                                    "skill_sha": None}), \
                 mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                rc = spawn._spawn_one(str(work), _ROLE, "fixture task.\n",
                                      unattended=True, issue=_ISSUE,
                                      checkpoint=True)
        finally:
            sys.stdout = old_stdout
            spawn.ROSTER = old_roster
        self.assertEqual(rc, 0)
        return work

    @pytest.mark.slow
    def test_resume_on_mid_wait_approval_lands_phase2_same_session(self):
        t0 = time.monotonic()
        work = self._run(approve_after=1.0, wait_max="30")
        elapsed = time.monotonic() - t0
        self.assertTrue((work / f"docs/issue-{_ISSUE}/proposal.md").exists())
        self.assertTrue((work / "phase2.txt").exists())
        log = subprocess.run(["git", "-C", str(work), "log", "--format=%s"],
                             capture_output=True, text=True).stdout
        self.assertIn("phase1-proposal", log)
        self.assertIn("phase2-implementation", log)
        # One session did both phases; the pause is over: no wait file left.
        self.assertFalse((work / spawn.DECLARED_WAIT_FILENAME).exists())
        print(f"[measure] checkpoint e2e wall-clock: {elapsed:.2f}s "
              f"(approval posted at t+1.0s)")

    @pytest.mark.slow
    def test_timeout_leaves_proposal_as_returned_state(self):
        work = self._run(approve_after=None, wait_max="0.3")
        self.assertTrue((work / f"docs/issue-{_ISSUE}/proposal.md").exists())
        self.assertFalse((work / "phase2.txt").exists())
        log = subprocess.run(["git", "-C", str(work), "log", "--format=%s"],
                             capture_output=True, text=True).stdout
        self.assertIn("phase1-proposal", log)
        self.assertNotIn("phase2-implementation", log)
        self.assertFalse((work / spawn.DECLARED_WAIT_FILENAME).exists())


class CheckpointDirectiveAssembly(unittest.TestCase):
    """The directive the session actually receives carries the checkpoint
    block under the flag and stays byte-free of it by default (the #1978
    byte-identical discipline, extended to #2129)."""

    def _delivered_prompt(self, checkpoint: bool) -> str:
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / f"issue-{_ISSUE}-{_ROLE}"
            _git_repo(work)
            roster = Path(td) / "active.json"
            old_roster, spawn.ROSTER = spawn.ROSTER, roster
            roster_calls = []
            orig_register = spawn.roster_register
            old_stdout, sys.stdout = sys.stdout, io.StringIO()
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, i, r: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, i, r: f"issue-{_ISSUE}/{_ROLE}"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda *a, **k: ([], True)), \
                     mock.patch.object(
                         spawn, "roster_register",
                         lambda key, entry: roster_calls.append((key, dict(entry)))
                         or orig_register(key, entry)), \
                     mock.patch.object(spawn, "_skill_repo_root",
                                       lambda: None), \
                     mock.patch.object(spawn, "resolved_skill_sources",
                                       lambda *a, **k: []), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda *a, **k: {"source": "none",
                                                            "skills": [],
                                                            "skill_dirs": [],
                                                            "skill_sha": None}), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda *a, **k: None):
                    spawn._spawn_one(str(work), _ROLE, "fixture task.\n",
                                     unattended=True, issue=_ISSUE,
                                     checkpoint=checkpoint)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
            log_path = [e for k, e in roster_calls
                        if k == f"issue-{_ISSUE}/{_ROLE}"][0]["log"]
            return Path(log_path).read_text()

    @pytest.mark.slow
    def test_default_prompt_has_no_checkpoint_block(self):
        delivered = self._delivered_prompt(checkpoint=False)
        self.assertNotIn("Checkpoint mode (issue #2129", delivered)
        self.assertNotIn("await-approval", delivered)

    @pytest.mark.slow
    def test_flag_appends_checkpoint_block(self):
        delivered = self._delivered_prompt(checkpoint=True)
        self.assertIn("Checkpoint mode (issue #2129", delivered)
        self.assertIn(f"await-approval --issue {_ISSUE} --role {_ROLE}",
                      delivered)
        # And the default portion is a strict prefix-superset relation:
        # removing the block reproduces the default prompt byte-for-byte.
        base = self._delivered_prompt(checkpoint=False)
        # Issue #2135: the inline appendage is the condensed index block;
        # the full contract prose is materialized as a workspace file.
        stripped = delivered.replace(
            "\n\n" + spawn._checkpoint_index_block(_ISSUE, _ROLE), "")
        self.assertEqual(stripped, base)


class CheckpointCliWiring(unittest.TestCase):
    def test_main_passes_checkpoint_flag_through(self):
        calls = {}

        def fake_spawn_one(*a, **k):
            calls.update(k)
            return 0

        with mock.patch.object(spawn, "_spawn_one", fake_spawn_one), \
             mock.patch.object(spawn, "require_board", lambda *a, **k: None), \
             mock.patch.object(spawn, "require_no_repo_config",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_acceptance_gate",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_requirement_linkage",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_doctor", lambda *a, **k: None), \
             mock.patch.object(spawn, "ensure_target_remote",
                               lambda *a, **k: None), \
             mock.patch.object(sys, "argv",
                               ["spawn.py", _ROLE, "task", "--issue",
                                str(_ISSUE), "--checkpoint"]):
            rc = spawn.main()
        self.assertEqual(rc, 0)
        self.assertIs(calls.get("checkpoint"), True)

    def test_main_default_checkpoint_false(self):
        calls = {}
        with mock.patch.object(spawn, "_spawn_one",
                               lambda *a, **k: calls.update(k) or 0), \
             mock.patch.object(spawn, "require_board", lambda *a, **k: None), \
             mock.patch.object(spawn, "require_no_repo_config",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_acceptance_gate",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_requirement_linkage",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_doctor", lambda *a, **k: None), \
             mock.patch.object(spawn, "ensure_target_remote",
                               lambda *a, **k: None), \
             mock.patch.object(sys, "argv",
                               ["spawn.py", _ROLE, "task", "--issue",
                                str(_ISSUE)]):
            spawn.main()
        self.assertIs(calls.get("checkpoint"), False)

    def test_checkpoint_conflicts_with_single_phase(self):
        with mock.patch.object(spawn, "require_board", lambda *a, **k: None), \
             mock.patch.object(spawn, "require_no_repo_config",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_acceptance_gate",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_requirement_linkage",
                               lambda *a, **k: None), \
             mock.patch.object(sys, "argv",
                               ["spawn.py", _ROLE, "task", "--issue",
                                str(_ISSUE), "--checkpoint",
                                "--single-phase"]):
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        self.assertIn("mutually exclusive", str(cm.exception))

    def test_checkpoint_requires_issue(self):
        with mock.patch.object(spawn, "require_board", lambda *a, **k: None), \
             mock.patch.object(spawn, "require_no_repo_config",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_acceptance_gate",
                               lambda *a, **k: None), \
             mock.patch.object(spawn, "require_requirement_linkage",
                               lambda *a, **k: None), \
             mock.patch.object(sys, "argv",
                               ["spawn.py", _ROLE, "task", "--checkpoint"]):
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        self.assertIn("--issue", str(cm.exception))

    def test_await_approval_usage_requires_issue_and_role(self):
        with mock.patch.object(sys, "argv", ["spawn.py", "await-approval"]):
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        self.assertIn("await-approval", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
