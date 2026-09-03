"""Issue #3182 round 3: an independent verification of PR #3184 found that
5 of the script's 9 `source` citations pointed a few lines away from the
call they claimed to cite -- close enough to look right, wrong enough to
mislead a reader who trusts the citation instead of opening the file. The
free-text `source` field is for humans; this test checks the underlying
claim mechanically so a future edit that shifts a cited file's lines fails
the suite instead of quietly drifting.

Round 4: PR #3184's round-3 verification (PR #3203) found the match itself
was a raw substring containment (`expected in actual`) against the cited
line's *text*, so an anchor moved onto a comment -- or onto a string
literal that merely mentions the call in prose, e.g. this module's own
docstrings quoting `os.statvfs()` -- would still pass. `_line_is_code_match`
below distinguishes real code from a comment or a bare string statement
(module/function/class docstring, or any standalone string-literal
statement) before checking containment:

  - `.py` files: tokenized with the stdlib `tokenize` module (not text
    heuristics, so a `#` or a matching phrase inside an actual code string
    -- e.g. `cmd = ["claude", ...]` -- is never mistaken for a comment or
    excluded). COMMENT tokens are always masked out. STRING tokens are
    masked out only when they form a whole bare statement by themselves
    (the token immediately before and after, ignoring blank/indent
    tokens, is a NEWLINE or start/end of file) -- exactly the docstring
    shape, leaving strings that participate in a real expression (a list
    element, a call argument) untouched.
  - non-`.py` files (the one shell citation in this script's CHECKS):
    a quote-aware `#`-strip, so a `#` inside a quoted string is not
    mistaken for a comment start.

Test derivation (test-derivation skill): each `CHECKS` entry in
`scripts/preflight/consumer_preconditions.py` carries a `line_anchors` list
of `(file, line, expected_substring)` triples -- one per file:line the
entry's `source` prose actually names. This is a decision-table check, one
row per anchor: open the cited file, read the cited line (1-indexed, same
convention as `sed -n '<N>p'` and every human reader), and assert the
expected substring is present in the line's *code*, not merely its text.
A line that has shifted -- whether the cited code moved, or the citation
was wrong to begin with -- fails here instead of only being catchable by a
human re-reading every citation by hand. The discrimination itself is
proved both ways with synthetic fixtures: a comment (and a docstring)
mentioning the target text must be rejected, and every one of the 16 real
anchors currently in CHECKS must still pass.

  python3 -m pytest tests/test_issue_3182_citation_line_accuracy.py -q
"""
from __future__ import annotations

import importlib.util
import tempfile
import tokenize
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


_BOUNDARY_TYPES = (tokenize.NEWLINE,)
_DROP_TYPES = (
    tokenize.NL,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.COMMENT,
    tokenize.ENCODING,
    tokenize.ENDMARKER,
)


def _python_masked_spans(path: Path) -> dict[int, list[tuple[int, int]]]:
    """Row -> [(start_col, end_col), ...] spans to blank before matching:
    every COMMENT token, plus every STRING token that is a bare statement
    by itself (a docstring, or any standalone string-literal statement)."""
    spans: dict[int, list[tuple[int, int]]] = {}

    def _add(row: int, start_col: int, end_col: int) -> None:
        spans.setdefault(row, []).append((start_col, end_col))

    with path.open("rb") as f:
        try:
            toks = list(tokenize.tokenize(f.readline))
        except (tokenize.TokenizeError, SyntaxError, IndentationError):
            return spans

    for t in toks:
        if t.type == tokenize.COMMENT:
            _add(t.start[0], t.start[1], t.end[1])

    significant = [t for t in toks if t.type not in _DROP_TYPES]
    for idx, t in enumerate(significant):
        if t.type != tokenize.STRING:
            continue
        prev_tok = significant[idx - 1] if idx > 0 else None
        next_tok = significant[idx + 1] if idx + 1 < len(significant) else None
        prev_is_boundary = prev_tok is None or prev_tok.type in _BOUNDARY_TYPES
        next_is_boundary = next_tok is None or next_tok.type in _BOUNDARY_TYPES
        if not (prev_is_boundary and next_is_boundary):
            continue  # participates in a real expression -- keep as code
        start_row, start_col = t.start
        end_row, end_col = t.end
        _TO_EOL = 1_000_000  # slicing past a line's length is a no-op, so
        # this just means "blank to end of line" without needing this
        # line's actual length.
        if start_row == end_row:
            _add(start_row, start_col, end_col)
        else:
            _add(start_row, start_col, _TO_EOL)
            for row in range(start_row + 1, end_row):
                _add(row, 0, _TO_EOL)
            _add(end_row, 0, end_col)
    return spans


