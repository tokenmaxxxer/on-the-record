"""Issue #3134, acceptance check 1: `amends.resolve_amendments()`, the
section-scoped correction primitive `supersedes:` (issue #3050) has no
shape for -- see `amends.py`'s module docstring for why the target
staying authoritative makes this harder than whole-artifact supersession.

Test derivation (test-derivation skill): the requirement under test is a
data-shape/structural resolver, same problem shape as
`tests/test_supersession_shape.py`'s own derivation, so it routes to
equivalence partitioning over the relationship an `amends:` edge can have
to the rest of its tree, one level more granular than `supersedes:`'s
partitions (target *and* section, not just target):

  - no record amends anything (degenerate/base case)
  - exactly one record amends exactly one section of one target (the
    sanctioned shape)
  - two records each amend a *different* section of the *same* target
    (independent -- both land in `amended`, no conflict)
  - an `amends:` target absent from the tree (dangling reference)
  - an `amends:` target present but the named section anchor is not
    among its own headings (renamed/never-real section)
  - two records both claim to amend the same section of the same target
    (conflict -- content alone cannot say which is real)
  - a cycle: A amends a section of B, B amends a section of A
  - a path-variant target (leading `./`), mirroring
    `supersession.py`'s own normalization contract

This risk classification is High (test-derivation skill, Step 3a): a bug
here reproduces the exact defect the issue exists to close (a reader
silently trusting a wrong section), so every partition gets an explicit
case rather than a summary count.

  python3 -m pytest tests/test_amends_resolution.py -q
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import amends  # noqa: E402


def _record(heading: str, extra_frontmatter: str = "") -> str:
    return (
        f"---\nissue: 1\nrole: coding\n{extra_frontmatter}---\n\n"
        f"## {heading}\n\nbody text\n"
    )


class SectionAnchorTest(unittest.TestCase):
    def test_lowercases_and_hyphenates(self):
        self.assertEqual(amends.section_anchor("Limitation"), "limitation")
        self.assertEqual(amends.section_anchor("Open Findings"), "open-findings")

    def test_strips_punctuation(self):
        self.assertEqual(amends.section_anchor("What did not work?"),
                          "what-did-not-work")


class ParseAmendsTest(unittest.TestCase):
    def test_no_frontmatter_returns_none(self):
        self.assertIsNone(amends.parse_amends("# just a body\n"))

    def test_frontmatter_without_field_returns_none(self):
        self.assertIsNone(amends.parse_amends(_record("X")))

    def test_frontmatter_with_field_returns_target_and_anchor(self):
        marker = amends.render_amends_field("docs/issue-1/reports/x.md",
                                              "Limitation", "reason")
        content = _record("Y", f"{marker}\n")
        self.assertEqual(amends.parse_amends(content),
                          ("docs/issue-1/reports/x.md", "limitation"))

    def test_trailing_comment_not_included_in_anchor(self):
        content = _record("Y", "amends: docs/issue-1/reports/x.md#limitation  # why\n")
        self.assertEqual(amends.parse_amends(content),
                          ("docs/issue-1/reports/x.md", "limitation"))

    def test_field_without_section_returns_none(self):
        # `amends:` with no `#<section>` is not a smaller amends -- it is
        # supersedes:'s shape; silently accepting it here would hide a
        # whole-record correction from supersession.py's own resolver.
        content = _record("Y", "amends: docs/issue-1/reports/x.md\n")
        self.assertIsNone(amends.parse_amends(content))

    def test_unterminated_frontmatter_returns_none(self):
        self.assertIsNone(amends.parse_amends("---\namends: x#y\nbody\n"))


class ExtractSectionAnchorsTest(unittest.TestCase):
    def test_headings_from_body_only(self):
        content = _record("Limitation")
        self.assertIn("limitation", amends.extract_section_anchors(content))

    def test_frontmatter_lines_not_treated_as_headings(self):
        content = _record("Limitation", "amends: x#y\n")
        self.assertNotIn("y", amends.extract_section_anchors(content))


class ResolveAmendmentsTest(unittest.TestCase):
    def test_no_amendments_all_clean(self):
        records = {"a.md": _record("Limitation"), "b.md": _record("Scope")}
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {})
        self.assertEqual(verdict["broken"], [])
        self.assertEqual(verdict["missing_section"], [])
        self.assertEqual(verdict["conflicts"], {})
        self.assertEqual(verdict["cycles"], [])

    def test_single_amendment_recorded(self):
        marker = amends.render_amends_field("a.md", "Limitation", "wrong axis")
        records = {"a.md": _record("Limitation"), "b.md": _record("Correction", f"{marker}\n")}
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {"a.md": {"limitation": "b.md"}})
        self.assertEqual(verdict["conflicts"], {})
        self.assertEqual(verdict["broken"], [])
        self.assertEqual(verdict["missing_section"], [])

    def test_two_different_sections_of_same_target_both_land(self):
        marker_b = amends.render_amends_field("a.md", "Limitation", "r1")
        marker_c = amends.render_amends_field("a.md", "Scope", "r2")
        records = {
            "a.md": _record("Limitation") + "\n## Scope\n\nbody\n",
            "b.md": _record("X", f"{marker_b}\n"),
            "c.md": _record("Y", f"{marker_c}\n"),
        }
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"],
                          {"a.md": {"limitation": "b.md", "scope": "c.md"}})
        self.assertEqual(verdict["conflicts"], {})

    def test_dangling_target_reported_broken(self):
        marker = amends.render_amends_field("missing.md", "Limitation", "reason")
        records = {"b.md": _record("X", f"{marker}\n")}
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {})
        self.assertEqual(verdict["broken"], ["missing.md"])
        self.assertEqual(verdict["missing_section"], [])

    def test_missing_section_anchor_reported_not_amended(self):
        marker = amends.render_amends_field("a.md", "NoSuchSection", "reason")
        records = {"a.md": _record("Limitation"), "b.md": _record("X", f"{marker}\n")}
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {})
        self.assertEqual(verdict["missing_section"], ["a.md#nosuchsection"])
        self.assertEqual(verdict["broken"], [])

    def test_conflicting_correctors_excluded_fail_closed(self):
        marker_b = amends.render_amends_field("a.md", "Limitation", "r1")
        marker_c = amends.render_amends_field("a.md", "Limitation", "r2")
        records = {
            "a.md": _record("Limitation"),
            "b.md": _record("X", f"{marker_b}\n"),
            "c.md": _record("Y", f"{marker_c}\n"),
        }
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {})
        self.assertEqual(verdict["conflicts"], {"a.md#limitation": ["b.md", "c.md"]})

    def test_cycle_excluded_from_both_ends_fail_closed(self):
        marker_a_to_b = amends.render_amends_field("b.md", "Scope", "r1")
        marker_b_to_a = amends.render_amends_field("a.md", "Limitation", "r2")
        records = {
            "a.md": _record("Limitation", f"{marker_a_to_b}\n"),
            "b.md": _record("Scope", f"{marker_b_to_a}\n"),
        }
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {})
        self.assertEqual(verdict["conflicts"], {})
        self.assertEqual(verdict["cycles"],
                          ["a.md->b.md#scope", "b.md->a.md#limitation"])

    def test_leading_dot_slash_variant_still_resolves_the_target(self):
        marker = amends.render_amends_field("./a.md", "Limitation", "reason")
        records = {"a.md": _record("Limitation"), "b.md": _record("X", f"{marker}\n")}
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {"a.md": {"limitation": "b.md"}})
        self.assertEqual(verdict["broken"], [])

    def test_reader_only_needs_content_no_filesystem_or_git(self):
        marker = amends.render_amends_field("x", "Section", "y")
        records = {"x": _record("Section"), "z": _record("Z", f"{marker}\n")}
        verdict = amends.resolve_amendments(records)
        self.assertEqual(verdict["amended"], {"x": {"section": "z"}})


if __name__ == "__main__":
    unittest.main()
