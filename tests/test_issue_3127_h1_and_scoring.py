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
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "issue-3127"))
import run_consumer_pair as rcp  # noqa: E402


SKILL_NAME = "my-skill"


def _init_line(mounted: bool) -> str:
    import json as _json
    plugins = ([{"name": SKILL_NAME,
                 "path": f"/some/skill-registry/skills/{SKILL_NAME}"}]
               if mounted else [])
    return _json.dumps({"type": "system", "subtype": "init",
                         "plugins": plugins}, separators=(",", ":"))


def _tool_use_line(skill: str) -> str:
    return ('{"type":"assistant","message":{"content":[{"type":"tool_use",'
            f'"name":"Skill","input":{{"skill":"{skill}"}}}}]}}')


class DiscoverArmBranchTest(unittest.TestCase):
    """Issue #3245 round 3: `_discover_arm_branch()` waits for the arm's
    real PR rather than concluding from one early poll -- a PR that is
    real but not yet indexed by `gh` must be "not yet observable", never
    silently reported as "never happened"."""

    def _fake_run(self, per_call_stdout):
        calls = []

        def _run(cmd, capture_output, text, timeout):
            calls.append(cmd)
            stdout = per_call_stdout[len(calls) - 1]
            return mock.Mock(returncode=0, stdout=stdout, stderr="")
        return _run, calls

    def test_finds_pr_on_a_later_poll_not_the_first(self):
        """The exact round-2 shape: the first poll(s) see no PR yet (the
        session had not registered/the PR was not yet indexed), and a
        later poll does -- this must be reported as found, not as
        exhausted after the first empty result."""
        import json as _json
        empty = _json.dumps([])
        found = _json.dumps([
            {"number": 29, "headRefName":
                "issue-19/product-discovery-hypothesis-preregistration-37412f31",
             "createdAt": "2026-09-03T02:01:31Z"}])
        fake_run, calls = self._fake_run([empty, empty, found])
        with mock.patch("subprocess.run", fake_run):
            result = rcp._discover_arm_branch(
                "JiwonJung94/study-companion", 19, retries=6, delay_s=0,
                _sleep=lambda s: None)
        self.assertTrue(result["found"])
        self.assertEqual(result["pr_number"], 29)
        self.assertEqual(
            result["branch"],
            "issue-19/product-discovery-hypothesis-preregistration-37412f31")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(len(calls), 3)  # stopped polling once found

    def test_never_found_reports_unfound_not_an_exception(self):
        import json as _json
        empty = _json.dumps([])
        fake_run, calls = self._fake_run([empty] * 4)
        with mock.patch("subprocess.run", fake_run):
            result = rcp._discover_arm_branch(
                "JiwonJung94/study-companion", 19, retries=4, delay_s=0,
                _sleep=lambda s: None)
        self.assertFalse(result["found"])
        self.assertIsNone(result["branch"])
        self.assertEqual(result["attempts"], 4)
        self.assertIn("no PR", result["reason"])
        self.assertEqual(len(calls), 4)

    def test_gh_failure_is_retried_not_raised(self):
        """A transient `gh` failure (rate limit, network blip) must not
        crash the caller -- it is recorded and retried like an empty
        result, per this function's own "never raises" contract."""
        calls = []

        def _run(cmd, capture_output, text, timeout):
            calls.append(cmd)
            if len(calls) == 1:
                return mock.Mock(returncode=1, stdout="", stderr="rate limited")
            import json as _json
            return mock.Mock(returncode=0, stdout=_json.dumps([
                {"number": 5, "headRefName": "issue-19/x",
                 "createdAt": "2026-09-03T00:00:00Z"}]), stderr="")

        with mock.patch("subprocess.run", _run):
            result = rcp._discover_arm_branch(
                "acme/sandbox", 19, retries=4, delay_s=0, _sleep=lambda s: None)
        self.assertTrue(result["found"])
        self.assertEqual(len(calls), 2)


