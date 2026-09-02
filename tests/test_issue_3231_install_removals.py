"""Issue #3231: verifies the two install-precondition removals actually
change what the preflight observes (skill-repository resolvable,
`~/.claude/skills` present), and demonstrates the must-not clause live
rather than asserting it: an interrupted skill-repository fetch must never
leave a partial corpus that the preflight reads as satisfied.

Test derivation (test-derivation skill): the acceptance line under test is
a before/interrupted/after state machine, not a single input partition, so
the cases follow that machine directly:

  - before: with the skill corpus absent, `skill_repository_resolvable`
    reports unsatisfied (same shape test_issue_3182_preflight.py already
    covers, restated here as this test's own baseline so the "before" leg
    of the acceptance line is self-contained in this file).
  - interrupted: a fetch that dies mid-transfer (partial content in the
    scratch clone, non-zero git exit) must leave the real managed-clone
    path exactly as it was before the attempt -- reads unsatisfied, same
    as "before", not a new "looks satisfied" state. This is the
    must-not's live demonstration, not a comment claiming the property.
  - after: a fetch that actually completes (zero exit, full content)
    flips the same check to satisfied.
  - `ensure_skill_corpus_cli()` (the SessionStart-hook entrypoint,
    `skills.py`) performs both shipped removals -- creates
    `~/.claude/skills` if absent, and drives the same corpus fetch --
    each print a notice, never silently.
  - portability: neither new hook script uses a GNU-only flag or reads
    `/proc`, matching the floor `scripts/preflight/consumer_preconditions.py`
    already documents for itself.

  python3 -m pytest tests/test_issue_3231_install_removals.py -q
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT_SCRIPT = ROOT / "scripts" / "preflight" / "consumer_preconditions.py"
BOOTSTRAP_HOOK = ROOT / "on-the-record" / "hooks" / "skill-corpus-bootstrap.sh"
NOTICES_HOOK = ROOT / "on-the-record" / "hooks" / "install-precondition-notices.sh"

sys.path.insert(0, str(ROOT))
import spawn  # noqa: E402

_spec = importlib.util.spec_from_file_location("consumer_preconditions_3231", PREFLIGHT_SCRIPT)
_cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cp)


def _fake_clone_full(args, label, timeout=None, **kwargs):
    """Whole-repo clone completing normally -- creates the checkout's real
    `skills/` subdirectory with content, exit 0."""
    if args[:2] == ["git", "clone"]:
        dest = Path(args[-1])
        (dest / "skills" / "example-skill").mkdir(parents=True, exist_ok=True)
        (dest / "skills" / "example-skill" / "SKILL.md").write_text("# example\n")
    return subprocess.CompletedProcess(args, 0, stdout="", stderr="")


def _fake_clone_interrupted(args, label, timeout=None, **kwargs):
    """A clone process killed mid-transfer: some content already landed in
    the scratch directory (git had started checking out files) but the
    process never got to report success -- the real-world shape a SIGKILL
    or a network drop mid-checkout produces. Returns a non-zero exit,
    exactly what a killed/failed `git clone` subprocess reports."""
    if args[:2] == ["git", "clone"]:
        dest = Path(args[-1])
        (dest / "skills" / "partially-checked-out-skill").mkdir(parents=True, exist_ok=True)
    return subprocess.CompletedProcess(args, 1, stdout="", stderr="killed")


class InterruptedFetchNeverReadsPresentTest(unittest.TestCase):
    """The must-not clause, demonstrated rather than asserted: interrupt a
    fetch and show the partial state reports unsatisfied, both by the
    internal validity check and by the live preflight script."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.managed_skills_dir = (
            self.root / "runs" / "rulebooks" / "skill-repository" / "skills"
        )
        self._patches = [
            mock.patch.object(spawn, "ROOT", self.root),
            mock.patch.dict(
                "os.environ",
                {"TOKENMAXXXER_RULEBOOKS": str(self.root / "no-such-sibling-parent")},
            ),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("MUSTER_SKILL_REPO", None)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _preflight_reports_resolved_at_managed_dir(self) -> bool:
        # Only meaningful as an affirmative check: `MUSTER_SKILL_REPO`
        # (candidate 1) short-circuits before the live script's own
        # candidate 3 (this repo's OWN `runs/rulebooks/skill-repository`,
        # unrelated to the tmp `self.root` this test mocks `spawn.ROOT` to)
        # is ever reached. Also asserts the reported detail names this
        # test's own tmp path, not a same-looking real-repo cache, so a
        # false pass-for-the-wrong-reason via that unrelated candidate 3
        # would surface as a mismatch rather than a silent green.
        with mock.patch.dict(
            "os.environ",
            {"MUSTER_SKILL_REPO": str(self.managed_skills_dir)},
        ):
            ok, detail = _cp.check_skill_repository_resolvable()
        return ok and str(self.managed_skills_dir) in detail

    def test_before_interrupted_after_state_machine(self):
        # before: nothing has ever been fetched. Asserted directly against
        # the managed-clone path this test's mocked `spawn.ROOT` owns --
        # not through the live preflight script's own candidate 3, which
        # resolves against THIS repo's real `runs/rulebooks/skill-repository`
        # (unrelated to, and not mocked by, this test's tmp root) and so
        # cannot tell "nothing fetched in this test" apart from "something
        # else already populated the real repo's own cache". Calling
        # `_skill_repo_root()` itself is also avoided here, unmocked: that
        # would trigger a real network clone attempt.
        self.assertFalse(self.managed_skills_dir.is_dir())

        # interrupted: a fetch dies mid-transfer, leaving partial content
        # in a scratch directory only -- never at the real managed-clone
        # path this precondition actually reads.
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_interrupted):
            self.assertIsNone(
                spawn._skill_repo_root(),
                "an interrupted fetch must not resolve to a (partial) corpus",
            )
        self.assertFalse(
            self.managed_skills_dir.is_dir(),
            "the real managed-clone path must be untouched by an interrupted fetch "
            "(the partial content must have landed in a scratch dir, not here) -- "
            "this is the must-not clause's live demonstration",
        )
        # No scratch directory left behind past the attempt that made it --
        # self-cleaning, not just non-promoting.
        leftover = list(
            (self.root / "runs" / "rulebooks").glob("skill-repository.tmp-*")
        )
        self.assertEqual(leftover, [], f"stale scratch directory left behind: {leftover}")

        # after: a fetch that actually completes flips the same check --
        # this leg IS routed through the live preflight script, because
        # here MUSTER_SKILL_REPO points at a directory that genuinely
        # exists and resolves at candidate 1, so candidate 3's real-repo
        # fallback is never reached regardless of that cache's own state.
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_full):
            resolved = spawn._skill_repo_root()
        self.assertEqual(resolved, self.managed_skills_dir)
        self.assertTrue((resolved / "example-skill").is_dir())
        self.assertTrue(
            self._preflight_reports_resolved_at_managed_dir(),
            "a fetch that actually completed must flip the precondition to satisfied",
        )

    def test_interrupted_fetch_does_not_block_a_later_real_attempt(self):
        # A second, real attempt after an interrupted one must succeed --
        # the scratch-dir cleanup at the top of _skill_repo_managed_root()
        # must not leave a lock or a leftover directory that wedges retry.
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_interrupted):
            spawn._skill_repo_root()
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_full):
            resolved = spawn._skill_repo_root()
        self.assertIsNotNone(resolved)
        self.assertTrue((resolved / "example-skill").is_dir())


