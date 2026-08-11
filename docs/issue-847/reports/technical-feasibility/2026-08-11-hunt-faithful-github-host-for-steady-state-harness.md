---
proposal: docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md
---

# Hunt record — faithful-github-host-for-steady-state-harness

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — record-claim-guard.sh's claim-integrity checks (bare N-of-M count claims,
orphaned backtick path references, canonical-source-tag requirement) are scoped only to writes
under `docs/issue-*/reports/`, never to `docs/issue-*/proposals/` — so this very proposal file
(and any future issue-847 proposal, including phase-2 wiring docs it recommends) can carry
unbacked count claims and dangling path references that would be denied at write time in
reports/ but sail through untouched in proposals/. This directly touches the deliverable under
review: `docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md`
made count claims ("candidate 1... rejection reasons... apply", multiple "N of M"-shaped
citations to survey.md Probes 1-4) and dozens of backtick path references, none of which were
ever write-time-checked, because the guard's scope regex excludes `proposals/` by construction.

Kind: silent-failure
Seed: on-the-record/hooks/record-claim-guard.sh (scope regex `docs/issue-[^/]+/reports/`); proposal at docs/issue-847/proposals/2026-08-11-faithful-github-host-for-steady-state-harness.md
cap_seconds: 180
tier: default
diff_stat_lines: 399 lines / 3 files (per dispatcher)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:03:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-847-technical-feasibility
content='See `doNOTexistXYZ/nope.md` for details. 3 of 5 items pass.'

# proposals/ path — bypasses the guard
payload=$(python3 -c "import json,sys; print(json.dumps({'tool_name':'Write','tool_input':{'file_path':sys.argv[1],'content':sys.argv[2]},'cwd':sys.argv[3]}))" \
  "docs/issue-847/proposals/2026-08-11-fake-test.md" "$content" "$(pwd)")
printf '%s' "$payload" | on-the-record/hooks/record-claim-guard.sh; echo "exit=$?"

# reports/ path — same content, correctly denied
payload=$(python3 -c "import json,sys; print(json.dumps({'tool_name':'Write','tool_input':{'file_path':sys.argv[1],'content':sys.argv[2]},'cwd':sys.argv[3]}))" \
  "docs/issue-847/reports/technical-feasibility/2026-08-11-fake-test.md" "$content" "$(pwd)")
printf '%s' "$payload" | on-the-record/hooks/record-claim-guard.sh; echo "exit=$?"
```

### Observed
`proposals/` write: `exit=0` (silently allowed, no denial text) — an orphaned path reference and
a bare, uncited "3 of 5" count claim pass through untouched.
`reports/` write with identical content: `exit=2`, with denial text citing issue #333 (bare
count claim) and issue #793 (no canonical-source tag) mirrors.

### Expected
The same claim-integrity rules record-claim-guard.sh's own header describes as porting
gates.py's whole-PR CI checks (issue #457) should apply to any docs/issue-*/ deliverable a role
writes and a merge later depends on — a proposal (like this one, which makes several count/path
claims and is exactly the kind of "role output" issue #793's canonical-source-tag rule targets)
should not get a free pass just because it lives one directory name away from `reports/`.
