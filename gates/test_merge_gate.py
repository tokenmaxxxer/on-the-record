#!/usr/bin/env python3
"""issue #3057 — `merge_gate.main()`'s exit code must distinguish allow,
refuse, and could-not-decide (a crash inside `evaluate()`). Before this
issue, refuse and an uncaught exception both surfaced as rc=1 (the
refusal via an explicit `return 1`, the crash via Python's default
handler for an uncaught exception) -- a caller branching on `$?` could
not tell them apart. These tests pin `main()`'s three-way split without
depending on a live PR's real verdict, which drifts.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gates"))
import merge_gate  # noqa: E402


def test_allowed_verdict_exits_zero(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["merge_gate.py", "1", "issue-1"])
    monkeypatch.setattr(merge_gate, "evaluate",
                         lambda root, repo, pr, subject: {"allowed": True, "reasons": []})

    rc = merge_gate.main()

    assert rc == merge_gate.EXIT_ALLOWED == 0


def test_refused_verdict_exits_one(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["merge_gate.py", "1", "issue-1"])
    monkeypatch.setattr(
        merge_gate, "evaluate",
        lambda root, repo, pr, subject: {"allowed": False, "reasons": ["some reason"]})

    rc = merge_gate.main()

    assert rc == merge_gate.EXIT_REFUSED == 1


def test_internal_failure_exits_two_not_zero_not_one(monkeypatch, capsys):
    """must-not (issue #3057): a crash inside `evaluate()` must not be
    caught-and-continued into a fabricated verdict -- it must abort with
    a distinct, non-zero code the caller can never confuse with
    `EXIT_REFUSED`."""
    monkeypatch.setattr(sys, "argv", ["merge_gate.py", "1", "issue-1"])

    def _boom(root, repo, pr, subject):
        raise AttributeError("module 'gates' has no attribute 'record_frontmatter'")

    monkeypatch.setattr(merge_gate, "evaluate", _boom)

    rc = merge_gate.main()

    assert rc == merge_gate.EXIT_COULD_NOT_DECIDE == 2
    assert rc not in (merge_gate.EXIT_ALLOWED, merge_gate.EXIT_REFUSED)
    out = capsys.readouterr()
    # the traceback is printed (to stderr, via traceback.print_exc()), not
    # swallowed -- "must not catch the AttributeError and continue" means
    # the failure stays visible.
    assert "AttributeError" in out.err
    assert "record_frontmatter" in out.err


def test_bad_pr_argument_is_could_not_decide_not_refused(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["merge_gate.py", "not-a-number", "issue-1"])

    rc = merge_gate.main()

    assert rc == merge_gate.EXIT_COULD_NOT_DECIDE == 2
