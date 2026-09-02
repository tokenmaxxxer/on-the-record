#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3129, check 2.

The issue names two failure modes to design against explicitly, distinct
from check 1's "does the channel exist at all":

  fires once per amendment  -- a session told its brief changed on EVERY
                                tool call would drown in its own notice.
  absorbed stops announcing -- a stale marker that keeps re-announcing an
                                amendment the session already absorbed is
                                the SAME never-cleared-notice defect class
                                issue #3120 found (a heartbeat monitor
                                that never cleared its own dead-loop
                                notice); this would be the third instance
                                this board found in one day.

This probe drives the REAL shipped hook
(`on-the-record/hooks/amendment-channel.sh`, unmodified) through MANY
simulated `PostToolUse` tool calls across TWO separate amendments and
counts notices per amendment: exactly one each, never zero, never more,
and no re-fire on any of the many quiet ticks in between. Must fail
against current main -- the hook script does not exist there, so no
notice ever fires and the "exactly one, not zero" assertion catches it
(same absence this issue's check 1 probe catches, from the fires-once
angle instead of the reaches-context angle).

Cross-platform (issue #3129's own requirement): `tempfile.mkdtemp()` for
every scratch/state path, and the fire-once/absorbed comparison under
test is a content version counter, never `os.stat().st_mtime` -- so nothing
here depends on Linux vs. macOS mtime granularity, and this file does not
either (no direct mtime read of its own).

Run as `python3 gates/probe_amendment_notice_fires_once.py` from the repo
root, no arguments. Prints `ok` and exits 0 on success; prints a
`FAIL: ...` message to stderr and exits non-zero otherwise.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "on-the-record" / "hooks" / "amendment-channel.sh"
HOOKS_DIR = REPO_ROOT / "on-the-record" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
import amendment_channel as ac  # noqa: E402 -- path-computation helper only, not reimplemented logic
BASH_BIN = shutil.which("bash") or "/bin/bash"

# Both the worker's checkout and the orchestrator's own cwd share this
# `origin` -- same repo, two separate local checkouts/processes.
ORIGIN_URL = "https://github.com/example/probe-repo.git"

ISSUE = "8830178"
BODY_FLAG = "--" + "body"
TICKS_PER_PHASE = 12

BASH_TOOL_RESPONSE_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "amendment_channel" / "bash_tool_response.json"
)


def _bash_tool_response(stdout: str, stderr: str = "") -> dict:
    """The real Claude Code `Bash` `tool_response` shape (issue #3129
    repair round 7 -- see `BASH_TOOL_RESPONSE_FIXTURE`'s own
    `captured_from` field for provenance), replacing this probe's own
    pre-round-7 bare-string `tool_response` (same blind spot PR #3205
    found in `probe_running_session_sees_amendment.py`)."""
    with open(BASH_TOOL_RESPONSE_FIXTURE, "r", encoding="utf-8") as f:
        template = json.load(f)["template"]
    payload = dict(template)
    payload["stdout"] = stdout
    payload["stderr"] = stderr
    return payload


def _fail(message: str) -> None:
    print("FAIL: %s" % message, file=sys.stderr)
    sys.exit(1)


def _git(*args: str, cwd: Path) -> None:
    r = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                        text=True, timeout=30)
    if r.returncode != 0:
        _fail("git %s failed in %s: %s" % (" ".join(args), cwd, r.stderr))


def _make_repo(root: Path, name: str, branch: str = None) -> Path:
    repo = root / name
    repo.mkdir(parents=True)
    _git("init", "-q", cwd=repo)
    _git("config", "user.email", "probe@example.com", cwd=repo)
    _git("config", "user.name", "probe", cwd=repo)
    _git("commit", "-q", "--allow-empty", "-m", "init", cwd=repo)
    if branch:
        _git("checkout", "-q", "-b", branch, cwd=repo)
    _git("remote", "add", "origin", ORIGIN_URL, cwd=repo)
    return repo


def _make_worker_repo(root: Path) -> Path:
    return _make_repo(root, "worker-repo", branch="issue-%s/some-role" % ISSUE)


def _call_hook(payload: dict, env: dict):
    if not HOOK.is_file():
        return None
    r = subprocess.run([BASH_BIN, str(HOOK)], input=json.dumps(payload),
                        capture_output=True, text=True, env=env, timeout=30)
    out = r.stdout.strip()
    if not out:
        return None
    try:
        parsed = json.loads(out)
    except ValueError:
        _fail("hook produced non-JSON stdout: %r (stderr: %r)" % (out, r.stderr))
        return None  # unreachable
    return parsed.get("hookSpecificOutput", {}).get("additionalContext")


