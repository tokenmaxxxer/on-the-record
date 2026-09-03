"""Real repaired code (issue #3228 sites 1 and 2), verbatim excerpt from
the current scripts/preflight/consumer_preconditions.py. The
os.statvfs() except now returns False (unsatisfied), and the inode
comparison is a bare `<` with no truthiness test on `free_inodes` first,
so a real 0 is compared, never coerced away."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

MIN_FREE_BYTES_DEFAULT = 357 * 1024 * 1024
MIN_FREE_INODES_DEFAULT = 1000


def check_workspace_disk_headroom() -> "tuple[bool, str]":
    probe = Path.cwd()
    while not probe.exists():
        probe = probe.parent
    try:
        usage = shutil.disk_usage(probe)
    except OSError as exc:
        return False, f"cannot read disk usage at {probe}: {exc}"
    min_bytes = int(os.environ.get("MUSTER_MIN_FREE_BYTES", MIN_FREE_BYTES_DEFAULT))
    if usage.free < min_bytes:
        return False, f"{usage.free} free at {probe}, below {min_bytes}"
    try:
        st = os.statvfs(probe)
        free_inodes = st.f_favail
    except (OSError, AttributeError) as exc:
        return False, (
            f"{usage.free} free at {probe}, but inode headroom could not "
            f"be observed: {type(exc).__name__}: {exc}")
    min_inodes = int(os.environ.get("MUSTER_MIN_FREE_INODES", MIN_FREE_INODES_DEFAULT))
    if free_inodes < min_inodes:
        return False, f"{free_inodes} free inodes at {probe}, below {min_inodes}"
    return True, f"{usage.free} free, {free_inodes} free inodes at {probe}"
