"""Issue #3229: live wiring for issue #3061's standing-delegation checker.

Drives the real shipped hook (`bash on-the-record/hooks/delegation-live-check.sh`)
as a subprocess against constructed Stop-hook JSON payloads -- same harness
shape as `test/test_approval_gate_carriers.py` -- rather than importing
`delegation_state.live_stop_decision()` directly, because the issue's own
must-not clause asks for each case demonstrated "by driving the real hook
binary with a constructed Stop payload," not by calling a Python function
that stands in for it.

Test derivation (test-derivation skill). The Stop payload determines the
hook's outcome through a short-circuit AND chain (grant on record and in
force AND manifest well-formed and non-empty AND transcript readable AND
final event ask-shaped AND transcript text matches the payload's own
last_assistant_message AND episode has >=1 tool_use) -- the same shape
`test/test_delegation_state.py`'s own
`ManifestLookupConditionsTest`/`AuditFlaggingConditionsTest` already route
to decision-table / MC/DC-style testing for `is_covered()`/`audit()`.
This file routes the SAME way for the live wrapper: one case per
condition flipped to false in isolation (`MustNotSuppressTest`), each
independently demonstrating that condition controls the leave-standing
outcome -- this is exactly the issue's own five named must-not
partitions, plus two safety properties that sit outside the AND chain
(the `stop_hook_active` retry guard and the `TOKENMAXXXER_SPAWNED` scope
guard, both checked before the chain ever runs) and one visibility
property (every decline other than "no grant at all" must be observable
on stderr).

issue #3229 round 2 (PR #3236 finding 4): the shipped suite's
`CoveredCleanEpisodeSuppressesTest` asserted a `decision:"block"` positive
case -- every episode action covered implies the ask is redundant. PR
#3236 decisively reproduced that this is unsound: an episode of
innocuous, individually-covered actions immediately preceding a
text-only ask about a completely different, dangerous, never-attempted
action was suppressed too, because the transcript carries no field
correlating a specific tool_use event to the ask that follows it (issue
#3061 round 6). Round 2's fix retired the previous-episode-coverage path
entirely -- every return site became `suppress: False` -- and
`CoveredCleanEpisodeSuppressesTest`'s own assertion was rewritten to
match ("still leaves stop untouched"), but its CLASS NAME was not
updated, and stayed "Suppresses" through PR #3241/#3236/#3248's own
reviews -- exactly how the round-2 over-correction (a permanent no-op:
the hook never suppresses anything, for any input, while still running
on every Stop event) survived a full round of review undetected. PR
#3248's round-2 verification named it directly (Section B).

issue #3229 round 3 (this file): restores one narrow, structurally-bound
suppression path -- see `delegation_state.py`'s own module comment above
`_live_stop_decision_body` for the full reasoning, including the named
residual risk. `CoveredCleanEpisodeSuppressesTest`'s assertion is fixed
to match its own class name again (a real `decision:"block"` case);
`GenuineRedundantAskSuppressesTest` adds two more independently-shaped
suppress cases; `AdjacencyDoesNotImplyCoverageTest` and
`PriorReviewMustNotVariantsTest` reconstruct PR #3236's original
under-refusal case plus its three PR #3248 variants, all still declining;
`SingleFailedUnrelatedActionResidualRiskTest` documents, rather than
hides, the one gap the narrow fix does not close.

issue #3229 round 4 (PR #3255 boundary-probe finding, item 3): round 3's
structural triple (episode length 1, covered, `is_error=True`) alone
could not tell "shall I proceed anyway?" apart from "should I instead
force-push origin main?" -- both suppressed, and the second is exactly
the kind of thing an operator would want surfaced. Round 4 adds
`delegation_state._ask_names_wider_scope()`, a narrow, closed-set,
disclosed check for literal scope-escalation markers absent from what
was actually attempted (see its own module comment for the full
reasoning and limits).
`ScopeWideningAfterFailedActionLeavesStopStandingTest` adds four
independently-shaped cases proving the new check; every case round 3's
own verification (PR #3255) confirmed sound is re-proven unchanged
(re-run live, not re-derived, per this round's own task) --
`CoveredCleanEpisodeSuppressesTest`, `GenuineRedundantAskSuppressesTest`,
`AdjacencyDoesNotImplyCoverageTest`, and `PriorReviewMustNotVariantsTest`
below are untouched by this round.
`SingleFailedUnrelatedActionResidualRiskTest` is narrowed (its ask no
longer happens to use a recognized marker) so it keeps demonstrating the
still-open residual (an unrelated pivot phrased without any of the
closed-set markers) rather than a sub-shape round 4 now closes.

Classification (Step 3a): every requirement here is High -- a bug in
either direction (suppressing a genuine escalation, or never suppressing
anything and leaving the live-wiring gap PR #3220 named) is exactly what
issue #3229 exists to prevent. Full derivation, one named case per
partition, below.

Traceability:
  - issue's must-not (no manifest)            -> test_no_manifest_recorded_leaves_stop_untouched
  - issue's must-not (malformed manifest)      -> test_malformed_manifest_leaves_stop_untouched
  - issue's must-not (action outside manifest) -> test_action_outside_manifest_leaves_stop_untouched
  - issue's must-not (no derivable action)     -> test_no_derivable_action_leaves_stop_untouched
  - issue's must-not (episode not complete)    -> test_incomplete_episode_leaves_stop_untouched
  - genuine redundant ask suppresses           -> CoveredCleanEpisodeSuppressesTest,
    (round 3)                                     GenuineRedundantAskSuppressesTest
  - covered-episode adjacency is not enough    -> AdjacencyDoesNotImplyCoverageTest,
    to refuse the stop on its own               PriorReviewMustNotVariantsTest
    (round 2, PR #3236 #4; reconfirmed round 3)
  - scope-widening ask after a failed covered  -> ScopeWideningAfterFailedActionLeavesStopStandingTest
    action does not suppress (round 4, PR #3255)
  - single-failed-action residual risk,        -> SingleFailedUnrelatedActionResidualRiskTest
    disclosed not hidden (round 3, narrowed round 4)
  - issue's must-not (never fire w/ no grant)  -> test_no_grant_produces_no_stderr_either
  - "says so where an operator can see it"     -> test_every_other_decline_produces_a_stderr_reason
  - retry-loop safety (issue #1725 contract)   -> test_stop_hook_active_never_suppresses_even_when_covered
  - orchestrator-only scope                    -> test_spawned_session_never_fires_even_when_covered
  - latency ("must not add latency the         -> LatencyTest
    operator can feel", scoped to the no-grant
    path -- see that class's own docstring)
  - crash direction (round 2, PR #3236 #3)     -> InternalCrashDeclinesRatherThanBlocksTest
    (subprocess-level, not just the internal
    function)

Residual: this file does not measure the harness's own decision:"block"
continuation behavior end-to-end against the real `claude` binary (that
experiment -- and the raw captured payloads it produced -- lives in
docs/issue-3229's record, not in a pytest suite that must run offline and
fast); it only proves the hook's OWN decision given a payload, which is
the part this repository's CI can actually check deterministically. A
second, disclosed residual is named above
(`SingleFailedUnrelatedActionResidualRiskTest`).

Run: python3 -m pytest tests/test_issue_3229_delegation_live_wiring.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "delegation-live-check.sh"
sys.path.insert(0, str(REPO_ROOT))
import delegation_state as ds  # noqa: E402

# The exact field set captured from a REAL Stop-hook payload (issue #3229's
# record has the full captured JSON and how it was obtained: a temporary
# Stop hook registered via `claude -p ... --settings`, run against the
# real `claude` binary, stdin dumped to disk). Every test payload below is
# built from exactly this set -- nothing invented, nothing extra -- so a
# future real-payload shape drift shows up here as a failure, not silently.
REAL_STOP_PAYLOAD_FIELDS = frozenset({
    "session_id", "transcript_path", "cwd", "prompt_id", "permission_mode",
    "effort", "hook_event_name", "stop_hook_active", "last_assistant_message",
    "background_tasks", "session_crons",
})


def _write_log(path: Path, events: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")


def _assistant_text_event(ts: datetime, text: str) -> dict:
    return {"type": "assistant", "timestamp": ts.isoformat(),
            "message": {"content": [{"type": "text", "text": text}]}}


def _assistant_tool_use_event(ts: datetime, tool: str, resource_field: str,
                               resource_value: str, tool_use_id: str = "t1") -> dict:
    return {"type": "assistant", "timestamp": ts.isoformat(),
            "message": {"content": [{"type": "tool_use", "id": tool_use_id, "name": tool,
                                      "input": {resource_field: resource_value}}]}}


def _tool_result_event(ts: datetime, tool_use_id: str, is_error: bool,
                        text: str = "error") -> dict:
    # issue #3229 round 3: a `tool_result` block is a structural harness
    # fact about what the TOOL returned (`is_error`), not an inference
    # over what the model wrote -- this is what
    # `trajectory_analyzer.tool_result_index()` reads, and what the round
    # 3 single-failed-action suppression path keys off of.
    return {"type": "user", "timestamp": ts.isoformat(),
            "message": {"content": [{"type": "tool_result", "tool_use_id": tool_use_id,
                                      "is_error": is_error, "content": text}]}}


class _HookHarness(unittest.TestCase):
    """Shared setup: a real git-less repo directory (delegation_state.py
    only ever needs a filesystem path, never a real git checkout) plus a
    real transcript file, and a `_run()` that drives the actual shipped
    hook binary as a subprocess -- never imports `live_stop_decision()`
    directly, per this file's own module docstring."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = str(Path(self._tmp.name) / "repo")
        Path(self.repo).mkdir()
        self.transcript = Path(self._tmp.name) / "transcript.jsonl"
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        self._tmp.cleanup()

    def _grant(self, manifest):
        ds.grant(self.repo, "go ahead", "jiwon", skill_env="", manifest=manifest)

    def _run(self, last_assistant_message: str, stop_hook_active: bool = False,
              env_extra: dict | None = None):
        payload = {
            "session_id": "s1",
            "transcript_path": str(self.transcript),
            "cwd": self.repo,
            "prompt_id": "p1",
            "permission_mode": "bypassPermissions",
            "effort": {"level": "low"},
            "hook_event_name": "Stop",
            "stop_hook_active": stop_hook_active,
            "last_assistant_message": last_assistant_message,
            "background_tasks": [],
            "session_crons": [],
        }
        self.assertEqual(set(payload) - {"hook_event_name"}, REAL_STOP_PAYLOAD_FIELDS - {"hook_event_name"})
        env = dict(os.environ)
        env.pop("ORCHESTRATE_OFF", None)
        env.pop("TOKENMAXXXER_SPAWNED", None)
        env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            ["bash", str(HOOK_PATH)], input=json.dumps(payload),
            capture_output=True, text=True, cwd=self.repo, env=env, timeout=30,
        )


