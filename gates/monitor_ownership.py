"""Per-session ownership for the poll-heartbeat monitor (issue #3293).

Before this, every session's heartbeat had a byte-identical command line
and shared one workspace-keyed alive marker. Nothing distinguished this
session's heartbeat from a neighbour's, and both consequences were observed
on 2026-09-03: a session cleaning up what it reasonably read as duplicate
heartbeats killed another session's with a `pkill -f` pattern that cannot
be narrowed, and an orchestrator that wanted to stop only its own had no
way to name it.

An owner token is `<pid>.<start-tick>` -- the same pid-reuse-proof pairing
`roster.py::_paired_liveness()` already trusts, because the OS will not
hand out that combination twice. `poll-heartbeat.sh` exports it as
`OTR_MONITOR_OWNER` and writes `owner-<token>` next to the shared `alive`
marker on every tick.

The refusal is the point. `stop_owned()` signals a process only when the
token names it AND the live process still matches that token. Anything
else -- an unknown token, a token whose pid now belongs to something else,
a marker with no live process -- is refused with a named reason. A caller
that cannot establish ownership gets an error, never a pattern match:
falling back to `pkill` is exactly the behaviour this module exists to
remove.
"""
from __future__ import annotations

import hashlib
import os
import signal
from pathlib import Path

ALIVE_ROOT = Path.home() / ".claude" / "tokenmaxxxer" / "monitor-alive"
OWNER_PREFIX = "owner-"


def alive_dir_for(cwd: str | os.PathLike[str]) -> Path:
    """The workspace-keyed marker directory `poll-heartbeat.sh` uses.

    Reimplements that script's hash inline rather than importing it -- the
    script is bash and this is the only shared constant. Any divergence
    shows up immediately as "no owner markers found" rather than silently
    stopping the wrong thing.
    """
    root = str(Path(cwd).resolve())
    h = hashlib.sha256(root.encode("utf-8", "surrogatepass")).hexdigest()[:24]
    return ALIVE_ROOT / h


def _proc_start_tick(pid: int) -> str | None:
    """Field 22 of `/proc/<pid>/stat`. `None` where there is no /proc."""
    try:
        with open("/proc/%d/stat" % pid, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        return None
    try:
        return raw[raw.rfind(")") + 2:].split()[19]
    except IndexError:
        return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        return False
    return True


def owner_matches(token: str, pid: int) -> tuple[bool, str]:
    """Does `pid` still answer to `token`? Returns (ok, reason-if-not).

    A token of `<pid>.nostat` means the heartbeat ran where `/proc` is
    unavailable (macOS). There the pid alone is the only evidence, which is
    weaker against pid reuse -- so it is accepted, and the weakness is
    stated in the returned reason rather than hidden.
    """
    want_pid_s, _, want_start = token.partition(".")
    try:
        want_pid = int(want_pid_s)
    except ValueError:
        return False, f"token {token!r} is not <pid>.<start>"
    if want_pid != pid:
        return False, f"token names pid {want_pid}, marker names pid {pid}"
    if not _alive(pid):
        return False, f"pid {pid} is not running -- stale marker"
    if want_start in ("nostat", "unknown"):
        return True, ("accepted on pid alone -- the heartbeat ran on a "
                      "platform without /proc, so start-time identity could "
                      "not be recorded and pid reuse is not ruled out")
    now_start = _proc_start_tick(pid)
    if now_start is None:
        return False, (f"cannot read pid {pid}'s start time to confirm it is "
                       "still the process the token names -- refusing rather "
                       "than signalling on the pid alone")
    if now_start != want_start:
        return False, (f"pid {pid} start time is {now_start}, token says "
                       f"{want_start} -- the pid was reused by an unrelated "
                       "process")
    return True, ""


def find_owned(cwd: str | os.PathLike[str]) -> list[dict]:
    """Every owner marker under `cwd`'s alive dir, with its liveness."""
    d = alive_dir_for(cwd)
    out: list[dict] = []
    try:
        entries = sorted(d.iterdir())
    except OSError:
        return out
    for p in entries:
        if not p.name.startswith(OWNER_PREFIX):
            continue
        token = p.name[len(OWNER_PREFIX):]
        try:
            pid = int(p.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            out.append({"token": token, "pid": None, "alive": False,
                        "reason": "marker unreadable or not a pid"})
            continue
        ok, reason = owner_matches(token, pid)
        out.append({"token": token, "pid": pid, "alive": ok, "reason": reason})
    return out


def stop_owned(token: str, cwd: str | os.PathLike[str]) -> dict:
    """Stop exactly the heartbeat named by `token`. Never anything else.

    Refuses -- with a reason -- when the token has no marker, names a pid
    that is gone, or names a pid the OS has since reused. It never widens
    to a pattern, and it never touches a marker it did not just stop.
    """
    d = alive_dir_for(cwd)
    marker = d / (OWNER_PREFIX + token)
    if not marker.is_file():
        return {"stopped": False,
                "reason": f"no heartbeat marker for owner {token!r} under "
                          f"{d} -- refusing to guess which process to signal"}
    try:
        pid = int(marker.read_text(encoding="utf-8").strip())
    except (OSError, ValueError) as exc:
        return {"stopped": False,
                "reason": f"marker {marker} is unreadable or not a pid: {exc}"}
    ok, reason = owner_matches(token, pid)
    if not ok:
        return {"stopped": False, "pid": pid, "reason": reason}
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return {"stopped": False, "pid": pid,
                "reason": f"could not signal pid {pid}: {exc}"}
    try:
        marker.unlink()
    except OSError:
        pass
    return {"stopped": True, "pid": pid, "token": token, "reason": reason}
