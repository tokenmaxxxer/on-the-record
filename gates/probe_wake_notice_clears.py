#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3120 (wake-notice half).

`on-the-record/hooks/directive.sh` writes `.orchestrate-wake-notice` in
the target workspace once the monitor's alive marker is stale past a
grace window (issue #947). Nothing removed it: `grep -rn
'orchestrate-wake-notice'` across the repo used to find only that write
and the directive text pointing at it -- the "alive" branch (the marker
IS fresh for this session) exited without clearing a notice left behind
by an earlier, monitor-late session in the same workspace. One
straggler session poisoned every later session's directive output in
that workspace permanently.

This probe drives the real `directive.sh` (unmodified, no monkeypatch)
as a subprocess, entirely inside a scratch HOME/checkout/workspace
triple so it never touches the operator's real
`~/.claude/tokenmaxxxer/monitor-alive/` state or this repo's own `runs/`
directory:

1. positive -- pre-plant a stale notice, make the alive marker fresh
   for the probing session, run the hook's check twice (first
   observation records session start; second, past a zero-length grace
   window, evaluates alive/stale), assert the notice is gone.
2. symmetric negative -- a separate scratch workspace with a genuinely
   absent alive marker still gets a notice written, unchanged.

Must fail against current main (the positive case: the notice survives
the alive branch). Cross-platform note: `_otr_mn_root` inside
directive.sh is bash's `pwd -P` (fully symlink-resolved) and its marker
path is `os.path.expanduser("~/...")` (a literal HOME-env substitution,
not fs-resolved) -- this probe resolves its own scratch dirs with
`os.path.realpath` up front and reuses those literal strings for both
the subprocess env and its own path-joins, so the hash/notice paths it
predicts match what the hook actually used on either Linux or macOS,
rather than assuming a bare `tempfile.mkdtemp()` string already is the
physical path (it is not on macOS, where `/tmp` is itself a symlink).

Run as `python3 gates/probe_wake_notice_clears.py` from the repo root,
no arguments. Prints `ok` and exits 0 on success; prints `FAIL` lines
and exits non-zero otherwise.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIRECTIVE_SH = REPO_ROOT / "on-the-record" / "hooks" / "directive.sh"

NOTICE_NAME = ".orchestrate-wake-notice"


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def _marker_dir(home_dir: str, workspace_root: str) -> str:
    digest = hashlib.sha256(
        workspace_root.encode("utf-8", "surrogatepass")
    ).hexdigest()[:24]
    return os.path.join(home_dir, ".claude", "tokenmaxxxer", "monitor-alive", digest)


def _run_directive(
    session_id: str,
    workspace_root: str,
    home_dir: str,
    checkout_dir: str,
    grace_seconds: str = "0",
) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["HOME"] = home_dir
    env["TOKENMAXXXER_CHECKOUT"] = checkout_dir
    env["MONITOR_NOTICE_GRACE_SECONDS"] = grace_seconds
    env.pop("ORCHESTRATE_OFF", None)
    env.pop("TOKENMAXXXER_SPAWNED", None)
    payload = json.dumps({"session_id": session_id}).encode("utf-8")
    return subprocess.run(
        ["bash", str(DIRECTIVE_SH)],
        input=payload,
        cwd=workspace_root,
        env=env,
        capture_output=True,
        timeout=30,
    )


def _new_scratch(prefix: str) -> str:
    # realpath up front: on macOS tempfile.mkdtemp() commonly lives under
    # /tmp, itself a symlink to /private/tmp -- resolving once here and
    # reusing the literal string everywhere keeps this probe's own path
    # predictions identical to what bash's `pwd -P` / Python's
    # os.path.expanduser will independently compute inside the hook.
    return os.path.realpath(tempfile.mkdtemp(prefix=prefix))


def _make_checkout() -> str:
    checkout_dir = _new_scratch("otr-wake-checkout-")
    # poll_rearm_resolve_checkout only probes for spawn.py's presence.
    Path(checkout_dir, "spawn.py").write_text("# probe stub\n")
    return checkout_dir


def check_positive_clears_stale_notice() -> None:
    workspace = _new_scratch("otr-wake-ws-pos-")
    home = _new_scratch("otr-wake-home-pos-")
    checkout = _make_checkout()
    session_id = "probe-wake-notice-positive"

    notice_path = os.path.join(workspace, NOTICE_NAME)
    with open(notice_path, "w") as f:
        f.write("stale notice left behind by an earlier, monitor-late session\n")
    if not os.path.exists(notice_path):
        _fail("setup: could not pre-plant the stale notice file")

    # First observation: directive.sh only records this session's start
    # time on the first call and exits before checking anything.
    first = _run_directive(session_id, workspace, home, checkout)
    if first.returncode not in (0, 2):
        _fail(
            "positive case, first (start-recording) invocation exited "
            f"rc={first.returncode}, stderr={first.stderr!r}"
        )

    marker_dir = _marker_dir(home, workspace)
    start_path = os.path.join(
        marker_dir,
        "." + "session-" + hashlib.sha256(
            session_id.encode("utf-8", "surrogatepass")
        ).hexdigest()[:24] + "-start",
    )
    if not os.path.exists(start_path):
        _fail(
            "setup: expected directive.sh's first invocation to record "
            f"a session-start marker at {start_path}, found none"
        )

    # Make the alive marker fresh for this session: touched strictly
    # after start_path was written, so its mtime is >= this session's
    # recorded start -- the exact "alive" condition the fix's removal
    # branch guards on.
    os.makedirs(marker_dir, exist_ok=True)
    alive_path = os.path.join(marker_dir, "alive")
    with open(alive_path, "w") as f:
        f.write("alive\n")
    if os.path.getmtime(alive_path) < os.path.getmtime(start_path):
        _fail("setup: alive marker mtime landed before session start mtime")

    second = _run_directive(session_id, workspace, home, checkout)
    if second.returncode not in (0, 2):
        _fail(
            "positive case, second (check) invocation exited "
            f"rc={second.returncode}, stderr={second.stderr!r}"
        )

    if os.path.exists(notice_path):
        _fail(
            "positive case: stale .orchestrate-wake-notice survived a "
            "directive.sh check where the alive marker is fresh for this "
            "session -- the alive branch must clear an existing notice"
        )

    shutil.rmtree(workspace, ignore_errors=True)
    shutil.rmtree(home, ignore_errors=True)
    shutil.rmtree(checkout, ignore_errors=True)


def check_negative_absent_monitor_still_notifies() -> None:
    workspace = _new_scratch("otr-wake-ws-neg-")
    home = _new_scratch("otr-wake-home-neg-")
    checkout = _make_checkout()
    session_id = "probe-wake-notice-negative"

    notice_path = os.path.join(workspace, NOTICE_NAME)
    if os.path.exists(notice_path):
        _fail("setup: fresh scratch workspace already has a notice file")

    first = _run_directive(session_id, workspace, home, checkout)
    if first.returncode not in (0, 2):
        _fail(
            "negative case, first (start-recording) invocation exited "
            f"rc={first.returncode}, stderr={first.stderr!r}"
        )

    marker_dir = _marker_dir(home, workspace)
    alive_path = os.path.join(marker_dir, "alive")
    if os.path.exists(alive_path):
        _fail("setup: negative case scratch workspace unexpectedly has an alive marker")

    second = _run_directive(session_id, workspace, home, checkout)
    if second.returncode not in (0, 2):
        _fail(
            "negative case, second (check) invocation exited "
            f"rc={second.returncode}, stderr={second.stderr!r}"
        )

    if not os.path.exists(notice_path):
        _fail(
            "negative case: a genuinely absent monitor (no alive marker "
            "at all) did not get .orchestrate-wake-notice written -- the "
            "removal fix must not have broken the original write path"
        )
    body = Path(notice_path).read_text()
    if "idle self-wake is unavailable" not in body:
        _fail(f"negative case: notice file has unexpected content: {body!r}")

    shutil.rmtree(workspace, ignore_errors=True)
    shutil.rmtree(home, ignore_errors=True)
    shutil.rmtree(checkout, ignore_errors=True)


def main() -> None:
    if not DIRECTIVE_SH.is_file():
        _fail(f"directive.sh not found at {DIRECTIVE_SH}")
    if shutil.which("bash") is None:
        _fail("bash not found on PATH -- required to run directive.sh")

    check_positive_clears_stale_notice()
    print("ok: stale wake-notice cleared once the alive marker is fresh")

    check_negative_absent_monitor_still_notifies()
    print("ok: genuinely absent monitor still gets a notice written")

    print("ok")


if __name__ == "__main__":
    main()
