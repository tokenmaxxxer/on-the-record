"""Issue #3044: `skill_verdict_reason_check` gains a converse check --
detecting a `skill-verdict: <name> — applied: invoked; ...` line whose
`name` is absent from the caller-supplied `mounted`/invoked-name list.
Since the hook's only real caller (`skill-verdict-guard.sh`) passes the
transcript-derived invoked set as `mounted`, "name absent from mounted"
there literally means "the transcript disproves this invocation claim".

Equivalence partitions covered in Part 1, cutting the input space by
(line type: `applied: invoked;` vs `not-applicable:`) x (name
membership: in the invoked list vs not):

  - applied:invoked, name IN invoked list      -> test_invoked_match_passes_unaffected
  - applied:invoked, name NOT in invoked list  -> test_invoked_mismatch_is_rejected
  - not-applicable, name NOT in invoked list   -> test_not_applicable_line_for_uninvoked_skill_is_not_a_mismatch
  (not-applicable, name IN invoked list is not a #3044 concern -- no
  invocation claim is made, nothing to disprove; #2039/#2062's existing
  checks already cover that shape and are exercised by the two
  regression tests below.)

Plus regression tests for the pre-existing #2039/#2062 shape checks
(must-not-weaken) and the #2062 empty-mounted no-op.

Part 2 runs the real shipped `on-the-record/hooks/skill-verdict-guard.sh`
Stop hook via a real Stop-event JSON payload against a fabricated
transcript file, proving the hook actually blocks on `invoked-mismatch`
and stays advisory-only for everything else -- same harness shape as
test/test_skill_verdict_guard_zero_invocation_signal.py.

Run standalone:
  python3 -m pytest on-the-record/hooks/test_skill_verdict_reason_check.py -q
Run selected by name (acceptance check):
  python3 -m pytest on-the-record/hooks/ -q -k invoked
Run the full suite (regression, must stay green):
  python3 -m pytest on-the-record/hooks/ -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "gates"))
import record_lint  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "skill-verdict-guard.sh"
_FIXTURE_BASE = Path.home() / ".otr-svg-test-fixture"


# --------------------------------------------------------------------
# Part 1 -- pure unit tests of skill_verdict_reason_check
# --------------------------------------------------------------------

class SkillVerdictInvokedMismatchTest(unittest.TestCase):
    def test_invoked_mismatch_is_rejected(self):
        text = (
            "skill-verdict: foo — applied: invoked; did X\n"
            "skill-verdict: bar — applied: invoked; did Y\n"
        )
        violations = record_lint.skill_verdict_reason_check(text, ["foo"])
        self.assertEqual(len(violations), 1)
        self.assertTrue(violations[0].startswith("invoked-mismatch"))
        self.assertIn("bar", violations[0])
        for v in violations:
            if v.startswith("invoked-mismatch"):
                self.assertNotIn("'foo'", v)

    def test_invoked_match_passes_unaffected(self):
        text = "skill-verdict: foo — applied: invoked; did X\n"
        violations = record_lint.skill_verdict_reason_check(text, ["foo"])
        self.assertEqual(violations, [])

    def test_not_applicable_line_for_uninvoked_skill_is_not_a_mismatch(self):
        text = "skill-verdict: bar — not-applicable: no shell/SQL sink here\n"
        violations = record_lint.skill_verdict_reason_check(text, ["foo"])
        for v in violations:
            self.assertFalse(v.startswith("invoked-mismatch"))

    def test_missing_verdict_line_still_detected(self):
        text = "no skill-verdict lines here\n"
        violations = record_lint.skill_verdict_reason_check(text, ["foo"])
        self.assertEqual(len(violations), 1)
        self.assertIn("마운트된 스킬에 skill-verdict 줄이 없다", violations[0])

    def test_missing_invoked_marker_still_detected(self):
        text = "skill-verdict: foo — applied: did X\n"
        violations = record_lint.skill_verdict_reason_check(text, ["foo"])
        self.assertEqual(len(violations), 1)
        self.assertIn("invoke-before-apply", violations[0])

    def test_empty_mounted_list_is_a_noop(self):
        text = "skill-verdict: foo — applied: invoked; did X\n"
        violations = record_lint.skill_verdict_reason_check(text, [])
        self.assertEqual(violations, [])


# --------------------------------------------------------------------
# Part 2 -- hook-level subprocess tests: the Stop hook actually blocks
# --------------------------------------------------------------------

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


def _checkout_issue_branch(repo: Path, issue: int, skill: str):
    subprocess.run(["git", "checkout", "-q", "-b", f"issue-{issue}/{skill}"],
                    cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t",
                     "commit", "-q", "--allow-empty", "-m", "init"],
                    cwd=repo, check=True)


def _write_record(repo: Path, issue: int, skill: str, body: str):
    d = repo / "docs" / f"issue-{issue}" / "reports"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{skill}.md").write_text(body, encoding="utf-8")


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


class HookInvokedMismatchBlockTest(_GuardTestBase):
    def test_hook_blocks_on_invoked_mismatch_record(self):
        _checkout_issue_branch(self.repo, 999999, "implementation")
        _write_record(
            self.repo, 999999, "implementation",
            "# record\n\n"
            "skill-verdict: foo — applied: invoked; did X\n"
            "skill-verdict: bar — applied: invoked; did Y\n",
        )
        _write_transcript(self.transcript_path, ["foo"])
        r = _run_guard(self.repo, self.transcript_path, "foo,bar", self.session_id)
        self.assertEqual(r.returncode, 0, r.stderr)
        parsed = json.loads(r.stdout)
        self.assertEqual(parsed["decision"], "block")
        self.assertIn("bar", parsed["reason"])
        for fragment in parsed["reason"].split("invoked-mismatch"):
            self.assertNotIn("'foo'", fragment)

    def test_hook_stays_advisory_when_all_invoked_claims_are_truthful(self):
        _checkout_issue_branch(self.repo, 999999, "implementation")
        _write_record(
            self.repo, 999999, "implementation",
            "# record\n\n"
            "skill-verdict: foo — applied: invoked; did X\n"
            "skill-verdict: bar — not-applicable: no sink here\n",
        )
        _write_transcript(self.transcript_path, ["foo"])
        r = _run_guard(self.repo, self.transcript_path, "foo,bar", self.session_id)
        self.assertEqual(r.returncode, 0, r.stderr)
        parsed = json.loads(r.stdout) if r.stdout.strip() else {}
        self.assertNotIn("decision", parsed)

    def test_hook_reports_not_blocks_when_transcript_missing(self):
        missing_path = Path(self._tmp.name) / "does-not-exist.jsonl"
        r = _run_guard(self.repo, missing_path, "foo,bar", self.session_id)
        self.assertEqual(r.returncode, 0, r.stderr)
        if r.stdout.strip():
            parsed = json.loads(r.stdout)
            self.assertNotIn("decision", parsed)


if __name__ == "__main__":
    unittest.main()
