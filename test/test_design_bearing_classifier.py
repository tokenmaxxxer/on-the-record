"""issue #2012 phase 2: gates/design_bearing_classifier.py 를 검증한다.

acceptance: 기계적 코퍼스(#1975/#1635/#1596/#1742, 이 저장소의 실제
이슈) 각 행이 개별적으로 design_bearing=False 를 내야 하고(오탐 0 —
precision-first), 디자인 개입 코퍼스(구성된 픽스처 A/B/C + 소비자
저장소의 실제 디자인 개입 이슈 tokenmaxxxer/tm-webfolio#1) 각 행이
design_bearing=True 와 비어있지 않은 근거를 내야 하며, override 경로
두 방향(기계적 본문에 yes 강제, 디자인 개입 본문에 no 강제) 모두 스코어
대신 override 태그 자체를 근거로 인용해야 한다. 근거 코퍼스는
docs/issue-2012/reports/implementation/corpus.md 에 있다.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "gates"))
import design_bearing_classifier as dbc


class TokenizeTest(unittest.TestCase):
    def test_lowercases_splits_nonalnum_and_drops_stopwords(self):
        self.assertEqual(
            dbc._tokenize("Use when a Landing Page needs Contrast."),
            {"landing", "page", "needs", "contrast"})

    def test_empty_text_yields_empty_set(self):
        self.assertEqual(dbc._tokenize(""), set())


class DesignBearingScoreTest(unittest.TestCase):
    def test_matching_keywords_are_counted_and_sorted(self):
        overlap, matched = dbc._design_bearing_score(
            "Needs a wireframe and a storyboard for the landing page.")
        self.assertEqual(matched, sorted(matched))
        self.assertEqual(set(matched), {"wireframe", "storyboard", "landing", "page"})
        self.assertEqual(overlap, 4)

    def test_no_match_yields_zero_overlap_empty_evidence(self):
        overlap, matched = dbc._design_bearing_score(
            "Fix the watcher pid liveness check in spawn.py.")
        self.assertEqual(overlap, 0)
        self.assertEqual(matched, [])


# 기계적 코퍼스 — 이 저장소의 실제 이슈 4건, 본문 발췌는
# docs/issue-2012/reports/implementation/corpus.md 를 그대로 따른다.
# 각 행이 개별 테스트인 이유: 향후 키워드 추가가 이 중 하나를 깨면
# 집계 카운트가 아니라 개별 실패로 드러나야 한다(제안서 What will be
# done).
class MechanicalCorpusTest(unittest.TestCase):
    def test_issue_1975_watcher_rearm_is_not_design_bearing(self):
        body = (
            "Observed live 2026-08-22 during issue-1959: the poll-report "
            "flagged 'watcher-silent: watcher pid 2119052 alive but 92min "
            "log-silent' and prescribed --rearm, but --rearm refused. "
            "Requirement: --rearm (or a new flag) must be able to replace "
            "an alive-but-silent watcher when its event log has been quiet "
            "longer than a threshold while the session log grew.")
        verdict = dbc.check_issue_body(1975, body)
        self.assertFalse(verdict["design_bearing"])
        self.assertEqual(verdict["evidence"], [])
        self.assertFalse(verdict["override"])

    def test_issue_1635_record_enums_bucketed_enum_fp_is_not_design_bearing(self):
        body = (
            "gates/gates.py record_enums iterates record_fields and treats "
            "a role spec's BUCKETED loop_state dict as a flat allow-list, "
            "so it checks value not in <dict keys> and flags a genuinely "
            "valid terminal value like handed-off as an enum violation.")
        verdict = dbc.check_issue_body(1635, body)
        self.assertFalse(verdict["design_bearing"])
        self.assertEqual(verdict["evidence"], [])
        self.assertFalse(verdict["override"])

    def test_issue_1596_record_lint_violation_is_not_design_bearing(self):
        body = (
            "Fingerprint: e2e53e107f80989c27afab436d7d71b61b3872c977e5c95c8b4c0e2222691863\n"
            "Rule / baseline ID: judge:test-authoring / record-lint-violation\n"
            "Location: docs/issue-831/reports/architecture.md@scan\n"
            "Evidence: [e2e-demo 2026-08-15] loop_state: done\n"
            "Proposed direction: address the record-lint-violation finding "
            "at the flagged location per the judge:test-authoring rule "
            "that flagged it.")
        verdict = dbc.check_issue_body(1596, body)
        # calibration-critical row: hits 'architecture' + 'demo' (overlap 2),
        # still below the >=3 threshold.
        self.assertFalse(verdict["design_bearing"])
        self.assertEqual(set(verdict["evidence"]), {"architecture", "demo"})
        self.assertFalse(verdict["override"])

    def test_issue_1742_skills_mount_phase1_is_not_design_bearing(self):
        body = (
            "Program context: dissolve the role/rulebook layer into a "
            "single skill axis. Operator hard constraint: convention "
            "adjustments must introduce ZERO bugs/conflicts - role-name "
            "remains the load-bearing identity string until every "
            "consumer reads the new fields. check: "
            "test/test_spawn_skills_mount.py (argv/env/workspace-layout "
            "assertions for both cases).")
        verdict = dbc.check_issue_body(1742, body)
        self.assertFalse(verdict["design_bearing"])
        self.assertEqual(set(verdict["evidence"]), {"identity", "layout"})
        self.assertFalse(verdict["override"])


# 디자인 개입 코퍼스 — 구성된 픽스처 3건 + 소비자 저장소의 실제 디자인
# 개입 이슈 1건(운영자 phase-2 승인 amendment).
class DesignBearingCorpusTest(unittest.TestCase):
    def test_fixture_a_landing_page_build_is_design_bearing(self):
        body = (
            "Build a landing page for the product: hero section, features "
            "grid, testimonials, and a footer. Needs a storyboard and "
            "information architecture pass before implementation - sketch "
            "the user flow from landing to signup, then a wireframe of "
            "each breakpoint (mobile/tablet/desktop) and an HTML demo for "
            "stakeholder review.")
        verdict = dbc.check_issue_body(90001, body)
        self.assertTrue(verdict["design_bearing"])
        self.assertTrue(verdict["evidence"])
        self.assertFalse(verdict["override"])

    def test_fixture_b_brand_identity_asset_is_design_bearing(self):
        body = (
            "Design a new brand identity: logo mark, color palette, and "
            "an SVG icon system. Deliverable includes a visual design "
            "mockup and a UI style guide (typography, spacing, layout "
            "grid) for downstream teams to apply consistently across "
            "surfaces.")
        verdict = dbc.check_issue_body(90002, body)
        self.assertTrue(verdict["design_bearing"])
        self.assertTrue(verdict["evidence"])
        self.assertFalse(verdict["override"])

    def test_fixture_c_k8s_platform_topology_design_is_design_bearing(self):
        body = (
            "Design the platform topology: a flow diagram of service "
            "boundaries and data paths, user scenarios for the three "
            "primary operator personas, and an information architecture "
            "for the ops dashboard UX before any manifests are written.")
        verdict = dbc.check_issue_body(90003, body)
        self.assertTrue(verdict["design_bearing"])
        self.assertTrue(verdict["evidence"])
        self.assertFalse(verdict["override"])

    def test_real_consumer_repo_exemplar_tm_webfolio_1_is_design_bearing(self):
        # tokenmaxxxer/tm-webfolio#1, fetched live 2026-08-22 via
        # `gh issue view 1 -R tokenmaxxxer/tm-webfolio --json body` —
        # the operator's phase-2 amendment: at least one real
        # consumer-repo design-bearing exemplar in the corpus and its
        # own test row.
        body = (
            "Build the landing page: semantic HTML (header/hero, "
            "projects grid of 6 placeholder cards, contact footer), "
            "responsive at 360/768/1280 via CSS grid/flex (no framework, "
            "no build step), accessible baseline (landmarks, alt text, "
            "focus-visible, color contrast tokens), and a small "
            "vanilla-JS theme toggle persisting via localStorage.")
        verdict = dbc.check_issue_body(1, body)
        self.assertTrue(verdict["design_bearing"])
        self.assertEqual(set(verdict["evidence"]), {"html", "landing", "page"})
        self.assertFalse(verdict["override"])


class OverridePathTest(unittest.TestCase):
    def test_override_yes_forces_design_bearing_on_mechanical_shaped_body(self):
        body = (
            "Fix the watcher pid liveness check in spawn.py.\n\n"
            "design-bearing-override: yes\n")
        verdict = dbc.check_issue_body(2, body)
        self.assertTrue(verdict["design_bearing"])
        self.assertTrue(verdict["override"])
        self.assertEqual(verdict["evidence"], ["design-bearing-override: yes"])

    def test_override_no_forces_not_design_bearing_on_design_shaped_body(self):
        body = (
            "Design a new brand identity: logo mark, visual mockup, UI "
            "layout, and information architecture storyboard.\n\n"
            "design-bearing-override: no\n")
        verdict = dbc.check_issue_body(3, body)
        self.assertFalse(verdict["design_bearing"])
        self.assertFalse(verdict["override"])
        self.assertEqual(verdict["evidence"], ["design-bearing-override: no"])


if __name__ == "__main__":
    unittest.main()
