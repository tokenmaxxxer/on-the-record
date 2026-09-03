"""Issue #3266: `spawn.py clean --dry-run` reported "지움 19, 남김 279" on a
19G `~/.tokenmaxxxer/work` -- 94% of workspaces kept, almost none of it
real work. Every "남김" line read `미보존 작업 있음  [미추적 파일 N건]`,
and the N files were, without exception, the `.on-the-record/` scaffolding
the harness writes at spawn time plus a report stub the session created
and never filled -- a crashed session's exact signature. Manually deleting
only the 219 workspaces with no unpushed commits reclaimed 13G of the 19G;
the cleaner's untracked-file test refused to touch almost any of it.

This file is the acceptance's two `check:` cases against
`spawn._workspace_clean_state()` (the `roster_clean()`/`auto_sweep()`
predicate, extracted to lifecycle.py -- see
tests/test_workspace_clean_state_predicate.py for the surrounding
decision table this issue's fix slots into) plus the two `must not`
guards: a real unpushed commit, and this repository's squash-merge case
(a landed branch's original commits are absent from `main` by SHA --
commit-SHA absence is not evidence of loss) must never be misread as
reclaimable.

  python3 -m pytest tests/test_issue_3266_reclaimable_stub.py -q
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    r = subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True,
                        text=True, timeout=30)
    assert r.returncode == 0, f"git {args} in {cwd} failed: {r.stderr}"
    return r


def _make_pushed_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(["init", "-q"], path)
    _git(["config", "user.email", "test@example.com"], path)
    _git(["config", "user.name", "Test"], path)
    (path / "f.txt").write_text("x\n")
    _git(["add", "f.txt"], path)
    _git(["commit", "-q", "-m", "init"], path)
    remote = path.parent / (path.name + "-remote.git")
    _git(["init", "-q", "--bare", str(remote)], path.parent)
    _git(["remote", "add", "origin", str(remote)], path)
    _git(["push", "-q", "-u", "origin", "HEAD"], path)
    return remote


_EMPTY_REPORT_STUB = """---
issue: 9999
role: crashed-role-abc12345
author: crashed-role-abc12345
skills: crashed-role (skill-repository(c05de12))
verifies_subject: false
loop_state: in-progress
upstream:
  - path: <docs/issue-9999/... or code path this record builds on>
    sha:
---

# issue-9999 -- crashed-role-abc12345 record

## What was done

<!-- fill: the delivered work, concretely -->

## Why

<!-- fill: rationale for the approach taken -->

## What did not work

None.

## Upstream basis

<!-- fill: the concrete upstream inputs -->

## Open findings

<!-- fill: each open finding with its resolution path, or "none" -->

## Next steps

<!-- fill while loop_state is non-terminal; set loop_state to the terminal
value for this record kind when done -->
"""

_REAL_REPORT = """---
issue: 9999
role: finished-role-abc12345
author: finished-role-abc12345
skills: finished-role (skill-repository(c05de12))
verifies_subject: false
loop_state: done
upstream:
  - path: docs/issue-9999/proposals/plan.md
    sha: same-commit
---

# issue-9999 -- finished-role-abc12345 record

## What was done

Rewrote the retry loop in the ingest worker to back off exponentially
instead of spinning at a fixed interval, which was the actual cause of
the CPU spike reported in the parent issue.

## Why

The fixed-interval retry was saturating a single core under sustained
upstream 503s; exponential backoff caps the steady-state rate.
"""

_HEADING_ONLY_REPORT = """---
issue: 9999
role: crashed-role-abc12345
author: crashed-role-abc12345
skills: crashed-role (skill-repository(c05de12))
verifies_subject: false
loop_state: in-progress
upstream:
  - path: <docs/issue-9999/... or code path this record builds on>
    sha:
---

### Root cause: retry loop lacked backoff, saturating one core under sustained 503s
"""

_BARE_HASH_LINE_REPORT = """---
issue: 9999
role: crashed-role-abc12345
author: crashed-role-abc12345
skills: crashed-role (skill-repository(c05de12))
verifies_subject: false
loop_state: in-progress
upstream:
  - path: <docs/issue-9999/... or code path this record builds on>
    sha:
---

