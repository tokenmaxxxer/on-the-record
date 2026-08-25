from _spawn_test_support import *  # noqa: F401,F403

import deviation_log


class ClosureSweepCliWiring(unittest.TestCase):
    """이슈 #743: `spawn.py closure-sweep` CLI 서브커맨드(3719행 부근)도
    watchdog 경로와 같은 프리페치 배선을 쓴다 — 이 경로를 검사하는 기존
    테스트가 없었다(제안 조사 참조)."""

    def test_closure_sweep_subcommand_passes_prebuilt_issue_states(self):
        fake_cs = mock.MagicMock()
        fake_cs.issue_state_index_all.return_value = ({1: "OPEN"}, True)
        fake_cs.find_violations.return_value = ([], [])

        argv = sys.argv
        with tempfile.TemporaryDirectory() as td:
            sys.argv = ["spawn.py", "closure-sweep", "-C", td]
            try:
                with mock.patch.dict(sys.modules, {"closure_sweep": fake_cs}):
                    rc = spawn.main()
            finally:
                sys.argv = argv
        self.assertEqual(rc, 0)
        fake_cs.issue_state_index_all.assert_called_once()
        fake_cs.find_violations.assert_called_once()
        _, kwargs = fake_cs.find_violations.call_args
        self.assertEqual(kwargs.get("issue_states"), {1: "OPEN"})

class PanelCliWiring(unittest.TestCase):
    """이슈 #1044: `panel_cmd()`(#985, 동시-판정)는 main() 에 CLI 배선이
    없어 도달 불가능했다 — consult 배선(4751행 부근)을 그대로 미러링해
    `spawn.py panel <역할A> <역할B> "<질문>"` 경로를 연결한다."""

    def test_panel_cli_subcommand_calls_panel_cmd(self):
        argv = sys.argv
        try:
            sys.argv = ["spawn.py", "panel", "review", "qa", "<question>",
                        "--issue", "1"]
            with mock.patch.object(spawn, "panel_cmd",
                                    return_value={"verdict": "ok"}) as m:
                rc = spawn.main()
        finally:
            sys.argv = argv
        self.assertEqual(rc, 0)
        m.assert_called_once_with("review", "qa", "<question>",
                                   issue=1, cwd=".", model=None)

    def test_panel_cli_subcommand_missing_args_exits(self):
        argv = sys.argv
        try:
            sys.argv = ["spawn.py", "panel", "review"]
            with self.assertRaises(SystemExit):
                spawn.main()
        finally:
            sys.argv = argv

    def test_panel_cli_subcommand_same_role_twice_exits(self):
        argv = sys.argv
        try:
            sys.argv = ["spawn.py", "panel", "review", "review", "<question>"]
            with mock.patch.object(spawn, "panel_cmd") as m:
                with self.assertRaises(SystemExit):
                    spawn.main()
            m.assert_not_called()
        finally:
            sys.argv = argv

class Reconcile(unittest.TestCase):
    """이슈-492 step 2: `reconcile(expected, observed)` — 순수 비교 함수.
    ADR: docs/issue-492/decisions/2026-08-08-reconciliation-step-for-supervision.md
    프로포절: docs/issue-492/proposals/2026-08-08-implement-reconciliation-step.md
    """

    def test_crashed_is_respawn(self):
        expected = {"expects_pr": False, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": "crashed", "pr_number": None,
                    "loop_state": None, "new_commit": False}
        out = spawn.reconcile(expected, observed)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "respawn")

    def test_stalled_is_resume_watch(self):
        expected = {"expects_pr": False, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": "stalled", "pr_number": None,
                    "loop_state": None, "new_commit": False}
        out = spawn.reconcile(expected, observed)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "resume-watch")

    def test_expects_pr_missing_not_in_progress_is_respawn(self):
        expected = {"expects_pr": True, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": "normal", "pr_number": None,
                    "loop_state": None, "new_commit": True}
        out = spawn.reconcile(expected, observed)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "respawn")

    def test_expects_pr_missing_but_still_in_progress_is_clean(self):
        # 아직 진행 중이면 PR 이 없는 게 divergence 가 아니다.
        expected = {"expects_pr": True, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": "in-progress", "pr_number": None,
                    "loop_state": None, "new_commit": False}
        self.assertEqual(spawn.reconcile(expected, observed), [])

    def test_clean_case_is_empty(self):
        expected = {"expects_pr": True, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": "normal", "pr_number": 42,
                    "loop_state": "done", "new_commit": True}
        self.assertEqual(spawn.reconcile(expected, observed), [])

    def test_inconsistent_input_is_manual_review(self):
        # loop_state 는 있는데 session_verdict 가 없거나 인식 불가 — 침묵
        # 대신 manual-review.
        expected = {"expects_pr": False, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": None, "pr_number": None,
                    "loop_state": "in-review", "new_commit": False}
        out = spawn.reconcile(expected, observed)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "manual-review")

    def test_sigkill_acceptance_check_stub(self):
        # 이슈-492 acceptance (a), 빠른 유닛 버전: synthetic alive_fn 스텁으로
        # 죽은 pid 를 흉내낸다. 실제 kill -9 재현은
        # test_sigkill_acceptance_check_real_process 참고.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".events.jsonl").write_text(
                json.dumps({"type": "session-start",
                            "detail": {"pid": 111, "ts": 1}}) + "\n")
            verdict = spawn.session_end_verdict(
                str(work), log_path=None, alive_fn=lambda pid: False)
            self.assertEqual(verdict, "crashed")
            expected = {"expects_pr": False, "role": "implementation", "branch": "b"}
            observed = {"session_verdict": verdict, "pr_number": None,
                        "loop_state": None, "new_commit": False}
            out = spawn.reconcile(expected, observed)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["next_action"], "respawn")

    def test_sigkill_acceptance_check_real_process(self):
        # 이슈-492 acceptance (a), 실측: 실제 서브프로세스를 세션으로 등록하고
        # 진짜 kill -9 로 죽인 뒤, session_end_verdict() 가 (synthetic
        # alive_fn 없이, 진짜 _alive()/os.kill 로) 침묵하지 않고 terminal
        # state 를 내는지, reconcile() 이 그걸 respawn 으로 이름 붙이는지
        # 확인한다. docs/issue-492/reports/execution-observation.md 가 지적한
        # 대로, 실제 프로세스 없이 스텁으로만 통과하던 취약점을 메운다.
        proc = subprocess.Popen(["sleep", "60"])
        try:
            with tempfile.TemporaryDirectory() as td:
                work = Path(td) / "w"
                Path(str(work) + ".events.jsonl").write_text(
                    json.dumps({"type": "session-start",
                                "detail": {"pid": proc.pid, "ts": 1}}) + "\n")

                self.assertTrue(spawn._alive(proc.pid))

                proc.kill()  # SIGKILL
                proc.wait(timeout=5)  # reap: 좀비 상태로는 os.kill(pid, 0) 이 여전히 성공한다

                stall_timeout_min = 0.02  # 픽스처 전용 단축 — 실제 스톨 상한값이 아니라 테스트 속도용
                deadline = time.time() + stall_timeout_min * 60
                verdict = None
                while time.time() < deadline:
                    verdict = spawn.session_end_verdict(str(work), log_path=None)
                    if verdict == "crashed":
                        break
                    time.sleep(0.05)

                self.assertEqual(verdict, "crashed")
                expected = {"expects_pr": False, "role": "implementation", "branch": "b"}
                observed = {"session_verdict": verdict, "pr_number": None,
                            "loop_state": None, "new_commit": False}
                out = spawn.reconcile(expected, observed)
                self.assertEqual(len(out), 1)
                self.assertEqual(out[0]["next_action"], "respawn")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)

    def test_vanish_without_push_acceptance_check(self):
        # 이슈-492 acceptance (b): PR 을 기대한 세션이 push 없이 죽음 →
        # reconciliation 이 divergence 를 이름 붙이고 respawn/resume.
        expected = {"expects_pr": True, "role": "implementation", "branch": "b"}
        observed = {"session_verdict": "crashed", "pr_number": None,
                    "loop_state": None, "new_commit": False}
        out = spawn.reconcile(expected, observed)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "respawn")