class RealPayloadShapeTest(_HookHarness):
    def test_real_captured_field_set_is_what_this_suite_builds_payloads_from(self):
        # Documents the real payload shape captured live (see module
        # docstring) as executable data, not just prose -- a future field
        # rename in the harness would break THIS assertion inside _run(),
        # not silently pass a stale fixture forever.
        self.assertIn("transcript_path", REAL_STOP_PAYLOAD_FIELDS)
        self.assertIn("stop_hook_active", REAL_STOP_PAYLOAD_FIELDS)
        self.assertIn("last_assistant_message", REAL_STOP_PAYLOAD_FIELDS)
        self.assertIn("cwd", REAL_STOP_PAYLOAD_FIELDS)


class CoveredCleanEpisodeSuppressesTest(_HookHarness):
    """issue #3229 round 3 (PR #3248 Section B, the round-3 defect): this
    class name has said "Suppresses" since round 1, but round 2 (PR #3236
    finding 4) rewrote its assertion to check the exact opposite --
    "still leaves stop untouched" -- while leaving the class name
    unchanged. That mismatch is how the round-2 over-correction (every
    return site in `_live_stop_decision_body()` became `suppress: False`,
    permanently) survived a round of review: a reader trusting the class
    name would believe suppression was still being exercised here. Fixed
    to actually assert suppression again, now that round 3 restores the
    narrow single-failed-action path (delegation_state.py's own module
    comment above `_live_stop_decision_body` has the full reasoning): a
    `git push` covered by the manifest, denied (`is_error=True` on its own
    `tool_result` -- the structural signal round 3 keys off, not the
    ask's prose), with nothing else in the episode, immediately followed
    by "shall I proceed anyway?" -- the textbook redundant-ask case this
    hook exists to remove."""

    def test_covered_clean_episode_suppresses(self):
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="remote rejected: push declined"),
            _assistant_text_event(self.now + timedelta(seconds=2),
                                   "Push was denied, shall I proceed anyway?"),
        ])
        r = self._run("Push was denied, shall I proceed anyway?")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotEqual(r.stdout, "", "expected a decision:\"block\" hook_output on stdout")
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block")
        self.assertIn("already-attempted, already-covered", r.stderr)


