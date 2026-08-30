#!/usr/bin/env python3
"""Rework-episode measurement over a session's raw stream-json log
(issue #2326 Ask #1: "Measure first: fraction of our tasks whose test
stage fails and forces re-entry into code (rework-turn count from
transcripts)").

Reuses `trajectory_analyzer.parse_session_log`/`tool_use_events`/
`tool_result_index` exactly as `scripts/session_waste_metrics.py` does —
this module only adds a test-stage classifier, a pass/fail heuristic for
that classifier's calls, and the fail -> edit -> next-pass "rework
episode" walk.

FAIL-DETECTION HEURISTIC (read before trusting any number this prints).
Real session logs in this corpus carry `tool_result.is_error == False`
for almost every `pytest` invocation, even ones whose own summary line
reads "16 failed, 579 passed" — the harness only flags `is_error` on a
hook refusal or a hard tool-level failure, not on a nonzero exit code
buried behind a shell pipe (`... | tail -30`, `... | grep FAILED`). So
`is_error` is used as a first, authoritative signal when present, but
the primary signal is **text pattern matching against the captured
`tool_result` content**, in this order:
  1. `tool_result.is_error` True -> fail (explicit signal, trust it).
  2. A pytest-style summary count (`"N failed"`, `"N error(s)"`,
     `"N passed"`, scanned via one regex over the whole result text) --
     the most reliable evidera this corpus offers, since most test-stage
     calls here are pytest. Any nonzero failed/error count -> fail; else
     a nonzero passed count, or literal "no tests ran" -> pass.
  3. Failing outside pytest's summary shape falls back to generic
     failure markers (`FAILED `, `AssertionError`, a raw traceback,
     `error:`, ruff/eslint "N problems (N errors)", shellcheck `SCxxxx`
     codes, `would reformat` for `black --check`, `--- FAIL`/`FAIL\t`
     for `go test`, a `FAIL` line for jest).
  4. Absent any failure marker, generic success markers (`All checks
     passed!`, `Success: no issues found`, `ok <pkg>` for `go test`,
     `PASS`, or simply empty/whitespace-only output — most linters are
     silent on success) count as pass.
  5. If none of the above match, the call is left **"unknown"** rather
     than guessed into pass or fail — this happens for e.g. a pytest
     call truncated by `| head -3` before its summary line ever prints.
     Unknown calls are counted and reported separately; they are
     excluded from the fail-fraction denominator's numerator but
     included in the "total test-stage calls" denominator, so a high
     unknown count is a visible flag that the measurement is degraded
     for that session, not a silently-dropped case.

This is text-pattern matching over unstructured shell output, not a real
exit-code capture — it is APPROXIMATE by construction (a false "pass" is
possible if a session's own text happens to contain a pass marker after
a truncating pipe; a false "fail" is possible if failure-looking text
appears in, say, a diff being displayed rather than a live tool run).
Treat every fraction this script prints as a directional estimate for
prioritization, not an audited count.

TEST-STAGE CLASSIFICATION. Only `Bash` tool_use calls are considered. A
raw command is split on shell chain operators (`&&`, `||`, `;`, `|`,
newline) into segments -- a naive split that does not understand quoting,
so a quoted `|` inside a string (e.g. a grep alternation pattern) can
mis-split; this is a known, accepted approximation, not a correctness
bug to chase. Each segment has leading `VAR=value` assignments and
`timeout <n>`/`env ...` wrapper prefixes stripped, then is matched
against the runner allowlist named in issue #2326's Ask #1: pytest,
`unittest`, `go test`, `npm test`/`jest`, `ruff`, `flake8`, `mypy`,
`black --check`, `eslint`, `shellcheck`, and this repo's own gate runner
(`gates.py` / `gates/*.py`, per `gates/` in this repo -- e.g.
`gates/gates.py`, `gates/acceptance_gate.py`). Matching only the first
real token per segment (not a raw substring search anywhere in the
command) is deliberate: it is what keeps a command like
`grep -rn "pytest\\|rework" docs/` from being misclassified as a test
run just because the word "pytest" appears inside a quoted search
pattern.

Out of scope by the issue's own runner list (documented here so a
reader does not mistake silence for zero): this repo's `core/` sibling
project runs its own gate suites via `bash core/hooks/tests/run-*.sh`,
which is not one of the enumerated runners above and is NOT counted as
a test-stage call here -- sessions whose only "test stage" is that
script under-count relative to sessions using bare pytest.

REWORK EPISODE. For each FAILING test-stage call, scan forward through
the same session's tool_use events for an `Edit`/`Write`/`MultiEdit`
call before either (a) the next test-stage call that resolves to "pass",
or (b) the session ends. If an edit call falls in that window, count one
"rework episode" with turn-cost = the number of tool_use events strictly
between the failing call and the resolving pass call (or session end).
If no edit call falls in the window, it is a "failure without re-entry"
-- split further into whether the window still closed on a later passing
test-stage call (plausibly "fixed without editing", e.g. a flaky test
or an environment fix) versus the session simply ending (plausibly
abandoned) -- both are real and distinct outcomes and neither is
assumed by default. Failing test-stage calls are each walked
independently, so a fail -> edit -> fail -> edit -> pass chain reports
two rework episodes, not one -- "how many times did the agent go back
into code after a red run" is the quantity being measured, and it
happened twice.

  python3 scripts/rework_fraction.py <session_log>
  python3 scripts/rework_fraction.py --batch '<glob>'
"""
from __future__ import annotations
import argparse
import glob
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import trajectory_analyzer as ta  # noqa: E402

