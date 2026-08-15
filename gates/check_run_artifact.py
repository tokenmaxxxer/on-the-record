#!/usr/bin/env python3
"""issue-1493 phase-2 — check-run 결과를 재사용 가능한 산출물(artifact)로
직렬화/역직렬화/검증하는 독립 스키마 모듈 (design record의 Alternative B).

`check_runner.py` (쓰기 쪽)와 `merge_gate.py` (읽기 쪽)가 공유하는
데이터 계약만 담는다 — subprocess/gh 호출은 없다.

  docs/issue-1493/proposals/check-run-artifact-design.md 참고.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

SCHEMA_VERSION = 1

_REQUIRED_FIELDS = {
    "schema_version", "command", "tier", "tree_hash", "env_fingerprint",
    "per_test_results", "exit_code", "output_hash", "produced_by",
}
_VALID_TIERS = {"fast", "slow", "full"}


def output_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def tree_hash(repo: Path) -> str | None:
    """추적중인 트리의 해시. git 커맨드 실패 시 `None`."""
    r = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=repo,
                        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout.strip()


def _is_non_hermetic(check: dict) -> bool:
    """`grep`/`file-existence`는 순수 파일시스템 읽기라 hermetic 이다.
    `test`는 임의 커맨드를 실행하므로 마커가 없는 한 non-hermetic 으로
    가정한다 (design record의 '마커 없으면 true' 기본값)."""
    return check.get("type") == "test"


def build_artifact(command: str, tier: str, repo: Path,
                    check_results: list[dict], exit_code: int,
                    produced_by: str,
                    env_fingerprint: dict | None = None) -> dict:
    """`check_runner.run_checks()`가 낸 `check_results` (각 항목:
    check/type/status/output, 원본 check dict의 command/pattern/path
    포함)로부터 산출물을 만든다."""
    if tier not in _VALID_TIERS:
        raise ValueError(f"알 수 없는 tier: {tier!r}")
    fp = {
        "interpreter_version": None,
        "os": None,
        "locale": None,
    }
    if env_fingerprint:
        fp.update(env_fingerprint)

    per_test_results = []
    for r in check_results:
        entry = dict(r)
        entry["output_hash"] = output_hash(r.get("output", ""))
        entry["non_hermetic"] = _is_non_hermetic(r)
        per_test_results.append(entry)

    all_output = "\n".join(r.get("output", "") for r in check_results)
    return {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "tier": tier,
        "tree_hash": tree_hash(repo),
        "env_fingerprint": fp,
        "per_test_results": per_test_results,
        "exit_code": exit_code,
        "output_hash": output_hash(all_output),
        "produced_by": produced_by,
    }


class ArtifactValidationError(Exception):
    """산출물이 스키마와 맞지 않는다."""


def validate(artifact: object) -> None:
    """스키마를 만족하지 않으면 `ArtifactValidationError`를 낸다."""
    if not isinstance(artifact, dict):
        raise ArtifactValidationError("산출물은 JSON 오브젝트여야 한다")
    missing = _REQUIRED_FIELDS - artifact.keys()
    if missing:
        raise ArtifactValidationError(f"필수 필드 누락: {sorted(missing)}")
    if artifact["schema_version"] != SCHEMA_VERSION:
        raise ArtifactValidationError(
            f"지원하지 않는 schema_version: {artifact['schema_version']!r}")
    if artifact["tier"] not in _VALID_TIERS:
        raise ArtifactValidationError(f"알 수 없는 tier: {artifact['tier']!r}")
    if not isinstance(artifact["per_test_results"], list):
        raise ArtifactValidationError("per_test_results는 list여야 한다")
    for entry in artifact["per_test_results"]:
        if not isinstance(entry, dict):
            raise ArtifactValidationError("per_test_results 항목은 dict여야 한다")
        for f in ("check", "status", "output_hash", "non_hermetic"):
            if f not in entry:
                raise ArtifactValidationError(
                    f"per_test_results 항목에 '{f}' 필드가 없다: {entry!r}")
    if not isinstance(artifact["env_fingerprint"], dict):
        raise ArtifactValidationError("env_fingerprint는 dict여야 한다")


def write_artifact(path: Path, artifact: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")


def read_artifact(path: Path) -> dict | None:
    """없거나 JSON 파싱이 실패하면 `None` — 호출자가 fail-closed 처리."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def sample_eligible(per_test_results: list[dict]) -> list[dict]:
    """non_hermetic=True 항목은 샘플링 대상에서 제외한다 — 그런 항목은
    항상 강제 재실행 대상이지 무작위 샘플 후보가 아니다."""
    return [e for e in per_test_results if not e.get("non_hermetic", True)]


def select_sample(eligible: list[dict], rate: float = 0.2, floor: int = 3) -> list[dict]:
    """>=20% 또는 >=3개 중 더 큰 쪽, per-artifact. `rate`를 0으로 두는
    것은 이 설계가 금지하는 정책이라 여기서도 거부한다."""
    if rate <= 0:
        raise ValueError("샘플링 비율은 0이 될 수 없다 (design record 제약)")
    if not eligible:
        return []
    n = max(floor, int(len(eligible) * rate + 0.999))
    n = min(n, len(eligible))
    step = max(1, len(eligible) // n)
    sample = eligible[::step][:n]
    if len(sample) < n:
        for e in eligible:
            if e not in sample:
                sample.append(e)
            if len(sample) >= n:
                break
    return sample
