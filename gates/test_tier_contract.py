"""issue #1518 — test-tier contract parser for target repos.

A target repo declares `.on-the-record/test-tiers.json` (fast command +
budget_seconds, optional slow command + trigger_change_classes),
mirroring #1490's landed pytest-tier shape (`-m "not slow"` default,
`-m slow` opt-in, <=300s budget) as a file convention instead of a
`roles/*.json` field, since a per-target-repo tier belongs in that
repo's own checkout, not in this plugin's shared role config
(docs/issue-1518/proposals/2026-08-15-test-tier-contract.md).
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

CONTRACT_RELPATH = ".on-the-record/test-tiers.json"
DEFAULT_BUDGET_SECONDS = 300


class Contract:
    def __init__(self, fast_command, budget_seconds, slow_command=None,
                 slow_trigger_change_classes=None):
        self.fast_command = fast_command
        self.budget_seconds = budget_seconds
        self.slow_command = slow_command
        self.slow_trigger_change_classes = list(slow_trigger_change_classes or [])


def parse_contract(raw):
    """Validate an already-parsed JSON object. Any shape violation ->
    None (fail-closed to the no-contract path, never raises)."""
    if not isinstance(raw, dict):
        return None
    fast = raw.get("fast")
    if not isinstance(fast, dict):
        return None
    command = fast.get("command")
    if not isinstance(command, str) or not command.strip():
        return None
    budget = fast.get("budget_seconds", DEFAULT_BUDGET_SECONDS)
    if isinstance(budget, bool) or not isinstance(budget, (int, float)) or budget <= 0:
        return None

    slow_command = None
    slow_trigger = []
    slow = raw.get("slow")
    if slow is not None:
        if not isinstance(slow, dict):
            return None
        slow_command = slow.get("command")
        if not isinstance(slow_command, str) or not slow_command.strip():
            return None
        trigger = slow.get("trigger_change_classes", [])
        if not isinstance(trigger, list) or not all(isinstance(t, str) for t in trigger):
            return None
        slow_trigger = trigger

    return Contract(command, budget, slow_command, slow_trigger)


def load_contract(repo_root):
    """Read CONTRACT_RELPATH under repo_root. Missing file, unreadable
    file, or invalid JSON/schema all resolve to None -- the caller's
    no-contract path, never an exception."""
    path = Path(repo_root) / CONTRACT_RELPATH
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text())
    except (ValueError, OSError):
        return None
    return parse_contract(raw)


def select_tier(contract, changed_paths):
    """'slow' iff a slow tier is declared and some changed path matches
    one of its trigger_change_classes globs; 'fast' otherwise (including
    when contract is None -- no contract means no slow trigger either,
    the no-contract path is handled separately by no_contract_gap)."""
    if contract is None or not contract.slow_command:
        return "fast"
    for changed in changed_paths:
        for pattern in contract.slow_trigger_change_classes:
            if fnmatch.fnmatch(changed, pattern):
                return "slow"
    return "fast"


def no_contract_gap(repo_root, measured_seconds):
    """req 3 -- the no-contract path: never a silent full run. Returns
    the gap record a verification role writes into its own record
    (measured cost + a proposal-worthy gap note), instead of running the
    full suite with nothing surfaced."""
    repo_root_str = str(repo_root)
    return {
        "target_repo": repo_root_str,
        "contract_present": False,
        "measured_full_run_seconds": measured_seconds,
        "gap": (
            f"{repo_root_str} has no {CONTRACT_RELPATH} tier contract; "
            f"full run measured at {measured_seconds}s -- file a tiering "
            "adoption proposal for this repo instead of assuming a full "
            "run stays affordable."
        ),
    }
