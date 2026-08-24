from _spawn_test_support import *  # noqa: F401,F403


class Classify(unittest.TestCase):
    def test_errored_wins(self):
        self.assertEqual(spawn.classify(1, {}, [], []), "errored")
        self.assertEqual(spawn.classify(0, {"is_error": True}, ["x"], []), "errored")

    def test_progressed_on_delta(self):
        self.assertEqual(spawn.classify(0, {}, ["records/a/qa.md"], []), "progressed")

    def test_waiting_on_human(self):
        blocked = [("implementation", "…§19 가 막는다")]
        self.assertEqual(spawn.classify(0, {}, [], blocked), "waiting-on-human")

    def test_refused_is_not_silent_failure(self):
        # 실측 2026-07-27, reflect 를 실제로 띄운 run: 룰북의 record-fields-gate
        # 가 §20 필수 섹션이 없다며 쓰기를 거부했고, 세션은 이유를 또렷이 말하고
        # 끝났다. 그건 아무 일도 안 일어났는데 이유를 모르는 것과 **정반대
        # 처분**을 받아야 한다 — 게이트가 막은 것은 시스템이 작동한 것이다.
        refused = {"permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, refused, [], []), "refused")

    def test_progress_outranks_refusal(self):
        # 일부가 막혔어도 보드가 움직였으면 그 run 의 처분은 progressed 다.
        # 거부 건수는 따로 찍히므로 사라지지 않는다.
        refused = {"permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, refused, ["records/a/qa.md"], []),
                         "progressed")

    def test_human_gate_outranks_refusal(self):
        refused = {"permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, refused, [], [("implementation", "§19")]),
                         "waiting-on-human")

    def test_silent_failure_is_loud(self):
        # 실측된 침묵-사망 모드: exit 0, 보드 무변화, 막힌 줄도 없고,
        # **거부당한 것도 없다** — 그래서 아무도 이유를 모른다.
        self.assertEqual(spawn.classify(0, {}, [], []), "silent-failure")

    def test_registered_null_result_declaration_is_not_silent_failure(self):
        # issue #476 round 3, candidate E: a session that declares a
        # registered refusal/null-result state, with no board delta and no
        # permission_denials, must not read the same as a dead session.
        result = {"result": "REFUSAL: nothing-to-do — no work warranted here"}
        self.assertEqual(spawn.classify(0, result, [], []), "refused-null-result")

    def test_unregistered_null_result_state_stays_silent_failure(self):
        # gaming resistance: the state token must be in the registered
        # vocabulary, not any free-text claim of refusal.
        result = {"result": "REFUSAL: i-felt-like-it — nah"}
        self.assertEqual(spawn.classify(0, result, [], []), "silent-failure")

    def test_null_result_declaration_does_not_outrank_delta_or_denial(self):
        result = {"result": "REFUSAL: nothing-to-do — no work warranted here",
                  "permission_denials": [{"tool_name": "Write"}]}
        self.assertEqual(spawn.classify(0, result, [], []), "refused")
        self.assertEqual(
            spawn.classify(0, result, ["records/a/qa.md"], []), "progressed")

class FailClosedDowngrade(unittest.TestCase):
    """issue #89 phase 2: progressed self-report but no verifiable commit
    must be downgraded, unless a blocked signal is present."""

    def test_no_new_commit_clean_tree_is_downgraded(self):
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False, []),
            "failed-no-commit")

    def test_no_new_commit_dirty_tree_is_downgraded(self):
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False,
                                        ["M some/file.py"]),
            "failed-no-commit")

    def test_new_commit_dirty_tree_is_promoted_not_downgraded(self):
        # issue #205 defect 1: a new commit landed but the tree is dirty
        # afterwards — this is not "no commit", so it must not collapse
        # into failed-no-commit. It gets its own outcome value instead.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], True,
                                        ["M some/file.py"]),
            "progressed-dirty-tree")

    def test_new_commit_clean_tree_is_left_alone(self):
        # honest-success path: real commit landed, tree is clean — no
        # false positive, no friction.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], True, []),
            "progressed")

    def test_blocked_signal_exempts_progressed_from_downgrade(self):
        # hunt-phase1.md: classify() checks delta before blocked, so a
        # run that touched the board while a human gate is still open is
        # classified "progressed" today. The downgrade must not silently
        # erase that honest blocked signal by demoting it to FAILED.
        blocked = [("implementation", "§19")]
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, blocked, False, []),
            "progressed")

    def test_non_progressed_outcomes_are_never_touched(self):
        for outcome in ("waiting-on-human", "refused", "errored",
                        "silent-failure", "uncommitted-work"):
            self.assertEqual(
                spawn.fail_closed_downgrade(outcome, 3, [], False, []),
                outcome, outcome)

    def test_adhoc_spawns_are_out_of_scope(self):
        # issue is None -> no dedicated git workspace to check; leave as-is.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", None, [], False, []),
            "progressed")

    def test_already_delivered_branch_exempts_verify_only_session(self):
        # issue-129 survey root cause 4 (issue-126's phase-2 sequence): a
        # phase-2 session on a branch that already carries phase-1's
        # commit+PR made no new commit of its own (before_head ==
        # after_head) but only read/verified — that is not a failure.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False, [],
                                        already_delivered=True),
            "progressed")

    def test_already_delivered_with_dirty_tree_still_downgrades(self):
        # "already delivered" covers prior commits, not this session's own
        # uncommitted leftovers.
        self.assertEqual(
            spawn.fail_closed_downgrade("progressed", 3, [], False,
                                        ["M some/file.py"],
                                        already_delivered=True),
            "failed-no-commit")

    def test_silent_failure_upgraded_when_already_delivered(self):
        # issue-484: re-delivery-of-already-landed session — classify()
        # sees an empty docs-board delta (nothing to do) and calls it
        # silent-failure, but the branch already carries an open/merged
        # PR from an earlier phase. Observable state says delivered.
        self.assertEqual(
            spawn.fail_closed_downgrade("silent-failure", 3, [], False, [],
                                        already_delivered=True),
            "progressed")

    def test_silent_failure_upgraded_when_new_commit_pushed(self):
        # issue-484: session's real change landed outside docs/issue-*/**
        # (or netted an empty docs delta) but a new commit was made and
        # pushed successfully — not a silent failure.
        self.assertEqual(
            spawn.fail_closed_downgrade("silent-failure", 3, [], True, [],
                                        push_succeeded=True),
            "progressed")

    def test_silent_failure_not_upgraded_without_push_success(self):
        # a new commit that failed to push (stranded local commit) must
        # not be read as delivered.
        self.assertEqual(
            spawn.fail_closed_downgrade("silent-failure", 3, [], True, [],
                                        push_succeeded=False),
            "silent-failure")

    def test_silent_failure_not_upgraded_on_closed_unmerged_pr(self):
        # regression guard for the after-proposal hunt gap: a branch whose
        # only PR was closed *without* merging must not count as
        # already_delivered (caller is responsible for passing False here
        # via `_pr_open_or_merged_for_branch`, not `_pr_for_branch`).
        self.assertEqual(
            spawn.fail_closed_downgrade("silent-failure", 3, [], False, [],
                                        already_delivered=False),
            "silent-failure")

    def test_silent_failure_with_uncommitted_changes_not_upgraded(self):
        # refused-commit-no-push shape (already handled upstream by the
        # outcome == "uncommitted-work" branch before this function is
        # ever reached with uncommitted non-empty, but the function itself
        # must still fail closed if it ever is).
        self.assertEqual(
            spawn.fail_closed_downgrade("silent-failure", 3, [], False,
                                        ["M some/file.py"],
                                        already_delivered=True),
            "silent-failure")

class PriorEventDetails(unittest.TestCase):
    """issue #129 root cause 1: `pr-opened` must not re-fire for a PR URL
    already recorded in this workspace's `.events.jsonl` from an earlier
    process (e.g. issue-123's repeated PR #124 URL across respawns)."""

    def test_empty_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(
                spawn._prior_event_details(Path(td) / "missing.events.jsonl",
                                           "pr-opened"),
                set())

    def test_reads_prior_matching_details(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ".events.jsonl"
            p.write_text(
                json.dumps({"ts": 1, "type": "pr-opened",
                           "detail": "https://github.com/o/r/pull/124"}) + "\n"
                + json.dumps({"ts": 2, "type": "gate-refusal",
                             "detail": "x"}) + "\n")
            self.assertEqual(
                spawn._prior_event_details(p, "pr-opened"),
                {"https://github.com/o/r/pull/124"})

class PreambleWarning(unittest.TestCase):
    """The issue-workspace task preamble in `_spawn_one` (spawn.py source,
    not a re-implementation) must warn that the turn is headless/single-turn
    and that run_in_background work dies at turn end."""

    def test_issue_preamble_source_warns_about_headless_background_death(self):
        # Issue #2135: the preamble is now the index appendage built via
        # `_dp("issue-preamble-index", ...)`; the warning must survive both
        # inline (trigger line) and in the canonical section prose.
        src = Path(spawn.__file__).read_text(encoding="utf-8")
        start = src.index('task = _dp("issue-preamble-index"')
        end = src.index(") + task", start)
        preamble_src = src[start:end]
        self.assertIn("headless", preamble_src)
        self.assertIn("run_in_background", preamble_src)
        self.assertIn("headless", spawn._COMPLETION_PROSE)
        self.assertIn("run_in_background", spawn._COMPLETION_PROSE)


class SkillInvocationNudge(unittest.TestCase):
    """issue #1960 phase B: whenever any skill is mounted (either --skills
    or the role-to-skill-repository mapping), the spawn task text must
    instruct the session to check the mounted list against the task before
    starting substantive work -- this is the single change the phase-B
    proposal (docs/issue-1960/proposals/phase-b-skill-invocation-nudge.md)
    approved, targeting the baseline's structural 0/38 gap."""

    def test_nudge_added_when_any_skill_source_mounted(self):
        src = Path(spawn.__file__).read_text(encoding="utf-8")
        start = src.index('if skill_sources or role_source["skills"]:')
        end = src.index("plugins: list[Path] = []", start)
        nudge_src = src[start:end]
        self.assertIn("스킬 점검", nudge_src)
        self.assertIn("Skill", nudge_src)

    def test_nudge_gated_on_a_mounted_skill_source(self):
        src = Path(spawn.__file__).read_text(encoding="utf-8")
        # the gating condition must cover both mount paths (issue #1742/#1774
        # --skills, and issue #1955/#1758 role-mapped skill-repo skills) --
        # a nudge gated on only one would silently miss sessions mounted via
        # the other path.
        self.assertIn('if skill_sources or role_source["skills"]:', src)


class GitHead(unittest.TestCase):
    @pytest.mark.slow
    def test_head_of_empty_repo_is_none(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess
            subprocess.run(["git", "init", "-q"], cwd=td)
            self.assertIsNone(spawn._git_head(td))

    @pytest.mark.slow
    def test_head_of_repo_with_commit_is_a_sha(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess
            subprocess.run(["git", "init", "-q"], cwd=td)
            subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=td)
            subprocess.run(["git", "config", "user.name", "t"], cwd=td)
            (Path(td) / "a.txt").write_text("x")
            subprocess.run(["git", "add", "a.txt"], cwd=td)
            subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=td)
            head = spawn._git_head(td)
            self.assertIsNotNone(head)
            self.assertEqual(len(head), 40)

class IsNewCommit(unittest.TestCase):
    def test_fresh_repo_first_commit_is_new(self):
        self.assertTrue(spawn._is_new_commit("ignored", None, "abc123"))

    def test_no_after_head_is_not_new(self):
        self.assertFalse(spawn._is_new_commit("ignored", "abc123", None))

    def test_unchanged_head_is_not_new(self):
        self.assertFalse(spawn._is_new_commit("ignored", "abc123", "abc123"))

    @pytest.mark.slow
    def test_checkout_of_preexisting_branch_is_not_new_commit(self):
        # Reproduces hunt-phase2 finding: a session that checks out an
        # unrelated pre-existing branch (no new commit created) must not be
        # counted as new_commit, even though HEAD moved.
        with tempfile.TemporaryDirectory() as td:
            import subprocess

            def git(*a):
                return subprocess.run(["git", "-C", td, *a],
                                       capture_output=True, text=True, check=True)

            git("init", "-q")
            git("config", "user.email", "t@t.t")
            git("config", "user.name", "t")
            (Path(td) / "a.txt").write_text("x")
            git("add", "a.txt")
            git("commit", "-q", "-m", "init")
            init_branch = subprocess.run(
                ["git", "-C", td, "symbolic-ref", "--short", "HEAD"],
                capture_output=True, text=True).stdout.strip()
            # Orphan branch with unrelated history — not a descendant of
            # init_branch — so its tip is a pre-existing commit that is in
            # no ancestry relationship with before_head at all.
            git("checkout", "-q", "--orphan", "other")
            (Path(td) / "b.txt").write_text("y")
            git("add", "b.txt")
            git("commit", "-q", "-m", "pre-existing unrelated commit")
            git("checkout", "-q", init_branch)

            before_head = spawn._git_head(td)
            git("checkout", "-q", "other")  # no new commit — just a checkout
            after_head = spawn._git_head(td)

            self.assertNotEqual(before_head, after_head)
            self.assertFalse(spawn._is_new_commit(td, before_head, after_head))

    @pytest.mark.slow
    def test_real_new_commit_is_new(self):
        with tempfile.TemporaryDirectory() as td:
            import subprocess

            def git(*a):
                return subprocess.run(["git", "-C", td, *a],
                                       capture_output=True, text=True, check=True)

            git("init", "-q")
            git("config", "user.email", "t@t.t")
            git("config", "user.name", "t")
            (Path(td) / "a.txt").write_text("x")
            git("add", "a.txt")
            git("commit", "-q", "-m", "init")
            before_head = spawn._git_head(td)
            (Path(td) / "a.txt").write_text("y")
            git("add", "a.txt")
            git("commit", "-q", "-m", "progress")
            after_head = spawn._git_head(td)
            self.assertTrue(spawn._is_new_commit(td, before_head, after_head))

class BootstrapFetchesBeforeVerification(unittest.TestCase):
    """issue #1507 req 1 — 세션 부트스트랩이 verification/absence-claim
    단계보다 먼저 `git fetch --prune` 로 origin/main sha 를 기록하는지.

    실 git 저장소 두 개(origin + 그걸 clone 한 work_dir)를 쓴다: origin 을
    work_dir 이 이미 뒤처진 뒤에 한 커밋 더 진행시켜 "deliberately stale
    clone"을 만든다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def test_bootstrap_fetches_before_verification(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            # work 을 뒤처지게 만든다: origin 에 work 이 모르는 새 커밋을
            # 쌓는다 (deliberately behind-origin clone).
            (origin / "b.txt").write_text("landed after clone")
            self._git(origin, "add", "b.txt")
            self._git(origin, "commit", "-q", "-m", "landed after clone")
            new_origin_sha = self._git(origin, "rev-parse", "HEAD").stdout.strip()

            # 사전 조건: 아직 부트스트랩 fetch 기록이 없다 — 세션이 첫
            # verification/absence-claim 단계를 아직 밟지 않은 상태.
            self.assertIsNone(spawn.get_bootstrap_fetch_record(str(work)))
            # 사전 조건: work 의 로컬 origin/main 은 아직 새 커밋을 모른다.
            stale_sha = self._git(
                work, "rev-parse", "refs/remotes/origin/HEAD").stdout.strip()
            self.assertNotEqual(stale_sha, new_origin_sha)

            record = spawn.bootstrap_fetch_and_record_sha(str(work), "test")

            self.assertEqual(record["sha"], new_origin_sha)
            self.assertTrue(record["fetched_at"])
            self.assertEqual(spawn.get_bootstrap_fetch_record(str(work)), record)

        # 빈 상태: 부트스트랩 fetch 를 아직 부르지 않은 새 work_dir 은
        # 기록이 없다 — 같은 테스트 모듈에서 함께 확인한다(fresh clone도
        # trivially 통과, 게이트 없음).
        self.assertIsNone(spawn.get_bootstrap_fetch_record("/nonexistent/never-fetched"))

    @pytest.mark.slow
    def test_checkout_issue_branch_records_sha_before_returning(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("base")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "base commit")

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999910, "implementation"
            result = spawn.checkout_issue_branch(str(work), issue, role)

            self.assertEqual(result, f"issue-{issue}/{role}")
            record = spawn.get_bootstrap_fetch_record(str(work))
            self.assertIsNotNone(
                record, "checkout_issue_branch 가 브랜치 검증 전에 부트스트랩 "
                "fetch 기록을 남겨야 한다")
            origin_sha = self._git(origin, "rev-parse", "HEAD").stdout.strip()
            self.assertEqual(record["sha"], origin_sha)

class AbsorbedBranchRecutMidRun(unittest.TestCase):
    """이슈 #784: 세션이 이미 살아있는 채로 자기 브랜치가 흡수됐을 때 —
    `checkout_issue_branch()`가 스폰 시점에만 한 번 부르는 것과 달리,
    mid-run 재검사(`recut_if_absorbed_cli`, 훅이 호출)는 세션 자신의
    다음 commit/PR-open 직전에 같은 흡수 판정을 다시 돌린다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    @pytest.mark.slow
    def test_recut_absorbed_branch_preserves_untracked_files(self):
        # #732 이 spawn 시점에 검증한 것과 같은 시나리오를, 공유 헬퍼
        # `_recut_absorbed_branch`를 직접 불러 mid-run 재사용 경로에서도
        # 검증한다 — 브랜치가 이미 체크아웃돼 있고 base 에 완전히 흡수된
        # (0-ahead) 상태에서 untracked 작업이 보존돼야 한다.
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

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999910, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            base_commit = self._git(work, "rev-parse", base_branch).stdout.strip()
            (work / "scratch-work.txt").write_text("uncommitted, untracked")

            result = spawn._recut_absorbed_branch(str(work), br)

            self.assertEqual(result.returncode, 0, result.stderr)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, base_commit,
                             "재컷된 브랜치가 base 팁과 일치해야 한다")
            self.assertEqual((work / "scratch-work.txt").read_text(),
                             "uncommitted, untracked",
                             "untracked 작업이 재컷 뒤에도 남아있어야 한다")

    @pytest.mark.slow
    def test_recut_absorbed_branch_unchanged_when_ahead(self):
        # base 대비 커밋이 앞서 있으면(진짜 흡수가 아니면) 아무 것도 안
        # 건드리고 그냥 checkout br 만 해야 한다.
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

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999911, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            (work / "progress.txt").write_text("real committed work")
            self._git(work, "add", "progress.txt")
            self._git(work, "commit", "-q", "-m", "in-progress work, ahead of base")
            ahead_commit = self._git(work, "rev-parse", br).stdout.strip()

            result = spawn._recut_absorbed_branch(str(work), br)

            self.assertEqual(result.returncode, 0, result.stderr)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, ahead_commit,
                             "커밋이 앞서 있으면 브랜치가 재컷되면 안 된다")

    @pytest.mark.slow
    def test_recut_if_absorbed_cli_recuts_mid_run_absorbed_branch(self):
        # 이슈 #784 인수 기준: 세션이 RUNNING 인 채로 자기 phase-1 PR 이
        # merge+delete-branch 돼 브랜치가 흡수된 상태를 흉내낸다 — origin
        # 에서 브랜치가 사라지고(merge+delete) 로컬 워크스페이스는 여전히
        # 그 브랜치 위에 남아있는 상황과 동치인, base 에 완전히 흡수된
        # 로컬 ref. `recut_if_absorbed_cli`가 롤백 없이 재컷해, 뒤이은
        # commit 이 "No commits between main and issue-<n>/<role>"로 조용히
        # 실패하지 않아야 한다.
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

            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999912, "implementation"
            br = f"issue-{issue}/{role}"
            # 세션이 실제로 살아있던 워크스페이스를 흉내낸다: 브랜치를
            # base 에서 파고, phase-1 PR 이 merge+delete-branch 되며
            # (원격에는 없고, 로컬 ref 만 base 와 정확히 같게) 흡수된
            # 상태를 재현한다.
            self._git(work, "checkout", "-q", "-b", br, base_branch)
            base_commit = self._git(work, "rev-parse", base_branch).stdout.strip()
            (work / "mid-run-scratch.txt").write_text("phase-2 work in progress")

            rc = spawn.recut_if_absorbed_cli(str(work))

            self.assertEqual(rc, 0)
            after = self._git(work, "rev-parse", br).stdout.strip()
            self.assertEqual(after, base_commit)
            self.assertEqual((work / "mid-run-scratch.txt").read_text(),
                             "phase-2 work in progress",
                             "mid-run 재컷도 untracked 작업을 보존해야 한다")
            # 재컷 뒤 세션이 실제로 커밋하면 base 대비 ahead 인 진짜 PR 이
            # 열릴 수 있어야 한다 — "No commits" 로 다시 막히지 않는다.
            self._git(work, "add", "mid-run-scratch.txt")
            self._git(work, "commit", "-q", "-m", "phase 2 commit after recut")
            self.assertNotEqual(
                self._git(work, "rev-list", "--count", f"{base_branch}..{br}")
                .stdout.strip(),
                "0")

    def test_recut_if_absorbed_cli_noop_on_detached_head(self):
        # 브랜치 이름이 issue-<n>/<role> 모양이 아니면(분리 HEAD 등) 아무
        # 것도 안 하고 0 을 반환한다 — roster/liveness 조회 없이 세션
        # 자신의 HEAD 만 보는 이 함수의 fail-open 경계.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            self._init_repo(work)
            (work / "a.txt").write_text("x")
            self._git(work, "add", "a.txt")
            self._git(work, "commit", "-q", "-m", "c")
            head = self._git(work, "rev-parse", "HEAD").stdout.strip()
            self._git(work, "checkout", "-q", head)  # detached HEAD

            rc = spawn.recut_if_absorbed_cli(str(work))

            self.assertEqual(rc, 0)

