---
proposal: docs/issue-534/proposals/2026-08-09-session-end-durability.md
---

# Hunt record — session-end-durability

## after-proposal — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — the proposed placement of `_post_session_end_comment()` inside `roster_watchdog()`'s dead-entry branch is cancelled by `roster_remove()`'s synchronous self-cleanup in the *same process* that ran the session, so no watchdog tick can ever observe a `normal`-verdict dead roster entry to comment on.
Kind: composition
Seed: docs/issue-534/proposals/2026-08-09-session-end-durability.md — "Call `_post_session_end_comment()` from `roster_watchdog()` (spawn.py:~1940-1948) alongside the existing `reconcile()` / `_auto_respawn_check()` calls"
cap_seconds: 120
tier: default
diff_stat_lines: docs-only proposal, ~5KB (no code diff yet)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:20:00Z

### Reproduce

`spawn.py:3988` (`_spawn_one()`, right after `proc.wait()`) already calls
`roster_remove(roster_key)` unconditionally, for every session end
regardless of verdict — this is the exact mechanism the codebase's own
`_self_trigger_respawn()` docstring (spawn.py:2360-2367) names as the
reason the `crashed` path had to be special-cased with an in-process
trigger instead of relying on a later watchdog tick: "`roster_remove()`
가 `proc.wait()` 직후 동기적으로 로스터 엔트리를 지우고 ... 이후 어떤
워치독 틱도 dead-but-registered 엔트리를 볼 수 없다".

The proposal's plan for the *new*, `normal`-verdict comment does not
apply that same fix — it plans to hang `_post_session_end_comment()` off
`roster_watchdog()`'s `if not _alive(e.get("pid", 0))` scan branch
(spawn.py:1933-1949), the very branch the crashed-path fix says can never
see a dead entry for a session that already cleaned itself up.

```
$ cat > repro_tmp_hunt2.py <<'PY'
import sys; sys.path.insert(0, ".")
import spawn
spawn.roster_register("role-1", {"pid": 999999, "issue": 42, "work": "/tmp/w", "log": "/tmp/l"})
spawn.roster_remove("role-1")   # what spawn.py:3988 does on every session end, any verdict
d = spawn._roster_load()
print("roster entries visible to the next watchdog tick:", d)
print("role-1 present for session-end comment to fire on?", "role-1" in d)
PY
$ python3 repro_tmp_hunt2.py
```

### Observed

```
roster entries visible to the next watchdog tick: {}
role-1 present for session-end comment to fire on? False
```

The roster entry is gone before any watchdog tick runs — `_roster_load()`
returns an empty dict for the key that just ended normally. Placing
`_post_session_end_comment()` inside `roster_watchdog()`'s dead-entry loop
means it will never fire for the ordinary case (session ends between
ticks, which is the common case since `_spawn_one()` removes its own
entry synchronously right after exit, not on the watchdog's schedule).

### Expected

The proposal should either (a) call `_post_session_end_comment()` from
inside `_spawn_one()` itself right where `session-end`/`roster_remove()`
already fire (spawn.py:~3988, the same place `_self_trigger_respawn()`
was forced to move to for the analogous `crashed` case), or (b) explicitly
account for why the roster-scan placement is safe here when the repo's
own prior finding says it isn't for the structurally identical
dead-entry-visibility problem. As written, "call it from
`roster_watchdog()`'s dead-entry branch" and "`roster_remove()` runs
synchronously in `_spawn_one()` before any tick" are two rules that are
individually fine and, composed, leave `verdict == "normal"` sessions
without a comment on the fast/common path — exactly the gap the
`--unreported` reconcile sweep is supposed to catch after the fact, except
now the sweep's own "acknowledgment = marker comment present" freshness
check will report *every* normally-ended session as unreported forever,
since the comment step it's checking for never runs.

## before-landing — stance 0: assume the gate/guard just added is bypassable — find the bypass

Verdict: FINDING — `spawn.py reconcile --unreported` detects session-end(normal) entries missing the `[watch]` marker comment, but never posts the comment: `_roster_reconcile_unreported()` only `print()`s "미보고" and returns a count — it never calls `_post_session_end_comment()` or issues any `gh api .../comments` write. The durability guarantee's stated recovery path for the exact scenario cited in the proposal (process killed between session-end event append and comment call) is detect-only, not self-healing, contrary to the docstring's framing ("오케스트레이터가 아무 때나 한 번의 호출로 회복하는 창구" — "a window the orchestrator can recover through with a single call").
Kind: silent-failure
Seed: spawn.py `_post_session_end_comment` (2298-2333), `_roster_reconcile_unreported` (1968-2010), `roster_reconcile` (2011-2036), `roster_watchdog` best-effort call (1944-1954), `_spawn_one` call site (4249), plus test_spawn.py and on-the-record/commands/run.md; ~250 lines touched
cap_seconds: 180
tier: default (size:>200 lines)
diff_stat_lines: ~250
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:20:00Z

### Reproduce
```
python3 - <<'PYEOF'
import sys, subprocess
sys.path.insert(0, "/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-534-implementation")
import spawn

calls = []
orig_run = subprocess.run
def spy_run(cmd, *a, **kw):
    calls.append(cmd)
    return orig_run(cmd, *a, **kw)
subprocess.run = spy_run

spawn._workspace_index_load = lambda: {
    "issue-999/worker": {"work": "/tmp/fake-workspace-999", "log": "/tmp/fake-999.log"}
}
spawn.session_end_verdict = lambda work, log: "normal"
spawn._issue_comments = lambda root, number: ([], True)  # marker absent -> flagged unreported

n = spawn._roster_reconcile_unreported(999)
print("unreported count returned:", n)
posting_calls = [c for c in calls if isinstance(c, list) and "comments" in " ".join(c)]
print("comment-posting subprocess calls made:", posting_calls)
PYEOF
```

### Observed
```
[reconcile --unreported] issue-999/worker: session-end(normal) 미보고 — issue #999, work=/tmp/fake-workspace-999, log=/tmp/fake-999.log
unreported count returned: 1
comment-posting subprocess calls made: []
```
The scenario is flagged as unreported (count=1, printed) but no `gh api repos/.../issues/999/comments` call — or any other comment-posting call — is made. The `[watch]` marker never lands on the issue. A human/cron who runs `spawn.py reconcile --unreported` and doesn't separately wire up posting from its stdout will see the durability gap "detected" forever without it ever closing. This matches the CLI's own `--unreported` help text, which says the flag "찍는다" (prints), not "posts" — unlike `closure-sweep --post`, `reconcile` has no `--post` companion flag to actually deliver the comment for unreported entries.

### Expected
For the "durable session-end reporting" guarantee to actually hold across the crash-between-event-and-comment scenario the proposal names, `_roster_reconcile_unreported()` (or a `--post`-gated companion) should call `_post_session_end_comment()` for each flagged entry so the marker comment actually gets posted — not just print a line that requires a human to notice and act on out-of-band.
