"""Tests for scripts/consumer-path/{prepare_arms,verify_manipulation}.py
(issue #3183, R007 launcher-owned trust root).

Covers: the exactly-one-difference property between the on/off arms a
real manifest produces, and every fail-closed path verify_manipulation.py
must take (missing manifest, missing transport record, hash mismatch,
malformed/incomplete transport record, mismatched HOME/skills-root).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONSUMER_PATH_DIR = ROOT / "scripts" / "consumer-path"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(
        name, CONSUMER_PATH_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare_arms = _load_module("prepare_arms")
verify_manipulation = _load_module("verify_manipulation")


@pytest.fixture
def populated_skills_root(tmp_path):
    root = tmp_path / "skills-corpus"
    (root / "skill-a").mkdir(parents=True)
    (root / "skill-a" / "SKILL.md").write_text(
        "---\nname: skill-a\n---\nReal guidance body for skill-a.\n")
    (root / "skill-b").mkdir(parents=True)
    (root / "skill-b" / "SKILL.md").write_text(
        "---\nname: skill-b\n---\nReal guidance body for skill-b.\n")
    return root


def _write_manifest(tmp_path, skills_root):
    manifest, created_dirs = prepare_arms.build_manifest(
        skills_root, "skill-a", "sonnet", "test-operator")
    try:
        manifest_path = tmp_path / "manifest.json"
        text = prepare_arms.render_manifest_json(manifest)
        manifest_path.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        (tmp_path / "manifest.json.sha256").write_text(digest + "\n")
        return manifest, manifest_path
    finally:
        prepare_arms._cleanup(created_dirs)


def _transport_for(manifest: dict, tamper: dict | None = None) -> dict:
    arms = {}
    for arm in manifest["arms"]:
        arms[arm["arm"]] = {
            "argv": ["python3", "spawn.py", "--skills", "skill-a", "task",
                     "--issue", "1", "-C", "repo"],
            "env": {"HOME": arm["home"], "MUSTER_SKILL_REPO": arm["skills_root"]},
        }
    record = {"captured_before_dispatch": True, "arms": arms}
    if tamper:
        record.update(tamper)
    return record


# --- resolve_skill_files / demonstrate_absence --------------------------

def test_resolve_skill_files_hashes_every_file(populated_skills_root):
    files = prepare_arms.resolve_skill_files(populated_skills_root)
    assert {f["path"] for f in files} == {
        "skill-a/SKILL.md", "skill-b/SKILL.md"}
    assert all(f["sha256"] for f in files)


def test_resolve_skill_files_skips_dot_directories(populated_skills_root):
    (populated_skills_root / ".git").mkdir()
    (populated_skills_root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    files = prepare_arms.resolve_skill_files(populated_skills_root)
    assert all(not f["path"].startswith(".") for f in files)


def test_front_matter_block_strips_body():
    text = "---\nname: skill-a\n---\nSome guidance body.\nMore lines.\n"
    assert prepare_arms.front_matter_block(text) == "---\nname: skill-a\n---\n"


def test_front_matter_block_falls_back_when_absent():
    assert prepare_arms.front_matter_block("no front matter here") == \
        "---\nname: (unknown)\n---\n"


def test_build_decoy_skill_root_drops_body(tmp_path, populated_skills_root):
    real = populated_skills_root / "skill-a" / "SKILL.md"
    decoy_root = prepare_arms.build_decoy_skill_root("skill-a", real)
    decoy_md = decoy_root / "skill-a" / "SKILL.md"
    assert decoy_md.is_file()
    text = decoy_md.read_text(encoding="utf-8")
    assert text.startswith("---\nname: skill-a\n")
    assert "Real guidance body" not in text
    assert decoy_md.read_bytes() != real.read_bytes()


def test_build_decoy_skill_root_drops_description_and_metadata(tmp_path):
    """Round 8 mid-flight correction: a decoy that copies the real
    front matter verbatim hands the off arm the description and
    metadata fields, which are themselves most of what a rubric-scored
    task measures. Only `name:` survives."""
    root = tmp_path / "skills-corpus"
    (root / "rich-skill").mkdir(parents=True)
    real = root / "rich-skill" / "SKILL.md"
    real.write_text(
        "---\n"
        "name: rich-skill\n"
        "description: >-\n"
        "  Use when a hypothesis needs its primary metric, numeric\n"
        "  threshold, and decision rule fixed before data collection.\n"
        "metadata:\n"
        "  axis: hypothesis-preregistration\n"
        "  rule_count_floor: 10\n"
        "---\n"
        "Body with the real guidance.\n",
        encoding="utf-8",
    )
    decoy_root = prepare_arms.build_decoy_skill_root("rich-skill", real)
    decoy_text = (decoy_root / "rich-skill" / "SKILL.md").read_text(
        encoding="utf-8")
    assert decoy_text.startswith("---\nname: rich-skill\n")
    assert "metadata:" not in decoy_text
    assert "rule_count_floor" not in decoy_text
    assert "primary metric" not in decoy_text
    assert "numeric" not in decoy_text
    assert "threshold" not in decoy_text
    assert "decision rule" not in decoy_text
    assert decoy_text != real.read_text(encoding="utf-8")


def test_build_decoy_skill_root_copies_real_policy_skills(
        tmp_path, populated_skills_root, monkeypatch):
    """Round 7 live finding: a decoy root holding only the manipulated
    skill still refused to dispatch -- `resolve_static_policy_source()`
    resolves `_STATIC_POLICY_SKILLS` against the same repo_root every
    issue-scoped `--skills` spawn uses, fail-closed if any name is
    missing. The decoy root must also carry a verbatim copy of those
    names from the real corpus."""
    monkeypatch.setattr(prepare_arms._skills_mod, "_STATIC_POLICY_SKILLS",
                         {"skill-b"})
    real = populated_skills_root / "skill-a" / "SKILL.md"
    decoy_root = prepare_arms.build_decoy_skill_root(
        "skill-a", real, populated_skills_root)
    policy_copy = decoy_root / "skill-b" / "SKILL.md"
    assert policy_copy.is_file()
    assert policy_copy.read_bytes() == \
        (populated_skills_root / "skill-b" / "SKILL.md").read_bytes()


def test_build_decoy_skill_root_skips_absent_policy_skill(
        tmp_path, populated_skills_root, monkeypatch):
    monkeypatch.setattr(prepare_arms._skills_mod, "_STATIC_POLICY_SKILLS",
                         {"no-such-policy-skill"})
    real = populated_skills_root / "skill-a" / "SKILL.md"
    decoy_root = prepare_arms.build_decoy_skill_root(
        "skill-a", real, populated_skills_root)
    assert not (decoy_root / "no-such-policy-skill").exists()


def test_build_decoy_skill_root_rejects_missing_source(tmp_path):
    with pytest.raises(prepare_arms.ArmPreparationError):
        prepare_arms.build_decoy_skill_root(
            "skill-a", tmp_path / "no-such-skill" / "SKILL.md")


def test_build_decoy_skill_root_rejects_body_free_source(tmp_path):
    root = tmp_path / "skills-corpus"
    (root / "skill-a").mkdir(parents=True)
    real = root / "skill-a" / "SKILL.md"
    real.write_text("---\nname: skill-a\n---\n")  # no body to strip
    with pytest.raises(prepare_arms.ArmPreparationError):
        prepare_arms.build_decoy_skill_root("skill-a", real)


# --- build_manifest: exactly-one-difference property --------------------

def test_arms_differ_only_in_manipulated_variable(populated_skills_root):
    manifest, created_dirs = prepare_arms.build_manifest(
        populated_skills_root, "skill-a", "sonnet", "test-operator")
    prepare_arms._cleanup(created_dirs)

    on = [a for a in manifest["arms"] if a["arm"] == "on"][0]
    off = [a for a in manifest["arms"] if a["arm"] == "off"][0]

    # The manipulated variable: real guidance vs. a same-named decoy with
    # none (issue #3280) -- both arms resolve a name and dispatch, but
    # only the on arm's SKILL.md carries a body.
    assert on["skill_files"] != []
    assert all(f.get("sha256") for f in on["skill_files"])
    assert off["skill_files"] != []
    assert off["decoy"]["has_body_guidance"] is False
    on_md = next(f for f in on["skill_files"] if f["path"] == "skill-a/SKILL.md")
    off_md = next(f for f in off["skill_files"] if f["path"] == "skill-a/SKILL.md")
    assert on_md["sha256"] != off_md["sha256"]

    # Isolation infrastructure differs (fresh HOME per arm) but the
    # dispatch shape itself -- argv template -- is identical, so nothing
    # besides HOME and the skills-root pointer varies between arms.
    assert on["home"] != off["home"]
    assert on["skills_root"] != off["skills_root"]
    assert manifest["dispatch"]["argv_identical_across_arms"] is True
    assert set(manifest["dispatch"]["env_keys_that_differ_by_arm"]) == {
        "HOME", manifest["skills_root_env_var"]}


def test_on_arm_mounts_only_the_named_skill(populated_skills_root):
    """Round 8 mid-flight correction: the on arm used to mount the
    entire registry (352 files against the off arm's 1). R007 asks
    what ONE skill is worth, so the on arm must mount exactly
    `skill_name` -- not `skill-b`, which is also present in the real
    corpus but not under test."""
    manifest, created_dirs = prepare_arms.build_manifest(
        populated_skills_root, "skill-a", "sonnet", "test-operator")
    on = [a for a in manifest["arms"] if a["arm"] == "on"][0]
    off = [a for a in manifest["arms"] if a["arm"] == "off"][0]
    prepare_arms._cleanup(created_dirs)

    on_paths = {f["path"] for f in on["skill_files"]}
    assert on_paths == {"skill-a/SKILL.md"}
    assert "skill-b/SKILL.md" not in on_paths

    # The exactly-one-difference property the issue asks for: same file
    # count on both sides, differing only in skill-a/SKILL.md's content.
    assert len(on["skill_files"]) == len(off["skill_files"])


def test_build_manifest_rejects_unequal_file_counts(
        tmp_path, populated_skills_root, monkeypatch):
    """If a future change makes the arms' file sets diverge again,
    build_manifest must refuse rather than silently emit a manifest a
    scored result cannot be attributed to."""
    real_off = prepare_arms.make_off_arm

    def _bloated_off_arm(home, skills_root_on, skill_name):
        arm = real_off(home, skills_root_on, skill_name)
        extra = Path(arm["skills_root"]) / "extra-file.md"
        extra.write_text("unrelated extra file\n", encoding="utf-8")
        arm["skill_files"] = prepare_arms.resolve_skill_files(
            Path(arm["skills_root"]))
        return arm

    monkeypatch.setattr(prepare_arms, "make_off_arm", _bloated_off_arm)
    with pytest.raises(prepare_arms.ArmPreparationError,
                        match="different file counts"):
        prepare_arms.build_manifest(
            populated_skills_root, "skill-a", "sonnet", "test-operator")


def test_on_arm_rejects_empty_corpus(tmp_path):
    empty_root = tmp_path / "empty-corpus"
    empty_root.mkdir()
    with pytest.raises(prepare_arms.ArmPreparationError):
        prepare_arms.build_manifest(empty_root, "skill-a", "sonnet", "op")


def test_build_manifest_cleans_up_homes_it_created(populated_skills_root):
    manifest, created_dirs = prepare_arms.build_manifest(
        populated_skills_root, "skill-a", "sonnet", "test-operator")
    assert all(d.is_dir() for d in created_dirs)
    prepare_arms._cleanup(created_dirs)
    assert all(not d.exists() for d in created_dirs)


# --- verify_manipulation.py: happy path ---------------------------------

def test_verify_succeeds_on_matching_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(_transport_for(manifest)))

    verdict = verify_manipulation.verify(manifest_path, transport_path)
    assert verdict["manipulation_held"] is True
    assert verdict["pair_excluded"] is False


# --- verify_manipulation.py: fail-closed paths --------------------------

def test_missing_manifest_excludes_pair(tmp_path):
    with pytest.raises(verify_manipulation.VerificationFailure):
        verify_manipulation.verify(
            tmp_path / "no-such-manifest.json", tmp_path / "transport.json")


def test_missing_manifest_cli_exits_nonzero(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(_transport_for(manifest)))
    manifest_path.unlink()

    import subprocess
    result = subprocess.run(
        [sys.executable, str(CONSUMER_PATH_DIR / "verify_manipulation.py"),
         "--manifest", str(manifest_path), "--transport", str(transport_path)],
        capture_output=True, text=True)
    assert result.returncode != 0
    verdict = json.loads(result.stdout)
    assert verdict["pair_excluded"] is True


def test_missing_transport_record_excludes_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    with pytest.raises(verify_manipulation.VerificationFailure):
        verify_manipulation.verify(
            manifest_path, tmp_path / "no-such-transport.json")


def test_manifest_hash_mismatch_excludes_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(_transport_for(manifest)))

    data = json.loads(manifest_path.read_text())
    data["arms"][0]["skill_files"] = []
    manifest_path.write_text(json.dumps(data))

    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="hash mismatch"):
        verify_manipulation.verify(manifest_path, transport_path)


def test_missing_sidecar_excludes_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(_transport_for(manifest)))
    (tmp_path / "manifest.json.sha256").unlink()

    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="sidecar"):
        verify_manipulation.verify(manifest_path, transport_path)


def test_home_mismatch_excludes_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport = _transport_for(manifest)
    transport["arms"]["on"]["env"]["HOME"] = "/some/other/home"
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(transport))

    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="HOME"):
        verify_manipulation.verify(manifest_path, transport_path)


def test_skills_root_mismatch_excludes_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport = _transport_for(manifest)
    transport["arms"]["off"]["env"]["MUSTER_SKILL_REPO"] = "/somewhere/else"
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(transport))

    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="MUSTER_SKILL_REPO"):
        verify_manipulation.verify(manifest_path, transport_path)


def test_bare_cli_argv_rejected_not_real_consumer_path(
        tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport = _transport_for(manifest)
    transport["arms"]["on"]["argv"] = ["claude", "-p", "task"]
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(transport))

    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="spawn.py"):
        verify_manipulation.verify(manifest_path, transport_path)


def test_missing_arm_in_transport_excludes_pair(tmp_path, populated_skills_root):
    manifest, manifest_path = _write_manifest(tmp_path, populated_skills_root)
    transport = _transport_for(manifest)
    del transport["arms"]["off"]
    transport_path = tmp_path / "transport.json"
    transport_path.write_text(json.dumps(transport))

    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="off"):
        verify_manipulation.verify(manifest_path, transport_path)


def test_malformed_manifest_json_excludes_pair(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{not valid json")
    (tmp_path / "manifest.json.sha256").write_text(
        hashlib.sha256(manifest_path.read_bytes()).hexdigest())
    with pytest.raises(verify_manipulation.VerificationFailure,
                        match="not valid JSON"):
        verify_manipulation.verify(manifest_path, tmp_path / "transport.json")
