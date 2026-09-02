#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3081.

Exists so the leak can be stated as a plain `check:` line
(`python3 gates/probe_drift_repo_leak.py`) instead of a shell one-liner.

`watchdog.requirement_drift`'s cache (`requirement_drift_cache.json`) is one
file shared across every repo an orchestrator sweeps -- correct per issue
#2240, and this probe does not touch that anchoring. The defect is that a
sweep read the whole file back without checking whose entries they were: a
delta-mode sweep of repo B's board would pull repo A's cached, uncited
issues/PRs into repo B's report, printed under repo B's prefix as if they
were repo B's own open items.

This probe seeds the shared cache with entries from two distinct repos (via
two real `requirement_drift` sweeps, not hand-written JSON, so it exercises
the same write path production code uses), then sweeps only one of them and
checks two things:

- the other repo's numbers appear nowhere in the swept repo's output
  (the leak), and
- the swept repo's own genuine drift entry still appears (the symmetric
  negative -- a fix must not pass this probe by suppressing all output).

Run as `python3 gates/probe_drift_repo_leak.py` from the repo root, no
arguments, no network (`gh` calls are mocked out). Prints `ok` and exits 0
on success; prints a message to stderr and exits non-zero otherwise.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
sys.path.insert(0, str(ROOT))

import state_paths  # noqa: E402
import spawn  # noqa: E402
import watchdog  # noqa: E402

watchdog._sp = spawn

REPO_A = "octo/on-the-record"
REPO_B = "octo/study-companion"

# issue #3081's live repro: on-the-record PRs 3048/3051/3056/3058 leaked
# into a study-companion sweep. Same shape, distinct numbers so a probe
# failure is unambiguous about which repo's data leaked.
REPO_A_NUMBERS = {3048, 3051}
REPO_B_OWN_NUMBER = 77


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def _item(number: int, body: str = "cites nothing") -> dict:
    return {"number": number, "title": "", "body": body, "state": "open"}


def _write_digest(root: Path) -> None:
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "docs" / "specs" / "requirement-digest.md").write_text(
        "- R001: something [open] (source: #1)\n")


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="probe-drift-repo-leak-"))
    try:
        root_a = tmp / "repo-a"
        root_b = tmp / "repo-b"
        _write_digest(root_a)
        _write_digest(root_b)

        def fake_repo_slug(root: Path) -> str:
            return REPO_A if root == root_a else REPO_B

        with mock.patch.object(state_paths, "STATE_ROOT", tmp / "state"), \
             mock.patch.object(spawn, "_repo_slug", side_effect=fake_repo_slug):
            # Seed repo A's entries the same way a real orchestrator tick
            # would -- a delta-mode sweep of repo A that fetches its own
            # open, uncited PRs successfully.
            with mock.patch.object(
                    spawn, "_fetch_issue_or_pr_via_cache",
                    side_effect=lambda root, n: _item(n)):
                with redirect_stdout(StringIO()):
                    spawn.requirement_drift(root_a, changed_numbers=set(REPO_A_NUMBERS))

            # Now sweep repo B. Its own `changed_numbers` never mentions
            # repo A's numbers at all -- if they leak into this sweep's
            # output, it is only because the reuse pass read repo A's
            # cache entries back without checking whose they were.
            with mock.patch.object(
                    spawn, "_fetch_issue_or_pr_via_cache",
                    side_effect=lambda root, n: _item(REPO_B_OWN_NUMBER)):
                buf = StringIO()
                with redirect_stdout(buf):
                    spawn.requirement_drift(root_b, changed_numbers={REPO_B_OWN_NUMBER})
                out = buf.getvalue()

        for leaked in REPO_A_NUMBERS:
            if str(leaked) in out:
                _fail(
                    f"repo A's number {leaked} appeared in repo B's sweep "
                    f"output -- a cache entry leaked across repos without "
                    f"attribution (issue #3081). Full output:\n{out}")

        if str(REPO_B_OWN_NUMBER) not in out:
            _fail(
                "repo B's own genuine open, uncited PR "
                f"{REPO_B_OWN_NUMBER} did not appear in repo B's sweep "
                "output -- a fix that suppresses all output (instead of "
                "filtering by repo) must not pass this probe. Full "
                f"output:\n{out}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
