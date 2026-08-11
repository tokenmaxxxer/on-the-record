---
proposal: docs/issue-752/proposals/2026-08-11-core-judgment-capability-audit.md
---

# Hunt record — core-judgment-capability-audit

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass.

Verdict: FINDING — record-claim-guard.sh only scopes its regex to `docs/issue-*/reports/**`, so the same unverifiable/bare-count claims it blocks in a report are silently allowed in a proposal file (e.g. `docs/issue-752/proposals/*.md`, the exact file this transition just wrote).
Kind: silent-failure
Seed: git diff main issue-752/architecture -- docs/issue-752/proposals/2026-08-11-core-judgment-capability-audit.md docs/issue-752/reports/architecture/survey.md
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 206 insertions across 2 files
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:01:00Z

### Reproduce
```
export RCG_GATES_DIR="$(pwd)/on-the-record/gates"
payload=$(python3 -c '
import json
print(json.dumps({
  "tool_name":"Write",
  "tool_input":{
    "file_path":"docs/issue-752/proposals/2026-08-11-fake.md",
    "content":"unverifiable:\nSome claim: 3 of 5 items passed."
  },
  "cwd":"'"$(pwd)"'"
}))')
echo "$payload" | ORCHESTRATE_OFF=0 RCG_GATES_DIR="$RCG_GATES_DIR" bash on-the-record/hooks/record-claim-guard.sh
echo "exit=$?"
```

### Observed
`exit=0` — the write is silently allowed even though the content has an `unverifiable:` line with no reason and a bare "3 of 5 items" count claim with no `derived:` tag. Running the identical content/payload against `docs/issue-752/reports/architecture/fake.md` instead produces `exit=2` with two `record-claim-guard: 레코드에 근거 없는 개수 주장 (issue #333)` denials — proving the check logic itself works, only the path scope excludes proposals.

### Expected
Either the guard's path regex should also cover `docs/issue-*/proposals/**` (proposals make the same kind of unverifiable/count claims reports do — this transition's own proposal file, `docs/issue-752/proposals/2026-08-11-core-judgment-capability-audit.md`, contains an `unverifiable:`-adjacent discussion and count claims like "5 sub-areas"), or the guard's header comment/intent should explicitly document that proposals are out of scope and why, so the gap isn't silent.
