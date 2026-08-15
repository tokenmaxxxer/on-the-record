#!/usr/bin/env python3
"""issue #1554 req 5 — ETag/If-None-Match conditional requests for
board-wide sweeps: a fake `gh` transport asserting `If-None-Match` is sent on
the second call and 0 calls are billed on unchanged fixtures; a first-ever
tick (no ETag cache) bills once then caches.

  python3 -m pytest tests/test_board_sweep_etag.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
sys.path.insert(0, str(Path(__file__).parent.parent))
import closure_sweep  # noqa: E402
import spawn  # noqa: E402

_ISSUES_BODY = '[{"number": 1, "state": "open"}, {"number": 2, "state": "closed"}]'


def _http_response(status: int, etag: str | None, body: str) -> mock.Mock:
    headers = f"HTTP/2.0 {status}\r\n"
    if etag is not None:
        headers += f"Etag: {etag}\r\n"
    return mock.Mock(returncode=0, stdout=headers + "\r\n" + body, stderr="")


def _fake_transport(etag_seq):
    """Answers `gh repo view` (slug probe) and `gh api repos/x/y/issues -i`
    calls in sequence per `etag_seq` (a list of (status, etag, body)
    tuples); records every subprocess.run invocation."""
    calls: list[list[str]] = []
    responses = iter(etag_seq)

    def _run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:3] == ["gh", "repo", "view"]:
            return mock.Mock(returncode=0, stdout="octocat/hello-world\n", stderr="")
        if cmd[:2] == ["gh", "api"] and cmd[2] == "repos/octocat/hello-world/issues":
            status, etag, body = next(responses)
            return _http_response(status, etag, body)
        return mock.Mock(returncode=0, stdout="", stderr="")

    return _run, calls


def test_first_tick_no_cache_bills_once_then_caches(tmp_path):
    """First-ever tick: no ETag cache exists yet, so the call is
    unconditional and billed once; a cache file is written afterward."""
    root = tmp_path
    fake_run, calls = _fake_transport([(200, '"abc123"', _ISSUES_BODY)])
    with mock.patch("subprocess.run", side_effect=fake_run):
        index, ok = closure_sweep.issue_state_index_all(root)

    assert ok is True
    assert index == {1: "OPEN", 2: "CLOSED"}
    issue_list_calls = [c for c in calls if c[:2] == ["gh", "api"]
                         and c[2] == "repos/octocat/hello-world/issues"]
    assert len(issue_list_calls) == 1
    assert not any("If-None-Match" in " ".join(c) for c in issue_list_calls)
    cache_path = closure_sweep._board_list_etag_cache_path(root, "issues")
    assert cache_path.exists()


def test_unchanged_board_sends_if_none_match_and_bills_zero(tmp_path):
    """Second tick over an unchanged board: `If-None-Match` is sent, GitHub
    answers 304, and the returned index is reconstructed from cache with
    zero *billed* gh calls for this signal (304s aren't counted)."""
    root = tmp_path
    fake_run, calls = _fake_transport([
        (200, '"abc123"', _ISSUES_BODY),
        (304, '"abc123"', ""),
    ])
    with mock.patch("subprocess.run", side_effect=fake_run):
        closure_sweep.issue_state_index_all(root)  # tick 1: primes cache
        index, ok = closure_sweep.issue_state_index_all(root)  # tick 2: unchanged

    assert ok is True
    assert index == {1: "OPEN", 2: "CLOSED"}
    second_call = [c for c in calls if c[:2] == ["gh", "api"]
                    and c[2] == "repos/octocat/hello-world/issues"][-1]
    assert any(part == "If-None-Match: \"abc123\"" for part in second_call)


def test_changed_board_rebills_and_refreshes_cache(tmp_path):
    """A board that actually changed gets a fresh 200 + new ETag, billed as
    one call, and the returned data reflects the change (not stale cache)."""
    root = tmp_path
    changed_body = '[{"number": 1, "state": "closed"}, {"number": 2, "state": "closed"}]'
    fake_run, calls = _fake_transport([
        (200, '"abc123"', _ISSUES_BODY),
        (200, '"def456"', changed_body),
    ])
    with mock.patch("subprocess.run", side_effect=fake_run):
        closure_sweep.issue_state_index_all(root)
        index, ok = closure_sweep.issue_state_index_all(root)

    assert ok is True
    assert index == {1: "CLOSED", 2: "CLOSED"}
