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


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
