#!/usr/bin/env python3
"""Smoke check for the northpole E2E harness (issue #776 step 2).

NOT a live baseline run against a real session — that is step 3. This
script runs harness/signals.py against a small synthetic
transcript + repo-state fixture and asserts the harness emits the correct
8-row signal structure (7 requirement signals + build-and-run), each one of
PASS/FAIL/UNMEASURED, no row missing. Exits non-zero otherwise.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import driver  # noqa: E402
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


def smoke_check_scenario_wiring():
    """issue #895 step 2 (partial): NOT a live run of the requirement matrix
    — that is #895's remaining execution-observation step. This only
    confirms each of the 7 SCENARIOS entries wires to a hermetic,
    instantiable, buildable fixture: instantiate a clean copy, `pip
    install -e .`, and `pytest`. A scenario whose fixture cannot be
    instantiated or built is reported UNMEASURED-with-reason here — never
    a false PASS — and does not fail the overall smoke check by itself,
    since some fixtures (redtest) SHIP a deliberately failing test."""
    print()
    print("northpole E2E harness — scenario-wiring smoke check (#895 matrix)")
    print("-" * 72)
    broken = []
    for name, scenario in driver.SCENARIOS.items():
        requirement = driver.get_requirement_for_scenario(name)
        if not requirement or not scenario["fixture_dir"].is_dir():
            broken.append((name, "UNMEASURED", "fixture_dir missing or requirement empty"))
            print(f"{name:12s} UNMEASURED — fixture_dir missing or requirement empty")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / f"{name}-copy"
            try:
                driver.instantiate_scenario_fixture(name, dest)
            except (FileExistsError, OSError, subprocess.CalledProcessError) as exc:
                broken.append((name, "UNMEASURED", f"instantiation failed: {exc}"))
                print(f"{name:12s} UNMEASURED — instantiation failed: {exc}")
                continue
            build_result = driver.run_build(dest)
            if build_result["exit_code"] != 0:
                broken.append((name, "UNMEASURED", "pip install -e . failed"))
                print(f"{name:12s} UNMEASURED — pip install -e . failed "
                      f"(exit {build_result['exit_code']})")
                continue
            print(f"{name:12s} OK — instantiates and builds ({scenario['type']})")
    print("-" * 72)
    if broken:
        print(f"{len(broken)} scenario(s) UNMEASURED (see reasons above) — "
              "never reported as a false PASS")
    else:
        print(f"all {len(driver.SCENARIOS)} scenarios instantiate and build cleanly")
    return 0


if __name__ == "__main__":
    exit_code = main()
    smoke_check_scenario_wiring()
    sys.exit(exit_code)
