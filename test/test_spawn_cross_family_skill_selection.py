"""이슈 #2001: family 세트는 그대로 두고(add-only), 스폰 태스크 텍스트와
크로스-패밀리 스킬의 SKILL.md "Use ..." 트리거 문장을 결정론적 키워드
겹침으로 채점해 top-K(K=2) 를 추가로 마운트한다.

acceptance: 매치되는 태스크는 마운트 목록이 정확히 그 스킬만큼(최대 K=2)
늘고 디렉티브에도 실린다; 매치 안 되는 태스크는 마운트/디렉티브가 오늘과
바이트 단위로 동일하다 — 둘 다 라이브(serial, -o addopts='')로 검증한다.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class TokenizeTest(unittest.TestCase):
    def test_lowercases_splits_nonalnum_and_drops_stopwords(self):
        self.assertEqual(
            spawn._tokenize("Use when a Landing Page needs Contrast."),
            {"landing", "page", "needs", "contrast"})

    def test_empty_text_yields_empty_set(self):
        self.assertEqual(spawn._tokenize(""), set())
        self.assertEqual(spawn._tokenize("a the or and is an use when"), set())


class CrossFamilySkillMatchesTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _skill(self, name, use_sentence):
        d = self.repo_root / name
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            f"description: >-\n"
            f"  Intro text. {use_sentence}\n"
            "---\n\n# body\n", encoding="utf-8")
        return d

    def test_matching_skill_clears_threshold_and_is_returned(self):
        d = self._skill(
            "accessibility-aria-and-contrast-rules",
            "Use when deciding an ARIA role, an accessible name, or a "
            "text/background contrast pair on a landing page.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page and check its contrast against WCAG.",
            "implementation", self.repo_root)
        self.assertEqual(matches, [d])

    def test_below_threshold_single_shared_token_no_match(self):
        self._skill("some-other-skill",
                     "Use when reviewing generic code quality issues.")
        matches = spawn._cross_family_skill_matches(
            "Write some code today.", "implementation", self.repo_root)
        self.assertEqual(matches, [])

    def test_family_skill_never_returned_as_cross_family_candidate(self):
        # implementation-blueprint is already in _ROLE_SKILLS['implementation']
        self._skill(
            "implementation-blueprint",
            "Use whenever you are about to produce non-trivial code "
            "spanning multiple modules landing pages contrast accessible.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page contrast accessible module.",
            "implementation", self.repo_root)
        self.assertEqual(matches, [])

    def test_k_cap_with_three_clearing_candidates_keeps_top_two(self):
        self._skill("zzz-skill-c",
                     "Use when a landing page needs contrast accessible review.")
        self._skill("aaa-skill-a",
                     "Use when a landing page needs contrast accessible review.")
        self._skill("mmm-skill-b",
                     "Use when a landing page needs contrast accessible review.")
        matches = spawn._cross_family_skill_matches(
            "Build a landing page that needs contrast accessible review.",
            "implementation", self.repo_root, k=2)
        self.assertEqual(len(matches), 2)
        # tie-break by name asc when scores are equal
        self.assertEqual([d.name for d in matches],
                         ["aaa-skill-a", "mmm-skill-b"])

    def test_no_trigger_line_skill_never_matches(self):
        d = self.repo_root / "no-desc-skill"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: no-desc-skill\n---\n",
                                    encoding="utf-8")
        matches = spawn._cross_family_skill_matches(
            "landing page contrast accessible", "implementation",
            self.repo_root)
        self.assertEqual(matches, [])


class SpawnOneCrossFamilyAcceptanceTest(unittest.TestCase):
    """acceptance: 라이브 `_spawn_one()` 을 통한 두 케이스 — 매치/비매치."""

    def setUp(self):
        self._old_roster = spawn.ROSTER
        self._old_idx = spawn.WORKSPACE_INDEX
        self._td = tempfile.TemporaryDirectory()
        spawn.ROSTER = Path(self._td.name) / "active.json"
        spawn.WORKSPACE_INDEX = Path(self._td.name) / "workspaces.json"

    def tearDown(self):
        spawn.ROSTER = self._old_roster
        spawn.WORKSPACE_INDEX = self._old_idx
        self._td.cleanup()

    def _prep_repo(self, td, name="work"):
        work = Path(td) / name
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        return work

    def _run(self, work, task_text, skill_repo_root, *, issue=2001):
        roster_calls = []
        real_roster_register = spawn.roster_register
        spawn_cmd_calls = []

        def spy_roster_register(key, entry):
            roster_calls.append((key, dict(entry)))
            return real_roster_register(key, entry)

        def spy_spawn_cmd(settings, role, unattended, core_plugins, plugins,
                          model, skill_dirs, skill_repo_sha_value):
            spawn_cmd_calls.append(list(skill_dirs))
            return (["cat"], {})

        role_source = {"source": "skill-repo", "skill_dirs": [],
                       "skills": [], "skill_sha": None}

        with mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, role: str(work)), \
             mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, role: "b"), \
             mock.patch.object(spawn, "resolve_role_source",
                               lambda role, repo_root: role_source), \
             mock.patch.object(spawn, "_skill_repo_root",
                               lambda: skill_repo_root), \
             mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
             mock.patch.object(spawn, "core_version", lambda: "v0"), \
             mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
             mock.patch.object(spawn, "spawn_cmd", spy_spawn_cmd), \
             mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
             mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
             mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
             mock.patch.object(spawn, "_undispositioned_role_prs",
                               lambda root, exclude_issue=None: ([], True)), \
             mock.patch.object(spawn, "roster_register", spy_roster_register), \
             mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
            rc = spawn._spawn_one(str(work), "implementation", task_text,
                                  unattended=True, issue=issue, bounded=False,
                                  no_wait=True)
        self.assertEqual(rc, 0)
        log_path = roster_calls[-1][1]["log"]
        delivered = Path(log_path).read_text()
        return delivered, spawn_cmd_calls[-1]

    def _seed_cross_family_skill(self, root):
        d = root / "accessibility-aria-and-contrast-rules"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\n"
            "name: accessibility-aria-and-contrast-rules\n"
            "description: >-\n"
            "  Use when deciding an ARIA role, an accessible name, or a\n"
            "  text/background contrast pair for a landing page redesign.\n"
            "---\n\n# body\n", encoding="utf-8")
        return d

    def test_matching_task_gains_exactly_that_skill_in_mounts_and_directive(self):
        with tempfile.TemporaryDirectory() as td, \
             tempfile.TemporaryDirectory() as skills_td:
            work = self._prep_repo(td)
            skill_repo_root = Path(skills_td)
            skill_dir = self._seed_cross_family_skill(skill_repo_root)
            delivered, mounted = self._run(
                work,
                "Redesign the landing page and fix its ARIA role and "
                "contrast pair.",
                skill_repo_root)
        self.assertIn("accessibility-aria-and-contrast-rules", delivered)
        self.assertEqual(mounted, [skill_dir])

    def test_non_matching_task_mounts_and_directive_byte_identical_to_baseline(self):
        with tempfile.TemporaryDirectory() as td_a, \
             tempfile.TemporaryDirectory() as td_b, \
             tempfile.TemporaryDirectory() as skills_td:
            skill_repo_root = Path(skills_td)
            self._seed_cross_family_skill(skill_repo_root)

            work_a = self._prep_repo(td_a, "work-a")
            delivered_a, mounted_a = self._run(
                work_a, "Refactor the internal batching pipeline.",
                skill_repo_root, issue=2001)

            work_b = self._prep_repo(td_b, "work-b")
            delivered_b, mounted_b = self._run(
                work_b, "Refactor the internal batching pipeline.",
                skill_repo_root, issue=2001)

        self.assertEqual(delivered_a, delivered_b)
        self.assertEqual(mounted_a, mounted_b)
        self.assertEqual(mounted_a, [])
        self.assertNotIn("accessibility-aria-and-contrast-rules", delivered_a)


if __name__ == "__main__":
    unittest.main()
