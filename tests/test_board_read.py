"""Issue #2103 layers 1+2: single GraphQL board query + delta reads over a
cached snapshot (gates/board_read.py) and its spawn.py wiring.

The acceptance metric is counted on the mocked gh boundary: a full board
read for a 30+ item fixture issues at most 2 gh invocations; a
steady-state read of an unchanged board issues exactly 1."""
import types

from _spawn_test_support import *  # noqa: F401,F403

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import board_read


def _iso(n):
    return f"2026-08-23T00:{n:02d}:00Z"


def _issue_node(number, state="OPEN", updated=None, title=None, body=""):
    return {"number": number, "state": state,
            "title": title or f"issue {number}", "body": body,
            "updatedAt": updated or _iso(number % 60),
            "comments": {"totalCount": 0},
            "labels": {"nodes": [{"name": "bug"}]}}


def _pr_node(number, state="OPEN", updated=None, branch=None, body=""):
    node = _issue_node(number, state=state, updated=updated, body=body)
    node["headRefName"] = branch or f"issue-{number}/implementation"
    return node


def _fake_gh(calls, issues=(), prs=(), search_nodes=(), fail=False):
    """Delegating gh fake for `board_read(run=...)` — inspects the GraphQL
    query text to decide which fixture to serve, and records every
    invocation in `calls` (the acceptance metric)."""
    def run(cmd, **kw):
        calls.append(list(cmd))
        if fail:
            return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")
        text = " ".join(cmd)
        if "search(" in text:
            doc = {"data": {"search": {"nodes": list(search_nodes)}}}
        elif "pullRequests(" in text:
            doc = {"data": {"repository": {"pullRequests": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": list(prs)}}}}
        else:
            doc = {"data": {"repository": {"issues": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": list(issues)}}}}
        return types.SimpleNamespace(returncode=0, stdout=json.dumps(doc),
                                     stderr="")
    return run


class FullBoardRead(unittest.TestCase):
    def test_full_board_at_most_two_calls_for_30_plus_items(self):
        """Acceptance: a 30+ item board is read in <=2 gh invocations
        regardless of size."""
        issues = [_issue_node(n) for n in range(1, 36)]        # 35 issues
        prs = [_pr_node(n) for n in range(100, 106)]           # 6 PRs
        calls = []
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "snap.json"
            board, meta = board_read.board_read(
                Path(td), "o/r", run=_fake_gh(calls, issues=issues, prs=prs),
                path=path)
        self.assertEqual(len(calls), 2)
        self.assertEqual(meta["api_calls"], 2)
        self.assertEqual(meta["source"], "full")
        self.assertEqual(len(board["issues"]), 35)
        self.assertEqual(len(board["prs"]), 6)
        self.assertEqual(board["prs"]["100"]["headRefName"],
                         "issue-100/implementation")
        # last_sweep_at comes from GitHub's updatedAt, not a local clock.
        all_updated = [n["updatedAt"] for n in issues + prs]
        self.assertEqual(meta["last_sweep_at"], max(all_updated))


class SteadyStateAndDelta(unittest.TestCase):
    def _prime(self, td, issues, prs):
        path = Path(td) / "snap.json"
        board, meta = board_read.board_read(
            Path(td), "o/r", run=_fake_gh([], issues=issues, prs=prs),
            path=path)
        self.assertEqual(meta["source"], "full")
        return path

    def test_unchanged_board_exactly_one_call_served_from_snapshot(self):
        issues = [_issue_node(n) for n in range(1, 31)]
        prs = [_pr_node(100)]
        with tempfile.TemporaryDirectory() as td:
            path = self._prime(td, issues, prs)
            calls = []
            board, meta = board_read.board_read(
                Path(td), "o/r", run=_fake_gh(calls, search_nodes=[]),
                path=path)
            self.assertEqual(len(calls), 1)
            self.assertEqual(meta["api_calls"], 1)
            self.assertEqual(meta["source"], "delta")
            self.assertEqual(len(board["issues"]), 30)
            self.assertEqual(len(board["prs"]), 1)
            # The single call is the search delta, not a repository read.
            self.assertIn("search(", " ".join(calls[0]))

    def test_delta_merge_updates_adds_and_closes(self):
        issues = [_issue_node(1, updated=_iso(1)), _issue_node(2, updated=_iso(2))]
        prs = [_pr_node(100, updated=_iso(3))]
        with tempfile.TemporaryDirectory() as td:
            path = self._prime(td, issues, prs)
            changed = _issue_node(1, updated=_iso(10), title="retitled")
            changed["__typename"] = "Issue"
            new = _issue_node(40, updated=_iso(11))
            new["__typename"] = "Issue"
            closed_pr = _pr_node(100, state="MERGED", updated=_iso(12))
            closed_pr["__typename"] = "PullRequest"
            calls = []
            board, meta = board_read.board_read(
                Path(td), "o/r",
                run=_fake_gh(calls, search_nodes=[changed, new, closed_pr]),
                path=path)
            self.assertEqual(len(calls), 1)
            self.assertEqual(meta["source"], "delta")
            self.assertEqual(board["issues"]["1"]["title"], "retitled")      # replaced
            self.assertIn("40", board["issues"])                             # new item
            self.assertEqual(board["issues"]["2"]["title"], "issue 2")       # untouched
            self.assertEqual(board["prs"]["100"]["state"], "MERGED")         # state update
            # Cursor advances to the max updatedAt of the delta items.
            self.assertEqual(meta["last_sweep_at"], _iso(12))
            snap = board_read.load_snapshot(path)
            self.assertEqual(snap["last_sweep_at"], _iso(12))

    def test_delta_overflow_falls_back_to_full_read(self):
        """A 100-node search page may be truncated — it must be discarded
        and replaced by the full read, never merged as if complete."""
        issues = [_issue_node(1)]
        with tempfile.TemporaryDirectory() as td:
            path = self._prime(td, issues, [])
            nodes = []
            for n in range(1, 101):
                node = _issue_node(n, updated=_iso(n % 60))
                node["__typename"] = "Issue"
                nodes.append(node)
            calls = []
            board, meta = board_read.board_read(
                Path(td), "o/r",
                run=_fake_gh(calls, issues=[_issue_node(n) for n in range(1, 120)],
                             search_nodes=nodes),
                path=path)
            self.assertEqual(meta["source"], "full")
            self.assertEqual(len(calls), 3)  # 1 delta probe + 2 full
            self.assertEqual(len(board["issues"]), 119)


class SnapshotSelfHeal(unittest.TestCase):
    def test_corrupt_snapshot_discarded_full_reread_no_crash(self):
        issues = [_issue_node(n) for n in range(1, 32)]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "snap.json"
            path.write_text("{not json", encoding="utf-8")
            calls = []
            board, meta = board_read.board_read(
                Path(td), "o/r", run=_fake_gh(calls, issues=issues, prs=[]),
                path=path)
            self.assertEqual(meta["source"], "full")
            self.assertEqual(len(calls), 2)
            self.assertEqual(len(board["issues"]), 31)
            # Self-healed: the rewritten snapshot is valid again.
            snap = board_read.load_snapshot(path)
            self.assertIsNotNone(snap)
            self.assertEqual(len(snap["issues"]), 31)

    def test_wrong_version_snapshot_treated_as_corrupt(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "snap.json"
            path.write_text(json.dumps({"version": 999, "last_sweep_at": _iso(1),
                                        "issues": {}, "prs": {}}))
            self.assertIsNone(board_read.load_snapshot(path))


class FailOpen(unittest.TestCase):
    def test_gh_failure_serves_stale_snapshot_and_fail_open_event(self):
        issues = [_issue_node(1), _issue_node(2)]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "snap.json"
            board_read.board_read(Path(td), "o/r",
                                  run=_fake_gh([], issues=issues, prs=[]),
                                  path=path)
            events = []
            board, meta = board_read.board_read(
                Path(td), "o/r", run=_fake_gh([], fail=True), path=path,
                on_fail_open=events.append)
            self.assertIsNotNone(board)                    # never crash the sweep
            self.assertEqual(meta["source"], "stale")
            self.assertEqual(len(board["issues"]), 2)
            self.assertEqual(len(events), 1)               # advisory ledger hook fired

    def test_gh_failure_without_snapshot_returns_none_with_event(self):
        with tempfile.TemporaryDirectory() as td:
            events = []
            board, meta = board_read.board_read(
                Path(td), "o/r", run=_fake_gh([], fail=True),
                path=Path(td) / "snap.json", on_fail_open=events.append)
            self.assertIsNone(board)
            self.assertIsNone(meta["source"])
            self.assertEqual(len(events), 1)


class SpawnWiring(unittest.TestCase):
    def test_spawn_board_read_fail_open_writes_ledger_event(self):
        ledger = []
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "_repo_slug", return_value="o/r"), \
             mock.patch.object(spawn, "ledger_write",
                               side_effect=lambda e: ledger.append(e)), \
             mock.patch.object(board_read, "board_read",
                               side_effect=lambda root, slug, on_fail_open=None,
                               **kw: (on_fail_open("boom"), (None, {}))[1]):
            spawn._board_read(Path(td))
        events = [e for e in ledger if e.get("event") == "board_read_fail_open"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["repo"], "o/r")

    def test_requirement_drift_full_mode_reads_via_board_read_no_gh_lists(self):
        """The converted call site: full-mode requirement_drift consumes the
        shared board read and issues no `gh issue list`/`gh pr list`."""
        board = {"issues": {"5": {"number": 5, "state": "OPEN",
                                  "title": "t", "body": "cites R001",
                                  "updatedAt": _iso(1), "labels": [],
                                  "comments": 0}},
                 "prs": {}}
        def _no_gh(cmd, *a, **kw):
            if cmd and cmd[0] == "gh":
                raise AssertionError(f"unexpected gh call: {cmd}")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = root / "docs" / "specs" / "requirement-digest.md"
            digest.parent.mkdir(parents=True)
            digest.write_text("- R001: thing [open] (source: #5)\n")
            buf = io.StringIO()
            with mock.patch.object(spawn, "_board_read",
                                   return_value=(board, {"source": "delta"})), \
                 mock.patch.object(spawn.subprocess, "run", side_effect=_no_gh), \
                 contextlib.redirect_stdout(buf):
                spawn.requirement_drift(root)
        # R001 is cited by the open issue served from the board read — no
        # unmentioned-requirement drift line, and no gh list calls happened.
        self.assertNotIn("R001", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
