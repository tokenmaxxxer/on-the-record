import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import patrol_board  # noqa: E402


def _entry(fp, path="roles/scout/foo.py", excerpt="bad thing here",
           lane="diff", status="open", finding_class="record-lint-violation",
           last_seen="abc123"):
    return {
        "fingerprint": fp,
        "scanner_id": "record_lint",
        "path": path,
        "finding_class": finding_class,
        "excerpt": excerpt,
        "first_seen": "abc123",
        "last_seen": last_seen,
        "lane": lane,
        "promotable": False,
        "status": status,
    }


# ---------------------------------------------------------------------------
# render from fixture queue
# ---------------------------------------------------------------------------

def test_select_board_entries_filters_lane_status_and_role():
    queue = [
        _entry("f1" * 20, path="roles/scout/a.py"),
        _entry("f2" * 20, path="roles/scout/b.py", lane="sweep"),
        _entry("f3" * 20, path="roles/scout/c.py", status="fixed"),
        _entry("f4" * 20, path="roles/other/d.py"),
    ]
    selected = patrol_board.select_board_entries(queue, "scout")
    assert [e["path"] for e in selected] == ["roles/scout/a.py"]


def test_render_board_body_pending_section_has_checkbox_lines():
    entries = [_entry("aa" * 20, excerpt="secret leaked here")]
    body = patrol_board.render_board_body(entries, [], [])
    assert "- [ ] `" + ("aa" * 20)[:12] + "`" in body
    assert patrol_board.PENDING_HEADING in body
    assert patrol_board.APPROVED_HEADING in body
    assert patrol_board.CLOSED_HEADING in body


def test_build_next_body_from_scratch_renders_all_pending():
    queue = [_entry("bb" * 20), _entry("cc" * 20)]
    body = patrol_board.build_next_body(None, "scout", queue)
    assert body.count("- [ ]") == 2


# ---------------------------------------------------------------------------
# edit-in-place idempotence
# ---------------------------------------------------------------------------

def test_same_queue_state_produces_identical_body_no_new_writes(tmp_path, monkeypatch):
    queue = [_entry("dd" * 20)]
    queue_path = tmp_path / "queue.jsonl"
    queue_path.write_text(json.dumps(queue[0], sort_keys=True) + "\n", encoding="utf-8")

    monkeypatch.setattr(patrol_board.spawn, "_repo_slug", lambda root: "acme/repo")
    first_body = patrol_board.build_next_body(None, "scout", queue)

    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        if cmd[:2] == ["gh", "api"]:
            payload = json.dumps([{"number": 42, "body": first_body}])
            stdout = f"HTTP/2.0 200 OK\r\netag: W/\"abc\"\r\n\r\n{payload}"
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        raise AssertionError(f"unexpected write call: {cmd}")

    monkeypatch.setattr(patrol_board.subprocess, "run", fake_run)
    result = patrol_board.run_patrol_board(tmp_path, "scout", queue_path,
                                            dry_run=False, date="2026-08-15")
    assert result["wrote"] is False
    assert not any(c[:3] == ["gh", "issue", "edit"] for c in calls)
    assert not any(c[:3] == ["gh", "issue", "create"] for c in calls)


# ---------------------------------------------------------------------------
# fingerprint dedup on board
# ---------------------------------------------------------------------------

def test_dedup_fingerprints_unchanged_entry_is_not_readded_or_bumped():
    fp = "ee" * 20
    existing = [patrol_board._finding_line(_entry(fp))]
    updated, fresh = patrol_board.dedup_fingerprints(existing, [_entry(fp)])
    assert fresh == []
    assert updated == existing


def test_dedup_fingerprints_bumps_counter_on_genuine_redetection():
    fp = "ff" * 20
    existing = [patrol_board._finding_line(_entry(fp, last_seen="abc123"))]
    updated, fresh = patrol_board.dedup_fingerprints(
        existing, [_entry(fp, last_seen="def456")])
    assert fresh == []
    assert "(seen 2x)" in updated[0]


def test_dedup_fingerprints_bump_increments_across_repeated_redetections():
    fp = "ab" * 20
    existing = [patrol_board._finding_line(_entry(fp, last_seen="abc123")) + " (seen 2x)"]
    updated, fresh = patrol_board.dedup_fingerprints(
        existing, [_entry(fp, last_seen="ghi789")])
    assert fresh == []
    assert "(seen 3x)" in updated[0]