class AdjacencyDoesNotImplyCoverageTest(_HookHarness):
    """issue #3229 round 2 (PR #3236 finding 4, the most severe finding of
    that review): live reproduction of the exact adjacency defect --
    an episode of innocuous, individually-covered actions (a `git log`, a
    changelog read) immediately preceding a text-only ask about a
    completely different, dangerous, NEVER-attempted action (a force-push
    to main). The force-push is never issued as a tool_use event; the
    orchestrator is asking BEFORE attempting it, the canonical "ask before
    acting" pattern. Must leave the stop untouched."""

    def test_unrelated_dangerous_ask_after_covered_episode_leaves_stop_untouched(self):
        self._grant([{"tool": "Bash", "resource": "*", "repo": "*"},
                      {"tool": "Read", "resource": "*", "repo": "*"}])
        ask = ("The last three git log entries look suspicious. Should I "
               "force-push origin main to roll the release branch back to "
               "the previous release tag?")
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git log --oneline -20"),
            _assistant_tool_use_event(self.now + timedelta(seconds=1), "Read", "file_path", "CHANGELOG.md"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "",
                          "the hook must never suppress this stop -- the pending "
                          "force-push was never attempted, so nothing in the "
                          "preceding covered episode can be bound to it")
        self.assertIn("no field correlating this ask", r.stderr)


