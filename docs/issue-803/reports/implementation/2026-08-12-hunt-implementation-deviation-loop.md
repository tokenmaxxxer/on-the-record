---
proposal: docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md
---

# Hunt record — implementation-deviation-loop

## after-proposal — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the guard's "no matching same-turn append" check has no named mechanism to determine file/turn state, because the template it's told to mirror (stop-gate.sh) has zero file-I/O capability
Kind: design-error
Seed: docs/issue-803/proposals/2026-08-12-implementation-deviation-loop.md ("What will be done" bullet for deviation-log-guard.sh)
cap_seconds: 60
tier: default
diff_stat_lines: 262 (2 files, docs-only)
started_at: 2026-08-12T11:01:47+09:00
ended_at: 2026-08-12T11:02:50+09:00

### Reproduce
```
grep -n "open(\|os.path\|subprocess\|git diff\|transcript" on-the-record/hooks/stop-gate.sh
# -> no output: stop-gate.sh performs no file, git, or transcript access at all
```
Compare to the proposal's own text (What will be done, deviation-log-guard.sh bullet):
"mirrors stop-gate.sh's shape (fail-closed trap, ORCHESTRATE_OFF kill switch,
CLAUDE_ROLE-unset orchestrator-only gate, reads the STOP_PAYLOAD env var) but
checks for a recognized-deviation marker in last_assistant_message with no
matching same-turn append to docs/issue-<n>/reports/deviation-log.md
(or docs/reports/deviation-log.md)".

### Observed
The proposal names stop-gate.sh as the shape template, and stop-gate.sh's shape
provides exactly one input: STOP_PAYLOAD's last_assistant_message string — no
file reads, no git diff, no transcript walk, no memory of what the log file
looked like before this turn. Yet the guard's actual job requires knowing
whether docs/.../deviation-log.md gained a new entry *in this turn specifically*
— a cross-turn/file-state fact that the named template cannot produce. The
sibling hook that does perform this kind of check, product-capture-stopgate.sh,
uses a different mechanism entirely (transcript_path + 
against the target file) that the proposal never names or references for this
guard. The proposal's write-set bullet asserts the "same-turn append" check as
if it followed for free from mirroring stop-gate.sh's shape; it does not — no
state exists in that shape to answer "did this file change this turn."

### Expected
Either the proposal should name the actual mechanism (e.g. product-capture-
stopgate.sh's transcript_path + git-diff cross-check pattern) as what
deviation-log-guard.sh must additionally borrow, or it should not claim
stop-gate.sh's shape suffices — as written, "mirrors stop-gate.sh's shape ...
but checks for ... no matching same-turn append" describes a check the named
template has no state to perform.
