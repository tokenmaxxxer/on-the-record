---
proposal: build-now, issue-2874
---

# Hunt record — reconcile-crash-verdict-race

## before-landing — stance 0: assume the check this diff just added is bypassable — find the bypass

Verdict: FINDING — `session_end_verdict(..., wrapper_pid=...)`'s new dead-child-but-wrapper-alive branch trusts a bare `os.kill(wrapper_pid, 0)`, which only proves *some* process currently holds that PID number, not that it is the original wrapper — so once a roster entry's real wrapper dies uncleanly (crash, before writing `session-end`), the stale `wrapper_pid` field left behind reads as "alive" the moment the OS reissues that PID number to *any* unrelated process, permanently flipping a genuine crash to `in-progress`/COMPLETED — suppressing `_auto_respawn_check()`'s respawn forever, and for no-issue (adhoc) entries, making `roster_watchdog()` call `roster_remove()` and erase the crash from the roster entirely.
Kind: silent-failure
Seed: build-now diff — board.py `session_end_verdict(wrapper_pid=...)`, spawn.py `_build_observed()`, lifecycle.py `_auto_respawn_check()`, watchdog.py `diagnose_health()` / `roster_watchdog()`
cap_seconds: 180
tier: size:large
diff_stat_lines: 221
started_at: 2026-08-30T09:05:00Z
ended_at: 2026-08-30T09:16:00Z

### Reproduce

```
cd <repo>
python3 - <<'PYEOF'
import sys, os, json, tempfile, time, subprocess
sys.path.insert(0, ".")
import board, spawn as sp, watchdog as wd

tmp = tempfile.mkdtemp()
work = os.path.join(tmp, "workspace")
os.makedirs(work, exist_ok=True)
events_path = sp._events_path(work)

# A child (claude) pid that has genuinely exited -- os.kill(pid,0) fails on it.
p = subprocess.Popen(["true"]); p.wait()
dead_child_pid = p.pid

# session-start only, no session-end ever written -- a real crash mid
# post-processing (wrapper died before push/gate/classify/ledger_write
# finished and appended session-end).
with open(events_path, "w") as f:
    f.write(json.dumps({"type": "session-start",
                         "detail": {"pid": dead_child_pid, "ts": time.time() - 600}}) + "\n")

# roster entry for this crashed session. wrapper_pid holds a PID number
# that merely happens to be alive right now for an UNRELATED process --
# standing in for the real wrapper's PID getting reissued by the OS after
# the real wrapper died without ever touching this entry again.
entry = {"pid": dead_child_pid, "work": work, "log": None, "issue": None,
         "expects_pr": False, "wrapper_pid": os.getpid()}

print("verdict:", board.session_end_verdict(work, None, wrapper_pid=entry["wrapper_pid"]))
print("diagnose_health:", wd.diagnose_health("adhoc/demo/1", entry, root=sp.ROOT))
PYEOF
```

### Observed

```
verdict: in-progress
diagnose_health: {'state': None, 'next_action': 'none', 'detail': 'ADHOC (no task recorded) — completion, not a health diagnosis', 'dirty_files': 0, 'minutes_since_checkpoint': None}
```

(Control run: the same fixture with `wrapper_pid` omitted correctly returns `verdict: crashed`.)

Tracing the consequences with the entry shape above:
- `lifecycle._auto_respawn_check()`: `verdict = session_end_verdict(..., wrapper_pid=entry.get("wrapper_pid"))` -> `"in-progress"` -> `if verdict != "crashed": return` — respawn is never queued, permanently, for a session that never produced a `session-end` and never will.
- `watchdog.roster_watchdog()`: for this adhoc shape (`expects_pr=False`, no issue), `dead_health["state"] is None` -> `roster_remove(key)` fires on the same tick — the roster entry (the only record that this session ever existed and died) is deleted outright.

### Expected

A dead child pid with no `session-end` event should read as `crashed` unless the caller can prove the *specific* wrapper process that owns this roster entry is still driving it to completion — not merely that some process, any process, is currently alive under the PID number cached in the entry. `alive_fn(wrapper_pid)` (a bare `os.kill(pid, 0)`) cannot distinguish "the original wrapper is still running" from "the OS reissued that PID number to something else after the wrapper died" — there is no process-identity check (start-time, cmdline, or similar) tying `wrapper_pid` back to the specific process that was forked for this roster entry.
