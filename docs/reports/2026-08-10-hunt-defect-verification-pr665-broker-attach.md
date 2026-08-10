---
proposal: docs/proposals/2026-08-10-defect-verification-pr665-broker-attach.md
---

# Hunt record — defect-verification-pr665-broker-attach

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — record-claim-guard.sh (which governs this defect-verification role's own report writes at docs/issue-653/reports/**, per the proposal's target file) is only wired for the Write|Edit|MultiEdit matcher and only checks `tool_name in ("Write","Edit","MultiEdit")`; writing the exact same disallowed content (e.g. a bare "N of M" count claim, #333/#310/#331 shape) into the same report path via the Bash tool (heredoc/tee/cat) bypasses the check entirely and exits 0, even though contract-guard.sh -- the gate this proposal is actually about -- correctly is wired for the Bash matcher.
Kind: composition
Seed: docs/proposals/2026-08-10-defect-verification-pr665-broker-attach.md (docs-only diff: the proposal doc + docs/issue-653/reports/defect-verification.md target); applied stance to on-the-record/hooks/record-claim-guard.sh and on-the-record/hooks/hooks.json, which govern this role's own commits per the dispatcher instruction.
cap_seconds: 60
tier: default
diff_stat_lines: 2 files (docs-only)
started_at: 2026-08-10T00:00:00Z
ended_at: 2026-08-10T00:05:00Z

### Reproduce
```
export ORCHESTRATE_OFF=0
printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"docs/issue-653/reports/defect-verification.md","content":"Verified 12 of 12 checks passed."}}' | ./on-the-record/hooks/record-claim-guard.sh; echo "Write exit=$?"

printf '%s' '{"tool_name":"Bash","tool_input":{"command":"cat > docs/issue-653/reports/defect-verification.md ..."}}' | ./on-the-record/hooks/record-claim-guard.sh; echo "Bash exit=$?"
```
Also confirmed in on-the-record/hooks/hooks.json: record-claim-guard.sh is registered only under `"matcher": "Write|Edit|MultiEdit"` (no Bash), unlike contract-guard.sh which is separately wired under `"matcher": "Bash"`.

### Observed
```
== Write path ==
record-claim-guard: (issue #333 message) 'Verified 12 of 12 checks passed.' -- bare count claim, no code-fence reproduction, no derived: citation.
Write exit=2

== Bash path (identical content, same target file) ==
Bash exit=0
```
The script's own gate (`if (e.get("tool_name") or "") not in ("Write","Edit","MultiEdit"): sys.exit(0)`) exits clean for any Bash-tagged payload before ever reaching record_lint.py's checks, and hooks.json never even dispatches it for the Bash matcher.

### Expected
A role writing an unverifiable/bare-count-claim into docs/issue-*/reports/** should be denied regardless of which tool (Write vs. Bash heredoc/tee/cat) performed the write, since both produce the identical on-disk record content this gate exists to police.
