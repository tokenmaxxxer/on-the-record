"""issue #2070 — 구조적 모델 라우팅(gates/model_routing.py) 및
`resolved_role_model()`의 라우팅 통합 테스트.

acceptance: policy file honored, override precedence, fail-open on
malformed policy, ledger(roster) line records model+rule.
"""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "gates"))

from model_routing import DEFAULT_POLICY, load_policy, route_model
import spawn


def test_policy_file_honored(tmp_path):
    policy_dir = tmp_path / ".on-the-record"
    policy_dir.mkdir()
    (policy_dir / "model-routing.json").write_text(json.dumps({
        "tiers": {
            "judgment": {"model": "claude-fable-5", "roles": ["ux-engineering"]},
            "mid-design": {"model": "opus", "roles": []},
            "mechanical": {"model": "sonnet", "roles": []},
        },
        "design_bearing_override": "judgment",
        "single_phase_tier": "mechanical",
        "default_tier": "mid-design",
    }))
    policy = load_policy(tmp_path)
    model, rule = route_model("ux-engineering", policy=policy)
    assert (model, rule) == ("claude-fable-5", "role-tier:judgment")


def test_load_policy_missing_file_returns_default(tmp_path):
    assert load_policy(tmp_path) == DEFAULT_POLICY


def test_route_model_single_phase_tier():
    model, rule = route_model("some-mechanical-role", single_phase=True)
    assert (model, rule) == ("sonnet", "single-phase-tier:mechanical")


def test_route_model_default_tier():
    model, rule = route_model("some-unmapped-role")
    assert (model, rule) == ("sonnet", "default-tier:mid-design")


def test_route_model_design_bearing_override_wins_over_role_tier():
    model, rule = route_model("some-unmapped-role", design_bearing_verdict=True)
    assert (model, rule) == ("sonnet", "design-bearing-override")


def test_route_model_fail_open_on_malformed_policy():
    assert route_model("any-role", policy={"garbage": True}) == (
        "sonnet", "fail-open-default")
    assert route_model("any-role", policy=None) == (
        "sonnet", "default-tier:mid-design")
    assert route_model("any-role", policy="not-even-a-dict") == (
        "sonnet", "fail-open-default")


def test_resolved_role_model_cli_override_precedence(monkeypatch):
    monkeypatch.delenv("MUSTER_ROLE_MODEL", raising=False)
    assert spawn.resolved_role_model("haiku", role="ux-engineering") == (
        "haiku", "cli-override")


def test_resolved_role_model_env_override_precedence(monkeypatch):
    monkeypatch.setenv("MUSTER_ROLE_MODEL", "opus")
    assert spawn.resolved_role_model(None, role="ux-engineering") == (
        "opus", "env-override")


def test_resolved_role_model_config_override_precedence(monkeypatch, tmp_path):
    monkeypatch.delenv("MUSTER_ROLE_MODEL", raising=False)
    monkeypatch.setattr(spawn, "ROLE_MODEL_CONFIG", tmp_path / "role_model.txt")
    (tmp_path / "role_model.txt").write_text("sonnet-config\n")
    assert spawn.resolved_role_model(None, role="ux-engineering") == (
        "sonnet-config", "config-override")


def test_resolved_role_model_routes_when_chain_empty(monkeypatch, tmp_path):
    monkeypatch.delenv("MUSTER_ROLE_MODEL", raising=False)
    monkeypatch.setattr(spawn, "ROLE_MODEL_CONFIG", tmp_path / "role_model.txt")
    monkeypatch.setattr(spawn, "ROOT", tmp_path)
    model, rule = spawn.resolved_role_model(None, role="ux-engineering")
    assert (model, rule) == ("sonnet", "role-tier:judgment")


def test_resolved_role_model_no_role_returns_plain_string(monkeypatch):
    monkeypatch.delenv("MUSTER_ROLE_MODEL", raising=False)
    result = spawn.resolved_role_model("haiku")
    assert result == "haiku"
    assert isinstance(result, str)


def test_spawn_cmd_env_carries_model_and_rule(monkeypatch, tmp_path):
    monkeypatch.delenv("MUSTER_ROLE_MODEL", raising=False)
    monkeypatch.setattr(spawn, "ROLE_MODEL_CONFIG", tmp_path / "role_model.txt")
    monkeypatch.setattr(spawn, "ROOT", tmp_path)
    cmd, env = spawn.spawn_cmd("settings.json", "ux-engineering", True)
    assert env["_MODEL_ROUTING_MODEL"] == "sonnet"
    assert env["_MODEL_ROUTING_RULE"] == "role-tier:judgment"
    assert "--model" in cmd
    assert cmd[cmd.index("--model") + 1] == "sonnet"
