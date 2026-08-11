---
proposal: docs/issue-659/proposals/implementation.md
---

# Hunt record --- implementation

## after-proposal --- stance 0: assume the gate just touched is bypassable --- find the bypass

Verdict: FINDING --- Axis 1 (batch_eligible_groups) will only ever run when impact-guard.sh's
pre-existing single-command "two-or-more merge invocations" regex gate fires; issuing each PR
merge as a separate Bash tool call (one merge per command) makes the hook exit 0 before
batch_blocked or the newly planned batch_eligible_groups call is ever reached, so the whole
write-set-overlap check the proposal adds is bypassable by simply not batching commands textually,
with no denial, no audit record, and no indication anything was skipped.
Kind: silent-failure
Seed: docs/issue-659/proposals/implementation.md ("Axis 1 runs in impact-guard.sh strictly after
the existing batch_blocked call", i.e. gated behind the same single-Bash-command
two-or-more-invocations regex check) --- commit bb60242, PR #709
cap_seconds: 60
tier: default
diff_stat_lines: 158 (89 + 69, docs-only)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:25:00Z

### Reproduce
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-659-implementation
export ORCHESTRATE_OFF=0
payload={"tool_name":"Bash","tool_input":{"command":"gh pr merge 101 --merge"}}
echo "$payload" | on-the-record/hooks/impact-guard.sh
echo "exit=$?"

Repeat with a second, separate single-merge command for a second, write-set-overlapping PR --- each
call independently exits 0.

### Observed
exit=0, no stderr, no denial, no audit record written for a single-merge Bash call --- even though
merging two write-set-overlapping PRs together would trip Axis 1's planned overlap check had they
been issued as one two-merge command. The gate the proposal is chaining onto (impact-guard.sh)
short-circuits (single-invocation commands return before reaching batch_blocked ->
batch_eligible_groups) whenever an operator (or an agent working around a denial) simply issues
merges one Bash call at a time.

### Expected
The proposal should flag that Axis 1's batch-eligibility check inherits impact-guard.sh's existing
"two-or-more-in-one-command" batch definition --- and is therefore silent on sequential single-PR
merges that write-set-overlap --- the same way the ADR/proposal text explicitly calls out file-list
staleness as a known caller-side gap. As written, an operator merging two write-set-overlapping PRs
in two separate Bash calls gets no Axis 1 signal at all, silently defeating the new gate's purpose.
