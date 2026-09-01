"""issue #2962: the visible fail-open notice path uses shell builtins only
-- it does not invoke python3 and does not require a writable disk. A
reporter that depends on the thing that just failed reports nothing.

    python3 -m pytest on-the-record/hooks/ -k notice_no_external_dependency -q
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

INVARIANT_INJECTING_WRAPPED = sorted(
    r["script"]
    for r in json.loads((HOOKS_DIR / "hook_classification.json").read_text())["registrations"]
    if r["wrapped"] and r["class"] == "invariant-injecting"
)
NOTICE_MARKER = "[fail-open][DEGRADED]"


def _make_fixture_hook(tmpdir: str, name: str) -> str:
    path = Path(tmpdir) / name
    path.write_text("#!/bin/sh\nexit 1\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


class NoticeNoExternalDependencyTest(unittest.TestCase):
    def test_source_prints_notice_before_any_python3_invocation(self):
        """Static ordering check: the printf that emits the notice must be
        lexically positioned before the first `python3` invocation in the
        fail-open path, so a missing/broken python3 can never prevent it."""
        src = WRAPPER.read_text()
        notice_pos = src.index(NOTICE_MARKER)
        first_python3_call_pos = src.index("command -v python3")
        self.assertLess(
            notice_pos, first_python3_call_pos,
            "the notice must be emitted before fail-open-wrapper.sh's "
            "first actual python3 invocation, not after",
        )

    def test_notice_fires_with_no_python3_on_path(self):
        with tempfile.TemporaryDirectory() as td:
            name = INVARIANT_INJECTING_WRAPPED[0]
            hook = _make_fixture_hook(td, name)
            # PATH with no python3 anywhere on it: a directory containing
            # only /bin/sh-reachable coreutils, nothing named python3.
            bin_only = Path(td) / "bin-only"
            bin_only.mkdir()
            for tool in ("bash", "sh", "printf", "grep", "mktemp", "cat",
                         "basename", "dirname", "rm", "test", "["):
                for real_dir in ("/bin", "/usr/bin"):
                    src_path = Path(real_dir) / tool
                    if src_path.exists():
                        (bin_only / tool).symlink_to(src_path)
                        break
            res = subprocess.run(
                [str(WRAPPER), hook],
                input="", capture_output=True, text=True, timeout=10,
                env={"PATH": str(bin_only)},
            )
        self.assertEqual(res.returncode, 1, res)
        self.assertIn(NOTICE_MARKER, res.stdout, res.stdout)

    def test_notice_fires_when_tmpdir_is_unwritable(self):
        """The wrapper's own bookkeeping (mktemp for stdin/stderr capture)
        degrades gracefully when TMPDIR is unwritable (its documented
        pass-through branch); the notice must still fire off the exit code
        alone in that case."""
        with tempfile.TemporaryDirectory() as td:
            name = INVARIANT_INJECTING_WRAPPED[0]
            hook = _make_fixture_hook(td, name)
            unwritable = Path(td) / "no-write"
            unwritable.mkdir(mode=0o000)
            try:
                res = subprocess.run(
                    [str(WRAPPER), hook],
                    input="", capture_output=True, text=True, timeout=10,
                    env={"PATH": "/usr/bin:/bin", "TMPDIR": str(unwritable)},
                )
            finally:
                unwritable.chmod(0o755)
        self.assertEqual(res.returncode, 1, res)
        self.assertIn(NOTICE_MARKER, res.stdout, res.stdout)


if __name__ == "__main__":
    unittest.main()
