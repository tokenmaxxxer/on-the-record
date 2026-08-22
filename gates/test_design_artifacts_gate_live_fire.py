"""live-fire test (issue #914 mechanism b) for
gates/design_artifacts_gate.py: exercises parse_declaration/missing_artifacts
from crafted scenarios and asserts the allow vs deny outcomes actually fire.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_artifacts_gate as dag


def test_no_declaration_is_byte_inert():
    assert dag.parse_declaration("Fix the watcher pid liveness check.") is None


def test_bulleted_declaration_present_files_pass():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "docs" / "issue-1" / "design").mkdir(parents=True)
        (repo / "docs" / "issue-1" / "design" / "scenarios.md").write_text("x")
        body = ("Build the thing.\n\ndesign-artifacts:\n"
                "- docs/issue-1/design/scenarios.md\n")
        declared = dag.parse_declaration(body)
        assert declared == ["docs/issue-1/design/scenarios.md"]
        assert dag.missing_artifacts(repo, declared) == []


def test_bulleted_declaration_missing_files_flags_them():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        body = ("Build the thing.\n\ndesign-artifacts:\n"
                "- docs/issue-1/design/scenarios.md\n"
                "- docs/issue-1/design/flow.md\n")
        declared = dag.parse_declaration(body)
        missing = dag.missing_artifacts(repo, declared)
        assert missing == ["docs/issue-1/design/scenarios.md",
                            "docs/issue-1/design/flow.md"]


if __name__ == "__main__":
    test_no_declaration_is_byte_inert()
    test_bulleted_declaration_present_files_pass()
    test_bulleted_declaration_missing_files_flags_them()
    print("ok")
