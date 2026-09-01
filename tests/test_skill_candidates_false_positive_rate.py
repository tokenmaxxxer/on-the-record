"""Issue #3018 (Acceptance: "the unrelated-query false-positive rate is
measured the same way the 89% baseline was, against the current corpus,
before and after"): re-derives the false-positive rate live, against the
corpus actually on disk when this test runs, rather than trusting the
frozen 89% figure quoted in the issue body -- the baseline itself was
measured against a corpus snapshot that has since moved on
(`docs/issue-2982/reports/adversarial-review-fc5c800d.md`'s own
disclosure: "a live rerun drifts as the ... corpus grows").

Population (Acceptance: "independently authored realistic unrelated task
queries, not drawn from any prior record's *examples*" -- read here as
not the record's own curated *headline* two examples, and not authored by
this session; per this issue's own routing text ("draw them from
repository history or from the prior verification records") the query
text itself is the same fixed 13-query set
`tests/test_skill_candidates_signal.py` also replays, drawn from two
independent prior verification sessions (PRs #3015/#3016), neither of
which is this one and neither of which built the code under test.

"Before" = the false-positive behaviour issue #2982's floor alone
produces (top1 score >= `_SKILL_CANDIDATES_RELEVANCE_FLOOR` => a
confident, unqualified top-1 -- the exact `bm25-only`-only vocabulary
`rank_skills()` had before this issue). "After" = this issue's actual
shipped `rank_skills()`, called live, unmocked. A query counts as a
"false positive" (confident wrong top-1) in each generation when that
generation's logic would present a top-1 without qualifying it as
ambiguous -- the same "did the caller get a plain top-1 it would
reasonably trust" reading the issue's own 89% figure used.

Run: python3 -m pytest tests/test_skill_candidates_false_positive_rate.py -q
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn

# Same 13 unrelated queries as tests/test_skill_candidates_signal.py's
# UNRELATED_QUERY_MARGINS -- see that module's docstring for provenance
# (10 from PR #3015's record, 3 from PR #3016's record; none authored by
# this session).
UNRELATED_QUERIES = [
    "fix an off-by-one error in the pagination loop",
    "add a retry with exponential backoff",
    "rename the internal variable foo to bar",
    "debug why the docker container exits immediately",
    "write a bash script that tails a log file",
    "convert this synchronous function to use asyncio",
    "investigate why the unit test for the parser is flaky",
    "update the changelog for the upcoming release",
    "fix a memory leak caused by an event listener",
    "reorder the columns in this CSV export",
    "fix this bug",
    "add a new feature",
    "clean this up",
]


class SkillCandidatesFalsePositiveRateTest(unittest.TestCase):
    """Live, unmocked measurement against the corpus on disk right now --
    deliberately not frozen fixture scores, because the Acceptance asks
    for "the current corpus", not a snapshot."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = spawn._skill_repo_root()
        cls.home = Path.home()
        cls.target = Path(".")

    def _before_is_confident_top1(self, query):
        """issue #2982's floor alone: any top1 >= floor is an
        unqualified, confident top-1 -- reproduces exactly what
        `rank_skills()` returned before this issue (outcome in
        {"no-candidates", "bm25-only"} was the full vocabulary)."""
        scored = spawn._bm25_cross_family_scores(
            query, "orchestrator", self.repo_root, self.home, self.target)
        if not scored:
            return False
        return scored[0][0] >= spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR

    def _after_is_confident_top1(self, query):
        """this issue's shipped rank_skills(), called live."""
        result = spawn.rank_skills(query, "orchestrator", self.repo_root,
                                   home=self.home, target_repo_root=self.target)
        return result["outcome"] == "bm25-only"

    def test_false_positive_rate_measured_before_and_after_on_current_corpus(self):
        before = [q for q in UNRELATED_QUERIES if self._before_is_confident_top1(q)]
        after = [q for q in UNRELATED_QUERIES if self._after_is_confident_top1(q)]
        before_rate = len(before) / len(UNRELATED_QUERIES)
        after_rate = len(after) / len(UNRELATED_QUERIES)
        # derived (this test's own live run, printed on failure for a
        # future reader re-deriving on a grown corpus):
        msg = (f"before={len(before)}/{len(UNRELATED_QUERIES)} ({before_rate:.1%}) "
               f"after={len(after)}/{len(UNRELATED_QUERIES)} ({after_rate:.1%})")
        # must not: this issue's own signal must not make the rate worse
        # -- the margin check only ever moves a query out of "bm25-only"
        # (into "ambiguous"), never in.
        self.assertLessEqual(len(after), len(before), msg)
        # the whole point of issue #3018: the rate must move, not just be
        # re-measured and left where PR #3011 left it (that would be the
        # "no-op dressed as a fix" failure mode
        # docs/issue-2982/reports/adversarial-review-fc5c800d.md already
        # named against the relevance floor alone).
        self.assertLess(len(after), len(before), msg)

    def test_false_positive_rate_stays_high_not_claimed_solved(self):
        # honesty check: this issue's own consult was explicit that the
        # margin signal is a partial, conservative fix, not a general
        # classifier (see consult.py's _SKILL_CANDIDATES_MARGIN_FLOOR
        # docstring and this module's known-limitation test). Asserting
        # the after-rate is still nonzero documents that the residual
        # failure is real and not being hidden by this change.
        after = [q for q in UNRELATED_QUERIES if self._after_is_confident_top1(q)]
        self.assertGreater(
            len(after), 0,
            "the margin signal is a conservative partial fix -- if this ever hits "
            "zero, the corpus or the signal changed enough to warrant re-deriving "
            "the residual rate honestly rather than assuming it is solved")


if __name__ == "__main__":
    unittest.main()
