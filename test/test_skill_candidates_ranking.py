"""Issue #2678: the orchestrator can obtain ranked skill candidates for a
task BEFORE spawning, instead of picking `--skills` blind. `rank_skills()`
(consult.py, aliased onto spawn.py) is the shared, read-only ranking
function -- it reuses `_bm25_cross_family_scores()` and
`_cross_family_skill_matches_with_consult()` byte-identical to spawn's own
internal add-only cross-family mount, so the orchestrator's preview and
spawn's actual mount decision cannot drift into two disagreeing
implementations.

Acceptance covered here:
  - ranked output differs and matches the task shape (design vs
    integration) -- TaskShapeRankingTest
  - empty state: a task matching nothing returns an empty ranking with
    outcome "no-candidates", never an arbitrary top-N -- EmptyStateTest
  - the candidate path and spawn's own internal selection use the same
    scoring -- SameScoringTest
  - the fail-open contract: a timeout/error on the judge stage is
    distinguishable, by `outcome`, from "ranked nothing" -- the exact
    defect #2679 exists because of, deliberately not repeated here --
    FailOpenDistinguishableTest

Run: python3 -m pytest test/test_skill_candidates_ranking.py -q
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import spawn


def _write_skill(root: Path, name: str, description: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: >-\n"
        f"  {description}\n"
        "---\n\n# body\n", encoding="utf-8")
    return d


class TaskShapeRankingTest(unittest.TestCase):
    """check: run the candidate command for two clearly different tasks (a
    design task and an integration task) and show the ranked output
    differs and matches the task."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        _write_skill(
            self.repo_root, "architecture-interface-contract-shape",
            "Use when choosing the shape of a boundary contract between "
            "services or modules, sync vs async orchestration choreography.")
        _write_skill(
            self.repo_root, "test-depth-audit",
            "Use when examining an existing test suite to classify each "
            "test by what it actually verifies, integration merge CI.")

    def test_design_task_ranks_the_boundary_contract_skill_first(self):
        result = spawn.rank_skills(
            "sync 호출을 이벤트로 바꿀지 orchestration vs choreography 로 "
            "boundary contract 를 설계해야 한다",
            "orchestrator", self.repo_root)
        self.assertEqual(result["outcome"], "bm25-only")
        self.assertTrue(result["ranked"])
        self.assertEqual(result["ranked"][0]["name"],
                         "architecture-interface-contract-shape")

    def test_integration_task_ranks_a_different_skill_first(self):
        design_result = spawn.rank_skills(
            "sync 호출을 이벤트로 바꿀지 orchestration vs choreography 로 "
            "boundary contract 를 설계해야 한다",
            "orchestrator", self.repo_root)
        integration_result = spawn.rank_skills(
            "verify the failing test suite, integration merge CI run and "
            "classify each test by what it actually verifies",
            "orchestrator", self.repo_root)
        self.assertEqual(integration_result["ranked"][0]["name"],
                         "test-depth-audit")
        self.assertNotEqual(design_result["ranked"][0]["name"],
                            integration_result["ranked"][0]["name"])


class EmptyStateTest(unittest.TestCase):
    """empty state: a task matching nothing returns an empty ranking and
    says so, rather than returning an arbitrary top-N."""

    def test_no_shared_tokens_yields_empty_ranked_and_no_candidates_outcome(self):
        with tempfile.TemporaryDirectory() as td:
            _write_skill(Path(td), "some-skill", "Use when doing X.")
            result = spawn.rank_skills("zzqx wvbn plkj gibberish nonsense",
                                       "orchestrator", Path(td))
        self.assertEqual(result, {"ranked": [], "outcome": "no-candidates",
                                  "picked": []})


class SameScoringTest(unittest.TestCase):
    """check: score one task through both paths and show identical
    rankings -- rank_skills() and spawn's own internal cross-family BM25
    call must return the same order for the same task, because they call
    the exact same function with the exact same arguments."""

    def test_candidate_path_matches_internal_bm25_scoring(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_skill(root, "alpha-skill", "Use when doing alpha work.")
            _write_skill(root, "beta-skill", "Use when doing beta work.")
            task = "some alpha work needs doing here"
            direct = spawn._bm25_cross_family_scores(task, "orchestrator",
                                                      root, None, None)
            via_rank_skills = spawn.rank_skills(task, "orchestrator", root)
        direct_names = [name for _score, name, _d, _source in direct]
        candidate_names = [r["name"] for r in via_rank_skills["ranked"]]
        self.assertEqual(direct_names, candidate_names)
        self.assertEqual(candidate_names[0], "alpha-skill")


class FailOpenDistinguishableTest(unittest.TestCase):
    """The load-bearing contract from issue #2678's third caveat: a
    timeout/error on the judge stage must be distinguishable, by the
    caller, from "ranked nothing" -- never collapse fail-open into an
    empty ranking the way #2679's invisible fail-open did."""

    def test_judge_timeout_still_returns_full_bm25_ranking_tagged_fail_open(self):
        scored_dir = Path("/tmp/does-not-need-to-exist-for-this-test")
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: [(1.0, "a-skill", scored_dir, "skill-repo")]), \
             mock.patch.object(spawn, "_skill_judge_consult",
                               side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=7)):
            result = spawn.rank_skills("task", "orchestrator", Path(td),
                                       issue=2678, cwd=td, use_judge=True)
        # ranked (BM25) survives the judge failure untouched -- fail-open
        # never means "ranked nothing".
        self.assertEqual([r["name"] for r in result["ranked"]], ["a-skill"])
        self.assertEqual(result["outcome"], "fail-open")
        # distinguishable from the genuine no-candidates empty state:
        self.assertNotEqual(result["outcome"], "no-candidates")

    def test_no_candidates_short_circuits_before_judge_is_ever_asked(self):
        with mock.patch.object(spawn, "_bm25_cross_family_scores",
                               lambda *a, **k: []), \
             mock.patch.object(spawn, "_skill_judge_consult",
                               side_effect=AssertionError(
                                   "judge must not be called when BM25 found nothing")):
            result = spawn.rank_skills("task", "orchestrator", Path("/tmp"),
                                       issue=2678, cwd="/tmp", use_judge=True)
        self.assertEqual(result, {"ranked": [], "outcome": "no-candidates",
                                  "picked": []})


if __name__ == "__main__":
    unittest.main()
