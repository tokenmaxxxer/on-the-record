---
proposal: docs/issue-947/proposals/monitor-unavailable-notice.md
---

# Hunt record — monitor-unavailable-notice

## before-landing — stance: assume this guard/detection mechanism goes silent when its own input is malformed — make it go silent

Verdict: FINDING — the session_id sanitizer's many-to-one character collapse lets one real session's marker files permanently silence the notice for a different, unrelated real session whose session_id sanitizes to the same string.
Kind: silent-failure
Seed: on-the-record/hooks/directive.sh monitor-notice block (`safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)`); on-the-record/monitors/poll-heartbeat.sh; on-the-record/hooks/test_monitor_notice.py
cap_seconds: 180
tier: size:>200
diff_stat_lines: >200 (directive.sh +182/-24, poll-heartbeat.sh new 96 lines, test_monitor_notice.py new, new ADR)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:20:00Z

### Reproduce
```
cd /tmp/mn2   # fresh dir
export TOKENMAXXXER_CHECKOUT=<repo>
export ORCHESTRATE_OFF=
unset CLAUDE_ROLE
export MONITOR_NOTICE_GRACE_SECONDS=1
HOOK=on-the-record/hooks/directive.sh

# Session A, session_id "sess/a" -> sanitizes to "sess_a". Genuinely
# monitor-unavailable (no alive marker). Runs to grace, gets notified once.
printf '{"session_id":"sess/a"}' | bash "$HOOK" >/dev/null
sleep 1.3
printf '{"session_id":"sess/a"}' | bash "$HOOK" > out5.txt
grep -c "idle self-wake" out5.txt   # -> 1 (correct: A was notified)

# Session B, a DIFFERENT real session_id "sess?a" -> also sanitizes to
# "sess_a" (re.sub maps both "/" and "?" to "_"). B is also genuinely
# monitor-unavailable and waits past its own grace window.
printf '{"session_id":"sess?a"}' | bash "$HOOK" >/dev/null
sleep 1.3
printf '{"session_id":"sess?a"}' | bash "$HOOK" > out6.txt
grep -c "idle self-wake" out6.txt   # -> 0 (WRONG: B never gets notified)
```

### Observed
Session B's second turn (past its own grace window, genuinely
monitor-unavailable, `alive` marker absent) prints nothing. The python
block reads `.orchestrate-monitor-alive/.session-sess_a-notified`, which
session A already created, so it takes the `if os.path.exists(notified_path):
sys.exit(0)` branch and treats session B as "already notified" even
though session B has never itself been checked past grace before. (The
same collision also makes session B's own *first* observation
mis-fire immediately instead of deferring, when A's start file is
already grace-stale — reproduced separately: B's very first turn prints
the notice instead of "nothing to check yet.")

### Expected
Each real session should get independent notice bookkeeping. Two
distinct `session_id` values that differ only in characters the
sanitizer maps identically (any two of `/ \ : * ? " < > | ` etc. all
collapse to the same `_`) silently share one session's start/notified
state, so the notice can go permanently silent for a session whose
Monitor is genuinely unavailable — exactly the case this feature exists
to surface — whenever an earlier, unrelated session's sanitized id
happens to collide.