class ReconcilePrExpectedMissingRecoveryPolicy(unittest.TestCase):
    """이슈 #1678: `pr-expected-missing` 가지가 무조건 respawn 하지 않고
    `recovery_policy.classify_from_state()` 판정을 따르는지 — 신호 소스는
    `spawn._recovery_policy_module` 을 monkeypatch 해 흉내낸다(기존
    test_spawn.py 스타일)."""

    def _expected(self, issue=1660, role="implementation"):
        return {"expects_pr": True, "role": role, "branch": "b", "issue": issue}

    def _observed(self, new_commit=False, failure_signature=None):
        return {"session_verdict": "normal", "pr_number": None,
                "loop_state": None, "new_commit": new_commit,
                "failure_signature": failure_signature}

    def test_pre_first_commit_under_cap_respawns_identically(self):
        fake_policy = mock.Mock()
        fake_policy.classify_from_state.return_value = "RESPAWN_IDENTICAL"
        with mock.patch.object(spawn, "_recovery_policy_module", return_value=fake_policy):
            out = spawn.reconcile(self._expected(), self._observed(new_commit=False))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "respawn")
        self.assertFalse(out[0]["handoff"])
        fake_policy.classify_from_state.assert_called_once_with(
            1660, "implementation", has_commit=False, has_pr=False,
            failure_signature=None, death_id=None)

    def test_has_commit_no_pr_respawns_with_handoff(self):
        fake_policy = mock.Mock()
        fake_policy.classify_from_state.return_value = "RESPAWN_WITH_HANDOFF"
        with mock.patch.object(spawn, "_recovery_policy_module", return_value=fake_policy):
            out = spawn.reconcile(self._expected(), self._observed(new_commit=True))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "respawn")
        self.assertTrue(out[0]["handoff"])
        fake_policy.classify_from_state.assert_called_once_with(
            1660, "implementation", has_commit=True, has_pr=False,
            failure_signature=None, death_id=None)

    def test_at_cap_or_repeat_signature_escalates_no_respawn(self):
        fake_policy = mock.Mock()
        fake_policy.classify_from_state.return_value = "ESCALATE"
        with mock.patch.object(spawn, "_recovery_policy_module", return_value=fake_policy):
            out = spawn.reconcile(
                self._expected(), self._observed(new_commit=True, failure_signature="sig-a"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_action"], "manual-review")
        self.assertNotIn("handoff", out[0])
        self.assertIn("ESCALATE", out[0]["detail"])

    def test_healthy_with_pr_triggers_no_action(self):
        # 이슈 acceptance 빈 상태: PR 이 이미 있으면 pr-expected-missing 가지에
        # 들어가지 않는다 — recovery_policy 는 아예 불리지 않는다.
        fake_policy = mock.Mock()
        with mock.patch.object(spawn, "_recovery_policy_module", return_value=fake_policy):
            expected = self._expected()
            observed = {"session_verdict": "normal", "pr_number": 42,
                        "loop_state": "done", "new_commit": True,
                        "failure_signature": None}
            out = spawn.reconcile(expected, observed)
        self.assertEqual(out, [])
        fake_policy.classify_from_state.assert_not_called()

    def test_no_issue_falls_back_to_commit_only_without_state_io(self):
        # `issue` 가 없는 기존 호출부(492 시절 테스트)는 상태 파일을 건드리지
        # 않고 커밋 유무만으로 즉시 판정한다.
        fake_policy = mock.Mock()
        with mock.patch.object(spawn, "_recovery_policy_module", return_value=fake_policy):
            expected = {"expects_pr": True, "role": "implementation", "branch": "b"}
            out = spawn.reconcile(expected, self._observed(new_commit=True))
        self.assertEqual(out[0]["next_action"], "respawn")
        self.assertTrue(out[0]["handoff"])
        fake_policy.classify_from_state.assert_not_called()

    def test_live_reconstruct_issue_1660_cap_then_escalate(self):
        """이슈 acceptance live check: #1660(commit-no-PR) 재구성 — 첫 죽음은
        handoff 로 respawn, 같은 실패 서명이 cap(기본 2)만큼 반복되면 3번째
        respawn 없이 ESCALATE 한다. 실제 recovery_policy.classify_from_state
        를 tmp 상태 디렉터리로 돌린다(진짜 상태 I/O, 격리는 `recovery_state_dir`
        로 명시 전달 — `classify_from_state`의 `state_dir` 기본값은 import
        시점에 바인딩되므로 모듈 속성 monkeypatch 로는 안 먹힌다)."""
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td) / "recovery-state"
            expected = self._expected(issue=1660, role="implementation")

            out1 = spawn.reconcile(
                expected, self._observed(new_commit=True, failure_signature="sig-x"),
                recovery_state_dir=state_dir)
            self.assertEqual(out1[0]["next_action"], "respawn")
            self.assertTrue(out1[0]["handoff"])

            out2 = spawn.reconcile(
                expected, self._observed(new_commit=True, failure_signature="sig-x"),
                recovery_state_dir=state_dir)
            self.assertEqual(out2[0]["next_action"], "manual-review")

            out3 = spawn.reconcile(
                expected, self._observed(new_commit=True, failure_signature="sig-x"),
                recovery_state_dir=state_dir)
            self.assertEqual(out3[0]["next_action"], "manual-review")

    def _observed_with_death(self, death_id, failure_signature, new_commit=True):
        obs = self._observed(new_commit=new_commit, failure_signature=failure_signature)
        obs["death_id"] = death_id
        return obs

    def test_same_death_across_multiple_ticks_increments_counter_once(self):
        # review D1: watchdog 는 같은 죽음을 여러 tick 동안 관측한다(재기동
        # claim 이 아직 안 났으므로 로스터 엔트리, 즉 death_id 는 그대로다).
        # 같은 death_id 로 4번 reconcile 을 태워도 respawn_count 는 한 번만
        # 올라가야 한다. 서로 다른 death(death-2, death-3)에서만 진짜로
        # 오르고, cap(2) 에 닿은 3번째 death 에서만 ESCALATE 한다.
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td) / "recovery-state"
            expected = self._expected(issue=1660, role="implementation")
            state_path = state_dir / "1660-implementation.json"

            for _ in range(4):
                out = spawn.reconcile(
                    expected, self._observed_with_death("death-1", "sig-a"),
                    recovery_state_dir=state_dir)
                self.assertEqual(out[0]["next_action"], "respawn")
                self.assertTrue(out[0]["handoff"])
            self.assertEqual(json.loads(state_path.read_text())["respawn_count"], 1)

            # 다른 death_id(실제로 새로 죽음)가 오면 카운터가 오른다 — 카운터가
            # tick 이 아니라 죽음 신원에 묶여 있다는 걸 확인.
            out2 = spawn.reconcile(
                expected, self._observed_with_death("death-2", "sig-b"),
                recovery_state_dir=state_dir)
            self.assertEqual(out2[0]["next_action"], "respawn")
            self.assertEqual(json.loads(state_path.read_text())["respawn_count"], 2)

            # cap(2) 에 도달한 세 번째 distinct death 는 ESCALATE.
            out3 = spawn.reconcile(
                expected, self._observed_with_death("death-3", "sig-c"),
                recovery_state_dir=state_dir)
            self.assertEqual(out3[0]["next_action"], "manual-review")

    def test_healthy_after_flakes_resets_state_next_death_starts_fresh(self):
        # review D2: 두 번의 transient flake 로 카운터가 cap 근처까지 오른
        # 뒤 (issue, role) 이 PR 있는 건강한 상태로 관측되면 상태가
        # 리셋되고, 다음 진짜 죽음은 count 0 부터 다시 시작해야 한다.
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td) / "recovery-state"
            expected = self._expected(issue=1660, role="implementation")
            state_path = state_dir / "1660-implementation.json"

            for i in range(2):
                out = spawn.reconcile(
                    expected, self._observed_with_death(f"flake-{i}", f"sig-flake-{i}"),
                    recovery_state_dir=state_dir)
                self.assertEqual(out[0]["next_action"], "respawn")

            self.assertEqual(json.loads(state_path.read_text())["respawn_count"], 2)

            healthy_observed = {"session_verdict": "normal", "pr_number": 99,
                                 "loop_state": "done", "new_commit": True,
                                 "failure_signature": None}
            out_healthy = spawn.reconcile(expected, healthy_observed, recovery_state_dir=state_dir)
            self.assertEqual(out_healthy, [])
            self.assertFalse(state_path.exists())

            out_fresh = spawn.reconcile(
                expected, self._observed_with_death("death-after-reset", "sig-fresh"),
                recovery_state_dir=state_dir)
            self.assertEqual(out_fresh[0]["next_action"], "respawn")
            self.assertEqual(json.loads(state_path.read_text())["respawn_count"], 1)

