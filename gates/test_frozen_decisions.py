#!/usr/bin/env python3
"""issue-2104 — frozen-decision registry: parse round-trip + repo lint.

Fast tier, no network (same convention as gates/test_acceptance_gate.py).

  python3 -m pytest gates/test_frozen_decisions.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import frozen_decisions as fd


def t_repo_registry_lints_clean():
    errors = fd.lint_registry()
    assert errors == [], f"docs/decisions registry lint failed: {errors}"


def t_known_frozen_principles_are_registered():
    ids = {d.decision_id for d in fd.frozen_decisions()}
    assert "single-skill-axis" in ids
    assert "single-enforcement-surface" in ids
    for d in fd.frozen_decisions():
        assert d.has_scope, f"{d.decision_id}: frozen without scope"


def t_front_matter_round_trip():
    meta = {
        "id": "example-frozen",
        "status": "frozen",
        "scope": {"globs": ["roles/**", "hooks/*.sh"], "keywords": ["role manifest"]},
    }
    text = fd.dump_front_matter(meta) + "\n# Example\n"
    parsed = fd.parse_front_matter(text)
    assert parsed == meta


def t_no_front_matter_is_none_and_a_lint_error():
    assert fd.parse_front_matter("# just a title\n") is None
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.md").write_text("# no front matter\n")
        errors = fd.lint_registry(Path(td))
        assert len(errors) == 1 and "missing front-matter" in errors[0]


def t_frozen_without_scope_fails_lint():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "f.md").write_text("---\nid: x\nstatus: frozen\n---\n# X\n")
        errors = fd.lint_registry(Path(td))
        assert any("frozen but scope is empty" in e for e in errors)


def t_bad_status_and_unterminated_block_fail_lint():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.md").write_text("---\nid: a\nstatus: landed\n---\n")
        (Path(td) / "b.md").write_text("---\nid: b\nstatus: active\n")  # no closing ---
        errors = fd.lint_registry(Path(td))
        assert any("not in frozen/active/superseded" in e for e in errors)
        assert any("unterminated" in e for e in errors)


def t_duplicate_id_fails_lint():
    with tempfile.TemporaryDirectory() as td:
        for name in ("a.md", "b.md"):
            (Path(td) / name).write_text("---\nid: same\nstatus: active\n---\n")
        errors = fd.lint_registry(Path(td))
        assert any("duplicate id" in e for e in errors)


def t_readme_is_excluded_from_registry():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "README.md").write_text("# no front matter, on purpose\n")
        (Path(td) / "a.md").write_text("---\nid: a\nstatus: active\n---\n")
        assert fd.lint_registry(Path(td)) == []
        assert [d.decision_id for d in fd.load_registry(Path(td))] == ["a"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
