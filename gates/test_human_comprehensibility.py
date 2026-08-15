"""issue #1165 (technical-writing, step 2): gates/human_comprehensibility.py
tier-1 structure-check tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import human_comprehensibility as hc


def test_lead_summary_bounded_sections_record_passes():
    fixture = """This record explains what changed and why, in plain
prose, so a reader can understand the shape of the work before diving
into the sections below.

## Summary of work

We implemented the tier-1 structure checks described in the proposal.
This section stays well under the size bound and has no raw dumps.

## Next steps

- follow up on tier-2
- follow up on tier-3
"""
    result = hc.check_record(fixture)
    assert result["exempt"] is False
    assert all(r["passed"] for r in result["results"]), result["results"]


def test_raw_dump_record_fails():
    log_lines = "\n".join(f"log line {i}" for i in range(30))
    fixture = f"""This record explains what changed and why, in plain
prose, before the raw dump below.

## Logs

```
{log_lines}
```
"""
    result = hc.check_record(fixture)
    by_rule = {r["rule"]: r for r in result["results"]}
    assert by_rule["no_raw_dump"]["passed"] is False


def test_no_lead_paragraph_fails():
    fixture = """## Summary of work

- did a thing
- did another thing

## Why

This section has real explanatory prose, but it does not count as the
lead paragraph because it comes after a heading with no prose before it.
"""
    result = hc.check_record(fixture)
    by_rule = {r["rule"]: r for r in result["results"]}
    assert by_rule["lead_paragraph_present"]["passed"] is False


def test_empty_or_no_prose_content_is_exempt():
    assert hc.check_record("")["exempt"] is True

    frontmatter_only = """---
code_under_review:
  - a/b.py
status: draft
---
"""
    assert hc.check_record(frontmatter_only)["exempt"] is True


def test_first_paragraph_is_prose_helper():
    real_prose = "This is a real explanatory paragraph about the change."
    assert hc.first_paragraph_is_prose(real_prose) is True

    trailer_only = "Part of #123"
    assert hc.first_paragraph_is_prose(trailer_only) is False

    frontmatter_then_prose = """---
status: draft
---

This is the real lead paragraph after frontmatter is stripped.
"""
    assert hc.first_paragraph_is_prose(frontmatter_then_prose) is True


def _record_with_oversized_second_section():
    """Lead paragraph + section 1 (fine) + section 2 (oversized, no
    escape hatch) -- used by the changed-content-only scoping fixtures
    below to prove a pre-existing failure in an *unchanged* section is
    suppressed, and the same failure in a *changed* section still fires."""
    lead = (
        "This record explains what changed and why, in plain prose, so a\n"
        "reader can understand the shape of the work before diving into\n"
        "the sections below.\n"
    )
    section1 = "## Section one\n\nShort and fine.\n"
    oversized_lines = "\n".join(f"prose line {i} of the oversized section" for i in range(160))
    section2 = f"## Section two\n\n{oversized_lines}\n"
    text = lead + "\n" + section1 + "\n" + section2
    lines = text.splitlines()
    section2_heading_line = next(
        i for i, l in enumerate(lines, start=1) if l.strip() == "## Section two"
    )
    return text, section2_heading_line, len(lines)


def test_changed_content_only_scoping_unchanged_section_failure_passes():
    text, sec2_start, _total = _record_with_oversized_second_section()
    # Only section one's lines were touched by the diff -- section two's
    # oversized failure is pre-existing, unchanged content.
    changed_ranges = [(1, sec2_start - 1)]
    result = hc.check_record(text, changed_ranges=changed_ranges)
    by_rule = {r["rule"]: r for r in result["results"]}
    assert by_rule["section_size_bound"]["passed"] is True, by_rule["section_size_bound"]


def test_changed_content_only_scoping_changed_section_failure_fails():
    text, sec2_start, total = _record_with_oversized_second_section()
    # The diff touches section two itself -- the same failure now fires.
    changed_ranges = [(sec2_start, total)]
    result = hc.check_record(text, changed_ranges=changed_ranges)
    by_rule = {r["rule"]: r for r in result["results"]}
    assert by_rule["section_size_bound"]["passed"] is False


def test_changed_content_only_scoping_default_none_is_whole_document():
    text, _sec2_start, _total = _record_with_oversized_second_section()
    result = hc.check_record(text)
    by_rule = {r["rule"]: r for r in result["results"]}
    assert by_rule["section_size_bound"]["passed"] is False


def test_citation_trailing_placement_own_line_passes():
    fixture = (
        "This record explains what changed and why.\n"
        "canonical: docs/issue-1165/reports/implementation.md\n"
    )
    ok, reason = hc.citation_trailing_placement(fixture)
    assert ok is True, reason


def test_citation_trailing_placement_trailing_clause_passes():
    fixture = "This record explains what changed, canonical: docs/foo.md.\n"
    ok, reason = hc.citation_trailing_placement(fixture)
    assert ok is True, reason


def test_citation_trailing_placement_mid_sentence_fails():
    fixture = (
        "This record explains canonical: docs/foo.md what changed and "
        "why the change happened.\n"
    )
    ok, reason = hc.citation_trailing_placement(fixture)
    assert ok is False


def test_check_record_includes_citation_trailing_placement_rule():
    fixture = (
        "This record explains canonical: docs/foo.md what changed and "
        "why the change happened.\n\n"
        "## Summary of work\n\nDone.\n"
    )
    result = hc.check_record(fixture)
    by_rule = {r["rule"]: r for r in result["results"]}
    assert "citation_trailing_placement" in by_rule
    assert by_rule["citation_trailing_placement"]["passed"] is False


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