def test_new_fingerprint_is_added_fresh():
    fp1, fp2 = "11" * 20, "22" * 20
    existing = [patrol_board._finding_line(_entry(fp1))]
    updated, fresh = patrol_board.dedup_fingerprints(existing, [_entry(fp2)])
    assert len(fresh) == 1
    assert fresh[0]["fingerprint"] == fp2
    assert len(updated) == 1


# ---------------------------------------------------------------------------
# absence-close section move
# ---------------------------------------------------------------------------

def test_absent_finding_moves_to_closed_section():
    queue_round1 = [_entry("33" * 20)]
    body1 = patrol_board.build_next_body(None, "scout", queue_round1)

    body2 = patrol_board.build_next_body(body1, "scout", [])
    sections = patrol_board.parse_board_body(body2)
    assert sections[patrol_board.PENDING_HEADING] == []
    assert any("33" * 20 in line[:20] or ("33" * 20)[:12] in line
               for line in sections[patrol_board.CLOSED_HEADING])


def test_still_present_finding_stays_pending_not_closed():
    fp = "44" * 20
    queue = [_entry(fp)]
    body1 = patrol_board.build_next_body(None, "scout", queue)
    body2 = patrol_board.build_next_body(body1, "scout", queue)
    sections = patrol_board.parse_board_body(body2)
    assert sections[patrol_board.CLOSED_HEADING] == []
    assert len(sections[patrol_board.PENDING_HEADING]) == 1


# ---------------------------------------------------------------------------
# write-budget drop-and-record
# ---------------------------------------------------------------------------

def test_write_budget_ok_respects_cap(tmp_path):
    date = "2026-08-15"
    assert patrol_board.write_budget_ok(tmp_path, date, cap=2) is True
    patrol_board.record_write(tmp_path, date)
    assert patrol_board.write_budget_ok(tmp_path, date, cap=2) is True
    patrol_board.record_write(tmp_path, date)
    assert patrol_board.write_budget_ok(tmp_path, date, cap=2) is False


def test_run_patrol_board_drops_and_records_when_budget_exceeded(tmp_path, monkeypatch):
    queue_path = tmp_path / "queue.jsonl"
    entry = _entry("55" * 20)
    queue_path.write_text(json.dumps(entry, sort_keys=True) + "\n", encoding="utf-8")

    monkeypatch.setattr(patrol_board.spawn, "_repo_slug", lambda root: "acme/repo")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        if cmd[:2] == ["gh", "api"]:
            stdout = "HTTP/2.0 200 OK\r\netag: W/\"z\"\r\n\r\n[]"
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        raise AssertionError(f"unexpected write call when budget should block it: {cmd}")

    monkeypatch.setattr(patrol_board.subprocess, "run", fake_run)

    date = "2026-08-15"
    # exhaust the budget before the run
    for _ in range(patrol_board.DEFAULT_DAILY_WRITE_BUDGET):
        patrol_board.record_write(tmp_path, date)

    result = patrol_board.run_patrol_board(tmp_path, "scout", queue_path,
                                            dry_run=False, date=date)
    assert result["dropped"] is True
    assert result["wrote"] is False
    drop_report = tmp_path / "docs" / "issue-1588" / "reports" / "write-budget-drops.md"
    assert drop_report.exists()
    assert "budget exceeded" in drop_report.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# ETag handling (mocked)
# ---------------------------------------------------------------------------

def test_find_board_issue_304_reuses_cache_and_bills_zero_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(patrol_board.spawn, "_repo_slug", lambda root: "acme/repo")
    cache_path = patrol_board._etag_cache_path(tmp_path, "scout")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({"etag": "W/\"abc\"",
                                       "raw": [{"number": 7, "body": "cached body"}]}),
                           encoding="utf-8")

    calls = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        assert any(h == "If-None-Match: W/\"abc\"" for h in cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="HTTP/2.0 304 Not Modified\r\n\r\n",
                                            stderr="")

    monkeypatch.setattr(patrol_board.subprocess, "run", fake_run)
    issue, ok, billed = patrol_board.find_board_issue(tmp_path, "scout")
    assert ok is True
    assert billed == 0
    assert issue == {"number": 7, "body": "cached body"}
    assert len(calls) == 1


