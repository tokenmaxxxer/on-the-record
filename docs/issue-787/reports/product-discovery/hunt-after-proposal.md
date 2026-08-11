---
proposal: docs/issue-787/proposals/product-discovery.md
---

# Hunt record — product-discovery

## after-proposal — stance 0: assume the gate just touched/discussed is bypassable — find the bypass

Verdict: FINDING — the "any git repo root reachable from cwd" precondition H1 specifies falls back to
`os.getcwd()` (the hook process's own working directory) whenever the PreToolUse payload's `cwd` field
is missing or empty, silently resolving relative `file_path` targets against the wrong base and letting
`root` come back `None` — an ALLOW — for a deliverable write that is actually inside a guarded repo.
Kind: silent-failure
Seed: on-the-record/hooks/deliverable-guard.sh (root-finding block: `cwd = e.get("cwd") or os.getcwd(); d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))`), read alongside docs/issue-787/proposals/product-discovery.md's H1 spec ("Target-repo precondition: ... replace it with 'any git repo root reachable from cwd'"). This root-finding code is not touched by H1's stated changes (only the tree regex and the approvers.md-presence requirement are), so the widened design inherits this fallback unchanged.
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only proposal, no code diff yet)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:01:00Z

### Reproduce
```
cd /tmp && mkdir -p bypass_test/target_repo/src && cd bypass_test/target_repo && git init -q \
  && mkdir -p docs/specs && touch docs/specs/approvers.md
cd /tmp
export ORCH_PAYLOAD='{"tool_name":"Write","tool_input":{"file_path":"src/malicious.py"},"session_id":"nosnap"}'
python3 -c "
import json, os, posixpath
e = json.loads(os.environ['ORCH_PAYLOAD'])
p = e['tool_input']['file_path']
n = posixpath.normpath(p)
cwd = e.get('cwd') or os.getcwd()
d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))
probe = posixpath.dirname(d)
root = None
while probe and probe != '/':
    if os.path.isdir(posixpath.join(probe, '.git')):
        root = probe; break
    probe = posixpath.dirname(probe)
print('root found:', root)
"
```
(This exercises the exact root-finding code already present in deliverable-guard.sh and unchanged by H1;
the payload simply omits `cwd`, which is not guaranteed present on every PreToolUse invocation and is
never validated as present/non-empty before use.)

### Observed
```
root found: None
```
The hook process's own `os.getcwd()` (here `/tmp`, wherever the hook binary happens to be invoked from)
is used instead of the target repo's actual working directory, `n` gets resolved to `/tmp/src/malicious.py`
which is nowhere near any `.git` root, so `root` is `None` and the gate falls through to `sys.exit(0)`
(ALLOW) even though the real write — relative to the session's actual cwd, `/tmp/bypass_test/target_repo` —
lands squarely inside `src/` of a repo that has `docs/specs/approvers.md` and would otherwise satisfy
even the *old*, unwidened precondition.

### Expected
The gate should either deny-and-fail-closed when it cannot determine a trustworthy cwd (matching the
guard's own stated philosophy elsewhere in the same file — "a delivery failure on stdin must not
silently become an ALLOW" — S4's fix for malformed payloads), or the root-finding must not silently
substitute the hook process's unrelated cwd for a missing session cwd. As specified, H1 replaces the
old approvers.md precondition with "any git repo root reachable from cwd" but never revisits how `cwd`
itself is obtained, so any invocation where the framework omits or blanks that field (undocumented
whether this ever happens, but the code already defends against it with `or os.getcwd()`, implying it's
anticipated) silently disables detection for every relative-path write in that turn — a silent failure
indistinguishable from a correct ALLOW on a genuinely out-of-scope path.
</content>
