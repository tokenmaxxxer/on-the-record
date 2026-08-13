"""issue #1160 step 3 machinery: gates/need_detector.py tests. Hermetic —
every fixture tree is built under pytest's own `tmp_path`, no fixture repos
on disk outside it, no network, no shelling out (proposal's Constraints
section, mirroring test_quality_bar.py's pure-function convention)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import need_detector


BRAND_DESIGN_SPEC = {
    "role": "brand-design",
    "use_when": {
        "need_detector": {
            "present_patterns": ["**/*.tsx", "**/*.jsx"],
            "absent_patterns": ["design-tokens/*.json"],
        }
    },
}


def _write_spec(root: Path, name: str, spec: dict) -> None:
    d = root / "roles" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.spec.json").write_text(json.dumps(spec), encoding="utf-8")


def test_with_need_fixture_fires(tmp_path):
    # has a *.tsx file, no design-tokens/*.json -> present-AND-NOT-absent
    _write_spec(tmp_path, "brand-design", BRAND_DESIGN_SPEC)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Button.tsx").write_text("export const Button = () => null;")

    due = need_detector.needs_due(tmp_path)

    assert due == [{
        "role": "brand-design",
        "reason": "present pattern matched '**/*.tsx', no absent pattern matched",
    }]


def test_without_need_fixture_stays_silent(tmp_path):
    # same *.tsx file, but design-tokens/*.json now exists -> absent
    # pattern matches -> silent (false-positive bound)
    _write_spec(tmp_path, "brand-design", BRAND_DESIGN_SPEC)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Button.tsx").write_text("export const Button = () => null;")
    (tmp_path / "design-tokens").mkdir()
    (tmp_path / "design-tokens" / "colors.json").write_text("{}")

    due = need_detector.needs_due(tmp_path)

    assert due == []


def test_no_present_pattern_hit_stays_silent(tmp_path):
    # backend-only tree: no *.tsx/*.jsx at all -> present_patterns never
    # matches -> silent, unconditionally
    _write_spec(tmp_path, "brand-design", BRAND_DESIGN_SPEC)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "server.py").write_text("print('hello')")

    due = need_detector.needs_due(tmp_path)

    assert due == []


def test_spec_with_no_need_detector_is_ignored(tmp_path):
    _write_spec(tmp_path, "test-authoring", {"role": "test-authoring", "use_when": {}})
    (tmp_path / "anything.tsx").write_text("x")

    due = need_detector.needs_due(tmp_path)

    assert due == []


def test_load_need_detector_specs_returns_only_specs_carrying_need_detector(tmp_path):
    _write_spec(tmp_path, "brand-design", BRAND_DESIGN_SPEC)
    _write_spec(tmp_path, "test-authoring", {"role": "test-authoring", "use_when": {}})

    specs = need_detector.load_need_detector_specs(tmp_path)

    assert set(specs.keys()) == {"brand-design"}


def test_format_report_empty_when_no_role_due():
    assert need_detector.format_report([]) == []


def test_dotdot_pattern_never_escapes_target_root(tmp_path):
    # warrant-hunt finding (before-landing, stance 0): a spec-supplied
    # pattern containing ".." must never match paths outside target_root.
    target = tmp_path / "target"
    (target / "roles" / "specs").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("secret")
    spec = {
        "role": "brand-design",
        "use_when": {"need_detector": {
            "present_patterns": ["../outside/*.txt"],
            "absent_patterns": [],
        }},
    }
    (target / "roles" / "specs" / "brand-design.spec.json").write_text(json.dumps(spec))

    due = need_detector.needs_due(target)

    assert due == []


def test_format_report_lists_due_roles():
    due = [{"role": "brand-design", "reason": "present pattern matched '**/*.tsx', no absent pattern matched"}]
    lines = need_detector.format_report(due)
    assert lines[0].startswith("[needs-due]")
    assert "brand-design" in lines[1]
