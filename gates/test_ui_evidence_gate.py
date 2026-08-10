#!/usr/bin/env python3
"""issue-685 — `ui_evidence_gate.check_record`/`is_ui_facing` 단위테스트.

네트워크 없음, `changed_paths` 를 인자로 직접 넘겨 diff 스캔을 건너뛴다
(`test_acceptance_gate.py` 와 같은 관례: 순수 함수만 직접 검증).

  python3 gates/test_ui_evidence_gate.py
"""
from __future__ import annotations
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ui_evidence_gate

_PASS_RECORD = """---
verdict: pass
---

body
"""


def _norepo_root() -> Path:
    return Path(tempfile.mkdtemp())


def t_ui_touch_unit_only_refused():
    root = _norepo_root()
    bad = ui_evidence_gate.check_record(
        root, "docs/issue-685/reports/implementation.md",
        _PASS_RECORD + "\nprovenance: executed-unit\n",
        ["src/screens/Home.tsx"])
    assert bad, "UI-touching diff with only executed-unit should be refused"


def t_ui_touch_executed_live_allowed():
    root = _norepo_root()
    bad = ui_evidence_gate.check_record(
        root, "docs/issue-685/reports/implementation.md",
        _PASS_RECORD + "\nprovenance: executed-live — screenshot: "
        "docs/issue-685/_assets/home.png\n",
        ["src/screens/Home.tsx"])
    assert bad == [], f"executed-live with evidence should pass, got {bad}"


def t_non_ui_diff_unit_pass_allowed():
    root = _norepo_root()
    bad = ui_evidence_gate.check_record(
        root, "docs/issue-685/reports/implementation.md",
        _PASS_RECORD + "\nprovenance: executed-unit\n",
        ["gates/gates.py"])
    assert bad == [], f"non-UI diff should not require executed-live, got {bad}"


def t_no_declaration_screenlike_path_fallback_refused():
    root = _norepo_root()
    assert not (root / "docs" / "specs" / "ui-surfaces.md").exists()
    bad = ui_evidence_gate.check_record(
        root, "docs/issue-685/reports/implementation.md",
        _PASS_RECORD + "\nprovenance: executed-unit\n",
        ["app/components/Widget.jsx"])
    assert bad, ("no ui-surfaces.md declared but a screen-like path changed "
                 "should still fail-closed refuse")


def t_declared_none_suppresses_fallback():
    root = _norepo_root()
    specs = root / "docs" / "specs"
    specs.mkdir(parents=True)
    (specs / "ui-surfaces.md").write_text("## Globs\n\nnone\n")
    bad = ui_evidence_gate.check_record(
        root, "docs/issue-685/reports/implementation.md",
        _PASS_RECORD + "\nprovenance: executed-unit\n",
        ["app/components/Widget.jsx"])
    assert bad == [], f"'none' declaration should suppress fallback, got {bad}"


def t_non_pass_verdict_never_checked():
    root = _norepo_root()
    bad = ui_evidence_gate.check_record(
        root, "docs/issue-685/reports/implementation.md",
        "---\nverdict: fail\n---\n",
        ["src/screens/Home.tsx"])
    assert bad == [], "non-pass verdict should never trigger this gate"


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"ok  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
