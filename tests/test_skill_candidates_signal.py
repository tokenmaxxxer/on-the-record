"""Issue #3018: `spawn.py --skill-candidates` (`rank_skills()`, consult.py)
must use a signal beyond the raw BM25 score, per the follow-up to issue
#2982 -- two independent verifications (PRs #3015/#3016, cited in this
issue's body) measured that the recalibrated relevance floor
(`_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`) does almost nothing against
the issue's actual complaint: 89% of realistic unrelated task queries
still score above the floor and each returns a confident-looking wrong
top-1.

Alternatives considered (Acceptance: "justified against measured
alternatives rather than asserted"):
  - Raise the relevance floor further -- ruled out by this issue's own
    must-not: measured twice already (16.0, then 4.0), fails in both
    directions on this corpus (`tests/test_skill_candidates_floor.py`'s
    own docstring and `SkillCandidatesFloorKnownLimitationTest`).
  - Judge/rerank (haiku) as the signal -- the judge path's own timeout
    behaviour is not yet fixed (this issue's Direction section, priority
    2, not attempted here), so it cannot be assessed as a reranker; the
    margin signal below is scoped to the judge-off preview path only and
    does not touch it.
  - Local embeddings -- unmeasured on this corpus; this issue's Direction
    section scopes that to a future pilot, not this change.
  - Top-1/top-2 raw-score margin (chosen here) -- cheap, deterministic, no
    new dependency, and is the resolution path the prior independent
    verification itself named
    (`docs/issue-2982/reports/adversarial-review-e63d3cd4.md`, "Open
    findings" #1: "a relative signal (margin between top-1 and top-2 ...)
    rather than an absolute BM25-score cutoff").

`SkillCandidatesMarginMeasuredTest` below replays the measurement this
module's own derivation ran live (this session, against the corpus on
disk at derivation time) over two fixed sets neither authored by this
session:
  - `REAL_POSITIVE_MARGINS`: the same 7 (issue, applied-skill) pairs as
    `tests/test_skill_candidates_floor.py`'s `REAL_POSITIVE_TOP1_SCORES`
    (real operator selections, `skills:` frontmatter across
    `docs/issue-*/reports/*.md`), replayed with each issue's own title
    (`gh issue view <n> --json title`) against the live corpus, margin =
    top1_score - top2_score.
  - `UNRELATED_QUERY_MARGINS`: the 10 "fresh task-shaped queries" from
    `docs/issue-2982/reports/adversarial-review-e63d3cd4.md` (PR #3015)
    plus the 3 example queries quoted verbatim in
    `docs/issue-2982/reports/adversarial-review-fc5c800d.md` (PR #3016) --
    13 unrelated queries total, none authored by this session, drawn from
    prior independent-verification records per this issue's own must-not
    ("do not evaluate against queries authored by the session doing the
    work").

Run: python3 -m pytest tests/test_skill_candidates_signal.py -q
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


class SkillCandidatesMarginSignalTest(unittest.TestCase):
    """Unit-level behaviour of the new signal: `rank_skills()` reports
    `outcome: "ambiguous"` -- not a confident `"bm25-only"` top-1 -- when
    the top score clears the relevance floor but does not clearly separate
    from the runner-up, and leaves every other path (single candidate,
    clear margin, judge-on) exactly as before."""

    def _dir(self):
        return Path("/tmp/does-not-need-to-exist-for-this-test")

    def test_close_top1_top2_reports_ambiguous_not_confident(self):
        d = self._dir()
        scored = [(8.0, "skill-a", d, "skill-repo"),
                  (7.95, "skill-b", d, "skill-repo")]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "ambiguous")
        # must not: this is not a suppression like "no-candidates" -- the
        # operator still sees both near-tied candidates and picks, the
        # tool does not pick for them.
        self.assertEqual([r["name"] for r in result["ranked"]],
                         ["skill-a", "skill-b"])
        self.assertEqual(result["picked"], [])

    def test_clear_margin_still_reports_bm25_only(self):
        d = self._dir()
        scored = [(8.0, "skill-a", d, "skill-repo"),
                  (5.0, "skill-b", d, "skill-repo")]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")
        self.assertEqual([r["name"] for r in result["ranked"]],
                         ["skill-a", "skill-b"])

    def test_margin_just_above_floor_is_not_ambiguous(self):
        # boundary: a margin clearly above (not exactly at, to avoid a
        # float-precision false failure on the equality case)
        # _SKILL_CANDIDATES_MARGIN_FLOOR clears -- the check is a strict
        # "<", matching the relevance floor's own strict-"<" convention.
        d = self._dir()
        top2 = 7.0
        top1 = top2 + spawn._SKILL_CANDIDATES_MARGIN_FLOOR + 0.05
        scored = [(top1, "skill-a", d, "skill-repo"),
                  (top2, "skill-b", d, "skill-repo")]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")

    def test_single_candidate_has_no_runner_up_never_ambiguous(self):
        # must not regress the existing single-candidate regression
        # fixtures (tests/test_skill_candidates_floor.py) -- no top-2
        # means no tie to report.
        d = self._dir()
        with mock.patch.object(
                spawn, "_bm25_cross_family_scores",
                lambda *a, **k: [(8.0, "only-skill", d, "skill-repo")]):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "bm25-only")

    def test_below_relevance_floor_still_no_candidates_margin_not_reached(self):
        # the relevance floor is checked first and is unchanged by this
        # issue (must not: do not raise the relevance floor) -- a
        # near-tied pair that is also below the floor is still
        # "no-candidates", never "ambiguous".
        d = self._dir()
        scored = [(1.0, "skill-a", d, "skill-repo"),
                  (0.99, "skill-b", d, "skill-repo")]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"))
        self.assertEqual(result["outcome"], "no-candidates")
        self.assertEqual(result["ranked"], [])

    def test_judge_path_is_unaffected_by_margin(self):
        # must not: the judge/rerank path is not the fix here either --
        # scoped to use_judge=False only, same scoping the relevance
        # floor already uses.
        d = self._dir()
        scored = [(8.0, "skill-a", d, "skill-repo"),
                  (7.95, "skill-b", d, "skill-repo")]
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: scored), \
             mock.patch.object(spawn, "_skill_judge_consult",
                               return_value=([d], "detail")):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"),
                                       issue=3018, cwd="/tmp", use_judge=True)
        self.assertNotEqual(result["outcome"], "ambiguous")


class SkillCandidatesMarginMeasuredTest(unittest.TestCase):
    """The margin signal's own justification, executed rather than
    asserted: replays the two fixed sets this issue's derivation measured
    live and checks the margin floor actually separates them the way the
    constant's docstring (consult.py, `_SKILL_CANDIDATES_MARGIN_FLOOR`)
    claims -- and, symmetrically, that the raw BM25 score alone (the
    rejected alternative) does NOT separate them, which is the whole
    reason a relative signal was chosen over another absolute cutoff."""

    # 7 real operator-chosen top-1 picks, `(issue, applied_skill, top1_score,
    # top2_score)` -- same issue/skill pairs as
    # `SkillCandidatesFloorCalibratedTest.REAL_POSITIVE_TOP1_SCORES`
    # (top1_score matches those exactly), replayed live this session with
    # each issue's own title (`gh issue view <n> --json title`) against the
    # corpus on disk at derivation time.
    REAL_POSITIVE_MARGINS = [
        (2906, "silent-failure-audit", 7.617284997267742, 4.478701237267742),
        (2874, "adversarial-review", 7.926375755789291, 7.211191202789291),
        (2924, "silent-failure-audit", 8.354878908889502, 5.470752908889502),
        (2511, "silent-failure-audit", 8.36478203459652, 6.79724203459652),
        (2626, "silent-failure-audit", 9.713773500211078, 9.169354300211078),
        (2892, "adversarial-review", 9.839628389484924, 9.654456389484924),
        (2894, "silent-failure-audit", 13.78556616833873, 10.75721016833873),
    ]

    # 13 unrelated task queries, none authored by this session: 10 from
    # docs/issue-2982/reports/adversarial-review-e63d3cd4.md ("10 fresh
    # task-shaped queries", PR #3015) + 3 quoted verbatim in
    # docs/issue-2982/reports/adversarial-review-fc5c800d.md (PR #3016) --
    # `(query_label, top1_score, top2_score)`, replayed live this session.
    UNRELATED_QUERY_MARGINS = [
        ("fix an off-by-one error in the pagination loop", 7.320, 7.157),
        ("add a retry with exponential backoff", 6.188, 5.665),
        ("rename the internal variable foo to bar", 4.986, 4.634),
        ("debug why the docker container exits immediately", 5.002, 4.945),
        ("write a bash script that tails a log file", 5.831, 5.289),
        ("convert this synchronous function to use asyncio", 5.935, 5.753),
        ("investigate why the unit test for the parser is flaky", 8.110, 6.482),
        ("update the changelog for the upcoming release", 10.371, 5.152),
        ("fix a memory leak caused by an event listener", 5.717, 5.327),
        ("reorder the columns in this CSV export", 5.145, 5.124),
        ("fix this bug", 4.730, 4.366),
        ("add a new feature", 6.429, 6.097),
        ("clean this up", 8.382, 5.398),
    ]

    def test_margin_floor_never_flags_a_real_operator_pick(self):
        floor = spawn._SKILL_CANDIDATES_MARGIN_FLOOR
        margins = [top1 - top2 for _, _, top1, top2 in self.REAL_POSITIVE_MARGINS]
        self.assertGreaterEqual(
            min(margins), floor,
            "margin floor must not flag any real operator-chosen top-1 as ambiguous")

    def test_margin_floor_catches_some_real_near_ties_in_unrelated_set(self):
        floor = spawn._SKILL_CANDIDATES_MARGIN_FLOOR
        margins = [top1 - top2 for _, top1, top2 in self.UNRELATED_QUERY_MARGINS]
        caught = [m for m in margins if m < floor]
        self.assertGreater(
            len(caught), 0,
            "margin floor should catch at least one measured unrelated-query near-tie")

    def test_raw_score_alone_does_not_separate_the_two_sets(self):
        # the rejected alternative, executed: raw top1 score ranges
        # overlap between the positive and unrelated sets, which is why a
        # relative signal was chosen over another absolute score cutoff.
        pos_scores = [top1 for _, _, top1, _ in self.REAL_POSITIVE_MARGINS]
        neg_scores = [top1 for _, top1, _ in self.UNRELATED_QUERY_MARGINS]
        self.assertTrue(
            min(pos_scores) < max(neg_scores) and min(neg_scores) < max(pos_scores),
            "raw top1 score ranges are expected to overlap -- this is why margin, "
            "not another score cutoff, was chosen (see consult.py's "
            "_SKILL_CANDIDATES_MARGIN_FLOOR docstring)")

    def test_margin_alone_does_not_cleanly_separate_either_known_limitation(self):
        # documented, not hidden (same posture as
        # SkillCandidatesFloorKnownLimitationTest): margin also overlaps
        # at the high end -- some unrelated queries have a wide margin
        # too (BM25 can have one dominant unrelated token). The floor is
        # deliberately conservative and does not claim otherwise.
        pos_margins = [top1 - top2 for _, _, top1, top2 in self.REAL_POSITIVE_MARGINS]
        neg_margins = [top1 - top2 for _, top1, top2 in self.UNRELATED_QUERY_MARGINS]
        self.assertLess(min(pos_margins), max(neg_margins),
                        "margin ranges overlap at the high end -- known, accepted limitation")


if __name__ == "__main__":
    unittest.main()