class GenuineRedundantAskSuppressesTest(_HookHarness):
    """issue #3229 round 3: two more genuine redundant-ask cases beyond
    `CoveredCleanEpisodeSuppressesTest`'s `git push`, each with a
    different tool/resource shape, all sharing the one structural pattern
    round 3 suppresses on: exactly one tool_use event in the episode, that
    action covered by the manifest, and its own `tool_result` reporting
    `is_error=True` -- attempted, blocked, then asked about again."""

    def test_covered_write_blocked_by_a_guard_suppresses(self):
        self._grant([{"tool": "Write", "resource": "*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Write", "file_path", "output.log"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="write blocked: guard denied this path"),
            _assistant_text_event(self.now + timedelta(seconds=2),
                                   "The write to output.log was blocked -- should I try again?"),
        ])
        r = self._run("The write to output.log was blocked -- should I try again?")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block")

    def test_covered_deploy_command_failed_suppresses(self):
        self._grant([{"tool": "Bash", "resource": "npm run deploy", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "npm run deploy"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="deploy failed: connection timed out"),
            _assistant_text_event(self.now + timedelta(seconds=2),
                                   "The deploy failed with a timeout -- should I retry it?"),
        ])
        r = self._run("The deploy failed with a timeout -- should I retry it?")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block")


class ScopeWideningAfterFailedActionLeavesStopStandingTest(_HookHarness):
    """issue #3229 round 4 (PR #3255 boundary-probe finding, item 3): the
    scope-widening shape the residual-risk disclosure had understated --
    a single covered action fails, and the ask that follows names a
    MATERIALLY WIDER scope than what was attempted (a destructive flag,
    a protected target never granted). Round 3's structural triple
    (episode length 1, covered, `is_error=True`) alone could not tell
    this apart from a genuine same-scope retry; round 4 adds
    `_ask_names_wider_scope()` (see delegation_state.py's own module
    comment above it) as an additional, narrow, closed-set check keyed
    off literal escalation markers absent from the attempted resource.
    Four independently-shaped cases below, all must leave the stop
    standing."""

    def test_narrow_push_denied_then_force_push_to_main_leaves_stop_standing(self):
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        ask = "Push was denied (non-fast-forward) -- should I instead run git push --force origin main?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="! [rejected] issue-x -> issue-x (non-fast-forward)"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "",
                          "a force-push to main was never attempted -- the narrow "
                          "git push grant does not extend to it just because the "
                          "verb rhymes")
        self.assertIn("materially wider scope", r.stderr)

    def test_deploy_command_failed_then_force_publish_to_production_leaves_stop_standing(self):
        self._grant([{"tool": "Bash", "resource": "npm run deploy", "repo": "*"}])
        ask = "The deploy failed -- should I skip verification and force-publish straight to production instead?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "npm run deploy"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="deploy failed: connection timed out"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_write_blocked_then_ask_about_writing_to_master_branch_leaves_stop_standing(self):
        self._grant([{"tool": "Write", "resource": "*", "repo": "*"}])
        ask = "The write was blocked by a guard -- should I instead commit this straight onto master?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Write", "file_path", "output.log"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="write blocked: guard denied this path"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_bash_command_failed_then_ask_with_dash_f_flag_leaves_stop_standing(self):
        self._grant([{"tool": "Bash", "resource": "rm build/*", "repo": "*"}])
        ask = "rm was denied by a guard -- should I retry with -f to skip the confirmation?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "rm build/stale.o"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="rm: permission denied"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")


