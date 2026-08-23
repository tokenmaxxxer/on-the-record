from _spawn_test_support import *  # noqa: F401,F403


def _prep_workspace(td, issue, role, task_text="original stale task"):
    """Real git workspace + stored `.task.txt`, same shape as the
    RespawnContinuationPreamble harness (tests/test_respawn_continuation_preamble.py)."""
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
    Path(str(work) + ".task.txt").write_text(task_text)
    return work


class ClosedIssueRespawnGate(unittest.TestCase):
    """Issue #2068: a returned branch whose subject issue is CLOSED must
    never be respawned — the branch is flagged for cleanup (ledger event +
    advisory) instead. The state is re-read at act time (level-triggered),
    never taken from the stored spawn-time payload."""

    def _run(self, work, issue_state, state_ok, issue=2068,
             role="implementation"):
        state = {}
        spawned = []
        ledger = []
        with mock.patch.object(spawn, "_subject_issue_state",
                               return_value=(issue_state, state_ok)), \
             mock.patch.object(spawn, "_spawn_one",
                               side_effect=lambda *a, **k: spawned.append(a)), \
             mock.patch.object(spawn, "ledger_write",
                               side_effect=lambda e: ledger.append(e)), \
             mock.patch.object(spawn, "_current_issue_task_text",
                               return_value=None), \
             mock.patch.object(spawn, "_respawn_state_save", lambda d: None):
            spawn._respawn_or_cap(f"issue-{issue}/{role}", str(work), issue,
                                  role, "l", 1, state,
                                  "watchdog-observed-crashed")
        return spawned, ledger, state

    def test_closed_issue_never_respawns_and_flags_branch(self):
        with tempfile.TemporaryDirectory() as td:
            work = _prep_workspace(td, 2068, "implementation")
            spawned, ledger, state = self._run(work, "CLOSED", True)
            self.assertEqual(spawned, [])          # no respawn
            events = [e for e in ledger
                      if e.get("event") == "stale_branch_cleanup_flagged"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["issue"], 2068)
            self.assertEqual(events[0]["branch"], "issue-2068/implementation")
            self.assertEqual(events[0]["source"], "respawn")
            # No attempt/cap budget is spent on a refused respawn.
            self.assertEqual(state, {})

    def test_gh_lookup_failure_fails_open_with_ledger_event(self):
        """Mirrors the returned-PR gate convention (issue #680): a broken gh
        must not strand a crashed-but-legitimate session."""
        with tempfile.TemporaryDirectory() as td:
            work = _prep_workspace(td, 2068, "implementation")
            spawned, ledger, state = self._run(work, None, False)
            self.assertEqual(len(spawned), 1)      # respawn proceeds
            events = [e for e in ledger
                      if e.get("event") == "issue_state_gate_fail_open"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["source"], "respawn")


class RespawnCarriesCurrentTaskText(unittest.TestCase):
    """Issue #2068 requirement 2: a legitimate respawn (open issue) carries
    the LATEST task text re-read from the issue at respawn time, not the
    `.task.txt` captured at original spawn."""

    def _run(self, work, current_task):
        state = {}
        spawned = []
        with mock.patch.object(spawn, "_subject_issue_state",
                               return_value=("OPEN", True)), \
             mock.patch.object(spawn, "_spawn_one",
                               side_effect=lambda *a, **k: spawned.append(a)), \
             mock.patch.object(spawn, "ledger_write", lambda e: None), \
             mock.patch.object(spawn, "_current_issue_task_text",
                               return_value=current_task), \
             mock.patch.object(spawn, "_respawn_state_save", lambda d: None):
            spawn._respawn_or_cap("issue-2068/implementation", str(work), 2068,
                                  "implementation", "l", 1, state,
                                  "watchdog-observed-crashed")
        self.assertEqual(len(spawned), 1)
        # _spawn_one(work, role, task, ...)
        return spawned[0][2]

    def test_open_issue_respawn_uses_latest_issue_text(self):
        with tempfile.TemporaryDirectory() as td:
            work = _prep_workspace(td, 2068, "implementation",
                                   task_text="stale task from original spawn")
            latest = "Issue #2068: fix it\n\nbody EDITED after original spawn\n"
            task = self._run(work, latest)
            self.assertEqual(task, latest)
            self.assertNotIn("stale task from original spawn", task)

    def test_fetch_failure_falls_back_to_stored_task(self):
        with tempfile.TemporaryDirectory() as td:
            work = _prep_workspace(td, 2068, "implementation",
                                   task_text="stale task from original spawn")
            task = self._run(work, None)
            self.assertEqual(task, "stale task from original spawn")

    def test_current_issue_task_text_reads_issue_via_gh_rest(self):
        sys.path.insert(0, str(spawn.ROOT / "gates"))
        import gh_rest
        with mock.patch.object(gh_rest, "fetch_issue",
                               return_value={"title": "T",
                                             "body": "CURRENT BODY"}):
            text = spawn._current_issue_task_text(Path("."), 2068)
        self.assertEqual(text, "Issue #2068: T\n\nCURRENT BODY\n")
        with mock.patch.object(gh_rest, "fetch_issue", return_value=None):
            self.assertIsNone(spawn._current_issue_task_text(Path("."), 2068))


