#!/usr/bin/env python3
"""issue #1005 — proves `roles/specs/secure-coding.spec.json`'s new
`use_when.trigger` actually makes the role reachable via
`gates/roles_due.py`'s evaluator.

Builds a scratch git repo the same way `gates/test_roles_due.py` does,
but loads the real `roles/specs/secure-coding.spec.json` from this
working tree (not a synthetic spec).

  python3 gates/test_secure_coding_routing.py
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import roles_due

REPO_ROOT = Path(__file__).parent.parent
SPEC_PATH = REPO_ROOT / "roles" / "specs" / "secure-coding.spec.json"


def _run(args, cwd):
    return subprocess.run(["git", "-C", str(cwd)] + args,
                           capture_output=True, text=True, check=True)


def _install_real_spec(repo):
    d = repo / "roles" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "secure-coding.spec.json").write_text(SPEC_PATH.read_text(encoding="utf-8"))


def _make_repo(tmp):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    _run(["init", "-q"], repo)
    _run(["config", "user.email", "a@b.c"], repo)
    _run(["config", "user.name", "t"], repo)
    (repo / "README.md").write_text("x\n")
    _run(["add", "README.md"], repo)
    _install_real_spec(repo)
    _run(["add", "-A"], repo)
    _run(["commit", "-q", "-m", "init"], repo)
    _run(["branch", "-M", "main"], repo)
    _run(["remote", "add", "origin", str(repo)], repo)
    _run(["update-ref", "refs/remotes/origin/main", "main"], repo)
    _run(["checkout", "-q", "-b", "issue-1/implementation"], repo)
    return repo


_CASES = []


def case(name):
    def deco(fn):
        _CASES.append((name, fn))
        return fn
    return deco


@case("seeded security-relevant diff -> secure-coding is due")
def _t1():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        (repo / "auth").mkdir()
        (repo / "auth" / "login.py").write_text("def authenticate(password):\n    pass\n")
        _run(["add", "-A"], repo)
        _run(["commit", "-q", "-m", "add auth login"], repo)
        due = roles_due.roles_due(repo, base="origin/main")
        assert len(due) == 1, due
        assert due[0]["role"] == "secure-coding"
        assert due[0]["subject"] == "issue-1"


@case("seeded unrelated diff -> secure-coding is not due")
def _t2():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        (repo / "widget.py").write_text("x = 1\n")
        _run(["add", "-A"], repo)
        _run(["commit", "-q", "-m", "add widget"], repo)
        due = roles_due.roles_due(repo, base="origin/main")
        assert due == [], due


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
