#!/usr/bin/env python3
"""issue-3231 round 3 repro helper: a local HTTP server that answers every
request with 401 + `WWW-Authenticate: Basic` -- the same credential
challenge shape a private/rate-limited git smart-http remote sends. git's
smart-http client responds to this exact response by asking the *invoking
process* for a username, which is the interactive prompt this round's fix
(`skills._skill_repo_git_env()`) suppresses.

Usage: `python3 auth_401_server.py <port>` -- runs until killed.
"""
from __future__ import annotations
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _challenge(self) -> None:
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="fake-git-remote"')
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 -- stdlib handler naming
        self._challenge()

    def do_POST(self) -> None:  # noqa: N802
        self._challenge()

    def log_message(self, fmt: str, *args) -> None:
        pass  # keep the transcript focused on the git client's own output


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8933
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
