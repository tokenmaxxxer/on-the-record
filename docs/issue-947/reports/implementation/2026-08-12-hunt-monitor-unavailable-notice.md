---
proposal: docs/issue-947/proposals/monitor-unavailable-notice.md
---

# Hunt record — monitor-unavailable-notice

## after-proposal — stance 0: bypass hunt (assume the notice mechanism is bypassable — find the bypass)

Verdict: FINDING — stale per-workspace start-marker from an earlier CLI session silently suppresses the notice in a later IDE session that reuses the same workspace directory
Kind: silent-failure
Seed: docs/issue-947/proposals/monitor-unavailable-notice.md (docs-only, no code yet); reused pattern is on-the-record/hooks/directive.sh's existing GREETED_MARKER
cap_seconds: 60
tier: default
diff_stat_lines: 1 file changed (proposal doc only)
started_at: 2026-08-12T16:00:00Z
ended_at: 2026-08-12T16:06:00Z

### Reproduce
The proposal (step 1) says the monitor start-marker is written "same
`pwd -P`-keyed convention as `GREETED_MARKER`" — i.e. one plain file per
workspace directory, with no session-id component and no expiry/cleanup.
`directive.sh`'s actual `GREETED_MARKER` demonstrates this convention has
exactly that lifetime today:

```
cd /tmp/repro-947
touch .orchestrate-greeted
ls -la .orchestrate-greeted
```
Observed: the marker is an ordinary file that persists indefinitely —
nothing in `directive.sh` (grep for `GREETED_MARKER` — only written once,
never removed) ever deletes or rotates it. Applying the identically-worded
convention to the proposed `.orchestrate-monitor-alive` marker means: once
any CLI session in a given workspace runs `poll-heartbeat.sh` and writes
the start-marker, that file sits in the workspace forever. A later session
opened on the same workspace via the IDE extension — the exact case #947
wants surfaced — will find the stale start-marker already present from the
earlier CLI session. Step 2's check ("the monitor start-marker from step 1
is still absent") reads false, so the grace-window degradation notice
never fires, even though Monitors are structurally unavailable in this
new IDE session.

### Expected
The start-marker (unlike GREETED_MARKER, which is fine to be
workspace-lifetime because "greeted once ever" is the intended semantics)
needs to be scoped to the current session — e.g. keyed by a session id or
process/PID-and-start-time, or truncated/removed at SessionStart — so that
a monitor's absence in *this* session cannot be masked by a marker some
*other*, earlier session wrote. As specified, the proposal reuses a
workspace-lifetime persistence convention for a signal whose truth value
is per-session, which is a design error, not just a nice-to-have edge
case: it silently defeats the notice for exactly the operators most likely
to need it (anyone who ever ran a CLI session in a repo before switching
to the IDE extension for it).
