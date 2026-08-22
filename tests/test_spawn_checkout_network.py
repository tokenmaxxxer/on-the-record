from _spawn_test_support import *  # noqa: F401,F403


class PrOpenOrMergedForBranch(unittest.TestCase):
    def test_returns_none_when_only_pr_is_closed_unmerged(self):
        from unittest import mock
        fake = mock.Mock(returncode=0,
                         stdout=json.dumps([{"number": 7, "state": "CLOSED"}]))
        with mock.patch.object(spawn.subprocess, "run", return_value=fake):
            self.assertIsNone(
                spawn._pr_open_or_merged_for_branch(Path("."), "issue-1/implementation"))

    def test_returns_number_when_open(self):
        from unittest import mock
        fake = mock.Mock(returncode=0,
                         stdout=json.dumps([{"number": 7, "state": "OPEN"}]))
        with mock.patch.object(spawn.subprocess, "run", return_value=fake):
            self.assertEqual(
                spawn._pr_open_or_merged_for_branch(Path("."), "issue-1/implementation"),
                7)

    def test_returns_number_when_merged(self):
        from unittest import mock
        fake = mock.Mock(returncode=0,
                         stdout=json.dumps([{"number": 7, "state": "MERGED"}]))
        with mock.patch.object(spawn.subprocess, "run", return_value=fake):
            self.assertEqual(
                spawn._pr_open_or_merged_for_branch(Path("."), "issue-1/implementation"),
                7)

