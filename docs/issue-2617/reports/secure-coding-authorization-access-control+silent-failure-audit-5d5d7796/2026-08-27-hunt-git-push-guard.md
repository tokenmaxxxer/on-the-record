---
proposal: (none — build-now bypass, contract v3 s19a; before-landing hunt over on-the-record/hooks/git-push-guard.sh + pretooluse_dispatcher.py registration, issue #2617)
---

# Hunt record — git-push-guard

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — a real newline between two shell statements (e.g. `true` on one line, `git push origin main` on the next) is a genuine bash command separator equivalent to `;`, but git-push-guard.sh's python-side segmenter only splits on shlex punctuation-char operator *tokens* (`&&`, `;`, `|`, `||`); a bare newline is swallowed as ordinary whitespace by `shlex.shlex(..., punctuation_chars=True)` with `whitespace_split=True`, so it never produces a segment boundary. A `git push` invocation placed after a leading no-op statement on its own line is flattened into one segment whose first token is the no-op, `_push_argv` never recognizes it as a `git push` invocation, and the whole command is allowed through untouched.
Kind: composition
Seed: on-the-record/hooks/git-push-guard.sh (new file) + GATES entry / `_grep_git_push` fastpath in on-the-record/hooks/pretooluse_dispatcher.py
cap_seconds: 180
tier: size (hooks/ directory change, mandatory full treatment per warrant-protocol.md)
diff_stat_lines: 1 new hook script (~270 lines) + ~6 line GATES/dispatcher addition
started_at: 2026-08-27T00:00:00Z
ended_at: 2026-08-27T00:10:00Z

### Reproduce
Tokenizer-level proof (`\n` between statements never becomes an operator token):

```
python3 -c "
import shlex
cmd = 'true' + chr(10) + 'git push origin main'
lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
lex.whitespace_split = True
print(list(lex))
"
# -> ['true', 'git', 'push', 'origin', 'main']   (one flat segment, no boundary at the newline)
```

End-to-end against the actual gate script (built two payloads, one plain, one with a leading no-op statement on its own line before the push):

```
GUARD=on-the-record/hooks/git-push-guard.sh

PAYLOAD_PLAIN=$(python3 -c "import json; print(json.dumps({'tool_name':'Bash','session_id':'s','tool_input':{'command':'git push origin main'}}))")
PAYLOAD_BYPASS=$(python3 -c "import json,sys; c='true'+chr(10)+'git push origin main'; print(json.dumps({'tool_name':'Bash','session_id':'s','tool_input':{'command':c}}))")

echo "$PAYLOAD_PLAIN"  | TOKENMAXXXER_SPAWNED=1 bash "$GUARD"; echo "plain rc=$?"
echo "$PAYLOAD_BYPASS" | TOKENMAXXXER_SPAWNED=1 bash "$GUARD"; echo "bypass rc=$?"
```

### Observed
```
plain rc=2
git-push-guard: a role session may not push directly to the remote's default branch ('main') ...

bypass rc=0
(no stderr output at all — silently allowed)
```
A role session's Bash-tool invocation of the two-line script

```
true
git push origin main
```

(an ordinary multi-line bash command — bash runs `true`, then `git push origin main`, exactly as if the two were separated by `;`) is let through with exit 0 by git-push-guard.sh, so the embedded push to the remote's default branch reaches git unobstructed by this gate. The bash-level fastpath grep in the `.sh` preamble still matches (both substrings "git" and "push" are present in the raw payload), so the leak is entirely inside the python segmenter's operator-token detection, not the cheap two-substring prefilter.

### Expected
Any real bash statement separator — `;`, `&&`, `||`, `|`, and a literal newline — should start a new segment for the `git push`-invocation scan, since bash treats all of them as command boundaries. A `git push origin main` (or `.../<default-branch>`) placed after any other statement on a subsequent line should be denied exactly like the single-statement form is, not silently waved through because the no-op statement it follows happened to occupy segment-index 0.

### Resolution
Fixed in the same commit: `_lexer.whitespace` is set to `" \t\r"` (dropping `\n`) after construction, while `\n` is kept in `punctuation_chars` — this routes an unquoted newline through the punctuation-token path instead of the whitespace-skip path, so it becomes its own operator token and starts a new segment, while a newline inside a quoted string (e.g. a `-m "line1\nline2"` commit body) still round-trips untouched inside its token. Reverified with the exact repro above: `true\ngit push origin main` now denies (rc=2) as a role-session push to the default branch.
