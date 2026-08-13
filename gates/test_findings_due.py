"""issue-1202 requirement 4 — findings-due board-reading integration.

Same integration-test style as `gates/test_need_detector.py` /
`gates/test_roles_due.py`: pure classifier + formatter, no network.

  python3 gates/test_findings_due.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import findings_due

_FINDING = """---
role: coding
date: 2026-08-13
domain_rule: playbook.md#error-handling
target_repo: /tmp/fixture
---

## Evidence
src/x.py:1

## Impact
bad

## Proposed direction
fix it
"""

_RELAYED_FINDING = _FINDING.replace(
    "target_repo: /tmp/fixture\n", "target_repo: /tmp/fixture\nrelayed_to_issue: 42\n")


def test_findings_due_empty_when_no_findings_dir():
    with tempfile.TemporaryDirectory() as d:
        assert findings_due.findings_due(Path(d)) == []
        assert findings_due.format_report([]) == []


def test_findings_due_lists_un_relayed_finding():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "docs" / "reports" / "findings" / "coding"
        role_dir.mkdir(parents=True)
        (role_dir / "2026-08-13-slug.md").write_text(_FINDING, encoding="utf-8")

        due = findings_due.findings_due(root)
        assert len(due) == 1
        assert due[0]["role"] == "coding"
        assert due[0]["domain_rule"] == "playbook.md#error-handling"

        lines = findings_due.format_report(due)
        assert any("coding" in line for line in lines)


def test_findings_due_skips_relayed_finding():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "docs" / "reports" / "findings" / "coding"
        role_dir.mkdir(parents=True)
        (role_dir / "2026-08-13-slug.md").write_text(_RELAYED_FINDING, encoding="utf-8")
        assert findings_due.findings_due(root) == []


def test_findings_due_skips_session_summary_files():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "docs" / "reports" / "findings" / "coding"
        role_dir.mkdir(parents=True)
        (role_dir / "2026-08-13-session-summary.md").write_text(
            "- 2 further findings observed, not filed (session bound N=3)\n",
            encoding="utf-8")
        assert findings_due.findings_due(root) == []


def test_findings_due_reads_per_issue_variant():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "docs" / "issue-1202" / "reports" / "findings" / "coding"
        role_dir.mkdir(parents=True)
        (role_dir / "2026-08-13-slug.md").write_text(_FINDING, encoding="utf-8")
        due = findings_due.findings_due(root)
        assert len(due) == 1
        assert due[0]["path"].startswith("docs/issue-1202/")


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    _run(tests)