_EDIT_TOOLS = ("Edit", "Write", "MultiEdit")

# ---------------------------------------------------------------------------
# Test-stage classification
# ---------------------------------------------------------------------------

_SEGMENT_SPLIT_RE = re.compile(r"&&|\|\||;|\||\n")

# Strips repeated `VAR=value` assignments and `timeout <n>` / `env ...`
# wrapper prefixes off the front of a segment so the runner check below
# only ever has to anchor on the runner's own token.
_WRAPPER_RE = re.compile(
    r"^\s*(?:"
    r"[A-Za-z_][A-Za-z0-9_]*=\S*\s+"
    r"|timeout\s+(?:-s\s+\S+\s+)?\S+\s+"
    r"|env\s+(?:-u\s+\S+\s+|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"
    r")+"
)

_TEST_RUNNER_PATTERNS = [
    ("pytest", re.compile(r"^(?:python3?\s+-m\s+)?pytest\b")),
    ("unittest", re.compile(r"^(?:python3?\s+-m\s+)?unittest\b")),
    ("go_test", re.compile(r"^go\s+test\b")),
    ("npm_test", re.compile(r"^npm\s+(?:run\s+)?test\b")),
    ("jest", re.compile(r"^(?:npx\s+)?jest\b")),
    ("ruff", re.compile(r"^ruff\b")),
    ("flake8", re.compile(r"^flake8\b")),
    ("mypy", re.compile(r"^(?:python3?\s+-m\s+)?mypy\b")),
    ("black_check", re.compile(r"^black\b.*--check\b")),
    ("eslint", re.compile(r"^(?:npx\s+)?eslint\b")),
    ("shellcheck", re.compile(r"^shellcheck\b")),
    ("gates", re.compile(r"^(?:python3?\s+)?gates(?:/[\w.-]+)?\.py\b")),
]


def classify_test_stage(command: str) -> str | None:
    """`command` -> the matched runner label, or `None` if no segment of
    it is a test/lint-runner invocation."""
    for raw_segment in _SEGMENT_SPLIT_RE.split(command or ""):
        segment = _WRAPPER_RE.sub("", raw_segment.lstrip())
        for label, pattern in _TEST_RUNNER_PATTERNS:
            if pattern.match(segment):
                return label
    return None


# ---------------------------------------------------------------------------
# Pass/fail heuristic (see module docstring for the full rationale)
# ---------------------------------------------------------------------------

_SUMMARY_COUNT_RE = re.compile(
    r"(\d+)\s+(failed|passed|error(?:s)?|xfailed|xpassed|skipped)\b")
_NO_TESTS_RAN_RE = re.compile(r"no tests ran", re.IGNORECASE)

_FAIL_MARKERS = [
    re.compile(r"^FAILED\s", re.MULTILINE),
    re.compile(r"AssertionError"),
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"(?im)^\s*error:"),
    re.compile(r"would reformat"),
    re.compile(r"^--- FAIL", re.MULTILINE),
    re.compile(r"^FAIL\t", re.MULTILINE),
    re.compile(r"^FAIL\b", re.MULTILINE),
    re.compile(r"\d+\s+problems?\s+\(\d+\s+errors?", re.IGNORECASE),
    re.compile(r"\bSC\d{4}\b"),
    re.compile(r"[✕✗]"),  # jest/eslint fail glyphs (x, heavy x)
]

