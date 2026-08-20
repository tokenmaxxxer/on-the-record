#!/usr/bin/env python3
"""Conditional auto-approval classifier — issue #1739 (shadow-mode first).

Approved phase-1 proposal: docs/issue-1739/proposals/auto-approval-shadow-mode.md
(APPROVE issue-1739/implementation), frozen by the follow-up issue comment:
config lives at docs/specs/auto-approval-config.json; runtime quota/circuit-
breaker state lives at .on-the-record/auto-approval-state.json (repo-root
runtime state, kept out of docs/specs/); delivery is shadow-only — this
module never touches on-the-record/hooks/approval-gate.sh and never bypasses
the human APPROVE requirement.

Two entry points:
- classify(diff_paths, out_of_scope_paths=()) -> (class_, reason): a pure,
  fail-closed classification of a diff into {"docs_only", "test_only",
  "not_eligible"}. Any diff touching a behavior-contract path
  (on-the-record/hooks/, gates/, docs/specs/, or any path this module
  itself treats as approval/gate semantics) is always not_eligible,
  independent of the rest of the diff. Mixed diffs (docs + code) and
  partially out-of-scope diffs are always not_eligible.
- shadow_verdict(...) -> ShadowVerdict: composes classify()'s result with
  the three existing deterministic gates' PASS/BLOCKED-shaped results plus
  quota/circuit-breaker state, and appends one audit-log line. It never
  approves or denies anything on its own — approval-gate.sh's human-APPROVE
  requirement is unaffected by any value this function returns.

  python3 gates/auto_approval_class.py classify <path...>
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

DOCS_ONLY = "docs_only"
TEST_ONLY = "test_only"
NOT_ELIGIBLE = "not_eligible"

# Behavior-contract paths: any diff touching one of these is always
# not_eligible, regardless of the rest of the diff (circular-trust ban —
# auto-approval logic can never approve a change to itself or its peers).
_CONTRACT_PREFIXES = (
    "on-the-record/hooks/",
    "gates/",
    "docs/specs/",
)

DEFAULT_CONFIG_PATH = Path("docs/specs/auto-approval-config.json")
DEFAULT_STATE_PATH = Path(".on-the-record/auto-approval-state.json")
DEFAULT_AUDIT_LOG_PATH = Path("docs/reports/auto-approval-audit-log.md")

_DEFAULT_QUOTA_PER_24H = 5
_CIRCUIT_BREAKER_WINDOW_DAYS = 28


def _is_contract_path(path: str) -> bool:
    return any(path.startswith(p) for p in _CONTRACT_PREFIXES)


def _is_docs_path(path: str) -> bool:
    return path.startswith("docs/") and not path.startswith("docs/specs/")


def _is_test_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or "/test/" in path
        or "/tests/" in path
    )


def classify(
    diff_paths,
    out_of_scope_paths=(),
    production_fixture_paths=(),
) -> tuple[str, str]:
    """Classify a diff's paths into (class_, reason). Fail-closed: any
    ambiguity, any behavior-contract touch, any mix of classes, or any
    partially-out-of-scope path returns not_eligible.

    `out_of_scope_paths` names paths the caller has determined fall
    outside the PR's declared scope (e.g. via gates/scope_adherence.py) —
    any non-empty intersection with diff_paths is not_eligible.

    `production_fixture_paths` names paths that look test-shaped by name
    (e.g. under test/) but actually edit a production fixture the tests
    depend on — the issue's adversarial case ("test file editing
    production fixture"). Any such path forces not_eligible even though
    the path itself matches the test-file naming convention.
    """
    paths = frozenset(diff_paths)
    if not paths:
        return NOT_ELIGIBLE, "empty diff"

    out_of_scope_hit = paths & frozenset(out_of_scope_paths)
    if out_of_scope_hit:
        return NOT_ELIGIBLE, f"out-of-scope paths: {', '.join(sorted(out_of_scope_hit))}"

    fixture_hit = paths & frozenset(production_fixture_paths)
    if fixture_hit:
        return NOT_ELIGIBLE, f"test-shaped path edits a production fixture: {', '.join(sorted(fixture_hit))}"

    contract_hit = sorted(p for p in paths if _is_contract_path(p))
    if contract_hit:
        return NOT_ELIGIBLE, f"behavior-contract path(s): {', '.join(contract_hit)}"

    is_docs = {p: _is_docs_path(p) for p in paths}
    is_test = {p: _is_test_path(p) for p in paths}

    if all(is_docs.values()):
        return DOCS_ONLY, "all paths under docs/ (excluding docs/specs/)"

    if all(is_test.values()):
        return TEST_ONLY, "all paths are test files"

    # Mixed diff: some paths are docs, some are test, some are neither, or
    # any combination thereof. Fail-closed regardless of the specific mix.
    unclassified = sorted(p for p in paths if not is_docs[p] and not is_test[p])
    if unclassified:
        return NOT_ELIGIBLE, f"non-docs, non-test paths present: {', '.join(unclassified)}"
    return NOT_ELIGIBLE, "mixed docs+test diff"


@dataclass(frozen=True)
class ShadowVerdict:
    would_auto_approve: bool
    reason: str
    class_: str
    quota_remaining: int
    circuit_breaker_suspended: bool


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError):
        return {}


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Absent config file == feature off. Callers that only need
    shadow_mode/quota_per_24h defaults get them via this function."""
    cfg = _load_json(config_path)
    return {
        "quota_per_24h": cfg.get("quota_per_24h", _DEFAULT_QUOTA_PER_24H),
        "shadow_mode": cfg.get("shadow_mode", True),
        "present": config_path.exists(),
    }


