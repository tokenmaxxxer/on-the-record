#!/usr/bin/env python3
"""issue #521 — validate the 6 batch-1 roles/specs/*.spec.json against the
#515 realization template shape (docs/specs/role-spec-template.schema.json,
checked by gates/role_spec_shape.py).

  python3 -m pytest gates/ -q -k "spec"
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import role_spec_shape

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "roles" / "specs"

BATCH1_ROLES = (
    "execution-observation",
    "conformance-review",
    "defect-verification",
    "security-threat-model",
    "accessibility",
    "secure-coding",
)


def test_batch1_spec_files_exist():
    for role in BATCH1_ROLES:
        assert (SPECS_DIR / f"{role}.spec.json").is_file(), f"missing spec: {role}"


def test_batch1_specs_pass_shape_check():
    bad = []
    for role in BATCH1_ROLES:
        path = SPECS_DIR / f"{role}.spec.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        reasons = role_spec_shape.check(spec)
        if reasons:
            bad.append(f"{path}: {reasons}")
    assert not bad, "\n".join(bad)


def test_batch1_specs_role_field_matches_filename():
    for role in BATCH1_ROLES:
        path = SPECS_DIR / f"{role}.spec.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert spec.get("role") == role, f"{path}: role field {spec.get('role')!r} != {role!r}"


def test_role_spec_shape_rejects_missing_loop_state_bucket():
    spec = {
        "role": "x",
        "source_standard": "x",
        "required_fields": [{"name": "a", "type": "string", "required": True}],
        "reference_resolution": {"rule": "x", "checked_by": "x"},
        "recomputation": {"rule": "x", "checked_by": "x"},
        "write_scope": [],
        "report_only": True,
        "loop_state": {"progress": [], "terminal": ["done"], "refusal": []},
        "use_when": {"board_condition": "x"},
    }
    assert role_spec_shape.check(spec), "missing 'error' bucket should fail the shape check"


_BASE_SPEC = {
    "role": "x",
    "source_standard": "x",
    "required_fields": [{"name": "a", "type": "string", "required": True}],
    "reference_resolution": {"rule": "x", "checked_by": "x"},
    "recomputation": {"rule": "x", "checked_by": "x"},
    "write_scope": [],
    "report_only": True,
    "loop_state": {"progress": [], "terminal": ["done"], "refusal": [], "error": []},
    "use_when": {"board_condition": "x"},
}


def test_role_spec_shape_playbook_refs_absent_is_legal():
    assert role_spec_shape.check(dict(_BASE_SPEC)) == []


def test_role_spec_shape_playbook_refs_valid_entry_passes():
    spec = dict(_BASE_SPEC)
    spec["playbook_refs"] = [
        {
            "axis": "control-selection",
            "repo": "tokenmaxxxer/ux-engineering-rulebook",
            "path": "playbook/control-selection.md",
            "section": "#field-type-to-control-mapping",
        }
    ]
    assert role_spec_shape.check(spec) == []


def test_role_spec_shape_playbook_refs_rejects_missing_field():
    spec = dict(_BASE_SPEC)
    spec["playbook_refs"] = [{"axis": "control-selection", "repo": "r", "path": "p"}]
    reasons = role_spec_shape.check(spec)
    assert any("section" in r for r in reasons)


def test_role_spec_shape_playbook_refs_rejects_non_array():
    spec = dict(_BASE_SPEC)
    spec["playbook_refs"] = "not-an-array"
    reasons = role_spec_shape.check(spec)
    assert any("playbook_refs must be an array" in r for r in reasons)
