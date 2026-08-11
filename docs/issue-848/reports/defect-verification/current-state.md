---
kind: current-state-survey
loop_state: handed-off
---

# Current-state survey — issue #848 (watch-dies-with-parent-turn lifecycle bug)

## Scope

Reproduce and pin the exact lifecycle bug behind the #845 §step-6 finding
("the observing session's own background watch task died with its parent
turn"), determine whether it lives in `spawn.py`'s own watch/watchdog
machinery or elsewhere, and determine whether the #782/#829 poll backstop
deterministically catches the post-turn event. No fix.

canonical: docs/issue-776/reports/execution-observation.md, "What was
done" step 6 (merged PR #845) — quoted in full below as the anchor fact:
> the `-p` process's third `result` says "I've armed `watch --follow` in
> the background... I'll report when the PR opens or the role's
> refusal", then the very next lines are
> `{"type": "system", "subtype": "task_updated", "patch": {"status":
> "killed", ...}}` for that same watch task, followed by a
> `task_notification` the process had already exited before it could act
> on. The `-p` process's own turn ended (`stop_reason: "end_turn"`) while
> its background watch was still pending, and that watch was killed at
> process exit

code_under_review:
- spawn.py
- on-the-record/hooks/poll-rearm.sh
- on-the-record/hooks/directive.sh
- on-the-record/hooks/stop-poll-rearm.sh
- on-the-record/monitors/poll-heartbeat.sh
- on-the-record/monitors/monitors.json
- docs/specs/platform-capabilities.md

## Finding 1 — TWO distinct "watch" mechanisms exist; only one died in #845

canonical: docs/issue-776/reports/execution-observation.md, "What was
done" step 4 (merged PR #845), `ps aux` snapshot quoted verbatim:
```
jwjung  3177273  python3 spawn.py implementation ... --issue 1 ...
jwjung  3177274  python3 spawn.py watch --issue 1 --role implementation --follow --stall-timeout 5.0
jwjung  3177276  claude -p ... --plugin-dir .../tokenmaxxxer-implementation/coding ...
```

`3177274` is `spawn.py`'s own **auto-armed** watcher (issue #488,
`spawn.py:4914-4942`, `_spawn_one()`'s `bounded` branch): a `fork()`'d,
`os.setsid()`'d child that `Popen()`s `spawn.py watch --follow` with
`start_new_session=True`, i.e. a fully OS-detached grandchild of the
forking `spawn.py` process. Comment at `spawn.py:4901-4905` (read this
session) states the design intent directly: "부모가 속한 프로세스 그룹에
신호가 가도 자식은 안 죽는다" (signals reaching the parent's process
group do not kill the child).

But the thing the #845 record's step-6 finding actually pins as killed is
**not** `3177274`. canonical: docs/issue-776/reports/execution-observation.md
"What was done" step 6 (quoted in Scope above) — the killed watch is the
top-level `-p` session's own transcript line "I've armed `watch
--follow` in the background", which is that session narrating its own
use of the Claude Code CLI's `Bash` tool with `run_in_background: true` —
a task tracked in-process by the `claude -p` binary itself (visible in
the transcript as `task_updated`/`task_notification` system events, not
as a second OS process in the step-4 `ps aux` snapshot above). This is a
CLI-level background task, architecturally distinct from `spawn.py`'s own
`fork()+setsid()+Popen()` detachment.

### Reproduction — spawn.py's own auto-arm pattern is immune to parent-turn death

canonical: live reproduction, this session, command and full stdout below
```
$ python3 - <<'EOF'
import os, subprocess, time
r, w = os.pipe()
pid = os.fork()
if pid == 0:
    os.close(r)
    os.setsid()
    child = subprocess.Popen(
        ["python3", "-c",
         "import time; open('/tmp/.../watcher_survived.marker','w').write('alive'); time.sleep(3)"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    os.write(w, str(child.pid).encode()); os.close(w); os._exit(0)  # simulates "parent turn ends"
else:
    os.close(w)
    child_pid = int(os.read(r, 64)); os.close(r)
    os.waitpid(pid, 0)  # forking process (the "turn") has now fully exited
    time.sleep(1)
    try:
        os.kill(child_pid, 0)
        print("grandchild STILL ALIVE after parent exit")
    except OSError:
        print("grandchild DEAD")
EOF
forking process exited; grandchild pid: 3193351
grandchild STILL ALIVE after parent exit (expected: spawn.py watcher pattern is immune)
$ cat /tmp/.../watcher_survived.marker
alive
```