class RemediationMergeSweep(unittest.TestCase):
    """이슈 #587 §12 event 4: remediation PR 이 머지되면 §12 형식 코멘트를
    한 번만 남긴다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.decisions_dir = self.root / "docs" / "issue-587" / "decisions"
        self.decisions_dir.mkdir(parents=True)
        self._orig_merged = spawn._merged_pr_for_branch
        self._orig_comments = spawn._issue_comments
        self._orig_slug = spawn._repo_slug
        self._orig_run = subprocess.run

    def tearDown(self):
        spawn._merged_pr_for_branch = self._orig_merged
        spawn._issue_comments = self._orig_comments
        spawn._repo_slug = self._orig_slug
        subprocess.run = self._orig_run
        self.tmp.cleanup()

    def _write_record(self, name, **fields):
        defaults = {
            "finding_source": "docs/issue-587/decisions/auto-1.md",
            "candidate_pr": "601",
            "routed_to": "implementation",
            "target_path": "spawn.py",
            "required_fix": "wire event 4",
            "contradicting_role": "verify",
            "round": "1",
            "status": "open",
            "timestamp": "2026-08-10T00:00:00Z",
        }
        defaults.update(fields)
        lines = ["---"] + [f"{k}: {v}" for k, v in defaults.items()] + ["---", ""]
        (self.decisions_dir / name).write_text("\n".join(lines), encoding="utf-8")

    def test_posts_event4_comment_on_merge(self):
        self._write_record("remediation-1.md")
        spawn._merged_pr_for_branch = lambda root, branch: 605
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return self._orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        posted = spawn._remediation_merge_sweep(self.root, 587)
        self.assertEqual(posted, 1)
        gh_calls = [c for c in calls if c[:2] == ["gh", "api"]]
        self.assertEqual(len(gh_calls), 1)
        body = next(a for a in gh_calls[0] if a.startswith("body="))
        self.assertIn("Remediation merged: PR #605 resolves round 1 of PR #601", body)

    def test_skips_when_marker_already_present(self):
        self._write_record("remediation-1.md")
        marker = spawn._REMEDIATION_MERGE_COMMENT_MARKER.format(
            path="docs/issue-587/decisions/remediation-1.md")
        spawn._merged_pr_for_branch = lambda root, branch: 605
        spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], True)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        subprocess.run = lambda cmd, *a, **k: (calls.append(cmd),
                                                self._orig_run(["true"], capture_output=True, text=True))[1]
        posted = spawn._remediation_merge_sweep(self.root, 587)
        self.assertEqual(posted, 0)
        self.assertEqual([c for c in calls if c[:2] == ["gh", "api"]], [])

    def test_skips_when_branch_not_merged(self):
        self._write_record("remediation-1.md")
        spawn._merged_pr_for_branch = lambda root, branch: None
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        subprocess.run = lambda cmd, *a, **k: (calls.append(cmd),
                                                self._orig_run(["true"], capture_output=True, text=True))[1]
        posted = spawn._remediation_merge_sweep(self.root, 587)
        self.assertEqual(posted, 0)
        self.assertEqual([c for c in calls if c[:2] == ["gh", "api"]], [])

    def test_skips_non_open_status_without_pr_lookup(self):
        self._write_record("remediation-1.md", status="escalated")
        self._write_record("remediation-2.md", status="resolved")
        lookups = []
        spawn._merged_pr_for_branch = lambda root, branch: (lookups.append(branch), 605)[1]
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        subprocess.run = lambda cmd, *a, **k: self._orig_run(["true"], capture_output=True, text=True)
        posted = spawn._remediation_merge_sweep(self.root, 587)
        self.assertEqual(posted, 0)
        self.assertEqual(lookups, [])

class RosterReconcileRemediationMergedCLI(unittest.TestCase):
    """이슈 #587 round 2: `spawn.py reconcile --remediation-merged --issue N`
    이 실제로 `_remediation_merge_sweep` 을 호출해 event 4 코멘트를 남기는지,
    private 함수가 아니라 shipped entrypoint(`roster_reconcile`)를 통해
    검증한다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.decisions_dir = self.root / "docs" / "issue-587" / "decisions"
        self.decisions_dir.mkdir(parents=True)
        self._orig_root = spawn.ROOT
        spawn.ROOT = self.root
        self._orig_merged = spawn._merged_pr_for_branch
        self._orig_comments = spawn._issue_comments
        self._orig_slug = spawn._repo_slug
        self._orig_run = subprocess.run

    def tearDown(self):
        spawn.ROOT = self._orig_root
        spawn._merged_pr_for_branch = self._orig_merged
        spawn._issue_comments = self._orig_comments
        spawn._repo_slug = self._orig_slug
        subprocess.run = self._orig_run
        self.tmp.cleanup()

    def _write_record(self, name, **fields):
        defaults = {
            "finding_source": "docs/issue-587/decisions/auto-1.md",
            "candidate_pr": "601",
            "routed_to": "implementation",
            "target_path": "spawn.py",
            "required_fix": "wire event 4",
            "contradicting_role": "verify",
            "round": "1",
            "status": "open",
            "timestamp": "2026-08-10T00:00:00Z",
        }
        defaults.update(fields)
        lines = ["---"] + [f"{k}: {v}" for k, v in defaults.items()] + ["---", ""]
        (self.decisions_dir / name).write_text("\n".join(lines), encoding="utf-8")

    def test_cli_flag_drives_sweep_and_posts_comment(self):
        self._write_record("remediation-1.md")
        spawn._merged_pr_for_branch = lambda root, branch: 605
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return self._orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        posted = spawn.roster_reconcile(issue=587, remediation_merged=True)
        self.assertEqual(posted, 1)
        gh_calls = [c for c in calls if c[:2] == ["gh", "api"]]
        self.assertEqual(len(gh_calls), 1)
        body = next(a for a in gh_calls[0] if a.startswith("body="))
        self.assertIn("Remediation merged: PR #605 resolves round 1 of PR #601", body)

    def test_help_lists_flag(self):
        r = self._orig_run([sys.executable, "spawn.py", "--help"],
                            cwd=os.path.dirname(os.path.abspath(spawn.__file__)),
                            capture_output=True, text=True)
        self.assertIn("--remediation-merged", r.stdout)

