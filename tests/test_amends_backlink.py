"""Issue #3134 repair round: `amends_backlink.py`, the discoverability
fix for the finding the independent verification of PR #3143 graded
Absent -- the generated index alone does not make "opening the amended
record directly" surface the amendment; a backlink written into the
target's own content, by the landing step, does.

Test derivation (test-derivation skill): High risk (Step 3a) -- a bug
here reproduces the exact defect class the repair round exists to close
(a reader opening a record and missing a correction), so EP/BVA over the
backlink's own lifecycle gets an explicit case per partition:

  - marker absent from a target with no amendment at all (base case)
  - marker present after insertion, directly under the amended heading
  - re-insertion for the same corrector/reason is idempotent (no
    duplicate marker)
  - insertion against an anchor with no matching heading raises rather
    than silently no-op'ing (caller-contract violation, not a data
    condition -- see `insert_backlink`'s own docstring)
  - two different sections of the same target each get their own marker,
    under their own heading (mirrors
    `test_amends_resolution.ResolveAmendmentsTest
    .test_two_different_sections_of_same_target_both_land`)
  - `apply_backlinks()` omits a target that needs no change (already
    linked, or has no amended edges at all)
  - `missing_backlinks()` reports an edge whose target lacks the marker,
    and is empty once `apply_backlinks()`'s output is adopted
  - `missing_backlinks()` never reports a broken/missing_section/
    conflict/cycle edge -- those are not `amended`, so there is nothing
    to backlink yet (mirrors `resolve_amendments()`'s own fails-closed
    exclusion, one layer up)

  python3 -m pytest tests/test_amends_backlink.py -q
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import amends  # noqa: E402
import amends_backlink  # noqa: E402


def _record(heading: str, extra_frontmatter: str = "", body: str = "body text") -> str:
    return (
        f"---\nissue: 1\nrole: coding\n{extra_frontmatter}---\n\n"
        f"## {heading}\n\n{body}\n"
    )


class RenderMarkerTest(unittest.TestCase):
    def test_marker_names_corrector_and_reason(self):
        marker = amends_backlink.render_backlink_marker("docs/issue-2/reports/b.md", "wrong axis")
        self.assertIn("docs/issue-2/reports/b.md", marker)
        self.assertIn("wrong axis", marker)
        self.assertIn("Amended", marker)


class HasBacklinkTest(unittest.TestCase):
    def test_absent_from_unamended_target(self):
        content = _record("Limitation")
        self.assertFalse(amends_backlink.has_backlink(content, "docs/issue-2/reports/b.md", "r"))

    def test_present_after_insertion(self):
        content = _record("Limitation")
        updated = amends_backlink.insert_backlink(content, "limitation", "docs/issue-2/reports/b.md", "r")
        self.assertTrue(amends_backlink.has_backlink(updated, "docs/issue-2/reports/b.md", "r"))


class InsertBacklinkTest(unittest.TestCase):
    def test_marker_lands_directly_under_the_amended_heading(self):
        content = _record("Limitation", body="original wrong claim")
        updated = amends_backlink.insert_backlink(content, "limitation", "docs/issue-2/reports/b.md", "wrong axis")
        lines = updated.splitlines()
        heading_idx = next(i for i, ln in enumerate(lines) if ln.strip() == "## Limitation")
        marker = amends_backlink.render_backlink_marker("docs/issue-2/reports/b.md", "wrong axis")
        # the marker must appear before the section's own (pre-existing) body text
        marker_idx = lines.index(marker)
        body_idx = next(i for i, ln in enumerate(lines) if "original wrong claim" in ln)
        self.assertLess(heading_idx, marker_idx)
        self.assertLess(marker_idx, body_idx)

    def test_reinsertion_is_idempotent(self):
        content = _record("Limitation")
        once = amends_backlink.insert_backlink(content, "limitation", "docs/issue-2/reports/b.md", "r")
        twice = amends_backlink.insert_backlink(once, "limitation", "docs/issue-2/reports/b.md", "r")
        self.assertEqual(once, twice)
        marker = amends_backlink.render_backlink_marker("docs/issue-2/reports/b.md", "r")
        self.assertEqual(twice.count(marker), 1)

    def test_missing_anchor_raises(self):
        content = _record("Limitation")
        with self.assertRaises(ValueError):
            amends_backlink.insert_backlink(content, "nosuchsection", "docs/issue-2/reports/b.md", "r")

    def test_two_sections_of_same_target_each_get_their_own_marker(self):
        content = _record("Limitation") + "\n## Scope\n\nscope body\n"
        step1 = amends_backlink.insert_backlink(content, "limitation", "docs/issue-2/reports/b.md", "r1")
        step2 = amends_backlink.insert_backlink(step1, "scope", "docs/issue-3/reports/c.md", "r2")
        self.assertIn(amends_backlink.render_backlink_marker("docs/issue-2/reports/b.md", "r1"), step2)
        self.assertIn(amends_backlink.render_backlink_marker("docs/issue-3/reports/c.md", "r2"), step2)


class ApplyBacklinksTest(unittest.TestCase):
    def test_no_amendments_no_updates(self):
        records = {"a.md": _record("Limitation")}
        self.assertEqual(amends_backlink.apply_backlinks(records), {})

    def test_single_amendment_updates_only_the_target(self):
        marker = amends.render_amends_field("a.md", "Limitation", "wrong axis")
        records = {
            "a.md": _record("Limitation"),
            "b.md": _record("Correction", f"{marker}\n"),
        }
        updated = amends_backlink.apply_backlinks(records)
        self.assertEqual(set(updated), {"a.md"})
        self.assertTrue(amends_backlink.has_backlink(updated["a.md"], "b.md", "wrong axis"))

    def test_already_linked_target_is_not_returned(self):
        marker = amends.render_amends_field("a.md", "Limitation", "wrong axis")
        already_linked = amends_backlink.insert_backlink(_record("Limitation"), "limitation", "b.md", "wrong axis")
        records = {
            "a.md": already_linked,
            "b.md": _record("Correction", f"{marker}\n"),
        }
        self.assertEqual(amends_backlink.apply_backlinks(records), {})

    def test_broken_and_conflicting_edges_produce_no_backlink(self):
        # A dangling target: nothing to insert into (no resolved target).
        dangling_marker = amends.render_amends_field("missing.md", "Limitation", "r")
        records = {"b.md": _record("X", f"{dangling_marker}\n")}
        self.assertEqual(amends_backlink.apply_backlinks(records), {})

        # A conflict: two correctors claim the same section -- fails
        # closed the same way resolve_amendments() does, so nothing is
        # inserted for either.
        marker_b = amends.render_amends_field("a.md", "Limitation", "r1")
        marker_c = amends.render_amends_field("a.md", "Limitation", "r2")
        records = {
            "a.md": _record("Limitation"),
            "b.md": _record("X", f"{marker_b}\n"),
            "c.md": _record("Y", f"{marker_c}\n"),
        }
        self.assertEqual(amends_backlink.apply_backlinks(records), {})


class MissingBacklinksTest(unittest.TestCase):
    def test_reports_target_missing_its_marker(self):
        marker = amends.render_amends_field("a.md", "Limitation", "wrong axis")
        records = {
            "a.md": _record("Limitation"),
            "b.md": _record("Correction", f"{marker}\n"),
        }
        missing = amends_backlink.missing_backlinks(records)
        self.assertEqual(missing, ["a.md#limitation (amended by b.md)"])

    def test_empty_once_apply_backlinks_output_is_adopted(self):
        marker = amends.render_amends_field("a.md", "Limitation", "wrong axis")
        records = {
            "a.md": _record("Limitation"),
            "b.md": _record("Correction", f"{marker}\n"),
        }
        updated = dict(records)
        updated.update(amends_backlink.apply_backlinks(records))
        self.assertEqual(amends_backlink.missing_backlinks(updated), [])

    def test_broken_missing_section_conflict_and_cycle_never_reported(self):
        dangling_marker = amends.render_amends_field("missing.md", "Limitation", "r")
        nosection_marker = amends.render_amends_field("a.md", "NoSuchSection", "r")
        conflict_marker_b = amends.render_amends_field("a.md", "Limitation", "r1")
        conflict_marker_c = amends.render_amends_field("a.md", "Limitation", "r2")
        cycle_marker_a = amends.render_amends_field("z.md", "Scope", "r1")
        cycle_marker_z = amends.render_amends_field("y.md", "Limitation", "r2")

        records = {
            "y.md": _record("X", f"{dangling_marker}\n"),
            "a.md": _record("Limitation"),
            "b.md": _record("X", f"{nosection_marker}\n"),
            "c.md": _record("Y", f"{conflict_marker_b}\n"),
            "d.md": _record("Z", f"{conflict_marker_c}\n"),
        }
        self.assertEqual(amends_backlink.missing_backlinks(records), [])

        cycle_records = {
            "y.md": _record("Limitation", f"{cycle_marker_a}\n"),
            "z.md": _record("Scope", f"{cycle_marker_z}\n"),
        }
        self.assertEqual(amends_backlink.missing_backlinks(cycle_records), [])


if __name__ == "__main__":
    unittest.main()
