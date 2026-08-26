---
proposal: docs/issue-2507/proposals/conformance-review.md
---

# Hunt record — conformance-review

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — approval-gate.sh's own tool_name allowlist (`("Write","Edit","MultiEdit")`) and the pretooluse_dispatcher.py registration (`tools=WRITE_TOOLS`) mean a role session's plain Bash-tool write to its own phase-2 record path (or a src/tests path) never reaches the approval check at all — the repo's checked-in gate fails open on the entire Bash surface, unconditionally, regardless of approvers.md state or any APPROVE comment.
Kind: composition
Seed: on-the-record/hooks/approval-gate.sh, on-the-record/hooks/pretooluse-dispatcher.sh, on-the-record/hooks/pretooluse_dispatcher.py (read live during this session; not part of the diff itself, which is docs-only)
cap_seconds: 60
tier: default
diff_stat_lines: 2 new files (survey.md, conformance-review.md), docs-only
started_at: 2026-08-26T17:07:59+09:00
ended_at: 2026-08-26T17:12:30+09:00

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2507-conformance-review

# repo source: approval-gate.sh's ONLY tool-name check (line 78 of the
# python GUARD body):
#   if not isinstance(e, dict) or (e.get("tool_name") or "") not in
#       ("Write", "Edit", "MultiEdit"): sys.exit(0)
# and pretooluse_dispatcher.py's own registration (line 301):
#   dict(script="approval-gate.sh", tools=WRITE_TOOLS, ...)
# — BASH_TOOLS is never unioned in for this gate, in either the
# standalone script or the single-dispatcher replica.

printf '%s\n' '{"session_id":"testsess","cwd":"'"$PWD"'","tool_name":"Bash","tool_input":{"command":"printf x > docs/issue-2507/reports/conformance-review.md"}}' > /tmp/ag_payload.json

CLAUDE_ROLE=conformance-review bash on-the-record/hooks/approval-gate.sh < /tmp/ag_payload.json
echo "exit=$?"
```

### Observed
`exit=0` — allowed, with zero stderr output (no deny, no bypass-logged
notice, nothing). No docs/specs/approvers.md was consulted, no `gh` lookup
was attempted, and CORE_BUILD_NOW was unset — the gate never even entered
its phase-2-shaped-target branch, because the tool_name check at the very
top of the GUARD body (`"Bash" not in ("Write","Edit","MultiEdit")`)
exits 0 unconditionally before the record_path / approvers.md / gh checks
are reached.

Live corroboration this session: this exact command text
(`printf x > docs/issue-2507/reports/conformance-review.md`), when run for
real as a genuine Bash tool call (not piped as inert stdin to the script),
WAS denied — but by a *different*, currently-mounted "core" rulebook copy
under `~/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/
tokenmaxxxer-core/core/hooks/pretooluse-dispatcher.sh`, whose approval-gate
apparently now also inspects Bash-tool command text (plus a separate
"citation-gate" check), diverging from the checked-in
`on-the-record/hooks/approval-gate.sh` in this working tree, which has no
such Bash coverage at all. That live copy is also over-broad in the
opposite direction — it flagged an unrelated, phase-1-legal
`mkdir -p docs/issue-2507/reports/conformance-review && test -f
docs/issue-2507/reports/conformance-review/hunt-conformance-review.md`
command purely because the filename `hunt-conformance-review.md` ends
with the substring `conformance-review.md`, suggesting its Bash-side
detection is itself pattern/substring-based rather than a real path
parse — consistent with the same class of bug (imprecise tool_name/path
scoping) on both the repo copy and whatever the mounted copy does.

### Expected
approval-gate.sh's phase-2-shaped-target check (record_path /
is_src_test) should be reachable regardless of which tool performed the
write — a role session should not be able to skip the entire
approvers.md/APPROVE-comment check simply by using the Bash tool
(`printf`, `tee`, `cat >`, `python3 -c "open(...).write(...)"`, `sed -i`,
etc.) instead of the Write/Edit/MultiEdit tool to produce the same
phase-2-shaped file. As written and as registered in
pretooluse_dispatcher.py's GATES table, it is the mechanical opposite:
a hard `tools=WRITE_TOOLS`-only scope with no Bash counterpart at all.
