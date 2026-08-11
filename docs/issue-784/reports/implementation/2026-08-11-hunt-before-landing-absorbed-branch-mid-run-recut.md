---
proposal: docs/issue-784/proposals/absorbed-branch-mid-run-recut.md
---

# Hunt record — absorbed-branch-mid-run-recut

## before-landing — stance 2: assume this guard goes silent when its own input is malformed — make it go silent

Verdict: FINDING — the "git commit" match is an exact string-prefix test (`cmd.lstrip().startswith("git commit")`), so any command that runs `git commit` after a preceding shell command (e.g. `cd <dir> && git commit -m x`, `set -e; git commit ...`, a `&&`/`;`-chained script) never matches, the extraction script silently exits 0 with no diagnostic, and the recut check is never invoked — inconsistent with the sibling `gh pr create` check on the very next line, which uses `re.search` (matches anywhere in the string) rather than an anchored prefix test.
Kind: silent-failure
Seed: on-the-record/hooks/absorbed-branch-recut-guard.sh (EXTRACT python heredoc, lines 79-81); spawn.py recut_if_absorbed_cli/_recut_absorbed_branch
cap_seconds: 120
tier: default
diff_stat_lines: (not measured — hunt scoped to the two touched files)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce
```
cd /tmp/testcwd
export CLAUDE_PLUGIN_ROOT=/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-784-implementation/on-the-record
echo '{"tool_name":"Bash","tool_input":{"command":"cd /tmp/testcwd && git commit -m x"}}' \
  | bash -x /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-784-implementation/on-the-record/hooks/absorbed-branch-recut-guard.sh
```

### Observed
`target_cwd=` (empty) and the script exits 0 immediately after the EXTRACT heredoc runs — `spawn.py recut-if-absorbed` is never invoked, and no stderr diagnostic is printed. The trace shows the python snippet falling through the `if not (cmd.lstrip().startswith("git commit") or ...)` branch and calling `sys.exit(0)` without ever reaching `print(os.getcwd())`.

### Expected
Per the hook's own stated purpose (recut the branch before *any* `git commit`/`gh pr create` that could surface a silent absorption), a `git commit` invoked as part of a compound command (a routine shell idiom — `cd <workdir> && git commit ...`, common when an agent's Bash tool call switches directories first) should still trigger the recut check. Instead it is silently skipped exactly like the fail-open path for genuinely malformed/absent input, so a real commit attempt on an absorbed branch gets no recut and still fails with "No commits between main and issue-<n>/<role>" — the exact failure mode issue #784 is meant to close, reopened by a command form the guard doesn't parse.
