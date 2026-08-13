# issue-1154 current-state survey

## Scope

Compares the spawn-time auto-arm watcher path against the `--rearm`
detached path PR #1149 (and its parent, #1133's `3ec4312`) hardened, to
find the structural gap that lets an auto-armed watcher die with its
caller while a rearm'd one survives.

Scout-sweep skip: pure bugfix that reproduces an already-fixed pattern
(#1133/#1149) in a sibling code path — no product-facing design
decision is open here, so the exemplar-search stage of scout is skipped
per its own stated skip condition. This survey is the current-state
research the fix is drafted from.

## Code under review

- `spawn.py` — `_spawn_one()`'s spawn-time auto-arm block
  (currently spawn.py:5905-5931, drifted slightly from the issue's
  cited spawn.py:5744-5766 range due to intervening commits)
- `spawn.py` — `_rearm_watcher_detached()` (spawn.py:3948-4012), the
  #1133/#1149-hardened reference shape
- `spawn.py` — `_await_bounded()` (spawn.py:3616-3675), the blocking
  wait auto-arm chains into
- `gates/test_watch_rearm_registry.py` — existing rearm coverage, the
  file the issue asks to extend with an auto-arm case

## What the two paths actually do

canonical: spawn.py:5903-5945, read this session, quoted verbatim
below (auto-arm, `_spawn_one`'s `if child_pid > 0:` branch, entered
only when `bounded=True`):

`derived: sed -n '5903,5945p' spawn.py`
```
                watcher_log = Path(str(cwd) + ".watcher.log")
                try:
                    with watcher_log.open("a", encoding="utf-8") as wf:
                        wproc = subprocess.Popen(
                            [sys.executable, str(Path(__file__).resolve()),
                             "watch", "--issue", str(issue), "--role", role,
                             "--follow", "--self-heal",
                             "--stall-timeout", str(stall_timeout_min)],
                            stdin=subprocess.DEVNULL, stdout=wf,
                            stderr=subprocess.STDOUT, start_new_session=True,
                        )
                except OSError as exc:
                    ...
                    return 1
                _workspace_index_put(issue, role, str(cwd), str(log_path),
                                      watcher_pid=wproc.pid,
                                      watcher_armed_at=time.time())
                print(...)
                if no_wait:
                    ...
                    return 0
                return _await_bounded(events_path, offset_path,
                                       stall_timeout_min, log_path)
```

canonical: spawn.py:3985-4012, read this session, quoted verbatim
below (`_rearm_watcher_detached`, the #1149-verified shape):

`derived: sed -n '3985,4012p' spawn.py`
```
        try:
            with watcher_log.open("a", encoding="utf-8") as wf:
                wproc = subprocess.Popen(
                    [sys.executable, str(Path(__file__).resolve()),
                     "-C", resolved_cwd,
                     "watch", "--issue", str(issue), "--role", rearm_role,
                     "--follow", "--self-heal",
                     "--stall-timeout", str(stall_timeout_min)],
                    stdin=subprocess.DEVNULL, stdout=wf,
                    stderr=subprocess.STDOUT, start_new_session=True,
                )
        except OSError as exc:
            ...
            return 1
        d = _workspace_index_load()
        ...
        d[key] = {"work": work, "log": log_path,
                  "watcher_pid": wproc.pid, "watcher_armed_at": time.time()}
        WORKSPACE_INDEX.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        print(...)
        return 0
```

Both call `subprocess.Popen(..., start_new_session=True, stdin=DEVNULL,
stdout=<watcher log file>, stderr=STDOUT)` — the detachment shape
itself (the part #1133's own proposal assumed was already
caller-safe, citing this exact auto-arm code as its reference) is
identical between the two. The Popen call is not where the two paths
diverge.

## Two divergences, read from the quoted code above

canonical: spawn.py:5903-5945 and spawn.py:3985-4012 (quoted above,
same session read).

1. **Blocking vs. immediate return (primary candidate).**
   `_rearm_watcher_detached()` arms the watcher, writes the registry
   entry, and returns 0 in the same statement — its own process exits
   normally within milliseconds of the `Popen()` call. The auto-arm
   path, when the caller omits `--no-wait`, falls through into
   `_await_bounded(...)` (spawn.py:5943-5944) — a polling loop
   (`derived: grep -n "os.kill\|killpg" spawn.py` — no match inside
   `_await_bounded()`'s body, spawn.py:3616-3675, so the block itself
   never kills anything) that blocks the *arming* process for up to
   `stall_timeout_min` or until the first event fires. For as long as
   it blocks, the arming CLI invocation remains a live, non-`setsid`'d
   member of whatever bounded call spawned it. The forked
   session-runner child a few lines below (`child_pid == 0` branch)
   explicitly calls `os.setsid()` on itself (spawn.py:5947) — its own
   adjacent comment states staying attached to the caller's
   stdio/session blocks the child with the caller. The auto-arming
   *parent* branch never does the same for itself, and it is the one
   left sitting in `_await_bounded()`, holding the bounded call open
   for up to `stall_timeout_min` after the watcher was already spawned
   and registered.
2. **Missing `-C <cwd>`.** The auto-arm's watcher argv omits the `-C`
   flag `_rearm_watcher_detached()` gained in PR #1149
   (`11efcb0`). That prior fix addressed a *different* failure mode
   (the detached child's own roster lookup missing the repo-prefixed
   key and self-exiting) — not the caller-lifetime bug this issue
   reopens. `_lookup_roster_entry()` still has a role-suffix fallback
   when `repo` is `None` (spawn.py:3754-3760), so this gap alone would
   only surface as a failure when the same issue+role is armed for two
   repos at once. Kept as a secondary hardening item, not the primary
   fix.

## Live reproduction attempted from this session, inconclusive on divergence 1

canonical: this session's own transcript this turn —
`/tmp/repro2.py`, `/tmp/repro3.py`, `/tmp/repro4.py`, each executed
live (fork + `start_new_session=True` child spawned from a process
that itself then blocks, then is terminated via `timeout -s KILL` or
the Bash tool's own call-scoped teardown).

`derived: python3 /tmp/repro4.py` (fork, `os.setsid()` in the child,
`Popen(start_new_session=True)` in the parent, parent then sleeps 30s
simulating `_await_bounded`, parent's own bounded Bash call ends) —
the detached heartbeat child still wrote all 20 expected heartbeat
lines and was still running afterward in every variant tried; same
result for `/tmp/repro2.py` (parent SIGKILLed directly via
`timeout -s KILL 2`) and `/tmp/repro3.py` (no explicit fork). This
session's own sandbox did not reproduce a caller-lifetime death for
this shape.

canonical: the issue body (`gh issue view 1154`, read at the start of
this session) — its own "Pattern observed" paragraph names 8 issue
numbers whose initial watchers died vs. 3 re-arms that survived; that
count is the issue's own claim, not independently re-derived by this
survey.

canonical: same issue body (`gh issue view 1154`), same paragraph.
That inconclusive local result does not contradict the issue's field
report: the reported deaths are specifically from *orchestrator*
bounded/background Bash calls, a different harness context than this
role session's own Bash tool, and this session has no way to attach
its own Bash tool to that harness to confirm the exact OS-level
teardown mechanism (process-group signal vs. cgroup/namespace
teardown) it uses. Divergence 1 is still the change that makes the
auto-arm path structurally match `_rearm_watcher_detached()`'s
field-proven shape — return immediately after registering the
watcher, regardless of `no_wait` — without requiring that
confirmation first, since it removes the one place the two paths
differ in whether the arming process keeps the bounded call open
after the watcher is already spawned and registered.

## Existing test coverage

canonical: `derived: ls gates/test_watch_rearm_registry.py` — the file
exists (from #1133/#1149); its test class covers only
`_rearm_watcher_detached()`, no case exercises the spawn-time auto-arm
block in `_spawn_one()`. The issue's Acceptance check 1 asks for a
sibling case here: simulate the caller exiting and assert the watcher
process/registry pid survives.

## Write set for the fix

- `spawn.py` (the auto-arm block in `_spawn_one()`)
- `gates/test_watch_rearm_registry.py` (new auto-arm survival case)
