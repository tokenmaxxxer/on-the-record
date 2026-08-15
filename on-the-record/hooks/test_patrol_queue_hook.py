"""Tests for gates/patrol_queue.py (issue #1582)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "gates"))

import patrol_queue as pq


def test_fingerprint_stable_under_line_shift():
    context = ["def foo():", "    return 1"]
    fp1 = pq.fingerprint("scanner-a", "src/x.py", context)
    fp2 = pq.fingerprint("scanner-a", "src/x.py", context)
    assert fp1 == fp2

    fp3 = pq.fingerprint("scanner-a", "src/x.py", ["", "", *context])
    assert fp1 == fp3, "blank-line shift must not change fingerprint identity"


def test_fingerprint_differs_by_scanner_and_path():
    context = ["same context"]
    fp_a = pq.fingerprint("scanner-a", "src/x.py", context)
    fp_b = pq.fingerprint("scanner-b", "src/x.py", context)
    fp_c = pq.fingerprint("scanner-a", "src/y.py", context)
    assert len({fp_a, fp_b, fp_c}) == 3


def _finding(fp, path="src/x.py", lane="sweep", promotable=False, seen="run1"):
    return {
        "fingerprint": fp,
        "scanner_id": "scanner-a",
        "path": path,
        "finding_class": "test-class",
        "excerpt": "some excerpt",
        "last_seen": seen,
        "lane": lane,
        "promotable": promotable,
    }


def test_enqueue_dedup_refreshes_last_seen_only():
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    queue = pq.enqueue([], _finding(fp, seen="run1"))
    assert len(queue) == 1
    assert queue[0]["first_seen"] == "run1"

    queue = pq.enqueue(queue, _finding(fp, seen="run2"))
    assert len(queue) == 1
    assert queue[0]["first_seen"] == "run1"
    assert queue[0]["last_seen"] == "run2"


def test_absence_close_marks_fixed():
    fp1 = pq.fingerprint("scanner-a", "src/x.py", ["ctx1"])
    fp2 = pq.fingerprint("scanner-a", "src/y.py", ["ctx2"])
    queue = pq.enqueue([], _finding(fp1, path="src/x.py", seen="run1"))
    queue = pq.enqueue(queue, _finding(fp2, path="src/y.py", seen="run1"))

    queue = pq.absence_close(queue, "src/", {fp1})
    by_fp = {e["fingerprint"]: e for e in queue}
    assert by_fp[fp1]["status"] == "open"
    assert by_fp[fp2]["status"] == "fixed"


def test_lane_separation_sweep_never_promotable():
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    queue = pq.enqueue([], _finding(fp, lane="sweep", promotable=True))
    assert queue[0]["lane"] == "sweep"
    assert queue[0]["promotable"] is False, \
        "sweep-lane entries must never be marked promotable regardless of caller intent"


def test_lane_diff_can_be_promotable():
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    queue = pq.enqueue([], _finding(fp, lane="diff", promotable=True))
    assert queue[0]["promotable"] is True


def test_lane_unknown_rejected():
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    try:
        pq.enqueue([], _finding(fp, lane="bogus"))
        assert False, "expected ValueError for unknown lane"
    except ValueError:
        pass


def test_apply_budget_truncates_and_reports_drop_count():
    findings = [
        {"scanner_id": "s1", "lane": "sweep"} for _ in range(5)
    ]
    kept, meta = pq.apply_budget(findings, per_scanner_cap=3)
    assert len(kept) == 3
    assert len(meta) == 1
    assert "2 more" in meta[0]["excerpt"]


def test_apply_budget_no_meta_when_under_cap():
    findings = [{"scanner_id": "s1", "lane": "sweep"} for _ in range(2)]
    kept, meta = pq.apply_budget(findings, per_scanner_cap=3)
    assert len(kept) == 2
    assert meta == []


def test_verify_drops_when_excerpt_missing(tmp_path):
    target = tmp_path / "file.py"
    target.write_text("actual content here\n", encoding="utf-8")
    finding_ok = {"path": "file.py", "excerpt": "actual content here"}
    finding_bad = {"path": "file.py", "excerpt": "this text is not present"}
    assert pq.verify(finding_ok, tmp_path) is True
    assert pq.verify(finding_bad, tmp_path) is False


def test_verify_drops_when_path_missing(tmp_path):
    finding = {"path": "nowhere.py", "excerpt": "anything"}
    assert pq.verify(finding, tmp_path) is False


def test_dismissal_suppresses_reappearance():
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    queue = pq.enqueue([], _finding(fp))
    queue = pq.record_dismissal(queue, fp, "false-positive")
    assert pq.is_dismissed(queue, fp) is True

    counts = pq.dismissal_counts(queue)
    assert counts["scanner-a"] == 1


def test_dismissal_unknown_reason_rejected():
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    queue = pq.enqueue([], _finding(fp))
    try:
        pq.record_dismissal(queue, fp, "bogus-reason")
        assert False, "expected ValueError for unknown dismissal reason"
    except ValueError:
        pass


def test_save_and_load_queue_roundtrip(tmp_path):
    fp = pq.fingerprint("scanner-a", "src/x.py", ["ctx"])
    queue = pq.enqueue([], _finding(fp))
    queue_path = tmp_path / ".on-the-record" / "findings" / "queue.jsonl"
    pq.save_queue(queue_path, queue)
    loaded = pq.load_queue(queue_path)
    assert loaded == queue


def test_run_scan_empty_repo_no_records(tmp_path):
    summary = pq.run_scan(tmp_path, lane="sweep")
    assert summary["raw_findings"] == 0
    assert summary["enqueued"] == 0
    queue_path = tmp_path / pq.QUEUE_REL_PATH
    assert pq.load_queue(queue_path) == []
