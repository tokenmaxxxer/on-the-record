"""issue #2104 — evidence-pointer contract for consult answers.

Unverified advisor claims measured ~50% wrong before repo-verification
was mandated (operator memory, 2026-08). Contract: each factual claim
in a consult answer MAY carry an evidence pointer on the same line:

    ... claim text ... evidence: gates/spawn.py:120
    ... claim text ... evidence-cmd: grep -n "def consult_cmd" spawn.py

This module is the cheap mechanical verifier (CiteGuard pattern):

- `evidence: <path>:<line>` — verified iff the file exists under the
  repo root and the line number is within range. `evidence: <path>`
  (no line) — verified iff the file exists.
- `evidence-cmd: <command>` — arbitrary commands are NEVER executed.
  Only an allowlist of read-only shapes runs (grep, test -f/-d,
  git log/show/grep with fixed argument shapes, wc -l); anything else
  is stamped `unverified-cmd` untouched.
- a line with no pointer is stamped `no-evidence` — advisory, not an
  error (claims without pointers are advisory-weight-zero by contract).

`stamp_claims()` returns per-claim stamps; `stamp_summary()` folds them
into one short string the consult trace line carries. The caller
(spawn.py consult path) wraps the whole thing fail-open — a verifier
crash must never stall a consult.
"""
from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

EVIDENCE_RE = re.compile(r"evidence:\s*(\S+)")
EVIDENCE_CMD_RE = re.compile(r"evidence-cmd:\s*(\S.*)$")
CMD_TIMEOUT = 10

# Read-only command allowlist: first token, then a shape check.
_ALLOWED_GIT_SUB = {"log", "show", "grep", "ls-files", "rev-parse"}
_SHELL_META = set(";|&`$><\n")


def _cmd_allowed(argv: list[str]) -> bool:
    if not argv:
        return False
    head = argv[0]
    if head == "grep":
        return True
    if head == "test":
        return len(argv) == 3 and argv[1] in ("-f", "-d", "-e")
    if head == "git":
        return len(argv) >= 2 and argv[1] in _ALLOWED_GIT_SUB
    if head == "wc":
        return len(argv) >= 2 and argv[1] == "-l"
    return False


def verify_path_pointer(pointer: str, root: Path) -> str:
    """`path` or `path:line` -> 'verified' | 'failed'."""
    path_part, sep, line_part = pointer.rpartition(":")
    if sep and line_part.isdigit():
        rel, lineno = path_part, int(line_part)
    else:
        rel, lineno = pointer, None
    target = (root / rel.lstrip("/")).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return "failed"  # pointer escapes the repo root
    if not target.is_file():
        return "failed"
    if lineno is not None:
        try:
            n = sum(1 for _ in target.open("rb"))
        except OSError:
            return "failed"
        if not (1 <= lineno <= n):
            return "failed"
    return "verified"


def verify_cmd_pointer(command: str, root: Path) -> str:
    """Allowlisted read-only command -> 'verified'/'failed' by exit code;
    anything outside the allowlist (or with shell metacharacters) is
    'unverified-cmd' and is NOT executed."""
    if any(c in _SHELL_META for c in command):
        return "unverified-cmd"
    try:
        argv = shlex.split(command)
    except ValueError:
        return "unverified-cmd"
    if not _cmd_allowed(argv):
        return "unverified-cmd"
    try:
        r = subprocess.run(argv, cwd=str(root), capture_output=True,
                           timeout=CMD_TIMEOUT, text=True)
    except (subprocess.TimeoutExpired, OSError):
        return "failed"
    return "verified" if r.returncode == 0 else "failed"


def stamp_claims(answer_text: str, root: Path) -> list[dict]:
    """One stamp per non-empty answer line. Lines carrying pointers get
    verified/failed/unverified-cmd; pointer-less lines get no-evidence."""
    stamps: list[dict] = []
    for line in answer_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m_cmd = EVIDENCE_CMD_RE.search(line)
        m_path = None if m_cmd else EVIDENCE_RE.search(line)
        if m_cmd:
            stamp = verify_cmd_pointer(m_cmd.group(1).strip(), root)
            pointer = m_cmd.group(1).strip()
        elif m_path:
            pointer = m_path.group(1).strip().rstrip(".,;")
            stamp = verify_path_pointer(pointer, root)
        else:
            stamp, pointer = "no-evidence", None
        stamps.append({"line": line[:120], "pointer": pointer, "stamp": stamp})
    return stamps


def stamp_summary(answer_text: str, root: Path) -> str:
    """Compact trace-line suffix, e.g.
    `evidence=[verified:2 failed:1 unverified-cmd:0 no-evidence:3; failed: spawn.py:9999]`"""
    stamps = stamp_claims(answer_text, root)
    counts = {"verified": 0, "failed": 0, "unverified-cmd": 0, "no-evidence": 0}
    failed_pointers: list[str] = []
    for s in stamps:
        counts[s["stamp"]] += 1
        if s["stamp"] == "failed" and s["pointer"]:
            failed_pointers.append(s["pointer"])
    body = " ".join(f"{k}:{v}" for k, v in counts.items())
    if failed_pointers:
        body += "; failed: " + ", ".join(failed_pointers[:3])
    return f"evidence=[{body}]"


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: evidence_check.py <answer-file> [repo-root]", file=sys.stderr)
        return 2
    root = Path(argv[2]) if len(argv) > 2 else Path.cwd()
    text = Path(argv[1]).read_text(encoding="utf-8")
    for s in stamp_claims(text, root):
        print(f"{s['stamp']:14} {s['pointer'] or '-':40} {s['line']}")
    print(stamp_summary(text, root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