class MarkerAlreadyGrantedDoesNotFalselyWidenTest(_HookHarness):
    """issue #3229 round 4 (test-derivation skill, decision-table gap):
    `_ask_names_wider_scope()` only counts a marker as widening when it
    is present in the ask but ABSENT from the attempted resource -- a
    marker already present on BOTH sides (the grant/attempt already used
    it) must not falsely trip the new check, or round 4 would itself
    over-refuse a genuine retry the same way round 2's blanket removal
    did. Two independently-shaped controls: a marker present on both
    sides (still suppresses), and a marker-shaped substring inside an
    unrelated word (word-boundary guard, still suppresses)."""

    def test_force_flag_already_in_the_attempted_command_does_not_widen(self):
        self._grant([{"tool": "Bash", "resource": "git push --force origin release-x", "repo": "*"}])
        ask = "The force push was rejected -- should I retry that same force push again?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push --force origin release-x"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="remote rejected"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block",
                          "the --force marker was already part of the granted, attempted "
                          "resource -- repeating it in the ask is not a widened scope")

    def test_word_boundary_false_positive_guard_maintain_is_not_main(self):
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        ask = "Push was denied -- I'll maintain the current branch and just retry, shall I proceed anyway?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="remote rejected"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block",
                          "'maintain' contains the substring 'main' but is not the word "
                          "'main' -- the word-boundary regex must not treat it as a "
                          "protected-target marker")


class SingleFailedUnrelatedActionResidualRiskTest(_HookHarness):
    """issue #3229 round 3 (narrowed, not closed, by round 4): the named,
    disclosed residual risk of the single-failed-action suppression path
    (see delegation_state.py's own module comment above
    `_live_stop_decision_body` for the full reasoning). `is_error=True`
    on the episode's one action is a structural fact about what the TOOL
    returned; it is NOT proof the ask that follows is about THAT action.
    Round 4 closes the sub-shape where the unrelated pivot happens to use
    one of `_ask_names_wider_scope()`'s literal markers (see
    `ScopeWideningAfterFailedActionLeavesStopStandingTest` above) -- but
    a pivot to a completely different, dangerous, never-attempted topic
    phrased WITHOUT any of those markers is still not distinguishable
    from the genuine redundant-ask shape by anything this transcript
    format carries. This test documents the actual (not hoped-for)
    behavior for that surviving, narrower gap: it suppresses, which is
    the wrong answer for THIS specific case."""

    def test_single_failed_covered_action_then_unrelated_dangerous_ask_still_suppresses(self):
        self._grant([{"tool": "Bash", "resource": "*", "repo": "*"}])
        ask = ("Never mind that -- should I go ahead and roll the release "
               "branch back to the previous tag instead?")
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "curl https://example.com/status"),
            _tool_result_event(self.now + timedelta(seconds=1), "t1", is_error=True,
                                text="curl: (28) connection timed out"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        # Documented residual risk, not the desired outcome: this DOES
        # suppress, even though the ask (rolling back the release branch)
        # has nothing to do with the failed curl call that precedes it,
        # and names no marker `_ask_names_wider_scope()` recognizes.
        out = json.loads(r.stdout)
        self.assertEqual(out.get("decision"), "block",
                          "if this assertion ever starts failing, the residual risk "
                          "named in delegation_state.py's module comment and this "
                          "test's own docstring may have been narrowed or closed -- "
                          "update both together rather than treating this as a bug")


class PriorReviewMustNotVariantsTest(_HookHarness):
    """issue #3229 round 3: the three independently-constructed variants
    from PR #3248's round-2 verification record (Section A) of PR #3236's
    original adjacency reproduction -- different action/ask shapes, same
    underlying defect class this suite must keep refusing. None of these
    actions ever error (no `tool_result` recorded at all, the realistic
    shape of an ordinary successful action), so the round-3
    single-failed-action suppression path never engages regardless of
    episode size -- must all leave the stop untouched exactly as PR #3248
    found."""

    def test_covered_write_then_unrelated_ask_about_deleting_prod_backups(self):
        self._grant([{"tool": "Write", "resource": "*", "repo": "*"}])
        ask = ("Finished writing the release notes. Should I also delete "
               "the production database backups from last month to free "
               "up space?")
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Write", "file_path", "RELEASE_NOTES.md"),
            _assistant_text_event(self.now + timedelta(seconds=1), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_covered_npm_test_then_unrelated_ask_about_force_publish(self):
        self._grant([{"tool": "Bash", "resource": "npm test", "repo": "*"}])
        ask = "Tests are green. Should I force-publish this over the existing tagged release?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "npm test"),
            _assistant_text_event(self.now + timedelta(seconds=1), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_covered_edit_and_read_pair_then_unrelated_ask_about_revoking_admin(self):
        self._grant([{"tool": "Edit", "resource": "*", "repo": "*"},
                      {"tool": "Read", "resource": "*", "repo": "*"}])
        ask = "By the way, should I also revoke the ops team's admin access on this repo?"
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Read", "file_path", "CONTRIBUTORS.md",
                                       tool_use_id="t1"),
            _assistant_tool_use_event(self.now + timedelta(seconds=1), "Edit", "file_path",
                                       "CONTRIBUTORS.md", tool_use_id="t2"),
            _assistant_text_event(self.now + timedelta(seconds=2), ask),
        ])
        r = self._run(ask)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")