_PASS_MARKERS = [
    re.compile(r"All checks passed!"),
    re.compile(r"Success: no issues found"),
    re.compile(r"^ok\s+\S+", re.MULTILINE),
    re.compile(r"\bPASS\b"),
    re.compile(r"All done!"),
]


def classify_test_result(is_error: bool, text: str) -> str:
    """`(is_error, tool_result text)` -> `"pass"`|`"fail"`|`"unknown"`.
    See the module docstring's FAIL-DETECTION HEURISTIC section for the
    full precedence order and its caveats."""
    if is_error:
        return "fail"
    text = text or ""
    counts = {}
    for num, label in _SUMMARY_COUNT_RE.findall(text):
        counts[label] = counts.get(label, 0) + int(num)
    failed_n = counts.get("failed", 0) + counts.get("error", 0) + counts.get("errors", 0)
    passed_n = counts.get("passed", 0)
    if failed_n > 0:
        return "fail"
    if passed_n > 0:
        return "pass"
    if _NO_TESTS_RAN_RE.search(text):
        return "pass"
    if any(p.search(text) for p in _FAIL_MARKERS):
        return "fail"
    if not text.strip():
        return "pass"
    if any(p.search(text) for p in _PASS_MARKERS):
        return "pass"
    return "unknown"


# ---------------------------------------------------------------------------
# Per-session analysis
# ---------------------------------------------------------------------------

def analyze_session(events: list[dict]) -> dict:
    uses = ta.tool_use_events(events)
    results = ta.tool_result_index(events)

    edit_indices = {i for i, u in enumerate(uses) if u["name"] in _EDIT_TOOLS}

    # Per tool_use-list-index (not raw event index) classification of
    # every Bash test-stage call: (runner_label, outcome).
    test_stage = {}
    for i, u in enumerate(uses):
        if u["name"] != "Bash":
            continue
        runner = classify_test_stage(u["input"].get("command", ""))
        if runner is None:
            continue
        r = results.get(u["tool_use_id"])
        if r is None:
            outcome = "unknown"  # in-flight / truncated log, no result yet
        else:
            outcome = classify_test_result(r["is_error"], r["text"])
        test_stage[i] = (runner, outcome)

    test_stage_indices = sorted(test_stage)
    passing_indices = [i for i in test_stage_indices if test_stage[i][1] == "pass"]
    failing_indices = [i for i in test_stage_indices if test_stage[i][1] == "fail"]
    unknown_indices = [i for i in test_stage_indices if test_stage[i][1] == "unknown"]

    rework_episodes = []           # turn-cost per RESOLVED episode with re-entry
    unresolved_reentry = 0         # edit seen, but no later pass before session end --
                                    # cost unknown, NOT charged as a turn-cost (see below)
    no_reentry_then_pass = 0       # window closed on a later pass, no edit seen
    no_reentry_session_end = 0     # window ran to session end, no edit seen

    for fail_i in failing_indices:
        # Next test-stage call (any index) that resolves to "pass",
        # strictly after this failing call.
        boundary = len(uses)  # default: session end
        resolved = False
        for j in test_stage_indices:
            if j > fail_i and test_stage[j][1] == "pass":
                boundary = j
                resolved = True
                break
        had_edit = any(fail_i < k < boundary for k in edit_indices)
        if had_edit and resolved:
            turn_cost = boundary - fail_i - 1
            rework_episodes.append(turn_cost)
        elif had_edit:
            # An edit followed the failure, but the session ended before
            # any test-stage call confirmed a pass. `boundary` is still
            # `len(uses)` here only because nothing resolved it -- it is
            # not a measured fix time, it is "however many turns were
            # left in the session." Charging that as a turn-cost silently
            # turns "we don't know if/when this was fixed" into "this
            # took N turns to fix," which inflates outliers (this is the
            # source of `rework_fraction` reports quoting costs as high
            # as the length of the remaining session). Count it
            # separately instead of folding it into `rework_episodes`.
            unresolved_reentry += 1
        elif resolved:
            no_reentry_then_pass += 1
        else:
            no_reentry_session_end += 1

    n_test_stage = len(test_stage_indices)
    n_fail = len(failing_indices)
    return {
        "total_tool_use_turns": len(uses),
        "total_edit_calls": len(edit_indices),
        "total_test_stage_calls": n_test_stage,
        "test_stage_pass": len(passing_indices),
        "test_stage_fail": n_fail,
        "test_stage_unknown": len(unknown_indices),
        "fail_fraction": (n_fail / n_test_stage) if n_test_stage else None,
        "rework_episodes_count": len(rework_episodes),
        "unresolved_reentry_count": unresolved_reentry,
        "failures_no_reentry_then_pass": no_reentry_then_pass,
        "failures_no_reentry_session_end": no_reentry_session_end,
        "rework_turn_costs": rework_episodes,
        "rework_turn_cost_median": (statistics.median(rework_episodes)
                                     if rework_episodes else None),
        "rework_turn_cost_mean": (statistics.fmean(rework_episodes)
                                   if rework_episodes else None),
    }


