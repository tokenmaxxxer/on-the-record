"""Acceptance tests for issue #1518's test-tier contract convention."""
import importlib.util
import json
from pathlib import Path

# issue #1619: `gates/gates.py` is bare-imported as top-level `gates` by
# gates/test_*.py (rootdir sys.path insertion for dirs with no
# __init__.py), which binds sys.modules['gates'] to that flat module.
# When gates/ collects before tests/ in a full-suite run, a later
# `from gates.test_tier_contract import ...` here finds the same
# sys.modules['gates'] entry and fails ("'gates' is not a package")
# since it has no __path__ -- load by explicit file path instead of by
# package name to sidestep the collision.
_spec = importlib.util.spec_from_file_location(
    "test_tier_contract", Path(__file__).resolve().parent.parent / "gates" / "test_tier_contract.py")
_test_tier_contract = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_test_tier_contract)
DEFAULT_BUDGET_SECONDS = _test_tier_contract.DEFAULT_BUDGET_SECONDS
load_contract = _test_tier_contract.load_contract
no_contract_gap = _test_tier_contract.no_contract_gap
parse_contract = _test_tier_contract.parse_contract
select_tier = _test_tier_contract.select_tier


def test_contract_parse_and_budget(tmp_path):
    otr_dir = tmp_path / ".on-the-record"
    otr_dir.mkdir()
    contract_path = otr_dir / "test-tiers.json"

    contract_path.write_text(json.dumps({
        "fast": {"command": 'python3 -m pytest -m "not slow"'},
    }))
    contract = load_contract(tmp_path)
    assert contract is not None
    assert contract.fast_command == 'python3 -m pytest -m "not slow"'
    assert contract.budget_seconds == DEFAULT_BUDGET_SECONDS

    contract_path.write_text(json.dumps({
        "fast": {"command": "pytest", "budget_seconds": 120},
    }))
    contract = load_contract(tmp_path)
    assert contract.budget_seconds == 120

    # malformed contract -> fail-closed to None, never raises
    contract_path.write_text("{not valid json")
    assert load_contract(tmp_path) is None

    contract_path.write_text(json.dumps({"fast": {"budget_seconds": 300}}))
    assert load_contract(tmp_path) is None  # missing required fast.command

    # empty state: a repo with NO contract file at all takes the same
    # no-contract path as a malformed one
    no_contract_repo = tmp_path / "no-contract-repo"
    no_contract_repo.mkdir()
    assert load_contract(no_contract_repo) is None


def test_slow_trigger_by_change_class():
    raw = {
        "fast": {"command": 'python3 -m pytest -m "not slow"', "budget_seconds": 300},
        "slow": {
            "command": "python3 -m pytest -m slow",
            "trigger_change_classes": ["spawn.py", "tests/test_spawn.py"],
        },
    }
    contract = parse_contract(raw)
    assert contract is not None

    assert select_tier(contract, ["spawn.py"]) == "slow"
    assert select_tier(contract, ["tests/test_spawn.py", "README.md"]) == "slow"
    assert select_tier(contract, ["docs/handbooks/operations.md"]) == "fast"
    assert select_tier(contract, []) == "fast"


def test_no_silent_full_run(tmp_path):
    fixture_repo = tmp_path / "fixture-no-contract-repo"
    fixture_repo.mkdir()

    assert load_contract(fixture_repo) is None

    gap = no_contract_gap(fixture_repo, measured_seconds=428.76)
    assert gap["target_repo"] == str(fixture_repo)
    assert gap["contract_present"] is False
    assert gap["measured_full_run_seconds"] == 428.76
    assert "gap" in gap and str(fixture_repo) in gap["gap"]
