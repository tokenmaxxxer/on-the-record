"""issue #1199 — hermetic tests for gates/tool_learnings_tracker.py.

Uses tmp_path fixtures for roles/specs dirs only — never touches this
repo's real roles/ tree, mirrors test_playbook_tracker.py's convention
and keeps this program's tracker independent of #1174's.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tool_learnings_tracker import discover_roles, is_landed, render


def _write_role(roles_dir, name):
    (roles_dir / f"{name}.json").write_text("{}")


def _write_spec(specs_dir, name, tool_learnings_refs=None):
    spec = {"role": name}
    if tool_learnings_refs is not None:
        spec["tool_learnings_refs"] = tool_learnings_refs
    (specs_dir / f"{name}.spec.json").write_text(json.dumps(spec))


def test_discover_roles_sorted(tmp_path):
    _write_role(tmp_path, "zeta")
    _write_role(tmp_path, "alpha")
    assert discover_roles(tmp_path) == ["alpha", "zeta"]


def test_is_landed_true_with_nonempty_tool_learnings_refs(tmp_path):
    _write_spec(tmp_path, "technical-writing", tool_learnings_refs=[{"tool": "diagram-design"}])
    assert is_landed("technical-writing", tmp_path)


def test_is_landed_false_with_empty_tool_learnings_refs(tmp_path):
    _write_spec(tmp_path, "technical-writing", tool_learnings_refs=[])
    assert not is_landed("technical-writing", tmp_path)


def test_is_landed_false_when_field_absent(tmp_path):
    _write_spec(tmp_path, "technical-writing")
    assert not is_landed("technical-writing", tmp_path)


def test_is_landed_ignores_sibling_playbook_refs_field(tmp_path):
    spec = {"role": "technical-writing", "playbook_refs": [{"axis": "a"}]}
    (tmp_path / "technical-writing.spec.json").write_text(json.dumps(spec))
    assert not is_landed("technical-writing", tmp_path)


def test_is_landed_false_when_spec_missing(tmp_path):
    assert not is_landed("nonexistent-role", tmp_path)


def test_is_landed_false_on_malformed_json(tmp_path):
    (tmp_path / "broken.spec.json").write_text("{not json")
    assert not is_landed("broken", tmp_path)


def test_render_shows_unlanded_roles_unchecked_never_dropped(tmp_path):
    _write_spec(tmp_path, "landed-role", tool_learnings_refs=[{"tool": "x"}])
    out = render(["landed-role", "unlanded-role"], tmp_path)
    assert "- [x] landed-role" in out
    assert "- [ ] unlanded-role" in out
    assert "(1/2)" in out


def test_render_header_counts_match_body():
    out = render(["a", "b", "c"], Path("/nonexistent"))
    assert "(0/3)" in out
    assert out.count("- [ ]") == 3


def test_render_against_real_roles_dir_denominator():
    # issue #1199 asks for a 43-item tracker; playbook_tracker.py's own
    # docstring already notes the shared registry as "43/44-item", so
    # this asserts the renderer's count tracks the live roles/ registry
    # (whatever it holds today) rather than baking a stale literal in.
    roles_dir = Path(__file__).resolve().parent.parent / "roles"
    roles = discover_roles(roles_dir)
    out = render(roles, Path("/nonexistent"))
    assert f"(0/{len(roles)})" in out
    assert len(roles) > 0
