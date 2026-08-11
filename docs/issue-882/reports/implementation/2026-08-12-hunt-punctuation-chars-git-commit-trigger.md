---
proposal: docs/issue-882/proposals/2026-08-12-punctuation-chars-git-commit-trigger.md
---

# Hunt record — punctuation-chars-git-commit-trigger

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — backtick command substitution (`` `git commit -m x` ``) is a real, executing git-commit invocation that the new `shlex.shlex(cmd, posix=True, punctuation_chars=True)` tokenizer still fuses into a non-"git" token, so all three fixed hooks (spec-index-preflight.sh, gate-registration-guard.sh, role-axis-completeness-guard.sh) silently skip their check on it — and the two hooks the fix claims this construction was "already landed and tested" in (merge-allow-gate.sh, spawn-allow-gate.sh) both explicitly guard against exactly this by bailing before tokenizing whenever `` ` `` / `$(` / `\n` appear in the raw command, a guard this commit never ported.
Kind: composition
Seed: on-the-record/hooks/spec-index-preflight.sh, on-the-record/hooks/gate-registration-guard.sh, on-the-record/hooks/role-axis-completeness-guard.sh (commit ebf6935); compared against on-the-record/hooks/merge-allow-gate.sh, on-the-record/hooks/spawn-allow-gate.sh
cap_seconds: 180
tier: size:large
diff_stat_lines: 638 insertions across 8 files
started_at: 2026-08-11T15:16:33Z
ended_at: 2026-08-11T15:18:24Z

### Reproduce

Tokenizer-level check (isolates the fusion):

```
python3 - <<'PY'
import shlex
cmd = '`git commit -m x`'
lexer = shlex.shlex(cmd, posix=True, punctuation_chars=True)
lexer.whitespace_split = True
tokens = list(lexer)
print(tokens, 'git' in tokens, 'commit' in tokens)
PY
# -> ['`git', 'commit', '-m', 'x`'] False True
```

Proof the wrapped form is a real, executing git commit (not just a syntactic curiosity):

```
TMPDIR=$(mktemp -d); cd "$TMPDIR"
git init -q; git config user.email t@t.com; git config user.name t
echo hello > file.txt; git add file.txt
bash -c '`git commit -m "backtick bypass test"`'
git log --oneline
# -> 91df7d0 backtick bypass test   (commit landed; outer shell then
#    errors "command not found" trying to run the captured commit-summary
#    line as a command, but the commit itself already happened)
```

Full end-to-end reproduction against the actual landed hook, showing the
same real drift is DENIED for a plain `git commit` and silently ALLOWED
for the backtick-wrapped equivalent:

```
TMPDIR=$(mktemp -d); cd "$TMPDIR"
git init -q; git config user.email t@t.com; git config user.name t
mkdir -p docs/specs
python3 -c "
import hashlib
content = b'ORIGINAL CONTENT\n'
h = hashlib.sha256(content).hexdigest()
open('protocol.md','wb').write(content)
open('docs/specs/reconciled-index.md','w').write('# idx\n\n| path | sha256 |\n| --- | --- |\n| \`protocol.md\` | \`%s\` |\n' % h)
"
git add -A && git commit -q -m init
python3 -c "open('protocol.md','w').write('DRIFTED CONTENT\n')"
git add protocol.md

HOOK=/path/to/on-the-record/hooks/spec-index-preflight.sh

echo -n '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"}}' | bash "$HOOK"; echo "exit: $?"
echo -n '{"tool_name":"Bash","tool_input":{"command":"`git commit -m x`"}}' | bash "$HOOK"; echo "exit: $?"
```

### Observed

Plain `git commit -m x`: hook prints
`spec-index-preflight: staged content changed for tracked spec file(s)
[protocol.md] but docs/specs/reconciled-index.md was not updated...` and
exits 2 (deny) — correct.

Backtick-wrapped `` `git commit -m x` ``: hook prints nothing and exits 0
(allow) — the same real drift is silently let through, even though the
wrapped command is a real, ordinary bash construct that actually runs
`git commit -m x` (proven above via `bash -c` + `git log`).

### Expected

Either the hook denies (or at minimum fails safe / does not silently skip
its check) for the backtick-wrapped commit exactly as it does for the
unwrapped one, since both execute the identical `git commit`. The two
hooks this construction was borrowed from (merge-allow-gate.sh,
spawn-allow-gate.sh) already encode the expected posture at line 99/114
respectively: `if "\`" in cmd or "$(" in cmd or "\n" in cmd: sys.exit(0)`
— they refuse to reason about backtick/`$(`/newline-bearing commands with
the tokenizer at all, because they know it can't be trusted there. This
commit's three hooks never adopted that guard; they run the tokenizer,
get a token list with no bare `"git"`, and treat that identically to a
command that legitimately isn't `git commit` — the fail-open branch that
was supposed to be reserved for "not a git commit," not "is a git commit
this tokenizer can't see."
