---
proposal: docs/issue-2166/proposals/execution-observation-record.md
---

# Hunt record — execution-observation-record

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — approval-gate.sh is registered only for the Write|Edit|MultiEdit matcher (canonical: on-the-record/hooks/pretooluse_dispatcher.py line ~300, `dict(script="approval-gate.sh", tools=WRITE_TOOLS, ...)`), so the identical phase-2-shaped record-file write lands unchecked when issued as a Bash command instead of the Write tool; no BASH_TOOLS-registered gate re-checks approval state for that path — heredoc-command-refusal-gate.sh (canonical: on-the-record/hooks/heredoc-command-refusal-gate.sh, `_COMMIT_RE`/`_GH_WRITE_RE`) only targets git-commit/gh-issue-pr heredocs, not arbitrary file redirects.
Kind: composition
Seed: on-the-record/hooks/approval-gate.sh; on-the-record/hooks/heredoc-command-refusal-gate.sh; on-the-record/hooks/pretooluse_dispatcher.py
cap_seconds: 180
tier: size:>200-lines
diff_stat_lines: 245
started_at: 2026-08-24T00:00:00Z
ended_at: 2026-08-24T00:15:00Z

### Reproduce
Ran the real union dispatcher directly (`on-the-record/hooks/pretooluse_dispatcher.py`), same role/branch (`CLAUDE_ROLE=execution-observation` on this session's own branch), targeting this role's own record-file path (`docs/issue-<n>/reports/<role>.md` shape), no `APPROVE issue-<n>/<role>` comment present anywhere:

```
$ printf '%s' '{"session_id":"s1","cwd":"<repo>","tool_name":"Write","tool_input":{"file_path":"<record-file-path>","content":"X"}}' \
  | CLAUDE_ROLE=execution-observation python3 on-the-record/hooks/pretooluse_dispatcher.py; echo RC=$?

$ printf '%s' '{"session_id":"s1","cwd":"<repo>","tool_name":"Bash","tool_input":{"command":"cat > <record-file-path> <<'"'"'EOF'"'"'\nX\nEOF\n"}}' \
  | CLAUDE_ROLE=execution-observation python3 on-the-record/hooks/pretooluse_dispatcher.py; echo RC=$?
```
(`<record-file-path>` = this role's own `docs/issue-<n>/reports/<role>.md` target, substituted verbatim in both payloads for a like-for-like comparison.)

### Observed
canonical: direct stdout/stderr of the two `python3 on-the-record/hooks/pretooluse_dispatcher.py` invocations run above in this session's own shell, this session's own turn.

Write-tool payload -> `RC=2`, stderr: `approval-gate: no matching 'APPROVE issue-<n>/<role>' issue comment ... needs phase-2 approval first.`

Bash-tool payload, identical target path, identical missing-approval state -> `RC=0`, empty stderr, no deny of any kind from any of the 20 dispatched gates.

### Expected
canonical: on-the-record/hooks/approval-gate.sh header comment, "Closes the coverage hole step 1's fixture measurement confirmed: no deployed hook checked phase-2 approval state for a role session's own writes (its record file, src/, test/)".
Per that stated purpose, a Bash-native write to the same record-file path (`cat`/`tee`/`printf` redirection) should be equally subject to the approval check, since it produces the identical phase-2-shaped artifact the gate exists to guard. Instead the coverage hole is closed only for the Write/Edit/MultiEdit tool_name (canonical: same pretooluse_dispatcher.py registration cited above), leaving the Bash path as a live, silent bypass.

## before-landing

skip, docs-only, no before-landing dispatch — canonical: this
transition's own write set (docs/issue-2166/reports/execution-observation/survey.md,
docs/issue-2166/proposals/execution-observation-record.md, this hunt
record) is entirely under docs/, per warrant-protocol's docs-only fast
path.
