import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import patrol_board  # noqa: E402
import patrol_promote  # noqa: E402


def _entry(fp, path="roles/scout/foo.py", excerpt="bad thing here",
           scanner_id="record_lint", finding_class="record-lint-violation",
           severity="medium", last_seen="abc123"):
    return {
        "fingerprint": fp,
        "scanner_id": scanner_id,
        "path": path,
        "finding_class": finding_class,
        "excerpt": excerpt,
        "first_seen": last_seen,
        "last_seen": last_seen,
        "lane": "diff",
        "promotable": True,
        "status": "open",
        "severity": severity,
    }


FP1 = "aa" * 20
FP2 = "bb" * 20


# ---------------------------------------------------------------------------
# tick detection from body diff
# ---------------------------------------------------------------------------

def test_detect_ticks_only_fires_on_transition():
    queue = [_entry(FP1), _entry(FP2)]
    unchecked_body = patrol_board.build_next_body(None, "scout", queue)
    # simulate a human checking FP1's box
    checked_body = unchecked_body.replace(f"- [ ] `{FP1[:12]}`", f"- [x] `{FP1[:12]}`")

    ticks = patrol_promote.detect_ticks(unchecked_body, checked_body, queue)
    assert [e["fingerprint"] for e in ticks] == [FP1]

    # a body already checked in both prior and new -> not a fresh tick
    ticks_again = patrol_promote.detect_ticks(checked_body, checked_body, queue)
    assert ticks_again == []


def test_detect_ticks_first_run_prior_none_treats_checked_as_fresh():
    queue = [_entry(FP1)]
    body = patrol_board.build_next_body(None, "scout", queue)
    checked_body = body.replace(f"- [ ] `{FP1[:12]}`", f"- [x] `{FP1[:12]}`")
    ticks = patrol_promote.detect_ticks(None, checked_body, queue)
    assert [e["fingerprint"] for e in ticks] == [FP1]


# ---------------------------------------------------------------------------
# structured issue body
# ---------------------------------------------------------------------------

def test_build_finding_issue_body_has_required_fields_and_marker():
    entry = _entry(FP1, severity="high", excerpt="leaked secret")
    body = patrol_promote.build_finding_issue_body(entry)
    assert FP1 in body
    assert "record_lint" in body
    assert "record-lint-violation" in body
    assert "roles/scout/foo.py@abc123" in body
    assert "high" in body
    assert "leaked secret" in body
    assert f"<!-- patrol:promoted fp={FP1} -->" in body


# ---------------------------------------------------------------------------
# rate caps
# ---------------------------------------------------------------------------

def test_rate_cap_hourly_blocks_third_promotion_same_hour():
    state = {"promotions": ["2026-08-15T10:00:00", "2026-08-15T10:30:00"],
              "open_issue_numbers": []}
    hourly_ok, open_ok = patrol_promote.rate_cap_ok(state, "2026-08-15T10")
    assert hourly_ok is False
    assert open_ok is True


def test_rate_cap_hourly_resets_next_hour():
    state = {"promotions": ["2026-08-15T10:00:00", "2026-08-15T10:30:00"],
              "open_issue_numbers": []}
    hourly_ok, _ = patrol_promote.rate_cap_ok(state, "2026-08-15T11")
    assert hourly_ok is True


def test_rate_cap_open_count_blocks_at_ten():
    state = {"promotions": [], "open_issue_numbers": list(range(10))}
    _, open_ok = patrol_promote.rate_cap_ok(state, "2026-08-15T10")
    assert open_ok is False


# ---------------------------------------------------------------------------
# board line move
# ---------------------------------------------------------------------------

def test_move_ticked_line_promotes_to_approved_section():
    pending = ["- [x] `aaaaaaaaaaaa` record-lint-violation roles/scout/foo.py@abc123 (medium): bad"]
    approved = []
    new_pending, new_approved = patrol_promote.move_ticked_line(
        pending, approved, "aaaaaaaaaaaa", 42)
    assert new_pending == []
    assert len(new_approved) == 1
    assert "#42" in new_approved[0]


def test_move_ticked_line_rate_cap_annotation_stays_pending():
    pending = ["- [x] `aaaaaaaaaaaa` record-lint-violation roles/scout/foo.py@abc123 (medium): bad"]
    new_pending, new_approved = patrol_promote.move_ticked_line(
        pending, [], "aaaaaaaaaaaa", None, annotation="queued: rate cap")
    assert new_approved == []
    assert len(new_pending) == 1
    assert new_pending[0].endswith("(queued: rate cap)")
    assert new_pending[0].startswith("- [x]")


# ---------------------------------------------------------------------------
# promotion idempotence + anti-loop marker (find_existing_promotion stubbed)
# ---------------------------------------------------------------------------

def test_promote_tick_idempotent_when_marker_already_found(monkeypatch, tmp_path):
    entry = _entry(FP1)
    monkeypatch.setattr(patrol_promote, "find_existing_promotion",
                         lambda root, fp: 7 if fp == FP1 else None)

    def _boom(*a, **k):
        raise AssertionError("gh issue create must not be called when already promoted")
    monkeypatch.setattr(patrol_promote.subprocess, "run", _boom)

    state = {"promotions": [], "open_issue_numbers": []}
    result = patrol_promote.promote_tick(tmp_path, "scout", entry, state, "2026-08-15T10:00:00")
    assert result == {"promoted": True, "issue": 7, "already_existed": True}
    assert state["promotions"] == []  # idempotent path never touches cap state


