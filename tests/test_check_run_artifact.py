#!/usr/bin/env python3
"""issue-1493 phase-2 — check-run artifact 스키마/write-side/read-side
단위테스트. 네트워크 없이, 로컬 git fixture 저장소에 대해서만 돈다.

  python3 -m pytest tests/test_check_run_artifact.py
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "gates"))
import check_run_artifact as cra  # noqa: E402
import check_runner as cr  # noqa: E402
import merge_gate as mg  # noqa: E402


@pytest.fixture()
def fixture_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "existing.txt").write_text("hello world\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def _sample_checks():
    return [
        {"type": "test", "raw": "`python3 -m pytest tests/test_ok.py`",
         "command": "python3 -m pytest tests/test_ok.py"},
        {"type": "grep", "raw": "grep: hello world", "pattern": "hello world"},
        {"type": "file-existence", "raw": "`existing.txt`", "path": "existing.txt"},
    ]


def test_schema_roundtrip(fixture_repo, tmp_path):
    results = cr.run_checks(fixture_repo, _sample_checks())
    artifact = cra.build_artifact(
        command="check_runner.py 1 1", tier="fast", repo=fixture_repo,
        check_results=results, exit_code=0, produced_by="test")
    cra.validate(artifact)
    path = tmp_path / "artifact.json"
    cra.write_artifact(path, artifact)
    reloaded = cra.read_artifact(path)
    cra.validate(reloaded)
    assert reloaded == artifact
    assert reloaded["tree_hash"] == cra.tree_hash(fixture_repo)


def test_validate_rejects_missing_field():
    with pytest.raises(cra.ArtifactValidationError):
        cra.validate({"schema_version": 1})


def test_validate_rejects_wrong_schema_version(fixture_repo):
    results = cr.run_checks(fixture_repo, _sample_checks())
    artifact = cra.build_artifact(
        command="c", tier="fast", repo=fixture_repo, check_results=results,
        exit_code=0, produced_by="test")
    artifact["schema_version"] = 999
    with pytest.raises(cra.ArtifactValidationError):
        cra.validate(artifact)


def test_sample_rate_never_zero():
    with pytest.raises(ValueError):
        cra.select_sample([{"check": "x"}], rate=0)


def test_sample_eligibility_excludes_non_hermetic():
    per_test = [
        {"check": "a", "non_hermetic": True},
        {"check": "b", "non_hermetic": False},
        {"check": "c", "non_hermetic": False},
    ]
    eligible = cra.sample_eligible(per_test)
    assert [e["check"] for e in eligible] == ["b", "c"]


def test_sample_floor_is_at_least_three_or_20_percent():
    per_test = [{"check": str(i), "non_hermetic": False} for i in range(50)]
    sample = cra.select_sample(cra.sample_eligible(per_test), rate=0.2, floor=3)
    assert len(sample) >= max(3, int(50 * 0.2))


def test_build_artifact_flags_test_checks_non_hermetic(fixture_repo):
    results = cr.run_checks(fixture_repo, _sample_checks())
    artifact = cra.build_artifact(
        command="c", tier="fast", repo=fixture_repo, check_results=results,
        exit_code=0, produced_by="test")
    by_type = {e["type"]: e["non_hermetic"] for e in artifact["per_test_results"]}
    assert by_type["test"] is True
    assert by_type["grep"] is False
    assert by_type["file-existence"] is False


def test_missing_or_invalid_artifact_fails_closed(fixture_repo):
    status = mg.verify_artifact(fixture_repo)
    assert status["trust"] is False
    assert status["reasons"]

    (fixture_repo / ".on-the-record").mkdir()
    (fixture_repo / mg.ARTIFACT_PATH).write_text("not json{{{")
    status = mg.verify_artifact(fixture_repo)
    assert status["trust"] is False


def test_tree_mismatch_forces_rerun(fixture_repo):
    results = cr.run_checks(fixture_repo, _sample_checks())
    artifact = cra.build_artifact(
        command="c", tier="fast", repo=fixture_repo, check_results=results,
        exit_code=0, produced_by="test")
    artifact["tree_hash"] = "0" * 40
    cra.write_artifact(fixture_repo / mg.ARTIFACT_PATH, artifact)
    status = mg.verify_artifact(fixture_repo)
    assert status["trust"] is False
    assert any("tree_hash" in r for r in status["reasons"])


def test_matching_tree_hash_trusts_after_sample_reexecution(fixture_repo):
    results = cr.run_checks(fixture_repo, _sample_checks())
    artifact = cra.build_artifact(
        command="c", tier="fast", repo=fixture_repo, check_results=results,
        exit_code=0, produced_by="test")
    cra.write_artifact(fixture_repo / mg.ARTIFACT_PATH, artifact)
    status = mg.verify_artifact(fixture_repo)
    assert status["trust"] is True
    assert status["reasons"] == []


def test_sample_divergence_fails_closed(fixture_repo):
    results = cr.run_checks(fixture_repo, _sample_checks())
    artifact = cra.build_artifact(
        command="c", tier="fast", repo=fixture_repo, check_results=results,
        exit_code=0, produced_by="test")
    for entry in artifact["per_test_results"]:
        if entry["type"] == "grep":
            entry["status"] = "fail"
    cra.write_artifact(fixture_repo / mg.ARTIFACT_PATH, artifact)
    status = mg.verify_artifact(fixture_repo)
    assert status["trust"] is False
    assert any("다르다" in r for r in status["reasons"])
