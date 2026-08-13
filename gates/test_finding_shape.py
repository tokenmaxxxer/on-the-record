"""issue-1202 requirement 2/3 — finding shape gate + rate bound.

Hermetic: tempfile fixtures only, no network/GitHub (`gates/test_acceptance_gate.py`
convention).

  python3 gates/test_finding_shape.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import finding_shape

_GOOD = """---
role: coding
date: 2026-08-13
domain_rule: playbook.md#error-handling — "never swallow an exception silently"
target_repo: /tmp/fixture-repo
---

## Evidence
src/handler.py:42 — bare `except: pass`

## Impact
Failures in the request path are invisible; on-call has no signal.

## Proposed direction
Log the exception with cause before continuing, or let it propagate.
"""


def test_finding_shape_accepts_complete_finding():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "2026-08-13-swallowed-exception.md"
        p.write_text(_GOOD, encoding="utf-8")
        assert finding_shape.check_finding(p) == []


def test_finding_shape_rejects_missing_domain_rule():
    bad = _GOOD.replace("domain_rule: playbook.md#error-handling"
                         ' — "never swallow an exception silently"\n', "")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "f.md"
        p.write_text(bad, encoding="utf-8")
        reasons = finding_shape.check_finding(p)
        assert any("domain_rule" in r for r in reasons)


def test_finding_shape_rejects_missing_evidence_section():
    bad = _GOOD.replace(
        "## Evidence\nsrc/handler.py:42 — bare `except: pass`\n\n", "")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "f.md"
        p.write_text(bad, encoding="utf-8")
        reasons = finding_shape.check_finding(p)
        assert any("Evidence" in r for r in reasons)


def test_finding_shape_rejects_empty_evidence_section():
    bad = _GOOD.replace(
        "src/handler.py:42 — bare `except: pass`", "")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "f.md"
        p.write_text(bad, encoding="utf-8")
        reasons = finding_shape.check_finding(p)
        assert any("Evidence" in r for r in reasons)


def test_finding_shape_rejects_missing_file():
    reasons = finding_shape.check_finding("/nonexistent/path/f.md")
    assert reasons and "does not exist" in reasons[0]


def _finding_with_session(session: str) -> str:
    return _GOOD.replace(
        "domain_rule: playbook.md#error-handling"
        ' — "never swallow an exception silently"\n',
        "domain_rule: playbook.md#error-handling"
        ' — "never swallow an exception silently"\n'
        f"session: {session}\n",
    )


def test_rate_bound_allows_under_bound():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "coding"
        role_dir.mkdir()
        for i in range(2):
            (role_dir / f"2026-08-13-finding-{i}.md").write_text(
                _finding_with_session("sess-a"), encoding="utf-8")
        assert finding_shape.check_rate_bound(root, "coding", "sess-a", bound=3) is None


def test_rate_bound_rejects_fourth_finding_with_summary_path():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "coding"
        role_dir.mkdir()
        for i in range(3):
            (role_dir / f"2026-08-13-finding-{i}.md").write_text(
                _finding_with_session("sess-a"), encoding="utf-8")
        reason = finding_shape.check_rate_bound(root, "coding", "sess-a", bound=3)
        assert reason is not None
        assert "session-summary" in reason


def test_rate_bound_is_per_session_not_cumulative():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "coding"
        role_dir.mkdir()
        for i in range(3):
            (role_dir / f"2026-08-13-finding-{i}.md").write_text(
                _finding_with_session("sess-a"), encoding="utf-8")
        # A different session_id is still under bound, even though the
        # standing queue already holds 3 findings for this role.
        assert finding_shape.check_rate_bound(root, "coding", "sess-b", bound=3) is None


def test_rate_bound_ignores_session_summary_files():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        role_dir = root / "coding"
        role_dir.mkdir()
        (role_dir / "2026-08-13-session-summary.md").write_text(
            "- 2 further findings observed, not filed (session bound N=3)\n",
            encoding="utf-8")
        assert finding_shape.check_rate_bound(root, "coding", "sess-a", bound=3) is None


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
