---
kind: current-state-survey
loop_state: handed-off
---

# Current-state survey — issue #927 (auto-arm watcher dies on stall/wall-clock instead of self-re-arming)

## Scope

canonical: `gh issue view 927`, read this session — reports that
`spawn.py`'s auto-armed detached watcher (`spawn.py watch --issue <n>
--role <r> --follow`, spawned at spawn.py:5088) plainly `return`s on
three non-session-end conditions, and that its "재무장하라" (re-arm)
stderr message is orphaned because auto-arm's stdout/stderr are
redirected to `<work>.watcher.log`, a file nothing reads for content.

No coding/qa/review record exists for issue-927 — canonical: `find
docs/issue-927` (before this survey's own writes) returned nothing —
the issue is itself the first diagnosis, asking this role to verify the
root-cause claim against current code before any fix is designed. This
survey reproduces the claim by direct code reading and grep against
spawn.py at `aaf7dac87f2be594b1a62b61b381a1788da852a5` (this branch's
base). No fix — that is out of scope for defect-verification and for
this phase.

code_under_review:
- spawn.py

## Finding 1 — three return paths kill `--follow` without re-arming, no mode distinguishes auto-arm from interactive

canonical: spawn.py, read this session, lines 3494-3497 (wall-clock cap):
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
canonical: spawn.py, read this session, `_watch`'s `while True:` loop
opening at line 3483 — all three quoted returns sit directly inside
that loop body. None of them loops back to re-invoke itself or re-exec
`spawn.py watch --follow`; two of the three (wall-clock, stall) print a
re-arm instruction, but none re-arms. `_watch` takes no parameter
distinguishing an auto-armed detached call from an interactive one:

derived: `grep -n "add_argument" spawn.py | grep -i "watch\|stall\|follow\|self.heal"`
```
4150:    ap.add_argument("--stall-timeout", type=float, default=5.0,
4152:    ap.add_argument("--role", dest="watch_role",
4154:    ap.add_argument("--follow", action="store_true",
```
No `--self-heal` (or any other mode) flag exists in the `watch`
subcommand's argument parser — the issue's proposed mode split has no
current counterpart to verify against; it is unbuilt, matching the
issue's own framing that structural fix design is out of scope for this
role.

## Finding 2 — auto-arm spawns the identical interactive command, with no distinguishing flag

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
canonical: spawn.py, read this session, the `argv` list quoted above —
it reads `watch --issue <n> --role <r> --follow --stall-timeout <n>`,
the same argv a human would type interactively. Nothing in this call
site, and (per Finding 1's citation of `_watch`'s signature and
argument parser) nothing in `_watch` itself, marks the process as
auto-armed, so the three stall/wall-clock/crash `return` paths quoted
in Finding 1 execute identically whether the watcher was armed by a
human or by this auto-arm code path.

## Finding 3 — auto-arm's stdout/stderr land in a file only ever read for mtime, not content

canonical: spawn.py, read this session, line 5089 (`stdout=wf,
stderr=subprocess.STDOUT` into the `watcher_log` opened at line 5085,
quoted in Finding 2).

derived: `grep -n "watcher_log\|watcher\.log" spawn.py`
```
2115:            watcher_log = Path(str(work) + ".watcher.log") if work else None
2116:            if armed_at is not None and watcher_log is not None and watcher_log.exists():
2117:                w_mtime = watcher_log.stat().st_mtime
2122:                        f"{int(silence_min)}분째 로그 무응답 ({watcher_log}) — "
5085:                watcher_log = Path(str(cwd) + ".watcher.log")
5087:                    with watcher_log.open("a", encoding="utf-8") as wf:
5103:                      f"(로그 {watcher_log})", file=sys.stderr)
```
canonical: spawn.py, read this session, lines 2115-2122 (the grep's
first match above) — the only read of `watcher_log` in the file checks
`watcher_log.stat().st_mtime`, a staleness/silence signal (watchdog
signal-6, cited by the issue); it never opens or parses the file's
text content. The "다시 spawn.py watch --follow 로 재무장하라" strings
from Finding 1 are written to a file whose sole reader inspects
modification time, never text: no code path in spawn.py surfaces that
string to a human or an orchestrator. This reproduces the issue's
"self-heal 지시가 고아가 된다" (self-heal instruction is orphaned)
claim.

## Finding 4 — no distinct "session ended without session-end" event exists for the crash path

canonical: spawn.py, read this session, line 3339 (`WATCH_CRASH_RC = 2
# `--follow`가 session-end 없이 pid 사망을 감지했을 때`) alongside
Finding 1's crash-path citation — the crash path prints to stderr and
returns a process exit code; it calls no `_append_event`/ledger-write
function there, so no fact of "ended without session-end" reaches
`events.jsonl` or any other durable log a downstream orchestrator could
read after the detached watcher process itself has exited. The issue's
proposed requirement (a durable event, distinct from a process exit
code / stderr line that Finding 3 shows nobody parses) has no current
implementation to verify against.

## Finding 5 — no existing test reproduces stall-survival-then-session-end for the auto-arm path

derived: `grep -rln "stall\|watcher\|auto.arm\|self.heal" tests/`
```
tests/test_silent_failure_repros.py
tests/test_spawn.py
```
canonical: tests/test_spawn.py, read this session — `grep -n
"stall_limit\|last_progress" tests/test_spawn.py` returns no match.
Every existing `--follow`/stall test in that file (e.g.
`test_follow_ignores_stall_and_keeps_going` at line 6615,
`test_follow_detects_dead_session_and_returns_crash_rc` at line 6631)
mocks `_await_bounded` to return 0 repeatedly to simulate a per-call
stall inside a single `_await_bounded` invocation, and asserts `_watch`
keeps looping across those calls — none of them drives `last_progress`
past `stall_limit_s` (the cumulative-wall-clock stall check quoted in
Finding 1) far enough to observe the bare `return 0`, and none spawns a
real detached `subprocess.Popen` auto-arm process to observe process
survival across that boundary or a subsequent real `session-end`
delivery. canonical: `gh issue view 927`'s Acceptance section, read
this session — its stated empty-state rule ("해당 테스트 부재 시 실패로
간주") is met here: the live-fire test it requires does not exist in
this tree.

## Conclusion

Every root-cause element the issue names is reproduced live against
current `spawn.py` (base `aaf7dac8`):
1. all three non-session-end `_watch` exits are plain `return`s with no
   re-arm loop (Finding 1);
2. auto-arm invokes the identical interactive `watch --follow` argv,
   with no flag or parameter distinguishing the two call modes
   (Finding 2);
3. the re-arm instructions those returns print are written only to
   `<work>.watcher.log`, a file whose sole reader inspects mtime, never
   content — the instruction is orphaned (Finding 3);
4. the crash path records no durable "ended without session-end" event,
   only a stderr line and a process exit code (Finding 4);
5. no test in `tests/` drives the cumulative stall_limit boundary,
   observes auto-arm process survival across it, or asserts a
   subsequent real session-end delivery (Finding 5) — the acceptance
   gate's live-fire test is genuinely absent, not merely unread.

The issue's diagnosis holds against the current codebase. No structural
fix is proposed or evaluated here — mode split, self-heal loop, and the
crash-path event are unbuilt design decisions that belong to
implementation, gated on this survey and the following proposal.

## Open findings

Findings 1-5 above all route to issue-927 phase 2 (implementation),
already scoped by the issue body: split `_watch`'s interactive-return
behavior from an auto-arm self-heal loop (a flag such as
`--self-heal`, gating the auto-arm-only branch off the three return
sites in Finding 1); keep the crash path as a terminal exit but add a
durable "ended without session-end" event write (Finding 4, ties to
issue #908's silent-death gap); and add the live-fire regression test
whose absence Finding 5 pins (canonical: `gh issue view 927`'s
Acceptance section, cited in Finding 5).

## What did not work

None.
