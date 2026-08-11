"""Per-requirement signal checks for the northpole E2E harness (issue #776).

Implements the 7-row signal table (docs/specs/northpole-harness.md §3) plus
the build-and-run assertion (§5) as pure functions over:
  - a transcript: a dict describing what happened during the driven run
  - a repo_state: a dict describing the resulting fixture repo's state

Each function returns one of "PASS", "FAIL", "UNMEASURED" — never silently
omitting a verdict (the empty-state rule).
"""

PASS = "PASS"
FAIL = "FAIL"
UNMEASURED = "UNMEASURED"

SIGNAL_NAMES = [
    "orchestration_to_completion",
    "full_record_ability",
    "real_wired_verification",
    "autonomous_completion_reporting",
    "problems_not_pushed_back",
    "condensed_requirement_management",
    "inviolable_constraint",
]


def check_orchestration_to_completion(transcript):
    """Signal #1: transcript shows >=1 delegation/spawn event and a final report."""
    if transcript is None:
        return UNMEASURED
    events = transcript.get("delegation_events")
    final_report = transcript.get("final_report")
    if events is None or final_report is None:
        return UNMEASURED
    if len(events) >= 1 and final_report:
        return PASS
    return FAIL


def check_full_record_ability(repo_state):
    """Signal #2: a fresh session (repo files only) can name the fix and its rationale."""
    if repo_state is None:
        return UNMEASURED
    record = repo_state.get("record_file")
    if record is None:
        return UNMEASURED
    if record.get("names_fix") and record.get("names_rationale"):
        return PASS
    return FAIL


def check_real_wired_verification(build_result, run_result):
    """Signal #3: the harness itself (not the session) checks out and runs build+run."""
    if build_result is None or run_result is None:
        return UNMEASURED
    if build_result.get("exit_code") == 0 and run_result.get("exit_code") == 0:
        return PASS
    return FAIL


def check_autonomous_completion_reporting(transcript):
    """Signal #4: final report states 4 named parts."""
    if transcript is None:
        return UNMEASURED
    final_report = transcript.get("final_report")
    if final_report is None:
        return UNMEASURED
    required_parts = ("what_broke", "what_changed", "what_became_possible", "what_limits_remain")
    if all(final_report.get(part) for part in required_parts):
        return PASS
    return FAIL


def check_problems_not_pushed_back(transcript, repo_state):
    """Signal #5: zero human-input stalls AND a resolution trail exists in-repo."""
    if transcript is None:
        return UNMEASURED
    reached_midcourse = transcript.get("reached_midcourse_moment")
    if reached_midcourse is None:
        return UNMEASURED
    if not reached_midcourse:
        return UNMEASURED
    stalls = transcript.get("human_input_stalls")
    resolution_trail = (repo_state or {}).get("resolution_trail")
    if stalls is None or resolution_trail is None:
        return UNMEASURED
    if len(stalls) == 0 and resolution_trail:
        return PASS
    return FAIL


def check_condensed_requirement_management(repo_state):
    """Signal #6: exactly one canonical, current record of the original requirement exists."""
    if repo_state is None:
        return UNMEASURED
    records = repo_state.get("requirement_records")
    if records is None:
        return UNMEASURED
    if len(records) == 0:
        return UNMEASURED
    if len(records) == 1 and records[0].get("matches_original"):
        return PASS
    return FAIL


def check_inviolable_constraint(transcript, prior_signals):
    """Signal #7: signals 1-6 pass under the as-installed, no-explicit-invocation precondition."""
    if transcript is None:
        return UNMEASURED
    if transcript.get("skill_explicitly_invoked_by_operator"):
        return FAIL
    if any(v is UNMEASURED for v in prior_signals.values()):
        return UNMEASURED
    if all(v == PASS for v in prior_signals.values()):
        return PASS
    return FAIL


def check_build_and_run(build_result, run_result):
    """Build-and-run assertion (spec §5): pip install -e . && fixture-target --version; pytest."""
    if build_result is None or run_result is None:
        return UNMEASURED
    if build_result.get("exit_code") == 0 and run_result.get("exit_code") == 0:
        return PASS
    return FAIL


def evaluate_all(transcript, repo_state, build_result, run_result):
    """Run all 7 signals + build-and-run, return an 8-entry dict, no row omitted."""
    results = {}
    results["orchestration_to_completion"] = check_orchestration_to_completion(transcript)
    results["full_record_ability"] = check_full_record_ability(repo_state)
    results["real_wired_verification"] = check_real_wired_verification(build_result, run_result)
    results["autonomous_completion_reporting"] = check_autonomous_completion_reporting(transcript)
    results["problems_not_pushed_back"] = check_problems_not_pushed_back(transcript, repo_state)
    results["condensed_requirement_management"] = check_condensed_requirement_management(repo_state)

    prior = {name: results[name] for name in SIGNAL_NAMES if name != "inviolable_constraint"}
    results["inviolable_constraint"] = check_inviolable_constraint(transcript, prior)

    results["build_and_run"] = check_build_and_run(build_result, run_result)
    return results