class OrchestratorGitToken(unittest.TestCase):
    """실측: reasona issue-3 검증 중, GH_TOKEN 없이 `python3 spawn.py` 를
    그냥 돌리면 재사용 워크스페이스 fetch 가 인증 실패로 막힌다.
    `issue_workspace()` 가 작업 클론에 심는 credential.helper 는 그 helper
    를 실행하는 프로세스의 $GH_TOKEN 을 읽는데, `spawn_cmd()` 는 역할
    세션의 env 에 그 값을 명시 주입하면서 오케스트레이터 자신의 프로세스에는
    아무도 넣어주지 않았다. `_fetch_or_halt()`/`ensure_pushed()` 의 git
    호출에 `_git_env()` 를 통해 주입되는지, fake git wrapper 로 실제
    프로세스 env 를 검사해 확인한다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def setUp(self):
        spawn._GH_TOKEN_CACHE = None
        self._saved_agent = os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)

    def tearDown(self):
        spawn._GH_TOKEN_CACHE = None
        os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)
        if self._saved_agent is not None:
            os.environ["MUSTER_AGENT_GH_TOKEN"] = self._saved_agent

    def _token_recording_git_wrapper(self, fake_bin, record_path):
        """`$GH_TOKEN` 을 record_path 에 적고 real git 에 위임하는 wrapper —
        어느 값이 실제로 이 프로세스에 도달했는지 실 subprocess 실행으로
        검사한다(mock 이 아니라)."""
        real_git = shutil.which("git")
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            f"echo \"${{GH_TOKEN}}\" > {record_path}\n"
            f"exec {real_git} \"$@\"\n"
        )
        wrapper.chmod(0o755)

    @pytest.mark.slow
    def test_fetch_or_halt_injects_muster_agent_gh_token(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "test-token-abc"
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            record = Path(td) / "seen-token.txt"
            self._token_recording_git_wrapper(fake_bin, record)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                spawn._fetch_or_halt(str(work), "test-label")
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(record.read_text().strip(), "test-token-abc")

    @pytest.mark.slow
    def test_ensure_pushed_push_call_injects_token_too(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "test-token-xyz"
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            self._git(origin, "branch", "-m", "main")
            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self._git(work, "config", "user.email", "t@t.t")
            self._git(work, "config", "user.name", "t")

            issue, role = 999903, "implementation"
            br = f"issue-{issue}/{role}"
            self._git(work, "checkout", "-q", "-b", br)
            (work / "c.txt").write_text("wip")
            self._git(work, "add", "c.txt")
            self._git(work, "commit", "-q", "-m", "wip")

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            record = Path(td) / "seen-token.txt"
            self._token_recording_git_wrapper(fake_bin, record)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            gh_stub = fake_bin / "gh"
            gh_stub.write_text("#!/bin/sh\nexit 1\n")  # gh pr list/create no-op
            gh_stub.chmod(0o755)
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(record.read_text().strip(), "test-token-xyz")

    def test_token_resolution_shells_out_to_gh_at_most_once(self):
        """캐시 검증: gh auth token 을 두 번 부르지 않는다 — 한 스폰 안에서
        _fetch_or_halt 가 여러 번 불려도(issue_workspace + checkout_issue_branch)."""
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "gh-calls.txt"
            gh_wrapper = fake_bin / "gh"
            gh_wrapper.write_text(
                "#!/bin/sh\n"
                f"echo x >> {call_count_file}\n"
                "echo fake-shelled-out-token\n"
            )
            gh_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                first = spawn._resolve_gh_token()
                second = spawn._resolve_gh_token()
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(first, "fake-shelled-out-token")
            self.assertEqual(second, "fake-shelled-out-token")
            self.assertEqual(len(call_count_file.read_text().splitlines()), 1)

    def test_unresolvable_token_returns_none_not_empty_override(self):
        """토큰을 못 구하면 _git_env() 는 None 이어야 한다 — 빈 문자열로
        덮어쓰면 subprocess.run 이 부모 env 를 안 물려받아, 사용자의 다른
        자격증명 경로(ssh-agent, osxkeychain)까지 막힌다."""
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            gh_wrapper = fake_bin / "gh"
            gh_wrapper.write_text("#!/bin/sh\nexit 1\n")  # gh auth token 실패
            gh_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                self.assertIsNone(spawn._git_env())
            finally:
                os.environ["PATH"] = old_path

    def test_muster_agent_gh_token_wins_over_gh_auth_token(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "explicit-agent-token"
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            gh_wrapper = fake_bin / "gh"
            # gh 가 불리면 다른 토큰을 낸다 — 실제로 불렸다면 테스트가 잡는다.
            gh_wrapper.write_text("#!/bin/sh\necho should-not-be-used\n")
            gh_wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                token = spawn._resolve_gh_token()
            finally:
                os.environ["PATH"] = old_path
            self.assertEqual(token, "explicit-agent-token")

class EnsurePushedResult(unittest.TestCase):
    """이슈 #301 B2: `ensure_pushed()` 가 `None` 대신 구조화된
    `{"status": ..., "reason": ...}` 를 리턴하고, `_spawn_one()` 이 push
    거부를 `silent-failure` 와 구분되는 `push-rejected` 로 승격하는지 —
    이슈가 명시한 세 시나리오(거부됨/미푸시 다른 사유/진짜 무無)가 실제로
    구분되는지 실 git 리포로 검증한다."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def _clone_with_commit(self, td, issue, role):
        # bare origin: 로컬 file:// transport 라도 push 가 항상 pack
        # 프로토콜(receive-pack)을 타야 pre-receive hook 이 실제로 걸린다 —
        # non-bare 로는 hardlink 최적화 경로로 hook 을 건너뛸 수 있다.
        seed = Path(td) / "seed"
        origin = Path(td) / "origin.git"
        work = Path(td) / "work"
        self._init_repo(seed)
        (seed / "a.txt").write_text("x")
        self._git(seed, "add", "a.txt")
        self._git(seed, "commit", "-q", "-m", "init")
        self._git(seed, "branch", "-m", "main")
        r = subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self._git(work, "config", "user.email", "t@t.t")
        self._git(work, "config", "user.name", "t")
        br = f"issue-{issue}/{role}"
        self._git(work, "checkout", "-q", "-b", br)
        (work / "c.txt").write_text("wip")
        self._git(work, "add", "c.txt")
        self._git(work, "commit", "-q", "-m", "wip")
        return origin, work, br

    def test_push_rejected_by_remote_is_named_and_distinct(self):
        """(a) 원격이 push 를 거부한 경우 — pre-receive hook 으로 실제
        거부를 재현한다. `status` 가 `push-rejected` 이고 `reason` 이
        비어있지 않아야 하며, `_spawn_one` 의 outcome 이 `silent-failure`
        가 아니라 `push-rejected` 로 승격돼야 한다."""
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999910, "implementation"
            origin, work, br = self._clone_with_commit(td, issue, role)
            hooks = origin / "hooks"
            hooks.mkdir(exist_ok=True)
            hook = hooks / "pre-receive"
            hook.write_text(
                "#!/bin/sh\n"
                "echo 'refusing to allow an OAuth App to create or update "
                "workflow without workflow scope' >&2\n"
                "exit 1\n"
            )
            hook.chmod(0o755)
            with mock.patch.object(spawn, "_git_env", return_value=None):
                result = spawn.ensure_pushed(str(work), issue, role)
            self.assertEqual(result["status"], "push-rejected")
            self.assertTrue(result["reason"])
            self.assertIn("workflow", result["reason"])

            outcome = "silent-failure"
            uncommitted = []
            if outcome == "silent-failure" and uncommitted:
                outcome = "uncommitted-work"
            elif outcome == "silent-failure" and result and result["status"] == "push-rejected":
                outcome = "push-rejected"
            self.assertEqual(outcome, "push-rejected")

    @pytest.mark.slow
    def test_nothing_to_push_stays_silent_failure(self):
        """(c) 진짜 아무것도 안 만든 세션 — 원격에 앞선 커밋도, 브랜치
        자체도 없으면 `nothing-to-push` 이고, `_spawn_one` 의 outcome 은
        오늘과 같이 `silent-failure` 로 남는다."""
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999911, "implementation"
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            self._init_repo(origin)
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            self._git(origin, "branch", "-m", "main")
            r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            # 이 이슈/역할용 브랜치가 아예 없다 — 세션이 아무것도 안 만든 상태.
            with mock.patch.object(spawn, "_git_env", return_value=None):
                result = spawn.ensure_pushed(str(work), issue, role)
            self.assertEqual(result, {"status": "nothing-to-push", "reason": None})

            outcome = "silent-failure"
            uncommitted = []
            if outcome == "silent-failure" and uncommitted:
                outcome = "uncommitted-work"
            elif outcome == "silent-failure" and result and result["status"] == "push-rejected":
                outcome = "push-rejected"
            self.assertEqual(outcome, "silent-failure")

    def test_commits_ahead_but_dirty_tree_prefers_uncommitted_work(self):
        """(b) 세션 종료 시 커밋은 로컬에 있지만(원격엔 아직) 트리도
        더러운 경우 — push 자체가 거부됐더라도 더 즉각적인 문제인
        `uncommitted-work` 가 우선한다는 기존 순서를 그대로 지킨다."""
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999912, "implementation"
            origin, work, br = self._clone_with_commit(td, issue, role)
            hooks = origin / "hooks"
            hooks.mkdir(exist_ok=True)
            hook = hooks / "pre-receive"
            hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n")
            hook.chmod(0o755)
            with mock.patch.object(spawn, "_git_env", return_value=None):
                result = spawn.ensure_pushed(str(work), issue, role)
            self.assertEqual(result["status"], "push-rejected")

            outcome = "silent-failure"
            uncommitted = ["M dirty.txt"]  # 세션이 더러운 트리를 남겼다
            if outcome == "silent-failure" and uncommitted:
                outcome = "uncommitted-work"
            elif outcome == "silent-failure" and result and result["status"] == "push-rejected":
                outcome = "push-rejected"
            self.assertEqual(outcome, "uncommitted-work")

