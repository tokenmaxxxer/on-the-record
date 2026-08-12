---
proposal: docs/issue-1033/proposals/credential-example-allowlist.md
---

# Hunt record — credential-example-allowlist

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — the allowlist module import happens before the docs/**-path scoping check in both guards, so a missing/unimportable credential_example_allowlist.py fails the ENTIRE guard closed for every Write/Edit/MultiEdit (or every Bash command, for the network guard) — not just docs/** writes — unlike the established sibling pattern (role-spec-reference-guard.sh / record-claim-guard.sh, per test_hook_cache_layout.py) where ownership/path checks are required to precede any crashable import.
Kind: design-error
Seed: on-the-record/hooks/credential_example_allowlist.py (new module), credential-record-guard.sh and credential-network-guard.sh (edited to sys.path.insert(CRG_HOOKS_DIR/CNG_HOOKS_DIR) and `from credential_example_allowlist import EXAMPLE_ALLOWLIST` at heredoc top, before any tool_name/path scoping)
cap_seconds: 120
tier: default
diff_stat_lines: 21-200 (default tier)
started_at: 2026-08-12T14:20:00+09:00
ended_at: 2026-08-12T14:35:00+09:00

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1033-implementation
mkdir -p /tmp/brokencache/hooks
cp on-the-record/hooks/credential-record-guard.sh /tmp/brokencache/hooks/
# deliberately do NOT copy credential_example_allowlist.py (e.g. a packaging/cache
# layout that misses the new sibling module, or the module simply not yet landed)
echo '{"tool_name":"Write","tool_input":{"file_path":"src/unrelated.py","content":"just plain code, no docs"}}' \
  | /tmp/brokencache/hooks/credential-record-guard.sh
echo "exit=$?"

# same for the network guard, with a completely unrelated Bash command:
mkdir -p /tmp/brokencache2/hooks
cp on-the-record/hooks/credential-network-guard.sh /tmp/brokencache2/hooks/
echo '{"tool_name":"Bash","tool_input":{"command":"echo hello world"}}' \
  | /tmp/brokencache2/hooks/credential-network-guard.sh
echo "exit=$?"
```

### Observed
```
Traceback (most recent call last):
  File "<string>", line 4, in <module>
ModuleNotFoundError: No module named 'credential_example_allowlist'
exit=2
```
for both guards — a write to `src/unrelated.py` (outside `docs/**`, the guard's own stated scope) and a `Bash` command with no credential-shaped text at all are both denied, purely because the sibling module wasn't resolvable. The `docs/` scoping check (`re.search(r"(^|/)docs/", n)`, line ~57 of credential-record-guard.sh) and the tool_name/command-shape checks in credential-network-guard.sh never run — the import exception aborts the whole process, and the shell's `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT` then maps python's non-zero exit through to exit 2 (deny) regardless of content.

### Expected
Per the guards' own stated scope ("PreToolUse (Write|Edit|MultiEdit): deny a write under docs/**...") and the precedent set by role-spec-reference-guard.sh / record-claim-guard.sh (issue #556, test_hook_cache_layout.py: "Ownership check precedes any crashable work"), a write outside docs/** (or a non-credential-shaped Bash command) should exit 0 even if the allowlist module can't be imported — the import of credential_example_allowlist should be deferred until after the path/tool scoping check, not hoisted to the top of the heredoc where it can crash-deny unrelated tool calls.
