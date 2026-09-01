"""issue #2962: when an invariant-injecting hook fails open, the session
gets an in-band notice that it is running degraded; an observability hook
keeps today's silent fail-open (this slice adds a class distinction, it
does not tighten the default); a hook that does not fail open never prints
a notice.

    python3 -m pytest on-the-record/hooks/ -k visible_fail_open -q
"""
from __future__ import annotations

import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
WRAPPER = HOOKS_DIR / "fail-open-wrapper.sh"

INVARIANT_INJECTING_WRAPPED = {
    r["script"]
    for r in json.loads((HOOKS_DIR / "hook_classification.json").read_text())["registrations"]
    if r["wrapped"] and r["class"] == "invariant-injecting"
}
OBSERVABILITY_WRAPPED = {
    r["script"]
    for r in json.loads((HOOKS_DIR / "hook_classification.json").read_text())["registrations"]
    if r["wrapped"] and r["class"] == "observability"
}

NOTICE_MARKER = "[fail-open][DEGRADED]"


def _make_fixture_hook(tmpdir: str, name: str, body: str) -> str:
    path = Path(tmpdir) / name
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


def _run_wrapper(hook_path: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(WRAPPER), hook_path],
        input="", capture_output=True, text=True, timeout=10, env=env,
    )


class VisibleFailOpenTest(unittest.TestCase):
    def test_invariant_injecting_hook_crash_prints_degraded_notice(self):
        with tempfile.TemporaryDirectory() as td:
            # one representative invariant-injecting name is enough to prove
            # the mechanism; classification coverage itself is
            # test_hook_classification.py's job.
            name = sorted(INVARIANT_INJECTING_WRAPPED)[0]
            hook = _make_fixture_hook(td, name, "exit 1")
            res = _run_wrapper(hook)
        self.assertEqual(res.returncode, 1, res)
        self.assertIn(NOTICE_MARKER, res.stdout, res.stdout)
        self.assertIn(name, res.stdout)

    def test_every_invariant_injecting_hook_triggers_the_notice(self):
        for name in sorted(INVARIANT_INJECTING_WRAPPED):
            with self.subTest(hook=name), tempfile.TemporaryDirectory() as td:
                hook = _make_fixture_hook(td, name, "exit 1")
                res = _run_wrapper(hook)
                self.assertIn(NOTICE_MARKER, res.stdout, (name, res.stdout))

    def test_observability_hook_crash_stays_silent_no_notice(self):
        # must not: do not suppress or reduce the existing fail-open
        # behaviour for observability hooks -- this only proves the notice
        # itself is absent, not that the crash goes unrecorded elsewhere.
        for name in sorted(OBSERVABILITY_WRAPPED):
            with self.subTest(hook=name), tempfile.TemporaryDirectory() as td:
                hook = _make_fixture_hook(td, name, "exit 1")
                res = _run_wrapper(hook)
                self.assertNotIn(NOTICE_MARKER, res.stdout, (name, res.stdout))
                self.assertEqual(res.returncode, 1, res)

    def test_success_produces_no_notice_for_an_invariant_injecting_hook(self):
        # empty state (acceptance): no failure means no notice; passes.
        with tempfile.TemporaryDirectory() as td:
            name = sorted(INVARIANT_INJECTING_WRAPPED)[0]
            hook = _make_fixture_hook(td, name, "exit 0")
            res = _run_wrapper(hook)
        self.assertEqual(res.returncode, 0, res)
        self.assertNotIn(NOTICE_MARKER, res.stdout, res.stdout)

    def test_deny_exit_2_produces_no_notice(self):
        # exit 2 is a normal deny outcome, not a fail-open, for either class.
        with tempfile.TemporaryDirectory() as td:
            name = sorted(INVARIANT_INJECTING_WRAPPED)[0]
            hook = _make_fixture_hook(td, name, "exit 2")
            res = _run_wrapper(hook)
        self.assertEqual(res.returncode, 2, res)
        self.assertNotIn(NOTICE_MARKER, res.stdout, res.stdout)

    def test_wrapper_still_forwards_original_exit_code_verdict_neutral(self):
        # the notice is additive -- it must never change what the wrapper
        # forwards to the platform.
        with tempfile.TemporaryDirectory() as td:
            name = sorted(INVARIANT_INJECTING_WRAPPED)[0]
            hook = _make_fixture_hook(td, name, "exit 17")
            res = _run_wrapper(hook)
        self.assertEqual(res.returncode, 17, res)
        self.assertIn(NOTICE_MARKER, res.stdout)


if __name__ == "__main__":
    unittest.main()
