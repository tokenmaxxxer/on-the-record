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
아니라 값만 눌러놓은 것이다. tier 이름·design_bearing_override·
single_phase_tier·default_tier 구조는 그대로다. 해제하려면 (a) 소비
레포에 `.on-the-record/model-routing.json`을 두어 tier별 model을
오버라이드하거나 (b) 이 DEFAULT_POLICY의 값을 되돌린다.

issue #2631 — operator ruling (2026-08-27): tier별 "roles" 고정 이름
목록과 그 membership test(`role in tier["roles"]`)를 제거했다. 이것으로
{ux-engineering, brand-design, content-design, architecture} 네 이름이
role-tier:judgment로 강제 배정되던 능력 자체가 없어진다 — 그
capability가 없어진 것이지 어딘가로 옮겨진 게 아니다. 이 네 역할은
이제 다른 모든 역할과 동일하게 design_bearing_override(참일 때) →
single_phase_tier → default_tier 순서로만 라우팅된다. #2148이 모든
tier의 model을 "sonnet"으로 고정해 놓은 상태라 오늘 시점에는 실제
선택되는 model이 바뀌지 않는다 — 다만 design_bearing_verdict가
거짓/None이고 single_phase도 아닌 경우, 이 네 역할의 rule 태그는
`role-tier:judgment`에서 `default-tier:mid-design`으로 바뀐다(모델은
여전히 sonnet). `route_model()`은 이제 `role` 인자를 받지 않는다 —
role은 더 이상 라우팅 신호가 아니다.

  from gates.model_routing import load_policy, route_model
"""
from __future__ import annotations
import json
from pathlib import Path

DEFAULT_POLICY = {
    "tiers": {
        "judgment": {"model": "sonnet"},
        "mid-design": {"model": "sonnet"},
        "mechanical": {"model": "sonnet"},
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


def route_model(single_phase: bool = False,
                 design_bearing_verdict: bool | None = None,
                 policy: dict | None = None) -> tuple[str, str]:
    """(model, rule) 을 돌려준다. `policy`가 malformed 여도(필요 키 누락,
    잘못된 타입) 절대 raise 하지 않고 `("sonnet", "fail-open-default")`로
    떨어진다.

    우선순위: design-bearing override(참일 때) > single_phase 이면
    `single_phase_tier` > `default_tier`.
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
