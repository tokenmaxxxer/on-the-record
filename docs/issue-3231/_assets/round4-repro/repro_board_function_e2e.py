#!/usr/bin/env python3
"""issue-3231 round 4: confirm `board._remote_branch_head()` itself (not
just the raw git argv) fails fast against a credential-demanding remote,
calling it exactly as `board.py` production code does -- `import spawn`
first so `board._sp` is wired the way `spawn.py` wires it at import time,
then call the real function, wall-clock timed, no probe-window guessing
needed since `_run_net`'s own timeout bounds it.

Usage: python3 repro_board_function_e2e.py
"""
from __future__ import annotations
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
import spawn  # noqa: E402 -- wires board._sp = spawn on import
import board  # noqa: E402
AUTH_SERVER = os.path.join(ROOT, "docs", "issue-3231", "_assets", "round3-repro",
                            "auth_401_server.py")


def main() -> None:
    port = 8970
    # silent-failure: allow -- long-running server process, terminated in
    # the finally block below, never awaited synchronously
    server = subprocess.Popen([sys.executable, AUTH_SERVER, str(port)])
    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}/fake.git"
    try:
        start = time.time()
        result = board._remote_branch_head(cwd="/tmp", remote=url, branch="main")
        elapsed = time.time() - start
        print("board._remote_branch_head() against a credential-demanding "
              f"remote returned: {result!r} in {elapsed:.3f}s "
              "(NETWORK_TIMEOUT would be ~180s if the fix regressed to "
              "blocking on the credential prompt instead of the fast "
              "401-triggered failure)")
        assert elapsed < 5.0, "regressed: took long enough to suggest blocking, not fast-fail"
        print("PASS")
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
