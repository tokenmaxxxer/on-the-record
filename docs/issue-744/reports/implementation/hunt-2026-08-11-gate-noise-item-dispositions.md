---
proposal: docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md
---

# Hunt record — gate-noise-item-dispositions

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the survey's "already fixed upstream, verified live" evidence for item 1 (and the untracked-file-staging half of item 4) was read from a git checkout that is a different, newer copy of tokenmaxxxer-core than the one actually cached at Claude Code's real plugin-cache path, and that real cache is stale and missing the fix.
Kind: design-error
Seed: docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md, docs/issue-744/reports/implementation/survey.md
cap_seconds: 180
tier: size:200+
diff_stat_lines: 488
started_at: 2026-08-11T07:57:25Z
ended_at: 2026-08-11T08:01:00Z

### Reproduce

```
$ diff /Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/directive.sh \
       /Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/directive.sh

$ grep -rn "reconciled-index" /Users/jk/.claude/plugins/cache/tokenmaxxxer-core/
# (no output — the string is entirely absent from the actual plugin cache tree)

$ grep -n "reconciled-index" /Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/directive.sh
163:  regenerate and stage docs/specs/reconciled-index.md (python3

$ stat -f "%Sm %N" /Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/directive.sh
Aug 11 12:03:51 2026 .../plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf/hooks/directive.sh

$ cd /Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core && \
  git show -s --format="%ci" 78f660d
2026-08-11 13:48:03 +0900
```

### Observed

Two distinct on-disk copies of tokenmaxxxer-core's `core/hooks/directive.sh`
exist on this machine, at different commits:

1. `/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core`
   — the checkout the survey describes reading ("A locally cached checkout
   of that repo (clean, tracking its own origin/main, distinct git
   history)"). It is a real git repo, `git log` shows `HEAD -> main
   [origin/main] 8178711`, working tree clean, and it **does** contain the
   issue-204 reconciled-index guidance text (commit `78f660d`, landed
   2026-08-11 13:48:03 +0900, file mtime 13:52).

2. `/Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf`
   — Claude Code's own plugin-cache path (the standard
   `~/.claude/plugins/cache/<repo>/<component>/<hash>/` layout; this
   directory carries `hooks.json` and `.claude-plugin/plugin.json`, i.e. it
   is a resolved, installed plugin bundle, not a scratch clone). Its
   `directive.sh` file mtime is 12:03:51 — **before** commit `78f660d`
   landed — and a recursive grep for "reconciled-index" across this
   entire cache tree returns nothing: the guidance text the survey cites
   as "confirmed present in this session's own context" is not merely
   absent from this file, it is absent from the whole cached bundle. The
   same diff shows this stale cache also lacks the issue-203
   untracked-file-staging guidance and the issue-204 PR-trailer-phase-split
   and test-claim-guard text — i.e. none of the three directive-text fixes
   the survey leans on for items 1 and 4 are present in it.

The survey's evidentiary chain for items 1 and 4 is: "read
tokenmaxxxer-core's git history in a local checkout" plus "this session's
own SessionStart/UserPromptSubmit context already states the fixed
guidance verbatim" — but it never checks, or even names,
`~/.claude/plugins/cache/`, which is the directory Claude Code's plugin
system actually materializes installed plugin content into (evidenced by
its `hooks.json`/`plugin.json` presence and hash-suffixed component
layout, absent from the `runs/rulebooks` checkout). If a role session's
live hooks/directive text is generated from this cache rather than from
`runs/rulebooks` — which is exactly what the standard plugin-cache
mechanism is for — then the "already fixed upstream, verified live"
disposition for item 1 (and part of item 4) is unverified at best and
possibly false for any session whose plugin cache has not been refreshed
past 2026-08-11 12:03: it would still see the old, gate-friction-causing
directive text with no error, no warning, and no visible difference from
a session that correctly received the fix — a silent split between "the
upstream repo has the fix" and "this machine's installed plugin has the
fix" that the proposal treats as settled.

### Expected

Before declaring item 1 (and the untracked-staging portion of item 4)
resolved "upstream, verified live," the survey should have identified
which on-disk copy of tokenmaxxxer-core actually backs this session's
installed "core" plugin (e.g. by locating the plugin-cache path Claude
Code resolves hooks from and diffing it against the checkout used for
git-history verification), rather than treating a `git log`/`gh issue
list` read of one clean checkout as proof of what a live role session's
directive/hook text contains. Absent that check, the proposal's phase-2
record (`docs/issue-744/reports/implementation.md`) should not state item
1 as unconditionally resolved without first confirming (or triggering a
refresh of) the plugin cache that actually governs hook execution.

### Resolution

Verified, not disputed: two on-disk copies of tokenmaxxxer-core do exist,
and the plugins/cache one is stale. But this session's actual hook
invocation does not go through the stale copy, on two independent pieces
of evidence beyond the finding's own diff:

1. This session's own environment carries
   CLAUDE_PLUGIN_ROOT_CORE=/Users/jk/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core,
   and trailer-gate.sh's own first executable line sources
   "${CLAUDE_PLUGIN_ROOT_CORE:-...}/hooks/lib/gate-lib.sh" — when this
   variable is set, it takes precedence over any fallback path, so this
   session's gates resolve from runs/rulebooks, never from the orphaned
   plugins/cache directory.
2. Independent of env-var inspection: real historical denial messages
   from actual past role sessions (issue-759's own session logs, examined
   earlier in this survey) self-report their gate's path as
   .../marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core/hooks/trailer-gate.sh
   — i.e. when trailer-gate.sh actually fired and denied a real commit
   today, the script's own BASH_SOURCE-derived self-path was already the
   runs/rulebooks copy, not plugins/cache. This is first-person evidence
   of which copy a live session executes, not an inference from
   configuration.

/Users/jk/.claude/plugins/cache/tokenmaxxxer-core/core/d0b6ce3aaddf carries
its own .orphaned_at marker (contents: a millisecond epoch timestamp),
consistent with it being a superseded artifact of Claude Code's generic
marketplace-plugin-install path that the CLAUDE_PLUGIN_ROOT_CORE override
(set by whatever provisioned this session, matching spawn.py's own
rulebook-checkout convention per the on-the-record handbook's
architecture section) has since bypassed — not a second, competing
source of truth a live role session could actually read from.

Residual risk this finding correctly surfaces, kept as a note rather than
a blocker: a session launched without CLAUDE_PLUGIN_ROOT_CORE set (e.g.
outside this provisioning path) would fall back to
"$(dirname BASH_SOURCE)/.." — wherever the hook script it actually runs
from resolves to — and could in principle read stale directive text with
no visible error. That is a provisioning-freshness question for
spawn.py/Claude Code's plugin cache, outside on-the-record's own write
set and outside #744's four items; not something this proposal's write
set can fix or needs to.

Closed. code_under_review: docs/issue-744/reports/implementation/survey.md, docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md

## before-landing

docs-only, no before-landing dispatch — every path in this commit's diff
is under docs/ (docs/issue-744/proposals/**, docs/issue-744/reports/**),
so the warrant plugin's docs-only fast path applies and the second
dispatch is skipped per that rule.
