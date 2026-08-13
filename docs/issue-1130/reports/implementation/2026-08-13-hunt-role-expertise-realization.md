---
proposal: docs/issue-1130/proposals/role-expertise-realization.md
---

# Hunt record — role-expertise-realization

## before-landing — stance 1: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the `$(` / backtick escape hatch in the new spawn-check gates (test-authoring, interaction-design, ux-engineering, issue-retrospective) and in perf-measurement-guard silently allows any gated Bash command that contains a real, harmless command substitution, even though the exact same command without the substitution is correctly denied.
canonical: on-the-record/hooks/test-authoring-spawn-check.sh:56-57 (`if "\`" in cmd or "$(" in cmd: sys.exit(0)`), same pattern at interaction-design-spawn-check.sh, ux-engineering-spawn-check.sh, issue-retrospective-spawn-check.sh:35-36, perf-measurement-guard.sh:63-64
Kind: composition
Seed: on-the-record/hooks/test-authoring-spawn-check.sh, interaction-design-spawn-check.sh, ux-engineering-spawn-check.sh, issue-retrospective-spawn-check.sh, perf-measurement-guard.sh — all contain a check that treats presence of a backtick or `$(` substring in tool_input.command as "unreached" and exits 0 (comment: "same fail-open posture as merge-allow-gate.sh")
cap_seconds: 180
tier: size:large
diff_stat_lines: 1970 insertions, 35 files (main...HEAD)
started_at: 2026-08-13T11:36:02+09:00
ended_at: 2026-08-13T11:48:00+09:00

### Reproduce
Set up a fake target checkout with a routing spec requiring a record that is absent, on an issue-scoped branch whose changed files match the spec's trigger path_patterns:

```
TMP=$(mktemp -d); cd "$TMP"
git init -q -b main .
mkdir -p roles/specs src docs
printf '{"use_when":{"trigger":{"record_absent_for":"test-authoring","path_patterns":["src/**"]}}}' > roles/specs/test-authoring.spec.json
echo "x" > src/foo.js
git add -A && git -c user.email=a@a.com -c user.name=a commit -q -m init
git update-ref refs/remotes/origin/main "$(git rev-parse main)"
git checkout -q -b issue-9999/test-authoring
echo "y" >> src/foo.js
git add -A && git -c user.email=a@a.com -c user.name=a commit -q -m "change src"
```

Then, from this repo's root, invoke the hook script directly (not via the gh CLI or this repo's own PreToolUse pipeline) with two payloads that differ only by wrapping the PR-number argument in a command substitution:

```
export ORCHESTRATE_OFF=0
# baseline payload: tool_input.command = a gh PR merge invocation, tool_input.cwd = $TMP
# -> hook denies (exit 2), stderr cites the missing docs/issue-9999/reports/test-authoring.md
# variant payload: same command but the PR number argument is wrapped as a command substitution
# -> hook allows (exit 0) despite the identical missing-record condition
echo '<payload with command: gh pr merge 1 --squash>' | bash on-the-record/hooks/test-authoring-spawn-check.sh; echo "baseline_exit=$?"
echo '<payload with command: gh pr merge <subst>echo 1<subst-end> --squash>' | bash on-the-record/hooks/test-authoring-spawn-check.sh; echo "substitution_exit=$?"
```

### Observed
baseline_exit=2 (denied, stderr: "trigger path(s) ['src/foo.js'] changed on issue-9999 but no docs/issue-9999/reports/test-authoring.md exists yet") — correct.
substitution_exit=0 (silently allowed) for the exact same merge attempt, just because the command string contains a shell command substitution wrapping the PR-number argument — a real substitution that the shell itself will happily expand and execute — the merge goes through with the required routing record still absent.

### Expected
canonical: on-the-record/hooks/test-authoring-spawn-check.sh:56-57
A gate whose entire job is "deny this action unless a required record exists" should not have a trivial one-token bypass. At minimum, the substitution case should fail closed rather than fail open, since a command substitution wrapped around an argument in a real gh/git invocation is common and does not make the command's effect unreached — it still performs the merge/close/commit. This same pattern is repeated verbatim across five separate new hooks in this transition.