def analyze(path) -> dict:
    events = ta.parse_session_log(path)
    report = analyze_session(events)
    report["session_log"] = str(path)
    return report


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _fmt_report(report: dict) -> str:
    ff = report["fail_fraction"]
    ff_s = "N/A, no test-stage calls" if ff is None else f"{ff:.1%}"
    lines = [
        f"session: {report['session_log']}",
        f"  tool_use turns: {report['total_tool_use_turns']}",
        f"  edit calls (Edit/Write/MultiEdit): {report['total_edit_calls']}",
        f"  test-stage calls: {report['total_test_stage_calls']} "
        f"(pass={report['test_stage_pass']}, fail={report['test_stage_fail']}, "
        f"unknown={report['test_stage_unknown']})",
        f"  test-stage fail fraction: {ff_s}",
        f"  rework episodes (fail -> edit -> next pass, cost known): "
        f"{report['rework_episodes_count']}",
        f"  unresolved re-entry (fail -> edit -> session ended, no confirming "
        f"pass -- cost unknown, NOT charged as a turn-cost): "
        f"{report['unresolved_reentry_count']}",
        f"  failures without re-entry: "
        f"{report['failures_no_reentry_then_pass']} fixed-without-edit-looking, "
        f"{report['failures_no_reentry_session_end']} ran to session end",
    ]
    costs = report["rework_turn_costs"]
    if costs:
        lines.append(f"  rework turn-costs: {costs}")
        lines.append(f"  rework turn-cost median={report['rework_turn_cost_median']:.1f} "
                      f"mean={report['rework_turn_cost_mean']:.2f}")
    else:
        lines.append("  rework turn-costs: none")
    return "\n".join(lines)


def batch_summary(paths: list[str]) -> dict:
    reports = []
    errors = []
    for p in paths:
        try:
            reports.append(analyze(p))
        except Exception as exc:  # noqa: BLE001 - batch sweep must not die on one bad log
            errors.append({"session_log": str(p), "error": f"{type(exc).__name__}: {exc}"})

    zero_test_stage = [r["session_log"] for r in reports if r["total_test_stage_calls"] == 0]
    with_test_stage = [r for r in reports if r["total_test_stage_calls"] > 0]

    total_test_stage = sum(r["total_test_stage_calls"] for r in reports)
    total_fail = sum(r["test_stage_fail"] for r in reports)
    total_edit_calls = sum(r["total_edit_calls"] for r in reports)
    total_rework = sum(r["rework_episodes_count"] for r in reports)
    total_unresolved_reentry = sum(r["unresolved_reentry_count"] for r in reports)
    total_no_reentry_pass = sum(r["failures_no_reentry_then_pass"] for r in reports)
    total_no_reentry_end = sum(r["failures_no_reentry_session_end"] for r in reports)
    all_costs = [c for r in reports for c in r["rework_turn_costs"]]

    return {
        "sessions": len(reports),
        "sessions_with_parse_errors": errors,
        "sessions_zero_test_stage_calls": zero_test_stage,
        "sessions_zero_test_stage_calls_note":
            "N/A, no test-stage calls -- excluded from rework-fraction "
            "denominators below, not silently dropped",
        "sessions_with_test_stage_calls": len(with_test_stage),
        "total_test_stage_calls": total_test_stage,
        "total_test_stage_fail": total_fail,
        "rework_fraction_of_test_stage_calls":
            (total_rework / total_test_stage) if total_test_stage else None,
        "fail_fraction_of_test_stage_calls":
            (total_fail / total_test_stage) if total_test_stage else None,
        "total_edit_calls": total_edit_calls,
        "rework_fraction_of_edit_turns":
            (total_rework / total_edit_calls) if total_edit_calls else None,
        "total_rework_episodes": total_rework,
        "total_unresolved_reentry": total_unresolved_reentry,
        "total_unresolved_reentry_note":
            "edit followed a failure but no test-stage call ever confirmed a "
            "pass before session end -- cost unknown, excluded from "
            "rework_turn_cost median/mean below, not charged as a "
            "full-remaining-session turn-cost",
        "total_failures_no_reentry_then_pass": total_no_reentry_pass,
        "total_failures_no_reentry_session_end": total_no_reentry_end,
        "rework_turn_cost_median": statistics.median(all_costs) if all_costs else None,
        "rework_turn_cost_mean": statistics.fmean(all_costs) if all_costs else None,
        "per_session": reports,
    }


