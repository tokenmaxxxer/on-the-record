#!/usr/bin/env python3
"""issue-3231 round 4: confirm the three call sites round-4's fix newly
guards (board.py `_remote_branch_head`, on-the-record/hooks/git-push-guard.sh
`_resolve_default_branch`, scripts/issue-3041/run_pair.sh's `git clone`)
each fail fast against a credential-demanding remote instead of blocking,
using the exact argv shape each call site issues and the same real-pty
probe method PR #3256's round-4 verification used (never "read the diff
and assume") -- reused from
docs/issue-3231/_assets/round3-repro/repro_1_credential_prompt.py.

Usage: python3 repro_round4_three_sites.py
"""
from __future__ import annotations
import fcntl
import os
import select
import signal
import subprocess
import sys
import termios
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
AUTH_SERVER = os.path.join(ROOT, "docs", "issue-3231", "_assets", "round3-repro",
                            "auth_401_server.py")


def run_via_pty(argv: list[str], env: dict, probe_seconds: float = 5.0):
    master_fd, slave_fd = __import__("pty").openpty()
    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
            os.close(master_fd)
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            fcntl.ioctl(0, termios.TIOCSCTTY, 0)
            os.close(slave_fd)
            os.execvpe(argv[0], argv, env)
        finally:
            os._exit(127)
    os.close(slave_fd)
    start = time.time()
    output = b""
    exited, status = False, None
    while time.time() - start < probe_seconds:
        r, _, _ = select.select([master_fd], [], [], 0.2)
        if r:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                chunk = b""
            if chunk:
                output += chunk
        wpid, wstatus = os.waitpid(pid, os.WNOHANG)
        if wpid == pid:
            exited, status = True, wstatus
            break
    elapsed = time.time() - start
    if not exited:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    os.close(master_fd)
    return {"exited_within_probe": exited, "status": status,
            "elapsed_s": round(elapsed, 3), "output": output.decode(errors="replace")}


def guarded_env() -> dict:
    ssh_cmd = os.environ.get("GIT_SSH_COMMAND", "ssh")
    return {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "true",
            "GIT_SSH_COMMAND": f"{ssh_cmd} -o BatchMode=yes"}


def bare_env() -> dict:
    return {k: v for k, v in os.environ.items()
            if k not in ("GIT_TERMINAL_PROMPT", "GIT_ASKPASS", "SSH_ASKPASS",
                          "GIT_SSH_COMMAND")}


def start_server(port: int) -> subprocess.Popen:
    # silent-failure: allow -- long-running server process, terminated by
    # its caller a few lines below (stop_server), never awaited
    # synchronously; a fresh server+port per BEFORE/AFTER sub-run avoids
    # any single-threaded-HTTPServer connection-state bleed between runs
    # (a shared server across sub-runs initially produced a false-fast
    # BEFORE result for one site here -- see this script's own git-blame
    # history / the round-4 record's derivation for the diagnosis).
    p = subprocess.Popen([sys.executable, AUTH_SERVER, str(port)])
    time.sleep(0.5)
    return p


def stop_server(p: subprocess.Popen) -> None:
    p.terminate()
    p.wait(timeout=5)


def report(label: str, port: int, argv_of_url) -> str:
    """Returns one of "PASS" (blocked before, fast-fails after -- the guard
    demonstrably closed a real hazard), "INCONCLUSIVE" (didn't block even
    before the guard -- this argv shape doesn't reproduce the hazard in
    this environment, not a defect in the fix), or "REGRESSION" (still
    blocks after the guard -- a real defect). Only REGRESSION should ever
    fail a caller's exit code; conflating INCONCLUSIVE into "FAIL" is
    exactly the silent-failure shape this issue exists to remove (a
    warrant-hunter caught an earlier version of this script doing that --
    printing "FAIL" but always exiting 0)."""
    print(f"\n=== {label} ===")
    server = start_server(port)
    try:
        url = f"http://127.0.0.1:{port}/fake.git"
        argv = argv_of_url(url)
        print("argv:", argv)
        print("-- BEFORE (bare env, fresh server, real pty, 5s probe) --")
        before = run_via_pty(argv, bare_env())
        print("still blocked (alive) after probe:", not before["exited_within_probe"],
              " elapsed:", before["elapsed_s"], "s  buffer:", repr(before["output"][:200]))
    finally:
        stop_server(server)

    server = start_server(port)
    try:
        url = f"http://127.0.0.1:{port}/fake.git"
        argv = argv_of_url(url)
        print("-- AFTER (guarded env, fresh server, real pty, 5s probe) --")
        after = run_via_pty(argv, guarded_env())
        print("exited within probe:", after["exited_within_probe"],
              " elapsed:", after["elapsed_s"], "s")
        print("exit status:", os.WEXITSTATUS(after["status"]) if after["status"] is not None else None,
              " buffer:", repr(after["output"][:200]))
    finally:
        stop_server(server)

    was_blocked_before = not before["exited_within_probe"]
    fails_fast_after = after["exited_within_probe"] and after["elapsed_s"] < 1.0
    if was_blocked_before and fails_fast_after:
        verdict = "PASS"
    elif not was_blocked_before:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "REGRESSION"
    print("VERDICT:", verdict)
    return verdict


def main() -> None:
    # silent-failure: allow -- git clone's own destination-exists check
    # (fatal, no hang possible) makes this cleanup best-effort scaffolding,
    # not a call whose hang this repro needs to detect
    subprocess.run(["rm", "-rf", "/tmp/_repro_round4_seed"])
    verdicts = []
    # board.py::_remote_branch_head's exact argv shape (cwd is any dir;
    # ls-remote takes an explicit URL as `remote` so it need not be a
    # real git repo).
    verdicts.append(report(
        "board.py _remote_branch_head: git ls-remote --heads <url> <branch>",
        8935, lambda url: ["git", "-C", "/tmp", "ls-remote", "--heads", url, "main"]))
    # git-push-guard.sh::_resolve_default_branch's exact argv shape.
    verdicts.append(report(
        "git-push-guard.sh _resolve_default_branch: git ls-remote --symref <url> HEAD",
        8936, lambda url: ["git", "ls-remote", "--symref", url, "HEAD"]))
    # scripts/issue-3041/run_pair.sh's exact argv shape.
    verdicts.append(report(
        "run_pair.sh: git clone --quiet <url> <dest>",
        8937, lambda url: ["git", "clone", "--quiet", url, "/tmp/_repro_round4_seed"]))
    print("\n=== SUMMARY ===", verdicts)
    if "REGRESSION" in verdicts:
        sys.exit(1)


if __name__ == "__main__":
    main()
