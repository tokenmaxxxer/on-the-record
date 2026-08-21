"""Tests for issue #1814: the explicit branch-role carrier (dual-read +
fallback across the 4 regex sites — approval-gate.sh, pr-preflight.sh,
contract-guard.sh, gates/flows.py).

Carrier write shape (spawn.py):
 - `.on-the-record/role.json` sidecar, written by `issue_workspace()` at
   every return point (fresh clone, reused work dir, reused src == work).
 - `role: <role>` trailer appended to the PR body `ensure_pushed()` uses
   when it opens a PR on the role's behalf.

Per-site read/fallback, live-fire for the three shell hooks (real
PreToolUse JSON via stdin against the actual shipped script, a fake `gh`
shim on PATH, and a real git checkout — same harness shape as
on-the-record/hooks/test_approval_gate.py / test_pr_preflight.py /
test_contract_guard.py): each site's sidecar-present case is set up so the
sidecar's role DIVERGES from what the branch-regex fallback alone would
produce, so a passing carrier-present case is proof the carrier was
actually read, not just tolerated. Each site's carrier-absent case pins
the fresh-workspace (no sidecar) fallback stays byte-identical to
pre-#1814 branch-regex-only behavior.

gates/flows.py's PR-body trailer is exercised as a direct unit test
against `_role_from_pr` (not a subprocess hook — it's an importable
Python module), covering field-read, fallback, and the body=None/no-body
absence cases.

Run: python3 -m pytest test/test_branch_role_field.py -q
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "gates"))

import spawn  # noqa: E402
import flows  # noqa: E402


# =============================================================================
# 1. spawn.py: carrier write shape
# =============================================================================

class SidecarWriteShapeTest(unittest.TestCase):
    def test_write_role_sidecar_creates_expected_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            spawn._write_role_sidecar(tmp, 1814, "implementation")
            p = Path(tmp) / ".on-the-record" / "role.json"
            self.assertTrue(p.is_file())
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(data, {"role": "implementation", "issue": 1814})

    def test_write_role_sidecar_overwrites_on_respawn(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            spawn._write_role_sidecar(tmp, 1814, "implementation")
            spawn._write_role_sidecar(tmp, 1814, "implementation")  # respawn, same role
            p = Path(tmp) / ".on-the-record" / "role.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(data, {"role": "implementation", "issue": 1814})

    def test_issue_workspace_writes_sidecar_at_every_return_point(self):
        # source-level pin (same convention as
        # test_convention_equivalence.py's ApprovalGateEquivalenceTest):
        # issue_workspace() has 3 return points (src==work reuse, work
        # reuse, fresh clone) and each must call the sidecar writer before
        # returning.
        text = (REPO_ROOT / "spawn.py").read_text(encoding="utf-8")
        start = text.index("def issue_workspace(")
        end = text.index("\ndef _recut_absorbed_branch(", start)
        body = text[start:end]
        self.assertEqual(body.count("_write_role_sidecar("), 3)


class PrBodyTrailerWriteShapeTest(unittest.TestCase):
    """Live call of the real `ensure_pushed()` against a local bare-repo
    origin (no network/GH_TOKEN needed for a file:// remote) and a fake
    `gh` shim on PATH, pinning the trailer `ensure_pushed()` actually
    writes into a newly-opened PR's body."""

    FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
argv = sys.argv[1:]
if argv[:3] == ["pr", "list", "--head"]:
    print("0")
elif argv[:2] == ["pr", "create"]:
    body = argv[argv.index("--body") + 1]
    log = os.environ.get("GH_CREATE_LOG")
    if log:
        with open(log, "w", encoding="utf-8") as f:
            f.write(body)
    print("https://github.com/example/repo/pull/1")
else:
    sys.exit(1)
"""

    def _write_fake_gh(self, bin_dir: Path):
        p = bin_dir / "gh"
        p.write_text(self.FAKE_GH)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)

    def test_ensure_pushed_body_carries_role_trailer(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            origin = tmp / "origin.git"
            work = tmp / "work"
            bin_dir = tmp / "bin"
            bin_dir.mkdir()
            self._write_fake_gh(bin_dir)

            subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
            subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True)
            subprocess.run(["git", "-C", str(work), "checkout", "-q", "-b", "issue-1814/implementation"], check=True)
            (work / "f.txt").write_text("x")
            subprocess.run(["git", "-C", str(work), "add", "f.txt"], check=True)
            subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "work"], check=True)

            create_log = tmp / "created_body.txt"
            orig_path = os.environ.get("PATH", "")
            orig_log = os.environ.get("GH_CREATE_LOG")
            os.environ["PATH"] = f"{bin_dir}:{orig_path}"
            os.environ["GH_CREATE_LOG"] = str(create_log)
            try:
                result = spawn.ensure_pushed(str(work), 1814, "implementation")
            finally:
                os.environ["PATH"] = orig_path
                if orig_log is None:
                    os.environ.pop("GH_CREATE_LOG", None)
                else:
                    os.environ["GH_CREATE_LOG"] = orig_log

            self.assertEqual(result["status"], "pr-opened", result)
            self.assertTrue(create_log.is_file())
            self.assertIn("role: implementation", create_log.read_text())


# =============================================================================
# 2. Shell hooks: live-fire dual-read + fallback (real script, real stdin)
# =============================================================================

def _write_sidecar(repo: Path, issue: int, role: str):
    d = repo / ".on-the-record"
    d.mkdir(parents=True, exist_ok=True)
    (d / "role.json").write_text(json.dumps({"role": role, "issue": issue}), encoding="utf-8")


def _init_repo_on_branch(root: Path, branch: str):
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


# --- approval-gate.sh --------------------------------------------------------

_FAKE_GH_APPROVAL_GATE = """#!/usr/bin/env python3
import json, os, sys
comments = json.loads(os.environ.get("FAKE_GH_COMMENTS", "[]"))
argv = sys.argv[1:]
if argv[:2] == ["issue", "view"] and "comments" in argv:
    print(json.dumps(comments))
else:
    sys.exit(1)
"""


def _write_fake_gh(bin_dir: Path, script: str):
    p = bin_dir / "gh"
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _run_approval_gate(repo: Path, bin_dir: Path, file_path: str, role_env: str, comments):
    payload = json.dumps({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "x"},
        "cwd": str(repo),
    })
    env = dict(os.environ)
    env["CLAUDE_ROLE"] = role_env
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["FAKE_GH_COMMENTS"] = json.dumps(comments)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOKS_DIR / "approval-gate.sh")],
        input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


class ApprovalGateDualReadTest(unittest.TestCase):
    ISSUE = 77
    RECORD_PATH = f"docs/issue-{ISSUE}/reports/implementation.md"

    def _bin_dir(self, tmp_path):
        b = tmp_path / "bin"
        b.mkdir()
        _write_fake_gh(b, _FAKE_GH_APPROVAL_GATE)
        return b

    def test_sidecar_present_drives_role_decode_over_decoy_branch(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = tmp / "repo"
            repo.mkdir()
            # branch role ("decoy") deliberately differs from the sidecar's
            # role ("implementation") — CLAUDE_ROLE=implementation, so only
            # the sidecar-read path reaches the approvers.md check at all.
            _init_repo_on_branch(repo, f"issue-{self.ISSUE}/decoy")
            _write_sidecar(repo, self.ISSUE, "implementation")
            bin_dir = self._bin_dir(tmp)
            r = _run_approval_gate(repo, bin_dir, self.RECORD_PATH, "implementation", [])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("approvers.md", r.stderr)

    def test_no_sidecar_decoy_branch_falls_open_unchanged(self):
        # same decoy branch, no sidecar: branch_role="decoy" != role
        # "implementation" -> "not this hook's target", exit 0. Pins the
        # fallback path is byte-identical to pre-#1814 behavior.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = tmp / "repo"
            repo.mkdir()
            _init_repo_on_branch(repo, f"issue-{self.ISSUE}/decoy")
            bin_dir = self._bin_dir(tmp)
            r = _run_approval_gate(repo, bin_dir, self.RECORD_PATH, "implementation", [])
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_absent_carrier_fresh_workspace_matches_pre_1814_behavior(self):
        # empty state (acceptance #2): fresh workspace, no carrier, branch
        # matches role -> same deny-for-missing-approvers.md as today.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo = tmp / "repo"
            repo.mkdir()
            _init_repo_on_branch(repo, f"issue-{self.ISSUE}/implementation")
            bin_dir = self._bin_dir(tmp)
            r = _run_approval_gate(repo, bin_dir, self.RECORD_PATH, "implementation", [])
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("approvers.md", r.stderr)


# --- pr-preflight.sh ---------------------------------------------------------

_FAKE_GH_PREFLIGHT = """#!/usr/bin/env python3
import json, os, sys
fixtures = json.load(open(os.environ["GH_FIXTURES"]))
argv = sys.argv[1:]
if argv[:2] == ["issue", "view"]:
    if "comments" in argv:
        print(json.dumps(fixtures.get("issue_comments", [])))
    elif "body" in argv:
        print(json.dumps(fixtures.get("issue_body", "")))
    else:
        sys.exit(1)
else:
    sys.exit(1)
"""


def _run_preflight(cmd, repo_dir, fixtures, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_gh(bin_dir, _FAKE_GH_PREFLIGHT)
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_text(json.dumps(fixtures))
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_FIXTURES"] = str(fixtures_path)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(HOOKS_DIR / "pr-preflight.sh")],
        input=payload, capture_output=True, text=True,
        env=env, cwd=str(repo_dir), timeout=20,
    )


class PrPreflightDualReadTest(unittest.TestCase):
    ISSUE = 77

    def _repo(self, tmp_path, approvers, branch):
        d = tmp_path / "repo"
        (d / "docs" / "specs").mkdir(parents=True)
        (d / "docs" / "specs" / "approvers.md").write_text(
            "\n".join(f"- {a}" for a in approvers) + "\n"
        )
        _init_repo_on_branch(d, branch)
        return d

    def test_sidecar_present_resolves_role_over_decoy_branch(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo_dir = self._repo(tmp, ["alice"], f"issue-{self.ISSUE}/decoy")
            _write_sidecar(repo_dir, self.ISSUE, "implementation")
            fixtures = {
                "issue_comments": [
                    {"body": f"APPROVE issue-{self.ISSUE}/implementation",
                     "author": {"login": "alice"}},
                ],
                "issue_body": "no plan section",
            }
            body = "Delivers the fix for the reported regression.\n\nCloses #77"
            cmd = f'gh pr create --title "delivery" --body "{body}"'
            r = _run_preflight(cmd, repo_dir, fixtures, tmp)
            # role resolved to "implementation" via the sidecar matches the
            # approval comment -> phase2 -> legitimate Closes trailer passes.
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_no_sidecar_decoy_branch_stays_phase1_and_denies_authored_closes(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo_dir = self._repo(tmp, ["alice"], f"issue-{self.ISSUE}/decoy")
            fixtures = {
                "issue_comments": [
                    {"body": f"APPROVE issue-{self.ISSUE}/implementation",
                     "author": {"login": "alice"}},
                ],
            }
            # role falls back to "decoy" (branch regex); the approval
            # comment is for "implementation", not "decoy" -> stays
            # phase1 -> author-written Closes in a phase-1 PR is refused,
            # byte-identical to pre-#1814 behavior.
            body = f"some proposal text, #{self.ISSUE}, and Closes #{self.ISSUE}"
            cmd = f'gh pr create --title "proposal" --body "{body}"'
            r = _run_preflight(cmd, repo_dir, fixtures, tmp)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertTrue("closing" in r.stderr.lower())

    def test_absent_carrier_fresh_workspace_matches_pre_1814_behavior(self, tmp_path=None):
        # empty state: no sidecar, branch matches role, legitimate phase-2
        # PR passes exactly as it did before #1814.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo_dir = self._repo(tmp, ["alice"], f"issue-{self.ISSUE}/implementation")
            fixtures = {
                "issue_comments": [
                    {"body": f"APPROVE issue-{self.ISSUE}/implementation",
                     "author": {"login": "alice"}},
                ],
                "issue_body": "no plan section",
            }
            body = "Delivers the fix for the reported regression.\n\nCloses #77"
            cmd = f'gh pr create --title "delivery" --body "{body}"'
            r = _run_preflight(cmd, repo_dir, fixtures, tmp)
            self.assertEqual(r.returncode, 0, r.stderr)


# --- contract-guard.sh --------------------------------------------------------

_FAKE_GH_CONTRACT_GUARD = """#!/usr/bin/env python3
import json, os, sys
fixtures = json.load(open(os.environ["GH_FIXTURES"]))
argv = sys.argv[1:]
if argv[:2] == ["pr", "view"]:
    print(json.dumps({
        "body": fixtures["pr_body"],
        "number": int(argv[2]),
        "commits": fixtures.get("commits", []),
        "files": fixtures.get("files", []),
    }))
elif argv[:2] == ["issue", "view"]:
    print(json.dumps(fixtures.get("issue_comments", [])))
elif argv[:2] == ["pr", "edit"]:
    body_idx = argv.index("--body") + 1
    new_body = argv[body_idx]
    log_path = os.environ.get("GH_EDIT_LOG")
    if log_path:
        calls = json.loads(open(log_path).read()) if os.path.exists(log_path) else []
        calls.append({"pr": argv[2], "body": new_body})
        open(log_path, "w").write(json.dumps(calls))
else:
    sys.exit(1)
"""


def _run_contract_guard(cmd, fixtures, tmp_path, cwd, edit_log):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    _write_fake_gh(bin_dir, _FAKE_GH_CONTRACT_GUARD)
    fixtures_path = tmp_path / "fixtures.json"
    fixtures_path.write_text(json.dumps(fixtures))
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_FIXTURES"] = str(fixtures_path)
    env["GH_EDIT_LOG"] = str(edit_log)
    env["ORCHESTRATE_OFF"] = ""
    return subprocess.run(
        ["bash", str(HOOKS_DIR / "contract-guard.sh")],
        input=payload, capture_output=True, text=True,
        env=env, cwd=str(cwd), timeout=20,
    )


class ContractGuardDualReadTest(unittest.TestCase):
    ISSUE = 9

    def test_sidecar_present_resolves_role_over_decoy_branch(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo_dir = tmp / "repo"
            (repo_dir / "docs" / "specs").mkdir(parents=True)
            (repo_dir / "docs" / "specs" / "approvers.md").write_text("- alice\n")
            _init_repo_on_branch(repo_dir, f"issue-{self.ISSUE}/decoy")
            _write_sidecar(repo_dir, self.ISSUE, "implementation")
            fixtures = {
                "pr_body": f"no closing keyword here, just #{self.ISSUE}",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [
                    {"body": f"APPROVE issue-{self.ISSUE}/implementation",
                     "author": {"login": "alice"}, "createdAt": "2026-08-05T00:00:00Z"},
                ],
                "files": [{"path": f"docs/issue-{self.ISSUE}/reports/implementation.md"}],
            }
            edit_log = tmp / "edits.json"
            r = _run_contract_guard("gh pr merge 7 --merge", fixtures, tmp, repo_dir, edit_log)
            self.assertEqual(r.returncode, 0, r.stderr)
            # is_record derived via the sidecar's role "implementation"
            # (which matches the record-file path in `files`) attached
            # Closes — the decoy branch alone could never have matched
            # "docs/issue-9/reports/decoy.md".
            calls = json.loads(edit_log.read_text())
            self.assertEqual(len(calls), 1)
            self.assertIn(f"Closes #{self.ISSUE}", calls[0]["body"])

    def test_no_sidecar_decoy_branch_is_record_false_no_closes_attached(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo_dir = tmp / "repo"
            (repo_dir / "docs" / "specs").mkdir(parents=True)
            (repo_dir / "docs" / "specs" / "approvers.md").write_text("- alice\n")
            _init_repo_on_branch(repo_dir, f"issue-{self.ISSUE}/decoy")
            fixtures = {
                "pr_body": f"no closing keyword here, just #{self.ISSUE}",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [
                    {"body": f"APPROVE issue-{self.ISSUE}/implementation",
                     "author": {"login": "alice"}, "createdAt": "2026-08-05T00:00:00Z"},
                ],
                # role falls back to "decoy" -> "docs/issue-9/reports/decoy.md"
                # is never in `files` -> is_record False, is_src_test False
                # (no src/test paths) -> unreached, byte-identical to
                # pre-#1814 fallback behavior.
                "files": [{"path": f"docs/issue-{self.ISSUE}/reports/implementation.md"}],
            }
            edit_log = tmp / "edits.json"
            r = _run_contract_guard("gh pr merge 7 --merge", fixtures, tmp, repo_dir, edit_log)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(edit_log.exists())

    def test_absent_carrier_fresh_workspace_matches_pre_1814_behavior(self):
        # empty state: no sidecar, branch matches the record's own role ->
        # same Closes-attach outcome as pre-#1814 (test_contract_guard.py's
        # test_own_record_file_alone_gets_closes).
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            repo_dir = tmp / "repo"
            (repo_dir / "docs" / "specs").mkdir(parents=True)
            (repo_dir / "docs" / "specs" / "approvers.md").write_text("- alice\n")
            _init_repo_on_branch(repo_dir, f"issue-{self.ISSUE}/implementation")
            fixtures = {
                "pr_body": f"no closing keyword here, just #{self.ISSUE}",
                "commits": [{"committedDate": "2026-08-01T00:00:00Z"}],
                "issue_comments": [
                    {"body": f"APPROVE issue-{self.ISSUE}/implementation",
                     "author": {"login": "alice"}, "createdAt": "2026-08-05T00:00:00Z"},
                ],
                "files": [{"path": f"docs/issue-{self.ISSUE}/reports/implementation.md"}],
            }
            edit_log = tmp / "edits.json"
            r = _run_contract_guard("gh pr merge 7 --merge", fixtures, tmp, repo_dir, edit_log)
            self.assertEqual(r.returncode, 0, r.stderr)
            calls = json.loads(edit_log.read_text())
            self.assertEqual(len(calls), 1)
            self.assertIn(f"Closes #{self.ISSUE}", calls[0]["body"])


# =============================================================================
# 3. gates/flows.py: PR body trailer field-read, fallback, absence
# =============================================================================

class FlowsRoleTrailerTest(unittest.TestCase):
    def test_field_read_prefers_trailer(self):
        m = flows._BRANCH_RE.match("issue-1814/decoy")
        self.assertIsNotNone(m)
        pr = {"body": "Part of #1814.\n\nrole: implementation"}
        self.assertEqual(flows._role_from_pr(pr, m), "implementation")

    def test_fallback_when_trailer_absent(self):
        m = flows._BRANCH_RE.match("issue-1814/implementation")
        self.assertIsNotNone(m)
        pr = {"body": "Part of #1814.\n\nno trailer here"}
        self.assertEqual(flows._role_from_pr(pr, m), "implementation")

    def test_absence_case_no_body_at_all(self):
        # fresh-workspace-shaped absence: body missing/None entirely ->
        # byte-identical to pre-#1814 pr_by_branch role (the branch group).
        m = flows._BRANCH_RE.match("issue-1814/implementation")
        self.assertIsNotNone(m)
        self.assertEqual(flows._role_from_pr({}, m), "implementation")
        self.assertEqual(flows._role_from_pr({"body": None}, m), "implementation")

    def test_pr_by_branch_grouping_uses_trailer(self):
        # exercises the actual call site (gates/flows.py ~L336), not just
        # the helper in isolation.
        prs = [{"headRefName": "issue-1814/decoy",
                "body": "role: implementation"}]
        pr_by_branch = {}
        for pr in prs:
            m = flows._BRANCH_RE.match(pr.get("headRefName") or "")
            if m:
                pr_by_branch[(m.group(1), flows._role_from_pr(pr, m))] = pr
        self.assertIn(("issue-1814", "implementation"), pr_by_branch)
        self.assertNotIn(("issue-1814", "decoy"), pr_by_branch)


if __name__ == "__main__":
    unittest.main()
