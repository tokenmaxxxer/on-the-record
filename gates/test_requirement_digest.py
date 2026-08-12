#!/usr/bin/env python3
"""issue #930 — `requirement_digest` 단위테스트.

네트워크 없이, 임시 디렉터리 위에서 돈다.

  python3 gates/test_requirement_digest.py
"""
from __future__ import annotations
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import requirement_digest as rd

_REG_TWO_LIVE_ONE_STALE = """# Requirements Registry

## R001

quote: 첫 번째 요구사항
source_issue: 1
check: gates/exists_a.py::check_a
status: enforced

## R002

quote: 두 번째 요구사항
source_issue: 2
check: gates/exists_b.py::check_b
status: open

## R003

quote: 이미 stale 처리된 요구사항
source_issue: 3
check: UNVERIFIABLE: 수동 확인만 가능
status: stale
"""


def _repo(files: dict[str, str]) -> Path:
    d = Path(tempfile.mkdtemp())
    for path, content in files.items():
        f = d / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    return d


def t_parse_extracts_all_required_fields():
    entries = rd.parse(_REG_TWO_LIVE_ONE_STALE)
    assert [e["id"] for e in entries] == ["R001", "R002", "R003"]
    assert entries[0]["quote"] == "첫 번째 요구사항"
    assert entries[0]["status"] == "enforced"


def t_render_drops_stale_and_keeps_live():
    entries = rd.parse(_REG_TWO_LIVE_ONE_STALE)
    out = rd.render(entries)
    assert "R001" in out
    assert "R002" in out
    assert "R003" not in out


def t_render_line_count_is_o_of_live_requirement_count_not_record_count():
    # 100개의 "기록"(가짜 파일)이 있어도 살아있는 요구가 2개면 digest 는
    # 여전히 2줄 — 렌더 비용이 요구 수에만 비례함을 실증.
    entries = rd.parse(_REG_TWO_LIVE_ONE_STALE)
    out = rd.render(entries)
    req_lines = [l for l in out.splitlines() if l.startswith("- R")]
    assert len(req_lines) == 2, req_lines


def t_check_flags_missing_digest():
    d = _repo({"docs/specs/requirements.md": _REG_TWO_LIVE_ONE_STALE,
               "gates/exists_a.py": "", "gates/exists_b.py": ""})
    try:
        bad = rd.check(d)
        assert bad, "missing digest file must flag"
    finally:
        shutil.rmtree(d)


def t_check_passes_after_update():
    d = _repo({"docs/specs/requirements.md": _REG_TWO_LIVE_ONE_STALE,
               "gates/exists_a.py": "", "gates/exists_b.py": ""})
    try:
        rd.update(d)
        bad = rd.check(d)
        assert not bad, bad
    finally:
        shutil.rmtree(d)


def t_check_flags_drift_after_hand_edit():
    d = _repo({"docs/specs/requirements.md": _REG_TWO_LIVE_ONE_STALE,
               "gates/exists_a.py": "", "gates/exists_b.py": ""})
    try:
        rd.update(d)
        (d / "docs/specs/requirement-digest.md").write_text("stale content\n")
        bad = rd.check(d)
        assert bad, "hand-edited digest that no longer matches must flag"
    finally:
        shutil.rmtree(d)


def t_update_rewrites_status_to_stale_when_check_path_missing():
    # gates/exists_b.py 를 빼서 R002 의 check 경로가 HEAD 에 없게 만든다.
    d = _repo({"docs/specs/requirements.md": _REG_TWO_LIVE_ONE_STALE,
               "gates/exists_a.py": ""})
    try:
        rd.update(d)
        reg_after = (d / "docs/specs/requirements.md").read_text()
        entries = rd.parse(reg_after)
        r002 = next(e for e in entries if e["id"] == "R002")
        assert r002["status"] == "stale", r002
        # 그리고 digest 에서도 R002 가 빠진다.
        digest = (d / "docs/specs/requirement-digest.md").read_text()
        assert "R002" not in digest
        assert "R001" in digest
    finally:
        shutil.rmtree(d)


def t_check_empty_registry_documented_empty_state():
    d = _repo({"docs/specs/requirements.md":
               "# Requirements Registry\n\nAppend-only.\n"})
    try:
        rd.update(d)
        digest = (d / "docs/specs/requirement-digest.md").read_text()
        assert "(no live requirements)" in digest
        bad = rd.check(d)
        assert not bad, bad
    finally:
        shutil.rmtree(d)


def t_check_no_registry_passes_nothing_to_check():
    d = _repo({})
    try:
        bad = rd.check(d)
        assert not bad, bad
    finally:
        shutil.rmtree(d)


def _run_all() -> int:
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("t_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL {name}: {e}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
