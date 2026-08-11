#!/usr/bin/env python3
"""Tests for test-authoring-invariant-guard.sh's ported classification
logic (issue #896 step 2) and the live hook end-to-end.

Same convention as test_pr_preflight.py: the hook embeds its checker as
inline Python inside a bash heredoc, so it isn't importable — most of this
file duplicates the exact same is_test/is_code/decision logic as plain
Python and asserts against it directly (no subprocess). The test_hook_*
functions drive the real script end-to-end against a scratch git repo.

Run: python3 on-the-record/hooks/test_test_authoring_invariant_guard.py
Run: python3 -m pytest on-the-record/hooks/test_test_authoring_invariant_guard.py -v
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
GUARD = HOOKS_DIR / "test-authoring-invariant-guard.sh"

# --- ported from test-authoring-invariant-guard.sh's inline GUARD ----------
CODE_EXT = (
    ".py", ".js", ".jsx", ".ts", ".tsx", ".sh", ".go", ".rb", ".java",
    ".rs", ".c", ".cpp", ".h", ".hpp", ".kt", ".swift", ".m", ".cs",
)
TEST_SEGMENTS = ("test", "tests", "spec", "specs")


def is_test(path):
    lower = path.lower()
    segs = re.split(r"[/\\]", lower)
    if any(s in TEST_SEGMENTS for s in segs[:-1]):
        return True
    base = segs[-1]
    return bool(re.match(r"^test_.+|.+_test\.[^.]+$|.+\.spec\.[^.]+$|.+\.test\.[^.]+$", base))


def is_code(path):
    lower = path.lower()
    if lower.startswith("docs/") or lower.endswith(".md"):
        return False
    return any(lower.endswith(ext) for ext in CODE_EXT)


def decision(paths, message=""):
    """Mirrors the guard's core decision: True means the commit is denied."""
    if re.search(r"^Test-N/A:\s*\S.*$", message, re.MULTILINE):
        return False
    code_paths = [p for p in paths if is_code(p) and not is_test(p)]
    test_touched = any(is_test(p) for p in paths)
    return bool(code_paths) and not test_touched


_CASES = []


def case(name):
    def deco(fn):
        _CASES.append((name, fn))
        return fn
    return deco


@case("code path with no test is denied")
def _t1():
    assert decision(["src/widget.py"]) is True


@case("code path with a matching test is allowed")
def _t2():
    assert decision(["src/widget.py", "test/test_widget.py"]) is False


@case("N/A trailer with a reason allows a code-only commit")
def _t3():
    assert decision(["src/widget.py"], message="fix typo\n\nTest-N/A: pure comment change, no behavior") is False


@case("N/A trailer with no reason still denies")
def _t4():
    assert decision(["src/widget.py"], message="fix typo\n\nTest-N/A:") is True


@case("docs-only change is allowed")
def _t5():
    assert decision(["docs/issue-1/reports/implementation.md"]) is False


@case("config-only change (no recognized code extension) is allowed")
def _t6():
    assert decision(["package.json", "README"]) is False


@case("a spec/ directory test file counts as a test")
def _t7():
    assert is_test("gates/test_roles_due.py") is True
    assert is_test("on-the-record/hooks/tests/widget_test.sh") is True


@case("empty diff is allowed")
def _t8():
    assert decision([]) is False


def run():
    failures = 0
    for name, fn in _CASES:
        try:
            fn()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {name}: {e}")
        else:
            print(f"PASS: {name}")
    return failures


# --- end-to-end: drive the real hook against a scratch git repo ------------
def _run_hook(payload, repo, env_extra=None):
    env = dict(os.environ)
    env.pop("ORCHESTRATE_OFF", None)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(
        ["bash", str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(repo),
        env=env,
        timeout=30,
    )
    return r


def _init_repo(tmp):
    repo = Path(tmp)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "a@b.c"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "README.md").write_text("x\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    return repo


def test_hook_denies_code_only_commit():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_repo(tmp)
        (repo / "widget.py").write_text("def f(): pass\n")
        subprocess.run(["git", "add", "widget.py"], cwd=repo, check=True)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'add widget'"}}
        r = _run_hook(payload, repo)
        assert r.returncode == 2, r.stderr


def test_hook_allows_code_with_test():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_repo(tmp)
        (repo / "widget.py").write_text("def f(): pass\n")
        (repo / "test_widget.py").write_text("def test_f(): pass\n")
        subprocess.run(["git", "add", "widget.py", "test_widget.py"], cwd=repo, check=True)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'add widget'"}}
        r = _run_hook(payload, repo)
        assert r.returncode == 0, r.stderr


def test_hook_allows_na_escape():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_repo(tmp)
        (repo / "widget.py").write_text("def f(): pass\n")
        subprocess.run(["git", "add", "widget.py"], cwd=repo, check=True)
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git commit -m 'add widget\n\nTest-N/A: config constant only'"},
        }
        r = _run_hook(payload, repo)
        assert r.returncode == 0, r.stderr


def test_hook_ignores_non_commit_command():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_repo(tmp)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
        r = _run_hook(payload, repo)
        assert r.returncode == 0, r.stderr


def test_hook_fails_open_on_malformed_payload():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_repo(tmp)
        r = subprocess.run(
            ["bash", str(GUARD)], input="not json", capture_output=True, text=True,
            cwd=str(repo), timeout=30,
        )
        assert r.returncode == 0, r.stderr


def test_hook_kill_switch():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _init_repo(tmp)
        (repo / "widget.py").write_text("def f(): pass\n")
        subprocess.run(["git", "add", "widget.py"], cwd=repo, check=True)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'x'"}}
        r = _run_hook(payload, repo, env_extra={"ORCHESTRATE_OFF": "1"})
        assert r.returncode == 0, r.stderr


if __name__ == "__main__":
    failures = run()
    for fn_name in (
        "test_hook_denies_code_only_commit",
        "test_hook_allows_code_with_test",
        "test_hook_allows_na_escape",
        "test_hook_ignores_non_commit_command",
        "test_hook_fails_open_on_malformed_payload",
        "test_hook_kill_switch",
    ):
        try:
            globals()[fn_name]()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {fn_name}: {e}")
        else:
            print(f"PASS: {fn_name}")
    sys.exit(1 if failures else 0)
