"""Regression test for issue #2637 (adversarial-review, aba56a87): the
`^`-anchored PRODUCT_CAPTURE_PRIORITIES_DIR_RE exemption added to close
a src/-rooted bypass must not also deny a legitimate priorities-shard
write whose `file_path` arrives absolute — the same shape
call-shape-guard.sh, accumulation-claim-guard.sh, and
record-claim-guard.sh already treat as ordinary input.

Runs the real shipped hook (`bash on-the-record/hooks/deliverable-guard.sh`)
via a real PreToolUse JSON payload on stdin, against a real git checkout —
same harness shape as test/test_approval_gate_carriers.py.

Run: python3 -m pytest test/test_deliverable_guard_priorities_shard.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "deliverable-guard.sh"

# deliverable-guard.sh exempts any path with a literal "tmp" path segment
# (scratch/tmp work areas, see the hook's own issue #787 H1 comment) — the
# fixture root must not live under the system tempdir (usually /tmp) or
# every absolute-path case below would exit 0 via that unrelated exemption
# instead of the priorities-shard regex this test targets.
_FIXTURE_BASE = Path.home() / ".otr-dg-test-fixture"


def _init_repo(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)


def _run_gate(repo: Path, file_path: str, cwd: str | None = None):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path},
        "cwd": cwd if cwd is not None else str(repo),
        "session_id": "test-sess",
    })
    env = dict(os.environ)
    env.pop("TOKENMAXXXER_SPAWNED", None)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


class DeliverableGuardPrioritiesShardTest(unittest.TestCase):
    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        _init_repo(self.repo)

    def test_relative_shard_write_is_exempt(self):
        r = _run_gate(self.repo, "docs/reports/product/priorities/x.md")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_relative_src_rooted_bypass_stays_denied(self):
        r = _run_gate(
            self.repo, "src/docs/reports/product/priorities/hack.md")
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_absolute_src_rooted_bypass_stays_denied(self):
        r = _run_gate(
            self.repo,
            str(self.repo / "src/docs/reports/product/priorities/hack.md"))
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_absolute_shard_write_is_exempt(self):
        r = _run_gate(
            self.repo,
            str(self.repo / "docs/reports/product/priorities/x.md"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_issue_scoped_shard_write_is_exempt(self):
        r = _run_gate(
            self.repo,
            str(self.repo
                / "docs/issue-99/reports/product/priorities/x.md"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_absolute_shard_write_with_dotdot_is_exempt(self):
        r = _run_gate(
            self.repo,
            str(self.repo
                / "foo/../docs/reports/product/priorities/x.md"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_real_deliverable_write_still_denied(self):
        r = _run_gate(self.repo, "src/foo.py")
        self.assertEqual(r.returncode, 2, r.stderr)

    def test_absolute_legacy_priorities_file_still_exempt(self):
        r = _run_gate(
            self.repo, str(self.repo / "docs/reports/product/priorities.md"))
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
