"""issue #2013 phase 2: gates/design_artifacts_gate.py 를 검증한다.

acceptance(docs/issue-2013/proposals/design-artifact-existence-gate.md
"How you'll know it worked"): 선언된 경로가 없는(missing) 경우 각 경로를
이름으로 거부, 선언된 경로가 모두 있는(present) 경우 통과, 선언 자체가
없는(undeclared) 이슈는 아무 것도 안 하는 세 경로 모두를 커버한다.
fail-closed 승인 amendment(이슈 #2013 코멘트, 2026-08-22): `gh` 본문
조회 자체가 실패하면 빈 리스트가 아니라 실행 가능한 거부 메시지를
내야 한다.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gates"))
import design_artifacts_gate as dag


class ParseDeclarationTest(unittest.TestCase):
    def test_no_tag_returns_none(self):
        self.assertIsNone(dag.parse_declaration("Fix the watcher pid liveness check."))

    def test_bulleted_list_is_parsed_in_order(self):
        body = ("Build the thing.\n\ndesign-artifacts:\n"
                "- docs/issue-9/design/scenarios.md\n"
                "- docs/issue-9/design/ia.md\n")
        self.assertEqual(
            dag.parse_declaration(body),
            ["docs/issue-9/design/scenarios.md", "docs/issue-9/design/ia.md"])

    def test_fenced_block_is_parsed(self):
        body = ("Build the thing.\n\ndesign-artifacts:\n"
                "```\n"
                "docs/issue-9/design/scenarios.md\n"
                "docs/issue-9/design/ia.md\n"
                "```\n")
        self.assertEqual(
            dag.parse_declaration(body),
            ["docs/issue-9/design/scenarios.md", "docs/issue-9/design/ia.md"])

    def test_tag_with_no_following_list_yields_empty_list(self):
        body = "Build the thing.\n\ndesign-artifacts:\n\nSome other paragraph.\n"
        self.assertEqual(dag.parse_declaration(body), [])

    def test_one_line_comma_form_parses_as_none(self):
        # issue #2037: this shape falls through to None -- malformed_declaration_line
        # is what catches it and refuses loudly, not parse_declaration itself.
        body = "Build the thing.\n\ndesign-artifacts: a.md, b.md, c.md\n"
        self.assertIsNone(dag.parse_declaration(body))


class MalformedDeclarationLineTest(unittest.TestCase):
    def test_one_line_comma_form_is_flagged(self):
        body = "Build the thing.\n\ndesign-artifacts: a.md, b.md, c.md\n"
        self.assertEqual(dag.malformed_declaration_line(body),
                          "design-artifacts: a.md, b.md, c.md")

    def test_well_formed_bulleted_declaration_is_not_flagged(self):
        body = "Build.\n\ndesign-artifacts:\n- a.md\n- b.md\n"
        self.assertIsNone(dag.malformed_declaration_line(body))

    def test_no_token_is_not_flagged(self):
        self.assertIsNone(dag.malformed_declaration_line("Fix the watcher pid liveness check."))


class MissingArtifactsTest(unittest.TestCase):
    def test_all_present_yields_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a.md").write_text("x")
            (repo / "b.md").write_text("x")
            self.assertEqual(dag.missing_artifacts(repo, ["a.md", "b.md"]), [])

    def test_missing_subset_is_returned_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "a.md").write_text("x")
            self.assertEqual(
                dag.missing_artifacts(repo, ["a.md", "b.md", "c.md"]),
                ["b.md", "c.md"])


class CheckAcceptancePathsTest(unittest.TestCase):
    def test_undeclared_issue_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(dag.gh_rest, "fetch_issue_body",
                                   return_value="Fix the watcher pid liveness check."):
            self.assertEqual(dag.check(Path(tmp), 1), [])

    def test_declared_and_present_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "scenarios.md").write_text("x")
            body = "Build.\n\ndesign-artifacts:\n- scenarios.md\n"
            with mock.patch.object(dag.gh_rest, "fetch_issue_body", return_value=body):
                self.assertEqual(dag.check(repo, 2), [])

    def test_declared_and_missing_names_each_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            body = "Build.\n\ndesign-artifacts:\n- scenarios.md\n- flow.md\n"
            with mock.patch.object(dag.gh_rest, "fetch_issue_body", return_value=body):
                violations = dag.check(repo, 3)
            self.assertEqual(len(violations), 1)
            self.assertIn("scenarios.md", violations[0])
            self.assertIn("flow.md", violations[0])

    def test_declared_one_line_comma_form_refuses_loudly(self):
        # issue #2037 acceptance: a one-line "design-artifacts: a.md, b.md"
        # declaration must refuse quoting the required tag+bullet shape,
        # not silently pass as an undeclared issue.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            body = "Build.\n\ndesign-artifacts: a.md, b.md\n"
            with mock.patch.object(dag.gh_rest, "fetch_issue_body", return_value=body):
                violations = dag.check(repo, 5)
            self.assertEqual(len(violations), 1)
            self.assertIn("design-artifacts:", violations[0])
            self.assertIn("- path/one.md", violations[0])

    def test_fetch_failure_fails_closed_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(dag.gh_rest, "fetch_issue_body", return_value=None):
            violations = dag.check(Path(tmp), 4)
            self.assertEqual(len(violations), 1)
            self.assertIn("#4", violations[0])
            self.assertIn("fail-closed", violations[0].lower())


if __name__ == "__main__":
    unittest.main()
