# issue-1245 current-state survey

skip-condition: none claimed — this is a design decision (where to put the
attachment gate, what counts as "no registration artifacts"), scout sweep
skipped separately as trivial per the issue's own
`validity-consult-skip: trivial` tag (direct implementation of the
operator's already-stated #1219 widened requirement); this survey still
runs per survey-order-directive.

## What attaches today

- `on-the-record/monitors/monitors.json` declares the plugin Monitor
  `poll-heartbeat` with `"when": "always"` — Claude Code starts
  `monitors/poll-heartbeat.sh` for every session where the Monitor tool is
  available, unconditionally on repo shape. This manifest is static and not
  itself a place to put a per-session board check.
- `on-the-record/monitors/poll-heartbeat.sh` is what actually runs. Today,
  before any board check, it unconditionally:
  1. resolves `CHECKOUT` via `poll_rearm_resolve_checkout` (the
     on-the-record checkout itself, for importing `spawn.py` — unrelated to
     the *target* repo);
  2. writes the registration/attachment artifact:
     ```
     mkdir -p "$(pwd -P)/.orchestrate-monitor-alive" && \
       touch "$(pwd -P)/.orchestrate-monitor-alive/alive"
     ```
     `pwd -P` here is the session's target repo (the Monitor process's
     cwd), not the checkout;
  3. enters the sleep/tick loop, which on a due tick calls `spawn.py
     watchdog --auto-respawn` against the target repo and appends to
     `runs/poll_heartbeat_last_state.json` /
     `~/.claude/tokenmaxxxer/poll-watchdog.log`.
- `on-the-record/hooks/directive.sh` (`MONITOR_NOTICE_GRACE_SECONDS` block,
  ~line 139-191) reads the `.orchestrate-monitor-alive/alive` marker's mtime
  to decide whether to print the "idle self-wake is unavailable" degradation
  notice. It infers whether this session's Monitor ever attached purely
  from that marker's presence/freshness.

So "registration" == the `.orchestrate-monitor-alive/` marker directory (the
artifact `directive.sh` itself reads back), plus, once a due tick fires,
`runs/poll_heartbeat_last_state.json` and
`~/.claude/tokenmaxxxer/poll-watchdog.log`. None of these exist unless
`poll-heartbeat.sh` runs past its current unconditional top.

## Board-check primitive already in the repo

`spawn.py` already has the marker constant and check used by
`require_board()`:

```
MARKER = "docs/specs/approvers.md"      # spawn.py:843
...
def require_board(cwd: str, override: bool) -> None:   # spawn.py:887
    root = Path(cwd).resolve()
    if (root / MARKER).is_file():
        return
    ...
```

No existing bash-side helper duplicates this check for hooks/monitors —
`directive.sh` and `poll-rearm.sh` do not test for `docs/specs/approvers.md`
anywhere. The gate this issue wants must live in
`monitors/poll-heartbeat.sh` itself (the one script that performs
attachment), checked against the *target* repo (`pwd -P`), not the checkout.

## Existing tests to extend

`on-the-record/monitors/test_poll_heartbeat.py` already runs
`poll-heartbeat.sh` as a subprocess with a fake `spawn.py`, bounded via
`POLL_HEARTBEAT_MAX_TICKS=1`/`POLL_HEARTBEAT_SLEEP_SECONDS=0`, and asserts
on `marker.log` (fake watchdog-ran marker) and stdout. None of the existing
cases supply `cwd=` to `subprocess.run` — they inherit the test process's
own working directory, which is inside this checkout (a real board — this
repo carries its own `docs/specs/approvers.md`). A hermetic non-board
fixture case needs an explicit `cwd=<tmp dir with no docs/specs/approvers.md>`
and must assert `.orchestrate-monitor-alive` is absent under that `cwd`
afterward — not just that stdout is empty (per the issue's absence-of-
registration framing).

## Write set

- `on-the-record/monitors/poll-heartbeat.sh` — add the board-presence gate
  before the alive-marker write.
- `on-the-record/monitors/test_poll_heartbeat.py` — add a non-board fixture
  case (assert no `.orchestrate-monitor-alive/` created, no
  `poll_heartbeat_last_state.json`, no `poll-watchdog.log`) and a board
  fixture case (assert unchanged behavior: marker created, existing
  due-tick output shape intact).