def load_state(state_path: Path = DEFAULT_STATE_PATH) -> dict:
    """Absent state file reads as zero-consumed, not unlimited: no
    suspended classes, and an empty approvals list (so quota checks that
    count recent approvals see zero, never treat 'no file' as 'no
    limit')."""
    state = _load_json(state_path)
    return {
        "approvals_last_24h": state.get("approvals_last_24h", []),
        "suspended_classes": state.get("suspended_classes", []),
        "reverts_last_28d": state.get("reverts_last_28d", []),
    }


def _quota_check(class_: str, config: dict, state: dict) -> tuple[bool, int, str | None]:
    quota = config["quota_per_24h"]
    consumed = len(state["approvals_last_24h"])
    remaining = max(0, quota - consumed)
    if consumed >= quota:
        return False, remaining, f"quota exhausted: {consumed}/{quota} used in trailing 24h"
    return True, remaining, None


def _circuit_breaker_check(class_: str, state: dict) -> tuple[bool, str | None]:
    if class_ in state["suspended_classes"]:
        return False, f"class '{class_}' suspended by circuit breaker (recorded revert within {_CIRCUIT_BREAKER_WINDOW_DAYS}d)"
    if state["reverts_last_28d"]:
        return False, (
            f"class '{class_}' suspended: revert(s) recorded within "
            f"{_CIRCUIT_BREAKER_WINDOW_DAYS}d ({', '.join(sorted(state['reverts_last_28d']))})"
        )
    return True, None


def _append_audit_log(line: str, audit_log_path: Path = DEFAULT_AUDIT_LOG_PATH) -> None:
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    if not audit_log_path.exists():
        audit_log_path.write_text(
            "# auto-approval shadow-mode audit log\n\n"
            "Append-only. One line per shadow_verdict() call:\n"
            "`<timestamp-iso> | issue=<n> | pr=<n> | class=<class> | "
            "would_auto_approve=<bool> | reason=<reason>`\n\n"
        )
    with audit_log_path.open("a") as f:
        f.write(line.rstrip("\n") + "\n")


def shadow_verdict(
    diff_paths,
    gate_results: dict,
    issue: int,
    pr: int,
    timestamp: str,
    out_of_scope_paths=(),
    production_fixture_paths=(),
    config_path: Path = DEFAULT_CONFIG_PATH,
    state_path: Path = DEFAULT_STATE_PATH,
    audit_log_path: Path = DEFAULT_AUDIT_LOG_PATH,
) -> ShadowVerdict:
    """Compose classify() with the three existing deterministic gates'
    results (gate_results: {"scope_adherence": bool, "stale_revert_guard":
    bool, "requirement_met": bool} — True means that gate's own PASS/
    ALLOW/YES outcome) plus quota/circuit-breaker state, and append one
    audit-log line in this same call.

    This is shadow-only: the returned would_auto_approve is a recorded
    label, never an action. approval-gate.sh is not called or modified by
    this function; its human-APPROVE requirement is unaffected by
    whatever this function returns.
    """
    class_, class_reason = classify(
        diff_paths, out_of_scope_paths, production_fixture_paths)

    config = load_config(config_path)
    state = load_state(state_path)

    reasons = []
    eligible = True

    if class_ == NOT_ELIGIBLE:
        eligible = False
        reasons.append(class_reason)

    for gate_name in ("scope_adherence", "stale_revert_guard", "requirement_met"):
        if not gate_results.get(gate_name, False):
            eligible = False
            reasons.append(f"{gate_name} did not pass")

    quota_ok, quota_remaining, quota_reason = _quota_check(class_, config, state)
    if not quota_ok:
        eligible = False
        reasons.append(quota_reason)

    breaker_ok, breaker_reason = _circuit_breaker_check(class_, state)
    if not breaker_ok:
        eligible = False
        reasons.append(breaker_reason)

    would_auto_approve = eligible
    reason = "; ".join(reasons) if reasons else "all checks passed"

    verdict = ShadowVerdict(
        would_auto_approve=would_auto_approve,
        reason=reason,
        class_=class_,
        quota_remaining=quota_remaining,
        circuit_breaker_suspended=not breaker_ok,
    )

    _append_audit_log(
        f"{timestamp} | issue={issue} | pr={pr} | class={class_} | "
        f"would_auto_approve={would_auto_approve} | reason={reason}",
        audit_log_path,
    )

    return verdict


def _main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] != "classify":
        print(__doc__)
        return 2
    class_, reason = classify(argv[1:])
    print(json.dumps({"class": class_, "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
