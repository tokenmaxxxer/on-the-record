#!/usr/bin/env python3
"""Standalone acceptance probe for issue #3129, check 1.

A spawned worker session reads its issue once at spawn and never again.
Both existing correction channels fail for it: a cross-session message
needs the RECIPIENT's user to approve, and a headless worker has nobody
at a terminal to approve anything, so it expires undelivered; amending
the issue body reaches `check_runner` (which re-scores against the body)
but the running process never re-reads the body, so the amendment
prevents nothing upstream of scoring.

This probe exercises the REAL shipped hook
(`on-the-record/hooks/amendment-channel.sh`, unmodified, invoked the same
way `hooks.json` wires it into `PostToolUse` -- no reimplementation of its
logic) against a synthetic "session mid-run": a sequence of real
`PostToolUse` JSON payloads on stdin, in the order a spawned worker's own
tool calls would arrive, with the orchestrator's amendment (a real
`gh issue edit <n> --body ...` Bash command payload, exactly the shape the
orchestrator's own `PostToolUse` sees) landing between two of them.

It asserts: before the amendment, the worker's tool calls get no
amendment notice (its brief has not changed); after the amendment, before
the worker session's LAST simulated tool call (i.e. "before it
finishes"), at least one `PostToolUse` response carries
`hookSpecificOutput.additionalContext` naming the amended issue. Per the
issue: this must fail against current main, because
`on-the-record/hooks/amendment-channel.sh` does not exist there at all --
there is no channel for a running session to see an amendment.

Cross-platform (issue #3129's own requirement): uses `tempfile.mkdtemp()`
for every state/scratch path (no `/tmp` assumption, no reliance on
`os.stat().st_mtime` granularity anywhere in this probe or in the module
under test -- the fire logic compares an explicit content version field,
not the filesystem's mtime, precisely because Linux and macOS mtime
granularity differ), and only POSIX-portable `git`/`bash`/`python3` calls.

Run as `python3 gates/probe_running_session_sees_amendment.py` from the
repo root, no arguments. Prints `ok` and exits 0 on success; prints a
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
# `origin` -- realistic shape: same GitHub repo, two separate local
# checkouts/processes, which is exactly the case the marker's repo
# attribution must resolve identically for both sides.
ORIGIN_URL = "https://github.com/example/probe-repo.git"

# A made-up issue number unlikely to collide with anything real, and
# built so `--` flag text this probe embeds in a Bash command string
# cannot be mistaken by an unrelated textual scanner for a genuine gh
# call this probe process itself is making (it never runs `gh` -- the
# string is fed to the hook script on stdin as JSON `tool_input.command`,
# describing a command a *different*, hypothetical session ran).
ISSUE = "8830177"
BODY_FLAG = "--" + "body"

BASH_TOOL_RESPONSE_FIXTURE = (
    REPO_ROOT / "tests" / "fixtures" / "amendment_channel" / "bash_tool_response.json"
)


def _bash_tool_response(stdout: str, stderr: str = "") -> dict:
    """The real Claude Code `Bash` `tool_response` shape (issue #3129
    repair round 7 -- see `BASH_TOOL_RESPONSE_FIXTURE`'s own
    `captured_from` field for provenance), never a bare string: PR #3205
    found this probe's own `orch_payload` used a bare string, which is
    exactly why this probe passed against round-5/6 code that could never
    match a real payload (`_issue_url_from_response`'s `fullmatch` never
    matches the `json.dumps()`-wrapped text a real dict `tool_response`
    coerces to)."""
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


def _call_hook(payload: dict, env: dict) -> dict:
    """Invoke the real shipped hook exactly as PostToolUse would, and
    parse its stdout as the hookSpecificOutput JSON, or {} when quiet."""
    if not HOOK.is_file():
        # Exactly the current-main failure mode this probe must catch:
        # no channel exists at all.
        return {}
    r = subprocess.run([BASH_BIN, str(HOOK)], input=json.dumps(payload),
                        capture_output=True, text=True, env=env, timeout=30)
    out = r.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except ValueError:
        _fail("hook produced non-JSON stdout: %r (stderr: %r)" % (out, r.stderr))
        return {}  # unreachable, _fail exits


def _additional_context(hook_output: dict):
    return hook_output.get("hookSpecificOutput", {}).get("additionalContext")


def main() -> None:
    work = Path(tempfile.mkdtemp(prefix="otr-amendment-probe1-"))
    try:
        state_dir = work / "state"
        worker_repo = _make_worker_repo(work)
        # a separate local checkout of the SAME repo (same `origin`) --
        # realistic shape for "the orchestrator runs the edit from
        # wherever it happens to be", which is not necessarily the
        # worker's own checkout path
        orchestrator_cwd = _make_repo(work, "orchestrator-cwd")
        repo_slug = ac.repo_slug_for_cwd(str(orchestrator_cwd))
        if repo_slug is None:
            _fail("test setup bug: orchestrator_cwd's repo slug did not "
                  "resolve (checked %s)" % orchestrator_cwd)

        env = dict(os.environ)
        env["OTR_AMENDMENT_STATE_DIR"] = str(state_dir)
        # issue #3129 repair round 5: the write side's "registered repo"
        # now comes from spawn.py's own roster (this orchestrator-call
        # subprocess's ancestry, walked via /proc), never from the
        # PostToolUse payload's `cwd` field -- a real hook invocation is
        # always a subprocess of a genuine spawn.py-registered session,
        # so this probe fakes that registration the same way: a roster
        # naming THIS probe process's own pid (the direct parent of the
        # `_call_hook()` subprocess below) as registered to
        # `orchestrator_cwd`.
        roster_path = work / "roster" / "active.json"
        roster_path.parent.mkdir(parents=True, exist_ok=True)
        roster_path.write_text(json.dumps({
            "issue-1/probe-orch": {
                "pid": os.getpid(), "work": str(orchestrator_cwd),
                "start_time": ac._proc_start_time(os.getpid()),
            }
        }))
        env["OTR_ROSTER_PATH"] = str(roster_path)

        worker_payload = lambda tool_name="Read", tool_input=None: {
            "session_id": "probe-worker-session",
            "tool_name": tool_name,
            "tool_input": tool_input or {},
            "cwd": str(worker_repo),
        }

        # --- session mid-run, BEFORE the orchestrator amends -------------
        pre = [_call_hook(worker_payload(), env) for _ in range(2)]
        for i, out in enumerate(pre):
            ctx = _additional_context(out)
            if ctx is not None:
                _fail("tool call %d before any amendment already carries a "
                      "notice -- false positive: %r" % (i, ctx))

        # --- orchestrator amends the worker's issue mid-flight ------------
        amend_cmd = 'gh issue edit %s %s "corrected brief: stop building the withdrawn probes"' % (
            ISSUE, BODY_FLAG
        )
        orch_payload = {
            "session_id": "probe-orchestrator-session",
            "tool_name": "Bash",
            "tool_input": {"command": amend_cmd},
            "cwd": str(orchestrator_cwd),
            # issue #3129 round-4: the write side now takes the edited
            # issue's repo+number from THIS field (gh issue edit's own
            # success output), never from the command text -- must name
            # the SAME repo as orchestrator_cwd's own `origin` (repo_slug)
            # or the new cross-repo policy-violation check refuses the
            # write.
            "tool_response": _bash_tool_response(
                "https://github.com/%s/issues/%s" % (repo_slug, ISSUE)),
        }
        _call_hook(orch_payload, env)

        marker = Path(ac.marker_path(str(state_dir), repo_slug, ISSUE))
        if not marker.is_file():
            _fail(
                "no amendment marker written after a gh issue edit --body "
                "call -- amendment-channel.sh missing or its write path "
                "broken (checked %s)" % marker
            )

        # --- session's remaining tool calls, i.e. "before it finishes" ---
        remaining = [_call_hook(worker_payload(), env) for _ in range(3)]
        contexts = [_additional_context(o) for o in remaining]
        fired = [c for c in contexts if c is not None]
        if not fired:
            _fail(
                "running worker session never saw the amendment before "
                "finishing its remaining tool calls -- the exact defect "
                "issue #3129 exists to fix (checked %d payload(s), state "
                "dir=%s, marker exists=%s)"
                % (len(remaining), state_dir, marker.is_file())
            )
        if ISSUE not in fired[0]:
            _fail("notice fired but does not name the amended issue #%s: %r"
                  % (ISSUE, fired[0]))

    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("ok")
    sys.exit(0)


if __name__ == "__main__":
    main()
