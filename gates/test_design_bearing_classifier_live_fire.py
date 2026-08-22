"""live-fire test (issue #914 mechanism b) for
gates/design_bearing_classifier.py: calls the module's own checking
function from >= 2 distinct crafted scenarios and asserts the allow
(not design-bearing) vs deny (design-bearing) outcomes actually fire.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design_bearing_classifier as dbc


def test_mechanical_body_is_allowed_not_design_bearing():
    verdict = dbc.check_issue_body(
        9999001,
        "Fix the watcher pid liveness check in spawn.py; --rearm "
        "must replace an alive-but-silent watcher.")
    assert verdict["design_bearing"] is False


def test_design_bearing_body_is_denied_flagged_design_bearing():
    verdict = dbc.check_issue_body(
        9999002,
        "Build a landing page: storyboard, information architecture, "
        "flow diagram, HTML demo for stakeholder review.")
    assert verdict["design_bearing"] is True


if __name__ == "__main__":
    test_mechanical_body_is_allowed_not_design_bearing()
    test_design_bearing_body_is_denied_flagged_design_bearing()
    print("ok")