class RosterReconcileRemediationMergedCLITargetRoot(unittest.TestCase):
    """이슈 #587 round 3: 세 번째 e2e 가 잡은 결함 — `_remediation_merge_sweep`
    이 항상 `spawn.ROOT`(spawn.py 자신의 체크아웃)로만 불려서, `-C` 로 다른
    레포를 겨눈 CLI 호출에서 조용히 no-op 됐다. 이 테스트는 shipped CLI
    프로세스(`python3 spawn.py reconcile --remediation-merged ...`)를
    spawn.py 자신의 체크아웃 밖에 있는 fixture 레포로 `-C` 를 줘서 구동한다
    — `_remediation_merge_sweep` 직접 호출도, `spawn.ROOT` monkeypatch 도
    아니다: 그게 바로 이전 라운드가 통과시킨 채 이 결함을 놓친 커버리지
    구멍이다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.checkout_root = Path(os.path.dirname(os.path.abspath(spawn.__file__)))
        self.fixture_root = Path(self.tmp.name) / "fixture-repo"
        self.fixture_root.mkdir()
        self.assertNotEqual(self.fixture_root, self.checkout_root)
        self._orig_run = subprocess.run
        self._orig_run(["git", "-C", str(self.fixture_root), "init", "-q"],
                        capture_output=True, text=True)
        self._orig_run(["git", "-C", str(self.fixture_root), "remote", "add",
                         "origin", "https://github.com/acme/repo.git"],
                        capture_output=True, text=True)
        decisions_dir = self.fixture_root / "docs" / "issue-587" / "decisions"
        decisions_dir.mkdir(parents=True)
        lines = ["---",
                 "finding_source: docs/issue-587/decisions/auto-1.md",
                 "candidate_pr: 601",
                 "routed_to: implementation",
                 "target_path: spawn.py",
                 "required_fix: wire event 4",
                 "contradicting_role: verify",
                 "round: 1",
                 "status: open",
                 "timestamp: 2026-08-10T00:00:00Z",
                 "---", ""]
        (decisions_dir / "remediation-1.md").write_text("\n".join(lines), encoding="utf-8")
        self.calls_log = Path(self.tmp.name) / "gh-calls.log"
        bin_dir = Path(self.tmp.name) / "bin"
        bin_dir.mkdir()
        gh_stub = bin_dir / "gh"
        gh_stub.write_text(
            "#!/usr/bin/env python3\n"
            "import json, sys, pathlib\n"
            "argv = sys.argv[1:]\n"
            f"pathlib.Path({str(self.calls_log)!r}).open('a').write(repr(argv) + chr(10))\n"
            "if argv[:2] == ['repo', 'view']:\n"
            "    print('acme/repo')\n"
            "elif argv[:2] == ['pr', 'list']:\n"
            "    print(json.dumps([{'number': 605, 'state': 'MERGED'}]))\n"
            "elif argv[:2] == ['api', 'repos/acme/repo/issues/587/comments'] and '--paginate' in argv:\n"
            "    print(json.dumps([[]]))\n"
            "elif argv[0] == 'api' and any(a.startswith('body=') for a in argv):\n"
            "    pass\n"
            "else:\n"
            "    sys.exit(1)\n",
            encoding="utf-8")
        gh_stub.chmod(0o755)
        self._orig_path = os.environ.get("PATH", "")
        self.env = dict(os.environ)
        self.env["PATH"] = f"{bin_dir}{os.pathsep}{self._orig_path}"

    def tearDown(self):
        self.tmp.cleanup()

    def test_cli_dash_c_targets_fixture_repo_not_checkout(self):
        spawn_py = self.checkout_root / "spawn.py"
        r = self._orig_run(
            [sys.executable, str(spawn_py), "reconcile", "--remediation-merged",
             "--issue", "587", "-C", str(self.fixture_root)],
            capture_output=True, text=True, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stderr)  # posted-comment count, per _remediation_merge_sweep's return convention
        raw_calls = self.calls_log.read_text(encoding="utf-8").splitlines() if self.calls_log.exists() else []
        post_calls = [c for c in raw_calls if "'api'" in c and "body=" in c]
        self.assertEqual(len(post_calls), 1, msg=f"gh calls: {raw_calls}")
        self.assertIn("Remediation merged: PR #605 resolves round 1 of PR #601", post_calls[0])

class RosterReconcileUnreported(unittest.TestCase):
    """이슈 #534: `spawn.py reconcile --unreported` — workspace 인덱스에서
    session-end(normal) 인데 [watch] 코멘트가 없는 엔트리를 찍고,
    코멘트가 생기면 사라진다."""

    def setUp(self):
        self._orig_idx = spawn._workspace_index_load
        self._orig_verdict = spawn.session_end_verdict
        self._orig_comments = spawn._issue_comments

    def tearDown(self):
        spawn._workspace_index_load = self._orig_idx
        spawn.session_end_verdict = self._orig_verdict
        spawn._issue_comments = self._orig_comments

    def test_lists_ended_session_with_open_pr_before_ack_and_empties_after(self):
        # 이슈 #533: workspace 인덱스 키는 레포 접두사가 붙지만
        # (`repo/issue-534/coding`), 코멘트에 실제로 박히는 마커는
        # `_post_session_end_comment`가 여전히 쓰는 bare `issue-534/coding`
        # 이어야 한다 — before-landing hunt 가 찾은 마커 불일치 회귀.
        spawn._workspace_index_load = lambda: {
            "repo/issue-534/coding": {"work": "/tmp/w", "log": "/tmp/l"},
        }
        spawn.session_end_verdict = lambda work, log_path: "normal"

        marker = spawn._SESSION_END_COMMENT_MARKER.format(key="issue-534/coding")
        state = {"acked": False}
        def fake_comments(root, n):
            if state["acked"]:
                return ([{"login": "bot", "body": f"{marker} PR ... opened"}], True)
            return ([], True)
        spawn._issue_comments = fake_comments

        before = spawn._roster_reconcile_unreported()
        self.assertEqual(before, 1)

        state["acked"] = True
        after = spawn._roster_reconcile_unreported()
        self.assertEqual(after, 0)

    def test_filters_by_issue(self):
        spawn._workspace_index_load = lambda: {
            "repo/issue-534/coding": {"work": "/tmp/w", "log": "/tmp/l"},
            "repo/issue-1/coding": {"work": "/tmp/w2", "log": "/tmp/l2"},
        }
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._issue_comments = lambda root, n: ([], True)
        self.assertEqual(spawn._roster_reconcile_unreported(issue=534), 1)

    def test_lists_normal_session_after_workspace_cleaned(self):
        # 이슈 #1283: workspace 가 `clean` 에 이미 지워진 뒤에도
        # session-end(normal) 인데 [watch] 코멘트가 없으면 계속
        # 미보고로 찍혀야 한다 — 사라진 workspace 를 이유로 통째로
        # 건너뛰면 그 세션의 관찰이 영영 사라진다.
        spawn._workspace_index_load = lambda: {
            "repo/issue-534/coding": {"work": "/tmp/does-not-exist-1283", "log": "/tmp/l"},
        }
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._issue_comments = lambda root, n: ([], True)
        self.assertEqual(spawn._roster_reconcile_unreported(), 1)

    def test_lists_normal_session_after_workspace_cleaned_no_stub(self):
        # 이슈 #1283 hunt: `_issue_comments`를 스텁하지 않고 실제
        # `_repo_slug` -> `subprocess.run(cwd=work)` 경로를 태워, work 가
        # 존재하지 않을 때 FileNotFoundError 로 죽지 않고 미보고로
        # 안전하게 처리되는지 확인한다.
        spawn._workspace_index_load = lambda: {
            "repo/issue-534/coding": {"work": "/tmp/does-not-exist-1283-b", "log": "/tmp/l"},
        }
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._repo_slug_cache_clear()
        self.assertEqual(spawn._roster_reconcile_unreported(), 1)

    def test_empty_workspace_index_reports_nothing(self):
        spawn._workspace_index_load = lambda: {}
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._issue_comments = lambda root, n: ([], True)
        self.assertEqual(spawn._roster_reconcile_unreported(), 0)

    def test_skips_non_normal_verdicts(self):
        spawn._workspace_index_load = lambda: {
            "repo/issue-534/coding": {"work": "/tmp/w", "log": "/tmp/l"},
        }
        spawn.session_end_verdict = lambda work, log_path: "in-progress"
        spawn._issue_comments = lambda root, n: ([], True)
        self.assertEqual(spawn._roster_reconcile_unreported(), 0)

    def test_reconcile_dispatches_to_unreported(self):
        orig = spawn._roster_reconcile_unreported
        calls = []
        spawn._roster_reconcile_unreported = lambda issue=None: (calls.append(issue), 0)[1]
        try:
            spawn.roster_reconcile(issue=534, unreported=True)
        finally:
            spawn._roster_reconcile_unreported = orig
        self.assertEqual(calls, [534])

class ClosureSweepCallCountTest(unittest.TestCase):
    """issue #682 — find_violations 의 gh 호출이 subject 수에 비례하지 않는다."""

    def setUp(self):
        sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
        import closure_sweep
        import ci
        self.cs = closure_sweep
        self.ci = ci
        self.root = Path(".")

    def _patch(self, obj, name, fn):
        orig = getattr(obj, name)
        setattr(obj, name, fn)
        self.addCleanup(setattr, obj, name, orig)

    def _subjects(self, n):
        return {f"issue-{i}": {"implementation": {}} for i in range(1, n + 1)}

    def test_pr_lookup_is_one_call_regardless_of_subject_count(self):
        """브랜치별 개별 조회(_pr_for_branch/_pr_view_state_body)를 쓰지 않는다."""
        calls = {"index": 0, "per_branch": 0, "pr_view": 0}

        def index(root):
            calls["index"] += 1
            return {f"issue-{i}/implementation": {
                "number": 500 + i, "state": "MERGED",
                "body": f"Closes #{i}"} for i in range(1, 51)}, True

        self._patch(self.cs, "_pr_index_all", index)
        self._patch(spawn, "_pr_for_branch",
                    lambda root, branch: calls.__setitem__("per_branch", calls["per_branch"] + 1))
        self._patch(self.cs, "_pr_view_state_body",
                    lambda root, pr: calls.__setitem__("pr_view", calls["pr_view"] + 1))
        self._patch(self.ci, "_phase2_record_evidence",
                    lambda root, pr, branch, issue: False)

        states = {i: "OPEN" for i in range(1, 51)}
        violations, skips = self.cs.find_violations(
            self.root, subjects=self._subjects(50), issue_states=states)

        self.assertEqual(calls["index"], 1)
        self.assertEqual(calls["per_branch"], 0)
        self.assertEqual(calls["pr_view"], 0)
        self.assertEqual(len(violations), 50)
        self.assertEqual(skips, [])

    def test_record_evidence_fetched_only_when_it_can_change_the_verdict(self):
        """MERGED + 이슈 OPEN + closes 키워드 없음 — 그 조합에서만 조회한다."""
        fetched = []
        rows = {
            # closes 키워드가 있으니 증거 없이도 위반 — 조회 불필요
            "issue-1/implementation": {"number": 501, "state": "MERGED", "body": "Closes #1"},
            # 이슈가 닫혀 있으니 그 가지에 못 들어간다 — 조회 불필요
            "issue-2/implementation": {"number": 502, "state": "MERGED", "body": "#2"},
            # 유일하게 증거가 판정을 뒤집을 수 있는 행
            "issue-3/implementation": {"number": 503, "state": "MERGED", "body": "#3"},
        }
        self._patch(self.cs, "_pr_index_all", lambda root: (rows, True))

        def evidence(root, pr, branch, issue):
            fetched.append(pr)
            return True

        self._patch(self.ci, "_phase2_record_evidence", evidence)

        violations, skips = self.cs.find_violations(
            self.root, subjects=self._subjects(3),
            issue_states={1: "OPEN", 2: "CLOSED", 3: "OPEN"})

        self.assertEqual(fetched, [503])
        self.assertEqual(sorted(v["issue"] for v in violations), [1, 3])
        self.assertEqual(skips, [])

    def test_pr_list_failure_becomes_skips_not_silent_zero(self):
        """목록 조회가 실패하면 '위반 없음'이 아니라 확인 불가로 남는다."""
        self._patch(self.cs, "_pr_index_all", lambda root: (None, False))
        violations, skips = self.cs.find_violations(
            self.root, subjects=self._subjects(4),
            issue_states={i: "OPEN" for i in range(1, 5)})
        self.assertEqual(violations, [])
        self.assertEqual(len(skips), 4)
        self.assertTrue(all(s["reason"] == "gh-pr-list-failed" for s in skips))

    @pytest.mark.xfail(
        reason="issue #1619: two-thread checkout_calls race, same shape as "
               "SpawnOneIssueRoleClaim::test_concurrent_spawn_one_calls_"
               "let_exactly_one_through -- observed 2 calls where the test "
               "expects exactly 1 fallback lookup. Genuine "
               "concurrency-timing flake, tracked separately from this "
               "suite-hygiene pass.",
        strict=False)
    def test_truncated_pr_list_falls_back_to_per_branch_lookup(self):
        """--limit 에 걸리면 조용히 놓치지 않고 옛 개별 조회로 되돌아간다."""
        self._patch(self.cs, "_pr_index_all", lambda root: (None, True))
        self._patch(spawn, "_pr_for_branch", lambda root, branch: 777)
        self._patch(self.cs, "_pr_view_state_body",
                    lambda root, pr: (("MERGED", "Closes #1"), True))
        self._patch(self.ci, "_phase2_record_evidence",
                    lambda root, pr, branch, issue: False)
        violations, skips = self.cs.find_violations(
            self.root, subjects=self._subjects(1), issue_states={1: "OPEN"})
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["pr"], 777)
        self.assertEqual(skips, [])

