"""Issue #3127 repair round, defect 2 (found by PR #3145's second
independent verification): H1 (the manipulation check -- "did the
skills-off arm actually mount a different corpus") existed only as prose
in docs/issue-3127/decisions/pre-registration.md, never enforced in code.
A pair whose two arms did not differ in directive bytes could still flow
straight into an H2 quality comparison with nothing to catch it.

This file covers compute_h1_manipulation() (the comparison itself),
gate_pair_on_h1() (the gate that refuses to compute/report H2 for a
failing pair), and build_execute_results() (the results-JSON assembly that
keeps a failed pair's H2 out of the reported figures).

defect 3 (found by the same verification, PR #3145): scrub_skill_slugs()
was defined and never called anywhere -- no blind-evaluator function
existed in the harness at all. EvaluatePairBlindTest below covers
evaluate_pair_blind(), wired into run_pair() (see
test_issue_3127_run_pair.py for the orchestration-level test), verifying
it is genuinely blind (arm labels never reach the evaluator) and that it
records whether scrubbing changed the score.

Defect 4 (wall-clock honesty) is added by a later commit to this same
file.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import run_consumer_pair as rcp  # noqa: E402


class ComputeH1ManipulationTest(unittest.TestCase):
    """H1 must be an actual, code-enforced comparison, capable of both
    passing and failing -- not prose."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _make_workspace(self, name: str, directive_bytes: bytes | None) -> Path:
        ws = Path(self._tmpdir.name) / name
        directive_dir = ws / ".on-the-record" / "directive"
        directive_dir.mkdir(parents=True)
        if directive_bytes is not None:
            (directive_dir / "core.md").write_bytes(directive_bytes)
        return ws

    def test_identical_directive_bytes_flagged_as_manipulation_failure(self):
        """Reproduces PR #3145 finding 1's silent-full-content-leak failure
        mode: both arms end up with byte-identical directive composition
        (the manipulation never actually happened) -- H1 must catch this,
        not silently pass it through to H2."""
        on_ws = self._make_workspace("on", b"same content twice-over padding")
        off_ws = self._make_workspace("off", b"same content twice-over padding")
        result = rcp.compute_h1_manipulation(on_ws, off_ws)
        self.assertFalse(result["differs"])
        self.assertIsNotNone(result["reason"])

    def test_differing_directive_bytes_passes(self):
        on_ws = self._make_workspace("on", b"a" * 5000)
        off_ws = self._make_workspace("off", b"a" * 12)
        result = rcp.compute_h1_manipulation(on_ws, off_ws)
        self.assertTrue(result["differs"])
        self.assertIsNone(result["reason"])

    def test_missing_workspace_data_is_a_failure_not_a_skip(self):
        on_ws = self._make_workspace("on", b"a" * 5000)
        result = rcp.compute_h1_manipulation(on_ws, None)
        self.assertFalse(result["differs"])
        self.assertIsNone(result["off_bytes"])


