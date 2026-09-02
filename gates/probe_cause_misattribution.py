#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3047.

Exists so the acceptance amendment's checks can be stated as plain
`check:` lines (`python3 gates/probe_cause_misattribution.py`) instead of
prose that `check_runner` would classify as unmapped judgment (#3059).

Runs `watchdog._classify_narrowing_prs` -- the board-sweep classifier that
decides why a `board_now`-mapped issue's subject-shaped PR branch is
absent from the board -- against two synthesised subjects, entirely
offline (no `gh`, no network, no live repo):

1. A brand-new issue with a single open PR and no merged record yet
   (issue #3042's actually-observed shape: the board reflects merged
   main only, the issue was filed minutes earlier, nothing has landed).
2. A genuinely corrupted merge-base subject (issue #2379's shape: this
   subject previously had a MERGED record, and a later PR for the same
   subject is now unmapped -- the one case that legitimately still
   deserves the `recut-corrupted` force-push repair).
3. A subject the existing `gh pr list`-equivalent index cannot resolve
   either way (a sibling branch closed without merging -- consistent
   with either normal supersession or an abandoned corrupted attempt).

Asserts, per the amendment's substance:
- (1) and (2) produce different classifier output.
- Only (2)'s output carries the `recut-corrupted` remediation sentence;
  (1)'s output does not.
- (3) is reported as its own distinct `unclassified` cause -- it must not
  silently fall into either the corrupted-merge-base or no-record-yet
  bucket.

The distinguishing signal is `pr_index` -- the same bulk
`gh api repos/{slug}/pulls?state=all` index `_board_wide_sweep` already
fetches once per delta-carrying tick (issue #1702/#1688) -- scanned for
sibling `issue-<n>/*` branches' MERGED/CLOSED state. No per-PR `gh` call
is made anywhere in this path; the probe itself makes no `gh` call at all.

Run as `python3 gates/probe_cause_misattribution.py` from the repo root,
no arguments. Prints `ok` and exits 0 on success; prints a message to
stderr and exits non-zero otherwise. Must fail against current main (the
`pr_index` parameter and the cause dimension it enables do not exist
there -- `_classify_narrowing_prs` collapses all three causes into one).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))
import spawn  # noqa: E402
import watchdog  # noqa: E402
import state_paths  # noqa: E402

watchdog._sp = spawn

# One-shot noise suppression (`_watchdog_note_unmappable_pr`, issue #2196)
# persists to `state_paths.STATE_ROOT` by PR number, keyed independently of
# this probe's synthesised subjects -- point it at a fresh tempdir so a
# repeat run of this probe is never silently suppressed by a prior run's
# leftover state (this is not the target repo's real `runs/` state).
state_paths.STATE_ROOT = Path(tempfile.mkdtemp(prefix="probe-cause-misattribution-"))

_ROOT = Path("/nonexistent")


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    # (1) new issue, open PR, no merged record yet -- issue #3042's shape.
    new_issue_pr_index = {
        "issue-3042/implementation-audit-0d4eb553":
            {"number": 43, "state": "OPEN", "body": ""},
    }
    (_changed, _non_subj, new_issue_loss, _repeat) = watchdog._classify_narrowing_prs(
        _ROOT, {43}, {43: "issue-3042/implementation-audit-0d4eb553"}, {},
        new_issue_pr_index)
    if len(new_issue_loss) != 1:
        _fail(f"expected exactly 1 mapping-loss item for the new-issue "
              f"subject, got {new_issue_loss!r}")
    new_issue_line = watchdog._format_mapping_loss_line(*new_issue_loss[0])

    # (2) genuinely corrupted merge-base -- issue #2379's shape: this
    # subject already has a MERGED record, and a later PR under the same
    # subject is unmapped.
    corrupted_pr_index = {
        "issue-2379/observability-signal-golden-abc123":
            {"number": 41, "state": "MERGED", "body": ""},
        "issue-2379/observability-signal-golden-def456":
            {"number": 42, "state": "OPEN", "body": ""},
    }
    (_changed, _non_subj, corrupted_loss, _repeat) = watchdog._classify_narrowing_prs(
        _ROOT, {42}, {42: "issue-2379/observability-signal-golden-def456"}, {},
        corrupted_pr_index)
    if len(corrupted_loss) != 1:
        _fail(f"expected exactly 1 mapping-loss item for the "
              f"corrupted-merge-base subject, got {corrupted_loss!r}")
    corrupted_line = watchdog._format_mapping_loss_line(*corrupted_loss[0])

    # (3) unclassifiable -- a sibling branch closed without merging, no
    # merged sibling anywhere. Must not silently fall into either bucket.
    unclassifiable_pr_index = {
        "issue-5000/some-skill-abc123":
            {"number": 44, "state": "CLOSED", "body": ""},
        "issue-5000/some-skill-def456":
            {"number": 45, "state": "OPEN", "body": ""},
    }
    (_changed, _non_subj, unclassifiable_loss, _repeat) = watchdog._classify_narrowing_prs(
        _ROOT, {45}, {45: "issue-5000/some-skill-def456"}, {}, unclassifiable_pr_index)
    if len(unclassifiable_loss) != 1:
        _fail(f"expected exactly 1 mapping-loss item for the "
              f"unclassifiable subject, got {unclassifiable_loss!r}")
    unclassifiable_cause = unclassifiable_loss[0][3]
    unclassifiable_line = watchdog._format_mapping_loss_line(*unclassifiable_loss[0])

    # Assertion 1: the two synthesised subjects produce different output.
    if new_issue_line == corrupted_line:
        _fail("new-issue and corrupted-merge-base subjects produced "
              f"identical classifier output: {new_issue_line!r}")

    # Assertion 2: only the corrupted-merge-base case carries the
    # `recut-corrupted` remediation sentence.
    if "recut-corrupted" not in corrupted_line:
        _fail("corrupted-merge-base output is missing its recut-corrupted "
              f"remediation sentence: {corrupted_line!r}")
    if "recut-corrupted" in new_issue_line:
        _fail("new-issue (no-record-yet) output wrongly carries a "
              f"recut-corrupted instruction: {new_issue_line!r}")

    # Assertion 3: the unclassifiable subject is reported as its own
    # distinct cause -- not silently folded into either bucket, and it
    # does not carry the repair instruction either (must-not clause).
    if unclassifiable_cause in (watchdog._MAPPING_LOSS_CORRUPTED,
                                 watchdog._MAPPING_LOSS_NO_RECORD_YET):
        _fail("subject with no established cause was bucketed into "
              f"{unclassifiable_cause!r} instead of being reported as "
              "unclassified")
    if unclassifiable_cause != watchdog._MAPPING_LOSS_UNCLASSIFIED:
        _fail(f"expected the unclassifiable subject's cause to be "
              f"{watchdog._MAPPING_LOSS_UNCLASSIFIED!r}, "
              f"got {unclassifiable_cause!r}")
    if "recut-corrupted" in unclassifiable_line:
        _fail("unclassified output wrongly carries a recut-corrupted "
              f"instruction: {unclassifiable_line!r}")
    if unclassifiable_line in (new_issue_line, corrupted_line):
        _fail("unclassified output is not distinguishable from one of "
              "the other two causes' output")

    print("ok")


if __name__ == "__main__":
    main()
