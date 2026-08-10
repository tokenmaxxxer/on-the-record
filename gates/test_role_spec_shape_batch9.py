#!/usr/bin/env python3
"""issue #573 (implementation phase 2) — validate the judgment_axes/
axis_evaluation shape additions to role_spec_shape.py: the two seeded
roles' roles/*.json + roles/specs/*.spec.json still pass the existing
shape check with the new field present, plus the new checker functions
(check_role_judgment_axes, check_axis_ownership, check_axis_evaluation_entry)
directly, including their rejection paths.

  python3 -m pytest gates/ -q -k "batch9"
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import role_spec_shape

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "roles" / "specs"
ROLES_DIR = ROOT / "roles"

BATCH9_ROLES = ("architecture", "security-threat-model")

_OWNED_AXIS = {
    "architecture": "maintenance_complexity",
    "security-threat-model": "attack_potential",
}

_WRITE_SCOPES = {
    "architecture": ["docs/decisions/*.md", "docs/issue-<n>/reports/architecture.md"],
    "security-threat-model": ["docs/issue-<n>/reports/security-threat-model.md"],
    "delegated-judgment-gate": ["on-the-record/hooks/*.sh"],
}


def test_batch9_role_files_exist():
    for role in BATCH9_ROLES:
        assert (ROLES_DIR / f"{role}.json").is_file(), f"missing role: {role}"
        assert (SPECS_DIR / f"{role}.spec.json").is_file(), f"missing spec: {role}"


def test_batch9_specs_still_pass_shape_check_with_axis_evaluation():
    bad = []
    for role in BATCH9_ROLES:
        path = SPECS_DIR / f"{role}.spec.json"
        spec = json.loads(path.read_text(encoding="utf-8"))
        reasons = role_spec_shape.check(spec)
        if reasons:
            bad.append(f"{path}: {reasons}")
    assert not bad, "\n".join(bad)


def test_batch9_roles_carry_judgment_axes_and_pass_check():
    for role in BATCH9_ROLES:
        cfg = json.loads((ROLES_DIR / f"{role}.json").read_text(encoding="utf-8"))
        assert cfg.get("judgment_axes") == [_OWNED_AXIS[role]]
        assert role_spec_shape.check_role_judgment_axes(cfg) == []


def test_batch9_judgment_axes_rejects_unknown_axis():
    reasons = role_spec_shape.check_role_judgment_axes({"judgment_axes": ["not-a-real-axis"]})
    assert reasons and "not in" in reasons[0]


def test_batch9_judgment_axes_absent_is_not_an_error():
    assert role_spec_shape.check_role_judgment_axes({}) == []


def test_batch9_axis_ownership_passes_for_seeded_roles():
    roles = {role: json.loads((ROLES_DIR / f"{role}.json").read_text(encoding="utf-8"))
             for role in BATCH9_ROLES}
    reasons = role_spec_shape.check_axis_ownership(roles)
    assert not any("owned by more than one role" in r for r in reasons)
    for role, axis in _OWNED_AXIS.items():
        assert not any(f"axis {axis!r} owned by zero roles" == r for r in reasons)


def test_batch9_axis_ownership_rejects_duplicate_owner():
    roles = {
        "architecture": {"judgment_axes": ["maintenance_complexity"]},
        "impostor": {"judgment_axes": ["maintenance_complexity"]},
    }
    reasons = role_spec_shape.check_axis_ownership(roles)
    assert any("more than one role" in r for r in reasons)


def test_batch9_axis_evaluation_supports_entry_is_valid():
    entry = {"axis": "maintenance_complexity", "verdict": "supports",
              "citation": "docs/product/priorities.md#p1"}
    assert role_spec_shape.check_axis_evaluation_entry(
        entry, ["maintenance_complexity"], _WRITE_SCOPES) == []


def test_batch9_axis_evaluation_contradicts_requires_finding():
    entry = {"axis": "maintenance_complexity", "verdict": "contradicts",
              "citation": "docs/product/priorities.md#p1"}
    reasons = role_spec_shape.check_axis_evaluation_entry(
        entry, ["maintenance_complexity"], _WRITE_SCOPES)
    assert any("finding is required" in r for r in reasons)


def test_batch9_axis_evaluation_contradicts_with_valid_finding_passes():
    entry = {
        "axis": "maintenance_complexity", "verdict": "contradicts",
        "citation": "docs/product/priorities.md#p1",
        "finding": {
            "target_path": "on-the-record/hooks/delegated-judgment-gate.sh",
            "required_fix": "register the hook in hooks.json",
        },
    }
    assert role_spec_shape.check_axis_evaluation_entry(
        entry, ["maintenance_complexity"], _WRITE_SCOPES) == []


def test_batch9_axis_evaluation_finding_target_path_must_resolve_write_scope():
    entry = {
        "axis": "maintenance_complexity", "verdict": "contradicts",
        "citation": "docs/product/priorities.md#p1",
        "finding": {"target_path": "nowhere/unowned.py", "required_fix": "fix it"},
    }
    reasons = role_spec_shape.check_axis_evaluation_entry(
        entry, ["maintenance_complexity"], _WRITE_SCOPES)
    assert any("does not resolve against any role's write_scope" in r for r in reasons)


def test_batch9_axis_evaluation_finding_forbidden_when_not_contradicting():
    entry = {
        "axis": "maintenance_complexity", "verdict": "supports",
        "citation": "docs/product/priorities.md#p1",
        "finding": {"target_path": "x", "required_fix": "y"},
    }
    reasons = role_spec_shape.check_axis_evaluation_entry(
        entry, ["maintenance_complexity"], _WRITE_SCOPES)
    assert any("must be absent" in r for r in reasons)


def test_batch9_axis_evaluation_rejects_axis_not_owned_by_role():
    entry = {"axis": "attack_potential", "verdict": "supports",
              "citation": "docs/product/priorities.md#p1"}
    reasons = role_spec_shape.check_axis_evaluation_entry(
        entry, ["maintenance_complexity"], _WRITE_SCOPES)
    assert any("not in this role's judgment_axes" in r for r in reasons)


def test_batch9_axis_ownership_rejects_zero_owner():
    roles = {
        "architecture": {"judgment_axes": ["maintenance_complexity"]},
        "security-threat-model": {"judgment_axes": ["attack_potential"]},
    }
    reasons = role_spec_shape.check_axis_ownership(roles)
    assert any("owned by zero roles" in r for r in reasons)


def test_batch9_roles_dir_cli_passes_when_all_five_axes_owned(tmp_path):
    roles = {
        "architecture": {"judgment_axes": ["maintenance_complexity"]},
        "security-threat-model": {"judgment_axes": ["attack_potential"]},
        "conformance-review": {"judgment_axes": ["alignment"]},
        "capacity-planning": {"judgment_axes": ["external_burden"]},
        "performance-engineering": {"judgment_axes": ["performance"]},
    }
    for name, cfg in roles.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(cfg), encoding="utf-8")
    assert role_spec_shape.main(["--roles-dir", str(tmp_path)]) == 0


def test_batch9_roles_dir_cli_fails_when_one_role_missing(tmp_path):
    roles = {
        "architecture": {"judgment_axes": ["maintenance_complexity"]},
        "security-threat-model": {"judgment_axes": ["attack_potential"]},
        "conformance-review": {"judgment_axes": ["alignment"]},
        "capacity-planning": {"judgment_axes": ["external_burden"]},
    }
    for name, cfg in roles.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(cfg), encoding="utf-8")
    assert role_spec_shape.main(["--roles-dir", str(tmp_path)]) == 1


if __name__ == "__main__":
    import inspect
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_batch9") and inspect.isfunction(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
