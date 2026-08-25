from _spawn_test_support import *  # noqa: F401,F403
from _spawn_test_support import _event  # noqa: F401


class RepoConfigRefusal(unittest.TestCase):
    def test_agents_and_mcp_are_rogue(self):
        # 프로젝트 스코프 에이전트 파일은 hooks/permissionMode frontmatter 를
        # 존중하고(sub-agents 문서), .mcp.json 은 레포가 적은 프로세스 실행
        # 표면이다 — 실측된 레포-커밋-훅 탈출과 같은 부류.
        for p in (".claude/agents", ".mcp.json"):
            self.assertIn(p, spawn.REPO_CONFIG, p)

    def test_refusal_fires_on_agents_dir(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / ".claude" / "agents").mkdir(parents=True)
            with self.assertRaises(SystemExit):
                spawn.require_no_repo_config(td, override=False)

class WebToolPermissionAccess(unittest.TestCase):
    """이슈 #65: #58 이 연 것은 샌드박스 네트워크 층(allowedDomains)뿐이었다.
    headless 세션은 --permission-mode acceptEdits 로 뜨고 답할 사람이 없어서
    permissions.allow 에 규칙이 없는 도구는 별개로 거부된다 — 그 TOOL-PERMISSION
    층을 role_settings() 가 채우는지 검증한다."""

    def test_web_tools_allowed_for_every_role(self):
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            allow = out["permissions"]["allow"]
            self.assertIn("WebSearch", allow, role)
            self.assertIn("WebFetch", allow, role)

    def test_read_only_tools_allowed_for_every_role(self):
        """이슈 #153: Read/Grep/Glob 은 sandbox.filesystem 경계를 넓히지 않는
        읽기 전용 조회이므로, WebSearch/WebFetch 와 같은 TOOL-PERMISSION 층에서
        모든 역할에 대해 허용된다."""
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            allow = out["permissions"]["allow"]
            self.assertIn("Read", allow, role)
            self.assertIn("Grep", allow, role)
            self.assertIn("Glob", allow, role)

    def test_role_declared_permissions_allow_entries_preserved(self):
        """이슈 #38 의 registry-host 병합과 같은 패턴: 병합이지 교체가 아니다."""
        f = Path(spawn.ROOT) / "roles" / "implementation.json"
        original_text = f.read_text()
        spec = json.loads(original_text)
        spec["permissions"] = {"allow": ["Bash(git *)"]}
        try:
            f.write_text(json.dumps(spec))
            out = spawn.role_settings("implementation")
            allow = out["permissions"]["allow"]
            self.assertIn("Bash(git *)", allow)
            self.assertIn("WebSearch", allow)
            self.assertIn("WebFetch", allow)
        finally:
            f.write_text(original_text)

class WorkspaceBashAllowlist(unittest.TestCase):
    """이슈 #558: 격리된 워크스페이스 안에서 정당한 venv/pip/테스트 스크립트
    실행은 헤드리스 세션에서 답할 사람이 없어 하네스 권한 층에 거부된다
    (2026-08-09 soongsil-course-registration 런 실측). role_settings 가
    cwd 로 앵커링된 Bash 허용 항목을 스폰 시점에 채우는지, 그리고 그
    항목이 전역이 아니라 그 cwd 로만 좁혀지는지 검증한다."""

    def test_no_workspace_bash_allow_when_cwd_is_none(self):
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertFalse([a for a in allow if a.startswith("Bash(") and "venv" in a], allow)

    def test_venv_and_pip_and_test_script_shapes_allowed_for_cwd(self):
        cwd = "/tmp/muster-work/issue-558-implementation"
        out = spawn.role_settings("implementation", cwd)
        allow = out["permissions"]["allow"]
        bash_entries = [a for a in allow if a.startswith("Bash(")]
        self.assertTrue(any("venv" in a for a in bash_entries), bash_entries)
        self.assertTrue(any("pip install" in a for a in bash_entries), bash_entries)
        self.assertTrue(any("test/" in a for a in bash_entries), bash_entries)

    def test_every_added_bash_entry_is_scoped_to_cwd(self):
        cwd = "/tmp/muster-work/issue-558-implementation"
        out = spawn.role_settings("implementation", cwd)
        allow = out["permissions"]["allow"]
        bash_entries = [a for a in allow if a.startswith("Bash(")]
        for entry in bash_entries:
            self.assertIn(cwd, entry, entry)

    def test_different_cwds_produce_differently_anchored_entries(self):
        out1 = spawn.role_settings("implementation", "/tmp/muster-work/issue-1")
        out2 = spawn.role_settings("implementation", "/tmp/muster-work/issue-2")
        bash1 = {a for a in out1["permissions"]["allow"] if a.startswith("Bash(")}
        bash2 = {a for a in out2["permissions"]["allow"] if a.startswith("Bash(")}
        self.assertTrue(bash1, bash1)
        self.assertFalse(bash1 & bash2, bash1 & bash2)

