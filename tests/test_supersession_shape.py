"""Issue #3050, acceptance checks 1-2: the sanctioned shape a correction
round uses when it cannot write into the record it is correcting.

Test derivation (test-derivation skill): the requirement under test is
`supersession.resolve_authoritative()` -- "a reader with only the merged
tree, no PR body, no issue comments, can identify the authoritative
artifact from file contents alone." This is a data-shape/structural
requirement (a small state space over how records reference each other),
so it routes to equivalence partitioning over the relationship a record
can have to the others in its tree, rather than EP/BVA over a scalar
input:

  - no record supersedes anything (degenerate/base case)
  - exactly one record supersedes exactly one other (the demonstrated
    correction shape, gates/probe_supersession_marker.py's case)
  - a chain of supersessions (B supersedes A, C supersedes B)
  - a `supersedes:` target absent from the tree (dangling reference)
  - two records both claim to supersede the same target (conflict --
    the shape issue #3050's own second report warns is the cost of
    getting this wrong: an independent second correction producing a
    third copy)

Each partition is exercised by >=1 case below; `parse_supersedes()` is
covered separately for the field-extraction contract
(`render_supersedes_field()` round-trip, absent frontmatter, frontmatter
without the field, trailing comment stripped).

  python3 -m pytest tests/test_supersession_shape.py -q
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import supersession  # noqa: E402


def _record(content_extra: str = "") -> str:
    return f"---\nissue: 1\nrole: coding\n{content_extra}---\n\nbody\n"


class ParseSupersedesTest(unittest.TestCase):
    def test_no_frontmatter_returns_none(self):
        self.assertIsNone(supersession.parse_supersedes("# just a body\n"))

    def test_frontmatter_without_field_returns_none(self):
        self.assertIsNone(supersession.parse_supersedes(_record()))

    def test_frontmatter_with_field_returns_path(self):
        marker = supersession.render_supersedes_field("docs/issue-1/reports/x.md", "reason")
        content = _record(f"{marker}\n")
        self.assertEqual(supersession.parse_supersedes(content),
                          "docs/issue-1/reports/x.md")

    def test_trailing_comment_not_included_in_path(self):
        content = _record("supersedes: docs/issue-1/reports/x.md  # why\n")
        self.assertEqual(supersession.parse_supersedes(content),
                          "docs/issue-1/reports/x.md")

    def test_unterminated_frontmatter_returns_none(self):
        self.assertIsNone(supersession.parse_supersedes("---\nsupersedes: x\nbody\n"))


class ResolveAuthoritativeTest(unittest.TestCase):
    def test_no_supersession_all_authoritative(self):
        records = {"a.md": _record(), "b.md": _record()}
        verdict = supersession.resolve_authoritative(records)
        self.assertEqual(verdict["authoritative"], ["a.md", "b.md"])
        self.assertEqual(verdict["superseded"], {})
        self.assertEqual(verdict["conflicts"], {})
        self.assertEqual(verdict["broken"], [])

    def test_single_correction_marks_original_superseded(self):
        marker = supersession.render_supersedes_field("a.md", "fabricated figures")
        records = {"a.md": _record(), "b.md": _record(f"{marker}\n")}
        verdict = supersession.resolve_authoritative(records)
        self.assertEqual(verdict["authoritative"], ["b.md"])
        self.assertEqual(verdict["superseded"], {"a.md": "b.md"})
        self.assertEqual(verdict["conflicts"], {})

    def test_chain_of_corrections_only_last_authoritative(self):
        marker_b = supersession.render_supersedes_field("a.md", "r1")
        marker_c = supersession.render_supersedes_field("b.md", "r2")
        records = {
            "a.md": _record(),
            "b.md": _record(f"{marker_b}\n"),
            "c.md": _record(f"{marker_c}\n"),
        }
        verdict = supersession.resolve_authoritative(records)
        self.assertEqual(verdict["authoritative"], ["c.md"])
        self.assertEqual(verdict["superseded"], {"a.md": "b.md", "b.md": "c.md"})

    def test_dangling_supersedes_target_reported_broken_not_authoritative_loss(self):
        marker = supersession.render_supersedes_field("missing.md", "reason")
        records = {"b.md": _record(f"{marker}\n")}
        verdict = supersession.resolve_authoritative(records)
        # b.md supersedes nothing verifiable from the tree, but b.md
        # itself is not superseded by anything -- it stays authoritative.
        self.assertEqual(verdict["authoritative"], ["b.md"])
        self.assertEqual(verdict["broken"], ["missing.md"])

    def test_conflicting_correctors_excluded_fail_closed(self):
        marker_b = supersession.render_supersedes_field("a.md", "r1")
        marker_c = supersession.render_supersedes_field("a.md", "r2")
        records = {
            "a.md": _record(),
            "b.md": _record(f"{marker_b}\n"),
            "c.md": _record(f"{marker_c}\n"),
        }
        verdict = supersession.resolve_authoritative(records)
        # Two independent corrections of the same original: content alone
        # cannot say which is real, so none of the three is authoritative.
        self.assertEqual(verdict["authoritative"], [])
        self.assertEqual(verdict["conflicts"], {"a.md": ["b.md", "c.md"]})
        self.assertEqual(verdict["superseded"], {})

    def test_leading_dot_slash_variant_still_resolves_the_target(self):
        # Warrant hunt, issue #3050 PR #3086: a `supersedes:` value citing
        # the same file with a harmless path variant (leading `./`) must
        # not leave the stale original in `authoritative` -- that is
        # exactly the failure this module exists to prevent.
        marker = supersession.render_supersedes_field("./a.md", "reason")
        records = {"a.md": _record(), "b.md": _record(f"{marker}\n")}
        verdict = supersession.resolve_authoritative(records)
        self.assertEqual(verdict["authoritative"], ["b.md"])
        self.assertEqual(verdict["superseded"], {"a.md": "b.md"})
        self.assertEqual(verdict["broken"], [])

    def test_reader_only_needs_content_no_filesystem_or_git(self):
        # The reader-with-only-the-merged-tree contract: content strings
        # keyed by path are the entire input -- no filesystem/git access
        # inside resolve_authoritative() itself.
        marker = supersession.render_supersedes_field("x", "y")
        records = {"x": _record(), "z": _record(f"{marker}\n")}
        verdict = supersession.resolve_authoritative(records)
        self.assertEqual(verdict["authoritative"], ["z"])


if __name__ == "__main__":
    unittest.main()