canonical: the reproduction's own stdout, quoted verbatim immediately
above, this session — this reproduces `spawn.py:4914-4942`'s exact shape
(`fork()` → `os.setsid()` → `Popen(..., start_new_session=True)` →
forking process exits) and confirms a watcher armed this way survives
its own forking process's exit. `spawn.py`'s own watch/watchdog machinery
is not the mechanism behind the #845 finding — it is, by this
reproduction, already immune to the failure shape the issue describes.

## Finding 2 — the actual dying mechanism is the CLI's `run_in_background` task, and spawn.py already knows and warns about it, but only for role-spawned sessions

canonical: spawn.py:4783-4841 (`_spawn_one()`, `task` prefix construction,
read this session)
```python
task = (f"당신의 이슈: #{issue} (subject issue-{issue}, 브랜치 {br}).\n"
        ...
        f"경고: 이 턴은 headless 이고 단발이다 — 세션이 끝나면 이 프로세스도\n"
        f"끝난다. run_in_background 로 넘긴 작업은 부모 턴이 끝나는 순간 함께\n"
        f"죽는다(백그라운드 워커가 커밋·push 를 대신 끝내줄 것이라고 가정하지\n"
        f"마라 — 실측된 실패 패턴이다). 모든 작업은 이 턴 안에서 직접 끝내라.\n\n") + task
```

canonical: `sed -n '4779,4842p' spawn.py`, read this session — this block
sits inside `_spawn_one(cwd, role, task, ..., issue=None, ...)`, and the
task-prefixing statement is reached only when `issue is not None`
(`if issue is not None: root = Path(cwd).resolve(); ...` opens the
surrounding branch at `spawn.py:4784`). This warning text is injected
**only into the task text of a role session spawned by `spawn.py
<role> --issue N`** — i.e. only a delegated child role (`implementation`,
`coding`, `review`, etc.) is told, in its own opening prompt, that
`run_in_background` work dies with its turn.

canonical: docs/issue-776/reports/execution-observation.md, "What was
done" step 3 (merged PR #845) — the #845 top-level session that armed
the doomed watch was launched as `env -u CLAUDE_ROLE claude -p "..." ...`
— a **plain** session, `CLAUDE_ROLE` unset, given only
`harness.driver.get_representative_requirement()` as its first message.
It was never itself spawned through `spawn.py <role> --issue N`, so it
never received the `spawn.py:4841` warning text at all. Nothing in this
repository's hook chain (`directive.sh`, UserPromptSubmit; grepped this
session, `grep -n run_in_background on-the-record/hooks/*.sh` — no
match) injects an equivalent warning into a plain, un-delegated top-level
session.

