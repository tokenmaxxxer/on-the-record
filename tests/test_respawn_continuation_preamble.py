from _spawn_test_support import *  # noqa: F401,F403


class RespawnContinuationPreamble(unittest.TestCase):
    """이슈 #1982: reconcile RESPAWN_IDENTICAL 이 dirty workspace 를 만나는
    respawn 경로에서, `_classify_workspace_completion()` 이 "finished" 로
    판정하면 continuation preamble 이 붙고, "unfinished" 로 판정하면
    `.task.txt` 원문과 byte-identical 이다."""

    ORIGINAL_TASK = "원래 맡길 일"

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
        Path(str(work) + ".task.txt").write_text(self.ORIGINAL_TASK)
        return work, run

    def _run_respawn(self, work):
        state = {}
        called = []
        orig = spawn._spawn_one
        spawn._spawn_one = lambda *a, **k: called.append(a)
        try:
            spawn._respawn_or_cap("issue-1982/implementation", str(work), 1982,
                                  "implementation", "l", 1, state,
                                  "self-triggered-abandoned")
        finally:
            spawn._spawn_one = orig
        self.assertEqual(len(called), 1)
        # _spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)
        return called[0][2]

    @pytest.mark.slow
    def test_finished_dirty_workspace_gets_continuation_preamble(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            record_dir = work / "docs" / "issue-1982" / "reports"
            record_dir.mkdir(parents=True)
            (record_dir / "implementation.md").write_text(
                "---\ntype: implementation\nloop_state: landed\n---\n\n"
                "## Summary of work\n\nDid the thing.\n")
            task = self._run_respawn(work)
            self.assertIn(spawn._CONTINUATION_PREAMBLE, task)
            self.assertIn(self.ORIGINAL_TASK, task)

    @pytest.mark.slow
    def test_unfinished_dirty_workspace_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            # dirty, but no record-shape-required path touched — code-only
            # scratch change.
            (work / "f.txt").write_text("y")
            task = self._run_respawn(work)
            self.assertEqual(task, self.ORIGINAL_TASK)

    @pytest.mark.slow
    def test_frontmatter_only_stub_stays_unfinished(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            record_dir = work / "docs" / "issue-1982" / "reports"
            record_dir.mkdir(parents=True)
            (record_dir / "implementation.md").write_text(
                "---\ntype: implementation\nloop_state: coding\n---\n")
            task = self._run_respawn(work)
            self.assertEqual(task, self.ORIGINAL_TASK)

    @pytest.mark.slow
    def test_clean_workspace_task_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            task = self._run_respawn(work)
            self.assertEqual(task, self.ORIGINAL_TASK)


class ClassifyWorkspaceCompletion(unittest.TestCase):
    """`_classify_workspace_completion()` 자체 단위 테스트."""

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
        return work, run

    def test_clean_tree_is_unfinished(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            self.assertEqual(
                spawn._classify_workspace_completion(str(work), "implementation"),
                "unfinished")

    def test_dirty_with_no_record_file_is_unfinished(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            (work / "f.txt").write_text("y")
            self.assertEqual(
                spawn._classify_workspace_completion(str(work), "implementation"),
                "unfinished")

    def test_dirty_with_nontrivial_record_body_is_finished(self):
        with tempfile.TemporaryDirectory() as td:
            work, run = self._prep_repo(td)
            record_dir = work / "docs" / "issue-1982" / "proposals"
            record_dir.mkdir(parents=True)
            (record_dir / "foo.md").write_text(
                "---\nstatus: proposed\n---\n\n## Request\n\nreal content\n")
            self.assertEqual(
                spawn._classify_workspace_completion(str(work), "implementation"),
                "finished")