class MustMcpAllowEnv(unittest.TestCase):
    """MUSTER_MCP_ALLOW: #58/#65 와 같은 TOOL-PERMISSION 결함이 사용자가 직접
    붙인 MCP 서버에도 있다 — 서버는 연결되는데 도구 호출은 permissions.allow
    에 규칙이 없어 거부된다(실측: reasona issue-3, world-data MCP,
    permission_denials 에 mcp__world-data__korean_law__search_laws 가 남았다).
    #58/#65 와 달리 대상 도구명을 tokenmaxxxer 코드가 미리 알 수 없으므로
    (사용자마다 다른 이름의 개인 MCP 서버), 운영자가 스폰 시점에 콤마로
    나열한다."""

    def setUp(self):
        self._saved = os.environ.pop("MUSTER_MCP_ALLOW", None)

    def tearDown(self):
        os.environ.pop("MUSTER_MCP_ALLOW", None)
        if self._saved is not None:
            os.environ["MUSTER_MCP_ALLOW"] = self._saved

    def test_unset_env_leaves_allow_list_unchanged(self):
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertEqual(allow, ["WebSearch", "WebFetch", "Read", "Grep", "Glob"])

    def test_single_pattern_is_merged_in(self):
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*"
        out = spawn.role_settings("implementation")
        self.assertIn("mcp__world-data__korean_law__*", out["permissions"]["allow"])

    def test_multiple_patterns_with_whitespace_are_all_merged(self):
        os.environ["MUSTER_MCP_ALLOW"] = (
            " mcp__world-data__korean_law__* , mcp__world-data__finnhub__* ")
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertIn("mcp__world-data__korean_law__*", allow)
        self.assertIn("mcp__world-data__finnhub__*", allow)

    def test_empty_segments_between_commas_are_ignored(self):
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*,,  ,"
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertIn("mcp__world-data__korean_law__*", allow)
        self.assertEqual(len(allow), 6)  # 5 고정 + 이 항목 하나뿐

    def test_non_mcp_prefixed_entries_are_dropped(self):
        """안전장치: 이 통로로 Write/Edit/Bash 처럼 board-gate/approval-gate
        가 지키는 도구를 열 수 없다 — 운영자 실수로도, 접두사가 mcp__ 가
        아니면 조용히 버린다."""
        os.environ["MUSTER_MCP_ALLOW"] = "Bash,Write,Edit,mcp__world-data__korean_law__*"
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertIn("mcp__world-data__korean_law__*", allow)
        self.assertNotIn("Bash", allow)
        self.assertNotIn("Write", allow)
        self.assertNotIn("Edit", allow)

    def test_duplicate_within_env_var_is_not_duplicated_in_output(self):
        os.environ["MUSTER_MCP_ALLOW"] = ("mcp__world-data__korean_law__*,"
                                          "mcp__world-data__korean_law__*")
        out = spawn.role_settings("implementation")
        allow = out["permissions"]["allow"]
        self.assertEqual(allow.count("mcp__world-data__korean_law__*"), 1)

    def test_duplicate_against_role_declared_entry_is_not_duplicated(self):
        f = Path(spawn.ROOT) / "roles" / "implementation.json"
        original_text = f.read_text()
        spec = json.loads(original_text)
        spec["permissions"] = {"allow": ["mcp__world-data__korean_law__*"]}
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*"
        try:
            f.write_text(json.dumps(spec))
            out = spawn.role_settings("implementation")
            allow = out["permissions"]["allow"]
            self.assertEqual(allow.count("mcp__world-data__korean_law__*"), 1)
        finally:
            f.write_text(original_text)

    def test_applies_to_every_role_not_just_one(self):
        os.environ["MUSTER_MCP_ALLOW"] = "mcp__world-data__korean_law__*"
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            self.assertIn("mcp__world-data__korean_law__*",
                          out["permissions"]["allow"], role)

class RoleSessionSandboxRemoved(unittest.TestCase):
    """이슈 #695: role_settings() 는 roles/*.json 이 무엇을 선언하든
    sandbox.enabled 를 중앙에서 강제로 끈다 — 반복된 차단 버그(#38/#58/
    #65/#72/#153)의 비용이 경계의 보호 가치를 넘어섰다는 운영자 결정."""

    def test_sandbox_never_enabled_regardless_of_role_declaration(self):
        """이슈 #695 인수 기준: 대표 역할(implementation)에 대해
        role_settings() 출력이 활성 샌드박스를 갖지 않고, 오늘의
        permissions.allow 항목은 그대로 남아있다."""
        f = Path(spawn.ROOT) / "roles" / "implementation.json"
        original_text = f.read_text()
        spec = json.loads(original_text)
        spec.setdefault("sandbox", {})["enabled"] = True
        try:
            f.write_text(json.dumps(spec))
            out = spawn.role_settings("implementation")
            self.assertFalse(out.get("sandbox", {}).get("enabled"))
            allow = out["permissions"]["allow"]
            for tool in ("WebSearch", "WebFetch", "Read", "Grep", "Glob"):
                self.assertIn(tool, allow)
        finally:
            f.write_text(original_text)

    def test_sandbox_disabled_for_every_role(self):
        for role_file in (Path(spawn.ROOT) / "roles").glob("*.json"):
            role = role_file.stem
            out = spawn.role_settings(role)
            self.assertFalse(out.get("sandbox", {}).get("enabled"), role)

class Ledger(unittest.TestCase):
    def test_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            old = spawn.ROOT
            spawn.ROOT = Path(td)
            try:
                p = spawn.ledger_write({"role": "execution-observation", "outcome": "progressed"})
                p2 = spawn.ledger_write({"role": "review", "outcome": "errored"})
            finally:
                spawn.ROOT = old
            self.assertEqual(p, p2)
            lines = [json.loads(l) for l in p.read_text().splitlines()]
            self.assertEqual([l["role"] for l in lines], ["execution-observation", "review"])

    @pytest.mark.slow
    def test_entry_carries_the_live_log_path(self):
        # 이슈 #192 요구사항 2: ledger 엔트리의 `log` 필드가 그 세션이 실제
        # 쓴 라이브 로그(로스터에 등록된 값)와 같아야, 세션 종료 뒤 그
        # 로그를 session_id 로 되짚어 찾을 수 있다.
        import subprocess as sp
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-9-eo"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            entries = []
            roster_calls = []
            orig_roster_register = spawn.roster_register

            def spy_roster_register(key, entry):
                roster_calls.append((key, dict(entry)))
                return orig_roster_register(key, entry)

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       spy_roster_register), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: ([], True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: entries.append(entry)):
                    spawn._spawn_one(str(work), "execution-observation", "task\n",
                                     unattended=True, issue=9)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

            roster_entry = dict([e for k, e in roster_calls
                                 if k == "issue-9/execution-observation"][0])
            # 이슈 #2213: `_skill_judge_consult()`가 이제 자신의 몫으로
            # `skill_judge_perf` ledger 이벤트를 하나 더 남긴다(per-spawn
            # cross_family 계측, Acceptance) — 스폰당 ledger 엔트리가
            # 1개에서 2개로 늘었다. `log` 필드는 그 이벤트에 없고 스폰
            # 마무리 엔트리에만 있으므로, 그 엔트리를 이벤트 태그로
            # 골라서 검사한다.
            spawn_entries = [e for e in entries if e.get("event") != "skill_judge_perf"]
            self.assertEqual(len(spawn_entries), 1, entries)
            self.assertEqual(spawn_entries[0]["log"], roster_entry["log"])
            self.assertTrue(Path(spawn_entries[0]["log"]).exists())

    @pytest.mark.slow
    def test_toolchain_cache_env_redirected_into_workspace(self):
        """이슈 #406: cargo git 의존성이 홈 밖 쓰기로 승인 프롬프트에
        막히지 않도록, GOCACHE 등과 같은 자리에서 CARGO_HOME 도
        워크스페이스(.muster-cache) 안으로 재지정된다."""
        import subprocess as sp
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-9-eo"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: None), \
                     mock.patch.object(spawn.subprocess, "Popen",
                                       wraps=sp.Popen) as spied:
                    spawn._spawn_one(str(work), "execution-observation", "task\n",
                                     unattended=True, issue=9)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

            env_calls = [c.kwargs["env"] for c in spied.call_args_list
                         if "env" in c.kwargs]
            self.assertTrue(env_calls, spied.call_args_list)
            env = env_calls[0]
            self.assertEqual(env.get("CARGO_HOME"),
                             os.path.join(str(work), ".muster-cache", "cargo"))

