"""issue #1518 — test-tier contract parser, rescoped by #2141 to the
PLUGIN'S OWN suite only (per #2137 verify-at-landing).

This repo declares `.on-the-record/test-tiers.json` (fast command +
budget_seconds, optional slow command + trigger_change_classes),
mirroring #1490's landed pytest-tier shape (`-m "not slow"` default,
`-m slow` opt-in, <=300s budget). The target-repo half of the original
contract (`select_tier`/`no_contract_gap`, the "target repos declare a
tier contract by default" framing) is RETIRED — target repos verify via
recorded acceptance commands (#2137), not default test suites. Sole live
consumer: watchdog.py's standing_red_check on the plugin checkout.
"""
from __future__ import annotations

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
