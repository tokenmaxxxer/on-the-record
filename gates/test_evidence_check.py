#!/usr/bin/env python3
"""issue-2104 — evidence-pointer verifier: stamps + fail-open wiring.

Fast tier, no network; commands executed are only the read-only
allowlist against a temp repo root.

  python3 -m pytest gates/test_evidence_check.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import evidence_check as ec


@pytest.fixture()
def root():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        (p / "mod.py").write_text("line1\nline2\nline3\n")
        yield p


def t_valid_path_line_verified(root):
    assert ec.verify_path_pointer("mod.py:2", root) == "verified"
    assert ec.verify_path_pointer("mod.py", root) == "verified"


def t_nonexistent_path_or_out_of_range_line_failed(root):
    assert ec.verify_path_pointer("nope.py:1", root) == "failed"
    assert ec.verify_path_pointer("mod.py:99", root) == "failed"
    assert ec.verify_path_pointer("../outside.py", root) == "failed"


def t_allowlisted_cmd_runs_and_stamps(root):
    assert ec.verify_cmd_pointer("grep -q line2 mod.py", root) == "verified"
    assert ec.verify_cmd_pointer("grep -q absent mod.py", root) == "failed"
    assert ec.verify_cmd_pointer("test -f mod.py", root) == "verified"
    assert ec.verify_cmd_pointer("test -f nope.py", root) == "failed"


def t_disallowed_cmd_is_unverified_and_not_executed(root):
    marker = root / "pwned"
    assert ec.verify_cmd_pointer(f"touch {marker}", root) == "unverified-cmd"
    assert ec.verify_cmd_pointer("rm -rf mod.py", root) == "unverified-cmd"
    assert ec.verify_cmd_pointer("grep x mod.py; touch pwned", root) == "unverified-cmd"
    assert ec.verify_cmd_pointer("grep x $(rm mod.py)", root) == "unverified-cmd"
    assert not marker.exists()
    assert (root / "mod.py").exists()


def t_stamp_claims_covers_all_four_stamps(root):
    answer = (
        "The module has three lines. evidence: mod.py:3\n"
        "There is a phantom helper. evidence: ghost.py:10\n"
        "Grep confirms line2. evidence-cmd: grep -q line2 mod.py\n"
        "Trust me on this one.\n"
        "Danger claim. evidence-cmd: curl http://evil\n"
    )
    stamps = [s["stamp"] for s in ec.stamp_claims(answer, root)]
    assert stamps == ["verified", "failed", "verified", "no-evidence", "unverified-cmd"]


def t_stamp_summary_counts_and_names_failures(root):
    answer = "a evidence: mod.py:1\nb evidence: ghost.py:5\nc no pointer\n"
    s = ec.stamp_summary(answer, root)
    assert "verified:1" in s and "failed:1" in s and "no-evidence:1" in s
    assert "ghost.py:5" in s


def t_spawn_consult_suffix_fail_open(monkeypatch):
    """Verifier crash => fail-open suffix + ledger event; env flag off => skipped."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import spawn

    events = []
    monkeypatch.setattr(spawn, "ledger_write", lambda e: events.append(e) or Path("."))
    monkeypatch.setattr(spawn, "_evidence_stamp_summary",
                        lambda text, root: (_ for _ in ()).throw(RuntimeError("boom")))
    suffix = spawn._consult_evidence_suffix({"answer": "x"}, None)
    assert "fail-open" in suffix
    assert events and events[0]["event"] == "evidence_check_crash"

    monkeypatch.setenv("OTR_EVIDENCE_CHECK", "0")
    assert spawn._consult_evidence_suffix({"answer": "x"}, None) == ""


def t_spawn_consult_suffix_stamps(monkeypatch, root):
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import spawn

    monkeypatch.delenv("OTR_EVIDENCE_CHECK", raising=False)
    suffix = spawn._consult_evidence_suffix(
        {"answer": "claim evidence: mod.py:1"}, str(root))
    assert "verified:1" in suffix


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