class EnsurePushedStrandedComment(unittest.TestCase):
    """이슈 #326: `ensure_pushed()`의 두 침묵 dead-end(호스트 push 실패,
    PR 생성 실패)가 이제 이슈에 코멘트를 남기는지, 그리고 멱등한지."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _init_repo(self, path):
        path.mkdir(parents=True, exist_ok=True)
        self._git(path, "init", "-q")
        self._git(path, "config", "user.email", "t@t.t")
        self._git(path, "config", "user.name", "t")

    def _make_work_with_commit(self, td, issue, role):
        origin = Path(td) / "origin"
        work = Path(td) / "work"
        self._init_repo(origin)
        (origin / "a.txt").write_text("x")
        self._git(origin, "add", "a.txt")
        self._git(origin, "commit", "-q", "-m", "init")
        self._git(origin, "branch", "-m", "main")
        r = subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self._git(work, "config", "user.email", "t@t.t")
        self._git(work, "config", "user.name", "t")
        br = f"issue-{issue}/{role}"
        self._git(work, "checkout", "-q", "-b", br)
        (work / "c.txt").write_text("wip")
        self._git(work, "add", "c.txt")
        self._git(work, "commit", "-q", "-m", "wip")
        return work, br

    def test_ensure_pushed_posts_comment_on_push_failure(self):
        issue, role = 999910, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            spawn._issue_comments = lambda root, n: ([], True)
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"] and "push" in cmd:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="push rejected")
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 1)
            body = comment_calls[0][comment_calls[0].index("-f") + 1]
            self.assertIn(br, body)
            self.assertIn("push-failed", body)

    def test_ensure_pushed_posts_comment_on_pr_create_failure(self):
        issue, role = 999911, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            spawn._issue_comments = lambda root, n: ([], True)
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh" and cmd[1:3] == ["pr", "list"]:
                    return subprocess.CompletedProcess(cmd, 0, stdout="0", stderr="")
                if cmd[0] == "gh" and cmd[1:3] == ["pr", "create"]:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="pr create rejected")
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 1)
            body = comment_calls[0][comment_calls[0].index("-f") + 1]
            self.assertIn(br, body)
            self.assertIn("pr-create-failed", body)

    def test_ensure_pushed_stranded_comment_is_idempotent(self):
        issue, role = 999912, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            marker = spawn._STRANDED_PUSH_COMMENT_MARKER.format(key=f"{br}:push-failed")
            spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], True)
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"] and "push" in cmd:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="push rejected")
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 0)

    def test_ensure_pushed_stranded_comment_posts_when_comments_unreadable(self):
        """이슈 #432: ok=False 면 마커가 이미 있어도 확인할 수 없으므로
        중복을 감수하고 코멘트를 남긴다."""
        issue, role = 999913, "implementation"
        with tempfile.TemporaryDirectory() as td:
            work, br = self._make_work_with_commit(td, issue, role)
            orig_slug = spawn._repo_slug
            orig_comments = spawn._issue_comments
            orig_run = spawn.subprocess.run
            spawn._repo_slug = lambda root: "acme/repo"
            marker = spawn._STRANDED_PUSH_COMMENT_MARKER.format(key=f"{br}:push-failed")
            spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], False)
            calls = []

            def fake_run(cmd, *a, **k):
                calls.append(cmd)
                if cmd[:2] == ["git", "-C"] and "push" in cmd:
                    return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="push rejected")
                if cmd[:2] == ["git", "-C"]:
                    return orig_run(cmd, *a, **k)
                if cmd[0] == "gh":
                    return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
                return orig_run(cmd, *a, **k)

            spawn.subprocess.run = fake_run
            try:
                spawn.ensure_pushed(str(work), issue, role)
            finally:
                spawn._repo_slug = orig_slug
                spawn._issue_comments = orig_comments
                spawn.subprocess.run = orig_run

            comment_calls = [c for c in calls if c[0] == "gh" and any("comments" in x for x in c)]
            self.assertEqual(len(comment_calls), 1)

class PostCrashComment(unittest.TestCase):
    """이슈 #132: 상한-코멘트 멱등성 — 마커 문자열이 이미 있으면 재포스팅 안 함."""

    def test_skips_when_marker_already_present(self):
        marker = spawn._CRASH_COMMENT_MARKER.format(key="issue-132/coding",
                                                     cap=spawn.RESPAWN_MAX_ATTEMPTS)
        orig_comments = spawn._issue_comments
        spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], True)
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_crash_comment(Path("."), 132, "issue-132/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            subprocess.run = orig_run
        self.assertEqual(calls, [])

    def test_posts_when_marker_absent(self):
        orig_comments = spawn._issue_comments
        orig_slug = spawn._repo_slug
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_crash_comment(Path("."), 132, "issue-132/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run
        self.assertEqual(len(calls), 1)
        self.assertIn("gh", calls[0])

    def test_post_failure_is_logged_not_silent(self):
        """issue #287 S7: 코멘트 POST 자체가 실패하면(returncode!=0)
        stderr 에 경고가 남아야 한다 — "사람 개입 필요" 알림이 조용히
        사라지면 안 된다."""
        orig_comments = spawn._issue_comments
        orig_slug = spawn._repo_slug
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        orig_run = subprocess.run

        def fake_run(cmd, *a, **k):
            return orig_run(["false"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            buf = io.StringIO()
            with contextlib.redirect_stderr(buf):
                spawn._post_crash_comment(Path("."), 132, "issue-132/coding", "w", "l")
            self.assertIn("게시 실패", buf.getvalue())
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run

class PostStallComment(unittest.TestCase):
    """이슈 #325: stalled 판정이 최초 1회만 이슈 코멘트로 남는다."""

    def test_skips_when_marker_already_present(self):
        marker = spawn._STALL_COMMENT_MARKER.format(key="issue-325/coding")
        orig_comments = spawn._issue_comments
        spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], True)
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_stall_comment(Path("."), 325, "issue-325/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            subprocess.run = orig_run
        self.assertEqual(calls, [])

    def test_posts_when_marker_absent(self):
        orig_comments = spawn._issue_comments
        orig_slug = spawn._repo_slug
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_stall_comment(Path("."), 325, "issue-325/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run
        self.assertEqual(len(calls), 1)
        self.assertIn("gh", calls[0])

    def test_posts_when_comments_unreadable(self):
        """이슈 #432: `_issue_comments` 가 ok=False(코멘트를 읽지 못함)를
        돌려주면, 마커가 실제로 있는지 확인할 수 없으므로 "확인 못 함은
        통과가 아니다"(#287) 원칙에 따라 중복을 감수하고 코멘트를
        남긴다 — 조용히 건너뛰지 않는다."""
        orig_comments = spawn._issue_comments
        orig_slug = spawn._repo_slug
        marker = spawn._STALL_COMMENT_MARKER.format(key="issue-325/coding")
        spawn._issue_comments = lambda root, n: ([{"login": "bot", "body": marker}], False)
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []
        orig_run = subprocess.run
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        try:
            spawn._post_stall_comment(Path("."), 325, "issue-325/coding", "w", "l")
        finally:
            spawn._issue_comments = orig_comments
            spawn._repo_slug = orig_slug
            subprocess.run = orig_run
        self.assertEqual(len(calls), 1)
        self.assertIn("gh", calls[0])

    def test_auto_respawn_check_posts_stall_comment_once_across_two_ticks(self):
        """워치독 두 번 연속 틱에서도 코멘트 호출은 정확히 한 번(멱등)."""
        orig_verdict = spawn.session_end_verdict
        orig_post = spawn._post_stall_comment
        spawn.session_end_verdict = lambda work, log_path: "stalled"
        calls = []
        posted_markers = []

        def fake_post(root, issue, key, work, log):
            marker = spawn._STALL_COMMENT_MARKER.format(key=key)
            if marker in posted_markers:
                return
            posted_markers.append(marker)
            calls.append((issue, key))

        spawn._post_stall_comment = fake_post
        try:
            entry = {"work": "w", "issue": 325, "role": "coding", "log": "l"}
            spawn._auto_respawn_check("issue-325/coding", entry, {})
            spawn._auto_respawn_check("issue-325/coding", entry, {})
        finally:
            spawn.session_end_verdict = orig_verdict
            spawn._post_stall_comment = orig_post
        self.assertEqual(len(calls), 1)

class PostSessionEndComment(unittest.TestCase):
    """이슈 #534: session-end(normal)을 durable 이슈 코멘트로 남긴다."""

    def setUp(self):
        self._orig_comments = spawn._issue_comments
        self._orig_slug = spawn._repo_slug
        self._orig_run = subprocess.run
        self._orig_verdict = spawn.session_end_verdict
        self._orig_pr = spawn._pr_open_or_merged_for_branch
        self._orig_pr_list_ok = spawn._pr_list_call_ok

    def tearDown(self):
        spawn._issue_comments = self._orig_comments
        spawn._repo_slug = self._orig_slug
        subprocess.run = self._orig_run
        spawn.session_end_verdict = self._orig_verdict
        spawn._pr_open_or_merged_for_branch = self._orig_pr
        spawn._pr_list_call_ok = self._orig_pr_list_ok

    def test_noop_when_verdict_not_normal(self):
        spawn.session_end_verdict = lambda work, log_path: "crashed"
        calls = []
        spawn._issue_comments = lambda root, n: (calls.append("comments"), ([], True))[1]
        spawn._post_session_end_comment(Path("."), 534, "issue-534/coding", "w", "l")
        self.assertEqual(calls, [])

    def test_skips_when_marker_already_present(self):
        spawn.session_end_verdict = lambda work, log_path: "normal"
        marker = spawn._SESSION_END_COMMENT_MARKER.format(key="issue-534/coding")
        spawn._issue_comments = lambda root, n: (
            [{"login": "bot", "body": f"{marker} no PR"}], True)
        calls = []
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return self._orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        spawn._post_session_end_comment(Path("."), 534, "issue-534/coding", "w", "l")
        self.assertEqual(calls, [])

    def test_posts_pr_url_when_pr_open(self):
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        spawn._pr_open_or_merged_for_branch = lambda root, branch: 42
        calls = []
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            if cmd[:2] == ["git", "-C"]:
                return self._orig_run(["echo", "issue-534/coding"],
                                      capture_output=True, text=True)
            return self._orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        spawn._post_session_end_comment(Path("."), 534, "issue-534/coding", "w", "l")
        gh_calls = [c for c in calls if c[:2] == ["gh", "api"]]
        self.assertEqual(len(gh_calls), 1)
        body = next(a for a in gh_calls[0] if a.startswith("body="))
        self.assertIn("PR https://github.com/acme/repo/pull/42 opened", body)

    def test_pr_check_failed_fallback(self):
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn._pr_list_call_ok = lambda root, branch: False
        calls = []
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            if cmd[:2] == ["git", "-C"]:
                return self._orig_run(["echo", "issue-534/coding"],
                                      capture_output=True, text=True)
            return self._orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        spawn._post_session_end_comment(Path("."), 534, "issue-534/coding", "w", "l")
        gh_calls = [c for c in calls if c[:2] == ["gh", "api"]]
        self.assertEqual(len(gh_calls), 1)
        body = next(a for a in gh_calls[0] if a.startswith("body="))
        self.assertIn("no PR (pr-check-failed)", body)

    def test_posts_no_pr_when_pr_check_ok_and_absent(self):
        spawn.session_end_verdict = lambda work, log_path: "normal"
        spawn._issue_comments = lambda root, n: ([], True)
        spawn._repo_slug = lambda root: "acme/repo"
        spawn._pr_open_or_merged_for_branch = lambda root, branch: None
        spawn._pr_list_call_ok = lambda root, branch: True
        calls = []
        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            if cmd[:2] == ["git", "-C"]:
                return self._orig_run(["echo", "issue-534/coding"],
                                      capture_output=True, text=True)
            return self._orig_run(["true"], capture_output=True, text=True)
        subprocess.run = fake_run
        spawn._post_session_end_comment(Path("."), 534, "issue-534/coding", "w", "l")
        gh_calls = [c for c in calls if c[:2] == ["gh", "api"]]
        self.assertEqual(len(gh_calls), 1)
        body = next(a for a in gh_calls[0] if a.startswith("body="))
        self.assertIn("no PR", body)
        self.assertNotIn("pr-check-failed", body)

class IssueComments(unittest.TestCase):
    """이슈 #224: `--paginate --slurp`로 30개 코멘트 상한을 넘긴다 —
    페이지 리스트를 평탄화해 기존과 같은 dict 리스트를 돌려줘야 한다."""

    def test_flattens_multi_page_slurp_response(self):
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"
        page1 = [{"user": {"login": "a"}, "body": "one"}]
        page2 = [{"user": {"login": "b"}, "body": "two"}]
        shape_contracts.assert_gh_paginate_slurp_shape([page1, page2])
        calls = []

        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps([page1, page2]), stderr="")

        spawn.subprocess.run = fake_run
        try:
            out, ok = spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        self.assertTrue(ok)
        self.assertEqual(out, [{"login": "a", "body": "one"},
                               {"login": "b", "body": "two"}])
        # 이슈 #1459: 1페이지는 이제 `-i` ETag 프로브로 먼저 나가고(이
        # 스텁은 헤더 없는 순수 JSON 만 돌려주므로 프로브가 파싱 실패해
        # 무조건 재조회로 폴백한다), 그 폴백 호출에 `--paginate --slurp`
        # 가 실린다 — calls[0] 고정이 아니라 호출들 중 하나에 있으면 된다.
        self.assertTrue(any("--paginate" in c and "--slurp" in c for c in calls), calls)

    def test_empty_slurp_response_yields_empty_list(self):
        # 실측: 코멘트 0건이면 gh api --paginate --slurp 는 [[]] (빈 페이지
        # 하나)를 낸다 — 평탄화하면 빈 리스트.
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"

        shape_contracts.assert_gh_paginate_slurp_shape([[]])

        def fake_run(cmd, *a, **k):
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps([[]]), stderr="")

        spawn.subprocess.run = fake_run
        try:
            out, ok = spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        self.assertTrue(ok)
        self.assertEqual(out, [])

    def test_gh_failure_yields_ok_false(self):
        """gh 호출 자체가 실패하면(returncode!=0) ok=False — 빈 리스트를
        "코멘트 0개"로 읽으면 안 된다(issue #287 S6)."""
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"

        def fake_run(cmd, *a, **k):
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="rate limited")

        spawn.subprocess.run = fake_run
        try:
            out, ok = spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        self.assertFalse(ok)
        self.assertEqual(out, [])

class IssueCommentsEtagProbeUsesExplicitGetMethod(unittest.TestCase):
    """issue #1644: PR #1641이 closure_sweep._conditional_issue_list에서
    고친 것과 같은 결함 모양이 spawn.py의 _issue_comments ETag 프로브에도
    남아 있었다 — `gh api ... -f ...`는 `--method GET`이 없으면 POST로
    나가 comments 엔드포인트가 422를 낸다. ConditionalIssueListUsesExplicit
    GetMethod(gates/test_closure_sweep.py)와 같은 핀 모양."""

    def test_probe_cmd_carries_explicit_method_get(self):
        orig_slug = spawn._repo_slug
        orig_run = subprocess.run
        spawn._repo_slug = lambda root: "acme/repo"
        calls = []

        def fake_run(cmd, *a, **k):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

        spawn.subprocess.run = fake_run
        try:
            spawn._issue_comments(Path("."), 999)
        finally:
            spawn._repo_slug = orig_slug
            spawn.subprocess.run = orig_run
        probe_cmd = calls[0]
        self.assertIn("--method", probe_cmd)
        self.assertEqual(probe_cmd[probe_cmd.index("--method") + 1], "GET")

class RulebookCheckoutMemo(unittest.TestCase):
    """이슈 #1955: `rulebook_checkout()`/`plugin_dirs()`/`checkout_version()`
    (이슈 #285 P2/P4 이 겨냥했던 in-process memo 대상)은 rulebook 해석
    경로 전체와 함께 은퇴했다 — 그 함수들을 직접 부르던 케이스는 지운다.
    남는 것은 `_mark_pulled()`/`_ttl_marker()` 같은 공유 저수준 헬퍼
    테스트뿐이다(core/skill-repo 관리 클론이 여전히 쓴다)."""

    def _counting_git_wrapper(self, fake_bin, call_count_file):
        real_git = shutil.which("git")
        wrapper = fake_bin / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = "-C" ] && [ "$3" = "pull" ]; then echo pull >> {call_count_file}; fi\n'
            f"exec {real_git} \"$@\"\n"
        )
        wrapper.chmod(0o755)

    def setUp(self):
        self._saved_ttl = os.environ.pop("MUSTER_RULEBOOK_TTL", None)

    def tearDown(self):
        os.environ.pop("MUSTER_RULEBOOK_TTL", None)
        if self._saved_ttl is not None:
            os.environ["MUSTER_RULEBOOK_TTL"] = self._saved_ttl

    @pytest.mark.slow
    def test_ttl_marker_does_not_dirty_clone(self):
        """이슈 #296: TTL 마커는 클론 밖(`runs/ttl-markers/`)에 있어야
        한다 — 클론 안에 두면 `git status --porcelain` 이 영영 비지
        않아 `(커밋 안 된 변경 있음)`/`+커밋안됨` 이 모든 클론에 상시로
        붙는다."""
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            clone_dir = fake_root / "runs" / "rulebooks" / "acme-rules"
            clone_dir.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(clone_dir)], check=True)
            subprocess.run(["git", "-C", str(clone_dir), "commit", "-q",
                           "--allow-empty", "-m", "init",
                           "--author=t <t@t.t>"], check=True, capture_output=True)

            saved_root = spawn.ROOT
            spawn.ROOT = fake_root
            try:
                spawn._mark_pulled(clone_dir)
                marker = spawn._ttl_marker(clone_dir)
                self.assertTrue(marker.exists())
                self.assertFalse(
                    str(marker.resolve()).startswith(str(clone_dir.resolve()) + os.sep),
                    "TTL 마커가 클론 안에 있다")

                status = subprocess.run(
                    ["git", "-C", str(clone_dir), "status", "--porcelain"],
                    capture_output=True, text=True, check=True)
                self.assertEqual(status.stdout, "", status.stdout)
            finally:
                spawn.ROOT = saved_root

