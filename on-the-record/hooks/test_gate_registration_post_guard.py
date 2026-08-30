"""Regression test for issue #2705: gate-registration-guard.sh's
PreToolUse read of `git diff --cached` fires before the intercepted Bash
command's text runs, so a bundled `git add gates/new_gate.py && git
commit` in ONE Bash call has nothing staged at hook-fire time and passes
silently. gate-registration-post-guard.sh is the weaker-promise companion
that catches that exact shape after the fact, by reading git's own
commit-success output rather than predicting the staged set from command
text.

Runs the real shipped hook (`bash on-the-record/hooks/
gate-registration-post-guard.sh <mode>`) via real PreToolUse/PostToolUse
JSON payloads on stdin, against a real git repo fixture — same harness
shape as test/test_deliverable_guard_worktree_submodule.py.

Run: python3 -m pytest on-the-record/hooks/test_gate_registration_post_guard.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "gate-registration-post-guard.sh"


def _run(mode: str, payload: dict, state_dir: Path, cwd: Path):
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    env["OTR_GRG_POST_STATE_DIR"] = str(state_dir)
    return subprocess.run(
        ["bash", str(HOOK_PATH), mode],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=cwd, env=env, timeout=30,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                           text=True, timeout=30, check=True)


class GateRegistrationPostGuardTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="otr-grg-post-test-")
        self.repo = Path(self._tmp.name) / "repo"
        self.state_dir = Path(self._tmp.name) / "state"
        self.repo.mkdir()
        self.state_dir.mkdir()
        _git(self.repo, "init", "-q")
        _git(self.repo, "config", "user.email", "a@b.c")
        _git(self.repo, "config", "user.name", "Test")
        (self.repo / "gates").mkdir()
        (self.repo / "docs" / "specs").mkdir(parents=True)
        (self.repo / "on-the-record" / "hooks").mkdir(parents=True)
        (self.repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
            "| mechanism | verdict |\n|---|---|\n"
        )
        (self.repo / "docs" / "specs" / "generated-paths.md").write_text(
            "| mechanism | classification | verdict |\n|---|---|---|\n"
        )
        (self.repo / "on-the-record" / "hooks" / "hooks.json").write_text(
            json.dumps({"hooks": {}})
        )
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def _commit_bundled(self, rel_path: str, content: str, message: str) -> str:
        """Simulates `git add <rel_path> && git commit -m <message>` as one
        shell call and returns git's own stdout — the exact tool_response
        text a real bundled Bash call would have produced."""
        full = self.repo / rel_path
        full.write_text(content)
        result = subprocess.run(
            f"git add {rel_path} && git commit -m {message!r}",
            shell=True, cwd=self.repo, capture_output=True, text=True,
            timeout=30, check=True,
        )
        return result.stdout

    def test_bundled_add_and_commit_of_unregistered_gate_is_recorded(self):
        stdout = self._commit_bundled(
            "gates/new_gate.py", "def check(): pass", "add new gate")
        # This is the bug #2705 documents: at PreToolUse-fire time (before
        # the bundled command runs) nothing is staged yet.
        cached = _git(self.repo, "diff", "--cached", "--name-status").stdout
        self.assertEqual(cached, "", "fixture invariant: nothing staged pre-run")

        payload = {
            "session_id": "sess-1", "tool_name": "Bash", "cwd": str(self.repo),
            "tool_input": {"command": "git add gates/new_gate.py && git commit -m x"},
            "tool_response": stdout,
        }
        post = _run("post", payload, self.state_dir, self.repo)
        self.assertEqual(post.returncode, 0, post.stderr)  # post never denies

        state_file = self.state_dir / "sess-1.json"
        self.assertTrue(state_file.exists())
        violations = json.loads(state_file.read_text())["violations"]
        self.assertEqual(len(violations), 1)
        self.assertIn("gates/new_gate.py", violations[0]["path"])

    def test_pre_mode_warns_then_clears_once_row_lands(self):
        stdout = self._commit_bundled(
            "gates/new_gate.py", "def check(): pass", "add new gate")
        payload = {
            "session_id": "sess-2", "tool_name": "Bash", "cwd": str(self.repo),
            "tool_input": {"command": "git add gates/new_gate.py && git commit -m x"},
            "tool_response": stdout,
        }
        self.assertEqual(_run("post", payload, self.state_dir, self.repo).returncode, 0)

        next_call = {"session_id": "sess-2", "cwd": str(self.repo),
                     "tool_name": "Read", "tool_input": {}}
        warned = _run("pre", next_call, self.state_dir, self.repo)
        self.assertEqual(warned.returncode, 0)
        out = json.loads(warned.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("gates/new_gate.py", ctx)
        self.assertIn("cannot be blocked or reverted", ctx)
        self.assertIn("gate-registration-guard.sh", ctx)

        # Fix it: add the row in a follow-up commit.
        (self.repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
            "| mechanism | verdict |\n|---|---|\n| `new_gate.py` | ok |\n"
        )
        _git(self.repo, "add", "docs/specs/enforcement-boundary.md")
        _git(self.repo, "commit", "-q", "-m", "register")

        resolved = _run("pre", next_call, self.state_dir, self.repo)
        self.assertEqual(resolved.returncode, 0)
        self.assertEqual(resolved.stdout.strip(), "", resolved.stdout)
        # issue #2705 CHANGES round: a resolved violation must delete its
        # state file, not leave a `{"violations": []}` file behind -- that
        # leftover file is exactly what defeats the `pre`-mode bash-only
        # fast path (existence-only check) forever.
        state_file = self.state_dir / "sess-2.json"
        self.assertFalse(state_file.exists(), "resolved state file should be removed")

    def test_bundled_add_and_commit_with_row_already_staged_is_clean(self):
        (self.repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
            "| mechanism | verdict |\n|---|---|\n| `clean_gate.py` | ok |\n"
        )
        _git(self.repo, "add", "docs/specs/enforcement-boundary.md")
        _git(self.repo, "commit", "-q", "-m", "pre-register")
        stdout = self._commit_bundled(
            "gates/clean_gate.py", "def clean(): pass", "add clean gate")
        payload = {
            "session_id": "sess-3", "tool_name": "Bash", "cwd": str(self.repo),
            "tool_input": {"command": "git add gates/clean_gate.py && git commit -m x"},
            "tool_response": stdout,
        }
        post = _run("post", payload, self.state_dir, self.repo)
        self.assertEqual(post.returncode, 0, post.stderr)
        # issue #2705 CHANGES round: a clean commit must not leave a state
        # file behind at all -- see test_pre_mode_warns_then_clears_once_row_lands.
        state_file = self.state_dir / "sess-3.json"
        self.assertFalse(state_file.exists(), "clean commit should write no state file")

    def test_non_bash_tool_is_noop(self):
        payload = {"session_id": "sess-4", "tool_name": "Write",
                   "cwd": str(self.repo), "tool_input": {},
                   "tool_response": "[master abc1234] fake"}
        result = _run("post", payload, self.state_dir, self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.state_dir / "sess-4.json").exists())

    def test_no_commit_success_line_in_response_is_noop(self):
        payload = {"session_id": "sess-5", "tool_name": "Bash",
                   "cwd": str(self.repo),
                   "tool_input": {"command": "git add gates/new_gate.py && git commit --quiet -m x"},
                   "tool_response": ""}
        result = _run("post", payload, self.state_dir, self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.state_dir / "sess-5.json").exists())

    def test_unbundled_shape_is_still_refused_by_the_unchanged_pre_guard(self):
        """gate-registration-guard.sh itself (not this file) must still
        refuse the unbundled shape exactly as before #2705 — proves the
        new post-guard is additive, not a replacement."""
        (self.repo / "gates" / "second_gate.py").write_text("def x(): pass")
        _git(self.repo, "add", "gates/second_gate.py")
        pre_guard = REPO_ROOT / "on-the-record" / "hooks" / "gate-registration-guard.sh"
        payload = {"tool_name": "Bash", "cwd": str(self.repo),
                   "tool_input": {"command": "git commit -m add-second-gate"}}
        result = subprocess.run(
            ["bash", str(pre_guard)], input=json.dumps(payload),
            capture_output=True, text=True, cwd=self.repo, timeout=30,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("gates/second_gate.py", result.stderr)

    def test_pre_mode_fast_path_survives_a_resolved_violation(self):
        """issue #2705 CHANGES round: the pre-mode bash-only short-circuit
        (checked before any process spawn, on every tool call) must not be
        a one-way door. A state file left behind after resolution -- even
        holding an empty `violations` list -- would defeat that
        short-circuit permanently for every later tool call sharing this
        TMPDIR, since it tests file existence, not content.

        Proven here with a `python3` stub on PATH that writes a marker
        file when invoked: if the bash-only fast path returns before ever
        reaching `python3 -c "$GUARD"`, the marker is never created,
        regardless of what the stub would have done. A real violation
        (state file present) must still reach the interpreter; a resolved
        one (state file removed) must not."""
        marker = Path(self._tmp.name) / "python3-invoked.marker"
        stub_dir = Path(self._tmp.name) / "python-stub-bin"
        stub_dir.mkdir()
        stub = stub_dir / "python3"
        # exec the REAL interpreter by its absolute path, not by PATH
        # lookup -- the stub dir is prepended to PATH below, so a bare
        # `python3`/`env python3` re-lookup would just re-invoke this
        # same stub forever.
        stub.write_text(f"#!/bin/sh\ntouch {marker}\nexec {sys.executable} \"$@\"\n")
        stub.chmod(0o755)
        env = dict(os.environ)
        env["OTR_GRG_POST_STATE_DIR"] = str(self.state_dir)
        env.pop("ORCHESTRATE_OFF", None)
        env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"

        def _run_with_stub(mode: str, payload: dict) -> subprocess.CompletedProcess:
            marker.unlink(missing_ok=True)
            return subprocess.run(
                ["bash", str(HOOK_PATH), mode], input=json.dumps(payload),
                capture_output=True, text=True, cwd=self.repo, env=env, timeout=30,
            )

        stdout = self._commit_bundled(
            "gates/new_gate.py", "def check(): pass", "add new gate")
        payload = {
            "session_id": "sess-7", "tool_name": "Bash", "cwd": str(self.repo),
            "tool_input": {"command": "git add gates/new_gate.py && git commit -m x"},
            "tool_response": stdout,
        }
        self.assertEqual(_run_with_stub("post", payload).returncode, 0)

        next_call = {"session_id": "sess-7", "cwd": str(self.repo),
                     "tool_name": "Read", "tool_input": {}}
        self.assertEqual(_run_with_stub("pre", next_call).returncode, 0)
        self.assertTrue(marker.exists(),
                         "an open violation must still reach the interpreter")

        (self.repo / "docs" / "specs" / "enforcement-boundary.md").write_text(
            "| mechanism | verdict |\n|---|---|\n| `new_gate.py` | ok |\n"
        )
        _git(self.repo, "add", "docs/specs/enforcement-boundary.md")
        _git(self.repo, "commit", "-q", "-m", "register")
        resolved = _run_with_stub("pre", next_call)
        self.assertEqual(resolved.returncode, 0)
        self.assertTrue(marker.exists(),
                         "resolving still requires one interpreter pass to re-check the tree")
        self.assertFalse((self.state_dir / "sess-7.json").exists())

        # The NEXT pre call, with the state file gone, must take the
        # bash-only fast path and never touch the (stubbed) interpreter.
        final = _run_with_stub("pre", next_call)
        self.assertEqual(final.returncode, 0)
        self.assertEqual(final.stdout.strip(), "")
        self.assertFalse(marker.exists(),
                          "fast path must not spawn python3 once no state file exists")

    def test_orchestrate_off_disables_both_modes(self):
        stdout = self._commit_bundled(
            "gates/new_gate.py", "def check(): pass", "add new gate")
        payload = {
            "session_id": "sess-6", "tool_name": "Bash", "cwd": str(self.repo),
            "tool_input": {"command": "git add gates/new_gate.py && git commit -m x"},
            "tool_response": stdout,
        }
        env = dict(os.environ)
        env["ORCHESTRATE_OFF"] = "1"
        env["OTR_GRG_POST_STATE_DIR"] = str(self.state_dir)
        result = subprocess.run(
            ["bash", str(HOOK_PATH), "post"], input=json.dumps(payload),
            capture_output=True, text=True, cwd=self.repo, env=env, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse((self.state_dir / "sess-6.json").exists())


if __name__ == "__main__":
    unittest.main()
