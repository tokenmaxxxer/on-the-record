#!/usr/bin/env python3
"""issue #587: remediation_spawn.py 의 finding -> spawn-task 생성 단위 테스트.

  python3 -m pytest gates/test_remediation_spawn.py
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import remediation_spawn


def _write_record(decisions_dir: Path, seq: int, **fields) -> Path:
    decisions_dir.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for k, v in fields.items():
        lines.append(f"{k}: {v}")
    lines += ["---", ""]
    path = decisions_dir / f"remediation-{seq}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _no_gh_no_branch(root, branch):
    return False


def _no_pr(root, remediation_path):
    return False


class OneOpenFinding(unittest.TestCase):
    def test_fixture_finding_yields_one_task(self):
        with _tmpdir() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs/issue-42/decisions"
            _write_record(decisions_dir, 1,
                           finding_source="docs/issue-42/decisions/auto-1.md",
                           routed_to="coding",
                           target_path="src/foo.py",
                           required_fix="add null check",
                           contradicting_role="qa",
                           round=1,
                           status="open",
                           timestamp="2026-08-10T00:00:00Z")
            with mock.patch.object(remediation_spawn, "_branch_exists", _no_gh_no_branch), \
                 mock.patch.object(remediation_spawn, "_pr_already_launched", _no_pr):
                tasks = remediation_spawn.pending_remediation_tasks(root, 42)
            self.assertEqual(len(tasks), 1)
            t = tasks[0]
            self.assertEqual(t["role"], "coding")
            self.assertEqual(
                t["task"],
                "Remediation round 1: fix `src/foo.py` — add null check "
                "(routed from `docs/issue-42/decisions/remediation-1.md`, "
                "finding: `docs/issue-42/decisions/auto-1.md`)")
            self.assertEqual(t["remediation_path"],
                              "docs/issue-42/decisions/remediation-1.md")


class ThreeRoundEscalation(unittest.TestCase):
    def test_escalated_record_excluded(self):
        with _tmpdir() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs/issue-7/decisions"
            _write_record(decisions_dir, 1,
                           finding_source="docs/issue-7/decisions/auto-1.md",
                           routed_to="coding", target_path="a.py",
                           required_fix="fix a", contradicting_role="qa",
                           round=1, status="open", timestamp="t1")
            _write_record(decisions_dir, 2,
                           finding_source="docs/issue-7/decisions/auto-2.md",
                           routed_to="coding", target_path="a.py",
                           required_fix="fix a again", contradicting_role="qa",
                           round=2, status="open", timestamp="t2")
            _write_record(decisions_dir, 3,
                           finding_source="docs/issue-7/decisions/auto-3.md",
                           routed_to="coding", target_path="a.py",
                           required_fix="fix a yet again", contradicting_role="qa",
                           round=4, status="escalated", timestamp="t3")
            with mock.patch.object(remediation_spawn, "_branch_exists", _no_gh_no_branch), \
                 mock.patch.object(remediation_spawn, "_pr_already_launched", _no_pr):
                tasks = remediation_spawn.pending_remediation_tasks(root, 7)
            self.assertEqual({t["remediation_path"] for t in tasks},
                              {"docs/issue-7/decisions/remediation-1.md",
                               "docs/issue-7/decisions/remediation-2.md"})


class NoFindings(unittest.TestCase):
    def test_no_records_yields_empty_list(self):
        with _tmpdir() as tmp:
            root = Path(tmp)
            tasks = remediation_spawn.pending_remediation_tasks(root, 99)
            self.assertEqual(tasks, [])

    def test_no_open_records_yields_empty_list(self):
        with _tmpdir() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs/issue-11/decisions"
            _write_record(decisions_dir, 1,
                           finding_source="x", routed_to="coding",
                           target_path="x.py", required_fix="x",
                           contradicting_role="qa", round=1,
                           status="escalated", timestamp="t")
            tasks = remediation_spawn.pending_remediation_tasks(root, 11)
            self.assertEqual(tasks, [])


class Idempotency(unittest.TestCase):
    def test_existing_branch_excludes_task(self):
        with _tmpdir() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs/issue-5/decisions"
            _write_record(decisions_dir, 1,
                           finding_source="x", routed_to="coding",
                           target_path="x.py", required_fix="x",
                           contradicting_role="qa", round=1,
                           status="open", timestamp="t")
            with mock.patch.object(remediation_spawn, "_branch_exists",
                                    lambda root, branch: True), \
                 mock.patch.object(remediation_spawn, "_pr_already_launched", _no_pr):
                tasks = remediation_spawn.pending_remediation_tasks(root, 5)
            self.assertEqual(tasks, [])

    def test_existing_pr_excludes_task(self):
        with _tmpdir() as tmp:
            root = Path(tmp)
            decisions_dir = root / "docs/issue-6/decisions"
            _write_record(decisions_dir, 1,
                           finding_source="x", routed_to="coding",
                           target_path="x.py", required_fix="x",
                           contradicting_role="qa", round=1,
                           status="open", timestamp="t")
            with mock.patch.object(remediation_spawn, "_branch_exists", _no_gh_no_branch), \
                 mock.patch.object(remediation_spawn, "_pr_already_launched",
                                    lambda root, remediation_path: True):
                tasks = remediation_spawn.pending_remediation_tasks(root, 6)
            self.assertEqual(tasks, [])


def _tmpdir():
    import tempfile
    return tempfile.TemporaryDirectory()


if __name__ == "__main__":
    unittest.main()
