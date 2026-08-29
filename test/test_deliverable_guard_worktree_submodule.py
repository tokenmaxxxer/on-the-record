"""Regression test for issue #2659: deliverable-guard's board-repo
activation walk used to find the root by walking up for a directory
literally named ".git". In a linked worktree or a submodule, ".git" at
the checkout root is a FILE holding a "gitdir: <path>" pointer, not a
directory — the walk matched nothing, and the hook's fallback on "no
root found" was to ALLOW the write outright (fail-open, in a guard,
exactly where the layout is unusual).

Runs the real shipped hook (`bash on-the-record/hooks/deliverable-guard.sh`)
via a real PreToolUse JSON payload on stdin, against three real git
layouts — an ordinary clone, a linked `git worktree add` checkout, and a
submodule checkout — same harness shape as
test/test_deliverable_guard_priorities_shard.py.

Run: python3 -m pytest test/test_deliverable_guard_worktree_submodule.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "deliverable-guard.sh"

# Avoid the system tempdir: on this machine /tmp itself carries a stray
# ".git" directory, which would silently satisfy the very os.path.isdir
# check this issue is about and mask the bug under test. Same rationale
# as test_deliverable_guard_priorities_shard.py's _FIXTURE_BASE.
_FIXTURE_BASE = Path.home() / ".otr-dg-test-fixture" / "worktree-submodule"


def _run_gate(repo: Path, file_path: str, cwd: str | None = None):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path},
        "cwd": cwd if cwd is not None else str(repo),
        "session_id": "test-sess",
    })
    env = dict(os.environ)
    env.pop("TOKENMAXXXER_SPAWNED", None)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


class DeliverableGuardLayoutParityTest(unittest.TestCase):
    """Acceptance: the same payload reaches the same verdict in an
    ordinary clone, a linked worktree, and a submodule."""

    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)

        self.clone = base / "clone"
        self.clone.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.clone, check=True)
        (self.clone / "README.md").write_text("hi\n")
        subprocess.run(["git", "add", "-A"], cwd=self.clone, check=True)
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-q", "-m", "init"],
            cwd=self.clone, check=True)

        subprocess.run(["git", "branch", "wt-branch"], cwd=self.clone,
                        check=True)
        self.worktree = base / "wt"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(self.worktree),
             "wt-branch"],
            cwd=self.clone, check=True)

        self.super = base / "super"
        self.super.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.super, check=True)
        subprocess.run(
            ["git", "-c", "protocol.file.allow=always", "submodule", "add",
             "-q", str(self.clone), "sub"],
            cwd=self.super, check=True)
        self.submodule = self.super / "sub"

    def _layouts(self):
        return [
            ("ordinary clone", self.clone),
            ("linked worktree", self.worktree),
            ("submodule", self.submodule),
        ]

    def test_deny_shaped_write_denied_in_every_layout(self):
        for label, repo in self._layouts():
            with self.subTest(layout=label):
                r = _run_gate(repo, str(repo / "src/x.py"), cwd=str(repo))
                self.assertEqual(r.returncode, 2, f"{label}: {r.stderr}")

    def test_allow_shaped_write_allowed_in_every_layout(self):
        for label, repo in self._layouts():
            with self.subTest(layout=label):
                r = _run_gate(
                    repo, str(repo / "docs/specs/approvers.md"),
                    cwd=str(repo))
                self.assertEqual(r.returncode, 0, f"{label}: {r.stderr}")

    def test_git_file_is_recognized_not_just_git_directory(self):
        # The defect's own shape: confirm .git is actually a FILE (not a
        # directory) in the two non-ordinary layouts, so a pass above
        # isn't accidentally exercising the directory-only old path.
        self.assertTrue((self.worktree / ".git").is_file())
        self.assertTrue((self.submodule / ".git").is_file())


class DeliverableGuardCannotDetermineTest(unittest.TestCase):
    """Acceptance: when the root genuinely cannot be determined, the
    outcome is a refusal that says so, not an allow."""

    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

        # A minimal PATH with no `git` on it: the hook's own git
        # rev-parse call cannot run, so it genuinely cannot determine
        # whether the write is inside a git repository.
        self._nogit_bin = Path(self._tmp.name) / "nogit-bin"
        self._nogit_bin.mkdir()
        for tool in ("bash", "python3", "sh", "env", "cat"):
            real = subprocess.run(
                ["/bin/sh", "-c", f"command -v {tool}"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            if real:
                (self._nogit_bin / tool).symlink_to(real)

    def test_missing_git_binary_refuses_with_explanation(self):
        payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "src/x.py"},
            "cwd": str(self.repo),
            "session_id": "test-sess",
        })
        env = {"PATH": str(self._nogit_bin), "HOME": os.environ.get("HOME", "")}
        r = subprocess.run(
            ["bash", str(HOOK_PATH)],
            input=payload, capture_output=True, text=True,
            cwd=self.repo, env=env, timeout=30,
        )
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("could not determine", r.stderr)
        self.assertNotIn("deliverable path in a board repo", r.stderr)


if __name__ == "__main__":
    unittest.main()
