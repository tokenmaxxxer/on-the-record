#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3091.

Asserts the property whose absence let 15 `test/` failures sit
unobserved while `tests/` alone was called green: every test file in the
repo is *accounted for* by a known, documented command, and no test file
can silently exist outside that account. This probe checks that claim
two ways, mechanically, never by scraping prose:

1. Every git-tracked `test_*.py`/`*_test.py` file that actually defines
   at least one collectible test item (a module matching the naming
   convention but defining zero tests, e.g. a parser library merely
   named `test_*.py`, does not count -- `pytest` reports "no tests
   collected" for it either way, so it was never hidden) must appear in
   `python3 -m pytest -q --collect-only`'s own collected-file set. A
   file present on disk but absent from that set is exactly the
   `test/`-vs-`tests/` shape this issue exists to catch.
2. Every git-tracked `*.sh` file living anywhere under `tests/`, at any
   depth (pytest can never collect a shell script) must be a KEY in
   `KNOWN_SHELL_TEST_COMMANDS` below, the command that runs it. A file
   in that position that is NOT a key is exactly the same
   silently-unobserved shape as (1), just in shell instead of Python.

Design decision (issue #3091 follow-up, recorded in
docs/issue-3091/reports/implementation-blueprint+test-derivation+silent-failure-audit-a7dcf475.md):
this probe does NOT require a single command to run the whole suite.
`tests/run-orchestrate-tests.sh`, `tests/test_stop_gate.sh`,
`tests/check-write-set-conflicts.test.sh` and
`tests/claim-scan-preflight.test.sh` are real, independent shell test
suites, each already exercising a hook end-to-end via subprocess/env
manipulation (`env -u CLAUDE_SKILL`, `env -u TOKENMAXXXER_SPAWNED`,
`mktemp`-rooted fixtures) that a thin pytest subprocess wrapper would
either duplicate or paper over. Forcing them into `pytest -q` (by
wrapping each in a `def test_x(): subprocess.run(...)` shim) or building
a combined runner script would make the probe report a single green
command while still not being the actual thing anyone runs by hand --
recreating, one layer down, the exact "looks complete but isn't" shape
issue #3091 diagnosed in `test/` vs `tests/`. The honest fix available
today is a registry: name every shell test file that exists, the exact
command that runs it, and fail loudly the moment a new one appears
without being added here. `docs/handbooks/operations.md` documents this
same list for humans (search "issue #3091").

Must fail against the tree as of issue #3091's first PR (#3111): at that
point neither shell file was in any registry, because there was no
registry -- only a bare existence check. This revision changes the shape
of the check (registry + drift detection) but not its stakes: an
unregistered shell test file still fails the probe.

Run as `python3 gates/probe_full_suite_is_one_command.py` from anywhere;
it resolves the repo root itself. Prints `ok` and exits 0 only when
every test file in the repo -- Python and shell alike -- is accounted
for by a known command; otherwise prints each violation to stderr and
exits non-zero.
"""
from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PY_TEST_FILE_SUFFIXES = ("_test.py",)

# Every `.sh` file that lives anywhere under `tests/` and is a real test
# suite (not a helper sourced by one), mapped to the exact command that
# runs it. `docs/handbooks/operations.md` ("issue #3091" section)
# documents this same list for humans. Add a new entry here in the same
# commit that adds the file, or this probe fails on purpose.
KNOWN_SHELL_TEST_COMMANDS: dict[str, str] = {
    "tests/run-orchestrate-tests.sh": "bash tests/run-orchestrate-tests.sh",
    "tests/test_stop_gate.sh": "bash tests/test_stop_gate.sh",
    "tests/check-write-set-conflicts.test.sh": "bash tests/check-write-set-conflicts.test.sh",
    "tests/claim-scan-preflight.test.sh": "bash tests/claim-scan-preflight.test.sh",
}

FULL_SUITE_COMMAND = [sys.executable, "-m", "pytest", "-q", "--collect-only", "-q"]
# per docs/handbooks/operations.md: "Run python3 -m pytest -q with no
# ignore flag" -- the documented Python full-suite invocation. It is not
# the *only* command required (see KNOWN_SHELL_TEST_COMMANDS above); it
# is the one this probe can mechanically verify collects every Python
# test file.


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


def _is_shell_test_candidate(relpath: str) -> bool:
    p = Path(relpath)
    # Anywhere under tests/, any depth -- not just direct children. A
    # shell test nested in a subdirectory (tests/subdir/x.test.sh) is
    # exactly as real and exactly as invisible to pytest as one sitting
    # directly in tests/; restricting to direct children would silently
    # exempt it (issue #3091 warrant-hunt finding, before-landing).
    return Path("tests") in p.parents and p.name.endswith(".sh")


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
    shell_candidates = [p for p in tracked if _is_shell_test_candidate(p)
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

    unregistered = [p for p in shell_candidates if p not in KNOWN_SHELL_TEST_COMMANDS]
    if unregistered:
        problems.append(
            f"{len(unregistered)} shell test file(s) exist under "
            f"`tests/` that are NOT in this probe's KNOWN_SHELL_TEST_COMMANDS "
            f"registry: {unregistered} -- pytest can never collect a shell "
            "script, so a file in this position with no registered command "
            "is exactly the same silently-unobserved shape issue #3091 "
            "diagnosed in test/ vs tests/. Add an entry (file, command) to "
            "KNOWN_SHELL_TEST_COMMANDS in this probe and to "
            "docs/handbooks/operations.md's \"issue #3091\" section in the "
            "same commit that adds the file.")

    if problems:
        _fail(problems)

    registered_present = sorted(p for p in shell_candidates if p in KNOWN_SHELL_TEST_COMMANDS)
    commands = ["python3 -m pytest -q"]
    commands += [KNOWN_SHELL_TEST_COMMANDS[p] for p in registered_present]
    print(
        "ok: every test file in the repo is accounted for by a known "
        f"command. Running all of them still takes {len(commands)} "
        f"commands, not one: " + "; ".join(f"`{c}`" for c in commands) +
        " -- see docs/handbooks/operations.md's \"issue #3091\" section."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