class GatePairOnH1Test(unittest.TestCase):
    """The gate must refuse to even CALL the H2 scorer for a pair that
    fails H1 -- not just fail to report it afterward."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _make_workspace(self, name: str, directive_bytes: bytes) -> Path:
        ws = Path(self._tmpdir.name) / name
        directive_dir = ws / ".on-the-record" / "directive"
        directive_dir.mkdir(parents=True)
        (directive_dir / "core.md").write_bytes(directive_bytes)
        return ws

    def test_h1_failure_excludes_pair_and_never_calls_h2_scorer(self):
        on_ws = self._make_workspace("on", b"identical")
        off_ws = self._make_workspace("off", b"identical")
        calls = []

        def compute_h2():
            calls.append(1)
            return {"should": "never run"}

        result = rcp.gate_pair_on_h1("01-study-groups", on_ws, off_ws,
                                      compute_h2=compute_h2)
        self.assertTrue(result["excluded_from_h2"])
        self.assertIsNone(result["h2"])
        self.assertIn("H1 manipulation check failed", result["exclusion_reason"])
        self.assertEqual(calls, [])  # compute_h2 was never invoked

    def test_h1_pass_calls_h2_scorer_and_includes_pair(self):
        on_ws = self._make_workspace("on", b"a" * 5000)
        off_ws = self._make_workspace("off", b"a" * 12)
        result = rcp.gate_pair_on_h1("01-study-groups", on_ws, off_ws,
                                      compute_h2=lambda: {"verdict": "ok"})
        self.assertFalse(result["excluded_from_h2"])
        self.assertEqual(result["h2"], {"verdict": "ok"})

    def test_h1_pass_with_no_scorer_supplied_leaves_h2_none_distinctly(self):
        on_ws = self._make_workspace("on", b"a" * 5000)
        off_ws = self._make_workspace("off", b"a" * 12)
        result = rcp.gate_pair_on_h1("01-study-groups", on_ws, off_ws)
        self.assertFalse(result["excluded_from_h2"])
        self.assertIsNone(result["h2"])
        self.assertIn("h2_unavailable_reason", result)


class BuildExecuteResultsTest(unittest.TestCase):
    """A results file must never report an H2 figure for a pair whose own
    H1 failed -- the core claim of defect 2."""

    def _plan(self):
        import argparse
        args = argparse.Namespace(
            repo="/tmp/sandbox", pinned_sha=None,
            skill="product-discovery-hypothesis-preregistration",
            model="sonnet", pairs="01-study-groups",
            skill_repo_on="$MUSTER_SKILL_REGISTRY_ROOT",
            skill_repo_off=None, watch_timeout=1800)
        return rcp.build_plan(args)

    def test_failed_h1_pair_never_appears_in_included_list(self):
        failed_pair = {"pair_id": "01-study-groups", "excluded_from_h2": True,
                        "exclusion_reason": "H1 manipulation check failed: x",
                        "h2": None}
        results = rcp.build_execute_results(self._plan(), [failed_pair])
        self.assertEqual(results["pairs_included_in_h2"], [])
        self.assertEqual(len(results["pairs_excluded_from_h2"]), 1)
        self.assertEqual(results["pairs_excluded_from_h2"][0]["pair_id"],
                          "01-study-groups")
        self.assertIn("H1", results["pairs_excluded_from_h2"][0]["reason"])

    def test_mixed_pairs_only_passing_ones_counted_as_included(self):
        failed_pair = {"pair_id": "01-study-groups", "excluded_from_h2": True,
                        "exclusion_reason": "H1 manipulation check failed: x",
                        "h2": None}
        passed_pair = {"pair_id": "02-onboarding-experiment",
                        "excluded_from_h2": False, "exclusion_reason": None,
                        "h2": {"scrubbed_scores_by_arm": {"skills-on": 8,
                                                           "skills-off": 5}}}
        results = rcp.build_execute_results(self._plan(),
                                             [failed_pair, passed_pair])
        self.assertEqual(results["pairs_included_in_h2"],
                          ["02-onboarding-experiment"])
        self.assertEqual([e["pair_id"] for e in results["pairs_excluded_from_h2"]],
                          ["01-study-groups"])

    def test_all_pairs_failing_h1_yields_no_h2_decision(self):
        failed_pair = {"pair_id": "01-study-groups", "excluded_from_h2": True,
                        "exclusion_reason": "H1 manipulation check failed: x",
                        "h2": None}
        results = rcp.build_execute_results(self._plan(), [failed_pair])
        self.assertIn("nothing to compare", results["decision"])


class EvaluatePairBlindTest(unittest.TestCase):
    """defect 3: the blind scorer must be genuinely blind (no arm labels
    reach the evaluator) and must actually scrub skill slugs before
    scoring, recording whether the scrub changed anything."""

    KNOWN_SLUGS = ["my-skill"]

    def test_arm_labels_never_appear_in_evaluator_prompt(self):
        captured_prompts = []

        def fake_evaluator(prompt: str) -> str:
            captured_prompts.append(prompt)
            return '{"document_1_score": 7, "document_2_score": 7, ' \
                   '"verdict": "indistinguishable", "reasoning": "x"}'

        result = rcp.evaluate_pair_blind(
            "task text", "rubric text",
            "on deliverable, no slug mention", "off deliverable, no slug",
            self.KNOWN_SLUGS, evaluator_fn=fake_evaluator)

        self.assertEqual(len(captured_prompts), 1)  # no-op scrub -> 1 call
        prompt = captured_prompts[0]
        self.assertNotIn("skills-on", prompt)
        self.assertNotIn("skills-off", prompt)
        self.assertFalse(result["scrub_changed_score"])

    def test_known_slug_is_scrubbed_before_reaching_evaluator(self):
        captured_prompts = []

        def fake_evaluator(prompt: str) -> str:
            captured_prompts.append(prompt)
            return '{"document_1_score": 6, "document_2_score": 6, ' \
                   '"verdict": "indistinguishable", "reasoning": "x"}'

        deliverable_on = "This brief was written using my-skill's method."
        deliverable_off = "This brief has no skill mention."
        result = rcp.evaluate_pair_blind(
            "task text", "rubric text", deliverable_on, deliverable_off,
            self.KNOWN_SLUGS, evaluator_fn=fake_evaluator)

        self.assertEqual(result["scrub_replacement_counts"]["skills-on"], 1)
        self.assertEqual(result["scrub_replacement_counts"]["skills-off"], 0)
        # First call (scrubbed) must not contain the raw slug text.
        self.assertNotIn("my-skill", captured_prompts[0])
        self.assertIn("[skill-name-redacted]", captured_prompts[0])
        # Because a replacement happened, a second (unscrubbed) call runs.
        self.assertEqual(len(captured_prompts), 2)
        self.assertIn("my-skill", captured_prompts[1])

    def test_records_scrub_changed_score_when_scores_actually_differ(self):
        calls = {"n": 0}

        def fake_evaluator(prompt: str) -> str:
            calls["n"] += 1
            # First call is the scrubbed pass, second is unscrubbed --
            # return different scores to simulate the slug mention itself
            # moving the evaluator's judgement.
            if calls["n"] == 1:
                return '{"document_1_score": 5, "document_2_score": 5, ' \
                       '"verdict": "indistinguishable", "reasoning": "x"}'
            return '{"document_1_score": 9, "document_2_score": 5, ' \
                   '"verdict": "document_1", "reasoning": "y"}'

        deliverable_on = "Uses my-skill extensively."
        deliverable_off = "No mention here."
        result = rcp.evaluate_pair_blind(
            "task text", "rubric text", deliverable_on, deliverable_off,
            self.KNOWN_SLUGS, evaluator_fn=fake_evaluator)
        self.assertTrue(result["scrub_changed_score"])
        self.assertIn("scrubbed_scores_by_arm", result)
        self.assertIn("unscrubbed_scores_by_arm", result)

    def test_no_slug_mention_skips_the_second_unscrubbed_call(self):
        calls = {"n": 0}

        def fake_evaluator(prompt: str) -> str:
            calls["n"] += 1
            return '{"document_1_score": 7, "document_2_score": 7, ' \
                   '"verdict": "indistinguishable", "reasoning": "x"}'

        rcp.evaluate_pair_blind(
            "task text", "rubric text", "clean on text", "clean off text",
            self.KNOWN_SLUGS, evaluator_fn=fake_evaluator)
        self.assertEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()
