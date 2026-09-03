#!/usr/bin/env python3
"""issue-3231 round 3, repro 2: a proxy/endpoint that accepts the TCP
connection and then never responds (blackhole) must still fail within a
bounded time -- not hang forever.

Unlike repro 1 (a credential prompt, which `GIT_TERMINAL_PROMPT`/
`GIT_ASKPASS` suppress), a TCP blackhole never reaches git's credential
layer at all -- the HTTP request just never gets a response. The
mechanism that bounds *this* wait is not the env guard; it is
`plumbing._run_net()`'s own `timeout=` argument, which is
`subprocess.run(..., timeout=timeout)` -- a real OS-level bound (SIGKILL
of the child via Python's subprocess machinery on expiry), not a
cooperative one. `_run_net` catches the resulting `subprocess.TimeoutExpired`
and converts it to `sys.exit(f"{label}: 시간초과({int(timeout)}s) — ...")`
(plumbing.py:41-49) -- a bounded, actionable error, not an indefinite hang.
skills.py's real call site passes `timeout=CLONE_TIMEOUT` (180s); this
script passes a short override (5s) to keep the demo fast, but exercises
the exact same code path (`spawn._run_net`, this round's
`spawn._skill_repo_git_env()` guard included) production uses.

Usage: python3 repro_2_tcp_blackhole.py
"""
from __future__ import annotations
import os
import socket
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
import spawn  # noqa: E402


def blackhole_server(port: int, stop: threading.Event) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    srv.settimeout(0.5)
    conns = []
    while not stop.is_set():
        try:
            conn, _ = srv.accept()
            conns.append(conn)  # accept, then never read or write -- blackhole
        except socket.timeout:
            continue
    for c in conns:
        c.close()
    srv.close()


def main() -> None:
    port = 8935
    stop = threading.Event()
    t = threading.Thread(target=blackhole_server, args=(port, stop), daemon=True)
    t.start()
    time.sleep(0.3)
    url = f"http://127.0.0.1:{port}/blackhole.git"
    dest = "/tmp/_repro2_dest"
    demo_timeout = 5  # production uses spawn.CLONE_TIMEOUT (180s); shortened for a fast demo
    print(f"demo timeout passed to _run_net: {demo_timeout}s "
          f"(production skills.py call site uses spawn.CLONE_TIMEOUT={spawn.CLONE_TIMEOUT}s)")
    start = time.time()
    try:
        spawn._run_net(["git", "clone", "-q", url, dest], "[repro] clone",
                        timeout=demo_timeout, env=spawn._skill_repo_git_env())
        print("UNEXPECTED: _run_net returned without raising")
    except SystemExit as exc:
        elapsed = time.time() - start
        print(f"SystemExit raised after {elapsed:.2f}s (bound requested: {demo_timeout}s)")
        print("message:", exc)
        bounded = elapsed < demo_timeout + 3  # small scheduling slack, not an open-ended wait
        print("bounded (elapsed < timeout + slack):", bounded)
    finally:
        stop.set()
        t.join(timeout=2)


if __name__ == "__main__":
    main()