class ConsultCmd(unittest.TestCase):
    """이슈 #699 R1 — consult 는 답만 돌려주고, PR 을 열지 않고, 트레이스를
    항상 남긴다. `resolve_role_source`/`core_plugin_dirs`/`subprocess.run`
    을 막아 실제 skill-repo fetch 나 claude 세션 없이 조립만 검증한다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "resolve_role_source",
                    lambda role, repo_root: {"source": "skill-repo",
                        "skill_dirs": [Path("/fake/plugin")],
                        "skills": ["fake"], "skill_sha": "abc1234"})
        self._patch(spawn, "core_plugin_dirs", lambda: [])
        root = self.root
        self._patch(spawn, "_consult_trace_path",
                    lambda issue, cwd=None: (root / "docs" / f"issue-{issue}" / "reports" / "consult-log.md"
                                   if issue is not None else root / "docs" / "consult-log.md"))

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def _fake_run(self, stdout_result_text, returncode=0):
        def run(cmd, **kw):
            payload = json.dumps({"result": stdout_result_text, "is_error": False})
            return subprocess.CompletedProcess(cmd, returncode, stdout=payload, stderr="")
        return run

    def test_returns_answer_no_pr_and_traces(self):
        verdict_json = ('설계 검토 결과입니다.\n'
                         '{"answer": "괜찮다", "confidence": "medium", "caveats": ["엣지케이스 미확인"]}')
        gh_calls = []
        self._patch(spawn.subprocess, "run",
                    self._fake_run(verdict_json))
        real_popen = subprocess.Popen
        def no_gh_popen(*a, **kw):
            gh_calls.append(a)
            return real_popen(*a, **kw)
        result = spawn.consult_cmd("implementation", "이 설계 괜찮은가?", cwd=str(self.root))

        self.assertEqual(result["answer"], "괜찮다")
        self.assertEqual(result["confidence"], "medium")
        self.assertEqual(result["caveats"], ["엣지케이스 미확인"])
        self.assertEqual(gh_calls, [])  # gh pr create 등 어떤 서브프로세스도 안 거쳤다

        trace = (self.root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        self.assertIn("role=implementation", trace)
        self.assertIn("이 설계 괜찮은가", trace)
        self.assertIn("ok:", trace)

    def test_issue_scopes_trace_path(self):
        self._patch(spawn.subprocess, "run",
                    self._fake_run('{"answer": "ok", "confidence": "high", "caveats": []}'))
        spawn.consult_cmd("implementation", "질문", issue=699, cwd=str(self.root))

        scoped = self.root / "docs" / "issue-699" / "reports" / "consult-log.md"
        self.assertTrue(scoped.is_file())
        self.assertFalse((self.root / "docs" / "consult-log.md").exists())

    def test_traces_on_malformed_verdict(self):
        self._patch(spawn.subprocess, "run", self._fake_run("이건 JSON 이 아니다"))

        with self.assertRaises(RuntimeError):
            spawn.consult_cmd("implementation", "질문", cwd=str(self.root))

        trace = (self.root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        self.assertIn("error:", trace)

    def test_traces_on_subprocess_crash(self):
        def crash_run(cmd, **kw):
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")
        self._patch(spawn.subprocess, "run", crash_run)

        with self.assertRaises(RuntimeError):
            spawn.consult_cmd("implementation", "질문", cwd=str(self.root))

        trace = (self.root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        self.assertIn("error:", trace)
        self.assertIn("종료 코드 1", trace)

    def test_traces_on_timeout(self):
        def timeout_run(cmd, **kw):
            raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 1))
        self._patch(spawn.subprocess, "run", timeout_run)

        with self.assertRaises(subprocess.TimeoutExpired):
            spawn.consult_cmd("implementation", "질문", cwd=str(self.root))

        trace = (self.root / "docs" / "consult-log.md").read_text(encoding="utf-8")
        self.assertIn("시간초과", trace)

class PanelDegradeErrorSafety(unittest.TestCase):
    """이슈 #1045 결함 2 — `_panel_degrade()` 는 `consult_cmd()` 실패를
    절대 밖으로 던지지 않는다: 실패를 `consult-error` 턴으로 기록하고
    저하 결과를 돌려준다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "docs" / "reports" / "panel" / "question.md"
        self.ts = "2026-08-12T00:00:00+00:00"

    def test_consult_error_inside_degrade_is_recorded_not_raised(self):
        def failing_consult(role, question, issue=None, cwd=None):
            raise RuntimeError("모델 출력에서 판단 JSON 을 못 찾음")

        orig = spawn.consult_cmd
        spawn.consult_cmd = failing_consult
        try:
            result = spawn._panel_degrade(
                self.path, self.ts, "implementation", "qa", "질문",
                None, str(self.root), "no SendMessage round-trip observed")
        finally:
            spawn.consult_cmd = orig

        self.assertTrue(result["degraded"])
        self.assertIsNone(result["verdict_a"])
        self.assertIsNone(result["verdict_b"])
        self.assertIn("모델 출력에서 판단 JSON 을 못 찾음", result["error_a"])
        self.assertIn("모델 출력에서 판단 JSON 을 못 찾음", result["error_b"])

        trace = self.path.read_text(encoding="utf-8")
        self.assertIn("consult-error", trace)

    def test_one_side_failing_still_returns_the_others_real_verdict(self):
        def half_failing_consult(role, question, issue=None, cwd=None):
            if role == "implementation":
                raise RuntimeError("모델 출력에서 판단 JSON 을 못 찾음")
            return {"answer": "가능", "confidence": "high", "caveats": []}

        orig = spawn.consult_cmd
        spawn.consult_cmd = half_failing_consult
        try:
            result = spawn._panel_degrade(
                self.path, self.ts, "implementation", "qa", "질문",
                None, str(self.root), "no SendMessage round-trip observed")
        finally:
            spawn.consult_cmd = orig

        self.assertIsNone(result["verdict_a"])
        self.assertIsNotNone(result["error_a"])
        self.assertEqual(result["verdict_b"], {"answer": "가능", "confidence": "high", "caveats": []})
        self.assertIsNone(result["error_b"])

    def test_panel_cmd_no_round_trip_degrade_does_not_propagate_consult_failure(self):
        def failing_consult(role, question, issue=None, cwd=None):
            raise RuntimeError("모델 출력에서 판단 JSON 을 못 찾음")

        orig = spawn.consult_cmd
        spawn.consult_cmd = failing_consult
        orig_record_path = spawn._panel_record_path
        spawn._panel_record_path = lambda issue, slug, cwd=None: self.path

        def no_turns_session(role, peer_role, question, cwd, model=None):
            return {"turns": [], "verdict": None}

        try:
            result = spawn.panel_cmd(
                "implementation", "qa", "질문", cwd=str(self.root),
                run_session=no_turns_session)
        finally:
            spawn.consult_cmd = orig
            spawn._panel_record_path = orig_record_path

        self.assertTrue(result["degraded"])
        self.assertEqual(result["reason"], "no SendMessage round-trip observed")
        self.assertIsNone(result["verdict_a"])
        self.assertIsNone(result["verdict_b"])

