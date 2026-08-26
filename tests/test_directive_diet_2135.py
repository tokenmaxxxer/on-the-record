"""Issue #2135: spawned-session context diet.

Covers, per the issue's acceptance:
- the composition-breakdown instrument (`composition_breakdown`);
- the diet mapping lint: the always-on index and the materialized section
  files cover the removed prose (index/file bijection, verbatim moved
  sentences — same discipline as PR #2106's tests);
- the record skeleton satisfies the record-format gate's structural
  expectations on a fixture (needle-level replica of core's
  record-fields-gate §20 checks, plus the real gate when a core checkout
  is resolvable);
- the assembled always-on directive overhead stays under a byte budget
  derived from the pre-diet measurement (3,912B overhead on the
  implementation-role shape -> post-diet fixture budget 2,048B).
"""
from _spawn_test_support import *  # noqa: F401,F403
import re

from test_spawn_directive_assembly import DirectiveAssemblyBase, _NO_SKILLS


class CompositionBreakdown(unittest.TestCase):
    def test_labels_bytes_and_total(self):
        parts = [("base-task", "abc"), ("issue-preamble-index", "한"),
                 ("artifact-smoke", "")]
        line = spawn.composition_breakdown(parts)
        self.assertIn("total=6B", line)  # 3 + 3 (UTF-8 한) + 0
        self.assertIn("base-task=3B", line)
        self.assertIn("issue-preamble-index=3B", line)
        # empty parts are elided from the cells, not from the total
        self.assertNotIn("artifact-smoke", line)


class SectionFileMapping(unittest.TestCase):
    """Zero normative loss: every moved sentence lives verbatim in a
    section file; conditional sections appear only with their trigger."""

    def test_completion_file_carries_the_moved_preamble_prose_verbatim(self):
        files = spawn.directive_section_files()
        body = files["completion-and-landing.md"]
        self.assertIn(spawn._COMPLETION_PROSE, body)
        # moved sentences, spot-checked
        self.assertIn("미커밋 변경은 존재하지 않는 것과 같다", body)
        self.assertIn("체크포인트 커밋", body)
        self.assertIn("run_in_background", body)
        self.assertIn("모든 작업은 이 턴 안에서 직접 끝내라", body)
        # issue #2135 item 4: landing batching guidance (guidance only)
        self.assertIn("Landing batching (issue #2135", body)
        self.assertIn("git add", body)
        self.assertIn("gh pr create", body)
        self.assertIn("guidance only", body)

    def test_repo_discovery_file_carries_the_git_ls_files_guidance(self):
        # Issue #2185: spawned sessions burned ~90s/spawn re-discovering
        # repo layout via unscoped `find`; the always-on section file
        # points them at `git ls-files` instead.
        files = spawn.directive_section_files()
        body = files["repo-discovery.md"]
        self.assertIn(spawn._REPO_DISCOVERY_PROSE, body)
        self.assertIn("git ls-files", body)
        self.assertIn("find", body)

    def test_known_paths_file_carries_the_exported_env_var_names(self):
        # Issue #2211: #2185's git-ls-files guidance only covers the repo
        # the session is in — it says nothing about the on-the-record
        # plugin checkout, core plugin, skill-repository, or sibling role
        # workspaces. The always-on section file names the four env vars
        # spawn_cmd() now injects so a session reads them instead of
        # running `find /`.
        files = spawn.directive_section_files()
        body = files["known-paths.md"]
        self.assertIn(spawn._KNOWN_PATHS_PROSE, body)
        self.assertIn("ON_THE_RECORD", body)
        self.assertIn("CLAUDE_PLUGIN_ROOT_CORE", body)
        self.assertIn("MUSTER_WORKSPACE_ROOT", body)
        self.assertIn("MUSTER_SKILL_REGISTRY_ROOT", body)
        self.assertIn("find", body)

    def test_turn_budget_file_carries_the_approach_cap_guidance(self):
        # Issue #2262: turn budget + grep-batching guidance is always-on,
        # same tier as completion-and-landing/repo-discovery/known-paths.
        files = spawn.directive_section_files()
        body = files["turn-budget.md"]
        self.assertIn(spawn._TURN_BUDGET_PROSE, body)
        self.assertIn(str(spawn.DEFAULT_SESSION_MAX_TURNS), body)
        self.assertIn("MUSTER_SESSION_MAX_TURNS_RESOLVED", body)
        self.assertIn("grep", body)
        # issue #2262 operator comment (2026-08-25, issuecomment-5403942012):
        # parallel subagent fan-out named explicitly alongside grep batching.
        self.assertIn("Task", body)
        self.assertIn("Explore", body)
        self.assertIn("run_in_background", body)

    def test_skill_and_checkpoint_sections_are_conditional(self):
        base = spawn.directive_section_files()
        self.assertEqual(set(base),
                         {"completion-and-landing.md", "repo-discovery.md",
                          "hook-contract.md", "known-paths.md",
                          "turn-budget.md"})
        with_skills = spawn.directive_section_files(skills_mounted=True)
        self.assertIn("skill-obligations.md", with_skills)
        self.assertIn(spawn._SKILL_CHECK_PROSE,
                      with_skills["skill-obligations.md"])
        self.assertIn(spawn._SKILL_VERDICT_PROSE,
                      with_skills["skill-obligations.md"])
        cp = spawn._checkpoint_contract_block(31, "implementation")
        with_cp = spawn.directive_section_files(checkpoint_block=cp)
        self.assertEqual(with_cp["checkpoint-mode.md"], cp)

    def test_materialize_writes_into_workspace_directive_dir(self):
        with tempfile.TemporaryDirectory() as td:
            spawn.materialize_directive_sections(
                td, spawn.directive_section_files(skills_mounted=True))
            d = Path(td) / ".on-the-record" / "directive"
            self.assertTrue((d / "completion-and-landing.md").is_file())
            self.assertTrue((d / "skill-obligations.md").is_file())


