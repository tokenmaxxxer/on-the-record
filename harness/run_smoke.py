#!/usr/bin/env python3
"""Smoke check for the northpole E2E harness (issue #776 step 2).

NOT a live baseline run against a real session — that is step 3. This
script runs harness/signals.py against a small synthetic
transcript + repo-state fixture and asserts the harness emits the correct
8-row signal structure (7 requirement signals + build-and-run), each one of
PASS/FAIL/UNMEASURED, no row missing. Exits non-zero otherwise.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import signals  # noqa: E402

EXPECTED_ROWS = signals.SIGNAL_NAMES + ["build_and_run"]

SYNTHETIC_TRANSCRIPT = {
    "delegation_events": [{"role": "implementation", "action": "spawn"}],
    "final_report": {
        "what_broke": "--version crashed with a stack trace",
        "what_changed": "fixed _resolve_version to read __version__",
        "what_became_possible": "fixture-target --version now prints the version",
        "what_limits_remain": "none noted",
    },
    "reached_midcourse_moment": True,
    "human_input_stalls": [],
    "skill_explicitly_invoked_by_operator": False,
}

SYNTHETIC_REPO_STATE = {
    "record_file": {"names_fix": True, "names_rationale": True},
    "resolution_trail": True,
    "requirement_records": [{"matches_original": True}],
}

SYNTHETIC_BUILD_RESULT = {"exit_code": 0, "stdout": "", "stderr": ""}
SYNTHETIC_RUN_RESULT = {"exit_code": 0, "stdout": "0.1.0\n", "stderr": ""}


def main():
    results = signals.evaluate_all(
        SYNTHETIC_TRANSCRIPT, SYNTHETIC_REPO_STATE, SYNTHETIC_BUILD_RESULT, SYNTHETIC_RUN_RESULT
    )

    print("northpole E2E harness — smoke check (synthetic fixture, not a live run)")
    print("-" * 72)
    missing = []
    invalid = []
    for name in EXPECTED_ROWS:
        if name not in results:
            missing.append(name)
            print(f"{name:38s} MISSING")
            continue
        verdict = results[name]
        if verdict not in (signals.PASS, signals.FAIL, signals.UNMEASURED):
            invalid.append((name, verdict))
        print(f"{name:38s} {verdict}")
    print("-" * 72)

    if missing:
        print(f"FAIL: {len(missing)} row(s) missing: {missing}")
        return 1
    if invalid:
        print(f"FAIL: {len(invalid)} row(s) with invalid verdict: {invalid}")
        return 1
    if len(results) != len(EXPECTED_ROWS):
        print(f"FAIL: expected exactly {len(EXPECTED_ROWS)} rows, got {len(results)}")
        return 1

    print(f"PASS: all {len(EXPECTED_ROWS)} rows present, each PASS/FAIL/UNMEASURED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
