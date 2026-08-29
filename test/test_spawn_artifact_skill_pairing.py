"""이슈 #2014 (artifact-gate phase 3): `design-artifacts:` 선언이 있으면
선언된 각 아티팩트 경로를 그 절차를 담당하는 마운트된 스킬과 짝지어
디렉티브에 한 줄씩 싣는다(#2013 parse_declaration + #1978B/#2001
tokenize/trigger 재사용). 선언이 없으면 오늘과 바이트 단위로 동일하다.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn

sys.path.insert(0, str((spawn.ROOT / "gates").resolve()))
import gh_rest


class SpawnOneArtifactSkillPairingTest(unittest.TestCase):
    """acceptance: 라이브 `_spawn_one()` 을 통한 두 케이스 — 선언 있음/없음."""

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

    def _seed_skill(self, root):
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

    def _run(self, work, skill_repo_root, issue_body, *, issue=2014,
             skill_skill_dirs=None):
        roster_calls = []
        real_roster_register = spawn.roster_register

        def spy_roster_register(key, entry):
            roster_calls.append((key, dict(entry)))
            return real_roster_register(key, entry)

        def spy_spawn_cmd(settings, skill, unattended, core_plugins, plugins,
                          model, skill_dirs, skill_repo_sha_value, **kwargs):
            return (["cat"], {})

        skill_source = {"source": "skill-repo",
                       "skill_dirs": skill_skill_dirs or [],
                       "skills": [], "skill_sha": None}

        with mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, skill: str(work)), \
             mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, skill: "b"), \
             mock.patch.object(spawn, "resolve_static_policy_source",
                               lambda repo_root: skill_source), \
             mock.patch.object(spawn, "_skill_repo_root",
                               lambda: skill_repo_root), \
             mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
             mock.patch.object(spawn, "core_version", lambda: "v0"), \
             mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
             mock.patch.object(spawn, "spawn_cmd", spy_spawn_cmd), \
             mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
             mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
             mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
             mock.patch.object(spawn, "_undispositioned_skill_prs",
                               lambda root, exclude_issue=None: ([], True)), \
             mock.patch.object(spawn, "roster_register", spy_roster_register), \
             mock.patch.object(spawn, "ledger_write", lambda *a, **k: None), \
             mock.patch.object(gh_rest, "fetch_issue",
                               lambda repo, issue: {"body": issue_body,
                                                     "title": "t"}), \
             mock.patch.object(spawn.Path, "home", lambda: work):
            # 이슈 #2055: cross-family BM25 코퍼스가 이제 `~/.claude/skills`
            # 도 본다 — 이 테스트는 그 tier 를 대상으로 하지 않으므로, 실행
            # 환경의 실제 홈이 아니라 격리된 작업 디렉터리를 홈으로 준다
            # (실제 `~/.claude/skills` 에 같은 이름의 스킬이 있으면 #2055
            # 의 same-name fail-closed 가 정확히 의도대로 발동해버린다).
            rc = spawn._spawn_one(str(work), "implementation", "do the task",
                                  unattended=True, issue=issue, bounded=False,
                                  no_wait=True)
        self.assertEqual(rc, 0)
        log_path = roster_calls[-1][1]["log"]
        return Path(log_path).read_text()

    def test_declared_artifact_matching_skill_gets_pairing_line(self):
        with tempfile.TemporaryDirectory() as td, \
             tempfile.TemporaryDirectory() as skills_td:
            work = self._prep_repo(td)
            skill_repo_root = Path(skills_td)
            skill_dir = self._seed_skill(skill_repo_root)
            body = ("Some issue text.\n\n"
                    "design-artifacts:\n"
                    "- docs/issue-2014/design/contrast-landing-page.md\n")
            delivered = self._run(work, skill_repo_root, body,
                                  skill_skill_dirs=[skill_dir])
        self.assertIn("아티팩트-스킬 짝짓기(이슈 #2014)", delivered)
        self.assertIn(
            "docs/issue-2014/design/contrast-landing-page.md ↔ "
            "accessibility-aria-and-contrast-rules", delivered)

    def test_no_declaration_line_byte_identical_to_baseline(self):
        with tempfile.TemporaryDirectory() as td_a, \
             tempfile.TemporaryDirectory() as td_b, \
             tempfile.TemporaryDirectory() as skills_td:
            skill_repo_root = Path(skills_td)
            self._seed_skill(skill_repo_root)
            body = "Some issue text with no artifact declaration.\n"

            work_a = self._prep_repo(td_a, "work-a")
            delivered_a = self._run(work_a, skill_repo_root, body, issue=2014)

            work_b = self._prep_repo(td_b, "work-b")
            delivered_b = self._run(work_b, skill_repo_root, body, issue=2014)

        self.assertEqual(delivered_a, delivered_b)
        self.assertNotIn("아티팩트-스킬 짝짓기", delivered_a)


if __name__ == "__main__":
    unittest.main()
