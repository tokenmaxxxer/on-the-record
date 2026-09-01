#!/usr/bin/env python3
"""issue #2974 — a batch merge must draw its approval requirement only
from open proposals its own PRs actually implicate, not from every
individually-required proposal sitting open in the repo. Live motivation:
`batch of 2 gh pr merge calls denied ... docs/issue-317/proposals/
playwright-98-cell-live-proof.md (reversibility=4)` blocked a two-PR batch
that had nothing to do with that proposal's write-set.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import risk_report  # noqa: E402


def _hook_proposal(path="docs/issue-317/proposals/playwright-98-cell-live-proof.md"):
    # a hook-directory path forces reversibility=AXIS_MAX
    # (`_reversibility_of`'s `HOOK_DIRS` branch) -> requires_individual_approval.
    return {"path": path, "files": ["on-the-record/hooks/some-gate.sh"],
            "added": 5, "removed": 0}


def test_batch_merge_unrelated_proposal_does_not_block_a_batch_it_does_not_implicate(tmp_path):
    unrelated = _hook_proposal()
    # neither PR in this batch touches on-the-record/hooks/ -- unrelated
    # to the individually-required proposal above.
    batch_files = [["docs/issue-1/reports/x.md"], ["gates/some_module.py"]]

    blocked = risk_report.batch_blocked([unrelated], tmp_path, batch_files=batch_files)

    assert blocked == []


def test_batch_merge_unrelated_proposal_implicated_proposal_still_blocks(tmp_path):
    implicated = _hook_proposal()
    # must-not (issue #2974): never weaken the requirement for a proposal
    # a batch genuinely implicates -- one PR here touches the same path.
    batch_files = [["on-the-record/hooks/some-gate.sh"]]

    blocked = risk_report.batch_blocked([implicated], tmp_path, batch_files=batch_files)

    assert len(blocked) == 1
    assert blocked[0]["path"] == implicated["path"]


def test_batch_merge_unrelated_proposal_empty_state_proceeds(tmp_path):
    # empty state (issue #2974 acceptance): a batch with no implicated
    # proposal proceeds.
    blocked = risk_report.batch_blocked([], tmp_path, batch_files=[["gates/x.py"]])
    assert blocked == []


def test_batch_merge_unrelated_proposal_no_batch_context_preserves_old_behavior(tmp_path):
    # batch_files=None (default): every individually-required proposal is
    # still included, unchanged from before #2974 -- callers without batch
    # context (e.g. the plain report()/CLI path) keep today's behavior.
    blocked = risk_report.batch_blocked([_hook_proposal()], tmp_path)
    assert len(blocked) == 1
