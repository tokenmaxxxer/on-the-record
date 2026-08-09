---
proposal: docs/proposals/2026-08-09-ps-watcher-visibility-and-bounded-watch-all.md
---

# Hunt record — ps-watcher-visibility-and-bounded-watch-all

## after-proposal — stance 0: assume the gate/guard just touched by this change is bypassable — find the bypass

Verdict: FINDING — `_watcher_looks_real(pid, issue)` (spawn.py:1698-1717), which the proposal plans to reuse verbatim for `ps` watcher-visibility and for `watch --all --until-idle`'s liveness check, verifies only `issue` presence in `/proc/<pid>/cmdline`, never the `role`. A pid that is a genuine, live watcher for a *different role of the same issue* is reported "real" for any other role's roster/workspace-index entry that happens to (re)point at that pid.
Kind: silent-failure
Seed: docs/issue-559/proposals/2026-08-09-ps-watcher-visibility-and-bounded-watch-all.md (plans to reuse `_watcher_looks_real`, spawn.py:1698-1717, and the bare-key/repo-prefixed-key join at spawn.py:2806-2811, unchanged)
cap_seconds: 60
tier: default (docs-only, size bucket <=20 lines-or-docs-only)
diff_stat_lines: docs-only (proposal file only, no code diff yet)
started_at: 2026-08-09T12:29:41+09:00
ended_at: 2026-08-09T12:41:00+09:00

### Reproduce
```python
import sys; sys.path.insert(0, ".")
import spawn
from pathlib import Path
import unittest.mock as mock

# pid 4242 is alive and is a REAL "spawn.py watch --issue 559 --role qa"
# process — i.e. a genuinely live watcher, but for role "qa".
FAKE_CMDLINE = b"python3\x00spawn.py\x00watch\x00--issue\x00559\x00--role\x00qa\x00"

with mock.patch.object(spawn, "_alive", return_value=True), \
     mock.patch.object(Path, "exists", lambda self: True), \
     mock.patch.object(Path, "read_bytes", lambda self: FAKE_CMDLINE):
    # A roster/workspace-index entry for issue 559, role "dev" (a DIFFERENT
    # role) has watcher_pid=4242 (e.g. stale record, or OS/pid-namespace
    # reuse — the exact mechanism issue #488 already worried about, just
    # one level short: same-issue cross-role collision instead of
    # cross-issue).
    print(spawn._watcher_looks_real(4242, 559))
```
(Note: this exercises the real, unmodified `_watcher_looks_real` with a
controlled `/proc/<pid>/cmdline`; live-pid experiments inside this sandbox
were blocked by a gVisor pid-namespace artifact where `os.getpid()` does not
resolve to an addressable `/proc/<pid>` path at all — confirmed separately by
`os.getpid()` returning 6 while `/proc/self` symlinks to a different host
pid. That is a property of this sandbox, not of the code under test.)

### Observed
`True` — role "dev"'s entry is vouched for as "watcher is real" by a pid
that is actually role "qa"'s watcher process for the same issue.

### Expected
The identity check should fail (or the function should require/verify the
role, not just the issue) so that a live watcher belonging to a sibling
role of the same issue cannot be mistaken for the watcher the roster entry
in question actually registered. As written, the check the proposal intends
to surface in `ps` (and gate `--until-idle`'s exit condition on) inherits
this role-blind spot: a dead watcher for role X can be silently reported
"alive" in `ps` — and `--until-idle` could keep treating the session as
"watched" — purely because some other role of the same issue happens to be
running a real watcher whose pid was assigned to (or reused for) role X's
stale roster/workspace-index record.
