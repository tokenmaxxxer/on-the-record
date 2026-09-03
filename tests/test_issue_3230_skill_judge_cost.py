"""Tests for issue-3230's diagnosis artifact:
scripts/issue-3230/measure_skill_judge.py.

Uses synthetic fixture ledger content written to tmp_path -- never depends
on the real ~/.tokenmaxxxer/work/ contents, which vary machine to machine
and may be empty in CI (same discipline as
tests/test_issue_3186_diagnosis_artifacts.py, per this issue's own
acceptance criterion for `--report`'s empty state).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "issue-3230" / "measure_skill_judge.py"

_spec = importlib.util.spec_from_file_location("measure_skill_judge", SCRIPT_PATH)
measure_skill_judge = importlib.util.module_from_spec(_spec)
sys.modules["measure_skill_judge"] = measure_skill_judge  # dataclasses needs this registered
_spec.loader.exec_module(measure_skill_judge)


def _real_event(wall_s: float, outcome_ok: bool = True, skill: str = "implementation",
                 issue: int = 4242) -> dict:
    return {
        "event": "skill_judge_perf", "ts": 1700000000, "skill": skill, "issue": issue,
        "wall_s": wall_s, "duration_ms": int(wall_s * 1000) - 200,
        "cache_read_input_tokens": 17416, "cache_creation_input_tokens": 7900,
        "concurrency": 1, "outcome_ok": outcome_ok,
    }


def _noise_event(issue: int = 2061) -> dict:
    # Shape of what this repo's own unit tests write when they monkeypatch
    # subprocess.run: zero wall clock, no duration_ms.
    return {
        "event": "skill_judge_perf", "ts": 1700000000, "skill": "implementation",
        "issue": issue, "wall_s": 0.0, "duration_ms": None,
        "cache_read_input_tokens": None, "cache_creation_input_tokens": None,
        "concurrency": 0, "outcome_ok": True,
    }


def _write_ledger(tmp_path: Path, name: str, events: list[dict]) -> Path:
    d = tmp_path / name / "runs"
    d.mkdir(parents=True)
    path = d / "ledger.jsonl"
    lines = [json.dumps(e) for e in events]
    # Interleave a non-skill_judge_perf event and a malformed line, matching
    # what a real ledger.jsonl looks like (other event types, and the
    # occasional partially-written line from a concurrent writer).
    lines.insert(0, json.dumps({"event": "issue_state_gate_fail_open", "ts": 1}))
    lines.append("{not valid json")
    path.write_text("\n".join(lines) + "\n")
    return path


class TestParsing:
    def test_parse_skill_judge_events_keeps_real_filters_noise(self, tmp_path):
        path = _write_ledger(tmp_path, "ws1", [
            _real_event(16.663), _noise_event(), _noise_event(issue=2274),
        ])
        raw, real = measure_skill_judge.parse_skill_judge_events(str(path))
        assert raw == 3
        assert len(real) == 1
        assert real[0].wall_s == 16.663

    def test_wall_s_below_floor_is_filtered_even_with_duration_ms(self, tmp_path):
        # duration_ms present but wall_s under the 1.0s plausibility floor --
        # still noise, not a real subprocess completion.
        event = _real_event(0.302)
        path = _write_ledger(tmp_path, "ws1", [event])
        _raw, real = measure_skill_judge.parse_skill_judge_events(str(path))
        assert real == []

    def test_wall_s_exactly_at_floor_is_kept(self, tmp_path):
        path = _write_ledger(tmp_path, "ws1", [_real_event(1.0)])
        _raw, real = measure_skill_judge.parse_skill_judge_events(str(path))
        assert len(real) == 1

    def test_malformed_lines_and_other_events_do_not_crash(self, tmp_path):
        path = _write_ledger(tmp_path, "ws1", [_real_event(10.0)])
        raw, real = measure_skill_judge.parse_skill_judge_events(str(path))
        assert raw == 1
        assert len(real) == 1


class TestAggregation:
    def test_timing_stats_computes_median_and_p90(self):
        events = [measure_skill_judge.SkillJudgeEvent(w, True, "implementation", 1, "f")
                  for w in (8.295, 10.0, 16.663, 23.0, 57.156)]
        stats = measure_skill_judge.timing_stats(events)
        assert stats["count"] == 5
        assert stats["min_s"] == 8.295
        assert stats["max_s"] == 57.156
        assert stats["median_s"] == 16.663
        assert stats["outcome_ok_count"] == 5

    def test_timing_stats_empty_list_reports_none_not_zero(self):
        stats = measure_skill_judge.timing_stats([])
        assert stats["count"] == 0
        assert stats["median_s"] is None

    def test_percentile_matches_linear_interpolation(self):
        assert measure_skill_judge._percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
        assert measure_skill_judge._percentile([1.0], 0.9) == 1.0


def _dispatch_ready_event(wall_s_to_popen: float, outcome: str,
                          issue: int = 4242) -> dict:
    return {
        "event": "dispatch_ready_perf", "ts": 1700000000, "skill": "implementation",
        "issue": issue, "skill_judge_outcome": outcome,
        "wall_s_to_popen": wall_s_to_popen,
    }


class TestDispatchReadyParsing:
    """Issue #3230: `dispatch_ready_perf` -- this round's own before/after
    evidence, added alongside the async dispatch change itself so a
    reader can compare consumer-facing wait pre/post from real
    `runs/ledger.jsonl` data, same discipline as the pre-existing
    `skill_judge_perf` scan above (must-not: extend the instrumentation,
    don't replace it)."""

    def test_parses_dispatch_ready_events_and_ignores_others(self, tmp_path):
        d = tmp_path / "ws1" / "runs"
        d.mkdir(parents=True)
        lines = [
            json.dumps(_dispatch_ready_event(20.7, "completed")),
            json.dumps(_real_event(16.663)),
            json.dumps(_dispatch_ready_event(0.05, "pending")),
        ]
        (d / "ledger.jsonl").write_text("\n".join(lines) + "\n")
        events = measure_skill_judge.parse_dispatch_ready_events(
            str(d / "ledger.jsonl"))
        assert len(events) == 2
        assert {e.skill_judge_outcome for e in events} == {"completed", "pending"}

    def test_missing_wall_s_field_is_skipped_not_crashed(self, tmp_path):
        d = tmp_path / "ws1" / "runs"
        d.mkdir(parents=True)
        (d / "ledger.jsonl").write_text(
            json.dumps({"event": "dispatch_ready_perf", "skill_judge_outcome": "pending"})
            + "\n")
        events = measure_skill_judge.parse_dispatch_ready_events(str(d / "ledger.jsonl"))
        assert events == []

    def test_stats_by_outcome_groups_and_reports_median(self):
        events = [
            measure_skill_judge.DispatchReadyEvent(20.0, "completed", "implementation", 1, "f"),
            measure_skill_judge.DispatchReadyEvent(24.0, "completed", "implementation", 1, "f"),
            measure_skill_judge.DispatchReadyEvent(0.05, "pending", "implementation", 1, "f"),
            measure_skill_judge.DispatchReadyEvent(0.07, "pending", "implementation", 1, "f"),
        ]
        by_outcome = measure_skill_judge.dispatch_ready_stats_by_outcome(events)
        assert by_outcome["completed"]["count"] == 2
        assert by_outcome["completed"]["median_s"] == 22.0
        assert by_outcome["pending"]["count"] == 2
        assert round(by_outcome["pending"]["median_s"], 6) == 0.06

    def test_empty_events_yields_empty_grouping(self):
        assert measure_skill_judge.dispatch_ready_stats_by_outcome([]) == {}


class TestReportShape:
    def test_report_contains_expected_sections(self, tmp_path):
        _write_ledger(tmp_path, "ws1", [_real_event(16.663), _noise_event()])
        scan = measure_skill_judge.scan_ledgers(str(tmp_path / "*" / "runs" / "ledger.jsonl"))
        report = measure_skill_judge.format_report(scan)
        assert "skill_judge subprocess wall-clock time" in report
        assert "n=1" in report
        assert "monkeypatched subprocess.run in this repo's own unit tests): 1" in report

    def test_cli_report_mode_exits_zero_and_prints_report(self, tmp_path):
        _write_ledger(tmp_path, "ws1", [_real_event(16.663)])
        glob_pattern = str(tmp_path / "*" / "runs" / "ledger.jsonl")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--ledger-glob", glob_pattern],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "skill_judge subprocess wall-clock time" in result.stdout
        assert "median=16.663s" in result.stdout


class TestEmptyState:
    """Acceptance criterion, verbatim: "if no skill_judge_perf event exists
    in any ledger, the report says so and exits nonzero rather than
    reporting a zero median"."""

    def test_no_ledger_files_at_all_exits_nonzero(self, tmp_path):
        glob_pattern = str(tmp_path / "nonexistent-*" / "runs" / "ledger.jsonl")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--ledger-glob", glob_pattern],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "no skill_judge_perf event found" in result.stderr.lower()
        assert "not a 0s median" in result.stderr.lower()
        assert result.stdout.strip() == ""

    def test_ledger_with_no_skill_judge_perf_lines_exits_nonzero(self, tmp_path):
        path = tmp_path / "ws1" / "runs"
        path.mkdir(parents=True)
        (path / "ledger.jsonl").write_text(
            json.dumps({"event": "issue_state_gate_fail_open", "ts": 1}) + "\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--ledger-glob",
             str(tmp_path / "*" / "runs" / "ledger.jsonl")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "no skill_judge_perf event found" in result.stderr.lower()

    def test_only_noise_events_exits_nonzero_distinct_message(self, tmp_path):
        path = _write_ledger(tmp_path, "ws1", [_noise_event(), _noise_event(issue=2040)])
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--report", "--ledger-glob",
             str(tmp_path / "*" / "runs" / "ledger.jsonl")],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "none passed the real-call filter" in result.stderr.lower()
        assert "share=" not in result.stdout
        assert result.stdout.strip() == ""

    def test_main_function_returns_nonzero_directly(self, tmp_path):
        glob_pattern = str(tmp_path / "nonexistent-*" / "runs" / "ledger.jsonl")
        rc = measure_skill_judge.main(["--report", "--ledger-glob", glob_pattern])
        assert rc != 0
