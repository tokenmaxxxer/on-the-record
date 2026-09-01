"""Issue #2982: `spawn.py --skill-candidates` (`rank_skills()`, consult.py)
must report "no-candidates" when every BM25 candidate falls below a
calibrated relevance floor, instead of a confident-looking ranked list of
unrelated skills -- the recall failure the issue's two regression cases
document. The judge/rerank path is untouched: this is a BM25-stage floor
only, scoped to `use_judge=False` (the `--skill-candidates` default), never
applied to spawn's own internal cross-family mount
(`_cross_family_skill_matches_with_consult()` calls
`_bm25_cross_family_scores()` directly and never passes through here).

Floor derivation (docs/issue-2982/reports/): measured against the live
skill-repository corpus (~270 skills), every real (issue, applied-skill)
pair from this repo's own `skill-verdict: <skill> -- applied: invoked`
records, replayed as a BM25 query and kept where the applied skill was the
genuine top-1 pick, scored >= 16.963. Every real, independently-written
task description with no on-topic skill in the corpus -- including this
issue's own two reported regressions -- scored top-1 <= 15.134.
`consult._SKILL_CANDIDATES_RELEVANCE_FLOOR = 16.0` sits in that measured
gap; `SkillCandidatesFloorCalibratedTest` pins the gap itself so a future
edit to the constant that breaks the measured separation fails loud here.

Run: python3 -m pytest tests/test_skill_candidates_floor.py -q
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class SkillCandidatesFloorTest(unittest.TestCase):
    """Issue #2982: a ranking whose candidates all fall below the
    calibrated relevance floor (`consult._SKILL_CANDIDATES_RELEVANCE_FLOOR`)
    is reported as "no-candidates" rather than as a confident-looking
    ranked list -- and a task with a strong match still ranks as today
    (empty state -- the floor must not eat genuine matches)."""

    def test_skill_candidates_floor_suppresses_all_low_score_candidates(self):
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR - 0.001,
                                   "weak-skill", scored_dir, "skill-repo")]):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result, {"ranked": [], "outcome": "no-candidates",
                                  "picked": []})

    def test_skill_candidates_floor_strong_match_still_ranks_as_today(self):
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR + 0.001,
                                   "strong-skill", scored_dir, "skill-repo")]):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")
        self.assertEqual([r["name"] for r in result["ranked"]], ["strong-skill"])

    def test_skill_candidates_floor_judge_path_is_unaffected(self):
        # must not: the judge/rerank path is not the fix for a recall
        # problem (issue #2982) -- the floor is scoped to use_judge=False
        # only, so a low-scoring BM25 pass-through to the judge is
        # unchanged by this issue.
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR - 0.001,
                                   "weak-skill", scored_dir, "skill-repo")]), \
             mock.patch.object(spawn, "_skill_judge_consult",
                               return_value=([scored_dir], "detail")):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"),
                                       issue=2678, cwd="/tmp", use_judge=True)
        self.assertNotEqual(result["outcome"], "no-candidates")
        self.assertEqual([r["name"] for r in result["ranked"]], ["weak-skill"])


class SkillCandidatesFloorCalibratedTest(unittest.TestCase):
    """Issue #2982: the floor must come from measurement over recorded
    task/selection pairs, not a freehand number. This test embeds the
    measured data points the floor was actually derived from (full
    derivation: docs/issue-2982/reports/) and checks the shipped constant
    against them directly, so a future change to the constant that breaks
    the measured separation fails loud here rather than silently drifting.

    POSITIVES: real (issue, applied skill) pairs pulled from this repo's
    own skill-verdict records (`skill-verdict: <skill> -- applied:
    invoked`), replayed as the issue's title against the live
    skill-repository corpus, kept where the applied skill was the
    BM25 top-1 pick (a genuine on-topic match, not a recall miss).
    NEGATIVES: real task descriptions (the two regressions this issue
    reports, plus independently-written jargon-heavy task text) replayed
    the same way, top-1 score kept -- none of these tasks has an on-topic
    match anywhere in the current corpus."""

    POSITIVE_TOP1_SCORES = [
        22.873312031309496,   # architecture-interface-contract-shape
        23.89840150795929,    # test-depth-audit
        51.663619541370785,   # test-derivation
        19.71452027269867,    # silent-failure-audit
        16.963157077618174,   # adversarial-review
        44.82385367480575,    # knowledge-management-taxonomy-tagging
        19.39626174860225,    # secure-coding-input-validation-injection-defense
    ]
    NEGATIVE_TOP1_SCORES = [
        15.134316351480955,   # top1=agent-coordination (workspace-preservation task)
        7.911048066340095,    # top1=secure-coding-session-authentication (200-turn-cap task)
        12.050935130438033,   # top1=agent-coordination
        11.61075563596152,    # top1=design-artifact-user-flow
        10.69661598388458,    # top1=test-depth-audit
        13.696502243775724,   # top1=user-discovery-saturation-stopping-rule
    ]

    def test_skill_candidates_floor_calibrated_separates_measured_pairs(self):
        floor = spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR
        self.assertGreater(min(self.POSITIVE_TOP1_SCORES), floor,
                            "floor must not suppress the weakest measured genuine match")
        self.assertLess(max(self.NEGATIVE_TOP1_SCORES), floor,
                         "floor must suppress the strongest measured false-positive top score")

    def test_skill_candidates_floor_calibrated_classifies_each_measured_pair(self):
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        for score in self.POSITIVE_TOP1_SCORES:
            with mock.patch.object(
                    spawn, "_bm25_cross_family_scores",
                    lambda *a, score=score, **k: [(score, "s", scored_dir, "skill-repo")]):
                result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
            self.assertEqual(result["outcome"], "bm25-only", score)
        for score in self.NEGATIVE_TOP1_SCORES:
            with mock.patch.object(
                    spawn, "_bm25_cross_family_scores",
                    lambda *a, score=score, **k: [(score, "s", scored_dir, "skill-repo")]):
                result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
            self.assertEqual(result["outcome"], "no-candidates", score)


class SkillCandidatesRegressionCasesTest(unittest.TestCase):
    """Issue #2982's own two measured failure cases: neither returns its
    recorded unrelated top candidates as a confident-looking ranked list
    once the floor is applied. Scores are the exact ones the issue body
    reports (a live rerun drifts as the skill-repository corpus grows --
    see docs/issue-2982/reports/ -- so this locks in the reported
    snapshot as a deterministic regression fixture rather than depending
    on today's corpus)."""

    def _dir(self):
        return Path("/tmp/does-not-need-to-exist-for-this-test")

    def test_skill_candidates_regression_cases_workspace_preservation_task(self):
        d = self._dir()
        scored = [
            (0.4325, "market-analysis-competitor-mapping", d, "skill-repo"),
            (0.4325, "growth-analytics-north-star", d, "skill-repo"),
            (0.4202, "conformance-review-traceability-and-evidence", d, "skill-repo"),
        ]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored):
            result = spawn.rank_skills(
                "rewrite the workspace preservation predicate in lifecycle.py from "
                "git-status-based to what-would-be-lost", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "no-candidates")
        self.assertEqual(result["ranked"], [])

    def test_skill_candidates_regression_cases_turn_cap_task(self):
        d = self._dir()
        scored = [
            (1.3324, "tech-feasibility", d, "skill-repo"),
            (1.3324, "usability-eval", d, "skill-repo"),
            (1.3066, "compliance-scan", d, "skill-repo"),
        ]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored):
            result = spawn.rank_skills(
                "remove the 200-turn session cap, replace with wall-clock/token backstops "
                "and an observe-only runaway signal", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "no-candidates")
        self.assertEqual(result["ranked"], [])


if __name__ == "__main__":
    unittest.main()
