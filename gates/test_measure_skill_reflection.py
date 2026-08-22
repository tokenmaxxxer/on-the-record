import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import measure_skill_reflection as msr

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
WITH_SKILLS = os.path.join(FIXTURE_DIR, "skill_reflection_with_skills.session.log")
NO_SKILLS = os.path.join(FIXTURE_DIR, "skill_reflection_no_skills.session.log")


def make_judge(sequence):
    calls = iter(sequence)

    def judge_fn(skill, lens, deliverable_text):
        return next(calls)

    return judge_fn


def test_majority_2_1_split():
    votes = [
        {"verdict": "yes", "evidence": "e1"},
        {"verdict": "yes", "evidence": "e2"},
        {"verdict": "no", "evidence": "e3"},
    ]
    reflected, evidence = msr.majority(votes)
    assert reflected == "yes"
    assert evidence == "e1"


def test_majority_2_judge_even_split_is_partial():
    votes = [
        {"verdict": "yes", "evidence": "e1"},
        {"verdict": "no", "evidence": "e2"},
    ]
    reflected, evidence = msr.majority(votes)
    assert reflected == "partial"


def test_majority_3_way_tie_is_partial():
    votes = [
        {"verdict": "yes", "evidence": "e1"},
        {"verdict": "no", "evidence": "e2"},
        {"verdict": "partial", "evidence": "e3"},
    ]
    reflected, evidence = msr.majority(votes)
    assert reflected == "partial"


def test_reflect_session_with_mounted_skills_uses_judge_panel():
    judge_fn = make_judge([
        {"verdict": "yes", "evidence": "e1"},
        {"verdict": "yes", "evidence": "e2"},
        {"verdict": "no", "evidence": "e3"},
    ])
    result = msr.reflect_session(WITH_SKILLS, judge_fn=judge_fn, panel_size=3)
    assert result["status"] == "measured"
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert row["skill"] == "implementation-blueprint"
    assert row["reflected"] == "yes"
    assert row["evidence"] == "e1"
    assert len(row["votes"]) == 3


def test_reflect_session_zero_mounted_skills_yields_not_applicable_row():
    result = msr.reflect_session(NO_SKILLS, judge_fn=make_judge([]))
    assert result == {"path": NO_SKILLS, "status": "not-applicable",
                       "reason": "no-mounted-skills"}


def test_score_skill_2_judge_panel_split_yields_partial():
    judge_fn = make_judge([
        {"verdict": "yes", "evidence": "e1"},
        {"verdict": "no", "evidence": "e2"},
    ])
    row = msr.score_skill("some-skill", "text", judge_fn, panel_size=2)
    assert row["reflected"] == "partial"
    assert len(row["votes"]) == 2


if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call(["python3", "-m", "pytest", "-o", "addopts=", __file__, "-v"]))
