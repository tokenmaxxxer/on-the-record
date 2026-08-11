# Hunt record — 2026-08-11-session-scoped-role-identity

proposal: docs/issue-698/proposals/2026-08-11-session-scoped-role-identity.md

(Filed under reports/implementation/ instead of reports/hunt-*.md: this
session's role is `implementation`, and board-gate.sh — contract v3 s11 —
restricts implementation-role writes to `implementation.md`/
`implementation/**` only, refusing a write to a foreign-shaped record
path even for a hunt record. Content preserved here rather than dropped.)

## after-proposal (stance 4: write set completeness)

Dispatched warrant-hunter, stance 4 ("assume the write set cannot carry
this work — find the path the build will need that the proposal does not
list"), 120s cap, default tier. The hunter could not write directly to
the intended hunt-record path either (same board-gate restriction, from
its own role) and returned its finding inline instead; recorded here by
the implementation session.

**FINDING**: the proposal's original write set omitted
`on-the-record/hooks/hooks.json`, the plugin's hook-registration
manifest. Every hook fires only via an entry in that manifest — confirmed
by reading it: `SessionStart` registered only `self-update.sh`, no
directory-scan or convention-based auto-registration exists anywhere in
the repo. Without adding a `SessionStart` entry for the new
`session-role-bind.sh`, the hook would exist on disk but Claude Code
would never invoke it — `approval-gate.sh`'s snapshot lookup would always
miss and silently fall through to the fail-open live-`CLAUDE_ROLE`
fallback, leaving the exact spoofing vector open while unit tests
(calling the script directly, bypassing the manifest) would still pass.

Reproduction:
```
grep -n "SessionStart" on-the-record/hooks/hooks.json
```
showed only the `self-update.sh` entry.

**Resolution**: `on-the-record/hooks/hooks.json` added to the proposal's
write set, and step 1 of "What will be done" now states the manifest
registration explicitly.
