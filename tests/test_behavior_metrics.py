import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import behavior_metrics as bm


def test_recheck_count_from_fixture_ledger():
    entries = [
        {"role": "conformance-review", "issue": "1163", "subject_hash": "abc123"},
        {"role": "conformance-review", "issue": "1163", "subject_hash": "abc123"},
        {"role": "conformance-review", "issue": "1163", "subject_hash": "abc123"},
    ]
    counts = bm.recheck_counts(entries)
    assert counts[("conformance-review", "1163", "abc123")] == 3


def test_recheck_count_distinguishes_different_subjects():
    entries = [
        {"role": "conformance-review", "issue": "1163", "subject_hash": "abc123"},
        {"role": "conformance-review", "issue": "1163", "subject_hash": "abc123"},
        {"role": "conformance-review", "issue": "1163", "subject_hash": "def456"},
    ]
    counts = bm.recheck_counts(entries)
    assert counts[("conformance-review", "1163", "abc123")] == 2
    assert counts[("conformance-review", "1163", "def456")] == 1


def test_zero_commit_session_flagged():
    sessions = [
        {"role": "implementation", "issue": "1490", "commits": 0},
        {"role": "consult", "issue": "1490", "commits": 0},
        {"role": "implementation", "issue": "1163", "commits": 4},
    ]
    flagged = bm.zero_commit_sessions(sessions)
    assert len(flagged) == 1
    assert flagged[0]["role"] == "implementation"
    assert flagged[0]["issue"] == "1490"


def test_round_trip_counts_group_by_issue():
    paths = [
        "docs/issue-1163/proposals/a.md",
        "docs/issue-1163/reports/implementation.md",
        "docs/issue-1163/reports/conformance-review/deviation-log.md",
        "docs/issue-1199/proposals/b.md",
    ]
    counts = bm.round_trip_counts(paths)
    assert counts["1163"] == 3
    assert counts["1199"] == 1


def test_wait_poll_time_aggregates_per_issue():
    entries = [
        {"issue": "1163", "seconds": 30.0},
        {"issue": "1163", "seconds": 15.0},
        {"issue": "1199", "seconds": 5.0},
    ]
    totals = bm.wait_poll_time(entries)
    assert totals["1163"] == 45.0
    assert totals["1199"] == 5.0


def test_extract_recheck_entries_reads_real_deviation_log():
    entries = bm.extract_recheck_entries(bm.REPO)
    issues = {e["issue"] for e in entries}
    assert "1163" in issues


def test_extract_wait_poll_entries_reports_gap_not_derivable():
    assert bm.extract_wait_poll_entries(bm.REPO) == []
