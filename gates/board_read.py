#!/usr/bin/env python3
"""Issue #2103 layers 1+2: one shared board read for every multi-item
consumer.

Layer 1 — single GraphQL board query. A full board (all issues + all PRs
with number/state/title/labels/updatedAt/body/comment count, plus
headRefName for PRs) is fetched in exactly TWO `gh api graphql --paginate`
invocations regardless of board size (`--paginate` follows the page
cursor inside one gh process; the two invocations exist because gh's
`--paginate` can only follow a single connection's pageInfo per query —
issues and pullRequests are two connections).

Layer 2 — delta reads over a cached snapshot. The board is persisted as a
JSON snapshot (under MUSTER_STATE_ROOT when set, else <root>/runs, same
anchoring as gates/gh_delta.py cursors) together with `last_sweep_at` —
the max `updatedAt` observed in GitHub's own responses, never a local
clock (skew, gh_delta condition 2). The steady-state read is ONE GraphQL
search call `repo:<slug> updated:>=<last_sweep_at>` merged into the
snapshot; an unchanged board costs exactly 1 API call. The full 2-call
read remains as reconciliation: missing/corrupt snapshot (self-heal:
detect, discard, full re-read), `BOARD_READ_FORCE_FULL=1`, every Nth
sweep (`BOARD_READ_FULL_EVERY`, default 20), or a delta page overflow
(100 nodes returned — the delta could be truncated, so it is discarded
rather than silently merged).

Failure contract (watch-coverage inviolable): a gh/network failure never
crashes the caller — the stale snapshot is served with
meta["source"]=="stale" and the `on_fail_open` callback is invoked (spawn
routes it to a `board_read_fail_open` ledger event, advisory). Only when
there is no usable snapshot at all does the read return `(None, meta)`.

Layer 3 of #2103 (event push over poll) is deliberately NOT here — it is
deferred as a follow-up; this module is the reconciliation substrate it
will demote to low frequency.
"""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

SNAPSHOT_VERSION = 1
_PAGE_SIZE = 100
_DEFAULT_FULL_EVERY = 20

_ISSUES_QUERY = """
query($owner: String!, $name: String!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $endCursor, states: [OPEN, CLOSED]) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number state title body updatedAt
        comments { totalCount }
        labels(first: 20) { nodes { name } }
      }
    }
  }
}
"""

_PRS_QUERY = """
query($owner: String!, $name: String!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, after: $endCursor, states: [OPEN, CLOSED, MERGED]) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number state title body updatedAt headRefName
        comments { totalCount }
        labels(first: 20) { nodes { name } }
      }
    }
  }
}
"""

_SEARCH_QUERY = """
query($q: String!) {
  search(query: $q, type: ISSUE, first: 100) {
    nodes {
      __typename
      ... on Issue {
        number state title body updatedAt
        comments { totalCount }
        labels(first: 20) { nodes { name } }
      }
      ... on PullRequest {
        number state title body updatedAt headRefName
        comments { totalCount }
        labels(first: 20) { nodes { name } }
      }
    }
  }
}
"""


def snapshot_path(root: Path) -> Path:
    """Snapshot location. Anchored to MUSTER_STATE_ROOT when set (the same
    override spawn.py's STATE_ROOT honors), else <root>/runs — the same
    anchoring gates/gh_delta.py uses for its cursors."""
    env = os.environ.get("MUSTER_STATE_ROOT")
    base = Path(env).resolve() if env else (root / "runs")
    return base / "board_snapshot.json"


