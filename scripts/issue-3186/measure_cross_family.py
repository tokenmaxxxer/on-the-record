#!/usr/bin/env python3
"""issue-3186: recompute the cross_family bootstrap-phase share and the
drift-guard trigger rate from real session logs.

Diagnosis-only tooling -- this script does not modify pipeline.py,
directive_assembly.py, or any dispatch path. It only reads session logs
already written by real spawns and reports statistics derived from them.

Portable by construction: parsing uses only the stdlib (`os`, `pathlib`,
`glob`, `re`, `json`, `argparse`) -- no shelling out to `date`, `stat`,
`find`, or any GNU-only tool, so behavior is identical on macOS and Linux.

Usage:
    python3 scripts/issue-3186/measure_cross_family.py --report
    python3 scripts/issue-3186/measure_cross_family.py --report --log-glob '/path/*.log'
    MEASURE_CROSS_FAMILY_LOG_GLOB='/path/*.log' python3 scripts/issue-3186/measure_cross_family.py --report

Empty-state discipline (silent-failure-audit relevant): if zero
bootstrap_timing lines are found anywhere in the scanned logs, this script
exits nonzero and prints an explicit "no data" message. It never reports a
0% phase share or a 0/0 trigger rate as if that were a real measurement --
a caller checking only the exit code cannot mistake "no data" for "rate is
zero" (see `--report`'s exit-code contract in `main()`).
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_LOG_GLOB = os.path.expanduser("~/.tokenmaxxxer/work/*.session.*.log")
LOG_GLOB_ENV_VAR = "MEASURE_CROSS_FAMILY_LOG_GLOB"

# One bootstrap_timing line looks like:
#   [<skill>] bootstrap_timing admission=0.024 skill_resolve=0.000 ... total=0.025
# `_bootstrap_timing_line()` in pipeline.py emits it; `_BOOTSTRAP_PHASES` in
# spawn.py fixes the phase name set (this script does not hardcode that
# tuple -- it just reads whatever `phase=value` pairs appear before `total=`).
_BOOTSTRAP_TIMING_RE = re.compile(
    r"\[([^\]\n]*)\]\s*bootstrap_timing\s+((?:\w+=[0-9.]+\s+)*total=([0-9.]+))"
)
_PHASE_PAIR_RE = re.compile(r"(\w+)=([0-9.]+)")

# The drift-abort marker: `_cross_family_candidate_corpus()` (pipeline.py)
# calls `sys.exit(f"cross-family 후보 스킬 {name} 가 둘 이상의 소스에서 겹친다 ...")`
# when the same skill name resolves to different content across tiers. That
# f-string, once a real name is interpolated, is a marker distinguishable
# from every other exit/abort message in this codebase (no other message
# shares the "cross-family 후보 스킬 ... 둘 이상의 소스에서 겹친다" phrase).
#
# A session log can also contain this exact text WITHOUT it ever having
# fired in real spawn dispatch -- e.g. another agent's transcript grepping
# pipeline.py's source, or a *deliberate* manual reproduction while testing
# the guard itself (both observed in this repo's real logs during issue-3186
# investigation -- see the record). The source-code render is syntactically
# distinguishable from ANY firing (deliberate or organic): the source line
# still carries the literal, un-interpolated `{name}` placeholder
# (`f"...스킬 {name} 가..."`), which this script filters out. It CANNOT
# further distinguish an organic dispatch-time abort from a deliberate
# manual reproduction (both have a real name interpolated) -- that
# attribution requires reading the surrounding transcript by hand. The
# report below labels the interpolated-name count as "raw marker matches"
# for this reason, not as a verified production trigger count.
_DRIFT_MARKER_RE = re.compile(
    r"cross-family 후보 스킬 (\S+) 가 둘 이상의 소스에서 겹친다"
)
_DRIFT_MARKER_TEMPLATE_LITERAL = "{name}"


@dataclass
class BootstrapTimingRecord:
    skill: str
    phases: dict[str, float]
    total: float
    source_file: str


@dataclass
class DriftMarkerHit:
    skill_name: str
    source_file: str
    is_template_literal: bool  # True => source-code render, not a real firing


@dataclass
class LogScanResult:
    files_scanned: list[str] = field(default_factory=list)
    timing_records: list[BootstrapTimingRecord] = field(default_factory=list)
    drift_hits: list[DriftMarkerHit] = field(default_factory=list)


def resolve_log_paths(log_glob: str | None = None) -> list[str]:
    """Resolve the glob pattern to scan: explicit arg > env var > built-in
    default. Uses `glob.glob` (stdlib, portable) -- never shells out."""
    pattern = log_glob or os.environ.get(LOG_GLOB_ENV_VAR) or DEFAULT_LOG_GLOB
    return sorted(glob.glob(os.path.expanduser(pattern)))


def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(errors="replace")
    except OSError:
        return ""


def parse_bootstrap_timing_lines(text: str, source_file: str = "") -> list[BootstrapTimingRecord]:
    """Extract every `bootstrap_timing` occurrence in `text`. Tolerant of the
    line appearing inside a larger JSON-transcript blob (session logs here
    are JSONL tool-output captures, not bare text files) -- matches at the
    text level regardless of surrounding JSON quoting, since JSON string
    escaping keeps the literal characters `[`, `]`, `=`, digits, and spaces
    unescaped."""
    records = []
    for m in _BOOTSTRAP_TIMING_RE.finditer(text):
        skill = m.group(1)
        body = m.group(2)
        total = float(m.group(3))
        phases = {name: float(val) for name, val in _PHASE_PAIR_RE.findall(body)
                  if name != "total"}
        records.append(BootstrapTimingRecord(skill=skill, phases=phases,
                                               total=total, source_file=source_file))
    return records


def parse_drift_marker_lines(text: str, source_file: str = "") -> list[DriftMarkerHit]:
    """Extract every occurrence of the drift-abort marker text. Flags
    occurrences that still carry the literal `{name}` placeholder as
    source-code renders rather than real firings (see module docstring on
    `_DRIFT_MARKER_RE`)."""
    hits = []
    for m in _DRIFT_MARKER_RE.finditer(text):
        name = m.group(1)
        hits.append(DriftMarkerHit(
            skill_name=name,
            source_file=source_file,
            is_template_literal=(name == _DRIFT_MARKER_TEMPLATE_LITERAL),
        ))
    return hits


def scan_logs(log_glob: str | None = None) -> LogScanResult:
    result = LogScanResult()
    for path in resolve_log_paths(log_glob):
        result.files_scanned.append(path)
        text = _read_text(path)
        if not text:
            continue
        result.timing_records.extend(parse_bootstrap_timing_lines(text, source_file=path))
        result.drift_hits.extend(parse_drift_marker_lines(text, source_file=path))
    return result


def phase_share_stats(records: list[BootstrapTimingRecord], phase: str = "cross_family",
                       slow_threshold_s: float = 1.0) -> dict:
    """Split records into "slow" (total > slow_threshold_s, the issue's own
    cutoff) and "all", and compute `phase`'s share of total wall time in
    each bucket. Returns a dict with counts, sums, and percentages -- never
    invents a percentage for an empty bucket (reports None instead)."""
    def _bucket_stats(bucket: list[BootstrapTimingRecord]) -> dict:
        if not bucket:
            return {"count": 0, "phase_sum_s": 0.0, "total_sum_s": 0.0, "share_pct": None}
        phase_sum = sum(r.phases.get(phase, 0.0) for r in bucket)
        total_sum = sum(r.total for r in bucket)
        share = (phase_sum / total_sum * 100.0) if total_sum > 0 else None
        return {"count": len(bucket), "phase_sum_s": phase_sum, "total_sum_s": total_sum,
                "share_pct": share}

    slow = [r for r in records if r.total > slow_threshold_s]
    return {
        "phase": phase,
        "slow_threshold_s": slow_threshold_s,
        "slow": _bucket_stats(slow),
        "all": _bucket_stats(records),
    }


def trigger_rate_stats(scan: LogScanResult) -> dict:
    """(marker text matches with a real name interpolated) / (spawns the
    logs cover, proxied by the count of bootstrap_timing lines found).
    Filters out source-code renders (literal `{name}` placeholder, never
    interpolated) but CANNOT further distinguish an organic dispatch-time
    abort from a deliberate manual reproduction of the guard, or from
    another session's transcript quoting a prior reproduction -- see the
    module docstring on `_DRIFT_MARKER_RE`. Callers that need that
    attribution must read the surrounding transcript by hand; this function
    reports a raw upper-bound count, not a verified production-firing rate."""
    named_hits = [h for h in scan.drift_hits if not h.is_template_literal]
    template_hits = [h for h in scan.drift_hits if h.is_template_literal]
    denominator = len(scan.timing_records)
    rate = (len(named_hits) / denominator) if denominator > 0 else None
    return {
        "named_match_count": len(named_hits),
        "template_literal_count": len(template_hits),
        "raw_marker_match_count": len(scan.drift_hits),
        "denominator_spawns": denominator,
        "rate": rate,
    }


def format_report(scan: LogScanResult) -> str:
    lines = []
    lines.append("issue-3186 cross_family diagnosis -- measured report")
    lines.append(f"log files scanned: {len(scan.files_scanned)}")
    lines.append(f"bootstrap_timing lines found: {len(scan.timing_records)}")
    lines.append("")

    share = phase_share_stats(scan.timing_records, phase="cross_family", slow_threshold_s=1.0)
    lines.append("-- cross_family phase share of bootstrap total --")
    for bucket_name in ("slow", "all"):
        b = share[bucket_name]
        label = "spawns with total > 1s" if bucket_name == "slow" else "all spawns"
        if b["count"] == 0:
            lines.append(f"  {label}: no records")
            continue
        pct = f"{b['share_pct']:.1f}%" if b["share_pct"] is not None else "n/a"
        lines.append(
            f"  {label}: n={b['count']} cross_family={b['phase_sum_s']:.3f}s "
            f"total={b['total_sum_s']:.3f}s share={pct}"
        )
    lines.append("")

    trig = trigger_rate_stats(scan)
    lines.append("-- drift-guard marker matches (raw, see caveat) --")
    lines.append(
        f"  named marker matches: {trig['named_match_count']} "
        f"(template-literal/source-render matches excluded: {trig['template_literal_count']}, "
        f"raw regex matches before filtering: {trig['raw_marker_match_count']})"
    )
    lines.append(f"  denominator (bootstrap_timing-covered spawns): {trig['denominator_spawns']}")
    if trig["rate"] is not None:
        lines.append(
            f"  raw rate: {trig['named_match_count']}/{trig['denominator_spawns']} "
            f"= {trig['rate'] * 100:.2f}%"
        )
    else:
        lines.append("  raw rate: n/a (denominator is 0)")
    lines.append(
        "  CAVEAT: this count cannot distinguish an organic dispatch-time "
        "abort from a deliberate manual reproduction of the guard (e.g. "
        "while testing it) or a transcript quoting one of those -- manual "
        "attribution of each match is required before treating this as a "
        "production trigger rate. A 0 (or near-0 organic) rate does not "
        "prove the guard is unnecessary -- small sample, no adversarial/"
        "multi-tier-drift scenario exercised in this log window."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true",
                         help="print a human-readable report")
    parser.add_argument("--log-glob", default=None,
                         help=f"glob pattern for session logs (default: env "
                              f"{LOG_GLOB_ENV_VAR} or {DEFAULT_LOG_GLOB!r})")
    args = parser.parse_args(argv)

    scan = scan_logs(args.log_glob)

    if not scan.timing_records:
        # Empty-state discipline: never report a 0% share or a 0/0 rate as
        # if it were real data. Loud failure, nonzero exit.
        print(
            "ERROR: no bootstrap_timing line found in any scanned session "
            f"log ({len(scan.files_scanned)} files matched "
            f"{args.log_glob or os.environ.get(LOG_GLOB_ENV_VAR) or DEFAULT_LOG_GLOB!r}). "
            "This means NO DATA, not a 0% cross_family share or a 0% trigger "
            "rate -- do not treat this exit as a measurement.",
            file=sys.stderr,
        )
        return 1

    if args.report:
        print(format_report(scan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
