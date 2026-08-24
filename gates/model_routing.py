#!/usr/bin/env python3
"""issue #2070 — spawn 시점 구조적 모델 라우팅. `resolved_role_model()`의
`--model` > `MUSTER_ROLE_MODEL` > `role_model.txt` 체인이 셋 다 비어 있을
때만 호출되는, 오늘의 하드코딩된 `"sonnet"` 종착점을 대체하는 계층.

fail-open: 정책 파일이 없거나 깨져 있거나 알 수 없는 역할이어도 절대
raise 하지 않는다 — 항상 (model, rule) 튜플을 돌려준다. 정책은
`.on-the-record/model-routing.json`에 데이터로 산다(제안서 Constraints,
test-tiers.json #1518 선례와 동일한 모양) — 소비 레포가 spawn.py를 건드리지
않고 오버라이드할 수 있게.

issue #2148 — operator pin (2026-08-24): DEFAULT_POLICY의 모든 tier
model 값이 "sonnet"으로 고정되어 있다. #2070의 구조적 tier
분리(judgment=claude-fable-5, mid-design=opus)는 SUSPENDED — 삭제가
아니라 값만 눌러놓은 것이다. tier 이름·roles 매핑·
design_bearing_override·single_phase_tier·default_tier 구조는 그대로다.
해제하려면 (a) 소비 레포에 `.on-the-record/model-routing.json`을 두어
tier별 model을 오버라이드하거나 (b) 이 DEFAULT_POLICY의 값을 되돌린다.

  from gates.model_routing import load_policy, route_model
"""
from __future__ import annotations
import json
from pathlib import Path

DEFAULT_POLICY = {
    "tiers": {
        "judgment": {
            "model": "sonnet",
            "roles": ["ux-engineering", "brand-design", "content-design", "architecture"],
        },
        "mid-design": {"model": "sonnet", "roles": []},
        "mechanical": {"model": "sonnet", "roles": []},
    },
    "design_bearing_override": "judgment",
    "single_phase_tier": "mechanical",
    "default_tier": "mid-design",
}

POLICY_REL_PATH = ".on-the-record/model-routing.json"


def load_policy(repo_root: str | Path) -> dict:
    """정책 파일을 읽는다. 없거나 파싱 실패면 `DEFAULT_POLICY`를 그대로
    돌려준다 — 절대 raise 하지 않는다."""
    path = Path(repo_root) / POLICY_REL_PATH
    try:
        return json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return DEFAULT_POLICY


def _role_tier(role: str, tiers: dict) -> str | None:
    for tier_name, tier in tiers.items():
        if role in (tier.get("roles") or []):
            return tier_name
    return None


def route_model(role: str, single_phase: bool = False,
                 design_bearing_verdict: bool | None = None,
                 policy: dict | None = None) -> tuple[str, str]:
    """(model, rule) 을 돌려준다. `policy`가 malformed 여도(필요 키 누락,
    잘못된 타입) 절대 raise 하지 않고 `("sonnet", "fail-open-default")`로
    떨어진다.

    우선순위: design-bearing override(참일 때) > 역할이 매핑된 tier >
    single_phase 이면 `single_phase_tier` > `default_tier`.
    """
    policy = policy or DEFAULT_POLICY
    try:
        tiers = policy["tiers"]

        def model_of(tier_name: str) -> str | None:
            tier = tiers.get(tier_name)
            return tier.get("model") if tier else None

        if design_bearing_verdict:
            override_tier = policy.get("design_bearing_override")
            model = model_of(override_tier) if override_tier else None
            if model:
                return model, "design-bearing-override"

        role_tier = _role_tier(role, tiers)
        if role_tier:
            model = model_of(role_tier)
            if model:
                return model, f"role-tier:{role_tier}"

        if single_phase:
            sp_tier = policy.get("single_phase_tier")
            model = model_of(sp_tier) if sp_tier else None
            if model:
                return model, f"single-phase-tier:{sp_tier}"

        default_tier = policy.get("default_tier")
        model = model_of(default_tier) if default_tier else None
        if model:
            return model, f"default-tier:{default_tier}"
    except (KeyError, AttributeError, TypeError):
        pass
    return "sonnet", "fail-open-default"