class MustNotSuppressTest(_HookHarness):
    """Each case departs from CoveredCleanEpisodeSuppressesTest's baseline
    on exactly ONE AND-chain condition, demonstrating that condition alone
    controls the suppress/leave-standing outcome -- MC/DC-style, matching
    test/test_delegation_state.py's own established derivation shape for
    is_covered()/audit(). Every case here must leave stdout EMPTY (the
    literal "leaves the stop untouched" the issue's must-not asks for)."""

    def test_no_manifest_recorded_leaves_stop_untouched(self):
        # No grant() call at all -- condition 1 false.
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1), "shall I proceed?"),
        ])
        r = self._run("shall I proceed?")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_malformed_manifest_leaves_stop_untouched(self):
        # A grant on record and in force, but its manifest field is not
        # list-shaped -- condition 2 false. Written directly (not via
        # grant(), which validates and would refuse) to reproduce a
        # genuinely malformed on-disk record.
        state_dir = Path(self.repo) / ".on-the-record"
        state_dir.mkdir(parents=True)
        record = {
            "scope": "go", "granted_by": "j",
            "granted_at": self.now.isoformat(),
            "expires_at": (self.now + timedelta(hours=1)).isoformat(),
            "revoked_at": None, "revoked_by": None,
            "manifest": "not-a-list",
        }
        (state_dir / "delegation-state.json").write_text(json.dumps(record))
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1), "shall I proceed?"),
        ])
        r = self._run("shall I proceed?")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_action_outside_manifest_leaves_stop_untouched(self):
        # Manifest well-formed and non-empty, but covers a different
        # action -- condition 7 (every episode action covered) false.
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command",
                                       "rm -rf /var/lib/postgres"),
            _assistant_text_event(self.now + timedelta(seconds=1), "shall I proceed?"),
        ])
        r = self._run("shall I proceed?")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_no_derivable_action_leaves_stop_untouched(self):
        # No tool_use event anywhere in the episode -- condition 6 (episode
        # has >=1 action) false: a pure conversational ask, nothing to
        # derive coverage against.
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_text_event(self.now, "what should I do next?"),
        ])
        r = self._run("what should I do next?")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_incomplete_episode_leaves_stop_untouched(self):
        # The transcript's final assistant text disagrees with the Stop
        # payload's own last_assistant_message -- condition 5 (episode can
        # be established as complete) false: the live analog of the
        # truncated-log ambiguity issue #3061's audit() already guards
        # against retrospectively (TruncatedLogIndeterminateTest in
        # test/test_delegation_state.py), reproduced here at Stop time.
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1),
                                   "Push was denied, shall I proceed anyway?"),
        ])
        r = self._run("a completely different message the transcript never recorded")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_tool_use_in_final_event_is_not_ask_shaped_leaves_stop_untouched(self):
        # Defensive case: the harness would never actually fire Stop on a
        # message still carrying a pending tool_use (it runs the tool
        # first), but this hook must not assume that and must decline
        # rather than crash or misclassify if it ever saw one.
        self._grant([{"tool": "Bash", "resource": "*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git status"),
        ])
        r = self._run("git status")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")