class RecordSkeleton(unittest.TestCase):
    def _needles_check(self, text: str) -> list:
        """Needle-level replica of core record-fields-gate §20 checks."""
        low = text.lower()
        missing = []
        if not any(n in low for n in ("what was done", "what i did", "## done",
                                      "work done", "summary of work")):
            missing.append("what-was-done")
        if not any(n in low for n in ("why", "rationale", "reason:")):
            missing.append("why")
        if not ("upstream" in low or "docs/issue-" in text):
            missing.append("upstream-basis")
        if not re.search(r"^\s*loop_state:\s*([A-Za-z0-9_-]+)\s*$", text, re.M):
            missing.append("loop_state")
        if not any(n in low for n in ("open findings", "open_findings",
                                      "open finding")):
            missing.append("open-findings")
        # non-terminal loop_state additionally requires:
        if not any(n in low for n in ("next steps", "next-steps", "next_steps")):
            missing.append("next-steps")
        if not any(n in low for n in ("resolution path", "resolution-path",
                                      "resolution_path")):
            missing.append("resolution-path")
        # sha: values must be same-commit / 40-hex / value-less
        fm = re.match(r"^---[ \t]*\r?\n(.*?\n)^---[ \t]*\r?$", text.lstrip(),
                      re.M | re.S)
        region = fm.group(1) if fm else text
        for m in re.finditer(r"^\s*sha:[ \t]*(.*)$", region, re.M):
            v = m.group(1).strip()
            if v and v != "same-commit" and not re.match(r"^[0-9a-f]{40}$", v):
                missing.append("sha-placeholder:%s" % v)
        return missing

    def test_skeleton_satisfies_record_gate_needles(self):
        with tempfile.TemporaryDirectory() as td:
            p = spawn.write_record_skeleton(td, 31, "implementation")
            text = p.read_text(encoding="utf-8")
        self.assertEqual(self._needles_check(text), [])
        self.assertIn("loop_state: in-progress", text)
        # roles/specs required_fields surface as empty frontmatter keys —
        # issue-2190: commit_sha realizes as code_under_review (the field
        # record-fields-gate.sh actually checks for coding/implementation),
        # and breaking surfaces despite being optional in the spec, since
        # every real delivery record carries it.
        self.assertIn("code_under_review:\n  - PLACEHOLDER: path/to/file",
                      text)
        self.assertNotIn("commit_sha:", text)
        self.assertIn("type: # one of: feat|fix|", text)
        self.assertIn("breaking: # string", text)
        self.assertIn("verdict: # one of: pass|fail", text)
        # issue-2190: `## What did not work` present-but-empty, matching
        # the near-universal convention across landed implementation
        # records (record-shape-directive, issue-2135's follow-on).
        self.assertIn("## What did not work\n\nNone.\n", text)

    def test_skeleton_loop_state_respects_role_enum(self):
        """A role whose record_fields enum lacks `in-progress` gets its
        enum's first value (record_lint enum discipline)."""
        with tempfile.TemporaryDirectory() as td:
            p = spawn.write_record_skeleton(td, 7, "execution-observation")
            text = p.read_text(encoding="utf-8")
        enum = json.loads((spawn.ROOT / "roles" /
                           "execution-observation.json").read_text())[
                               "record_fields"]["loop_state"]
        flat = ([v for vs in enum.values() for v in vs]
                if isinstance(enum, dict) else list(enum))
        m = re.search(r"^loop_state: (.+)$", text, re.M)
        self.assertIn(m.group(1), flat)

    def test_skeleton_never_overwrites_an_existing_record(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "docs" / "issue-31" / "reports" / "implementation.md"
            p.parent.mkdir(parents=True)
            p.write_text("existing", encoding="utf-8")
            self.assertIsNone(spawn.write_record_skeleton(td, 31,
                                                          "implementation"))
            self.assertEqual(p.read_text(encoding="utf-8"), "existing")

    def test_skeleton_passes_the_real_record_fields_gate_when_available(self):
        """Run core's actual record-fields-gate.sh against a Write of the
        skeleton content, when a core checkout is resolvable (skips
        otherwise — the needle replica above still guards CI)."""
        gate = None
        for _label, cand in spawn._core_candidates():
            if not cand or "$" in str(cand):
                continue
            g = Path(os.path.expanduser(os.path.expandvars(cand))) / \
                "core" / "hooks" / "record-fields-gate.sh"
            if g.is_file():
                gate = g
                break
        if gate is None:
            fallback = (spawn.ROOT / "runs" / "rulebooks" /
                        "tokenmaxxxer-core" / "core" / "hooks" /
                        "record-fields-gate.sh")
            if fallback.is_file():
                gate = fallback
        if gate is None:
            self.skipTest("no tokenmaxxxer-core checkout on this machine")
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["git", "init", "-q"], cwd=td, check=True)
            p = spawn.write_record_skeleton(td, 31, "implementation")
            payload = json.dumps({
                "tool_name": "Write",
                "tool_input": {"file_path": str(p),
                               "content": p.read_text(encoding="utf-8")}})
            env = {**os.environ, "CLAUDE_ROLE": "implementation",
                   "CLAUDE_PROJECT_DIR": td,
                   "CLAUDE_PLUGIN_ROOT_CORE": str(gate.parent.parent)}
            r = subprocess.run(["bash", str(gate)], input=payload,
                               capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0,
                         f"record-fields-gate refused the skeleton: "
                         f"{r.stderr}")