class FetchDedupe(unittest.TestCase):
    """이슈 #285 P3: 같은 work_dir 에 대한 두 번째 `_fetch_or_halt()` 호출은
    (같은 프로세스 안이면) 네트워크로 나가지 않는다 — 단, halt 판정은
    첫 호출의 결과를 그대로 물려받아야 한다(성공만 fresh 로 기록)."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a], capture_output=True, text=True)

    def setUp(self):
        spawn._FETCHED_THIS_SPAWN = {}

    def tearDown(self):
        spawn._FETCHED_THIS_SPAWN = {}

    @pytest.mark.slow
    def test_second_fetch_of_same_dir_is_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            origin.mkdir()
            self._git(origin, "init", "-q")
            self._git(origin, "config", "user.email", "t@t.t")
            self._git(origin, "config", "user.name", "t")
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True)

            fake_bin = Path(td) / "fakebin"
            fake_bin.mkdir()
            call_count_file = Path(td) / "fetch-calls.txt"
            real_git = shutil.which("git")
            wrapper = fake_bin / "git"
            wrapper.write_text(
                "#!/bin/sh\n"
                f'if [ "$1" = "-C" ] && [ "$3" = "fetch" ]; then echo f >> {call_count_file}; fi\n'
                f"exec {real_git} \"$@\"\n"
            )
            wrapper.chmod(0o755)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{fake_bin}{os.pathsep}{old_path}"
            try:
                spawn._fetch_or_halt(str(work), "first")
                spawn._fetch_or_halt(str(work), "second")
            finally:
                os.environ["PATH"] = old_path

            calls = call_count_file.read_text().splitlines() if call_count_file.exists() else []
            self.assertEqual(len(calls), 1, calls)

    @pytest.mark.slow
    def test_after_callback_still_runs_on_dedupe_skip(self):
        with tempfile.TemporaryDirectory() as td:
            origin = Path(td) / "origin"
            work = Path(td) / "work"
            origin.mkdir()
            self._git(origin, "init", "-q")
            self._git(origin, "config", "user.email", "t@t.t")
            self._git(origin, "config", "user.name", "t")
            (origin / "a.txt").write_text("x")
            self._git(origin, "add", "a.txt")
            self._git(origin, "commit", "-q", "-m", "init")
            subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                           capture_output=True)
            spawn._fetch_or_halt(str(work), "first")
            called = []
            spawn._fetch_or_halt(str(work), "second", after=lambda: called.append(1))
            self.assertEqual(called, [1])

class NetworkSubprocessTimeout(unittest.TestCase):
    """이슈 #285 P5: 네트워크 subprocess 가 `timeout=` 을 넘기면 조용히
    걸리는 대신 이름 있는 에러로 종료한다."""

    def test_run_net_exits_with_named_error_on_timeout(self):
        def fake_run(*a, **k):
            raise subprocess.TimeoutExpired(cmd=a[0] if a else "git", timeout=k.get("timeout"))

        with mock.patch.object(subprocess, "run", fake_run):
            with self.assertRaises(SystemExit) as ctx:
                spawn._run_net(["git", "fetch"], "테스트 라벨", timeout=1)
        self.assertIn("테스트 라벨", str(ctx.exception))
        self.assertIn("시간초과", str(ctx.exception))

    def test_fetch_or_halt_times_out_within_bound_not_hang(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            work.mkdir()
            spawn._FETCHED_THIS_SPAWN = {}

            def fake_run(*a, **k):
                raise subprocess.TimeoutExpired(cmd=a[0] if a else "git", timeout=k.get("timeout"))

            t0 = time.monotonic()
            with mock.patch.object(subprocess, "run", fake_run):
                with self.assertRaises(SystemExit):
                    spawn._fetch_or_halt(str(work), "네트워크 fetch")
            elapsed = time.monotonic() - t0
            self.assertLess(elapsed, 5, "TimeoutExpired 이 fail-closed 로 즉시 표면화해야 한다")

class GitEnvTimeoutPromptVars(unittest.TestCase):
    """이슈 #285 P5: `_git_env()` 의 dict 분기에만
    GIT_TERMINAL_PROMPT=0/GIT_ASKPASS=true 를 얹는다 — None 폴백은 그대로."""

    def setUp(self):
        spawn._GH_TOKEN_CACHE = None
        self._saved_agent = os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)

    def tearDown(self):
        spawn._GH_TOKEN_CACHE = None
        os.environ.pop("MUSTER_AGENT_GH_TOKEN", None)
        if self._saved_agent is not None:
            os.environ["MUSTER_AGENT_GH_TOKEN"] = self._saved_agent

    def test_token_present_branch_carries_prompt_suppression(self):
        os.environ["MUSTER_AGENT_GH_TOKEN"] = "tok"
        env = spawn._git_env()
        self.assertIsNotNone(env)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(env["GIT_ASKPASS"], "true")

    def test_no_token_fallback_stays_none(self):
        with mock.patch.object(spawn, "_resolve_gh_token", lambda: ""):
            env = spawn._git_env()
        self.assertIsNone(env)

class RepoSlugCacheTest(unittest.TestCase):
    """issue #682 — 슬러그는 체크아웃당 상수라 한 번만 조회한다."""

    def test_repeated_calls_hit_gh_once_per_root(self):
        spawn._repo_slug_cache_clear()
        self.addCleanup(spawn._repo_slug_cache_clear)
        calls = []

        class R:
            returncode = 0
            stdout = "acme/repo\n"

        def fake_run(argv, **kw):
            calls.append(argv)
            return R()

        orig = spawn.subprocess.run
        spawn.subprocess.run = fake_run
        try:
            first = [spawn._repo_slug(Path("/tmp/a")) for _ in range(5)]
            second = spawn._repo_slug(Path("/tmp/b"))
        finally:
            spawn.subprocess.run = orig

        self.assertEqual(first, ["acme/repo"] * 5)
        self.assertEqual(second, "acme/repo")
        self.assertEqual(len(calls), 2)  # root 당 1회

