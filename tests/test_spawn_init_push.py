"""issue #2022 → #2125: `spawn.py init` must VERIFY the board is on the
remote (every workspace clones from the remote; a remote-invisible board
strands every spawn at admission, #2123/#2126). Contract:

- remote default branch already carries the marker -> quiet exit 0;
- marker not on the remote (or no origin) -> nonzero, with a
  copy-pasteable add+commit+push block naming the CURRENT branch and the
  "board not yet on the remote" warning;
- `init --push` -> add+commit+push directly, exit 0."""
from _spawn_test_support import *  # noqa: F401,F403


def _bare_and_clone(td):
    bare = Path(td) / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    clone = Path(td) / "clone"
    subprocess.run(["git", "clone", "-q", str(bare), str(clone)], check=True)
    subprocess.run(["git", "-C", str(clone), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(clone), "config", "user.name", "t"], check=True)
    (clone / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(clone), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(clone), "commit", "-q", "-m", "init"], check=True)
    subprocess.run(["git", "-C", str(clone), "push", "-q", "-u", "origin", "HEAD"], check=True)
    return bare, clone


def _branch(cwd):
    return subprocess.run(["git", "-C", str(cwd), "symbolic-ref", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()


class InitPushFlagPushesBoardFiles(unittest.TestCase):
    def test_init_push_commits_and_pushes_to_bare_remote(self):
        with tempfile.TemporaryDirectory() as td:
            bare, clone = _bare_and_clone(td)
            rc = spawn.init_board(str(clone), login="alice", push=True)
            self.assertEqual(rc, 0)

            other = Path(td) / "checkout"
            subprocess.run(["git", "clone", "-q", str(bare), str(other)], check=True)
            self.assertTrue((other / spawn.MARKER).is_file())
            self.assertEqual((other / spawn.MARKER).read_text(encoding="utf-8"), "- alice\n")
            # requirement digest travels with the marker (issue #1695)
            self.assertTrue((other / spawn.REQUIREMENT_DIGEST_MARKER).is_file())

            log = subprocess.run(["git", "-C", str(clone), "log", "-1", "--format=%B",
                                  "HEAD"], capture_output=True, text=True, check=True)
            self.assertIn("Subject: board-setup", log.stdout)

    def test_init_push_exits_nonzero_and_warns_when_push_impossible(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            subprocess.run(["git", "init", "-q", str(work)], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True)
            (work / "README.md").write_text("x\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(work), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "init"], check=True)
            # no origin remote configured -> push is impossible

            with self.assertRaises(SystemExit) as ctx:
                spawn.init_board(str(work), login="alice", push=True)
            msg = str(ctx.exception)
            self.assertIn("push", msg)
            self.assertIn("스폰", msg)
            # commit itself must have gone through even though push failed
            log = subprocess.run(["git", "-C", str(work), "log", "-1", "--format=%B"],
                                 capture_output=True, text=True, check=True)
            self.assertIn("Subject: board-setup", log.stdout)


class InitVerifiesRemote(unittest.TestCase):
    """issue #2125: init without --push must verify remote presence and
    either stay quiet (already pushed) or print an actionable block."""

    def test_no_remote_marker_exits_nonzero_with_current_branch_block(self):
        with tempfile.TemporaryDirectory() as td:
            bare, clone = _bare_and_clone(td)
            branch = _branch(clone)
            self.assertTrue(branch)
            buf_err = io.StringIO()
            with contextlib.redirect_stderr(buf_err):
                rc = spawn.init_board(str(clone), login="alice")
            self.assertNotEqual(rc, 0)
            err = buf_err.getvalue()
            self.assertIn("board not yet on the remote", err)
            self.assertIn("refused at admission", err)
            self.assertIn(f"git push --set-upstream origin {branch}", err)
            self.assertIn(f"git add {spawn.MARKER}", err)
            # nothing was committed — the block is for the human to run
            log = subprocess.run(["git", "-C", str(clone), "log", "-1", "--format=%B"],
                                 capture_output=True, text=True, check=True)
            self.assertNotIn("board-setup", log.stdout)

    def test_no_origin_at_all_exits_nonzero_with_guidance(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td) / "work"
            subprocess.run(["git", "init", "-q", str(work)], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True)
            (work / "README.md").write_text("x\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(work), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "init"], check=True)
            branch = _branch(work)
            buf_err = io.StringIO()
            with contextlib.redirect_stderr(buf_err):
                rc = spawn.init_board(str(work), login="alice")
            self.assertNotEqual(rc, 0)
            err = buf_err.getvalue()
            self.assertIn("board not yet on the remote", err)
            self.assertIn(f"git push --set-upstream origin {branch}", err)

    def test_already_pushed_board_exits_zero_quietly(self):
        with tempfile.TemporaryDirectory() as td:
            bare, clone = _bare_and_clone(td)
            # board files already committed and pushed
            rc = spawn.init_board(str(clone), login="alice", push=True)
            self.assertEqual(rc, 0)
            # remote probe answers True for this slug
            with mock.patch.object(spawn, "_repo_slug", lambda root: "o/r"), \
                 mock.patch.object(spawn, "_board_marker_probe", lambda slug: True):
                buf_out, buf_err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
                    rc = spawn.init_board(str(clone), login="alice")
            self.assertEqual(rc, 0)
            self.assertNotIn("board not yet on the remote", buf_err.getvalue())
            self.assertNotIn("git push", buf_err.getvalue())


if __name__ == "__main__":
    unittest.main()