def test_find_board_issue_200_writes_new_etag_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(patrol_board.spawn, "_repo_slug", lambda root: "acme/repo")

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        payload = json.dumps([{"number": 9, "body": "fresh body"}])
        stdout = f"HTTP/2.0 200 OK\r\netag: W/\"new-etag\"\r\n\r\n{payload}"
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(patrol_board.subprocess, "run", fake_run)
    issue, ok, billed = patrol_board.find_board_issue(tmp_path, "scout")
    assert ok is True
    assert billed == 1
    assert issue == {"number": 9, "body": "fresh body"}

    cache_path = patrol_board._etag_cache_path(tmp_path, "scout")
    cached = json.loads(cache_path.read_text(encoding="utf-8"))
    assert cached["etag"] == "W/\"new-etag\""


# ---------------------------------------------------------------------------
# --dry-run: 0 API calls
# ---------------------------------------------------------------------------

def test_dry_run_makes_zero_subprocess_calls(tmp_path, monkeypatch):
    queue_path = tmp_path / "queue.jsonl"
    entry = _entry("66" * 20)
    queue_path.write_text(json.dumps(entry, sort_keys=True) + "\n", encoding="utf-8")

    def fail_run(*a, **k):
        raise AssertionError("dry-run must make 0 subprocess calls")

    monkeypatch.setattr(patrol_board.subprocess, "run", fail_run)
    result = patrol_board.run_patrol_board(tmp_path, "scout", queue_path,
                                            dry_run=True, date="2026-08-15")
    assert result["api_calls"] == 0
    assert result["wrote"] is False
    assert ("66" * 20)[:12] in result["body"]


def test_select_routes_judge_scanner_id_to_role_board():
    # spawn.py judge_cmd enqueues with scanner_id="judge:<role>" and the
    # violated file's repo path — role boards must pick these up even though
    # the path carries no roles/<role>/ prefix (integration defect caught in
    # PR #1592 review).
    queue = [
        {"fingerprint": "a" * 64, "scanner_id": "judge:secure-coding",
         "path": "gates/foo.py", "finding_class": "x", "excerpt": "e",
         "lane": "diff", "status": "open"},
        {"fingerprint": "b" * 64, "scanner_id": "judge:other-role",
         "path": "gates/foo.py", "finding_class": "x", "excerpt": "e",
         "lane": "diff", "status": "open"},
        {"fingerprint": "c" * 64, "scanner_id": "record_lint",
         "path": "roles/secure-coding/thing.md", "finding_class": "x",
         "excerpt": "e", "lane": "diff", "status": "open"},
    ]
    got = patrol_board.select_board_entries(queue, "secure-coding")
    assert [e["fingerprint"][:1] for e in got] == ["a", "c"]


def test_find_board_issue_forces_get_method(monkeypatch, tmp_path):
    # gh api with -f fields and no explicit method defaults to POST, and
    # POST /issues is issue creation — the lookup must pin -X GET
    # (PR #1594 review, observed live as a 422 near-miss).
    seen = {}
    def fake_run(cmd, **kw):
        seen["cmd"] = cmd
        class R: returncode = 1; stdout = ""; stderr = ""
        return R()
    monkeypatch.setattr(patrol_board.subprocess, "run", fake_run)
    monkeypatch.setattr(patrol_board.spawn, "_repo_slug", lambda root: "o/r")
    patrol_board.find_board_issue(tmp_path, "x")
    i = seen["cmd"].index("-X")
    assert seen["cmd"][i + 1] == "GET"


def test_run_aborts_on_failed_lookup(monkeypatch, tmp_path):
    # ok=False from find_board_issue must never fall through to create.
    monkeypatch.setattr(patrol_board, "find_board_issue",
                        lambda root, role: (None, False, 1))
    called = {}
    monkeypatch.setattr(patrol_board.subprocess, "run",
                        lambda *a, **k: called.setdefault("create", True))
    qp = tmp_path / "queue.jsonl"; qp.write_text("")
    out = patrol_board.run_patrol_board(tmp_path, "x", qp, False, "2026-08-15")
    assert out.get("error") and "create" not in called
