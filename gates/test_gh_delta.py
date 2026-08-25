from __future__ import annotations
import json
from types import SimpleNamespace

import gh_delta


def _response(status: int, headers: dict, body: str, returncode: int | None = None) -> SimpleNamespace:
    """issue #2315: real `gh api` exits 1 on any non-2xx status, 304
    included — `returncode` defaults to that real behavior (0 for 2xx,
    1 otherwise) unless a caller overrides it."""
    head_lines = [f"HTTP/2 {status}"] + [f"{k}: {v}" for k, v in headers.items()]
    stdout = "\r\n".join(head_lines) + "\r\n\r\n" + body
    if returncode is None:
        returncode = 0 if 200 <= status < 300 else 1
    return SimpleNamespace(returncode=returncode, stdout=stdout)


def _page_response(items, etag=None, has_next=False):
    headers = {}
    if etag:
        headers["etag"] = etag
    if has_next:
        headers["link"] = '<https://api.github.com/x?page=2>; rel="next"'
    return _response(200, headers, json.dumps(items))


def test_delta_returns_items_since_cursor_and_persists_advanced_cursor(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"since": "2026-08-01T00:00:00+00:00",
                                        "etag": None,
                                        "last_reconciliation": "2026-08-16T00:00:00+00:00"}),
                            encoding="utf-8")
    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        assert "since=2026-08-01T00:00:00+00:00" in " ".join(cmd)
        items = [{"number": 1, "updated_at": "2026-08-10T00:00:00+00:00"},
                  {"number": 2, "updated_at": "2026-08-16T00:00:00+00:00"}]
        return _page_response(items, etag='"e1"')

    items, new_cursor, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file)

    assert classification == "delta"
    assert [i["number"] for i in items] == [1, 2]
    assert new_cursor == "2026-08-16T00:00:00+00:00"
    assert len(calls) == 1

    persisted = json.loads(cursor_file.read_text(encoding="utf-8"))
    assert persisted["since"] == "2026-08-16T00:00:00+00:00"
    assert persisted["etag"] == '"e1"'


def test_no_change_tick_makes_exactly_one_probe_and_zero_detail_fetches(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"since": "2026-08-15T00:00:00+00:00",
                                        "etag": '"cached-etag"',
                                        "last_reconciliation": "2026-08-15T00:00:00+00:00"}),
                            encoding="utf-8")
    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        assert 'If-None-Match: "cached-etag"' in " ".join(cmd)
        return _response(304, {}, "")

    items, new_cursor, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-15T01:00:00+00:00", path=cursor_file)

    assert classification == "no-change"
    assert items == []
    assert len(calls) == 1
    assert new_cursor == "2026-08-15T00:00:00+00:00"


def test_genuine_non_304_error_still_classifies_error(tmp_path):
    """issue #2315 regression guard: the 304-before-returncode reorder
    must not swallow real failures (bad token / 5xx) into no-change —
    only page-1 status 304 short-circuits the returncode check."""
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"since": "2026-08-15T00:00:00+00:00",
                                        "etag": '"cached-etag"',
                                        "last_reconciliation": "2026-08-15T00:00:00+00:00"}),
                            encoding="utf-8")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        return _response(401, {}, '{"message": "Bad credentials"}')

    items, new_cursor, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-15T01:00:00+00:00", path=cursor_file)

    assert classification == "error"
    assert items is None
    assert new_cursor == "2026-08-15T00:00:00+00:00"


def test_corrupted_cursor_file_classifies_full_rescan(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text("{not valid json", encoding="utf-8")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        assert "since=" not in " ".join(cmd)
        return _page_response([{"number": 1, "updated_at": "2026-08-16T00:00:00+00:00"}])

    items, new_cursor, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file)

    assert classification == "full-rescan"


def test_missing_since_key_in_cursor_file_classifies_full_rescan(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"etag": '"x"'}), encoding="utf-8")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        return _page_response([])

    _, _, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file)

    assert classification == "full-rescan"


def test_pagination_follows_pages_burst_over_30_never_dropped(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"since": "2026-08-01T00:00:00+00:00",
                                        "etag": None,
                                        "last_reconciliation": "2026-08-16T00:00:00+00:00"}),
                            encoding="utf-8")
    pages = [
        [{"number": i, "updated_at": "2026-08-10T00:00:00+00:00"} for i in range(10)],
        [{"number": i, "updated_at": "2026-08-11T00:00:00+00:00"} for i in range(10, 20)],
        [{"number": i, "updated_at": "2026-08-12T00:00:00+00:00"} for i in range(20, 35)],
    ]
    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        page_idx = len(calls) - 1
        has_next = page_idx < len(pages) - 1
        return _page_response(pages[page_idx], has_next=has_next)

    items, new_cursor, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file, per_page=10)

    assert len(calls) == 3
    assert len(items) == 35
    assert classification == "delta"


def test_page_overflow_beyond_max_pages_classifies_full_rescan(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"since": "2026-08-01T00:00:00+00:00",
                                        "etag": None,
                                        "last_reconciliation": "2026-08-16T00:00:00+00:00"}),
                            encoding="utf-8")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        return _page_response([{"number": 1, "updated_at": "2026-08-10T00:00:00+00:00"}],
                               has_next=True)

    _, _, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file, per_page=1, max_pages=2)

    assert classification == "full-rescan"


def test_periodic_reconciliation_forces_full_rescan_even_without_corruption(tmp_path):
    cursor_file = tmp_path / "cursor.json"
    cursor_file.write_text(json.dumps({"since": "2026-08-01T00:00:00+00:00",
                                        "etag": '"stale-etag"',
                                        "last_reconciliation": "2026-08-10T00:00:00+00:00"}),
                            encoding="utf-8")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        assert "since=" not in " ".join(cmd)
        assert "If-None-Match" not in " ".join(cmd)
        return _page_response([{"number": 1, "updated_at": "2026-08-16T00:00:00+00:00"}])

    _, _, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file, reconcile_interval_hours=24.0)

    assert classification == "full-rescan"


def test_pulls_resource_hits_issues_endpoint_no_since_symmetry_bug(tmp_path):
    """binding condition 3: GET /pulls has no `since` — fetch_delta must
    call repos/{slug}/issues even for resource='pulls', then client-filter
    by the pull_request key."""
    cursor_file = tmp_path / "cursor.json"
    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        assert "repos/acme/widget/issues" in cmd
        assert "repos/acme/widget/pulls" not in " ".join(cmd)
        assert "since=" not in " ".join(cmd)
        assert "If-None-Match" not in " ".join(cmd)
        items = [
            {"number": 1, "updated_at": "2026-08-10T00:00:00+00:00"},
            {"number": 2, "updated_at": "2026-08-11T00:00:00+00:00",
             "pull_request": {"url": "x"}},
        ]
        return _page_response(items)

    items, _, classification = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "pulls", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file)

    assert [i["number"] for i in items] == [2]
    assert classification == "full-rescan"  # cold cursor, first tick


def test_issues_resource_excludes_pull_requests(tmp_path):
    cursor_file = tmp_path / "cursor.json"

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        items = [
            {"number": 1, "updated_at": "2026-08-10T00:00:00+00:00"},
            {"number": 2, "updated_at": "2026-08-11T00:00:00+00:00",
             "pull_request": {"url": "x"}},
        ]
        return _page_response(items)

    items, _, _ = gh_delta.fetch_delta(
        tmp_path, "acme/widget", "issues", run=fake_run,
        now="2026-08-16T01:00:00+00:00", path=cursor_file)

    assert [i["number"] for i in items] == [1]
