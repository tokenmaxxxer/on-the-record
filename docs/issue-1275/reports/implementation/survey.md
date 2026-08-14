# Survey — issue #1275

Write surfaces:
- `on-the-record/hooks/poll-rearm.sh` — `poll_rearm_arm_if_due()` (called by `directive.sh` UserPromptSubmit and `stop-poll-rearm.sh` Stop) launches `spawn.py watchdog --auto-respawn` with no `-C`, so `root` defaults to the calling process's cwd (spawn.py's own `-C` argparse default `"."`). No root validation exists before that launch.
- `on-the-record/monitors/poll-heartbeat.sh` — same no-`-C` pattern for its own due-tick `spawn.py watchdog --auto-respawn` call, and it loops forever (60s ticks) — this is the process the issue's "fails every tick" description points at.
- Tests: `on-the-record/hooks/test_poll_rearm.py` and `on-the-record/monitors/test_poll_heartbeat.py` both stub `spawn.py` via a fake-spawn.py harness and run the real shell scripts through `subprocess.run`, already exposing a `cwd=` lever point to add for the new fixtures (non-git root, git-root-without-board, valid board root).

Skip condition: pure bugfix (issue states `validity-consult-skip: trivial`) — input validation at an existing entry point, fully specified by the issue's own Requirements section (git repo + docs/specs/approvers.md presence). No design decision is open; scouting/full proposal round skipped per scout-directive's bugfix skip condition.
