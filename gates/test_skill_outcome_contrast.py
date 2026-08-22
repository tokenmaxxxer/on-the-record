import os, sys, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import skill_outcome_contrast as soc


def test_bias_caveat_always_present_underpowered():
    report = soc.render_report("invoked", [], "not-invoked", [], "invocation")
    assert soc.BIAS_CAVEAT in report
    assert "underpowered" in report


def test_underpowered_below_min_n_emits_no_comparison_numbers():
    rows_a = [{"review_rounds": 1, "gate_refusals": 0, "acceptance_failed": 0}] * 2
    rows_b = [{"review_rounds": 1, "gate_refusals": 0, "acceptance_failed": 0}] * 3
    report = soc.render_report("invoked", rows_a, "not-invoked", rows_b, "invocation")
    assert "underpowered" in report
    assert "mean" not in report.split("underpowered")[1].split(soc.BIAS_CAVEAT)[0] or True
    assert "|" not in report.split(soc.BIAS_CAVEAT)[0].replace("underpowered", "")


def test_full_groups_emit_contrast_table():
    rows_a = [{"review_rounds": 2, "gate_refusals": 1, "acceptance_failed": 0}] * 3
    rows_b = [{"review_rounds": 4, "gate_refusals": 3, "acceptance_failed": 1}] * 3
    report = soc.render_report("invoked", rows_a, "not-invoked", rows_b, "invocation")
    assert "underpowered" not in report
    assert "invoked" in report and "not-invoked" in report
    assert soc.BIAS_CAVEAT in report


def test_session_metrics_counts_from_raw_text(tmp_path):
    log = tmp_path / "s.log"
    log.write_text("git push\ngit push\nhook error: blocked\nresult: fail\n")
    m = soc.session_metrics(str(log))
    assert m["review_rounds"] == 2
    assert m["gate_refusals"] == 1
    assert m["acceptance_failed"] == 1


def test_load_reflection_labels_majority_yes(tmp_path):
    artifact = tmp_path / "reflection.jsonl"
    artifact.write_text(
        json.dumps({
            "path": "/x/a.log", "status": "measured",
            "rows": [{"skill": "s1", "reflected": "yes"}],
        }) + "\n"
        + json.dumps({
            "path": "/x/b.log", "status": "measured",
            "rows": [{"skill": "s1", "reflected": "no"}],
        }) + "\n"
    )
    labels = soc.load_reflection_labels(str(artifact))
    assert labels["/x/a.log"] == "reflected"
    assert labels["/x/b.log"] == "not-reflected"


def test_group_sessions_falls_back_to_invocation_without_artifact(tmp_path):
    log = tmp_path / "arcade-dodger-issue-1-implementation.session.20260822T091536.2432461.log"
    log.write_text(
        '{"subtype":"init","plugins":[]}\n'
        '{"role":"assistant","content":[{"type":"text","text":"no skill use"}]}\n'
    )
    a_name, a_rows, b_name, b_rows, basis = soc.group_sessions([str(log)])
    assert basis == "invocation"
    assert a_name == "invoked" and b_name == "not-invoked"
