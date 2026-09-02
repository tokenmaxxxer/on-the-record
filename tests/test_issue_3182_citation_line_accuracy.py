"""Issue #3182 round 3: an independent verification of PR #3184 found that
5 of the script's 9 `source` citations pointed a few lines away from the
call they claimed to cite -- close enough to look right, wrong enough to
mislead a reader who trusts the citation instead of opening the file. The
free-text `source` field is for humans; this test checks the underlying
claim mechanically so a future edit that shifts a cited file's lines fails
the suite instead of quietly drifting.

Test derivation (test-derivation skill): each `CHECKS` entry in
`scripts/preflight/consumer_preconditions.py` carries a `line_anchors` list
of `(file, line, expected_substring)` triples -- one per file:line the
entry's `source` prose actually names. This is a decision-table check, one
row per anchor: open the cited file, read the cited line (1-indexed, same
convention as `sed -n '<N>p'` and every human reader), and assert the
expected substring is present. A line that has shifted -- whether the cited
code moved, or the citation was wrong to begin with -- fails here instead
of only being catchable by a human re-reading every citation by hand.

  python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "preflight" / "consumer_preconditions.py"

_spec = importlib.util.spec_from_file_location("consumer_preconditions", SCRIPT)
_cp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cp)


def _line(path: Path, lineno: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert 1 <= lineno <= len(lines), (
        f"{path} has {len(lines)} lines, cannot read line {lineno}"
    )
    return lines[lineno - 1]


class CitationLineAccuracyTest(unittest.TestCase):
    def test_every_check_declares_at_least_one_line_anchor(self):
        for check in _cp.CHECKS:
            self.assertIn(
                "line_anchors", check, f"{check['name']}: missing line_anchors"
            )
            self.assertTrue(
                check["line_anchors"], f"{check['name']}: line_anchors is empty"
            )

    def test_every_cited_line_contains_the_call_it_claims(self):
        failures = []
        for check in _cp.CHECKS:
            for rel_path, lineno, expected in check["line_anchors"]:
                cited_path = ROOT / rel_path
                if not cited_path.is_file():
                    failures.append(
                        f"{check['name']}: {rel_path} does not exist under {ROOT}"
                    )
                    continue
                actual = _line(cited_path, lineno)
                if expected not in actual:
                    failures.append(
                        f"{check['name']}: {rel_path}:{lineno} does not contain "
                        f"{expected!r} -- actual line: {actual!r}"
                    )
        self.assertFalse(failures, "citation drift found:\n" + "\n".join(failures))

    def test_every_line_anchor_file_is_named_in_the_source_field(self):
        # Cheap cross-check that line_anchors and the human-readable source
        # prose were not edited independently of each other.
        for check in _cp.CHECKS:
            source = check["source"]
            for rel_path, _lineno, _expected in check["line_anchors"]:
                basename = rel_path.rsplit("/", 1)[-1]
                self.assertIn(
                    basename, source,
                    f"{check['name']}: line_anchors cites {rel_path!r} but "
                    f"'source' text does not mention {basename!r}: {source!r}",
                )


if __name__ == "__main__":
    unittest.main()