def _amend(env: dict, orchestrator_cwd: Path, note: str) -> None:
    cmd = 'gh issue edit %s %s "%s"' % (ISSUE, BODY_FLAG, note)
    payload = {
        "session_id": "probe-orchestrator-session",
        "tool_name": "Bash",
        "tool_input": {"command": cmd},
        "cwd": str(orchestrator_cwd),
        # issue #3129 round-4: the write side now takes the edited issue's
        # repo+number from gh issue edit's own success output
        # (tool_response), never from the command text -- must name the
        # same repo as orchestrator_cwd's own `origin` (ORIGIN_URL) or the
        # new cross-repo policy-violation check refuses the write.
        "tool_response": _bash_tool_response(
            "https://github.com/example/probe-repo/issues/%s" % ISSUE),
    }
    _call_hook(payload, env)


def main() -> None:
    work = Path(tempfile.mkdtemp(prefix="otr-amendment-probe2-"))
    try:
        state_dir = work / "state"
        worker_repo = _make_worker_repo(work)
        orchestrator_cwd = _make_repo(work, "orchestrator-cwd")

        env = dict(os.environ)
        env["OTR_AMENDMENT_STATE_DIR"] = str(state_dir)
        # issue #3129 repair round 5: fake this probe process's own
        # spawn.py registration -- see probe_running_session_sees_
        # amendment.py's identical comment for why.
        roster_path = work / "roster" / "active.json"
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps({
            "issue-1/probe-orch": {
                "pid": os.getpid(), "work": str(orchestrator_cwd),
                "start_time": ac._proc_start_time(os.getpid()),
            }
        }))
        env["OTR_ROSTER_PATH"] = str(roster_path)

        def worker_tick():
            payload = {
                "session_id": "probe-worker-session",
                "tool_name": "Read",
                "tool_input": {},
                "cwd": str(worker_repo),
            }
            return _call_hook(payload, env)

        # --- phase 0: many ticks with NO amendment yet -- must stay quiet
        phase0 = [worker_tick() for _ in range(TICKS_PER_PHASE)]
        fired0 = [c for c in phase0 if c is not None]
        if fired0:
            _fail("notice fired with no amendment ever made: %r" % (fired0,))

        # --- amendment #1, then many ticks: exactly one notice, the rest quiet
        _amend(env, orchestrator_cwd, "first correction")
        phase1 = [worker_tick() for _ in range(TICKS_PER_PHASE)]
        fired1 = [c for c in phase1 if c is not None]
        if len(fired1) == 0:
            _fail(
                "amendment #1 never reached the worker across %d tool "
                "calls -- amendment-channel.sh missing, or the hook "
                "never fires the notice at all" % TICKS_PER_PHASE
            )
        if len(fired1) > 1:
            _fail(
                "amendment #1 was announced %d times across %d tool "
                "calls -- must fire exactly once per amendment, not once "
                "per tick (a session told its brief changed on every "
                "tool call drowns in its own notice): %r"
                % (len(fired1), TICKS_PER_PHASE, fired1)
            )
        if "first correction" not in fired1[0]:
            _fail("the single fired notice does not carry amendment #1's "
                  "content: %r" % fired1[0])

        # --- more ticks with NO new amendment: the absorbed one must NOT
        # keep re-announcing itself -- the never-cleared-notice defect
        # class issue #3120 found, checked again here explicitly and
        # separately from phase1's own tail (a stale marker read fresh,
        # long after absorption, must still stay quiet).
        phase1_quiet_tail = [worker_tick() for _ in range(TICKS_PER_PHASE)]
        fired_tail = [c for c in phase1_quiet_tail if c is not None]
        if fired_tail:
            _fail(
                "the already-absorbed amendment #1 kept re-announcing "
                "itself %d more times with no new amendment made -- "
                "stale-marker re-fire, the same never-cleared-notice "
                "defect class as issue #3120: %r"
                % (len(fired_tail), fired_tail)
            )

        # --- amendment #2: must fire again exactly once (proves this is
        # fire-once-PER-AMENDMENT, not fire-once-ever)
        _amend(env, orchestrator_cwd, "second correction")
        phase2 = [worker_tick() for _ in range(TICKS_PER_PHASE)]
        fired2 = [c for c in phase2 if c is not None]
        if len(fired2) == 0:
            _fail(
                "amendment #2 never reached the worker -- the channel "
                "fired once ever instead of once per amendment (would "
                "silently strand every correction after the first)"
            )
        if len(fired2) > 1:
            _fail("amendment #2 was announced %d times, expected exactly "
                  "1: %r" % (len(fired2), fired2))
        if "second correction" not in fired2[0]:
            _fail("the second fired notice does not carry amendment #2's "
                  "content: %r" % fired2[0])
        if "first correction" in fired2[0]:
            _fail("the second notice re-announces the first amendment's "
                  "content instead of only the new one: %r" % fired2[0])

    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