class ClosedIssueRelayGate(unittest.TestCase):
    """Issue #2068: `ensure_pushed()` must not (re)create a PR from a
    returned branch whose subject issue is CLOSED — that was the 5-stale-
    re-opens-in-one-night incident shape."""

    def _git(self, cwd, *a):
        return subprocess.run(["git", "-C", str(cwd), *a],
                              capture_output=True, text=True)

    def _clone_with_commit(self, td, issue, role):
        # Same real-git harness as EnsurePushedResult
        # (tests/test_spawn_checkout_network.py).
        seed = Path(td) / "seed"
        origin = Path(td) / "origin.git"
        work = Path(td) / "work"
        seed.mkdir()
        self._git(seed, "init", "-q")
        self._git(seed, "config", "user.email", "t@t.t")
        self._git(seed, "config", "user.name", "t")
        (seed / "a.txt").write_text("x")
        self._git(seed, "add", "a.txt")
        self._git(seed, "commit", "-q", "-m", "init")
        self._git(seed, "branch", "-m", "main")
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)],
                       capture_output=True, text=True, check=True)
        subprocess.run(["git", "clone", "-q", str(origin), str(work)],
                       capture_output=True, text=True, check=True)
        self._git(work, "config", "user.email", "t@t.t")
        self._git(work, "config", "user.name", "t")
        br = f"issue-{issue}/{role}"
        self._git(work, "checkout", "-q", "-b", br)
        (work / "c.txt").write_text("wip")
        self._git(work, "add", "c.txt")
        self._git(work, "commit", "-q", "-m", "wip")
        return work, br

    def _run_ensure_pushed(self, work, issue, role, issue_state, state_ok):
        gh_calls = []
        real_run = subprocess.run

        def fake_run(cmd, *a, **k):
            if cmd and cmd[0] == "gh":
                gh_calls.append(list(cmd))
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")
            return real_run(cmd, *a, **k)

        ledger = []
        with mock.patch.object(spawn, "_git_env", return_value=None), \
             mock.patch.object(spawn.subprocess, "run", side_effect=fake_run), \
             mock.patch.object(spawn, "_subject_issue_state",
                               return_value=(issue_state, state_ok)), \
             mock.patch.object(spawn, "ledger_write",
                               side_effect=lambda e: ledger.append(e)):
            result = spawn.ensure_pushed(str(work), issue, role)
        return result, gh_calls, ledger

    def test_closed_issue_no_pr_reopen_branch_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999977, "implementation"
            work, br = self._clone_with_commit(td, issue, role)
            result, gh_calls, ledger = self._run_ensure_pushed(
                work, issue, role, "CLOSED", True)
            self.assertEqual(result,
                             {"status": "issue-closed-stale-branch",
                              "reason": None})
            self.assertFalse(any(c[:3] == ["gh", "pr", "create"]
                                 for c in gh_calls))
            events = [e for e in ledger
                      if e.get("event") == "stale_branch_cleanup_flagged"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["branch"], br)
            self.assertEqual(events[0]["source"], "relay")

    def test_gh_lookup_failure_fails_open_to_pr_create(self):
        with tempfile.TemporaryDirectory() as td:
            issue, role = 999978, "implementation"
            work, br = self._clone_with_commit(td, issue, role)
            result, gh_calls, ledger = self._run_ensure_pushed(
                work, issue, role, None, False)
            # fail-open: the pr-create attempt is made (and fails only
            # because the stubbed gh returns 1 — that is the pre-existing
            # pr-create-failed path, not a new refusal).
            self.assertTrue(any(c[:3] == ["gh", "pr", "create"]
                                for c in gh_calls))
            events = [e for e in ledger
                      if e.get("event") == "issue_state_gate_fail_open"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["source"], "relay")


class Issue77StyleReplay(unittest.TestCase):
    """Fixture replay of the incident shape: one CLOSED issue, multiple
    stale returned branches observed repeatedly across watchdog ticks =>
    zero stale PR re-opens and zero respawns, each branch flagged once per
    machinery pass."""

    def test_closed_issue_with_multiple_stale_branches_zero_reopens(self):
        roles = ("implementation", "review", "product")
        spawned = []
        ledger = []
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(spawn, "_subject_issue_state",
                                   return_value=("CLOSED", True)), \
                 mock.patch.object(spawn, "_spawn_one",
                                   side_effect=lambda *a, **k: spawned.append(a)), \
                 mock.patch.object(spawn, "ledger_write",
                                   side_effect=lambda e: ledger.append(e)), \
                 mock.patch.object(spawn, "_current_issue_task_text",
                                   return_value=None), \
                 mock.patch.object(spawn, "_respawn_state_save", lambda d: None):
                for i, role in enumerate(roles):
                    work = Path(td) / f"w-{role}"
                    work.mkdir()
                    run = lambda *a: subprocess.run(a, cwd=str(work),
                                                    capture_output=True,
                                                    text=True, check=True)
                    run("git", "init", "-q")
                    run("git", "config", "user.email", "t@example.com")
                    run("git", "config", "user.name", "t")
                    (work / "f.txt").write_text("x")
                    run("git", "add", "f.txt")
                    run("git", "commit", "-q", "-m", "init")
                    Path(str(work) + ".task.txt").write_text("stale task")
                    # Two watchdog ticks observe the same dead entry — the
                    # second tick must not re-open either (5 re-opens for
                    # one closed issue came from repeated ticks).
                    for tick in range(2):
                        spawn._respawn_or_cap(f"issue-77/{role}", str(work),
                                              77, role, "l", 1 + tick, {},
                                              "watchdog-observed-crashed")
        self.assertEqual(spawned, [])
        flags = [e for e in ledger
                 if e.get("event") == "stale_branch_cleanup_flagged"]
        self.assertEqual(len(flags), len(roles) * 2)
        self.assertTrue(all(e["issue"] == 77 for e in flags))
