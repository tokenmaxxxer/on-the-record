import os, subprocess, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import measure_skill_reflection as msr

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
WITH_SKILLS = os.path.join(FIXTURE_DIR, "skill_reflection_with_skills.session.log")
NO_SKILLS = os.path.join(FIXTURE_DIR, "skill_reflection_no_skills.session.log")
WITH_ARTIFACTS = os.path.join(FIXTURE_DIR, "skill_reflection_artifacts_session.session.log")
ARTIFACTS_WORKSPACE = os.path.join(FIXTURE_DIR, "skill_reflection_artifacts_workspace")
EMPTY_DELIVERABLE = os.path.join(FIXTURE_DIR, "skill_reflection_empty_deliverable_session.session.log")


def make_code_workspace(tmp_path):
    """Build a throwaway git repo with one commit, for the code-shaped
    deliverable fallback (issue #2038). Built at test time rather than
    checked in as a fixture, since a nested .git under gates/fixtures
    would stage as a submodule gitlink instead of real file content."""
    workspace = str(tmp_path / "code_workspace")
    os.makedirs(workspace)
    run = lambda *cmd: subprocess.run(cmd, cwd=workspace, check=True,
                                       capture_output=True, text=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    with open(os.path.join(workspace, "foo.py"), "w") as fh:
        fh.write("def add(a, b):\n    return a + b\n")
    run("git", "add", "foo.py")
    run("git", "commit", "-q", "-m", "add foo.add helper")
    return workspace


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


def test_parse_consult_output_extracts_prose_from_pretty_json():
    import json as _json
    raw = _json.dumps(
        {"answer": "no", "confidence": "high",
         "caveats": ["deliverable never cites the skill's rule"]},
        indent=2,
    )
    result = msr.parse_consult_output(raw)
    assert result["verdict"] == "no"
    assert result["evidence"] == "deliverable never cites the skill's rule"
    assert '"answer"' not in result["evidence"]
    assert "{" not in result["evidence"]


def test_parse_consult_output_no_caveats_yields_no_rationale_marker():
    import json as _json
    raw = _json.dumps({"answer": "yes", "confidence": "low", "caveats": []}, indent=2)
    result = msr.parse_consult_output(raw)
    assert result["verdict"] == "yes"
    assert result["evidence"] == "judge-gave-no-rationale"


def test_parse_consult_output_unparseable_falls_back_to_partial():
    result = msr.parse_consult_output("not json at all")
    assert result["verdict"] == "partial"
    assert result["evidence"] == "judge-gave-no-rationale"
    assert "{" not in result["evidence"]


def test_score_skill_2_judge_panel_split_yields_partial():
    judge_fn = make_judge([
        {"verdict": "yes", "evidence": "e1"},
        {"verdict": "no", "evidence": "e2"},
    ])
    row = msr.score_skill("some-skill", "text", judge_fn, panel_size=2)
    assert row["reflected"] == "partial"
    assert len(row["votes"]) == 2


def test_parse_pairing_lines_extracts_artifact_skill_pairs():
    _, text = msr.extract_session(WITH_ARTIFACTS)
    pairings = msr.parse_pairing_lines(text)
    assert pairings == [
        {"artifact": "plan/ia.md", "skill": "implementation-blueprint"},
        {"artifact": "plan/missing.md", "skill": "implementation-blueprint"},
    ]


def test_parse_pairing_lines_empty_when_no_marker_block():
    assert msr.parse_pairing_lines("no pairing lines here") == []


def test_read_artifact_returns_none_for_missing_file():
    assert msr.read_artifact(ARTIFACTS_WORKSPACE, "plan/missing.md") is None


def test_read_artifact_returns_file_text():
    text = msr.read_artifact(ARTIFACTS_WORKSPACE, "plan/ia.md")
    assert "Navigation depth" in text


def test_score_artifact_missing_file_yields_absent_with_no_judge_call():
    calls = []

    def judge_fn(skill, lens, artifact_text):
        calls.append((skill, lens, artifact_text))
        raise AssertionError("judge_fn must not be called for a missing artifact")

    row = msr.score_artifact("plan/missing.md", "implementation-blueprint", None,
                              judge_fn, panel_size=3)
    assert row["verdict"] == "absent"
    assert row["votes"] == []
    assert calls == []


def test_score_artifact_full_majority():
    judge_fn = make_judge([
        {"verdict": "full", "evidence": "e1"},
        {"verdict": "full", "evidence": "e2"},
        {"verdict": "partial", "evidence": "e3"},
    ])
    row = msr.score_artifact("plan/ia.md", "implementation-blueprint", "text",
                              judge_fn, panel_size=3)
    assert row["verdict"] == "full"
    assert row["evidence"] == "e1"
    assert len(row["votes"]) == 3


def test_score_artifact_receives_only_one_skill_and_one_artifact_text():
    seen = []

    def judge_fn(skill, lens, artifact_text):
        seen.append((skill, lens, artifact_text))
        return {"verdict": "full", "evidence": "ok"}

    msr.score_artifact("plan/ia.md", "implementation-blueprint", "the artifact text",
                        judge_fn, panel_size=3)
    for skill, lens, artifact_text in seen:
        assert skill == "implementation-blueprint"
        assert artifact_text == "the artifact text"
        assert "plan/missing.md" not in artifact_text
        assert "implementation-blueprint" == skill  # never the full skill list


def test_reflect_artifacts_measured_from_workspace():
    judge_fn = make_judge([
        {"verdict": "full", "evidence": "e1"},
        {"verdict": "full", "evidence": "e2"},
        {"verdict": "full", "evidence": "e3"},
    ])
    result = msr.reflect_artifacts(WITH_ARTIFACTS, ARTIFACTS_WORKSPACE, judge_fn=judge_fn,
                                    panel_size=3)
    assert result["status"] == "measured"
    assert len(result["rows"]) == 2
    present = next(r for r in result["rows"] if r["artifact"] == "plan/ia.md")
    absent = next(r for r in result["rows"] if r["artifact"] == "plan/missing.md")
    assert present["verdict"] == "full"
    assert present["evidence"] == "e1"
    assert absent["verdict"] == "absent"
    assert absent["votes"] == []


def test_reflect_artifacts_not_applicable_when_no_pairing_lines():
    result = msr.reflect_artifacts(NO_SKILLS, ARTIFACTS_WORKSPACE, judge_fn=make_judge([]))
    assert result == {"path": NO_SKILLS, "status": "not-applicable",
                       "reason": "no-pairing-lines"}


def test_reflect_session_empty_deliverable_no_workspace_refuses(tmp_path):
    calls = []

    def judge_fn(skill, lens, deliverable_text):
        calls.append((skill, lens, deliverable_text))
        raise AssertionError("judge_fn must not be called with an empty deliverable")

    result = msr.reflect_session(EMPTY_DELIVERABLE, judge_fn=judge_fn)
    assert result["status"] == "no-deliverable-extracted"
    assert result["rows"] == []
    assert calls == []


def test_reflect_session_empty_deliverable_falls_back_to_workspace_diff(tmp_path):
    workspace = make_code_workspace(tmp_path)
    seen = []

    def judge_fn(skill, lens, deliverable_text):
        seen.append(deliverable_text)
        return {"verdict": "yes", "evidence": "code diff shows foo.add helper"}

    result = msr.reflect_session(EMPTY_DELIVERABLE, judge_fn=judge_fn,
                                  workspace_root=workspace)
    assert result["status"] == "measured"
    assert len(result["rows"]) == 1
    assert result["rows"][0]["reflected"] == "yes"
    assert seen, "judge_fn should have been called with the diff-backed deliverable"
    for text in seen:
        assert "workspace final commit diff" in text
        assert "foo.add helper" in text


def test_get_final_commit_diff_returns_none_for_non_git_dir(tmp_path):
    assert msr.get_final_commit_diff(str(tmp_path)) is None


def test_get_final_commit_diff_returns_none_for_missing_workspace():
    assert msr.get_final_commit_diff(None) is None
    assert msr.get_final_commit_diff("/no/such/path") is None


if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call(["python3", "-m", "pytest", "-o", "addopts=", __file__, "-v"]))
