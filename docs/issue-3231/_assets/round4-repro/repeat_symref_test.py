#!/usr/bin/env python3
"""issue-3231 round 4 scratch: run `git ls-remote --symref <url> HEAD`
against a credential-demanding remote, unguarded, N times in a row (fresh
server+port each time) to check whether its fast-exit (no interactive
block) is a stable property of this argv shape or a flake.

Usage: python3 repeat_symref_test.py [n]
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
import pty

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
AUTH_SERVER = os.path.join(ROOT, "docs", "issue-3231", "_assets", "round3-repro",
                            "auth_401_server.py")


def run_via_pty(argv, env, probe_seconds=5.0):
    master_fd, slave_fd = pty.openpty()
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
    return {"exited": exited, "elapsed": round(elapsed, 3),
            "out": output.decode(errors="replace")}


def bare_env() -> dict:
    return {k: v for k, v in os.environ.items()
            if k not in ("GIT_TERMINAL_PROMPT", "GIT_ASKPASS", "SSH_ASKPASS",
                          "GIT_SSH_COMMAND")}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    env = bare_env()
    for i in range(n):
        port = 8960 + i
        # silent-failure: allow -- long-running server process, terminated
        # in the finally block below, never awaited synchronously
        server = subprocess.Popen([sys.executable, AUTH_SERVER, str(port)])
        time.sleep(0.5)
        url = f"http://127.0.0.1:{port}/fake.git"
        try:
            r = run_via_pty(["git", "ls-remote", "--symref", url, "HEAD"], env,
                             probe_seconds=5.0)
            print(f"trial {i}: exited={r['exited']} elapsed={r['elapsed']}s "
                  f"out={r['out'][:80]!r}")
        finally:
            server.terminate()
            server.wait(timeout=5)


if __name__ == "__main__":
    main()