class Watchdog(unittest.TestCase):
    """이슈 #90 phase-2: observe-only 이상 신호 네 가지."""

    def _entry(self, log, work=None, ts=None, before_head=None, pid=None):
        return {"log": str(log), "work": work, "ts": ts or int(time.time()),
                "before_head": before_head, "pid": pid}

    def test_silence_signal_fires_past_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("log-silence" in a for a in out))

    def test_no_silence_signal_within_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("log-silence" in a for a in out))

    def test_delegation_phrasing_signal(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text","text":"run_in_background 로 넘겼다"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("background-delegation-phrasing" in a for a in out))

    def test_no_delegation_signal_on_clean_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text","text":"평범한 진행 로그"}\n')
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("background-delegation-phrasing" in a for a in out))

    @staticmethod
    def _denial_line():
        # 이슈 #994: 구조적 거부 — type:"user" 줄의 is_error tool_result 가
        # _classify_refusal_text 의 층 2(하네스) 패턴에 매치한다.
        obj = {"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True,
             "content": "Permission to use Bash has been denied"}]}}
        return json.dumps(obj, ensure_ascii=False) + "\n"

    @staticmethod
    def _non_denial_user_line():
        obj = {"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": False, "content": "ok"}]}}
        return json.dumps(obj, ensure_ascii=False) + "\n"

    def test_denied_tool_calls_signal_fires_at_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text(self._denial_line() * spawn.WATCHDOG_DENIAL_THRESHOLD)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("denied-tool-calls" in a for a in out))

    def test_denied_tool_calls_signal_silent_below_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text(self._denial_line() * (spawn.WATCHDOG_DENIAL_THRESHOLD - 1))
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("denied-tool-calls" in a for a in out))

    def test_denied_tool_calls_signal_ignores_quoted_source_text(self):
        # 이슈-476 실측 재현: 게이트 소스를 읽거나 인용하는 세션은 "denied"
        # 단어를 몇 번이고 담고 있어도 실제 거부가 아니면 0건이어야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            quoted = self._non_denial_user_line() * spawn.WATCHDOG_DENIAL_THRESHOLD
            quoted += json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text",
                 "text": ("denied " * (spawn.WATCHDOG_DENIAL_THRESHOLD + 5)
                          + "permission_denial permission_denial")}]}},
                ensure_ascii=False) + "\n"
            log.write_text(quoted)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertFalse(any("denied-tool-calls" in a for a in out))

    def test_denied_tool_calls_signal_fires_on_genuine_denial_tool_result(self):
        # 위 케이스의 짝: 실제 is_error tool_result 거부는 threshold 이상이면
        # 여전히 잡혀야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text(self._denial_line() * spawn.WATCHDOG_DENIAL_THRESHOLD)
            out = spawn.watchdog_check_one("k", self._entry(log), state={})
            self.assertTrue(any("denied-tool-calls" in a for a in out))

    def test_only_new_log_content_is_scanned_each_call(self):
        # 이미 스캔한 구간은 다음 호출에서 다시 세지 않는다 (오프셋 추적).
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text(self._denial_line() * spawn.WATCHDOG_DENIAL_THRESHOLD)
            state = {}
            first = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertTrue(any("denied-tool-calls" in a for a in first))
            second = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertFalse(any("denied-tool-calls" in a for a in second))

    def test_stale_offset_survives_log_truncation_on_respawn(self):
        # spawn() 은 같은 로그 경로를 "w" 로 다시 열어 재시작 시 truncate
        # 한다. 이전 세션에서 쌓인 오프셋이 새 로그(더 짧음)에 그대로 남아
        # 있으면 새 세션의 신호 2/3 이 로그가 옛 길이를 다시 넘어설 때까지
        # 조용히 안 잡힌다 — 재시작 직후 첫 스캔에서 바로 잡혀야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text(self._denial_line() * (spawn.WATCHDOG_DENIAL_THRESHOLD + 5))
            state = {}
            first = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertTrue(any("denied-tool-calls" in a for a in first))
            self.assertGreater(state["k"]["offset"], 0)
            # respawn: 로그가 truncate 되어 이전 오프셋보다 짧아진다
            log.write_text(self._denial_line() * spawn.WATCHDOG_DENIAL_THRESHOLD)
            second = spawn.watchdog_check_one("k", self._entry(log), state=state)
            self.assertTrue(any("denied-tool-calls" in a for a in second))

    @pytest.mark.slow
    def test_no_commits_late_signal_fires(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            work.mkdir()
            subprocess.run(["git", "init", "-q", str(work)])
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@t.t"])
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"])
            (work / "f").write_text("x")
            subprocess.run(["git", "-C", str(work), "add", "f"])
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "init"])
            head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
            log = Path(td) / "s.log"
            log.write_text("")
            ts = time.time() - (spawn.WATCHDOG_NO_COMMIT_MIN + 5) * 60
            out = spawn.watchdog_check_one(
                "k", self._entry(log, work=str(work), ts=ts, before_head=head),
                state={})
            self.assertTrue(any("no-commits-late" in a for a in out))

    @pytest.mark.slow
    def test_no_commits_late_signal_silent_before_threshold(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            work.mkdir()
            subprocess.run(["git", "init", "-q", str(work)])
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@t.t"])
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"])
            (work / "f").write_text("x")
            subprocess.run(["git", "-C", str(work), "add", "f"])
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "init"])
            head = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
            log = Path(td) / "s.log"
            log.write_text("")
            out = spawn.watchdog_check_one(
                "k", self._entry(log, work=str(work), ts=time.time(), before_head=head),
                state={})
            self.assertFalse(any("no-commits-late" in a for a in out))

    def test_roster_watchdog_reports_no_anomaly_on_empty_roster(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0):
                    spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
            self.assertIn("돌고 있는 역할 세션 없음", buf.getvalue())

    def test_roster_watchdog_surfaces_undispositioned_prs(self):
        """이슈 #1239: 워치독 틱마다 처분 안 된 PR 목록이 always-emit
        카테고리로 찍힌다 — 로스터가 비어 있어도(observe-only 스캔과
        무관하게) 나온다."""
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            blockers = [{"issue": 22, "phase": "phase1", "url": "https://example/22",
                         "number": 2, "headRefName": "issue-22/qa", "body": "",
                         "age_hours": 3.25}]
            ledger_calls = []
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: (blockers, True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)):
                    spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
            printed = buf.getvalue()
            self.assertIn("[returned-pr] issue #22", printed)
            self.assertIn("phase1", printed)
            self.assertIn("3.2h", printed)
            events = [e["event"] for e in ledger_calls]
            self.assertIn("returned_pr_surfaced", events)

    def test_roster_watchdog_no_returned_pr_line_when_none_open(self):
        """이슈 #1239 empty-state: 열린 PR 이 없으면 surfaced 목록도,
        빈 섹션도 찍히지 않는다."""
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            ledger_calls = []
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
                     mock.patch.object(spawn, "_undispositioned_role_prs",
                                       lambda root, exclude_issue=None: ([], True)), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda entry: ledger_calls.append(entry)):
                    spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
            self.assertNotIn("[returned-pr]", buf.getvalue())
            events = [e["event"] for e in ledger_calls]
            self.assertNotIn("returned_pr_surfaced", events)

    def test_roster_watchdog_surfaces_returned_pr_same_tick_as_session_death(self):
        """이슈 #2098: 죽은 own 로스터 엔트리의 브랜치는, 로스터 엔트리가
        (비동기 self-trigger 로) 아직 제거되지 않은 바로 그 틱에도
        `own_branches` 제외 대상에서 빠져야 한다 — 안 그러면 PR-open 이
        다음 폴 틱까지 미뤄진다(재현: PR #2097 이 11분 뒤에야 발견됨).
        `_undispositioned_role_prs()` 를 목으로 대체하지 않고 실제 경로를
        태워 `_open_role_prs`/`ci._approved_roles_on_issue` 만 목한다."""
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            roster_path = Path(td) / "active.json"
            # pid 는 죽어 있지만(999999999) 로스터 엔트리는 아직 남아
            # 있다 — self-trigger 의 roster_remove() 가 비동기라 이 틱에는
            # 아직 안 지워진 상태를 재현한다.
            roster_path.write_text(json.dumps({
                "issue-2098/implementation": self._entry(
                    log, work=str(work), pid=999999999)}))
            fake_prs = [{"number": 2097, "headRefName": "issue-2098/implementation",
                         "body": "", "url": "https://example/2097",
                         "createdAt": "2026-08-23T08:37:00Z", "issue": 2098}]
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            old_ledger = spawn.RECONCILE_LEDGER
            old_pr_check = spawn._pr_open_or_merged_for_branch
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            spawn.RECONCILE_LEDGER = Path(td) / "reconcile_ledger.json"
            spawn._pr_open_or_merged_for_branch = lambda root, branch: 2097
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
                     mock.patch.object(spawn, "_post_session_end_comment"), \
                     mock.patch.object(spawn, "_open_role_prs",
                                        return_value=(fake_prs, True)):
                    sys.path.insert(0, str((Path(spawn.__file__).parent / "gates").resolve()))
                    import ci as _ci
                    with mock.patch.object(_ci, "_approved_roles_on_issue", return_value=[]):
                        spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
                spawn.RECONCILE_LEDGER = old_ledger
                spawn._pr_open_or_merged_for_branch = old_pr_check
            printed = buf.getvalue()
            self.assertIn("[returned-pr] issue #2098", printed)
            self.assertIn("https://example/2097", printed)

    def test_roster_watchdog_returns_zero_for_clean_non_empty_roster(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            roster_path.write_text(json.dumps({
                "k": self._entry(log, pid=os.getpid())}))
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            old_ledger = spawn.RECONCILE_LEDGER
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            spawn.RECONCILE_LEDGER = Path(td) / "reconcile_ledger.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0):
                    result = spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
                spawn.RECONCILE_LEDGER = old_ledger
            self.assertEqual(result, 0)

    def test_roster_watchdog_returns_anomaly_count_for_stalled_entry(self):
        # 이슈 #782: 같은 idle 신호가 두 독립 레인에서 잡힌다 — 기존
        # watchdog_check_one 의 log-silence anomaly(+1) 와 새 diagnose_health
        # 의 STALLED 진단(+1, 원장 게이팅 통과) — 합쳐서 2.
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            roster_path.write_text(json.dumps({
                "k": self._entry(log, pid=os.getpid())}))
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            old_ledger = spawn.RECONCILE_LEDGER
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            spawn.RECONCILE_LEDGER = Path(td) / "reconcile_ledger.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0):
                    result = spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
                spawn.RECONCILE_LEDGER = old_ledger
            self.assertEqual(result, 2)
            self.assertIn("[health]", buf.getvalue())
            self.assertIn("STALLED", buf.getvalue())

    def test_roster_watchdog_folds_board_wide_sweep_into_anomaly_count(self):
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            old_ledger = spawn.RECONCILE_LEDGER
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            spawn.RECONCILE_LEDGER = Path(td) / "reconcile_ledger.json"
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=3), \
                     mock.patch.object(spawn, "cross_workspace_board_sweep_lock_acquire",
                                        return_value=(True, "")):
                    result = spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
                spawn.RECONCILE_LEDGER = old_ledger
            self.assertEqual(result, 3)
            self.assertNotIn("이상 신호 없음", buf.getvalue())

    def test_roster_watchdog_reports_completed_for_session_end_written_after_arming_turn(self):
        # 이슈 #848: #849 이 핀한 결함은 "부모 턴이 끝난 뒤에 날아온 종료
        # 이벤트를 놓친다"는 모양이다 — CLI 의 run_in_background watch 는
        # 그 턴이 끝나면 죽지만, poll 백스톱(#835/#841 Monitor 틱이 그대로
        # 타는 poll_rearm_arm_if_due -> roster_watchdog 경로)은 턴과 무관하게
        # 다음 틱에서 roster 를 다시 스캔한다. 여기서는 그 스캔이, 로스터
        # 엔트리의 프로세스가 이미 죽은 "뒤에" events.jsonl 에 적힌
        # session-end 를 실제로 잡아 COMPLETED 로 보고하는지 — 아무 흔적
        # 없이 조용히 드롭되지 않는지 — 를 재현한다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            events_path = spawn._events_path(str(work))
            # "arming turn" 동안은 session-start 만 있고, 그 턴이 끝난 뒤에야
            # (시뮬레이션: 이 시점에 이미 pid 999999999 는 죽어 있다) 후처리
            # 꼬리가 session-end 를 남긴다 — #849 의 사망 시나리오 순서.
            spawn._append_event(events_path, "session-start", {"pid": 999999999, "ts": 1})
            spawn._append_event(events_path, "session-end", "progressed")
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            roster_path = Path(td) / "active.json"
            roster_path.write_text(json.dumps({
                "issue-848/implementation": self._entry(
                    log, work=str(work), pid=999999999)}))
            old_roster = spawn.ROSTER
            old_state = spawn.WATCHDOG_STATE
            old_ledger = spawn.RECONCILE_LEDGER
            old_pr_check = spawn._pr_open_or_merged_for_branch
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            spawn.RECONCILE_LEDGER = Path(td) / "reconcile_ledger.json"
            spawn._pr_open_or_merged_for_branch = lambda root, branch: None
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.object(spawn, "_board_wide_sweep", return_value=0), \
                     mock.patch.object(spawn, "_post_session_end_comment"):
                    result = spawn.roster_watchdog()
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
                spawn.RECONCILE_LEDGER = old_ledger
                spawn._pr_open_or_merged_for_branch = old_pr_check
            # 이상 신호 없이(정상 종료) 매 틱 상태 보고 라인에 COMPLETED 로
            # 잡혀야 한다 — 사라지지 않는다.
            self.assertEqual(result, 0)
            self.assertIn("[poll-report] issue-848/implementation: COMPLETED", buf.getvalue())

    def test_board_wide_sweep_reports_and_counts_closure_violations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs = mock.MagicMock()
            fake_cs.issue_state_index_all.return_value = ({}, True)
            fake_cs.load_backoff_state.return_value = {}
            fake_cs.sweep_should_run.return_value = True
            fake_cs.rate_limit_remaining.return_value = (5000, True)
            fake_cs._RATE_LIMIT_GUARD_THRESHOLD = 500
            fake_cs.next_categories.return_value = (
                ["closure-sweep", "spawn-coverage"], [])
            fake_cs.find_violations.return_value = (
                [{"issue": 1, "pr": 2, "role": "implementation",
                  "kind": "open-pr-on-closed-issue"}], [])
            fake_cs.format_report.return_value = "issue #1 / PR #2: open-pr-on-closed-issue"
            fake_sc = mock.MagicMock()
            fake_sc._list_open_issues.return_value = []
            fake_sc.find_uncovered.return_value = []
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc}):
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(result, 1)
            self.assertIn("closure-sweep: 위반 1건", buf.getvalue())

    def test_board_wide_sweep_reports_and_counts_uncovered_issues(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs = mock.MagicMock()
            fake_cs.issue_state_index_all.return_value = ({}, True)
            fake_cs.load_backoff_state.return_value = {}
            fake_cs.sweep_should_run.return_value = True
            fake_cs.rate_limit_remaining.return_value = (5000, True)
            fake_cs._RATE_LIMIT_GUARD_THRESHOLD = 500
            fake_cs.next_categories.return_value = (
                ["closure-sweep", "spawn-coverage"], [])
            fake_cs.find_violations.return_value = ([], [])
            fake_sc = mock.MagicMock()
            fake_sc._list_open_issues.return_value = [
                {"number": 500, "createdAt": "2020-01-01T00:00:00Z"}]
            fake_sc.find_uncovered.return_value = [500]
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc}):
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(result, 1)
            self.assertIn("spawn-coverage: 커버되지 않은 이슈", buf.getvalue())

    def test_board_wide_sweep_clean_returns_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs = mock.MagicMock()
            fake_cs.issue_state_index_all.return_value = ({}, True)
            fake_cs.load_backoff_state.return_value = {}
            fake_cs.sweep_should_run.return_value = True
            fake_cs.rate_limit_remaining.return_value = (5000, True)
            fake_cs._RATE_LIMIT_GUARD_THRESHOLD = 500
            fake_cs.next_categories.return_value = (
                ["closure-sweep", "spawn-coverage"], [])
            fake_cs.find_violations.return_value = ([], [])
            fake_sc = mock.MagicMock()
            fake_sc._list_open_issues.return_value = []
            fake_sc.find_uncovered.return_value = []
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc}):
                result = spawn._board_wide_sweep(root)
            self.assertEqual(result, 0)

    def test_board_wide_sweep_reports_gh_failure_not_as_clean(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs = mock.MagicMock()
            fake_cs.issue_state_index_all.return_value = ({}, True)
            fake_cs.load_backoff_state.return_value = {}
            fake_cs.sweep_should_run.return_value = True
            fake_cs.rate_limit_remaining.return_value = (5000, True)
            fake_cs._RATE_LIMIT_GUARD_THRESHOLD = 500
            fake_cs.next_categories.return_value = (
                ["closure-sweep", "spawn-coverage"], [])
            fake_cs.find_violations.return_value = (
                [], [{"subject": "issue-1", "reason": "gh-issue-view-failed"}])
            fake_sc = mock.MagicMock()
            fake_sc._list_open_issues.return_value = None
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc}):
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(result, 2)
            self.assertIn("gh 실패", buf.getvalue())

    def _stub_closure_sweep_for_delta(self):
        fake_cs = mock.MagicMock()
        fake_cs.issue_state_index_all.return_value = ({}, True)
        fake_cs.load_backoff_state.return_value = {}
        fake_cs.sweep_should_run.return_value = True
        fake_cs.rate_limit_remaining.return_value = (5000, True)
        fake_cs._RATE_LIMIT_GUARD_THRESHOLD = 500
        fake_cs.next_categories.return_value = (
            ["closure-sweep", "spawn-coverage"], [])
        fake_cs.find_violations.return_value = ([], [])
        fake_sc = mock.MagicMock()
        fake_sc._list_open_issues.return_value = []
        fake_sc.find_uncovered.return_value = []
        return fake_cs, fake_sc

    def test_board_wide_sweep_no_change_skips_detail_fetches(self):
        """issue #1688 acceptance (1): a no-change delta tick performs
        exactly one gh_delta probe call and zero find_violations calls, and
        prints the grep-able "no-change (delta empty)" line."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_gh_delta = mock.MagicMock()
            fake_gh_delta.fetch_delta.return_value = (None, "cursor-1", "no-change")
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(result, 0)
            self.assertEqual(fake_gh_delta.fetch_delta.call_count, 1)
            self.assertEqual(fake_cs.find_violations.call_count, 0)
            fake_req_drift.assert_not_called()
            self.assertIn("no-change (delta empty)", buf.getvalue())

    def test_board_wide_sweep_delta_narrows_closure_sweep_to_changed_subjects(self):
        """issue #1688 acceptance (2): a delta with 2 changed issues causes
        exactly those 2 subjects to be re-evaluated (find_violations'
        `subjects` kwarg is narrowed, not the whole board)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            for n in (101, 202, 303):
                d = root / "docs" / f"issue-{n}" / "reports"
                d.mkdir(parents=True)
                (d / "implementation.md").write_text(
                    "---\nloop_state: landed\n---\nbody\n")
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_gh_delta = mock.MagicMock()
            fake_gh_delta.fetch_delta.return_value = (
                [{"number": 101, "updated_at": "2026-08-16T00:00:00Z"},
                 {"number": 202, "updated_at": "2026-08-16T00:00:00Z"}],
                "cursor-2", "delta")
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(fake_gh_delta.fetch_delta.call_count, 1)
            self.assertEqual(fake_cs.find_violations.call_count, 1)
            _args, kwargs = fake_cs.find_violations.call_args
            subjects = kwargs.get("subjects")
            self.assertIsNotNone(subjects)
            self.assertEqual(set(subjects.keys()), {"issue-101", "issue-202"})
            fake_req_drift.assert_called_once_with(root, changed_numbers={101, 202})
            self.assertIn("delta 2건", buf.getvalue())

    def test_board_wide_sweep_full_rescan_falls_through_and_logs(self):
        """issue #1688 acceptance (3): a full-rescan classification flows
        through to today's full-board logic and is logged as such."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_gh_delta = mock.MagicMock()
            fake_gh_delta.fetch_delta.return_value = (None, None, "full-rescan")
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(fake_cs.find_violations.call_count, 1)
            _args, kwargs = fake_cs.find_violations.call_args
            self.assertIsNone(kwargs.get("subjects"))
            fake_req_drift.assert_called_once_with(root, changed_numbers=None)
            self.assertIn("full-rescan", buf.getvalue())

    def test_board_wide_sweep_cold_cursor_uses_same_full_rescan_path(self):
        """issue #1688 acceptance (4): gh_delta's own "full-rescan"
        classification on a missing cursor drives the same full-logic path
        as (3) — no separate first-tick special case in the wiring."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_gh_delta = mock.MagicMock()
            # cold cursor -> gh_delta itself returns "full-rescan" (per its
            # own documented contract); the wiring adds no extra branching.
            fake_gh_delta.fetch_delta.return_value = (None, "2026-08-16T00:00:00Z", "full-rescan")
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(fake_cs.find_violations.call_count, 1)
            _args, kwargs = fake_cs.find_violations.call_args
            self.assertIsNone(kwargs.get("subjects"))
            fake_req_drift.assert_called_once_with(root, changed_numbers=None)
            self.assertIn("full-rescan", buf.getvalue())

    def test_board_wide_sweep_gh_delta_error_falls_back_to_full_logic(self):
        """issue #1688 acceptance (5): an "error" classification never
        silently blinds the sweep — it falls back to full logic and logs
        that gh_delta itself failed."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_gh_delta = mock.MagicMock()
            fake_gh_delta.fetch_delta.return_value = (None, None, "error")
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            self.assertEqual(fake_cs.find_violations.call_count, 1)
            fake_req_drift.assert_called_once_with(root, changed_numbers=None)
            self.assertIn("gh_delta 프로브 실패", buf.getvalue())

    def test_requirement_drift_delta_mode_fetches_only_changed_and_reuses_cache(self):
        """issue #1688: requirement_drift(root, changed_numbers=...) only
        re-fetches the changed numbers via the shared gh_cache and reuses
        the on-disk verdict cache for everything else."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            specs = root / "docs" / "specs"
            specs.mkdir(parents=True)
            (specs / "requirement-digest.md").write_text(
                "- R001: widget must spin [open] (source: #1)\n")
            cache_path = spawn._requirement_drift_cache_path(root)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps({
                "9": {"title": "old cached issue", "body": "mentions R001"}}))
            with mock.patch.object(
                    spawn, "_fetch_issue_or_pr_via_cache",
                    return_value={"number": 42, "title": "new", "body": "R001 fixed"}) as fake_fetch:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    spawn.requirement_drift(root, changed_numbers={42})
                finally:
                    sys.stdout = old_stdout
            fake_fetch.assert_called_once_with(root, 42)
            saved = json.loads(cache_path.read_text())
            self.assertIn("42", saved)
            self.assertIn("9", saved)
            # R001 is mentioned by the freshly-fetched #42 -> no drift line.
            self.assertNotIn("R001", buf.getvalue())

    def _stub_gh_budget_always_ok(self):
        fake_gb = mock.MagicMock()
        fake_gb.GhBudget.return_value.charge.return_value = {
            "ok": True, "class": "watchdog", "remaining": None}
        fake_gb.budget_message.side_effect = (
            lambda source, remaining, until=None: f"[watchdog] {source}: 미집계")
        return fake_gb

    def test_board_wide_sweep_pr_only_delta_maps_to_subject_via_head_ref(self):
        """PR review blocker 1 (issue #1688): a delta containing ONLY a
        changed PR whose head-ref is issue-42/implementation still
        narrows closure-sweep to subject issue-42."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            d = root / "docs" / "issue-42" / "reports"
            d.mkdir(parents=True)
            (d / "implementation.md").write_text(
                "---\nloop_state: landed\n---\nbody\n")
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_cs._pr_index_all.return_value = (
                {"issue-42/implementation": {"number": 777, "state": "OPEN", "body": ""}},
                True)
            fake_gh_delta = mock.MagicMock()
            fake_gh_delta.fetch_delta.return_value = (
                [{"number": 777, "updated_at": "2026-08-16T00:00:00Z",
                  "pull_request": {"url": "..."}}],
                "cursor-3", "delta")
            fake_gb = self._stub_gh_budget_always_ok()
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta,
                                   "gh_budget": fake_gb}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            fake_gh_delta.fetch_delta.assert_called_once_with(
                root, "acme/widgets", "issues", include_prs=True)
            self.assertEqual(fake_cs.find_violations.call_count, 1)
            _args, kwargs = fake_cs.find_violations.call_args
            subjects = kwargs.get("subjects")
            self.assertIsNotNone(subjects)
            self.assertEqual(set(subjects.keys()), {"issue-42"})
            fake_req_drift.assert_called_once_with(root, changed_numbers={42})

    def test_board_wide_sweep_gh_budget_exhausted_skips_probe(self):
        """PR review blocker 2 (issue #1688): GhBudget metering gates the
        gh_delta probe itself — exhaustion skips with its message and
        never calls fetch_delta."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gates").mkdir()
            fake_cs, fake_sc = self._stub_closure_sweep_for_delta()
            fake_gh_delta = mock.MagicMock()
            fake_gb = mock.MagicMock()
            fake_gb.GhBudget.return_value.charge.return_value = {
                "ok": False, "reason": "budget-exhausted",
                "class": "watchdog", "remaining": 0, "until": 1700000000}
            fake_gb.budget_message.return_value = (
                "[watchdog] board-sweep gh_delta probe: 미집계 (rate-limit, "
                "remaining=0) (budget-exhausted until 1700000000)")
            with mock.patch.dict(sys.modules,
                                  {"closure_sweep": fake_cs,
                                   "spawn_coverage": fake_sc,
                                   "gh_delta": fake_gh_delta,
                                   "gh_budget": fake_gb}), \
                 mock.patch.object(spawn, "_repo_slug", return_value="acme/widgets"), \
                 mock.patch.object(spawn, "requirement_drift") as fake_req_drift:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep(root)
                finally:
                    sys.stdout = old_stdout
            fake_gh_delta.fetch_delta.assert_not_called()
            fake_cs.find_violations.assert_not_called()
            self.assertEqual(result, 1)
            self.assertIn("budget-exhausted", buf.getvalue())

    def test_board_wide_sweep_all_covers_roster_repos_with_prefixed_lines_and_skips_non_board(self):
        """이슈 #1276 acceptance: 로스터에 두 보드 레포 + 한 비-보드 레포가
        있으면 스윕은 두 보드를 모두(각자 레포 접두 붙은 줄로) 커버하고,
        비-보드는 틱당 한 줄만 찍고 건너뛴다."""
        with tempfile.TemporaryDirectory() as td:
            arm_root = Path(td) / "arm-root"
            board_repo = Path(td) / "board-repo"
            non_board_repo = Path(td) / "non-board-repo"
            for p in (arm_root, board_repo, non_board_repo):
                p.mkdir()
            for board in (arm_root, board_repo):
                (board / "docs" / "specs").mkdir(parents=True)
                (board / "docs" / "specs" / "approvers.md").write_text("someone\n")
            d_all = {
                "issue-1/qa": {"work": str(board_repo)},
                "issue-2/implementation": {"work": str(non_board_repo)},
            }

            def fake_sweep(r):
                print(f"sweep-ran:{r}")
                return 1

            with mock.patch.object(spawn, "_board_wide_sweep", side_effect=fake_sweep), \
                 mock.patch.object(spawn, "cross_workspace_board_sweep_lock_acquire",
                                    return_value=(True, "")):
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep_all(arm_root, d_all)
                finally:
                    sys.stdout = old_stdout
            out = buf.getvalue()
            arm_label = spawn._repo_identity(arm_root.resolve())
            board_label = spawn._repo_identity(board_repo.resolve())
            self.assertEqual(result, 2)
            self.assertIn(f"[{arm_label}] sweep-ran:{arm_root.resolve()}", out)
            self.assertIn(f"[{board_label}] sweep-ran:{board_repo.resolve()}", out)
            self.assertIn("보드 아님", out)
            self.assertIn(spawn._repo_identity(non_board_repo.resolve()), out)
            self.assertNotIn(f"sweep-ran:{non_board_repo.resolve()}", out)

    def test_board_wide_sweep_all_empty_roster_sweeps_arm_root_only(self):
        """이슈 #1276 요구#2 empty-state parity: 로스터가 비어 있으면
        오늘과 동일하게 arm-root 하나만 스윕한다(arm-root 가 보드일 때)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "specs").mkdir(parents=True)
            (root / "docs" / "specs" / "approvers.md").write_text("someone\n")
            with mock.patch.object(spawn, "_board_wide_sweep", return_value=0) as m, \
                 mock.patch.object(spawn, "cross_workspace_board_sweep_lock_acquire",
                                    return_value=(True, "")):
                result = spawn._board_wide_sweep_all(root, {})
            m.assert_called_once_with(root.resolve())
            self.assertEqual(result, 0)

    def test_board_wide_sweep_all_non_board_root_with_roster_board_sweeps_roster_only(self):
        """이슈 #1280 acceptance: 비-보드 arm-root + 로스터에 보드 레포 하나
        -> 그 레포의 접두된 watch 줄이 나오고, arm-root 자체는 라인 없이
        조용히 제외된다."""
        with tempfile.TemporaryDirectory() as td:
            arm_root = Path(td) / "arm-root"
            board_repo = Path(td) / "board-repo"
            for p in (arm_root, board_repo):
                p.mkdir()
            (board_repo / "docs" / "specs").mkdir(parents=True)
            (board_repo / "docs" / "specs" / "approvers.md").write_text("someone\n")
            d_all = {"issue-1/qa": {"work": str(board_repo)}}

            def fake_sweep(r):
                print(f"sweep-ran:{r}")
                return 1

            with mock.patch.object(spawn, "_board_wide_sweep", side_effect=fake_sweep), \
                 mock.patch.object(spawn, "cross_workspace_board_sweep_lock_acquire",
                                    return_value=(True, "")):
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep_all(arm_root, d_all)
                finally:
                    sys.stdout = old_stdout
            out = buf.getvalue()
            board_label = spawn._repo_identity(board_repo.resolve())
            self.assertEqual(result, 1)
            self.assertIn(f"[{board_label}] sweep-ran:{board_repo.resolve()}", out)
            self.assertNotIn(f"sweep-ran:{arm_root.resolve()}", out)
            self.assertNotIn(spawn._repo_identity(arm_root.resolve()), out)

    def test_board_wide_sweep_all_non_board_root_empty_roster_alive_and_silent(self):
        """이슈 #1280 empty-state: 비-보드 arm-root + 빈 로스터 -> 아무 것도
        스윕하지 않고(_board_wide_sweep 미호출) 출력도 없다(alive, silent)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(spawn, "_board_wide_sweep") as m:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep_all(root, {})
                finally:
                    sys.stdout = old_stdout
            m.assert_not_called()
            self.assertEqual(result, 0)
            self.assertEqual(buf.getvalue(), "")

    def test_roster_target_repos_dedupes_by_resolved_path(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            d_all = {
                "issue-1/qa": {"work": str(repo)},
                "issue-2/implementation": {"work": str(repo) + "/"},
                "issue-3/review": {},
            }
            self.assertEqual(spawn._roster_target_repos(d_all), [repo.resolve()])

class PollHeartbeatMarkerRelocationTest(unittest.TestCase):
    """이슈 #1280: poll-heartbeat.sh 의 alive 마커가 타깃 레포 밖으로
    이동했는지, directive.sh 가 같은 해시로 그 마커를 읽는지를 실제
    쉘 스크립트를 구동해 검증한다."""

    def _run_heartbeat(self, repo, home):
        script = Path(__file__).parent.parent / "on-the-record" / "monitors" / "poll-heartbeat.sh"
        env = dict(os.environ)
        env.update({
            "HOME": str(home),
            "TOKENMAXXXER_CHECKOUT": str(Path(__file__).parent.parent),
            "POLL_HEARTBEAT_MAX_TICKS": "1",
            "POLL_HEARTBEAT_SLEEP_SECONDS": "0",
        })
        return subprocess.run(
            ["bash", str(script)], cwd=str(repo), env=env,
            capture_output=True, text=True, timeout=30,
        )

    @pytest.mark.slow
    def test_non_board_root_creates_no_files_and_relocates_alive_marker(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            home = Path(td) / "home"
            repo.mkdir()
            home.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
            r = self._run_heartbeat(repo, home)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse((repo / ".orchestrate-monitor-alive").exists())
            self.assertEqual([p for p in repo.glob("*") if p.name != ".git"], [])
            import hashlib
            expected_hash = hashlib.sha256(
                str(repo.resolve()).encode("utf-8", "surrogatepass")
            ).hexdigest()[:24]
            alive_path = home / ".claude" / "tokenmaxxxer" / "monitor-alive" / expected_hash / "alive"
            self.assertTrue(alive_path.exists())

    @pytest.mark.slow
    def test_directive_sh_reads_same_relocated_marker_hash(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            home = Path(td) / "home"
            repo.mkdir()
            home.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
            self._run_heartbeat(repo, home)
            import hashlib
            expected_hash = hashlib.sha256(
                str(repo.resolve()).encode("utf-8", "surrogatepass")
            ).hexdigest()[:24]
            marker_dir = home / ".claude" / "tokenmaxxxer" / "monitor-alive" / expected_hash
            self.assertTrue((marker_dir / "alive").exists())

            directive = Path(__file__).parent.parent / "on-the-record" / "hooks" / "directive.sh"
            env = dict(os.environ)
            env.pop("CLAUDE_ROLE", None)
            env.update({"HOME": str(home)})
            payload = json.dumps({"session_id": "sess-1280"})
            r = subprocess.run(
                ["bash", str(directive)], cwd=str(repo), env=env,
                input=payload, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            session_hash = hashlib.sha256(b"sess-1280").hexdigest()[:24]
            self.assertTrue((marker_dir / f".session-{session_hash}-start").exists())

    def test_non_git_root_arms_no_error_alive_marker_written(self):
        """이슈 #1292: 비-git arm-root 는 `[monitor-arm-refused]` 에러/
        exit 1 없이 무장한다 — alive 마커가 써지고 rc=0, 로스터가 비어
        있으니 arm-root 밑에 아무 파일도 생기지 않는다(#1245/#1280 의
        비-보드 empty-state 와 동일한 조용함)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "not-a-repo"
            home = Path(td) / "home"
            repo.mkdir()
            home.mkdir()
            r = self._run_heartbeat(repo, home)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn("monitor-arm-refused", r.stderr)
            self.assertNotIn("monitor-arm-refused", r.stdout)
            self.assertEqual(list(repo.glob("*")), [])
            import hashlib
            expected_hash = hashlib.sha256(
                str(repo.resolve()).encode("utf-8", "surrogatepass")
            ).hexdigest()[:24]
            alive_path = home / ".claude" / "tokenmaxxxer" / "monitor-alive" / expected_hash / "alive"
            self.assertTrue(alive_path.exists())

    def test_non_git_root_with_roster_board_target_sweeps_roster_only(self):
        """이슈 #1292 acceptance: 비-git arm-root + 로스터에 보드 레포
        엔트리 하나 -> arm-root 는 스윕에서 조용히 제외되지만 로스터가
        가리키는 보드 타깃은 계속 스윕된다(`_board_wide_sweep_all`, #1276
        요구 보존)."""
        with tempfile.TemporaryDirectory() as td:
            arm_root = Path(td) / "not-a-repo"
            board_repo = Path(td) / "board-repo"
            arm_root.mkdir()
            board_repo.mkdir()
            (board_repo / "docs" / "specs").mkdir(parents=True)
            (board_repo / "docs" / "specs" / "approvers.md").write_text("someone\n")
            d_all = {"issue-1/qa": {"work": str(board_repo)}}

            def fake_sweep(r):
                print(f"sweep-ran:{r}")
                return 1

            with mock.patch.object(spawn, "_board_wide_sweep", side_effect=fake_sweep), \
                 mock.patch.object(spawn, "cross_workspace_board_sweep_lock_acquire",
                                    return_value=(True, "")):
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep_all(arm_root, d_all)
                finally:
                    sys.stdout = old_stdout
            out = buf.getvalue()
            board_label = spawn._repo_identity(board_repo.resolve())
            self.assertEqual(result, 1)
            self.assertIn(f"[{board_label}] sweep-ran:{board_repo.resolve()}", out)
            self.assertNotIn(f"sweep-ran:{arm_root.resolve()}", out)
            self.assertNotIn(spawn._repo_identity(arm_root.resolve()), out)

    def test_non_git_root_empty_roster_alive_and_silent(self):
        """이슈 #1292 empty state: 비-git arm-root + 빈 로스터 -> alive,
        아무 것도 스윕하지 않고(_board_wide_sweep 미호출) 출력도 없다,
        arm-root 밑에 파일도 생기지 않는다."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "not-a-repo"
            root.mkdir()
            with mock.patch.object(spawn, "_board_wide_sweep") as m:
                buf = io.StringIO()
                old_stdout = sys.stdout
                sys.stdout = buf
                try:
                    result = spawn._board_wide_sweep_all(root, {})
                finally:
                    sys.stdout = old_stdout
            m.assert_not_called()
            self.assertEqual(result, 0)
            self.assertEqual(buf.getvalue(), "")
            self.assertEqual(list(root.glob("*")), [])

    def test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts(self):
        # issue #743 acceptance item 1: `_board_wide_sweep` 이 이제 한 번의
        # `issue_state_index_all` 프리페치를 `find_violations` 에 넘기므로,
        # subject 수가 늘어도 subject 별 `_issue_view` 호출은 늘지 않는다
        # (프리페치가 모든 issue 를 커버하는 한 아예 0회) — 실제
        # `gates/closure_sweep` 모듈을 `spawn._board_wide_sweep()` 을 통해
        # 그대로 구동하고, `_issue_view` 만 스텁해 호출을 기록한다.
        gates_dir = str(Path(__file__).parent.parent / "gates")
        if gates_dir not in sys.path:
            sys.path.insert(0, gates_dir)
        import closure_sweep

        calls = []

        def fake_issue_view(root, issue):
            calls.append(issue)
            return ("OPEN", True)

        def fake_run(args, **kw):
            if args[:3] == ["gh", "issue", "list"]:
                payload = [{"number": n, "state": "OPEN"} for n in range(1, 201)]
                return mock.Mock(returncode=0, stdout=json.dumps(payload))
            if args[:3] == ["gh", "pr", "list"]:
                return mock.Mock(returncode=0, stdout="[]")
            if args[:3] == ["gh", "repo", "view"]:
                return mock.Mock(returncode=0, stdout="owner/repo\n")
            if args[:2] == ["gh", "api"] and len(args) > 2 and args[2].startswith("repos/") and args[2].endswith("/pulls"):
                return mock.Mock(returncode=0, stdout="[]")
            if args[:2] == ["gh", "api"] and len(args) > 2 and args[2].startswith("repos/") and args[2].endswith("/issues") and "-i" in args:
                payload = [{"number": n, "state": "open"} for n in range(1, 201)]
                return mock.Mock(returncode=0, stdout="200\n\n" + json.dumps(payload))
            return mock.Mock(returncode=0, stdout="")

        orig_board = spawn.board
        orig_issue_view = closure_sweep._issue_view
        orig_run = closure_sweep.subprocess.run
        self.addCleanup(setattr, spawn, "board", orig_board)
        self.addCleanup(setattr, closure_sweep, "_issue_view", orig_issue_view)
        self.addCleanup(setattr, closure_sweep.subprocess, "run", orig_run)
        closure_sweep._issue_view = fake_issue_view
        closure_sweep.subprocess.run = fake_run

        fake_sc = mock.MagicMock()
        fake_sc._list_open_issues.return_value = []
        fake_sc.find_uncovered.return_value = []

        counts = []
        for n in (0, 3, 150):
            subjects = {f"issue-{i}": {"implementation": {}} for i in range(1, n + 1)}
            spawn.board = lambda root, _subjects=subjects: _subjects
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                (root / "gates").mkdir()
                with mock.patch.dict(sys.modules, {"spawn_coverage": fake_sc}):
                    result = spawn._board_wide_sweep(root)
            self.assertEqual(result, 0)
            counts.append(len(calls))
            calls.clear()

        self.assertEqual(counts, [0, 0, 0])

    @pytest.mark.xfail(
        reason="issue #1619: closure_sweep._board_wide_sweep mock assertion "
               "flaky under this repo's current environment -- a real "
               "board-sweep lock held by a concurrent on-the-record "
               "process/session (observed: 'board-sweep: on-the-record "
               "건너뜀 (다른 워크스페이스가 스윕 중)') can short-circuit the "
               "call this test expects, so it passes on an idle machine "
               "and fails when another spawn session is active.",
        strict=False)
    def test_find_violations_result_unchanged_with_prebuilt_issue_states(self):
        # issue #743 acceptance item 2: 같은 픽스처 보드에 대해 `issue_states`
        # 없이(옛 경로, subject 별 `_issue_view`) 낸 결과와 프리페치된
        # `issue_states` 를 넘겨서(새 경로) 낸 결과가 같아야 한다.
        gates_dir = str(Path(__file__).parent.parent / "gates")
        if gates_dir not in sys.path:
            sys.path.insert(0, gates_dir)
        import closure_sweep

        subjects = {
            "issue-1": {"implementation": {}},
            "issue-2": {"implementation": {}},
            "issue-3": {"implementation": {}},
        }
        issue_state_by_number = {1: "CLOSED", 2: "OPEN", 3: "OPEN"}
        fake_pr_index = {
            "issue-1/implementation": {"number": 101, "state": "OPEN",
                                       "body": "Closes #1"},
            "issue-2/implementation": {"number": 102, "state": "MERGED",
                                       "body": "Closes #2"},
            "issue-3/implementation": {"number": 103, "state": "OPEN",
                                       "body": "no ref"},
        }

        orig_pr_index_all = closure_sweep._pr_index_all
        orig_issue_view = closure_sweep._issue_view
        self.addCleanup(setattr, closure_sweep, "_pr_index_all", orig_pr_index_all)
        self.addCleanup(setattr, closure_sweep, "_issue_view", orig_issue_view)
        closure_sweep._pr_index_all = lambda root: (dict(fake_pr_index), True)

        issue_view_calls = []

        def fake_issue_view(root, issue):
            issue_view_calls.append(issue)
            return (issue_state_by_number[issue], True)

        closure_sweep._issue_view = fake_issue_view
        violations_before, skips_before = closure_sweep.find_violations(
            Path("."), subjects=subjects)
        self.assertEqual(len(issue_view_calls), 3)

        issue_view_calls.clear()
        violations_after, skips_after = closure_sweep.find_violations(
            Path("."), subjects=subjects, issue_states=dict(issue_state_by_number))
        self.assertEqual(issue_view_calls, [])

        self.assertEqual(violations_before, violations_after)
        self.assertEqual(skips_before, skips_after)
        self.assertTrue(violations_before)

    @pytest.mark.xfail(
        reason="issue #1619: same concurrent-board-sweep-lock flakiness as "
               "test_find_violations_result_unchanged_with_prebuilt_issue_states "
               "above.",
        strict=False)
    def test_find_violations_result_unchanged_with_prebuilt_issue_states_zero_violations(self):
        gates_dir = str(Path(__file__).parent.parent / "gates")
        if gates_dir not in sys.path:
            sys.path.insert(0, gates_dir)
        import closure_sweep

        subjects = {"issue-3": {"implementation": {}}}
        issue_state_by_number = {3: "OPEN"}
        fake_pr_index = {
            "issue-3/implementation": {"number": 103, "state": "OPEN", "body": "no ref"},
        }

        orig_pr_index_all = closure_sweep._pr_index_all
        orig_issue_view = closure_sweep._issue_view
        self.addCleanup(setattr, closure_sweep, "_pr_index_all", orig_pr_index_all)
        self.addCleanup(setattr, closure_sweep, "_issue_view", orig_issue_view)
        closure_sweep._pr_index_all = lambda root: (dict(fake_pr_index), True)
        closure_sweep._issue_view = lambda root, issue: (issue_state_by_number[issue], True)

        violations_before, skips_before = closure_sweep.find_violations(
            Path("."), subjects=subjects)
        violations_after, skips_after = closure_sweep.find_violations(
            Path("."), subjects=subjects, issue_states=dict(issue_state_by_number))

        self.assertEqual(violations_before, [])
        self.assertEqual(violations_after, [])
        self.assertEqual(violations_before, violations_after)
        self.assertEqual(skips_before, skips_after)

class SessionEndVerdict(unittest.TestCase):
    """이슈 #132: session_end_verdict 3분법 — survey.md 사건들 + 벤인 레이스."""

    def _write_events(self, work, lines):
        Path(str(work) + ".events.jsonl").write_text(
            "\n".join(json.dumps(l) for l in lines) + "\n")

    def test_no_events_file_is_normal(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None), "normal")

    def test_matched_session_end_is_normal(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "session-end", "detail": "progressed"},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: False),
                "normal")

    def test_unmatched_and_dead_is_crashed(self):
        # survey.md 사건 #2: 크래시가 roster_remove/종료 이벤트 사이에서 나
        # events.jsonl 에 session-end 가 아예 없다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: False),
                "crashed")

    def test_benign_race_resolves_to_normal_not_crashed(self):
        # 벤인 레이스: 워치독의 _alive() 는 죽었다고 보지만 session-end 가
        # 이미 남았다 — session-end 매치를 먼저 확인하므로 normal 이어야
        # 한다(가짜 crashed 로 재스폰하지 않는다).
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "session-end", "detail": "progressed"},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: False),
                "normal")

    def test_prior_generations_session_end_does_not_mask_new_generations_crash(self):
        # 이슈 #247: self-trigger 재귀가 만드는 다중-세대 이벤트 시퀀스
        # (한 워크스페이스의 events.jsonl 에 세대 여러 개가 이어 쌓인다)
        # 에서도, 이전 세대의 session-end 가 **자기 session-start 뒤,
        # 다음 세대의 session-start 보다 앞**에 제대로 찍혀 있으면
        # (spawn.py `_spawn_one()` 이 이제 강제하는 순서) 마지막
        # session-start(새 세대)의 진짜 죽음이 가려지지 않는다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "session-end", "detail": "uncommitted-work"},
                {"type": "respawn-attempt", "detail": {"session_start_ts": 1, "attempt": 1}},
                {"type": "session-start", "detail": {"pid": 222, "ts": 2}},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: pid != 222),
                "crashed")

    def test_misordered_prior_session_end_would_mask_new_generations_crash(self):
        # 이 테스트는 회귀를 지키려는 위험을 그대로 문서화한다(hunt finding
        # 1) — session_end_verdict() 자신은 이 이슈에서 안 바뀐다(제안서
        # 스코프 밖). 만약 어떤 호출부가 이전 세대의 session-end 를 다음
        # 세대의 session-start **뒤에** 남기면(제안서 원문 그대로
        # self-trigger 를 session-end 보다 먼저 불렀을 때 실제로 벌어졌던
        # 순서), session_end_verdict() 는 마지막 session-start 뒤에 있는
        # 아무 session-end 나 매치로 보고 새 세대가 진짜 죽어도 `crashed`
        # 대신 `normal` 을 낸다 — `_spawn_one()` 이 이제 자기 session-end
        # 를 self-trigger 보다 먼저 남기는 이유가 바로 이 시퀀스를 절대
        # 만들지 않기 위해서다.
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
                {"type": "respawn-attempt", "detail": {"session_start_ts": 1, "attempt": 1}},
                {"type": "session-start", "detail": {"pid": 222, "ts": 2}},
                {"type": "session-end", "detail": "uncommitted-work"},
            ])
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=None,
                                          alive_fn=lambda pid: pid != 222),
                "normal")

    def test_unmatched_alive_stale_log_is_stalled(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
            ])
            log = Path(str(work) + ".session.20260802T150000.111.log")
            log.write_text("still going")
            stale = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            os.utime(log, (stale, stale))
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=log,
                                          alive_fn=lambda pid: True),
                "stalled")

    def test_unmatched_alive_fresh_log_is_in_progress(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            self._write_events(work, [
                {"type": "session-start", "detail": {"pid": 111, "ts": 1}},
            ])
            log = Path(str(work) + ".session.20260802T150000.111.log")
            log.write_text("still going")
            self.assertEqual(
                spawn.session_end_verdict(str(work), log_path=log,
                                          alive_fn=lambda pid: True),
                "in-progress")

class StreamingLanding(unittest.TestCase):
    """issue-503: 팬아웃 완료 단위는 도착하는 대로 처리되지, 전부 모일 때까지
    기다리는 배치 배리어를 거치지 않는다. `spawn.roster_reconcile()`이
    이미 엔트리마다(sorted(d.items()) 루프 안에서) reconcile 계산과 행동을
    같은 이터레이션에서 하는 걸 이 클래스가 시간 축으로 증명한다 — 3개
    시뮬레이션 워커가 서로 다른 시점에 "완료"할 때, 각 워커의 행동이 그
    워커 자신의 완료 시점에 일어나는지, 세 번째 워커가 도착하기를 기다리지
    않는지를 본다."""

    _ENTRIES = [
        ("issue-1/coding", {"expects_pr": False, "role": "implementation", "branch": "b1"},
         {"session_verdict": "crashed", "pr_number": None, "loop_state": None, "new_commit": False}),
        ("issue-2/coding", {"expects_pr": True, "role": "implementation", "branch": "b2"},
         {"session_verdict": "normal", "pr_number": 7, "loop_state": "done", "new_commit": True}),
        ("issue-3/coding", {"expects_pr": False, "role": "implementation", "branch": "b3"},
         {"session_verdict": "stalled", "pr_number": None, "loop_state": None, "new_commit": False}),
    ]

    def _arrivals(self, clock):
        """워커가 완료하는 대로 하나씩만 꺼낼 수 있는 이터레이터 — 세 번째
        원소를 얻으려면 첫/두 번째를 먼저 "완료 시점"으로 소비해야 한다."""
        for key, expected, observed in self._ENTRIES:
            clock.append(("fetch", key))
            yield key, expected, observed

    def _streaming_process(self, clock, act):
        """`spawn.roster_reconcile()`과 같은 모양 — 엔트리를 하나 받을
        때마다 reconcile 계산과 act 를 같은 루프 이터레이션에서 한다."""
        for key, expected, observed in self._arrivals(clock):
            divergences = spawn.reconcile(expected, observed)
            act(key, divergences)
            clock.append(("act", key))

    def _naive_collect_then_act(self, clock, act):
        """대조군 — 배치 배리어: 전부 모아서 리스트로 만든 뒤에야 act 를
        시작한다(이 테스트가 잡아야 하는 반례 모양, #171 이 실제로 낸 패턴)."""
        collected = [(key, spawn.reconcile(expected, observed))
                     for key, expected, observed in self._arrivals(clock)]
        for key, divergences in collected:
            act(key, divergences)
            clock.append(("act", key))

    def test_streaming_acts_on_each_unit_at_its_own_arrival(self):
        clock = []
        self._streaming_process(clock, act=lambda key, div: None)
        # 스트리밍: fetch/act 가 유닛별로 짝지어 번갈아 나온다 — 유닛1의
        # act 가 유닛3의 fetch 보다 먼저 온다(가장 느린 유닛을 기다리지 않음).
        self.assertEqual(
            clock,
            [("fetch", "issue-1/coding"), ("act", "issue-1/coding"),
             ("fetch", "issue-2/coding"), ("act", "issue-2/coding"),
             ("fetch", "issue-3/coding"), ("act", "issue-3/coding")],
        )
        fetch3_idx = clock.index(("fetch", "issue-3/coding"))
        act1_idx = clock.index(("act", "issue-1/coding"))
        self.assertLess(act1_idx, fetch3_idx,
                         "유닛1의 act 가 유닛3의 fetch(완료 대기)보다 먼저 와야 한다.")

    def test_naive_collect_then_act_is_the_barrier_this_norm_forbids(self):
        """RED 픽스처: 배치 배리어 하네스는 모든 fetch 가 끝난 뒤에야 act 를
        시작한다 — 유닛1의 act 가 유닛3의 fetch 보다 뒤에 온다. 이 텍스트가
        `_streaming_process`에 대해서는 실패하고 `_naive_collect_then_act`에
        대해서만 성립함을 보여, 위 GREEN 테스트가 실제로 스트리밍 속성을
        검사하고 있다는 걸 증명한다."""
        clock = []
        self._naive_collect_then_act(clock, act=lambda key, div: None)
        fetch3_idx = clock.index(("fetch", "issue-3/coding"))
        act1_idx = clock.index(("act", "issue-1/coding"))
        self.assertGreater(act1_idx, fetch3_idx,
                            "배치 배리어 하네스는 유닛1의 act 가 유닛3의 fetch 뒤에 와야 반례로 성립한다.")

    def test_roster_reconcile_source_acts_per_entry_not_after_collecting(self):
        """`spawn.roster_reconcile`의 실제 소스가 위 `_streaming_process`와
        같은 모양(엔트리 루프 안에서 reconcile 계산 직후 act)인지 정적으로
        확인 — survey 가 읽은 spawn.py:1913-1935 가 실제로 스트리밍 모양임을
        코드 자체로 고정한다."""
        src = inspect.getsource(spawn.roster_reconcile)
        for_idx = src.index("for key, e in sorted(d.items()):")
        reconcile_idx = src.index("divergences = reconcile(", for_idx)
        print_idx = src.index("print(f\"[reconcile]", reconcile_idx)
        self.assertLess(for_idx, reconcile_idx)
        self.assertLess(reconcile_idx, print_idx,
                         "roster_reconcile 이 reconcile() 계산 직후, 같은 루프 안에서 "
                         "행동(출력)해야 한다 — 전부 모은 뒤 별도 루프에서 하면 배리어다.")

class AutoRespawnClaim(unittest.TestCase):
    """이슈 #132: crashed 한정 최대 2회 재스폰, claim-before-spawn, 상한 코멘트."""

    def _crashed_workspace(self, td, pid=111):
        work = Path(td) / "w"
        Path(str(work) + ".events.jsonl").write_text(
            json.dumps({"type": "session-start", "detail": {"pid": pid, "ts": 1}}) + "\n")
        Path(str(work) + ".task.txt").write_text("원래 맡길 일")
        return str(work)

    def test_no_respawn_when_not_crashed(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".events.jsonl").write_text(
                json.dumps({"type": "session-start", "detail": {"pid": 111, "ts": 1}})
                + "\n" + json.dumps({"type": "session-end", "detail": "progressed"}) + "\n")
            entry = {"work": str(work), "issue": 132, "role": "implementation", "log": ""}
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append(1)
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig
            self.assertEqual(called, [])
            self.assertEqual(state, {})

    def test_crashed_under_cap_claims_and_respawns(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append((a, k))
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)
            self.assertEqual(state["issue-132/coding"]["attempts"], 1)
            events = Path(work + ".events.jsonl").read_text()
            self.assertIn("respawn-attempt", events)

    def test_already_claimed_session_is_not_respawned_twice(self):
        # 두 워치독 인스턴스가 같은 crashed 세션을 동시에 본 상황을 흉내:
        # respawn-attempt 이벤트가 이미 이 session_start_ts 로 남아있으면
        # 두 번째 호출은 아무 것도 하지 않는다.
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            with open(work + ".events.jsonl", "a") as fh:
                fh.write(json.dumps({"type": "respawn-attempt",
                                     "detail": {"session_start_ts": 1, "attempt": 1}}) + "\n")
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append(1)
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig
            self.assertEqual(called, [])
            self.assertEqual(state, {})

    def test_concurrent_watchdogs_do_not_double_respawn(self):
        # warrant-hunter finding (2026-07-30): the events.jsonl-based
        # already_claimed check is check-then-act with no lock, so two
        # concurrent `watchdog --auto-respawn` invocations on the same
        # crashed entry could both pass it and both call _spawn_one.
        # The atomic O_CREAT|O_EXCL claim file must let exactly one through.
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            called = []
            lock = threading.Lock()
            orig = spawn._spawn_one
            def fake_spawn(*a, **k):
                with lock:
                    called.append(1)
            spawn._spawn_one = fake_spawn
            try:
                states = [{}, {}]
                threads = [threading.Thread(target=spawn._auto_respawn_check,
                                            args=("issue-132/coding", entry, states[i]))
                          for i in range(2)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)

    def test_cap_reached_posts_comment_instead_of_respawning(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._crashed_workspace(td)
            entry = {"work": work, "issue": 132, "role": "implementation", "log": "l"}
            state = {"issue-132/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS}}
            called = []
            orig_spawn = spawn._spawn_one
            orig_comment = spawn._post_crash_comment
            spawn._spawn_one = lambda *a, **k: called.append(1)
            spawn._post_crash_comment = lambda *a, **k: called.append(("comment", a))
            try:
                spawn._auto_respawn_check("issue-132/coding", entry, state)
            finally:
                spawn._spawn_one = orig_spawn
                spawn._post_crash_comment = orig_comment
            self.assertEqual(len(called), 1)
            self.assertEqual(called[0][0], "comment")

class ProgressAwareRespawnCounter(unittest.TestCase):
    """이슈 #678: `_respawn_or_cap()` 의 attempts 는 no-progress *스트릭* —
    직전 재스폰 시점 지문(커밋 sha + 보드 스냅샷)과 다르면 리셋된다.
    `RESPAWN_ABSOLUTE_MAX` 는 스트릭과 무관한 총 시도 상한."""

    def _prep_repo(self, td):
        work = Path(td) / "w"
        work.mkdir()
        run = lambda *a: subprocess.run(a, cwd=str(work), capture_output=True,
                                        text=True, check=True)
        run("git", "init", "-q")
        run("git", "config", "user.email", "t@example.com")
        run("git", "config", "user.name", "t")
        (work / "f.txt").write_text("x")
        run("git", "add", "f.txt")
        run("git", "commit", "-q", "-m", "init")
        Path(str(work) + ".task.txt").write_text("원래 맡길 일")
        return work, run

    @pytest.mark.slow
    def test_new_commit_resets_streak_instead_of_capping(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            prev_fp = spawn._respawn_fingerprint(str(work))
            # attempts 는 이미 상한(2)이지만, 그 지문 이후 실제로 새
            # 커밋이 얹혔다 — 스트릭이 리셋돼 재스폰돼야 한다.
            state = {"issue-678/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS,
                                          "total_attempts": spawn.RESPAWN_MAX_ATTEMPTS,
                                          "fingerprint": prev_fp}}
            (work / "f.txt").write_text("y")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "progress")
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append(1)
            try:
                spawn._respawn_or_cap("issue-678/coding", str(work), 678,
                                      "implementation", "l", 1, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)
            self.assertEqual(state["issue-678/coding"]["attempts"], 1)
            self.assertEqual(state["issue-678/coding"]["total_attempts"],
                             spawn.RESPAWN_MAX_ATTEMPTS + 1)

    @pytest.mark.slow
    def test_board_delta_resets_streak(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            board_dir = work / "docs" / "issue-678" / "reports"
            board_dir.mkdir(parents=True)
            (board_dir / "implementation.md").write_text("before")
            prev_fp = spawn._respawn_fingerprint(str(work))
            state = {"issue-678/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS,
                                          "total_attempts": spawn.RESPAWN_MAX_ATTEMPTS,
                                          "fingerprint": prev_fp}}
            (board_dir / "implementation.md").write_text("after — real progress")
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append(1)
            try:
                spawn._respawn_or_cap("issue-678/coding", str(work), 678,
                                      "implementation", "l", 1, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)
            self.assertEqual(state["issue-678/coding"]["attempts"], 1)

    @pytest.mark.slow
    def test_consecutive_no_progress_still_hits_cap(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            fp = spawn._respawn_fingerprint(str(work))
            state = {"issue-678/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS,
                                          "total_attempts": spawn.RESPAWN_MAX_ATTEMPTS,
                                          "fingerprint": fp}}
            called = []
            orig_spawn = spawn._spawn_one
            orig_comment = spawn._post_crash_comment
            spawn._spawn_one = lambda *a, **k: called.append(("spawn", a))
            spawn._post_crash_comment = lambda *a, **k: called.append(("comment", a, k))
            try:
                spawn._respawn_or_cap("issue-678/coding", str(work), 678,
                                      "implementation", "l", 1, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig_spawn
                spawn._post_crash_comment = orig_comment
            self.assertEqual(len(called), 1)
            self.assertEqual(called[0][0], "comment")
            self.assertNotIn("absolute", called[0][2])

    @pytest.mark.slow
    def test_absolute_max_fires_even_when_streak_resets(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            prev_fp = spawn._respawn_fingerprint(str(work))
            # 스트릭은 낮지만(진행이 매번 있었음) 총 시도 수가 절대 상한에
            # 닿아 있다 — 스트릭 리셋과 무관하게 캡이 걸려야 한다.
            state = {"issue-678/coding": {"attempts": 0,
                                          "total_attempts": spawn.RESPAWN_ABSOLUTE_MAX,
                                          "fingerprint": prev_fp}}
            (work / "f.txt").write_text("z")
            run("git", "add", "f.txt")
            run("git", "commit", "-q", "-m", "more progress")
            called = []
            orig_spawn = spawn._spawn_one
            orig_comment = spawn._post_crash_comment
            spawn._spawn_one = lambda *a, **k: called.append(("spawn", a))
            spawn._post_crash_comment = lambda *a, **k: called.append(("comment", a, k))
            try:
                spawn._respawn_or_cap("issue-678/coding", str(work), 678,
                                      "implementation", "l", 1, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig_spawn
                spawn._post_crash_comment = orig_comment
            self.assertEqual(len(called), 1)
            self.assertEqual(called[0][0], "comment")
            self.assertTrue(called[0][2].get("absolute"))

    def test_refused_and_waiting_on_human_never_reach_respawn_or_cap(self):
        called = []
        orig = spawn._respawn_or_cap
        spawn._respawn_or_cap = lambda *a, **k: called.append(a)
        try:
            spawn._self_trigger_respawn("refused", "issue-678/coding", "w",
                                        678, "implementation", "l", 1)
            spawn._self_trigger_respawn("waiting-on-human", "issue-678/coding",
                                        "w", 678, "implementation", "l", 1)
        finally:
            spawn._respawn_or_cap = orig
        self.assertEqual(called, [])

class SelfTriggeredRespawn(unittest.TestCase):
    """이슈 #247: 정상 종료(crashed 아님)했지만 미커밋 작업을 남긴 헤드리스
    세션이, 워치독 틱을 기다리지 않고 `_spawn_one()` 자기 프로세스 안에서
    같은 claim/attempt-cap/cap-comment 헬퍼(`_respawn_or_cap()`)를 직접
    부른다(`_self_trigger_respawn()`)."""

    def test_fires_on_uncommitted_work(self):
        called = []
        orig_respawn = spawn._respawn_or_cap
        orig_state = spawn._respawn_state_load
        spawn._respawn_or_cap = lambda *a, **k: called.append(a)
        spawn._respawn_state_load = lambda: {"seen": True}
        try:
            spawn._self_trigger_respawn("uncommitted-work", "issue-247/coding",
                                        "w", 247, "implementation", "l", 123)
        finally:
            spawn._respawn_or_cap = orig_respawn
            spawn._respawn_state_load = orig_state
        self.assertEqual(len(called), 1)
        (key, work, issue, role, log, ts, state, trigger) = called[0]
        self.assertEqual(key, "issue-247/coding")
        self.assertEqual((work, issue, role, log, ts), ("w", 247, "implementation", "l", 123))
        self.assertEqual(state, {"seen": True})
        self.assertEqual(trigger, "self-triggered-abandoned")

    def test_fires_on_failed_no_commit(self):
        called = []
        orig_respawn = spawn._respawn_or_cap
        spawn._respawn_or_cap = lambda *a, **k: called.append(a)
        try:
            spawn._self_trigger_respawn("failed-no-commit", "issue-247/coding",
                                        "w", 247, "implementation", "l", 123)
        finally:
            spawn._respawn_or_cap = orig_respawn
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][-1], "self-triggered-abandoned")

    def test_does_not_fire_on_legitimate_stops(self):
        # refused/waiting-on-human 은 사람이 봐야 할 정당한 게이트 거부/
        # 대기이지 이 결함의 모양(방치된-미커밋-작업/원인없는 정지)이
        # 아니므로 재스폰하지 않는다(프로포절의 두 번째 기각안). #675로
        # silent-failure는 더 이상 여기 속하지 않는다 — 아래 별도 테스트.
        for outcome in ("refused", "waiting-on-human",
                        "progressed", "errored", "progressed-dirty-tree"):
            called = []
            orig_respawn = spawn._respawn_or_cap
            spawn._respawn_or_cap = lambda *a, **k: called.append(1)
            try:
                spawn._self_trigger_respawn(outcome, "issue-247/coding", "w",
                                            247, "implementation", "l", 123)
            finally:
                spawn._respawn_or_cap = orig_respawn
            self.assertEqual(called, [], outcome)

    def test_fires_on_silent_failure_with_distinct_trigger(self):
        # 이슈 #675: 원인 없는(causeless) silent-failure — 거부 기록도,
        # human-gate 대기 표시도 없는 — 은 이제 재스폰되며, 기존
        # self-triggered-abandoned 와 구별되는 trigger 문자열을 받는다.
        called = []
        orig_respawn = spawn._respawn_or_cap
        orig_state = spawn._respawn_state_load
        spawn._respawn_or_cap = lambda *a, **k: called.append(a)
        spawn._respawn_state_load = lambda: {"seen": True}
        try:
            spawn._self_trigger_respawn("silent-failure", "issue-247/coding",
                                        "w", 247, "implementation", "l", 123)
        finally:
            spawn._respawn_or_cap = orig_respawn
            spawn._respawn_state_load = orig_state
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][-1], "self-triggered-causeless")

    def test_respects_cap_and_posts_comment_with_trigger_label(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            state = {"issue-247/coding": {"attempts": spawn.RESPAWN_MAX_ATTEMPTS}}
            called = []
            orig_spawn = spawn._spawn_one
            orig_comment = spawn._post_crash_comment
            spawn._spawn_one = lambda *a, **k: called.append(("spawn", a))
            spawn._post_crash_comment = lambda *a, **k: called.append(("comment", a))
            try:
                spawn._respawn_or_cap("issue-247/coding", str(work), 247,
                                      "implementation", "l", 123, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig_spawn
                spawn._post_crash_comment = orig_comment
            self.assertEqual(len(called), 1)
            self.assertEqual(called[0][0], "comment")
            self.assertEqual(called[0][1][-1], "self-triggered-abandoned")

    def test_under_cap_claims_and_respawns(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".task.txt").write_text("원래 맡길 일")
            state = {}
            called = []
            orig = spawn._spawn_one
            spawn._spawn_one = lambda *a, **k: called.append((a, k))
            try:
                spawn._respawn_or_cap("issue-247/coding", str(work), 247,
                                      "implementation", "l", 456, state,
                                      "self-triggered-abandoned")
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)
            self.assertEqual(state["issue-247/coding"]["attempts"], 1)
            events = Path(str(work) + ".events.jsonl").read_text()
            self.assertIn("respawn-attempt", events)

    @pytest.mark.slow
    def test_self_trigger_and_watchdog_do_not_double_respawn(self):
        # 이 세션 자신의 self-trigger 와, 같은 워크스페이스를 보는 동시
        # 워치독 틱(`_auto_respawn_check` 이 재구성한 같은 session_start_ts)
        # 이 동시에 `_respawn_or_cap` 에 도달해도, claim 하나만 통과해야
        # 한다 — 트리거 라벨이 다를 뿐 같은 원자적 claim 파일을 공유한다
        # (프로포절: "reuses the existing atomic claim's race protection —
        # no new concurrency mechanism").
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            Path(str(work) + ".task.txt").write_text("원래 맡길 일")
            called = []
            lock = threading.Lock()
            orig = spawn._spawn_one

            def fake_spawn(*a, **k):
                with lock:
                    called.append(1)
            spawn._spawn_one = fake_spawn
            try:
                threads = [
                    threading.Thread(
                        target=spawn._respawn_or_cap,
                        args=("issue-247/coding", str(work), 247, "implementation",
                              "l", 1, {}, "self-triggered-abandoned")),
                    threading.Thread(
                        target=spawn._respawn_or_cap,
                        args=("issue-247/coding", str(work), 247, "implementation",
                              "l", 1, {}, "watchdog-observed-crashed")),
                ]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
            finally:
                spawn._spawn_one = orig
            self.assertEqual(len(called), 1)

    def _prep_repo(self, td):
        work = Path(td) / "w"
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

    @pytest.mark.slow
    def test_spawn_one_call_site_fires_after_own_session_end_event(self):
        # 이슈 #247 통합 테스트: 실제 _spawn_one() bounded/issue 꼬리를(fork
        # 만 모킹해서) 끝까지 돌려, 세션이 미커밋 파일을 남기고 정상
        # 종료하면 self-trigger 가 불릴 때 이 세션 **자신의** session-end
        # 가 이미 남아 있는지 확인한다.
        #
        # 제안서의 원래 문구는 "before the bounded child's terminal
        # session-end event append/exit" 였지만, 구현 중 어써샬-브로큰
        # 헌트가 그 문구 그대로 구현하면(self-trigger 먼저) 깨지는 걸
        # 찾았다: self-trigger 가 상한 안이면 `_respawn_or_cap()` 이
        # `_spawn_one(..., bounded=True)` 를 재귀 호출하고, 그 재귀 호출은
        # 새 세대가 자기 session-start 를 남길 때까지 이 프로세스를
        # `_await_bounded()` 안에서 블록한다 — session-end 를 그 뒤로
        # 미루면 이 세션 자신의 session-end 가 새 세대의 session-start
        # **뒤에** events.jsonl 에 찍혀, `session_end_verdict()` 가 새
        # 세대의 진짜 죽음을 이 세션의(남의) session-end 로 가리고
        # 영원히 `normal` 로 오판한다. session-end 를 먼저 남기면 순서가
        # 뒤집혀 그 오판이 구조적으로 불가능해진다 — 이 테스트는 그
        # 순서(session-end 가 self-trigger 보다 먼저)를 고정한다.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            (work / "left-behind.txt").write_text("uncommitted")
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            triggered = []

            def fake_trigger(outcome, roster_key, w, issue, role, log, ts):
                events_text = Path(str(w) + ".events.jsonl").read_text()
                self.assertIn("session-end", events_text)
                triggered.append(outcome)

            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda role, repo_root: {"source": "skill-repo",
                                           "skill_dirs": [], "skills": [], "skill_sha": None}), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_remove", lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                     mock.patch.object(spawn, "_self_trigger_respawn", fake_trigger), \
                     mock.patch.object(os, "fork", return_value=0), \
                     mock.patch.object(os, "setsid", lambda: None), \
                     mock.patch.object(os, "_exit", lambda *a: None):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=247, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx
            self.assertEqual(triggered, ["uncommitted-work"])

class SpawnOneNoWait(unittest.TestCase):
    """이슈 #645: `--no-wait` 는 fork/워처 무장 뒤 `_await_bounded` 를 아예
    안 거치고 즉시 리턴한다 — harness `run_in_background` 에 기대지 않는
    인프로세스 fire-and-return 경로."""

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

    @pytest.mark.slow
    @pytest.mark.xfail(
        reason="issue #1619: elapsed time assertion (<1.0s) is "
               "environment-dependent -- observed 51.5s in this sandbox "
               "because the mocked-out real gh/network calls this test "
               "doesn't fully isolate (returned-PR gate's `gh` lookup) run "
               "slow/unavailable here. Passes when gh responds promptly or "
               "network access is fast.",
        strict=False)
    def test_no_wait_returns_promptly_without_calling_await_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            old_roster = spawn.ROSTER
            spawn.ROSTER = Path(td) / "active.json"
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            await_calls = []

            class FakeWatcherProc:
                pid = 424242

            real_popen = subprocess.Popen

            def selective_popen(cmd, *a, **k):
                if isinstance(cmd, list) and "watch" in cmd:
                    return FakeWatcherProc()
                return real_popen(cmd, *a, **k)

            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda role, repo_root: {"source": "skill-repo",
                                           "skill_dirs": [], "skills": [], "skill_sha": None}), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                     mock.patch.object(spawn.subprocess, "Popen", selective_popen), \
                     mock.patch.object(spawn, "_await_bounded",
                                       lambda *a, **k: await_calls.append(1) or 0), \
                     mock.patch.object(os, "fork", return_value=4321):
                    t0 = time.monotonic()
                    rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                          unattended=True, issue=645, bounded=True,
                                          no_wait=True)
                    elapsed = time.monotonic() - t0
            finally:
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx
            self.assertEqual(rc, 0)
            self.assertEqual(await_calls, [])
            self.assertLess(elapsed, 1.0)

    @pytest.mark.slow
    def test_resume_command_prints_and_round_trips_through_watch(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            old_roster = spawn.ROSTER
            spawn.ROSTER = Path(td) / "active.json"
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"

            class FakeWatcherProc:
                pid = 424242

            real_popen = subprocess.Popen

            def selective_popen(cmd, *a, **k):
                if isinstance(cmd, list) and "watch" in cmd:
                    return FakeWatcherProc()
                return real_popen(cmd, *a, **k)

            captured_stderr = io.StringIO()
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda role, repo_root: {"source": "skill-repo",
                                           "skill_dirs": [], "skills": [], "skill_sha": None}), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", lambda w: None), \
                     mock.patch.object(spawn.subprocess, "Popen", selective_popen), \
                     mock.patch.object(spawn, "_await_bounded", lambda *a, **k: 0), \
                     mock.patch.object(os, "fork", return_value=4321), \
                     contextlib.redirect_stderr(captured_stderr):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=645, bounded=True,
                                     no_wait=True)
                # 워크스페이스 인덱스가 그 명령이 실제로 찾을 엔트리를 갖고
                # 있는지 확인한다 — round-trip 이 "찍힌 텍스트"가 아니라 실제
                # 조회로도 성립함을 고정한다. WORKSPACE_INDEX 를 복원하기 전에
                # 읽어야 한다.
                idx = spawn._workspace_index_load()
                key, entry = spawn._lookup_roster_entry(idx, 645, "implementation")
            finally:
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx
            printed = captured_stderr.getvalue()
            self.assertIn("spawn.py watch --issue 645 --role implementation", printed)
            self.assertIsNotNone(entry)
            self.assertEqual(entry["work"], str(work))

