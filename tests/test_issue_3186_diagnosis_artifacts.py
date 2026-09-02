"""Tests for issue-3186's diagnosis artifacts:
scripts/issue-3186/measure_cross_family.py.

Uses synthetic fixture log content written to tmp_path -- never depends on
the real ~/.tokenmaxxxer/work/ contents, which vary machine to machine and
may be empty in CI (per the issue's acceptance criterion).
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "issue-3186" / "measure_cross_family.py"

_spec = importlib.util.spec_from_file_location("measure_cross_family", SCRIPT_PATH)
measure_cross_family = importlib.util.module_from_spec(_spec)
sys.modules["measure_cross_family"] = measure_cross_family  # dataclasses needs this registered
_spec.loader.exec_module(measure_cross_family)


FIXTURE_LOG_SLOW = (
    '{"type":"user","message":{"content":"noise before"}}\n'
    "[implementation] bootstrap_timing admission=0.030 skill_resolve=0.010 "
    "workspace=1.800 branch=0.500 returned_pr_gate=0.000 auto_sweep=0.000 "
    "rulebook=0.000 core=0.000 gh_token=0.020 settings=0.001 "
    "cross_family=5.300 issue_fetch=0.400 directive_write=0.001 "
    "design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.100 total=7.300\n"
    "more noise\n"
)

FIXTURE_LOG_FAST = (
    "[implementation] bootstrap_timing admission=0.024 skill_resolve=0.000 "
    "workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 "
    "rulebook=0.000 core=0.000 gh_token=0.000 settings=0.000 "
    "cross_family=0.000 issue_fetch=0.000 directive_write=0.000 "
    "design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.000 total=0.025\n"
)

FIXTURE_LOG_WITH_REAL_MARKER = (
    "[implementation] bootstrap_timing admission=0.030 skill_resolve=0.010 "
    "workspace=1.800 branch=0.500 returned_pr_gate=0.000 auto_sweep=0.000 "
    "rulebook=0.000 core=0.000 gh_token=0.020 settings=0.001 "
    "cross_family=26.200 issue_fetch=0.400 directive_write=0.001 "
    "design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.100 total=29.500\n"
    "sys.exit: cross-family 후보 스킬 dup-skill 가 둘 이상의 소스에서 겹친다 "
    "-- skill-repo(/tmp/a/dup-skill), local-user(/tmp/b/dup-skill)\n"
)

FIXTURE_LOG_WITH_TEMPLATE_LITERAL = (
    "[implementation] bootstrap_timing admission=0.020 skill_resolve=0.000 "
    "workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 "
    "rulebook=0.000 core=0.000 gh_token=0.000 settings=0.000 "
    "cross_family=0.000 issue_fetch=0.000 directive_write=0.000 "
    "design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.000 total=0.021\n"
    'source quote: sys.exit(f"cross-family 후보 스킬 {name} 가 둘 이상의 '
    '소스에서 겹친다 ...")\n'
)

FIXTURE_LOG_NO_TIMING = (
    '{"type":"user","message":{"content":"nothing bootstrap-related here"}}\n'
)


def _write_logs(tmp_path: Path, contents: dict[str, str]) -> str:
    for name, text in contents.items():
        (tmp_path / name).write_text(text)
    return str(tmp_path / "*.session.*.log")


class TestParsing:
    def test_parse_bootstrap_timing_lines_extracts_phases_and_total(self):
        records = measure_cross_family.parse_bootstrap_timing_lines(FIXTURE_LOG_SLOW)
        assert len(records) == 1
        r = records[0]
        assert r.skill == "implementation"
        assert r.total == 7.300
        assert r.phases["cross_family"] == 5.300
        assert r.phases["workspace"] == 1.800

    def test_parse_drift_marker_lines_filters_template_literal(self):
        real_hits = measure_cross_family.parse_drift_marker_lines(FIXTURE_LOG_WITH_REAL_MARKER)
        assert len(real_hits) == 1
        assert real_hits[0].skill_name == "dup-skill"
        assert real_hits[0].is_template_literal is False

        template_hits = measure_cross_family.parse_drift_marker_lines(
            FIXTURE_LOG_WITH_TEMPLATE_LITERAL)
        assert len(template_hits) == 1
        assert template_hits[0].is_template_literal is True

    def test_parse_bootstrap_timing_lines_returns_empty_for_no_match(self):
        assert measure_cross_family.parse_bootstrap_timing_lines(FIXTURE_LOG_NO_TIMING) == []


class TestAggregation:
    def test_phase_share_stats_splits_slow_and_all_buckets(self):
        records = (
            measure_cross_family.parse_bootstrap_timing_lines(FIXTURE_LOG_SLOW)
            + measure_cross_family.parse_bootstrap_timing_lines(FIXTURE_LOG_FAST)
        )
        stats = measure_cross_family.phase_share_stats(records, phase="cross_family",
                                                          slow_threshold_s=1.0)
        assert stats["slow"]["count"] == 1
        assert stats["slow"]["phase_sum_s"] == 5.300
        assert stats["slow"]["total_sum_s"] == 7.300
        assert abs(stats["slow"]["share_pct"] - (5.300 / 7.300 * 100)) < 1e-6

        assert stats["all"]["count"] == 2
        assert abs(stats["all"]["total_sum_s"] - 7.325) < 1e-6

    def test_phase_share_stats_empty_bucket_reports_none_not_zero(self):
        stats = measure_cross_family.phase_share_stats([], phase="cross_family")
        assert stats["slow"]["count"] == 0
        assert stats["slow"]["share_pct"] is None

    def test_trigger_rate_stats_counts_named_vs_template(self):
        scan = measure_cross_family.LogScanResult()
        scan.timing_records = measure_cross_family.parse_bootstrap_timing_lines(
            FIXTURE_LOG_WITH_REAL_MARKER)
        scan.drift_hits = (
            measure_cross_family.parse_drift_marker_lines(FIXTURE_LOG_WITH_REAL_MARKER)
            + measure_cross_family.parse_drift_marker_lines(FIXTURE_LOG_WITH_TEMPLATE_LITERAL)
        )
        trig = measure_cross_family.trigger_rate_stats(scan)
        assert trig["named_match_count"] == 1
        assert trig["template_literal_count"] == 1
        assert trig["denominator_spawns"] == 1
        assert trig["rate"] == 1.0


class TestReportShape:
    def test_report_contains_expected_sections(self, tmp_path):
        glob_pattern = _write_logs(tmp_path, {
            "a.session.1.log": FIXTURE_LOG_SLOW,
            "b.session.2.log": FIXTURE_LOG_FAST,
        })
        scan = measure_cross_family.scan_logs(glob_pattern)
        report = measure_cross_family.format_report(scan)
        assert "cross_family phase share" in report
        assert "drift-guard marker matches" in report
        assert "CAVEAT" in report
        assert "log files scanned: 2" in report
        assert "bootstrap_timing lines found: 2" in report

    def test_cli_report_mode_exits_zero_and_prints_report(self, tmp_path):
        _write_logs(tmp_path, {"a.session.1.log": FIXTURE_LOG_SLOW})
        glob_pattern = str(tmp_path / "*.session.*.log")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--log-glob", glob_pattern],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "cross_family phase share" in result.stdout


class TestEmptyState:
    """Acceptance criterion, verbatim: "if no session log carries a
    bootstrap_timing line, the report says so and exits nonzero rather than
    reporting a zero rate"."""

    def test_no_bootstrap_timing_line_exits_nonzero_with_clear_message(self, tmp_path):
        glob_pattern = _write_logs(tmp_path, {"a.session.1.log": FIXTURE_LOG_NO_TIMING})
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--log-glob", glob_pattern],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "no bootstrap_timing line found" in result.stderr.lower()
        assert "not a 0%" in result.stderr or "NOT A 0%" in result.stderr.upper()
        # The empty-state message must not print a fabricated 0% share or
        # 0/0 rate to stdout as if it were a real report.
        assert "share=" not in result.stdout
        assert result.stdout.strip() == ""

    def test_no_matching_log_files_at_all_also_exits_nonzero(self, tmp_path):
        glob_pattern = str(tmp_path / "nonexistent-*.log")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--log-glob", glob_pattern],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "no bootstrap_timing line found" in result.stderr.lower()

    def test_main_function_returns_nonzero_directly(self, tmp_path):
        glob_pattern = _write_logs(tmp_path, {"a.session.1.log": FIXTURE_LOG_NO_TIMING})
        rc = measure_cross_family.main(["--report", "--log-glob", glob_pattern])
        assert rc != 0
