"""issue #2593: a consumer orchestrator read the board, saw bare
`[implementation]`/`[coding]` lines, and typed `--skills implementation`
-- the only vocabulary the board actually showed it. `board.status()`'s
bracket used to print just the record's filename stem with nothing
marking it as a historical record rather than a spawnable `--skills`
name. This reproduces the exact reported shape (an `implementation`-named
record under an issue) against the real `board.status()` entry point and
checks the fix: every bracket line now reads `[record: <name>]`, so the
same reader cannot mistake it for a `--skills` value without a caveat
living somewhere else on the page."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import board  # noqa: E402
import spawn  # noqa: E402

board._sp = spawn


class BoardBracketNamesTheRecordTest(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tmpdir.name)
        self.addCleanup(self._tmpdir.cleanup)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        spawn.write_record_skeleton(str(self.root), 1005, "implementation")
        spawn.write_record_skeleton(str(self.root), 103, "coding")

    def test_legacy_named_records_render_with_a_record_marker(self):
        out = board.status(str(self.root))
        text = "\n".join(out)
        self.assertIn("[record: implementation]", text)
        self.assertIn("[record: coding]", text)
        # the exact ambiguous shape the bug report quoted must not survive
        # bare (no bracket line is just "[implementation]"/"[coding]" with
        # no marker).
        self.assertNotIn("  [implementation] ", text)
        self.assertNotIn("  [coding] ", text)


if __name__ == "__main__":
    unittest.main()
