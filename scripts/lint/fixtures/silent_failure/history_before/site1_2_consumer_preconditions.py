"""Reconstructed pre-repair shape (issue #3228 sites 1 and 2) of
scripts/preflight/consumer_preconditions.py's check_workspace_disk_headroom.
No subprocess call anywhere in this shape -- it uses os.statvfs()/
shutil.disk_usage(), a filesystem syscall, not a subprocess. This is a
DOCUMENTED MISS for the mechanism in scripts/lint/silent_failure.py: an
os.statvfs() exception being coerced into `True` (site 1) and a real
zero-inode reading being coerced falsy by `if free_inodes and ...`
(site 2) are the same "unobserved reads as fine" shape the issue names,
but neither involves subprocess.run/Popen/check_output/check_call, so
the chosen mechanism (subprocess-observation lint) does not and cannot
see this file. See the record's "what it does not catch" section for
why that is an accepted, stated tradeoff rather than a silent gap.
"""
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
    except (OSError, AttributeError):
        # site 1: an unobservable inode count silently reported the whole
        # precondition satisfied instead of unsatisfied.
        return True, f"{usage.free} free at {probe}, inode check unavailable"
    min_inodes = int(os.environ.get("MUSTER_MIN_FREE_INODES", MIN_FREE_INODES_DEFAULT))
    # site 2: `free_inodes == 0` (a genuinely full filesystem -- the one
    # condition this check exists to catch) is falsy, so this `and` skips
    # the comparison and falls through to the "satisfied" return below.
    if free_inodes and free_inodes < min_inodes:
        return False, f"{free_inodes} free inodes at {probe}, below {min_inodes}"
    return True, f"{usage.free} free, {free_inodes} free inodes at {probe}"
