"""Issue #2681: a mounted skill can go un-invoked for a whole session with
no signal anywhere -- #2153's narrowing (mounted-but-never-invoked owes no
skill-verdict line) has a floor at zero: "mounted zero skills" and
"mounted N skills, invoked zero" used to produce byte-identical output
from `on-the-record/hooks/skill-verdict-guard.sh` (at most the folded
obligations reminder, dedup'd per session).

Runs the real shipped hook via a real Stop-event JSON payload on stdin
against a fabricated transcript file -- same harness shape as
test/test_deliverable_guard_priorities_shard.py.

Acceptance covered here:
  - a run that mounts skills and invokes none is distinguishable from a
    run that mounts none, and the artifact carrying the distinction is
    named -- ZeroMountedVsZeroInvokedTest
  - the signal lands in the Stop hook's additionalContext, the same
    channel `spawn.py watch`/session logs already surface to a human or
    the orchestrator -- SignalLandsInAdditionalContextTest
  - replaying the issue's own consumer-session shape (one mounted skill,
    zero invocations) fires the signal -- ConsumerSessionReplayTest
  - invoking at least one mounted skill suppresses the new notice (no
    behavior change to the existing #2153 path) -- InvokedSuppressesNoticeTest

Run: python3 -m pytest test/test_skill_verdict_guard_zero_invocation_signal.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "skill-verdict-guard.sh"
_FIXTURE_BASE = Path.home() / ".otr-svg-test-fixture"


def _write_transcript(path: Path, skill_tool_uses: list[str]):
    """One assistant transcript line per name in `skill_tool_uses`, each a
    tool_use block named "Skill" invoking that name -- empty list means a
    transcript with no Skill tool call at all."""
    lines = []
    for name in skill_tool_uses:
        lines.append(json.dumps({
            "type": "assistant",
            "message": {"content": [
                {"type": "tool_use", "name": "Skill", "input": {"skill": name}},
            ]},
        }))
    if not lines:
        lines.append(json.dumps({
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "no skill calls here"}]},
        }))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_guard(repo: Path, transcript_path: Path, mounted: str, session_id: str):
    payload = json.dumps({
        "session_id": session_id,
        "transcript_path": str(transcript_path),
        "stop_hook_active": False,
    })
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    env["MUSTER_SKILLS"] = mounted
    env.pop("HOME", None)
    env["HOME"] = str(_FIXTURE_BASE)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload, capture_output=True, text=True,
        cwd=repo, env=env, timeout=30,
    )


def _additional_context(result: subprocess.CompletedProcess) -> str:
    if not result.stdout.strip():
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


class _GuardTestBase(unittest.TestCase):
    def setUp(self):
        _FIXTURE_BASE.mkdir(parents=True, exist_ok=True)
        self._tmp = tempfile.TemporaryDirectory(dir=str(_FIXTURE_BASE))
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.transcript_path = Path(self._tmp.name) / "transcript.jsonl"
        self.session_id = f"test-{uuid.uuid4().hex[:12]}"


class ZeroMountedVsZeroInvokedTest(_GuardTestBase):
    """check: run both shapes and show the artifacts differ -- name the
    artifact that carries the distinction."""

    def test_mounted_but_unused_produces_distinct_marker_zero_mounted_does_not(self):
        _write_transcript(self.transcript_path, [])
        mounted_unused = _run_guard(self.repo, self.transcript_path,
                                    "architecture-interface-contract-shape",
                                    self.session_id)
        zero_mounted = _run_guard(self.repo, self.transcript_path, "",
                                  f"{self.session_id}-b")
        self.assertEqual(mounted_unused.returncode, 0, mounted_unused.stderr)
        self.assertEqual(zero_mounted.returncode, 0, zero_mounted.stderr)
        mounted_ctx = _additional_context(mounted_unused)
        zero_ctx = _additional_context(zero_mounted)
        self.assertIn("skill-verdict-guard: zero-invocation", mounted_ctx)
        self.assertNotIn("skill-verdict-guard: zero-invocation", zero_ctx)
        self.assertNotEqual(mounted_ctx, zero_ctx)


class SignalLandsInAdditionalContextTest(_GuardTestBase):
    """check: produce the case and show where the signal lands -- the
    Stop hook's hookSpecificOutput.additionalContext, the channel the
    session transcript / `spawn.py watch` already surface."""

    def test_notice_names_the_mounted_skill_and_stays_advisory(self):
        _write_transcript(self.transcript_path, [])
        r = _run_guard(self.repo, self.transcript_path,
                       "silent-failure-audit", self.session_id)
        self.assertEqual(r.returncode, 0, r.stderr)
        parsed = json.loads(r.stdout)
        self.assertEqual(parsed["hookSpecificOutput"]["hookEventName"], "Stop")
        self.assertNotIn("decision", parsed)  # never a block
        ctx = parsed["hookSpecificOutput"]["additionalContext"]
        self.assertIn("silent-failure-audit", ctx)
        self.assertIn("Advisory only", ctx)
        self.assertIn("no skill-verdict line is owed", ctx)


class ConsumerSessionReplayTest(_GuardTestBase):
    """check: replay that session's shape (one mounted skill, zero
    invocations) and show the signal fires."""

    def test_replays_the_issues_own_consumer_session_shape(self):
        _write_transcript(self.transcript_path, [])
        r = _run_guard(self.repo, self.transcript_path,
                       "architecture-interface-contract-shape,work-in-english",
                       self.session_id)
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = _additional_context(r)
        self.assertIn("skill-verdict-guard: zero-invocation", ctx)
        self.assertIn("architecture-interface-contract-shape", ctx)
        self.assertIn("work-in-english", ctx)


class InvokedSuppressesNoticeTest(_GuardTestBase):
    """No behavior change to #2153's existing path: invoking at least one
    mounted skill must not trigger the new zero-invocation notice."""

    def test_invoking_one_mounted_skill_suppresses_the_notice(self):
        _write_transcript(self.transcript_path, ["silent-failure-audit"])
        r = _run_guard(self.repo, self.transcript_path,
                       "silent-failure-audit,architecture-interface-contract-shape",
                       self.session_id)
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = _additional_context(r)
        self.assertNotIn("zero-invocation", ctx)


if __name__ == "__main__":
    unittest.main()
