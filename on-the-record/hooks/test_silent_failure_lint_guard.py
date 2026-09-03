"""Live-fire test for silent-failure-lint-guard.sh (issue #3228 round 2),
matching live-fire-test-guard.sh's own required shape for a newly-staged
on-the-record/hooks/*.sh module: pipes a crafted PreToolUse payload via
subprocess.run(..., input=...) into the real shipped script and asserts
>= 2 distinct exit-code outcomes (allow=0, deny=2).

Run: python3 -m pytest on-the-record/hooks/test_silent_failure_lint_guard.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = REPO_ROOT / "on-the-record" / "hooks" / "silent-failure-lint-guard.sh"


def _run(payload: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=json.dumps(payload), capture_output=True, text=True,
        timeout=30, env=env,
    )


class SilentFailureLintGuardTest(unittest.TestCase):
    def test_new_call_with_no_timeout_is_denied(self):
        r = _run({
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.py",
                "content": "import subprocess\nsubprocess.run(['ls'])\n",
            },
        })
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("SF001", r.stderr)
        self.assertIn("timeout", r.stderr)

    def test_call_with_timeout_is_allowed(self):
        r = _run({
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.py",
                "content": "import subprocess\nsubprocess.run(['ls'], timeout=5)\n",
            },
        })
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(r.stderr, "")

    def test_allow_marker_escape_hatch_is_allowed(self):
        r = _run({
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.py",
                "content": (
                    "import subprocess\n"
                    "subprocess.run(['ls'])  # silent-failure: allow fire-and-forget\n"
                ),
            },
        })
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_non_python_file_is_allowed(self):
        r = _run({
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.sh",
                "content": "subprocess.run(['ls'])\n",
            },
        })
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unrelated_bare_name_run_is_not_mistaken_for_subprocess(self):
        # No `subprocess.` prefix -- a fragment alone carries no import
        # context, so only the unambiguous dotted-attribute call shape is
        # matched (see the guard's own header comment).
        r = _run({
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.py",
                "content": "def run(x):\n    return x\nrun(1)\n",
            },
        })
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_edit_fragment_without_enclosing_def_is_still_checked(self):
        # A realistic Edit new_string: an indented statement with no
        # enclosing `def` in the fragment itself (its real function lives
        # outside the edited region) -- the dedent/synthetic-wrap fallback
        # must still parse and flag this.
        r = _run({
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.py",
                "old_string": "    pass",
                "new_string": "    result = subprocess.run([cmd])\n    return result",
            },
        })
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_multiedit_with_one_bad_edit_among_several_is_denied(self):
        r = _run({
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": "/tmp/otr-sflg-test/a.py",
                "edits": [
                    {"old_string": "x", "new_string": "y = 1"},
                    {"old_string": "z", "new_string": "subprocess.run([cmd])"},
                ],
            },
        })
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_non_write_tool_is_ignored(self):
        r = _run({
            "tool_name": "Bash",
            "tool_input": {"command": "subprocess.run(['ls'])"},
        })
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_orchestrate_off_kill_switch_allows_everything(self):
        env = dict(os.environ)
        env["ORCHESTRATE_OFF"] = "1"
        r = subprocess.run(
            ["bash", str(HOOK_PATH)],
            input=json.dumps({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": "/tmp/otr-sflg-test/a.py",
                    "content": "import subprocess\nsubprocess.run(['ls'])\n",
                },
            }),
            capture_output=True, text=True, timeout=30, env=env,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_malformed_payload_fails_open(self):
        env = dict(os.environ)
        env.pop("ORCHESTRATE_OFF", None)
        proc = subprocess.run(
            ["bash", str(HOOK_PATH)], input="not json{{{", capture_output=True,
            text=True, timeout=30, env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