#3266 was the root cause, confirmed via bisect against commit abc123.
"""


def _seed_harness_scaffolding(w: Path) -> None:
    (w / ".on-the-record").mkdir()
    (w / ".on-the-record" / "role.json").write_text('{"issue": 9999}\n')
    (w / ".on-the-record" / "model-routing.json").write_text("{}\n")
    directive = w / ".on-the-record" / "directive"
    directive.mkdir()
    (directive / "turn-budget.md").write_text("# turn budget\n")


class ReclaimableStubTest(unittest.TestCase):
    """check: a workspace whose only untracked files are harness
    scaffolding and an empty report stub is classified as reclaimable."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.root = Path(self._td.name)

    def _clean_state(self, w: Path):
        return spawn._workspace_clean_state(w, live={}, unreadable=None)

    def test_crashed_session_shape_is_reclaimable(self):
        """The exact shape the issue names: `.on-the-record/` scaffolding
        plus an unfilled report stub, nothing else untracked, no unpushed
        commits. This is the 279-of-298 case that must flip to safe."""
        w = self.root / "crashed"
        _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        (reports / "crashed-role-abc12345.md").write_text(_EMPTY_REPORT_STUB)
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)

    def test_real_report_content_is_never_reclaimed(self):
        """check: a workspace holding a report with real body content is
        never reclaimed -- the opposite failure this issue warns against."""
        w = self.root / "real-work"
        _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        (reports / "finished-role-abc12345.md").write_text(_REAL_REPORT)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미추적", detail)

    def test_unpushed_commit_with_stub_and_scaffolding_is_never_deleted(self):
        """must not: a workspace with commits that exist nowhere else must
        never be deleted -- an unpushed commit must dominate even when
        every untracked file is otherwise reclaimable noise."""
        w = self.root / "unpushed"
        _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        (reports / "crashed-role-abc12345.md").write_text(_EMPTY_REPORT_STUB)
        (w / "g.txt").write_text("unpushed content\n")
        _git(["add", "g.txt"], w)
        _git(["commit", "-q", "-m", "never pushed"], w)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)
        self.assertIn("미push", detail)

    def test_squash_merged_branch_with_stub_is_reclaimable_after_fetch(self):
        """must not (the squash-merge corollary): this repository
        squash-merges, so a landed branch's original commits are absent
        from `main` by SHA -- local `ahead` state must not be mistaken
        for real loss once a fetch shows the branch's tip content already
        landed under a different ref/SHA. Exercises the existing
        `git fetch --all`-then-recheck at lifecycle.py:903-921, which this
        fix must not disturb: with only reclaimable noise otherwise
        untracked, the workspace must resolve to safe once the fetch
        clears the stale-ahead read, exactly as it does today for a
        plain (non-squash) merge to a differently-named ref."""
        w = self.root / "squash-merged"
        remote = _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        (reports / "crashed-role-abc12345.md").write_text(_EMPTY_REPORT_STUB)
        (w / "h.txt").write_text("squashed content\n")
        _git(["add", "h.txt"], w)
        _git(["commit", "-q", "-m", "will be squash-merged"], w)
        commit = _git(["rev-parse", "HEAD"], w).stdout.strip()
        # Simulate the squash-merge landing on the shared remote under a
        # different ref (its content is preserved, its original SHA is
        # not necessarily the one main carries) while this workspace's
        # local remote-tracking knowledge of that ref is stale.
        _git(["push", "-q", "origin", "HEAD:refs/heads/landed"], w)
        _git(["update-ref", "-d", "refs/remotes/origin/landed"], w)
        ahead_before = _git(
            ["log", "--branches", "--not", "--remotes", "--oneline"], w
        ).stdout.strip()
        self.assertIn(commit[:7], ahead_before,
                       "test setup must reproduce a falsely-ahead commit")
        reason, detail = self._clean_state(w)
        self.assertIsNone(reason, detail)

    def test_fifo_report_path_is_never_deleted_and_does_not_hang(self):
        """PR #3271 finding: a named pipe at a report path has no content
        to classify -- `_report_stub_has_no_content()` must fail closed
        (kept, not reclaimable) without blocking on the read that a FIFO
        with no writer never satisfies. Exercised directly against the
        predicate, not through `_workspace_clean_state()`: `git ls-files
        -z --others` itself never lists a FIFO (verified separately), so
        the full clean-sweep path never reaches this file at all -- the
        predicate must still fail closed if it is ever handed one, e.g.
        by a future caller that lists the filesystem directly."""
        w = self.root / "fifo"
        _make_pushed_repo(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        os.mkfifo(reports / "crashed-role-abc12345.md")
        result: dict = {}

        def _run():
            result["value"] = spawn._report_stub_has_no_content(
                w, "docs/issue-9999/reports/crashed-role-abc12345.md")

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=5)
        self.assertFalse(t.is_alive(),
                          "_report_stub_has_no_content must not hang on a FIFO")
        self.assertFalse(result["value"], "a FIFO must fail closed (kept)")

    def test_symlink_escaping_workspace_to_stub_shaped_target_is_never_deleted(self):
        """PR #3271 finding: a report-path symlink pointing outside the
        workspace must be judged on the workspace's own file, not on
        whatever the external target looks like -- even when that target
        happens to be stub-shaped."""
        w = self.root / "symlink-escape"
        _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        external_stub = outside / "external.md"
        external_stub.write_text(_EMPTY_REPORT_STUB)
        os.symlink(external_stub, reports / "crashed-role-abc12345.md")
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)

    def test_content_expressed_only_in_a_heading_is_never_reclaimed(self):
        """PR #3272 finding: a report whose only body line is a sub-heading
        carrying the actual finding is real prose, not disposable heading
        noise -- it must not be misread as a content-free stub."""
        w = self.root / "heading-only"
        _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        (reports / "crashed-role-abc12345.md").write_text(_HEADING_ONLY_REPORT)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)

    def test_bare_hash_prefixed_line_is_never_reclaimed(self):
        """PR #3272 finding: a line starting with `#` that is not valid
        ATX heading syntax (no space after the hash) is body prose, not
        heading noise -- it must not be misread as a content-free stub."""
        w = self.root / "bare-hash"
        _make_pushed_repo(w)
        _seed_harness_scaffolding(w)
        reports = w / "docs" / "issue-9999" / "reports"
        reports.mkdir(parents=True)
        (reports / "crashed-role-abc12345.md").write_text(_BARE_HASH_LINE_REPORT)
        reason, detail = self._clean_state(w)
        self.assertEqual(reason, "dirty", detail)


if __name__ == "__main__":
    unittest.main()
