#!/usr/bin/env python3
"""issue-3231 round 4 scratch: does `git ls-remote --symref <url> HEAD`
block on a credential prompt under a CLEAN HOME (no gitconfig credential
helper), isolating this sandbox's own injected `credential.helper`
(`x-access-token`/`$GH_TOKEN`, global config -- see `git config --list |
grep credential`) as the suspected reason the main round4 repro's
--symref BEFORE case exited fast even without GIT_TERMINAL_PROMPT/
GIT_ASKPASS set.

Usage: python3 isolate_symref_test.py
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


def run_via_pty(argv: list[str], env: dict, probe_seconds: float = 5.0):
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


CASES = [
    ("ls-remote --symref <url> HEAD", lambda url: ["git", "ls-remote", "--symref", url, "HEAD"]),
    ("ls-remote --heads <url> HEAD", lambda url: ["git", "ls-remote", "--heads", url, "HEAD"]),
    ("ls-remote <url> HEAD (bare)", lambda url: ["git", "ls-remote", url, "HEAD"]),
    ("ls-remote --heads <url> main (board.py's real branch arg)",
     lambda url: ["git", "ls-remote", "--heads", url, "main"]),
]


def main() -> None:
    clean_home = "/tmp/_clean_home_repro"
    os.makedirs(clean_home, exist_ok=True)
    clean_env = {"PATH": os.environ["PATH"], "HOME": clean_home}
    for i, (label, argv_of_url) in enumerate(CASES):
        port = 8940 + i
        # silent-failure: allow -- long-running server process, terminated
        # in the finally block below, never awaited synchronously
        server = subprocess.Popen([sys.executable, AUTH_SERVER, str(port)])
        time.sleep(0.5)
        url = f"http://127.0.0.1:{port}/fake.git"
        try:
            r = run_via_pty(argv_of_url(url), clean_env, probe_seconds=5.0)
            print(f"clean-HOME (no credential.helper) {label}, no guard env:")
            print("  exited within probe:", r["exited"], " elapsed:", r["elapsed"],
                  "s  buffer:", repr(r["out"][:200]))
        finally:
            server.terminate()
            server.wait(timeout=5)


if __name__ == "__main__":
    main()
