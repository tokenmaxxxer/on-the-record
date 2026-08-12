---
proposal: docs/issue-1006/proposals/operator-experience-layer-build.md
---

# Hunt record — operator-experience-layer-build

## before-landing — stance 4: assume the write set cannot carry this work — find the path the build will need that the proposal does not list

Verdict: FINDING — block A's "per-workspace" first-contact marker (`${CHECKOUT}/.orchestrate-greeted`) is actually written into the single shared on-the-record repo checkout that `poll_rearm_resolve_checkout()` resolves to for every session and every workspace on the machine, so the greeting fires once ever, machine-wide, not once per workspace as designed/commented.
Kind: silent-failure
Proposal: docs/issue-1006/proposals/operator-experience-layer-build.md
Transition: before-landing
Seed: git diff of on-the-record/hooks/directive.sh (block A, .orchestrate-greeted marker gated on ${CHECKOUT})
cap_seconds: 120
tier: size:default
diff_stat_lines: (directive.sh diff ~30 added lines for block A/B/C/D; full build also adds gates/operator_experience.py + harness fixtures)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
cd on-the-record-issue-1006-implementation
env -u CLAUDE_ROLE TOKENMAXXXER_CHECKOUT="$(pwd)" ORCHESTRATE_OFF=0 bash -c '
touch spawn.py
rm -f .orchestrate-greeted
echo "=== run1 (workspace A) ==="
bash on-the-record/hooks/directive.sh | grep -A2 "First time"
echo "=== run2 (workspace B, same shared checkout, different session) ==="
bash on-the-record/hooks/directive.sh | grep -A2 "First time" || echo "(no greeting - suppressed)"
rm -f .orchestrate-greeted spawn.py
'
```

### Observed
```
=== run1 (workspace A) ===
[orchestrate] First time in this workspace — how to work with on-the-record:
...
=== run2 (workspace B, same shared checkout, different session) ===
(no greeting - suppressed)
```
Because `CHECKOUT` is `poll_rearm_resolve_checkout()`'s single resolved on-the-record clone (e.g. `~/.claude/tokenmaxxxer/on-the-record` or the marketplace clone), not anything tied to the user's actual working directory/workspace, the marker file created for the first-ever session on a machine permanently suppresses the greeting for every later workspace on that same machine, even brand-new ones a real user is seeing for the first time.

### Expected
The marker should be keyed on something that actually varies per workspace (e.g. the caller's actual `cwd`/session workspace path, or a session id), so a genuinely new workspace still gets the first-contact greeting instead of inheriting suppression from an unrelated prior session that happened to run first on the same machine.