class RequireDoctor(unittest.TestCase):
    def _with_root(self, td):
        old = spawn.ROOT
        spawn.ROOT = Path(td)
        return old

    def test_halts_without_doctor_pass(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                with self.assertRaises(SystemExit):
                    spawn.require_doctor(version="2.1.220 (Claude Code)")
            finally:
                spawn.ROOT = old

    def test_halts_on_version_change(self):
        # CLI 는 자동 업데이트된다. 훅이 headless 에서 도는 것은 문서가 아니라
        # 실측이 보증한다 — 버전이 바뀌면 보증도 끝난다.
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                (Path(td) / "runs").mkdir()
                (Path(td) / "runs" / "doctor-ok").write_text("2.1.219 (Claude Code)")
                with self.assertRaises(SystemExit):
                    spawn.require_doctor(version="2.1.220 (Claude Code)")
            finally:
                spawn.ROOT = old

    def test_passes_on_match(self):
        with tempfile.TemporaryDirectory() as td:
            old = self._with_root(td)
            try:
                (Path(td) / "runs").mkdir()
                (Path(td) / "runs" / "doctor-ok").write_text("2.1.220 (Claude Code)")
                spawn.require_doctor(version="2.1.220 (Claude Code)")  # no raise
            finally:
                spawn.ROOT = old

class FixtureShapeContracts(unittest.TestCase):
    """이슈 #335: 픽스처 shape 이 실제 인터페이스에서 벗어나면 조용히
    통과하는 대신 여기서 시끄럽게 실패해야 한다."""

    GOLDEN_GH_PATH = os.path.join(
        os.path.dirname(__file__), "fixtures", "golden",
        "gh_paginate_slurp_sample.json")

    def _golden_gh_payload(self):
        with open(self.GOLDEN_GH_PATH, encoding="utf-8") as f:
            return json.load(f)

    def test_gh_paginate_slurp_golden_sample_matches_own_shape_check(self):
        # 실제 dependency(gh api)에 대해 완전히 검증되는 유일한 리그: 이
        # 픽스처는 실측 캡처본이고(proposal 참고), 그 자체를 shape-check로
        # 검증한다 — 체크가 자기 자신만 확인하는 게 아님을 보인다.
        payload = self._golden_gh_payload()
        shape_contracts.assert_gh_paginate_slurp_shape(payload)

    def test_gh_paginate_slurp_shape_fails_loudly_on_missing_field(self):
        payload = self._golden_gh_payload()
        broken = [[dict(c) for c in page] for page in payload]
        for page in broken:
            for comment in page:
                del comment["body"]
        if not any(comment for page in broken for comment in page):
            self.skipTest("golden sample has no comments to break")
        with self.assertRaises(AssertionError) as cm:
            shape_contracts.assert_gh_paginate_slurp_shape(broken)
        self.assertIn("body", str(cm.exception))

    def test_gh_paginate_slurp_shape_fails_on_non_list_page(self):
        with self.assertRaises(AssertionError):
            shape_contracts.assert_gh_paginate_slurp_shape([{"not": "a list"}])

    def test_stream_event_shape_accepts_fixtures_spawn_py_reads(self):
        _event("result", permission_denials=[{"tool_name": "Write"}])
        _event("user", message={"content": [
            {"type": "tool_result", "is_error": True, "tool_use_id": "t1",
             "content": "boom"}]})
        _event("assistant", message={"content": [
            {"type": "tool_use", "id": "t1", "name": "Write", "input": {}}]})

    def test_stream_event_shape_fails_when_fixture_missing_field_parser_reads(self):
        # tool_use_id 가 spawn.py:1608 부근에서 상관관계 확인에 쓰인다 —
        # 픽스처가 이 필드를 빠뜨리면 시끄럽게 실패해야 한다.
        with self.assertRaises(AssertionError) as cm:
            _event("user", message={"content": [
                {"type": "tool_result", "is_error": True, "content": "boom"}]})
        self.assertIn("tool_use_id", str(cm.exception))

    def test_stream_event_shape_rejects_unknown_top_level_type(self):
        # spawn.py 파서가 읽지 않는 필드를 픽스처가 선언하면(여기서는
        # top-level type 자체가 파서 기대 밖) — 파서가 실제로 읽는 값
        # 집합과 픽스처가 어긋났다는 뜻이므로 실패해야 한다.
        with self.assertRaises(AssertionError):
            shape_contracts.assert_claude_stream_event_shape({"type": "system"})


class DryRunCwdValidation(unittest.TestCase):
    """#288 N2: --dry-run 은 -C 를 검증하지 않고 세션 설정 JSON을 찍어
    존재하지 않는 경로도 "검증됨"처럼 보이게 만들었다."""

    def test_dry_run_rejects_nonexistent_cwd(self):
        old_argv = sys.argv
        sys.argv = ["spawn.py", "coding", "task", "--dry-run",
                    "-C", "/nonexistent/path/does-not-exist-288"]
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        finally:
            sys.stdout = old_stdout
            sys.argv = old_argv
        self.assertNotEqual(cm.exception.code, 0)
        self.assertEqual(buf.getvalue(), "")

    def test_dry_run_rejects_cwd_that_is_a_file(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "plainfile"
            f.write_text("x")
            old_argv = sys.argv
            sys.argv = ["spawn.py", "coding", "task", "--dry-run", "-C", str(f)]
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with self.assertRaises(SystemExit) as cm:
                    spawn.main()
            finally:
                sys.stdout = old_stdout
                sys.argv = old_argv
            self.assertNotEqual(cm.exception.code, 0)
            self.assertEqual(buf.getvalue(), "")

class IssueArgValidation(unittest.TestCase):
    """#288 N3: --issue 는 argparse type=int 라 0/음수/거대정수도 통과했다."""

    def test_positive_int_accepts_valid(self):
        self.assertEqual(spawn.positive_int("51"), 51)

    def test_positive_int_rejects_zero(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            spawn.positive_int("0")

    def test_positive_int_rejects_negative(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            spawn.positive_int("-5")

    def test_issue_zero_rejected_at_parse_time_before_any_logic(self):
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "0"]
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        finally:
            sys.stderr = old_stderr
            sys.argv = old_argv
        self.assertEqual(cm.exception.code, 2)

    def test_issue_negative_rejected_at_parse_time(self):
        old_argv = sys.argv
        sys.argv = ["spawn.py", "watch", "--issue", "-5"]
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            with self.assertRaises(SystemExit) as cm:
                spawn.main()
        finally:
            sys.stderr = old_stderr
            sys.argv = old_argv
        self.assertEqual(cm.exception.code, 2)

class BoardNonNumericSubjectWarning(unittest.TestCase):
    """#288 N4: board() 는 issue-NaN 같은 비숫자 issue-* 디렉터리를 아무
    경고 없이 그냥 빼버렸다 — 서브젝트가 오케스트레이터 라우팅에서 조용히
    사라졌다."""

    def test_non_numeric_subject_dir_excluded_and_warned(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            docs = root / "docs"
            good = docs / "issue-12" / "reports"
            bad = docs / "issue-NaN" / "reports"
            good.mkdir(parents=True)
            bad.mkdir(parents=True)
            role = spawn.ROLES[0]
            (good / f"{role}.md").write_text("---\nloop_state: done\n---\nbody")
            (bad / f"{role}.md").write_text("---\nloop_state: done\n---\nbody")

            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                found = spawn.board(root)
                warned = sys.stderr.getvalue()
            finally:
                sys.stderr = old_stderr

            self.assertIn("issue-12", found)
            self.assertNotIn("issue-NaN", found)
            self.assertIn("issue-NaN", warned)

class DiagnoseHealth(unittest.TestCase):
    """이슈 #782 스코프-확장: HEALTHY/STALLED/DEADLOCKED/DEAD-ERRORED."""

    def setUp(self):
        self._orig_pr = spawn._pr_open_or_merged_for_branch
        self._orig_verdict = spawn.session_end_verdict

    def tearDown(self):
        spawn._pr_open_or_merged_for_branch = self._orig_pr
        spawn.session_end_verdict = self._orig_verdict

    def _entry(self, log, work=None, pid=None, issue=1, role="implementation"):
        return {"log": str(log), "work": work, "ts": int(time.time()),
                "pid": pid, "issue": issue, "role": role}

    def test_healthy_when_alive_and_no_anomalies(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid()), state={})
            self.assertEqual(out["state"], "HEALTHY")
            self.assertEqual(out["next_action"], "none")

    def test_adhoc_entry_detail_is_tagged_and_names_task(self):
        """Issue #2293: a no-issue (adhoc) entry's detail must say ADHOC
        prominently and name the task's first words, so a `[poll-report]`
        HEALTHY line can never read as "your issue-N spawn is fine"."""
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            entry = self._entry(log, pid=os.getpid(), issue=None)
            entry["task"] = "538"
            out = spawn.diagnose_health("k", entry, state={})
            self.assertEqual(out["state"], "HEALTHY")
            self.assertIn("ADHOC", out["detail"])
            self.assertIn("538", out["detail"])

    def test_issue_scoped_entry_detail_has_no_adhoc_tag(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid(), issue=1), state={})
            self.assertEqual(out["state"], "HEALTHY")
            self.assertNotIn("ADHOC", out["detail"])

    def test_stalled_when_alive_but_idle_past_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid()), state={})
            self.assertEqual(out["state"], "STALLED")
            self.assertEqual(out["next_action"], "resume-watch")

    def test_deadlocked_when_same_refusal_signature_repeats_no_progress(self):
        with tempfile.TemporaryDirectory() as td:
            work = str(Path(td) / "work")
            events_path = spawn._events_path(work)
            for _ in range(spawn.DEADLOCK_MIN_REPEATS):
                spawn._append_event(events_path, "gate-refusal",
                                     {"gate": "g", "reason": "no"})
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.diagnose_health(
                "k", self._entry(log, work=work, pid=os.getpid()), state={})
            self.assertEqual(out["state"], "DEADLOCKED")
            self.assertEqual(out["next_action"], "surface-repeating-cause")

    def test_not_deadlocked_when_progress_event_follows_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            work = str(Path(td) / "work")
            events_path = spawn._events_path(work)
            for _ in range(spawn.DEADLOCK_MIN_REPEATS):
                spawn._append_event(events_path, "gate-refusal",
                                     {"gate": "g", "reason": "no"})
            spawn._append_event(events_path, "progress", {"file_path": "x"})
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.diagnose_health(
                "k", self._entry(log, work=work, pid=os.getpid()), state={})
            self.assertNotEqual(out["state"], "DEADLOCKED")

    def test_not_deadlocked_when_refusal_signatures_differ(self):
        with tempfile.TemporaryDirectory() as td:
            work = str(Path(td) / "work")
            events_path = spawn._events_path(work)
            for i in range(spawn.DEADLOCK_MIN_REPEATS):
                spawn._append_event(events_path, "gate-refusal",
                                     {"gate": "g", "reason": f"no-{i}"})
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.diagnose_health(
                "k", self._entry(log, work=work, pid=os.getpid()), state={})
            self.assertNotEqual(out["state"], "DEADLOCKED")

    def test_dead_errored_when_absent_from_ps_and_no_pr(self):
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn.session_end_verdict = lambda work, log_path, now=None: "crashed"
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.diagnose_health(
                "k", self._entry(log, work=str(Path(td) / "work"), pid=999999999),
                state={})
            self.assertEqual(out["state"], "DEAD-ERRORED")
            self.assertEqual(out["next_action"], "respawn")

    def test_completion_no_event_reports_none_state_when_pr_found(self):
        # completion-no-event: 세션이 죽었는데 watch 이벤트가 없어도, PR 이
        # 이미 열려 있으면(폴링이 gh pr list 로 확인) 이건 헬스 진단
        # 대상이 아니라 completion — diagnose_health 는 조용히 비켜준다.
        spawn._pr_open_or_merged_for_branch = lambda root, branch: 42
        spawn.session_end_verdict = lambda work, log_path, now=None: None
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.diagnose_health(
                "k", self._entry(log, work=str(Path(td) / "work"), pid=999999999),
                state={})
            self.assertIsNone(out["state"])

    def test_completion_no_event_reports_none_state_when_verdict_normal(self):
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn.session_end_verdict = lambda work, log_path, now=None: "normal"
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.diagnose_health(
                "k", self._entry(log, work=str(Path(td) / "work"), pid=999999999),
                state={})
            self.assertIsNone(out["state"])

    def test_dead_unrecovered_commits_when_commit_count_given(self):
        # 이슈 #2193: plugin reload 등으로 워처 자신까지 죽어
        # `ensure_pushed()` 가 못 돈 죽음은 "커밋은 있는데 PR 없음" —
        # `commit_count` 를 넘기면 그냥 DEAD-ERRORED 로 뭉개지 않고 브랜치명
        # + 커밋 개수를 이름 붙인 별도 상태로 갈린다.
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn.session_end_verdict = lambda work, log_path, now=None: "crashed"
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("")
            work = str(Path(td) / "issue-2193" / "implementation")
            out = spawn.diagnose_health(
                "issue-2193/implementation",
                self._entry(log, work=work, pid=999999999, issue=2193),
                state={}, commit_count=3)
            self.assertEqual(out["state"], "DEAD-UNRECOVERED-COMMITS")
            self.assertEqual(out["next_action"], "recover-unpushed")
            self.assertIn("implementation", out["detail"])
            self.assertIn("커밋 3개", out["detail"])

    def test_dead_errored_when_commit_count_zero(self):
        # empty state (이슈 본문): 커밋이 아예 없던 죽음은 여전히
        # DEAD-ERRORED — 회복할 게 없다는 뜻이므로 새 상태로 갈리지 않는다.
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn.session_end_verdict = lambda work, log_path, now=None: "crashed"
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.diagnose_health(
                "k", self._entry(log, work=str(Path(td) / "work"), pid=999999999),
                state={}, commit_count=0)
            self.assertEqual(out["state"], "DEAD-ERRORED")

    def test_completed_and_pushed_not_dead_errored_even_with_commits(self):
        # 회귀 가드(이슈 #2180 오보 재현 방지): PR 이 실제로 존재하면(=
        # 완료+push 됨) commit_count 가 몇이든 DEAD-ERRORED 로도
        # DEAD-UNRECOVERED-COMMITS 로도 보고되면 안 된다 — completion 이다.
        spawn._pr_open_or_merged_for_branch = lambda root, branch: 2183
        spawn.session_end_verdict = lambda work, log_path, now=None: None
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.diagnose_health(
                "k", self._entry(log, work=str(Path(td) / "work"), pid=999999999),
                state={}, commit_count=5)
            self.assertIsNone(out["state"])
            self.assertNotEqual(out["state"], "DEAD-ERRORED")

    def test_idle_no_double_act_reusing_precomputed_anomalies(self):
        # idle-no-double-act: watchdog_check_one() 은 오프셋을 소비하는
        # 부수효과가 있다 — 같은 틱에서 두 번 부르면 두 번째 호출이 빈
        # 텍스트만 보고 신호를 놓친다. diagnose_health 에 미리 계산한
        # anomalies 를 넘기면 이 이중-소비가 안 일어난다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            entry = self._entry(log, pid=os.getpid())
            state = {}
            anomalies = spawn.watchdog_check_one("k", entry, state=state)
            self.assertTrue(any("log-silence" in a for a in anomalies))
            out = spawn.diagnose_health("k", entry, state=state, anomalies=anomalies)
            self.assertEqual(out["state"], "STALLED")
            # anomalies 를 넘겼으니 diagnose_health 가 watchdog_check_one 을
            # 다시 부르지 않는다 — state["k"]["offset"] 이 그대로다(재소비 없음).
            offset_after_first_call = state["k"]["offset"]
            self.assertEqual(offset_after_first_call, log.stat().st_size)

    @staticmethod
    def _hb_line(ts, extra=None):
        obj = {"type": "tool_progress",
               "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ts))}
        if extra:
            obj.update(extra)
        return json.dumps(obj)

    @staticmethod
    def _substantive_line(ts):
        return json.dumps({"type": "assistant",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ts)),
                            "message": {"content": [{"type": "text", "text": "working"}]}})

    def test_advisory_heartbeat_only_stall_for_observed_hang_shape(self):
        # 이슈 #1966: 이슈-1959 실측(22분간 pytest-xdist 워커가 futex 에
        # 걸려 tool_progress 하트비트만 계속 찍고 실질 진행은 없던 형태)을
        # 재현하는 합성 픽스처. WATCHDOG_HEARTBEAT_ONLY_MIN(18분)보다 긴
        # 22분간 하트비트 줄만 있으면 새 advisory 서브상태로 분류되어야
        # 한다 — log-silence 는 mtime 이 계속 갱신되므로 안 잡힌다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            now = time.time()
            start = now - 22 * 60
            lines = []
            ts = start
            while ts <= now:
                lines.append(self._hb_line(ts))
                ts += 60
            log.write_text("\n".join(lines) + "\n")
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid()), state={}, now=now)
            self.assertEqual(out["state"], "STALLED-HEARTBEAT-ONLY")

    def test_healthy_when_substantive_lines_interleaved_with_heartbeats(self):
        # 같은 22분짜리 하트비트-only 픽스처에 substantive 줄(assistant
        # 텍스트) 하나를 최근 창 안에 섞으면 HEALTHY 로 분류돼야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            now = time.time()
            start = now - 22 * 60
            lines = []
            ts = start
            while ts <= now:
                lines.append(self._hb_line(ts))
                ts += 60
            lines.append(self._substantive_line(now - 60))
            log.write_text("\n".join(lines) + "\n")
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid()), state={}, now=now)
            self.assertEqual(out["state"], "HEALTHY")

    def test_advisory_heartbeat_only_state_never_reaches_kill_refusal_or_gate_action(self):
        # 구조적 확인: advisory 상태의 next_action 이 kill/spawn-거부/
        # 게이트-블록 경로에 닿지 않는다 — STALLED 가 이미 속한 것과 같은
        # 허용된 advisory 액션 집합에 속해야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            now = time.time()
            start = now - 22 * 60
            lines = []
            ts = start
            while ts <= now:
                lines.append(self._hb_line(ts))
                ts += 60
            log.write_text("\n".join(lines) + "\n")
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid()), state={}, now=now)
            self.assertEqual(out["state"], "STALLED-HEARTBEAT-ONLY")
            allowed_advisory_actions = {"resume-watch"}
            self.assertIn(out["next_action"], allowed_advisory_actions)
            kill_refusal_gate_actions = {"respawn", "surface-repeating-cause"}
            self.assertNotIn(out["next_action"], kill_refusal_gate_actions)
            src = inspect.getsource(spawn)
            self.assertNotIn("STALLED-HEARTBEAT-ONLY", "\n".join(
                l for l in src.splitlines()
                if any(k in l for k in ("kill", "refuse", "refusal", "gate_block",
                                         "spawn_refusal"))))

    def test_unmeasurable_log_without_heartbeat_tag_stays_healthy(self):
        # 이슈 #1966 제약: tool_progress 태그를 아예 안 찍는(구식/다른 종류)
        # 로그는 판정 불가 -> HEALTHY 로 남아야 한다, 조용히 STALLED 로
        # 오판하지 않는다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            now = time.time()
            start = now - 22 * 60
            lines = []
            ts = start
            while ts <= now:
                lines.append(self._substantive_line(ts))
                ts += 60
            log.write_text("\n".join(lines) + "\n")
            out = spawn.diagnose_health(
                "k", self._entry(log, pid=os.getpid()), state={}, now=now)
            self.assertEqual(out["state"], "HEALTHY")