def test_promote_tick_over_cap_defers_without_gh_call(monkeypatch, tmp_path):
    entry = _entry(FP1)
    monkeypatch.setattr(patrol_promote, "find_existing_promotion", lambda root, fp: None)

    def _boom(*a, **k):
        raise AssertionError("gh issue create must not be called over cap")
    monkeypatch.setattr(patrol_promote.subprocess, "run", _boom)

    state = {"promotions": ["2026-08-15T10:00:00", "2026-08-15T10:10:00"],
              "open_issue_numbers": []}
    result = patrol_promote.promote_tick(tmp_path, "scout", entry, state, "2026-08-15T10:20:00")
    assert result == {"promoted": False, "reason": "rate_cap"}


def test_promote_tick_creates_issue_and_records_state(monkeypatch, tmp_path):
    entry = _entry(FP1)
    monkeypatch.setattr(patrol_promote, "find_existing_promotion", lambda root, fp: None)

    calls = []

    class _R:
        returncode = 0
        stdout = "https://github.com/acme/repo/issues/99\n"
        stderr = ""

    def _fake_run(cmd, **kwargs):
        calls.append(cmd)
        return _R()

    monkeypatch.setattr(patrol_promote.subprocess, "run", _fake_run)

    state = {"promotions": [], "open_issue_numbers": []}
    result = patrol_promote.promote_tick(tmp_path, "scout", entry, state, "2026-08-15T10:00:00")
    assert result == {"promoted": True, "issue": 99}
    assert state["promotions"] == ["2026-08-15T10:00:00"]
    assert state["open_issue_numbers"] == [99]
    create_calls = [c for c in calls if c[:3] == ["gh", "issue", "create"]]
    assert create_calls[0][:3] == ["gh", "issue", "create"]
    assert patrol_promote.LABEL_PROMOTED in calls[0]


# ---------------------------------------------------------------------------
# state persistence (restart durability)
# ---------------------------------------------------------------------------

def test_state_survives_reload(tmp_path):
    state = {"promotions": ["2026-08-15T10:00:00"], "open_issue_numbers": [5]}
    patrol_promote.save_state(tmp_path, "scout", state)
    reloaded = patrol_promote.load_state(tmp_path, "scout")
    assert reloaded == state


def test_prior_body_survives_reload(tmp_path):
    patrol_promote.save_prior_body(tmp_path, "scout", "some body text")
    assert patrol_promote.load_prior_body(tmp_path, "scout") == "some body text"
    assert patrol_promote.load_prior_body(tmp_path, "other-role") is None


# ---------------------------------------------------------------------------
# end-to-end: run_patrol_promote, gh stubbed
# ---------------------------------------------------------------------------

def test_end_to_end_one_tick_promotes_exactly_once_then_zero_writes(monkeypatch, tmp_path):
    queue = [_entry(FP1, path="roles/scout/foo.py")]
    queue_path = tmp_path / ".on-the-record" / "findings" / "queue.jsonl"
    queue_path.parent.mkdir(parents=True)
    queue_path.write_text("\n".join(json.dumps(e, sort_keys=True) for e in queue) + "\n")

    unchecked_body = patrol_board.build_next_body(None, "scout", queue)
    checked_body = unchecked_body.replace(f"- [ ] `{FP1[:12]}`", f"- [x] `{FP1[:12]}`")

    board_state = {"body": checked_body, "number": 5}

    def _fake_find_board_issue(root, role):
        return board_state, True, 1
    monkeypatch.setattr(patrol_board, "find_board_issue", _fake_find_board_issue)
    monkeypatch.setattr(patrol_promote.patrol_board, "find_board_issue", _fake_find_board_issue)

    monkeypatch.setattr(patrol_promote, "find_existing_promotion", lambda root, fp: None)

    gh_calls = []

    class _R:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def _fake_run(cmd, **kwargs):
        gh_calls.append(cmd)
        if cmd[:3] == ["gh", "issue", "create"]:
            return _R(stdout="https://github.com/acme/repo/issues/101\n")
        if cmd[:3] == ["gh", "issue", "edit"]:
            board_state["body"] = cmd[cmd.index("--body") + 1]
            return _R()
        if cmd[:3] == ["gh", "label", "create"]:
            return _R()
        raise AssertionError(f"unexpected gh call: {cmd}")

    monkeypatch.setattr(patrol_promote.subprocess, "run", _fake_run)

    result1 = patrol_promote.run_patrol_promote(
        tmp_path, "scout", queue_path, dry_run=False, now_iso="2026-08-15T10:00:00")

    assert result1["promotions"] == [{"fingerprint": FP1, "issue": 101}]
    assert "#101" in board_state["body"]
    create_calls = [c for c in gh_calls if c[:3] == ["gh", "issue", "create"]]
    assert len(create_calls) == 1

    # second poll: nothing new ticked, body unchanged from what run 1 wrote ->
    # zero further gh writes (the only call may be the ETag-conditional read,
    # stubbed above to bill 1; no create/edit calls this time).
    gh_calls.clear()
    result2 = patrol_promote.run_patrol_promote(
        tmp_path, "scout", queue_path, dry_run=False, now_iso="2026-08-15T10:05:00")
    assert result2["promotions"] == []
    assert gh_calls == []
