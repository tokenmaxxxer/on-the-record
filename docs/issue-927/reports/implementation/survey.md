# Current-state survey — issue #927 implementation, phase 1

canonical: `find docs/issue-927` (before this survey's own writes)
returned only `proposals/defect-verification.md` and
`reports/defect-verification/current-state.md` — no implementation
record exists yet; this survey is the first for this role.

## Write surface

canonical: `grep -n "WATCH_CRASH_RC\|WATCH_WALLCLOCK_RC" spawn.py` —
every reference to these constants, and the auto-arm `Popen` argv,
resolves inside `spawn.py`. No other file in the tree constructs that
argv or imports these constants, so `spawn.py` is the sole write
surface for the fix itself.

## Finding 1 — three return paths, no mode distinguishes auto-arm from interactive

canonical: spawn.py, read this session, lines 3494-3497 (wall-clock
cap):
```
            if remaining <= 0:
                print(f"[watch] follow wall-clock cap 도달 — 다시 spawn.py "
                      f"watch --follow 로 재무장하라", file=sys.stderr)
                return WATCH_WALLCLOCK_RC
```
canonical: spawn.py, read this session, lines 3548-3550 (crash / pid
loss):
```
        if pid is not None and not _alive(pid):
            print(f"[watch] 세션 프로세스가 사라졌다(pid {pid}) — session-end "
                  f"없이 끝났다. 크래시로 보고 멈춘다", file=sys.stderr)
            return WATCH_CRASH_RC
```
canonical: spawn.py, read this session, lines 3553-3556 (follow-stall):
```
        if time.monotonic() - last_progress >= stall_limit_s:
            secs = int(time.monotonic() - last_progress)
            print(f"[watch] follow stall: {secs}초째 진행 없음 — 이벤트도 "
                  f"로그 변화도 없이 멈춘다. 다시 spawn.py watch --follow 로 "
                  f"재무장하라", file=sys.stderr)
            return 0
```
canonical: spawn.py, read this session, `_watch`'s signature at lines
3422-3424 — `follow`, `stall_timeout_min`, `repo`, `max_wait_min` are
its only parameters; none marks a call as auto-armed vs interactive.

canonical: `grep -n "add_argument" spawn.py | grep -i
"watch\|stall\|follow\|self.heal"` returns `--stall-timeout` (4150),
`--role`/watch_role (4152), `--follow` (4154), `--max-wait` (4157) —
no `--self-heal` or other mode flag exists in the parser.

## Finding 2 — auto-arm spawns the identical interactive argv

canonical: spawn.py, read this session, lines 5085-5093:
```
                watcher_log = Path(str(cwd) + ".watcher.log")
                try:
                    with watcher_log.open("a", encoding="utf-8") as wf:
                        wproc = subprocess.Popen(
                            [sys.executable, str(Path(__file__).resolve()),
                             "watch", "--issue", str(issue), "--role", role,
                             "--follow", "--stall-timeout", str(stall_timeout_min)],
                            stdin=subprocess.DEVNULL, stdout=wf,
                            stderr=subprocess.STDOUT, start_new_session=True,
                        )
```
canonical: the argv quoted above, same read — it is `watch --issue <n>
--role <r> --follow --stall-timeout <n>`, the same argv a human would
type interactively; nothing in it or in `_watch`'s parameters (Finding
1) marks this call auto-armed.

## Finding 3 — the re-arm hint is orphaned

canonical: spawn.py, read this session, line 5089
(`stdout=wf, stderr=subprocess.STDOUT`, quoted in Finding 2) — auto-arm
redirects the child's stdout/stderr into `watcher_log`.

canonical: `grep -n "watcher_log" spawn.py` — the only other reference
is lines 2115-2122, inside the roster watchdog's signal-6
(`watcher-silent`) check:
```
2115:            watcher_log = Path(str(work) + ".watcher.log") if work else None
2117:                w_mtime = watcher_log.stat().st_mtime
```
canonical: spawn.py lines 2115-2122, same read — this code reads only
`watcher_log.stat().st_mtime`, never the file's text, so the re-arm
strings Finding 1 quotes are written to a file nothing parses for
content.

## Finding 4 — no durable event on the crash path

canonical: spawn.py, read this session, lines 2752-2763 —
`_append_event(events_path, ev_type, detail)` appends a
`{"ts","type","detail"}` line to `<work>.events.jsonl`; this is the
mechanism every other lifecycle event (`session-start`, `session-end`,
`pr-opened`) uses.

canonical: `grep -n "_append_event" spawn.py` returns no call between
lines 3422 and 3557 — `_watch`'s three return paths (Finding 1) write
no durable event. `work`/`events_path` are already local to `_watch`
(spawn.py:3436-3437, same read), so an event write from inside `_watch`
needs no new plumbing.

## Finding 5 — watchdog detection already exists (context, unchanged)

canonical: spawn.py, read this session, lines 2093-2123 — signal-5
(`watcher-dead`, 2098-2106) and signal-6 (`watcher-silent`, 2108-2123)
already detect a dead/stalled auto-arm watcher from the roster side.
This survey's write set does not touch these lines; they are cited only
because self-heal must not duplicate what they already detect.

## Finding 6 — no live-fire stall-survival test exists

canonical: `grep -n "def test_.*watch\|def test_.*follow\|def
test_.*stall" tests/test_spawn.py` returns 25 matches.

canonical: tests/test_spawn.py, read this session — `grep -n
"stall_limit\|last_progress" tests/test_spawn.py` returns no match.
Every existing test (e.g. `test_follow_ignores_stall_and_keeps_going`,
`test_follow_detects_dead_session_and_returns_crash_rc`) mocks
`_await_bounded` to simulate a per-call stall; none drives
`last_progress` past the cumulative `stall_limit_s` boundary or spawns
a real detached auto-arm subprocess to observe survival plus a
subsequent real `session-end`.

canonical: `gh issue view 927`'s Acceptance section, read this session
— its stated empty-state rule ("해당 테스트 부재 시 실패로 간주") is met:
this live-fire test does not exist in this tree.

## Conclusion

canonical: Findings 1-6 above, this survey — the mechanism
docs/issue-927/proposals/defect-verification.md already verified live
(PR #932, merged; canonical: `gh pr view 932 --json state,mergedAt`)
still holds against the current tree read this session: no mode split,
no self-heal loop, no crash-path durable event, no live-fire test.

## Scout

canonical: `gh issue view 927`'s "구조적 수정 방향" section, read this
session — it already names the fix shape (mode-split flag, self-heal
loop for auto-arm only, crash path stays terminal but durable-events
its end). There is no external product-shaped surface here — an
internal process-supervision retry loop — to scout against a category's
best-in-class; only implementation choices remain, inside the
`_watch`/`_append_event`/`argparse` machinery Findings 1-4 located.
