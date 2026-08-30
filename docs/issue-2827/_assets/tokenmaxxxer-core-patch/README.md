# tokenmaxxxer-core patch — prepared, not applied here (issue-2827)

canonical: `git -C
/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core
remote -v` — `origin  https://github.com/tokenmaxxxer/tokenmaxxxer-core.git
(fetch)`. tokenmaxxxer-core is a separate GitHub repository from
on-the-record. This session is spawned against on-the-record#2827 only —
contract v3's own rule ("Requirements are user-authored GitHub ISSUES;
your issue is assigned in the spawning prompt — never pick or file one")
and the PR-target rule ("ALL of your output ... returns to the user as a
PULL REQUEST" against the assigned repo's main) both scope this session's
write authority to on-the-record, branch
issue-2827/diagnose-first+technical-writing-minimalism-scoping-9ef999ec.
It has no issue assignment, no branch, and no review path in
tokenmaxxxer-core, so it does not commit or push there. These three files
are the prepared, measured patch for a session that IS spawned against a
tokenmaxxxer-core issue to apply directly (each is a drop-in replacement
for the tokenmaxxxer-core path named by its filename, `-` standing for
`/`).

## What each file is

- `core-hooks-directive.sh` -> `core/hooks/directive.sh`: adds a
  `CORE_BUILD_NOW` branch that cats a shorter build-now-specific protocol
  file and a condensed INVARIANTS block instead of the full two-phase
  text, when `CORE_BUILD_NOW=1`. Non-build-now behavior (the `else`
  branch) is byte-identical to the file this replaces.
- `core-directive-session-protocol-build-now.md` -> new file at
  `core/directive/session-protocol-build-now.md`: the build-now variant
  of `session-protocol.md` — every bullet that still applies under
  build-now is kept verbatim (layout, commit-trailer, headless/single-shot
  delegation, board-is-merged, record required fields, terminal
  loop_state per kind, operational-surface commit rule, specs-regen,
  verify-at-landing); the two-phase default description, checkpoint-mode
  description, and the full Approve-signal mechanics (two-account vs
  single-account string-equality test, near-match reporting duty) are
  condensed to one pointer sentence back to `session-protocol.md`, since
  none of that machinery can fire while `CORE_BUILD_NOW=1` skips the
  approval boundary entirely. The phase-split PR-trailer rule is reworded
  for the single-PR build-now case (Closes/Fixes/Resolves when the issue
  is complete, Advances/Part of when intentionally partial) rather than
  removed, since a delivery PR's trailer choice still matters.
- `warrant-hooks-state.sh` -> `warrant/hooks/state.sh`: when the session
  is issue/role-scoped (`CLAUDE_SKILL` set and the current branch resolves
  to exactly `issue-<n>/<CLAUDE_SKILL>` — the same detection
  warrant-protocol's own hunt-record routing already documents), scans
  `docs/issue-<n>/proposals/` (the issue's own per-issue-layout proposals
  directory) instead of the top-level `docs/proposals/`. A non-issue-scoped
  session's behavior (the branch doesn't match, or `CLAUDE_SKILL` is
  unset) is unchanged.

## Why (measured, not assumed)

derived — this session's own real SessionStart hook output, read from its
own live session log (`type=system, subtype=hook_response` events):
```
python3 -c "
import json
p='on-the-record-issue-2827-diagnose-first+technical-writing-minimalism-scoping-9ef999ec.session.20260830T150909.863199.log'
with open(p) as f:
    lines = f.readlines()
for i in range(0, 15):
    d = json.loads(lines[i])
    if d.get('type') == 'system' and d.get('subtype') == 'hook_response':
        out = d.get('stdout') or ''
        print(d.get('hook_id'), len(out.encode('utf-8')), out[:50].replace(chr(10),' '))
"
```
result (under `$MUSTER_WORKSPACE_ROOT`):
```
91afe276-... 1026 warrant: open work units in this repository —   AW
7be3631f-... 10916 [core] Interaction protocol for role diagnose-firs
```
— 1,026 B (257 tok) for warrant's SessionStart injection, 10,916 B
(2,729 tok) for core's, both matching this issue's own established
figures for these two sources within the rounding this issue's own
byte/4≈token convention allows.

Reproduced against a scratch copy of the unmodified files (same env this
session's own spawn carries: `CLAUDE_PLUGIN_ROOT_CORE`, `CLAUDE_SKILL`,
`TOKENMAXXXER_SPAWNED=1`, `CORE_BUILD_NOW=1`, real repo/branch) —
byte-identical to the live log above (10,916 B; the extra byte vs the
1-role-name-shorter session this issue's 2,701-tok figure was measured on
is fully explained by this session's longer role-name string appearing
twice in the INVARIANTS block, `diagnose-first+technical-writing-minimalism-scoping-9ef999ec` vs `diagnose-first-6c16a19d`).

## Measured effect of the patch (scratch reproduction, before/after)

Both hooks are static heredocs/reports keyed only on env vars and repo
state (confirmed by `core/hooks/directive.sh`'s own comment: "this block
renders byte-identical every session regardless of role"), so a scratch
copy under the exact same env this session's real spawn carries
reproduces what a real spawn would inject, without needing a second
nested `claude -p` invocation (deliberately not run — see the record's
"What did not work" section for why).

`core/hooks/directive.sh`, `CORE_BUILD_NOW=1` (this session's own mode,
and the default since issue #2152):
```
CLAUDE_PLUGIN_ROOT_CORE=.../tokenmaxxxer-core/core CLAUDE_PLUGIN_ROOT=<scratch>/core \
CLAUDE_SKILL=diagnose-first+technical-writing-minimalism-scoping-9ef999ec \
TOKENMAXXXER_SPAWNED=1 CORE_BUILD_NOW=1 bash <script> | wc -c
```
before (unmodified): 10916 B = 2729.0 tok
after (this patch):   8396 B = 2099.0 tok
delta:                2520 B =  630.0 tok saved, this session's mode only

`warrant/hooks/state.sh`, this session's real repo/branch (no
`docs/issue-2827/proposals/` directory exists — confirmed: `ls
docs/issue-2827/` -> `reports` only, no `proposals`):
```
CLAUDE_PLUGIN_ROOT_CORE=.../tokenmaxxxer-core/core CLAUDE_PLUGIN_ROOT=<scratch or live>/warrant \
CLAUDE_SKILL=diagnose-first+technical-writing-minimalism-scoping-9ef999ec bash <script> | wc -c
```
before (unmodified, live): 1026 B = 257.0 tok
after (this patch):           0 B =   0.0 tok
delta:                     1026 B = 257.0 tok saved, this session's exact
state (no own open proposal)

Combined for this session's exact conditions (build-now, no own open
issue-scoped proposal — true of nearly every current spawn, since
build-now is the default per #2152 and build-now sessions never open a
proposal at all): 2520+1026=3546 B = 886.5 tok ≈ **887 tok saved**, derived:
arithmetic on the two deltas above.

Verified NOT to silently drop a real signal: with `WARRANT_PROPOSALS_REL`
resolved to a real open unit's directory
(`docs/issue-1000/proposals/`, which does hold an open, status:-proposed
file in this repo), the patched script's python body still reports it:
```
warrant: open work units in this repository —
  AWAITING APPROVAL: docs/issue-1000/proposals/implementation.md — do not start this work until the user approves it. — deferred (auto, stale since 2026-08-12T06:30:27Z)
```
— derived: running the patched script's python body directly with
`WARRANT_BRANCH=issue-1000/implementation` and the resolved
`WARRANT_PROPOSALS_REL`, against this repo's real
`docs/issue-1000/proposals/implementation.md`. And the branch-to-directory
resolution itself, tested in isolation against five cases (matching
issue-scoped branch, non-matching branch, no `CLAUDE_SKILL`, `main`,
unrelated branch) — all five resolve to the expected directory (the
matching case to its own issue's directory, all four others fall back to
the top-level `docs/proposals` unchanged).

## What this patch does NOT do

It does not touch `--append-system-prompt` files (out of scope per this
session's spawning prompt — see on-the-record#2204's live-spawn evidence
for why those ride the system prompt), does not unregister any skill or
slash command, and does not change item (d)'s composition — no code lever
was found there (see the record's item-(d) section: the bulk of that
listing is Claude Code's own built-in default skills, present regardless
of any tokenmaxxxer plugin-dir mount).
