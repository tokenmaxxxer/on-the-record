#!/usr/bin/env python3
"""issue-3231 round 3, repro 1: a credential-demanding remote must fail
closed quickly, not hang the SessionStart clone waiting for interactive
input.

`script`/pexpect-style pty wrappers turned out to depend on the *outer*
process having a real controlling terminal to forward keystrokes from --
this sandbox's own stdin is not a tty, so a naive `script -qec ... ` repro
returns instantly (git's isatty() check on inherited stdin already fails)
regardless of the fix, which would falsely "pass" even without it. This
script instead opens its own kernel pty pair directly (`pty.openpty()`),
forks a child, makes the pty slave the child's controlling terminal via
`TIOCSCTTY`, and execs the *exact* `git clone` shape
skills.py::_skill_repo_managed_root() issues as that child -- fully
independent of whatever terminal this script itself is run from. The
parent then probes the pty master with a bounded `select()` window and
reports whether the child was still alive (blocked reading its controlling
terminal) when the probe window closed, or had already exited.

Run against a local server that always answers with a 401 credential
challenge (`auth_401_server.py`), twice:
  BEFORE: env has neither GIT_TERMINAL_PROMPT nor GIT_ASKPASS set (this
    round's starting state) -- expect the child to still be alive/blocked
    after the probe window (it is reading "Username for '...': " from its
    controlling terminal, which nothing ever answers).
  AFTER: env = the real `spawn._skill_repo_git_env()` (this round's fix)
    -- expect the child to have already exited with a fast, actionable
    error, well inside the probe window.

Usage: python3 repro_1_credential_prompt.py
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
import spawn  # noqa: E402  -- sets skills._sp = spawn on import


def run_git_clone_via_pty(env: dict, url: str, dest: str,
                           probe_seconds: float = 5.0):
    master_fd, slave_fd = pty_openpty()
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
            os.execvpe("git", ["git", "clone", "-q", url, dest], env)
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


def pty_openpty():
    import pty
    return pty.openpty()


def main() -> None:
    port = 8934
    server = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "auth_401_server.py"), str(port)])
    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}/fake.git"
    try:
        print("=== fix's actual env (from the real function) ===")
        fix_env = spawn._skill_repo_git_env()
        print("GIT_TERMINAL_PROMPT =", fix_env.get("GIT_TERMINAL_PROMPT"))
        print("GIT_ASKPASS         =", fix_env.get("GIT_ASKPASS"))

        before_env = {k: v for k, v in os.environ.items()
                      if k not in ("GIT_TERMINAL_PROMPT", "GIT_ASKPASS", "SSH_ASKPASS")}
        print("\n=== BEFORE: no guard env, real pty, 5s probe window ===")
        r1 = run_git_clone_via_pty(before_env, url, "/tmp/_repro1_before", probe_seconds=5.0)
        print("still blocked (alive) after probe window:", not r1["exited_within_probe"])
        print("elapsed:", r1["elapsed_s"], "s  child terminal read so far:", repr(r1["output"]))

        print("\n=== AFTER: GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=true (this round's fix), real pty, 5s probe window ===")
        r2 = run_git_clone_via_pty(fix_env, url, "/tmp/_repro1_after", probe_seconds=5.0)
        print("exited within probe window:", r2["exited_within_probe"])
        print("elapsed:", r2["elapsed_s"], "s  exit status:", os.WEXITSTATUS(r2["status"]) if r2["status"] is not None else None)
        print("child output:", repr(r2["output"]))
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
