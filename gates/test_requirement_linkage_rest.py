#!/usr/bin/env python3
"""issue #1569 acceptance — priority instance: `requirement_linkage.check()`
must succeed off REST alone when the GraphQL-shaped `gh issue view` command
is rate-limited, and must refuse when both paths fail, and must refuse when
`gh` is entirely absent. Hermetic: monkeypatches `gh_rest.subprocess.run` so
no real `gh`/network call happens.

  python3 gates/test_requirement_linkage_rest.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))
import gh_rest
import requirement_linkage

_BODY = "Closes the loop for R001."


def _install(fake_run):
    real = gh_rest.subprocess.run
    gh_rest.subprocess.run = fake_run
    return real


def _restore(real):
    gh_rest.subprocess.run = real


def t_check_passes_when_graphql_rate_limited_and_rest_alive():
    def fake_run(argv, cwd=None, capture_output=True, text=True):
        if argv[:2] == ["git", "remote"]:
            return SimpleNamespace(returncode=0, stdout="git@github.com:owner/repo.git\n")
        if argv[:3] == ["gh", "issue", "view"]:
            return SimpleNamespace(returncode=1, stdout="", stderr="API rate limit exceeded")
        if argv[:2] == ["gh", "api"]:
            return SimpleNamespace(returncode=0, stdout='{"title": "t", "body": "%s"}' % _BODY)
        raise AssertionError(f"unexpected call: {argv}")
    real = _install(fake_run)
    try:
        bad = requirement_linkage.check(Path("."), 1550)
        assert bad == [], bad
    finally:
        _restore(real)


def t_check_refuses_when_both_paths_fail():
    def fake_run(argv, cwd=None, capture_output=True, text=True):
        if argv[:2] == ["git", "remote"]:
            return SimpleNamespace(returncode=0, stdout="git@github.com:owner/repo.git\n")
        return SimpleNamespace(returncode=1, stdout="", stderr="rate limited")
    real = _install(fake_run)
    try:
        bad = requirement_linkage.check(Path("."), 1550)
        assert bad, "both paths failing must refuse, not pass"
    finally:
        _restore(real)


def t_check_refuses_when_no_gh_at_all():
    def fake_run(argv, cwd=None, capture_output=True, text=True):
        raise FileNotFoundError("gh: command not found")
    real = _install(fake_run)
    try:
        bad = requirement_linkage.check(Path("."), 1550)
        assert bad, "no gh available must refuse, not pass"
    finally:
        _restore(real)


def _run(fns):
    ok = 0
    for name, fn in fns:
        fn()
        ok += 1
        print(f"ok - {name}")
    print(f"{ok}/{len(fns)} passed")


if __name__ == "__main__":
    _run([(n, f) for n, f in list(globals().items())
          if n.startswith("t_") and callable(f)])