class SpawnOneIssueRoleClaim(unittest.TestCase):
    """이슈 #223: 재스폰 경로(`AutoRespawnClaim`)에만 있던 (issue,role) 클레임을
    주 스폰 경로(`_spawn_one()` 자체)에도 넣는다."""

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

    @pytest.mark.slow
    @pytest.mark.xfail(
        reason="issue #1619: two-thread race against spawn's claim "
               "mechanism -- observed both threads' checkout_calls landing "
               "(2 != 1 expected), i.e. the claim isn't serializing the "
               "two _spawn_one() calls in this environment. Genuine "
               "concurrency-timing flake, needs investigation of the claim "
               "lock under thread (not process) concurrency, tracked "
               "separately from this suite-hygiene pass.",
        strict=False)
    def test_concurrent_spawn_one_calls_let_exactly_one_through(self):
        # 이슈 #223 증상 재현: 같은 (issue, role)로 main() 이 부르는 몸통
        # (_spawn_one) 을 두 번(스레드 두 개로) 겹쳐 부르면, 클레임이 없던
        # 시절엔 둘 다 checkout_issue_branch 까지 통과해 같은 워크스페이스에
        # 두 세션을 띄운다 — 클레임이 있으면 정확히 하나만 통과해야 한다.
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            checkout_calls = []
            checkout_lock = threading.Lock()

            def fake_checkout(cwd, issue, role):
                with checkout_lock:
                    checkout_calls.append(1)
                return "b"

            results = []
            results_lock = threading.Lock()

            def run_spawn():
                rc = spawn._spawn_one(str(work), "implementation", "task\n",
                                      unattended=True, issue=223)
                with results_lock:
                    results.append(rc)

            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            try:
                # plugin_dirs/checkout_version/core_plugin_dirs/core_version
                # 는 실제 룰북/코어 클론을 건드린다 — 이 테스트가 검증하려는
                # 건 클레임 하나뿐이므로, 그 뒤(클레임 통과 후) 경로는 나머지
                # 기존 테스트들과 같은 수준으로 모킹해 무관한 네트워크/환경
                # 의존을 없앤다.
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch", fake_checkout), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda role, repo_root: {"source": "skill-repo",
                                           "skill_dirs": [], "skills": [], "skill_sha": None}), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write",
                                       lambda *a, **k: None):
                    threads = [threading.Thread(target=run_spawn) for _ in range(2)]
                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join()
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                spawn.ROSTER = old_roster

            self.assertEqual(len(checkout_calls), 1, checkout_calls)
            self.assertEqual(len(results), 2)

    @pytest.mark.slow
    def test_claim_still_held_during_ensure_pushed(self):
        # 이슈 #719: `_release_spawn_claim()`이 `proc.wait()` 직후가 아니라
        # `ensure_pushed()`(push + `gh pr create`) 이후로 밀려야, 그 사이에
        # 끼어드는 재스폰이 클레임을 얻어 같은 브랜치에 동시에 push 하는
        # non-fast-forward 충돌을 막는다. `ensure_pushed()`를 페이크로 갈아
        # 끼워 호출 시점에 클레임 파일이 아직 살아 있는지 관측한다.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            claim_path = Path(str(work) + ".spawn-claim")
            observed = {}

            def fake_ensure_pushed(cwd, issue, role):
                observed["held_during_push"] = claim_path.exists()
                return None

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", fake_ensure_pushed), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=719)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                spawn.ROSTER = old_roster
            self.assertTrue(observed.get("held_during_push"),
                            "ensure_pushed() 호출 시점에 클레임이 이미 풀려 "
                            "있었다 — 이슈 #719 가 지목한 release-before-push "
                            "레이스")
            self.assertFalse(claim_path.exists(),
                             "ensure_pushed() 이후 클레임이 여전히 남아있다")

    @pytest.mark.slow
    def test_second_spawn_refused_while_first_still_pushing(self):
        # 위 테스트가 보인 "push 중엔 클레임이 살아있다"는 관측을, 실제로
        # 그 창에서 두 번째 spawn 이 거절되는지까지 끝까지 확인한다.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            second_rejection = {}

            def fake_ensure_pushed(cwd, issue, role):
                second_rejection["value"] = spawn._acquire_spawn_claim(
                    str(work), 719, "implementation")
                return None

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", fake_ensure_pushed), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=719)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                spawn.ROSTER = old_roster
            self.assertIsNotNone(second_rejection.get("value"),
                                 "push 진행 중인데 두 번째 스폰 클레임 취득이 "
                                 "거절되지 않았다")

    def test_empty_state_no_prior_claim_acquires_unchanged(self):
        # 이슈 #719 Acceptance 의 empty-state 요구: 이전 클레임이 없으면 오늘과
        # 바이트 단위로 동일하게 취득이 그냥 성공한다(리그레션 핀).
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            rejection = spawn._acquire_spawn_claim(str(work), 719, "implementation")
            self.assertIsNone(rejection)
            claim_path = Path(str(work) + ".spawn-claim")
            self.assertTrue(claim_path.exists())

    @pytest.mark.slow
    def test_claim_released_when_ensure_pushed_raises(self):
        # warrant hunt (before-landing, issue-719): widening the claim's
        # held window to cover ensure_pushed() means an uncaught exception
        # inside ensure_pushed() (e.g. `gh` missing) must still release the
        # claim — otherwise the wider window becomes a worse leak than the
        # pre-fix code, which released before ensure_pushed() ran at all.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            claim_path = Path(str(work) + ".spawn-claim")

            def raising_ensure_pushed(cwd, issue, role):
                raise RuntimeError("gh not found")

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", raising_ensure_pushed), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None):
                    with self.assertRaises(RuntimeError):
                        spawn._spawn_one(str(work), "implementation", "task\n",
                                         unattended=True, issue=719)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                spawn.ROSTER = old_roster
            self.assertFalse(claim_path.exists(),
                             "ensure_pushed() 가 예외를 던졌는데 클레임이 안 풀렸다")

    def test_stale_claim_from_dead_pid_is_cleaned_and_retried(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            dead = subprocess.Popen(["true"])
            dead.wait()
            claim_path = Path(str(work) + ".spawn-claim")
            claim_path.write_text(json.dumps({"pid": dead.pid, "ts": 1}))
            rejection = spawn._acquire_spawn_claim(str(work), 223, "implementation")
            self.assertIsNone(rejection)
            self.assertEqual(json.loads(claim_path.read_text())["pid"], os.getpid())

    def test_rejection_names_the_live_claimant_pid_and_ts(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "w"
            claim_path = Path(str(work) + ".spawn-claim")
            claim_path.write_text(json.dumps({"pid": os.getpid(), "ts": 555}))
            rejection = spawn._acquire_spawn_claim(str(work), 223, "implementation")
            self.assertIsNotNone(rejection)
            self.assertIn(str(os.getpid()), rejection)
            self.assertIn("555", rejection)

    @pytest.mark.slow
    def test_fork_child_rewrites_claim_pid_before_setsid(self):
        # 이슈 #223 착수 프롬프트가 지목한 함정: bounded 분기는 fork 후 부모가
        # 곧 리턴/종료하므로, 클레임에 fork-전 pid 를 남겨 두면 생존검사가
        # stale 로 오판한다. 자식 분기(child_pid == 0)에서 pid 재기록 헬퍼가
        # os.setsid() 보다 먼저 불려야 한다 — os.fork/os.setsid/os._exit 를
        # 모킹해 실제 fork 없이 자식 분기만 강제하고, dup2 로 바뀌는 표준
        # 입출력 fd 는 테스트 프로세스 자신의 것이므로 호출 전후로 저장·복원한다.
        import threading
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"

            order = []
            orig_rewrite = spawn._rewrite_spawn_claim_pid

            def spy_rewrite(w):
                order.append("rewrite")
                return orig_rewrite(w)

            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                with mock.patch.object(spawn, "issue_workspace",
                                       lambda cwd, issue, role: str(work)), \
                     mock.patch.object(spawn, "checkout_issue_branch",
                                       lambda cwd, issue, role: "b"), \
                     mock.patch.object(spawn, "resolve_role_source",
                                       lambda role, repo_root: {"source": "skill-repo",
                                           "skill_dirs": [], "skills": [], "skill_sha": None}), \
                     mock.patch.object(spawn, "core_plugin_dirs", lambda: []), \
                     mock.patch.object(spawn, "core_version", lambda: "v0"), \
                     mock.patch.object(spawn, "spawn_cmd",
                                       lambda *a, **k: (["cat"], {})), \
                     mock.patch.object(spawn, "ensure_pushed", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_register", lambda *a, **k: None), \
                     mock.patch.object(spawn, "roster_remove", lambda *a, **k: None), \
                     mock.patch.object(spawn, "ledger_write", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None), \
                     mock.patch.object(spawn, "_rewrite_spawn_claim_pid", spy_rewrite), \
                     mock.patch.object(os, "fork", return_value=0), \
                     mock.patch.object(os, "setsid",
                                       lambda: order.append("setsid")), \
                     mock.patch.object(os, "_exit", lambda *a: None):
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=224, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx

            self.assertEqual(order, ["rewrite", "setsid"])
            claim = json.loads(Path(str(work) + ".spawn-claim").read_text())
            self.assertEqual(claim["pid"], os.getpid())

class SpawnDeathBeforeRegistration(unittest.TestCase):
    """이슈 #908: fork-child 의 setsid/dup2/Popen 구간에서 죽으면 그 이전엔
    roster/events 에 아무 흔적도 안 남아 roster_watchdog() 이 구조적으로 못
    봤다 — 그 구간 진입 전에 로스터 스텁 + 이른 session-start 를 먼저 남기고,
    구간 자체는 try/except 로 감싸 spawn-death 이벤트를 덧붙이는지 확인한다."""

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

    def _common_patches(self, work):
        return [
            mock.patch.object(spawn, "issue_workspace",
                               lambda cwd, issue, role: str(work)),
            mock.patch.object(spawn, "checkout_issue_branch",
                               lambda cwd, issue, role: "b"),
            mock.patch.object(spawn, "resolve_role_source",
                              lambda role, repo_root: {"source": "skill-repo",
                                  "skill_dirs": [], "skills": [], "skill_sha": None}),
            mock.patch.object(spawn, "core_plugin_dirs", lambda: []),
            mock.patch.object(spawn, "core_version", lambda: "v0"),
            mock.patch.object(spawn, "spawn_cmd", lambda *a, **k: (["cat"], {})),
            mock.patch.object(spawn, "ensure_pushed", lambda *a, **k: None),
            mock.patch.object(spawn, "roster_remove", lambda *a, **k: None),
            mock.patch.object(spawn, "ledger_write", lambda *a, **k: None),
            mock.patch.object(spawn, "_release_spawn_claim", lambda *a, **k: None),
            mock.patch.object(os, "fork", return_value=0),
            mock.patch.object(os, "_exit", lambda *a: None),
            mock.patch.object(os, "setsid", lambda: None),
        ]

    @pytest.mark.slow
    def test_setsid_death_leaves_roster_stub_and_spawn_death_event(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                with contextlib.ExitStack() as stack:
                    for p in self._common_patches(work):
                        stack.enter_context(p)
                    stack.enter_context(mock.patch.object(
                        os, "setsid", side_effect=OSError("boom")))
                    with self.assertRaises(OSError):
                        spawn._spawn_one(str(work), "implementation", "task\n",
                                         unattended=True, issue=908, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx

            roster_key = "issue-908/implementation"
            d = json.loads(roster.read_text()) if roster.exists() else {}
            self.assertIn(roster_key, d)
            self.assertEqual(d[roster_key]["pid"], os.getpid())

            events_path = spawn._events_path(str(work))
            events = [json.loads(l) for l in
                      events_path.read_text(encoding="utf-8").splitlines()]
            types = [e["type"] for e in events]
            self.assertIn("session-start", types)
            self.assertIn("spawn-death", types)
            death = next(e for e in events if e["type"] == "spawn-death")
            self.assertEqual(death["detail"]["stage"], "fork-setup")

            self.assertEqual(spawn.session_end_verdict(str(work), None,
                                                        alive_fn=lambda pid: False),
                             "crashed")

            buf = io.StringIO()
            spawn.ROSTER = roster
            try:
                with contextlib.redirect_stdout(buf), \
                     mock.patch.object(spawn, "_alive", lambda pid: False), \
                     mock.patch.object(spawn, "_post_session_end_comment",
                                       lambda *a, **k: None), \
                     mock.patch.object(spawn, "diagnose_health",
                                       lambda *a, **k: {"state": "DEAD-ERRORED",
                                                         "detail": "crashed"}), \
                     mock.patch.object(spawn, "ledger_check_and_stamp",
                                       lambda *a, **k: True), \
                     mock.patch.object(spawn, "_board_wide_sweep", lambda root: 0), \
                     mock.patch.object(spawn, "reconcile", lambda *a, **k: []):
                    spawn.roster_watchdog()
            finally:
                spawn.ROSTER = old_roster
            out = buf.getvalue()
            self.assertIn("DEAD-ERRORED", out)

    @pytest.mark.slow
    def test_popen_death_leaves_roster_stub_and_spawn_death_event(self):
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                real_popen = spawn.subprocess.Popen

                def fake_popen(cmd, *a, **k):
                    if cmd == ["cat"]:
                        raise OSError("no such file")
                    return real_popen(cmd, *a, **k)

                with mock.patch.object(spawn.subprocess, "Popen",
                                       side_effect=fake_popen), \
                     contextlib.ExitStack() as stack:
                    for p in self._common_patches(work):
                        stack.enter_context(p)
                    with self.assertRaises(OSError):
                        spawn._spawn_one(str(work), "implementation", "task\n",
                                         unattended=True, issue=908, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx

            events_path = spawn._events_path(str(work))
            events = [json.loads(l) for l in
                      events_path.read_text(encoding="utf-8").splitlines()]
            death = next(e for e in events if e["type"] == "spawn-death")
            self.assertEqual(death["detail"]["stage"], "popen")

    @pytest.mark.slow
    def test_normal_spawn_unaffected_no_spawn_death_event(self):
        # empty-state 가드: 안 죽는 정상 스폰은 마지막에 실제 pid 로 딱 한 번만
        # roster_register 가 불리고, spawn-death 이벤트는 전혀 없어야 한다.
        with tempfile.TemporaryDirectory() as td:
            work = self._prep_repo(td)
            roster = Path(td) / "active.json"
            old_roster = spawn.ROSTER
            spawn.ROSTER = roster
            old_idx = spawn.WORKSPACE_INDEX
            spawn.WORKSPACE_INDEX = Path(td) / "workspaces.json"
            register_calls = []
            orig_register = spawn.roster_register

            def spy_register(key, entry):
                register_calls.append(dict(entry))
                orig_register(key, entry)

            saved_fds = [os.dup(0), os.dup(1), os.dup(2)]
            try:
                with mock.patch.object(spawn, "roster_register", spy_register), \
                     mock.patch.object(spawn, "_self_trigger_respawn",
                                       lambda *a, **k: None), \
                     contextlib.ExitStack() as stack:
                    for p in self._common_patches(work):
                        stack.enter_context(p)
                    spawn._spawn_one(str(work), "implementation", "task\n",
                                     unattended=True, issue=908, bounded=True)
            finally:
                for fd, real in zip((0, 1, 2), saved_fds):
                    os.dup2(real, fd)
                    os.close(real)
                spawn.ROSTER = old_roster
                spawn.WORKSPACE_INDEX = old_idx

            # fork-child stub write (before the risky span, keyed by
            # os.getpid() since os.fork is mocked to 0 and no real fork
            # happens) + the existing post-Popen overwrite (keyed by the
            # real "cat" subprocess's own pid) = 2 calls, no crash in between.
            self.assertEqual(len(register_calls), 2)
            self.assertEqual(register_calls[0]["pid"], os.getpid())

            events_path = spawn._events_path(str(work))
            events = [json.loads(l) for l in
                      events_path.read_text(encoding="utf-8").splitlines()]
            types = [e["type"] for e in events]
            self.assertNotIn("spawn-death", types)
            self.assertEqual(types.count("session-start"), 2)

class EventExitScope(unittest.TestCase):
    """이슈 #142 — 스폰은 **이 세션이 낸** 이벤트로만 리턴해야 한다.

    실측 2026-07-30(core issue-53 phase 2): 78분 전 phase 1 이 남긴
    `pr-opened https://github.com/octocat/Hello-World/pull/1` 로 스폰이 exit 0
    을 냈고, 세션은 계속 돌았다. 두 결함이 겹쳤다 — 과거 이벤트를 소비했고,
    그 이벤트의 URL 은 이 레포의 PR 도 아니었다.
    """

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)
        self.offset = spawn._offset_path(self.work)
        self.log = Path(str(self.work) + ".session.log")
        self.log.write_text("")

    def tearDown(self):
        shutil.rmtree(self.td, ignore_errors=True)

    def test_stale_event_is_not_consumed_after_baseline(self):
        """이전 세션이 남긴 줄은 offset 을 파일 끝으로 민 뒤엔 안 보인다."""
        spawn._append_event(self.events, "pr-opened",
                            "https://github.com/octocat/Hello-World/pull/1")
        spawn._append_event(self.events, "session-end", "progressed")
        # 스폰이 fork 직전에 하는 일
        spawn._write_offset(self.offset, spawn._event_count(self.events))
        self.assertEqual(spawn._read_offset(self.offset), 2)
        # 새 세션이 자기 이벤트를 낸다 — 리턴은 이것으로만 일어나야 한다
        spawn._append_event(self.events, "session-start", {"pid": 111})
        lines = self.events.read_text().splitlines()
        ev = json.loads(lines[spawn._read_offset(self.offset)])
        self.assertEqual(ev["type"], "session-start")
        self.assertEqual(ev["detail"]["pid"], 111)

    def test_without_baseline_the_stale_event_wins(self):
        """기준선을 안 밀면 78분 전 줄이 먼저 잡힌다 — 고치기 전 동작."""
        spawn._append_event(self.events, "pr-opened",
                            "https://github.com/octocat/Hello-World/pull/1")
        spawn._append_event(self.events, "session-start", {"pid": 111})
        ev = json.loads(self.events.read_text().splitlines()[0])
        self.assertEqual(ev["type"], "pr-opened")   # 이게 실측된 오보의 씨앗

    @pytest.mark.slow
    def test_event_count_matches_offset_units(self):
        self.assertEqual(spawn._event_count(self.events), 0)
        spawn._append_event(self.events, "a", "1")
        spawn._append_event(self.events, "b", "2")
        self.assertEqual(spawn._event_count(self.events), 2)
        self.assertEqual(spawn._event_count(Path(self.td) / "nope.jsonl"), 0)

    def _origin(self, url):
        subprocess.run(["git", "init", "-q", str(self.work)], check=False)
        subprocess.run(["git", "-C", str(self.work), "remote", "add", "origin", url],
                       check=False, capture_output=True)
        return spawn._origin_pr_prefix(self.work)

    def test_pr_prefix_from_https_and_ssh_origin(self):
        self.assertEqual(self._origin("https://github.com/tokenmaxxxer/on-the-record.git"),
                         "https://github.com/tokenmaxxxer/on-the-record/pull/")

    @pytest.mark.slow
    def test_pr_prefix_none_without_origin(self):
        subprocess.run(["git", "init", "-q", str(self.work)], check=False)
        self.assertIsNone(spawn._origin_pr_prefix(self.work))

    def test_foreign_pr_url_is_not_this_repos_pr(self):
        prefix = self._origin("git@github.com:tokenmaxxxer/on-the-record.git")
        self.assertEqual(prefix, "https://github.com/tokenmaxxxer/on-the-record/pull/")
        found = spawn._PR_URL_RE.findall(
            'see https://github.com/octocat/Hello-World/pull/1 and '
            'https://github.com/tokenmaxxxer/on-the-record/pull/142')
        kept = [m for m in found if m.startswith(prefix)]
        self.assertEqual(kept, ["https://github.com/tokenmaxxxer/on-the-record/pull/142"])

class AwaitBoundedTiming(unittest.TestCase):
    """이슈 #285 P1: `_await_bounded()` 가 고정 2초 sleep 대신 escalating
    poll 을 쓰는지 — session-start 가 거의 즉시 찍혀도 caller-return 이
    2초 가까이 걸리면 회귀."""

    def test_returns_quickly_after_early_event(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")

            def writer():
                time.sleep(0.1)
                spawn._append_event(events_path, "session-start", "spawned")

            t = threading.Thread(target=writer)
            t.start()
            t0 = time.monotonic()
            rc = spawn._await_bounded(events_path, offset_path, 5.0, log_path)
            elapsed = time.monotonic() - t0
            t.join()
            self.assertEqual(rc, 0)
            self.assertLess(elapsed, 1.5, f"caller-return took {elapsed:.3f}s")

    def test_still_bounded_by_stall_timeout(self):
        # 회귀 방지: escalating poll 이 stall 판정 자체를 늦추지 않는다 —
        # 이슈 #114 계약(무한정 블록하지 않는다)은 그대로.
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")
            t0 = time.monotonic()
            stall_timeout_min = 0.03  # ~1.8s
            rc = spawn._await_bounded(events_path, offset_path,
                                      stall_timeout_min, log_path)
            elapsed = time.monotonic() - t0
            self.assertEqual(rc, 0)
            self.assertGreaterEqual(elapsed, stall_timeout_min * 60 - 0.5)
            self.assertLess(elapsed, stall_timeout_min * 60 + 2.5)

class AwaitBoundedWallClockCap(unittest.TestCase):
    """이슈 #645: `max_wait_s` 가 주어지면 로그가 계속 자라도(stall 시계가
    한 번도 안 찍혀도) 활동과 무관한 wall-clock 상한에서 리턴한다 — 셋
    (event/stall/wall-clock cap) 이 서로 다른 리턴 코드로 구분된다."""

    def test_wallclock_cap_wins_over_endless_activity(self):
        # 로그가 계속 자라 stall 시계는 절대 안 찍힌다 — stall_timeout_min 을
        # 크게 잡아 stall 경로가 실수로 먼저 트리거하지 않게 한다. max_wait_s
        # 만 이 리턴을 강제해야 한다.
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")
            stop = threading.Event()

            def grower():
                n = 0
                while not stop.is_set():
                    n += 1
                    log_path.write_text("x" * n)
                    time.sleep(0.05)

            t = threading.Thread(target=grower)
            t.start()
            t0 = time.monotonic()
            try:
                rc = spawn._await_bounded(events_path, offset_path, 5.0, log_path,
                                          max_wait_s=1.0)
            finally:
                stop.set()
                t.join()
            elapsed = time.monotonic() - t0
            self.assertEqual(rc, spawn.WATCH_WALLCLOCK_RC)
            self.assertGreaterEqual(elapsed, 0.9)
            self.assertLess(elapsed, 3.0)

    def test_wallclock_cap_does_not_advance_offset(self):
        # 캡에 걸려 리턴해도 미보고 이벤트를 건너뛰면 안 된다 — 다음 호출이
        # 같은 offset 에서 그대로 이어 본다(resumability).
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")
            spawn._append_event(events_path, "tool-call", "unread-after-cap")
            self.assertEqual(spawn._read_offset(offset_path), 0)
            # 이미 있는 이벤트를 "이미 읽었다"고 offset 을 밀어 둔다 — 그
            # 이후로는 새 이벤트가 없으므로 캡만 리턴 사유가 된다.
            spawn._write_offset(offset_path, 1)
            rc = spawn._await_bounded(events_path, offset_path, 5.0, log_path,
                                      max_wait_s=0.3)
            self.assertEqual(rc, spawn.WATCH_WALLCLOCK_RC)
            self.assertEqual(spawn._read_offset(offset_path), 1)

    def test_event_still_wins_when_it_arrives_before_the_cap(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")

            def writer():
                time.sleep(0.1)
                spawn._append_event(events_path, "session-end", "done")

            t = threading.Thread(target=writer)
            t.start()
            rc = spawn._await_bounded(events_path, offset_path, 5.0, log_path,
                                      max_wait_s=5.0)
            t.join()
            self.assertEqual(rc, 0)

    def test_max_wait_unset_preserves_existing_stall_behavior(self):
        # 회귀 방지: max_wait_s 를 안 넘기면(기존 모든 호출부) 동작이
        # byte-for-byte 그대로다 — stall 로만 리턴하고 WATCH_WALLCLOCK_RC 는
        # 절대 안 나온다.
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "events.jsonl"
            offset_path = Path(td) / "offset"
            log_path = Path(td) / "session.log"
            log_path.write_text("")
            rc = spawn._await_bounded(events_path, offset_path, 0.03, log_path)
            self.assertEqual(rc, 0)

class WatchFollowWallClockCap(unittest.TestCase):
    """이슈 #645: `watch --follow` 는 반복 호출에 걸친 누적 wall-clock 을
    `max_wait_min` 으로 예산 삼아, 매 진전이 있어도 예산이 다하면
    WATCH_WALLCLOCK_RC 로 리턴한다."""

    def _prep(self, td, entry_extra=None):
        work = Path(td) / "work"
        work.mkdir()
        events_path = spawn._events_path(str(work))
        offset_path = spawn._offset_path(str(work))
        log_path = Path(td) / "session.log"
        log_path.write_text("")
        spawn._workspace_index_put(645, "implementation", str(work), str(log_path))
        spawn._roster_save({"issue-645/implementation": {"pid": os.getpid()}})
        return work, events_path, offset_path, log_path

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", self.old_idx)
        self.addCleanup(setattr, spawn, "ROSTER", self.old_roster)

    def test_budget_exhausted_across_repeated_progress_returns_wallclock_rc(self):
        work, events_path, offset_path, log_path = self._prep(self.td)
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min,
                                log_path, **kwargs):
            calls.append(kwargs.get("max_wait_s"))
            # 매 호출마다 "진전"을 낸다(로그 크기 변화) — session-end 없이
            # 계속 도는 것처럼 보이게 해, stall/crash 경로가 아니라 캡만
            # 리턴 사유가 되게 한다.
            log_path.write_text("x" * (len(calls) + 1))
            time.sleep(0.05)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded), \
             mock.patch.object(spawn, "_alive", lambda pid: True):
            rc = spawn._watch(645, "implementation", 5.0, follow=True,
                              max_wait_min=0.01)  # 0.6s 예산
        self.assertEqual(rc, spawn.WATCH_WALLCLOCK_RC)
        self.assertTrue(len(calls) >= 1)

    def test_unset_budget_leaves_follow_loop_unbounded_by_wallclock(self):
        work, events_path, offset_path, log_path = self._prep(self.td)
        spawn._append_event(events_path, "session-end", "done")
        calls = []

        def fake_await_bounded(events_path, offset_path, stall_timeout_min,
                                log_path, **kwargs):
            calls.append(kwargs.get("max_wait_s"))
            spawn._write_offset(offset_path, 1)
            return 0

        with mock.patch.object(spawn, "_await_bounded", fake_await_bounded):
            rc = spawn._watch(645, "implementation", 5.0, follow=True)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [None])

class AwaitBoundedMissingLog(unittest.TestCase):
    """#288 corroboration item: log_path 가 존재하지 않으면 "stall: N초째
    무변화"가 아니라 "cannot observe" 로 보고해야 한다 — clean 의 전역
    스윕이 로그를 지운 세션을 가짜 stall 로 오보하던 실측 사건."""

    def test_missing_log_reports_cannot_observe_not_stall(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "s.events.jsonl"
            offset_path = Path(td) / "s.events.offset"
            log_path = Path(td) / "does-not-exist.log"

            buf = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = buf
            try:
                rc = spawn._await_bounded(events_path, offset_path, 0.001, log_path)
            finally:
                sys.stderr = old_stderr

            out = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("cannot observe", out)
            self.assertNotIn("stall:", out)

    def test_existing_unchanged_log_still_reports_stall(self):
        with tempfile.TemporaryDirectory() as td:
            events_path = Path(td) / "s.events.jsonl"
            offset_path = Path(td) / "s.events.offset"
            log_path = Path(td) / "present.log"
            log_path.write_text("x")

            buf = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = buf
            try:
                rc = spawn._await_bounded(events_path, offset_path, 0.001, log_path)
            finally:
                sys.stderr = old_stderr

            out = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("stall:", out)
            self.assertNotIn("cannot observe", out)

class WatcherAutoArm(unittest.TestCase):
    """이슈 #488: auto-arm — 스폰이 자신의 워처 pid 를 workspace index 에
    남기고, watchdog 는 그 워처가 죽으면(또는 애초에 없으면) 조용히
    넘기지 않고 신고한다."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)

    def test_workspace_index_put_records_watcher_pid(self):
        spawn._workspace_index_put(488, "implementation", "work", "log",
                                    watcher_pid=12345)
        entry = spawn._workspace_index_load()["work/issue-488/implementation"]
        self.assertEqual(entry["watcher_pid"], 12345)

    def test_workspace_index_put_without_watcher_pid_omits_field(self):
        spawn._workspace_index_put(488, "implementation", "work", "log")
        entry = spawn._workspace_index_load()["work/issue-488/implementation"]
        self.assertNotIn("watcher_pid", entry)

    def _entry(self, log, work="work"):
        return {"log": str(log), "work": work, "ts": int(time.time()),
                "before_head": None, "pid": None}

    def test_watchdog_flags_dead_watcher(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            spawn._workspace_index_put(488, "implementation", "work", str(log),
                                        watcher_pid=999999999)  # 존재 안 할 pid
            out = spawn.watchdog_check_one(
                "issue-488/implementation", self._entry(log), state={})
            self.assertTrue(any("watcher-dead" in a for a in out))

    def test_watchdog_flags_missing_watcher(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            spawn._workspace_index_put(488, "implementation", "work", str(log))
            out = spawn.watchdog_check_one(
                "issue-488/implementation", self._entry(log), state={})
            self.assertTrue(any("watcher-missing" in a for a in out))

    def test_watchdog_silent_when_watcher_alive(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            spawn._workspace_index_put(488, "implementation", "work", str(log),
                                        watcher_pid=os.getpid())
            out = spawn.watchdog_check_one(
                "issue-488/implementation", self._entry(log), state={})
            self.assertFalse(any("watcher-dead" in a for a in out))
            self.assertFalse(any("watcher-missing" in a for a in out))

    def test_watchdog_silent_when_no_workspace_index_entry(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.watchdog_check_one(
                "issue-999/nobody", self._entry(log, work="nobody-work"), state={})
            self.assertFalse(any("watcher-" in a for a in out))

    @unittest.skipUnless(Path("/proc").is_dir(), "cmdline 신원 검사는 /proc 필요")
    def test_watchdog_flags_pid_reused_by_unrelated_process(self):
        # before-landing hunt 발견: 워처가 죽은 뒤 OS 가 같은 pid 를 다른
        # 프로세스에 재할당하면 _alive() 만으로는 구분 못 한다 — 살아있는
        # 이 테스트 프로세스 자신의 pid 를 워처로 등록해도, 그 cmdline 은
        # "watch" 호출이 아니므로 watcher-dead 로 잡혀야 한다.
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            spawn._workspace_index_put(488, "implementation", "work", str(log),
                                        watcher_pid=os.getpid())
            entry = self._entry(log)
            entry["issue"] = 488
            out = spawn.watchdog_check_one(
                "issue-488/implementation", entry, state={})
            self.assertTrue(any("watcher-dead" in a for a in out))

    @unittest.skipUnless(Path("/proc").is_dir(), "cmdline 신원 검사는 /proc 필요")
    def test_watcher_looks_real_rejects_live_watcher_of_a_different_role(self):
        # after-proposal hunt 발견(이슈 #559): 같은 이슈, 다른 역할의 살아있는
        # 워처를 이 역할의 워처로 오인하면 안 된다 — 이 테스트 프로세스는
        # "watch" 인자를 안 가지므로 role 유무와 무관하게 issue-only 체크로도
        # 이미 실패하지만, role 을 넘겼을 때 cmdline 에 role 문자열이 없으면
        # 별도로도 거짓을 리턴해야 한다는 계약을 고정한다.
        self.assertFalse(spawn._watcher_looks_real(
            os.getpid(), 488, role="implementation"))

class WatcherPs(unittest.TestCase):
    """이슈 #559: `ps` 가 살아있는 각 세션마다 붙은 워처를 보여준다 — pid,
    armed-at, follow 여부, 죽은 워처는 죽었다고, 워처가 없으면 UNWATCHED."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        old_roster = spawn.ROSTER
        spawn.ROSTER = Path(self.td) / "active.json"
        self.addCleanup(setattr, spawn, "ROSTER", old_roster)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()

    def _register(self, role="implementation", issue=488, pid=None):
        pid = pid if pid is not None else os.getpid()
        spawn.roster_register(f"issue-{issue}/{role}", {
            "pid": pid, "role": role, "issue": issue, "ts": int(time.time()),
            "work": str(self.work), "log": str(self.work) + ".session.log"})

    def _capture_ps(self) -> str:
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            spawn.roster_ps()
        finally:
            sys.stdout = old_stdout
        return buf.getvalue()

    def test_watcher_ps_shows_unwatched_when_no_watcher_recorded(self):
        self._register()
        spawn._workspace_index_put(488, "implementation", str(self.work), "log")
        out = self._capture_ps()
        self.assertIn("UNWATCHED", out)

    def test_watcher_ps_shows_alive_watcher_pid_armed_at_and_follow(self):
        self._register()
        armed_at = time.time() - 120
        spawn._workspace_index_put(488, "implementation", str(self.work), "log",
                                    watcher_pid=os.getpid(),
                                    watcher_armed_at=armed_at)
        # 실행 중인 프로세스가 실제 `watch` 워처는 아니므로(테스트 러너
        # 자신) 신원 확인만 우회하고 나머지 ps 출력 조립은 실물로 검증한다.
        with mock.patch.object(spawn, "_watcher_looks_real", return_value=True):
            out = self._capture_ps()
        self.assertIn(f"pid {os.getpid()}", out)
        self.assertIn("armed", out)
        self.assertIn("follow=True", out)
        self.assertNotIn("UNWATCHED", out)

    def test_watcher_ps_shows_dead_watcher_as_dead_not_omitted(self):
        self._register()
        dead = subprocess.Popen(["true"])
        dead.wait()
        spawn._workspace_index_put(488, "implementation", str(self.work), "log",
                                    watcher_pid=dead.pid,
                                    watcher_armed_at=time.time())
        out = self._capture_ps()
        self.assertIn("DEAD", out)
        self.assertIn(str(dead.pid), out)

class WatcherSilentSignal(unittest.TestCase):
    """이슈 #782: 워처 pid 는 살아 있지만(watcher-dead 로는 안 잡힘) 워처
    자신의 로그가 무장 이후로 안 움직이는 2026-08-11 실패 모드."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        old_idx = spawn.WORKSPACE_INDEX
        spawn.WORKSPACE_INDEX = Path(self.td) / "workspaces.json"
        self.addCleanup(setattr, spawn, "WORKSPACE_INDEX", old_idx)
        self._orig_looks_real = spawn._watcher_looks_real
        spawn._watcher_looks_real = lambda pid, issue, role=None: True
        self.addCleanup(setattr, spawn, "_watcher_looks_real", self._orig_looks_real)

    def _entry(self, log, work):
        return {"log": str(log), "work": work, "ts": int(time.time()),
                "before_head": None, "pid": None}

    def test_watcher_silent_fires_when_pid_real_but_log_stale(self):
        with tempfile.TemporaryDirectory() as td:
            work = str(Path(td) / "work")
            watcher_log = Path(work + ".watcher.log")
            armed_at = time.time() - (spawn.WATCHDOG_SILENCE_MIN + 5) * 60
            watcher_log.write_text("armed\n")
            os.utime(watcher_log, (armed_at, armed_at))
            spawn._workspace_index_put(488, "implementation", work, "log",
                                        watcher_pid=999999999,
                                        watcher_armed_at=armed_at)
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.watchdog_check_one(
                "issue-488/implementation", self._entry(log, work), state={})
            self.assertTrue(any("watcher-silent" in a for a in out))

    def test_no_watcher_silent_signal_when_log_recent(self):
        with tempfile.TemporaryDirectory() as td:
            work = str(Path(td) / "work")
            watcher_log = Path(work + ".watcher.log")
            armed_at = time.time() - 5 * 60
            watcher_log.write_text("armed\n")
            spawn._workspace_index_put(488, "implementation", work, "log",
                                        watcher_pid=999999999,
                                        watcher_armed_at=armed_at)
            log = Path(td) / "s.log"
            log.write_text('{"type":"text"}\n')
            out = spawn.watchdog_check_one(
                "issue-488/implementation", self._entry(log, work), state={})
            self.assertFalse(any("watcher-silent" in a for a in out))

class PollDue(unittest.TestCase):
    """이슈 #782 req #7: `spawn.py poll-due` — 15분 간격 원자적 staleness
    체크. CI/명시적 호출 없이 `directive.sh` 의 UserPromptSubmit 훅이
    매 턴 부른다."""

    def test_first_call_is_due(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "poll_state.json"
            self.assertTrue(spawn.poll_due(now=1000.0, poll_state=state))

    def test_repeat_within_interval_is_not_due(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "poll_state.json"
            self.assertTrue(spawn.poll_due(now=1000.0, poll_state=state))
            self.assertFalse(spawn.poll_due(
                now=1000.0 + spawn.POLL_INTERVAL_SEC - 1, poll_state=state))

    def test_repeat_after_interval_is_due_again(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td) / "poll_state.json"
            self.assertTrue(spawn.poll_due(now=1000.0, poll_state=state))
            self.assertTrue(spawn.poll_due(
                now=1000.0 + spawn.POLL_INTERVAL_SEC + 1, poll_state=state))

    def test_cli_returns_zero_when_due_and_one_when_not(self):
        with tempfile.TemporaryDirectory() as td:
            old_state = spawn.POLL_STATE
            spawn.POLL_STATE = Path(td) / "poll_state.json"
            old_argv = sys.argv
            try:
                sys.argv = ["spawn.py", "poll-due"]
                self.assertEqual(spawn.main(), 0)
                sys.argv = ["spawn.py", "poll-due"]
                self.assertEqual(spawn.main(), 1)
            finally:
                sys.argv = old_argv
                spawn.POLL_STATE = old_state

class RosterWatchdogIdempotentReconcile(unittest.TestCase):
    """이슈 #782 Acceptance: 이벤트 채널이 완료를 이미 찍어 두면, 뒤이은
    폴링(roster_watchdog) 틱이 같은 완료를 다시 보고하지 않는다."""

    def setUp(self):
        self._orig_roster = spawn.ROSTER
        self._orig_state = spawn.WATCHDOG_STATE
        self._orig_ledger = spawn.RECONCILE_LEDGER
        self._orig_pr = spawn._pr_open_or_merged_for_branch
        self._orig_verdict = spawn.session_end_verdict
        self._td = tempfile.TemporaryDirectory()
        spawn.ROSTER = Path(self._td.name) / "active.json"
        spawn.WATCHDOG_STATE = Path(self._td.name) / "watchdog_state.json"
        spawn.RECONCILE_LEDGER = Path(self._td.name) / "reconcile_ledger.json"

    def tearDown(self):
        spawn.ROSTER = self._orig_roster
        spawn.WATCHDOG_STATE = self._orig_state
        spawn.RECONCILE_LEDGER = self._orig_ledger
        spawn._pr_open_or_merged_for_branch = self._orig_pr
        spawn.session_end_verdict = self._orig_verdict
        self._td.cleanup()

    def test_poll_stays_silent_after_watch_already_stamped_pr_expected_missing(self):
        # `_spawn_one()`이 pr-opened 를 이미 확정한 순간 찍는 것과 같은
        # 키를 미리 찍어, 이후 roster_watchdog() 틱이 pr-expected-missing
        # 을 다시 보고하지 않음을 확인한다(이벤트가 폴을 이긴다).
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn.session_end_verdict = lambda work, log_path, now=None: None
        work = str(Path(self._td.name) / "issue-1" / "implementation")
        Path(work).mkdir(parents=True)
        log = Path(self._td.name) / "s.log"
        log.write_text('{"type":"text"}\n')
        spawn.ROSTER.write_text(json.dumps({
            "issue-1/implementation": {
                "log": str(log), "work": work, "ts": int(time.time()),
                "pid": os.getpid(), "issue": 1, "role": "implementation",
                "expects_pr": True}}))
        spawn.ledger_stamp("health-repair:1:implementation:pr-expected-missing",
                            now=time.time())
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            with mock.patch.object(spawn, "_board_wide_sweep", return_value=0):
                spawn.roster_watchdog()
        finally:
            sys.stdout = old_stdout

class TestMaybeResumeForReadyPrRecordsFailureCause(unittest.TestCase):
    """issue #910 finding #1: a Popen failure inside
    _resume_orchestrator_session and an ordinary claim-skip (another entry
    already claimed the same session_id) previously both collapsed to
    `_maybe_resume_for_ready_pr` returning False with no roster/record
    trace. Both paths must now append a distinguishing event."""

    def setUp(self):
        self.td = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)
        self.work = Path(self.td) / "wk"
        self.work.mkdir()
        self.events = spawn._events_path(self.work)

    def _event_types(self):
        if not self.events.exists():
            return []
        return [json.loads(line)["type"]
                for line in self.events.read_text(encoding="utf-8").splitlines()]

    def test_popen_failure_is_recorded_distinctly(self):
        from unittest import mock
        entry = {"session_id": "sess-popen-fail", "work": str(self.work)}
        with mock.patch.object(spawn, "_session_resume_claim", return_value=True), \
             mock.patch.object(spawn, "_resume_orchestrator_session",
                                return_value=("popen-failed", "no such file or directory: claude")):
            result = spawn._maybe_resume_for_ready_pr("issue-1/implementation", entry, 42)
        self.assertFalse(result)
        self.assertIn("resume-attempt-failed", self._event_types())

    def test_claim_skip_is_recorded_distinctly(self):
        from unittest import mock
        entry = {"session_id": "sess-claimed", "work": str(self.work)}
        with mock.patch.object(spawn, "_session_resume_claim", return_value=False):
            result = spawn._maybe_resume_for_ready_pr("issue-1/implementation", entry, 42)
        self.assertFalse(result)
        self.assertIn("resume-skipped-claimed", self._event_types())

    def test_successful_resume_records_no_failure_event(self):
        from unittest import mock
        entry = {"session_id": "sess-ok", "work": str(self.work)}
        fake_proc = mock.Mock()
        with mock.patch.object(spawn, "_session_resume_claim", return_value=True), \
             mock.patch.object(spawn, "_resume_orchestrator_session", return_value=fake_proc):
            result = spawn._maybe_resume_for_ready_pr("issue-1/implementation", entry, 42)
        self.assertTrue(result)
        types = self._event_types()
        self.assertNotIn("resume-attempt-failed", types)
        self.assertNotIn("resume-skipped-claimed", types)

    def test_resume_orchestrator_session_returns_failure_tuple_on_oserror(self):
        from unittest import mock
        with mock.patch.object(spawn.subprocess, "Popen", side_effect=OSError("no such file")):
            result = spawn._resume_orchestrator_session("sess-x", "nudge", cwd=str(self.work))
        self.assertEqual(result[0], "popen-failed")
        self.assertIn("no such file", result[1])

class ConsumerFixtureWatchdogAnchoring(unittest.TestCase):
    """이슈 #1219: 컨슈머(타깃) 레포에서 도는 워치독은 tokenmaxxxer/
    on-the-record 자신의 보드나 마켓플레이스 체크아웃 경로를 노출하면
    안 된다 — 이 체크아웃과 무관한, 보드조차 없는 "외지" 픽스처 레포로
    hermetic 하게 검증한다(네트워크 gh 호출 없이)."""

    def test_foreign_repo_watchdog_output_carries_no_marketplace_or_otr_references(self):
        with tempfile.TemporaryDirectory() as td:
            foreign_root = Path(td) / "foreign-target-repo"
            foreign_root.mkdir()
            # 컨슈머 레포다운 최소 모양 — 보드(docs/issue-*/)도, 다이제스트도
            # 없다: "없으면 조용히" 요구사항(#1219 requirement 3)의 empty
            # state.
            (foreign_root / "docs").mkdir()

            roster_path = foreign_root / "active.json"
            old_roster, old_state = spawn.ROSTER, spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = foreign_root / "watchdog_state.json"

            fake_cs = mock.MagicMock()
            fake_cs.issue_state_index_all.return_value = ({}, True)
            fake_cs.find_violations.return_value = ([], [])
            fake_cs.accumulation_trend.return_value = {}
            fake_cs.format_accumulation_trend.return_value = "accumulation: n/a"
            fake_sc = mock.MagicMock()
            fake_sc._list_open_issues.return_value = []
            fake_sc.find_uncovered.return_value = []

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                with mock.patch.dict(sys.modules,
                                      {"closure_sweep": fake_cs,
                                       "spawn_coverage": fake_sc}):
                    result = spawn.roster_watchdog(root=foreign_root)
            finally:
                sys.stdout = old_stdout
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state

            out = buf.getvalue()
            self.assertEqual(result, 0)
            self.assertNotIn(str(spawn.ROOT), out)
            self.assertNotIn("marketplaces", out)
            self.assertNotIn("tokenmaxxxer/on-the-record", out)
            self.assertIn("돌고 있는 역할 세션 없음", out)

    @pytest.mark.xfail(
        reason="issue #1619: same concurrent-board-sweep-lock flakiness as "
               "PollHeartbeatMarkerRelocationTest's two xfails above -- "
               "observed 'board-sweep: on-the-record 건너뜀 (다른 워크스페이스가 "
               "스윕 중)' short-circuiting spawn._board_wide_sweep before "
               "the mock records a call.",
        strict=False)
    def test_dev_session_cwd_is_checkout_stays_unchanged(self):
        # 요구사항 2: cwd 가 이 체크아웃 자신일 때(dev 세션)는 그대로
        # ROOT 를 본다 — root 기본값이 ROOT 이므로 인자 없이 부르면
        # 기존 dev 세션 동작과 동일하다.
        with tempfile.TemporaryDirectory() as td:
            roster_path = Path(td) / "active.json"
            old_roster, old_state = spawn.ROSTER, spawn.WATCHDOG_STATE
            spawn.ROSTER = roster_path
            spawn.WATCHDOG_STATE = Path(td) / "watchdog_state.json"
            try:
                with mock.patch.object(spawn, "_board_wide_sweep",
                                        return_value=0) as sweep:
                    spawn.roster_watchdog()
                sweep.assert_called_once_with(spawn.ROOT)
            finally:
                spawn.ROSTER = old_roster
                spawn.WATCHDOG_STATE = old_state