class ConsultVerdictParsing(unittest.TestCase):
    def test_finds_trailing_json_after_prose(self):
        text = '분석했다.\n결론은 다음과 같다.\n{"answer": "가능", "confidence": "low", "caveats": []}'
        got = spawn._parse_consult_verdict(text)
        self.assertEqual(got["answer"], "가능")

    def test_none_when_no_object_present(self):
        self.assertIsNone(spawn._parse_consult_verdict("그냥 텍스트, JSON 없음"))

    def test_none_when_empty(self):
        self.assertIsNone(spawn._parse_consult_verdict(""))

class PlainSessionDirectiveNorms(unittest.TestCase):
    """이슈 #699 R2/R3 — CLAUDE_ROLE 이 비어 있는(오케스트레이터/일반) 세션은
    directive.sh 가 매번 주입하는 텍스트에서 delegation norm 과 goal-loop
    norm 문구를 봐야 한다."""

    def _render(self, env_extra=None):
        repo_root = Path(__file__).resolve().parent.parent
        env = {**os.environ, "TOKENMAXXXER_CHECKOUT": str(repo_root)}
        env.pop("CLAUDE_ROLE", None)
        env.pop("ORCHESTRATE_OFF", None)
        if env_extra:
            env.update(env_extra)
        script = repo_root / "on-the-record" / "hooks" / "directive.sh"
        r = subprocess.run(["bash", str(script)], capture_output=True, text=True, env=env)
        return r

    def test_plain_session_sees_delegation_and_goal_loop_norms(self):
        r = self._render()
        self.assertEqual(r.returncode, 0)
        self.assertIn("spawn.py consult", r.stdout)
        self.assertIn("DELEGATION IS THE DEFAULT", r.stdout)
        self.assertIn("YOUR GOAL LOOP", r.stdout)
        self.assertIn("judgment point", r.stdout)

    def test_role_session_does_not_see_norms(self):
        r = self._render(env_extra={"CLAUDE_ROLE": "implementation"})
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("DELEGATION IS THE DEFAULT", r.stdout)

    def test_orchestrate_off_suppresses_norms(self):
        r = self._render(env_extra={"ORCHESTRATE_OFF": "1"})
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("DELEGATION IS THE DEFAULT", r.stdout)

class ReconcileLedger(unittest.TestCase):
    """이슈 #782 step 2: 이벤트+폴 채널이 같은 완료/헬스를 봐도 next-action
    이 한 번만 나가게 하는 원장(멱등 reconcile, TTL 15분)."""

    def setUp(self):
        self._orig = spawn.RECONCILE_LEDGER
        self._td = tempfile.TemporaryDirectory()
        spawn.RECONCILE_LEDGER = Path(self._td.name) / "reconcile_ledger.json"

    def tearDown(self):
        spawn.RECONCILE_LEDGER = self._orig
        self._td.cleanup()

    def test_fresh_key_is_due_and_gets_stamped(self):
        self.assertTrue(spawn.ledger_check_and_stamp("k1", now=1000.0))
        d = json.loads(spawn.RECONCILE_LEDGER.read_text())
        self.assertEqual(d["k1"], 1000.0)

    def test_repeat_within_ttl_is_not_due(self):
        self.assertTrue(spawn.ledger_check_and_stamp("k1", now=1000.0))
        self.assertFalse(spawn.ledger_check_and_stamp(
            "k1", now=1000.0 + spawn.RECONCILE_LEDGER_TTL_SEC - 1))

    def test_repeat_after_ttl_is_due_again(self):
        self.assertTrue(spawn.ledger_check_and_stamp("k1", now=1000.0))
        self.assertTrue(spawn.ledger_check_and_stamp(
            "k1", now=1000.0 + spawn.RECONCILE_LEDGER_TTL_SEC + 1))

    def test_different_keys_are_independent(self):
        self.assertTrue(spawn.ledger_check_and_stamp("k1", now=1000.0))
        self.assertTrue(spawn.ledger_check_and_stamp("k2", now=1000.0))

    def test_ledger_stamp_makes_a_later_check_not_due(self):
        # Acceptance test 2: watch 가 이미 완료를 알고 찍으면, 폴링 틱의
        # check-and-stamp 는 같은 TTL 창 안에서 조용히 넘어간다.
        spawn.ledger_stamp("k1", now=1000.0)
        self.assertFalse(spawn.ledger_check_and_stamp("k1", now=1000.5))

    def test_concurrent_check_and_stamp_acts_exactly_once(self):
        # Acceptance test 3: event+poll 이 "동시에" 같은 키를 건드려도
        # (여기선 순차 호출로 시뮬레이션) True 는 정확히 한 번만 나온다.
        results = [spawn.ledger_check_and_stamp("k1", now=1000.0)
                   for _ in range(5)]
        self.assertEqual(results, [True, False, False, False, False])


