"""issue #2326 Ask #2 acceptance gate: `lint-test-on-edit.sh` is a real,
wired `PostToolUse` hook that shortens the fail->re-edit rework loop
(rework fraction re-derived in docs/issue-2326/reports/diagnose-first-
71f82584.md against the live $MUSTER_WORKSPACE_ROOT session-log corpus).
This test invokes the real shipped hook script
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
TIMEOUT_PLUGIN_PATH = (
    REPO_ROOT / "on-the-record" / "hooks" / "otr_lint_test_timeout_plugin.py"
)
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

    def test_timeout_plugin_file_exists(self):
        self.assertTrue(TIMEOUT_PLUGIN_PATH.is_file(), TIMEOUT_PLUGIN_PATH)


def _assert_post_tool_use_additive(before_commands: set, after_commands: set) -> None:
    """The additive-only guard: raises AssertionError iff a PostToolUse
    `command` string present in `before_commands` is missing from
    `after_commands`. Deliberately repo-state-independent -- it must
    pass when `before == after` (the state right after this change has
    merged and `origin/main` already contains it too), and fail only
    when something was actually removed. Shared with
    gates/probe_hooks_additive_survives_merge.py (issue #3083) so that
    module's before/after-identical and removal simulations exercise
    this exact function, not a reimplementation of it."""
    missing = before_commands - after_commands
    assert missing == set(), (
        "PostToolUse commands removed by this change: %s" % missing)


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
        _assert_post_tool_use_additive(before_commands, after_commands)


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

    def test_dotdot_traversal_does_not_fool_the_docs_fast_path(self):
        """issue #2326 round 3 hunt finding: a `file_path` like
        `docs/../real.py` matches the bash fast path's `docs/*` glob on
        the raw, un-normalized string, even though it normalizes to a
        real code file. The bash fast path must fall through to
        python's authoritative posixpath.normpath check instead of
        fast-skipping on any guess containing `..`."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            _git_init(repo)
            bad = repo / "broken_repro.py"
            bad.write_text("def foo(:\n    pass\n")

            payload = json.dumps({
                "tool_name": "Edit",
                "tool_input": {"file_path": "docs/../broken_repro.py"},
                "cwd": str(repo),
                "session_id": "test-sess",
            })
            r = _run_hook(payload, cwd=repo)

            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            ctx = out["hookSpecificOutput"]["additionalContext"]
            self.assertIn("lint failed", ctx)

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
    """These fixture test files use `from good import add` / `import
    good`, which import-graph selection matches on the module stem --
    the same shape the shipped hook's own selector looks for, just not
    limited to a `test_<stem>.py` filename match."""

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

    def test_descriptive_multi_word_test_name_is_matched_by_import_not_stem(self):
        """The failure mode round 2 found: this repo's own test-naming
        convention is descriptive multi-word names, not `test_<stem>.py`.
        A test file named nothing like the module still gets selected as
        long as it imports the module."""
        src = self.repo / "widget.py"
        src.write_text("def broken():\n    raise ValueError('nope')\n")
        (self.repo / "tests" / "test_widget_behavior_end_to_end.py").write_text(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import widget\n\n\n"
            "def test_calls_broken():\n"
            "    widget.broken()\n" % str(self.repo)
        )

        r = _run_hook(_payload(src, self.repo), cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("impacted test failed", ctx)
        self.assertIn("test_widget_behavior_end_to_end.py", ctx)


class PerFileTimeoutBoundsSlowMatchWithoutExcludingByName(unittest.TestCase):
    """issue #2326 round 3: import-graph selection can match many test
    files for a high-fan-in module; one matched file with an unrelated
    long-running test must not block the whole invocation or blow the
    combined budget, and must not need to be excluded by filename to be
    bounded."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)
        (self.repo / "tests").mkdir()

    def test_slow_matched_file_is_bounded_and_fast_matched_file_still_reports(self):
        src = self.repo / "shared_module.py"
        src.write_text("def broken():\n    raise ValueError('nope')\n")
        (self.repo / "tests" / "test_fast_consumer.py").write_text(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import shared_module\n\n\n"
            "def test_calls_broken():\n"
            "    shared_module.broken()\n" % str(self.repo)
        )
        (self.repo / "tests" / "test_slow_unrelated_consumer.py").write_text(
            "import sys, time\n"
            "sys.path.insert(0, %r)\n"
            "import shared_module\n\n\n"
            "def test_sleeps_long_and_unrelated():\n"
            "    time.sleep(20)\n" % str(self.repo)
        )

        t0 = time.monotonic()
        r = _run_hook(
            _payload(src, self.repo), cwd=self.repo,
            env_extra={
                "OTR_LINT_TEST_PER_FILE_TIMEOUT_S": "1",
                "OTR_LINT_TEST_BUDGET_S": "15",
            },
        )
        elapsed = time.monotonic() - t0

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertLess(
            elapsed, 10,
            "per-file timeout did not bound the slow match: took %.1fs" % elapsed)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("impacted test failed", ctx)
        self.assertIn("test_fast_consumer.py", ctx)
        self.assertIn("test_slow_unrelated_consumer.py", ctx)
        self.assertIn("otr-per-file-timeout", ctx)


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


class SymlinkDocsFastPathIsNotFooled(unittest.TestCase):
    """issue #2326 round 4 finding: a docs/-prefixed symlink pointing at
    real code (`docs/live_spawn.py -> ../spawn.py`) defeated both the
    bash fast path and the old python check, since neither ever
    resolved symlinks before classifying the path as docs-only."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)

    def test_docs_symlink_to_real_code_is_not_skipped(self):
        real = self.repo / "spawn.py"
        real.write_text("def broken(:\n    pass\n")
        docs_dir = self.repo / "docs"
        docs_dir.mkdir()
        link = docs_dir / "live_spawn.py"
        link.symlink_to(Path("..") / "spawn.py")

        payload = json.dumps({
            "tool_name": "Write",
            "tool_input": {"file_path": "docs/live_spawn.py"},
            "cwd": str(self.repo),
            "session_id": "test-sess",
        })
        r = _run_hook(payload, cwd=self.repo)

        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("lint failed", ctx)


class GitWorktreeRootIsRecognized(unittest.TestCase):
    """issue #2326 round 4 finding: the repo-root walk only recognized a
    real `.git` directory, never a `git worktree` checkout's `.git`
    file -- nested under an ancestor with its own `.git`, impacted-test
    selection silently found zero candidates under the wrong root."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.outer = Path(self._tmp.name) / "outer"
        _git_init(self.outer)

    def test_worktree_git_file_root_is_used_not_the_ancestor(self):
        inner_source = Path(self._tmp.name) / "inner-source"
        _git_init(inner_source)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-q", "-m", "init"],
            cwd=inner_source, check=True, timeout=30)
        worktree = self.outer / "nested-worktree"
        subprocess.run(
            ["git", "worktree", "add", "-q", str(worktree)],
            cwd=inner_source, check=True, timeout=30)
        self.assertTrue((worktree / ".git").is_file(),
                         "expected a worktree .git FILE at %s" % worktree)

        (worktree / "tests").mkdir()
        src = worktree / "shared_thing.py"
        src.write_text("def broken():\n    raise ValueError('nope')\n")
        (worktree / "tests" / "test_shared_thing.py").write_text(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import shared_thing\n\n\n"
            "def test_calls_broken():\n"
            "    shared_thing.broken()\n" % str(worktree)
        )

        r = _run_hook(_payload(src, worktree), cwd=worktree)

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(
            r.stdout.strip(), "",
            "worktree root misresolution silently found zero impacted "
            "tests")
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("impacted test failed", ctx)
        self.assertIn("test_shared_thing.py", ctx)


class BudgetExceededIsNeverMistakableForClean(unittest.TestCase):
    """issue #2326 round 4's decisive finding: a budget-exceeded run
    must always emit an explicit, non-empty report -- and if any
    impacted test already failed before the clock ran out, that
    specific failure must be surfaced, never silently discarded in
    favor of a generic message that reads like a pass."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)
        (self.repo / "tests").mkdir()

    def test_partial_failure_already_confirmed_before_timeout_is_surfaced(self):
        src = self.repo / "shared_thing.py"
        src.write_text("def broken():\n    raise ValueError('nope')\n")
        (self.repo / "tests" / "test_a_fails_fast.py").write_text(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import shared_thing\n\n\n"
            "def test_calls_broken():\n"
            "    shared_thing.broken()\n" % str(self.repo)
        )
        (self.repo / "tests" / "test_b_sleeps_past_budget.py").write_text(
            "import sys, time\n"
            "sys.path.insert(0, %r)\n"
            "import shared_thing\n\n\n"
            "def test_sleeps():\n"
            "    time.sleep(30)\n" % str(self.repo)
        )

        r = _run_hook(
            _payload(src, self.repo), cwd=self.repo,
            env_extra={
                "OTR_LINT_TEST_PER_FILE_TIMEOUT_S": "100",
                "OTR_LINT_TEST_BUDGET_S": "5",
            },
            timeout=30,
        )

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(r.stdout.strip(), "",
                             "budget-exceeded run must never be silent")
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("budget exceeded", ctx)
        self.assertIn("ALREADY CONFIRMED FAILING", ctx)
        self.assertIn("test_a_fails_fast.py", ctx)
        self.assertNotIn("verdict INCOMPLETE", ctx,
                          "a confirmed failure must be reported as a "
                          "failure, not folded into the generic "
                          "no-evidence incomplete message")

    def test_no_evidence_recovered_still_reports_explicit_incomplete(self):
        src = self.repo / "lonely_module.py"
        src.write_text("def noop():\n    return None\n")
        (self.repo / "tests" / "test_only_sleeps.py").write_text(
            "import sys, time\n"
            "sys.path.insert(0, %r)\n"
            "import lonely_module\n\n\n"
            "def test_sleeps():\n"
            "    time.sleep(30)\n" % str(self.repo)
        )

        r = _run_hook(
            _payload(src, self.repo), cwd=self.repo,
            env_extra={
                "OTR_LINT_TEST_PER_FILE_TIMEOUT_S": "100",
                "OTR_LINT_TEST_BUDGET_S": "3",
            },
            timeout=30,
        )

        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(r.stdout.strip(), "",
                             "budget-exceeded run must never be silent")
        out = json.loads(r.stdout)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("budget exceeded", ctx)
        self.assertIn("INCOMPLETE", ctx)
        self.assertIn("NOT verified clean", ctx)


class ConcurrentInvocationsNeverReportSilently(unittest.TestCase):
    """issue #2326 round 4's decisive finding, reproduced at CI scale:
    under real concurrent contention (the hook's actual deployment
    shape -- fires on every edit, fleet-wide), some invocations used to
    hit the budget and discard whatever partial evidence existed.
    Every invocation, budget-exceeded or not, must still emit
    something -- never bare empty stdout -- and a confirmed failure
    must never be silently replaced by a generic message."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _git_init(self.repo)
        (self.repo / "tests").mkdir()
        self.src = self.repo / "shared_thing.py"
        self.src.write_text("def broken():\n    raise ValueError('nope')\n")
        (self.repo / "tests" / "test_a_fails_fast.py").write_text(
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import shared_thing\n\n\n"
            "def test_calls_broken():\n"
            "    shared_thing.broken()\n" % str(self.repo)
        )
        (self.repo / "tests" / "test_b_sleeps_past_budget.py").write_text(
            "import sys, time\n"
            "sys.path.insert(0, %r)\n"
            "import shared_thing\n\n\n"
            "def test_sleeps():\n"
            "    time.sleep(30)\n" % str(self.repo)
        )

    def test_no_invocation_is_silent_under_concurrency(self):
        import concurrent.futures

        def _invoke(_i):
            return _run_hook(
                _payload(self.src, self.repo), cwd=self.repo,
                env_extra={
                    "OTR_LINT_TEST_PER_FILE_TIMEOUT_S": "100",
                    "OTR_LINT_TEST_BUDGET_S": "4",
                },
                timeout=30,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(_invoke, range(6)))

        for i, r in enumerate(results):
            self.assertEqual(r.returncode, 0, "run %d: %s" % (i, r.stderr))
            self.assertNotEqual(
                r.stdout.strip(), "",
                "run %d produced bare empty stdout -- a silent budget "
                "exhaustion (issue #2326 round 4's decisive finding)"
                % i)
            out = json.loads(r.stdout)
            ctx = out["hookSpecificOutput"]["additionalContext"]
            ok = (
                ("ALREADY CONFIRMED FAILING" in ctx and
                 "test_a_fails_fast.py" in ctx)
                or "impacted test failed" in ctx
                or ("budget exceeded" in ctx and "INCOMPLETE" in ctx)
            )
            self.assertTrue(ok, "run %d: unrecognized report shape: %s"
                             % (i, ctx))


class PluginMissingIsDistinguishedFromRealFailure(unittest.TestCase):
    """issue #2326 round 4 finding: if the harness's own timeout plugin
    cannot be imported, pytest's own ModuleNotFoundError traceback used
    to render identically to a real multi-test failure. Copies the
    hooks directory aside and removes the plugin file there to force
    this condition without touching the real shipped file."""

    def test_plugin_missing_reports_harness_internal_error(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            hooks_copy = Path(tmp) / "hooks"
            shutil.copytree(REPO_ROOT / "on-the-record" / "hooks",
                             hooks_copy)
            (hooks_copy / "otr_lint_test_timeout_plugin.py").unlink()

            repo = Path(tmp) / "repo"
            _git_init(repo)
            (repo / "tests").mkdir()
            src = repo / "thing.py"
            src.write_text("def f():\n    return 1\n")
            (repo / "tests" / "test_thing.py").write_text(
                "import sys\n"
                "sys.path.insert(0, %r)\n"
                "import thing\n\n\n"
                "def test_uses_it():\n"
                "    assert thing.f() == 1\n" % str(repo)
            )

            env = dict(os.environ)
            env.pop("ORCHESTRATE_OFF", None)
            r = subprocess.run(
                [BASH_BIN, str(hooks_copy / "lint-test-on-edit.sh"), "post"],
                input=_payload(src, repo), capture_output=True, text=True,
                cwd=str(repo), env=env, timeout=30,
            )

            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout)
            ctx = out["hookSpecificOutput"]["additionalContext"]
            self.assertIn("harness internal error", ctx)
            self.assertNotIn("impacted test failed", ctx)


if __name__ == "__main__":
    unittest.main()
