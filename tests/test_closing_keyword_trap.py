"""A closing keyword closes the issue even when the sentence denies it.

GitHub acts on `close/closes/closed/fix/fixes/fixed/resolve/resolves/
resolved #<n>` anywhere in a merged PR body or squash commit message. It
does not parse the surrounding sentence. Backticks do not neutralise it and
neither does negation.

Issue #3266 auto-closed twice in one session on exactly this, both times
from text written to prevent it:

- PR #3272 was a verification record whose finding was that PR #3269 carried
  a stale closing trailer. Quoting the phrase closed the issue.
- PR #3279's body said "This does not close #3266." That closed #3266.

The convention this pins: a PR that advances an issue without finishing it
writes `Advances #<n>` or `Part of #<n>` and says nothing else about
closing. The rule has to reach every session that installs the plugin, so it
lives in the injected directive, not in habit.

  python3 -m pytest tests/test_closing_keyword_trap.py -q
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# GitHub's own keyword set, as documented for linked issues.
CLOSING_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#\d+", re.IGNORECASE)


class TheKeywordIsRecognisedRegardlessOfContextTest(unittest.TestCase):
    """Pins the trap itself: these all fire, which is why the convention
    cannot rely on wording around the token."""

    def test_a_plain_trailer_fires(self):
        self.assertTrue(CLOSING_RE.search("Closes #3266"))

    def test_a_negated_sentence_still_fires(self):
        """The exact text that closed #3266 the second time."""
        self.assertTrue(CLOSING_RE.search("This does not close #3266."))

    def test_backticks_do_not_neutralise_it(self):
        """The shape that closed #3266 the first time -- a record quoting
        the keyword in order to report it as a defect."""
        self.assertTrue(CLOSING_RE.search(
            "Found a stale `Closes #3266` trailer on PR #3269"))

    def test_advances_does_not_fire(self):
        self.assertIsNone(CLOSING_RE.search("Advances #3266"))

    def test_part_of_does_not_fire(self):
        self.assertIsNone(CLOSING_RE.search("Part of #3266"))

    def test_a_broken_token_does_not_fire(self):
        """The sanctioned way to name the keyword when reporting it."""
        self.assertIsNone(CLOSING_RE.search("a stale close-s #3266 trailer"))


class TheRuleReachesEverySessionTest(unittest.TestCase):
    def test_the_directive_names_the_trap(self):
        src = (ROOT / "on-the-record" / "hooks" / "directive.sh").read_text(
            encoding="utf-8")
        self.assertIn("closing-keyword", src)
        self.assertIn("Advances #<n>", src)

    def test_the_section_exists_and_gives_the_alternative(self):
        doc = (ROOT / "on-the-record" / "directive"
               / "record-claim-shape.md").read_text(encoding="utf-8")
        self.assertIn("Never write a closing keyword", doc)
        self.assertIn("Advances #<n>", doc)
        self.assertIn("squash commit", doc)

    def test_the_section_records_both_real_incidents(self):
        """A rule with no incident behind it gets edited away later."""
        doc = (ROOT / "on-the-record" / "directive"
               / "record-claim-shape.md").read_text(encoding="utf-8")
        self.assertIn("#3272", doc)
        self.assertIn("#3279", doc)


if __name__ == "__main__":
    unittest.main()
