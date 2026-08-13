#!/usr/bin/env python3
"""이슈 #1124 — `spawn.py clean`/`reconcile --unreported` 안전성 회귀.

  python3 gates/test_clean_reconcile_safety.py
"""
from __future__ import annotations
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _bare_workspace(wb: Path, name: str) -> Path:
    """미커밋 변경도, unpushed 커밋도 없는(=삭제 대상) 워크스페이스."""
    w = wb / name
    w.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=w, check=True)
    return w


class CleanReconcileSafetyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        self.state_root = self.tmp / "state"
        self.wb = self.tmp / "work"
        self.wb.mkdir()

        self._orig_root = spawn.ROOT
        self._orig_roster = spawn.ROSTER
        self._orig_idx = spawn.WORKSPACE_INDEX
        spawn.ROOT = self.root
        spawn.ROSTER = self.state_root / "active.json"
        spawn.WORKSPACE_INDEX = self.state_root / "workspaces.json"

    def tearDown(self):
        spawn.ROOT = self._orig_root
        spawn.ROSTER = self._orig_roster
        spawn.WORKSPACE_INDEX = self._orig_idx
        self._tmp.cleanup()

    def _write_ledger(self, entries: list[dict]) -> None:
        d = self.root / "runs"
        d.mkdir(parents=True, exist_ok=True)
        with (d / "ledger.jsonl").open("w", encoding="utf-8") as fh:
            for e in entries:
                fh.write(json.dumps(e) + "\n")

    # (a) reconcile: 삭제된(존재하지 않는) 워크스페이스는 크래시가 아니라 skip.
    def test_reconcile_unreported_skips_missing_workspace(self):
        missing_work = str(self.tmp / "gone-workspace")
        spawn.WORKSPACE_INDEX.parent.mkdir(parents=True, exist_ok=True)
        spawn.WORKSPACE_INDEX.write_text(json.dumps({
            "on-the-record/issue-1110/implementation": {
                "work": missing_work, "log": missing_work + ".session.log",
            },
        }))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            total = spawn._roster_reconcile_unreported()
        self.assertEqual(total, 0)
        self.assertIn("건너뜀", buf.getvalue())

    # (b) clean: refused 등 non-landed outcome 의 로그는 archive, 워크스페이스는 지운다.
    def test_clean_archives_non_landed_log(self):
        w = _bare_workspace(self.wb, "on-the-record-issue-99-refused")
        log = self.wb / (w.name + ".session.20260813.1.log")
        log.write_text("refusal reason\n")
        self._write_ledger([{"log": str(log), "outcome": "refused"}])

        rc = spawn.roster_clean(self.wb, None)
        self.assertEqual(rc, 0)
        self.assertFalse(w.exists())
        self.assertFalse(log.exists())
        archived = self.wb / ".archived-logs" / log.name
        self.assertTrue(archived.exists())
        self.assertEqual(archived.read_text(), "refusal reason\n")

    # (c) clean: landed(progressed) outcome 은 오늘처럼 로그까지 삭제.
    def test_clean_deletes_landed_log(self):
        w = _bare_workspace(self.wb, "on-the-record-issue-100-landed")
        log = self.wb / (w.name + ".session.20260813.2.log")
        log.write_text("landed session\n")
        self._write_ledger([{"log": str(log), "outcome": "progressed"}])

        rc = spawn.roster_clean(self.wb, None)
        self.assertEqual(rc, 0)
        self.assertFalse(w.exists())
        self.assertFalse(log.exists())
        self.assertFalse((self.wb / ".archived-logs" / log.name).exists())

    # (d) 빈 상태: ledger.jsonl 없음, work dir 비어있음, roster/workspace 인덱스 없음.
    def test_empty_state_noops_cleanly(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = spawn.roster_clean(self.wb, None)
            total = spawn._roster_reconcile_unreported()
        self.assertEqual(rc, 0)
        self.assertEqual(total, 0)
        self.assertEqual(spawn._ledger_log_outcomes(), {})


if __name__ == "__main__":
    unittest.main()
