"""Regression tests for scripts/measure_skill_invocation.py's `analyze()`
(issue #3288: a decoy-design arm mounting its skill from a one-off temp
root -- e.g. /tmp/consumer-path-on-skills-<x> -- was measured as
`mounted: []`, indistinguishable from a failed observation, because the
old `mounted` filter matched only the literal substring
'/skill-registry/skills/'. Both consumer-path arms (issue #3245's decoy
design, PR #3280/round 8) mount from such a temp root, never that literal
path, so this was not a corner case -- it was every real run.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "measure_skill_invocation", ROOT / "scripts" / "measure_skill_invocation.py")
msi = importlib.util.module_from_spec(spec)
sys.modules["measure_skill_invocation"] = msi
spec.loader.exec_module(msi)


def _write_log(tmp_path, lines):
    path = tmp_path / "fake.session.20260101T000000.123.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _init_line(plugins):
    return json.dumps({"type": "system", "subtype": "init", "plugins": plugins},
                       separators=(",", ":"))


def _skill_call_line(skill_name):
    return ('[{"type":"tool_use","name":"Skill","input":'
            f'{{"skill":"{skill_name}"}}}}]')


def test_temp_root_mount_is_measured_not_empty(tmp_path):
    """The core regression: a plugin mounted from a temp root outside
    /skill-registry must show up in `mounted`, not be silently dropped
    into an empty list that reads as "nothing was mounted"."""
    temp_root = "/tmp/consumer-path-on-skills-abc123"
    plugins = [
        {"name": "core", "path": "/home/user/.claude/plugins/marketplaces/x/core"},
        {"name": "my-skill", "path": f"{temp_root}/my-skill"},
    ]
    log = _write_log(tmp_path, [
        _init_line(plugins),
        _skill_call_line("my-skill"),
    ])

    result = msi.analyze("fake", str(log), skills_root=temp_root)

    assert result["status"] == "measured"
    assert result["mounted"] == ["my-skill"]
    assert "my-skill" in result["invoked_skills"]


def test_temp_root_mount_without_skills_root_falls_back_to_empty(tmp_path):
    """Documents the fallback: with no skills_root supplied, a temp-root
    mount is invisible to the production-default heuristic. Callers with
    an arm-specific skills root (prepare_arms.py's manifest) MUST pass it
    -- this is not itself the bug, omitting it is."""
    temp_root = "/tmp/consumer-path-off-skills-decoy-xyz789"
    plugins = [{"name": "my-skill", "path": f"{temp_root}/my-skill"}]
    log = _write_log(tmp_path, [_init_line(plugins)])

    result = msi.analyze("fake", str(log))

    assert result["status"] == "measured"
    assert result["mounted"] == []


def test_production_registry_path_still_detected_by_default(tmp_path):
    plugins = [{"name": "my-skill",
                "path": "/home/user/skill-registry/skills/my-skill"}]
    log = _write_log(tmp_path, [_init_line(plugins)])

    result = msi.analyze("fake", str(log))

    assert result["status"] == "measured"
    assert result["mounted"] == ["my-skill"]


def test_no_init_line_is_unmeasurable_with_named_reason(tmp_path):
    log = _write_log(tmp_path, [_skill_call_line("my-skill")])

    result = msi.analyze("fake", str(log))

    assert result["status"] == "unmeasurable"
    assert result["reason"] == "no-init-plugins-line"
    assert "mounted" not in result


def test_unparseable_init_line_is_unmeasurable_with_distinct_reason(tmp_path):
    log = _write_log(tmp_path, ['{"type":"system","subtype":"init","plugins":['])

    result = msi.analyze("fake", str(log))

    assert result["status"] == "unmeasurable"
    assert result["reason"] == "init-line-unparseable"
