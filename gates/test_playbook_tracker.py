"""issue #1174 — hermetic tests for gates/playbook_tracker.py.

Uses tmp_path fixtures for roles/specs dirs only — never touches this
repo's real roles/ tree, so a role landing mid-program can't flip these
assertions.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from playbook_tracker import discover_roles, is_landed, render


def _write_role(roles_dir, name):
    (roles_dir / f"{name}.json").write_text("{}")


def _write_spec(specs_dir, name, playbook_refs=None):
    spec = {"role": name}
    if playbook_refs is not None:
        spec["playbook_refs"] = playbook_refs
    (specs_dir / f"{name}.spec.json").write_text(json.dumps(spec))


def test_discover_roles_sorted(tmp_path):
    _write_role(tmp_path, "zeta")
    _write_role(tmp_path, "alpha")
    assert discover_roles(tmp_path) == ["alpha", "zeta"]


def test_is_landed_true_with_nonempty_playbook_refs(tmp_path):
    _write_spec(tmp_path, "ux-engineering", playbook_refs=[{"axis": "a"}])
    assert is_landed("ux-engineering", tmp_path)


def test_is_landed_false_with_empty_playbook_refs(tmp_path):
    _write_spec(tmp_path, "ux-engineering", playbook_refs=[])
    assert not is_landed("ux-engineering", tmp_path)


def test_is_landed_false_when_field_absent(tmp_path):
    _write_spec(tmp_path, "ux-engineering")
    assert not is_landed("ux-engineering", tmp_path)


def test_is_landed_false_when_spec_missing(tmp_path):
    assert not is_landed("nonexistent-role", tmp_path)


def test_is_landed_false_on_malformed_json(tmp_path):
    (tmp_path / "broken.spec.json").write_text("{not json")
    assert not is_landed("broken", tmp_path)


def test_render_shows_unlanded_roles_unchecked_never_dropped(tmp_path):
    _write_spec(tmp_path, "landed-role", playbook_refs=[{"axis": "a"}])
    out = render(["landed-role", "unlanded-role"], tmp_path)
    assert "- [x] landed-role" in out
    assert "- [ ] unlanded-role" in out
    assert "(1/2)" in out


def test_render_header_counts_match_body():
    out = render(["a", "b", "c"], Path("/nonexistent"))
    assert "(0/3)" in out
    assert out.count("- [ ]") == 3
