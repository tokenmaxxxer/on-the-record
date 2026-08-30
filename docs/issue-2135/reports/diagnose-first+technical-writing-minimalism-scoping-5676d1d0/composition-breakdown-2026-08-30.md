---
kind: evidence
subject: issue-2135
doc-type: reference
---

# issue-2135 — composition breakdown, re-measurement (2026-08-30)

Scope per the issue's 2026-08-28 triage comment: "re-run the first-turn
standing-context measurement on the same shape PR #2143 measured (arm-A,
sonnet, `--single-phase`) and state the number against the ≤25K target —
then close, or reopen the diet with a fresh breakdown if it still misses."
canonical: `gh issue view 2135 --repo tokenmaxxxer/on-the-record --comments`
(2026-08-28 comment by JiwonJung94, quoted above). This file is that
re-run plus the fresh breakdown, since the number still misses.

## Basis

This session is itself a live arm-A production spawn — `sonnet`,
single-phase via `CORE_BUILD_NOW=1` (contract v3 s19a), launched through
`spawn.py` against the live board, same shape category PR #2143's
original measurement used. Session log:
`on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log`
under `$MUSTER_WORKSPACE_ROOT`.

## The number

**44,840 tokens** at first turn (9,797 cache-creation + 35,043 cache-read).

- derived:
```
python3 -c "
import json
p='.../on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log'
with open(p) as f:
    for l in f:
        d = json.loads(l)
        if d.get('type') == 'assistant':
            u = d.get('message', {}).get('usage', {})
            if u:
                print(u.get('cache_creation_input_tokens'), u.get('cache_read_input_tokens'))
                break
"
```
  result: `9797 35043` → 44,840 total.

