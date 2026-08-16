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
import closure_sweep  # noqa: E402

BUDGET_EXHAUSTED = "budget-exhausted"


def budget_message(source: str, remaining: int | None) -> str:
    """Distinct budget/rate-limit degradation line, matching board-
    sweep's existing convention (`gates/closure_sweep.py:645`) exactly,
    so requirement-drift/closure-sweep/any future watchdog caller emit
    one recognizable string instead of an ordinary-failure line."""
    return f"[watchdog] {source}: 미집계 (rate-limit, remaining={remaining})"


class GhBudget:
    """Per-consumer-class token-bucket budget over a cached account
    snapshot. `classes` maps a metered consumer-class name to its point
    budget for this tracker's lifetime; any class not present in
    `classes` (e.g. "orchestration") is unmetered and always fails
    open. `reserve` is the account-level remaining floor a metered
    charge must never cross."""

    def __init__(self, root: Path, classes: dict[str, int], reserve: int = 0,
                 fetch_snapshot: Callable[[Path], tuple[int | None, bool]] | None = None):
        self.root = root
        self.classes = dict(classes)
        self.reserve = reserve
        self._fetch_snapshot = fetch_snapshot or closure_sweep.rate_limit_remaining
        self._snapshot: int | None = None
        self._snapshot_fetched = False
        self._snapshot_ok = True
        self._consumed: dict[str, int] = {name: 0 for name in self.classes}
        self.fetch_calls = 0

    def _ensure_snapshot(self) -> None:
        if self._snapshot_fetched:
            return
        self._snapshot_fetched = True
        self.fetch_calls += 1
        remaining, ok = self._fetch_snapshot(self.root)
        self._snapshot_ok = ok
        self._snapshot = remaining if ok else None

    def charge(self, consumer_class: str, cost: int = 1) -> dict:
        """Attempt to spend `cost` points as `consumer_class`. Returns
        `{"ok": True, "class": ..., "remaining": <snapshot or None>}` on
        success, or `{"ok": False, "reason": "budget-exhausted",
        "class": ..., "remaining": <snapshot or None>}` when a metered
        class's own budget or the account reserve floor would be
        crossed. Unmetered classes (not a key of `classes`) always
        fail open and are not charged against the snapshot."""
        if consumer_class not in self.classes:
            return {"ok": True, "class": consumer_class, "remaining": self._snapshot}

        self._ensure_snapshot()

        budget = self.classes[consumer_class]
        consumed = self._consumed[consumer_class]
        if consumed + cost > budget:
            return {"ok": False, "reason": BUDGET_EXHAUSTED,
                     "class": consumer_class, "remaining": self._snapshot}

        if self._snapshot_ok and self._snapshot is not None:
            projected = self._snapshot - cost
            if projected < self.reserve:
                return {"ok": False, "reason": BUDGET_EXHAUSTED,
                         "class": consumer_class, "remaining": self._snapshot}

        self._consumed[consumer_class] = consumed + cost
        if self._snapshot_ok and self._snapshot is not None:
            self._snapshot -= cost
        return {"ok": True, "class": consumer_class, "remaining": self._snapshot}