class RetryAndScopeSafetyTest(_HookHarness):
    """Two properties outside the AND chain, checked before it ever runs."""

    def test_stop_hook_active_never_suppresses_even_when_covered(self):
        # issue #1725 contract: a forced-retry turn (this hook's own prior
        # suppression, or any other Stop hook's) must never re-suppress --
        # otherwise a covered episode could loop the harness forever.
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1),
                                   "Push was denied, shall I proceed anyway?"),
        ])
        r = self._run("Push was denied, shall I proceed anyway?", stop_hook_active=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")

    def test_spawned_session_never_fires_even_when_covered(self):
        # A spawned (skill) session is never the orchestrator asking the
        # operator a question -- must not fire at all, even on an
        # otherwise-textbook covered episode.
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1),
                                   "Push was denied, shall I proceed anyway?"),
        ])
        r = self._run("Push was denied, shall I proceed anyway?",
                       env_extra={"TOKENMAXXXER_SPAWNED": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "")


class VisibilityTest(_HookHarness):
    """"must not silently do nothing when it cannot decide: every path
    that declines to act says so where an operator can see it" -- except
    the one explicitly-silent case, "must not fire on sessions that have
    no recorded grant at all"."""

    def test_no_grant_produces_no_stderr_either(self):
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1), "shall I proceed?"),
        ])
        r = self._run("shall I proceed?")
        self.assertEqual(r.stdout, "")
        self.assertEqual(r.stderr, "")

    def test_every_other_decline_produces_a_stderr_reason(self):
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command",
                                       "rm -rf /var/lib/postgres"),
            _assistant_text_event(self.now + timedelta(seconds=1), "shall I proceed?"),
        ])
        r = self._run("shall I proceed?")
        self.assertEqual(r.stdout, "")
        self.assertNotEqual(r.stderr.strip(), "")
        self.assertIn("leaving the question standing", r.stderr)


class InternalCrashDeclinesRatherThanBlocksTest(_HookHarness):
    """issue #3229 silent-failure audit finding, fixed before landing: an
    uncaught exception inside the decision must decline (suppress=False),
    never propagate into the hook's own trap remapping it to a BLOCKING
    exit code -- the one outcome that would be worse than never running at
    all, since it would suppress a question via a crash instead of via a
    real, checked decision. Exercised at the Python layer directly
    (`live_stop_decision()`'s own crash barrier), since reliably forcing a
    mid-flight OS-level crash (a file removed between the readability
    check and the parse) through a subprocess boundary would be flaky by
    construction."""

    def test_uncaught_exception_during_derivation_still_declines(self):
        import unittest.mock as mock
        import trajectory_analyzer

        self._grant([{"tool": "Bash", "resource": "*", "repo": "*"}])
        self.transcript.write_text("")
        with mock.patch.object(trajectory_analyzer, "parse_session_log",
                                side_effect=PermissionError("simulated")):
            decision = ds.live_stop_decision(
                {"transcript_path": str(self.transcript), "cwd": self.repo,
                 "last_assistant_message": "shall I proceed?"},
                self.repo,
            )
        self.assertFalse(decision["suppress"])
        self.assertIsNone(decision["hook_output"])
        self.assertIn("internal error", decision["reason"])


