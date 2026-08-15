"""Live-fire test for patrol_queue.py (issue #914 mechanism b): calls the
module's own checking functions from >= 2 distinct scenarios and asserts
an outcome from each, in-process (patrol_queue.py has no hooks.json
lifecycle-event surface — it's invoked in-process by other gates/CLI,
not piped a stdin payload)."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patrol_queue as pq


def test_verify_allows_when_excerpt_present(tmp_path):
    target = tmp_path / "f.py"
    target.write_text("exact text here\n", encoding="utf-8")
    assert pq.verify({"path": "f.py", "excerpt": "exact text here"}, tmp_path) is True


def test_verify_denies_when_excerpt_absent(tmp_path):
    target = tmp_path / "f.py"
    target.write_text("something else\n", encoding="utf-8")
    assert pq.verify({"path": "f.py", "excerpt": "not present"}, tmp_path) is False


def test_finding_rule_id_reads_issue_number_from_context():
    finding = {"context_lines": [
        "레코드에 canonical 소스 인용 없는 상태/결함 주장 (issue #793): 'x'"]}
    assert pq._finding_rule_id(finding) == "793"


def test_finding_rule_id_none_when_no_context():
    assert pq._finding_rule_id({"context_lines": []}) is None


def _git(args, cwd):
    p = subprocess.run(["git", *args], cwd=str(cwd),
                        capture_output=True, text=True)
    assert p.returncode == 0, (args, p.stdout, p.stderr)


def _repo_with_disabled_rule_record(tmp_path):
    """A record that trips a #870-disabled rule (bare 'done.' claim, no
    canonical/derived evidence) — the sweep lane must exclude it and
    report the exclusion; the diff lane must still enqueue it."""
    _git(["init", "-q", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@example.com"], tmp_path)
    _git(["config", "user.name", "t"], tmp_path)
    rec = tmp_path / "docs/issue-2000/reports/other-role.md"
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_text(
        "---\nloop_state: landed\n---\n\n# record\n\n"
        "The migration is done.\n\n## What did not work\n\nNone.\n")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "head"], tmp_path)
    return tmp_path


def test_sweep_lane_excludes_disabled_rule_and_reports_count(tmp_path):
    root = _repo_with_disabled_rule_record(tmp_path)
    summary = pq.run_scan(root, "sweep")
    assert summary["sweep_disabled_rules_excluded"] >= 1, summary
    assert summary["sweep_disabled_rules_excluded_by_rule"].get("870", 0) >= 1, summary
    assert summary["enqueued"] == 0, summary


def test_diff_lane_keeps_disabled_rule_findings(tmp_path):
    root = _repo_with_disabled_rule_record(tmp_path)
    summary = pq.run_scan(root, "diff")
    assert summary["sweep_disabled_rules_excluded"] == 0, summary
    assert summary["enqueued"] >= 1, summary
