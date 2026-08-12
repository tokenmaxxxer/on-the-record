#!/usr/bin/env python3
"""issue #993 acceptance check — a utilization-report gate test.

Counts board records per `roles/*.json` stem using the exact derivation
rule the merged product-discovery survey used
(docs/issue-993/reports/product-discovery/current-state.md line 16): a
flat `docs/issue-<n>/reports/<role>.md` OR a nested
`docs/issue-<n>/reports/<role>/*.md`, matched by literal stem equality.
No fuzzy matching, and the known `coding` plugin-dir / `implementation`
role-name doubling is left unreconciled — same scope as the survey.

  python3 gates/test_role_utilization_report.py
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_OVERLAP_MARKER = "(b) scope overlap"


def role_stems(root: Path) -> list[str]:
    return sorted(p.stem for p in (root / "roles").glob("*.json"))


def count_records(root: Path, stems: list[str]) -> dict[str, int]:
    """role stem -> count of board records matching the survey's rule."""
    counts = {stem: 0 for stem in stems}
    stem_set = set(stems)
    docs = root / "docs"
    if not docs.is_dir():
        return counts
    for issue_dir in sorted(docs.glob("issue-*")):
        if not issue_dir.is_dir() or not re.match(r"^issue-\d+$", issue_dir.name):
            continue
        reports = issue_dir / "reports"
        if not reports.is_dir():
            continue
        for entry in reports.iterdir():
            if entry.is_file() and entry.suffix == ".md":
                stem = entry.stem
                if stem in stem_set:
                    counts[stem] += 1
            elif entry.is_dir() and entry.name in stem_set:
                counts[entry.name] += len(list(entry.glob("*.md")))
    return counts


def overlap_disposition_roles(root: Path, roles: list[str]) -> dict[str, bool]:
    """role -> whether its roles/<role>.json use_when carries the
    (b)-style overlap disposition marker."""
    out = {}
    for role in roles:
        p = root / "roles" / f"{role}.json"
        text = p.read_text(encoding="utf-8") if p.is_file() else ""
        out[role] = _OVERLAP_MARKER in text
    return out


def test_all_43_role_stems_present_as_keys_in_count_map():
    stems = role_stems(ROOT)
    assert len(stems) == 43, f"expected 43 role stems, found {len(stems)}: {stems}"
    counts = count_records(ROOT, stems)
    for stem in stems:
        assert stem in counts, f"missing count key for role {stem!r}"


def test_counts_are_nonnegative_ints_no_stray_keys():
    stems = role_stems(ROOT)
    counts = count_records(ROOT, stems)
    assert set(counts.keys()) == set(stems)
    for stem, n in counts.items():
        assert isinstance(n, int) and n >= 0, f"{stem}: {n!r}"


def test_refactoring_legacy_and_test_authoring_carry_overlap_disposition():
    disp = overlap_disposition_roles(ROOT, ["refactoring-legacy", "test-authoring"])
    for role, has_marker in disp.items():
        assert has_marker, (
            f"roles/{role}.json use_when is missing the (b)-style scope-overlap "
            f"disposition note (issue #993 product-discovery diagnosis)"
        )


_CASES = [
    ("all 43 role stems present as keys in the count map (zero is valid, absence is not)",
     test_all_43_role_stems_present_as_keys_in_count_map),
    ("counts are non-negative ints, no stray keys beyond the 43 stems",
     test_counts_are_nonnegative_ints_no_stray_keys),
    ("refactoring-legacy and test-authoring carry the (b) overlap disposition in use_when",
     test_refactoring_legacy_and_test_authoring_carry_overlap_disposition),
]


def run():
    failures = 0
    for name, fn in _CASES:
        try:
            fn()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {name}: {e}")
        except Exception as e:
            failures += 1
            print(f"FAIL: {name}: unexpected {type(e).__name__}: {e}")
        else:
            print(f"PASS: {name}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run() else 0)
