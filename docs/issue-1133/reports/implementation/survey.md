# Survey: issue-1133 — watcher re-arm registry staleness + blocking remediation

## Scope

Pure bugfix + a wire-safe remediation-text change on an existing internal
CLI (`spawn.py`). No product-shaped surface, no external dependency
choice. Scout-directive skip condition applies: this is a pure bugfix
to internal tooling (issue's own Acceptance section names the exact
generator and the exact fix shape — registry write path + message
string) — scouting for "category best-in-class" has no referent here.
Recorded per survey-order-directive's mandatory skip-record requirement.

## Reproduction (live, this session, 2026-08-13)

canonical: gh issue view 1133 (Problem/Requirements/Acceptance sections)

Using `MUSTER_STATE_ROOT` (issue #857's hermetic test root) to isolate
roster/workspace-index files from the real ones:

```
$ export MUSTER_STATE_ROOT=/tmp/mst1133b/runs
$ python3 spawn.py -C /tmp/mst1133b/work watch --issue 1133 --role implementation \
    --follow --stall-timeout 0.05
[watch] stall: 세션 로그 3초째 무변화 — 이벤트 없이 멈춘다. 다시 spawn.py watch 로 재무장하라
[watch] 세션 프로세스가 사라졌다(pid 2695198) — session-end 없이 끝났다. 크래시로 보고 멈춘다
```

derived: cat /tmp/mst1133b/runs/workspaces.json (this session, after the
above run) — held the new watch process's own pid (2696431), confirming
spawn.py:3791-3796 (`_watch`'s follow-entry re-arm write) does execute
and does write a genuinely new `watcher_pid` at follow-start.

The failure is downstream of that write, not in it: the newly-armed
watcher is itself the blocking foreground `--follow` process named in
the issue's requirement 2. The issue text itself (gh issue view 1133,
quoted above) states the orchestrator's own remediation call timed out
at 2m, exit 143 — i.e. the caller killed the just-armed watcher. Once
killed, that same now-dead pid is what the next watchdog tick reports:

```
$ python3 -c "import spawn; print(spawn.watchdog_check_one('issue-1133/implementation', spawn._roster_load()['issue-1133/implementation']))"
['watcher-dead: 워처 pid 2696431 가 죽어 있거나...']
```

derived: the two commands above, run in this session against the
`MUSTER_STATE_ROOT`-isolated fixture — the reported-dead pid (2696431)
is the exact pid the prior command's registry write had just recorded
as new.

canonical: gh issue view 1133 (Problem section, "워처 프로세스는 3개 떠
있으나 레지스트리는 여전히 옛 pid를 DEAD로 표시", and "orchestrator call
timed out 2m") — each remediation attempt that follows the current
message text spawns one more short-lived watcher, gets killed by the
caller's own timeout wrapper, and leaves one more stale DEAD pid behind
in the registry; this matches the operator's repeated-recurrence report
without requiring the registry-write code path itself to be defective.

## Root cause

canonical: the two `derived:` command runs quoted in the Reproduction
section above, and spawn.py:3791-3796 (read this session)

Requirement 1's registry-write mechanism (spawn.py:3791-3796,
`_workspace_index_put` inside `_watch`'s follow branch) is not
defective on its own — it does write a fresh `watcher_pid`. The defect
is requirement 2: there is no code path that arms a watcher without
blocking the calling process in the foreground. The only re-arm
entrypoint (`spawn.py watch --issue <n> --follow`) is inherently a
long-running loop (`_watch()`'s `while True` at spawn.py:3806), so any
caller that cannot itself block indefinitely (an orchestrator turn, a
CI step, a human backgrounding it incorrectly) kills it — and killing
it re-creates exactly the registry-staleness symptom requirement 1
names, even though the write path itself is correct.

The existing detached-arm pattern already exists once in the codebase
— the spawn-time auto-arm at spawn.py:5744-5766 — which
`subprocess.Popen`s a `watch --follow --self-heal` child with
`start_new_session=True`, `stdin=DEVNULL`, redirected stdout/stderr to
a `.watcher.log` file, and returns immediately without waiting on it.
That is the shape a non-blocking *re*-arm needs to reuse.

## Write surfaces

- `spawn.py`:
  - a new CLI-reachable re-arm path that spawns the follow-watcher
    detached (mirrors spawn.py:5744-5766) and returns immediately,
    rather than blocking in the caller's own process — this satisfies
    requirement 1's "re-arm updates the registry entry" without also
    requiring the caller to block.
  - the `watcher-dead` (spawn.py:2259-2261) and `watcher-silent`
    (spawn.py:2278) remediation message strings, which currently name
    bare `spawn.py watch --issue <n> --follow` — replaced with the new
    non-blocking form.
- gates/test_watch_rearm_registry.py (new, does not exist yet on this
  branch — this survey names it as a write-set target, not an existing
  reference): exercises the new re-arm path against a
  `MUSTER_STATE_ROOT`-isolated fixture — arm, kill, re-arm, assert
  `watchdog_check_one` reports no `watcher-dead` and the registry holds
  the new (alive) pid; a never-armed entry is asserted unaffected
  (empty-state case per Acceptance); and asserts neither remediation
  string contains a bare `--follow` token.

## Alternatives considered

- Just change the message text to add a backgrounding note (e.g. "run
  this with `&`/`nohup`") without adding a real non-blocking entrypoint:
  rejected — leaves requirement 1 exposed to the same timeout-kill
  failure mode every time an orchestrator actually follows the
  instruction verbatim, since backgrounding a `--follow` invocation
  from an already-bounded orchestrator turn still ties the watcher's
  lifetime to that turn's process group in several harnesses. A
  first-class detached re-arm command is the only shape that both
  survives the caller's own timeout and gives the gate test something
  concrete to invoke and assert on.
- Have the watchdog itself auto-respawn dead watchers (fold into
  `roster_watchdog`'s existing `--auto-respawn` path): rejected as out
  of scope — `--auto-respawn` today is scoped to role sessions, and
  folding watcher lifecycle into it changes an existing,
  already-relied-upon observe-only contract boundary (watchdog reports,
  it does not act, except behind that one explicit opt-in flag). The
  issue's Acceptance asks for a re-arm code path and a message fix, not
  a new autonomous-action surface.
