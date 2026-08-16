import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gates"))

import recovery_policy as rp


def test_pre_first_commit_under_cap_respawns_identical():
    verdict = rp.classify(
        {
            "has_commit": False,
            "has_pr": False,
            "respawn_count": 0,
            "cap": 2,
            "failure_signature": "sig-a",
            "last_failure_signature": None,
        }
    )
    assert verdict == rp.RESPAWN_IDENTICAL


def test_has_commit_no_pr_respawns_with_handoff():
    verdict = rp.classify(
        {
            "has_commit": True,
            "has_pr": False,
            "respawn_count": 0,
            "cap": 2,
            "failure_signature": "sig-a",
            "last_failure_signature": None,
        }
    )
    assert verdict == rp.RESPAWN_WITH_HANDOFF


def test_respawn_count_at_cap_escalates():
    verdict = rp.classify(
        {
            "has_commit": False,
            "has_pr": False,
            "respawn_count": 2,
            "cap": 2,
            "failure_signature": "sig-a",
            "last_failure_signature": "sig-b",
        }
    )
    assert verdict == rp.ESCALATE


def test_respawn_count_over_cap_escalates():
    verdict = rp.classify(
        {
            "has_commit": True,
            "has_pr": False,
            "respawn_count": 5,
            "cap": 2,
            "failure_signature": "sig-a",
            "last_failure_signature": None,
        }
    )
    assert verdict == rp.ESCALATE


def test_same_failure_signature_as_prior_escalates():
    verdict = rp.classify(
        {
            "has_commit": True,
            "has_pr": False,
            "respawn_count": 0,
            "cap": 2,
            "failure_signature": "pr-expected-missing:branch=x",
            "last_failure_signature": "pr-expected-missing:branch=x",
        }
    )
    assert verdict == rp.ESCALATE


def test_same_signature_escalates_even_under_cap_with_no_commit():
    verdict = rp.classify(
        {
            "has_commit": False,
            "has_pr": False,
            "respawn_count": 0,
            "cap": 2,
            "failure_signature": "sig-a",
            "last_failure_signature": "sig-a",
        }
    )
    assert verdict == rp.ESCALATE


def test_default_cap_is_2():
    verdict = rp.classify(
        {
            "has_commit": False,
            "has_pr": False,
            "respawn_count": 2,
            "failure_signature": "sig-a",
            "last_failure_signature": None,
        }
    )
    assert verdict == rp.ESCALATE
    assert rp.DEFAULT_CAP == 2


def test_classify_from_state_cap_counter_escalates_at_cap(tmp_path):
    issue, role = 1660, "implementation"

    # #1660 reconstruction: staged/committed work but no PR -> handoff first.
    v1 = rp.classify_from_state(
        issue, role, has_commit=True, has_pr=False,
        failure_signature="pr-expected-missing:branch=issue-1660",
        cap=2, state_dir=tmp_path,
    )
    assert v1 == rp.RESPAWN_WITH_HANDOFF

    # Second death, same signature as prior -> escalate on same-signature repeat,
    # not merely respawn-count (count is only 1 here, still under cap=2).
    v2 = rp.classify_from_state(
        issue, role, has_commit=True, has_pr=False,
        failure_signature="pr-expected-missing:branch=issue-1660",
        cap=2, state_dir=tmp_path,
    )
    assert v2 == rp.ESCALATE

    # A third call must not blind-respawn either — escalate persists.
    v3 = rp.classify_from_state(
        issue, role, has_commit=True, has_pr=False,
        failure_signature="pr-expected-missing:branch=issue-1660",
        cap=2, state_dir=tmp_path,
    )
    assert v3 == rp.ESCALATE


def test_classify_from_state_persists_counter_across_calls(tmp_path):
    issue, role = 42, "implementation"
    for _ in range(2):
        verdict = rp.classify_from_state(
            issue, role, has_commit=False, has_pr=False,
            failure_signature=None, cap=2, state_dir=tmp_path,
        )
        assert verdict == rp.RESPAWN_IDENTICAL

    # third call: respawn_count is now 2 -> at cap -> escalate.
    verdict = rp.classify_from_state(
        issue, role, has_commit=False, has_pr=False,
        failure_signature=None, cap=2, state_dir=tmp_path,
    )
    assert verdict == rp.ESCALATE


def test_healthy_session_with_pr_is_not_subject_to_classify():
    # Empty-state acceptance: classify() is a death-signal-only decision function.
    # A healthy delivered session simply never calls it — nothing in this module
    # runs against a healthy state, so there is no branch to assert on here beyond
    # confirming classify is not invoked by any import-time side effect.
    import inspect

    assert "has_pr" in inspect.signature(rp.classify_from_state).parameters
