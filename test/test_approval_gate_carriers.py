"""Live-fire carrier matrix for issue #1821: approval-gate.sh dual-reads
the `.on-the-record/role.json` sidecar (#1814) and the structured
`.git/gh-read-cache/issue-<n>-approvals.json` approval record (#1818),
falling back to its existing branch-regex parse and `gh` needle scan when
a carrier is absent or unparseable — byte-identical decisions on every
combination, plus a new fail-closed sidecar-vs-branch role-mismatch deny.

Runs the real shipped hook (`bash on-the-record/hooks/approval-gate.sh`)
via a real PreToolUse JSON payload on stdin, against a real git checkout
and a fake `gh` shim on PATH — same harness shape as
test/test_branch_skill_field.py's ApprovalGateDualReadTest.

Run: python3 -m pytest test/test_approval_gate_carriers.py -q
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
HOOK_PATH = HOOKS_DIR / "approval-gate.sh"
ISSUE = 88
SKILL = "implementation"
RECORD_FILE_PATH = f"docs/issue-{ISSUE}/reports/{SKILL}.md"

_FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
comments = json.loads(os.environ.get("FAKE_GH_COMMENTS", "[]"))
argv = sys.argv[1:]
if argv[:2] == ["issue", "view"] and "comments" in argv:
    print(json.dumps(comments))
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir: Path):
    p = bin_dir / "gh"
    p.write_text(_FAKE_GH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _init_repo_on_branch(root: Path, branch: str):
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com",
         "commit", "-q", "--allow-empty", "-m", "init"],
        cwd=root, check=True,
    )


def _write_approvers(root: Path, approvers):
    specs = root / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "approvers.md").write_text("\n".join(f"- {a}" for a in approvers) + "\n")


def _write_sidecar(root: Path, issue: int, skill: str):
    d = root / ".on-the-record"
    d.mkdir(parents=True, exist_ok=True)
    (d / "role.json").write_text(json.dumps({"skill": skill, "issue": issue}), encoding="utf-8")


def _write_sidecar_raw(root: Path, text: str):
    d = root / ".on-the-record"
    d.mkdir(parents=True, exist_ok=True)
    (d / "role.json").write_text(text, encoding="utf-8")


def _record_path(root: Path, issue: int) -> Path:
    return root / ".git" / "gh-read-cache" / f"issue-{issue}-approvals.json"


def _write_record(root: Path, issue: int, record: dict):
    p = _record_path(root, issue)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record), encoding="utf-8")


def _write_record_raw(root: Path, issue: int, text: str):
    p = _record_path(root, issue)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _run_gate(repo: Path, bin_dir: Path, comments=()):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": RECORD_FILE_PATH, "content": "x"},
        "cwd": str(repo),
    })
    env = dict(os.environ)
    env["CLAUDE_SKILL"] = SKILL
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GH_COMMENTS"] = json.dumps(list(comments))
    env.pop("ORCHESTRATE_OFF", None)
    env.pop("CORE_BUILD_NOW", None)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


class ApprovalGateCarrierMatrixTest(unittest.TestCase):
    def _workspace(self, tmp: Path, branch=None):
        repo = tmp / "repo"
        _init_repo_on_branch(repo, branch or f"issue-{ISSUE}/{SKILL}")
        _write_approvers(repo, ["alice"])
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        _write_fake_gh(bin_dir)
        return repo, bin_dir

    # --- both carriers present, agreeing/approved -----------------------

    def test_both_carriers_present_agreeing_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar(repo, ISSUE, SKILL)
            _write_record(repo, ISSUE, {SKILL: {"actor": "alice", "timestamp": "t"}})
            r = _run_gate(repo, bin_dir, comments=[])  # no gh call needed
            self.assertEqual(r.returncode, 0, r.stderr)

    # --- sidecar-only (no record) — falls back to needle scan -----------

    def test_sidecar_only_falls_back_to_needle_scan_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar(repo, ISSUE, SKILL)
            comments = [{"body": f"APPROVE issue-{ISSUE}/{SKILL}", "author": {"login": "alice"}}]
            r = _run_gate(repo, bin_dir, comments=comments)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_sidecar_only_falls_back_to_needle_scan_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar(repo, ISSUE, SKILL)
            r = _run_gate(repo, bin_dir, comments=[])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn(f"APPROVE issue-{ISSUE}/{SKILL}", r.stderr)

    # --- record-only (no sidecar) — role from branch regex, approval from record

    def test_record_only_skill_from_branch_approval_from_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_record(repo, ISSUE, {SKILL: {"actor": "alice", "timestamp": "t"}})
            r = _run_gate(repo, bin_dir, comments=[])  # no gh call needed
            self.assertEqual(r.returncode, 0, r.stderr)

    # --- neither carrier — byte-identical to pre-#1821 behavior ---------

    def test_neither_carrier_fresh_workspace_approved_matches_pre_1821(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            comments = [{"body": f"APPROVE issue-{ISSUE}/{SKILL}", "author": {"login": "alice"}}]
            r = _run_gate(repo, bin_dir, comments=comments)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_neither_carrier_fresh_workspace_denied_matches_pre_1821(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            r = _run_gate(repo, bin_dir, comments=[])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn(f"APPROVE issue-{ISSUE}/{SKILL}", r.stderr)

    # --- corrupt carriers — fall back cleanly, no crash ------------------

    def test_corrupt_sidecar_falls_back_to_branch_regex(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar_raw(repo, "{not valid json")
            comments = [{"body": f"APPROVE issue-{ISSUE}/{SKILL}", "author": {"login": "alice"}}]
            r = _run_gate(repo, bin_dir, comments=comments)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_corrupt_record_falls_back_to_needle_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar(repo, ISSUE, SKILL)
            _write_record_raw(repo, ISSUE, "[1, 2, 3]")  # parses, wrong shape (not a dict)
            comments = [{"body": f"APPROVE issue-{ISSUE}/{SKILL}", "author": {"login": "alice"}}]
            r = _run_gate(repo, bin_dir, comments=comments)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_corrupt_record_unparseable_json_falls_back_to_needle_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar(repo, ISSUE, SKILL)
            _write_record_raw(repo, ISSUE, "{not valid json")
            r = _run_gate(repo, bin_dir, comments=[])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn(f"APPROVE issue-{ISSUE}/{SKILL}", r.stderr)

    # --- sidecar-vs-branch role mismatch — hard deny, names both values --

    def test_skill_mismatch_both_resolve_hard_deny(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp, branch=f"issue-{ISSUE}/decoy")
            _write_sidecar(repo, ISSUE, SKILL)
            r = _run_gate(repo, bin_dir, comments=[])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn(f"issue-{ISSUE}/{SKILL}", r.stderr)
            self.assertIn(f"issue-{ISSUE}/decoy", r.stderr)
            self.assertIn("disagrees with the", r.stderr)

    def test_issue_number_mismatch_both_resolve_hard_deny(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            other_issue = ISSUE + 1
            repo, bin_dir = self._workspace(tmp, branch=f"issue-{other_issue}/{SKILL}")
            _write_sidecar(repo, ISSUE, SKILL)
            r = _run_gate(repo, bin_dir, comments=[])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn(f"issue-{ISSUE}/{SKILL}", r.stderr)
            self.assertIn(f"issue-{other_issue}/{SKILL}", r.stderr)

    def test_sidecar_present_unparseable_branch_no_mismatch_possible(self):
        # detached HEAD after sidecar resolves: no branch to cross-check
        # against, so it proceeds on the sidecar values alone — unchanged.
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo, bin_dir = self._workspace(tmp)
            _write_sidecar(repo, ISSUE, SKILL)
            sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True,
            ).stdout.strip()
            subprocess.run(["git", "checkout", "-q", sha], cwd=repo, check=True)
            comments = [{"body": f"APPROVE issue-{ISSUE}/{SKILL}", "author": {"login": "alice"}}]
            r = _run_gate(repo, bin_dir, comments=comments)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
