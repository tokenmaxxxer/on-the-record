#!/usr/bin/env python3
"""issue-3230: recompute the skill_judge dispatch-wait statistics from real
`runs/ledger.jsonl` `skill_judge_perf` events (issue-3186 located this cost
inside `_skill_judge_consult()`'s subprocess; PR #3200 first pulled a median
from this same instrumentation -- n=19, 8.3-57.2s, median 16.663s).

Diagnosis-only tooling -- this script does not modify consult.py, spawn.py,
or any dispatch path. It only reads `skill_judge_perf` ledger events already
written by real spawns (`consult.py:_skill_judge_consult`'s `finally` block)
and reports statistics derived from them.

Portable by construction: parsing uses only the stdlib (`os`, `pathlib`,
`glob`, `json`, `argparse`, `statistics`) -- no shelling out to `date`,
`stat`, `find`, or any GNU-only tool, and no `/proc` reads, so behavior is
identical on macOS and Linux.

Usage:
    python3 scripts/issue-3230/measure_skill_judge.py --report
    python3 scripts/issue-3230/measure_skill_judge.py --report --ledger-glob '/path/*/runs/ledger.jsonl'
    MEASURE_SKILL_JUDGE_LEDGER_GLOB='/path/*/runs/ledger.jsonl' python3 scripts/issue-3230/measure_skill_judge.py --report

Empty-state discipline (silent-failure-audit relevant, same discipline
scripts/issue-3186/measure_cross_family.py uses): if zero *real* (i.e.
plausible, non-test-noise) `skill_judge_perf` events are found anywhere in
the scanned ledgers, this script exits nonzero and prints an explicit
"no data" message. It never reports a 0s median as if that were a real
measurement -- a caller checking only the exit code cannot mistake "no
data" for "the wait is zero" (see `--report`'s exit-code contract in
`main()`).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_LEDGER_GLOB = os.path.expanduser("~/.tokenmaxxxer/work/*/runs/ledger.jsonl")
LEDGER_GLOB_ENV_VAR = "MEASURE_SKILL_JUDGE_LEDGER_GLOB"

# consult.py's own `_MIN_PLAUSIBLE_JUDGE_WALL_S` (1.0) and its
# `_skill_judge_perf_samples()` filter: an event counts as a real subprocess
# completion only when it carries a `duration_ms` (the model's own reported
# duration) AND a `wall_s` at or above this floor. Both conditions together
# are what excludes this repo's own unit tests for `_skill_judge_consult`,
# which monkeypatch `subprocess.run` and write `wall_s=0.0`/`duration_ms=None`
# noise into whatever ledger the test happened to run against (issue-3186's
# diagnosis measured 1262 such noise events against 19 real ones). Hardcoded
# here rather than imported from consult.py so this script stays a
# standalone, dependency-free reader of the ledger file format, matching
# scripts/issue-3186/measure_cross_family.py's independence from
# pipeline.py/spawn.py -- if consult.py's threshold ever changes, a reader
# of both files must update this constant too (no single source of truth
# across the diagnosis-script / dispatch-path boundary).
MIN_PLAUSIBLE_JUDGE_WALL_S = 1.0


@dataclass
class SkillJudgeEvent:
    wall_s: float
    outcome_ok: bool | None
    skill: str | None
    issue: object
    source_file: str


@dataclass
class LedgerScanResult:
    files_scanned: list[str] = field(default_factory=list)
    raw_event_count: int = 0  # every skill_judge_perf event, including noise
    real_events: list[SkillJudgeEvent] = field(default_factory=list)


def resolve_ledger_paths(ledger_glob: str | None = None) -> list[str]:
    """Resolve the glob pattern to scan: explicit arg > env var > built-in
    default. Uses `glob.glob` (stdlib, portable) -- never shells out."""
    pattern = ledger_glob or os.environ.get(LEDGER_GLOB_ENV_VAR) or DEFAULT_LEDGER_GLOB
    return sorted(glob.glob(os.path.expanduser(pattern)))


def _iter_jsonl(path: str):
    try:
        text = Path(path).read_text(errors="replace")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def parse_skill_judge_events(path: str) -> tuple[int, list[SkillJudgeEvent]]:
    """Returns (raw_count, real_events) for one ledger file. `raw_count`
    counts every `skill_judge_perf` line regardless of plausibility, so the
    report can show how much noise was filtered out (issue-3186's own
    1262-vs-19 finding)."""
    raw = 0
    real: list[SkillJudgeEvent] = []
    for obj in _iter_jsonl(path):
        if not isinstance(obj, dict) or obj.get("event") != "skill_judge_perf":
            continue
        raw += 1
        if obj.get("duration_ms") is None:
            continue
        wall = obj.get("wall_s")
        if not isinstance(wall, (int, float)) or wall < MIN_PLAUSIBLE_JUDGE_WALL_S:
            continue
        real.append(SkillJudgeEvent(
            wall_s=float(wall),
            outcome_ok=obj.get("outcome_ok"),
            skill=obj.get("skill"),
            issue=obj.get("issue"),
            source_file=path,
        ))
    return raw, real


def scan_ledgers(ledger_glob: str | None = None) -> LedgerScanResult:
    result = LedgerScanResult()
    for path in resolve_ledger_paths(ledger_glob):
        result.files_scanned.append(path)
        raw, real = parse_skill_judge_events(path)
        result.raw_event_count += raw
        result.real_events.extend(real)
    return result


def _percentile(sorted_data: list[float], p: float) -> float:
    """Linear-interpolation percentile (same method as numpy's default
    'linear' and consult.py's own `_percentile()`) -- `sorted_data` must
    already be ascending."""
    if not sorted_data:
        raise ValueError("empty data")
    k = (len(sorted_data) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


def timing_stats(events: list[SkillJudgeEvent]) -> dict:
    if not events:
        return {"count": 0, "min_s": None, "max_s": None, "mean_s": None,
                "median_s": None, "p90_s": None}
    walls = sorted(e.wall_s for e in events)
    ok_count = sum(1 for e in events if e.outcome_ok is True)
    return {
        "count": len(walls),
        "min_s": walls[0],
        "max_s": walls[-1],
        "mean_s": statistics.mean(walls),
        "median_s": statistics.median(walls),
        "p90_s": _percentile(walls, 0.9),
        "outcome_ok_count": ok_count,
    }


def format_report(scan: LedgerScanResult) -> str:
    lines = []
    lines.append("issue-3230 skill_judge dispatch-wait -- measured report")
    lines.append(f"ledger files scanned: {len(scan.files_scanned)}")
    lines.append(f"raw skill_judge_perf events found: {scan.raw_event_count}")
    lines.append(
        f"real (plausible) events after filter "
        f"(duration_ms present AND wall_s >= {MIN_PLAUSIBLE_JUDGE_WALL_S}s): "
        f"{len(scan.real_events)}"
    )
    noise = scan.raw_event_count - len(scan.real_events)
    if noise:
        lines.append(
            f"  filtered out as test-fixture noise (monkeypatched "
            f"subprocess.run in this repo's own unit tests): {noise}"
        )
    lines.append("")

    stats = timing_stats(scan.real_events)
    lines.append("-- skill_judge subprocess wall-clock time, per real dispatch --")
    lines.append(
        f"  n={stats['count']} min={stats['min_s']:.3f}s max={stats['max_s']:.3f}s "
        f"mean={stats['mean_s']:.3f}s median={stats['median_s']:.3f}s "
        f"p90={stats['p90_s']:.3f}s"
    )
    lines.append(
        f"  outcome_ok=True: {stats['outcome_ok_count']}/{stats['count']}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true",
                         help="print a human-readable report")
    parser.add_argument("--ledger-glob", default=None,
                         help=f"glob pattern for runs/ledger.jsonl files (default: env "
                              f"{LEDGER_GLOB_ENV_VAR} or {DEFAULT_LEDGER_GLOB!r})")
    args = parser.parse_args(argv)

    scan = scan_ledgers(args.ledger_glob)

    if not scan.real_events:
        # Empty-state discipline: never report a 0s median as if it were
        # real data. Loud failure, nonzero exit. Distinguish "no
        # skill_judge_perf event at all" from "events exist but all were
        # filtered out as noise" -- both are "no data", but for different
        # reasons a reader should know about.
        pattern = args.ledger_glob or os.environ.get(LEDGER_GLOB_ENV_VAR) or DEFAULT_LEDGER_GLOB
        if scan.raw_event_count == 0:
            detail = (f"no skill_judge_perf event found in any scanned ledger "
                      f"({len(scan.files_scanned)} files matched {pattern!r}).")
        else:
            detail = (f"{scan.raw_event_count} skill_judge_perf event(s) found "
                      f"in {len(scan.files_scanned)} file(s) matching {pattern!r}, "
                      f"but none passed the real-call filter (duration_ms "
                      f"present and wall_s >= {MIN_PLAUSIBLE_JUDGE_WALL_S}s) -- "
                      f"all of them look like monkeypatched test noise.")
        print(
            f"ERROR: {detail} This means NO DATA, not a 0s median wait -- "
            "do not treat this exit as a measurement.",
            file=sys.stderr,
        )
        return 1

    if args.report:
        print(format_report(scan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