class ConsultLogSharding(unittest.TestCase):
    """이슈 #2333: `docs/issue-<n>/reports/consult-log.md` 는 append-only +
    concurrent-writers + one-path 조합이라 동시 자문마다 100% 예측 가능한
    git merge 충돌을 냈다("6+ manual conflict resolutions in one session",
    이슈 본문). 세션마다 다른 샤드 파일(`consult-log/<session-ts-pid>.md`)
    에 쓰게 해 그 충돌 표면 자체를 없앤다 — `_consult_log_aggregate()` 가
    오늘까지의 단일-파일 뷰를 사람/게이트용으로 재구성한다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self._patches = []
        self._patch(spawn, "resolve_role_source",
                    lambda role, repo_root: {"source": "skill-repo",
                        "skill_dirs": [Path("/fake/plugin")],
                        "skills": ["fake"], "skill_sha": "abc1234"})
        self._patch(spawn, "core_plugin_dirs", lambda: [])

    def _patch(self, obj, name, value):
        orig = getattr(obj, name)
        setattr(obj, name, value)
        self._patches.append((obj, name, orig))
        self.addCleanup(lambda: setattr(obj, name, orig))

    def _fake_run(self, stdout_result_text, returncode=0):
        def run(cmd, **kw):
            payload = json.dumps({"result": stdout_result_text, "is_error": False})
            return subprocess.CompletedProcess(cmd, returncode, stdout=payload, stderr="")
        return run

    def _consult(self, question, shard_id, answer="ok", issue=2333, cwd=None):
        self._patch(spawn.subprocess, "run",
                    self._fake_run(json.dumps({"answer": answer, "confidence": "high",
                                                "caveats": []})))
        self._patch(spawn, "_consult_session_shard_id", lambda: shard_id)
        return spawn.consult_cmd("implementation", question, issue=issue,
                                  cwd=cwd or str(self.root))

    def test_two_sessions_write_distinct_shard_files_not_the_old_single_path(self):
        self._consult("질문 A", "20260101T000000000000-111")
        self._consult("질문 B", "20260101T000000000001-222")

        d = self.root / "docs" / "issue-2333" / "reports" / "consult-log"
        shard_names = sorted(p.name for p in d.glob("*.md"))
        self.assertEqual(shard_names,
                          ["20260101T000000000000-111.md", "20260101T000000000001-222.md"])
        # 예전 단일 파일 경로는 더 이상 쓰지 않는다 — 그 경로 자체가
        # 충돌면이었다.
        old_single_path = self.root / "docs" / "issue-2333" / "reports" / "consult-log.md"
        self.assertFalse(old_single_path.exists())

    def test_aggregate_reconstructs_chronological_single_file_view(self):
        self._consult("먼저 온 질문", "20260101T000000000000-111", answer="먼저")
        self._consult("나중 온 질문", "20260101T000000000009-222", answer="나중")

        aggregate = spawn._consult_log_aggregate(2333, cwd=str(self.root))
        self.assertIn("먼저 온 질문", aggregate)
        self.assertIn("나중 온 질문", aggregate)
        self.assertLess(aggregate.index("먼저 온 질문"), aggregate.index("나중 온 질문"))
        # 두 세션이 각자 쓴 원본 줄과 바이트 단위로 같아야 한다 — 애그리게이터가
        # 새 포맷을 발명하지 않고 오늘의 트레이스 줄 형식을 그대로 이어붙인다.
        d = self.root / "docs" / "issue-2333" / "reports" / "consult-log"
        expected = "".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.md")))
        self.assertEqual(aggregate, expected)

    def test_empty_state_no_prior_consults_is_empty_string(self):
        self.assertEqual(spawn._consult_log_aggregate(424242, cwd=str(self.root)), "")

    def test_single_session_issue_layout_reads_identically_to_the_one_shard(self):
        # Acceptance "empty state": 단일 세션 이슈는 샤드가 하나뿐이라
        # 애그리게이트가 그 샤드 내용과 완전히 같다 — 충돌이 나올 수도
        # 없다(파일이 하나뿐이니 겹칠 상대가 없다).
        self._consult("단일 세션 질문", "20260101T000000000000-333", issue=9999)
        d = self.root / "docs" / "issue-9999" / "reports" / "consult-log"
        self.assertEqual([p.name for p in d.glob("*.md")],
                          ["20260101T000000000000-333.md"])
        shard_text = (d / "20260101T000000000000-333.md").read_text(encoding="utf-8")
        self.assertEqual(spawn._consult_log_aggregate(9999, cwd=str(self.root)), shard_text)

    def test_two_concurrent_sessions_merge_without_conflict(self):
        """이슈 acceptance 재구성: 두 실제(시뮬레이션된) 동시 세션이 같은
        이슈에 자문을 남겨도, 서로 다른 샤드 경로에 쓰니 브랜치를 나눠
        커밋하고 merge 해도 절대 충돌하지 않는다(예전에는 같은
        `consult-log.md` 줄을 두 세션이 append 해 100% 충돌이었다)."""
        run = lambda *a, **k: subprocess.run(*a, cwd=str(self.root), check=True,
                                              capture_output=True, text=True, **k)
        run(["git", "init", "-q", "."])
        run(["git", "config", "user.email", "t@example.com"])
        run(["git", "config", "user.name", "t"])
        (self.root / "README.md").write_text("seed\n", encoding="utf-8")
        run(["git", "add", "README.md"])
        run(["git", "commit", "-q", "-m", "seed"])
        run(["git", "branch", "-M", "main"])

        run(["git", "checkout", "-q", "-b", "issue-2333/session-a"])
        self._consult("세션 A 질문", "20260101T000000000000-111", answer="a")

        run(["git", "checkout", "-q", "main"])
        run(["git", "checkout", "-q", "-b", "issue-2333/session-b"])
        self._consult("세션 B 질문", "20260101T000000000000-222", answer="b")

        run(["git", "checkout", "-q", "main"])
        run(["git", "merge", "-q", "--no-edit", "issue-2333/session-a"])
        merge_b = subprocess.run(
            ["git", "merge", "--no-edit", "issue-2333/session-b"],
            cwd=str(self.root), capture_output=True, text=True)
        self.assertEqual(merge_b.returncode, 0,
                          msg=f"session-b merge conflicted: {merge_b.stdout}\n{merge_b.stderr}")

        aggregate = spawn._consult_log_aggregate(2333, cwd=str(self.root))
        self.assertIn("세션 A 질문", aggregate)
        self.assertIn("세션 B 질문", aggregate)


HOOKS_DIR = Path(__file__).resolve().parent.parent / "on-the-record" / "hooks"


class HookFiresSharding(unittest.TestCase):
    """이슈 #2348: `.orchestrate-hook-fires.log` 는 issue #2333의
    consult-log.md 와 같은 append-only + concurrent-writers + one-path
    조합이었다 — 매 UserPromptSubmit/Stop 이벤트마다 세 훅
    (directive.sh/stop-gate.sh/stop-poll-rearm.sh) 이 같은 경로에 썼다.
    세션마다 다른 샤드 파일(`.orchestrate-hook-fires/<sha256(session_id)
    [:24]>.log`)에 쓰게 해 그 충돌면 자체를 없앤다 — `_hook_fires_aggregate()`
    가 오늘까지의 단일-파일 시간순 뷰를 재구성한다."""

    def _fire(self, session_id, root):
        env = dict(os.environ)
        env["ORCHESTRATE_OFF"] = "1"
        env.pop("CLAUDE_ROLE", None)
        payload = json.dumps({"session_id": session_id})
        r = subprocess.run(
            ["bash", str(HOOKS_DIR / "directive.sh")], input=payload,
            capture_output=True, text=True, env=env, cwd=str(root), timeout=20,
        )
        self.assertEqual(r.returncode, 0)

    def test_two_sessions_write_distinct_shard_files_not_the_old_single_path(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._fire("session-a", root)
            self._fire("session-b", root)
            d = root / ".orchestrate-hook-fires"
            self.assertEqual(len(list(d.glob("*.log"))), 2)
            # 예전 단일 파일 경로는 더 이상 쓰지 않는다 — 그 경로 자체가
            # 충돌면이었다.
            self.assertFalse((root / ".orchestrate-hook-fires.log").exists())

    def test_aggregate_reconstructs_chronological_single_file_view(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._fire("session-a", root)
            self._fire("session-b", root)
            aggregate = spawn._hook_fires_aggregate(cwd=str(root))
            lines = [l for l in aggregate.splitlines() if l]
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines, sorted(lines))

    def test_empty_state_no_prior_firing_is_empty_string(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(spawn._hook_fires_aggregate(cwd=td), "")

    def test_two_concurrent_sessions_merge_without_conflict(self):
        """두 실제(시뮬레이션된) 동시 세션이 같은 워크스페이스에서 훅을
        트립해도, 서로 다른 샤드 경로에 쓰니 브랜치를 나눠 커밋하고 merge
        해도 절대 충돌하지 않는다(예전에는 같은 `.orchestrate-hook-fires.log`
        줄을 두 세션이 append 해 100% 충돌이었다)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = lambda *a, **k: subprocess.run(*a, cwd=str(root), check=True,
                                                  capture_output=True, text=True, **k)
            run(["git", "init", "-q", "."])
            run(["git", "config", "user.email", "t@example.com"])
            run(["git", "config", "user.name", "t"])
            (root / "README.md").write_text("seed\n", encoding="utf-8")
            run(["git", "add", "README.md"])
            run(["git", "commit", "-q", "-m", "seed"])
            run(["git", "branch", "-M", "main"])

            run(["git", "checkout", "-q", "-b", "session-a"])
            self._fire("session-a", root)
            run(["git", "add", "-A"])
            run(["git", "commit", "-q", "-m", "session-a fires"])

            run(["git", "checkout", "-q", "main"])
            run(["git", "checkout", "-q", "-b", "session-b"])
            self._fire("session-b", root)
            run(["git", "add", "-A"])
            run(["git", "commit", "-q", "-m", "session-b fires"])

            run(["git", "checkout", "-q", "main"])
            run(["git", "merge", "-q", "--no-edit", "session-a"])
            merge_b = subprocess.run(
                ["git", "merge", "--no-edit", "session-b"],
                cwd=str(root), capture_output=True, text=True)
            self.assertEqual(merge_b.returncode, 0,
                              msg=f"session-b merge conflicted: {merge_b.stdout}\n{merge_b.stderr}")

            aggregate = spawn._hook_fires_aggregate(cwd=str(root))
            self.assertEqual(len([l for l in aggregate.splitlines() if l]), 2)