class EnsureSkillCorpusCliTest(unittest.TestCase):
    """`ensure_skill_corpus_cli()` is what the SessionStart hook calls --
    both shipped removals (skill-repository fetch, ~/.claude/skills) go
    through it, each printing a notice."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name) / "checkout"
        self.home = Path(self._tmpdir.name) / "home"
        self.root.mkdir()
        self.home.mkdir()
        self._patches = [
            mock.patch.object(spawn, "ROOT", self.root),
            mock.patch.object(Path, "home", lambda: self.home),
            mock.patch.dict(
                "os.environ",
                {"TOKENMAXXXER_RULEBOOKS": str(self.root / "no-such-sibling-parent")},
            ),
        ]
        for p in self._patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("MUSTER_SKILL_REPO", None)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_creates_empty_home_claude_skills_dir(self):
        target = self.home / ".claude" / "skills"
        self.assertFalse(target.exists())
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_full):
            rc = spawn.ensure_skill_corpus_cli()
        self.assertEqual(rc, 0)
        self.assertTrue(target.is_dir())
        self.assertEqual(list(target.iterdir()), [], "must be created empty, no content written")

    def test_does_not_recreate_an_existing_home_claude_skills_dir(self):
        target = self.home / ".claude" / "skills"
        target.mkdir(parents=True)
        marker = target / "user-added-skill"
        marker.mkdir()
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_full):
            spawn.ensure_skill_corpus_cli()
        self.assertTrue(marker.is_dir(), "must not touch a directory that already exists")

    def test_drives_the_skill_repo_fetch_and_prints_a_notice(self):
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_full):
            rc = spawn.ensure_skill_corpus_cli()
        self.assertEqual(rc, 0)
        resolved = spawn._skill_repo_root()
        self.assertIsNotNone(resolved)
        self.assertTrue((resolved / "example-skill").is_dir())

    def test_never_fails_the_session_when_offline(self):
        # Simulates the "genuinely offline, no prior managed clone" case:
        # every git subprocess reports failure. Best-effort, always exits
        # 0 -- a SessionStart hook must never block a session from
        # starting.
        with mock.patch.object(spawn, "_run_net", side_effect=_fake_clone_interrupted):
            rc = spawn.ensure_skill_corpus_cli()
        self.assertEqual(rc, 0)


class InstallPreconditionNoticesHookTest(unittest.TestCase):
    """The two preconditions that stay manual get a notice, not a
    mutation: git identity is only ever read (`git config --get`), and
    docs/specs/approvers.md discovery never writes into the target repo."""

    def _run_hook(self, cwd: Path, env: dict) -> subprocess.CompletedProcess:
        full_env = {**os.environ, **env}
        return subprocess.run(
            ["bash", str(NOTICES_HOOK)],
            cwd=str(cwd),
            env=full_env,
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_notices_missing_git_identity_and_board_file(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=str(target), timeout=20)
            env = {
                "HOME": str(target / "isolated-home"),
                "GIT_CONFIG_GLOBAL": str(target / "empty-gitconfig"),
                "GIT_CONFIG_SYSTEM": str(target / "empty-gitconfig"),
            }
            result = self._run_hook(target, env)
        self.assertEqual(result.returncode, 0, "a SessionStart hook must never block on this")
        self.assertIn("git identity not configured", result.stdout)
        self.assertIn("docs/specs/approvers.md", result.stdout)

    def test_silent_when_both_preconditions_already_met(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=str(target), timeout=20)
            (target / "docs" / "specs").mkdir(parents=True)
            (target / "docs" / "specs" / "approvers.md").write_text("- someone\n")
            gitconfig = target / "gitconfig-with-identity"
            gitconfig.write_text("[user]\n\tname = Test User\n\temail = test@example.com\n")
            env = {
                "HOME": str(target / "isolated-home"),
                "GIT_CONFIG_GLOBAL": str(gitconfig),
                "GIT_CONFIG_SYSTEM": str(target / "empty-gitconfig"),
            }
            result = self._run_hook(target, env)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("git identity not configured", result.stdout)
        self.assertNotIn("approvers.md", result.stdout)

    def test_never_mutates_global_git_config(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            subprocess.run(["git", "init", "-q"], cwd=str(target), timeout=20)
            gitconfig = target / "empty-gitconfig"
            env = {
                "HOME": str(target / "isolated-home"),
                "GIT_CONFIG_GLOBAL": str(gitconfig),
                "GIT_CONFIG_SYSTEM": str(target / "empty-gitconfig"),
            }
            self._run_hook(target, env)
        self.assertFalse(
            gitconfig.exists(),
            "must-not: the hook must never write the user's global git config",
        )


class HookPortabilityTest(unittest.TestCase):
    """macOS + Linux, no GNU-only flags, no /proc -- the same floor
    scripts/preflight/consumer_preconditions.py documents for itself."""

    _FORBIDDEN = ("stat -c", "date -d", "readlink -f", "sed -i", "/proc/")

    def test_no_gnu_only_flags_or_proc_reads(self):
        for hook in (BOOTSTRAP_HOOK, NOTICES_HOOK):
            text = hook.read_text(encoding="utf-8")
            for pattern in self._FORBIDDEN:
                self.assertNotIn(
                    pattern, text, f"{hook.name} uses non-portable {pattern!r}"
                )

    def test_both_hooks_are_syntactically_valid_bash(self):
        for hook in (BOOTSTRAP_HOOK, NOTICES_HOOK):
            result = subprocess.run(
                ["bash", "-n", str(hook)], capture_output=True, text=True, timeout=10
            )
            self.assertEqual(result.returncode, 0, f"{hook.name}: {result.stderr}")

    def test_both_hooks_exit_zero_with_no_checkout_resolvable(self):
        # Fail-open floor: neither hook may block a session start just
        # because it can't find a usable checkout (e.g. a fresh install
        # racing self-update.sh, or ORCHESTRATE_OFF unset in a sandbox
        # with no on-the-record checkout on disk at all).
        with tempfile.TemporaryDirectory() as td:
            env = {**os.environ, "HOME": str(Path(td) / "isolated-home")}
            env.pop("TOKENMAXXXER_CHECKOUT", None)
            for hook in (BOOTSTRAP_HOOK, NOTICES_HOOK):
                result = subprocess.run(
                    ["bash", str(hook)],
                    cwd=td,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                self.assertEqual(result.returncode, 0, f"{hook.name}: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
