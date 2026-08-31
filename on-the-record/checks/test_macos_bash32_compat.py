#!/usr/bin/env python3
"""issue #2924: the standing macOS/bash-3.2 compat check runs as part of
the normal `pytest` invocation, and stays quiet on a clean pass -- see
macos_bash32_compat.py for the check itself and the rules it enforces.

`test_would_have_caught_issue_2919_regressions` is the literal
fail-then-pass proof the issue's acceptance criteria demand: the check
run against the pre-#2919 poll-heartbeat.sh (git history,
29d00cb553aec34cd7c87e950cd4b4153ead24de, the parent of #2919's fix
commit a826a010) reports both of #2919's shipped failures; the same
check run against the current file at HEAD reports zero.

  python3 on-the-record/checks/test_macos_bash32_compat.py
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import macos_bash32_compat as check

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRE_2919_SHA = "29d00cb553aec34cd7c87e950cd4b4153ead24de"
POLL_HEARTBEAT_REL = "on-the-record/monitors/poll-heartbeat.sh"


def _git_show(sha: str, path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout


class MacosBash32CompatTest(unittest.TestCase):
    def test_current_head_is_clean(self):
        ok, report = check.run(verbose=True)
        self.assertTrue(ok, report)

    def test_would_have_caught_issue_2919_regressions(self):
        pre_content = _git_show(PRE_2919_SHA, POLL_HEARTBEAT_REL)
        pre_violations = check.check_sh_file(POLL_HEARTBEAT_REL, pre_content)
        self.assertTrue(
            any("flock" in v for v in pre_violations),
            f"did not flag pre-#2919 unguarded flock; got: {pre_violations}",
        )
        self.assertTrue(
            any("[@]" in v for v in pre_violations),
            f"did not flag pre-#2919 unsafe array expansion; got: {pre_violations}",
        )

        head_content = (REPO_ROOT / POLL_HEARTBEAT_REL).read_text()
        head_violations = check.check_sh_file(POLL_HEARTBEAT_REL, head_content)
        self.assertEqual(head_violations, [], head_violations)

    def test_decision_queue_stopgate_stat_c_fallback_is_recognized_safe(self):
        rel = "on-the-record/hooks/decision-queue-stopgate.sh"
        content = (REPO_ROOT / rel).read_text()
        violations = check.check_sh_file(rel, content)
        self.assertEqual(
            [v for v in violations if "stat -c" in v], [],
            "decision-queue-stopgate.sh's stat -c || stat -f fallback "
            "should not be flagged",
        )

    def test_new_proc_site_outside_reviewed_set_is_flagged(self):
        violations = check.check_py_file(
            "some_new_module.py",
            'cmdline = Path(f"/proc/{pid}/cmdline").read_text()\n',
        )
        self.assertEqual(len(violations), 1)


if __name__ == "__main__":
    unittest.main()