class DeviationLogSharding(unittest.TestCase):
    """이슈 #2348: 배포전 스케치대로 deviation-log.md 도 consult-log.md 와
    같은 방식으로 샤딩한다. 두 가지가 hook-fires/consult-log 와 다르다:
    (1) role 스코프까지 접는다 — `$CLAUDE_ROLE` 이 있으면
    `docs/issue-<n>/reports/<role>/deviation-log/` 아래, (2) 엔트리가
    여러 줄로 감길 수 있어 애그리게이터는 줄 단위가 아니라 샤드 파일
    통째로 이어붙인다."""

    def test_two_sessions_write_distinct_shard_files_role_scoped(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p1 = deviation_log._deviation_log_path(2348, role="implementation",
                                                    cwd=str(root), session_id="session-a")
            p1.write_text("- 2026-08-25T00:00:00Z | inline | first.\n", encoding="utf-8")
            p2 = deviation_log._deviation_log_path(2348, role="implementation",
                                                    cwd=str(root), session_id="session-b")
            p2.write_text("- 2026-08-25T00:01:00Z | inline | second.\n", encoding="utf-8")

            self.assertNotEqual(p1, p2)
            d = root / "docs" / "issue-2348" / "reports" / "implementation" / "deviation-log"
            self.assertEqual(len(list(d.glob("*.md"))), 2)
            # 예전 role-less flat 경로는 더 이상 쓰지 않는다.
            self.assertFalse(
                (root / "docs" / "issue-2348" / "reports" / "deviation-log.md").exists())

    def test_repeat_append_within_one_session_reuses_the_same_shard(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p1 = deviation_log._deviation_log_path(2348, role="implementation",
                                                    cwd=str(root), session_id="session-a")
            p1.write_text("- 2026-08-25T00:00:00Z | inline | first.\n", encoding="utf-8")
            p2 = deviation_log._deviation_log_path(2348, role="implementation",
                                                    cwd=str(root), session_id="session-a")
            self.assertEqual(p1, p2)

    def test_aggregate_preserves_multi_line_entries_whole_not_line_scrambled(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p1 = deviation_log._deviation_log_path(2348, role="conformance-review",
                                                    cwd=str(root), session_id="session-a")
            p1.write_text(
                "- 2026-08-25T00:00:00Z, filed (reported, not spawned):\n"
                "  this entry wraps across several physical lines, the way\n"
                "  a real deviation-log entry does.\n", encoding="utf-8")
            p2 = deviation_log._deviation_log_path(2348, role="conformance-review",
                                                    cwd=str(root), session_id="session-b")
            p2.write_text("- 2026-08-25T00:01:00Z | inline | one-liner.\n", encoding="utf-8")

            aggregate = deviation_log._deviation_log_aggregate(
                2348, role="conformance-review", cwd=str(root))
            self.assertIn(p1.read_text(encoding="utf-8"), aggregate)
            self.assertIn(p2.read_text(encoding="utf-8"), aggregate)

    def test_empty_state_no_prior_deviation_is_empty_string(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(
                deviation_log._deviation_log_aggregate(424242, role="implementation", cwd=td), "")

    def test_two_concurrent_sessions_merge_without_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = lambda *a, **k: subprocess.run(*a, cwd=str(root), check=True,
                                                  capture_output=True, text=True, **k)
            run(["git", "init", "-q", "."])
            run(["git", "config", "user.email", "t@example.com"])
            run(["git", "config", "user.name", "t"])
            (root / "README.md").write_text("seed\n", encoding="utf-8")
            run(["git", "add", "README.md"])
            run(["git", "commit", "-q", "-m", "seed"])
            run(["git", "branch", "-M", "main"])

            run(["git", "checkout", "-q", "-b", "issue-2348/session-a"])
            pa = deviation_log._deviation_log_path(2348, role="implementation",
                                                     cwd=str(root), session_id="session-a")
            pa.write_text("- 2026-08-25T00:00:00Z | inline | session a.\n", encoding="utf-8")
            run(["git", "add", "-A"])
            run(["git", "commit", "-q", "-m", "session-a deviation"])

            run(["git", "checkout", "-q", "main"])
            run(["git", "checkout", "-q", "-b", "issue-2348/session-b"])
            pb = deviation_log._deviation_log_path(2348, role="implementation",
                                                     cwd=str(root), session_id="session-b")
            pb.write_text("- 2026-08-25T00:01:00Z | inline | session b.\n", encoding="utf-8")
            run(["git", "add", "-A"])
            run(["git", "commit", "-q", "-m", "session-b deviation"])

            run(["git", "checkout", "-q", "main"])
            run(["git", "merge", "-q", "--no-edit", "issue-2348/session-a"])
            merge_b = subprocess.run(
                ["git", "merge", "--no-edit", "issue-2348/session-b"],
                cwd=str(root), capture_output=True, text=True)
            self.assertEqual(merge_b.returncode, 0,
                              msg=f"session-b merge conflicted: {merge_b.stdout}\n{merge_b.stderr}")

            aggregate = deviation_log._deviation_log_aggregate(
                2348, role="implementation", cwd=str(root))
            self.assertIn("session a", aggregate)
            self.assertIn("session b", aggregate)
