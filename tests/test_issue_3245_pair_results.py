"""Tests for issue #3245 (R007 consumer-path pair results): the
multi-pair `--report` mode added to `scripts/consumer-path/
verify_manipulation.py`, and the trust-rooted dispatch/argv construction
added by `scripts/consumer-path/run_pair.py`.

Covers: the report's empty-state failure (no manifest anywhere -> says so,
exits nonzero, never a fabricated "0 pairs, all clean"), multi-pair
discovery and per-pair pass/exclude aggregation, the off arm's `skill-repo:`
source qualifier (never a stub -- issue #3245's must-not), and the
verification/cost collectors' fail-closed "None, not fabricated" shape
when their expected artifacts are absent.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONSUMER_PATH_DIR = ROOT / "scripts" / "consumer-path"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prepare_arms = _load_module("prepare_arms", CONSUMER_PATH_DIR / "prepare_arms.py")
verify_manipulation = _load_module(
    "verify_manipulation", CONSUMER_PATH_DIR / "verify_manipulation.py")
run_pair = _load_module("run_pair", CONSUMER_PATH_DIR / "run_pair.py")


@pytest.fixture
def populated_skills_root(tmp_path):
    root = tmp_path / "skills-corpus"
    (root / "skill-a").mkdir(parents=True)
    (root / "skill-a" / "SKILL.md").write_text("---\nname: skill-a\n---\n")
    return root


def _write_pair(pair_dir: Path, skills_root: Path, skill_name: str,
                 tamper_manifest=None, write_transport=True,
                 transport_argv_ok=True):
    pair_dir.mkdir(parents=True, exist_ok=True)
    manifest, created_dirs = prepare_arms.build_manifest(
        skills_root, skill_name, "sonnet", "test-operator")
    if tamper_manifest:
        tamper_manifest(manifest)
    manifest_path = pair_dir / "manifest.json"
    text = prepare_arms.render_manifest_json(manifest)
    manifest_path.write_text(text, encoding="utf-8")
    digest = prepare_arms._sha256_bytes(manifest_path.read_bytes())
    (pair_dir / "manifest.json.sha256").write_text(digest + "\n")
    prepare_arms._cleanup(created_dirs)

    if write_transport:
        transport = run_pair.build_transport(
            manifest, skill_name, "sonnet", "task text",
            "/tmp/fake-repo", 101, 102)
        if not transport_argv_ok:
            transport["arms"]["on"]["argv"] = ["claude", "-p", "task"]
        (pair_dir / "transport.json").write_text(
            json.dumps(transport, indent=2), encoding="utf-8")
    return manifest


# --- run_pair.py: off arm carries the source qualifier, never a stub ----

def test_off_arm_skills_argument_carries_qualifier_not_a_stub():
    assert run_pair._skills_argument("my-skill", "on") == "my-skill"
    assert run_pair._skills_argument("my-skill", "off") == "skill-repo:my-skill"
    # The qualifier is a string on the --skills argument, not a directory
    # this module writes -- nothing under run_pair.py creates files for
    # the off arm's skills root (that remains prepare_arms.py's job, and
    # prepare_arms.py never creates one either).
    assert "stub" not in run_pair._skills_argument("my-skill", "off")


def test_spawn_command_is_byte_identical_except_skills_and_issue():
    argv_on = run_pair.spawn_command("s", "sonnet", "task", 1, "/repo", "on")
    argv_off = run_pair.spawn_command("s", "sonnet", "task", 2, "/repo", "off")
    diffs = [(a, b) for a, b in zip(argv_on, argv_off) if a != b]
    assert {a for a, b in diffs} == {"s", "1"}
    assert {b for a, b in diffs} == {"skill-repo:s", "2"}


def test_build_transport_env_matches_manifest_arms(populated_skills_root):
    manifest, created = prepare_arms.build_manifest(
        populated_skills_root, "my-skill", "sonnet", "op")
    prepare_arms._cleanup(created)
    transport = run_pair.build_transport(
        manifest, "my-skill", "sonnet", "task", "/repo", 19, 20)
    on_arm = [a for a in manifest["arms"] if a["arm"] == "on"][0]
    off_arm = [a for a in manifest["arms"] if a["arm"] == "off"][0]
    assert transport["arms"]["on"]["env"]["HOME"] == on_arm["home"]
    assert transport["arms"]["on"]["env"]["MUSTER_SKILL_REPO"] == on_arm["skills_root"]
    assert transport["arms"]["off"]["env"]["HOME"] == off_arm["home"]
    assert transport["arms"]["off"]["env"]["MUSTER_SKILL_REPO"] == off_arm["skills_root"]
    assert transport["arms"]["on"]["env"]["HOME"] != transport["arms"]["off"]["env"]["HOME"]


def test_build_transport_verifies_clean_against_prepare_arms_manifest(
        tmp_path, populated_skills_root):
    manifest = _write_pair(tmp_path / "pair", populated_skills_root, "my-skill")
    verdict = verify_manipulation.verify(
        tmp_path / "pair" / "manifest.json", tmp_path / "pair" / "transport.json")
    assert verdict["manipulation_held"] is True
    assert verdict["pair_excluded"] is False


# --- run_pair() fails closed before dispatch when credentials could not
# be provisioned into an arm's isolated HOME (issue #3245 root cause) ---

def test_run_pair_fails_closed_when_credentials_not_provisioned(
        monkeypatch, tmp_path, populated_skills_root):
    # run_pair.py loads its own separate `prepare_arms` module instance
    # (_load_module at import time) -- patch that instance, not this
    # test file's own top-level `prepare_arms` reference, or the patch
    # silently never reaches the code under test.
    monkeypatch.setattr(
        run_pair.prepare_arms, "default_credentials_source",
        lambda: tmp_path / "no-such-credentials.json")
    monkeypatch.setenv("MUSTER_SKILL_REGISTRY_ROOT", str(populated_skills_root))
    task_file = run_pair.TASKS_DIR / "01-study-groups.txt"
    assert task_file.exists(), "fixture assumes an existing pair task file"

    result = run_pair.run_pair(
        "01-study-groups", "/tmp/fake-repo", "skill-a", "sonnet",
        101, 102, tmp_path / "out", 1800, confirm_real_spawn=True)

    assert result["status"] == "credentials-provisioning-failed"
    assert result["excluded_from_h2"] is True
    assert "on" in result["reason"] or "off" in result["reason"]


# --- collect_verification_rounds / collect_cost: fail-closed, not fabricated

def test_collect_verification_rounds_missing_pr_returns_none(tmp_path):
    result = run_pair.collect_verification_rounds(
        str(tmp_path), 999999, "no-such-skill")
    assert result["verification_rounds"] is None
    assert result["measured"] is False
    assert result["reason"]


def test_collect_cost_missing_ledger_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(run_pair, "ROOT", tmp_path)
    result = run_pair.collect_cost(str(tmp_path), 1, "skill")
    assert result["cost_usd"] is None
    assert result["measured"] is False


def test_collect_cost_sums_matching_ledger_entries(monkeypatch, tmp_path):
    monkeypatch.setattr(run_pair, "ROOT", tmp_path)
    (tmp_path / "runs").mkdir()
    ledger = tmp_path / "runs" / "ledger.jsonl"
    ledger.write_text(
        json.dumps({"issue": 19, "skill": "s", "cost_usd": 1.25}) + "\n"
        + json.dumps({"issue": 19, "skill": "s", "cost_usd": 0.75}) + "\n"
        + json.dumps({"issue": 20, "skill": "s", "cost_usd": 9.0}) + "\n")
    result = run_pair.collect_cost(str(tmp_path), 19, "s")
    assert result["measured"] is True
    assert result["cost_usd"] == pytest.approx(2.0)


# --- verify_manipulation.py --report: multi-pair aggregation -----------

def test_report_empty_state_says_so_and_would_exit_nonzero(tmp_path):
    empty_root = tmp_path / "nothing-here"
    result = verify_manipulation.report(empty_root)
    assert result["status"] == "no-manifests-found"
    assert result["pairs_found"] == 0
    assert "reason" in result and result["reason"]


def test_report_cli_empty_state_exits_nonzero(tmp_path):
    r = subprocess.run(
        [sys.executable, str(CONSUMER_PATH_DIR / "verify_manipulation.py"),
         "--report", "--root", str(tmp_path / "empty")],
        capture_output=True, text=True)
    assert r.returncode != 0
    payload = json.loads(r.stdout)
    assert payload["status"] == "no-manifests-found"


def test_report_finds_multiple_pair_dirs(tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-a", populated_skills_root, "skill-a")
    _write_pair(tmp_path / "pair-b", populated_skills_root, "skill-a")
    result = verify_manipulation.report(tmp_path)
    assert result["pairs_found"] == 2
    assert len(result["pairs_included"]) == 2
    assert result["pairs_excluded"] == []


def test_report_excludes_pair_with_bad_argv_and_keeps_others(
        tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-good", populated_skills_root, "skill-a")
    _write_pair(tmp_path / "pair-bad", populated_skills_root, "skill-a",
                transport_argv_ok=False)
    result = verify_manipulation.report(tmp_path)
    assert result["pairs_found"] == 2
    assert len(result["pairs_included"]) == 1
    assert len(result["pairs_excluded"]) == 1
    excluded_dir = result["pairs_excluded"][0]["pair_dir"]
    assert excluded_dir.endswith("pair-bad")
    assert "spawn.py" in result["pairs_excluded"][0]["reason"]


def test_report_excludes_pair_missing_transport(tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-no-transport", populated_skills_root,
                "skill-a", write_transport=False)
    result = verify_manipulation.report(tmp_path)
    assert result["pairs_found"] == 1
    assert result["pairs_included"] == []
    assert len(result["pairs_excluded"]) == 1
    assert "transport" in result["pairs_excluded"][0]["reason"]


def test_report_cli_exits_zero_when_all_pairs_verify(
        tmp_path, populated_skills_root):
    _write_pair(tmp_path / "pair-a", populated_skills_root, "skill-a")
    r = subprocess.run(
        [sys.executable, str(CONSUMER_PATH_DIR / "verify_manipulation.py"),
         "--report", "--root", str(tmp_path)],
        capture_output=True, text=True)
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["pairs_found"] == 1
    assert payload["pairs_excluded"] == []


def test_no_pair_reported_as_scored_without_passing_manipulation_check(
        tmp_path, populated_skills_root):
    """issue #3245's must-not: every pair reported as scored has a
    passing manipulation check recorded against it. Simulates a results
    aggregation step reading `report()`'s output and asserts it can only
    ever treat `pairs_included` (manipulation_held=True) pairs as scored
    -- `pairs_excluded` entries carry no manipulation_held=True verdict
    to be misread as a pass."""
    _write_pair(tmp_path / "pair-good", populated_skills_root, "skill-a")
    _write_pair(tmp_path / "pair-bad", populated_skills_root, "skill-a",
                transport_argv_ok=False)
    result = verify_manipulation.report(tmp_path)
    for pair in result["pairs"]:
        if pair["pair_dir"] in result["pairs_included"]:
            assert pair["manipulation_held"] is True
        else:
            assert pair.get("manipulation_held") is not True