Against target ≤25,000 tokens: misses, by 19,840 tokens (1.79x over).
Against the 2026-08-24 pre-diet baseline of 55,505 tokens — canonical:
`gh issue view 2135 --repo tokenmaxxxer/on-the-record --comments`
(2026-08-24 comment by JiwonJung94: "First-turn standing context =
31,073 cache-creation + 24,432 cache-read = 55,505 tokens") — this is a
19.2% reduction (44840/55505 = 0.808, i.e. -19.2%). The issue's other
acceptance leg (≥30% per-task cost reduction via a blind-graded ablation
re-run) is not re-measured in this file; see "What did not run" below
for why, with its own citation.

## Fresh breakdown by source

| # | Source | Measured | Owner | This repo can cut it further? |
|---|--------|----------|-------|------------------------|
| 1 | base task + spawn-assembled directive index (materialized to `<workspace>.task.txt` at spawn) | 2,563 B (≈641 tok) | on-the-record `spawn.py`/`directive_assembly.py` | No — already the post-diet size from issue #2135 / PR #2143. |
| 2 | on-demand section files, delivered via `--append-system-prompt` (issue #2204) — `completion-and-landing.md`, `repo-discovery.md`, `hook-contract.md`, `record-order.md`, `known-paths.md`, `task-lookup.md`, `turn-budget.md`, `skill-obligations.md` | 12,384 B (≈3,096 tok) | on-the-record `directive_assembly.py` | No — see "Why item 2 rides the system prompt" below. |
| 3 | per-turn UserPromptSubmit re-injection index (record-shape, proposal-shape, survey-order, freelunch, terse, warrant, scout — 7 lines), fires turn 1 and every turn | 2,969 B (≈742 tok) | tokenmaxxxer-core | No — already dieted by tokenmaxxxer-core#278. |
| 4 | CLI baseline (system prompt + tool schemas) + core plugin SessionStart hook injection + settings-sources listing | remainder: 44,840 − (641+3,096+742) ≈ 40,361 tok | Claude Code / agent-SDK harness + tokenmaxxxer-core SessionStart hook | Not owned by this repo at all. |

- derived (item 1, this spawn's own materialized task file): `wc -c
  on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.task.txt`
  under `$MUSTER_WORKSPACE_ROOT` → `2563`.
- derived (item 2, same code path this spawn used):
```
cd <workspace> && python3 -c "
import spawn, directive_assembly as da
files = da.directive_section_files(skills_mounted=True, checkpoint_block=None, code_scoped=True)
print(sum(len(v.encode('utf-8')) for v in files.values()), 'B files')
print(len(da._directive_system_prompt_block(files).encode('utf-8')), 'B system-prompt block')
"
```
  result: `12203 B files` / `12384 B system-prompt block` (the
  system-prompt block adds `# <name>` join headers over the raw file
  total, hence the small delta) — the 12,384 B figure in row 2 above.
- derived (item 3, this turn's literal reminders, copied verbatim to a
  scratch file and measured): `wc -c /tmp/ups_reminders_2135.txt` →
  `2969`.
- derived (item 3 status): canonical: `gh issue view 2135 --repo
  tokenmaxxxer/on-the-record --comments` (2026-08-28 comment: "That
  follow-up exists and is closed: tokenmaxxxer-core#278"); the 2,969 B
  measured directly above is the live confirmation that its "≤3KB
  byte-stable index" target is met in practice on this spawn.
- derived (item 4 structural facts): this session's own `system/init`
  event, field `tools` (len 26) / `slash_commands` (len 54) /
  `mcp_servers` (len 0) — read from
  `on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log`,
  first `{"type": "system", "subtype": "init", ...}` line.
- unverifiable: a same-shape historical tool/slash-command count to diff
  item 4's 26 tools / 54 slash commands / 0 mcp servers (derived: same
  `system/init` event cited in the bullet above) against — reason: the
  2026-08-24 comment on this issue recorded only the aggregate
  25,033-token CLI-baseline number, not a tool or slash-command count, so
  there is no comparable historical figure from that date.

## Amdahl check: is a further on-the-record-repo cut worth doing?

Items 1–3 (everything this repo owns) sum to 2,563 + 12,384 + 2,969 =
17,916 B ≈ 4,479 tok — 10% of the 44,840-token total (derived: 4479 /
44840 = 0.0999, arithmetic on the numbers measured above). Zeroing all
three completely (not attempted — would cost normative content) would
still leave ≈40,361 tokens, 1.61x over the 25,000 target. A repo-scope
cut is capped at a 10% share of the whole; it cannot reach the target on
its own. No edit to `spawn.py`/`directive_assembly.py`/
`on-the-record/directive/*.md` is made in this delivery — derived: `git
diff origin/main --stat -- spawn.py directive_assembly.py
'on-the-record/**'` (see the record's Acceptance verification section for
the actual post-commit output) shows no change to any of the three.

## Why item 2 rides the system prompt (issue #2204) instead of being lazy-loaded

canonical: `directive_assembly.py` lines 480-490 (read this session,
quoted in full below) — the original issue #2135 design paired
`directive_section_files()` with an inline "Read `<file>` when
`<condition>`" pointer, and issue #2204's live-spawn session log showed
sessions reading every pointed-at file sequentially before their first
task action (~46s):
```
# Issue #2204: platform-native injection for the on-demand section files.
# `directive_section_files()` used to be paired with an inline "Read <file>
# when <condition>" pointer in the stdin task text (issue #2135's design) —
# a live-spawn session log showed sessions read every pointed-at file
# sequentially before their first task action (~46s), because "read it
# when the condition holds" reads, in practice, as "read it now to be
# safe." The section files are still materialized into the workspace
```
Net effect: item 2 is always-on token weight now, not truly on-demand —
the alternative traded ~3K tokens for a ~46s-per-spawn latency and
turn-count regression, on content that (per the Amdahl check above)
cannot close the 25K gap either way. Not reopened in this delivery.

## Turn-count reducers (issue #2135 item 3) — status: already landed, still functioning

- Record skeleton pre-generation. canonical: this session read
  `docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0.md`
  as its first repo action, before any Write/Edit call in this session —
  it already carried frontmatter (`issue:`, `role:`, `author:`, `skills:`,
  `verifies_subject:`, `loop_state: in-progress`, `upstream:`) and section
  headings (What was done / Why / Upstream basis / Open findings / Next
  steps).
- Landing-sequence batching guidance. canonical: this session's own
  `--append-system-prompt` block (materialized to
  `.on-the-record/directive/completion-and-landing.md` in this
  workspace), which carries the "Landing batching (issue #2135, guidance
  only — no gate)" paragraph verbatim.

Neither needed new code this round — both are the mechanisms issue #2135
already shipped in PR #2143, observed live in this very spawn.

## What did not run (scope boundary, stated explicitly)

The issue's full Acceptance also asks for a post-diet ablation re-run of
≥2 tasks showing per-task cost down ≥30% with unchanged blind-graded
verdicts. canonical: `gh issue view 2135 --repo tokenmaxxxer/on-the-record
--comments` (2026-08-28 comment: "Remaining scope is narrow and specific:
re-run the first-turn standing-context measurement... — then close, or
reopen the diet with a fresh breakdown if it still misses. Do not treat
this as an open design question.") — that comment scopes this delivery to
the standing-context number, not a fresh ablation. No `bench/ablation.py`
run was made this session — derived: `git status --short` before this
commit shows only this record and this breakdown file as new/changed
paths, no ablation output paths among them.

## Recommendation

The ≤25K target is not reachable by any further edit inside
on-the-record — derived: the Amdahl check above (10% max repo-owned
share, arithmetic on the measured byte counts). The remaining ~40K-token
share is CLI/tool-schema baseline + core-plugin SessionStart hook —
Claude Code / agent-SDK harness scope and tokenmaxxxer-core scope, not
on-the-record. This mirrors how the per-turn item (the prior dominant
lever) was correctly spun out to tokenmaxxxer-core#278 rather than chased
inside this repo. A human maintainer should decide whether to close this
issue on the basis that on-the-record's own share is dieted and
confirmed (derived: measurements above), or open a narrowly-scoped
follow-up against the CLI/tool-schema baseline in its owning repo — this
session does not file that follow-up itself (spawned sessions do not pick
or file their own issues).
