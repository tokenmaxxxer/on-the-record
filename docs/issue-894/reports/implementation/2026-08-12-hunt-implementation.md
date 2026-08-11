---
proposal: docs/issue-894/proposals/implementation.md
---

# Hunt record — implementation

## before-landing — stance 2: assume git-fetch-allow-gate.sh goes silent on malformed/edge-case input

Verdict: FINDING — a trailing/embedded newline in `tool_input.command` (e.g. `"git fetch\n"`) silently drops the allow signal for an otherwise-perfectly-shaped `git fetch`, because the hook's `"\n" in cmd` substitution-guard (line 85) rejects the whole string before shlex tokenization ever runs, and that rejection is indistinguishable from any other silent fall-through (`exit 0`, no JSON) — no error, no reason recorded anywhere.
Kind: silent-failure
Seed: on-the-record/hooks/git-fetch-allow-gate.sh (new file, PreToolUse gate for `git fetch`, part of #894's bypassPermissions removal)
cap_seconds: 120
tier: default
diff_stat_lines: ~21-200 (default tier)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
python3 -c "
import json
print(json.dumps({'tool_name':'Bash','session_id':'s1','tool_input':{'command':'git fetch\n'}}))
" | CLAUDE_ROLE= bash on-the-record/hooks/git-fetch-allow-gate.sh; echo "rc=$?"

echo "---control, same command without trailing newline---"
python3 -c "
import json
print(json.dumps({'tool_name':'Bash','session_id':'s1','tool_input':{'command':'git fetch'}}))
" | CLAUDE_ROLE= bash on-the-record/hooks/git-fetch-allow-gate.sh; echo "rc=$?"
```

### Observed
The trailing-newline case prints nothing (empty stdout) and exits 0 — the hook falls all the way through `"\n" in cmd → sys.exit(0)` with no `hookSpecificOutput`, so the resumed orchestrator gets no allow signal and (with `bypassPermissions` now removed by this same change) falls back to the host's default-deny for this Bash call. The control case (identical command, no trailing `\n`) prints the expected `{"hookSpecificOutput": {... "permissionDecision": "allow" ...}}` JSON and exits 0.

Both cases exit 0, so nothing distinguishes "recognized shape, allowed" from "rejected for containing a newline" from the process's exit code alone — this is the hook going silent on an input shape (a command string carrying a trailing `\n`, which is a normal artifact of how command strings get assembled/logged, not an attack payload) that its own design intends to allow. None of the three sibling hooks (`merge-allow-gate.sh`, `spawn-allow-gate.sh`, `gh-write-allow-gate.sh`) contain any `"\n" in cmd`-style check (`grep -n '\\\\n' on-the-record/hooks/{merge,spawn,gh-write}-allow-gate.sh` → no matches), so this substitution-guard is unique to git-fetch-allow-gate.sh and not a pattern carried over from the sibling it claims to mirror.

### Expected
A trailing newline on an otherwise well-shaped `git fetch` (or `cd DIR && git fetch`) command should not silently cancel the allow signal — at minimum the command should be stripped of trailing whitespace/newline before the substitution check, matching the intent stated in the hook's own header ("this hook only ever ADDS a permission signal"). As written, a command shape indistinguishable in meaning from the allowed one produces a different, unlogged outcome for a reason nothing surfaces.
