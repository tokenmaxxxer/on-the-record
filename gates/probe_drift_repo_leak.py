#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3081.

Exists so the leak can be stated as a plain `check:` line
(`python3 gates/probe_drift_repo_leak.py`) instead of a shell one-liner.

`watchdog.requirement_drift`'s cache (`requirement_drift_cache.json`) is one
file shared across every repo an orchestrator sweeps -- correct per issue
#2240, and this probe does not touch that anchoring. The defect is that a
sweep read the whole file back without checking whose entries they were,
and the issue's 5th comment established this is bidirectional: with no
per-repo filter at report time, every sweep prints the whole cache under
its own prefix, so two repos sharing a cache converge on printing the
identical union of every repo's numbers -- not just one repo's numbers
leaking into the other's report.

This probe seeds the shared cache with entries from two distinct repos (via
two real `requirement_drift` sweeps, not hand-written JSON, so it exercises
the same write path production code uses), then does one more delta-mode
sweep per repo with an empty `changed_numbers` (so the sweep runs entirely
off the reuse pass -- no fresh fetch of its own) and checks:

- neither repo's output contains the other repo's numbers (the leak, both
  directions), and
- each repo's own genuine drift entry still appears in its own output (the
  symmetric negative -- a fix must not pass this probe by suppressing all
  output), and
- the two repos' outputs are not identical (per the issue's 5th comment:
  an identical-output pair is the tightest available signal that no
  per-repo filtering is happening at all -- a looser assertion could pass
  on a filter that is merely too permissive without ever detecting that no
  filter runs).

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
# into a study-companion sweep, and the 5th comment showed the reverse
# direction too (a study-companion PR leaking into on-the-record's board).
# Same shape, distinct numbers so a probe failure is unambiguous about
# which repo's data leaked which way.
REPO_A_NUMBERS = {3048, 3051}
REPO_B_NUMBERS = {77}


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def _item(number: int, body: str = "cites nothing") -> dict:
    return {"number": number, "title": "", "body": body, "state": "open"}


def _write_digest(root: Path) -> None:
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "docs" / "specs" / "requirement-digest.md").write_text(
        "- R001: something [open] (source: #1)\n")


def _sweep(root: Path, numbers: set[int]) -> None:
    """Seed `root`'s repo entries via a real delta-mode sweep that fetches
    each of `numbers` successfully, same write path production code uses."""
    with mock.patch.object(
            spawn, "_fetch_issue_or_pr_via_cache",
            side_effect=lambda _root, n: _item(n)):
        with redirect_stdout(StringIO()):
            spawn.requirement_drift(root, changed_numbers=set(numbers))


def _reuse_only_sweep(root: Path) -> str:
    """A delta-mode sweep with nothing changed of its own -- every item in
    its output can only have come from the reuse pass reading the shared
    cache back, which is exactly the report-time filter under test."""
    buf = StringIO()
    with redirect_stdout(buf):
        spawn.requirement_drift(root, changed_numbers=set())
    return buf.getvalue()


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
            _sweep(root_a, REPO_A_NUMBERS)
            _sweep(root_b, REPO_B_NUMBERS)

            out_a = _reuse_only_sweep(root_a)
            out_b = _reuse_only_sweep(root_b)

        for leaked in REPO_B_NUMBERS:
            if str(leaked) in out_a:
                _fail(
                    f"repo B's number {leaked} appeared in repo A's sweep "
                    f"output -- a cache entry leaked across repos without "
                    f"attribution (issue #3081). Full output:\n{out_a}")
        for leaked in REPO_A_NUMBERS:
            if str(leaked) in out_b:
                _fail(
                    f"repo A's number {leaked} appeared in repo B's sweep "
                    f"output -- a cache entry leaked across repos without "
                    f"attribution (issue #3081). Full output:\n{out_b}")

        for own in REPO_A_NUMBERS:
            if str(own) not in out_a:
                _fail(
                    f"repo A's own genuine open, uncited PR {own} did not "
                    "appear in repo A's sweep output -- a fix that "
                    "suppresses all output (instead of filtering by repo) "
                    f"must not pass this probe. Full output:\n{out_a}")
        for own in REPO_B_NUMBERS:
            if str(own) not in out_b:
                _fail(
                    f"repo B's own genuine open, uncited PR {own} did not "
                    "appear in repo B's sweep output -- a fix that "
                    "suppresses all output (instead of filtering by repo) "
                    f"must not pass this probe. Full output:\n{out_b}")

        # issue #3081, 5th comment: the tightest available signal that no
        # per-repo filtering is happening at all is that both boards print
        # the identical union of every repo's numbers -- assert the two
        # repos' outputs are not identical, not just that each one
        # individually looks plausible.
        if out_a == out_b:
            _fail(
                "repo A's and repo B's sweep outputs are byte-identical -- "
                "each board is printing the same union of every repo's "
                "cache entries instead of its own. Output:\n" + out_a)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