class DietIntegration(DirectiveAssemblyBase):
    """Slow: assembled directive vs materialized workspace files."""

    def _skill_dir(self, root: Path) -> Path:
        d = root / "implementation-blueprint"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\nname: implementation-blueprint\ndescription: >-\n"
            "  Intro. Use whenever code is non-trivial.\n---\n\n# b\n",
            encoding="utf-8")
        return d

    @pytest.mark.slow
    def test_moved_prose_absent_inline_present_via_system_prompt(self):
        # Issue #2204: the #2135 design paired every materialized section
        # file with an inline "Read <file> when <condition>" pointer in
        # the stdin task text — a live-spawn measurement showed sessions
        # read every pointed-at file sequentially before their first task
        # action (~46s), because the pointer reads as "read it now." The
        # fix drops the pointer entirely: the same full prose instead
        # rides --append-system-prompt, already in context at turn 1.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            skill_dir = self._skill_dir(Path(td) / "skills")
            role_source = {"source": "skill-repo", "skill_dirs": [skill_dir],
                           "skills": ["implementation-blueprint"],
                           "skill_sha": "abc123"}
            captured = {}
            delivered = self._run(work, role_source, {},
                                  captured_spawn_cmd=captured)
            d = work / ".on-the-record" / "directive"
            on_disk = {p.name for p in d.iterdir()}
            # moved prose is NOT inline any more
            self.assertNotIn("모든 작업은 이 턴 안에서 직접 끝내라", delivered)
            self.assertNotIn("스킬-verdict 의무(이슈 #2039)", delivered)
            # nor is there any "Read <file>" pointer left in the stdin task
            self.assertNotIn(".on-the-record/directive/", delivered)
            # every materialized file's exact content is present in the
            # --append-system-prompt blob exactly once (zero Read round
            # trips: it's already there at session start)
            system_prompt = captured["append_system_prompt"]
            self.assertTrue(on_disk)
            for name in on_disk:
                body = (d / name).read_text(encoding="utf-8")
                self.assertEqual(system_prompt.count(body), 1)
            # record skeleton pre-written and announced (inline, unaffected)
            self.assertTrue((work / "docs" / "issue-31" / "reports" /
                             "implementation.md").is_file())
            self.assertIn("레코드 스켈레톤", delivered)

    @pytest.mark.slow
    def test_always_on_overhead_under_budget(self):
        """Budget derivation (issue #2135 breakdown): pre-diet spawn-side
        overhead measured 3,912B on the implementation shape (preamble
        1,165 + role-skill triggers 1,515 + skill prose 1,232); post-diet
        the fixture shape (1 mounted skill) must fit in 2,048B."""
        base_task = "원래 맡긴 일.\n"
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            skill_dir = self._skill_dir(Path(td) / "skills")
            role_source = {"source": "skill-repo", "skill_dirs": [skill_dir],
                           "skills": ["implementation-blueprint"],
                           "skill_sha": "abc123"}
            delivered = self._run(work, role_source, {})
        overhead = len(delivered.encode("utf-8")) - len(base_task.encode("utf-8"))
        self.assertLessEqual(overhead, 2048,
                             f"always-on directive overhead {overhead}B "
                             f"exceeds the 2,048B budget")
