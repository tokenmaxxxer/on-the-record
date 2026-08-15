"""issue #1614 requirement 3 — precision_measure.py unit tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import precision_measure as pm


def test_wilson_lower_bound_matches_known_value():
    # 90/100 successes, 90% one-sided Wilson LB is a well-known reference
    # value (~0.843), no fpc.
    lb = pm.wilson_lower_bound(90, 100)
    assert 0.83 < lb < 0.86


def test_wilson_lower_bound_zero_n_is_zero():
    assert pm.wilson_lower_bound(0, 0) == 0.0


def test_wilson_lower_bound_fpc_shrinks_interval():
    lb_no_fpc = pm.wilson_lower_bound(9, 10)
    lb_fpc = pm.wilson_lower_bound(9, 10, population=10)
    assert lb_fpc >= lb_no_fpc


def _pop(rule_counts):
    pop = []
    for rule, count in rule_counts.items():
        for i in range(count):
            pop.append({"rule": rule, "path": f"docs/issue-1/reports/r{i}.md",
                        "excerpt": f"x{i}", "violation": f"(issue #{rule})"})
    return pop


def test_stratified_sample_proportional_with_floor():
    pop = _pop({"793": 80, "870": 15, "330": 3, "333": 2})
    sample = pm.stratified_sample(pop, n=100, floor=5, seed=1)
    by_rule = {}
    for it in sample:
        by_rule[it["rule"]] = by_rule.get(it["rule"], 0) + 1
    assert by_rule.get("330", 0) >= 3  # floor 5 capped at pool size 3
    assert by_rule.get("333", 0) >= 2
    assert sum(by_rule.values()) <= 100


def test_stratified_sample_reproducible_with_seed():
    pop = _pop({"793": 40, "870": 40})
    a = pm.stratified_sample(pop, n=20, seed=42)
    b = pm.stratified_sample(pop, n=20, seed=42)
    assert [it["excerpt"] for it in a] == [it["excerpt"] for it in b]


def test_stratified_sample_empty_population():
    assert pm.stratified_sample([]) == []


def test_build_report_no_findings():
    report = pm.build_report([], {}, 0)
    assert report["status"] == "no-findings"
    assert "precision undefined" in report["message"]


def test_build_report_promotes_when_pass_rule_met():
    sample = [{"id": f"s{i}", "rule": "330"} for i in range(100)]
    judgments = {f"s{i}": "TP" for i in range(95)}
    report = pm.build_report(sample, judgments, 100)
    assert report["promote"] is True


def test_build_report_kills_low_precision_rule():
    sample = ([{"id": f"a{i}", "rule": "793"} for i in range(50)]
              + [{"id": f"b{i}", "rule": "330"} for i in range(50)])
    judgments = {f"a{i}": "FP" for i in range(50)}
    judgments.update({f"b{i}": "TP" for i in range(50)})
    report = pm.build_report(sample, judgments, 100)
    assert report["per_rule"]["793"]["kill"] is True
    assert report["promote"] is False


def test_format_report_no_findings_message():
    text = pm.format_report({"status": "no-findings",
                              "message": "no findings — precision undefined, promotion not applicable"})
    assert "not applicable" in text


if __name__ == "__main__":
    import traceback
    tests = [(n, f) for n, f in globals().items()
             if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
        else:
            print(f"ok {name}")
    print(f"{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
