#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3095.

Exists so the leak can be stated as a plain `check:` line (`python3
gates/probe_parked_report_repo_leak.py`) instead of a shell one-liner --
same convention as `probe_drift_repo_leak.py` (issue #3081).

`gates/spawn_on_pr.py`'s park state (`spawn_on_pr_parked.json`) is one file
shared across every repo an orchestrator sweeps -- correct per issue #2240,
untouched by this probe. The defect (identical in shape to #3081's
requirement-drift cache leak) is that `parked_report()` returned every
`parked=True` entry in the file with no per-repo filter, so a subject
parked while sweeping one repo printed as `waiting-for-human` on a
different repo's report too, even naming a subject/issue that repo doesn't
have.

This probe drives the real entrypoint (`spawn_on_pr.spawn_missing_for_pr`,
the same function `watchdog.py`'s board-sweep calls every tick) with the
gh/git/spawn boundaries monkeypatched out, to genuinely park a subject
under two distinct repos, then checks `parked_report()`:

- called against two different roots, must not return byte-identical
  output (the tightest available signal that no per-repo filtering runs at
  all -- same rationale #3081's probe used), and
- each root's own genuine parked subject must still be reported (a fix
  must not pass this probe by suppressing all output), and
- the retention split: a subject already parked under this repo's own
  attribution stays parked on a further tick (retained), while a
  same-named subject whose only park-state entry belongs to a *different*
  repo is not inherited -- it is evicted and spawns fresh instead of
  silently staying parked on another repo's history.

Run as `python3 gates/probe_parked_report_repo_leak.py` from the repo
root, no arguments, no network (`gh`/spawn boundaries are mocked). Prints
`ok` and exits 0 on success; prints a message to stderr and exits non-zero
otherwise.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gates"))
sys.path.insert(0, str(ROOT))

import spawn  # noqa: E402
import spawn_on_pr  # noqa: E402

REPO_A = "octo/on-the-record"
REPO_B = "octo/study-companion"

# issue #3095's live repro: a consumer working their own repo saw
# `spawn-on-pr: waiting-for-human 1건: ['issue-3059']` -- issue-3059
# belongs to the plugin repo and was already closed there. Same subject
# name (`issue-<n>`, repo-local issue numbers), two different repos.
SUBJECT = "issue-3059"


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def _wire(monkeypatch_ctx, root: Path, park_path: Path, *, missing: dict,
          blocked: bool):
    """Monkeypatch every gh/git/spawn boundary spawn_missing_for_pr()
    touches (same idiom as gates/test_spawn_on_pr.py's `_wire` fixture),
    while leaving the park/ceiling/repo-attribution logic itself real.

    `_park_state_path` is deliberately NOT scoped here -- callers must
    keep it patched for as long as they also call `parked_report()`
    afterwards, or a closed context would silently fall back to this
    process's real, shared state file."""
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr, "missing_verification",
                           lambda r, issue_states=None, pr_index=None: dict(missing)))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr, "subject_deliverable_branch",
                           lambda r, subject, pr_index: f"{subject}/impl"))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr, "_pr_number_for_branch",
                           lambda r, branch, pr_index: 1))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr, "resolve_live_base", lambda r: "deadbeef"))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr, "is_approval_blocked",
                           lambda r, issue, skill: blocked))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr.spawn, "roster_register", lambda *a, **k: None))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr.spawn, "_spawn_one", lambda *a, **k: None))
    monkeypatch_ctx.enter_context(
        mock.patch.object(spawn_on_pr.spawn, "ledger_write", lambda entry: None))


def main() -> None:
    from contextlib import ExitStack

    tmp = Path(tempfile.mkdtemp(prefix="probe-parked-report-repo-leak-"))
    try:
        root_a = tmp / "repo-a"
        root_b = tmp / "repo-b"
        root_a.mkdir()
        root_b.mkdir()
        park_path = tmp / "spawn_on_pr_parked.json"  # one shared file, issue #2240

        def fake_repo_slug(root: Path) -> str:
            return REPO_A if root == root_a else REPO_B

        # `_repo_slug`/`_park_state_path` stay patched for the whole probe
        # body -- letting either fall back to the real implementation
        # between calls would silently read/write this process's actual
        # shared state file instead of the probe's isolated tmp copy.
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(spawn, "_repo_slug",
                                                    side_effect=fake_repo_slug))
            stack.enter_context(
                mock.patch.object(spawn_on_pr, "_park_state_path", lambda r: park_path))

            # Tick 1: repo A parks SUBJECT (still blocked -- no approval
            # comment yet). Seed an already-blocked-and-parked prior
            # directly (mirrors gates/test_spawn_on_pr.py's seeding idiom)
            # so this tick's recheck exercises the real park/retain path,
            # not the first-candidate-always-spawns path.
            park_path.write_text(json.dumps({
                SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                          "attempts": 1, "repo": REPO_A},
            }))
            with ExitStack() as wire_a:
                _wire(wire_a, root_a, park_path, missing={SUBJECT: 1}, blocked=True)
                spawn_on_pr.spawn_missing_for_pr(
                    root_a, cwd=str(root_a), dry_run=False,
                    backoff_state={"sweeps": {}, "recheck": {}})

            out_a = spawn_on_pr.parked_report(root_a)
            out_b = spawn_on_pr.parked_report(root_b)

            if out_a == out_b:
                _fail(
                    "parked_report(root_a) and parked_report(root_b) are "
                    f"identical ({out_a!r}) -- no per-repo filter is "
                    "running at all (issue #3095).")

            if SUBJECT not in out_a:
                _fail(
                    f"repo A's own genuine parked subject {SUBJECT!r} did "
                    "not appear in repo A's own report -- a fix that "
                    "suppresses all output must not pass this probe. Got: "
                    f"{out_a!r}")

            if SUBJECT in out_b:
                _fail(
                    f"repo A's parked subject {SUBJECT!r} leaked into "
                    f"repo B's report, which never parked it: {out_b!r}. "
                    "This is the issue #3095 defect: 'spawn-on-pr: "
                    f"waiting-for-human 1건: [{SUBJECT!r}]' printed on a "
                    "repo where that subject does not exist.")

            # --- retention split -----------------------------------------
            # Own-repo entry: still blocked on a further tick -> stays
            # parked (retained). Cross-repo entry (same subject name, a
            # different repo's park history): must NOT be inherited -- it
            # evicts, and this tick's own repo treats it as a fresh
            # candidate and spawns.
            park_path.write_text(json.dumps({
                SUBJECT: {"blocked": True, "pr_number": 1, "parked": True,
                          "attempts": 1, "repo": REPO_B},
            }))
            with ExitStack() as wire_a2:
                _wire(wire_a2, root_a, park_path, missing={SUBJECT: 1}, blocked=True)
                spawned = spawn_on_pr.spawn_missing_for_pr(
                    root_a, cwd=str(root_a), dry_run=True,
                    backoff_state={"sweeps": {}, "recheck": {}})

            if not spawned:
                _fail(
                    "repo A inherited repo B's park/attempts history for "
                    f"the same-named subject {SUBJECT!r} instead of "
                    "evicting it -- a cross-repo entry must not be "
                    "treated as this repo's own genuine prior (issue "
                    "#3095 retention split).")

            still_b = spawn_on_pr.parked_report(root_b)
            if SUBJECT not in still_b:
                _fail(
                    f"repo B's own park-state entry for {SUBJECT!r} was "
                    f"lost or evicted by repo A's unrelated tick: "
                    f"{still_b!r} -- an own-repo transient park state "
                    "must retain, only a *foreign* repo's entry should "
                    "ever evict.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
