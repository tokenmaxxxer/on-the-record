"""Tests for gates/patrol_trigger.py (issue #1582), including the
#1360-class regression test: patrol's own artifact commits must never
re-arm the trigger."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "gates"))

import patrol_trigger as pt
import patrol_queue as pq


def test_should_fire_on_genuine_change():
    event = {"changed_files": ["src/app.py", "README.md"]}
    assert pt.should_fire(event) is True


def test_should_fire_false_on_no_changed_files():
    assert pt.should_fire({"changed_files": []}) is False
    assert pt.should_fire({}) is False


def test_should_fire_false_when_only_queue_file_changed_1360_regression():
    """#1360-class regression: an event whose only diff is patrol's own
    queue-file commit must not re-arm the trigger."""
    event = {"changed_files": [pq.QUEUE_REL_PATH]}
    assert pt.should_fire(event) is False, (
        "patrol-produced queue-file-only diff must not satisfy the "
        "re-arm condition (#1360-class recursive self-triggering)"
    )


def test_should_fire_false_when_only_measurement_record_changed():
    event = {"changed_files": [
        "docs/issue-1582/reports/patrol-measurement-2026-08-15.md",
    ]}
    assert pt.should_fire(event) is False


def test_should_fire_true_when_mixed_with_genuine_change():
    event = {"changed_files": [pq.QUEUE_REL_PATH, "src/app.py"]}
    assert pt.should_fire(event) is True, (
        "a mixed diff containing a genuine change must still fire even "
        "if a patrol artifact is also present"
    )


def test_1360_regression_fails_without_origin_check():
    """Proves the guard is load-bearing: with the origin-check inlined
    out (simulating the pre-fix `should_fire`), a queue-only event would
    incorrectly fire. This asserts the *correct* function still refuses
    it — the companion "would fire without the check" fact is documented
    here, not executed, since reverting a private module function isn't
    meaningful outside the source file itself."""
    naive_should_fire = lambda event: bool(event.get("changed_files"))
    event = {"changed_files": [pq.QUEUE_REL_PATH]}
    assert naive_should_fire(event) is True, \
        "sanity: a naive (pre-#1360-fix-shaped) check would incorrectly fire"
    assert pt.should_fire(event) is False, \
        "the actual origin-check-bearing should_fire must refuse the same event"


def test_run_if_eligible_skips_when_not_eligible(tmp_path):
    event = {"changed_files": [pq.QUEUE_REL_PATH]}
    result = pt.run_if_eligible(event, tmp_path)
    assert result is None


def test_run_if_eligible_runs_scan_when_eligible(tmp_path):
    event = {"changed_files": ["src/app.py"]}
    result = pt.run_if_eligible(event, tmp_path, lane="sweep")
    assert result is not None
    assert result["lane"] == "sweep"
