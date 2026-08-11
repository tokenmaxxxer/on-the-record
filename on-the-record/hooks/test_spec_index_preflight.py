#!/usr/bin/env python3
"""Pure-Python tests for spec-index-preflight.sh's drift-detection logic
(issue #459). No live `git`/`gh` calls — the comparison logic from the
hook's embedded GUARD python body is duplicated here as plain,
import-free functions operating on in-memory index-row text and a
staged-path -> bytes map, matching test_contract_guard.py's convention
of exercising hook logic directly rather than shelling out.

Run: python3 on-the-record/hooks/test_spec_index_preflight.py
Exit 0 all pass / exit 1 on any failure. Prints PASS/FAIL per case.
"""
from __future__ import annotations
import hashlib
import re
import shlex
import sys

INDEX_REL = "docs/specs/reconciled-index.md"
_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{64})`\s*\|\s*$")


def is_git_commit_invocation(cmd):
    """Mirrors the GUARD python body's trigger check (issue #866, tokenizer
    swapped to `punctuation_chars=True` in issue #882): tokenize first,
    then require both `git` and `commit` as standalone tokens — survives
    any global option (`-c key=val`, `-C <path>`, ...) between them, does
    not fire on `commit` appearing inside an unrelated token or a quoted
    string, and (issue #882) does not fuse an unspaced `(`/`)` onto the
    adjacent word, which plain `shlex.split` did."""
    try:
        _lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        _lexer.whitespace_split = True
        tokens = list(_lexer)
    except ValueError:
        return False
    return "git" in tokens and "commit" in tokens


def parse_rows(text):
    rows = []
    for line in text.splitlines():
        m = _ROW_RE.match(line)
        if m:
            rows.append((m.group(1), m.group(2)))
    return rows


def find_mismatches(on_disk_index_text, staged_paths, staged_bytes):
    """Mirrors the GUARD python body: resolve rows (staged index if
    staged, else on-disk), then compare each staged tracked file's
    staged-content hash against the recorded hash.

    staged_paths: set of rel paths in `git diff --cached --name-only`.
    staged_bytes: dict rel_path -> bytes (staged content via `git show
    :<path>`); a path absent from this dict means git show failed / file
    unreadable and must be skipped, not treated as a mismatch.
    """
    rows = parse_rows(on_disk_index_text)
    if INDEX_REL in staged_paths and INDEX_REL in staged_bytes:
        try:
            rows = parse_rows(staged_bytes[INDEX_REL].decode("utf-8"))
        except UnicodeDecodeError:
            pass

    mismatches = []
    for rel_path, recorded_hash in rows:
        if rel_path not in staged_paths:
            continue
        content = staged_bytes.get(rel_path)
        if content is None:
            continue
        actual_hash = hashlib.sha256(content).hexdigest()
        if actual_hash != recorded_hash:
            mismatches.append(rel_path)
    return mismatches


def _row(path, content_bytes):
    h = hashlib.sha256(content_bytes).hexdigest()
    return f"| `{path}` | `{h}` |\n"


def _index_text(rows):
    return "| Path | SHA256 |\n| --- | --- |\n" + "".join(rows)


TESTS = []


def test(name):
    def deco(fn):
        TESTS.append((name, fn))
        return fn
    return deco


@test("red: tracked file staged content changed, index not staged -> mismatch")
def _t1():
    old_content = b"# spec v1\ncontent\n"
    new_content = b"# spec v1\ncontent CHANGED\n"
    index_text = _index_text([_row("docs/specs/foo.md", old_content)])

    staged_paths = {"docs/specs/foo.md"}  # index itself NOT staged
    staged_bytes = {"docs/specs/foo.md": new_content}

    mismatches = find_mismatches(index_text, staged_paths, staged_bytes)
    assert mismatches == ["docs/specs/foo.md"], mismatches


@test("red: tracked file changed, index staged but still carries OLD hash")
def _t2():
    old_content = b"# spec v1\ncontent\n"
    new_content = b"# spec v1\ncontent CHANGED\n"
    on_disk_index_text = _index_text([_row("docs/specs/foo.md", old_content)])
    # staged index still has the old (stale) hash row
    staged_index_text = _index_text([_row("docs/specs/foo.md", old_content)])

    staged_paths = {"docs/specs/foo.md", INDEX_REL}
    staged_bytes = {
        "docs/specs/foo.md": new_content,
        INDEX_REL: staged_index_text.encode("utf-8"),
    }

    mismatches = find_mismatches(on_disk_index_text, staged_paths, staged_bytes)
    assert mismatches == ["docs/specs/foo.md"], mismatches


@test("green: tracked file changed, staged index carries matching NEW hash")
def _t3():
    old_content = b"# spec v1\ncontent\n"
    new_content = b"# spec v1\ncontent CHANGED\n"
    on_disk_index_text = _index_text([_row("docs/specs/foo.md", old_content)])
    staged_index_text = _index_text([_row("docs/specs/foo.md", new_content)])

    staged_paths = {"docs/specs/foo.md", INDEX_REL}
    staged_bytes = {
        "docs/specs/foo.md": new_content,
        INDEX_REL: staged_index_text.encode("utf-8"),
    }

    mismatches = find_mismatches(on_disk_index_text, staged_paths, staged_bytes)
    assert mismatches == [], mismatches


@test("green: unrelated file staged, tracked file untouched -> no mismatch")
def _t4():
    content = b"# spec v1\ncontent\n"
    index_text = _index_text([_row("docs/specs/foo.md", content)])

    staged_paths = {"README.md"}
    staged_bytes = {"README.md": b"whatever\n"}

    mismatches = find_mismatches(index_text, staged_paths, staged_bytes)
    assert mismatches == [], mismatches


@test("green: tracked file staged but content unchanged -> no mismatch")
def _t5():
    content = b"# spec v1\ncontent\n"
    index_text = _index_text([_row("docs/specs/foo.md", content)])

    staged_paths = {"docs/specs/foo.md"}
    staged_bytes = {"docs/specs/foo.md": content}

    mismatches = find_mismatches(index_text, staged_paths, staged_bytes)
    assert mismatches == [], mismatches


@test("skip: tracked file staged but git show failed (deletion) -> no mismatch")
def _t6():
    old_content = b"# spec v1\ncontent\n"
    index_text = _index_text([_row("docs/specs/foo.md", old_content)])

    staged_paths = {"docs/specs/foo.md"}
    staged_bytes = {}  # git show :path failed -> absent

    mismatches = find_mismatches(index_text, staged_paths, staged_bytes)
    assert mismatches == [], mismatches


@test("trigger: plain `git commit` is recognized")
def _t7():
    assert is_git_commit_invocation('git commit -m "x"') is True


@test("trigger: issue #866 regression — `git -c k=v commit` is recognized")
def _t8():
    # PR #863-shaped drift landed via a plain `git commit`, but the
    # original `\bgit\s+commit\b` regex only matched when `commit`
    # immediately followed `git` (whitespace only) — any global option in
    # between (a completely ordinary, legitimate git invocation) skipped
    # the check entirely with no denial. Live-reproduced (issue #866
    # after-proposal hunt) via `git -c commit.gpgsign=false commit -m x`
    # exiting 0 with no stderr against the exact PR #863 staged drift.
    assert is_git_commit_invocation('git -c commit.gpgsign=false commit -m "x"') is True


@test("trigger: `git log --grep=commit` is not a commit invocation")
def _t9():
    assert is_git_commit_invocation("git log --grep=commit") is False


@test("trigger: `git commit-tree` is not `git commit`")
def _t10():
    assert is_git_commit_invocation("git commit-tree deadbeef") is False


@test("trigger: 'commit' only inside a quoted string is not a commit invocation")
def _t11():
    assert is_git_commit_invocation('echo "please run git commit before pushing"') is False


@test("trigger: unparseable command (unbalanced quote) fails open -> False")
def _t12():
    assert is_git_commit_invocation('git commit -m "unterminated') is False


@test("trigger: issue #882 regression — `(git commit -m x)` subshell wrap is recognized")
def _t13():
    # plain `shlex.split` fuses the unspaced `(` onto `git`, producing
    # `"(git"` as one token — `"git" in tokens` was False even though the
    # wrapped command is a real, ordinary subshell commit (issue #876's
    # before-landing hunt reproduced this live: exit 0, commit landed).
    assert is_git_commit_invocation('(git commit -m "x")') is True


@test("trigger: `cd /tmp && git commit -m x` chained invocation is recognized")
def _t14():
    assert is_git_commit_invocation("cd /tmp && git commit -m x") is True


def main():
    failures = 0
    for name, fn in TESTS:
        try:
            fn()
        except AssertionError as ex:
            print(f"FAIL: {name}: {ex}")
            failures += 1
        except Exception as ex:  # noqa: BLE001
            print(f"FAIL: {name}: unexpected {type(ex).__name__}: {ex}")
            failures += 1
        else:
            print(f"PASS: {name}")
    if failures:
        print(f"{failures} failure(s)")
        return 1
    print("all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
