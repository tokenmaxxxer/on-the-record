---
proposal: docs/issue-706/proposals/2026-08-11-presence-only-hooks-session-role-bind.md
---

# Hunt record — presence-only-hooks-session-role-bind

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — an orchestrator session (never legitimately CLAUDE_ROLE-bound) can forge `CLAUDE_ROLE` at runtime to bypass deliverable-guard.sh (and by the identical resolve pattern, retry-loop-bound.sh and decision-queue-stopgate.sh), because session-role-bind.sh only writes a snapshot when CLAUDE_ROLE is already set at SessionStart, so an orchestrator session simply has no snapshot to contradict a later forged env var, and the hooks' fallback-to-live-env-var-when-no-snapshot path accepts it uncontested.
Kind: composition
Seed: git diff -- on-the-record/hooks/deliverable-guard.sh on-the-record/hooks/decision-queue-stopgate.sh on-the-record/hooks/retry-loop-bound.sh on-the-record/hooks/role-test-claim-guard.sh
cap_seconds: 180
tier: default
diff_stat_lines: ~190 (4 files)
started_at: 2026-08-11T11:42:00+09:00
ended_at: 2026-08-11T11:56:00+09:00

### Reproduce
```bash
cd on-the-record-issue-706-implementation
export TMPDIR=/tmp
STATE_DIR="$TMPDIR/otr-role-bind"
mkdir -p "$STATE_DIR"
SID="orch-sess-1"
python3 -c "import os; p='$STATE_DIR/$SID.json'; os.path.exists(p) and os.remove(p)"
# confirm no snapshot exists for this session (true for every real orchestrator
# session, since session-role-bind.sh no-ops when CLAUDE_ROLE is unset at
# SessionStart -- see the `[ -n "${CLAUDE_ROLE:-}" ] || exit 0` guard there)

payload=$(python3 -c 'import json; print(json.dumps({"session_id":"orch-sess-1","tool_name":"Write","tool_input":{"file_path":"src/foo.py","content":"x"}}))')

unset CLAUDE_ROLE
echo "$payload" | bash on-the-record/hooks/deliverable-guard.sh; echo "rc=$?"   # rc=2, correctly denied

export CLAUDE_ROLE=fake-role   # orchestrator forges the env var mid-session
echo "$payload" | bash on-the-record/hooks/deliverable-guard.sh; echo "rc=$?"   # rc=0
```

### Observed
First call (genuine orchestrator, no forged env var): `rc=2`, denied as expected
("this is an orchestrator session and src/foo.py is a deliverable path...").

Second call, same session_id, same payload, only `CLAUDE_ROLE=fake-role` exported
at runtime: `rc=0` — the write is silently allowed. No snapshot file exists for
`orch-sess-1` at any point (verified before running), so the hook's
`except (OSError, ValueError): pass # no snapshot yet — fall back to the live
env var` path is taken, and the live (forged) env var is trusted outright.

### Expected
The #698/#706 fix's stated goal is that CLAUDE_ROLE identity should be
resolved from the SessionStart-bound snapshot rather than the live env var,
specifically so the env var can't be manipulated mid-session to flip a hook's
branch. That only holds for sessions that had a snapshot recorded (real role
sessions unsetting CLAUDE_ROLE). Sessions that never had a snapshot recorded —
every real orchestrator session, since session-role-bind.sh only snapshots
when CLAUDE_ROLE is already set at SessionStart — get no protection at all:
the "fall back to live env var when no snapshot exists" branch means an
orchestrator can forge CLAUDE_ROLE at any point in the session to escape
deliverable-guard.sh's deny (and, by the same fallback pattern, retry-loop-
bound.sh's retry cap and decision-queue-stopgate.sh's nudge/block), which is
the mirror-image of the exact attack #706 claims to close.