def _fmt_batch(summary: dict) -> str:
    rf = summary["rework_fraction_of_test_stage_calls"]
    rf_s = "N/A, no test-stage calls in corpus" if rf is None else f"{rf:.1%}"
    ff = summary["fail_fraction_of_test_stage_calls"]
    ff_s = "N/A, no test-stage calls in corpus" if ff is None else f"{ff:.1%}"
    re_edit = summary["rework_fraction_of_edit_turns"]
    re_edit_s = "N/A, no edit calls in corpus" if re_edit is None else f"{re_edit:.1%}"
    lines = [
        f"=== corpus rollup: {summary['sessions']} session(s) ===",
        f"sessions with parse errors: {len(summary['sessions_with_parse_errors'])}",
    ]
    for e in summary["sessions_with_parse_errors"]:
        lines.append(f"  ERROR {e['session_log']}: {e['error']}")
    lines.append(
        f"sessions with zero test-stage calls "
        f"({summary['sessions_zero_test_stage_calls_note']}): "
        f"{len(summary['sessions_zero_test_stage_calls'])}")
    for s in summary["sessions_zero_test_stage_calls"]:
        lines.append(f"  {s}")
    lines += [
        f"sessions with >=1 test-stage call: {summary['sessions_with_test_stage_calls']}",
        f"total test-stage calls: {summary['total_test_stage_calls']} "
        f"(fail={summary['total_test_stage_fail']}, "
        f"fail_fraction={ff_s})",
        f"total edit calls (Edit/Write/MultiEdit): {summary['total_edit_calls']}",
        f"total rework episodes (cost known): {summary['total_rework_episodes']}",
        f"  rework_fraction_of_test_stage_calls (rework / test-stage calls): {rf_s}",
        f"  rework_fraction_of_edit_turns (rework / edit calls): {re_edit_s}",
        f"total unresolved re-entry ({summary['total_unresolved_reentry_note']}): "
        f"{summary['total_unresolved_reentry']}",
        f"total failures without re-entry: "
        f"{summary['total_failures_no_reentry_then_pass']} fixed-without-edit-looking, "
        f"{summary['total_failures_no_reentry_session_end']} ran to session end",
    ]
    if summary["rework_turn_cost_median"] is not None:
        lines.append(
            f"rework turn-cost across corpus: median={summary['rework_turn_cost_median']:.1f} "
            f"mean={summary['rework_turn_cost_mean']:.2f} "
            f"(n={len(summary['per_session']) and sum(len(r['rework_turn_costs']) for r in summary['per_session'])})")
    else:
        lines.append("rework turn-cost across corpus: no rework episodes found")
    lines.append("")
    lines.append("--- per-session ---")
    for r in summary["per_session"]:
        lines.append(_fmt_report(r))
        lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session_log", nargs="?", help="path to a single session log")
    ap.add_argument("--batch", help="glob of session logs to summarize together")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of the text report")
    args = ap.parse_args(argv)

    if args.batch:
        paths = sorted(glob.glob(args.batch))
        if not paths:
            print(f"error: no files match {args.batch!r}", file=sys.stderr)
            return 1
        summary = batch_summary(paths)
        print(json.dumps(summary, indent=2, ensure_ascii=False) if args.json
              else _fmt_batch(summary))
        return 0

    if not args.session_log:
        print("error: give a session_log path or --batch <glob>", file=sys.stderr)
        return 1
    path = Path(args.session_log)
    if not path.is_file():
        print(f"error: session log not found: {path}", file=sys.stderr)
        return 1
    report = analyze(path)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json
          else _fmt_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
