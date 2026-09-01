"""Issue #2982: `spawn.py --skill-candidates` (`rank_skills()`, consult.py)
must report "no-candidates" when every BM25 candidate falls below a
calibrated relevance floor, instead of a confident-looking ranked list of
unrelated skills -- the recall failure the issue's two regression cases
document. The judge/rerank path is untouched: this is a BM25-stage floor
only, scoped to `use_judge=False` (the `--skill-candidates` default), never
applied to spawn's own internal cross-family mount
(`_cross_family_skill_matches_with_consult()` calls
`_bm25_cross_family_scores()` directly and never passes through here).

Floor re-derivation (issue #2982 follow-up, docs/issue-2982/reports/):
the first shipped floor (16.0) was fit to 7 positive examples the
calibrating session hand-wrote itself, and PR #3007's independent
verification reproduced 3 realistic queries with genuine, unambiguous
top-1 matches (14.53/11.19/10.53) that it silently suppressed -- the
exact "floor too high eats correct candidates" failure the issue itself
warned against.

This floor instead comes from real operator selections: `skills:`
frontmatter across `docs/issue-*/reports/*.md` (what an operator actually
chose for a real spawn), replayed as that issue's own title against the
live skill-repository corpus, kept where the applied skill was the
genuine BM25 top-1 (`REAL_POSITIVE_TOP1_SCORES` below). That real-history
positive set scores much lower than the first attempt's self-authored
examples -- as low as 7.62 -- which overlaps the score range of
plausible-looking wrong matches documented by the prior derivation's own
negative probes (7.91-15.13). No floor separates "genuinely on-topic"
from "plausible but wrong" cleanly across that overlap, and this module
does not claim otherwise (see `SkillCandidatesFloorKnownLimitationTest`).
The shipped floor (`consult._SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`)
sits only in the narrower gap the evidence actually supports: above the
two near-zero degenerate matches this issue originally reported
(0.4325, 1.3324) and below every documented genuine top-1 match (7.62
lowest, real or probed).

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
    """Issue #2982 (re-derivation): the floor must come from measurement
    over recorded task/selection pairs an operator actually made, not a
    number picked freehand -- and not fit to examples the calibrating
    session wrote itself, which is exactly how the first shipped floor
    (16.0) failed (docs/issue-2982/reports/).

    REAL_POSITIVE_TOP1_SCORES: real (issue, applied-skill) pairs read
    from this repo's own `skills:` report frontmatter -- what an operator
    actually chose for a real spawn, before this issue existed -- replayed
    as that issue's own title against the live skill-repository corpus,
    kept where the applied skill was the genuine BM25 top-1 pick.

    DOCUMENTED_DEGENERATE_NEGATIVE_SCORES: the two near-zero spurious
    top-1 scores issue #2982 itself originally reported (workspace-
    preservation and turn-cap tasks, on the corpus snapshot at filing
    time) -- real observed defects, not chosen to fit a threshold.

    This test only claims the floor separates these two evidence sets. It
    does NOT claim the floor separates "genuine top-1" from "plausible
    but wrong" in general -- see `SkillCandidatesFloorKnownLimitationTest`
    for the documented, deliberate gap in that broader claim."""

    REAL_POSITIVE_TOP1_SCORES = [
        7.617284997267742,   # issue #2906, applied skill=silent-failure-audit
        7.926375755789291,   # issue #2874, applied skill=adversarial-review
        8.354878908889502,   # issue #2924, applied skill=silent-failure-audit
        8.36478203459652,    # issue #2511, applied skill=silent-failure-audit
        9.713773500211078,   # issue #2626, applied skill=silent-failure-audit
        9.839628389484924,   # issue #2892, applied skill=adversarial-review
        13.78556616833873,   # issue #2894, applied skill=silent-failure-audit
    ]
    DOCUMENTED_DEGENERATE_NEGATIVE_SCORES = [
        0.4325,   # issue #2982's own workspace-preservation regression, as filed
        1.3324,   # issue #2982's own turn-cap regression, as filed
    ]

    def test_skill_candidates_floor_calibrated_separates_measured_pairs(self):
        floor = spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR
        self.assertGreater(min(self.REAL_POSITIVE_TOP1_SCORES), floor,
                            "floor must not suppress the weakest real operator-chosen match")
        self.assertLess(max(self.DOCUMENTED_DEGENERATE_NEGATIVE_SCORES), floor,
                         "floor must still suppress the two originally-reported degenerate matches")

    def test_skill_candidates_floor_calibrated_classifies_each_measured_pair(self):
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        for score in self.REAL_POSITIVE_TOP1_SCORES:
            with mock.patch.object(
                    spawn, "_bm25_cross_family_scores",
                    lambda *a, score=score, **k: [(score, "s", scored_dir, "skill-repo")]):
                result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
            self.assertEqual(result["outcome"], "bm25-only", score)
        for score in self.DOCUMENTED_DEGENERATE_NEGATIVE_SCORES:
            with mock.patch.object(
                    spawn, "_bm25_cross_family_scores",
                    lambda *a, score=score, **k: [(score, "s", scored_dir, "skill-repo")]):
                result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
            self.assertEqual(result["outcome"], "no-candidates", score)


class SkillCandidatesFloorKnownLimitationTest(unittest.TestCase):
    """Issue #2982 (re-derivation): documents, rather than hides, what the
    recalibrated floor deliberately does not do. The prior derivation's
    own negative probes (task descriptions with no on-topic skill in the
    corpus, scored live against today's corpus in the prior derivation
    record) top out at 15.13 -- inside the same 7.62-15.13 band real
    genuine top-1 matches also occupy. No hard BM25-score floor can
    separate that band without either letting some wrong matches through
    or eating some correct ones; this fix chooses the latter never
    happens, at the cost of the former still happening. These scores
    therefore still rank as `bm25-only`, not `no-candidates` -- a known,
    accepted scope limit, not a regression to chase."""

    MID_BAND_PLAUSIBLE_BUT_WRONG_SCORES = [
        7.911048066340095,    # top1=secure-coding-session-authentication (off-topic probe)
        15.134316351480955,   # top1=agent-coordination (off-topic probe)
    ]

    def test_skill_candidates_floor_does_not_suppress_mid_band_scores(self):
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        for score in self.MID_BAND_PLAUSIBLE_BUT_WRONG_SCORES:
            with mock.patch.object(
                    spawn, "_bm25_cross_family_scores",
                    lambda *a, score=score, **k: [(score, "s", scored_dir, "skill-repo")]):
                result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
            self.assertEqual(result["outcome"], "bm25-only", score)


class SkillCandidatesRegressionCasesTest(unittest.TestCase):
    """Issue #2982's own two measured failure cases: neither returns its
    recorded unrelated top candidates as a confident-looking ranked list
    once the floor is applied. Scores are the exact ones the issue body
    reports (a live rerun drifts as the skill-repository corpus grows --
    see docs/issue-2982/reports/ -- so this locks in the reported
    snapshot as a deterministic regression fixture rather than depending
    on today's corpus).

    Also covers the opposite direction, added by this issue's follow-up
    after PR #3007's independent verification: three realistic,
    unambiguous top-1 matches it reproduced against the (then-)shipped
    16.0 floor, which must NOT collapse to no-candidates under the
    recalibrated floor -- suppressing a genuine match is the failure
    direction issue #2982 named as worse than the original defect."""

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

    def test_skill_candidates_regression_cases_pr3007_sla_tier_task_survives(self):
        d = self._dir()
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(14.528541509218531, "customer-support-sla-tier-priority",
                                   d, "skill-repo")]):
            result = spawn.rank_skills(
                "define SLA tiers and escalation priority for support tickets",
                "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")
        self.assertEqual([r["name"] for r in result["ranked"]],
                         ["customer-support-sla-tier-priority"])

    def test_skill_candidates_regression_cases_pr3007_risk_aggregation_task_survives(self):
        d = self._dir()
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(11.185550391505078, "risk-management-aggregation-consolidation",
                                   d, "skill-repo")]):
            result = spawn.rank_skills(
                "consolidate and aggregate risk exposure across business units",
                "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")
        self.assertEqual([r["name"] for r in result["ranked"]],
                         ["risk-management-aggregation-consolidation"])

    def test_skill_candidates_regression_cases_pr3007_conformance_sampling_task_survives(self):
        d = self._dir()
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(10.530965217698867, "conformance-review-sampling-derivation",
                                   d, "skill-repo")]):
            result = spawn.rank_skills(
                "derive the sampling method for this conformance review",
                "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")
        self.assertEqual([r["name"] for r in result["ranked"]],
                         ["conformance-review-sampling-derivation"])


if __name__ == "__main__":
    unittest.main()