def _atomic_write_json(path: Path, data: dict) -> None:
    # Same atomic temp+rename pattern as gates/gh_delta.py::_atomic_write_json
    # (that helper is module-private; small local duplicate by precedent —
    # see spawn.py::_save_requirement_drift_cache).
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent),
                                        prefix=".board-snap-", suffix=".tmp")
    except OSError:
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp_name, path)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def load_snapshot(path: Path) -> dict | None:
    """Read the snapshot. Missing, unreadable, non-JSON, wrong version, or
    shape-invalid all return None — the caller treats that as an explicit
    full-read reason (self-heal: a corrupt snapshot is discarded, never
    silently merged into)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("version") != SNAPSHOT_VERSION:
        return None
    if not isinstance(data.get("last_sweep_at"), str):
        return None
    if not isinstance(data.get("issues"), dict) or not isinstance(data.get("prs"), dict):
        return None
    return data


def _node_item(node: dict, is_pr: bool) -> dict:
    labels = [l.get("name") for l in (node.get("labels") or {}).get("nodes", [])
              if isinstance(l, dict) and l.get("name")]
    item = {
        "number": node.get("number"),
        "state": node.get("state"),
        "title": node.get("title", ""),
        "body": node.get("body", "") or "",
        "updatedAt": node.get("updatedAt"),
        "labels": labels,
        "comments": (node.get("comments") or {}).get("totalCount", 0),
    }
    if is_pr:
        item["headRefName"] = node.get("headRefName", "")
    return item


def _run_graphql(run: Callable, root: Path, query: str,
                 fields: dict[str, str], paginate: bool) -> list[dict] | None:
    """One `gh api graphql` invocation. Returns the list of response
    documents (`--paginate` concatenates one JSON doc per page on stdout),
    or None on any failure (gh missing, non-zero exit, unparseable body)."""
    cmd = ["gh", "api", "graphql"]
    if paginate:
        cmd.append("--paginate")
    cmd += ["-f", f"query={query}"]
    for k, v in fields.items():
        cmd += ["-f", f"{k}={v}"]
    try:
        r = run(cmd, cwd=root, capture_output=True, text=True)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    docs: list[dict] = []
    decoder = json.JSONDecoder()
    text = r.stdout.strip()
    idx = 0
    while idx < len(text):
        try:
            doc, end = decoder.raw_decode(text, idx)
        except ValueError:
            return None
        if not isinstance(doc, dict):
            return None
        docs.append(doc)
        idx = end
        while idx < len(text) and text[idx] in " \r\n\t":
            idx += 1
    return docs if docs else None


def _full_read(run: Callable, root: Path, slug: str) -> tuple[dict | None, int]:
    """Full board via 2 paginated GraphQL calls. Returns (board, calls)."""
    owner, _, name = slug.partition("/")
    calls = 0
    board = {"issues": {}, "prs": {}}
    for query, conn, key, is_pr in ((_ISSUES_QUERY, "issues", "issues", False),
                                    (_PRS_QUERY, "pullRequests", "prs", True)):
        calls += 1
        docs = _run_graphql(run, root, query,
                            {"owner": owner, "name": name}, paginate=True)
        if docs is None:
            return None, calls
        for doc in docs:
            repo = ((doc.get("data") or {}).get("repository") or {})
            nodes = (repo.get(conn) or {}).get("nodes")
            if not isinstance(nodes, list):
                return None, calls
            for node in nodes:
                if isinstance(node, dict) and node.get("number") is not None:
                    board[key][str(node["number"])] = _node_item(node, is_pr)
    return board, calls


def _delta_read(run: Callable, root: Path, slug: str,
                since: str) -> tuple[list[dict] | None, bool]:
    """One search call for items updated at/after `since`. Returns
    (nodes, overflow). `updated:>=` deliberately re-sees the boundary item —
    the merge is idempotent, and `>` could silently drop a same-second
    update (gh_delta condition 2 precedent). overflow=True means 100 nodes
    came back and the delta may be truncated — the caller must discard it
    and take the full-read path instead of merging a possibly-partial set."""
    q = f"repo:{slug} updated:>={since}"
    docs = _run_graphql(run, root, _SEARCH_QUERY, {"q": q}, paginate=False)
    if docs is None:
        return None, False
    nodes = (((docs[0].get("data") or {}).get("search") or {}).get("nodes"))
    if not isinstance(nodes, list):
        return None, False
    return nodes, len(nodes) >= _PAGE_SIZE


def _max_updated_at(items: list[dict]) -> str | None:
    stamps = [i.get("updatedAt") for i in items
              if isinstance(i.get("updatedAt"), str)]
    return max(stamps) if stamps else None


def board_read(root: Path, slug: str, run: Callable | None = None,
               path: Path | None = None,
               on_fail_open: Callable[[str], None] | None = None,
               force_full: bool | None = None,
               full_every: int | None = None) -> tuple[dict | None, dict]:
    """The shared board read. Returns `(board, meta)`.

    `board` is `{"issues": {str(number): item}, "prs": {str(number): item}}`
    or None only when nothing could be read (gh failed AND no snapshot).
    Item fields: number, state (GraphQL vocabulary OPEN/CLOSED/MERGED),
    title, body, updatedAt, labels (names), comments (count), and
    headRefName for PRs.

    `meta`: {"source": "full"|"delta"|"stale"|None,
             "api_calls": <int>, "last_sweep_at": <str|None>,
             "error": <str|None>}.
    """
    run = run or subprocess.run
    spath = path or snapshot_path(root)
    snap = load_snapshot(spath)
    if force_full is None:
        force_full = os.environ.get("BOARD_READ_FORCE_FULL") == "1"
    if full_every is None:
        try:
            full_every = int(os.environ.get("BOARD_READ_FULL_EVERY",
                                            _DEFAULT_FULL_EVERY))
        except ValueError:
            full_every = _DEFAULT_FULL_EVERY
    sweep_seq = (snap.get("sweep_seq", 0) if snap else 0)
    due_reconcile = full_every > 0 and snap is not None and \
        (sweep_seq + 1) % full_every == 0

    def _fail(detail: str) -> tuple[dict | None, dict]:
        if on_fail_open is not None:
            try:
                on_fail_open(detail)
            except Exception:
                pass
        if snap is not None:
            # Serve the stale snapshot rather than crash the sweep —
            # advisory fail-open, same inviolable-watch contract as the
            # rest of the watch family.
            return ({"issues": snap["issues"], "prs": snap["prs"]},
                    {"source": "stale", "api_calls": calls,
                     "last_sweep_at": snap["last_sweep_at"], "error": detail})
        return None, {"source": None, "api_calls": calls,
                      "last_sweep_at": None, "error": detail}

    calls = 0
    if snap is not None and not force_full and not due_reconcile:
        # Steady-state path: one search call merged into the snapshot.
        calls = 1
        nodes, overflow = _delta_read(run, root, slug, snap["last_sweep_at"])
        if nodes is None:
            return _fail("delta search call failed")
        if not overflow:
            issues = dict(snap["issues"])
            prs = dict(snap["prs"])
            merged_items = []
            for node in nodes:
                if not isinstance(node, dict) or node.get("number") is None:
                    continue
                is_pr = node.get("__typename") == "PullRequest"
                item = _node_item(node, is_pr)
                (prs if is_pr else issues)[str(node["number"])] = item
                merged_items.append(item)
            # Timestamps come from GitHub's updatedAt, never a local clock.
            last = _max_updated_at(merged_items) or snap["last_sweep_at"]
            board = {"issues": issues, "prs": prs}
            _atomic_write_json(spath, {
                "version": SNAPSHOT_VERSION, "last_sweep_at": last,
                "sweep_seq": sweep_seq + 1,
                "issues": issues, "prs": prs})
            return board, {"source": "delta", "api_calls": calls,
                           "last_sweep_at": last, "error": None}
        # overflow: the 100-node page may be truncated — fall through to
        # the full read (never merge a possibly-partial delta).

    board, full_calls = _full_read(run, root, slug)
    calls += full_calls
    if board is None:
        return _fail("full GraphQL board read failed")
    all_items = list(board["issues"].values()) + list(board["prs"].values())
    last = _max_updated_at(all_items)
    if last is None:
        # Empty board: keep the previous cursor if any; otherwise there is
        # nothing to delta from — persist without last_sweep_at so the next
        # read is full again (an empty snapshot with a fabricated local
        # timestamp would be a skew bug).
        last = snap["last_sweep_at"] if snap else None
    data = {"version": SNAPSHOT_VERSION, "sweep_seq": sweep_seq + 1,
            "issues": board["issues"], "prs": board["prs"]}
    if last is not None:
        data["last_sweep_at"] = last
        _atomic_write_json(spath, data)
    return board, {"source": "full", "api_calls": calls,
                   "last_sweep_at": last, "error": None}


def pr_index(board: dict) -> dict[str, dict]:
    """`closure_sweep._pr_index_all`-shaped index (branch -> {number,
    state, body}) built from an already-fetched board — 0 extra gh calls.
    Most-recently-updated PR wins a branch-name collision, matching the
    'most recent PR for the branch' semantic of the per-branch helpers."""
    out: dict[str, dict] = {}
    prs = sorted(board.get("prs", {}).values(),
                 key=lambda p: p.get("updatedAt") or "")
    for pr in prs:
        branch = pr.get("headRefName") or ""
        if branch:
            out[branch] = {"number": pr.get("number"),
                           "state": pr.get("state"),
                           "body": pr.get("body", "") or ""}
    return out
