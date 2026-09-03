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
    (root / "skill-a" / "SKILL.md").write_text("---\nname: skill-a\n---\n")
    (root / "skill-b").mkdir(parents=True)
    (root / "skill-b" / "SKILL.md").write_text("---\nname: skill-b\n---\n")
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


def test_demonstrate_absence_on_nonexistent_path(tmp_path):
    absent = tmp_path / "never-created"
    result = prepare_arms.demonstrate_absence(absent)
    assert result["skills_root_exists"] is False
    assert result["file_count"] == 0
    assert result["files_found"] == []


def test_demonstrate_absence_reports_existing_but_nonempty(tmp_path):
    populated = tmp_path / "populated"
    populated.mkdir()
    (populated / "leaked.md").write_text("leak")
    result = prepare_arms.demonstrate_absence(populated)
    assert result["skills_root_exists"] is True
    assert result["file_count"] == 1


# --- build_manifest: exactly-one-difference property --------------------

def test_arms_differ_only_in_manipulated_variable(populated_skills_root):
    manifest, created_dirs = prepare_arms.build_manifest(
        populated_skills_root, "skill-a", "sonnet", "test-operator")
    prepare_arms._cleanup(created_dirs)

    on = [a for a in manifest["arms"] if a["arm"] == "on"][0]
    off = [a for a in manifest["arms"] if a["arm"] == "off"][0]

    # The manipulated variable: corpus reachable vs. not.
    assert on["skill_files"] != []
    assert all(f.get("sha256") for f in on["skill_files"])
    assert off["skill_files"] == []
    assert off["absence_check"]["skills_root_exists"] is False

    # Isolation infrastructure differs (fresh HOME per arm) but the
    # dispatch shape itself -- argv template -- is identical, so nothing
    # besides HOME and the skills-root pointer varies between arms.
    assert on["home"] != off["home"]
    assert on["skills_root"] != off["skills_root"]
    assert manifest["dispatch"]["argv_identical_across_arms"] is True
    assert set(manifest["dispatch"]["env_keys_that_differ_by_arm"]) == {
        "HOME", manifest["skills_root_env_var"]}


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


# --- provision_credentials: PR #3251's isolated-HOME auth gap ------------
# Both independent verifications of PR #3251 traced its "environment-wide
# CLI/hook regression" misdiagnosis to this exact gap: an isolated HOME
# with no credentials makes `claude -p` fail auth before any hook fires,
# which `spawn.py doctor()`'s coarse check misreports as hooks not firing.

def test_provision_credentials_copies_only_the_credentials_file(tmp_path):
    source_home = tmp_path / "source-home"
    (source_home / ".claude").mkdir(parents=True)
    (source_home / ".claude" / ".credentials.json").write_text('{"token": "x"}')
    (source_home / ".claude" / "settings.json").write_text('{"other": "config"}')
    (source_home / ".claude" / "plugins").mkdir()

    dest_home = tmp_path / "arm-home"
    dest_home.mkdir()
    result = prepare_arms.provision_credentials(dest_home, source_home=source_home)

    assert result["provisioned"] is True
    assert (dest_home / ".claude" / ".credentials.json").read_text() == '{"token": "x"}'
    # Nothing else from the source .claude/ directory is copied.
    assert sorted(p.name for p in (dest_home / ".claude").iterdir()) == [
        ".credentials.json"]


def test_provision_credentials_missing_source_reports_not_provisioned(tmp_path):
    source_home = tmp_path / "source-home-no-creds"
    source_home.mkdir()
    dest_home = tmp_path / "arm-home"
    dest_home.mkdir()

    result = prepare_arms.provision_credentials(dest_home, source_home=source_home)

    assert result["provisioned"] is False
    assert not (dest_home / ".claude").exists()


def test_build_manifest_provisions_credentials_into_both_arm_homes(
        monkeypatch, populated_skills_root, tmp_path):
    source_home = tmp_path / "source-home"
    (source_home / ".claude").mkdir(parents=True)
    (source_home / ".claude" / ".credentials.json").write_text('{"token": "x"}')
    monkeypatch.setenv("HOME", str(source_home))

    manifest, created_dirs = prepare_arms.build_manifest(
        populated_skills_root, "skill-a", "sonnet", "test-operator")
    try:
        on = [a for a in manifest["arms"] if a["arm"] == "on"][0]
        off = [a for a in manifest["arms"] if a["arm"] == "off"][0]
        assert on["credential_provisioning"]["provisioned"] is True
        assert off["credential_provisioning"]["provisioned"] is True
        assert Path(on["credential_provisioning"]["dest"]).read_text() == '{"token": "x"}'
        assert Path(off["credential_provisioning"]["dest"]).read_text() == '{"token": "x"}'
        # The off arm's skills-root absence guarantee is untouched by
        # credential provisioning -- still nothing to read there.
        assert off["skill_files"] == []
        assert off["absence_check"]["skills_root_exists"] is False
    finally:
        prepare_arms._cleanup(created_dirs)


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
