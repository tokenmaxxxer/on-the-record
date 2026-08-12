#!/usr/bin/env python3
"""issue #896 step 2 — `gates/roles_due.py` unit tests.

Builds a scratch git repo (origin/main + a feature branch) so
`gates.changed_files` has a real diff to read, and a scratch
`roles/specs/*.spec.json` set so the evaluator doesn't depend on this
repo's actual 43 specs.

  python3 gates/test_roles_due.py
"""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import roles_due


def _run(args, cwd):
    return subprocess.run(["git", "-C", str(cwd)] + args,
                           capture_output=True, text=True, check=True)


def _make_repo(tmp):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    _run(["init", "-q"], repo)
    _run(["config", "user.email", "a@b.c"], repo)
    _run(["config", "user.name", "t"], repo)
    (repo / "README.md").write_text("x\n")
    _run(["add", "README.md"], repo)
    _run(["commit", "-q", "-m", "init"], repo)
    _run(["branch", "-M", "main"], repo)
    _run(["remote", "add", "origin", str(repo)], repo)  # self-remote, enough for BASE lookups in tests
    _run(["update-ref", "refs/remotes/origin/main", "main"], repo)
    _run(["checkout", "-q", "-b", "issue-1/implementation"], repo)
    return repo


def _write_spec(repo, role, trigger, record_absent_for=None):
    d = repo / "roles" / "specs"
    d.mkdir(parents=True, exist_ok=True)
    spec = {
        "role": role,
        "use_when": {
            "board_condition": "test",
            "trigger": {**trigger, "record_absent_for": record_absent_for or role},
        },
    }
    (d / f"{role}.spec.json").write_text(json.dumps(spec))


_CASES = []


def case(name):
    def deco(fn):
        _CASES.append((name, fn))
        return fn
    return deco


@case("no trigger fires -> empty due list")
def _t1():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        _write_spec(repo, "security-threat-model", {"path_patterns": ["**/auth/**"]})
        (repo / "widget.py").write_text("x = 1\n")
        _run(["add", "widget.py"], repo)
        _run(["commit", "-q", "-m", "add widget"], repo)
        due = roles_due.roles_due(repo, base="origin/main")
        assert due == [], due


@case("matching path with no record -> due")
def _t2():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        _write_spec(repo, "security-threat-model", {"path_patterns": ["**/auth/**"]})
        (repo / "auth").mkdir()
        (repo / "auth" / "login.py").write_text("x = 1\n")
        _run(["add", "auth/login.py"], repo)
        _run(["commit", "-q", "-m", "add auth"], repo)
        due = roles_due.roles_due(repo, base="origin/main")
        assert len(due) == 1, due
        assert due[0]["role"] == "security-threat-model"
        assert due[0]["subject"] == "issue-1"


@case("matching path but record already exists -> not due")
def _t3():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        _write_spec(repo, "security-threat-model", {"path_patterns": ["**/auth/**"]})
        (repo / "auth").mkdir()
        (repo / "auth" / "login.py").write_text("x = 1\n")
        rep = repo / "docs" / "issue-1" / "reports"
        rep.mkdir(parents=True)
        (rep / "security-threat-model.md").write_text("---\nloop_state: landed\n---\n")
        _run(["add", "-A"], repo)
        _run(["commit", "-q", "-m", "add auth + record"], repo)
        due = roles_due.roles_due(repo, base="origin/main")
        assert due == [], due


@case("stale record predating a new qualifying diff -> still due (issue #1088)")
def _t3b():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        _write_spec(repo, "security-threat-model", {"path_patterns": ["**/auth/**"]})
        (repo / "auth").mkdir()
        (repo / "auth" / "login.py").write_text("x = 1\n")
        _run(["add", "auth/login.py"], repo)
        _run(["commit", "-q", "-m", "add auth"], repo)

        rep = repo / "docs" / "issue-1" / "reports"
        rep.mkdir(parents=True)
        (rep / "security-threat-model.md").write_text("---\nloop_state: landed\n---\n")
        _run(["add", "-A"], repo)
        _run(["commit", "-q", "-m", "add stale record"], repo)

        # A genuinely new qualifying diff lands after the record.
        (repo / "auth" / "login.py").write_text("x = 2\n")
        _run(["add", "auth/login.py"], repo)
        _run(["commit", "-q", "-m", "change auth again"], repo)

        due = roles_due.roles_due(repo, base="origin/main")
        assert len(due) == 1, due
        assert due[0]["role"] == "security-threat-model"


@case("content pattern match fires")
def _t4():
    with tempfile.TemporaryDirectory() as tmp:
        repo = _make_repo(tmp)
        _write_spec(repo, "security-threat-model",
                     {"path_patterns": [], "content_patterns": ["trust boundary"]})
        (repo / "design.md").write_text("this introduces a new trust boundary\n")
        _run(["add", "design.md"], repo)
        _run(["commit", "-q", "-m", "design doc"], repo)
        due = roles_due.roles_due(repo, base="origin/main")
        assert len(due) == 1, due


@case("format_report renders one line per due role, empty list -> no lines")
def _t5():
    assert roles_due.format_report([]) == []
    lines = roles_due.format_report(
        [{"role": "security-threat-model", "reason": "x", "subject": "issue-1"}])
    assert len(lines) == 2
    assert "security-threat-model" in lines[1]


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
