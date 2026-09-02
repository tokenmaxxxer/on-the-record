"""Issue #3182 round 2: `docs/handbooks/install-sufficiency.md` and
`scripts/preflight/consumer_preconditions.py` make overlapping claims
about the same nine preconditions in two different formats -- machine
`name` fields in one, human prose in the other. Nothing forces them to
stay in sync; a precondition added to the script with no matching doc
update would silently understate the gap the handbook exists to
describe honestly.

Test derivation (test-derivation skill): this is a decision-table /
consistency check between two artifacts, not a partition over a single
input, so the cases are:

  - existence: the doc file must exist at all.
  - content: the doc must carry the literal phrase "cannot be removed"
    -- the honesty claim the whole handbook is written around (`grep`
    fails silently if that section's wording drifts).
  - cross-reference: every precondition `name` the live preflight run
    emits must be traceable into the doc. Preflight names are
    machine-cased snake_case (`posix_fork_support`); the doc is prose
    ("POSIX fork support"). An exact-string match would be a false
    negative on every entry, so the check is word-level: every
    underscore-separated word of length > 2 in the name (dropping
    filler words like "on"/"of") must appear as a case-insensitive
    substring of the doc. Substring rather than whole-word matching is
    deliberate: an abbreviated name word like "dir" is legitimately
    covered by the doc's "directory", and that is a naming choice, not
    drift. A whole new precondition added to the script with zero
    matching prose in the doc would still fail this -- none of its
    words would appear anywhere, abbreviated or not -- while a
    precondition whose doc mention is merely reworded still passes,
    which is the point: this catches drift, not phrasing choices.

  python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "preflight" / "consumer_preconditions.py"
DOC = ROOT / "docs" / "handbooks" / "install-sufficiency.md"

def _preflight_names() -> list[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )
    data = json.loads(result.stdout)
    return [entry["name"] for entry in data["preconditions"]]


class InstallSufficiencyDocTest(unittest.TestCase):
    def test_doc_exists(self):
        self.assertTrue(DOC.is_file(), f"missing {DOC}")

    def test_doc_states_cannot_be_removed(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("cannot be removed", text)

    def test_every_precondition_name_is_traceable_into_the_doc(self):
        text_lower = DOC.read_text(encoding="utf-8").lower()
        names = _preflight_names()
        self.assertGreaterEqual(len(names), 5)
        for name in names:
            words = [w for w in name.lower().split("_") if len(w) > 2]
            self.assertTrue(words, f"precondition name {name!r} has no significant words")
            missing = [w for w in words if w not in text_lower]
            self.assertFalse(
                missing,
                f"precondition {name!r}: word(s) {missing} from its name do not "
                f"appear anywhere in {DOC.relative_to(ROOT)} -- doc and preflight "
                "have drifted apart",
            )


if __name__ == "__main__":
    unittest.main()
