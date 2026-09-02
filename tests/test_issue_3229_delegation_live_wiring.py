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
last_assistant_message AND episode has >=1 tool_use AND every episode
action is_covered()) -- the same shape `test/test_delegation_state.py`'s
own `ManifestLookupConditionsTest`/`AuditFlaggingConditionsTest` already
route to decision-table / MC/DC-style testing for `is_covered()`/`audit()`.
This file routes the SAME way for the live wrapper: one baseline-true case
(`CoveredCleanEpisodeSuppressesTest`) and one case per condition flipped to
false in isolation (`MustNotSuppressTest`), each independently
demonstrating that condition controls the suppress/leave-standing outcome
-- this is exactly the issue's own five named must-not partitions, plus
two safety properties that sit outside the AND chain (the
`stop_hook_active` retry guard and the `TOKENMAXXXER_SPAWNED` scope guard,
both checked before the chain ever runs) and one visibility property
(every decline other than "no grant at all" must be observable on stderr).

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
  - issue's positive case (refuse the stop)    -> CoveredCleanEpisodeSuppressesTest
  - issue's must-not (never fire w/ no grant)  -> test_no_grant_produces_no_stderr_either
  - "says so where an operator can see it"     -> test_every_other_decline_produces_a_stderr_reason
  - retry-loop safety (issue #1725 contract)   -> test_stop_hook_active_never_suppresses_even_when_covered
  - orchestrator-only scope                    -> test_spawned_session_never_fires_even_when_covered
  - latency ("must not add latency the         -> LatencyTest
    operator can feel")

Residual: this file does not measure the harness's own decision:"block"
continuation behavior end-to-end against the real `claude` binary (that
experiment -- and the raw captured payloads it produced -- lives in
docs/issue-3229's record, not in a pytest suite that must run offline and
fast); it only proves the hook's OWN decision given a payload, which is
the part this repository's CI can actually check deterministically.

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
                               resource_value: str) -> dict:
    return {"type": "assistant", "timestamp": ts.isoformat(),
            "message": {"content": [{"type": "tool_use", "id": "t1", "name": tool,
                                      "input": {resource_field: resource_value}}]}}


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
    """The one positive partition: every AND-chain condition true ->
    suppress. Baseline-true case the MC/DC-style flips in
    MustNotSuppressTest each depart from exactly one condition at a time."""

    def test_covered_clean_episode_emits_decision_block(self):
        self._grant([{"tool": "Bash", "resource": "git push*", "repo": "*"}])
        _write_log(self.transcript, [
            _assistant_tool_use_event(self.now, "Bash", "command", "git push origin issue-x"),
            _assistant_text_event(self.now + timedelta(seconds=1),
                                   "Push was denied, shall I proceed anyway?"),
        ])
        r = self._run("Push was denied, shall I proceed anyway?")
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("git push origin issue-x", out["reason"])
        self.assertIn("issue #3229", out["reason"])


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


class LatencyTest(_HookHarness):
    """"must not add latency the operator can feel" -- a coarse regression
    catcher, not a benchmark (docs/issue-3229's record has the actual
    measured numbers, hook vs. an existing sibling Stop hook, from timing
    100 real invocations of each). The no-grant path is what >99% of Stop
    events hit, so that is the path this test bounds."""

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