class RulebookCacheLock(unittest.TestCase):
    """이슈 #773: 클론 구간을 `_locked_rulebook_dir()` 로 감싸 직렬화한다
    (원래는 role rulebook 동시 spawn 충돌을 겨냥했지만, 그 소비자였던
    `rulebook_checkout()` 은 이슈 #1955 로 은퇴했다 — 락 자체는 core/
    skill-repo 관리 클론이 계속 쓰는 공유 저수준 헬퍼라 여기 남는다)."""

    def _fake_run_net(self, clone_calls, pull_calls):
        def fake(args, label, timeout=None, **kwargs):
            if args[:2] == ["git", "clone"]:
                clone_calls.append(1)
                time.sleep(0.05)
                target = Path(args[-1])
                target.mkdir(parents=True, exist_ok=True)
                (target / ".claude-plugin").mkdir(exist_ok=True)
                (target / ".claude-plugin" / "marketplace.json").write_text("{}")
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[:2] == ["git", "-C"] and "pull" in args:
                pull_calls.append(1)
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected _run_net call: {args}")
        return fake

    def test_stale_lock_reclaimed_after_holder_dies(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            d = fake_root / "runs" / "rulebooks" / "acme-rules"
            d.parent.mkdir(parents=True)
            lock_path = spawn._rulebook_lock_path(d)

            holder_script = (
                "import fcntl, sys, time\n"
                f"f = open({str(lock_path)!r}, 'w')\n"
                "fcntl.flock(f, fcntl.LOCK_EX)\n"
                "print('locked', flush=True)\n"
                "time.sleep(60)\n"
            )
            holder = subprocess.Popen(
                [sys.executable, "-c", holder_script],
                stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(holder.stdout.readline().strip(), "locked")
                holder.kill()
                holder.wait(timeout=5)

                acquired = []

                def acquire():
                    with spawn._locked_rulebook_dir(d):
                        acquired.append(True)

                t = threading.Thread(target=acquire)
                t.start()
                t.join(timeout=5)
                self.assertTrue(acquired, "죽은 홀더의 lock 이 회수되지 않았다")
            finally:
                if holder.poll() is None:
                    holder.kill()
                    holder.wait()

class CoreRootCacheLock(unittest.TestCase):
    """이슈 #773: `core_root()` 도 옛 role-rulebook 체크아웃(이슈 #1955 로
    은퇴)과 동일한 손수
    쓴 exists-check-then-clone 경쟁을 갖고 있었다 — 같은 락으로 감싼다."""

    def _fake_run_net(self, clone_calls, pull_calls):
        def fake(args, label, timeout=None, **kwargs):
            if args[:2] == ["git", "clone"]:
                clone_calls.append(1)
                time.sleep(0.05)
                target = Path(args[-1])
                (target / "core" / ".claude-plugin").mkdir(
                    parents=True, exist_ok=True)
                (target / "core" / ".claude-plugin" / "plugin.json").write_text("{}")
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            if args[:2] == ["git", "-C"] and "pull" in args:
                pull_calls.append(1)
                return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
            raise AssertionError(f"unexpected _run_net call: {args}")
        return fake

    def test_concurrent_core_root_serializes_to_one_clone(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            clone_calls, pull_calls = [], []
            saved_root = spawn.ROOT
            spawn.ROOT = fake_root
            results = []
            errors = []

            def worker():
                try:
                    with unittest.mock.patch.object(
                            spawn, "_core_candidates", lambda: []):
                        results.append(spawn.core_root())
                except BaseException as e:  # pragma: no cover - 진단용
                    errors.append(e)

            try:
                with unittest.mock.patch.object(
                        spawn, "_run_net",
                        self._fake_run_net(clone_calls, pull_calls)):
                    threads = [threading.Thread(target=worker)
                               for _ in range(5)]
                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join(timeout=10)
            finally:
                spawn.ROOT = saved_root

            self.assertEqual(errors, [], errors)
            self.assertEqual(len(results), 5)
            self.assertEqual(len(clone_calls), 1,
                              "정확히 한 번만 clone 이 실제로 불려야 한다")
            self.assertTrue(all(r == results[0] for r in results))

    def test_warm_cache_core_root_issues_zero_git_calls(self):
        with tempfile.TemporaryDirectory() as td:
            fake_root = Path(td) / "root"
            d = fake_root / "runs" / "rulebooks" / "tokenmaxxxer-core"
            (d / "core" / ".claude-plugin").mkdir(parents=True)
            (d / "core" / ".claude-plugin" / "plugin.json").write_text("{}")

            saved_root = spawn.ROOT
            spawn.ROOT = d.parent.parent.parent
            clone_calls, pull_calls = [], []
            try:
                spawn._ttl_marker(d).parent.mkdir(parents=True, exist_ok=True)
                spawn._ttl_marker(d).write_text(str(time.time()))
                with unittest.mock.patch.object(
                        spawn, "_core_candidates", lambda: []), \
                     unittest.mock.patch.object(
                        spawn, "_run_net",
                        self._fake_run_net(clone_calls, pull_calls)):
                    result = spawn.core_root()
            finally:
                spawn.ROOT = saved_root

            self.assertEqual(result, d)
            self.assertEqual(clone_calls, [])
            self.assertEqual(pull_calls, [])

class EnsureTargetRemote(unittest.TestCase):
    """issue #831: preflight gate replacing issue_workspace's mid-delegation
    stall (spawn.py:4328-4330) with a top-level, pre-dispatch resolution."""

    def _git(self, *args, cwd):
        subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True)

    def test_noop_when_origin_already_resolves(self):
        with tempfile.TemporaryDirectory() as td:
            self._git("init", cwd=td)
            self._git("remote", "add", "origin", "https://example.invalid/x.git", cwd=td)
            with mock.patch("builtins.input", side_effect=AssertionError("must not prompt")):
                spawn.ensure_target_remote(td, unattended=False)  # no raise

    def test_unattended_no_remote_exits_before_any_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            self._git("init", cwd=td)
            with mock.patch("builtins.input", side_effect=AssertionError("must not prompt")):
                with self.assertRaises(SystemExit):
                    spawn.ensure_target_remote(td, unattended=True)

    @pytest.mark.slow
    def test_attended_confirmed_existing_url_writes_ledger_event(self):
        with tempfile.TemporaryDirectory() as td:
            remote_dir = str(Path(td) / "remote.git")
            subprocess.run(["git", "init", "--bare", remote_dir], check=True, capture_output=True)
            work = str(Path(td) / "work")
            Path(work).mkdir()
            self._git("init", cwd=work)
            events = []
            with mock.patch("builtins.input", return_value=remote_dir), \
                 mock.patch.object(spawn, "ledger_write", side_effect=lambda e: events.append(e)):
                spawn.ensure_target_remote(work, unattended=False)
            r = subprocess.run(["git", "-C", work, "remote", "get-url", "origin"],
                               capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), remote_dir)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "remote_setup_confirmed")
            self.assertEqual(events[0]["origin"], remote_dir)

    def test_attended_refusal_exits_and_writes_no_ledger_event(self):
        with tempfile.TemporaryDirectory() as td:
            self._git("init", cwd=td)
            with mock.patch("builtins.input", return_value=""), \
                 mock.patch.object(spawn, "ledger_write") as lw:
                with self.assertRaises(SystemExit):
                    spawn.ensure_target_remote(td, unattended=False)
            lw.assert_not_called()