class ComputeH1ManipulationTest(unittest.TestCase):
    """H1 must be an actual, code-enforced comparison, capable of both
    passing and failing -- not prose.

    Re-operationalized 2026-09-02 (issue #3127 consult,
    `runs/consult-logs/20260902T125610799701-948846.log`): PR #3172 found,
    with live evidence from two real skills-on sessions, that the
    original directive_composition_bytes proxy cannot see a
    skills-on/skills-off difference for a skill delivered via the
    runtime Skill tool -- both real workspaces held identical baseline
    bytes regardless of which skill was mounted. The gate now reads
    `<workspace>.session.*.log` (the same artifact
    `scripts/measure_skill_invocation.py` already parses in production)
    for a real `Skill` tool_use call naming the target skill; these
    fixtures build that log directly instead of only varying directive
    bytes."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _make_workspace(self, name: str, directive_bytes: bytes | None,
                         session_log_lines: list[str] | None = None) -> Path:
        ws = Path(self._tmpdir.name) / name
        directive_dir = ws / ".on-the-record" / "directive"
        directive_dir.mkdir(parents=True)
        if directive_bytes is not None:
            (directive_dir / "core.md").write_bytes(directive_bytes)
        if session_log_lines is not None:
            log_path = ws.parent / (ws.name + ".session.20260902T000000.1.log")
            log_path.write_text("\n".join(session_log_lines) + "\n",
                                 encoding="utf-8")
        return ws

    def test_on_invoked_off_did_not_passes(self):
        on_ws = self._make_workspace(
            "on", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        off_ws = self._make_workspace(
            "off", b"a" * 12, session_log_lines=[_init_line(False)])
        result = rcp.compute_h1_manipulation(on_ws, off_ws, SKILL_NAME)
        self.assertTrue(result["differs"])
        self.assertIsNone(result["reason"])
        self.assertTrue(result["on_invocation"]["invoked"])
        self.assertFalse(result["off_invocation"]["invoked"])

    def test_neither_arm_invoked_flagged_as_manipulation_failure(self):
        """On arm never actually called the Skill tool even though it was
        configured to -- H1 must catch this, not silently pass it
        through to H2."""
        on_ws = self._make_workspace(
            "on", b"same content twice-over padding",
            session_log_lines=[_init_line(True)])
        off_ws = self._make_workspace(
            "off", b"same content twice-over padding",
            session_log_lines=[_init_line(False)])
        result = rcp.compute_h1_manipulation(on_ws, off_ws, SKILL_NAME)
        self.assertFalse(result["differs"])
        self.assertIsNotNone(result["reason"])

    def test_both_arms_invoked_is_a_leak_and_fails(self):
        """Mirror image of issue #3053's retracted zero-mount run: the
        skills-off arm's isolation leaked and it invoked the skill too."""
        on_ws = self._make_workspace(
            "on", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        off_ws = self._make_workspace(
            "off", b"a" * 12,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        result = rcp.compute_h1_manipulation(on_ws, off_ws, SKILL_NAME)
        self.assertFalse(result["differs"])
        self.assertIn("ALSO recorded", result["reason"])

    def test_missing_on_session_log_is_a_failure_not_a_skip(self):
        on_ws = self._make_workspace("on", b"a" * 5000)  # no session log
        off_ws = self._make_workspace(
            "off", b"a" * 12, session_log_lines=[_init_line(False)])
        result = rcp.compute_h1_manipulation(on_ws, off_ws, SKILL_NAME)
        self.assertFalse(result["differs"])
        self.assertFalse(result["on_invocation"]["measured"])

    def test_missing_on_session_log_without_repo_issue_is_never_dispatched(self):
        """Back-compat: a caller that supplies no repo/issue (the shape
        every pre-round-3 call site used) keeps the old label -- this
        behavior is unchanged unless a caller opts into discovery."""
        on_ws = self._make_workspace("on", b"a" * 5000)  # no session log
        result = rcp.collect_skill_invocation(on_ws, SKILL_NAME)
        self.assertEqual(result["status"], "never-dispatched")
        self.assertIn("never reached a dispatched", result["reason"])

    def test_missing_session_log_with_repo_issue_but_no_pr_is_unknown_not_never_dispatched(self):
        """Issue #3245 round 3: round 2's `01-study-groups` pair dispatched
        and watched BOTH arms to completion (dispatch_returncode 0,
        watch_returncode 0) but this file's own H1 check still reported
        "the arm never reached a dispatched, log-producing state" --
        false, because the guessed workspace path never matched the real
        one. When a caller supplies repo/issue, a missing log must not be
        silently reported as "never happened" if it also cannot be
        resolved by discovery -- it is "unknown"."""
        on_ws = self._make_workspace("on", b"a" * 5000)  # no session log
        with mock.patch.object(rcp, "_discover_arm_branch") as m_disc:
            m_disc.return_value = {"found": False, "branch": None,
                                    "pr_number": None, "attempts": 3,
                                    "reason": "no PR found after 3 polls"}
            result = rcp.collect_skill_invocation(
                on_ws, SKILL_NAME, repo="acme/sandbox", issue=19)
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(result["measured"])
        self.assertIn("unobservable, not evidence the arm never ran",
                       result["reason"])
        self.assertNotIn("never reached a dispatched", result["reason"])
        m_disc.assert_called_once_with("acme/sandbox", 19)

    def test_missing_guessed_log_but_discovered_branch_finds_the_real_one(self):
        """The core repair: the workspace path this harness guesses
        (built from the skill name) is not the workspace spawn.py's
        `--skills` dispatch actually used (it appends a disambiguator
        minted at dispatch time -- see `_discover_arm_branch()`'s
        docstring). Discovering the real branch and re-deriving the
        workspace path from it must find the log the guess missed."""
        guessed_ws = self._make_workspace("sandbox-issue-19-my-skill",
                                           b"a" * 5000)  # no log here
        real_ws = self._make_workspace(
            "sandbox-issue-19-my-skill-37412f31", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        with mock.patch.object(rcp, "_discover_arm_branch") as m_disc:
            m_disc.return_value = {
                "found": True,
                "branch": "issue-19/my-skill-37412f31",
                "pr_number": 29, "attempts": 2}
            result = rcp.collect_skill_invocation(
                guessed_ws, SKILL_NAME, repo="acme/sandbox", issue=19)
        self.assertTrue(result["measured"])
        self.assertTrue(result["invoked"])
        self.assertEqual(result["session_log"],
                          str(real_ws.parent /
                              (real_ws.name + ".session.20260902T000000.1.log")))

    def test_missing_off_session_log_is_compatible_with_h1_pass(self):
        """The skills-off arm never dispatched at all (PR #3172's actual
        real-run outcome for both registered pairs) -- absence of
        invocation evidence is itself evidence of non-invocation, so this
        does not by itself fail the gate."""
        on_ws = self._make_workspace(
            "on", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        off_ws = self._make_workspace("off", b"a" * 12)  # no session log
        result = rcp.compute_h1_manipulation(on_ws, off_ws, SKILL_NAME)
        self.assertTrue(result["differs"])
        self.assertFalse(result["off_invocation"]["measured"])

    def test_no_skill_name_is_a_failure(self):
        on_ws = self._make_workspace(
            "on", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        result = rcp.compute_h1_manipulation(on_ws, None, None)
        self.assertFalse(result["differs"])
        self.assertIn("no skill_name supplied", result["reason"])

    def test_directive_bytes_are_reported_but_never_gate(self):
        """Byte-identical arms must still pass H1 as long as invocation
        genuinely differs -- the construct-validity fix's core claim."""
        on_ws = self._make_workspace(
            "on", b"identical baseline bytes",
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        off_ws = self._make_workspace(
            "off", b"identical baseline bytes",
            session_log_lines=[_init_line(False)])
        result = rcp.compute_h1_manipulation(on_ws, off_ws, SKILL_NAME)
        self.assertTrue(result["differs"])
        self.assertEqual(result["directive_bytes_parity"]["on_bytes"],
                          result["directive_bytes_parity"]["off_bytes"])


class GatePairOnH1Test(unittest.TestCase):
    """The gate must refuse to even CALL the H2 scorer for a pair that
    fails H1 -- not just fail to report it afterward."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)

    def _make_workspace(self, name: str, directive_bytes: bytes,
                         session_log_lines: list[str] | None = None) -> Path:
        ws = Path(self._tmpdir.name) / name
        directive_dir = ws / ".on-the-record" / "directive"
        directive_dir.mkdir(parents=True)
        (directive_dir / "core.md").write_bytes(directive_bytes)
        if session_log_lines is not None:
            log_path = ws.parent / (ws.name + ".session.20260902T000000.1.log")
            log_path.write_text("\n".join(session_log_lines) + "\n",
                                 encoding="utf-8")
        return ws

    def test_h1_failure_excludes_pair_and_never_calls_h2_scorer(self):
        on_ws = self._make_workspace(
            "on", b"identical", session_log_lines=[_init_line(True)])
        off_ws = self._make_workspace(
            "off", b"identical", session_log_lines=[_init_line(False)])
        calls = []

        def compute_h2():
            calls.append(1)
            return {"should": "never run"}

        result = rcp.gate_pair_on_h1("01-study-groups", on_ws, off_ws,
                                      skill_name=SKILL_NAME,
                                      compute_h2=compute_h2)
        self.assertTrue(result["excluded_from_h2"])
        self.assertIsNone(result["h2"])
        self.assertIn("H1 manipulation check failed", result["exclusion_reason"])
        self.assertEqual(calls, [])  # compute_h2 was never invoked

    def test_h1_pass_calls_h2_scorer_and_includes_pair(self):
        on_ws = self._make_workspace(
            "on", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        off_ws = self._make_workspace(
            "off", b"a" * 12, session_log_lines=[_init_line(False)])
        result = rcp.gate_pair_on_h1("01-study-groups", on_ws, off_ws,
                                      skill_name=SKILL_NAME,
                                      compute_h2=lambda: {"verdict": "ok"})
        self.assertFalse(result["excluded_from_h2"])
        self.assertEqual(result["h2"], {"verdict": "ok"})

    def test_h1_pass_with_no_scorer_supplied_leaves_h2_none_distinctly(self):
        on_ws = self._make_workspace(
            "on", b"a" * 5000,
            session_log_lines=[_init_line(True), _tool_use_line(SKILL_NAME)])
        off_ws = self._make_workspace(
            "off", b"a" * 12, session_log_lines=[_init_line(False)])
        result = rcp.gate_pair_on_h1("01-study-groups", on_ws, off_ws,
                                      skill_name=SKILL_NAME)
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


class ExecuteArmWallClockTest(unittest.TestCase):
    """defect 4: execute_arm() must never label session-end time as
    "landed" -- wall_clock_to_landed_s is always None with an explicit
    reason, and the honestly-measured number lives under
    wall_clock_to_pr_open_s."""

    def _plan(self):
        import argparse
        args = argparse.Namespace(
            repo="/tmp/sandbox", pinned_sha=None,
            skill="my-skill", model="sonnet", pairs="01-study-groups",
            skill_repo_on="$MUSTER_SKILL_REGISTRY_ROOT",
            skill_repo_off=None, watch_timeout=5)
        return rcp.build_plan(args)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._plan_cache.arms[1].skill_repo_env_override,
                       ignore_errors=True)

    def _fake_completed(self, returncode=0, stderr=""):
        class _Result:
            pass
        r = _Result()
        r.returncode = returncode
        r.stderr = stderr
        r.stdout = ""
        return r

    def test_successful_run_reports_pr_open_not_landed(self):
        self._plan_cache = plan = self._plan()
        pair = plan.pairs[0]
        arm = plan.arms[0]

        def fake_run(cmd, **kwargs):
            return self._fake_completed(returncode=0)

        import unittest.mock as mock
        with mock.patch.object(rcp.subprocess, "run", side_effect=fake_run):
            result = rcp.execute_arm(plan, pair, arm, 999,
                                      confirm_real_spawn=True)

        self.assertEqual(result["status"], "watched-to-completion")
        self.assertIsInstance(result["wall_clock_to_pr_open_s"], float)
        self.assertIsNone(result["wall_clock_to_landed_s"])
        self.assertIn("not_measured", result["landing_measurement_status"])
        self.assertIn("phase-1 proposal PR", result["landing_measurement_status"])

    def test_watch_timeout_still_reports_pr_open_not_landed(self):
        self._plan_cache = plan = self._plan()
        pair = plan.pairs[0]
        arm = plan.arms[0]
        calls = {"n": 0}

        def fake_run(cmd, **kwargs):
            calls["n"] += 1
            if calls["n"] <= 2:
                return self._fake_completed(returncode=0)
            raise __import__("subprocess").TimeoutExpired(cmd, kwargs.get("timeout"))

        import unittest.mock as mock
        with mock.patch.object(rcp.subprocess, "run", side_effect=fake_run):
            result = rcp.execute_arm(plan, pair, arm, 999,
                                      confirm_real_spawn=True)

        self.assertEqual(result["status"], "watch-timed-out")
        self.assertIsInstance(result["wall_clock_to_pr_open_s"], float)
        self.assertIsNone(result["wall_clock_to_landed_s"])
        self.assertIn("not_measured", result["landing_measurement_status"])


class EmitNotExecutedResultsTest(unittest.TestCase):
    """Issue #3127 repair round 2 (PR #3158 finding): emit_not_executed_
    results() was defined but never called from anywhere, so the
    committed docs/issue-3127/_assets/consumer-path-results.json skeleton
    drifted from it -- it kept the pre-defect-4 single
    wall_clock_to_landed_s field with no wall_clock_to_pr_open_s and no
    landing_measurement_status reason. This class covers the function
    directly; CliEmitNotExecutedTest below covers the --emit-not-executed
    CLI wiring that makes it reachable."""

    def _plan(self):
        import argparse
        args = argparse.Namespace(
            repo="/tmp/sandbox", pinned_sha=None,
            skill="my-skill", model="sonnet", pairs="01-study-groups",
            skill_repo_on="$MUSTER_SKILL_REGISTRY_ROOT",
            skill_repo_off=None, watch_timeout=5)
        return rcp.build_plan(args)

    def test_arms_carry_both_wall_clock_fields_with_a_reason(self):
        plan = self._plan()
        self.addCleanup(__import__("shutil").rmtree,
                         plan.arms[1].skill_repo_env_override, ignore_errors=True)
        results = rcp.emit_not_executed_results(plan)
        for arm_name in ("skills-on", "skills-off"):
            arm = results["arms"][arm_name]
            self.assertIn("wall_clock_to_pr_open_s", arm)
            self.assertIsNone(arm["wall_clock_to_pr_open_s"])
            self.assertIn("wall_clock_to_landed_s", arm)
            self.assertIsNone(arm["wall_clock_to_landed_s"])
            self.assertIn("landing_measurement_status", arm)
            self.assertTrue(arm["landing_measurement_status"])


class CliEmitNotExecutedTest(unittest.TestCase):
    """Proves --emit-not-executed actually reaches
    emit_not_executed_results() end to end through main(), not just that
    the function is callable in isolation -- the shape of defect this
    round's must-not (do not mock the function under test) targets."""

    def test_cli_writes_file_matching_the_function_output(self):
        import json
        import subprocess
        import tempfile as _tempfile
        with _tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "results.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "issue-3127" /
                                      "run_consumer_pair.py"),
                 "--emit-not-executed", "--out", str(out_path)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(out_path.is_file())
            data = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(data["run_status"], "not_executed")
            for arm_name in ("skills-on", "skills-off"):
                arm = data["arms"][arm_name]
                self.assertIn("wall_clock_to_pr_open_s", arm)
                self.assertIn("wall_clock_to_landed_s", arm)
                self.assertTrue(arm["landing_measurement_status"])


if __name__ == "__main__":
    unittest.main()
