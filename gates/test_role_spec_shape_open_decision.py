#!/usr/bin/env python3
"""issue #609 (implementation phase 2) — validate the `open_decision_item`
shape addition to role_spec_shape.py (check_open_decision_item) and the
requirements-engineering.spec.json field it enables, per new-batch-file
convention (never edit an existing test_role_spec_shape_batch*.py file).

  python3 -m pytest gates/test_role_spec_shape_open_decision.py -q
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import role_spec_shape

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "roles" / "specs"

_VALID_ENTRY = {
    "item": "should ambiguous EARS statements auto-escalate",
    "source_role": "requirements-engineering",
    "source_path": "docs/issue-609/reports/requirements-engineering.md",
    "candidate_axes": ["alignment"],
}


def test_valid_entry_passes():
    assert role_spec_shape.check_open_decision_item(_VALID_ENTRY) == []


def test_missing_item_fails():
    entry = dict(_VALID_ENTRY)
    del entry["item"]
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("item must be a non-empty string" in r for r in reasons)


def test_empty_item_fails():
    entry = dict(_VALID_ENTRY, item="")
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("item must be a non-empty string" in r for r in reasons)


def test_missing_source_role_fails():
    entry = dict(_VALID_ENTRY)
    del entry["source_role"]
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("source_role must be a non-empty string" in r for r in reasons)


def test_missing_source_path_fails():
    entry = dict(_VALID_ENTRY)
    del entry["source_path"]
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("source_path must be a non-empty string" in r for r in reasons)


def test_candidate_axes_missing_fails():
    entry = dict(_VALID_ENTRY)
    del entry["candidate_axes"]
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("candidate_axes must be a non-empty array" in r for r in reasons)


def test_candidate_axes_empty_fails():
    entry = dict(_VALID_ENTRY, candidate_axes=[])
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("candidate_axes must be a non-empty array" in r for r in reasons)


def test_candidate_axes_unknown_entry_fails():
    entry = dict(_VALID_ENTRY, candidate_axes=["not-a-real-axis"])
    reasons = role_spec_shape.check_open_decision_item(entry)
    assert any("not in" in r for r in reasons)


def test_entry_not_a_dict_fails():
    reasons = role_spec_shape.check_open_decision_item("nope")
    assert reasons == ["open_decision_item entry is not an object"]


def test_requirements_engineering_spec_carries_field_and_still_passes_shape_check():
    path = SPECS_DIR / "requirements-engineering.spec.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    names = [f["name"] for f in spec["required_fields"]]
    assert "open_decision_item" in names
    field = next(f for f in spec["required_fields"] if f["name"] == "open_decision_item")
    assert field["type"] == "ref[]"
    assert field["required"] is False
    assert role_spec_shape.check(spec) == []


if __name__ == "__main__":
    import inspect
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and inspect.isfunction(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
