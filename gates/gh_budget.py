#!/usr/bin/env python3
"""issue #1681: client-side quota budget over the shared GraphQL/REST
account rate limit. A heavy drive can push GraphQL to 0 (measured live:
GraphQL 0 while REST sat at 4995/5000) with only passive recovery. This
module gives every recurring caller a per-consumer-class token-bucket
budget over ONE cached rate-limit snapshot, decremented locally — no
`gh api rate_limit` query per call. A metered class (watchdog/sweep)
that exhausts its own budget, or whose next charge would push the
account below the reserved floor, gets an explicit budget-exhausted
result and skips; it never drives the account to 0. Unmetered classes
(one-off/orchestration calls) fail open — the account-level reserve
floor is what keeps quota available for them, not a cap on them."""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

BUDGET_EXHAUSTED = "budget-exhausted"


def _default_fetch_snapshot(root: Path) -> tuple[int | None, bool, int | None]:
    """Single `gh api rate_limit` call returning `(remaining, ok,
    reset)` — the GraphQL resource's `reset` epoch-seconds field sits
    right next to `remaining` in the same payload
    `closure_sweep.rate_limit_remaining` already reads (issue #1681
    review). Reading it directly here, instead of widening
    `rate_limit_remaining`'s own 2-tuple return shape, keeps
    closure_sweep.py's existing caller (closure_sweep.py:643)
    untouched and avoids a second `gh api rate_limit` round trip."""
    import json
    import subprocess
    r = subprocess.run(["gh", "api", "rate_limit"], cwd=root,
                        capture_output=True, text=True)
    if r.returncode != 0:
        return None, False, None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None, False, None
    graphql = data.get("resources", {}).get("graphql", {})
    remaining = graphql.get("remaining")
    if not isinstance(remaining, int):
        return None, False, None
    reset = graphql.get("reset")
    if not isinstance(reset, int):
        reset = None
    return remaining, True, reset


def budget_message(source: str, remaining: int | None, until: int | None = None) -> str:
    """Distinct budget/rate-limit degradation line, matching board-
    sweep's existing convention (`gates/closure_sweep.py:645`) exactly,
    so requirement-drift/closure-sweep/any future watchdog caller emit
    one recognizable string instead of an ordinary-failure line. When
    `until` (the rate-limit reset epoch-seconds) is known, it is
    appended per the issue's own design ('budget-exhausted until <t>')."""
    base = f"[watchdog] {source}: 미집계 (rate-limit, remaining={remaining})"
    if until is None:
        return base
    return f"{base} (budget-exhausted until {until})"


class GhBudget:
    """Per-consumer-class token-bucket budget over a cached account
    snapshot. `classes` maps a metered consumer-class name to its point
    budget for this tracker's lifetime; any class not present in
    `classes` (e.g. "orchestration") is unmetered and always fails
    open. `reserve` is the account-level remaining floor a metered
    charge must never cross. Classification is honor-based: the caller
    names its own `consumer_class` on every `charge()` call, and any
    class not present in `classes` is treated as unmetered and fails
    open — this trusts callers not to mislabel a metered workload as an
    unknown/unmetered one, which is acceptable for this repo's
    cooperative consumers but is not enforced here."""

    def __init__(self, root: Path, classes: dict[str, int], reserve: int = 0,
                 fetch_snapshot: Callable[[Path], tuple[int | None, bool, int | None]] | None = None):
        self.root = root
        self.classes = dict(classes)
        self.reserve = reserve
        self._fetch_snapshot = fetch_snapshot or _default_fetch_snapshot
        self._snapshot: int | None = None
        self._reset: int | None = None
        self._snapshot_fetched = False
        self._snapshot_ok = True
        self._consumed: dict[str, int] = {name: 0 for name in self.classes}
        self.fetch_calls = 0

    def _ensure_snapshot(self) -> None:
        if self._snapshot_fetched:
            return
        self._snapshot_fetched = True
        self.fetch_calls += 1
        remaining, ok, reset = self._fetch_snapshot(self.root)
        self._snapshot_ok = ok
        self._snapshot = remaining if ok else None
        self._reset = reset if ok else None

    def charge(self, consumer_class: str, cost: int = 1) -> dict:
        """Attempt to spend `cost` points as `consumer_class`. Returns
        `{"ok": True, "class": ..., "remaining": <snapshot or None>}` on
        success, or `{"ok": False, "reason": "budget-exhausted",
        "class": ..., "remaining": <snapshot or None>, "until": <reset
        epoch-seconds or None>}` when a metered class's own budget or
        the account reserve floor would be crossed. Unmetered classes
        (not a key of `classes`) always fail open and are not charged
        against the snapshot."""
        if consumer_class not in self.classes:
            return {"ok": True, "class": consumer_class, "remaining": self._snapshot}

        self._ensure_snapshot()

        budget = self.classes[consumer_class]
        consumed = self._consumed[consumer_class]
        if consumed + cost > budget:
            return {"ok": False, "reason": BUDGET_EXHAUSTED,
                     "class": consumer_class, "remaining": self._snapshot,
                     "until": self._reset}

        if self._snapshot_ok and self._snapshot is not None:
            projected = self._snapshot - cost
            if projected < self.reserve:
                return {"ok": False, "reason": BUDGET_EXHAUSTED,
                         "class": consumer_class, "remaining": self._snapshot,
                         "until": self._reset}

        self._consumed[consumer_class] = consumed + cost
        if self._snapshot_ok and self._snapshot is not None:
            self._snapshot -= cost
        return {"ok": True, "class": consumer_class, "remaining": self._snapshot}