class ForcedExit2AtShellLayerDoesNotBlockTest(_HookHarness):
    """issue #3229 round 2 (PR #3236 finding 3): the shipped hook's last
    three lines disabled its own top-of-file safety trap (`trap - EXIT`)
    immediately before the one exit that matters most -- the invoked
    `python3 -c "$CHECK"` call -- so a crash that happened to exit with
    the literal code 2 (a C-level interpreter fault, or a future edit
    that calls `sys.exit()` with a nonzero argument for an unrelated
    reason) would have forced the same-turn continuation exactly like
    `decision:"block"` does, independent of stdout. Fixed by leaving the
    trap active through the final exit instead of disabling it. This test
    drives that exact boundary -- the real subprocess/shell-trap seam,
    not `live_stop_decision()`'s internal try/except (already covered by
    InternalCrashDeclinesRatherThanBlocksTest above) -- by forcing the
    invoked python program itself to exit 2, the shape no test in the
    original suite exercised."""

    def test_python_program_forced_to_exit_2_still_exits_0(self):
        scratch = Path(self._tmp.name) / "delegation-live-check-crashtest.sh"
        original = HOOK_PATH.read_text()
        self.assertEqual(original.count("import delegation_state as ds"), 1,
                          "fixture assumption: exactly one import site to patch")
        crashing = original.replace(
            "import delegation_state as ds\n",
            "import delegation_state as ds\nimport sys as _crash; _crash.exit(2)\n",
            1,
        )
        # Runs from HOOK_PATH's own directory (not the scratch tempdir) so
        # this hook's own `dirname "${BASH_SOURCE[0]}"`-based sourcing of
        # hook-fires.sh/poll-rearm.sh still resolves -- only the CHECK
        # heredoc content is mutated, not the script's location.
        real_scratch = HOOK_PATH.parent / "delegation-live-check-crashtest.sh"
        real_scratch.write_text(crashing)
        self.addCleanup(real_scratch.unlink)

        _write_log(self.transcript, [_assistant_text_event(self.now, "hello")])
        env = dict(os.environ)
        env.pop("ORCHESTRATE_OFF", None)
        env.pop("TOKENMAXXXER_SPAWNED", None)
        env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
        payload = json.dumps({
            "session_id": "s1", "transcript_path": str(self.transcript),
            "cwd": self.repo, "stop_hook_active": False,
            "last_assistant_message": "hello",
        })
        r = subprocess.run(["bash", str(real_scratch)], input=payload,
                            capture_output=True, text=True, cwd=self.repo,
                            env=env, timeout=30)
        self.assertEqual(r.returncode, 0,
                          f"a python-layer exit(2) must never propagate as this "
                          f"hook's own exit code -- exit 2 on a Stop event forces "
                          f"the same-turn continuation exactly like "
                          f"decision:\"block\" does (docs/issue-3229's record has "
                          f"the harness-level confirmation); stderr={r.stderr!r}")


class LatencyTest(_HookHarness):
    """"must not add latency the operator can feel" -- a coarse regression
    catcher, not a benchmark (docs/issue-3229's record has the actual
    measured numbers, hook vs. an existing sibling Stop hook, from timing
    100 real invocations of each). The no-grant path is what >99% of Stop
    events hit, so that is the path this test bounds.

    Scope (issue #3229 round 2, PR #3236 finding 6, Surface): the
    "dominated by interpreter startup" measurement holds for this
    no-grant path and for a small manifest at any transcript length --
    independently re-measured at ~40ms avg. It does NOT hold for a large
    manifest: latency roughly triples at 2000 manifest entries
    (`is_covered()` re-validates the whole manifest via `_safe_manifest()`
    on every call, an O(manifest size) walk done at least twice per
    invocation). 2000 entries is not a realistic size for a hand-authored
    "go ahead" grant, so this is scoped honestly here rather than
    claimed generally; no manifest-size regression test is added since
    fixing the re-validation is out of this round's scope (PR #3236's
    own record names the cheap fix: validate once, pass the validated
    list through)."""

    def test_no_grant_path_completes_quickly(self):
        _write_log(self.transcript, [
            _assistant_text_event(self.now, "hello"),
        ])
        payload = json.dumps({
            "session_id": "s1", "transcript_path": str(self.transcript),
            "cwd": self.repo, "stop_hook_active": False,
            "last_assistant_message": "hello",
        })
        env = dict(os.environ)
        env.pop("ORCHESTRATE_OFF", None)
        env.pop("TOKENMAXXXER_SPAWNED", None)
        env["TOKENMAXXXER_CHECKOUT"] = str(REPO_ROOT)
        start = time.monotonic()
        r = subprocess.run(["bash", str(HOOK_PATH)], input=payload,
                            capture_output=True, text=True, cwd=self.repo,
                            env=env, timeout=30)
        elapsed = time.monotonic() - start
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertLess(elapsed, 2.0,
                         f"no-grant path took {elapsed:.3f}s -- expected well under a "
                         f"second (dominated by python3 interpreter startup, same as "
                         f"every sibling Stop hook)")


if __name__ == "__main__":
    unittest.main()
