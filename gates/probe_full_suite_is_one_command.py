#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3091.

Asserts the property whose absence let 15 `test/` failures sit
unobserved while `tests/` alone was called green: **one** documented
command collects and runs every test file in the repo, and no test file
lives outside what that command collects.

`docs/handbooks/operations.md` documents `python3 -m pytest -q` (no path
argument, no `--ignore=gates`) as *the* full-suite command. This probe
checks that claim two ways, mechanically, never by scraping prose:

1. Every git-tracked `test_*.py`/`*_test.py` file that actually defines
   at least one collectible test item (a module matching the naming
   convention but defining zero tests, e.g. a parser library merely
   named `test_*.py`, does not count -- `pytest` reports "no tests
   collected" for it either way, so it was never hidden) must appear in
   `python3 -m pytest -q --collect-only`'s own collected-file set. A
   file present on disk but absent from that set is exactly the
   `test/`-vs-`tests/` shape this issue exists to catch.
2. No git-tracked file matches a non-pytest-collectible test-file
   pattern (`*.test.sh`) -- pytest can never collect a shell script, so
   the mere existence of one means a second, separate command
   (`bash tests/run-orchestrate-tests.sh`, per
   `docs/handbooks/on-the-record.md`) is required to run "every test in
   the repo." That second command's necessity is itself the violation:
   there is no longer a *single* command that suffices.

Must fail against the tree as of issue #3091 (two `.test.sh` files:
`tests/check-write-set-conflicts.test.sh`,
`tests/claim-scan-preflight.test.sh` -- neither is invoked by
`python3 -m pytest -q`, nor by `tests/run-orchestrate-tests.sh` itself).

Run as `python3 gates/probe_full_suite_is_one_command.py` from anywhere;
it resolves the repo root itself. Prints `ok` and exits 0 only when a
single command already covers every test file; otherwise prints each
violation to stderr and exits non-zero.
"""
from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PY_TEST_FILE_SUFFIXES = ("_test.py",)
SHELL_TEST_FILE_SUFFIXES = (".test.sh",)

FULL_SUITE_COMMAND = [sys.executable, "-m", "pytest", "-q", "--collect-only", "-q"]
# per docs/handbooks/operations.md: "Run python3 -m pytest -q with no
# ignore flag" -- the documented single full-suite invocation.


def _fail(messages: list[str]) -> None:
    for m in messages:
        print(f"FAIL: {m}", file=sys.stderr)
    sys.exit(1)


def _norecursedirs() -> list[str]:
    cfg = configparser.ConfigParser()
    cfg.read(REPO_ROOT / "pytest.ini")
    raw = cfg.get("pytest", "norecursedirs", fallback="")
    return [d for d in raw.split() if d]


def _is_py_test_filename(name: str) -> bool:
    return name.startswith("test_") and name.endswith(".py") or name.endswith("_test.py")


def _is_shell_test_filename(name: str) -> bool:
    return name.endswith(".test.sh")


def _git_tracked_files() -> list[str]:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-files"],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        _fail([f"git ls-files failed: {r.stderr.strip()}"])
    return r.stdout.splitlines()


def _under_excluded_dir(path: str, excluded: list[str]) -> bool:
    parts = Path(path).parts
    for exc in excluded:
        exc_parts = Path(exc).parts
        if tuple(parts[:len(exc_parts)]) == exc_parts:
            return True
    return False


def _defines_any_test_item(relpath: str) -> bool:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only", "-q", relpath],
        capture_output=True, text=True, timeout=60, cwd=REPO_ROOT,
    )
    return bool(r.stdout) and "::" in r.stdout


def _collected_files() -> set[str]:
    r = subprocess.run(FULL_SUITE_COMMAND, capture_output=True, text=True,
                       timeout=180, cwd=REPO_ROOT)
    files = set()
    for line in r.stdout.splitlines():
        if "::" not in line:
            continue
        files.add(line.split("::", 1)[0])
    return files


def main() -> None:
    excluded = _norecursedirs()
    tracked = _git_tracked_files()

    py_candidates = [p for p in tracked if _is_py_test_filename(Path(p).name)
                      and not _under_excluded_dir(p, excluded)]
    shell_candidates = [p for p in tracked if _is_shell_test_filename(Path(p).name)
                         and not _under_excluded_dir(p, excluded)]

    collected = _collected_files()

    problems: list[str] = []

    missing = [p for p in py_candidates if p not in collected]
    genuinely_missing = [p for p in missing if _defines_any_test_item(p)]
    if genuinely_missing:
        problems.append(
            "test file(s) on disk with real test items are NOT collected by "
            f"`{' '.join(FULL_SUITE_COMMAND[:4])}`: {genuinely_missing} -- "
            "this is the test/-vs-tests/ shape (issue #3091): a file exists "
            "that the documented full-suite command silently skips.")

    if shell_candidates:
        problems.append(
            f"{len(shell_candidates)} shell test file(s) exist that "
            f"`python3 -m pytest` can never collect: {shell_candidates} -- "
            "running every test in the repo therefore requires a SECOND, "
            "separate command (`bash tests/run-orchestrate-tests.sh`, per "
            "docs/handbooks/on-the-record.md), so no single command "
            "currently suffices.")

    if problems:
        _fail(problems)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
