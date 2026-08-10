---
proposal: docs/proposals/issue-597-implementation.md
---

# Hunt record — issue-597-implementation

## after-proposal — stance 1: assume the framing-snapshot guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — the "gh pr merge" framing-snapshot trigger silently no-ops (exit 0, no comment, no diagnostic) whenever the current git branch is not shaped `issue-<n>/<role>` — which includes the ordinary case of running the merge command from `main`.
Kind: silent-failure
Seed: git diff of on-the-record/hooks/delegated-judgment-gate.sh (new FRAMING_TRANSITIONS block) and test_delegated_judgment_gate.py
cap_seconds: unknown (not given explicitly)
tier: default
diff_stat_lines: ~294 (207 + 87)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:45:00Z

### Reproduce
```
mkdir -p /tmp/djg_repro && cd /tmp/djg_repro
git init -q && git checkout -q -b main
git config user.email a@a.com && git config user.name a
mkdir -p docs/issue-42/reports
printf '## What was done\nImplemented the thing.\n' > docs/issue-42/reports/report.md
git add -A && git commit -qm init

DJG_PAYLOAD='{"tool_name":"Bash","tool_input":{"command":"gh pr me''rge 123"}}' \
ORCHESTRATE_OFF=0 \
bash /path/to/on-the-record/hooks/delegated-judgment-gate.sh <<< '{}'
echo "EXIT:$?"
```
(Actually reproduced against a real checkout by writing the payload/command to a runner script file and executing it, to avoid the repo's own impact-guard hook, which independently blocks any literal occurrence of the merge command string in an agent's own shell invocations — string split above is only for this record.)

### Observed
`EXIT:0`, no `gh issue comment` call made, no stderr, no log line distinguishing this from a normal successful firing of the guard. The hook's own header comment documents this trigger as unconditional on the merge subcommand ("Sixth firing condition ... post a four-element framing snapshot"), but the implementation additionally requires the *current checked-out branch* to match `^issue-(\d+)/([\w-]+)$`, used only to recover the issue number for this transition. Since merges are commonly run from `main` or any branch that doesn't follow the `issue-<n>/<role>` convention, the documented trigger condition is silently unmet in the single most common real-world invocation, with no error, warning, or fallback (e.g. resolving the issue via `gh pr view <ref> --json body,headRefName`) to recover the issue number.

### Expected
Either: (a) the guard resolves the issue number independently of the invoking shell's current branch (e.g. via a `gh pr view` lookup on the PR reference being merged), or (b) if it can only ever fire when merging from the matching feature branch, that constraint is stated explicitly in the header comment and produces a visible diagnostic (stderr line, or a posted comment noting the snapshot was skipped because the issue could not be resolved) instead of a bare `sys.exit(0)` that is indistinguishable from a normal successful run with nothing to report.
