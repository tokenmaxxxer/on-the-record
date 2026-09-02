"""Issue #3127 repair round (PR #3131 defects, found by PR #3145's second
independent verification): scripts/issue-3127/run_consumer_pair.py's
skills-off arm did not achieve "corpus present but empty" in a real
environment, H1 existed only as prose, the blind scorer was defined and
never called, and wall-clock-to-landed measured time-to-session-end.

This file covers defect 1 (skills-off arm genuine isolation). Defect 2 (H1
enforcement), defect 3 (blind scorer wiring), and defect 4 (wall-clock
honesty) are covered in test_issue_3127_h1_scoring_wallclock.py, added by
their own later commits, so each defect's own commit carries its own tests.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import spawn  # noqa: E402
import run_consumer_pair as rcp  # noqa: E402


class BuildStubSkillRepoTest(unittest.TestCase):
    """defect 1: the stub the skills-off arm's MUSTER_SKILL_REPO points at
    must be a REAL directory (not a literal placeholder string no code
    ever created) containing only frontmatter, no procedure body."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def test_creates_real_directory_with_only_frontmatter(self):
        dest = Path(self._tmpdir.name) / "stub-repo"
        rcp.build_stub_skill_repo("some-skill", dest)
        skill_md = dest / "some-skill" / "SKILL.md"
        self.assertTrue(skill_md.is_dir().__class__ is bool)  # sanity: no crash
        self.assertTrue((dest / "some-skill").is_dir())
        self.assertTrue(skill_md.is_file())
        content = skill_md.read_text(encoding="utf-8")
        self.assertIn("name: some-skill", content)
        self.assertIn("---", content)
        # No procedure body: the content is short (frontmatter only), not a
        # full skill document with numbered steps/sections.
        self.assertLess(len(content), 400)
        self.assertNotIn("## ", content)

    def test_skill_repo_root_finds_the_stub_directly_no_fallback(self):
        """Old bug (finding 1b): a literal placeholder string is never a
        real directory, so `_skill_repo_root()`'s `Path(...).is_dir()`
        check fails and it silently falls through to the sibling/managed-
        clone fallback chain -- resolving to the REAL corpus. A genuinely
        created stub directory must not trigger that fallback."""
        dest = Path(self._tmpdir.name) / "stub-repo"
        rcp.build_stub_skill_repo("some-skill", dest)
        import os
        old_env = os.environ.get("MUSTER_SKILL_REPO")
        os.environ["MUSTER_SKILL_REPO"] = str(dest)
        try:
            resolved = spawn._skill_repo_root()
        finally:
            if old_env is None:
                os.environ.pop("MUSTER_SKILL_REPO", None)
            else:
                os.environ["MUSTER_SKILL_REPO"] = old_env
        self.assertEqual(resolved, dest)


class SkillsArgumentForArmTest(unittest.TestCase):
    """defect 1: skills-on keeps the bare name (byte-identical to
    production); skills-off adds the skill-repo: qualifier."""

    def test_on_arm_uses_bare_name(self):
        args = _fake_args(skill="my-skill")
        plan = rcp.build_plan(args)
        on_arm = plan.arms[0]
        self.assertEqual(on_arm.name, "skills-on")
        self.assertEqual(rcp._skills_argument_for_arm(plan, on_arm), "my-skill")

    def test_off_arm_uses_qualified_name(self):
        args = _fake_args(skill="my-skill")
        plan = rcp.build_plan(args)
        off_arm = plan.arms[1]
        self.assertEqual(off_arm.name, "skills-off")
        self.assertEqual(rcp._skills_argument_for_arm(plan, off_arm),
                          "skill-repo:my-skill")


class OldMechanismReproducedThenFixedTest(unittest.TestCase):
    """defect 1's "PROVE it" requirement: show a real conflict scenario
    where the OLD (unqualified) mechanism fails -- so the manipulation
    check the harness relies on (genuine corpus emptying) is known to be
    capable of failing, not trivially always-true -- then show the fix
    (skill-repo: qualifier) resolves it cleanly.

    Reproduces the exact shape PR #3145's verification found live: a stub
    skill-repo directory (skills-off's real corpus) and a real,
    differently-contented ~/.claude/skills entry for the same skill name
    (as happens on any machine that has already used `spawn.py --skills`
    for real) -- resolved_skill_sources() reads BOTH sources unconditionally
    when unqualified, and refuses because the content differs.
    """

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        base = Path(self._tmpdir.name)
        self.stub_repo_root = base / "stub-skill-repo"
        self.home = base / "home"
        self.target_repo = base / "target-repo"
        (self.home / ".claude").mkdir(parents=True)
        (self.target_repo / ".claude" / "skills").mkdir(parents=True)
        rcp.build_stub_skill_repo("alpha", self.stub_repo_root)
        # A real, differently-contented ~/.claude/skills/alpha -- the
        # multi-source conflict PR #3145 reproduced live.
        (self.home / ".claude" / "skills" / "alpha").mkdir(parents=True)
        (self.home / ".claude" / "skills" / "alpha" / "SKILL.md").write_text(
            "full real skill content, not a stub", encoding="utf-8")
        self._saved_home = spawn.Path.home
        spawn.Path.home = staticmethod(lambda: self.home)

    def tearDown(self):
        spawn.Path.home = self._saved_home

    def test_old_unqualified_mechanism_fails_closed_on_real_conflict(self):
        """The check IS capable of failing: without the qualifier fix, the
        stub-repo tier and the real ~/.claude/skills tier disagree on
        content for the same name, and resolved_skill_sources() refuses."""
        with self.assertRaises(SystemExit) as ctx:
            spawn.resolved_skill_sources(
                "alpha", self.stub_repo_root, home=self.home,
                target_repo_root=self.target_repo)
        msg = str(ctx.exception)
        self.assertIn("alpha", msg)

    def test_qualified_mechanism_resolves_cleanly_to_only_the_stub(self):
        """The fix: `skill-repo:alpha` filters to only the skill-repo
        source before the conflicting local-user tier is even considered."""
        result = spawn.resolved_skill_sources(
            "skill-repo:alpha", self.stub_repo_root, home=self.home,
            target_repo_root=self.target_repo)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source"], "skill-repo")
        self.assertEqual(result[0]["dir"], self.stub_repo_root / "alpha")


def _fake_args(**overrides):
    import argparse
    ns = argparse.Namespace(
        repo="<sandbox-repo-not-yet-chosen>", pinned_sha=None,
        skill="product-discovery-hypothesis-preregistration", model="sonnet",
        pairs=None, skill_repo_on="$MUSTER_SKILL_REGISTRY_ROOT",
        skill_repo_off=None, watch_timeout=1800)
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


if __name__ == "__main__":
    unittest.main()
