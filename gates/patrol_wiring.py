"""issue-1597 E1 — post-merge patrol wiring: kill-switch, should_fire,
up-to-3-role selection reusing judge's Haiku prefilter, judge_cmd per
selected role, patrol_board.run for roles with new queue entries.

Wiring lives at the merge-command seam (docs/issue-392 precedent: no
git-native hooks) — on-the-record/commands/run.md's merge step calls
this module's CLI entry point right after `gh pr merge`.

Binding review correction (PR #1601): the per-merge role cap enforced
here must count only prefilter-HIT judge runs, not raw trace lines —
judge_cmd's own trace also logs prefilter MISSES (outcome "ok: prefilter
미스"), and stopping the role loop off a raw trace-line count would
exhaust the 3-role cap after 3 *attempts* rather than 3 real judged
roles. This module counts hits from judge_cmd's own return value
(`skipped` is False), never a trace-line count.
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import patrol_trigger  # noqa: E402
import patrol_board  # noqa: E402
import patrol_queue  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
KILL_SWITCH_REL_PATH = ".on-the-record/patrol-disabled"
RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")
# Mirrors spawn.JUDGE_MAX_ROLES_PER_MERGE — this loop reads that constant
# directly rather than defining a second cap number that could drift.
MAX_ROLES_PER_MERGE = 3


def kill_switch_active(repo_root: Path) -> bool:
    """Shared helper — this issue's E1 entry point and the future E2
    entry point both check this first, before touching should_fire,
    judge, or the board. Presence of the marker file is the only
    signal checked; content is ignored."""
    return (Path(repo_root) / KILL_SWITCH_REL_PATH).exists()


def _changed_files(repo_root: str, merge_sha: str) -> list[str]:
    r = subprocess.run(
        ["git", "-C", repo_root, "show", "--no-color", "--name-only",
         "--pretty=format:", merge_sha],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        return []
    return [line for line in r.stdout.splitlines() if line.strip()]


def _merge_roles(changed: list[str]) -> list[str]:
    """issue #2610: this used to iterate every name in the (now-deleted)
    44-entry role catalog and probe `judge_cmd` for each, relying on
    judge's own prefilter to decide jurisdiction — the catalog was pure
    iteration scaffolding, not a validity check, but it was still a
    closed set: a real session's role/skill slug that never happened to
    equal one of those 44 names could never be probed at all, and the
    sweep wasted probes on roles unrelated to this merge.

    Task-derived replacement, no catalog: this merge's own changed files
    already name every role whose record it touched
    (`docs/issue-<n>/reports/<role>.md`) — probe exactly those, and only
    those. Strictly more precise (never probes an unrelated role) and
    strictly more coverage (works for any role/skill slug, not just a
    legacy 44-name subset)."""
    out = set()
    for f in changed:
        m = RECORD_PATH.match(f)
        if m:
            out.add(m.group(1))
    return sorted(out)


def run(repo_root: str, merge_sha: str, judge_cmd=None) -> dict:
    """Entry point issue #1597 E1 calls from run.md's merge step.
    Kill-switch first; then should_fire; then up to
    MAX_ROLES_PER_MERGE roles' worth of judge_cmd HITS (reusing judge's
    own Haiku prefilter for jurisdiction — no second selector), then
    patrol_board.run for roles with new queue entries.

    `judge_cmd` is injectable (tests pass a stub); production callers
    leave it None and get spawn.judge_cmd, imported lazily since
    spawn.py is the heavy CLI module."""
    root = Path(repo_root).resolve()
    if kill_switch_active(root):
        print("[patrol-wiring] kill-switch active, skipping")
        return {"skipped": True, "reason": "kill_switch"}

    event = {"changed_files": _changed_files(str(root), merge_sha)}
    if not patrol_trigger.should_fire(event):
        print("[patrol-wiring] should_fire=False, skipping")
        return {"skipped": True, "reason": "should_fire_false"}

    if judge_cmd is None:
        sys.path.insert(0, str(ROOT))
        import spawn
        judge_cmd = spawn.judge_cmd

    hits = 0
    board_roles = []
    for role in _merge_roles(event["changed_files"]):
        if hits >= MAX_ROLES_PER_MERGE:
            print(f"[patrol-wiring] role cap reached ({MAX_ROLES_PER_MERGE} hits), stopping role loop")
            break
        try:
            result = judge_cmd(role, merge_sha, cwd=str(root))
        except Exception as e:
            print(f"[patrol-wiring] role={role} errored ({type(e).__name__}): continuing")
            continue
        if result.get("skipped"):
            print(f"[patrol-wiring] role={role} skipped ({result.get('reason')})")
            continue
        hits += 1
        enqueued = result.get("enqueued", [])
        print(f"[patrol-wiring] role={role} judged, enqueued={len(enqueued)}")
        if enqueued:
            board_roles.append(role)

    from datetime import datetime, timezone
    date = datetime.now(timezone.utc).date().isoformat()
    queue_path = root / patrol_queue.QUEUE_REL_PATH
    for role in board_roles:
        patrol_board.run_patrol_board(root, role, queue_path, False, date)
        print(f"[patrol-wiring] board refreshed for role={role}")

    return {"skipped": False, "hits": hits, "board_roles": board_roles}


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[0] != "run":
        print("usage: python3 gates/patrol_wiring.py run <repo-root> <merge-sha>")
        return 2
    run(argv[1], argv[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
