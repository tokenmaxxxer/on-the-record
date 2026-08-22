"""issue #2022: `spawn.py init` must commit and push the board files, or
fail loudly when push is impossible — otherwise a fresh clone can't see
approvers.md and board-gate strands the first spawn (skill-repository #50)."""
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


class InitPushesBoardFiles(unittest.TestCase):
    def test_init_commits_and_pushes_to_bare_remote(self):
        with tempfile.TemporaryDirectory() as td:
            bare, clone = _bare_and_clone(td)
            rc = spawn.init_board(str(clone), login="alice")
            self.assertEqual(rc, 0)

            other = Path(td) / "checkout"
            subprocess.run(["git", "clone", "-q", str(bare), str(other)], check=True)
            self.assertTrue((other / spawn.MARKER).is_file())
            self.assertEqual((other / spawn.MARKER).read_text(encoding="utf-8"), "- alice\n")

            log = subprocess.run(["git", "-C", str(clone), "log", "-1", "--format=%B",
                                  "HEAD"], capture_output=True, text=True, check=True)
            self.assertIn("Subject: board-setup", log.stdout)

    def test_init_exits_nonzero_and_warns_when_push_impossible(self):
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
                spawn.init_board(str(work), login="alice")
            msg = str(ctx.exception)
            self.assertIn("push", msg)
            self.assertIn("스폰", msg)
            # commit itself must have gone through even though push failed
            log = subprocess.run(["git", "-C", str(work), "log", "-1", "--format=%B"],
                                 capture_output=True, text=True, check=True)
            self.assertIn("Subject: board-setup", log.stdout)


if __name__ == "__main__":
    unittest.main()