class RequirementIntakeValidityConsult(unittest.TestCase):
    """issue-1024: intake with a validity-consult trace recorded passes;
    intake without consult and without an explicit skip reason is
    flagged."""

    @classmethod
    def setUpClass(cls):
        gates_dir = str(Path(__file__).resolve().parent.parent / "gates")
        if gates_dir not in sys.path:
            sys.path.insert(0, gates_dir)
        import requirement_intake_consult
        cls.mod = requirement_intake_consult

    def test_intake_with_consult_trace_passes(self):
        body = "## Request\nAdd a thing.\n\nvalidity-consult: req-eng run, feasible.\n"
        self.assertEqual(self.mod.check_issue_body(1024, body), [])

    def test_intake_with_skip_trivial_passes(self):
        body = "## Request\nFix a typo.\n\nvalidity-consult-skip: trivial\n"
        self.assertEqual(self.mod.check_issue_body(1024, body), [])

    def test_intake_without_consult_or_skip_is_flagged(self):
        body = "## Request\nAdd a thing with no consult recorded.\n"
        bad = self.mod.check_issue_body(1024, body)
        self.assertTrue(bad)

class RequireRequirementLinkageRemoteBranch(unittest.TestCase):
    """issue-1042: `require_requirement_linkage` must detect a
    remote-only `issue-N/*` branch as already-spawned (not misread as
    never-spawned), and must still fall through to the requirement-linkage
    check when no such branch exists at all — local or remote."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def _make_marker(self, root):
        (root / "docs" / "specs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "specs" / "approvers.md").write_text("- someone\n")

    @pytest.mark.slow
    def test_remote_branch_only_detected_as_already_spawned(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")
            base_branch = subprocess.run(
                ["git", "-C", str(origin), "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()

            issue = 999902
            br = f"issue-{issue}/implementation"
            self._git(origin, "checkout", "-q", "-b", br)
            (origin / "b.txt").write_text("work")
            self._git(origin, "add", "b.txt")
            self._git(origin, "commit", "-q", "-m", "issue branch commit")
            self._git(origin, "checkout", "-q", base_branch)

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                                capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")
            self._make_marker(work)

            # 사전 조건: work 저장소엔 로컬 `br` 브랜치가 없다 — 원격
            # 트래킹 참조로만 존재한다.
            self.assertNotEqual(
                self._git(work, "rev-parse", "--verify", "-q", br).returncode, 0)

            sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
            import ci as _ci

            with mock.patch.object(_ci, "_approved_roles_on_issue", lambda root, iss: set()):
                spawn.require_requirement_linkage(str(work), issue)  # 예외 없이 통과해야 한다

    def test_no_remote_branch_no_local_falls_through_to_requirement_linkage_check(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            (work / "a.txt").write_text("base")
            self._git(work, "add", "a.txt")
            self._git(work, "commit", "-q", "-m", "base commit")
            self._make_marker(work)

            issue = 999903
            sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
            import ci as _ci
            import requirement_linkage as _requirement_linkage

            with mock.patch.object(_ci, "_approved_roles_on_issue", lambda root, iss: set()), \
                 mock.patch.object(_requirement_linkage, "check", lambda root, iss: ["no requirement id cited"]):
                with self.assertRaises(SystemExit):
                    spawn.require_requirement_linkage(str(work), issue)

    def test_refusal_message_is_self_serviceable(self):
        """issue #2125: the refusal must carry (a) the digest path, (b) an
        example citation line, (c) the escape-hatch tag verbatim, (d) when
        that tag is appropriate — a first-time consumer must be able to act
        without reading source."""
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            (work / "a.txt").write_text("base")
            self._git(work, "add", "a.txt")
            self._git(work, "commit", "-q", "-m", "base commit")
            self._make_marker(work)

            issue = 999904
            sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
            import ci as _ci
            import requirement_linkage as _requirement_linkage

            with mock.patch.object(_ci, "_approved_roles_on_issue", lambda root, iss: set()), \
                 mock.patch.object(_requirement_linkage, "check", lambda root, iss: ["no requirement id cited"]):
                with self.assertRaises(SystemExit) as ctx:
                    spawn.require_requirement_linkage(str(work), issue)
            msg = str(ctx.exception)
            self.assertIn("docs/specs/requirement-digest.md", msg)
            self.assertIn("Targets R1.", msg)
            self.assertIn("infrastructure/no-direct-requirement", msg)
            self.assertIn("적절하다", msg)  # the when-appropriate sentence

class RequirementDigestScaffold(unittest.TestCase):
    """issue #1695: `spawn.py init` scaffolds
    `docs/specs/requirement-digest.md` on a fresh repo, never overwrites."""

    def test_creates_stub_when_absent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wrote = spawn.init_requirement_digest(str(root))
            self.assertTrue(wrote)
            dest = root / spawn.REQUIREMENT_DIGEST_MARKER
            self.assertTrue(dest.is_file())
            text = dest.read_text(encoding="utf-8")
            self.assertRegex(text, r"\bR\d+\b")
            self.assertIn("R-entry format", text)

    def test_second_run_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dest = root / spawn.REQUIREMENT_DIGEST_MARKER
            dest.parent.mkdir(parents=True)
            custom = "- R1: hand-authored entry [enforced] (source: #1)\n"
            dest.write_text(custom, encoding="utf-8")

            wrote = spawn.init_requirement_digest(str(root))

            self.assertFalse(wrote)
            self.assertEqual(dest.read_text(encoding="utf-8"), custom)

    def test_init_board_scaffolds_digest_alongside_approvers(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(
                    subprocess, "run",
                    return_value=subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="octocat\n")):
                rc = spawn.init_board(str(root), login=None)
            self.assertEqual(rc, 0)
            self.assertTrue((root / spawn.MARKER).is_file())
            self.assertTrue((root / spawn.REQUIREMENT_DIGEST_MARKER).is_file())

    def test_init_board_leaves_existing_digest_untouched_on_second_call(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(
                    subprocess, "run",
                    return_value=subprocess.CompletedProcess(
                        args=[], returncode=0, stdout="octocat\n")):
                spawn.init_board(str(root), login="octocat")
                digest = root / spawn.REQUIREMENT_DIGEST_MARKER
                custom = "- R7: already here [enforced] (source: #7)\n"
                digest.write_text(custom, encoding="utf-8")

                spawn.init_board(str(root), login="octocat")

            self.assertEqual(digest.read_text(encoding="utf-8"), custom)


class DesignBearingSingleFetch(unittest.TestCase):
    """이슈 #2186: `_spawn_one`은 이슈 본문을 "issue_fetch" 단계에서 이미
    `gh_rest.fetch_issue()`로 한 번 받아온다. design-bearing 판정이 같은
    본문을 `gh_rest.fetch_issue_body()`로 또 받아오면(예전 동작) 스폰마다
    똑같은 `gh api` 왕복이 중복된다 — 그 중복 fetch 가 다시는 없는지
    검증한다(이미 있는 `body`를 `check_issue_body()`에 바로 넘긴다)."""

    @pytest.mark.slow
    def test_design_bearing_never_refetches_the_issue_body(self):
        import subprocess as sp
        from unittest import mock

        sys.path.insert(0, str((Path(spawn.ROOT) / "gates").resolve()))
        import gh_rest

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-9-impl"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster

            design_bearing_body = ("design-bearing-override: yes\n\n"
                                   "이 이슈는 새 화면을 설계한다.\n")
            fetch_issue_body_calls = []

            def spy_fetch_issue_body(*a, **k):
                fetch_issue_body_calls.append((a, k))
                return design_bearing_body

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: ([], True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: None), \
                     mock.patch.object(gh_rest, "fetch_issue",
                                       lambda repo, issue, run=None:
                                           {"title": "t", "body": design_bearing_body}), \
                     mock.patch.object(gh_rest, "fetch_issue_body",
                                       spy_fetch_issue_body):
                    spawn._spawn_one(str(work), "execution-observation", "task\n",
                                     unattended=True, issue=9)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

            self.assertEqual(fetch_issue_body_calls, [],
                             "design-bearing check re-fetched the issue body "
                             "via gh_rest.fetch_issue_body() instead of reusing "
                             "the body already fetched by issue_fetch (issue #2186)")


class ReturnedPRGateIsNonBlocking(unittest.TestCase):
    """이슈 #2201: #2186 의 "겹쳐서 join" 설계는 실측 스폰에서도 여전히
    6.608s(전체의 21%)를 세션 시작 전 블로킹 경로에 남겼다 — 그 결과
    (`_print_returned_pr_surfaced()`/ledger 이벤트)는 세션에 전달되는
    task 텍스트 어디에도 안 쓰이므로, auto_sweep(#2195)과 같은 완전
    fire-and-forget 데몬 스레드로 바꿨다. 이 스위트는 (1) gh 조회가
    느려도(워크스페이스 셋업이 그만큼 안 겹쳐도) "returned_pr_gate"
    단계가 그 완료를 기다리지 않는다, (2) 조회 자체는 실제로 백그라운드
    에서 실행된다(회귀 가드)를 함께 확인한다
    (`test_auto_sweep_nonblocking.py` 와 같은 패턴)."""

    @pytest.mark.slow
    def test_slow_gh_lookup_does_not_block_spawn_or_its_timed_phase(self):
        import subprocess as sp
        from unittest import mock

        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-9-impl"
            work.mkdir()
            run = lambda *a: sp.run(a, cwd=str(work), capture_output=True,
                                    text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster

            started = threading.Event()
            release = threading.Event()
            _SLOW_LOOKUP_SECONDS = 2.0

            def slow_undispositioned_role_prs(root, exclude_issue=None):
                started.set()
                # 워크스페이스 셋업이 이 시간을 전혀 겹쳐주지 않아도(아래
                # issue_workspace 는 즉시 리턴한다) 여전히 안 기다려야
                # 한다는 것을 보이려고, 겹칠 다른 작업 없이 그냥 오래 잡는다.
                release.wait(_SLOW_LOOKUP_SECONDS)
                return [], True

            buf = io.StringIO()
            stderr_buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            spawn._BOOTSTRAP_TIMING.clear()
            try:
                with contextlib.redirect_stderr(stderr_buf), \
                     mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       slow_undispositioned_role_prs), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: None):
                    spawn._spawn_one(str(work), "execution-observation", "task\n",
                                     unattended=True, issue=9)

                # (1) 블로킹 경로에서 빠졌다: gh 조회가 2s 를 쥐고 있어도
                # "returned_pr_gate" bootstrap phase(디스패치만 잰다)는
                # 짧다.
                join_wait = spawn._BOOTSTRAP_TIMING.get("returned_pr_gate", 0.0)
                self.assertLess(
                    join_wait, _SLOW_LOOKUP_SECONDS / 2,
                    f"returned_pr_gate phase 가 gh 조회 완료를 기다린 것으로 "
                    f"보인다 (phase={join_wait})")

                # (2) 회귀 가드: 조회 자체는 실제로(백그라운드에서) 여전히
                # 실행된다.
                self.assertTrue(started.wait(_SLOW_LOOKUP_SECONDS),
                                "returned-PR 게이트가 백그라운드에서도 "
                                "호출되지 않았다")
                release.set()

                # (3) 회귀 가드: 백그라운드 완료가 stderr 에서 완전히 안
                # 보이게 되진 않는다 — 걸린 시간이 찍힌다.
                deadline = time.monotonic() + _SLOW_LOOKUP_SECONDS
                while ("returned-pr 게이트(백그라운드)" not in stderr_buf.getvalue()
                       and time.monotonic() < deadline):
                    time.sleep(0.02)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster

        self.assertIn("returned-pr 게이트(백그라운드)", stderr_buf.getvalue())

    @pytest.mark.slow
    def test_bounded_fork_parent_join_still_captures_a_slow_lookup(self):
        """이슈 #2201 헌트(docs/issue-2201/reports/implementation/2026-08-24-
        hunt-bootstrap-cross-family-returned-pr-gate.md): `--issue` 로 도는
        실제 CLI 경로는 `bounded=True` 다 — 그 parent 는 워처를 무장한 뒤
        곧장 `return 0` 하고, 곧이어 `sys.exit()` 로 인터프리터가 죽는다.
        데몬 스레드는 join 없이 그 시점에 그냥 죽으므로, 이 join 이 없으면
        gh 조회가 그 짧은 창을 못 맞출 때 surfacing/ledger 부수효과가
        통째로 사라진다(헌트가 mock 스캐폴딩으로 재현). 이 테스트는
        `os.fork()` 를 실제로 하지 않고 parent 분기를 흉내내(기존
        `test_spawn_board_flows.py::_full_mock_scaffold` 와 같은 패턴)
        gh 조회가 join 상한(10s) 안에서 끝나면 `_spawn_one()` 자신의
        리턴 시점에 이미 완료돼 있음을 확인한다."""
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "issue-9-impl"
            work.mkdir()
            run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                            text=True, check=True)
            run("git", "init", "-q")
            run("git", "config", "user.email", "t@example.com")
            run("git", "config", "user.name", "t")
            (work / "f.txt").write_text("x")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "init")

            old_roster, old_idx = spawn.ROSTER, spawn.WORKSPACE_INDEX
            spawn.ROSTER = Path(td) / "active.json"
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"

            ledger_calls = []
            _LOOKUP_SECONDS = 1.0  # < 10s join 상한 — 끝났어야 정상

            def slow_undispositioned_role_prs(root, exclude_issue=None):
                time.sleep(_LOOKUP_SECONDS)
                return [], False  # fail-open 경로 — ledger 이벤트로 관측한다

            class FakeWatcherProc:
                pid = 424242

            real_popen = subprocess.Popen

            def selective_popen(cmd, *a, **k):
                if isinstance(cmd, list) and "watch" in cmd:
                    return FakeWatcherProc()
                return real_popen(cmd, *a, **k)

            try:
                with mock.patch.object(os, "fork", return_value=4321), \
                     mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda role, repo_root: {
                                           "source": "skill-repo", "skill_dirs": [],
                                           "skills": [], "skill_sha": None}), \
                     mock.patch.object(spawn, "_skill_repo_root", lambda: Path(td)), \
                     mock.patch.object(spawn, "_cross_family_skill_matches_with_consult",
                                       lambda *a, **k: ([], "no-candidates")), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "_clean_auto_enabled", lambda: False), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                     mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       slow_undispositioned_role_prs), \
                     mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                     mock.patch.object(spawn.subprocess, "Popen", selective_popen), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)):
                    t0 = time.monotonic()
                    rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                          unattended=True, issue=9, bounded=True,
                                          no_wait=True)
                    elapsed = time.monotonic() - t0
            finally:
                spawn.ROSTER, spawn.WORKSPACE_INDEX = old_roster, old_idx

            self.assertEqual(rc, 0)
            # 스폰 자신의 리턴 시점에 이미 gh 조회(1s)가 끝나 있어야 한다 —
            # join 이 없다면(헌트가 재현한 회귀) ledger 에 아무 것도 안 남는다.
            events = [e.get("event") for e in ledger_calls]
            self.assertIn(
                "returned_pr_gate_fail_open", events,
                f"bounded parent 가 리턴하기 전에 returned_pr_gate 백그라운드 "
                f"스레드를 join 하지 않은 것으로 보인다 (ledger={ledger_calls})")
            # join 상한이 실제로 걸려 있다는 방향 증거 — 1s 조회가 1s 근처에서
            # 끝났지, 10s 상한을 다 채우지 않았다.
            self.assertLess(elapsed, _LOOKUP_SECONDS + 5.0,
                            f"join 이 예상보다 훨씬 오래 걸렸다 (elapsed={elapsed:.3f}s)")

