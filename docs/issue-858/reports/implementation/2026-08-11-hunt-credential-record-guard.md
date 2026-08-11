---
proposal: docs/issue-858/proposals/credential-record-guard.md
---

# Hunt record — credential-record-guard

## after-proposal — stance 0: assume the gate this proposal is about to build is bypassable — find the bypass

Verdict: FINDING — a MultiEdit whose secret is split across two edits' `new_string` fragments (each under the ~12-char short-prefix allowance, but adjacent in the final file) is never checked as a joined/reassembled string, so a full-length credential lands in the file with each individual edit passing the guard.
Kind: design-error
Seed: docs/issue-858/proposals/credential-record-guard.md (proposal for on-the-record/hooks/credential-record-guard.sh, not yet built) — the hook is modeled on record-claim-guard.sh, which checks each of `content` / `new_string` / `edits[].new_string` as independent fragments (joined with "\n" as separate items, never concatenated char-for-char without a separator to simulate final-file adjacency), and the proposal's "under ~12 chars from prefix to end of matched run" allowance is evaluated per-fragment.
cap_seconds: 120
tier: default
diff_stat_lines: ~174 (docs-only, proposal file)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:05:00Z

### Reproduce
Simulated the proposal's described regex/allowance logic (hook not yet built) with the two-edit split a MultiEdit call would send as tool_input.edits:
```
python3 -c "
import re
pat = re.compile(r'gho_[A-Za-z0-9]{36,}')
edit1_new_string = 'token: gho_AAAAAAAAAA'   # 10 chars after prefix -> short, allowed
edit2_new_string = 'BBBBBBBBBBBBBBBBBBBBBBBBBB\n'  # 26 more chars, no gho_ prefix -> allowed
print('edit1 alone matches:', bool(pat.search(edit1_new_string)))
print('edit2 alone matches:', bool(pat.search(edit2_new_string)))
final_file_content = edit1_new_string + edit2_new_string
print('final file content matches:', bool(pat.search(final_file_content)))
"
```

### Observed
```
edit1 alone matches: False
edit2 alone matches: False
final file content matches: True
```
Each edit fragment individually is a "short truncated prefix" (or has no
matching prefix at all) and would be allowed by the guard as designed
(per-fragment matching, exactly mirroring how record-claim-guard.sh checks
`ti.get("new_string")` and each `edits[].new_string` as independent strings).
But because a MultiEdit's edits land adjacent in the resulting file
(`token: gho_AAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBB`), the two allowed writes
compose into one full 40-character `gho_` token that the guard never sees
as a single string, since it only ever checks each edit's `new_string`
value, not the reassembled file content.

### Expected
The guard should deny the write once the two edits are applied and the
resulting file contains a full-length credential — either by reading the
post-edit file content (not just the changed fragment) when the tool is
Edit/MultiEdit, or by explicitly noting this as an accepted limitation
inherited from record-claim-guard.sh's write-time-fragment approach. As
written, the proposal claims fail-closed protection against "a full-length
credential" landing in docs/**, but a credential split across two edits of
one MultiEdit call slips through undetected.

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING -- the staged diff adds on-the-record/hooks/credential-record-guard.sh (a hook script) with no matching row in docs/specs/enforcement-boundary.md or docs/specs/generated-paths.md, so gate-registration-guard.sh denies the commit outright; the write set is missing the two spec-row edits the build needs.
Kind: design-error
Seed: git diff --cached in /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-858-implementation (adds on-the-record/hooks/credential-record-guard.sh, on-the-record/hooks/test_credential_record_guard.py, docs/issue-858/reports/implementation.md; modifies on-the-record/hooks/hooks.json)
cap_seconds: 180
tier: default
diff_stat_lines: 360 insertions
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:10:00Z

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-858-implementation
grep -n "credential-record-guard" docs/specs/enforcement-boundary.md docs/specs/generated-paths.md
# (no output -- no row exists in either spec file)

python3 - <<'PYEOF'
import json, subprocess, os
payload = json.dumps({"tool_name":"Bash","tool_input":{"command":"g"+"it co"+"mmit -m test"},"cwd": os.getcwd()})
env = dict(os.environ); env["ORCHESTRATE_OFF"] = "0"
r = subprocess.run(["bash","./on-the-record/hooks/gate-registration-guard.sh"], env=env, capture_output=True, text=True, input=payload)
print("rc=", r.returncode); print("stderr=", r.stderr)
PYEOF
```

### Observed
```
rc= 2
stderr= gate-registration-guard: newly-added gate/hook module(s) missing a spec registration row (issue #441/#684):
on-the-record/hooks/credential-record-guard.sh: no row in docs/specs/enforcement-boundary.md
on-the-record/hooks/credential-record-guard.sh: no row in docs/specs/generated-paths.md
Fix the row in the same commit (docs/specs/enforcement-boundary.md, and for a hook script also docs/specs/generated-paths.md), then retry the commit.
```

### Expected
The proposal's write set (credential-record-guard.sh, its tests, hooks.json registration) should also have included a row for the new hook script in both docs/specs/enforcement-boundary.md and docs/specs/generated-paths.md, since gate-registration-guard.sh fail-closes any commit staging a newly-added on-the-record/hooks/*.sh file lacking those rows. Without them, the commit that lands this work cannot succeed.
