"""issue #2326 Ask #2 acceptance gate: `lint-test-on-edit.sh` is a real,
wired `PostToolUse` hook that shortens the fail->re-edit rework loop the
issue's own measurement found (across 17 real session transcripts, 7.9%
of edit turns -- 18/228 -- sat inside such a loop, costing a median 41/
mean 54.6 turns per episode, up to 98 in the worst family, once it
happens). This test invokes the real shipped hook script
(`bash on-the-record/hooks/lint-test-on-edit.sh post`) via a real
`PostToolUse` JSON payload on stdin, against real synthetic files on
disk -- same harness shape as
test/test_upstream_defect_scope_guard_cross_repo_cwd.py -- not a mock of
the hook's own internals.

  python3 -m pytest tests/test_spawn_gate_wiring.py -q
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "lint-test-on-edit.sh"
WRAPPER_PATH = REPO_ROOT / "on-the-record" / "hooks" / "fail-open-wrapper.sh"
HOOKS_JSON_PATH = REPO_ROOT / "on-the-record" / "hooks" / "hooks.json"
# resolved once, against the *unmodified* environment -- used as argv[0]
# so a test that strips PATH down (to prove python3-missing fail-open)
# doesn't also make `bash` itself unresolvable.
BASH_BIN = shutil.which("bash") or "/bin/bash"


def _git_init(repo: Path) -> None:
    """A real `.git` at the fixture root so the hook's own walk-up-for-
    `.git` root resolution (same pattern accumulation-claim-guard.sh
    uses) lands on the fixture itself, not some unrelated ancestor."""
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, timeout=30)


def _run_hook(payload_text: str, cwd: Path, env_extra: dict | None = None,
              timeout: float = 30):
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [BASH_BIN, str(HOOK_PATH), "post"],
        input=payload_text, capture_output=True, text=True,
        cwd=str(cwd), env=env, timeout=timeout,
    )


def _payload(file_path: Path, cwd: Path, session_id: str = "test-sess") -> str:
    return json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": str(file_path)},
        "cwd": str(cwd),
        "session_id": session_id,
    })


class HookScriptShippedAndExecutable(unittest.TestCase):
    def test_hook_file_exists_and_is_executable(self):
        self.assertTrue(HOOK_PATH.is_file(), HOOK_PATH)
        self.assertTrue(os.access(HOOK_PATH, os.X_OK),
                         "%s is not executable" % HOOK_PATH)


class HooksJsonWiringIsAdditive(unittest.TestCase):
    """Wired via fail-open-wrapper.sh, same as every other PostToolUse
    hook, and no pre-existing PostToolUse entry was removed to make room
    for it."""

    def setUp(self):
        self.hooks = json.loads(HOOKS_JSON_PATH.read_text())

    def test_post_tool_use_entry_wraps_the_new_hook_via_fail_open_wrapper(self):
        post = self.hooks["hooks"]["PostToolUse"]
        commands = [
            h["command"]
            for block in post
            for h in block.get("hooks", [])
        ]
        matches = [
            c for c in commands
            if "fail-open-wrapper.sh" in c and "lint-test-on-edit.sh" in c
        ]
        self.assertEqual(len(matches), 1, commands)
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh",
                       matches[0])

    def test_pre_existing_post_tool_use_commands_are_all_still_present(self):
        """Diffs hooks.json against git HEAD (or the merge-base with
        origin/main when available) and asserts every PostToolUse
        `command` string that existed before this change is still
        present verbatim -- additive-only, nothing removed/reordered
        away."""
        base_ref = None
        for candidate in ("origin/main", "HEAD"):
            r = subprocess.run(
                ["git", "rev-parse", "--verify", candidate],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)
            if r.returncode == 0:
                base_ref = candidate
                break
        if base_ref is None:
            self.skipTest("no git ref available to diff hooks.json against")

        show = subprocess.run(
            ["git", "show", "%s:on-the-record/hooks/hooks.json" % base_ref],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)
        if show.returncode != 0:
            self.skipTest("hooks.json not present at %s" % base_ref)
        before = json.loads(show.stdout)
        before_commands = {
            h["command"]
            for block in before.get("hooks", {}).get("PostToolUse", [])
            for h in block.get("hooks", [])
        }
        after_commands = {
            h["command"]
            for block in self.hooks["hooks"]["PostToolUse"]
            for h in block.get("hooks", [])
        }
        missing = before_commands - after_commands
        self.assertEqual(missing, set(),
                          "PostToolUse commands removed by this change: %s"
                          % missing)
        self.assertGreater(len(after_commands), len(before_commands))


class DocsOnlyEmptyState(unittest.TestCase):
    """Acceptance's stated empty state: a docs-only edit fires no
    lint/test subprocess at all, and costs effectively zero added
    latency."""

    def test_docs_md_path_produces_no_additional_context_and_is_fast(self):
        payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/issue-2326/reports/notes.md"},
            "cwd": str(REPO_ROOT),
            "session_id": "test-sess",
        })
        t0 = time.monotonic()
        r = _run_hook(payload, cwd=REPO_ROOT)
        elapsed = time.monotonic() - t0

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "", r.stdout)
        self.assertLess(elapsed, 0.5,
                         "docs-only path took %.3fs, expected < 0.5s" % elapsed)

    def test_docs_nested_and_txt_rst_also_skip(self):
        for fp in ("docs/a/b/c/deep.md", "notes.txt", "readme.rst",
                   "some/nested/docs/path/file.py"):
            with self.subTest(fp=fp):
                payload = json.dumps({
                    "tool_name": "Write",
                    "tool_input": {"file_path": fp},
                    "cwd": str(REPO_ROOT),
                    "session_id": "test-sess",
                })
                r = _run_hook(payload, cwd=REPO_ROOT)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), "", r.stdout)


class CodeEditSyntaxErrorSurfacesAsAdditionalContext(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)

    def test_python_syntax_error_reported(self):
        bad = self.repo / "broken.py"
        bad.write_text("def foo(:\n    pass\n")

        r = _run_hook(_payload(bad, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("lint failed", ctx)
        self.assertTrue("SyntaxError" in ctx or "syntax" in ctx.lower(), ctx)

    def test_shell_syntax_error_reported(self):
        bad = self.repo / "broken.sh"
        bad.write_text("if [ true ]\n  echo missing then\n")

        r = _run_hook(_payload(bad, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("lint failed", ctx)


class PassingCodeProducesNoFalsePositive(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)
        (self.repo / "tests").mkdir()

    def _write_good(self, passing: bool):
        src = self.repo / "good.py"
        src.write_text("def add(a, b):\n    return a + b\n")
        expected = 3 if passing else 999
        (self.repo / "tests" / "test_good.py").write_text(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "from good import add\n\n\n"
            "def test_add():\n"
            "    assert add(1, 2) == %d\n" % (str(self.repo), expected)
        )
        return src

    def test_valid_py_with_passing_impacted_test_has_no_failure_content(self):
        src = self._write_good(passing=True)

        r = _run_hook(_payload(src, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "", r.stdout)

    def test_valid_py_with_failing_impacted_test_is_reported(self):
        src = self._write_good(passing=False)

        r = _run_hook(_payload(src, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("impacted test failed", ctx)
        self.assertIn("test_good.py", ctx)

    def test_valid_py_with_no_matching_test_file_is_silent(self):
        src = self.repo / "lonely.py"
        src.write_text("def noop():\n    return None\n")

        r = _run_hook(_payload(src, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "", r.stdout)

    def test_editing_the_test_file_itself_is_treated_as_its_own_impacted_test(self):
        (self.repo / "tests" / "test_selfcheck.py").write_text(
            "def test_x():\n    assert 1 == 2\n"
        )
        own_test = self.repo / "tests" / "test_selfcheck.py"

        r = _run_hook(_payload(own_test, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("impacted test failed", ctx)
        self.assertIn("test_selfcheck.py", ctx)


class BudgetIsHonored(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)

    def test_zero_budget_reports_budget_exceeded_without_running_checks(self):
        src = self.repo / "anything.py"
        src.write_text("def f():\n    return 1\n")

        r = _run_hook(_payload(src, self.repo),
                      cwd=self.repo, env_extra={"OTR_LINT_TEST_BUDGET_S": "0"})

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("budget exceeded", ctx)

    def test_default_budget_env_var_name_is_otr_lint_test_budget_s(self):
        """A bogus (non-numeric) budget value degrades to the built-in
        default rather than crashing the hook -- still fail-open."""
        src = self.repo / "anything.py"
        src.write_text("def f():\n    return 1\n")

        r = _run_hook(_payload(src, self.repo),
                      cwd=self.repo,
                      env_extra={"OTR_LINT_TEST_BUDGET_S": "not-a-number"})

        self.assertEqual(r.returncode, 0, r.stderr)


class FailOpenOnMalformedPayload(unittest.TestCase):
    def test_malformed_json_stdin_exits_zero_silently(self):
        r = _run_hook("{not valid json at all", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_empty_stdin_exits_zero_silently(self):
        r = _run_hook("", cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_missing_file_path_exits_zero_silently(self):
        payload = json.dumps({
            "tool_name": "Write", "tool_input": {}, "cwd": str(REPO_ROOT),
            "session_id": "test-sess",
        })
        r = _run_hook(payload, cwd=REPO_ROOT)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_no_python3_on_path_exits_zero_silently(self):
        """Strips python3 from PATH entirely -- the bash preamble's own
        `command -v python3` fail-open check must catch this before the
        python3 body ever runs."""
        env = dict(os.environ)
        env.pop("ORCHESTRATE_OFF", None)
        env["PATH"] = "/nonexistent-empty-bin-dir"
        payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "somefile.py"},
            "cwd": str(REPO_ROOT), "session_id": "test-sess",
        })
        r = subprocess.run(
            [BASH_BIN, str(HOOK_PATH), "post"],
            input=payload, capture_output=True, text=True,
            cwd=str(REPO_ROOT), env=env, timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
