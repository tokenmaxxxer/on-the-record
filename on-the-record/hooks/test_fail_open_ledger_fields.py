"""issue #2962: the fail-open ledger records the hook's exit status and
whether the fallback (visible in-band notice) fired as fields distinct
from any success indication -- one string merging "wrapper survived" with
"hook succeeded" is why this was unobservable in the first place.

    python3 -m pytest on-the-record/hooks/ -k fail_open_ledger_fields -q
"""
from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))
import hook_ledger  # noqa: E402

WRAPPER = HOOKS_DIR / "fail-open-wrapper.sh"
INVARIANT_INJECTING_WRAPPED = sorted(
    r["script"]
    for r in json.loads((HOOKS_DIR / "hook_classification.json").read_text())["registrations"]
    if r["wrapped"] and r["class"] == "invariant-injecting"
)
OBSERVABILITY_WRAPPED = sorted(
    r["script"]
    for r in json.loads((HOOKS_DIR / "hook_classification.json").read_text())["registrations"]
    if r["wrapped"] and r["class"] == "observability"
)


def _read_ledger_lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


class LedgerSchemaUnitTest(unittest.TestCase):
    """Direct unit tests of hook_ledger.record_fail_open, bypassing the
    shell wrapper -- the schema is what acceptance checks, per the
    issue's own stated empty state ('an empty ledger passes')."""

    def test_empty_ledger_passes_no_entries_no_error(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "fail-open.jsonl"
            self.assertEqual(_read_ledger_lines(path), [])

    def test_recorded_entry_carries_exit_code_and_fallback_fired_as_distinct_fields(self):
        with tempfile.TemporaryDirectory() as td:
            ledger_path = Path(td) / "fail-open.jsonl"
            import os
            old = os.environ.get("OTR_FAIL_OPEN_LEDGER")
            os.environ["OTR_FAIL_OPEN_LEDGER"] = str(ledger_path)
            try:
                ok = hook_ledger.record_fail_open(
                    "directive.sh", argv=["directive.sh"], digest="sha256:abc",
                    exit_code=1, reason="nonzero-exit", fallback_fired=True,
                )
                lines = _read_ledger_lines(ledger_path)
            finally:
                if old is None:
                    os.environ.pop("OTR_FAIL_OPEN_LEDGER", None)
                else:
                    os.environ["OTR_FAIL_OPEN_LEDGER"] = old
        self.assertTrue(ok)
        self.assertEqual(len(lines), 1)
        entry = lines[0]
        # exit_code and fallback_fired must both be present, independently
        # inspectable, and neither may be folded into a "success" string.
        self.assertIn("exit_code", entry)
        self.assertIn("fallback_fired", entry)
        self.assertEqual(entry["exit_code"], 1)
        self.assertIs(entry["fallback_fired"], True)
        self.assertNotIn("success", entry)
        for v in entry.values():
            if isinstance(v, str):
                self.assertNotIn("success", v.lower())

    def test_fallback_fired_defaults_false_when_not_passed(self):
        with tempfile.TemporaryDirectory() as td:
            ledger_path = Path(td) / "fail-open.jsonl"
            import os
            old = os.environ.get("OTR_FAIL_OPEN_LEDGER")
            os.environ["OTR_FAIL_OPEN_LEDGER"] = str(ledger_path)
            try:
                hook_ledger.record_fail_open(
                    "self-update.sh", exit_code=1, reason="nonzero-exit",
                )
                entry = _read_ledger_lines(ledger_path)[0]
            finally:
                if old is None:
                    os.environ.pop("OTR_FAIL_OPEN_LEDGER", None)
                else:
                    os.environ["OTR_FAIL_OPEN_LEDGER"] = old
        self.assertIs(entry["fallback_fired"], False)


class LedgerEndToEndTest(unittest.TestCase):
    """Runs the real wrapper end to end and inspects the JSONL it writes."""

    def _run_and_read_ledger(self, hook_name: str, body: str) -> dict:
        with tempfile.TemporaryDirectory() as td:
            hook = Path(td) / hook_name
            hook.write_text(f"#!/bin/sh\n{body}\n")
            hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
            ledger_path = Path(td) / "fail-open.jsonl"
            subprocess.run(
                [str(WRAPPER), str(hook)],
                input="", capture_output=True, text=True, timeout=10,
                env={"PATH": "/usr/bin:/bin",
                     "OTR_FAIL_OPEN_LEDGER": str(ledger_path)},
            )
            lines = _read_ledger_lines(ledger_path)
        self.assertEqual(len(lines), 1, lines)
        return lines[0]

    def test_invariant_injecting_crash_records_fallback_fired_true(self):
        name = INVARIANT_INJECTING_WRAPPED[0]
        entry = self._run_and_read_ledger(name, "exit 1")
        self.assertEqual(entry["exit_code"], 1)
        self.assertIs(entry["fallback_fired"], True)

    def test_observability_crash_records_fallback_fired_false(self):
        name = OBSERVABILITY_WRAPPED[0]
        entry = self._run_and_read_ledger(name, "exit 1")
        self.assertEqual(entry["exit_code"], 1)
        self.assertIs(entry["fallback_fired"], False)


if __name__ == "__main__":
    unittest.main()