_PY_SPAN_CACHE: dict[Path, dict[int, list[tuple[int, int]]]] = {}


def _strip_shell_comment(line: str) -> str:
    """Quote-aware '#' stripper: a '#' inside a single- or double-quoted
    string is not a comment start."""
    in_single = in_double = False
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if in_single:
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue
        if ch == "'":
            in_single = True
        elif ch == '"':
            in_double = True
        elif ch == "#":
            return line[:i]
        i += 1
    return line


def _code_only_line(path: Path, lineno: int) -> str:
    """The cited line with any comment or bare-string-statement portion
    blanked out, so a citation match against prose is rejected instead of
    passing on a bare text hit."""
    raw = _line(path, lineno)
    if path.suffix != ".py":
        return _strip_shell_comment(raw)
    spans = _PY_SPAN_CACHE.get(path)
    if spans is None:
        spans = _python_masked_spans(path)
        _PY_SPAN_CACHE[path] = spans
    for start_col, end_col in spans.get(lineno, []):
        raw = raw[:start_col] + " " * max(0, min(end_col, len(raw)) - start_col) + raw[end_col:]
    return raw


def _line_is_code_match(path: Path, lineno: int, expected: str) -> bool:
    return expected in _code_only_line(path, lineno)


def _code_occurrences(path: Path, expected: str) -> list[int]:
    """Line numbers where `expected` appears as real code, in order."""
    total = len(path.read_text(encoding="utf-8").splitlines())
    return [n for n in range(1, total + 1)
            if expected in _code_only_line(path, n)]


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
        anchor_count = 0
        for check in _cp.CHECKS:
            for rel_path, ordinal, expected in check["line_anchors"]:
                anchor_count += 1
                cited_path = ROOT / rel_path
                if not cited_path.is_file():
                    failures.append(
                        f"{check['name']}: {rel_path} does not exist under {ROOT}"
                    )
                    continue
                # Issue #3297: anchors are ordinals now -- the Nth
                # real-code occurrence -- because line numbers drifted six
                # times as these files grew, twice in one day. An ordinal
                # only moves when someone adds or removes an occurrence of
                # that exact call, which is a change worth noticing.
                hits = _code_occurrences(cited_path, expected)
                if len(hits) < ordinal:
                    failures.append(
                        f"{check['name']}: {rel_path} has {len(hits)} "
                        f"real-code occurrence(s) of {expected!r}, so the "
                        f"anchor's #{ordinal} does not exist -- the cited "
                        "call was removed or renamed"
                    )
        # Locks in the count this docstring and the round-4 record cite --
        # a silent drop in anchor count (a check losing its line_anchors
        # entirely) would otherwise pass this loop by iterating zero times.
        self.assertEqual(
            anchor_count, 16,
            f"expected 16 line_anchors across all CHECKS, found {anchor_count}",
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


class CitationCommentAndStringDiscriminationTest(unittest.TestCase):
    """Round 4: prove the matcher tells real code apart from a comment or
    a bare string statement (docstring) that merely mentions the same
    text, in both directions -- reject the prose, accept the code."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_dir = Path(self._tmp.name)

    def test_python_comment_line_is_rejected(self):
        p = self.tmp_dir / "fake.py"
        p.write_text(
            "x = 1\n"
            "# os.fork() is called a few lines below\n"
            "child_pid = os.fork()\n"
        )
        self.assertFalse(
            _line_is_code_match(p, 2, "os.fork()"),
            "a full-line comment mentioning the target text must not match",
        )
        self.assertTrue(
            _line_is_code_match(p, 3, "os.fork()"),
            "the real call on the following line must still match",
        )

    def test_python_trailing_comment_is_rejected(self):
        p = self.tmp_dir / "fake_trailing.py"
        p.write_text("y = 2  # os.fork() mentioned here, not called\n")
        self.assertFalse(
            _line_is_code_match(p, 1, "os.fork()"),
            "a trailing comment mentioning the target text must not match",
        )

    def test_python_docstring_mention_is_rejected(self):
        p = self.tmp_dir / "fake_doc.py"
        p.write_text(
            '"""This module mirrors os.fork() semantics for its callers."""\n'
            "import os\n"
            "\n"
            "\n"
            "def spawn():\n"
            '    """Calls os.fork() to create the child."""\n'
            "    child_pid = os.fork()\n"
            "    return child_pid\n"
        )
        self.assertFalse(
            _line_is_code_match(p, 1, "os.fork()"),
            "a module docstring mentioning the target text must not match",
        )
        self.assertFalse(
            _line_is_code_match(p, 6, "os.fork()"),
            "a function docstring mentioning the target text must not match",
        )
        self.assertTrue(
            _line_is_code_match(p, 7, "os.fork()"),
            "the real call must still match",
        )

    def test_python_string_literal_that_is_real_code_still_matches(self):
        # Guard against an over-broad fix that excludes every string --
        # e.g. pipeline.py's real citation is a string element inside an
        # actual list-construction statement, not a bare statement.
        p = self.tmp_dir / "fake_call.py"
        p.write_text('cmd = ["claude", "-p", "--settings", settings_path]\n')
        self.assertTrue(
            _line_is_code_match(p, 1, 'cmd = ["claude"'),
            "a string literal that is itself part of real code must still match",
        )

    def test_shell_comment_line_is_rejected(self):
        p = self.tmp_dir / "fake.sh"
        p.write_text(
            "x=1\n"
            "# _ROLE_BRANCH_RE.match(d) happens further down\n"
            "if all(_ROLE_BRANCH_RE.match(d) for d in dsts); then\n"
        )
        self.assertFalse(
            _line_is_code_match(p, 2, "_ROLE_BRANCH_RE.match(d)"),
            "a full-line shell comment mentioning the target text must not match",
        )
        self.assertTrue(
            _line_is_code_match(p, 3, "_ROLE_BRANCH_RE.match(d)"),
            "the real code line must still match",
        )

    def test_shell_hash_inside_quotes_is_not_treated_as_comment(self):
        p = self.tmp_dir / "fake_quoted.sh"
        p.write_text('deny "denying (fail-closed, issue #2617)."\n')
        self.assertTrue(
            _line_is_code_match(p, 1, "issue #2617"),
            "a '#' inside a quoted string must not be mistaken for a comment start",
        )

    def test_all_sixteen_real_anchors_still_pass(self):
        # Restates test_every_cited_line_contains_the_call_it_claims's
        # count/pass assertions through the same discriminating matcher,
        # so the "real anchors still pass" half of the proof lives next
        # to the "comment is rejected" half above rather than only in the
        # older test class.
        checked = 0
        for check in _cp.CHECKS:
            for rel_path, ordinal, expected in check["line_anchors"]:
                checked += 1
                cited_path = ROOT / rel_path
                self.assertTrue(cited_path.is_file(), f"{rel_path} missing")
                # Same discriminating matcher, resolved by ordinal
                # (issue #3297) -- comments and docstrings still do not
                # count as occurrences, which is what this class proves.
                hits = _code_occurrences(cited_path, expected)
                self.assertGreaterEqual(
                    len(hits), ordinal,
                    f"{check['name']}: {rel_path} has {len(hits)} real-code "
                    f"occurrence(s) of {expected!r}, anchor wants #{ordinal}",
                )
        self.assertEqual(checked, 16)


if __name__ == "__main__":
    unittest.main()
