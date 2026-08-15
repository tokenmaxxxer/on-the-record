"""issue-1582 — role-patrol post-merge trigger, #1360-class origin guard.

Kept separate from patrol_queue.py: the trigger-identity guard here
(recursive self-triggering) is a different failure axis from the
queue's own correctness (fingerprint stability, dedup, budgets), and
this module's contract test needs to exercise exactly one function
(`should_fire`) — not the whole queue module's behavior.

Not wired into a git-native `.git/hooks/post-merge` file (git hooks are
local-only, don't propagate via clone/fork, and are invisible to the
harness driving role sessions — the same reasoning docs/issue-392's
post-merge-reconciliation proposal used to reject a standalone hook
file). `should_fire`/`run_if_eligible` are meant to be called from the
merge-command seam instead.

#1360 lesson (gates/spawn_on_pr.py lines 14-22): a watchdog re-armed
itself off patrol's own commits, causing recursive self-triggering.
`should_fire` refuses to arm when the triggering event's changed paths
are entirely patrol-produced artifacts (the queue file itself, or a
patrol measurement report).
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import patrol_queue  # noqa: E402

# Paths a patrol run itself writes to. An event whose changed-file set is
# a non-empty subset of these paths (or matches this prefix) is patrol's
# own artifact commit, not a genuine post-merge event to react to.
_PATROL_ARTIFACT_PATHS = {patrol_queue.QUEUE_REL_PATH}
_PATROL_ARTIFACT_PREFIXES = ("docs/issue-1582/reports/patrol-measurement",)


def _is_patrol_artifact(path: str) -> bool:
    if path in _PATROL_ARTIFACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _PATROL_ARTIFACT_PREFIXES)


def should_fire(event: dict) -> bool:
    """`event`: {"changed_files": [str, ...]}. Returns False when the
    event has no changed files, or when every changed file is a
    patrol-produced artifact — the #1360-class regression guard: patrol's
    own commits must never re-arm patrol."""
    changed = event.get("changed_files") or []
    if not changed:
        return False
    return not all(_is_patrol_artifact(p) for p in changed)


def run_if_eligible(event: dict, repo_root: Path, lane: str = "diff") -> dict | None:
    """Runs the tier-1 scan only when `should_fire(event)` is True.
    Returns the scan summary, or None when the event was skipped."""
    if not should_fire(event):
        return None
    return patrol_queue.run_scan(repo_root, lane)


def main(argv: list[str]) -> int:
    import json
    if not argv:
        print("usage: python3 -m gates.patrol_trigger <changed-file> [<changed-file> ...]")
        return 2
    event = {"changed_files": argv}
    print(json.dumps({"should_fire": should_fire(event)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
