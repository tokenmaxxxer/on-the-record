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
