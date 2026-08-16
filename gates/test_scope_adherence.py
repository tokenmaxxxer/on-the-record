from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import scope_adherence as sa  # noqa: E402


def test_blocks_when_file_outside_every_declared_prefix():
    kind, reason = sa.classify(
        frozenset({"src/auth/"}),
        frozenset({"src/auth/login.py", "src/payments/x.py"}),
        1658,
    )
    assert kind == sa.BLOCKED
    assert "src/payments/x.py" in reason


def test_passes_when_all_files_within_declared_prefixes():
    kind, reason = sa.classify(
        frozenset({"src/auth/"}),
        frozenset({"src/auth/login.py", "src/auth/session.py"}),
        1658,
    )
    assert kind == sa.PASS
    assert reason is None


def test_declared_scope_none_is_advisory_and_never_blocks():
    kind, reason = sa.classify(None, frozenset({"src/anything/x.py"}), 1658)
    assert kind == sa.PASS
    assert reason == sa.ADVISORY


def test_declared_scope_none_never_blocks_even_with_wild_paths():
    kind, _ = sa.classify(None, frozenset({"../../etc/passwd"}), 1658)
    assert kind == sa.PASS


def test_own_record_tree_always_in_scope():
    kind, reason = sa.classify(
        frozenset({"src/auth/"}),
        frozenset({"docs/issue-1658/reports/implementation.md"}),
        1658,
    )
    assert kind == sa.PASS
    assert reason is None


def test_own_record_tree_in_scope_alongside_declared_prefix_files():
    kind, reason = sa.classify(
        frozenset({"src/auth/"}),
        frozenset({"src/auth/login.py", "docs/issue-1658/reports/implementation.md"}),
        1658,
    )
    assert kind == sa.PASS
    assert reason is None


def test_empty_pr_files_passes_regardless_of_declared_scope():
    kind, reason = sa.classify(frozenset({"src/auth/"}), frozenset(), 1658)
    assert kind == sa.PASS
    assert reason is None


def test_parse_declared_scope_single_prefix():
    body = "some text\nscope: src/auth/\nmore text\n"
    assert sa.parse_declared_scope(body) == frozenset({"src/auth/"})


def test_parse_declared_scope_comma_list():
    body = "scope: src/auth/, src/session/\n"
    assert sa.parse_declared_scope(body) == frozenset({"src/auth/", "src/session/"})


def test_parse_declared_scope_case_insensitive():
    body = "Scope: src/auth/\n"
    assert sa.parse_declared_scope(body) == frozenset({"src/auth/"})


def test_parse_declared_scope_absent_returns_none():
    body = "no scope field here\nother: stuff\n"
    assert sa.parse_declared_scope(body) is None


def test_parse_declared_scope_empty_value_returns_none():
    body = "scope: \n"
    assert sa.parse_declared_scope(body) is None
