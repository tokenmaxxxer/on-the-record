
## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the proposed hook point (_PROGRESS_BASH_PREFIXES match at spawn.py:4812) cannot run "immediately before" the session's own commit/PR-open, because that match fires inside the parent orchestrator's `for line in proc.stdout:` loop (spawn.py:4725) reading NDJSON asynchronously streamed from the `claude` subprocess (`proc = subprocess.Popen(...)`, spawn.py:4630) — a separate OS process from the one that actually runs `git commit`/`gh pr create` inside the session. This site today only appends a log event (`_append_event(..., "progress", ...)`); it has no mechanism to block/delay the child's tool execution. By the time the parent's line-by-line JSONL scan reaches the `tool_use` block naming `git commit`, the session's own Bash tool has already been dispatched (or already run) that command — there is no synchronization point that guarantees the parent's proposed recut-helper call completes in the shared workspace before the child's real commit/PR-create executes. So a session absorbed mid-run would still race: the recut (if it runs at all before the child moves on) is not actually interposed before the failing command, and could just as easily run after the child's `git commit`/`gh pr create` has already failed with "No commits between main and issue-<n>/<role>" — i.e. the fix as scoped to this hook point does not give the "gate mechanically enforced" guarantee the proposal claims, since observation of a bash-prefix in the streamed transcript is not the same as gating that bash call's execution (unlike the real PreToolUse hook mechanism at spawn.py:3456 used by contract-guard.sh, which is synchronous and can refuse via exit 2).
Kind: design-error
Seed: docs/issue-784/proposals/absorbed-branch-mid-run-recut.md
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only proposal, no code diff yet)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce
```
grep -n "_PROGRESS_BASH_PREFIXES" spawn.py
# spawn.py:2251:_PROGRESS_BASH_PREFIXES = ("git commit", "git push", "gh pr create", ...)
# spawn.py:4812:    if command.startswith(_PROGRESS_BASH_PREFIXES):
sed -n '4630,4635p;4720,4730p;4805,4817p' spawn.py
```

### Observed
`_PROGRESS_BASH_PREFIXES` is matched inside the parent monitoring loop (`for line in proc.stdout:`, line 4725) that scans NDJSON already streamed out of the `claude` child subprocess (`Popen` at line 4630). The match at line 4812 only calls `_append_event(events_path, "progress", ...)` — pure logging in the parent's own process, with no hook back into the child to block or precede its tool execution.

### Expected
A mid-run gate capable of running the recut "immediately before" the session's own `git commit`/`gh pr create` needs a synchronous interposition point inside the session itself (e.g. the existing `PreToolUse` hook mechanism spawn.py already uses for `contract-guard.sh`, spawn.py:3456), not the parent's post-hoc, asynchronous transcript-logging site — otherwise the recut can race with (and lose to) the very command it is meant to precede, leaving the session stranded exactly as before.