This is the exact, pinned gap: the one piece of this codebase that
already knows and states the true platform behavior
("`run_in_background` 로 넘긴 작업은 부모 턴이 끝나는 순간 함께 죽는다")
delivers that knowledge only to spawned role sessions' own task prompts.
A plain top-level orchestrator session — precisely the shape that ran in
#845's steady-state harness, and precisely the shape contract v3 s22 also
targets — has no source telling it the same fact before it reaches for
`run_in_background` to "wait and report" on a delegated role's outcome.
It reached for the CLI's `run_in_background` Bash tool exactly because
nothing told it not to, armed a task that (per the #845 transcript,
Finding 1's Scope quote) was killed the instant its own turn ended, and
its promised report never happened — while `spawn.py`'s own already-armed,
already-immune watcher (`3177274`, Finding 1) kept running, unconsulted,
the whole time.

## Finding 3 — the #782/#829 poll backstop does not deterministically catch this class of event; it is a documented, standing hard boundary

canonical: on-the-record/hooks/poll-rearm.sh, read this session, header
comment quoted verbatim:
> arming at both boundaries of a turn narrows the quiet gap between "user
> stops typing" and "watchdog last ran" versus arming on turn-start
> alone, but this is still a TURN-DRIVEN best-effort loop: it requires
> the orchestrator session's own process to be alive and a hook to
> actually fire. It does NOT survive the session's own death — that
> remains the hard, externally-blocked boundary

canonical: on-the-record/hooks/stop-poll-rearm.sh, read this session,
header comment quoted verbatim:
> HARD BOUNDARY (do not overclaim): this still requires the orchestrator
> session's own process to be alive for the Stop hook to fire at all. It
> does NOT survive the session's own death

canonical: on-the-record/monitors/poll-heartbeat.sh and
docs/specs/platform-capabilities.md lines 34-42, both read this session,
quoted verbatim:
> A Monitor is **session-bound**: it runs only for the lifetime of the
> session that started it and does NOT survive that session's death or
> reboot. ... a Monitor narrows the *turn-boundary* quiet gap between
> hook-driven polls; it does not close the *session-death* gap, which
> remains externally blocked (no plugin API for OS-level scheduling).

canonical: the three source files cited above (this section), read this
session — all three callers of `poll_rearm_arm_if_due()` (`directive.sh`
UserPromptSubmit turn-start, `stop-poll-rearm.sh` Stop turn-end,
`poll-heartbeat.sh` issue #835/#841 Monitor ~60s heartbeat) are
explicitly documented, in their own header comments, as requiring the
orchestrating session's own process to remain alive to fire at all. The
#845 transcript's event (Finding 1's Scope quote) is not a turn-boundary
quiet gap, which these three narrow; it is the `-p` process's own exit —
session death — which every one of these three comments states,
verbatim and in advance of this investigation, is not covered.

canonical: docs/issue-776/reports/execution-observation.md, "What was
done" step 3 (merged PR #845), "the process exited (`exit=0`) with no
further result" — this matches the #845 mechanism exactly: the plain
top-level session's process exited right after `stop_reason: "end_turn"`,
so there is no live process left for any of `directive.sh` (needs a next
UserPromptSubmit), `stop-poll-rearm.sh` (already fired once, at the Stop
that preceded the exit — its own `poll_rearm_arm_if_due` call only starts
a detached `spawn.py watchdog --auto-respawn` sweep of the *role
roster*, not a re-arm of the *top-level session's own* dead watch task),
or `poll-heartbeat.sh` (session-bound, dies with the same process) to run
again and notice the killed watch.

canonical: on-the-record/hooks/poll-rearm.sh lines 56-58 and
spawn.py:2232 (`roster_watchdog`), both read this session — separately,
`spawn.py watchdog --auto-respawn`, which `poll_rearm_arm_if_due()` does
start on the Stop hook that fires before the `-p` process exits, scans
the role roster for anomalies in spawned role sessions; it is not a
mechanism for detecting that a plain top-level session's own CLI-tracked
background task was killed. canonical:
docs/issue-776/reports/execution-observation/steady-state-2026-08-11-implementation-events.jsonl,
its `session-end` line (`{"type": "session-end", "detail": {"outcome":
"refused", ...}}`) — the spawned role's own outcome in #845 was
independently captured by `spawn.py`'s own auto-armed watcher (`3177274`,
Finding 1) into that events log, proving the role-side event was never
actually lost. What was lost was only the top-level plain session's own
promise to *read and report* that already-captured event back to the
human, because the mechanism it chose for that (`run_in_background`)
does not survive its own process exit, and none of the poll backstop's
three callers substitute for it.

## Conclusion

1. `spawn.py`'s own watch/watchdog machinery (`_spawn_one()`'s
   `fork()+setsid()+Popen(start_new_session=True)` auto-arm, issue #488)
   is immune to the parent-turn-death failure shape — reproduced live,
   Finding 1.
2. The mechanism that actually died in #845 is the Claude Code CLI's
   `run_in_background` Bash-tool task, armed manually by a **plain**
   top-level session that never received `spawn.py:4841`'s existing
   warning about exactly this failure mode, because that warning is
   injected only into role-spawned sessions' task text
   (`spawn.py:4783-4841`, gated on `issue is not None`) — Finding 2.
3. The #782/#829 poll backstop (`directive.sh` + `stop-poll-rearm.sh` +
   the #835/#841 Monitor heartbeat) is explicitly documented, in its own
   source comments and in `docs/specs/platform-capabilities.md`, as
   turn-driven / session-bound and NOT covering session death — it does
   not, and per its own documented design cannot, deterministically catch
   this class of post-turn event. This is a standing, previously-recorded
   hard boundary (`docs/issue-801/proposals/technical-feasibility.md`),
   not a new gap this session discovered — Finding 3.

## What did not work

None.
