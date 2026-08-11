---
proposal: docs/issue-787/proposals/product-discovery.md
---

# Hunt record — h1-deliverable-guard

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — a relative `cwd` in the PreToolUse payload defeats the git-root walk, silently ALLOWing a deliverable write that an absolute `cwd` (same repo, same file) correctly DENIES.
Kind: silent-failure
Seed: git diff on-the-record/hooks/deliverable-guard.sh; on-the-record/hooks/test_deliverable_guard.py
cap_seconds: 120
tier: default
diff_stat_lines: (guard script rewrite, see git diff)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:10:00Z

### Reproduce
```
mkdir -p /tmp/h1test/board-repo && cd /tmp/h1test/board-repo && git init -q
mkdir -p src

echo '{"session_id":"s1","tool_name":"Write","tool_input":{"file_path":"src/evil.py"},"cwd":"/tmp/h1test/board-repo"}' > /tmp/h1test/payload_abs.json
echo '{"session_id":"s1","tool_name":"Write","tool_input":{"file_path":"src/evil.py"},"cwd":"."}' > /tmp/h1test/payload_rel.json

cd /tmp/h1test/board-repo
env -u CLAUDE_ROLE bash on-the-record/hooks/deliverable-guard.sh < /tmp/h1test/payload_abs.json; echo "abs RC=$?"
env -u CLAUDE_ROLE bash on-the-record/hooks/deliverable-guard.sh < /tmp/h1test/payload_rel.json; echo "rel RC=$?"
```
(run with cwd `/tmp/h1test/board-repo` for the shell itself, i.e. standing right inside the board repo when the relative payload is fed)

### Observed
```
orchestrate: this is an orchestrator session and src/evil.py is a deliverable path...
abs RC=2
rel RC=0
```
The absolute-cwd payload is denied (rc=2) as intended. The relative-cwd payload (`"cwd": "."`), fed to the guard while the shell's actual working directory IS the board repo containing `src/evil.py`, is silently ALLOWED (rc=0) — same repo, same file, same session, only the string form of `cwd` differs.

### Expected
Per the H1 policy header ("Only guard writes inside a git repo reachable from cwd"), this write should be denied regardless of whether `cwd` is spelled absolutely or relatively, since it resolves to the same board-repo location either way. Root cause: `d = n if posixpath.isabs(n) else posixpath.normpath(posixpath.join(cwd, n))` never forces `cwd` itself to be absolute, so when `cwd` is relative (e.g. `"."`), `d` stays relative and the subsequent `os.path.isdir(posixpath.join(probe, ".git"))` walk is evaluated by Python against the *hook process's own* `os.getcwd()` rather than the session's real cwd — exactly the "unrelated cwd" failure mode the same code block's own deny message for missing/empty `cwd` says it exists to prevent. A relative `cwd` in the payload is a silent full bypass of the widened gate.
